"""Docker boundaries use new literal public observations, never a real payload."""

import importlib.util
import json
import threading
from pathlib import Path

import pytest


def driver():
    path = Path(__file__).parents[1] / "scripts/public_containment_driver.py"
    spec = importlib.util.spec_from_file_location("public_containment_driver_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_owned_state_accepts_canonical_capdrop_and_rejects_foreign_owner() -> None:
    subject = driver()
    case = {"name": "topolab-full60-20261116-a1-pid1", "owner": "b" * 64,
            "mode": "pid1-death"}
    cid = "a" * 64
    value = {
        "Id": cid, "Name": "/" + case["name"], "Image": subject.IMAGE,
        "Config": {"Image": subject.IMAGE, "Entrypoint": None,
                   "Cmd": subject.payload_argv(case["mode"]),
                   "Labels": {"topolab.scope": subject.IDENTITY, "topolab.owner": case["owner"]}},
        "Mounts": [],
        "HostConfig": {"Privileged": False, "PidMode": "", "CgroupnsMode": "private",
                       "CapAdd": None, "CapDrop": ["CAP_SYS_ADMIN"],
                       "SecurityOpt": ["no-new-privileges"], "Binds": None,
                       "Memory": 3221225472, "MemorySwap": 3221225472,
                       "NanoCpus": 1000000000, "PidsLimit": 256, "NetworkMode": "none",
                       "RestartPolicy": {"Name": "no"}, "AutoRemove": False},
        "State": {"Running": False, "Pid": 0, "ExitCode": 23},
    }
    assert subject.owned_state(case, cid, value) == value["State"]
    value["Config"]["Labels"]["topolab.owner"] = "c" * 64
    with pytest.raises(ValueError, match="ownership"):
        subject.owned_state(case, cid, value)


def test_ready_file_is_published_only_after_complete_write(tmp_path, monkeypatch):
    subject = driver()
    target = tmp_path / "ready.json"
    opened, release = threading.Event(), threading.Event()
    original_open = Path.open
    errors = []

    def paused_open(path, mode="r", *args, **kwargs):
        stream = original_open(path, mode, *args, **kwargs)
        if mode == "xb":
            opened.set()
            assert release.wait(2)
        return stream

    monkeypatch.setattr(Path, "open", paused_open)

    def writer():
        try:
            subject.new_json(target, {"status": "READY"})
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        assert opened.wait(2)
        assert not target.exists(), "reader could observe partial READY JSON"
    finally:
        release.set()
        thread.join(timeout=2)
    assert not thread.is_alive() and errors == []
    assert json.loads(target.read_bytes()) == {"status": "READY"}
    assert not (tmp_path / "ready.json.pending").exists()
