// Load this function in the actual API caller with its own tools and identity.
// The caller pins the contract, checkout and actor before dispatch. Returned
// clocks are measured here, at the receiving end of each API request.
async function nativeBCDispatch(tools, config) {
  const {role,repo,path,digest,author,release}=config;
  const stage=role==='resource-preflight'?'B':'C';
  const start=Date.now();
  function metadataRequest(code,title) {
    // Every individual tool invocation remains subject to the platform's code
    // review limit, including a metadata-only reinitialization after an idle reset.
    let bytes=0;
    for(const char of code){
      const cp=char.codePointAt(0);
      bytes+=cp<=0x7f?1:cp<=0x7ff?2:cp<=0xffff?3:4;
    }
    if(bytes>64000) throw Error('Metadata call exceeds 64000 UTF-8 bytes; not dispatched');
    return {code,title,timeout_ms:120000};
  }
  async function metadata(expression,title) {
    let result=await tools.mcp__node_repl__js(metadataRequest(expression,title));
    if(result.content.some(item=>item.type==='text'&&item.text.startsWith(
      'Kernel state was reset after inactivity. This code was not executed.'))) {
      // The transport explicitly observed no execution. Rehydrate its read-only
      // bindings before replaying this one undelivered metadata operation.
      result=await tools.mcp__node_repl__js(metadataRequest(
        expression.startsWith(initialize)?expression:initialize+expression,title));
    }
    if(result.isError) throw Error(result.content.map(x=>x.text).join('\n'));
    const line=result.content.find(x=>x.type==='text');
    if(!line)throw Error('metadata API returned no original result');
    return JSON.parse(line.text);
  }
  const args=JSON.stringify, pathToAPIModule='file://'+repo+'/scripts/native_bc_caller.mjs';
  const initialize=`var bcMod=await import(${args(pathToAPIModule)});var bcS=await bcMod.openCaller(${args(path)},${args(digest)},${args(author)});`;
  const begin=role==='scientific-auditor'?'{}':`await bcMod.begin(bcS,${args(stage)},${start},${args(release??null)})`;
  await metadata(initialize+'nodeRepl.write(JSON.stringify('+begin+'))','登记本次调用起点');
  const publicRows=stage==='C'&&await metadata('nodeRepl.write(JSON.stringify(bcS.contract.public_row_fixture))','核对公开行写入夹具');
  const labels=publicRows?['publication','reservation','controller']:['publication','reservation','controller','binder','verifier','final-observer'];
  if(stage==='C'&&!publicRows) labels.push('reader-ack');
  if(role!=='scientific-producer') labels.push('finish');
  const quote=word=>/^[a-zA-Z0-9_@%+=:,./-]+$/.test(word)?word:"'"+word.replaceAll("'","'\"'\"'")+"'";
  const env=['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'];
  let last=null;
  for(const label of labels) {
    await metadata('nodeRepl.write(JSON.stringify(await bcMod.clockGuard(bcS,'+args(role)+','+args(label)+')))','核对下一步的剩余时钟');
    if(label==='finish') await metadata('nodeRepl.write(JSON.stringify(await bcMod.prefix(bcS,'+args(role)+')))','独立核对原始退出和原生计量');
    const argv=await metadata('nodeRepl.write(JSON.stringify(bcMod.argvFor(bcS,'+args(role)+','+args(label)+')))','核对合同登记命令');
    const request={cmd:'exec '+['env',...env.map(k=>k+'=1'),...argv].map(quote).join(' '),workdir:repo,
      sandbox_permissions:'require_escalated',justification:config.justification,
      max_output_tokens:16000,yield_time_ms:1000};
    let count=0,commitment=null,session=null;
    const record=async(index,kind,value)=>{
      const code='nodeRepl.write(JSON.stringify(await bcMod.journal(bcS,'+
        [role,label,index,kind,value,commitment].map(args).join(',')+')))';
      return await metadata(code,'保存本次工具请求与实际返回');
    };
    const recordError=async(index,kind,value,primary)=>{
      try {await record(index,kind,value);}
      catch(secondary){throw Error('primary: '+String(primary)+'; journal filing: '+String(secondary));}
    };
    let tool='exec_command',input=request,result;
    do {
      const index=count;
      try {commitment=await record(index,'intent',{tool,arguments:input,intent_ms:Date.now()});}
      catch(err){
        await recordError(index,'filing-error',{stage:'pre-dispatch intent journal',tool,
          last_observed_session:session,dispatched:false,error:String(err),time_ms:Date.now()},err);
        throw err;
      }
      const requested_ms=Date.now();
      try {
        result=await tools[tool](input);
      } catch(err) {
        await recordError(index,'exception',{tool,arguments:input,requested_ms,returned_ms:Date.now(),
          exception:{name:err.name,message:String(err),stack:err.stack??null},
          last_observed_session:session},err);
        throw err;
      }
      const row={tool,arguments:input,requested_ms,returned_ms:Date.now(),result};
      try {commitment=await record(index,'returned',row);}
      catch(err){
        await recordError(index,'filing-error',{stage:'original return journal',tool,requested_ms,
          returned_ms:row.returned_ms,observed_exit:result.exit_code??null,
          last_observed_session:result.session_id??null,error:String(err),time_ms:Date.now()},err);
        throw err;
      }
      count++;
      session=result.session_id??null;
      if(session!==null&&result.exit_code==null) {
        tool='write_stdin';input={session_id:session,chars:'',yield_time_ms:30000,max_output_tokens:16000};
      }
    } while(session!==null&&result.exit_code==null);
    const store='nodeRepl.write(JSON.stringify(await bcMod.receive(bcS,'+
      [role,label,count,commitment].map(args).join(',')+')))';
    try {last=await metadata(store,'保存并核验调用方原始返回');}
    catch(err){
      await recordError(count,'filing-error',{error:String(err),time_ms:Date.now()},err);
      throw Error(role+'/'+label+' exit='+String(result.exit_code)+' '+String(err)+' '+result.output.slice(-1500));
    }
  }
  return last;
}
