// Close an already stopped C command from the tool caller's actual terminal and
// immutable control files. This receipt never grants a successor or a lease.
import {createHash} from 'node:crypto';

const MiB=1024**2;
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const requireValue=(ok,message)=>{if(!ok) throw Error(message);};

function times(actual) {
  requireValue(actual.responses.length>0,'missing original tool responses');
  let previous=0;
  for(const [i,response] of actual.responses.entries()) {
    requireValue(Number.isSafeInteger(response.requested_ms)&&Number.isSafeInteger(response.returned_ms)&&
      previous<=response.requested_ms&&response.requested_ms<=response.returned_ms,'invalid actual tool clock');
    if(i===0) requireValue(response.tool==='exec_command','first actual tool');
    else requireValue(response.tool==='write_stdin'&&
      response.arguments.session_id===actual.responses[i-1].result.session_id&&
      actual.responses[i-1].result.exit_code==null,'stopped native session continuity');
    previous=response.returned_ms;
  }
  const last=actual.responses.at(-1);
  requireValue(Number.isInteger(last.result.exit_code)&&last.result.session_id==null,'terminal required');
  return [actual.responses[0].requested_ms,last.returned_ms];
}

async function sharedPeak(c,sha,role,read,observer) {
  const spec=c.roles[role],reservation=c.shared_helpers[role].reservation;
  const pub=JSON.parse(await read(spec.publication_return_path));
  const event=JSON.parse(await read(spec.root+'/reservation-return.json'));
  const publication=observer.auditClockWatch(c,sha,role,'publication',
    await read(spec.publication_profile_path+'.resource.json',4*MiB,pub.publication_resource_sha256),
    await read(spec.publication_profile_path,MiB,pub.profile_sha256),
    await read(spec.publication_readiness_path,4*MiB,pub.stdout_sha256),pub.start_seconds,pub.end_seconds);
  const reserve=observer.validateDispatch(c,role,'reservation',{
    contract_sha256:sha,event,dispatch:await read(reservation.dispatch_path,MiB,event.dispatch_stdout_sha256),
    preflush:await read(reservation.dispatch_path.replace(/\.json$/,'-preflush.json')),
    profile:await read(reservation.profile_path,MiB,event.profile_sha256),
    log:await read(reservation.log_path,4*MiB,event.stdout_sha256),
  });
  requireValue(pub.complete&&pub.exit_code===0&&pub.end_seconds<=event.start_seconds,'stopped role prerequisites');
  return {peak_bytes:Math.max(publication.rss_bytes,reserve.peak_bytes),
    start_ms:Math.round(pub.start_seconds*1000),end_ms:Math.round(event.end_seconds*1000)};
}

export async function stoppedController(s,role,actual,actualRaw,read,observer) {
  const c=s.contract,sha=s.contractSHA256,spec=c.roles[role],outerSpec=spec.native_dispatch.controller;
  const [start,end]=times(actual);
  const dispatch=Buffer.from(actual.responses.map(r=>r.result.output).join(''),'ascii');
  const rawRecord=await read(outerSpec.dispatch_path,MiB,digest(dispatch));
  requireValue(rawRecord.equals(dispatch),'tool output differs from stopped native packet');
  const original=observer.lossless(dispatch,true).value;
  const event={start_seconds:start/1000,end_seconds:end/1000,dispatch_argv:actual.argv,
    actual_tool_exit_code:actual.responses.at(-1).result.exit_code};
  const profile=await read(outerSpec.profile_path,MiB,original.profile_sha256);
  const outerLog=await read(outerSpec.log_path,4*MiB,original.log_sha256);
  const outer=observer.auditStoppedController(c,role,{contract_sha256:sha,event,dispatch,profile,log:outerLog,
    preflush:await read(outerSpec.dispatch_path.replace(/\.json$/,'-preflush.json'))});

  const headerRaw=await read(spec.root+'/controller-stop-metadata.json',64*1024);
  const header=observer.lossless(headerRaw,true).value;
  requireValue(header.schema==='topolab.c-controller-stop-metadata.v1'&&header.status==='STOP_NO_RETRY'&&
    header.role===role&&header.contract_sha256===sha&&outerLog.includes(headerRaw),'stopped controller header binding');
  const startSpec=spec.inner_starts[0],base=spec.root+'/native/'+startSpec.name+'/';
  const recordRaw=await read(base+'command.json',128*MiB);
  const record=observer.lossless(observer.compactLexemes(recordRaw),true).value;
  const innerProfile=await read(base+'command.time',MiB,record.profile_sha256);
  const innerLog=await read(base+'command.log',4*MiB,record.log_sha256);
  const helpers={};
  requireValue(Array.isArray(record.helpers)&&record.helpers.length<=65536,'stopped payload sampler count');
  for(const [i,h] of record.helpers.entries()) {
    requireValue(h.profile==='sampler-'+i+'.time','stopped payload sampler path');
    helpers[h.profile]=await read(base+h.profile,MiB,h.profile_sha256);
  }
  const inner=observer.auditStoppedPayload(record,innerProfile,innerLog,helpers,startSpec,c,sha);
  const prior=await sharedPeak(c,sha,role,read,observer);
  const cStart=JSON.parse(await read(s.root+'/C-clock-start.json'));
  requireValue(cStart.contract_sha256===sha&&Number.isSafeInteger(cStart.start_ms)&&
    cStart.start_ms<=prior.start_ms&&prior.end_ms<=start,'stopped C clock order');
  const total=c.public_row_fixture?20:c.call_plan.references.length+c.call_plan.queries.length;
  const wall=(end-start)/1000,peak=Math.max(inner.peak_bytes+outer.peak_bytes,prior.peak_bytes);
  const progress=stoppedRows(header,total,Math.max(wall,inner.wall_seconds,outer.elapsed_seconds));
  return {
    schema:'topolab.c-caller-controller-stop.v1',status:'STOP_C_CONTROLLER_OBSERVED',
    contract_sha256:sha,role,successor_authorized:false,actual_sha256:digest(actualRaw),
    payload_exit:record.exit_code,controller_exit:original.exit_code,dispatcher_exit:event.actual_tool_exit_code,
    first_error:header.first_error,...progress,
    start_ms:start,end_ms:end,c_start_ms:cStart.start_ms,controller_wall_seconds:wall,
    c_wall_to_return_seconds:(end-cStart.start_ms)/1000,
    inner_peak_bytes:inner.peak_bytes,outer_peak_bytes:outer.peak_bytes,shared_peak_bytes:prior.peak_bytes,
    conservative_recorded_peak_bytes:peak,resource_cap_exceeded:peak>c.resource_limit_bytes,
    controller_profile_sha256:digest(profile),payload_profile_sha256:digest(innerProfile),
    inner_record_sha256:digest(recordRaw),retained_log_sha256:digest(outerLog),
    stdout_observed_bytes:original.stdout_observed_bytes,stdout_retained_bytes:original.stdout_retained_bytes,
    stdout_observed_truncated_bytes:original.stdout_observed_truncated_bytes,
    header_sha256:digest(headerRaw),controller_failure_sha256:header.controller_failure_sha256,
    retained_context_sha256:header.retained_context_sha256,secondary_error_counts:header.secondary_error_counts,
    dispatch_errors:original.cleanup_errors,
  };
}

// Missing row observations do not erase a closed native process, clock or RSS.
// An explicit zero comes from the payload's pre-panel marker or recorded row counters.
export function stoppedRows(header,total,wall) {
  const {attempted_rows:attempts,fully_filed_rows:filed,internal_row_charge_seconds:rowCharge}=header;
  requireValue(header.planned_rows===total&&
    (attempts===null||(Number.isSafeInteger(attempts)&&attempts>=0&&attempts<=total))&&
    (filed===null||(Number.isSafeInteger(filed)&&filed>=0&&filed<=total&&(attempts===null||filed<=attempts)))&&
    header.unattempted_rows===(attempts===null?null:total-attempts)&&
    (rowCharge===null||(Number.isFinite(rowCharge)&&rowCharge>=0)),'stopped row coverage');
  let floor=wall+10;
  if(attempts!==null) floor+=attempts;
  if(rowCharge!==null) floor=Math.max(floor,rowCharge);
  return {
    planned_rows:total,attempted_rows:attempts,fully_filed_rows:filed,current_row:header.current_row,
    unattempted_rows:header.unattempted_rows,internal_row_charge_seconds:rowCharge,
    row_execution_stage:header.row_execution_stage??null,
    row_progress:attempts!==null&&filed!==null?'RECORDED':'UNKNOWN_OR_PARTIAL',
    known_role_charge_seconds:attempts!==null&&rowCharge!==null?floor:null,
    measured_role_charge_lower_bound_seconds:floor,
  };
}
