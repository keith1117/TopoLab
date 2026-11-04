import assert from 'node:assert/strict';
import {test} from 'node:test';
import {coordinateMilliseconds, launchGate, executeOwned} from '../scripts/m2_acquisition_cohort.mjs';
const roles=['independent-public-check','exporter-r0','independent-r0','exporter-r1','independent-r1','shared-closeout'];
const start=1793790000000,root='/private/tmp/topolab-public-registered-source-acquisition-20261104-v3';
const plan={root,plan_sha256:'a'.repeat(64),execution_identity:'topolab.v2.p17-m2-registered-source-acquisition.20261104.v2',scope:'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY',formal_authority:false,actor_start_ms:start,actor_window_seconds:4500,role_order:roles,coordination_limit_ms:240000};
const proof=(role,t0=start,t1=start+1000)=>({role,T0_ms:t0,T1_ms:t1,accepted:true,complete:true,actual_exit_codes:[0,0]});
test('original observed public2 coordination remains407761ms and fails240000',()=>{
 const gaps=[72369,111502,76806,94082,53002];let t=start;const done=roles.map((r,i)=>{if(i)t+=gaps[i-1];const p=proof(r,t,t+1000);t+=1000;return p;});
 assert.equal(coordinateMilliseconds(done),407761);
 assert.throws(()=>launchGate(plan,roles[5],done.slice(0,5),done[5].T0_ms),/coordination/);
});
for(const mutation of ['late-first','closed-root','identity','window','missing-proof','wrong-order','incomplete','nonzero','expired','negative-time'])test('reject '+mutation+' before next source dispatch',()=>{
 const p=structuredClone(plan),done=[];let role=roles[0],now=start+1;
 if(mutation==='late-first')now=start+30001;
 if(mutation==='closed-root')p.root=root.replace('-v3','-v2');
 if(mutation==='identity')p.execution_identity=p.execution_identity.replace('.v2','.v1');
 if(mutation==='window')p.actor_window_seconds=4501;
 if(mutation==='missing-proof')role=roles[1];
 if(['wrong-order','incomplete','nonzero','negative-time'].includes(mutation)){
  role=roles[1];done.push(proof(roles[0],start,start+1000));now=start+1001;
  if(mutation==='wrong-order')done[0].role=roles[2];
  if(mutation==='incomplete')done[0].complete=false;
  if(mutation==='nonzero')done[0].actual_exit_codes[0]=7;
  if(mutation==='negative-time')done[0].T1_ms=start-1;
 }
 if(mutation==='expired')now=start+4500001;
 assert.throws(()=>launchGate(p,role,done,now));
});
test('two real author schedules interleave without a model handoff and preserve order',async()=>{
 const completed=[],waiters=new Map();let now=start;
 const wait=async role=>{if(!completed.some(x=>x.role===role))await new Promise(resolve=>waiters.set(role,resolve));return completed.slice();};
 const boundary=author=>({prepare:async()=>structuredClone(plan),plan:async()=>structuredClone(plan),wait,
  run:async(role)=>{now+=100;const result=proof(role,now,now+100);now+=100;completed.push(result);waiters.get(role)?.();return result;},
  metadata:async role=>({role,accepted:true}),certificate:async()=>({public_only:true}),freeze:async value=>value});
 const results=await Promise.all(['producer','independent'].map(author=>executeOwned({author},boundary(author),()=>now)));
 assert.deepEqual(completed.map(x=>x.role),roles);assert.equal(coordinateMilliseconds(completed),500);
 assert.ok(results.every(x=>x.status==='OWNED_COHORT_COMPLETE_NEEDS_ACTUAL_RETURN'));
});
test('STOP freezes one attempt, never retries or consumes a successor',async()=>{
 const calls=[];const result=await executeOwned({author:'independent'},{prepare:async()=>plan,
  run:async role=>{calls.push(role);return {...proof(role),accepted:false};},
  freeze:async value=>value},()=>start+1);
 assert.equal(result.status,'STOP_RETAINED_NO_RETRY');assert.deepEqual(calls,[roles[0]]);
});

const actualModule=await import('../scripts/m2_acquisition_actual_boundary.mjs');
const actualConfig={author:'producer',repo:'/private/tmp/topolab-input-certificate-closure-20261104',evidence_root:'/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-20261103T173800Z',root,event_prefix:'unit-PUBLIC-NO-TOOLS'};
function dispatcher({fileFailure=false}={}) {
 const calls=[];let tick=start;
 const invoke=async(tool,args)=>{
  calls.push({tool,args});let output='{}\n',code=0;
  if(args.cmd.includes('await_m2_acquisition_receipt.py'))output=JSON.stringify({plan,proofs:[],source_or_payload_reads:0})+'\n';
  if(args.cmd.includes('file_m2_acquisition_event.py persist'))output=JSON.stringify({path:'/new-public/packet.json',sha256:'b'.repeat(64),bytes:10})+'\n';
  if(args.cmd.includes('file_m2_acquisition_event.py file')&&fileFailure){code=1;output='original public filing failure\n';}
  if(args.cmd.includes(' bind '))output=JSON.stringify({full_role_evidence_accepted:true,metadata_evidence_accepted:false,actual_exit_codes:[0,0]})+'\n';
  const row={tool,arguments:args,requested_ms:tick++,returned_ms:tick++,result:{exit_code:code,output,original_token_count:10}};return row;
 };return {invoke,calls};
}
test('actual boundary retains original tool rows and unique SUP/REC/bind',async()=>{
 const fake=dispatcher(),boundary=actualModule.createActualBoundary(fake.invoke,actualConfig);
 await boundary.plan();const result=await boundary.run('exporter-r0');
 assert.equal(result.accepted,true);assert.equal(boundary.raw.length,8);
 const commands=fake.calls.map(x=>x.args.cmd);
 assert.equal(commands.filter(x=>x.includes('py supervise ')&&!x.includes('file_m2_acquisition_event.py')).length,1);
 assert.equal(commands.filter(x=>x.includes('py record ')&&!x.includes('file_m2_acquisition_event.py')).length,1);
 assert.equal(commands.filter(x=>x.includes('py bind ')&&!x.includes('file_m2_acquisition_event.py')).length,1);
 assert.equal(boundary.packets['exporter-r0-supervise'].packet.responses[0].requested_ms,start+2);
});
test('failed filing still observes exactly the existing REC and never binds or repeats SUP',async()=>{
 const fake=dispatcher({fileFailure:true}),boundary=actualModule.createActualBoundary(fake.invoke,actualConfig);
 await boundary.plan();await assert.rejects(boundary.run('exporter-r0'),/AFTER unique REC/);
 const commands=fake.calls.map(x=>x.args.cmd);
 assert.equal(commands.filter(x=>x.includes('py supervise ')&&!x.includes('file_m2_acquisition_event.py')).length,1);
 assert.equal(commands.filter(x=>x.includes('py record ')&&!x.includes('file_m2_acquisition_event.py')).length,1);
 assert.equal(commands.filter(x=>x.includes('py bind ')&&!x.includes('file_m2_acquisition_event.py')).length,0);
});
test('caller failure is a disclosed failure record rather than fabricated actual-return packet',async()=>{
 const fake=dispatcher(),boundary=actualModule.createActualBoundary(fake.invoke,actualConfig);
 await boundary.freeze({status:'STOP_RETAINED_NO_RETRY'});
 assert.ok(fake.calls[0].args.cmd.includes('topolab.m2-acquisition-caller-failure.v1'));
});
test('bad actual dispatcher and escaped roots fail without real IO',async()=>{
 assert.throws(()=>actualModule.createActualBoundary(()=>assert.fail('IO'),{...actualConfig,event_prefix:'../escape'}));
 const boundary=actualModule.createActualBoundary(async()=>({result:{exit_code:0}}),actualConfig);
 await assert.rejects(boundary.plan(),/original tool row/);
});

test('stronger funded parent deadline cannot be extended by4500 identity window',()=>{
 assert.throws(()=>launchGate({...plan,applicable_deadline_ms:start+4199999},roles[0],[],start),/remaining full cohort/);
});
