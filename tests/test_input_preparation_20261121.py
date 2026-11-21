"""Exercise both November 21 retention calls with isolated public evidence."""

import hashlib
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

ENTRY = Path(__file__).resolve().parents[1] / "scripts/input_preparation_20261121.py"


def test_readiness_requires_return_from_separate_retention_call(tmp_path, monkeypatch):
    namespace = runpy.run_path(str(ENTRY))
    prepare = namespace["prepare"]
    root, backup = tmp_path / "a.json", tmp_path / "b.json"
    actual, readiness = tmp_path / "actual.json", tmp_path / "ready.json"
    policy = {
        "public_roots": [str(tmp_path)],
        "new_input_budget": {"sha256": "b" * 64},
        "actors": {"executor": "/root"},
        "independent_author_start_ms": 0,
        "global_deadline_ms": 2**53 - 1,
        "preparation_closure_paths": [str(root), str(backup)],
        "preparation_retention_actual_path": str(actual),
        "readiness_path": str(readiness),
    }

    def need(test, reason):
        if not test:
            raise ValueError(reason)

    def canonical(obj):
        return (json.dumps(obj, sort_keys=True) + "\n").encode()

    def sha(raw):
        return hashlib.sha256(raw).hexdigest()

    def put(path, obj):
        with path.open("xb") as stream:
            stream.write(canonical(obj))

    def read_pin(pin):
        data = Path(pin["path"]).read_bytes()
        assert sha(data) == pin["sha256"]
        return json.loads(data)

    def check_actual(packet, argv, actor):
        assert (argv, actor) == (["/physical/python", "-I", str(ENTRY), "retain"], "/root")
        return packet["start"], packet["end"]

    modules = {
        "p17_m2_source_acquisition_independent": SimpleNamespace(
            native=SimpleNamespace(_software_bytes=Path.read_bytes)
        ),
        "p17_m2_source_binding_recovery": SimpleNamespace(exact_actual=check_actual),
    }
    producer = SimpleNamespace(canonical=canonical, sha=sha, parse=json.loads)
    subject = SimpleNamespace(
        authority=lambda: policy,
        IDENTITY="new",
        PROTOCOL="contract",
        producer=producer,
        control=SimpleNamespace(
            base=lambda: SimpleNamespace(put=put, runtime=lambda: {"python": "/physical/python"}),
            source_freeze=lambda identity: {"contract": "c", "source": "s"},
            load=modules.__getitem__,
        ),
        _read_pin=read_pin,
        need=need,
    )
    proofs = ({"sha256": "1" * 64}, {"sha256": "2" * 64}, 100)
    monkeypatch.setitem(prepare.__globals__, "public_proof", lambda *_: proofs)
    summary = prepare(subject, "retain")
    assert root.read_bytes() == backup.read_bytes() and not root.samefile(backup)
    assert not readiness.exists()
    with pytest.raises(FileNotFoundError):
        prepare(subject, "readiness")
    packet = {
        "responses": [{"result": {"output": canonical(summary).decode()}}],
        "start": 99,
        "end": 160,
    }
    put(actual, packet)
    with pytest.raises(ValueError, match="return differs"):
        prepare(subject, "readiness")
    assert not readiness.exists()
    packet["start"] = 120
    actual.write_bytes(canonical(packet))
    ready = read_pin(prepare(subject, "readiness"))
    assert ready["preparation_retention_actual"]["sha256"] == sha(actual.read_bytes())
    assert ready["published_source_sha256"] == {"source": "s"}
    assert ready["public_certificate_actual"] == proofs[1]
