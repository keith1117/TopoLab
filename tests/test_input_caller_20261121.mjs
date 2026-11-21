// Injected original-tool responses only. No process/source/target/Native graph is executed.
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {createActualBoundary,qualification20261121,captureDispatch,
 permissionInputPrefixes,permissionThenPrepare} from '../scripts/full60_input_actual_boundary.mjs';
import {executeOwned} from '../scripts/full60_input_cohort.mjs';

const START=1795242000000;
const E='/Users/keith1117/Documents/TopoLab-data/metadata-input-acceptance-20261121';
const REPO='/private/tmp/topolab-meta-input-20261121';
const ROLES=['independent-public-check','exporter-r0','independent-r0',
 'exporter-r1','independent-r1','shared-closeout'];
const GATE={public:{certificate_sha256:'a'.repeat(64),finalize_actual_sha256:'b'.repeat(64)},
 formal:{certificate_sha256:'c'.repeat(64),finalize_actual_sha256:'d'.repeat(64)}};
function config(author,formal=false){return qualification20261121({author,formal,
 root:formal?'/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-20261121-a1':
 '/private/tmp/topolab-public-source-acquisition-20261121-a1',
 event_prefix:'declared-mock-'+author,metadata_gate:GATE});}
function harness(formal,{failSuperviseFiling=false,liveSupervise=false,superviseExit=0}={}){
 let plan,readyPlan,serial=0;const planReady=new Promise(resolve=>{readyPlan=resolve;});
 let stopped=false;const accepted=[],calls=[],waiters=[];
 const publish=()=>{for(const wake of waiters.splice(0))wake();};
 async function waitUntil(predicate){while(!predicate())await new Promise(resolve=>waiters.push(resolve));}
 const dispatcher=author=>async(tool,args)=>{
  const requested_ms=Date.now();calls.push({author,tool,args});let output='{}',exit_code=0;
  if(tool==='write_stdin')throw Error('no poll expected in declared immediate fixture');
  const cmd=args.cmd.split(' --packet-json ')[0];
  if(cmd.includes('input_control_20261121.py prepare-rehearsal ')||
     cmd.includes('input_control_20261121.py activate-formal ')){
   const q=config(author,formal);
   plan={root:q.root,plan_sha256:'f'.repeat(64),execution_identity:q.execution_identity,
    scope:formal?'SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY':'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY',
    formal_authority:formal,actor_window_seconds:4500,coordination_limit_ms:240000,
    role_order:ROLES,actor_start_ms:START,whole_start_ms:START,whole_end_ms:START+4500000,
    applicable_deadline_ms:START+4500000};readyPlan();
   output=JSON.stringify({formal_authority:formal,plan_sha256:plan.plan_sha256});
  }else if(cmd.includes('await_input_receipt_20261121.py')){
   await planReady;const role=cmd.match(/--role ([a-z0-9-]+)/)[1];
   if(role!=='plan')await waitUntil(()=>stopped||accepted.some(p=>p.role===role));
   output=JSON.stringify({...(stopped?{status:'STOP'}:{}),source_or_payload_reads:0,plan,
    proofs:role==='plan'?[]:accepted.slice(0,ROLES.indexOf(role)+1)});
  }else if(cmd.includes('file_input_event_20261121.py persist')){
   if(args.cmd.includes('topolab.m2-acquisition-caller-failure.v1')){stopped=true;publish();}
   output=JSON.stringify({path:E+'/declared-mock-'+serial+++'.json',sha256:'a'.repeat(64)});
  }else if(cmd.includes('file_input_event_20261121.py file ')){
   if(failSuperviseFiling&&cmd.includes('--event-mode supervise')){
    output='DECLARED_PENDING_MISSING';exit_code=1;
   }
  }else if(cmd.includes('input_control_20261121.py supervise ')){
   exit_code=superviseExit;
   if(liveSupervise)return {tool,arguments:args,requested_ms,returned_ms:Date.now(),
     result:{session_id:123,output:'DECLARED_LIVE_NO_EXIT'}};
  }else if(cmd.includes('input_control_20261121.py bind ')){
   const role=cmd.match(/--role ([a-z0-9-]+)/)[1];
   if(ROLES.includes(role)){accepted.push({role,accepted:true,complete:true,
    actual_exit_codes:[0,0],T0_ms:START,T1_ms:START});publish();}
   output=JSON.stringify({full_role_evidence_accepted:true,metadata_evidence_accepted:true});
  }else if(cmd.includes('input_control_20261121.py certify-')){
   output=JSON.stringify({scope:'DECLARED_MOCK_ONLY',source_input_accepted:false});
  }
  return {tool,arguments:args,requested_ms,returned_ms:Date.now(),result:{exit_code,output}};
 };
 return {dispatcher,calls,accepted};
}
for(const formal of [false,true])test('two owned mock schedules complete with exact effects '+formal,async()=>{
 const old=Date.now;Date.now=()=>START;
 try{
  const h=harness(formal);
  const qRoot=config('producer',formal),qI=config('independent',formal);
  const root=createActualBoundary(h.dispatcher('producer'),qRoot);
  const independent=createActualBoundary(h.dispatcher('independent'),qI);
  const results=Promise.all([executeOwned(qRoot,root),executeOwned(qI,independent)]);
  let timer;const limit=new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('mock schedule stalled')),1000);});
  let a,b;try{[a,b]=await Promise.race([results,limit]);}finally{clearTimeout(timer);}
  assert.equal(a.status,'OWNED_COHORT_COMPLETE_NEEDS_ACTUAL_RETURN');
  assert.equal(b.status,'OWNED_COHORT_COMPLETE_NEEDS_ACTUAL_RETURN');
  assert.deepEqual(h.accepted.map(x=>x.role),ROLES);
  for(const row of h.calls){
   const controlled=row.args.cmd.split(' --packet-json ')[0].includes('input_control_20261121.py ');
   const native=controlled&&/\.py (supervise|record) /.test(row.args.cmd);
   const library=formal&&(controlled||row.args.cmd.split(' --packet-json ')[0].includes('file_input_event_20261121.py file '));
   assert.equal(row.args.sandbox_permissions,(native||library)?'require_escalated':undefined);
   assert.equal(row.args.prefix_rule,undefined);
   if(native||library)assert.match(row.args.justification,/允许在/);
  }
  const rootNative=h.calls.filter(x=>x.author==='producer'&&x.args.cmd.split(' --packet-json ')[0].includes('.py supervise '));
  assert.deepEqual(rootNative.map(x=>x.args.cmd.match(/--role ([a-z0-9-]+)/)[1]),
   ['exporter-r0','exporter-r1','shared-closeout','final-filing','lease-release']);
 }finally{Date.now=old;}
});

test('failed SUP pending/event filing stops before REC and preserves STOP',async()=>{
 const old=Date.now;Date.now=()=>START;
 try{
  const h=harness(false,{failSuperviseFiling:true}),q=config('independent');
  const boundary=createActualBoundary(h.dispatcher('independent'),q);
  const result=await executeOwned(q,boundary);
  assert.equal(result.status,'STOP_RETAINED_NO_RETRY');
  assert.match(result.reason,/pending\/event filing failed/);
  assert.equal(h.calls.filter(x=>x.args.cmd.includes('input_control_20261121.py record ')).length,0);
  assert.ok(boundary.raw.some(x=>x.result.exit_code===1));
  assert.ok(h.calls.some(x=>x.args.cmd.includes('-caller-STOP.json')));
 }finally{Date.now=old;}
});

test('original malformed row is retained, never rewritten as exit0',async()=>{
 let tick=10;const rows=[],args={cmd:'declared metadata',sandbox_permissions:'require_escalated'};
 const original={tool:'wrong',arguments:args,requested_ms:11,returned_ms:12,
  result:{output:'original',session_id:7}};
 await assert.rejects(captureDispatch(async()=>original,'exec_command',args,rows,()=>tick++),
  /original ordered tool row/);
 assert.equal(rows[0],original);assert.equal(rows[0].result.exit_code,undefined);
});

test('actual new input prefix help preserves permission fields and30s yield',async()=>{
 let clock=START;const rows=[],calls=[];
 const q={...config('producer'),author:'/root'};
 const result=await permissionInputPrefixes(async(tool,args)=>{
  calls.push(args);return {tool,arguments:args,requested_ms:clock++,returned_ms:clock++,
   result:{exit_code:0,output:'usage: declared mock only'}};
 },q,rows,()=>clock++);
 assert.equal(result.source_or_payload_reads,0);assert.equal(calls.length,2);
 assert.ok(calls.every(x=>x.sandbox_permissions==='require_escalated'&&x.yield_time_ms===30000));
 assert.ok(calls[0].cmd.includes('input_control_20261121.py --help'));
});


test('terminal SUP1 with matched pending receives one closing REC then STOP',async()=>{
 const old=Date.now;Date.now=()=>START;
 try{
  const h=harness(false,{superviseExit:1}),q=config('independent');
  const boundary=createActualBoundary(h.dispatcher('independent'),q);
  const result=await executeOwned(q,boundary);
  assert.equal(result.status,'STOP_RETAINED_NO_RETRY');
  assert.match(result.reason,/original SUP\/REC exit 1\/0 retained/);
  const commands=h.calls.map(x=>x.args.cmd.split(' --packet-json ')[0]);
  assert.equal(commands.filter(x=>x.includes('input_control_20261121.py record ')).length,1);
  assert.equal(commands.filter(x=>x.includes('input_control_20261121.py bind ')).length,0);
  assert.equal(boundary.packets['independent-public-check-supervise'].packet.responses[0].result.exit_code,1);
 }finally{Date.now=old;}
});

test('caller STOP reaches the other author without opening a successor',async()=>{
 const old=Date.now;Date.now=()=>START;
 try{
  const h=harness(false,{failSuperviseFiling:true});
  const qr=config('producer'),qi=config('independent');
  const result=await Promise.all([executeOwned(qr,createActualBoundary(h.dispatcher('producer'),qr)),
   executeOwned(qi,createActualBoundary(h.dispatcher('independent'),qi))]);
  assert.ok(result.every(x=>x.status==='STOP_RETAINED_NO_RETRY'));
  assert.match(result[0].reason,/predecessor STOP/);
  assert.equal(h.calls.filter(x=>x.args.cmd.split(' --packet-json ')[0].includes('input_control_20261121.py supervise ')).length,1);
 }finally{Date.now=old;}
});

test('new metadata help asks one scoped Chinese permission without reusable prefix',async()=>{
 let clock=START;const calls=[],raw=[];
 const q={execution_identity:'topolab.v2.p17-binding-certificate-recovery.20261121.v1',
  repo:REPO,evidence_root:E,author:'/root/full60_independent',event_prefix:'mock-meta',
  standards_sha:'a'.repeat(64),spec_sha:'b'.repeat(64),public_capability_sha:'c'.repeat(64)};
 await permissionThenPrepare(async(tool,args)=>{
  calls.push(args);const output=args.cmd.includes(' persist ')?JSON.stringify({
   path:E+'/independent/FULL60-public-metadata-a1-permission-preflight-raw-actual-call.json',sha256:'a'.repeat(64)}):'usage: mock';
  return {tool,arguments:args,requested_ms:clock++,returned_ms:clock++,result:{exit_code:0,output}};
 },q,raw,()=>clock++);
 assert.equal(calls[0].prefix_rule,undefined);assert.match(calls[0].justification,/允许仅执行本轮/);
 assert.equal(calls[1].sandbox_permissions,undefined);
});
