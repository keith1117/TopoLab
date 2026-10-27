import assert from 'node:assert/strict';
import {test} from 'node:test';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import * as ingress from '../scripts/p17_m2_scientific_tool_ingress.mjs';
import {buildMetadataManifest} from '../scripts/p17_m2_scientific_metadata_manifest.mjs';
import * as observer from '../scripts/p17_m2_scientific_metadata.mjs';
const actionParent='/private/tmp/topolab-funded-continuation-20261026';
const identity='topolab.v2.p17-m2-native-homotopy.rss.v1',role='resource-preflight';
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const canonical=v=>v===null?'null':Array.isArray(v)?'['+v.map(canonical).join(',')+']':typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
const bytes=v=>Buffer.from(canonical(v)+'\n');
const limits={max_files:65536,max_total_bytes:536870912,max_record_bytes:134217728,max_log_bytes:4194304,max_profile_bytes:1048576,max_manifest_bytes:16777216,max_contract_bytes:4194304};
const notExists=async name=>{await assert.rejects(fs.lstat(name),{code:'ENOENT'});};
async function publicRoot({outsideAction=false}={}){
  let base=await fs.realpath(process.env.TOPOLAB_INGRESS_TEST_ROOT||os.tmpdir());
  if(outsideAction&&(base===actionParent||base.startsWith(actionParent+'/')))base=await fs.realpath(os.tmpdir());
  if(outsideAction)assert.ok(base!==actionParent&&!base.startsWith(actionParent+'/'));
  return fs.mkdtemp(path.join(base,'m2-ingress-'));
}
function contractFor(root,{formal=false,invalidStart=false,mutateLimits=()=>{},outputAlias=false}={}){
  const spec={root:root+'/resource-preflight',FULL_seconds:180,publication_argv:['/public/python','publication-check','@SCIENTIFIC_CONTRACT_SHA256@'],publication_readiness_path:root+'/publication-proof.json',publication_return_path:root+'/publication-return.json',exit_argv:{},native_dispatch:{},inner_starts:(invalidStart?['../rejected']:['success','exit-seven','timeout']).map(name=>({name,timeout_seconds:1}))};
  for(const label of ['controller','binder','verifier','final-observer']){
    const base=spec.root+'/'+label;spec.exit_argv[label]=['/public/intended-native',label];spec.native_dispatch[label]={dispatch_path:base+'.dispatch.json',profile_path:base+'.time',log_path:base+'.log',dispatch_argv:['/public/intended-dispatch',label]};
  }
  const contract={schema:'topolab.v2.m2-scientific-contract.v1',execution_identity:identity,public_fixture_only:!formal,roles:{[role]:spec},shared_helpers:{[role]:{reservation:{argv:['/public/intended-reserve'],dispatch_path:root+'/reservation.dispatch.json',profile_path:root+'/reservation.time',log_path:root+'/reservation.log',dispatch_argv:['/public/intended-reserve-dispatch']}}},api_metadata:{schema:'topolab.v2.m2-api-metadata-policy.v1',root,manifests:{B:root+(outputAlias?'/alias':'')+'/manifest.json',FINAL:root+'/FINAL-manifest.json'},limits:{...limits},sample_interval_seconds:.5}};
  mutateLimits(contract.api_metadata.limits);return contract;
}
async function contractFile(contract,root){const raw=bytes(contract),contractPath=root+'/contract.json';await fs.writeFile(contractPath,raw,{mode:0o600,flag:'wx'});return {contractPath,contractSHA256:hash(raw),raw};}
const call=(contract,overrides={})=>({contract,contractSHA256:'a'.repeat(64),role,label:'controller',observer,result:{exit_code:1,output:'not JSON: actual failed stdout\n'},start_seconds:100,end_seconds:101,actualArgv:['/public/ACTUALLY-called-dispatch'],...overrides});

test('incomplete sessions and future exits cannot become completed events',async()=>{
  const root=await publicRoot(),contract=contractFor(root);
  for(const result of [{exit_code:0,session_id:123,output:'{}\n'},{exit_code:'UNKNOWN',output:'{}\n'},{output:'{}\n'}])await assert.rejects(ingress.nativeReturn(call(contract,{result})),/actual complete tool return/);
  await notExists(contract.roles[role].root+'/controller-return.json');
});
test('failed event preserves original raw stdout, actual argv, exit and parse context before rejected output',async()=>{
  const root=await publicRoot({outsideAction:true}),contract=contractFor(root),output='not JSON: actual failed stdout\n';
  await assert.rejects(ingress.nativeReturn(call(contract)),error=>{
    const failure=error.metadata_output_failure,event=JSON.parse(Buffer.from(failure.raw_output_base64,'base64'));
    assert.equal(failure.stage,'literal-output');assert.equal(event.dispatch_stdout,output);assert.equal(event.dispatch_stdout_sha256,hash(Buffer.from(output)));assert.equal(event.exit_code,1);assert.equal(event.actual_tool_exit_code,1);assert.equal(event.complete,true);
    assert.deepEqual(event.dispatch_argv,['/public/ACTUALLY-called-dispatch']);assert.deepEqual(event.registered_dispatch_argv_intent,['/public/intended-dispatch','controller']);assert.ok(event.packet_parse_error);return true;
  });
  await notExists(contract.roles[role].root+'/controller-return.json');
});
test('publication rejects an incomplete return and retains exact raw failed proof',async()=>{
  const root=await publicRoot({outsideAction:true}),contract=contractFor(root),output='original publication failure\n';
  await assert.rejects(ingress.publicationReturn({...call(contract),result:{exit_code:0,session_id:7,output}}),/actual complete tool return/);
  await assert.rejects(ingress.publicationReturn({...call(contract),result:{exit_code:2,output}}),error=>{assert.equal(Buffer.from(error.metadata_output_failure.raw_output_base64,'base64').toString(),output);assert.equal(error.metadata_output_failure.sha256,hash(Buffer.from(output)));return true;});
  await notExists(contract.roles[role].publication_readiness_path);
});
test('four-return table refuses incomplete events before IO',async()=>{
  const root=await publicRoot(),contract=contractFor(root);
  await assert.rejects(ingress.trustedReturns({contract,role,events:[{complete:true}]}),/four actual outer returns/);
  await assert.rejects(ingress.trustedReturns({contract,role,events:[{complete:true},{complete:true},{complete:false},{complete:true}]}),/four actual outer returns/);
  await notExists(contract.roles[role].root+'/trusted-returns.json');
});
test('formal contract cannot redirect native return output',async()=>{
  const root=await publicRoot(),contract=contractFor(root,{formal:true});
  await assert.rejects(ingress.nativeReturn(call(contract,{outputOverride:root+'/redirect.json'})),/formal return path override forbidden/);await notExists(root+'/redirect.json');
});
test('wrong contract hash retains full read and FD/closing tuple',async()=>{
  const root=await publicRoot(),contract=contractFor(actionParent+'/PUBLIC_ONLY_NOT_CREATED'),f=await contractFile(contract,root);
  await assert.rejects(buildMetadataManifest({...f,contractSHA256:'0'.repeat(64),scope:'B',observer}),error=>{
    const evidence=error.metadata_manifest_failure.evidence;assert.match(error.message,/trusted metadata SHA mismatch/);assert.equal(evidence.returned_bytes,f.raw.length);assert.equal(evidence.sha256,hash(f.raw));assert.deepEqual(evidence.before,evidence.closing);return true;
  });
});
test('manifest semantic failure preserves successful contract prefix and original hash',async()=>{
  const root=await publicRoot(),contract=contractFor(actionParent+'/PUBLIC_ONLY_NOT_CREATED',{invalidStart:true}),f=await contractFile(contract,root);
  await assert.rejects(buildMetadataManifest({...f,scope:'B',observer}),error=>{
    const failure=error.metadata_manifest_failure;assert.match(error.message,/registered inner start/);assert.equal(failure.metadata_files_read,1);assert.equal(failure.metadata_bytes_read,f.raw.length);assert.equal(failure.prior_observations.length,1);assert.equal(failure.prior_observations[0].sha256,hash(f.raw));assert.deepEqual(failure.prior_observations[0].before,failure.prior_observations[0].closing);return true;
  });
});
test('manifest rejects nonformal scope, enlarged byte/count caps and formal public override',async()=>{
  const root=await publicRoot();await assert.rejects(buildMetadataManifest({contractPath:root+'/absent',contractSHA256:'a'.repeat(64),scope:'UNKNOWN',observer}),/scope/);
  for(const [key,value] of [['max_files',65537],['max_total_bytes',536870913],['max_record_bytes',134217729],['max_profile_bytes',1048577]]){
    const dir=await publicRoot(),contract=contractFor(actionParent+'/PUBLIC_ONLY_NOT_CREATED',{mutateLimits:v=>v[key]=value}),f=await contractFile(contract,dir);
    await assert.rejects(buildMetadataManifest({...f,scope:'B',observer}),/metadata limits/);
  }
  const dir=await publicRoot(),contract=contractFor(actionParent+'/PUBLIC_ONLY_NOT_CREATED',{formal:true}),f=await contractFile(contract,dir);
  await assert.rejects(buildMetadataManifest({...f,scope:'B',observer,publicFixturePolicy:contract.api_metadata}),/formal metadata policy override forbidden/);
});

// These two integrations exercise the fixed action-domain identity on its actual
// host. Linux runs the portable negatives above and never creates /private/tmp.
async function boundHostAvailable(){if(process.platform!=='darwin')return false;try{const s=await fs.lstat(actionParent);return s.isDirectory()&&!s.isSymbolicLink();}catch{return false;}}
const boundAvailable=await boundHostAvailable();
async function boundFixture(options={}){
  const root=await fs.mkdtemp(actionParent+'/api-regression-public-'),contract=contractFor(root,options),spec=contract.roles[role],files=new Map();
  await fs.mkdir(spec.root,{mode:0o700});
  for(const label of ['reservation','controller','binder','verifier','final-observer']){
    const item=label==='reservation'?contract.shared_helpers[role].reservation:spec.native_dispatch[label];
    files.set(item.dispatch_path,Buffer.from('public dispatch bytes\n'));files.set(item.dispatch_path.replace(/\.json$/,'-preflush.json'),Buffer.from('public preflush bytes\n'));files.set(item.profile_path,Buffer.from('public profile bytes\n'));files.set(item.log_path,Buffer.from('public log bytes\n'));files.set(spec.root+'/'+label+'-return.json',Buffer.from('public return bytes\n'));
  }
  for(const name of ['quota-pending.json','controller-summary.json','case-spans.json','controller-exit.json','binder-exit.json','verifier-exit.json'])files.set(spec.root+'/'+name,Buffer.from('new public metadata '+name+'\n'));
  for(const start of spec.inner_starts){
    const base=spec.root+'/controls/'+start.name;await fs.mkdir(base,{recursive:true,mode:0o700});
    files.set(base+'/command.json',bytes({helpers:options.emptyHelpers?[]:[{profile:'sampler-0.time'}]}));files.set(base+'/command.time',Buffer.from('public command profile\n'));files.set(base+'/command.log',Buffer.from('public command log\n'));files.set(base+'/sampler-0.time',Buffer.from('public sampler raw profile\n'));
  }
  for(const [name,raw] of files)await fs.writeFile(name,raw,{mode:0o600,flag:'wx'});
  const f=await contractFile(contract,root);return {root,contract,files,...f};
}
test('bound-host real outputs retain actual event bytes and independently hashed complete manifest',{skip:!boundAvailable},async()=>{
  const f=await boundFixture(),spec=f.contract.roles[role];
  // Existing fixture metadata deliberately occupies the standard event name;
  // the new public override demonstrates truthful ingress without overwriting it.
  const stdout='{"argv":["/public/actual-native"],"log_sha256":"'+'b'.repeat(64)+'","profile_sha256":"'+'c'.repeat(64)+'","started_unix_ns":1793041621733057634}\n';
  const saved=await ingress.nativeReturn(call(f.contract,{outputOverride:f.root+'/actual-return.json',result:{exit_code:0,output:stdout}}));
  const eventBytes=await fs.readFile(saved.receipt.path);assert.equal(hash(eventBytes),saved.receipt.sha256);assert.equal(saved.event.dispatch_stdout,stdout);assert.equal(saved.event.dispatch_stdout_sha256,hash(Buffer.from(stdout)));assert.deepEqual(saved.event.argv,['/public/actual-native']);assert.deepEqual(saved.event.dispatch_argv,['/public/ACTUALLY-called-dispatch']);assert.equal(Number((await fs.stat(saved.receipt.path)).mode)&0o777,0o600);
  const bad=await ingress.nativeReturn(call(f.contract,{outputOverride:f.root+'/failed-return.json'}));assert.equal(bad.event.exit_code,1);assert.ok(bad.event.packet_parse_error);assert.equal(JSON.parse(await fs.readFile(bad.receipt.path,'utf8')).dispatch_stdout,'not JSON: actual failed stdout\n');
  const manifest=await buildMetadataManifest({...f,scope:'B',observer}),m=JSON.parse(await fs.readFile(manifest.manifestPath));assert.equal(hash(await fs.readFile(manifest.manifestPath)),manifest.manifestSHA256);assert.equal(manifest.files,43);assert.equal(manifest.observations.length,44);assert.equal(Object.keys(m.files).length,43);
  for(const [relative,item] of Object.entries(m.files)){const raw=await fs.readFile(f.root+'/'+relative);assert.equal(item.sha256,hash(raw));assert.equal(item.bytes,raw.length);}
  assert.ok(!Object.hasOwn(m.files,'actual-return.json'));assert.ok(!Object.hasOwn(m.files,'failed-return.json'));
  const failure=await boundFixture({emptyHelpers:true});await assert.rejects(buildMetadataManifest({...failure,scope:'B',observer}),error=>{const e=error.metadata_manifest_failure;assert.match(error.message,/registered sampler count/);assert.equal(e.metadata_files_read,2);assert.equal(e.prior_observations.length,2);return true;});
});
test('bound-host ancestor symlink rejects before either output creation',{skip:!boundAvailable},async()=>{
  const f=await boundFixture({outputAlias:true}),outside=await publicRoot();await fs.symlink(outside,f.root+'/alias');
  await assert.rejects(ingress.nativeReturn(call(f.contract,{outputOverride:f.root+'/alias/escaped-return.json'})),error=>{assert.match(error.message,/parent symlink/);assert.equal(error.metadata_output_failure.stage,'output-parents');assert.ok(error.metadata_output_failure.raw_output_base64);return true;});await notExists(outside+'/escaped-return.json');
  await assert.rejects(buildMetadataManifest({...f,scope:'B',observer}),error=>{assert.match(error.message,/output parent symlink/);assert.equal(error.metadata_manifest_failure.stage,'manifest-output-parents');assert.equal(error.metadata_manifest_failure.prior_observations.length,44);return true;});await notExists(outside+'/manifest.json');
});

// Smaller declared policies are effective before any additional metadata IO.
test('smaller count and byte policy reject at bootstrap before command metadata',async()=>{
  for(const [key,value] of [['max_files',1],['max_total_bytes',1]]){
    const root=await publicRoot(),contract=contractFor(actionParent+'/PUBLIC_ONLY_NOT_CREATED',{mutateLimits:v=>v[key]=value}),f=await contractFile(contract,root);
    await assert.rejects(buildMetadataManifest({...f,scope:'B',observer}),error=>{const x=error.metadata_manifest_failure;assert.equal(x.stage,'policy');assert.equal(x.metadata_files_read,1);assert.equal(x.metadata_bytes_read,f.raw.length);assert.equal(x.prior_observations.length,1);assert.equal(x.prior_observations[0].sha256,hash(f.raw));return true;});
  }
});
test('smaller count policy reserves the output slot before a first command read',async()=>{
  const root=await publicRoot(),contract=contractFor(actionParent+'/PUBLIC_ONLY_NOT_CREATED',{mutateLimits:v=>v.max_files=2}),f=await contractFile(contract,root);
  await assert.rejects(buildMetadataManifest({...f,scope:'B',observer}),error=>{const x=error.metadata_manifest_failure;assert.match(error.message,/metadata count cap/);assert.equal(x.metadata_files_read,1);assert.equal(x.prior_observations.length,1);return true;});
});
test('bound-host aggregate policy stops before reading a member that exceeds it',{skip:!boundAvailable},async()=>{
  const f=await boundFixture({mutateLimits:v=>v.max_total_bytes=4096});assert.ok(f.raw.length<4096);
  await assert.rejects(buildMetadataManifest({...f,scope:'B',observer}),error=>{const x=error.metadata_manifest_failure;assert.match(error.message,/metadata identity\/byte bound/);assert.ok(x.metadata_bytes_read<=4096);assert.ok(x.metadata_files_read>1);assert.equal(x.evidence.returned_bytes,0);assert.ok(x.evidence.before);assert.ok(x.evidence.closing);return true;});
});
