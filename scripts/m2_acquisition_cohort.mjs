// Pure schedule used by two actual caller boundaries. Every IO/Native request is injected.
const ID='topolab.v2.p17-m2-registered-source-acquisition.20261104.v2';
const PUBLIC='/private/tmp/topolab-public-registered-source-acquisition-20261104-v3';
const PARENT='/Users/keith1117/Library/Application Support/TopoLab-custody/';
const FORMAL=[PARENT+'p17-m2-local-input-version-v8-strict-binding-20261103',PARENT+'p17-m2-local-input-version-v9-strict-binding-remedy-20261103'];
const ROLES=['independent-public-check','exporter-r0','independent-r0','exporter-r1','independent-r1','shared-closeout'];
const FULL=[300,300,300,1200,1200,300];
const require=(condition,reason)=>{if(!condition)throw Error('COHORT_STOP: '+reason);};
const integer=value=>Number.isSafeInteger(value)&&value>=0;
export function coordinateMilliseconds(proofs) {
 let total=0;
 for(let i=0;i<proofs.length;i++){
  const p=proofs[i];require(integer(p.T0_ms)&&integer(p.T1_ms)&&p.T0_ms<=p.T1_ms,'invalid actual endpoints');
  if(i){require(p.T0_ms>=proofs[i-1].T1_ms,'negative actual coordination');total+=p.T0_ms-proofs[i-1].T1_ms;}
 }
 return total;
}
export function launchGate(plan,role,proofs,now) {
 const formal=FORMAL.includes(plan.root);
 require(plan.root===PUBLIC||formal,'closed or unregistered root');
 require(plan.execution_identity===ID&&/^[a-f0-9]{64}$/.test(plan.plan_sha256),'execution identity/plan hash');
 require(plan.scope===(formal?'SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY':'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY')&&plan.formal_authority===formal,'scope');
 require(plan.actor_window_seconds===4500&&plan.coordination_limit_ms===240000&&JSON.stringify(plan.role_order)===JSON.stringify(ROLES),'frozen profile/order');
 require(integer(now)&&integer(plan.actor_start_ms)&&now>=plan.actor_start_ms,'actual clock');
 const index=ROLES.indexOf(role);require(index>=0&&proofs.length===index,'missing predecessor proof');
 proofs.forEach((p,i)=>require(p.role===ROLES[i]&&p.accepted===true&&p.complete===true&&JSON.stringify(p.actual_exit_codes)==='[0,0]','incomplete/unaccepted/wrong-order predecessor'));
 const consumed=coordinateMilliseconds(proofs);
 if(!index)require(now-plan.actor_start_ms<=30000,'late first SUP');
 else require(now>=proofs.at(-1).T1_ms&&consumed+now-proofs.at(-1).T1_ms<=240000,'actual coordination240 exceeded');
 const end=Math.min(plan.actor_start_ms+4500000,plan.applicable_deadline_ms??Infinity);
 require(end-now>=(FULL.slice(index).reduce((a,b)=>a+b,0)+600)*1000,'remaining full cohort/closeout suffix unavailable');
 return {coordination_ms:consumed,index};
}
export async function executeOwned(config,boundary,now=Date.now) {
 const observed=[];let plan;
 try {
  require(['producer','independent'].includes(config.author),'distinct registered author');
  plan=await (config.author==='independent'?boundary.prepare():boundary.plan());
  const schedule=config.author==='independent'?[
   ['independent-public-check',null],['independent-r0','exporter-r0'],['independent-r1','exporter-r1']
  ]:[['exporter-r0','independent-public-check'],['exporter-r1','independent-r0'],['shared-closeout','independent-r1']];
  for(const [role,predecessor] of schedule){
   const proofs=predecessor?await boundary.wait(predecessor):[];
   launchGate(plan,role,proofs,now());
   const result=await boundary.run(role,plan);observed.push(result);
   require(result.accepted===true,'actual role STOP; successor remains unopened');
  }
  if(config.author==='producer'){
   for(const role of ['final-filing','lease-release']){
    const result=await boundary.metadata(role,plan);observed.push(result);require(result.accepted===true,'metadata closeout STOP');
   }
   observed.push(await boundary.certificate(plan));
  }
  return {status:'OWNED_COHORT_COMPLETE_NEEDS_ACTUAL_RETURN',author:config.author,plan,observed};
 } catch(error){
  const failure={status:'STOP_RETAINED_NO_RETRY',author:config.author,plan,observed,reason:String(error)};
  try{await boundary.freeze(failure);}catch(secondary){failure.filing_failure=String(secondary);}
  return failure;
 }
}
