"""Lossless metadata wire size; no Native, historical source or target IO."""

import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def subject(monkeypatch):
    path = ROOT / "scripts/p17_m2_source_binding_recovery.py"
    value = types.ModuleType("metadata_plan_size_subject")
    value.__file__ = str(path)
    sys.modules[value.__name__] = value
    exec(compile(path.read_bytes(), str(path), "exec"), value.__dict__)
    monkeypatch.setattr(value, "CONTINUATION_INPUT", value.FULL60_INPUT)
    monkeypatch.setattr(value, "IDENTITY", value.FULL60_RECOVERY)
    return value


def capture(module):
    value = {"timestamp_ns": 1794837706790123456, "text": "raw stays exact"}
    raw = module.canonical(value).decode()
    return {"preflight": value, "preflight_raw": raw,
            "preflight_reference": {"path": "/new/preflight.json",
                                    "sha256": module.sha(raw.encode())}}


def test_raw_only_formal_entry_preserves_original_bytes_and_large_integer(monkeypatch):
    module = subject(monkeypatch)
    original = capture(module)
    compact = module.compact_formal_entry(original)
    assert "preflight" not in compact
    assert original["preflight_raw"] == compact["preflight_raw"]
    assert "preflight" in original  # Do not mutate a retained input buffer.
    assert module.formal_preflight(compact) == original["preflight"]
    assert module.formal_preflight(original) == original["preflight"]
    compact["preflight_raw"] += " "
    with pytest.raises(ValueError, match="SHA"):
        module.formal_preflight(compact)


def test_compact_marker_is_new_only_and_unambiguous(monkeypatch):
    module = subject(monkeypatch)
    compact = module.compact_formal_entry(capture(module))
    compact["preflight"] = {}
    with pytest.raises(ValueError, match="representation"):
        module.formal_preflight(compact)
    del compact["preflight"]
    monkeypatch.setattr(module, "CONTINUATION_INPUT", None)
    with pytest.raises(ValueError, match="representation"):
        module.formal_preflight(compact)


def test_realistic_nested_capture_fits_the_unchanged_reader_cap(monkeypatch):
    module = subject(monkeypatch)
    value = {"payload": "x" * (9_439_194 - len(module.canonical({"payload": ""}))) }
    raw = module.canonical(value).decode()
    assert len(raw.encode()) == 9_439_194
    admitted = {"preflight": value, "preflight_raw": raw,
                "preflight_reference": {"path": "/new/preflight.json",
                                        "sha256": module.sha(raw.encode())}}
    other = "x" * 3_871_794
    old = {"formal": admitted, "local": other}
    assert len(module.canonical(old)) > 16 * 1024**2
    compact = module.compact_formal_entry(admitted)
    assert len(module.canonical({"formal": compact, "local": other})) < 16 * 1024**2
    assert compact['preflight_raw'] == raw
    assert module.formal_preflight(compact) == value


def test_oversize_plan_fails_before_parent_or_target_io(monkeypatch, tmp_path):
    module = subject(monkeypatch)
    core = module.load('p17_m2_source_binding')
    monkeypatch.setattr(core, "source_parent", lambda *_: pytest.fail("parent must not be opened"))
    root = tmp_path / "uncreated"
    plan = {"text": "é" * 20}
    with pytest.raises(ValueError, match="plan byte cap"):
        module.publish_plan(root, plan, maximum=32)
    assert not root.exists()


def test_exact_byte_boundary_can_publish(monkeypatch, tmp_path):
    module = subject(monkeypatch)
    plan = {"text": "bounded"}
    expected = module.canonical(plan)
    import os

    core = module.load('p17_m2_source_binding')
    monkeypatch.setattr(core, "source_parent",
                        lambda parent, _: os.open(parent, os.O_RDONLY | os.O_DIRECTORY))
    monkeypatch.setattr(module, "write_new", lambda path, value: (
        path.write_bytes(module.canonical(value)), module.sha(module.canonical(value)))[1])
    root = tmp_path / "new"
    assert module.publish_plan(root, plan, maximum=len(expected)) == module.sha(expected)
    assert (root / "plan.json").read_bytes() == expected
    assert json.loads(expected) == plan
