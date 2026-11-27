import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import test from 'node:test';
import {journalJSON,journalLink,replayJournal} from '../scripts/native_bc_journal.mjs';

const role='scientific-producer', label='controller';
const cwd='/public-fixture',sha='1'.repeat(64);
const binding={contractSHA256:sha,author:'/root',role,label,cwd,
  argv:['/python','-I','/public/tool','--contract-sha',sha],byteCap:128*1024**2};
const environment='exec env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 ';
const request={cmd:environment+binding.argv.join(' '),workdir:cwd,sandbox_permissions:'require_escalated',
  justification:'公开夹具',max_output_tokens:16000,yield_time_ms:1000};
const poll={session_id:73,chars:'',yield_time_ms:30000,max_output_tokens:16000};

function fixture(count=217) {
  return Array.from({length:count},(_,i)=>{
    const tool=i===0?'exec_command':'write_stdin',args=i===0?request:poll;
    const result={chunk_id:'chunk-'+i,wall_time_seconds:0.025,
      ...(i===count-1?{exit_code:0}:{session_id:73}),original_token_count:65,
      output:i===0?'literal data: ` \u2028 " $ 不作为命令':'public output '.repeat(14)};
    return [{tool,arguments:{...args},intent_ms:1000+3*i},
      {tool,arguments:{...args},requested_ms:1001+3*i,returned_ms:1002+3*i,result}];
  });
}
const member=(rows,i,kind)=>journalJSON(rows[i][kind==='intent'?0:1]);
function chain(rows,who=binding) {
  let h=null;
  for(let i=0;i<rows.length;i++)for(const kind of ['intent','returned'])
    h=journalLink(who,i,kind,member(rows,i,kind),h);
  return h;
}
function replay(rows,commitment=chain(rows),who=binding,reader=(i,k)=>member(rows,i,k)) {
  return replayJournal(who,rows.length,commitment,reader);
}
test('217 timed originals reconstruct the exact complete caller envelope bytes',async()=>{
  const rows=fixture(),original={schema:'topolab.v2.m2-strict-source-binding.actual-call.v1',
    author:binding.author,argv:binding.argv,request,responses:rows.map(pair=>pair[1])};
  assert.ok(journalJSON(original).length>64000);
  const rebuilt=await replay(rows);
  assert.deepEqual(journalJSON(rebuilt),journalJSON(original));
});
test('missing, replaced and reordered pairs and wrong bindings cannot close',async()=>{
  const rows=fixture(3),h=chain(rows);
  await assert.rejects(replay(rows,h,binding,(i,k)=>{
    if(i===1&&k==='intent')throw Error('ENOENT');return member(rows,i,k);
  }),/ENOENT/);
  rows[1][1].result.output+='X';
  await assert.rejects(replay(rows,h),/commitment/);
  for(const change of [{contractSHA256:'2'.repeat(64)},{author:'/root/other'},
    {role:'scientific-auditor'},{label:'binder'},{cwd:'/different'}]) {
    const valid=fixture(3);
    await assert.rejects(replay(valid,chain(valid),{...binding,...change}),/commitment|frozen exec/);
  }
  rows[1].reverse();
  await assert.rejects(replay(rows),/intent/);
});
test('semantically invalid bytes are refused even when rehashed',async()=>{
  const changes=[
    r=>{r[1][0].arguments.session_id=r[1][1].arguments.session_id=88;},
    r=>{r[1][1].arguments.max_output_tokens=100;},
    r=>{r[0][0].arguments.cmd=r[0][1].arguments.cmd='exec /not-registered';},
    r=>{r[0][1].result.exit_code=0;},
    r=>{r[2][1].result.session_id=73;},
    r=>{r[2][1].requested_ms=r[1][1].returned_ms-1;},
  ];
  for(const change of changes){const rows=fixture(3);change(rows);await assert.rejects(replay(rows));}
  const rows=fixture(3); rows[2][1].result.exit_code=-15;
  assert.equal((await replay(rows)).responses.at(-1).result.exit_code,-15);
});

test('the reviewed driver sends a fixed final invocation for a long sequence',async()=>{
  const code=await fs.readFile(new URL('../scripts/native_bc_api_driver.js',import.meta.url),'utf8');
  const run=new Function(code+'\nreturn nativeBCDispatch;')();
  const rows=fixture(),meta=[],receives=[],labels=[];
  let position=0,previous=null,current=null;
  const tools={
    mcp__node_repl__js:async({code})=>{
      meta.push(Buffer.byteLength(code));
      let match=code.match(/bcMod\.(journal|receive)\(bcS,(.*)\)\)\)$/s);
      let value=true;
      if(match){
        const [r,l,...args]=JSON.parse('['+match[2]+']');
        const b={...binding,role:r,label:l};
        if(match[1]==='journal'){
          const [i,k,data,h]=args;
          if(k==='intent'&&i===0){position=0;previous=null;current=l;}
          assert.equal(h,previous);
          value=journalLink(b,i,k,journalJSON(data),h);previous=value;
        } else {
          assert.equal(l,current);assert.deepEqual(args,[rows.length,previous]);
          assert.ok(Buffer.byteLength(code)<256);receives.push(code);labels.push(l);
        }
      } else if(code.includes('bcS.contract.public_row_fixture'))value='rows-positive';
      else if(code.includes('bcMod.argvFor'))value=binding.argv;
      return {content:[{type:'text',text:JSON.stringify(value)}]};
    },
    exec_command:async()=>rows[position++][1].result,
    write_stdin:async()=>rows[position++][1].result,
  };
  await run(tools,{repo:cwd,path:'/public-fixture/contract.json',digest:sha,role,
    author:binding.author,justification:'公开夹具'});
  assert.deepEqual(labels,['publication','reservation','controller']);
  assert.equal(receives.length,3);
  assert.ok(Math.max(...meta)<64000);
});
