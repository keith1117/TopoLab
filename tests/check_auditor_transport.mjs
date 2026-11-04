// Pure metadata validation against the frozen observer; no scientific input IO.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {constants} from 'node:fs';
import {pathToFileURL} from 'node:url';
const [repo, metadata] = process.argv.slice(2);
const observer = await import(pathToFileURL(repo + '/scripts/p17_m2_scientific_metadata.mjs'));
observer.configure(crypto);
const {contract, original, projected} = JSON.parse(await fs.readFile(metadata, 'utf8'));
const sha = original.result.scientific_contract_sha256;
const expected = contract.roles['scientific-auditor'].inner_starts[0];
if(process.env.TOPO_EXPECT_ORIGINAL_LIST_RED === '1') {
  // Intentional regression run: exercise the unadapted real legacy summary.
  observer.validateScientificResult(contract, sha, 'scientific-auditor', original, expected);
  throw Error('legacy descriptor-list incompatibility unexpectedly disappeared');
}
assert.throws(() => observer.validateScientificResult(contract, sha, 'scientific-auditor',
  original, expected), /pending own native return/);
const result = observer.validateScientificResult(contract, sha, 'scientific-auditor', projected,
  expected);
assert.equal(result.status, 'FAIL_SCIENCE_GATE');
assert.equal(result.seed17_repaired, false);
assert.deepEqual(result.failed_predicates, original.result.decision.failed_predicates);
assert.deepEqual(projected.result.summary_packet, original.result.summary_packet);
assert.deepEqual(projected.result.completed_row_descriptors, original.result.completed_rows);
console.log('original-list rejected; projected FAIL preserved; no Native/FEM/input calls');

// Exercise both real policy/namespace constructors with RAM metadata. The
// expected missing-evidence rejection occurs before any native return verifier.
const canonical = value => value === null ? 'null' : Array.isArray(value)
  ? '[' + value.map(canonical).join(',') + ']' : typeof value === 'object'
  ? '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k]))
    .join(',') + '}' : JSON.stringify(value);
const bytes = value => Buffer.from(canonical(value) + '\n', 'ascii');
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
for (const scope of ['B', 'FINAL']) {
  const contractPath = '/PUBLIC-METADATA-ONLY-NOT-ON-DISK/contract.json';
  const manifestPath = contract.api_metadata.manifests[scope];
  const contractRaw = bytes(contract), contractSHA256 = hash(contractRaw);
  const manifestRaw = bytes({schema:'topolab.v2.m2-api-metadata-manifest.v1', scope,
    contract_sha256:contractSHA256, files:{}});
  const files = new Map([[contractPath, contractRaw], [manifestPath, manifestRaw]]);
  const info = (size, directory=false) => ({dev:1n,ino:2n,size:BigInt(size),mtimeNs:1n,
    mode:directory?16832n:33152n,nlink:1n,isFile:()=>!directory,isDirectory:()=>directory,
    isSymbolicLink:()=>false});
  const memory = {
    async lstat(path) {
      if(files.has(path))return info(files.get(path).length);
      assert.ok([...files.keys()].some(name=>name.startsWith(path+'/')),
        'unexpected metadata namespace probe: '+path);
      return info(0,true);
    },
    async open(path) {
      assert.ok(files.has(path), 'unexpected metadata read: '+path);
      const raw=files.get(path);
      return {async stat(){return info(raw.length);},async close(){},
        async read(buffer,offset,length,position){
          const piece=raw.subarray(position,position+length);piece.copy(buffer,offset);
          return {bytesRead:piece.length};
        }};
    }
  };
  await assert.rejects(observer.observeMetadata({fs:memory,constants,crypto,scope,contractPath,
    contractSHA256,manifestPath,manifestSHA256:hash(manifestRaw)}), error => {
    assert.match(error.message,/missing registered metadata member/);
    assert.equal(error.metadata_operation.metadata_files_read,2);
    return true;
  });
}
console.log('real B and FINAL metadata policy/namespace accepted; absent evidence STOP retained');
