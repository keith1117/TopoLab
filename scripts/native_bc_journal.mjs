// Reconstruct the API caller's original envelope from its closed data journals.
// A digest returned to the caller at each write anchors the next event.
import {createHash} from 'node:crypto';

const hash = raw => createHash('sha256').update(raw).digest('hex');
const hex = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
const need = (condition, message) => { if (!condition) throw Error(message); };
const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);
const maxResponses = 4096;
const maxJournalBytes = 4 * 1024**2;

export const journalJSON = value => Buffer.from(JSON.stringify(value).replace(/[^\x00-\x7f]/g,
  c => '\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'))+'\n','ascii');

function startDigest(binding) {
  return hash(journalJSON(['topolab.native-bc.tool-journal.v1',binding.contractSHA256,
    binding.author,binding.role,binding.label,binding.argv,binding.cwd]));
}

export function journalLink(binding,index,kind,raw,previous) {
  need(Number.isSafeInteger(index) && index >= 0 && index < maxResponses &&
    ['intent','returned'].includes(kind),'invalid journal sequence');
  const start = index === 0 && kind === 'intent';
  need(start ? previous === null : hex(previous),'missing original caller journal commitment');
  return hash(journalJSON([start ? startDigest(binding) : previous,index,kind,raw.length,hash(raw)]));
}

function parseOriginal(raw) {
  const value = JSON.parse(raw.toString('utf8'));
  need(raw.equals(journalJSON(value)),'noncanonical or duplicate-key journal');
  return value;
}

function literalCommand(argv) {
  const names=['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'];
  const quote=word=>/^[a-zA-Z0-9_@%+=:,./-]+$/.test(word)?word:"'"+word.replaceAll("'","'\"'\"'")+"'";
  return 'exec '+['env',...names.map(k=>k+'=1'),...argv].map(quote).join(' ');
}

function checkRequest(args,binding) {
  need(same(Object.keys(args).sort(),
    ['cmd','justification','max_output_tokens','sandbox_permissions','workdir','yield_time_ms']) &&
    args.cmd===literalCommand(binding.argv) && args.workdir===binding.cwd &&
    args.sandbox_permissions==='require_escalated' && typeof args.justification==='string' &&
    args.justification.length>0 && args.max_output_tokens===16000 && args.yield_time_ms===1000,
    'journal original frozen exec request differs');
}

function checkRow(intent,row,index,count,binding,session,priorEnd) {
  const expectedTool = index===0 ? 'exec_command' : 'write_stdin';
  need(same(Object.keys(intent),['tool','arguments','intent_ms']) &&
    same(Object.keys(row),['tool','arguments','requested_ms','returned_ms','result']) &&
    intent.tool===expectedTool && row.tool===expectedTool && same(intent.arguments,row.arguments),
    'journal intent/original request differs');
  need(Number.isSafeInteger(intent.intent_ms) && Number.isSafeInteger(row.requested_ms) &&
    Number.isSafeInteger(row.returned_ms) && priorEnd<=intent.intent_ms &&
    intent.intent_ms<=row.requested_ms && row.requested_ms<=row.returned_ms,
    'journal original clock sequence differs');
  if(index===0) checkRequest(row.arguments,binding);
  else need(same(row.arguments,{session_id:session,chars:'',yield_time_ms:30000,max_output_tokens:16000}),
    'journal poll arguments or session differ');
  const result=row.result;
  need(result && typeof result.output==='string' && typeof result.chunk_id==='string' &&
    Number.isFinite(result.wall_time_seconds) && result.wall_time_seconds>=0,
    'missing original tool return');
  if(index===count-1) need(Number.isInteger(result.exit_code) && result.session_id==null,
    'journal has no actual terminal exit');
  else need(Number.isSafeInteger(result.session_id) && result.session_id>0 && result.exit_code==null &&
    (index===0 || result.session_id===session),'journal live return/session differs');
}

export async function replayJournal(binding,count,commitment,readPairMember) {
  need(hex(binding.contractSHA256) && Number.isSafeInteger(count) && count>0 &&
    count<=maxResponses && hex(commitment),'invalid final journal count or commitment');
  let previous=null,session=null,priorEnd=0,bytes=0;
  const responses=[];
  for(let index=0;index<count;index++){
    const pair=[];
    for(const kind of ['intent','returned']){
      const remaining=binding.byteCap-bytes;
      need(remaining>0,'journal exceeds contract metadata bound');
      const raw=await readPairMember(index,kind,Math.min(maxJournalBytes,remaining));
      bytes+=raw.length;
      need(bytes<=binding.byteCap && raw.length<=maxJournalBytes,'journal exceeds contract metadata bound');
      previous=journalLink(binding,index,kind,raw,previous);
      pair.push(parseOriginal(raw));
    }
    const [intent,row]=pair;
    checkRow(intent,row,index,count,binding,session,priorEnd);
    responses.push(row);
    priorEnd=row.returned_ms;
    session=row.result.session_id;
  }
  need(previous===commitment,'original caller journal commitment differs');
  return {schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',author:binding.author,
    argv:binding.argv,request:responses[0].arguments,responses};
}
