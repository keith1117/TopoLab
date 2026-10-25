"""S1 new source-attested capability stays separate from public certificates."""

import importlib.util
import sys
from pathlib import Path

import pytest

ENTRY = Path(__file__).parents[1] / "scripts/p17_m2_source_verified_input.py"


def load():
    spec = importlib.util.spec_from_file_location("source_verified_input_test", ENTRY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_serialized_or_old_public_pass_cannot_open_new_source_attested_reader(monkeypatch):
    module = load()

    def forbidden(*args, **kwargs):
        pytest.fail("unverified capability reached scientific IO")

    monkeypatch.setattr("os.open", forbidden)
    for packet in ({"status": "PASS", "formal_authority": True}, object()):
        with pytest.raises(ValueError, match="UNVERIFIED_SOURCE_CERTIFICATE"):
            module.VerifiedAcquisitionInput(packet, "scientific-producer")
