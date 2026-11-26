// Exercise the original native public predecessor chain and the shared role transport.
export async function publicCloseout(config, host, shared) {
  const {root, control, python, checkout, mode, end} = config;
  const roles = ['independent-public-check','exporter-r0','independent-r0','exporter-r1','independent-r1','shared-closeout'];
  const caps = [300,300,300,1200,1200,300];
  const rolesResult = {};
  const calls = {};
  const controlled = [];
  const require = (condition, reason) => { if (!condition) throw Error(reason); };
  const begin = Date.now();
  let role = null, stage = 'prepare', roleDeadline = end;
  const native = [python,'-I',control];
  const argumentsFor = (op, tail) => [...native,op,'--root',root,...tail];
  function record(id, argv, rows) {
    calls[id] = {schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',author:'/root/closeout_public',
      event_id:id,argv,request:rows[0].arguments,responses:rows};
    return calls[id];
  }
  async function run(id, argv, {supervise = false, deadline = roleDeadline} = {}) {
    stage = id;
    const request = {cmd:shared.literalCommand(argv),workdir:checkout,login:false,
      yield_time_ms:supervise?1000:30000,max_output_tokens:6000};
    if (supervise) Object.assign(request,{sandbox_permissions:'require_escalated',
      justification:'允许在全新公开合成夹具中运行冻结原生监督器，并读取该夹具进程组的资源回执吗？'});
    const rows=[];
    function checkResult(row, ownedSession) {
      const r=row.result;
      require(r && typeof r.output==='string' && !r.output.includes('tokens truncated') &&
        !r.output.includes('Warning: truncated output') && (r.original_token_count==null ||
        (Number.isInteger(r.original_token_count) && r.original_token_count<=request.max_output_tokens)),
      'incomplete '+id);
      if (r.session_id!=null) {
        require(Number.isInteger(r.session_id) && r.session_id===ownedSession && r.exit_code==null,
          'owned session drift/type '+id);
      } else {
        require(Number.isInteger(r.exit_code),'actual terminal exit required '+id);
      }
    }
    let row;
    try {
      let clock=Date.now();
      require(clock<deadline,'public dispatch deadline exhausted');
      row=await host.invoke('exec_command',request); rows.push(row);
      const ownedSession=row.result?.session_id;
      checkResult(row,ownedSession);
      while (row.result.session_id!=null) {
        const now=Date.now();
        require(now>=clock,'backwards caller clock');
        clock=now;
        const remaining=deadline-now;
        require(remaining>=5000,'original polling window exhausted');
        require(rows.length<65,'public poll budget exhausted');
        row=await host.invoke('write_stdin',{session_id:ownedSession,chars:'',
          yield_time_ms:Math.min(30000,remaining),max_output_tokens:6000});
        rows.push(row);
        checkResult(row,ownedSession);
      }
      require(row.returned_ms<=deadline && row.result.exit_code===0, 'late or failed '+id);
    } finally {
      if (rows.length) record(id,argv,rows);
    }
    return {packet:calls[id],value:JSON.parse(rows.map(r=>r.result.output).join('')),
      first:rows[0].requested_ms,last:row.returned_ms};
  }
  async function courier(id, args, actual) {
    stage = id;
    const argv=argumentsFor('persist-closeout-record',args);
    const rows=[];
    try {
      const saved=await shared.retainCloseoutRecord({argv,workdir:checkout,packet:actual.packet,
        deadline:roleDeadline,invoke:async(tool,args)=>{
          const row=await host.invoke(tool,args);
          // A real, controlled transport delivery delay occurs after the underlying tool
          // has returned its terminal result. Keep both observations in separate fields.
          if (mode==='late' && row.result?.exit_code===0 && row.result.session_id==null) {
            const underlying=row.returned_ms;
            while (Date.now()<=roleDeadline) await host.wait(Math.min(10000,roleDeadline+25-Date.now()));
            controlled.push({tool,underlying_tool_returned_ms:underlying,
              caller_delivery_ms:Date.now(),stage:id});
            rows.push(row);
            return row;
          }
          rows.push(row); return row;
        }});

      return saved;
    } finally {
      if (rows.length) record(id,[...argv,'--deadline-ms',String(roleDeadline)],rows);
    }
  }
  try {
    const prepared=await run('prepare',argumentsFor(mode==='late'?'prepare-replay':'prepare-public',[]));
    if (mode==='late') {
      role='shared-closeout';
      const source=prepared.value;
      require(source.formal_authority===false && source.scope==='PUBLIC_CLOSEOUT_RECEIPT_REPLAY_ONLY',
        'sealed positive public controls required');
      const entered=Date.now();
      roleDeadline=Math.min(end,entered+290000);
      rolesResult[role]={entered_ms:entered,deadline_ms:roleDeadline,source_plan:source.origin.plan_sha256,
        native_replay:true,origin_slot:source.origin.slot};
      await shared.dispatchRoleEvents({
        dispatch:async op=>({packet:source.original_returns[op]}),
        retain:async(op,actual)=>{
          if(op!=='record') return;
          return courier(role+'-persist-record',['--plan-sha',source.origin.plan_sha256,'--role',role,
            '--event-mode',op],actual);
        },
        accept:actual=>actual.packet.responses.at(-1).result.exit_code===0,
        file:async op=>{require(op==='supervise','late recorder reached filing');},
        bind:async()=>{throw Error('late replay reached binder');}
      });
      throw Error('late replay did not stop');
    }
    const plan=prepared.value.plan_sha256;
    require(/^[0-9a-f]{64}$/.test(plan) && prepared.value.formal_authority===false,'public plan required');
    for (let i=0;i<roles.length;i++) {
      role=roles[i];
      const entered=Date.now();
      roleDeadline=Math.min(end,entered+caps[i]*1000-10000);
      const info=rolesResult[role]={entered_ms:entered,deadline_ms:roleDeadline};
      const tail=['--plan-sha',plan,'--role',role];
      const bound=await shared.dispatchRoleEvents({
        dispatch: op=>run(role+'-'+op,argumentsFor(op,tail),{supervise:op==='supervise'}),
        async retain(op, actual) {
          const id=role+'-persist-'+op; stage=id;
          const args=[...tail,'--event-mode',op];
          if (role==='shared-closeout' && op==='record') {
            const saved=await courier(id,args,actual);
            info.courier=saved; return saved;
          }
          const saved=await run(id,argumentsFor('persist-public',[...args,'--packet-json',JSON.stringify(actual.packet)]));
          require(saved.value.status==='PAIRED_PERSISTED', 'incomplete original custody');
          return saved.value;
        },
        accept:actual=>actual.packet.responses.at(-1).result.exit_code===0,
        async file(op,saved) {
          return run(role+'-file-'+op,argumentsFor('file-public',[...tail,'--event-mode',op,
            '--packet-sha',saved.sha256,'--intent-sha',saved.file_intent_sha256,'--program-sha',saved.program_sha256]));
        },
        bind:()=>run(role+'-bind',argumentsFor('bind',tail))
      });
      require(bound.value.full_role_evidence_accepted===true,'independent role acceptance failed');
      info.bind_return_ms=bound.last;
      info.remaining_ms=roleDeadline-bound.last;
    }
    return {status:'PASS_PUBLIC_NATIVE_CLOSEOUT',mode,root,begin_ms:begin,end_ms:Date.now(),
      roles:rolesResult,calls,controlled};
  } catch(error) {
    return {status:'STOP_PUBLIC_CLOSEOUT',mode,root,begin_ms:begin,end_ms:Date.now(),
      role,stage,error:String(error),roles:rolesResult,calls,controlled};
  }
}
