"""Finite source release and exclusive canonical IO; standard library only."""

import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO / "docs/planning/b4_30_z_reflection_repair_contract.json"
CONTRACT_SHA = "ddb69d4947c01e849306b387bac5e23dbf9fd5fa42b896b29edac376b6bb63d3"
THREADS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate evidence key")
        result[key] = value
    return result


def read(path, expected=None):
    raw = Path(path).read_bytes()
    if expected is not None and sha(raw) != expected:
        raise ValueError("evidence hash differs before decoding: " + str(path))
    value = json.loads(raw, object_pairs_hook=pairs)
    if canonical(value) != raw:
        raise ValueError("canonical finite JSON required: " + str(path))
    return value


def contract():
    return read(CONTRACT_PATH, CONTRACT_SHA)


def plan_payload():
    c = contract()
    paths = subprocess.check_output(
        ["git", "ls-files", "src", "scripts", "pyproject.toml", "uv.lock", ".github/workflows"],
        cwd=REPO,
        text=True,
    ).splitlines()
    paths.extend(
        (
            "docs/numerical_conventions.md",
            "docs/planning/b4_30_z_reflection_repair_protocol.md",
            "docs/planning/b4_30_z_reflection_repair_contract.json",
        )
    )
    # Untracked source is not allowed at release; defaults still work before staging.
    paths.extend(str(p.relative_to(REPO)) for p in (REPO / "scripts").glob("b4_30_*.py"))
    paths.extend(("src/topolab/b4_reflection.py", "src/topolab/b4_reflection_repair.py"))
    value = {
        "version": c["version"],
        "contract_sha256": CONTRACT_SHA,
        "population": c["population"],
        "methods": c["methods"],
        "resources": c["resources"],
        "source_sha256": {name: digest(REPO / name) for name in sorted(set(paths))},
        "new_fits": 0,
        "final_access": False,
    }
    value["plan_sha256"] = sha(canonical(value))
    return value


def contained(root, name):
    root, name = Path(root).resolve(), Path(name)
    path = root / name
    if name.is_absolute() or ".." in name.parts or not path.resolve().is_relative_to(root):
        raise ValueError("contained evidence path required")
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise ValueError("evidence cannot follow symlinks")
    return path


def release(output):
    if Path(output).resolve().name != contract()["evidence_root_name"]:
        raise ValueError("fixed external evidence root required")
    value = read(Path(output) / "audit_receipts/production_release.json")
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
        raise ValueError("clean locked merged tested source and exact-head/main CI required")
    if any(os.environ.get(name) != "1" for name in THREADS):
        raise ValueError("all frozen BLAS/OpenMP variables must equal1")
    return head


def guard_inputs(parent, output, stage):
    journal = Path(output) / "audit_receipts" / (stage + ".access.jsonl")
    with journal.open("xb"):
        pass
    for name, expected in contract()["protected_external_metadata_sha256"].items():
        path = contained(parent, name)
        with journal.open("ab") as stream:
            stream.write(canonical({"phase": "before", "path": name, "sha256": expected}))
            stream.flush()
            os.fsync(stream.fileno())
        raw = path.read_bytes()
        if sha(raw) != expected:
            raise ValueError("protected input identity differs: " + name)
        with journal.open("ab") as stream:
            stream.write(
                canonical({"phase": "after", "path": name, "sha256": sha(raw), "bytes": len(raw)})
            )
            stream.flush()
            os.fsync(stream.fileno())
    if (Path(parent) / "b4-10-post-plateau-polish/fresh").exists():
        raise ValueError("old B4.10 fresh remains sealed")


def native(text):
    times = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", text)
    rss = re.search(r"(\d+)\s+maximum resident set size", text)
    if times is None or rss is None or int(rss[1]) <= 0:
        raise ValueError("complete native through-exit profile required")
    values = [float(times[i]) for i in (1, 2, 3)]
    if not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError("finite native times required")
    return dict(
        zip(
            ("wall_seconds", "user_seconds", "system_seconds", "rss_bytes"),
            [*values, int(rss[1])],
            strict=True,
        )
    )
