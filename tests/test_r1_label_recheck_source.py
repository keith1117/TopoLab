"""An unchanged checkout cannot certify a different buffer already executed."""

import hashlib
import runpy
from pathlib import Path

import pytest


@pytest.mark.parametrize("changed", [False, True])
def test_reader_requires_exact_compiled_source(tmp_path, monkeypatch, changed):
    worker = runpy.run_path(str(Path(__file__).parents[1] / "scripts/r1_label_recheck.py"))
    verify = worker["verify_reader_sources"]
    name = "scripts/p17_m2_registered_input.py"
    published = b"released reader"
    observed = b"other compiled reader" if changed else published
    loaded = {str(tmp_path / name): hashlib.sha256(observed).hexdigest()}
    monkeypatch.setitem(verify.__globals__, "READER_SCRIPTS", (name,))
    monkeypatch.setitem(verify.__globals__, "published_blob", lambda *_: published)
    if changed:
        with pytest.raises(ValueError, match="executed reader differs"):
            verify(tmp_path, "main", {}, loaded)
    else:
        assert verify(tmp_path, "main", {}, loaded) == {name: loaded[str(tmp_path / name)]}


def test_neutral_entry_executes_the_same_buffer_it_checked(tmp_path, monkeypatch):
    worker = runpy.run_path(str(Path(__file__).parents[1] / "scripts/r1_label_recheck.py"))
    load_entry = worker["published_module"]
    name = "entry.py"
    path = tmp_path / name
    original = b"version = 'published'"
    path.write_bytes(original)

    def frozen_blob(*_args):
        path.write_bytes(b"version = 'replacement'")
        return original

    monkeypatch.setitem(load_entry.__globals__, "published_blob", frozen_blob)
    entry, digest = load_entry(tmp_path, "main", name)
    assert entry["version"] == "published" and digest == hashlib.sha256(original).hexdigest()
    with pytest.raises(ValueError, match="checkout differs"):
        load_entry(tmp_path, "main", name)
