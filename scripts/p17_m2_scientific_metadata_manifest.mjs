// One action's bounded metadata inventory. No scans, subprocess or scientific input IO.
import * as fs from 'node:fs/promises';
import {constants as flags} from 'node:fs';
import * as crypto from 'node:crypto';
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const need=(v,m)=>{if(!v)throw Error(m);};
const fields=['dev','ino','size','mtimeNs','mode','nlink'];
const same=(a,b)=>a&&b&&fields.every(k=>a[k]===b[k]);
const tuple=s=>s?Object.fromEntries(fields.map(k=>[k,String(s[k])])):null;
export async function buildMetadataManifest({contractPath,contractSHA256,scope,observer,publicFixturePolicy}) {
  need(['B','FINAL'].includes(scope)&&/^[a-f0-9]{64}$/.test(contractSHA256),'registered scope/trusted contract SHA');
  const cache=new Map(),observations=[];let total=0,stage='trusted-contract',activeLimits=null;
  async function read(path,cap,expected) {
    need(path.startsWith('/')&&!path.split('/').slice(1).some(x=>!x||x==='.'||x==='..'),'literal metadata path');
    if(cache.has(path)){const r=cache.get(path);need(r.raw.length<=cap&&(!expected||r.sha256===expected),'changed cached metadata cap/hash');return r;}
    need(cache.size<(activeLimits?activeLimits.max_files-1:65536),'metadata count cap');
    let h,declared,before,raw,error=null;
    const evidence={path,declared:null,before:null,after:null,closing:null,returned_bytes:0,sha256:null,secondary_errors:[]};
    try {
      let parent='';for(const part of path.split('/').slice(1,-1)){parent+='/'+part;const st=await fs.lstat(parent,{bigint:true});need(st.isDirectory()&&!st.isSymbolicLink(),'metadata parent symlink/type');}
      declared=await fs.lstat(path,{bigint:true});evidence.declared=tuple(declared);
      need(declared.isFile()&&declared.nlink===1n,'metadata regular/single-link');
      h=await fs.open(path,flags.O_RDONLY|flags.O_NOFOLLOW|flags.O_NONBLOCK);
      before=await h.stat({bigint:true});evidence.before=tuple(before);
      need(same(declared,before)&&before.size>=0n&&before.size<=BigInt(cap)&&total+Number(before.size)<=(activeLimits?.max_total_bytes??512*1024**2),'metadata identity/byte bound');
      raw=Buffer.alloc(Number(before.size));
      while(evidence.returned_bytes<raw.length){const n=evidence.returned_bytes;const r=await h.read(raw,n,raw.length-n,n);need(Number.isSafeInteger(r.bytesRead)&&r.bytesRead>0&&r.bytesRead<=raw.length-n,'metadata short read');evidence.returned_bytes+=r.bytesRead;}
      need((await h.read(Buffer.alloc(1),0,1,raw.length)).bytesRead===0,'metadata grew');
      const after=await h.stat({bigint:true});evidence.after=tuple(after);need(same(before,after),'metadata fstat drift');
      evidence.sha256=hash(raw);need(!expected||evidence.sha256===expected,'trusted metadata SHA mismatch');
    } catch(problem){error=problem;}
    finally {
      if(h)try{await h.close();}catch(problem){evidence.secondary_errors.push({stage:'close',type:problem.name,reason:problem.message});error??=problem;}
      if(declared)try{const closing=await fs.lstat(path,{bigint:true});evidence.closing=tuple(closing);if(!same(before||declared,closing))throw Error('metadata closing drift');}catch(problem){evidence.secondary_errors.push({stage:'closing',type:problem.name,reason:problem.message});error??=problem;}
    }
    if(error){error.metadata_manifest_failure={evidence,prior_observations:observations};throw error;}
    const r={raw,sha256:evidence.sha256};cache.set(path,r);observations.push(evidence);total+=raw.length;return r;
  }
  try {
  const contractRaw=(await read(contractPath,4*1024**2,contractSHA256)).raw;
  const contract=observer.lossless(contractRaw,true).value;
  need(contract.schema==='topolab.v2.m2-scientific-contract.v1','metadata contract schema');
  need(!publicFixturePolicy||contract.public_fixture_only===true,'formal metadata policy override forbidden');
  stage='policy';const policy=publicFixturePolicy??contract.api_metadata,limits=policy?.limits;
  need(policy?.schema==='topolab.v2.m2-api-metadata-policy.v1'&&policy.sample_interval_seconds===0.5,'metadata policy');
  const ceilings={max_files:65536,max_total_bytes:512*1024**2,max_record_bytes:128*1024**2,max_log_bytes:4*1024**2,max_profile_bytes:1024**2,max_manifest_bytes:16*1024**2,max_contract_bytes:4*1024**2};
  need(limits&&Object.keys(limits).length===Object.keys(ceilings).length&&Object.entries(ceilings).every(([k,v])=>Number.isSafeInteger(limits[k])&&limits[k]>0&&limits[k]<=v),'metadata limits');
  need(contractRaw.length<=limits.max_contract_bytes,'contract byte cap');
  activeLimits=limits;need(cache.size+1<=limits.max_files&&total<=limits.max_total_bytes,'metadata active policy bootstrap bounds');
  const root=policy.root,manifestPath=policy.manifests?.[scope];
  need(typeof root==='string'&&(root.startsWith('/private/tmp/topolab-funded-continuation-20261026/')||root==='/private/tmp/topolab-funded-continuation-20261026'),'NEW metadata root');
  need(typeof manifestPath==='string'&&manifestPath.startsWith(root+'/')&&!manifestPath.split('/').slice(1).some(x=>!x||x==='.'||x==='..'),'registered literal manifest output');
  const wanted=new Map();
  const add=(p,cap)=>{need(typeof p==='string'&&p.startsWith(root+'/')&&!p.split('/').some(x=>x==='..'||x==='.'),'metadata path escaped root');need(!wanted.has(p)||wanted.get(p)===cap,'metadata path cap conflict');wanted.set(p,cap);};
  stage='contract-namespace';
  for(const role of scope==='B'?['resource-preflight']:['resource-preflight','scientific-producer','scientific-auditor']) {
    const spec=contract.roles[role],r=spec.root;
    for(const label of ['reservation','controller','binder','verifier','final-observer',...(role==='resource-preflight'?[]:['reader-ack'])]) {
      const item=['reservation','reader-ack'].includes(label)?contract.shared_helpers[role][label]:spec.native_dispatch[label];
      add(item.dispatch_path,limits.max_record_bytes);add(item.dispatch_path.replace(/\.json$/,'-preflush.json'),limits.max_record_bytes);
      add(item.profile_path,limits.max_profile_bytes);add(item.log_path,limits.max_log_bytes);add(r+'/'+label+'-return.json',limits.max_record_bytes);
    }
    for(const name of ['quota-pending.json','controller-summary.json','case-spans.json','controller-exit.json','binder-exit.json','verifier-exit.json'])add(r+'/'+name,limits.max_record_bytes);
    if(contract.public_fixture_only!==true){add(r+'/trusted-returns.json',limits.max_record_bytes);add(spec.publication_readiness_path,limits.max_record_bytes);add(spec.publication_return_path,limits.max_record_bytes);}
    for(const start of spec.inner_starts) {
      need(/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(start.name)&&Number.isSafeInteger(start.timeout_seconds)&&start.timeout_seconds>0&&start.timeout_seconds<=spec.FULL_seconds,'registered inner start');
      const base=r+(role==='resource-preflight'?'/controls/':'/native/')+start.name;
      add(base+'/command.json',limits.max_record_bytes);add(base+'/command.time',limits.max_profile_bytes);add(base+'/command.log',limits.max_log_bytes);
      stage='command-record:'+base+'/command.json';const record=observer.lossless(observer.compactLexemes((await read(base+'/command.json',limits.max_record_bytes)).raw)).value;
      need(Array.isArray(record.helpers)&&record.helpers.length>0&&record.helpers.length<=Math.ceil(start.timeout_seconds/policy.sample_interval_seconds)+2,'registered sampler count');
      record.helpers.forEach((item,index)=>{need(item.profile==='sampler-'+index+'.time','sampler profile index');add(base+'/'+item.profile,limits.max_profile_bytes);});
    }
  }
  need(wanted.size+2<=limits.max_files,'metadata policy count cap');
  stage='strict-member-read';const files={};
  for(const [path,cap] of [...wanted].sort(([a],[b])=>a.localeCompare(b))){const r=await read(path,cap);files[path.slice(root.length+1)]={bytes:r.raw.length,sha256:r.sha256};}
  const value={schema:'topolab.v2.m2-api-metadata-manifest.v1',scope,contract_sha256:contractSHA256,files};
  const raw=Buffer.from(JSON.stringify(value)+'\n');
  need(raw.length<=limits.max_manifest_bytes&&total+raw.length<=limits.max_total_bytes,'manifest/total byte cap');
  stage='manifest-output-parents';let parent='';
  for(const part of manifestPath.split('/').slice(1,-1)){parent+='/'+part;const s=await fs.lstat(parent,{bigint:true});need(s.isDirectory()&&!s.isSymbolicLink(),'manifest output parent symlink/non-directory');}
  let h,d,outputError=null;const secondary=[];
  try {stage='manifest-create';h=await fs.open(manifestPath,flags.O_WRONLY|flags.O_CREAT|flags.O_EXCL|flags.O_NOFOLLOW,0o600);stage='manifest-write-and-sync';await h.writeFile(raw);await h.sync();stage='manifest-directory-sync';d=await fs.open(manifestPath.slice(0,manifestPath.lastIndexOf('/')),flags.O_RDONLY|flags.O_DIRECTORY|flags.O_NOFOLLOW);await d.sync();}
  catch(error){outputError=error;}
  finally {for(const [label,handle] of [['close-manifest',h],['close-directory',d]])if(handle)try{await handle.close();}catch(error){secondary.push({stage:label,type:error.name,reason:error.message});outputError??=error;}}
  if(outputError){outputError.metadata_output_failure={path:manifestPath,bytes:raw.length,sha256:hash(raw),secondary_errors:secondary};throw outputError;}
  return {manifestPath,manifestSHA256:hash(raw),scope,files:wanted.size,total_metadata_bytes:total,manifest_bytes:raw.length,observations,new_native_or_FEM_or_input_calls:0};
  } catch(error) {
    const current=error.metadata_manifest_failure;
    error.metadata_manifest_failure={...current,scope,contractPath,contractSHA256,stage,metadata_files_read:cache.size,metadata_bytes_read:total,prior_observations:observations};
    throw error;
  }
}
