"""New input budget projection; no source, target, lease or native role IO."""

import importlib.util
from pathlib import Path

import pytest


def window():
    path = Path(__file__).resolve().parents[1] / "scripts/full60_input_window.py"
    spec = importlib.util.spec_from_file_location("full60_input_window_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_whole_window_begins_at_original_request_and_never_adds_result_1800():
    subject = window()
    start = 1794834000000  # 13:00 UTC, not now or a restarted stage.
    value = subject.declare(start, start + 1200)
    assert value["whole_start_ms"] == start
    assert value["whole_end_ms"] == start + 4500000
    assert subject.result_end(value, start + 4400000) == start + 4500000
    assert subject.result_end(value, start + 1000) == start + 1801000
    with pytest.raises(ValueError, match="whole"):
        subject.check(value, start + 4500001)


def test_entry_requires_remaining_whole_and_7200_result_suffix():
    subject = window()
    latest = 1794852900000 - (4500 + 7200) * 1000
    assert subject.declare(latest, latest)["whole_end_ms"] == latest + 4500000
    with pytest.raises(ValueError, match="suffix"):
        subject.declare(latest + 1, latest + 1)
    with pytest.raises(ValueError, match="clock"):
        subject.declare(latest, latest - 1)


def test_forged_whole_end_or_later_stage_start_is_rejected():
    subject = window()
    start = 1794834000000
    value = subject.declare(start, start)
    value["whole_end_ms"] += 1800000
    with pytest.raises(ValueError, match="whole"):
        subject.check(value, start + 1000)


def test_locked_site_precedes_global_site_and_checks_origins(tmp_path):
    import json
    import subprocess
    import sys

    root = tmp_path / "declared-software-fixture"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / "scripts/full60_input_loader.py"
    (scripts / source.name).write_bytes(source.read_bytes())
    packages = root / ".venv/lib/python3.12/site-packages"
    packages.mkdir(parents=True)
    global_site = root / "declared-global/site-packages"
    global_site.mkdir(parents=True)
    (global_site / "choice.py").write_text("MARKER='GLOBAL'\n")
    (packages / "choice.py").write_text("MARKER='LOCKED'\n")
    lock = []
    for name in ("numpy", "scipy", "pydantic"):
        (packages / (name + ".py")).write_text("__version__='1.0'\n")
        lock.append('[[package]]\nname="' + name + '"\nversion="1.0"\n')
    (root / "uv.lock").write_text("\n".join(lock))
    code = f"""import importlib.util,json,sys
sys.path.insert(0,{str(global_site)!r})
spec=importlib.util.spec_from_file_location('declared_loader',{str(scripts / source.name)!r})
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.install(require_locked_environment=True)
import choice,numpy,scipy,pydantic
print(json.dumps(dict(marker=choice.MARKER,origins=[p.__file__ for p in (numpy,scipy,pydantic)])))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["marker"] == "LOCKED"
    assert all(Path(path).is_relative_to(packages) for path in value["origins"])


def test_new_native_wrapper_does_not_mutate_default_resource_module(tmp_path):
    import hashlib
    import json
    import sys

    repo = Path(__file__).resolve().parents[1]
    path = repo / "scripts/p17_m2_input_continuation.py"
    spec = importlib.util.spec_from_file_location("p17_m2_input_continuation", path)
    profiles = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = profiles
    spec.loader.exec_module(profiles)
    control = profiles.profile("control", profiles.FULL60_INPUT)
    control.base().load("p17_m2_homotopy")
    default = control.load("p17_m2_resource_control")
    original = default.invoke
    data = {
        "source_tree": {
            "scripts/p17_m2_resource_control.py": hashlib.sha256(
                (repo / "scripts/p17_m2_resource_control.py").read_bytes()
            ).hexdigest()
        }
    }
    raw = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (tmp_path / "plan.json").write_bytes(raw)
    transport = control.AcquisitionTransport(tmp_path, hashlib.sha256(raw).hexdigest())
    native = transport.native_module()
    assert native is not default and native.__name__.startswith("p17_m2_resource_control_full60_")
    assert default.invoke is original


def test_caller_does_not_reset_full_deadline_for_record():
    import json
    import subprocess

    repo = Path(__file__).resolve().parents[1]
    path = repo / "scripts/full60_input_actual_boundary.mjs"
    script = r"""
import {createActualBoundary} from ENTRY;
let clock=1794834000000,native=0;
Date.now=()=>clock;
const root='/private/tmp/topolab-public-full60-source-acquisition-20261116-a1';
const plan={root,plan_sha256:'a'.repeat(64),whole_end_ms:clock+4500000};
const dispatch=async(tool,args)=>{
 const requested_ms=clock;let output='{}';
 if(args.cmd.includes('file_full60_input_event.py persist')){
  clock+=2000;output=JSON.stringify({path:'/declared',sha256:'b'.repeat(64)});
 }
 else if(args.cmd.includes('await_full60_input_receipt.py')){
  output=JSON.stringify({source_or_payload_reads:0,plan,proofs:[]});
 }
 else if(args.cmd.includes('input_control_full60_20261116.py supervise')){native++;clock+=289000;}
 else if(args.cmd.includes('input_control_full60_20261116.py record')){native++;}
 return {tool,arguments:args,requested_ms,returned_ms:clock,result:{exit_code:0,output}};
};
const boundary=createActualBoundary(dispatch,{author:'independent',formal:true,root,
 repo:'/private/tmp/topolab-input-admission-20261116',
 evidence_root:'/Users/keith1117/Documents/TopoLab-data/container-full60-input-admission-20261116',event_prefix:'declared-pure-fixture'});
await boundary.prepare();let rejected=false;
try{await boundary.run('exporter-r0');}catch(error){rejected=true;}
console.log(JSON.stringify({native,rejected}));
""".replace("ENTRY", json.dumps(path.as_uri()))
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"native": 1, "rejected": True}
