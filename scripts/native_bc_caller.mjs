// API-side, metadata-only receiver. Command execution and poll times are supplied
// by the owning tools. Scientific processes cannot manufacture their own returns.
import * as fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {constants} from 'node:fs';
import * as crypto from 'node:crypto';
import * as ingress from './p17_m2_scientific_tool_ingress.mjs';
import * as observer from './p17_m2_scientific_metadata.mjs';
import {buildMetadataManifest} from './p17_m2_scientific_metadata_manifest.mjs';
import {entryRoot,formalRoot} from './native_bc_paths.mjs';
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
// Keep the complete tool request, including a localized approval prompt, in
// the ASCII metadata format accepted by both independent parsers.
const json=value=>Buffer.from(JSON.stringify(value).replace(/[^\x00-\x7f]/g,
  ch=>'\\u'+ch.charCodeAt(0).toString(16).padStart(4,'0'))+'\n','ascii');
const requireValue=(ok,msg)=>{if(!ok)throw Error(msg);};
const labels=['controller','binder','verifier','final-observer'];
const expand=(args,sha)=>args.map(word=>word.replaceAll('@SCIENTIFIC_CONTRACT_SHA256@',sha));
const roleScope={'resource-preflight':'B','scientific-producer':'C','scientific-auditor':'C'};

const MiB=1024**2;
function read(path,cap=4*MiB,expected=null) {
  return observer.readCallerControl({fs,constants},path,cap,expected);
}
export async function openCaller(path,digest,author) {
  const formal=fileURLToPath(new URL('../docs/planning/p17_m2_scientific_execution_protocol.json',import.meta.url));
  const ext='.contract.json';
  requireValue(path===formal||(path.endsWith(ext)&&entryRoot(path.slice(0,-ext.length),true)),
    'registered contract path required before opening');
  observer.configure(crypto);
  const raw=await read(path,4*MiB,digest);
  const c=observer.lossless(raw,true).value,root=c.api_metadata.root;
  requireValue(sha(raw)===digest&&c.entry_repair==='native-bc-entry-20261126-r2'&&
    entryRoot(root,c.public_fixture_only)&&(c.public_fixture_only?path===root+ext:path===formal)&&['/root','/root/authorize'].includes(author),
    'registered post-B1 caller, contract and root required');
  const s={contract:c,contractSHA256:digest,contractPath:path,root,author};
  return s;
}

export function argvFor(s,role,label) {
  const c=s.contract, spec=c.roles[role];
  requireValue(roleScope[role]&&spec,'registered role required');
  const expected=role==='scientific-producer'?'/root':'/root/authorize';
  requireValue(c.public_fixture_only ? role==='resource-preflight' : s.author===expected,
    'role requires its registered caller');
  let command;
  if(label==='publication') command=spec.publication_argv;
  else if(label==='finish') command=c[roleScope[role].toLowerCase()+'_caller_clock'].verification_argv;
  else if(label==='reservation'||label==='reader-ack') command=c.shared_helpers[role][label].dispatch_argv;
  else if(labels.includes(label)) command=spec.native_dispatch[label].dispatch_argv;
  requireValue(Array.isArray(command),'registered invocation required');
  return expand(command,s.contractSHA256);
}

async function writeRaw(path,raw) {
  let dirPath='';
  for(const name of path.split('/').slice(1,-1)){
    dirPath+='/'+name;const st=await fs.lstat(dirPath);
    requireValue(st.isDirectory()&&!st.isSymbolicLink(),'caller evidence parent type differs');
  }
  const handle=await fs.open(path,constants.O_CREAT|constants.O_EXCL|constants.O_WRONLY|constants.O_NOFOLLOW,0o600);
  try{await handle.writeFile(raw);await handle.sync();}finally{await handle.close();}
  const dir=await fs.open(path.slice(0,path.lastIndexOf('/')),constants.O_RDONLY|constants.O_DIRECTORY|constants.O_NOFOLLOW);
  try{await dir.sync();}finally{await dir.close();}
  requireValue((await read(path,Math.max(raw.length,1),sha(raw))).equals(raw),'caller evidence readback differs');
}

async function independentRelease(s) {
  const fixed='/Users/keith1117/Documents/TopoLab-data/native-bc-entry-20261126-r2';
  requireValue(s.contract.scientific_release.evidence_root===fixed,'registered release directory required');
  const pair=async name=>{
    const p=fixed+'/'+name,b=fixed+'-backup/'+name;
    const [raw,copy,st,bt]=await Promise.all([read(p,16*MiB),read(b,16*MiB),fs.lstat(p),fs.lstat(b)]);
    requireValue(st.isFile()&&bt.isFile()&&st.nlink===1&&bt.nlink===1&&
      (st.dev!==bt.dev||st.ino!==bt.ino)&&raw.equals(copy),'independent release duplicate differs');
    return raw;
  };
  const actual=JSON.parse(await pair('independent-release.json'));
  const releaseRaw=await pair('scientific-release.json'),release=JSON.parse(releaseRaw);
  const expected=[s.contract.runtime.python_entry,'-I',s.contract.runtime.cwd+'/scripts/scientific_entry_release.py',
    '--contract',s.contractPath,'--contract-sha',s.contractSHA256];
  const rows=actual.responses,last=rows.at(-1);
  requireValue(actual.author==='/root/authorize'&&JSON.stringify(actual.argv)===JSON.stringify(expected)&&
    actual.schema==='topolab.v2.m2-strict-source-binding.actual-call.v1'&&last.result.exit_code===0&&
    last.result.session_id==null,'original independent exact-merge terminal required before B');
  const proof=JSON.parse(rows.map(r=>r.result.output).join(''));
  requireValue(proof.status==='PASS_EXACT_MERGE_PUBLIC_ENTRY'&&proof.actor===actual.author&&
    proof.contract_sha256===s.contractSHA256&&proof.main===release.main&&proof.release_sha256===sha(releaseRaw)&&
    proof.host==='Apple M2'&&proof.version===s.contract.input_version_id&&
    proof.B1_plan_sha256===s.contract.acquisition.plan_sha256&&
    proof.public_raw_B_sha256===sha(await pair('merged-public-B-clock-return.json'))&&
    proof.public_caller_sha256===sha(await pair('merged-public-B-caller-receipt.json')),
    'exact-merge release/public exercise contract differs');
}
export async function begin(s,stage,startMs,publicRelease) {
  // startMs is sampled before the caller sends its first per-attempt operation.
  const {root,contract:c,contractSHA256:digest}=s;
  requireValue(Number.isSafeInteger(startMs)&&startMs<=Date.now()&&['B','C'].includes(stage),'invalid caller start');
  if(stage==='B'){
    requireValue(c.public_fixture_only||s.author==='/root/authorize','B independent caller required');
    if(!c.public_fixture_only) await independentRelease(s);
    await fs.mkdir(root,{mode:0o700});
    for(const child of ['roles','shared']) await fs.mkdir(root+'/'+child,{mode:0o700});
    if(c.public_fixture_only) {
      requireValue(publicRelease?.scope==='ENGINEERING_PUBLIC'&&publicRelease.scientific_contract_sha256===digest,
        'public engineering release binding required');
      const backup=root+'-backup';
      await fs.mkdir(backup,{mode:0o700});
      const releaseRaw=json(publicRelease);
      await writeRaw(root+'/scientific-release.json',releaseRaw);
      await writeRaw(backup+'/scientific-release.json',releaseRaw);
    }
  } else {
    requireValue(s.author==='/root'&&root===formalRoot,'C producer caller required');
    const pass=JSON.parse(await read(root+'/B-caller-receipt.json'));
    const actual=await read(root+'/B-clock-return.json');
    const jsPrefixRaw=await read(root+'/B-js-prefix.json'),prefix=JSON.parse(jsPrefixRaw);
    const checked=observer.validateBCallerClock({...s,prefix,jsPrefixRaw,returnRaw:actual,
      startRaw:await read(root+'/B-clock-start.json'),verifyProfileRaw:await read(root+'/B-verify.time'),
      verifyResourceRaw:await read(root+'/B-verify.time.resource.json'),
      manifestSHA256:sha(await read(c.api_metadata.manifests.B,16*MiB))});
    requireValue(Object.entries(checked).every(([key,value])=>pass[key]===value),'B signed caller return differs');
    requireValue(pass.status==='PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL'&&pass.scientific_contract_sha256===digest&&
      pass.b_caller_return_sha256===sha(actual)&&pass.b_caller_end_ms<=startMs,'current verified B required before C');
  }
  const raw=json({contract_sha256:digest,schema:'topolab.'+stage.toLowerCase()+'-clock-start.v1',start_ms:startMs});
  return ingress.entryControl({...s,name:stage+'-clock-start.json',raw});
}

// Stop before any successor when a completed receipt or elapsed time already
// proves a cap exceeded. The independent final checker charges the exact spans.
export async function clockGuard(s,role,label) {
  const stage=roleScope[role],now=Date.now();
  const clock=JSON.parse(await read(s.root+'/'+stage+'-clock-start.json'));
  requireValue(clock.contract_sha256===s.contractSHA256&&now>=clock.start_ms,'caller clock changed');
  if(stage==='B'){
    requireValue(now-clock.start_ms<=170000,'STOP B FULL180 before next operation');
    return true;
  }
  let roleMs=0;
  for(const r of ['scientific-producer','scientific-auditor']){
    const prior=s.contract.roles[r].root;
    let start,finish;
    try{start=JSON.parse(await read(prior+'/controller-return.json')).start_seconds;}
    catch(err){if(err.code!=='ENOENT')throw err;continue;}
    try{finish=JSON.parse(await read(prior+'/final-observer-return.json')).end_seconds;}
    catch(err){if(err.code!=='ENOENT')throw err;finish=now/1000;}
    requireValue(finish>=start&&(finish-start)+360+10<=s.contract.roles[r].FULL_seconds,
      'STOP C role FULL before next operation: '+r);
    roleMs+=Math.round((finish-start)*1000);
  }
  requireValue(now-clock.start_ms-roleMs<=166000&&now-clock.start_ms<=14580000,
    'STOP C shared FULL180 before '+label);
  return true;
}

export async function journal(s,role,label,index,kind,value) {
  argvFor(s,role,label);
  requireValue(Number.isSafeInteger(index)&&index>=0&&index<=4096&&
    ['intent','returned','exception','filing-error'].includes(kind),'invalid API journal key');
  const path=s.root+'/'+role+'-'+label+'-api-'+index+'-'+kind+'.json';
  await writeRaw(path,json(value));
  return true;
}

export async function receive(s,role,label,actual) {
  const argv=argvFor(s,role,label);
  requireValue(actual.author===s.author&&JSON.stringify(actual.argv)===JSON.stringify(argv),'original actor/command differs');
  const rows=actual.responses,last=rows.at(-1);
  const root=s.root, raw=json(actual);
  await writeRaw(root+'/'+role+'-'+label+'-actual.json',raw);
  requireValue(last.result.exit_code===0&&last.result.session_id==null,'actual terminal command failed: '+role+'/'+label);
  const result={exit_code:last.result.exit_code,output:rows.map(row=>row.result.output).join('')};
  const info={...s,role,result,actualArgv:argv,start_seconds:rows[0].requested_ms/1000,
    end_seconds:last.returned_ms/1000,observer};
  if(label==='publication'){
    const value=await ingress.publicationReturn(info);
    return {sha256:value.proofReceipt.sha256};
  }
  if(label!=='finish'){
    const spec=s.contract.roles[role];
    const publicationSHA256=label==='reservation'?sha(await read(spec.publication_readiness_path)):undefined;
    const filed=await ingress.nativeReturn({...info,label,publicationSHA256});
    requireValue(filed.event.dispatcher_exit===0,'failed native dispatcher');
    const native=['reservation','reader-ack'].includes(label)
      ?s.contract.shared_helpers[role][label]:spec.native_dispatch[label];
    const [preflush,profile,log]=await Promise.all([
      read(native.dispatch_path.replace(/\.json$/,'-preflush.json'),4*MiB),
      read(native.profile_path,MiB,filed.event.profile_sha256),read(native.log_path,4*MiB,filed.event.stdout_sha256),
    ]);
    observer.validateDispatch(s.contract,role,label,{contract_sha256:s.contractSHA256,event:filed.event,
      dispatch:Buffer.from(result.output,'utf8'),preflush,profile,log});
    if(label==='final-observer'){
      const events=[];
      for(const name of labels) events.push(JSON.parse(await read(spec.root+'/'+name+'-return.json')));
      await ingress.trustedReturns({...s,role,events});
    }
    return {sha256:filed.receipt.sha256};
  }
  const stage=roleScope[role],startRaw=await read(root+'/'+stage+'-clock-start.json');
  const verifyProfileRaw=await read(root+'/'+stage+'-verify.time');
  const verifyResourceRaw=await read(root+'/'+stage+'-verify.time.resource.json');
  const jsPrefixRaw=await read(root+'/'+stage+'-js-prefix.json');
  const prefix=JSON.parse(jsPrefixRaw);
  const returnRaw=json({schema:'topolab.'+stage.toLowerCase()+'-clock-return.v1',contract_sha256:s.contractSHA256,
    start_sha256:sha(startRaw),verification_profile_sha256:sha(verifyProfileRaw),verification_resource_sha256:sha(verifyResourceRaw),actual});
  await ingress.entryControl({...s,name:stage+'-clock-return.json',raw:returnRaw});
  const manifestSHA256=sha(await read(s.contract.api_metadata.manifests[stage==='B'?'B':'FINAL'],16*MiB));
  const validate=stage==='B'?observer.validateBCallerClock:observer.validateCCallerClock;
  const proof=validate({...s,startRaw,returnRaw,jsPrefixRaw,verifyProfileRaw,verifyResourceRaw,manifestSHA256,prefix});
  const receipt={...proof,scientific_contract_sha256:s.contractSHA256,
    source_main:prefix.source_main??null,input_version:s.contract.input_version_id,public_fixture_only:s.contract.public_fixture_only};
  await ingress.entryControl({...s,name:stage+'-caller-receipt.json',raw:json(receipt)});
  return receipt;
}

export async function prefix(s,role) {
  const stage=roleScope[role],scope=stage==='B'?'B':'FINAL';
  argvFor(s,role,'finish');
  const m=await buildMetadataManifest({...s,scope,observer});
  const inspected=await observer.observeMetadata({...s,scope,fs,constants,crypto,
    manifestPath:m.manifestPath,manifestSHA256:m.manifestSHA256});
  await writeRaw(s.root+'/'+stage+'-metadata-observer.json',json(inspected));
  const pre=stage==='B'?inspected.b_native_prefix:inspected.c_native_prefix;
  requireValue(pre&&pre.contract_sha256===s.contractSHA256,'independent native prefix required');
  return ingress.entryControl({...s,name:stage+'-js-prefix.json',raw:json(pre)});
}
