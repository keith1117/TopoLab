"""Protected release evidence must belong to this scientific commit and CI run."""

import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "scripts/scientific_publication.py"
SPEC = importlib.util.spec_from_file_location("publication_evidence_test", PATH)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
HEAD = "a" * 40


def evidence():
    def response(endpoint, payload):
        return {
            "argv": ["gh", "api", release.BASE + endpoint],
            "stdout": json.dumps(payload),
            "stderr": "",
            "exit_code": 0,
        }

    protected = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["quality", "frontend", "clean-linux-smoke"],
        },
        "enforce_admins": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
        "required_conversation_resolution": {"enabled": True},
    }
    run = {
        "head_sha": HEAD,
        "head_branch": "main",
        "id": 57,
        "status": "completed",
        "conclusion": "success",
    }
    jobs = [
        dict(head_sha=HEAD, run_id=57, name=name, status="completed", conclusion="success")
        for name in release.JOBS
    ]
    return {
        "main": response("commits/main", {"sha": HEAD}),
        "protection": response("branches/main/protection", protected),
        "runs": response(
            "actions/runs?head_sha=" + HEAD + "&per_page=100", {"workflow_runs": [run]}
        ),
        "jobs": response("actions/runs/57/jobs?per_page=100", {"jobs": jobs}),
    }


def test_four_jobs_belong_to_exact_protected_main():
    assert release.check_github(evidence(), HEAD) == 57


@pytest.mark.parametrize(
    "key,bad",
    [
        ("head_sha", "d" * 40),
        ("run_id", 13),
        ("conclusion", "skipped"),
    ],
)
def test_other_jobs_cannot_release_scientific_contract(key, bad):
    commands = evidence()
    jobs = json.loads(commands["jobs"]["stdout"])
    jobs["jobs"][-1][key] = bad
    commands["jobs"]["stdout"] = json.dumps(jobs)
    with pytest.raises(ValueError, match="four jobs"):
        release.check_github(commands, HEAD)


def test_old_commit_and_nonzero_original_fail_closed():
    commands = evidence()
    with pytest.raises(ValueError, match="current main differs"):
        release.check_github(commands, "b" * 40)
    commands["main"]["exit_code"] = False
    with pytest.raises(ValueError, match="original GitHub return"):
        release.check_github(commands, HEAD)
