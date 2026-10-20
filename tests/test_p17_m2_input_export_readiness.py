"""Public synthetic controls for prospective, once-only R/v3 activation."""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "independent_readiness", REPO / "scripts/p17_m2_input_export_independent.py"
)
assert CHECKER_SPEC and CHECKER_SPEC.loader
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
def test_refused_window_is_locked_before_any_tool_or_attempt() -> None:
    # No clock reversal or source/root exists. A refusal cannot gain more time by
    # supplying a later activation, a new plan SHA or a different actor deadline.
    command = r"""
const fs=require('fs'), vm=require('vm'), state=new Map();
const activation=1792479600.123, now=(activation+841)*1000;
let calls=0;
const sandbox={module:{exports:{}},load:key=>state.get(key),store:(key,v)=>state.set(key,v),
  text:()=>{},Date:class extends Date{static now(){return now;}},
  tools:{exec_command:async()=>{calls++;throw new Error('unexpected native invocation');}}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
const roles=['independent-public-check','exporter-r0','independent-r0',
  'exporter-r1','independent-r1','shared-closeout'];
const deadline=new Date((activation+2700)*1000).toISOString();
const context={execution_identity:'topolab.v2.p17-m2-input-export-preparation.v3',
  plan_sha256:'a'.repeat(64),actor_activation_UTC_seconds:activation,actor_window_seconds:2700,
  actor_deadlines_UTC:{exporter:deadline,independent:deadline},
  FULL_caps_seconds:Object.fromEntries(roles.map((r,i)=>[r,[120,120,120,780,660,60][i]])),
  external_argv:Object.fromEntries(roles.map(r=>[r,[['public-supervise'],['public-finalize']]]))};
async function refuses(ctx){
  try{await sandbox.module.exports.dispatchRoleV3(ctx,roles[0]);return false;}
  catch(error){return true;}
}
(async()=>{
  const first=await refuses(context);
  const moved=structuredClone(context);
  moved.actor_activation_UTC_seconds+=100;
  const later=new Date((moved.actor_activation_UTC_seconds+2700)*1000).toISOString();
  moved.actor_deadlines_UTC={exporter:later,independent:later};
  const second=await refuses(moved);
  const third=await refuses({...context,plan_sha256:'b'.repeat(64)});
  console.log(JSON.stringify({first,second,third,calls,locked:state.has('r3-activation'),
    attempted:state.has('r3-attempted-'+roles[0])}));
})();
"""
    observed = subprocess.run(
        ["node", "-e", command, str(REPO / "scripts/p17_m2_input_export_dispatch.js")],
        text=True, capture_output=True, check=True,
    )
    assert json.loads(observed.stdout) == {
        "first": True, "second": True, "third": True, "calls": 0,
        "locked": True, "attempted": False,
    }


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
def test_python_and_JS_agree_on_realistic_millisecond_activation() -> None:
    context = {
        "actor_activation_UTC_seconds": 1792479600.123,
        "actor_window_seconds": 2700,
        "actor_deadlines_UTC": {
            "exporter": "2026-10-20T07:45:00.123Z",
            "independent": "2026-10-20T07:45:00.123Z",
        },
    }
    activation, deadline = checker.actor_window(context)
    command = (
        "const fs=require('fs');const {validateActorWindow}=require(process.argv[1]);"
        "console.log(JSON.stringify(validateActorWindow(JSON.parse(fs.readFileSync(0,'utf8')))));"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(REPO / "scripts/p17_m2_input_export_dispatch.js")],
        input=json.dumps(context), text=True, capture_output=True, check=True,
    )
    assert json.loads(observed.stdout) == {"activation": activation, "deadline": deadline}
