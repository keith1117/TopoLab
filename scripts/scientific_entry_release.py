"""Independently replay the post-merge public admission before a formal B."""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUTHOR = "/root/r3_independent"
PUBLIC = "/private/tmp/topolab-native-bc-public-20261127-r5-merged-rows-positive"
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
        and result["public_rows_sha256"] == sha(pair(root, "independent-row-return-merged.json"))
        and result["journal_review_sha256"] == sha(pair(root, "independent-r4-journal-merged.json"))
        and result["prerow_stop_sha256"] == sha(pair(root, "merged-public-prerow-stop.json"))
        and result["public_raw_B_sha256"] == sha(pair(root, "merged-public-B-clock-return.json"))
        and result["public_caller_sha256"] == sha(pair(root, "merged-public-B-caller-receipt.json"))
        and result["review_sha256"] == sha(pair(root, "independent-source-review.json"))
        and result["PR_sha256"] == sha(pair(root, "protected-pr.json"))
        and result["PR_CI_sha256"] == sha(pair(root, "protected-pr-ci.json")),
        "independent release identities or original public returns differ",
    )
    return {"sha256": sha(raw), "main": main, "public_raw_B_sha256": result["public_raw_B_sha256"]}


def checked_rows(root, contract_sha, freeze_sha, current):
    raw = pair(root, "independent-row-return-merged.json")
    actual = json.loads(pair(root, "independent-row-return-merged-actual.json"))
    proof = json.loads(raw)
    negative = PUBLIC.removesuffix("-rows-positive") + "-rows-failure"
    expected_args = ["-B", "-I", str(root / "independent-row-return-check.py"),
                     "--phase", "merged", "--formal-contract-sha", contract_sha,
                     "--positive-root", PUBLIC, "--failure-root", negative]
    need(actual["exit"] == 0 and actual["argv"][1:] == expected_args
         and Path(actual["argv"][0]).is_absolute() and actual["cwd"] == str(REPO)
         and actual["stdout"].encode("utf-8") == raw and actual["stderr"] == "",
         "original independently executed row review required")
    need(proof["status"] == "PASS_PUBLIC_ROW_RETURN_REVIEW" and proof["phase"] == "merged"
         and proof["source_main"] == current and proof["scientific_contract_sha256"] == contract_sha
         and proof["source_freeze_sha256"] == freeze_sha
         and proof["checker_sha256"] == sha(pair(root, "independent-row-return-check.py"))
         == json.loads(pair(root, "independent-source-review.json"))["checker_sha256"],
         "independent public row review binding differs")
    for key, path in (("positive", PUBLIC), ("failure", negative)):
        read = module("p17_m2_scientific_orchestration").read_native_log
        digest = sha(read(Path(path + ".contract.json"), cap=4 * 1024**2)[0])
        original = read(Path(path) / "scientific-producer-controller-actual.json",
                        cap=16 * 1024**2)[0]
        need(proof[key]["contract_sha256"] == digest
             and proof[key]["original_return_sha256"] == sha(original),
             "original merged public row controller differs")
    return sha(raw)


def checked_prerow_stop(root, freeze, current):
    control = module("p17_m2_scientific_orchestration")
    directory = Path(PUBLIC.removesuffix("-rows-positive") + "-rows-prerow")
    path = module("native_bc_paths").public_contract_path(directory)
    contract_sha = sha(control.read_native_log(path)[0])
    public = control.read_contract(path, contract_sha, publication_check=True,
                                   independent_release=True)
    admission = json.loads(control.read_native_log(directory / "B-caller-receipt.json")[0])
    name = "scientific-producer-controller-stop.json"
    raw = pair(root, "merged-public-prerow-stop.json")
    stop = json.loads(raw)
    original = control.read_native_log(directory / "scientific-producer-controller-actual.json")[0]
    need(public.get("public_row_fixture") == "rows-prerow" and public["source_freeze"] == freeze
         and admission["source_main"] == current
         and admission["scientific_contract_sha256"] == contract_sha
         and admission["status"] == "PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL"
         and raw == control.read_native_log(directory / name)[0]
         and stop["status"] == "STOP_C_CONTROLLER_OBSERVED"
         and stop["contract_sha256"] == contract_sha
         and stop["actual_sha256"] == sha(original) and stop["successor_authorized"] is False
         and stop["planned_rows"] == stop["unattempted_rows"] == 20
         and stop["attempted_rows"] == stop["fully_filed_rows"] == 0
         and stop["payload_exit"] != 0 and stop["controller_exit"] != 0
         and stop["c_wall_to_return_seconds"] > 0 and stop["conservative_recorded_peak_bytes"] > 0,
         "registered pre-panel write failure and actual zero-row STOP required")
    return sha(raw)


def checked_journal(root, contract, contract_sha, current):
    name = "independent-r4-journal-check.py"
    raw = pair(root, "independent-r4-journal-merged.json")
    actual = json.loads(pair(root, "independent-r4-journal-merged-actual.json"))
    review = json.loads(pair(root, "independent-source-review.json"))
    expected = ["-B", "-I", str(root / name), "--phase", "merged",
                "--formal-contract-sha", contract_sha]
    need(actual["exit"] == 0 and Path(actual["argv"][0]).is_absolute()
         and actual["argv"][1:] == expected and actual["cwd"] == str(REPO)
         and actual["stdout"].encode("utf-8") == raw and actual["stderr"] == "",
         "original exact-merge long journal check required")
    proof = json.loads(raw)
    control = module("p17_m2_scientific_orchestration")
    need(proof["status"] == "PASS_INDEPENDENT_R4_JOURNAL_AND_LARGE_PREFIX"
         and proof["actor"] == AUTHOR and proof["phase"] == "merged"
         and proof["attempt_id"] == contract["attempt_id"] and proof["source_main"] == current
         and proof["scientific_contract_sha256"] == contract_sha
         and proof["source_freeze_sha256"] == sha(control.canonical(contract["source_freeze"]))
         and proof["driver_sha256"] == contract["source_freeze"]["scripts/native_bc_api_driver.js"]
         and proof["checker_sha256"] == review["journal_checker_sha256"] == sha(pair(root, name))
         and proof["prior_terminal_prefix_sha256"]
         == "4c8ecdf41d275ad332adc1cd27ffcdc719c1f093689b74ca8d58076c5e863e4c"
         and proof["formal_roles"] == proof["scientific_payload_opens"] == 0,
         "independent long journal proof or closed-source identity differs")
    positive = proof["positive"]
    need(positive["true_replies"] >= 217 and positive["final_outer_exit"] == 0
         and positive["truncation"] is False and 0 < positive["source_expression_bytes"] <= 64000,
         "observed long control return and bounded public entry required")
    return sha(raw)


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
        "public_rows_sha256": checked_rows(
            root, args.contract_sha, sha(control.canonical(contract["source_freeze"])), current
        ),
        "actor": AUTHOR,
        "journal_review_sha256": checked_journal(root, contract, args.contract_sha, current),
        "prerow_stop_sha256": checked_prerow_stop(root, contract["source_freeze"], current),
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
