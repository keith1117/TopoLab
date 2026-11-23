// One new staged graph only. Dispatches original tools; no old profile or authority is selected.
const REPO='/private/tmp/topolab-staged-input-20261121';
const E='/Users/keith1117/Documents/TopoLab-data/staged-input-acceptance-20261121';
const ID='topolab.v2.p17-m2-registered-source-acquisition.staged-20261121.v1';
const BUDGET='7212bce05d9f1d953c44b800c59d941e2e1e44111777845ae57f2479be170687';
const PUBLIC='/private/tmp/topolab-public-staged-input-20261121-a1';
const FORMAL='/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-staged-input-20261121-a1';
const PYTHON='/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python';
const GLOBAL_START=Date.parse('2026-11-21T20:40:00Z'),GLOBAL_END=Date.parse('2026-11-22T12:40:00Z');
const formalOnly={
 REPO:'/private/tmp/topolab-formal-input-20261122', E:'/Users/keith1117/Documents/TopoLab-data/formal-input-20261122',
 ID:'topolab.v2.p17-m2-registered-source-acquisition.formal-20261122.v1', BUDGET:'96c2a727428bb7d30c8d2c00dee43c1f42c7f55b73660959cc51c8c33db33f7b',
 PUBLIC:null, FORMAL:'/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-formal-input-20261122-a1',
 GLOBAL_START:Date.parse('2026-11-22T03:40:00Z'), GLOBAL_END:Date.parse('2026-11-22T21:40:00Z'), prefix:'formal_input'
};
const r0Read={
 REPO:'/private/tmp/topolab-r0-read-20261122', E:'/Users/keith1117/Documents/TopoLab-data/r0-read-acceptance-20261122',
 ID:'topolab.v2.p17-m2-registered-source-acquisition.r0-read-20261122.v1', BUDGET:'149fe42c5df8849c49d3cb39b62004a8b0d7d82bf3ce1c7bca131f24f9c0b666',
 PUBLIC:null, FORMAL:'/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-r0-read-20261122-a1', GLOBAL_START:1795333814731, GLOBAL_END:1795420214731, prefix:'r0_input'
};
const catalog={
 REPO:'/private/tmp/topolab-catalog-r0-20261122', E:'/Users/keith1117/Documents/TopoLab-data/catalog-r0-acceptance-20261122',
 ID:'topolab.v2.p17-m2-registered-source-acquisition.catalog-20261122.v1', BUDGET:'985ad9aa67a4cbdc8a5c36cadbf4c7920f39559c57e2115a98e902d17d31c11f',
 PUBLIC:null, FORMAL:'/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-catalog-r0-20261122-a1', GLOBAL_START:1795381083469, GLOBAL_END:1795467483469, prefix:'catalog_input'
};
const cycle={
 REPO:'/private/tmp/topolab-input-cycle-20261123', E:'/Users/keith1117/Documents/TopoLab-data/input-cycle-20261123-a1',
 ID:'topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a1.v1', BUDGET:'ebfe2a88f7c838a08bbc5e7f04c7978dd446b552c9e3db206b3a044dec580862',
 PUBLIC:null, FORMAL:'/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-input-cycle-20261123-a1', GLOBAL_START:1795403546212, GLOBAL_END:1795576346212, prefix:'cycle_input'
};
const cycleR1={
 REPO:'/private/tmp/topolab-input-cycle-20261123-a2', E:'/Users/keith1117/Documents/TopoLab-data/input-cycle-20261123-a2',
 ID:'topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a2.v1', BUDGET:'6f4168eb23d191629a98c42c469933e0016a1ba2090c521995fc0eeb606a06de',
 PUBLIC:null, FORMAL:'/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-input-cycle-20261123-a2', GLOBAL_START:1795403546212, GLOBAL_END:1795576346212, prefix:'cycle_r1_input'
};
const staged={REPO,E,ID,BUDGET,PUBLIC,FORMAL,GLOBAL_START,GLOBAL_END,prefix:'staged_input'};
function routeFor(identity){return [staged,formalOnly,r0Read,catalog,cycle,cycleR1].find(route=>route.ID===identity)??staged;}
const ROLES=['independent-public-check','exporter-r0','independent-r0','exporter-r1','independent-r1','shared-closeout'];
const FULL=[300,300,300,1200,1200,300];
const need=(condition,reason)=>{if(!condition)throw Error('STAGED_CALLER_STOP: '+reason);};
const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const quote=s=>/^[A-Za-z0-9_@%+=:,./-]+$/.test(s)?s:"'"+s.replaceAll("'","'\"'\"'")+"'";
export const literalCommand=argv=>'exec '+['env','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1','VECLIB_MAXIMUM_THREADS=1','NUMEXPR_NUM_THREADS=1',...argv].map(quote).join(' ');
export function qualify(config){
 const route=routeFor(config.execution_identity),{REPO,E,ID,BUDGET,PUBLIC,FORMAL}=route;
 need(route.PUBLIC!==null||config.formal===true,'formal-only contract');
 need(['producer','independent'].includes(config.author)&&typeof config.formal==='boolean','separate registered author/scope required');
 need(config.root===(config.formal?FORMAL:PUBLIC)&&/^[A-Za-z0-9_-]{1,80}$/.test(config.event_prefix),'literal new target/prefix required');
 for(const [key,value] of Object.entries({repo:REPO,evidence_root:E,execution_identity:ID,owner_budget_sha256:BUDGET}))
  need(config[key]===undefined||config[key]===value,'fixed '+key+' differs');
 for(const key of ['registration_certificate_sha','registration_finalize_actual_sha','formal_registration_certificate_sha','formal_registration_finalize_actual_sha'])
  need(hash(config[key]),'actual registration certificate/finalizer SHA missing: '+key);
 if(config.formal)need(config.registration_certificate_sha===config.formal_registration_certificate_sha&&config.registration_finalize_actual_sha===config.formal_registration_finalize_actual_sha,'formal metadata pins differ');
 return {...config,repo:REPO,evidence_root:E,execution_identity:ID,owner_budget_sha256:BUDGET};
}
export function launchGate(plan,role,proofs,now){
 const {ID,PUBLIC,FORMAL,GLOBAL_START,GLOBAL_END}=routeFor(plan.execution_identity);
 need(typeof plan.root==='string','literal root required');
 const index=ROLES.indexOf(role);
 need(index>=0&&plan.execution_identity===ID&&hash(plan.plan_sha256)&&[PUBLIC,FORMAL].includes(plan.root),'new plan/role differs');
 need(plan.formal_authority===(plan.root===FORMAL)&&plan.scope===(plan.root===FORMAL?'SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY':'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY'),'plan scope differs');
 need(plan.actor_window_seconds===4500&&plan.coordination_limit_ms===240000&&JSON.stringify(plan.role_order)===JSON.stringify(ROLES),'frozen order/window differs');
 need(Number.isSafeInteger(now)&&plan.whole_start_ms===plan.actor_start_ms&&plan.whole_start_ms>=GLOBAL_START&&plan.whole_end_ms===plan.whole_start_ms+4500000&&plan.whole_end_ms+7200000<=GLOBAL_END&&now>=plan.whole_start_ms,'original whole4500+7200 differs');
 need(proofs.length===index,'missing predecessor proof');let coordination=0;
 for(let i=0;i<proofs.length;i++){
  const p=proofs[i];need(p.role===ROLES[i]&&p.accepted===true&&p.complete===true&&JSON.stringify(p.actual_exit_codes)==='[0,0]'&&Number.isSafeInteger(p.T0_ms)&&Number.isSafeInteger(p.T1_ms)&&p.T0_ms<=p.T1_ms,'unaccepted predecessor');
  if(i){need(p.T0_ms>=proofs[i-1].T1_ms,'negative coordination');coordination+=p.T0_ms-proofs[i-1].T1_ms;}
 }
 if(!index)need(now-plan.whole_start_ms<=30000,'late first SUP');
 else need(now>=proofs.at(-1).T1_ms&&coordination+now-proofs.at(-1).T1_ms<=240000,'coordination240 exhausted');
 need(Math.min(plan.whole_end_ms,plan.applicable_deadline_ms??Infinity)-now>=(FULL.slice(index).reduce((a,b)=>a+b,0)+600)*1000,'complete remaining cohort unavailable');
}
export async function executeActor(input,dispatch,now=Date.now){
 const config=qualify(input),raw=[],packets={},observed=[],author=config.author==='producer'?'/root':'/root/full60_independent';
 const {REPO,E,ID,PUBLIC,GLOBAL_START,GLOBAL_END,prefix:scriptPrefix}=routeFor(config.execution_identity);
 const script=REPO+'/scripts/'+scriptPrefix;
 const control=script+'_control.py',filer=script+'_filer.py',waiter=script+'_waiter.py';
 const prefix=config.event_prefix+'-'+config.author;
 let plan=null,active=null,serial=0,toolCalls=0,failureDeadline=null;
 async function invoke(tool,args){
  need(++toolCalls<=2048,'metadata dispatch cap reached');const requested_ms=now(),previous=raw.at(-1);let row;
  try{row=await dispatch(tool,args);}catch(error){row={tool,arguments:args,requested_ms,returned_ms:now(),error:String(error)};raw.push(row);throw error;}
  raw.push(row);
  need(row&&row.tool===tool&&JSON.stringify(row.arguments)===JSON.stringify(args)&&Number.isSafeInteger(row.requested_ms)&&Number.isSafeInteger(row.returned_ms)&&requested_ms<=row.requested_ms&&row.requested_ms<=row.returned_ms&&row.returned_ms<=now()&&(!previous||previous.returned_ms<=row.requested_ms),'original ordered tool response required');
  return row;
 }
 function permission(words,native){
  const entry=words[2],mode=words[3];let purpose=null;
  if(native)purpose='执行本轮 '+mode+' '+active.role+'，采集原生 RSS 和完整退出回执';
  else if(config.formal&&entry===control)purpose=mode==='activate-formal'?'核验已发布 GitHub 源码及独立预检并创建本轮正式目标':'写入本轮正式输入的 '+mode+' 控制回执';
  else if(config.formal&&entry===filer&&mode==='file')purpose='核对本轮 pending 并写入实际 SUP/REC 事件';
  return purpose?{sandbox_permissions:'require_escalated',justification:'允许在 '+config.root+' '+purpose+'吗？'}:{};
 }
 async function complete(words,{native=false,deadline=now()+180000,max=16000}={}){
  const first=raw.length,end=Math.min(deadline,GLOBAL_END,failureDeadline??plan?.whole_end_ms??Infinity),entered=now();let row=null,error=null;
  const args={cmd:literalCommand(words),workdir:REPO,login:false,yield_time_ms:1000,max_output_tokens:max,...permission(words,native)};
  try{
   function resultRow(row,owned=null){
    const r=row.result;need(r&&typeof r.output==='string'&&!r.output.includes('Warning: truncated output')&&!r.output.includes('tokens truncated')&&(r.original_token_count==null||(Number.isInteger(r.original_token_count)&&r.original_token_count<=max)),'original complete output required');
    if(r.session_id!=null)need(Number.isInteger(r.session_id)&&r.exit_code==null&&(owned===null||r.session_id===owned),'owned session drift/type');
    else need(Number.isInteger(r.exit_code),'actual terminal exit required');
   }
   need(entered<end,'dispatch deadline exhausted');row=await invoke('exec_command',args);resultRow(row);
   const ownedSession=row.result.session_id;let live=ownedSession!=null,polls=0,clock=entered;
   while(live&&polls++<64){
    const t=now();need(t>=clock,'backwards caller clock');clock=t;const left=end-t;if(left<5000)break;
    row=await invoke('write_stdin',{session_id:ownedSession,chars:'',yield_time_ms:Math.min(30000,left),max_output_tokens:max});
    resultRow(row,ownedSession);live=row.result.session_id!=null;
   }
  }catch(cause){error=String(cause);}
  const packet={schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',author,event_id:prefix+'-'+serial++,argv:words,request:args,responses:raw.slice(first)};
  const ended=!error&&row?.result?.session_id==null&&Number.isInteger(row?.result?.exit_code);
  return {packet,ended,on_time:!!row&&row.returned_ms<=end,exit_code:row?.result?.exit_code,error,stdout:packet.responses.map(r=>r.result?.output??'').join('')};
 }
 function successful(result){return result.ended&&result.on_time&&result.exit_code===0&&!result.error;}
 async function command(words,options){const result=await complete(words,options);need(successful(result),'command '+words[3]+' failed/live/late: exit='+result.exit_code+', ended='+result.ended+', on_time='+result.on_time+', error='+result.error+', event='+result.packet.event_id);return result;}
 async function persist(packet,tag,destination=null){
  const path=destination??E+'/'+prefix+'-'+tag+'.json';
  const deadline=failureDeadline??active?.deadline_ms??plan?.whole_end_ms??now()+180000;
  const actual=await command([PYTHON,'-I',filer,'persist','--packet-json',JSON.stringify(packet),'--destination',path],{deadline,max:3000});
  const saved=JSON.parse(actual.stdout);need(saved.status==='PAIRED_PERSISTED','original packet custody incomplete: '+actual.stdout);return saved;
 }
 async function get(role){
  const end=plan?.whole_end_ms??Math.min(now()+4500000,GLOBAL_END-7200000);
  for(let attempt=0;attempt<32;attempt++){
   const left=end-now();need(left>=1000,'predecessor wait exhausted');
   const actual=await command([PYTHON,'-I',waiter,'--root',config.root,'--role',role,'--timeout-seconds',String(Math.max(1,Math.min(160,Math.floor(left/1000))))],{deadline:end,max:5000});
   const value=JSON.parse(actual.stdout);need(value.source_or_payload_reads===0,'waiter source boundary');
   need(value.status!=='STOP','predecessor STOP closes this graph');if(value.status==='NOT_READY')continue;
   need(value.plan.root===config.root,'waiter target differs');
   if(plan)need(value.plan.plan_sha256===plan.plan_sha256,'plan changed');else plan=value.plan;
   return value;
  }
  throw Error('bounded predecessor wait exhausted');
 }
 const roleArgv=(mode,role)=>[PYTHON,'-I',control,mode,'--root',config.root,'--plan-sha',plan.plan_sha256,'--role',role];
 async function runRole(role){
  const full=FULL[ROLES.indexOf(role)]??180,entered=now(),deadline=Math.min(plan.whole_end_ms,entered+full*1000-10000);
  need(plan.whole_end_ms-entered>=(role==='final-filing'?360:full)*1000,'complete closeout FULL unavailable');
  active={role,full,entered_ms:entered,deadline_ms:deadline,supervise:null,record:null,native_dispatch:'NOT_REQUESTED'};
  if(role===ROLES[0]){const reservation=await command([PYTHON,'-I',filer,'reserve','--root',config.root,'--plan-sha',plan.plan_sha256,'--role',role],{deadline,max:3000});packets.shared_reservation=JSON.parse(reservation.stdout);need(packets.shared_reservation.status==='PAIRED_PERSISTED','shared300 reservation custody failed');}
  for(const mode of ['supervise','record']){
   if(mode==='supervise'&&role===ROLES[0])need(now()-plan.whole_start_ms<=30000,'first SUP30 exhausted after reservation');
   active.native_dispatch='REQUEST_ATTEMPTED_NOT_LAUNCH_PROOF';
   const actual=await complete(roleArgv(mode,role),{native:true,deadline});active[mode]=actual;
   if(!successful(actual)){active.first_failure='first '+mode+' failed/live/late: exit='+actual.exit_code+', ended='+actual.ended+', on_time='+actual.on_time+', error='+actual.error+', event='+actual.packet.event_id;failureDeadline??=Math.min(now()+180000,GLOBAL_END);}
   // Save the original response even when live, nonzero, malformed or late.
   const saved=await persist(actual.packet,role+'-'+mode+'-actual');packets[role+'-'+mode]={...saved,packet:actual.packet};
   need(successful(actual),'first '+mode+' failed/live/late; no additional named command: '+actual.packet.event_id);
   await command([PYTHON,'-I',filer,'file','--root',config.root,'--plan-sha',plan.plan_sha256,'--role',role,'--event-mode',mode,'--packet',saved.path,'--packet-sha',saved.sha256],{deadline,max:3000});
  }
  const bound=await command(roleArgv('bind',role),{deadline,max:4000}),proof=JSON.parse(bound.stdout);
  const result={role,accepted:proof.full_role_evidence_accepted===true||proof.metadata_evidence_accepted===true,complete:true,actual_exit_codes:[active.supervise.exit_code,active.record.exit_code],T0_ms:active.supervise.packet.responses[0].requested_ms,T1_ms:active.record.packet.responses.at(-1).returned_ms,proof};
  need(result.accepted&&result.T1_ms<=plan.whole_end_ms&&result.T1_ms-result.T0_ms+10000<=full*1000,'actual role evidence/FULL rejected');
  const savedBind=await persist(bound.packet,role+'-bind-actual');
  if(ROLES.includes(role)){const released=await command([PYTHON,'-I',filer,'accept-role','--root',config.root,'--plan-sha',plan.plan_sha256,'--role',role,'--packet',savedBind.path,'--packet-sha',savedBind.sha256],{deadline,max:3000});need(JSON.parse(released.stdout).status==='PAIRED_PERSISTED','actual caller release custody failed');}
  observed.push(result);active=null;return result;
 }
 async function stop(reason){
  const secondary=[];if(active?.first_failure){if(String(reason)!==active.first_failure)secondary.push({stage:'after first '+active.role,reason:String(reason)});reason=active.first_failure;}
  failureDeadline??=Math.min(now()+180000,GLOBAL_END);
  const failure={schema:'topolab.staged-input-caller-failure.v1',author,event_id:prefix+'-STOP',execution_identity:ID,caller_root:config.root,reason:String(reason),plan,active,observed,
   ...([r0Read.ID,catalog.ID,cycle.ID,cycleR1.ID].includes(ID)?{original_row_count:raw.length,full_rows_custody:'outer actor result'}:{original_rows:raw}),shared_reservation:packets.shared_reservation??'NOT_REQUESTED_BY_THIS_ACTOR',own_future_return:'NOT_CLAIMED'};
  let saved=null;
  try{saved=await persist(failure,'caller-STOP');}catch(error){secondary.push({stage:'failure packet',reason:String(error)});}
  if(saved&&plan){
   try{
    const custody=await command([PYTHON,'-I',filer,'retain-failure','--root',config.root,'--plan-sha',plan.plan_sha256,'--role',active?.role??'none','--packet',saved.path,'--packet-sha',saved.sha256],{deadline:failureDeadline,max:6000});
    packets.failure_custody=JSON.parse(custody.stdout);
   }catch(error){secondary.push({stage:'existing failure custody',reason:String(error)});}
  }
  return {status:'STOP_RETAINED_NO_RETRY',author:config.author,reason:String(reason),plan,active,observed,secondary,raw,packets,own_future_return:'NOT_CLAIMED'};
 }
 try{
  if((!config.formal&&config.author==='independent')||(config.formal&&config.author==='producer')){
   const wholeStart=now();need(wholeStart>=GLOBAL_START&&wholeStart+4500000+7200000<=GLOBAL_END,'new whole4500/result reserve unavailable');
   if([cycle.ID,cycleR1.ID].includes(ID)){
    const note=await command([PYTHON,'-I',filer,'dispatch-note','--root',config.root],{deadline:wholeStart+30000,max:3000});
    need(JSON.parse(note.stdout).status==='COORDINATOR_NOTE_RETAINED','paired launch note missing');
   }
   const words=[PYTHON,'-I',control,config.formal?'activate-formal':'prepare-rehearsal','--root',config.root,'--registration-certificate-sha',config.registration_certificate_sha,'--registration-finalize-actual-sha',config.registration_finalize_actual_sha];
   if(!config.formal)words.push('--formal-registration-certificate-sha',config.formal_registration_certificate_sha,'--formal-registration-finalize-actual-sha',config.formal_registration_finalize_actual_sha);
   words.push('--whole-start-ms',String(wholeStart));
   const actual=await command(words,{deadline:wholeStart+30000,max:4000});packets.activation=actual.packet;
   const value=JSON.parse(actual.stdout);need(value.formal_authority===config.formal,'initial scope differs');
   {
    const saved=await persist(actual.packet,'activation-actual');packets.activation_filed=true;
    const released=await command([PYTHON,'-I',filer,'activate-release','--root',config.root,'--plan-sha',value.plan_sha256,'--packet',saved.path,'--packet-sha',saved.sha256],{deadline:wholeStart+30000,max:3000});
    need(JSON.parse(released.stdout).status==='PAIRED_PERSISTED','formal actual activation release incomplete');
   }
   await get('plan');need(value.plan_sha256===plan.plan_sha256,'initial plan hash differs');
  }else await get('plan');
  const schedule=config.author==='independent'?[[ROLES[0],null],[ROLES[2],ROLES[1]],[ROLES[4],ROLES[3]]]:[[ROLES[1],ROLES[0]],[ROLES[3],ROLES[2]],[ROLES[5],ROLES[4]]];
  for(const [role,previous] of schedule){const proofs=previous?(await get(previous)).proofs:[];launchGate(plan,role,proofs,now());await runRole(role);if(packets.activation&&!packets.activation_filed){await persist(packets.activation,'activation-actual');packets.activation_filed=true;}}
  if(config.author==='producer'){
   await runRole('final-filing');await runRole('lease-release');
   const result=await complete(roleArgv(config.formal?'certify-input-version':'certify-rehearsal','certificate'),{deadline:plan.whole_end_ms});
   const saved=await persist(result.packet,'certificate-actual',config.formal?null:PUBLIC+'/certify-rehearsal-raw-actual-call.json');
   packets.certificate={...saved,packet:result.packet};need(successful(result),'certificate actual return rejected');
  }
  return {status:'OWNED_COMPLETE_ACTUAL_RETURN_PENDING',author:config.author,plan,observed,raw,packets,own_future_return:'NOT_CLAIMED'};
 }catch(error){return stop(error);}
}
