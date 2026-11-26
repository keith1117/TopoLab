"""Publish readiness to real, fresh metadata directories with frozen fixture inputs."""

import json
import os
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def preparation(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    primary, backup = root / "primary", root / "backup"
    primary.mkdir(mode=0o700)
    backup.mkdir(mode=0o700)
    paths = [str(area / "readiness.json") for area in (primary, backup)]
    actual = primary / "retention-actual.json"
    raw_base = runpy.run_path(str(SCRIPTS / "p17_m2_content_verified_control.py"))
    base = SimpleNamespace(**{k: raw_base[k] for k in ("put", "physical", "nofollow_directory")})
    base.runtime = lambda: {"python": "fixture-python"}
    producer = SimpleNamespace(canonical=raw_base["canonical"], sha=raw_base["sha"],
                               parse=json.loads)
    policy = dict(independent_author_start_ms=0, global_deadline_ms=2**53 - 1,
                  actors={"executor": "fixture-owner"}, new_input_budget={"graph": 1},
                  preparation_closure_paths=[str(d / "closure.json") for d in (primary, backup)],
                  preparation_retention_actual_path=str(actual), readiness_path=paths[0],
                  readiness_paths=paths,
                  fixed_target={"attempts": {"1": {"generation": str(root / "target")}}})
    contract = json.dumps(policy, indent=2).encode()
    tree = {"fixture-contract.json": producer.sha(contract), "source": "a" * 64}
    modules = {
        "p17_m2_input_continuation":
            SimpleNamespace(FORMAL_ONLY_IDENTITIES=set(), PROOF_MODULES={}),
        "p17_m2_source_acquisition_independent":
            SimpleNamespace(native=SimpleNamespace(_software_bytes=Path.read_bytes)),
        "p17_m2_source_binding_recovery":
            SimpleNamespace(exact_actual=lambda *unused: (100, 101)),
    }
    subject = SimpleNamespace(
        public_stop_veto=lambda: None, authority=lambda: policy, authority_raw=lambda: contract,
        need=raw_base["need"], producer=producer, IDENTITY="fixture",
        PROTOCOL="fixture-contract.json",
        control=SimpleNamespace(base=lambda: base, load=modules.__getitem__,
                                source_freeze=lambda identity: tree),
        _read_pin=lambda pin: json.loads(Path(pin["path"]).read_bytes()),
    )
    prepare = runpy.run_path(str(SCRIPTS / "staged_input_preparation.py"))["prepare"]
    monkeypatch.setitem(prepare.__globals__, "public_proof",
                        lambda *unused: ({"sha256": "1" * 64}, {"sha256": "2" * 64}, 99))
    retained = prepare(subject, "retain")
    base.put(actual, {"responses": [{"result": {"output": producer.canonical(retained).decode()}}]})
    return SimpleNamespace(run=lambda: prepare(subject, "readiness"), base=base, policy=policy,
                           contract=contract, producer=producer, tree=tree,
                           first=Path(paths[0]), second=Path(paths[1]))


def test_complete_pair_binds_writes_readbacks_and_verbatim_contract(preparation):
    p = preparation
    result = p.run()
    raw = p.first.read_bytes()
    assert raw == p.second.read_bytes() and not p.first.samefile(p.second)
    ready = json.loads(raw)
    assert ready["contract_sha256"] == p.producer.sha(p.contract)
    assert ready["contract_sha256"] != p.producer.sha(p.producer.canonical(p.policy))
    assert ready["source_tree"] == p.tree
    assert ready["readiness_paths"] == p.policy["readiness_paths"]
    assert ready["target"] == p.policy["fixed_target"]["attempts"]["1"]["generation"]
    assert result["path"] == str(p.first) and result["sha256"] == p.producer.sha(raw)
    for path, observation in zip((p.first, p.second), result["readiness_copies"], strict=True):
        st = path.lstat()
        assert observation == {
            "path": str(path), "sha256": p.producer.sha(path.read_bytes()), **p.base.physical(st),
            "st_mode": st.st_mode, "st_uid": os.geteuid(), "st_nlink": 1,
        }
        assert st.st_mode & 0o7777 == 0o600


def test_failed_second_write_preserves_primary_and_occupied_backup(preparation):
    p = preparation
    p.second.write_bytes(b"prior evidence")
    with pytest.raises(FileExistsError):
        p.run()
    assert json.loads(p.first.read_bytes())["contract_sha256"] == p.producer.sha(p.contract)
    assert p.second.read_bytes() == b"prior evidence"
    with pytest.raises(FileExistsError):
        p.run()


@pytest.mark.parametrize("change", ["replace", "link", "mode", "byte"])
def test_refuse_changed_primary_after_second_write(preparation, monkeypatch, change):
    p = preparation
    put = p.base.put

    def changed_after_write(path, value):
        identity = put(path, value)
        if path == p.second:
            if change == "replace":
                p.first.rename(p.first.with_suffix(".old"))
                put(p.first, value)
            elif change == "link":
                os.link(p.first, p.first.with_suffix(".link"))
            elif change == "mode":
                p.first.chmod(0o644)
            else:
                before = p.first.stat()
                with p.first.open("r+b") as stream:
                    stream.write(b"!")
                os.utime(p.first, ns=(before.st_atime_ns, before.st_mtime_ns))
        return identity

    monkeypatch.setattr(p.base, "put", changed_after_write)
    with pytest.raises(ValueError, match="readiness"):
        p.run()
