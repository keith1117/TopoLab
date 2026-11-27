"""Check the scientific release independently from the B1 issuance commit."""

import hashlib
import json
import re
from pathlib import Path

BASE = "repos/keith1117/TopoLab/"
JOBS = {"quality", "frontend", "clean-linux-smoke", "i1-native-software"}


def need(ok, message):
    if not ok:
        raise ValueError("scientific publication: " + message)


def checkout_head(repo, read):
    git = repo / ".git"
    head = read(git / "HEAD").decode("ascii").strip()
    if head.startswith("ref: "):
        ref = head.removeprefix("ref: ")
        need(
            re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+", ref)
            and all(part not in (".", "..", "") for part in ref.split("/")),
            "invalid checkout ref",
        )
        try:
            head = read(git / ref).decode("ascii").strip()
        except FileNotFoundError:
            lines = read(git / "packed-refs").decode("ascii").splitlines()
            matches = [line.split()[0] for line in lines if line.endswith(" " + ref)]
            need(len(matches) == 1, "cannot resolve checkout ref")
            head = matches[0]
    need(re.fullmatch(r"[0-9a-f]{40}", head), "invalid checkout commit")
    return head


def check_github(commands, main):
    def response(name, endpoint):
        row = commands[name]
        need(
            row["argv"] == ["gh", "api", BASE + endpoint]
            and type(row["exit_code"]) is int
            and row["exit_code"] == 0
            and isinstance(row["stderr"], str)
            and isinstance(row["stdout"], str),
            "original GitHub return differs: " + name,
        )
        return json.loads(row["stdout"])

    need(response("main", "commits/main")["sha"] == main, "current main differs")
    protection = response("protection", "branches/main/protection")
    required = protection["required_status_checks"]
    need(
        required["strict"] is True
        and protection["enforce_admins"]["enabled"] is True
        and protection["allow_force_pushes"]["enabled"] is False
        and protection["allow_deletions"]["enabled"] is False
        and protection["required_conversation_resolution"]["enabled"] is True
        and {"quality", "frontend", "clean-linux-smoke"} <= set(required["contexts"]),
        "protected branch rules differ",
    )
    runs = response("runs", "actions/runs?head_sha=" + main + "&per_page=100")["workflow_runs"]
    passed = {
        run["id"]
        for run in runs
        if run["head_sha"] == main
        and run["head_branch"] == "main"
        and run["status"] == "completed"
        and run["conclusion"] == "success"
        and type(run["id"]) is int
    }
    endpoint = commands["jobs"]["argv"][-1]
    match = re.fullmatch(
        re.escape(BASE) + r"actions/runs/([1-9][0-9]*)/jobs\?per_page=100", endpoint
    )
    need(match and int(match[1]) in passed, "successful exact main CI run missing")
    run_id = int(match[1])
    jobs = response("jobs", "actions/runs/" + str(run_id) + "/jobs?per_page=100")["jobs"]
    need(
        JOBS
        <= {
            job["name"]
            for job in jobs
            if job["run_id"] == run_id
            and job["head_sha"] == main
            and job["status"] == "completed"
            and job["conclusion"] == "success"
        },
        "four jobs on exact scientific commit required",
    )
    return run_id


def checked_release(contract, contract_sha, role, head, paths, read_file, freeze_sha):
    root = Path(contract["api_metadata"]["root"])
    scope = paths.scope(root)
    public = scope == "ENGINEERING_PUBLIC"
    evidence = root if public else paths.EVIDENCE
    spec = contract["scientific_release"]
    need(
        contract["public_fixture_only"] is public
        and head != paths.HISTORICAL
        and (not public or role == "resource-preflight")
        and spec
        == dict(scope=scope, evidence_root=str(evidence), basename="scientific-release.json"),
        "scope, role, checkout or release location differs",
    )
    name = spec["basename"]
    left, a = read_file(evidence / name)
    right, b = read_file(evidence.with_name(evidence.name + "-backup") / name)
    physical = ("st_dev", "st_ino")
    need(
        left == right
        and tuple(a["before"][k] for k in physical) != tuple(b["before"][k] for k in physical),
        "release pair differs",
    )
    record = json.loads(left)
    need(
        record["schema"] == "topolab.scientific-release.v1"
        and record["scope"] == scope
        and record["scientific_contract_sha256"] == contract_sha
        and record["main"] == head
        and record["source_freeze_sha256"] == freeze_sha,
        "different scientific commit/contract/freeze",
    )
    result = dict(main=head, scope=scope, release_sha256=hashlib.sha256(left).hexdigest())
    if not public or "commands" in record:
        result["main_CI_run"] = check_github(record["commands"], head)
    return result
