"""The caller accepts a paired receipt only on its original clock."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "scenario", ["pass", "late", "partial", "switched_session", "extra_output"]
)
def test_owned_data_return_before_filing(scenario):
    code = """
import assert from 'node:assert/strict';
import {retainCloseoutRecord} from './scripts/staged_input_actor.mjs';
const scenario = process.argv[1];
const digest = 'a'.repeat(64);
let clock = 900, sends = 0, filed = 0, stage = 0;
const saved = {status:'PAIRED_PERSISTED',path:'/public/receipt',bytes:42,sha256:digest,
 copies:['/public/receipt','/backup/receipt'].map(path=>({path,bytes:42,sha256:digest})),
 failures:[],file_intent_sha256:digest,program_sha256:digest};
if(scenario==='partial')saved.copies.pop();
const invoke = async(tool,args) => {
 const start=clock++;
 let result;
 if(stage++===0){
  assert.equal(tool,'exec_command');
  assert.equal(args.tty,true);
  assert.ok(!args.cmd.includes('ACTUAL_PACKET'));
  result={session_id:42,output:'CLOSEOUT_RECEIPT_READY_V1\\n'};
 } else if(stage===2){
  assert.equal(tool,'write_stdin');assert.equal(args.session_id,42);
  assert.deepEqual(JSON.parse(args.chars),{event_id:'ACTUAL_PACKET'});
  sends++;result={session_id:scenario==='switched_session'?43:42,output:''};
 } else {
  assert.equal(args.chars,'');
  if(scenario==='late') clock=7001;
  result={exit_code:0,output:JSON.stringify(saved)+'\\n'+(scenario==='extra_output'?'extra':'')};
 }
 return {tool,arguments:args,requested_ms:start,returned_ms:clock,result};
};
try{
 await retainCloseoutRecord({argv:['/python','-I','/filer','persist-closeout-record'],
   workdir:'/public',packet:{event_id:'ACTUAL_PACKET'},deadline:7000,invoke,now:()=>clock});
 filed++;
} catch (error) { if(scenario==='pass') throw error; }
assert.equal(sends,1);assert.equal(filed,scenario==='pass'?1:0);
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", code, scenario], cwd=REPO, check=True, timeout=15
    )


@pytest.mark.skipif(os.name != "posix", reason="closeout uses a POSIX data terminal")
def test_real_terminal_keeps_same_scale_packet_out_of_argv_and_verifies_both_writes(tmp_path):
    import pty
    import select

    program = """
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import closeout_receipt
import staged_input_filer as wire
wire.EVIDENCE, wire.BACKUP = Path(sys.argv[2]), Path(sys.argv[3])
target = wire.EVIDENCE / 'receipt.json'
def persist(packet, timing):
    with closeout_receipt.track_writes(wire, target, wire.BACKUP / target.name, timing):
        return wire.publish_pair(target, wire.canonical(packet))
closeout_receipt.serve(persist, int(sys.argv[4]))
"""
    primary, backup = tmp_path / "primary", tmp_path / "backup"
    for directory in (primary, backup):
        directory.mkdir(mode=0o700)
    packet = {"event_id": "public-REC", "output": "z" * 4600}
    raw = (json.dumps(packet, separators=(",", ":")) + "\n").encode()
    argv = [
        sys.executable,
        "-I",
        "-c",
        program,
        str(REPO / "scripts"),
        str(primary),
        str(backup),
        str(time.time_ns() // 1_000_000 + 20_000),
    ]
    master, slave = pty.openpty()
    try:
        with subprocess.Popen(argv, stdin=slave, stdout=subprocess.PIPE) as child:
            assert child.stdout is not None
            assert select.select([child.stdout], [], [], 10)[0]
            assert child.stdout.readline() == b"CLOSEOUT_RECEIPT_READY_V1\n"
            with os.fdopen(os.dup(master), "wb", buffering=0) as sender:
                sender.write(raw)
            out, _ = child.communicate(timeout=15)
            assert child.returncode == 0
    finally:
        os.close(master)
        os.close(slave)
    result = json.loads(out)
    left, right = (primary / "receipt.json"), (backup / "receipt.json")
    assert not left.samefile(right) and left.read_bytes() == right.read_bytes() == raw
    assert result["sha256"] == hashlib.sha256(raw).hexdigest()
    times = result["timing"]
    keys = [
        "worker_entered",
        "packet_received",
        "primary_write_verified",
        "backup_write_verified",
        "before_result_write",
    ]
    for clock in ("monotonic_us", "utc_us"):
        stamps = [times[key][clock] for key in keys]
        assert stamps == sorted(stamps)



@pytest.mark.parametrize("profile", ["readiness", "receipt"])
def test_paired_readiness_profile_keeps_shared_rec_transport_and_original_clock(profile):
    contract = json.loads((REPO / f"docs/planning/{profile}_formal_contract.json").read_bytes())
    source = """
import assert from 'node:assert/strict';
import {initialWait, qualify, useCloseoutReceiver} from './scripts/staged_input_actor.mjs';
const policy=JSON.parse(process.argv[1]), id=policy.execution_identity;
const target=policy.fixed_target.attempts['1'].generation;
const pin=policy.registration.formal;
const config=qualify({formal:true,author:'independent',
  event_prefix:process.argv[2]+'-formal-independent',
  root:target,execution_identity:id,registration_certificate_sha:pin.certificate_sha256,
  formal_registration_certificate_sha:pin.certificate_sha256,
  registration_finalize_actual_sha:pin.finalize_actual_sha256,
  formal_registration_finalize_actual_sha:pin.finalize_actual_sha256});
assert.equal(config.owner_budget_sha256,policy.new_input_budget.sha256);
const root = policy.readiness_path.slice(0,policy.readiness_path.lastIndexOf('/'));
assert.equal(config.evidence_root,root);
for(const role of policy.role_order){
 for(const mode of ['supervise','record','bind']){
  assert.equal(useCloseoutReceiver(id,role,mode,true),role==='shared-closeout' && mode==='record');
  assert.equal(useCloseoutReceiver(id,role,mode,false),false);
 }
}
assert.equal(initialWait(id,'bind',419),419);
assert.equal(initialWait(id,'file',50000),30000);
assert.throws(()=>qualify({...config,root:target+'-unregistered'}));
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", source, json.dumps(contract), profile],
        cwd=REPO, check=True, timeout=15,
    )
