"""Registration gates use generated files and untrusted packet variants in these tests."""

import hashlib
import importlib
import json
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def binding(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("staged_public_binding")


def test_separate_readers_register_a_single_fixed_generation(binding, tmp_path):
    source = tmp_path.resolve() / "source"
    expected = {}
    for item in binding.producer.whitelist():
        target = source / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        data = item["path"].encode()
        target.write_bytes(data)
        target.chmod(0o600)
        expected[item["path"]] = (len(data), hashlib.sha256(data).hexdigest())
    a = binding.producer.scan(source, expected, availability=True)
    b = binding.independent.scan(source, expected, availability=True)
    p = binding.producer.scan(source, expected, availability=False)
    i = binding.independent.scan(source, expected, availability=False)
    assert binding.independent.compare(expected, a, b, p, i) == i
    name = next(iter(expected))
    path = source / name
    other = path.with_suffix(".new")
    other.write_bytes(path.read_bytes())
    other.chmod(0o600)
    other.replace(path)
    replaced = binding.independent.scan(source, expected, availability=False)
    with pytest.raises(ValueError, match="disagree"):
        binding.independent.compare(expected, a, b, p, replaced)


def test_prior_actual_return_sets_result_clock(binding):
    plan = {"core_start_ms": 70000, "prepared_ms": 70100, "core_end_ms": 1870000}
    prior = [{"returned_ms": ms} for ms in (80000, 90000, 100000, 110000, 120000)]
    assert binding.plan_window(binding.ROLES[4], prior[:4], plan) == (110000, 1870000)
    assert binding.plan_window(binding.ROLES[5], prior, plan) == (120000, 1920000)


def test_external_terminal_gates_next_role(binding, monkeypatch):
    argv = binding.args("finalize")
    request = {"cmd": binding.literal_command(argv), "workdir": str(binding.RUNTIME)}
    result = {"exit_code": 0, "output": '{"bindings":23}\n'}
    packet = {
        "schema": "topolab.staged-binding.actual.v1",
        "author": "/root",
        "request": request,
        "argv": argv,
        "responses": [
            {
                "requested_ms": 1,
                "returned_ms": 7,
                "tool": "exec_command",
                "arguments": request,
                "result": result,
            }
        ],
    }
    monkeypatch.setattr(binding, "pair", lambda *a: json.dumps(packet).encode())
    assert binding.actual("finalize", "/root", lambda _: argv)[:3] == (1, 7, {"bindings": 23})
    result.update(exit_code=None, session_id=4)
    with pytest.raises(ValueError, match="terminal"):
        binding.actual("finalize", "/root", lambda _: argv)


def test_registration_cap_and_old_authorities_remain_distinct(binding):
    policy = binding.policy()
    assert policy["role_order"] == list(binding.ROLES)
    assert sum(policy["FULL"]) == 1200
    assert policy["new_original_registration"] == policy["new_foundation_helpers"] == 0
    assert policy["source"] not in {str(binding.ROOT), str(binding.B)}
    assert policy["actors"][0] != policy["actors"][1]


def test_registration_tool_return_and_poll_ownership():
    case = Path(__file__).with_name("test_staged_binding_caller.mjs")
    subprocess.run(["node", "--test", str(case)], check=True, capture_output=True)
