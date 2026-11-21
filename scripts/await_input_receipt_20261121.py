"""Exact 20261121 receipt signalling; no Original or payload IO."""

import argparse
import hashlib
import sys
import time
import types
from pathlib import Path

path = Path(__file__).with_name("full60_input_loader.py")
loader = sys.modules.get("full60_input_loader")
if loader is None or Path(loader.__file__).resolve() != path.resolve():
    loader = types.ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    raw = path.read_bytes()
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path.resolve())] = loader.hashlib.sha256(raw).hexdigest()
entry = Path(__file__).resolve()
loader.loaded_source_sha256[str(entry)] = loader.hashlib.sha256(entry.read_bytes()).hexdigest()
loader.install(require_locked_environment=True)
legacy = loader.load(
    "full60_metadata_signal_boundary", path.with_name("await_m2_acquisition_receipt.py")
)
window = loader.load(
    "metadata_input_window_20261121", path.with_name("metadata_input_window_20261121.py")
)
ID = "topolab.v2.p17-m2-registered-source-acquisition.20261121.v1"
PUBLIC = "/private/tmp/topolab-public-source-acquisition-20261121-a1"
FORMAL = (
    "/Users/keith1117/Library/Application Support/TopoLab-custody/"
    "p17-m2-local-input-version-20261121-a1",
)
ROOTS = (PUBLIC, *FORMAL)
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data/metadata-input-acceptance-20261121")
ROLES = legacy.ROLES
read_metadata = legacy.read_metadata


def project(plan, raw, root):
    legacy.need(
        root in ROOTS and plan["root"] == root and plan["execution_identity"] == ID,
        "NEW literal root/id",
    )
    legacy.need(
        plan["role_order"] == list(ROLES) and plan["actor_window_seconds"] == 4500,
        "NEW role/clock profile",
    )
    legacy.need(
        plan["formal_authority"] is (root in FORMAL)
        and plan["scope"]
        == (
            "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
            if root in FORMAL
            else "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
        ),
        "NEW formal scope",
    )
    window.check(plan, time.time_ns() // 10**6)
    start = legacy.milliseconds(plan["actor_activation_UTC_seconds"])
    legacy.need(start == plan["whole_start_ms"], "NEW original actor start differs")
    return dict(
        root=root,
        plan_sha256=hashlib.sha256(raw).hexdigest(),
        execution_identity=ID,
        scope=plan["scope"],
        formal_authority=plan["formal_authority"],
        actor_window_seconds=4500,
        actor_start_ms=start,
        whole_start_ms=start,
        whole_end_ms=plan["whole_end_ms"],
        role_order=list(ROLES),
        coordination_limit_ms=240000,
        applicable_deadline_ms=plan["whole_end_ms"],
    )


def caller_stop_path(root):
    legacy.need(root in ROOTS, "NEW caller STOP root")
    kind = "public" if root == PUBLIC else "formal"
    return EVIDENCE / ("input-" + kind + "-a1-caller-STOP.json")


def caller_stopped(root):
    try:
        notice, _ = read_metadata(caller_stop_path(root))
    except FileNotFoundError:
        return False
    legacy.need(
        notice.get("schema") == "topolab.input-caller-stop.20261121.v1"
        and notice.get("execution_identity") == ID
        and notice.get("root") == root,
        "NEW caller STOP identity differs",
    )
    return True


def wait(root, role, seconds):
    legacy.need(root in ROOTS and (role == "plan" or role in ROLES), "NEW root/role")
    legacy.need(type(seconds) is int and 1 <= seconds <= 160, "NEW bounded wait")
    end = time.monotonic() + seconds
    while True:
        if caller_stopped(root) or (Path(root) / "STOP.json").is_file():
            return {"status": "STOP", "source_or_payload_reads": 0}
        try:
            plan, raw = read_metadata(Path(root) / "plan.json")
            projection = project(plan, raw, root)
            proofs = []
            if role != "plan":
                for name in ROLES[: ROLES.index(role) + 1]:
                    accepted, _ = read_metadata(Path(root) / (name + "-accepted.json"))
                    proofs.append(
                        legacy.role_projection(
                            accepted, projection["plan_sha256"], name, identity=ID
                        )
                    )
            return dict(plan=projection, proofs=proofs, source_or_payload_reads=0)
        except FileNotFoundError:
            if (
                time.monotonic() >= end
                or time.time_ns() // 10**6 >= window.GLOBAL_END_MS - window.RESULT_SUFFIX_MS
            ):
                return {"status": "NOT_READY", "source_or_payload_reads": 0}
            time.sleep(min(0.05, max(0, end - time.monotonic())))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--timeout-seconds", type=int, default=160)
    a = p.parse_args()
    print(legacy.json.dumps(wait(a.root, a.role, a.timeout_seconds), sort_keys=True))


if __name__ == "__main__":
    main()
