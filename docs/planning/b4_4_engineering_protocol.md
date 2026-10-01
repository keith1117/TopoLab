# B4.4 finite timing and checkpoint repair protocol

Version: `topolab.b4_4.engineering.v1`. Frozen before any sentinel model read or
numerical query. This is a new engineering experiment, with new source and output
identity. It does not retime B4.2, change its failed Gate, train or select a model,
or access labels, nearest-neighbor populations or sealed B5 cases. Uniform remains
the operational default. This protocol establishes no learned acceleration claim.

## Fixed population and order

`scripts/b4_4_engineering_sentinel.py --plan` (the default without `--execute`)
prints the canonical metadata-only plan and SHA-256. The exact six exposed case
IDs, their designated seeds and the complete 76-query schedule are frozen in
`CASES` and `schedule()`. The first five cover a small-y timing outlier, a small-z
timing outlier, both P/29 failures and the P/43 failure. The sixth is the first
canonical high-volume large-y specialist case. The first five compare uniform,
P and the numerically identical P-without-S; the sixth compares uniform and the
three identical S/17 routes C/P/A. Only P/17, P/29, P/43 and S/17 selected artifacts
may be opened through the existing provenance-checked model reader.

Two arms use unchanged `evaluate_query`, projection, optimizer, 360-update cap,
physical-plateau policy, 1.001 compliance bound and 0.005 volume bound. Each arm
executes nineteen queries in each of two rounds. Round zero is legacy then
compact; round one is compact then legacy, with reversed learned alias order.
Uniform is first in every case block. Every attempt, failure, fresh uniform
fallback and repetition is retained. No faster-repeat selection is allowed.

Both arms force a durable flush on checkpoint call two (the first solver update),
then use a five-second cadence at safe callbacks. This is a checkpoint-stress
sentinel, not a production benchmark. The legacy arm additionally invokes the
unchanged full-index writer on a shadow fixture containing the exact complete
48-case B4.2 execution index. Its prefix never grows or changes. It is an
engineering write-cost fixture, not an authoritative B3 ledger or freeze. It
reads/writes no original file. Its cadence starts after each write, so this test
isolates bounded persistence without reproducing the old pre-write cadence bug.

## Timing and charging

The new outer wall/CPU envelope encloses the entire query including initial/final
callbacks, witness packaging, validation and full fallback. Legacy phase sums
are separately retained. Inclusive callback wall/CPU, flush wall, flush count
and written bytes are measured without subtracting any channel from query time.
Flush wall is the whole callback duration on callbacks that wrote; it includes
resource bookkeeping as well as the durable write. CPU is process CPU, not a
machine utilization or suspension attribution claim.

The stage charge also includes input checks, runtime capture, model loads,
independent terminal FEM audits, canonical result serialization, immutable result
publication and boundary progress writes. These stage costs are not hidden inside
a query or reported as free. The final report gives total stage charge and the
residual above all query envelopes. A fixed ten-second close allowance covers
last progress/summary publication and command startup. Whole-command profiles and
a separately charged independent audit reconcile this accounting; no guessed
correction is applied to historical timing. Recovery additionally charges the
complete unclosed UTC interval, including downtime and failed work.

## Persistence and ownership

`topolab.b4.progress.v1` is at most 4,096 bytes, independent of completed outcome
count. Iteration callbacks never parse or serialize an outcome ledger. An OS
nonblocking exclusive lock owns the external output root. Each unit has a frozen
ordinal/identity, context hash and prior-record hash. Units are canonical,
immutable and directory-fsynced. A pending attempt and monotonically increasing
attempt count are durable before any query. Publication precedes acknowledgement
in progress. On recovery an unchanged pending unit may rerun and all prior cost
is retained; a fully published pending unit is reconciled without rerunning it.
Completed prefix, hash, context, permanent failure flags, charges and RSS cannot
be reset by a new run. Recovery validates the whole retained prefix before
execution; only constant-size progress is touched inside callbacks. Temporary
files are never inputs. Progress stores start-of-write UTC conservatively and
cadence uses end-of-write monotonic time. Five seconds is a scheduling threshold
at safe callbacks, not an absolute bound on the duration of a solver update.

Synthetic tests must cover lock exclusion, prefix/hash/context corruption,
interrupted pending work, publication before acknowledgement, charged downtime,
permanent resource/integrity stops, callback byte bounds, post-write cadence and
inclusive query timing. Filesystem process-crash recovery is tested; no claim is
made about storage hardware surviving power loss.

## Frozen acceptance and limits

Execution uses a clean merged revision and unchanged frozen numerical anchor,
lock, runtime and B4.1 selections. Hash-bind both stopped B4.2 index and original
complete execution snapshot. All 76 numerical outcomes, including full terminal
witnesses, metrics, routes and failure types, must be bit-identical to the
corresponding retained B4.2 outcome after removing only timing fields. Independently
re-solve every candidate/fallback terminal witness and check its metric. The
three known failed P attempts and their duplicate controls must remain failures.

Engineering acceptance requires completeness, exact numerical/status identity,
independent terminal audits, persistence tests and honest cost closure; aggregate
compact callback wall must be at most 0.25 of legacy, and aggregate complete query
wall at most 1.05 of legacy, using all counterbalanced repetitions. No same-quality
or speed threshold is loosened. The finite stage cap, including recovery and all
supplemental audits, is 7,200 seconds and peak self-RSS is 2 GiB. Stop permanently
on cap or integrity failure. No discretionary rerun or additional case is permitted.

After an engineering pass, B4.5 separately freezes one sensitivity-weighted
terminal-design generalist hypothesis using already audited labels, unchanged
inputs/architecture/seeds and fixed specialist, with fresh disjoint development
validation. An engineering failure is reported and resolved under a new explicit
contract before any learning-side execution. The complete new B4 Gate and
independent confirmation are mandatory before B5.
