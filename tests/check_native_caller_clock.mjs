// Replay the same public, invented caller events as the Python boundary checks.
import * as crypto from 'node:crypto';
import * as observer from '../scripts/p17_m2_scientific_metadata.mjs';
let raw='';
for await(const chunk of process.stdin)raw+=chunk;
const options=JSON.parse(raw);
for(const name of ['startRaw','returnRaw','jsPrefixRaw','verifyProfileRaw','verifyResourceRaw'])options[name]=Buffer.from(options[name]);
observer.configure(crypto);
const check=options.role==='b'?observer.validateBCallerClock:observer.validateCCallerClock;
try { console.log(JSON.stringify(check(options))); }
catch(error) { console.error(error.message);process.exitCode=1; }
