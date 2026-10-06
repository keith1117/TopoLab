# B4.20 bounded surrogate representation and correctness review

Frozen 2026-10-05 before any new train-label bytes or numerical observations.
This reviews B4.19's precision assumption and missing durable prefix. It does
not rerun B4.19, select a normalizer, measure local fidelity or a fitting cost,
fit a network, optimize, generate labels, open models or screen/final cases.
All historical failures, charges, unknown B4.19 counts/gap and P/17 stay intact.
Uniform remains default; the 48 unused B4.10 cases and B5 stay sealed.

Exactly the same eight canonical expanded train cases as B4.15 may be read,
through its exact-subset guard and B3 fitting guard before artifact lookup.
Bind B4.19's closed failed attempt, profiles, command/release/CI receipts,
metadata-only audit, resource proof and evidence publication. Verify recursive
B4.18 through B3 guards. No lost B4.19 value/counter is imputed from this review.
Default planning is static, performs no evidence read and creates no output.
Execution uses clean, CI-passed merged source, locked Python, one numerical
thread and fixed sibling external roots. Outputs and attempts are exclusive.

ONE new training-only version, `topolab.stored-normalizer-tangent.v2`, retains
the audited stored compliance C_s as a constant. With original stored float32
design x*, set rho_c=F(float64(x*)) and rho_s=float64(float32(rho_c)). These
are distinct analyzed states. Pay one fresh FEM solve for each state. Require
rho_s equal the serialized label physical density exactly and C(rho_s) agree
with C_s at the unchanged relative1e-9/absolute0. Do not require C(rho_c)=C_s.
The normalized continuous objective remains B4.15's C(F(P(z)))/C_s. Its tangent
is L(z)=C(rho_c)/C_s + [F.T(dC/drho at rho_c)/C_s].T(P(z)-x*).
Thus its intercept can differ from one. It differentiates continuous filtering,
not quantization. No tolerance, stored normalizer, label or v1 kernel changes.
Signed gradients and negative affine estimates remain un-clipped. The new
kernel receives the paid anchor analysis; construction and predictions do not
solve, and retain no mesh/displacement/numeric factorization.

For each case preserve both physical arrays, compliances, normalized difference,
signed gradient and whether the old equality would reject THIS NEW anchor.
This is new measured evidence, not identification of B4.19's unknown failed case.
Use exactly B4.15's two synthetic raw fixtures: interior v+.02*sin(.37*i)+
.01*cos(.13*i), and clipped repeated [.02,.5,.98], i=1..n. Preserve both
projected states and gradients; run one CPU-float64 Torch forward/backward
per state as correctness only, with no timing extrapolation. At each state,
check sine and cosine unit-max directions at both1e-4/2e-4 central steps:
64 directional rows and128 sides. No physics at prediction/side states.
Candidate:16 anchor solves. Independent auditor:16 anchor solves, uncached
Hex8 energy adjoint and separate Brent projection, no production tangent,
projection, pullback or Torch bridge. Total32 new FEM solves. Numerical rows
are never discarded to pass an acceptance condition.

Acceptance requires complete ordered eight anchors/sixteen fixtures/64 rows,
both anchor compliance reconstructions at rtol1e-9, signed gradient and
projected raw gradient rtol1e-9/atol1e-10, design/physical atol2e-11,
value rtol1e-9/atol1e-10, volume<=1e-12, shift derivative<=1e-10,
Torch value/gradient agreement and stable clipping sets on all sides.
Directional error abs(FD-adjoint)/max(abs(FD),abs(adjoint),1e-8)<=1e-4.
The production kink rejection1e-10 remains. No step/input/tolerance search.
At least one clipped and one free coordinate across the panel is required.
Synthetic nonuniform serialized-state regressions must exercise nonunit
intercepts before production. v1 must still reject a mismatched normalizer.

Before EACH label lookup, FEM invocation and case, append a fsync'ed event with
plan/source/sequence/case/operation, attempted and completed counters, physical
SHA, normalizer and context. Complete label metadata, anchor results and each
fixture/difference prefix are appended immediately after completion. On an
exception append its class/message/traceback and current counters before
rethrowing; even a hard kill retains the last before-call event and pending
operation. Attempts do not imply completed solves. No automatic retry/resume
or output overwrite. Independent audit has its own exclusive journal too.
Tests inject a FEM rejection and check that no later operation occurs.

All native startup/exit, evidence/label I/O, solves, correctness observations,
durable writing, failures and audits are paid. Probe/audit each cap300 charged
seconds (complete native wall+10, at least internal charge); whole cap660
seconds/1GiB, including a fully paid60-second plan/closure/verification reserve.
Use native wall/user/system/RSS with permissions from the first invocation.
Reserve use is sum complete native wall+10 (closure max with internal charge)
and must fit60; verify closure after its native profile exists. Failed attempts
retain complete profiles/exit codes and full charges; missing profiles cannot
certify caps. No free rerun. Original B4.19 charge73.93 is unchanged and carried
in later objective feasibility/amortization; this slice reports no fit proxy.

Ordered next: correctness pass => B4.21 bounded versioned local-surrogate
fidelity and cost probe; failure => B4.21 bounded surrogate correctness
failure review. Neither begins automatically. Full training memory, learned
repair and independent confirmation remain pending before a compatible final
contract or B5. Report the next slice and stop.
