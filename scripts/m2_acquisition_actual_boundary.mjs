// Actual original-tool boundary for the pure two-author cohort scheduler.
// The dispatcher returns its ORIGINAL request/result/true endpoint row, never a summary.
const R='/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-20261103T173800Z';
const REPO='/private/tmp/topolab-input-certificate-closure-20261104';
const ROOTS=new Set(['/private/tmp/topolab-public-registered-source-acquisition-20261104-v3',...['p17-m2-local-input-version-v8-strict-binding-20261103','p17-m2-local-input-version-v9-strict-binding-remedy-20261103'].map(name=>'/Users/keith1117/Library/Application Support/TopoLab-custody/'+name)]);
const PHYSICAL='/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python';
const quote=s=>"'"+s.replaceAll("'","'\"'\"'")+"'";
const word=s=>/^[A-Za-z0-9_@%+=:,./-]+$/.test(s)?s:quote(s);
export const literalCommand=argv=>'exec '+['env','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1','VECLIB_MAXIMUM_THREADS=1','NUMEXPR_NUM_THREADS=1',...argv].map(word).join(' ');
const require=(condition,reason)=>{if(!condition)throw Error('ACTUAL_BOUNDARY_STOP: '+reason);};
export function createActualBoundary(dispatch,config) {
 const raw=[],packets={},accepted=[];
 let projection;
 const actor=config.author==='independent'?'/root/binding_route_independent_v1':'/root';
 require(['producer','independent'].includes(config.author)&&config.repo===REPO&&config.evidence_root===R&&ROOTS.has(config.root)&&/^[A-Za-z0-9_-]{1,100}$/.test(config.event_prefix),'fixed caller context');
 const control=config.repo+'/scripts/p17_m2_source_acquisition_control.py';
 const filer=config.repo+'/scripts/file_m2_acquisition_event.py';
 const waiter=config.repo+'/scripts/await_m2_acquisition_receipt.py';
 const argv=(mode,role)=>[PHYSICAL,'-I',control,mode,'--root',config.root,'--plan-sha',projection.plan_sha256,'--role',role];
 async function invoke(tool,args){
  const row=await dispatch(tool,args);
  require(row.tool===tool&&JSON.stringify(row.arguments)===JSON.stringify(args)&&Number.isSafeInteger(row.requested_ms)&&Number.isSafeInteger(row.returned_ms)&&row.requested_ms<=row.returned_ms,'original tool row required');
  raw.push(row);return row;
 }
 async function complete(words,{native=false,max=20000}={}){
  const args={cmd:literalCommand(words),workdir:config.repo,login:false,yield_time_ms:1000,max_output_tokens:max,...(native?{sandbox_permissions:'require_escalated',justification:'Run the authorized bounded acquisition role with complete native RSS and exit evidence; no original reads before frozen gates.'}:{})};
  let row=await invoke('exec_command',args),session=row.result.session_id,polls=0;const responses=[row];
  while(session!=null&&row.result.exit_code==null&&polls++<16){
   row=await invoke('write_stdin',{session_id:session,chars:'',yield_time_ms:30000,max_output_tokens:max});responses.push(row);session=row.result.session_id;
  }
  const packet={schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',author:actor,event_id:config.event_prefix+'-'+packets.count++,argv:words,request:args,responses};
  const ended=row.result.session_id==null&&Number.isInteger(row.result.exit_code);
  return {packet,ended,exit_code:row.result.exit_code,stdout:responses.map(x=>x.result.output).join('')};
 }
 packets.count=0;
 async function command(words,options){
  const result=await complete(words,options);
  require(result.ended&&result.exit_code===0,'metadata command did not return0: '+result.stdout);
  return result;
 }
 async function persist(packet,name){
  const result=await command([PHYSICAL,'-I',filer,'persist','--packet-json',JSON.stringify(packet),'--destination',name],{max:2000});
  return JSON.parse(result.stdout);
 }
 async function get(role){
  const result=await command([PHYSICAL,'-I',waiter,'--root',config.root,'--role',role,'--timeout-seconds','160'],{max:4000});
  const value=JSON.parse(result.stdout);
  require(value.source_or_payload_reads===0,'waiter source boundary');
  if(projection)require(value.plan.plan_sha256===projection.plan_sha256,'plan changed while awaiting predecessor');
  else projection=value.plan;
  return value;
 }
 async function prepare(){
  if(config.formal)return (await get('plan')).plan;
  const result=await command([PHYSICAL,'-I',control,'prepare-rehearsal','--root',config.root,'--registration-certificate-sha',config.registration_certificate_sha,'--registration-finalize-actual-sha',config.registration_finalize_actual_sha],{max:2000});
  const small=JSON.parse(result.stdout);
  require(small.formal_authority===false,'public preparation scope');
  const value=await get('plan');require(value.plan.plan_sha256===small.plan_sha256,'actual prepare hash differs');
  // Persisting the prepare courier is deferred until AFTER first SUP to preserve startup reserve.
  packets.prepare=result.packet;return value.plan;
 }
 async function plan(){
  if(config.formal){
   const result=await command([PHYSICAL,'-I',control,'activate-formal','--root',config.root,'--registration-certificate-sha',config.registration_certificate_sha,'--registration-finalize-actual-sha',config.registration_finalize_actual_sha],{max:2000});
   packets.activation=result.packet;
  }
  return (await get('plan')).plan;
 }
 async function roleRun(role){
  const modes={},filingErrors=[];
  for(const mode of ['supervise','record']){
   const result=await complete(argv(mode,role),{native:true});
   modes[mode]=result;
   const path=R+'/'+config.event_prefix+'-'+role+'-'+mode+'-raw-actual-call.json';
   try {
    const saved=await persist(result.packet,path);
    packets[role+'-'+mode]={...saved,packet:result.packet};
    if(packets.prepare&&!packets.prepare_filed){await persist(packets.prepare,R+'/'+config.event_prefix+'-prepare-raw-actual-call.json');packets.prepare_filed=true;}
    require(result.ended,'live original role return retained; no retry');
    await command([PHYSICAL,'-I',filer,'file','--root',config.root,'--plan-sha',projection.plan_sha256,'--role',role,'--event-mode',mode,'--packet',saved.path,'--packet-sha',saved.sha256],{max:2000});
   } catch(error){filingErrors.push({mode,reason:String(error)});}
   require(result.ended,'live original return retained; REC not launched against live SUP');
  }
  require(filingErrors.length===0,'filing failures retained AFTER unique REC: '+JSON.stringify(filingErrors));
  const bound=await command(argv('bind',role));
  const proof=JSON.parse(bound.stdout);
  const ok=modes.supervise.exit_code===0&&modes.record.exit_code===0&&(proof.full_role_evidence_accepted===true||proof.metadata_evidence_accepted===true);
  const result={role,accepted:ok,complete:true,actual_exit_codes:[modes.supervise.exit_code,modes.record.exit_code],T0_ms:modes.supervise.packet.responses[0].requested_ms,T1_ms:modes.record.packet.responses.at(-1).returned_ms,proof,bind_actual:bound.packet};
  accepted.push(result);return result;
 }
 async function certificate(){
  const mode=config.formal?'certify-input-version':'certify-rehearsal';
  const result=await complete(argv(mode,'certificate'));
  const destination=config.formal?R+'/'+config.event_prefix+'-certify-input-version-raw-actual-call.json':config.root+'/certify-rehearsal-raw-actual-call.json';
  const saved=await persist(result.packet,destination);
  require(result.ended&&result.exit_code===0,'certificate STOP retained; never retry');
  return {accepted:true,actual:saved,result:JSON.parse(result.stdout)};
 }
 async function freeze(value){
  // The attempt's data/Native directories stay intact. Save a separate caller failure packet.
  const packet={schema:'topolab.m2-acquisition-caller-failure.v1',author:actor,event_id:config.event_prefix+'-caller-STOP',caller_failure:value,original_rows:raw,own_future_return:'NOT_CLAIMED'};
  await persist(packet,R+'/'+config.event_prefix+'-'+config.author+'-caller-STOP.json');
 }
 return {prepare,plan,wait:async role=>(await get(role)).proofs,run:roleRun,metadata:roleRun,certificate,freeze,raw,packets,accepted};
}
