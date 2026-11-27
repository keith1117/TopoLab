"""Independently replay the post-merge public admission before a formal B."""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUTHOR = "/root/authorize"
PUBLIC = "/private/tmp/topolab-native-bc-public-20261126-r2-merged"
CHECKS = {"quality", "frontend", "clean-linux-smoke", "i1-native-software"}
FORMAL_CONTRACT = REPO / "docs/planning/p17_m2_scientific_execution_protocol.json"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def module(name):
    path = REPO / "scripts" / (name + ".py")
    if name in sys.modules and Path(sys.modules[name].__file__) == path:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    instance = importlib.util.module_from_spec(spec)
    sys.modules[name] = instance
    spec.loader.exec_module(instance)
    return instance


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pair(root, name):
    reader = module("p17_m2_scientific_orchestration").read_native_log
    values = [
        reader(directory / name, cap=16 * 1024**2)
        for directory in (root, root.with_name(root.name + "-backup"))
    ]
    (raw, first), (backup, other) = values
    need(
        raw == backup
        and tuple(first["declared"][k] for k in ("st_dev", "st_ino"))
        != tuple(other["declared"][k] for k in ("st_dev", "st_ino")),
        "distinct matching independent release copies required",
    )
    return raw


def argv(contract, digest):
    return [
        contract["runtime"]["python_entry"],
        "-I",
        str(Path(__file__).resolve()),
        "--contract",
        str(FORMAL_CONTRACT),
        "--contract-sha",
        digest,
    ]


def check_independent(contract, contract_sha, main, release_sha):
    """Check the original independent tool terminal and both receipt copies without a child."""
    root = module("native_bc_paths").EVIDENCE
    need(
        contract["scientific_release"]["evidence_root"] == str(root)
        and not contract["public_fixture_only"],
        "registered independent release root required",
    )
    raw = pair(root, "independent-release.json")
    actual = json.loads(raw)
    need(actual["responses"], "independent release lacked original responses")
    _, _, stdout = module("r0_read_independent").terminal(
        actual,
        argv(contract, contract_sha),
        author=AUTHOR,
        cwd=str(REPO),
        window=(0, 2**53 - 1),
        full=None,
    )
    result = json.loads(stdout)
    need(
        result.get("status") == "PASS_EXACT_MERGE_PUBLIC_ENTRY"
        and result["main"] == main
        and result["release_sha256"] == release_sha
        and result["contract_sha256"] == contract_sha
        and result["B1_plan_sha256"] == contract["acquisition"]["plan_sha256"]
        and result["version"] == contract["input_version_id"]
        and result["host"] == "Apple M2"
        and result["actor"] == AUTHOR
        and result["public_raw_B_sha256"] == sha(pair(root, "merged-public-B-clock-return.json"))
        and result["public_caller_sha256"] == sha(pair(root, "merged-public-B-caller-receipt.json"))
        and result["review_sha256"] == sha(pair(root, "independent-source-review.json"))
        and result["PR_sha256"] == sha(pair(root, "protected-pr.json"))
        and result["PR_CI_sha256"] == sha(pair(root, "protected-pr-ci.json")),
        "independent release identities or original public returns differ",
    )
    return {"sha256": sha(raw), "main": main, "public_raw_B_sha256": result["public_raw_B_sha256"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--contract-sha", required=True)
    args = p.parse_args()
    need(
        sys.flags.isolated and args.contract == FORMAL_CONTRACT and Path.cwd() == REPO,
        "exact merged isolated release command required",
    )
    control = module("p17_m2_scientific_orchestration")
    paths = module("native_bc_paths")
    contract = control.read_contract(
        args.contract, args.contract_sha, publication_check=True, independent_release=True
    )
    need(
        sys.orig_argv
        == control.startup_argv(
            argv(contract, args.contract_sha), args.contract_sha, contract["runtime"]
        ),
        "actual independent release argv differs",
    )
    root = paths.EVIDENCE
    release = pair(root, "scientific-release.json")
    declaration = json.loads(release)
    candidate = json.loads(pair(root, "independent-source-review.json"))
    need(
        candidate.get("actor") == AUTHOR
        and candidate.get("status") == "PASS_SOURCE_REVIEW"
        and candidate.get("contract_sha256") == args.contract_sha
        and candidate.get("source_freeze_sha256")
        == sha(control.canonical(contract["source_freeze"])),
        "independent source review for this candidate required",
    )
    # The old public record never attested to this merged checkout.
    current = (
        control.subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, check=True, capture_output=True
        )
        .stdout.decode()
        .strip()
    )
    need(
        current == declaration["main"]
        and declaration["scope"] == "PROTECTED_MAIN"
        and declaration["scientific_contract_sha256"] == args.contract_sha,
        "current protected release identity differs",
    )
    module("scientific_publication").check_github(declaration["commands"], current)
    pr_raw = pair(root, "protected-pr.json")
    pr_capture = json.loads(pr_raw)
    need(pr_capture["exit_code"] == 0, "original PR evidence failed")
    pr = json.loads(pr_capture["stdout"])
    head = pr["headRefOid"]
    need(
        pr_capture["argv"]
        == [
            "gh",
            "pr",
            "view",
            str(pr["number"]),
            "--repo",
            "keith1117/TopoLab",
            "--json",
            "number,headRefOid,mergeCommit,baseRefName,state,statusCheckRollup",
        ]
        and pr["state"] == "MERGED"
        and pr["baseRefName"] == "main"
        and pr["mergeCommit"]["oid"] == current
        and len(head) == 40,
        "PR was not merged into this exact main",
    )
    run_raw = pair(root, "protected-pr-ci.json")
    captured = json.loads(run_raw)
    run = json.loads(captured["stdout"])
    need(
        captured["exit_code"] == 0
        and captured["argv"]
        == [
            "gh",
            "run",
            "view",
            str(run["databaseId"]),
            "--repo",
            "keith1117/TopoLab",
            "--json",
            "databaseId,event,headSha,conclusion,jobs",
        ]
        and run["event"] == "pull_request"
        and run["headSha"] == head
        and run["conclusion"] == "success",
        "original exact-head successful PR workflow required",
    )
    checks = [job for job in run["jobs"] if job.get("name") in CHECKS]
    need(
        len(checks) == 4
        and {job["name"] for job in checks} == CHECKS
        and all(job["conclusion"] == "success" and job["status"] == "completed" for job in checks),
        "four successful jobs on the exact PR head required",
    )
    host = (
        control.subprocess.run(
            ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"], check=True, capture_output=True
        )
        .stdout.decode()
        .strip()
    )
    need(host == "Apple M2" and control.os.uname().machine == "arm64", "native M2 required")
    public_path = paths.public_contract_path(PUBLIC)
    public_digest = sha(control.read_native_log(public_path, cap=4 * 1024**2)[0])
    public = control.read_contract(
        public_path, public_digest, publication_check=True, independent_release=True
    )
    need(
        public["public_fixture_only"]
        and all(
            public[key] == contract[key]
            for key in (
                "source_freeze",
                "runtime",
                "acquisition",
                "call_plan",
                "case_definitions",
                "input_role_views",
            )
        ),
        "merged public exercise differs from frozen formal software and panel",
    )
    admission = control.load("p17_m2_scientific_independent").check_b_preflight(
        public, control.load_role_evidence(public, "resource-preflight")
    )
    caller_raw = pair(root, "merged-public-B-caller-receipt.json")
    b_return = pair(root, "merged-public-B-clock-return.json")
    need(
        caller_raw == control.read_native_log(Path(PUBLIC) / "B-caller-receipt.json")[0]
        and b_return == control.read_native_log(Path(PUBLIC) / "B-clock-return.json")[0],
        "public exercise original return bytes differ",
    )
    caller = json.loads(caller_raw)
    need(
        caller["status"] == admission.proof["status"] == "PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL"
        and caller["b_caller_return_sha256"] == sha(b_return)
        and caller["source_main"] == current
        and caller["public_fixture_only"] is True
        and caller["scientific_contract_sha256"] == public_digest,
        "public terminal acceptance or merged source differs",
    )
    result = {
        "status": "PASS_EXACT_MERGE_PUBLIC_ENTRY",
        "actor": AUTHOR,
        "main": current,
        "contract_sha256": args.contract_sha,
        "release_sha256": sha(release),
        "B1_plan_sha256": paths.PLAN,
        "version": paths.VERSION,
        "host": host,
        "review_sha256": sha(pair(root, "independent-source-review.json")),
        "PR_sha256": sha(pr_raw),
        "PR_head": head,
        "PR_CI_sha256": sha(run_raw),
        "public_contract_sha256": public_digest,
        "public_caller_sha256": sha(caller_raw),
        "public_raw_B_sha256": sha(b_return),
    }
    sys.stdout.buffer.write(control.canonical(result))


if __name__ == "__main__":
    main()
