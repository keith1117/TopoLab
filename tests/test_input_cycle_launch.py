"""The production producer schedules two real handlers against disposable custody.

Only external readiness, case data, kernel locality on non-Darwin and the
fixed generation namespace are supplied by the fixture. Both exclusive
writes, target creation, the lease and setup proof use production code.
"""

import json
import runpy
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FROZEN_NOW = 1795403556212
ENTRY = "formal-activation-entry-a1.json"
NOTE = "coordinator-launch-note-a1.json"


def scratch_command(folder, command):
    # Run with -I in a separate process, including each repeat invocation.
    words = shlex.split(command)
    at = words.index("-I")
    script, mode, *options = words[at + 1 :]
    entry = Path(script).name
    evidence = folder / "evidence"
    target = folder / "custody" / "generation"
    nominal = options[options.index("--root") + 1]
    options[options.index("--root") + 1] = str(target)
    if mode == "dispatch-note":
        assert entry in ("cycle_input_filer.py", "cycle_r1_input_filer.py")
        route_path = REPO / "scripts" / entry.replace("_filer.py", "_route.py")
        route = runpy.run_path(str(route_path))
        wire = route["filer"]()
        assert nominal == wire.FORMAL
        wire.EVIDENCE = evidence
        wire.BACKUP = evidence.with_name("evidence-backup")
        wire.FORMAL = str(target)
        wire.ROOTS = (str(target),)
        route["sibling"]("cycle_input_filer").dispatch(wire, [mode, *options])
        return
    assert entry in ("cycle_input_control.py", "cycle_r1_input_control.py")
    assert mode == "activate-formal"
    control = runpy.run_path(str(REPO / "scripts" / entry))["subject"]
    profiles = control.load("p17_m2_input_continuation")
    ident = control.REGISTERED_IDENTITY
    config = profiles.config(ident)
    assert (nominal,) == config["generations"]
    config.update(generations=(str(target),), evidence_root=str(evidence))
    profiles.STAGED_EVIDENCE = str(evidence)
    control.REGISTERED_GENERATIONS = config["generations"]
    r = control.load("p17_m2_registered_input")
    r.GENERATIONS = config["generations"]
    r.authority = lambda *_: {}
    r.registration_reference = lambda *_: {"fixture_registration": True}
    r.activation_readiness = lambda *_: dict(
        readiness_reference={}, independent_preflight_reference={}
    )
    r.formal_plan = lambda *_a, **_kw: dict(
        execution_identity=ident,
        scope=control.FORMAL_SCOPE,
        root=str(target),
        content_root=str(target / "content"),
        backup_root=str(target.with_name("backup")),
        source_tree={},
        contract_sha256="a" * 64,
        formal_authority=True,
        actor_activation_UTC_seconds=FROZEN_NOW / 1000,
    )
    r.control.load("p17_m2_source_acquisition_independent").validate_binding = lambda *_: None
    control.time.time_ns = lambda: FROZEN_NOW * 10**6
    control.time.time = lambda: FROZEN_NOW / 1000
    if sys.platform != "darwin":
        control.local_filesystem = lambda _fd: {"available_bytes": 3 * 1024**3}
    argv = [str(REPO / "scripts" / entry), mode, *options]
    sys.argv = argv
    sys.orig_argv = [str(Path(sys.executable).resolve()), "-I", *argv]
    assert control.main() == 0


# The registered target is checked and mapped to the disposable directory at
# the subprocess boundary. Only the launch and activation requests are served.
DRIVER = r"""
import {executeActor} from './scripts/staged_input_actor.mjs';
import {spawnSync} from 'node:child_process';
const [config,python,driver,folder,now]=process.argv.slice(1).map(JSON.parse);
const responses=[];
await executeActor(config,async (tool,args)=>{
 const entry=args.cmd.split(" --packet-json ")[0];
 if(!/cycle_(?:r1_)?input_(?:filer\.py dispatch-note|control\.py activate-formal) /.test(entry)){
   process.stdout.write(JSON.stringify(responses));process.exit(0);
 }
 const r=spawnSync(python,['-I',driver,folder,args.cmd],{encoding:'utf8',timeout:25000});
 if(r.error)throw r.error;
 const output=r.stdout+r.stderr, mode=args.cmd.includes(' dispatch-note ')?'note':'activation';
 responses.push({mode,code:r.status,output});
 return {tool,arguments:args,requested_ms:now,returned_ms:now,result:{exit_code:r.status,output}};
},()=>now);
process.stdout.write(JSON.stringify(responses));
"""


@pytest.mark.parametrize("occupied", ["none", "primary", "backup"])
@pytest.mark.parametrize("ordinal", [1, 2])
def test_scheduled_activation_and_exclusive_duplicate(tmp_path, occupied, ordinal):
    folder = tmp_path.resolve()
    for directory in ("evidence", "evidence-backup", "custody"):
        (folder / directory).mkdir(mode=0o700)
    dirs = [folder / "evidence", folder / "evidence-backup"]
    target = folder / "custody/generation"
    if occupied != "none":
        (dirs[occupied == "backup"] / ENTRY).write_bytes(b"existing activation receipt")

    policy = json.loads((REPO / f"docs/planning/input_cycle_a{ordinal}_contract.json").read_bytes())
    pin = policy["registration"]["formal"]
    config = dict(
        author="producer",
        formal=True,
        execution_identity=policy["execution_identity"],
        root=policy["fixed_target"]["attempts"]["1"]["generation"],
        event_prefix="disposable-launch",
        registration_certificate_sha=pin["certificate_sha256"],
        registration_finalize_actual_sha=pin["finalize_actual_sha256"],
        formal_registration_certificate_sha=pin["certificate_sha256"],
        formal_registration_finalize_actual_sha=pin["finalize_actual_sha256"],
    )

    def schedule():
        args = [config, sys.executable, str(Path(__file__).resolve()), str(folder), FROZEN_NOW]
        proc = subprocess.run(
            ["node", "--input-type=module", "-e", DRIVER, *map(json.dumps, args)],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
            timeout=70,
        )
        rows = json.loads(proc.stdout)
        assert [r["mode"] for r in rows] == ["note", "activation"], rows
        assert rows[0]["code"] == 0, rows
        assert (dirs[0] / NOTE).read_bytes() == (dirs[1] / NOTE).read_bytes()
        assert not (dirs[0] / NOTE).samefile(dirs[1] / NOTE)
        return rows[-1]

    result = schedule()
    if occupied != "none":
        assert result["code"] != 0 and "FileExistsError" in result["output"], result
        assert (dirs[occupied == "backup"] / ENTRY).read_bytes() == b"existing activation receipt"
        assert not target.exists()
        return
    assert result["code"] == 0 and json.loads(result["output"])["formal_authority"], result
    assert json.loads((target / "setup-proof.json").read_bytes())["formal_readiness_verified"]
    claim = (dirs[0] / ENTRY).read_bytes()
    assert claim == (dirs[1] / ENTRY).read_bytes() and claim != (dirs[0] / NOTE).read_bytes()
    lease = (target / "custody-acquired.json").read_bytes()
    duplicate = schedule()
    assert duplicate["code"] != 0 and "FileExistsError" in duplicate["output"]
    assert claim == (dirs[0] / ENTRY).read_bytes() == (dirs[1] / ENTRY).read_bytes()
    assert (target / "custody-acquired.json").read_bytes() == lease


@pytest.mark.parametrize("name", [ENTRY, NOTE])
def test_generic_packet_filer_cannot_claim_launch_name(monkeypatch, tmp_path, name):
    module = runpy.run_path(str(REPO / "scripts/cycle_input_filer.py"))
    wire = runpy.run_path(str(REPO / "scripts/cycle_input_route.py"))["filer"]()
    path = tmp_path / name
    argv = ["persist", "--packet-json", "{}", "--destination=" + str(path)]
    monkeypatch.setattr(sys, "argv", ["cycle_input_filer.py", *argv])
    with pytest.raises(ValueError, match="reserved launch file"):
        module["dispatch"](wire, argv)
    assert not path.exists()


if __name__ == "__main__":
    scratch_command(Path(sys.argv[1]), sys.argv[2])
