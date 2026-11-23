// All tool returns are injected public software fixtures, never real Native/input commands.
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {executeActor,qualify} from '../scripts/staged_input_actor.mjs';
const START=Date.parse('2026-11-22T08:00:00Z');
const CURRENT_ID='topolab.v2.p17-m2-registered-source-acquisition.formal-20261122.v1';
const CURRENT_ROOT='/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-formal-input-20261122-a1';
const ROLES=['independent-public-check','exporter-r0','independent-r0','exporter-r1','independent-r1','shared-closeout'];
const PUBLIC='/private/tmp/topolab-public-staged-input-20261121-a1';
const FORMAL='/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-staged-input-20261121-a1';
const RECOVERY_ID='topolab.v2.p17-m2-registered-source-acquisition.r0-read-20261122.v1';
const RECOVERY_ROOT='/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-r0-read-20261122-a1';
const CATALOG_ID='topolab.v2.p17-m2-registered-source-acquisition.catalog-20261122.v1';
const CATALOG_ROOT='/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-catalog-r0-20261122-a1';
const CATALOG_START=1795381093469;
const CYCLE_ID='topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a1.v1';
const CYCLE_ROOT='/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-input-cycle-20261123-a1';
const NEXT_ID=CYCLE_ID.replace('-a1.', '-a2.');
const NEXT_ROOT=CYCLE_ROOT.replace(/-a1$/, '-a2');
function startFor(current){return ['cycle','second'].includes(current)?1795403556212:current==='catalog'?CATALOG_START:START;}
function prefixFor(current){
 return current==='second'?'cycle_r1_input':current==='cycle'?'cycle_input':current==='catalog'?'catalog_input':current==='recovery'?'r0_input':current?'formal_input':'staged_input';
}
function config(author,formal=false,current=false){return qualify({author,formal,root:current==='second'?NEXT_ROOT:current==='cycle'?CYCLE_ROOT:current==='catalog'?CATALOG_ROOT:current==='recovery'?RECOVERY_ROOT:current?CURRENT_ROOT:formal?FORMAL:PUBLIC,
 ...(current?{execution_identity:current==='second'?NEXT_ID:current==='cycle'?CYCLE_ID:current==='catalog'?CATALOG_ID:current==='recovery'?RECOVERY_ID:CURRENT_ID}:{}),event_prefix:'mock-'+author,
 registration_certificate_sha:(formal?'c':'a').repeat(64),registration_finalize_actual_sha:(formal?'d':'b').repeat(64),
 formal_registration_certificate_sha:'c'.repeat(64),formal_registration_finalize_actual_sha:'d'.repeat(64)});}
function graph({formal=false,current=false,supExit=0,late=null,partial=false,failPacket=false,pollDrift=false,truncate=false}={}){
 const start=startFor(current);
 let plan,created,serial=0;const ready=new Promise(r=>created=r),proofs=[],calls=[],wakes=[];
 const publish=()=>{for(const fn of wakes.splice(0))fn();};
 const dispatcher=author=>async(tool,args)=>{
  const requested_ms=Date.now();calls.push({author,tool,args});let output='{}',exit_code=0;
  if(tool==='write_stdin'){if(pollDrift)return {tool,arguments:args,requested_ms,returned_ms:Date.now(),result:{output:'original drift',session_id:8}};throw Error('DECLARED_POLL_FAILURE');}
  const cmd=args.cmd.split(' --packet-json ')[0];
  const prefix=prefixFor(current);
  if(cmd.includes(' dispatch-note '))output=JSON.stringify({status:'COORDINATOR_NOTE_RETAINED'});
  else if(cmd.includes(' prepare-rehearsal ')||cmd.includes(' activate-formal ')){
   const route=config(author,formal,current);plan={root:route.root,plan_sha256:'f'.repeat(64),execution_identity:route.execution_identity,
    formal_authority:formal,scope:formal?'SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY':'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY',actor_window_seconds:4500,
    actor_start_ms:start,whole_start_ms:start,whole_end_ms:start+4500000,
    role_order:ROLES,coordination_limit_ms:240000,applicable_deadline_ms:start+4500000};
   created();output=JSON.stringify({formal_authority:formal,plan_sha256:plan.plan_sha256});
  }else if(cmd.includes(prefix+'_waiter.py')){
   await ready;const role=cmd.match(/--role ([a-z0-9-]+)/)[1];
   while(role!=='plan'&&!proofs.some(p=>p.role===role))await new Promise(r=>wakes.push(r));
   output=JSON.stringify({source_or_payload_reads:0,plan,proofs:role==='plan'?[]:proofs.slice(0,ROLES.indexOf(role)+1)});
  }else if(cmd.includes(prefix+'_control.py supervise ')){
   if(partial)return {tool,arguments:args,requested_ms,returned_ms:Date.now(),result:{output:'original partial',session_id:7}};
   exit_code=supExit;if(truncate)output='Warning: truncated output';if(late)late();
  }else if(cmd.includes(prefix+'_filer.py accept-role ')||cmd.includes(prefix+'_filer.py reserve ')||cmd.includes(prefix+'_filer.py activate-release ')){output=JSON.stringify({status:'PAIRED_PERSISTED'});
  }else if(cmd.includes(prefix+'_filer.py retain-failure')){output=JSON.stringify({status:'FAILURE_CUSTODY_RETAINED_NO_ACCEPTANCE'});
  }else if(cmd.includes(prefix+'_filer.py persist')){
   if(failPacket&&args.cmd.includes('"supervise"')){exit_code=1;output='DECLARED_COURIER_FAILURE';return {tool,arguments:args,requested_ms,returned_ms:Date.now(),result:{exit_code,output}};}
   output=JSON.stringify({status:'PAIRED_PERSISTED',path:config(author,formal,current).evidence_root+'/mock-'+serial+++'.json',sha256:'a'.repeat(64)});
  }else if(cmd.includes(prefix+'_control.py bind ')){
   const role=cmd.match(/--role ([a-z0-9-]+)/)[1];
   if(ROLES.includes(role)){proofs.push({role,accepted:true,complete:true,actual_exit_codes:[0,0],T0_ms:start,T1_ms:start});publish();}
   output=JSON.stringify({full_role_evidence_accepted:true,metadata_evidence_accepted:true});
  }else if(cmd.includes(' certify-'))output=JSON.stringify({source_input_accepted:false});
  return {tool,arguments:args,requested_ms,returned_ms:Date.now(),result:{output,exit_code}};
 };
 return {dispatcher,proofs,calls};
}
for(const [formal,current] of [[false,false],[true,false],[true,true],[true,'recovery'],[true,'catalog'],[true,'cycle'],[true,'second']])test(
 'two actors complete the SUP/REC schedule (formal='+formal+', current='+current+')',async()=>{
 const old=Date.now;Date.now=()=>startFor(current);
 try{
  const h=graph({formal,current});const [root,independent]=await Promise.all([
   executeActor(config('producer',formal,current),h.dispatcher('producer')),
   executeActor(config('independent',formal,current),h.dispatcher('independent'))]);
  assert.equal(root.status,'OWNED_COMPLETE_ACTUAL_RETURN_PENDING');
  assert.equal(independent.status,'OWNED_COMPLETE_ACTUAL_RETURN_PENDING');
  assert.deepEqual(h.proofs.map(p=>p.role),ROLES);
  const native=h.calls.filter(c=>/\.py (supervise|record) /.test(c.args.cmd.split(' --packet-json ')[0]));
  assert.equal(native.length,16);assert.ok(native.every(c=>c.args.sandbox_permissions==='require_escalated'));
  assert.ok(h.calls.every(c=>c.args.prefix_rule===undefined));
  for(const row of h.calls){const cmd=row.args.cmd.split(' --packet-json ')[0];
   const prefix=prefixFor(current);
   if(current)assert.equal(row.args.workdir,current==='second'?'/private/tmp/topolab-input-cycle-20261123-a2':current==='cycle'?'/private/tmp/topolab-input-cycle-20261123':current==='catalog'?'/private/tmp/topolab-catalog-r0-20261122':current==='recovery'?'/private/tmp/topolab-r0-read-20261122':'/private/tmp/topolab-formal-input-20261122');
   if(cmd.includes(prefix+'_filer.py persist')||cmd.includes(prefix+'_waiter.py'))assert.equal(row.args.sandbox_permissions,undefined);
   if(formal&&cmd.includes(prefix+'_filer.py file '))assert.equal(row.args.sandbox_permissions,'require_escalated');
  }
 }finally{Date.now=old;}
});

for(const mode of ['failed','late','partial','failed-plus-courier'])test(mode+' SUP retains first evidence and never opens REC',async()=>{
 let clock=START;const old=Date.now;Date.now=()=>clock;
 try{
  const h=graph({supExit:mode.startsWith('failed')?1:0,partial:mode==='partial',
   late:mode==='late'?()=>{clock+=290001;}:null,failPacket:mode==='failed-plus-courier'});
  const result=await executeActor(config('independent'),h.dispatcher('independent'));
  assert.equal(result.status,'STOP_RETAINED_NO_RETRY');assert.match(result.reason,/first supervise failed\/live\/late/);
  const native=h.calls.filter(c=>/\.py (supervise|record) /.test(c.args.cmd?.split(' --packet-json ')[0]??''));
  assert.equal(native.length,1);assert.ok(native[0].args.cmd.includes(' supervise '));
  assert.ok(result.active.supervise.packet.responses.length>=1);
  if(mode.startsWith('failed'))assert.equal(result.active.supervise.packet.responses[0].result.exit_code,1);
  if(mode==='partial')assert.equal(result.active.supervise.packet.responses[0].result.session_id,7);
  if(mode==='failed-plus-courier')assert.ok(result.secondary.length>0);
 }finally{Date.now=old;}
});

test('session drift is retained without polling any unowned session',async()=>{
 const old=Date.now;Date.now=()=>START;
 try{
  const h=graph({partial:true,pollDrift:true});
  const result=await executeActor(config('independent'),h.dispatcher('independent'));
  assert.equal(result.status,'STOP_RETAINED_NO_RETRY');assert.match(result.reason,/session drift/);
  const polls=h.calls.filter(c=>c.tool==='write_stdin');
  assert.equal(polls.length,1);assert.equal(polls[0].args.session_id,7);
  assert.equal(result.active.supervise.packet.responses[1].result.session_id,8);
 }finally{Date.now=old;}
});
test('truncated original SUP output never permits REC',async()=>{
 const old=Date.now;Date.now=()=>START;
 try{
  const h=graph({truncate:true});const result=await executeActor(config('independent'),h.dispatcher('independent'));
  assert.equal(result.status,'STOP_RETAINED_NO_RETRY');assert.match(result.reason,/complete output/);
  assert.equal(h.calls.filter(c=>c.args.cmd?.includes('staged_input_control.py record ')).length,0);
  assert.equal(result.active.supervise.packet.responses[0].result.output,'Warning: truncated output');
 }finally{Date.now=old;}
});

test('new formal caller rejects the closed generation and uses the new filer on activation failure',async()=>{
 const old=Date.now;Date.now=()=>Date.parse('2026-11-22T04:00:00Z');
 try{
  const identity='topolab.v2.p17-m2-registered-source-acquisition.formal-20261122.v1';
  const root='/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-formal-input-20261122-a1';
  const base={author:'producer',formal:true,event_prefix:'software-formal',root,execution_identity:identity,
   registration_certificate_sha:'1'.repeat(64),registration_finalize_actual_sha:'2'.repeat(64),
   formal_registration_certificate_sha:'1'.repeat(64),formal_registration_finalize_actual_sha:'2'.repeat(64)};
  assert.throws(()=>qualify({...base,root:FORMAL}));
  assert.throws(()=>qualify({...base,formal:false,root:PUBLIC}));
  const settings=qualify(base),calls=[];
  const result=await executeActor(settings,async(tool,args)=>{
   const t=Date.now();calls.push(args);const fail=args.cmd.includes(' activate-formal ');
   return {tool,arguments:args,requested_ms:t,returned_ms:t,
    result:{exit_code:fail?1:0,output:fail?'declared activation failure':'{"status":"PAIRED_PERSISTED"}'}};
  });
  assert.equal(result.status,'STOP_RETAINED_NO_RETRY');assert.equal(calls.length,2);
  assert.ok(calls[0].cmd.includes('formal_input_control.py activate-formal '));
  assert.ok(calls[1].cmd.includes('formal_input_filer.py persist '));
  assert.ok(calls.every(c=>c.workdir==='/private/tmp/topolab-formal-input-20261122'));
 }finally{Date.now=old;}
});