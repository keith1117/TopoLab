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

const NOV21_ID='topolab.v2.p17-m2-registered-source-acquisition.20261121.v1';
const NOV21_RECOVERY='topolab.v2.p17-binding-certificate-recovery.20261121.v1';
const NOV21_PROFILE=Object.freeze({
 repo:'/private/tmp/topolab-meta-input-20261121',
 evidence:'/Users/keith1117/Documents/TopoLab-data/metadata-input-acceptance-20261121',
 roots:['/private/tmp/topolab-public-source-acquisition-20261121-a1',
 '/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-local-input-version-20261121-a1'],
 globalEnd:1795281660000,latestWholeEnd:1795274460000,
 control:'input_control_20261121.py',registered:'registered_input_20261121.py',
 recovery:'binding_recovery_20261121.py',waiter:'await_input_receipt_20261121.py',
 filer:'file_input_event_20261121.py'
});
const oldProfile={repo:REPO,evidence:R,roots:[...ROOTS],globalEnd:1794852900000,
 latestWholeEnd:1794845700000,control:'input_control_full60_20261116.py',
 registered:'registered_input_full60_20261116.py',recovery:'binding_recovery_full60_20261116.py',
 waiter:'await_full60_input_receipt.py',filer:'file_full60_input_event.py'};
const profileFor=config=>[NOV21_ID,NOV21_RECOVERY].includes(config.execution_identity)?NOV21_PROFILE:oldProfile;
export function qualification20261121(config){
 require(['producer','independent'].includes(config.author)&&typeof config.formal==='boolean',
 'new dated author/formal qualification');
 require(NOV21_PROFILE.roots.includes(config.root)&&config.formal===(config.root===NOV21_PROFILE.roots[1]),
 'new dated root/scope qualification');
 for(const [key,value] of Object.entries({repo:NOV21_PROFILE.repo,evidence_root:NOV21_PROFILE.evidence,
 execution_identity:NOV21_ID}))require(config[key]===undefined||config[key]===value,'new dated fixed '+key);
 const gate=config.metadata_gate,hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 require(gate&&['public','formal'].every(kind=>gate[kind]&&hash(gate[kind].certificate_sha256)&&hash(gate[kind].finalize_actual_sha256)),'both NEW metadata certificate/finalizer pins required before input');
 const selected=gate[config.formal?'formal':'public'];
 const derived={registration_certificate_sha:selected.certificate_sha256,
 registration_finalize_actual_sha:selected.finalize_actual_sha256,
 formal_registration_certificate_sha:gate.formal.certificate_sha256,
 formal_registration_finalize_actual_sha:gate.formal.finalize_actual_sha256};
 for(const [key,value] of Object.entries(derived))require(config[key]===undefined||config[key]===value,'new dated metadata pin differs: '+key);
 return {...config,...derived,repo:NOV21_PROFILE.repo,evidence_root:NOV21_PROFILE.evidence,execution_identity:NOV21_ID};
}
// An approval is scoped to one exact operation and target. E-only couriers stay sandboxed.
export function permission20261121(words,config,native=false){
 const entry=words[2],mode=words[3],script=name=>NOV21_PROFILE.repo+'/scripts/'+name;
 const rootIndex=words.indexOf('--root'),root=rootIndex<0?null:words[rootIndex+1];
 if(root!==null)require(root===config.root&&NOV21_PROFILE.roots.includes(root),'permission root differs');
 let purpose=null;
 if(native){
  require(entry===script(NOV21_PROFILE.control)&&['supervise','record'].includes(mode)&&root===config.root,'native operation differs');
  purpose='执行本轮 '+mode+'/'+words[words.indexOf('--role')+1]+'，采集原生 RSS 和完整真实退出回执';
 }else if(entry===script(NOV21_PROFILE.control)){
  require(['prepare-rehearsal','activate-formal','bind','certify-rehearsal','certify-input-version'].includes(mode)&&root===config.root,'control operation differs');
  if(config.formal)purpose=mode==='activate-formal'?'核验 GitHub 已发布源码及独立预检，并创建本轮正式输入目标':'读取或写入本轮正式输入的 '+mode+' 元数据';
 }else if(entry===script(NOV21_PROFILE.filer)){
  require(['file','persist'].includes(mode),'courier operation differs');
  if(mode==='file'&&config.formal){require(root===config.root,'formal event root differs');purpose='读取本轮正式输入 pending 并写入原始工具事件';}
 }else if(entry===script(NOV21_PROFILE.waiter)){
  require(root===config.root,'waiter root differs');
  // This waiter only reads metadata; the declared filesystem read scope covers it.
 }else require(false,'unregistered caller operation');
 return purpose?{sandbox_permissions:'require_escalated',justification:'允许在 '+config.root+' '+purpose+'吗？'}:{};
}
export function createActualBoundary(dispatch,config) {
 const profile=profileFor(config),R=profile.evidence,REPO=profile.repo,ROOTS=new Set(profile.roots);
 if(profile===NOV21_PROFILE)config=qualification20261121(config);
 const raw=[],packets={},accepted=[];
 let projection,activeDeadline=null,failureFilingDeadline=null;
 const fullByRole={"independent-public-check":300,"exporter-r0":300,"independent-r0":300,"exporter-r1":1200,"independent-r1":1200,"shared-closeout":300,"final-filing":180,"lease-release":180};
 const actor=config.author==='independent'?(V35_ROOTS.includes(config.root)?'/root/full60_independent':V33_ROOTS.includes(config.root)?'/root/full60_independent':'/root/full60_independent'):'/root';
 require(['producer','independent'].includes(config.author)&&config.repo===REPO&&config.evidence_root===R&&ROOTS.has(config.root)&&/^[A-Za-z0-9_-]{1,100}$/.test(config.event_prefix),'fixed caller context');
 const control=config.repo+'/scripts/'+profile.control;
 const filer=config.repo+'/scripts/'+profile.filer;
 const waiter=config.repo+'/scripts/'+profile.waiter;
 const argv=(mode,role)=>[PHYSICAL,'-I',control,mode,'--root',config.root,'--plan-sha',projection.plan_sha256,'--role',role];
 async function invoke(tool,args){
  return captureDispatch(dispatch,tool,args,raw);
 }
 async function complete(words,{native=false,max=20000,deadlineMs=null}={}){
  const entered=Date.now();let previousClock=entered;
  const end=Math.min(deadlineMs??(entered+180000),activeDeadline??Infinity,projection?.whole_end_ms??failureFilingDeadline??profile.latestWholeEnd);
  require(entered<end,'original deadline exhausted before exec dispatch');
  const permission=profile===NOV21_PROFILE?permission20261121(words,config,native):(native?{sandbox_permissions:'require_escalated',justification:'Run the authorized bounded acquisition role with complete native RSS and exit evidence; no original reads before frozen gates.'}:{});
  const args={cmd:literalCommand(words),workdir:config.repo,login:false,yield_time_ms:1000,max_output_tokens:max,...permission};
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
  const formalPins=profile===NOV21_PROFILE?['--formal-registration-certificate-sha',config.formal_registration_certificate_sha,'--formal-registration-finalize-actual-sha',config.formal_registration_finalize_actual_sha]:[];
  const result=await command([PHYSICAL,'-I',control,'prepare-rehearsal','--root',config.root,'--registration-certificate-sha',config.registration_certificate_sha,'--registration-finalize-actual-sha',config.registration_finalize_actual_sha,...formalPins,'--whole-start-ms',String(wholeStart)],{max:2000,deadlineMs:wholeStart+30000});
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
   if(profile===NOV21_PROFILE){
    const small=JSON.parse(result.stdout);require(small.formal_authority===true,'formal activation scope');
    const value=await get('plan');require(value.plan.plan_sha256===small.plan_sha256,'actual activation hash differs');
    return value.plan;
   }
  }
  return (await get('plan')).plan;
 }
 async function roleRun(role){
  const full=fullByRole[role];const roleEntered=Date.now();const roleDeadline=Math.min(projection.whole_end_ms,roleEntered+full*1000-10000);activeDeadline=roleDeadline;
  require(Number.isInteger(full)&&projection.whole_end_ms-Date.now()>=(role==='final-filing'?360:full)*1000,'original whole4500 complete tail unavailable');
  const modes={},filingErrors=[];
  for(const mode of ['supervise','record']){
   if(mode==='record'&&profile===NOV21_PROFILE)require(filingErrors.length===0,'SUP pending/event filing failed; REC remains unopened');
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
  if(profile===NOV21_PROFILE)require(modes.supervise.exit_code===0&&modes.record.exit_code===0,'original SUP/REC exit '+modes.supervise.exit_code+'/'+modes.record.exit_code+' retained after unique closing REC; successor remains unopened');
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
  require(Date.now()+180000<=profile.globalEnd,'new result filing original global end exhausted');failureFilingDeadline=Date.now()+180000;
  // The attempt's data/Native directories stay intact. Save a separate caller failure packet.
  const packet={schema:'topolab.m2-acquisition-caller-failure.v1',author:actor,event_id:config.event_prefix+'-caller-STOP',caller_failure:value,...(profile===NOV21_PROFILE?{caller_root:config.root,execution_identity:NOV21_ID}:{}),original_rows:raw,own_future_return:'NOT_CLAIMED'};
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
 const previous=raw.at(-1);raw.push(row);
 require(row.tool===tool&&JSON.stringify(row.arguments)===JSON.stringify(args)&&Number.isSafeInteger(row.requested_ms)&&Number.isSafeInteger(row.returned_ms)&&requested_ms<=row.requested_ms&&row.requested_ms<=row.returned_ms&&row.returned_ms<=now()&&(!previous||previous.returned_ms<=row.requested_ms),'original ordered tool row required');
 return row;
}
export async function permissionThenPrepare(dispatch,config,raw,now=Date.now) {
 const profile=profileFor(config),R=profile.evidence,REPO=profile.repo;
 require(['/root/full60_independent','/root/full60_independent'].includes(config.author)&&config.repo===REPO&&config.evidence_root===R&&/^[A-Za-z0-9_-]{1,100}$/.test(config.event_prefix)&&/^[a-f0-9]{64}$/.test(config.standards_sha)&&/^[a-f0-9]{64}$/.test(config.spec_sha),'fixed permission caller context');
 const v35=config.author==='/root/full60_independent';
 const entry=REPO+'/scripts/'+profile.recovery;
 const python=PHYSICAL,words=[python,'-I',entry,'--help'];
 const prefix=['env','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1','VECLIB_MAXIMUM_THREADS=1','NUMEXPR_NUM_THREADS=1',python,'-I',entry];
 const args={cmd:literalCommand(words),workdir:REPO,login:false,yield_time_ms:30000,max_output_tokens:4000,sandbox_permissions:'require_escalated',...(profile===NOV21_PROFILE?{justification:'允许仅执行本轮 binding_recovery_20261121.py --help，核对物理解释器和入口，不启动元数据角色或读取输入吗？'}:{justification:'Approve the authorized exact metadata entry prefix using harmless help before any actor, Native, root or Source work.',prefix_rule:prefix})};
 const approved=await captureDispatch(dispatch,'exec_command',args,raw,now);
 require(approved.result?.exit_code===0&&approved.result.session_id==null&&approved.result.output.includes('usage:'),'permission complete successful actual return required');
 const packet={schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',author:config.author,event_id:config.event_prefix+'-permission',argv:words,request:args,responses:[approved]};
 const path=R+'/independent/'+(v35?'FULL60-public-metadata-a1-permission-preflight-raw-actual-call.json':'FULL60-public-metadata-a1-permission-preflight-raw-actual-call.json');
 const saved=await captureDispatch(dispatch,'exec_command',{cmd:literalCommand([PHYSICAL,'-I',REPO+'/scripts/'+profile.filer,'persist','--packet-json',JSON.stringify(packet),'--destination',path]),workdir:REPO,login:false,yield_time_ms:1000,max_output_tokens:2000},raw,now);
 require(saved.result?.exit_code===0&&saved.result.session_id==null,'permission courier complete return required');
 const pin=JSON.parse(saved.result.output);
 require(pin.path===path&&/^[a-f0-9]{64}$/.test(pin.sha256),'permission courier literal pin required');
 return captureDispatch(dispatch,'exec_command',{cmd:literalCommand([python,'-I',entry,'prepare','--kind','public','--attempt','1','--standards-sha',config.standards_sha,'--spec-sha',config.spec_sha,'--permission-packet',path,'--permission-packet-sha',pin.sha256,'--public-capability-sha',config.public_capability_sha]),workdir:REPO,login:false,yield_time_ms:1000,max_output_tokens:20000},raw,now);
}

// Each actual input prefix receives its own harmless native permission probe.
export async function permissionInputPrefixes(dispatch,config,raw,now=Date.now){
 const profile=profileFor(config),R=profile.evidence,REPO=profile.repo;
 require(config.repo===REPO&&config.evidence_root===R,'NEW prefix context');
 const executableSha='93d04da16de15e537a76fa1278accf982dd35ff1107e06460433315512eb381f';
 const results=[];
 for(const name of [profile.control,profile.registered]){
  const words=[PHYSICAL,'-I',REPO+'/scripts/'+name,'--help'];
  const args={cmd:literalCommand(words),workdir:REPO,login:false,yield_time_ms:30000,max_output_tokens:4000,sandbox_permissions:'require_escalated',justification:profile===NOV21_PROFILE?'允许仅执行本轮 '+name+' --help，核对物理解释器和入口，不启动输入时钟或访问目标/源吗？':'Check the authorized NEW input exact interpreter/entry prefix with harmless help before any input clock or target/source operation.'};
  const row=await captureDispatch(dispatch,'exec_command',args,raw,now);
  require(row.result?.exit_code===0&&row.result.session_id==null&&row.result.output.includes('usage:'),'NEW exact input prefix did not return0');results.push(row);
 }
 return {python:PHYSICAL,python_sha256:executableSha,results,source_or_payload_reads:0};
}
