import assert from 'node:assert/strict';
import {test} from 'node:test';
import fs from 'node:fs/promises';
import {constants} from 'node:fs';
import crypto from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import * as observer from '../scripts/p17_m2_scientific_metadata.mjs';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const raw = v => Buffer.from(JSON.stringify(v)+'\n');
async function fixture() {
  const root = await fs.mkdtemp(path.join(await fs.realpath(process.env.TOPOLAB_METADATA_TEST_ROOT || os.tmpdir()),'m2-metadata-'));
  const contractPath = path.join(root,'contract.json');
  const bytes = raw({schema:'test-public-contract',public_fixture_only:true});
  await fs.writeFile(contractPath,bytes,{mode:0o600,flag:'wx'});
  return {root,contractPath,contractSHA256:sha(bytes),manifestPath:path.join(root,'manifest.json'),manifestSHA256:'1'.repeat(64),scope:'B',fs,constants,crypto};
}

test('contract-bound interface refuses absent anchors before any filesystem IO',async()=>{
  const noIO = new Proxy({}, {get(){throw Error('UNAUTHORIZED_IO');}});
  await assert.rejects(observer.observeMetadata({fs:noIO,constants,crypto,contractPath:'/absent',contractSHA256:'bad',manifestPath:'/absent',manifestSHA256:'bad',scope:'B'}),/anchor/);
});
test('raw integer nanoseconds retain exact value and string lexemes',()=>{
  const parsed=observer.lossless('{"n":1793041621733057634,"s":"1793041621733057634"}\n');
  assert.equal(parsed.value.n,1793041621733057634n);
  assert.equal(parsed.value.s,'1793041621733057634');
  assert.throws(()=>observer.lossless('{"n":1,"n":2}\n'),/duplicate/);
  assert.throws(()=>observer.lossless('{}{}\n'),/trailing/);
});
test('wrong trusted contract hash rejects with original tuple and complete returned length',async()=>{
  const opts=await fixture();opts.contractSHA256='0'.repeat(64);
  await assert.rejects(observer.observeMetadata(opts),error=>{
    assert.match(error.message,/anchor mismatch/);
    assert.equal(error.metadata_evidence.returned_bytes,61);
    assert.ok(error.metadata_evidence.before.mtime_ns);
    assert.equal(error.metadata_evidence.before.inode,error.metadata_evidence.closing.inode);
    return true;
  });
});
test('missing closing observation preserves prior tuple and primary failure',async()=>{
  const opts=await fixture();let fileStats=0;
  opts.fs=new Proxy(fs,{get(target,key){if(key==='lstat')return async(p,...args)=>{
    if(p===opts.contractPath&&++fileStats===2)throw Object.assign(Error('injected closing unavailable'),{code:'EIO'});
    return target.lstat(p,...args);
  };return Reflect.get(target,key);}});
  await assert.rejects(observer.observeMetadata(opts),error=>{
    assert.match(error.message,/closing observation unavailable/);
    assert.ok(error.metadata_evidence.before);
    assert.equal(error.metadata_evidence.closing,null);
    assert.ok(error.metadata_evidence.secondary_errors.some(x=>x.reason==='injected closing unavailable'));
    return true;
  });
});
test('same-byte inode replacement is rejected at path close',async()=>{
  const opts=await fixture();let fileStats=0;
  opts.fs=new Proxy(fs,{get(target,key){if(key==='lstat')return async(p,...args)=>{
    const stat=await target.lstat(p,...args);
    if(p===opts.contractPath&&++fileStats===2)return new Proxy(stat,{get(s,k){return k==='ino'?s.ino+1n:Reflect.get(s,k);}});
    return stat;
  };return Reflect.get(target,key);}});
  await assert.rejects(observer.observeMetadata(opts),/closing path identity/);
});
test('short read and close error both survive in one retained failure packet',async()=>{
  const opts=await fixture();opts.fs=new Proxy(fs,{get(target,key){if(key==='open')return async(...args)=>{
    const h=await target.open(...args);
    return {stat:(...a)=>h.stat(...a),read:async()=>({bytesRead:0}),close:async()=>{await h.close();throw Error('injected close failure');}};
  };return Reflect.get(target,key);}});
  await assert.rejects(observer.observeMetadata(opts),error=>{
    assert.match(error.message,/short read/);
    assert.equal(error.metadata_evidence.returned_bytes,0);
    assert.ok(error.metadata_evidence.secondary_errors.some(x=>x.reason==='injected close failure'));
    return true;
  });
});
test('non-ASCII numeric/evidence bytes and invalid JSON whitespace are rejected',()=>{
  assert.throws(()=>observer.lossless(Buffer.from([0xfb,0x7d,0x0a])),/ASCII/);
  assert.throws(()=>observer.compactLexemes(Buffer.from('{\v"x":1}\n')),/whitespace/);
});
test('hash failure keeps closing replacement as a secondary error',async()=>{
  const opts=await fixture();opts.contractSHA256='0'.repeat(64);let fileStats=0;
  opts.fs=new Proxy(fs,{get(target,key){if(key==='lstat')return async(p,...args)=>{
    const stat=await target.lstat(p,...args);
    if(p===opts.contractPath&&++fileStats===2)return new Proxy(stat,{get(s,k){return k==='ino'?s.ino+1n:Reflect.get(s,k);}});
    return stat;
  };return Reflect.get(target,key);}});
  await assert.rejects(observer.observeMetadata(opts),error=>{
    assert.match(error.message,/anchor mismatch/);
    assert.ok(error.metadata_evidence.secondary_errors.some(x=>x.stage==='closing_identity'));
    return true;
  });
});
const frozenPredicateKeys=[
  'fixed_H17_zero_failed_attempts_and_fallbacks',
  'all_seven_historical_target_predicates_repaired',
  'historical_49_P_acceptances_preserved',
  'matched_plain_P_and_P_keep_acceptances_preserved',
  'two_old_small_z_negative_failures_retained',
  'fixed_plain_P17_counterexample_retained',
  'primary_target_mean_and_sum_at_most_one',
  'primary_strictly_better_fixed_controls',
  'primary_better_than_W17',
  'primary_each_scale_mean_and_sum_at_most_point_nine',
  'at_least_two_H_seeds_and_fixed_H17_pass',
];
const fixedMethods=['uniform','physics_heuristic','nearest_neighbor','C/17','C/29','C/43','P-keep/17','P-keep/29','P-keep/43','W/17','W/29','W/43','plain-P/17','plain-P/29','plain-P/43','H/17','H/29','H/43','uniform-homotopy'];
function scientificFixture(pass=false) {
  const runtime={python_entry:'/public/python',python_startup_entry:'/public/startup',torch_threads_policy:{intraop:1,interop:8}};
  const contract={runtime},sha='a'.repeat(64),expected={argv:['/public/python','-I','public-reader','@SCIENTIFIC_CONTRACT_SHA256@']};
  const failing=new Set(['fixed_H17_zero_failed_attempts_and_fallbacks','all_seven_historical_target_predicates_repaired','primary_target_mean_and_sum_at_most_one','primary_each_scale_mean_and_sum_at_most_point_nine','at_least_two_H_seeds_and_fixed_H17_pass']);
  const predicates=Object.fromEntries(frozenPredicateKeys.map(k=>[k,pass||!failing.has(k)]));
  const metrics=Object.fromEntries(fixedMethods.map(method=>[method,{mean_ratio:1.2,sum_ratio:1.2,failed_attempts:2}]));
  metrics.uniform={mean_ratio:1,sum_ratio:1,failed_attempts:0};
  metrics['H/17']={mean_ratio:pass?.8:1.1,sum_ratio:pass?.8:1.1,failed_attempts:pass?0:1};
  metrics['H/29']={mean_ratio:.8,sum_ratio:.8,failed_attempts:2};
  metrics['H/43']={mean_ratio:pass?1.1:.8,sum_ratio:pass?1.1:.8,failed_attempts:0};
  metrics.H17_target={mean_ratio:pass?.9:1.1,sum_ratio:pass?.9:1.1,failed_attempts:pass?0:1};
  for(const seed of [17,29,43])for(const scale of ['(12, 6, 3)','(24, 12, 6)'])metrics['H/'+seed+':'+scale]={...metrics['H/'+seed]};
  const status=pass?'SCIENTIFIC_PREDICATES_PASS_PENDING_NATIVE_EXIT':'FAIL_SCIENCE_GATE';
  const result={schema:'topolab.v2.m2-scientific-auditor-summary.v1',execution_identity:'topolab.v2.p17-m2-native-homotopy.rss.v1',scientific_contract_sha256:sha,status,attempted_rows:360,completed_rows:360,internal_row_charge_seconds:1,own_resource_and_actual_exit:'PENDING_INDEPENDENT_NATIVE_OUTER_RETURN',seed17_repaired:'NOT_ESTABLISHED_BEFORE_OWN_NATIVE_RETURN',decision:{outcome_status:status,scientific_predicates_passed:pass,predicates,failed_predicates:frozenPredicateKeys.filter(k=>!predicates[k]),passing_H_seeds:pass?[17,29]:[29,43],seed_gate_results:{'H/17':pass,'H/29':true,'H/43':!pass},metrics,resource_and_actual_return:'NOT_ESTABLISHED_BY_METRIC_ARITHMETIC'}};
  const payload={result,actual_numerical_runtime:{...runtime,startup_orig_argv:['/public/startup','-I','public-reader',sha],torch_threads:runtime.torch_threads_policy}};
  return {contract,sha,expected,payload};
}
test('valid independent scientific FAIL is retained after a successful program exit',()=>{
  const f=scientificFixture(),result=observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected);
  assert.equal(result.status,'FAIL_SCIENCE_GATE');assert.equal(result.scientific_predicates_passed,false);assert.equal(result.seed17_repaired,false);
  assert.equal(result.metrics['H/17'].failed_attempts,1);
});
test('incomplete independent population or fabricated PASS never establishes repair',()=>{
  let f=scientificFixture();f.payload.result.completed_rows=359;
  assert.throws(()=>observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected),/pending own native return/);
  f=scientificFixture();f.payload.result.status='SCIENTIFIC_PREDICATES_PASS_PENDING_NATIVE_EXIT';
  assert.throws(()=>observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected),/outcome status/);
});
test('independent failed predicate order is retained across canonical key sorting',()=>{
  const f=scientificFixture();f.payload.result.decision.predicates=Object.fromEntries(Object.entries(f.payload.result.decision.predicates).sort());
  f.payload.result.decision.failed_predicates.reverse();
  const wanted=[...f.payload.result.decision.failed_predicates];
  const result=observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected);
  assert.deepEqual(result.failed_predicates,wanted);assert.equal(result.seed17_repaired,false);
});
test('duplicate passing seed identifiers cannot satisfy two-seed acceptance',()=>{
  const f=scientificFixture(true),d=f.payload.result.decision;d.passing_H_seeds=[17,17];
  assert.throws(()=>observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected),/seed/);
});
const limits={max_files:65536,max_total_bytes:536870912,max_record_bytes:134217728,max_log_bytes:4194304,max_profile_bytes:1048576,max_manifest_bytes:16777216,max_contract_bytes:4194304};
const canonical=value=>value===null?'null':Array.isArray(value)?'['+value.map(canonical).join(',')+']':typeof value==='object'?'{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}':JSON.stringify(value);
function publicationFixture(main='8366b260650cdb67ea9d299813d78526d5da0572') {
  observer.configure(crypto);
  const role='resource-preflight',digest='a'.repeat(64);
  const spec={publication_readiness_path:'/public/proof.json',publication_return_path:'/public/event.json',publication_argv:['/public/python','publication-check','@SCIENTIFIC_CONTRACT_SHA256@']};
  const contract={roles:{[role]:spec}},fields={source_freeze:raw({source:'fixed'}),runtime:raw({python:'fixed'})};
  const proof={execution_identity:'topolab.v2.p17-m2-native-homotopy.rss.v1',scientific_contract_sha256:digest,role,metadata_only:true,publication_readiness:{main},source_freeze_sha256:sha(fields.source_freeze),runtime_sha256:sha(fields.runtime),start_seconds:10.5,end_seconds:11};
  const proofRaw=Buffer.from(canonical(proof)+'\n');
  const event={complete:true,exit_code:0,argv:['/public/python','publication-check',digest],stdout_sha256:sha(proofRaw),start_seconds:10,end_seconds:12};
  const chain={reservation:{event:{start_seconds:12,publication_readiness_sha256:sha(proofRaw)},log:Buffer.from(canonical({publication_readiness:proof})+'\n')}};
  return {proof,event,chain,run:()=>observer.auditPublication(contract,digest,role,chain,async name=>name===spec.publication_readiness_path?proofRaw:raw(event),name=>name,fields)};
}
test('formal publication return accepts the actual 40-hex Git commit format',async()=>{
  await publicationFixture().run();
});
test('formal publication return rejects a content SHA256 used as the Git main identity',async()=>{
  await assert.rejects(publicationFixture('a'.repeat(64)).run(),/publication identity\/main/);
});
test('formal publication return keeps raw proof hashes and fresh actual ordering mandatory',async()=>{
  let f=publicationFixture();f.event.stdout_sha256='0'.repeat(64);
  await assert.rejects(f.run(),/actual fresh publication return/);
  f=publicationFixture();f.chain.reservation.event.start_seconds=43;
  await assert.rejects(f.run(),/actual fresh publication return/);
  f=publicationFixture();f.chain.reservation.event.publication_readiness_sha256='0'.repeat(64);
  await assert.rejects(f.run(),/reservation publication proof anchor/);
});
async function metadataFixture({formal=false,files={},alterPolicy=()=>{}}={}) {
  const root=await fs.mkdtemp(path.join(await fs.realpath(process.env.TOPOLAB_METADATA_TEST_ROOT || os.tmpdir()),'m2-policy-'));
  const contractPath=root+'/contract.json',manifestPath=root+'/B-manifest.json',broot=root+'/B';
  const dispatch=label=>({dispatch_path:broot+'/'+label+'.dispatch.json',profile_path:broot+'/'+label+'.time',log_path:broot+'/'+label+'.log'});
  const policy={schema:'topolab.v2.m2-api-metadata-policy.v1',root,manifests:{B:manifestPath,FINAL:root+'/FINAL-manifest.json'},limits:{...limits},sample_interval_seconds:.5};alterPolicy(policy);
  const contract={schema:'topolab.v2.m2-scientific-contract.v1',execution_identity:'topolab.v2.p17-m2-native-homotopy.rss.v1',public_fixture_only:!formal,permissions:{B:true,C:true},source_freeze:{'scripts/p17_m2_scientific_metadata.mjs':'1'.repeat(64)},runtime:{platform:'darwin'},resource_limit_bytes:4294967296,shared_FULL_seconds:180,api_metadata:policy,roles:{'resource-preflight':{root:broot,FULL_seconds:180,inner_starts:[{name:'success',timeout_seconds:10},{name:'exit-seven',timeout_seconds:10},{name:'timeout',timeout_seconds:1}],native_dispatch:Object.fromEntries(['controller','binder','verifier','final-observer'].map(label=>[label,dispatch(label)])),publication_readiness_path:root+'/B-publication.json',publication_return_path:root+'/B-publication-return.json'}},shared_helpers:{'resource-preflight':{reservation:dispatch('reservation')}}};
  const contractRaw=Buffer.from(canonical(contract)+'\n'),contractSHA256=sha(contractRaw);
  const manifestRaw=Buffer.from(canonical({schema:'topolab.v2.m2-api-metadata-manifest.v1',scope:'B',contract_sha256:contractSHA256,files})+'\n');
  await fs.writeFile(contractPath,contractRaw,{mode:0o600,flag:'wx'});await fs.writeFile(manifestPath,manifestRaw,{mode:0o600,flag:'wx'});
  const opened=[];const traced=new Proxy(fs,{get(target,key){if(key==='open')return async(p,...args)=>{opened.push(p);return target.open(p,...args);};return Reflect.get(target,key);}});
  return {options:{fs:traced,constants,crypto,contractPath,contractSHA256,manifestPath,manifestSHA256:sha(manifestRaw),scope:'B'},opened,root,policy};
}
test('B metadata manifest refuses model/payload paths before file open',async()=>{
  const f=await metadataFixture({files:{'B/models/weight.json':{bytes:1,sha256:'1'.repeat(64)}}});
  await assert.rejects(observer.observeMetadata(f.options),/unregistered metadata member/);
  assert.deepEqual(f.opened,[f.options.contractPath,f.options.manifestPath]);
});
test('B prefix forbids a later scientific role member and oversized sampler index',async()=>{
  for(const rel of ['C/native/payload/command.json','B/controls/success/sampler-999999.time','B/controls/success/sampler-00.time']){
    const f=await metadataFixture({files:{[rel]:{bytes:1,sha256:'1'.repeat(64)}}});
    await assert.rejects(observer.observeMetadata(f.options),/unregistered metadata member/);
    assert.equal(f.opened.length,2);
  }
});
test('missing registered member rejects before role IO',async()=>{
  const f=await metadataFixture();await assert.rejects(observer.observeMetadata(f.options),/missing registered metadata member/);assert.equal(f.opened.length,2);
});
test('contract cannot expand fixed metadata hard ceilings',async()=>{
  const f=await metadataFixture({alterPolicy:p=>p.limits.max_total_bytes*=2});
  await assert.rejects(observer.observeMetadata(f.options),/hard cap/);assert.equal(f.opened.length,1);
});
test('formal contract cannot opt into public fixture policy',async()=>{
  const f=await metadataFixture({formal:true});f.options.publicFixturePolicy=f.policy;
  await assert.rejects(observer.observeMetadata(f.options),/forbids public policy override/);assert.equal(f.opened.length,1);
});
test('multi-megabyte metadata compaction preserves every numeric lexeme',()=>{
  const body='x'.repeat(2*1024*1024),bytes=Buffer.from('{\n  "n": 1793041621733057634,\n  "padding": "'+body+'"\n}\n');
  const compact=observer.compactLexemes(bytes),parsed=observer.lossless(compact);
  assert.equal(parsed.value.n,1793041621733057634n);assert.equal(parsed.value.padding.length,2097152);
  assert.ok(compact.includes(Buffer.from('1793041621733057634')));
});
test('ACK must acknowledge exact raw pending receipt including unsafe nanoseconds',()=>{
  observer.configure(crypto);
  const pending=Buffer.from('{"st_mtime_ns":1793041621733057634}\n'),ack={execution_identity:'topolab.v2.p17-m2-native-homotopy.rss.v1',scientific_contract_sha256:'a'.repeat(64),role:'scientific-auditor',status:'SCIENTIFIC_READER_RETURN_ACKNOWLEDGED',lease_state:'RELEASED',consumer_actual_exit_observed:true,reader_receipt_sha256:sha(pending)};
  observer.validateAck(ack,'a'.repeat(64),'scientific-auditor',pending);
  assert.throws(()=>observer.validateAck(ack,'a'.repeat(64),'scientific-auditor',Buffer.from('{"st_mtime_ns":1793041621733057635}\n')),/pending receipt/);
});
test('lower operation total cap stops before manifest IO when bootstrap already consumes it',async()=>{
  const f=await metadataFixture({alterPolicy:p=>p.limits.max_total_bytes=256});
  await assert.rejects(observer.observeMetadata(f.options),/bootstrap cap/);assert.equal(f.opened.length,1);
});

test('every frozen scientific predicate is required and UNKNOWN or extra keys reject',()=>{
  for(const key of frozenPredicateKeys){
    for(const missing of [true,false]){
      const f=scientificFixture(true);if(missing)delete f.payload.result.decision.predicates[key];else f.payload.result.decision.predicates[key]='UNKNOWN';
      assert.throws(()=>observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected),/predicate/);
    }
  }
  const f=scientificFixture(true);f.payload.result.decision.predicates.unknown_extra=true;
  assert.throws(()=>observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected),/predicate/);
});
test('complete actual metric population and three seed-gate results are required',()=>{
  for(const mutate of [d=>delete d.metrics,d=>delete d.metrics['H/17'],d=>delete d.metrics['H/17:(24, 12, 6)'],d=>d.metrics['H/17'].mean_ratio=NaN,d=>d.metrics['H/17'].sum_ratio=-1,d=>d.metrics['H/17'].failed_attempts=1.5,d=>delete d.seed_gate_results,d=>delete d.seed_gate_results['H/29'],d=>d.seed_gate_results['H/17']='UNKNOWN',d=>d.passing_H_seeds=[17,43]]){
    const f=scientificFixture(true);mutate(f.payload.result.decision);
    assert.throws(()=>observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected),/metric|seed/);
  }
});
test('complete fixed eleven-predicate two-of-three result remains pending native return',()=>{
  const f=scientificFixture(true),result=observer.validateScientificResult(f.contract,f.sha,'scientific-auditor',f.payload,f.expected);
  assert.equal(result.scientific_predicates_passed,true);assert.equal(result.seed17_repaired,false);
});
