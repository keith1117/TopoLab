import assert from 'node:assert/strict';
import {test} from 'node:test';
import * as boundary from '../scripts/m2_acquisition_actual_boundary.mjs';
const repo='/private/tmp/topolab-input-certificate-closure-20261104';
const root='/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-20261103T173800Z';
const config={author:'/root/permission_remedy_reader_v1',repo,evidence_root:root,
 event_prefix:'V33-unit-only',standards_sha:'a'.repeat(64),spec_sha:'b'.repeat(64)};
const original='exec_command failed: CreateProcess { message: "Rejected(\\\"The automatic permission approval review did not finish before its deadline.\\\")" }';
test('approval timeout retains original args/endpoints/error and never starts actor',async()=>{
 const rows=[],calls=[];let tick=100;
 await assert.rejects(boundary.permissionThenPrepare(async(tool,args)=>{calls.push(args);throw Error(original);},config,rows,()=>tick++),/automatic permission approval/);
 assert.equal(calls.length,1);assert.equal(rows.length,1);
 assert.equal(rows[0].error,'Error: '+original);assert.equal(rows[0].requested_ms,100);assert.equal(rows[0].returned_ms,101);
 assert.equal(rows[0].result,undefined);assert.equal(rows[0].arguments.sandbox_permissions,'require_escalated');
 assert.ok(calls[0].cmd.endsWith(' --help'));assert.ok(!calls[0].cmd.includes(' prepare '));
});
test('same-author approved exact prefix precedes courier and unique actor prepare',async()=>{
 const calls=[],rows=[];let tick=100;
 const result=await boundary.permissionThenPrepare(async(tool,args)=>{
  calls.push(args);let output='usage: recovery\n';
  if(args.cmd.includes('file_m2_acquisition_event.py persist'))output=JSON.stringify({path:root+'/independent/V33-public9-permission-preflight-raw-actual-call.json',sha256:'c'.repeat(64)})+'\n';
  if(args.cmd.includes(' prepare '))output=JSON.stringify({actor_start_ms:200})+'\n';
  return {tool,arguments:args,requested_ms:tick++,returned_ms:tick++,result:{exit_code:0,output}};
 },config,rows);
 assert.equal(calls.length,3);assert.equal(result.result.exit_code,0);
 assert.ok(calls[0].prefix_rule.at(-1).endsWith('/p17_m2_source_binding_recovery_v7.py'));
 assert.ok(calls[2].cmd.includes(' --permission-packet '));assert.ok(calls[2].cmd.includes(' --permission-packet-sha '+ 'c'.repeat(64)));
 assert.equal(rows.length,3);
});
test('incomplete permission receipt and old author cannot prepare',async()=>{
 let calls=0;
 await assert.rejects(boundary.permissionThenPrepare(async(tool,args)=>{calls++;return {tool,arguments:args,requested_ms:1,returned_ms:2,result:{session_id:3,output:''}};},config,[]),/permission complete/);
 assert.equal(calls,1);
 await assert.rejects(boundary.permissionThenPrepare(()=>assert.fail('dispatch'),{...config,author:'/root/binding_route_independent_v1'},[]),/fixed permission/);
});
test('V33 acquisition boundary keeps thrown metadata dispatch observation',async()=>{
 const rows=[],config2={author:'independent',repo,evidence_root:root,
  root:'/private/tmp/topolab-public-registered5-source-acquisition-20261104-v7',event_prefix:'V33-unit-source'};
 const actual=boundary.createActualBoundary(async(tool,args)=>{rows.push({tool,args});throw Error(original);},config2);
 await assert.rejects(actual.plan(),/automatic permission approval/);
 assert.equal(rows.length,1);assert.equal(actual.raw.length,1);
 assert.equal(actual.raw[0].error,'Error: '+original);
 assert.deepEqual(actual.raw[0].arguments,rows[0].args);
 assert.ok(Number.isSafeInteger(actual.raw[0].requested_ms)&&actual.raw[0].requested_ms<=actual.raw[0].returned_ms);
});
