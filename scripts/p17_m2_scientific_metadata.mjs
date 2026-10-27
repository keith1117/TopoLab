// Metadata-only adaptation of TopoLab's separately authored public observer.
// No subprocess, Python, model, acquisition payload, numerical solver or
// producer acceptance oracle is used. Native scientific paths remain unchanged.
let cryptoAPI;
export function configure(crypto) { cryptoAPI = crypto; }
export function compactLexemes(raw) {
  need(Buffer.isBuffer(raw)&&raw.every(byte=>byte<=127),'ASCII metadata required');
  const text=raw.toString('ascii'),parts=[];
  let quoted=false,escaped=false,start=0;
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(quoted) {
      if(escaped)escaped=false;
      else if(c==='\\')escaped=true;
      else if(c==='"')quoted=false;
    }else if(c==='"')quoted=true;
    else if(/[ \t\r\n]/.test(c)) {
      if(start<i)parts.push(text.slice(start,i));
      start=i+1;
    }else need(!/\s/.test(c),'invalid JSON whitespace');
  }
  need(!quoted,'unclosed JSON string');
  if(start<text.length)parts.push(text.slice(start));
  return Buffer.from(parts.join('')+'\n','ascii');
}
const fail = m => { throw Error(m); };
const need = (v,m) => { if (!v) fail(m); };
const hash = raw => cryptoAPI.createHash('sha256').update(raw).digest('hex');
const eq = (a,b) => {
  if (typeof a !== typeof b) return false;
  if (a === null || typeof a !== 'object') return a === b;
  const ka=Object.keys(a),kb=Object.keys(b);
  return ka.length===kb.length && ka.every(k=>Object.hasOwn(b,k)&&eq(a[k],b[k]));
};
const finite = x => typeof x==='number' && Number.isFinite(x) && x>=0;
const posint = x => Number.isSafeInteger(x)&&x>0;
const roles=['resource-preflight','scientific-producer','scientific-auditor'];
const labels=['controller','binder','verifier','final-observer'];
const ID='topolab.v2.p17-m2-native-homotopy.rss.v1';
const CAP=4294967296;
const resolve = (a,sha) => a.map(s=>s.replaceAll('@SCIENTIFIC_CONTRACT_SHA256@',sha));

// Compact JSON grammar; duplicate keys rejected. Unsafe integer tokens become
// BigInt. Raw numeric lexemes and exact byte ranges remain untouched.
export function lossless(raw, ordered=false) {
  if(Buffer.isBuffer(raw))need(raw.every(byte=>byte<=127),'ASCII metadata required');
  const text=Buffer.isBuffer(raw)?raw.toString('ascii'):raw;
  need(typeof text==='string'&&!/[^\x00-\x7f]/.test(text),'ASCII metadata required');
  need(typeof text==='string'&&text.endsWith('\n'),'JSON final newline');
  let i=0,rootTokens;
  const string=()=>{
    const start=i++; need(text[start]==='"','JSON string');
    while(i<text.length){ const c=text[i++]; if(c==='\\'){i++;continue;} if(c==='"')return JSON.parse(text.slice(start,i)); need(c.charCodeAt(0)>=32,'JSON control'); }
    fail('unterminated string');
  };
  const value=(depth=0)=>{
    need(depth<=64,'JSON depth');
    if(text[i]==='"')return string();
    if(text[i]==='{'){
      i++;const out=Object.create(null),tokens=Object.create(null);let prior=null;
      if(text[i]==='}'){i++;if(depth===0)rootTokens=tokens;return out;}
      while(true){
        const memberStart=i,k=string();
        need(!Object.hasOwn(out,k)&& (!ordered||prior===null||prior<k),'duplicate/unsorted JSON key'); prior=k;
        need(text[i++]===':','JSON colon/whitespace');const start=i;
        out[k]=value(depth+1);tokens[k]={memberStart,start,end:i};
        if(text[i]==='}'){i++;break;} need(text[i++ ]===',','JSON comma/whitespace');
      }
      if(depth===0)rootTokens=tokens;return out;
    }
    if(text[i]==='['){i++;const out=[];if(text[i]===']'){i++;return out;}while(true){out.push(value(depth+1));if(text[i]===']'){i++;return out;}need(text[i++ ]===',','JSON array delimiter');}}
    for(const [token,result] of [['true',true],['false',false],['null',null]])if(text.startsWith(token,i)){i+=token.length;return result;}
    const m=/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(text.slice(i));need(m,'JSON number');i+=m[0].length;
    const word=m[0];if(!/[.eE]/.test(word)){const n=BigInt(word);return n>BigInt(Number.MAX_SAFE_INTEGER)||n<BigInt(Number.MIN_SAFE_INTEGER)?n:Number(word);}
    const n=Number(word);need(Number.isFinite(n),'nonfinite JSON');return n;
  };
  const out=value();need(i===text.length-1,'JSON trailing bytes');return {value:out,tokens:rootTokens,text};
}
function native(raw){
  const text=raw.toString('ascii');
  const times=[...text.matchAll(/^\s*([0-9.]+)\s+real\s+([0-9.]+)\s+user\s+([0-9.]+)\s+sys\s*$/gm)];
  const peaks=[...text.matchAll(/^\s*(\d+)\s+maximum resident set size\s*$/gm)];
  need(times.length===1&&peaks.length===1,'ambiguous Darwin profile');
  const [wall_seconds,user_seconds,system_seconds]=times[0].slice(1).map(Number),rss_bytes=Number(peaks[0][1]);
  need([wall_seconds,user_seconds,system_seconds].every(finite)&&posint(rss_bytes),'native units/values');
  return {wall_seconds,user_seconds,system_seconds,rss_bytes};
}
function timer(t,pid,exit){
  need(t.pid===pid&&t.exit_code===exit&&t.statistics_source==='os.wait4'&&t.wall_source==='controller_monotonic_observed'&&t.rss_unit==='bytes','timer wait4 PID/exit/source/units');
  need(t.source==='parent os.wait4 native exit rusage; possible descendant aggregation','timer source');
  need(['wall_seconds','user_seconds','system_seconds'].every(k=>finite(t.native[k]))&&posint(t.native.rss_bytes),'timer rusage');return t.native.rss_bytes;
}
export function validateDispatch(contract,role,label,e){
  const sha=e.contract_sha256,shared=['reservation','reader-ack'].includes(label);
  const spec=shared?contract.shared_helpers[role][label]:contract.roles[role].native_dispatch[label];
  const argv=resolve(shared?spec.argv:contract.roles[role].exit_argv[label],sha),da=resolve(spec.dispatch_argv,sha);
  const event=e.event,parsed=lossless(e.dispatch,true),r=parsed.value,span=event.end_seconds-event.start_seconds;
  need(eq(argv.slice(0,4),['/usr/bin/time','-l','-o',spec.profile_path])&&spec.timeout_seconds>0&&spec.timeout_seconds<=contract.roles[role].FULL_seconds,'registered native prefix/timeout');
  need(event.complete===true&&event.actual_tool_exit_code===0&&event.exit_code===0&&event.dispatcher_exit===0&&finite(event.start_seconds)&&finite(event.end_seconds)&&span>=0,'actual tool return missing');
  need(eq(event.argv,argv)&&eq(event.dispatch_argv,da)&&event.dispatch_stdout===e.dispatch.toString('ascii')&&event.dispatch_stdout_sha256===hash(e.dispatch),'actual argv/raw stdout anchor');
  need(event.stdout_sha256===hash(e.log)&&event.profile_sha256===hash(e.profile),'actual log/profile anchor');
  need(r.schema==='topolab.v2.m2-native-dispatch.v1'&&r.execution_identity===ID&&r.contract_sha256===sha&&r.role===role&&r.label===label&&eq(r.argv,argv)&&eq(r.dispatch_argv,da),'dispatch identity');
  need(r.status==='COMPLETED_WITH_NATIVE_RETURN'&&r.exit_code===0&&r.group_gone===true&&eq(r.cleanup_errors,[])&&eq(r.descendant_groups,[])&&r.watchdog_helper===null,'dispatch outcome/coverage');
  need(r.log_sha256===hash(e.log)&&r.profile_sha256===hash(e.profile),'dispatch hashes');
  need(r.python_entry===contract.runtime.python_entry&&eq(r.startup_orig_argv,[contract.runtime.python_startup_entry,...da.slice(1)]),'raw startup argv');
  need(eq(r.self_rss_phases,['pre_preview_write','post_preview_write_pre_final_serialization'])&&r.self_rss_scope==='empirical before/after retained preflush packet; final serializer closed externally','self RSS boundary');
  const previewEdits=[{start:parsed.tokens.preflush_sha256.memberStart,end:parsed.tokens.preflush_sha256.end+1,value:''},{start:parsed.tokens.self_rss_bytes_after_flush.start,end:parsed.tokens.self_rss_bytes_after_flush.end,value:'null'}].sort((a,b)=>b.start-a.start);
  let preview=parsed.text;for(const edit of previewEdits)preview=preview.slice(0,edit.start)+edit.value+preview.slice(edit.end);
  need(Buffer.from(preview,'ascii').equals(e.preflush)&&hash(e.preflush)===r.preflush_sha256,'raw preflush identity');
  const c=r.cleanup;need(c.group_gone===true&&c.final_group_gone===true&&c.leader_exit===0&&c.observation_limit_exceeded===false&&eq(c.signals,[])&&c.observations.length>0&&c.observations.at(-1).group_gone===true&&c.observations.at(-1).leader_exit===0,'dispatch cleanup');
  need(r.stdout_observed_bytes===e.log.length&&r.stdout_retained_bytes===e.log.length&&r.stdout_observed_truncated_bytes===0&&r.unobserved_stdout_after_cap==='NOT_TRUNCATED','stdout completeness');
  const f=r.native_log_facts;need(eq(f.declared,f.before)&&eq(f.before,f.after)&&eq(f.after,f.closing)&&f.returned_bytes===e.log.length&&f.declared.st_size===e.log.length&&f.declared.st_nlink===1&&(f.declared.st_mode&0o170000)===0o100000&&f.path===spec.log_path,'raw source tuples');
  need(posint(r.pid)&&posint(r.native_pid)&&r.pid!==r.native_pid&&posint(r.self_rss_bytes_before_flush)&&posint(r.self_rss_bytes_after_flush)&&r.self_rss_bytes_after_flush>=r.self_rss_bytes_before_flush,'dispatch PID/self peak');
  need(typeof r.started_unix_ns==='bigint'&&typeof r.returned_unix_ns==='bigint'&&r.started_unix_ns<=r.returned_unix_ns,'raw ns type/order');
  const measured=native(e.profile),timerRSS=timer(r.timer_native_exit,r.native_pid,0);
  need(event.start_seconds-1<=Number(r.started_unix_ns)/1e9&&Number(r.returned_unix_ns)/1e9<=event.end_seconds+1&&finite(r.elapsed_seconds)&&r.elapsed_seconds<=span+1&&r.elapsed_seconds<=spec.timeout_seconds+10&&measured.wall_seconds<=r.elapsed_seconds+1&&r.timer_native_exit.native.wall_seconds<=r.elapsed_seconds+1,'dispatch actual wall');
  const peak=measured.rss_bytes+timerRSS+Math.max(r.self_rss_bytes_before_flush,r.self_rss_bytes_after_flush);need(peak<=CAP,'outer native resource cap');
  return {role,label,peak_bytes:peak,command_rss_bytes:measured.rss_bytes,timer_rss_bytes:timerRSS,self_rss_bytes:Math.max(r.self_rss_bytes_before_flush,r.self_rss_bytes_after_flush),elapsed_seconds:r.elapsed_seconds,active_charge_seconds:span+1,dispatch_sha256:hash(e.dispatch),event,record:r,native:measured};
}

export function validateAck(v,sha,role,pendingRaw=null){
  need(v.execution_identity===ID&&v.scientific_contract_sha256===sha&&v.role===role&&v.status==='SCIENTIFIC_READER_RETURN_ACKNOWLEDGED'&&v.lease_state==='RELEASED'&&v.consumer_actual_exit_observed===true&&/^[0-9a-f]{64}$/.test(v.reader_receipt_sha256),'actual reader ACK identity/RELEASED');
  if(pendingRaw!==null)need(v.reader_receipt_sha256===hash(pendingRaw),'ACK exact raw pending receipt hash');
}
function auditInner(r,profile,log,helpers,expected,contract,sha){
  need(r.schema==='topolab.v2.m2-native-rss-exit-assurance.v1'&&r.software_only===true&&r.platform==='darwin'&&r.status==='PENDING_POSTEXIT'&&r.controller_complete_exit==='UNKNOWN_PENDING_OUTER_PROFILE'&&r.scientific_resource_admission==='NOT_RUN','inner disclosed assurance scope');
  need(r.role===expected.name&&eq(r.argv,resolve(expected.argv,sha))&&r.timeout_seconds===expected.timeout_seconds&&r.exit_code===expected.expected_exit_code&&r.software_result===expected.expected_status&&r.limit_bytes===CAP,'inner exact calls/outcomes');
  need(r.cwd===contract.runtime.cwd&&r.controller_python===contract.runtime.python_entry&&r.lock_sha256===contract.runtime.lock_sha256&&eq(r.thread_environment,contract.runtime.threads)&&r.ps_rss_unit==='KiB*1024'&&r.native_rss_unit==='bytes','inner runtime/units');
  const n=native(profile);need(r.profile_sha256===hash(profile)&&r.log_sha256===hash(log)&&eq(r.native,n),'inner raw profile/log');
  need(r.cleanup.group_gone===true&&r.cleanup.leader_exit===r.exit_code&&r.samples.length>0&&r.samples.length===r.helpers.length&&posint(r.controller_rss_peak_bytes)&&finite(r.observed_outer_wall_seconds)&&r.target_sample_interval_seconds>0&&r.target_sample_interval_seconds<=.5,'inner sampler/cleanup');
  const commandTimer=timer(r.timer_native_exit,r.pid,r.exit_code);let previous=null,helperPeak=0,peak=n.rss_bytes;
  r.helpers.forEach((h,i)=>{
    const raw=helpers[h.profile],hn=native(raw),s=r.samples[i];
    need(h.role==='rss-sampler-'+i&&h.profile_sha256===hash(raw)&&eq(h.native,hn)&&h.exit_code===0&&h.problem===null&&h.cleanup.group_gone===true&&h.cleanup.leader_exit===0,'inner sampler native/cleanup');
    const helperTimer=timer(h.timer_native_exit,h.pid,0),hp=hn.rss_bytes+helperTimer;helperPeak=Math.max(helperPeak,hp);
    need(finite(s.offset_seconds)&&s.offset_seconds<=r.observed_outer_wall_seconds&&((previous===null&&s.actual_interval_seconds===null)||(previous!==null&&s.offset_seconds>=previous&&Math.abs(s.actual_interval_seconds-(s.offset_seconds-previous))<=1e-12)),'inner actual sample intervals');previous=s.offset_seconds;
    need(posint(s.controller_rss_bytes)&&s.controller_rss_bytes<=r.controller_rss_peak_bytes&&Array.isArray(s.roles),'inner controller sample');
    const pids=new Set();let sum=0;for(const row of s.roles){need(posint(row.pid)&&!pids.has(row.pid)&&Number.isSafeInteger(row.parent)&&Number.isSafeInteger(row.pgid)&&Number.isSafeInteger(row.rss_bytes)&&row.rss_bytes>=0,'inner process tuple');pids.add(row.pid);sum+=row.rss_bytes;}
    if(r.exit_code===0)need(s.roles.length<=2&&s.roles.every(row=>row.pgid===r.pid&&(row.pid===r.pid||row.parent===r.pid)),'inner unregistered descendants');
    need(s.group_plus_controller_rss_bytes===sum+s.controller_rss_bytes,'inner group RSS arithmetic');peak=Math.max(peak,s.group_plus_controller_rss_bytes+hp);
  });
  const overlap=n.rss_bytes+commandTimer+r.controller_rss_peak_bytes+helperPeak;need(r.native_plus_controller_and_sampler_rss_bytes===overlap,'inner overlap arithmetic');peak=Math.max(peak,overlap);
  if(r.exit_code===0)need(peak<=CAP&&r.observed_outer_wall_seconds<=r.timeout_seconds&&r.escaped_group_cleanup.every(x=>x.group_gone===true),'inner actual successful cap');
  need(peak<=CAP,'inner native resource cap');return {peak_bytes:peak,wall_seconds:r.observed_outer_wall_seconds};
}



const SHA256 = /^[0-9a-f]{64}$/;
const HARD_LIMITS = Object.freeze({
  max_files:65536, max_total_bytes:512*1024**2,
  max_record_bytes:128*1024**2, max_log_bytes:4*1024**2,
  max_profile_bytes:1024**2, max_manifest_bytes:16*1024**2,
  max_contract_bytes:4*1024**2,
});
function absolute(path) {
  need(typeof path==='string'&&path.startsWith('/')&&!path.split('/').slice(1).some(p=>!p||p==='.'||p==='..'),'literal absolute metadata path required');
  return path;
}
function tuple(st) {
  if(!st)return null;
  return {dev:String(st.dev),inode:String(st.ino),size:String(st.size),mtime_ns:String(st.mtimeNs),mode:String(st.mode),nlink:String(st.nlink)};
}
const sameTuple = (a,b) => a&&b&&['dev','ino','size','mtimeNs','mode','nlink'].every(k=>a[k]===b[k]);
function reader({fs,constants},limits) {
  const cache=new Map(),observations=[];let total=0;
  async function read(path,expected,cap) {
    absolute(path);need(SHA256.test(expected),'trusted SHA256 anchor required');
    if(cache.has(path)){const prior=cache.get(path);need(prior.sha256===expected&&prior.raw.length<=cap,'cached metadata anchor/cap changed');return prior.raw;}
    need(cache.size<limits.max_files,'metadata file count cap');
    const evidence={path,declared:null,before:null,after:null,closing:null,returned_bytes:0,eof_probe_bytes:null,sha256:null,secondary_errors:[]};
    let declared,before,after,closing,h,raw,problem=null;
    const secondary=(stage,error)=>evidence.secondary_errors.push({stage,error_type:error.name,reason:error.message});
    try {
      let parent='';for(const item of path.split('/').slice(1,-1)){
        parent+='/'+item;const st=await fs.lstat(parent,{bigint:true});need(st.isDirectory()&&!st.isSymbolicLink(),'symlink/non-directory metadata parent');
      }
      declared=await fs.lstat(path,{bigint:true});evidence.declared=tuple(declared);
      need(declared.isFile()&&!declared.isSymbolicLink()&&declared.nlink===1n,'metadata path type/single-link');
      h=await fs.open(path,constants.O_RDONLY|constants.O_NOFOLLOW|constants.O_NONBLOCK);
      before=await h.stat({bigint:true});evidence.before=tuple(before);
      need(before.isFile()&&before.nlink===1n&&sameTuple(declared,before),'metadata initial FD identity');
      need(before.size>=0n&&before.size<=BigInt(cap)&&total+Number(before.size)<=limits.max_total_bytes,'metadata file/total byte cap');
      raw=Buffer.alloc(Number(before.size));
      while(evidence.returned_bytes<raw.length){
        const offset=evidence.returned_bytes,part=await h.read(raw,offset,raw.length-offset,offset);
        need(Number.isSafeInteger(part.bytesRead)&&part.bytesRead>0&&part.bytesRead<=raw.length-offset,'metadata short read');
        evidence.returned_bytes+=part.bytesRead;
      }
      const extra=Buffer.alloc(1);evidence.eof_probe_bytes=(await h.read(extra,0,1,raw.length)).bytesRead;need(evidence.eof_probe_bytes===0,'metadata grew');
      after=await h.stat({bigint:true});evidence.after=tuple(after);need(sameTuple(before,after),'metadata fstat identity drift');
      evidence.sha256=hash(raw);need(evidence.sha256===expected,'metadata anchor mismatch');
    } catch(error){problem=error;}
    finally {
      if(h)try{await h.close();}catch(error){secondary('close',error);problem??=Error('metadata close failed');}
      if(declared)try{closing=await fs.lstat(path,{bigint:true});evidence.closing=tuple(closing);if(!sameTuple(before||declared,closing)){const drift=Error('metadata closing path identity drift');if(problem)secondary('closing_identity',drift);else problem=drift;}}
      catch(error){secondary('closing',error);problem??=Error('metadata closing observation unavailable');}
    }
    if(problem){problem.metadata_evidence=evidence;problem.prior_metadata_observations=observations;throw problem;}
    total+=raw.length;observations.push(evidence);cache.set(path,{raw,sha256:expected});return raw;
  }
  return {read,observations,get bytes(){return total;},get files(){return cache.size;},cache};
}
function policyFor(contract,options) {
  need(['B','FINAL'].includes(options.scope),'registered metadata scope required');
  const publicOnly=contract.public_fixture_only===true;
  need(publicOnly||options.publicFixturePolicy===undefined,'formal contract forbids public policy override');
  const policy=publicOnly&&options.publicFixturePolicy?options.publicFixturePolicy:contract.api_metadata;
  need(policy?.schema==='topolab.v2.m2-api-metadata-policy.v1','frozen API metadata policy required');
  absolute(policy.root);
  need(policy.manifests?.[options.scope]===options.manifestPath,'unregistered metadata manifest path');
  need(policy.sample_interval_seconds===0.5,'frozen metadata sampler interval required');
  need(eq(Object.keys(policy.limits).sort(),Object.keys(HARD_LIMITS).sort()),'complete metadata limit fields required');
  for(const [key,ceiling] of Object.entries(HARD_LIMITS))need(posint(policy.limits[key])&&policy.limits[key]<=ceiling,'metadata policy hard cap: '+key);
  need(contract.execution_identity===ID&&contract.runtime?.platform==='darwin'&&contract.resource_limit_bytes===CAP&&contract.shared_FULL_seconds===180,'scientific metadata identity/resource/shared scope');
  if(!publicOnly)need(contract.permissions?.B===true&&contract.permissions?.C===true&&SHA256.test(contract.source_freeze?.['scripts/p17_m2_scientific_metadata.mjs']),'formal metadata observer source/adoption required');
  return {policy,publicOnly};
}
function namespaceFor(contract,policy,selected) {
  const fixed=new Map(),families=[];
  const relative=p=>{absolute(p);need(p.startsWith(policy.root+'/'),'registered metadata path escaped root');return p.slice(policy.root.length+1);};
  const add=(p,cap)=>{
    const rel=relative(p);need(!fixed.has(rel)||fixed.get(rel)===cap,'metadata member bound conflict');fixed.set(rel,cap);return rel;
  };
  const rootFor=role=>{const p=absolute(contract.roles[role].root);relative(p+'/x');return p;};
  for(const role of selected){
    const spec=contract.roles[role],root=rootFor(role),full={'resource-preflight':180,'scientific-producer':10800,'scientific-auditor':3600}[role];
    need(spec.FULL_seconds===full&&spec.inner_starts.length===(role==='resource-preflight'?3:1),'fixed role FULL/start count');
    for(const label of ['reservation',...labels,...(role==='resource-preflight'?[]:['reader-ack'])]){
      const item=['reservation','reader-ack'].includes(label)?contract.shared_helpers[role][label]:spec.native_dispatch[label];
      add(item.dispatch_path,policy.limits.max_record_bytes);add(item.dispatch_path.replace(/\.json$/,'-preflush.json'),policy.limits.max_record_bytes);
      add(item.profile_path,policy.limits.max_profile_bytes);add(item.log_path,policy.limits.max_log_bytes);
      add(root+'/'+label+'-return.json',policy.limits.max_record_bytes);
    }
    for(const file of ['quota-pending.json','controller-summary.json','case-spans.json','controller-exit.json','binder-exit.json','verifier-exit.json'])add(root+'/'+file,policy.limits.max_record_bytes);
    if(!contract.public_fixture_only){
      add(root+'/trusted-returns.json',policy.limits.max_record_bytes);
      add(spec.publication_readiness_path,policy.limits.max_record_bytes);
      add(spec.publication_return_path,policy.limits.max_record_bytes);
    }
    for(const start of spec.inner_starts){
      need(/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(start.name)&&posint(start.timeout_seconds)&&start.timeout_seconds<=full,'registered inner metadata name/timeout');
      const base=root+(role==='resource-preflight'?'/controls/':'/native/')+start.name;
      add(base+'/command.json',policy.limits.max_record_bytes);add(base+'/command.time',policy.limits.max_profile_bytes);add(base+'/command.log',policy.limits.max_log_bytes);
      families.push({prefix:relative(base)+'/sampler-',max_index:Math.ceil(start.timeout_seconds/policy.sample_interval_seconds)+1,cap:policy.limits.max_profile_bytes});
    }
  }
  const capFor=rel=>{
    need(typeof rel==='string'&&!rel.startsWith('/')&&!rel.split('/').some(x=>!x||x==='.'||x==='..'),'metadata member path syntax');
    if(fixed.has(rel))return fixed.get(rel);
    for(const family of families)if(rel.startsWith(family.prefix)){
      const tail=rel.slice(family.prefix.length),match=/^(0|[1-9]\d*)\.time$/.exec(tail);
      if(match&&Number.isSafeInteger(Number(match[1]))&&Number(match[1])<=family.max_index)return family.cap;
    }
    fail('unregistered metadata member: '+rel);
  };
  return {relative,rootFor,fixed,capFor};
}
// Exact metadata population emitted by frozen independent assess_panel().
// These fields establish completeness; numerical analysis remains in that auditor.
const SCIENTIFIC_PREDICATES=[
  'fixed_H17_zero_failed_attempts_and_fallbacks',
  'all_seven_historical_target_predicates_repaired',
  'historical_49_P_acceptances_preserved',
  'matched_plain_P_and_P_keep_acceptances_preserved',
  'two_old_small_z_negative_failures_retained',
  'fixed_plain_P17_counterexample_retained',
  'primary_target_mean_and_sum_at_most_one',
  'primary_strictly_better_fixed_controls',
  'primary_better_than_W17',
  'primary_each_scale_mean_and_sum_at_most_point_nine',
  'at_least_two_H_seeds_and_fixed_H17_pass',
];
const SCIENTIFIC_METHODS=['uniform','physics_heuristic','nearest_neighbor','C/17','C/29','C/43','P-keep/17','P-keep/29','P-keep/43','W/17','W/29','W/43','plain-P/17','plain-P/29','plain-P/43','H/17','H/29','H/43','uniform-homotopy'];
const SCIENTIFIC_METRICS=Object.fromEntries([
  ['H17_target',13],...SCIENTIFIC_METHODS.map(method=>[method,18]),
  ...[17,29,43].flatMap(seed=>[['H/'+seed+':(12, 6, 3)',3],['H/'+seed+':(24, 12, 6)',15]]),
]);
function validateDecisionEvidence(decision) {
  need(decision&&decision.predicates&&eq(Object.keys(decision.predicates).sort(),[...SCIENTIFIC_PREDICATES].sort())&&Object.values(decision.predicates).every(x=>typeof x==='boolean'),'complete fixed eleven scientific predicates required');
  need(decision.metrics&&eq(Object.keys(decision.metrics).sort(),Object.keys(SCIENTIFIC_METRICS).sort()),'complete fixed scientific metric population required');
  for(const [key,population] of Object.entries(SCIENTIFIC_METRICS)) {
    const metric=decision.metrics[key];
    need(metric&&eq(Object.keys(metric).sort(),['failed_attempts','mean_ratio','sum_ratio'])&&finite(metric.mean_ratio)&&finite(metric.sum_ratio)&&Number.isSafeInteger(metric.failed_attempts)&&metric.failed_attempts>=0&&metric.failed_attempts<=population,'finite scientific metric fields/population bound: '+key);
  }
  const seedKeys=['H/17','H/29','H/43'];
  need(decision.seed_gate_results&&eq(Object.keys(decision.seed_gate_results).sort(),seedKeys)&&Object.values(decision.seed_gate_results).every(value=>typeof value==='boolean'),'complete three independent seed gate results required');
  const passing=[17,29,43].filter(seed=>decision.seed_gate_results['H/'+seed]);
  need(eq(decision.passing_H_seeds,passing),'passing seed population must equal independent seed gate results');
  need(decision.predicates.at_least_two_H_seeds_and_fixed_H17_pass===(passing.length>=2&&passing.includes(17)),'fixed H17 and two independent seed predicate consistency');
  need(decision.resource_and_actual_return==='NOT_ESTABLISHED_BY_METRIC_ARITHMETIC','scientific metric resource/actual-return boundary required');
}
export function validateScientificResult(contract,sha,role,payload,expected) {
  need(role==='scientific-producer'||role==='scientific-auditor','scientific metadata result role');
  const actual=payload.actual_numerical_runtime;
  need(actual?.python_entry===contract.runtime.python_entry&&eq(actual.startup_orig_argv,[contract.runtime.python_startup_entry,...resolve(expected.argv,sha).slice(1)])&&eq(actual.torch_threads,contract.runtime.torch_threads_policy),'actual scientific returned runtime');
  const value=payload.result;
  need(value?.execution_identity===ID&&value.scientific_contract_sha256===sha&&value.attempted_rows===360&&finite(value.internal_row_charge_seconds),'independent scientific result identity/complete rows');
  if(role==='scientific-producer'){
    need(value.schema==='topolab.v2.m2-scientific-producer-summary.v1'&&value.status==='PRODUCER_PANEL_COMPLETE_PENDING_INDEPENDENT_AUDIT'&&value.software_only===false&&Array.isArray(value.rows)&&value.rows.length===360&&value.seed17_repaired==='NOT_ESTABLISHED_BY_PRODUCER','producer result is not an acceptance oracle');
    const order=[...contract.call_plan.references.map(row=>['reference',row]),...contract.call_plan.queries.map(row=>['query',row])];
    need(contract.call_plan.references.length===18&&contract.call_plan.queries.length===342,'fixed scientific call population');
    value.rows.forEach((row,i)=>{const [phase,want]=order[i];need(row.phase===phase&&row.ordinal===want.ordinal&&row.case_id===want.case_id&&row.method===want.method,'producer complete ordered descriptor population');});
    return {status:value.status,scientific_predicates_passed:null,seed17_repaired:false};
  }
  need(value.schema==='topolab.v2.m2-scientific-auditor-summary.v1'&&value.completed_rows===360&&value.seed17_repaired==='NOT_ESTABLISHED_BEFORE_OWN_NATIVE_RETURN'&&value.own_resource_and_actual_exit==='PENDING_INDEPENDENT_NATIVE_OUTER_RETURN','independent result pending own native return');
  const decision=value.decision;
  validateDecisionEvidence(decision);
  const failed=Object.keys(decision.predicates).filter(key=>decision.predicates[key]===false);
  need(Array.isArray(decision.failed_predicates)&&eq([...failed].sort(),[...decision.failed_predicates].sort())&&decision.scientific_predicates_passed===(failed.length===0),'independent decision/failed predicates consistency');
  const status=!decision.predicates.fixed_plain_P17_counterexample_retained?'STOP_ROUTE_NOT_ISOLATED':failed.length?'FAIL_SCIENCE_GATE':'SCIENTIFIC_PREDICATES_PASS_PENDING_NATIVE_EXIT';
  need(value.status===status&&decision.outcome_status===status,'independent scientific outcome status');
  if(!failed.length)need(Array.isArray(decision.passing_H_seeds)&&decision.passing_H_seeds.includes(17)&&decision.passing_H_seeds.length>=2&&new Set(decision.passing_H_seeds).size===decision.passing_H_seeds.length&&decision.passing_H_seeds.every(seed=>[17,29,43].includes(seed)),'fixed H17 and at least two independent seed predicates required');
  return {status,scientific_predicates_passed:failed.length===0,failed_predicates:decision.failed_predicates,passing_H_seeds:decision.passing_H_seeds,metrics:decision.metrics,predicates:decision.predicates,seed_gate_results:decision.seed_gate_results,resource_and_actual_return:decision.resource_and_actual_return,seed17_repaired:false};
}
function rawField(parsed,key) {
  const range=parsed.tokens[key];need(range,'required raw metadata field: '+key);
  return Buffer.from(parsed.text.slice(range.start,range.end)+'\n','ascii');
}
export async function auditPublication(contract,sha,role,chain,get,relative,contractFields) {
  const spec=contract.roles[role],proofRaw=await get(relative(spec.publication_readiness_path));
  const proof=lossless(proofRaw,true).value,event=lossless(await get(relative(spec.publication_return_path))).value;
  const reservation=lossless(chain.reservation.log).value;
  need(proof.execution_identity===ID&&proof.scientific_contract_sha256===sha&&proof.role===role&&proof.metadata_only===true&&typeof proof.publication_readiness?.main==='string'&&/^[0-9a-f]{40}$/.test(proof.publication_readiness.main),'publication identity/main');
  need(proof.source_freeze_sha256===hash(contractFields.source_freeze)&&proof.runtime_sha256===hash(contractFields.runtime),'publication source/runtime binding');
  need(event.complete===true&&event.exit_code===0&&eq(event.argv,resolve(spec.publication_argv,sha))&&event.stdout_sha256===hash(proofRaw)&&finite(event.start_seconds)&&finite(event.end_seconds)&&finite(proof.start_seconds)&&finite(proof.end_seconds)&&event.start_seconds<=proof.start_seconds&&proof.start_seconds<=proof.end_seconds&&proof.end_seconds<=event.end_seconds&&event.end_seconds<=chain.reservation.event.start_seconds&&chain.reservation.event.start_seconds<=event.end_seconds+30,'actual fresh publication return before native reservation');
  need(eq(reservation.publication_readiness,proof)&&chain.reservation.event.publication_readiness_sha256===hash(proofRaw),'reservation publication proof anchor');
}
export async function observeMetadata(options) {
  need(SHA256.test(options.contractSHA256)&&SHA256.test(options.manifestSHA256),'trusted SHA256 anchor required');
  configure(options.crypto);const started=Date.now(),operationLimits={...HARD_LIMITS},source=reader(options,operationLimits);
  try {
    const contractRaw=await source.read(options.contractPath,options.contractSHA256,HARD_LIMITS.max_contract_bytes),contractParsed=lossless(contractRaw,true),contract=contractParsed.value,sha=options.contractSHA256;
    need(contract.schema==='topolab.v2.m2-scientific-contract.v1','scientific metadata contract schema');
    const {policy,publicOnly}=policyFor(contract,options),selected=options.scope==='B'?roles.slice(0,1):roles;
    const contractFields=publicOnly?null:{runtime:rawField(contractParsed,'runtime'),source_freeze:rawField(contractParsed,'source_freeze')};
    need(contractRaw.length<=policy.limits.max_contract_bytes&&source.files<=policy.limits.max_files&&source.bytes<=policy.limits.max_total_bytes,'metadata policy bootstrap cap');
    Object.assign(operationLimits,policy.limits);
    const namespace=namespaceFor(contract,policy,selected),{relative,rootFor}=namespace;
    const manifestRaw=await source.read(options.manifestPath,options.manifestSHA256,policy.limits.max_manifest_bytes),manifest=lossless(compactLexemes(manifestRaw)).value;
    need(source.files<=policy.limits.max_files&&source.bytes<=policy.limits.max_total_bytes,'metadata policy initial cap');
    need(manifest.schema==='topolab.v2.m2-api-metadata-manifest.v1'&&manifest.scope===options.scope&&manifest.contract_sha256===sha&&manifest.files&&typeof manifest.files==='object'&&!Array.isArray(manifest.files),'exact metadata operation manifest binding');
    need(Object.keys(manifest.files).length+2<=policy.limits.max_files,'metadata manifest file count cap');
    for(const [rel,item] of Object.entries(manifest.files)){
      const cap=namespace.capFor(rel);
      need(eq(Object.keys(item).sort(),['bytes','sha256'])&&Number.isSafeInteger(item.bytes)&&item.bytes>=0&&item.bytes<=cap&&SHA256.test(item.sha256),'metadata manifest member hash/byte cap');
    }
    need([...namespace.fixed.keys()].every(rel=>Object.hasOwn(manifest.files,rel)),'missing registered metadata member');
    let declaredTotal=contractRaw.length+manifestRaw.length;
    for(const item of Object.values(manifest.files))declaredTotal+=item.bytes;
    need(Number.isSafeInteger(declaredTotal)&&declaredTotal<=policy.limits.max_total_bytes,'metadata manifest total byte cap');
    const consumed=new Set(),get=async rel=>{
      const cap=namespace.capFor(rel);need(Object.hasOwn(manifest.files,rel),'unregistered metadata file: '+rel);
      const item=manifest.files[rel],raw=await source.read(policy.root+'/'+rel,item.sha256,cap);
      need(raw.length===item.bytes,'manifest byte size mismatch');consumed.add(rel);return raw;
    };
    const dispatches=[],byRole={},shared=[],payloads={},outcomes={},rolePeaks={},roleCharges={},innerResults={};let lastEnd=0,innerProfiles=0;
    for(const role of selected){
      const root=rootFor(role),chain=byRole[role]={};
      for(const label of ['reservation',...labels,...(role==='resource-preflight'?[]:['reader-ack'])]){
        const spec=['reservation','reader-ack'].includes(label)?contract.shared_helpers[role][label]:contract.roles[role].native_dispatch[label];
        const event=lossless(await get(relative(root+'/'+label+'-return.json'))).value;
        const evidence={contract_sha256:sha,event,dispatch:await get(relative(spec.dispatch_path)),preflush:await get(relative(spec.dispatch_path.replace(/\.json$/,'-preflush.json'))),profile:await get(relative(spec.profile_path)),log:await get(relative(spec.log_path))};
        const proof=validateDispatch(contract,role,label,evidence);proof.log=evidence.log;
        need(lastEnd<=event.start_seconds,'actual registered command order/overlap');lastEnd=event.end_seconds;
        chain[label]=proof;dispatches.push(proof);
        if(label==='reservation'||label==='reader-ack'){
          const output=lossless(evidence.log,true).value;
          need(output.execution_identity===ID&&output.scientific_contract_sha256===sha&&output.role===role,'shared returned identity');
          if(label==='reservation'){
            need(output.status==='CONSUMED_BEFORE_CONTROLLER_INTERPRETER'&&output.FULL_seconds===contract.roles[role].FULL_seconds&&output.began_UTC_seconds>=event.start_seconds&&output.began_UTC_seconds<=event.end_seconds,'reservation outcome/time');
            const pending=await get(relative(root+'/quota-pending.json'));
            need(evidence.log.equals(pending)&&(publicOnly||event.pending_sha256===hash(pending)),'reservation pending raw bytes/actual return anchor');
          }else validateAck(output,sha,role);
          shared.push(proof);
        }
      }
      if(!publicOnly){
        const events=lossless(await get(relative(root+'/trusted-returns.json'))).value;
        need(eq(events,labels.map(label=>chain[label].event)),'complete role trusted-return table');
        await auditPublication(contract,sha,role,chain,get,relative,contractFields);
      }
      let priorRaw=await get(relative(root+'/controller-summary.json'));
      need(priorRaw.equals(chain.controller.log),'controller summary actual raw log');
      const summary=lossless(priorRaw,true).value,spansRaw=await get(relative(root+'/case-spans.json')),spans=lossless(spansRaw).value;
      need(summary.execution_identity===ID&&summary.scientific_contract_sha256===sha&&summary.role===role&&summary.status==='PENDING_POSTEXIT'&&summary.case_spans_sha256===hash(spansRaw)&&spans.length===contract.roles[role].inner_starts.length,'inner summary identity/span anchor/count');
      let innerEnd=chain.controller.event.start_seconds;const recordLexemes=[],peaks=[];innerResults[role]=[];
      for(let index=0;index<contract.roles[role].inner_starts.length;index++){
        const expected=contract.roles[role].inner_starts[index],base=root+(role==='resource-preflight'?'/controls/':'/native/')+expected.name;
        const raw=await get(relative(base+'/command.json')),compact=compactLexemes(raw),record=lossless(compact).value;
        need(Array.isArray(record.helpers)&&record.helpers.length>0&&record.helpers.length<=Math.ceil(expected.timeout_seconds/policy.sample_interval_seconds)+2&&record.target_sample_interval_seconds===policy.sample_interval_seconds,'fixed sampler count/interval');
        const helpers=Object.create(null);
        for(let i=0;i<record.helpers.length;i++){
          const helper=record.helpers[i];need(helper.profile==='sampler-'+i+'.time','exact sampler helper index order');
          helpers[helper.profile]=await get(relative(base+'/'+helper.profile));innerProfiles++;
        }
        const profile=await get(relative(base+'/command.time')),log=await get(relative(base+'/command.log'));
        const inner=auditInner(record,profile,log,helpers,expected,contract,sha),span=spans[index];
        need(span.name===expected.name&&span.group_gone===true&&finite(span.start_seconds)&&finite(span.end_seconds)&&innerEnd<=span.start_seconds&&span.start_seconds<=span.end_seconds&&span.end_seconds<=chain.controller.event.end_seconds&&span.end_seconds-span.start_seconds+.001>=inner.wall_seconds,'inner disjoint actual lifetime');innerEnd=span.end_seconds;
        recordLexemes.push(compact.toString('ascii').slice(0,-1));peaks.push(inner.peak_bytes);innerResults[role].push({name:expected.name,...inner});
        if(role!=='resource-preflight'){
          const payloadParsed=lossless(log,true),payload=payloadParsed.value;payloads[role]=payload;
          const pending=payload.reader_pending,pendingRaw=rawField(payloadParsed,'reader_pending'),ack=lossless(chain['reader-ack'].log,true).value;
          validateAck(ack,sha,role,pendingRaw);
          need(pending.schema==='topolab.v2.m2-scientific-reader-lease.v1'&&pending.status==='PENDING_ACTUAL_OUTER_RETURN'&&pending.execution_identity===ID&&pending.role===role&&pending.root===contract.acquisition.content_root&&pending.version_id===contract.acquisition.version_id&&pending.lease_path===contract.acquisition.content_root+'.cooperative-reader.lease'&&pending.independent_source_sha256===contract.source_freeze['scripts/p17_m2_scientific_independent.py'],'pending reader identity/accepted input/source');
          need(pending.scope===(publicOnly?'NEW_PUBLIC_SCIENTIFIC_INTEGRATION_ONLY':'SCIENTIFIC_SOURCE_ATTESTED_FIXED_P17')&&eq(pending.consumer_orig_argv,[contract.runtime.python_startup_entry,...resolve(expected.argv,sha).slice(1)])&&record.samples.some(sample=>sample.roles.some(row=>row.pid===pending.consumer_pid)),'pending reader scope/startup/observed consumer PID');
          if(publicOnly){
            need(payload.schema==='topolab.v2.m2-public-scientific-reader.v1'&&payload.result.status==='PUBLIC_SCIENTIFIC_BUFFERS_DECODED'&&payload.result.attempted_rows===0&&payload.result.member_reads===(role==='scientific-producer'?542:1070)&&payload.result.loaded_models===12&&payload.result.NN_producer_views===528&&payload.result.auditor_reanalysis===(role==='scientific-producer'?0:1056),'public actual decoder result scope');
            need(payload.actual_numerical_runtime.python_entry===contract.runtime.python_entry&&eq(payload.actual_numerical_runtime.startup_orig_argv,[contract.runtime.python_startup_entry,...resolve(expected.argv,sha).slice(1)])&&eq(payload.actual_numerical_runtime.torch_threads,contract.runtime.torch_threads_policy),'public consumer actual runtime');
          }else outcomes[role]=validateScientificResult(contract,sha,role,payload,expected);
        }
      }
      need(summary.case_records_sha256===hash(Buffer.from('['+recordLexemes.join(',')+']\n','ascii')),'raw full case-records anchor');
      rolePeaks[role]=Math.max(Math.max(...peaks)+chain.controller.peak_bytes,...labels.slice(1).map(label=>chain[label].peak_bytes),chain.reservation.peak_bytes);
      need(rolePeaks[role]<=CAP,'complete recorded role native RSS cap');
      const transitions=[['controller','PENDING_POSTEXIT','PENDING_BINDER_EXIT'],['binder','PENDING_BINDER_EXIT','PENDING_VERIFIER_EXIT'],['verifier','PENDING_VERIFIER_EXIT','PENDING_VERIFIER_EXIT']];
      for(let i=0;i<transitions.length;i++){
        const [label,priorStatus,status]=transitions[i],raw=await get(relative(root+'/'+label+'-exit.json')),binding=lossless(raw,true).value,proof=chain[label];
        need(binding.schema==='topolab.v2.m2-scientific-native-exit-binding.v1'&&binding.execution_identity===ID&&binding.scientific_contract_sha256===sha&&binding.role===role&&binding.bound_role===label&&binding.prior_status===priorStatus&&binding.status===status&&binding.record_sha256===hash(priorRaw)&&binding.profile_sha256===proof.record.profile_sha256&&binding.log_sha256===proof.record.log_sha256&&binding.exit_code===0&&binding.resource_cap_exceeded===false&&eq(binding.native,proof.native),'native three-link exit chain');
        need(raw.equals(chain[labels[i+1]].log),'native exit binding next actual stdout');priorRaw=raw;
      }
      const whole=chain['final-observer'].event.end_seconds-chain.controller.event.start_seconds;
      const outerWall=labels.reduce((sum,label)=>sum+Math.max(chain[label].native.wall_seconds,chain[label].elapsed_seconds),0);
      const internal=role==='resource-preflight'?innerResults[role].reduce((sum,item)=>sum+item.wall_seconds,0):payloads[role].result.internal_row_charge_seconds;
      const rows=role==='resource-preflight'||publicOnly?0:360,charge=Math.max(Math.max(whole,outerWall)+rows+10,internal);
      need(finite(internal)&&charge<=contract.roles[role].FULL_seconds,'complete scientific role charge exceeded');
      roleCharges[role]={FULL_charged_seconds:contract.roles[role].FULL_seconds,whole_wall_seconds:whole,inner_charge_seconds:internal,known_complete_charge_seconds:charge};
    }
    need(dispatches.length===(options.scope==='B'?5:17)&&shared.length===(options.scope==='B'?1:5),'registered native/shared helper count');
    const active=shared.reduce((sum,proof)=>sum+proof.active_charge_seconds,10);need(active<=180,'shared active FULL180 exceeded');
    need(consumed.size===Object.keys(manifest.files).length,'unconsumed metadata manifest member');
    if(!publicOnly&&options.scope==='FINAL'){
      const proof=payloads['scientific-auditor'].result.producer_return_verified,producer='scientific-producer';
      need(proof.execution_identity===ID&&proof.scientific_contract_sha256===sha&&proof.role===producer&&proof.status==='PASS_RSS_EXIT_EMPIRICAL'&&proof.actual_final_verifier_exit_observed===true&&proof.conservative_recorded_peak_bytes===rolePeaks[producer]&&Object.entries(roleCharges[producer]).every(([key,value])=>proof[key]===value),'independent producer native-return provenance');
    }
    const independent=outcomes['scientific-auditor']||null;
    return {schema:'topolab.v2.m2-api-metadata-closeout.v2',scope:publicOnly?'NEW_PUBLIC_SOFTWARE_ONLY':options.scope,operation_scope:options.scope,status:options.scope==='B'?'ACTUAL_B_NATIVE_RETURNS_VERIFIED':'ACTUAL_17_NATIVE_RETURNS_AND_FIVE_SHARED_HELPERS_VERIFIED',contract_sha256:sha,manifest_sha256:options.manifestSHA256,actual_dispatcher_commands:dispatches.length,shared_helpers:shared.length,shared_active_charge_seconds:active,shared_native_peak_bytes:Math.max(...shared.map(p=>p.peak_bytes)),conservative_recorded_peaks_by_role:rolePeaks,role_charges:roleCharges,inner_resources:innerResults,inner_sampler_native_profiles:innerProfiles,last_ack_actual_exit_observed:options.scope==='FINAL',last_ack_lease_state:options.scope==='FINAL'?'RELEASED':'NOT_APPLICABLE_B_PREFIX',exact_ns_lexemes_preserved:true,metadata_files_read:source.files,metadata_bytes_read:source.bytes,limits:policy.limits,API_transport_infrastructure_RSS:'UNKNOWN_NOT_WHOLE_HOST_4GiB',native_helper_created:false,producer_PASS_used_as_oracle:false,scientific_FEM_or_model_or_input_consumption:0,formal_B_C_calls:0,independent_scientific_outcome:independent,seed17_repaired:!publicOnly&&options.scope==='FINAL'&&independent.scientific_predicates_passed===true,full_v2_delivered:false,observer_elapsed_seconds:(Date.now()-started)/1000,observations:source.observations};
  }catch(error){error.metadata_operation={scope:options.scope,contract_sha256:options.contractSHA256,manifest_sha256:options.manifestSHA256,metadata_files_read:source.files,metadata_bytes_read:source.bytes,observations:source.observations};throw error;}
}
