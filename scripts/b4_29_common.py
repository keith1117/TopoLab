"""Hash-bound scalar IO and source release; no numerical imports or raw discovery."""

import hashlib
import json
import math
import os
import re
import subprocess
import traceback
from pathlib import Path
from time import perf_counter

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "docs/planning/b4_29_active_set_outcome_review_contract.json"
CONTRACT_SHA = "89555316a9895f9e7ffe65757178da9f45969fa5e19a112800c7c6a6d5ce468d"
SOURCES = (
    "scripts/b4_29_common.py",
    "scripts/b4_29_outcome_review.py",
    "scripts/b4_29_independent_audit.py",
    "scripts/b4_29_native_execution.py",
    "docs/planning/b4_29_active_set_outcome_review_contract.json",
    "docs/planning/b4_29_active_set_outcome_review_protocol.md",
    "uv.lock",
    "pyproject.toml",
)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def save(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def pairs(items):
    result = {}
    for name, value in items:
        if name in result:
            raise ValueError("duplicate metadata key")
        result[name] = value
    return result


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite metadata")
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)


def decode(data):
    value = json.loads(data, object_pairs_hook=pairs)
    finite(value)
    return value


def read(path):
    return decode(Path(path).read_bytes())


def contract():
    data = CONTRACT.read_bytes()
    if sha(data) != CONTRACT_SHA:
        raise ValueError("frozen readonly contract differs")
    return decode(data)


def plan_payload():
    c = contract()
    plan = {
        "version": c["version"],
        "contract_sha256": CONTRACT_SHA,
        "inputs_sha256": c["inputs_sha256"],
        "budget": c["new_budget"],
        "route": c["route"],
        "source_sha256": {p: digest(REPO / p) for p in SOURCES},
        "numerical_calls": 0,
        "fits": 0,
        "final_access": False,
    }
    plan["plan_sha256"] = sha(canonical(plan))
    return plan


def release(output):
    value = read(output / "audit_receipts/production_release.json")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=REPO, text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO
    )
    if (
        dirty
        or branch != "main"
        or value["source_revision"] != head
        or not value["passed"]
        or not value["main_ci_passed"]
        or not value["all_applicable_ci_passed_before_merge"]
        or not value["source_tree_same"]
        or value["plan"] != plan_payload()
        or value["owner_authorization_sha256"]
        != contract()["authority"]["owner_authorization_sha256"]
    ):
        raise ValueError("clean locked merged exact-head/main CI source required")
    return head


class Inputs:
    """The literal allowlist is checked before any input path is opened."""

    def __init__(self, root, journal, spec=None):
        self.root = Path(root).resolve()
        self.journal = Path(journal)
        self.spec = spec or contract()
        if self.root.name != self.spec["allowed_input_root_name"]:
            raise ValueError("fixed metadata input root required")
        # Exclusive journal creation prevents any repeated stage.
        with self.journal.open("xb"):
            pass

    def event(self, value):
        with self.journal.open("ab") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())

    def load(self, name):
        if name not in self.spec["inputs_sha256"]:
            raise ValueError("unregistered input rejected before open")
        path = self.root / name
        if (
            Path(name).is_absolute()
            or ".." in Path(name).parts
            or not path.resolve().is_relative_to(self.root)
            or any(p.is_symlink() for p in [path, *path.parents] if p != self.root.parent)
            or path.stat().st_size > self.spec["max_input_file_bytes"]
        ):
            raise ValueError("contained bounded regular input required")
        self.event(
            {"phase": "before", "path": name, "expected_sha256": self.spec["inputs_sha256"][name]}
        )
        data = path.read_bytes()
        if sha(data) != self.spec["inputs_sha256"][name]:
            raise ValueError("immutable scalar input identity differs")
        value = decode(data) if name.endswith(".json") else data.decode()
        self.event({"phase": "after", "path": name, "sha256": sha(data), "bytes": len(data)})
        return value

    def all(self):
        return {name: self.load(name) for name in self.spec["inputs_sha256"]}


def native(text):
    times = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", text)
    rss = re.search(r"(\d+)\s+maximum resident set size", text)
    if not times or not rss or int(rss[1]) <= 0:
        raise ValueError("complete native through-exit profile required")
    values = [float(times[i]) for i in (1, 2, 3)]
    if not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError("finite nonnegative native times required")
    return dict(
        zip(
            ("wall_seconds", "user_seconds", "system_seconds", "rss_bytes"),
            [*values, int(rss[1])],
            strict=True,
        )
    )


def execute_stage(stage, root, output, algorithm):
    started = perf_counter()
    revision = release(output)
    inputs = Inputs(root, output / (stage + ".access.jsonl"))
    try:
        result = algorithm(inputs.all(), contract(), output)
    except Exception as error:
        inputs.event({"phase": "failure", "exception": type(error).__name__, "message": str(error)})
        result = {
            "passed": False,
            "exception": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
    result.update(
        source_revision=revision,
        plan_sha256=plan_payload()["plan_sha256"],
        internal_seconds=perf_counter() - started,
        numerical_calls=0,
        fits=0,
        final_access=False,
        old_fresh_sealed=True,
    )
    save(output / (stage + ".json"), result)
    return result
