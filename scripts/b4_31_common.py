"""B4.31 source-only release guards and literal scalar IO; no numerical imports."""

import subprocess
import traceback
from pathlib import Path
from time import perf_counter

from b4_29_common import Inputs, canonical, decode, digest, read, save, sha

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "docs/planning/b4_31_reflection_failure_cost_review_contract.json"
CONTRACT_SHA = "54b99d649ad53edc0c2afbe32a87bb4c87354e97a1d6c86e851c1d0b91a895c2"
SOURCES = (
    "scripts/b4_31_common.py",
    "scripts/b4_31_reflection_failure_cost_review.py",
    "scripts/b4_31_independent_audit.py",
    "scripts/b4_31_native_execution.py",
    "scripts/b4_29_common.py",
    "scripts/b4_29_native_execution.py",
    "docs/planning/b4_31_reflection_failure_cost_review_contract.json",
    "docs/planning/b4_31_reflection_failure_cost_review_protocol.md",
    "uv.lock",
    "pyproject.toml",
)


def contract():
    data = CONTRACT.read_bytes()
    if sha(data) != CONTRACT_SHA:
        raise ValueError("frozen B4.31 contract differs")
    return decode(data)


def plan_payload():
    c = contract()
    for name, expected in c["source_and_report_sha256"].items():
        if digest(REPO / name) != expected:
            raise ValueError("historical source/report identity differs")
    plan = {
        "version": c["version"],
        "contract_sha256": CONTRACT_SHA,
        "inputs_sha256": c["inputs_sha256"],
        "budget": c["new_budget"],
        "source_sha256": {p: digest(REPO / p) for p in SOURCES},
        "numerical_calls": 0,
        "fits": 0,
        "final_access": False,
    }
    plan["plan_sha256"] = sha(canonical(plan))
    return plan


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def release(path):
    value = read(path)
    head = git("rev-parse", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")
    checks = value["required_checks"]
    required = {"quality", "frontend", "clean-linux-smoke"}
    if (
        git("status", "--porcelain", "--untracked-files=all")
        or git("branch", "--show-current") != "main"
        or git("rev-parse", "origin/main") != head
        or value["source_revision"] != head
        or value["source_tree"] != tree
        or value["tested_tree"] != tree
        or set(checks) != required
        or any(v != {"head": "success", "main": "success"} for v in checks.values())
        or not all(
            value[k]
            for k in (
                "passed",
                "locked_sync_passed",
                "protected_merge",
                "all_applicable_ci_passed_before_merge",
            )
        )
        or value["plan"] != plan_payload()
        or value["owner_authorization_sha256"]
        != contract()["authority"]["owner_authorization_sha256"]
    ):
        raise ValueError("whole-clean locked merged tested-tree/exact-head/main CI required")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", contract()["starting_main"], head],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    return head


class ScalarInputs(Inputs):
    def __init__(self, root, journal, spec):
        if Path(root).is_symlink():
            raise ValueError("nonsymlink fixed root required")
        super().__init__(root, journal, spec)

    def load(self, name):
        # Reused IO checks literal membership before stat/open. Also reject directories.
        if name not in self.spec["inputs_sha256"]:
            raise ValueError("unregistered input rejected before open")
        if not (self.root / name).is_file():
            raise ValueError("regular scalar input required")
        return super().load(name)


def execute_stage(stage, root, output, algorithm):
    started = perf_counter()
    revision = release(output / "audit_receipts/production_release.json")
    inputs = ScalarInputs(root, output / (stage + ".access.jsonl"), contract())
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
