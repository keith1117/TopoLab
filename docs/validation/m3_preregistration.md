# M3.0 exposed-failure diagnosis and pre-registration validation

Date: 2026-09-25

Status: **Gate M3.0 passes for a bounded, falsifiable follow-up. No new label,
checkpoint, model fit, or final evaluation was produced.** The binding plan is
`docs/m3_preregistration.md`. M1 and M2 retain their failed gates; uniform remains
the operational default.

## Evidence and method

The read-only diagnosis inspected the already exposed M1 evaluation index and the
M0 v1/v2 and M2 materialization indexes. It verified the following SHA-256 values
before analysis; generated artifacts stay outside Git:

| Index | SHA-256 |
|---|---|
| M0 v1 materialization | `9f517be3816e4fb978b5034cd677393de93246cd0cd9cb8e1ab4efe902b73ef0` |
| M0 v2 materialization | `4a02c67265241af7852d9f2da9caa475d2f018e2ac5882834175d60c8bcae458` |
| M1 held-out evaluation | `2d15a9303fb4dd6b07ff224a027b2650a0eabcaf0391d5db642f40777fed1f73` |
| M2 materialization | `c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f` |

M1 rows were joined to the M0 v2 manifest by verified case ID. Every learned
end-to-end time was divided by the same case's uniform end-to-end time. Counts below
retain all five seeds, failed attempts, and charged fallbacks. `Success-only` ratios
are diagnostic and never substitute for the claim metric. Load position is the
M0 x-fast node index decoded as `y = (node // 13) % 7`, `z = node // 91`; an edge
touches `y=0/6` or `z=0/3`. M2 statistics used the index's frozen split and outcome
fields only; no successful M2 label file was opened for this diagnosis.

## Observations

| M1 split/volume | Cases | Seed attempts | Quality failures | Mean charged ratio | Successful-attempt mean ratio |
|---|---:|---:|---:|---:|---:|
| ID, all | 6 | 30 | 7 | 1.193 | 0.905 |
| OOD, all | 80 | 400 | 100 | 1.550 | 1.197 |
| OOD, 0.20 | 16 | 80 | 11 | 0.571 | 0.445 |
| OOD, 0.30 | 16 | 80 | 8 | 0.827 | 0.733 |
| OOD, 0.40 | 16 | 80 | 0 | 1.256 | 1.256 |
| OOD, 0.50 | 16 | 80 | 40 | 2.632 | 2.195 |
| OOD, 0.60 | 16 | 80 | 41 | 2.463 | 2.240 |

All 107 learned failures were `quality_error`; each failed candidate exceeded the
`1.001 * uniform final compliance` limit. Eighteen also exhausted 120 iterations.
The largest candidate physical-volume error across M1 was below `1e-8`, so there
is no evidence of a volume projection defect. M1 records final, not initial,
compliance and does not retain raw/projected predicted fields; this index cannot
attribute the failure to projection distortion or quantify initial compliance.
Those mechanisms remain hypotheses, not observed causes.

The M1 OOD edge/interior split was 52 failures in 300 edge attempts versus 48 in
100 interior attempts; this association does not isolate receptive field from
training-direction coverage or target volume. With the exact observed model seeds,
an impossible post-hoc selector that chooses the fastest successful seed for each
case and otherwise runs uniform has a mean ratio of 0.733 on six ID cases and
1.054 on 80 OOD cases, before charging selection. One ID case and 16 OOD cases
had no successful seed. This is an observed-candidate oracle, **not** an attainable
policy or proof of an ideal density warm-start ceiling.

For a separate optimistic cost scale, charge each case's mean learned
setup-plus-projection time and only `uniform refinement time / uniform iterations`
for a hypothetical one-iteration refinement. Its mean ratio is 0.031 on ID and
0.033 on OOD. This is an idealized timing floor, not a measured solver result or
a quality-feasible warm start: solver iterations need not have identical cost, and
an actual candidate may require many iterations. The gap between that floor and
observed outcomes leaves room for an intervention, but does not predict its gain.

The M2 index contains 756 complete outcomes: 746 successful labels and ten
retained terminal failures. All ten are at volume 0.45: seven `y` training cases,
one `y` ID-test case, and two `x` OOD cases. The previous read-only re-solves
reported terminal density changes above `0.01` at iteration 120 while physical
volumes stayed within about `9e-9` of target. No failure is a usable successful
label. The M2 train/validation partitions contain 425/432 and 36/36 successful
labels respectively; the only deficient training stratum is `y,0.45` at 17/24.
M2's complete-label gate therefore remains failed.

Removing only `optimization.max_iterations` from canonical physical problem JSON
shows all 160 M0 v1 cases coincide physically with M0 v2, and all 160 M0 v2
cases occur in M2. The exposed physical-case union is 756, despite distinct M0 v1
and v2 case IDs. M3's final volumes lie outside that union. M3.1 must implement
and independently verify this exposure ledger before any fitting.

## Interpretation and Gate M3.0 decision

The evidence supports two limited observations: low-volume warm starts sometimes
save substantial refinement time, and quality failures plus full fallback erase
that gain; at higher volume, observed learned refinement is often slower even
when the candidate meets quality. The M2 0.45 failures expose a separate
uniform-label availability issue. The data do not establish whether the learned
quality problem is caused by training direction, local receptive field, the MSE
objective, or optimizer basin behavior.

Gate M3.0 passes only for the specific test in `docs/m3_preregistration.md`:
reuse auditable M2 train/validation successes under an explicit availability gate;
compare the M1 control to one dilated-convolution candidate; calibrate a finite
volume/uncertainty rejection policy on validation; and open a physically disjoint
final catalog once after freeze. The fixed M3.2 validation screen can stop this
path before final evaluation. This decision claims plausibility, not learned
acceleration or OOD safety.

## Validation of this slice

The catalog construction, based only on M2 case metadata, produced 432 train,
36 validation, 64 new ID-test, and 32 new OOD cases, all 564 case IDs unique.
The canonical catalog SHA-256 is
`ddb0a0b4c6b3e5790187acad70459e6128b1f94d8a8b3be7ea8339395a16cbe3`.
No generated catalog file was written. The final cases use eight volume fractions
absent from M0/M1/M2; none can overlap those physical-case definitions.

Repository validation before commit: `uv sync --dev --locked`,
`uv run ruff check .`, `uv run mypy src`, `uv run pytest` (265 passed),
`git diff --check`, and `git diff --cached --check` all passed. No numerical
tolerance or source behavior changed in this document-only slice.

The next independent slice in the recommended v1.x sequence is **A2.1 worker
protocol**. A2.2 durability follows it; M3.1 returns to the frozen data gate
after those platform slices. Start each only on a new user instruction.
