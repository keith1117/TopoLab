// NEW dated20261116-only caller; reused scheduling aliases all resolve to the same three NEW roots.
// Actual original-tool boundary for the pure two-author cohort scheduler.
// The dispatcher returns its ORIGINAL request/result/true endpoint row, never a summary.
const R='/Users/keith1117/Documents/TopoLab-data/container-full60-input-admission-20261116';
const REPO='/private/tmp/topolab-input-admission-20261116';
const ROOTS=new Set(['/private/tmp/topolab-public-full60-source-acquisition-20261116-a1',...['p17-m2-local-input-version-20261116-full60-a1','p17-m2-local-input-version-20261116-full60-a2'].map(name=>'/Users/keith1117/Library/Application Support/TopoLab-custody/'+name)]);
ROOTS.add('/private/tmp/topolab-public-full60-source-acquisition-20261116-a1');
for(const name of ["p17-m2-local-input-version-20261116-full60-a1", "p17-m2-local-input-version-20261116-full60-a2"])ROOTS.add('/Users/keith1117/Library/Application Support/TopoLab-custody/'+name);
for(const root of ['/private/tmp/topolab-public-full60-source-acquisition-20261116-a1','/private/tmp/topolab-public-full60-source-acquisition-20261116-a1',...['p17-m2-local-input-version-20261116-full60-a1','p17-m2-local-input-version-20261116-full60-a2'].map(name=>'/Users/keith1117/Library/Application Support/TopoLab-custody/'+name)])ROOTS.add(root);

const V33_ROOTS=["/private/tmp/topolab-public-full60-source-acquisition-20261116-a1", "/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-20261116-full60-a1", "/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-20261116-full60-a2"];
for(const root of V33_ROOTS)ROOTS.add(root);
const V35_ROOTS=["/private/tmp/topolab-public-full60-source-acquisition-20261116-a1", "/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-20261116-full60-a1", "/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-20261116-full60-a2"];
for(const root of V35_ROOTS)ROOTS.add(root);
const PHYSICAL='/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python';
const quote=s=>"'"+s.replaceAll("'","'\"'\"'")+"'";
const word=s=>/^[A-Za-z0-9_@%+=:,./-]+$/.test(s)?s:quote(s);
export const literalCommand=argv=>'exec '+['env','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1','VECLIB_MAXIMUM_THREADS=1','NUMEXPR_NUM_THREADS=1',...argv].map(word).join(' ');
const require=(condition,reason)=>{if(!condition)throw Error('ACTUAL_BOUNDARY_STOP: '+reason);};
export function createActualBoundary(dispatch,config) {
 const raw=[],packets={},accepted=[];
 let projection,activeDeadline=null,failureFilingDeadline=null;
 const fullByRole={"independent-public-check":300,"exporter-r0":300,"independent-r0":300,"exporter-r1":1200,"independent-r1":1200,"shared-closeout":300,"final-filing":180,"lease-release":180};
 const actor=config.author==='independent'?(V35_ROOTS.includes(config.root)?'/root/full60_independent':V33_ROOTS.includes(config.root)?'/root/full60_independent':'/root/full60_independent'):'/root';
 require(['producer','independent'].includes(config.author)&&config.repo===REPO&&config.evidence_root===R&&ROOTS.has(config.root)&&/^[A-Za-z0-9_-]{1,100}$/.test(config.event_prefix),'fixed caller context');
 const control=config.repo+'/scripts/input_control_full60_20261116.py';
 const filer=config.repo+'/scripts/file_full60_input_event.py';
 const waiter=config.repo+'/scripts/await_full60_input_receipt.py';
 const argv=(mode,role)=>[PHYSICAL,'-I',control,mode,'--root',config.root,'--plan-sha',projection.plan_sha256,'--role',role];
 async function invoke(tool,args){
  return captureDispatch(dispatch,tool,args,raw);
 }
 async function complete(words,{native=false,max=20000,deadlineMs=null}={}){
  const entered=Date.now();let previousClock=entered;
  const end=Math.min(deadlineMs??(entered+180000),activeDeadline??Infinity,projection?.whole_end_ms??failureFilingDeadline??1794845700000);
  require(entered<end,'original deadline exhausted before exec dispatch');
  const args={cmd:literalCommand(words),workdir:config.repo,login:false,yield_time_ms:1000,max_output_tokens:max,...(native?{sandbox_permissions:'require_escalated',justification:'Run the authorized bounded acquisition role with complete native RSS and exit evidence; no original reads before frozen gates.'}:{})};
  let row=await invoke('exec_command',args),session=row.result.session_id,polls=0;const responses=[row];
  while(session!=null&&row.result.exit_code==null&&polls++<64){
   const current=Date.now();require(current>=previousClock,'backwards original caller clock');previousClock=current;
   const left=end-current;if(left<5000)break;
   row=await invoke('write_stdin',{session_id:session,chars:'',yield_time_ms:Math.min(30000,left),max_output_tokens:max});responses.push(row);session=row.result.session_id;
  }
  const packet={schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',author:actor,event_id:config.event_prefix+'-'+packets.count++,argv:words,request:args,responses};
  const ended=row.result.session_id==null&&Number.isInteger(row.result.exit_code);
  return {packet,ended,on_time:row.returned_ms<=end,exit_code:row.result.exit_code,stdout:responses.map(x=>x.result.output).join('')};
 }
 packets.count=0;
 async function command(words,options){
  const result=await complete(words,options);
  require(result.ended&&result.on_time&&result.exit_code===0,'metadata command did not return0: '+result.stdout);
  return result;
 }
 async function persist(packet,name){
  const result=await command([PHYSICAL,'-I',filer,'persist','--packet-json',JSON.stringify(packet),'--destination',name],{max:2000});
  return JSON.parse(result.stdout);
 }
 async function get(role){
  const waitingEnd=projection?.whole_end_ms??(Date.now()+30000);
  for(let attempt=0;attempt<32;attempt++){
   const left=waitingEnd-Date.now();require(left>=1000,'original predecessor wait exhausted');
   const result=await command([PHYSICAL,'-I',waiter,'--root',config.root,'--role',role,'--timeout-seconds',String(Math.max(1,Math.min(160,Math.floor(left/1000))))],{max:4000,deadlineMs:waitingEnd});
   const value=JSON.parse(result.stdout);
   require(value.source_or_payload_reads===0,'waiter source boundary');
   require(value.status!=='STOP','predecessor STOP remains closed');
   if(value.status==='NOT_READY')continue;
   if(projection)require(value.plan.plan_sha256===projection.plan_sha256,'plan changed while awaiting predecessor');
   else projection=value.plan;
   return value;
  }
  throw Error('original bounded predecessor wait exhausted');
 }
 async function prepare(){
  if(config.formal)return (await get('plan')).plan;
  const wholeStart=Date.now();
  const result=await command([PHYSICAL,'-I',control,'prepare-rehearsal','--root',config.root,'--registration-certificate-sha',config.registration_certificate_sha,'--registration-finalize-actual-sha',config.registration_finalize_actual_sha,'--whole-start-ms',String(wholeStart)],{max:2000,deadlineMs:wholeStart+30000});
  const small=JSON.parse(result.stdout);
  require(small.formal_authority===false,'public preparation scope');
  const value=await get('plan');require(value.plan.plan_sha256===small.plan_sha256,'actual prepare hash differs');
  // Persisting the prepare courier is deferred until AFTER first SUP to preserve startup reserve.
  packets.prepare=result.packet;return value.plan;
 }
 async function plan(){
  if(config.formal){
   const wholeStart=Date.now();
   const result=await command([PHYSICAL,'-I',control,'activate-formal','--root',config.root,'--registration-certificate-sha',config.registration_certificate_sha,'--registration-finalize-actual-sha',config.registration_finalize_actual_sha,'--whole-start-ms',String(wholeStart)],{max:2000,deadlineMs:wholeStart+30000});
   packets.activation=result.packet;
  }
  return (await get('plan')).plan;
 }
 async function roleRun(role){
  const full=fullByRole[role];const roleEntered=Date.now();const roleDeadline=Math.min(projection.whole_end_ms,roleEntered+full*1000-10000);activeDeadline=roleDeadline;
  require(Number.isInteger(full)&&projection.whole_end_ms-Date.now()>=(role==='final-filing'?360:full)*1000,'original whole4500 complete tail unavailable');
  const modes={},filingErrors=[];
  for(const mode of ['supervise','record']){
   const result=await complete(argv(mode,role),{native:true,deadlineMs:roleDeadline});
   modes[mode]=result;
   const path=R+'/'+config.event_prefix+'-'+role+'-'+mode+'-raw-actual-call.json';
   try {
    const saved=await persist(result.packet,path);
    packets[role+'-'+mode]={...saved,packet:result.packet};
    if(packets.prepare&&!packets.prepare_filed){await persist(packets.prepare,R+'/'+config.event_prefix+'-prepare-raw-actual-call.json');packets.prepare_filed=true;}
    require(result.ended&&result.on_time,'late/live original role return retained; no retry');
    await command([PHYSICAL,'-I',filer,'file','--root',config.root,'--plan-sha',projection.plan_sha256,'--role',role,'--event-mode',mode,'--packet',saved.path,'--packet-sha',saved.sha256],{max:2000});
   } catch(error){filingErrors.push({mode,reason:String(error)});}
   require(result.ended&&result.on_time,'late/live original return retained; REC not launched');
  }
  require(filingErrors.length===0,'filing failures retained AFTER unique REC: '+JSON.stringify(filingErrors));
  const bound=await command(argv('bind',role));
  const proof=JSON.parse(bound.stdout);
  const ok=modes.supervise.exit_code===0&&modes.record.exit_code===0&&(proof.full_role_evidence_accepted===true||proof.metadata_evidence_accepted===true);
  const result={role,accepted:ok,complete:true,actual_exit_codes:[modes.supervise.exit_code,modes.record.exit_code],T0_ms:modes.supervise.packet.responses[0].requested_ms,T1_ms:modes.record.packet.responses.at(-1).returned_ms,proof,bind_actual:bound.packet};
  require(result.T1_ms<=projection.whole_end_ms && result.T1_ms-result.T0_ms+10000<=full*1000,'original whole return/FULL tariff exceeds limit');
  activeDeadline=null;accepted.push(result);return result;
 }
 async function certificate(){
  require(Date.now()<projection.whole_end_ms,'original whole4500 certificate expired');
  const mode=config.formal?'certify-input-version':'certify-rehearsal';
  const result=await complete(argv(mode,'certificate'));
  const destination=config.formal?R+'/'+config.event_prefix+'-certify-input-version-raw-actual-call.json':config.root+'/certify-rehearsal-raw-actual-call.json';
  const saved=await persist(result.packet,destination);
  require(result.ended&&result.on_time&&result.exit_code===0,'certificate STOP retained; never retry');
  require(result.packet.responses.at(-1).returned_ms<=projection.whole_end_ms,'original certificate actualreturn expired');
  return {accepted:true,actual:saved,result:JSON.parse(result.stdout)};
 }
 async function freeze(value){
  activeDeadline=null;const savedProjection=projection;projection=null;
  require(Date.now()+180000<=1794852900000,'new result filing original global end exhausted');failureFilingDeadline=Date.now()+180000;
  // The attempt's data/Native directories stay intact. Save a separate caller failure packet.
  const packet={schema:'topolab.m2-acquisition-caller-failure.v1',author:actor,event_id:config.event_prefix+'-caller-STOP',caller_failure:value,original_rows:raw,own_future_return:'NOT_CLAIMED'};
  await persist(packet,R+'/'+config.event_prefix+'-'+config.author+'-caller-STOP.json');projection=savedProjection;
 }
 return {prepare,plan,wait:async role=>(await get(role)).proofs,run:roleRun,metadata:roleRun,certificate,freeze,raw,packets,accepted};
}

// Permission-service waits happen before the immutable300s metadata actor starts.
// Thrown dispatch errors retain exact arguments and original error, never fake exits.
export async function captureDispatch(dispatch,tool,args,raw,now=Date.now) {
 const requested_ms=now();let row;
 try {row=await dispatch(tool,args);}
 catch(error){raw.push({tool,arguments:args,requested_ms,returned_ms:now(),error:String(error)});throw error;}
 require(row.tool===tool&&JSON.stringify(row.arguments)===JSON.stringify(args)&&Number.isSafeInteger(row.requested_ms)&&Number.isSafeInteger(row.returned_ms)&&requested_ms<=row.requested_ms&&row.requested_ms<=row.returned_ms&&row.returned_ms<=now()&&(!raw.length||raw.at(-1).returned_ms<=row.requested_ms),'original ordered tool row required');
 raw.push(row);return row;
}
export async function permissionThenPrepare(dispatch,config,raw,now=Date.now) {
 require(['/root/full60_independent','/root/full60_independent'].includes(config.author)&&config.repo===REPO&&config.evidence_root===R&&/^[A-Za-z0-9_-]{1,100}$/.test(config.event_prefix)&&/^[a-f0-9]{64}$/.test(config.standards_sha)&&/^[a-f0-9]{64}$/.test(config.spec_sha),'fixed permission caller context');
 const v35=config.author==='/root/full60_independent';
 const entry=REPO+'/scripts/'+(v35?'binding_recovery_full60_20261116.py':'binding_recovery_full60_20261116.py');
 const python=PHYSICAL,words=[python,'-I',entry,'--help'];
 const prefix=['env','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1','VECLIB_MAXIMUM_THREADS=1','NUMEXPR_NUM_THREADS=1',python,'-I',entry];
 const args={cmd:literalCommand(words),workdir:REPO,login:false,yield_time_ms:1000,max_output_tokens:4000,sandbox_permissions:'require_escalated',justification:'Approve the authorized exact metadata entry prefix using harmless help before any actor, Native, root or Source work.',prefix_rule:prefix};
 const approved=await captureDispatch(dispatch,'exec_command',args,raw,now);
 require(approved.result?.exit_code===0&&approved.result.session_id==null&&approved.result.output.includes('usage:'),'permission complete successful actual return required');
 const packet={schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',author:config.author,event_id:config.event_prefix+'-permission',argv:words,request:args,responses:[approved]};
 const path=R+'/independent/'+(v35?'FULL60-public-metadata-a1-permission-preflight-raw-actual-call.json':'FULL60-public-metadata-a1-permission-preflight-raw-actual-call.json');
 const saved=await captureDispatch(dispatch,'exec_command',{cmd:literalCommand([PHYSICAL,'-I',REPO+'/scripts/file_full60_input_event.py','persist','--packet-json',JSON.stringify(packet),'--destination',path]),workdir:REPO,login:false,yield_time_ms:1000,max_output_tokens:2000},raw,now);
 require(saved.result?.exit_code===0&&saved.result.session_id==null,'permission courier complete return required');
 const pin=JSON.parse(saved.result.output);
 require(pin.path===path&&/^[a-f0-9]{64}$/.test(pin.sha256),'permission courier literal pin required');
 return captureDispatch(dispatch,'exec_command',{cmd:literalCommand([python,'-I',entry,'prepare','--kind','public','--attempt','1','--standards-sha',config.standards_sha,'--spec-sha',config.spec_sha,'--permission-packet',path,'--permission-packet-sha',pin.sha256,'--public-capability-sha',config.public_capability_sha]),workdir:REPO,login:false,yield_time_ms:1000,max_output_tokens:20000},raw,now);
}

// Each actual input prefix receives its own harmless native permission probe.
export async function permissionInputPrefixes(dispatch,config,raw,now=Date.now){
 require(config.repo===REPO&&config.evidence_root===R,'NEW prefix context');
 const executableSha='93d04da16de15e537a76fa1278accf982dd35ff1107e06460433315512eb381f';
 const results=[];
 for(const name of ['input_control_full60_20261116.py','registered_input_full60_20261116.py']){
  const words=[PHYSICAL,'-I',REPO+'/scripts/'+name,'--help'];
  const args={cmd:literalCommand(words),workdir:REPO,login:false,yield_time_ms:1000,max_output_tokens:4000,sandbox_permissions:'require_escalated',justification:'Check the authorized NEW input exact interpreter/entry prefix with harmless help before any input clock or target/source operation.'};
  const row=await captureDispatch(dispatch,'exec_command',args,raw,now);
  require(row.result?.exit_code===0&&row.result.session_id==null&&row.result.output.includes('usage:'),'NEW exact input prefix did not return0');results.push(row);
 }
 return {python:PHYSICAL,python_sha256:executableSha,results,source_or_payload_reads:0};
}
