// Actual API caller ingress only; never launches a process or reads scientific inputs.
import * as fs from 'node:fs/promises';
import {constants as flags} from 'node:fs';
import * as crypto from 'node:crypto';
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const need = (value, reason) => { if (!value) throw Error(reason); };
const resolve = (argv, sha) => argv.map(word => word.replaceAll('@SCIENTIFIC_CONTRACT_SHA256@', sha));
const roles = ['resource-preflight','scientific-producer','scientific-auditor'];
const labels = ['controller','binder','verifier','final-observer'];
const parents = ['/private/tmp/topolab-funded-continuation-20261026',
  '/private/tmp/topolab-new-source-science-20261028'];
async function put(path, raw) {
  const evidence={path,bytes:raw.length,sha256:hash(raw),stage:'literal-output',parent_observations:[],secondary_errors:[]};
  let handle,directory,problem=null;
  try {
    need(parents.some(parent=>path.startsWith(parent+'/'))&&!path.split('/').slice(1).some(word=>!word||word==='..'||word==='.'), 'unregistered NEW metadata output');
    evidence.stage='output-parents';let component='';
    for(const word of path.split('/').slice(1,-1)){
      component+='/'+word;const s=await fs.lstat(component,{bigint:true});
      evidence.parent_observations.push({path:component,dev:String(s.dev),inode:String(s.ino),mode:String(s.mode)});
      need(s.isDirectory()&&!s.isSymbolicLink(),'output parent symlink/non-directory');
    }
    evidence.stage='exclusive-create';handle=await fs.open(path,flags.O_WRONLY|flags.O_CREAT|flags.O_EXCL|flags.O_NOFOLLOW,0o600);
    evidence.stage='write-and-sync';await handle.writeFile(raw);await handle.sync();
    evidence.stage='directory-sync';directory=await fs.open(path.slice(0,path.lastIndexOf('/')),flags.O_RDONLY|flags.O_DIRECTORY|flags.O_NOFOLLOW);await directory.sync();
  } catch(error){problem=error;}
  finally {
    for(const [stage,h] of [['close-output',handle],['close-directory',directory]])if(h)try{await h.close();}catch(error){evidence.secondary_errors.push({stage,type:error.name,reason:error.message});problem??=error;}
  }
  if(problem){evidence.raw_output_base64=raw.toString('base64');problem.metadata_output_failure=evidence;throw problem;}
  return {path,bytes:raw.length,sha256:hash(raw)};
}
function actual({result,start_seconds,end_seconds}) {
  need(Number.isInteger(result.exit_code)&&result.session_id===undefined,'actual complete tool return required');
  need(Number.isFinite(start_seconds)&&Number.isFinite(end_seconds)&&0<=start_seconds&&start_seconds<=end_seconds,'actual tool clock required');
  return {complete:true,exit_code:result.exit_code,start_seconds,end_seconds};
}
export async function publicationReturn({contract,contractSHA256,role,result,start_seconds,end_seconds,actualArgv}) {
  need(roles.includes(role),'registered role');
  need(Array.isArray(actualArgv),'actual called argv required');
  const event={...actual({result,start_seconds,end_seconds}),argv:actualArgv,registered_argv_intent:resolve(contract.roles[role].publication_argv,contractSHA256),stdout_sha256:hash(Buffer.from(result.output,'utf8')),observer:'actual complete functions exec_command tool return; original stdout bytes'};
  const spec=contract.roles[role],proof=Buffer.from(result.output,'utf8');
  const proofReceipt=await put(spec.publication_readiness_path,proof);
  const eventReceipt=await put(spec.publication_return_path,Buffer.from(JSON.stringify(event)+'\n'));
  return {event,proofReceipt,eventReceipt,native_helpers_spawned:0};
}
export async function nativeReturn({contract,contractSHA256,role,label,result,start_seconds,end_seconds,observer,publicationSHA256,outputOverride,actualArgv}) {
  need(roles.includes(role)&&[...labels,'reservation','reader-ack'].includes(label),'registered native return');
  need(!outputOverride||contract.public_fixture_only===true,'formal return path override forbidden');
  const completed=actual({result,start_seconds,end_seconds}),packetRaw=Buffer.from(result.output,'utf8');
  need(packetRaw.length<=1024**2&&Array.isArray(actualArgv),'complete bounded dispatch stdout and actual called argv required');
  const shared=['reservation','reader-ack'].includes(label);
  const spec=shared?contract.shared_helpers[role][label]:contract.roles[role].native_dispatch[label];
  let packet=null,packetError=null;
  try { packet=observer.lossless(packetRaw,true).value; } catch(error) { packetError={type:error.name,reason:error.message}; }
  const event={...completed,argv:packet?.argv??null,dispatch_argv:actualArgv,registered_argv_intent:resolve(shared?spec.argv:contract.roles[role].exit_argv[label],contractSHA256),registered_dispatch_argv_intent:resolve(spec.dispatch_argv,contractSHA256),dispatch_stdout:packetRaw.toString('utf8'),dispatch_stdout_sha256:hash(packetRaw),dispatcher_exit:result.exit_code,actual_tool_exit_code:result.exit_code,stdout_sha256:packet?.log_sha256??null,profile_sha256:packet?.profile_sha256??null,observer:'actual functions exec_command/write_stdin complete tool return; exact original dispatcher stdout retained'};
  if(packetError)event.packet_parse_error=packetError;
  if(label==='reservation') { event.pending_sha256=packet?.log_sha256??null; event.publication_readiness_sha256=publicationSHA256??null; }
  const receipt=await put(outputOverride??contract.roles[role].root+'/'+label+'-return.json',Buffer.from(JSON.stringify(event)+'\n'));
  return {event,receipt,native_helpers_spawned:0};
}
export async function trustedReturns({contract,role,events}) {
  need(roles.includes(role)&&events.length===4&&events.every(event=>event.complete===true),'four actual outer returns required');
  return put(contract.roles[role].root+'/trusted-returns.json',Buffer.from(JSON.stringify(events)+'\n'));
}
