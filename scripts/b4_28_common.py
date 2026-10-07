"""Frozen roles, source release, exclusive IO and durable finite calls."""

import argparse
import hashlib
import json
import os
import resource
import subprocess
import traceback
from pathlib import Path
from time import perf_counter

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "docs/planning/b4_28_active_set_execution_contract.json"
CONTRACT_SHA = "acfb9cac7dedd01270bee301cf807b27c68585cd4b9f0ee55baf2f4af830642d"
THREADS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
KINDS = ("label", "fem", "projection", "pointwise", "interval")


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def save(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def read(path, expected=None):
    data = Path(path).read_bytes()
    if expected is not None and sha(data) != expected:
        raise ValueError("immutable input identity differs: " + str(path))
    return json.loads(data)


def contract():
    value = read(CONTRACT, CONTRACT_SHA)
    if (
        value["version"] != "topolab.b4_28.active-set-numerical-evidence.v1"
        or not value["owner_authorized"]
    ):
        raise ValueError("separate frozen owner contract required")
    return value


def plan_payload():
    value = contract()
    plan = {
        "version": value["version"],
        "contract_sha256": CONTRACT_SHA,
        "population": value["population"],
        "execution": value["execution"],
        "budget": value["new_budget"],
        "source_sha256": value["source_and_contract_sha256"],
        "input_sha256": value["allowed_inputs_after_released_source"],
        "fits": 0,
        "final_access": False,
        "old_fresh_sealed": True,
        "prediction_timing": False,
    }
    plan["plan_sha256"] = sha(canonical(plan))
    return plan


def entries():
    from topolab.b3_catalog import B3CatalogEntry

    return tuple(B3CatalogEntry.model_validate(e) for e in contract()["population"]["entries"])


def peak_rss():
    # macOS reports bytes; Linux reports KiB.
    import sys

    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def check_budget(started):
    if perf_counter() - started + 10 > 600 or peak_rss() > 1073741824:
        raise RuntimeError("frozen stage time or native memory cap exceeded")


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("legacy", "data", "output"):
        parser.add_argument("--" + name + "-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    roots = tuple(p.resolve() for p in (args.legacy_root, args.data_root, args.output_root))
    if (
        any(p.is_relative_to(REPO) for p in roots)
        or any(a.is_relative_to(b) for a in roots for b in roots if a != b)
        or len(set(roots)) != 3
    ):
        raise ValueError("separate external roots required")
    if args.execute and (
        tuple(p.name for p in roots)
        != (
            "b4-23-versioned-surrogate-feasibility",
            "b3-v1-data",
            "b4-28-active-set-numerical-evidence",
        )
        or len({p.parent for p in roots}) != 1
    ):
        raise ValueError("fixed sibling roots required")
    return args, *roots


def source_manifest():
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO).decode().split("\0")
    named = {
        "PROVENANCE.md",
        "docs/numerical_conventions.md",
        "docs/planning/b4_28_active_set_numerical_evidence_protocol.md",
        str(CONTRACT.relative_to(REPO)),
        "pyproject.toml",
        "uv.lock",
    }
    return {
        p: digest(REPO / p)
        for p in paths
        if p and (p in named or (p.endswith(".py") and p.startswith(("src/", "scripts/"))))
    }


def ci_passed(checks, head, main):
    return (
        bool(checks)
        and {"quality", "frontend", "clean-linux-smoke"} <= {c["name"] for c in checks}
        and any(c["name"] == "clean-linux-smoke" and c["conclusion"] == "success" for c in checks)
        and all(
            c["head_sha"] == head
            and c["status"] == "completed"
            and (
                c["conclusion"] == "success"
                or (not main and c["name"] == "clean-linux-smoke" and c["conclusion"] == "skipped")
            )
            for c in checks
        )
    )


def release(output):
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO):
        raise ValueError("clean tracked committed source required")
    if any(os.environ.get(k) != "1" for k in THREADS):
        raise ValueError("five one-thread CPU settings required")
    data = read(output / "audit_receipts/production_release.json")
    if (
        data["source_revision"] != revision
        or data["plan"] != plan_payload()
        or not data["all_applicable_ci_passed_before_merge"]
        or not data["main_ci_passed"]
    ):
        raise ValueError("clean merged exact-head/main CI source release required")
    if not ci_passed(data["head_ci"], data["tested_head"], False) or not ci_passed(
        data["main_ci"], revision, True
    ):
        raise ValueError("all actual exact-head/main required checks needed")
    tree = subprocess.check_output(
        ["git", "rev-parse", revision + "^{tree}"], cwd=REPO, text=True
    ).strip()
    tested = subprocess.check_output(
        ["git", "rev-parse", data["tested_head"] + "^{tree}"], cwd=REPO, text=True
    ).strip()
    if tree != tested or data["source_sha256"] != source_manifest():
        raise ValueError("complete identical tested/merged source manifest required")
    for path, expected in data["source_sha256"].items():
        if digest(REPO / path) != expected:
            raise ValueError("released source identity differs: " + path)
    for path, expected in contract()["source_and_contract_sha256"].items():
        if digest(REPO / path) != expected:
            raise ValueError("unchanged prerequisite differs: " + path)
    return revision


def legacy_inputs(root):
    expected = contract()["allowed_inputs_after_released_source"]["b4_23_sha256"]
    for name, value in expected.items():
        if digest(root / name) != value:
            raise ValueError("immutable legacy file differs: " + name)
    panel = read(root / "probe.json")
    audit = read(root / "independent_audit.json")
    flags = audit["condition_results"]
    ids = [e.case.case_id for e in entries()]
    if (
        len(flags) != 3976
        or any(type(v) is not bool for v in flags)
        or sum(flags) != 3907
        or audit["failed_condition_indices"] != [i for i, flag in enumerate(flags) if not flag]
    ):
        raise ValueError("all3976 original flags and69 failed positions required")
    if [(r["case_id"], r["state"]) for r in panel["rows"]] != [
        (cid, j) for cid in ids for j in range(9)
    ] or [r["case_id"] for r in panel["labels"]] != ids:
        raise ValueError("complete ordered legacy population required")
    if (
        sum(len(r["differences"]) for r in panel["rows"]) != 64
        or sum(len(r["timings"]) for r in panel["rows"]) != 216
    ):
        raise ValueError("all original intervals/first timings required")
    return panel, audit


def label_index(data):
    from topolab.b3_materialization import B3MaterializationIndex

    value = contract()["allowed_inputs_after_released_source"]["b3_index_sha256"]
    index = B3MaterializationIndex.model_validate(read(data / "b3_materialization.json", value))
    if not index.data_gate_passed:
        raise ValueError("closed B3 data Gate required")
    return index


def train_label(data, index, entry):
    from b4_15_offline_compliance_adjoint import train_label as guarded_read

    if (
        entry.model_dump(mode="json") not in contract()["population"]["entries"]
        or entry.role != "train"
        or "expanded" not in entry.training_sets
    ):
        raise ValueError("reject role/population before artifact lookup")
    return guarded_read(data, index, entry)


class Journal:
    def __init__(self, path, revision):
        self.path = Path(path)
        self.stream = self.path.open("xb")
        self.revision = revision
        self.plan_sha = plan_payload()["plan_sha256"]
        self.sequence = 0
        self.counts = {kind: {"attempted": 0, "completed": 0} for kind in KINDS}
        self.emit("start")

    def emit(self, event, **values):
        self.stream.write(
            canonical(
                {
                    "sequence": self.sequence,
                    "event": event,
                    "source_revision": self.revision,
                    "plan_sha256": self.plan_sha,
                    "counts": self.counts,
                    **values,
                }
            )
        )
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.sequence += 1

    def invoke(self, kind, case_id, context, call, encode):
        self.counts[kind]["attempted"] += 1
        self.emit("before_" + kind, case_id=case_id, context=context)
        try:
            result = call()
        except Exception as error:
            self.emit(
                "failure",
                case_id=case_id,
                context=context,
                error_type=type(error).__name__,
                error=str(error),
                traceback=traceback.format_exc(),
            )
            raise
        self.counts[kind]["completed"] += 1
        try:
            encoded = encode(result)
        except Exception as error:
            self.emit(
                "after_" + kind,
                case_id=case_id,
                context=context,
                result={"encoding_failed": True, "error": str(error)},
            )
            raise
        self.emit("after_" + kind, case_id=case_id, context=context, result=encoded)
        return result

    def close(self):
        self.stream.close()


def event_prefix(path, revision=None, allow_incomplete=False):
    payload = Path(path).read_bytes()
    lines = payload.splitlines()
    if not payload.endswith(b"\n"):
        if not allow_incomplete:
            raise ValueError("complete durable lines required")
        lines = lines[:-1]
    events = [json.loads(line) for line in lines]
    counts = {kind: {"attempted": 0, "completed": 0} for kind in KINDS}
    pending = []
    if not events or events[0]["event"] != "start":
        raise ValueError("durable start required")
    for sequence, event in enumerate(events):
        if (
            event["sequence"] != sequence
            or event["plan_sha256"] != plan_payload()["plan_sha256"]
            or (revision is not None and event["source_revision"] != revision)
        ):
            raise ValueError("durable source/plan/sequence differs")
        for kind in KINDS:
            if event["event"] == "before_" + kind:
                counts[kind]["attempted"] += 1
                pending.append((kind, event["case_id"], event["context"]))
            elif event["event"] == "after_" + kind:
                if not pending or pending.pop() != (kind, event["case_id"], event["context"]):
                    raise ValueError("completion lacks identical durable before-call")
                counts[kind]["completed"] += 1
        if event["counts"] != counts:
            raise ValueError("durable counters differ")
    return events, counts, pending


def finish(output, name, result, journal, started):
    check_budget(started)
    journal.emit("complete")
    result.update(
        plan=plan_payload(),
        source_revision=journal.revision,
        counts=journal.counts,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
        journal_sha256=digest(journal.path),
    )
    save(output / (name + ".json"), result)


def failed(journal, error):
    journal.emit(
        "abort", error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc()
    )
