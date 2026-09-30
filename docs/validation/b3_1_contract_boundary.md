# B3.1 contract and final exposure planning audit

Date: 2026-09-30 (America/New_York)

Status: **B3.1 planning Gate passed.** The new
[B3 contract](../b3_experiment_contract.md) freezes a finite formal
experiment after B2.28 feasibility and B2.29 independent confirmation.
The metadata-only acceptance audit passed without a solver call, label
or checkpoint access, fitting, or final outcome. This completes the
planning slice; **Gate B3 data audit remains pending**. Uniform remains
the operational default and no final acceleration claim follows.

## Frozen experiment and decisions

`topolab.b3.experiment.v1` retains the existing thirteen-channel context
CNN, weighted terminal-design generalist, and large-y specialist route.
It freezes 528 train definitions, 32 fit-validation cases, 48 independent
screen-validation cases, 96 final ID cases across both mesh scales,
and 48 matched x-direction OOD cases. All labels and queries use the
same 360-update physical-plateau policy and unchanged quality tolerances.
Training labels will be regenerated under new B3 identities.

There are twelve fixed fits: three seeds for weighted base control,
weighted expanded candidate, unweighted expanded ablation, and shared
specialist. The generalist-only route ablation requires no extra fit.
All seeds, failed candidates, and fallback costs remain in the records.
Prospective B4 selection requires a zero-failure candidate on the new
screen, with fixed quality/speed/control criteria and deterministic
ties. B2 confirmation outcomes cannot select the deployment seed.

Final evaluation freezes that primary pair before opening ID, OOD,
or replication results. It requires two-scale point savings of at least
10%, upper 95% paired-ratio limits below one, complete-scan time savings,
non-ML comparisons, zero selected-primary ID failures/fallbacks, OOD
safety, and independently installed Linux execution of the same artifacts.
Every stage has a cumulative compute cap; the entire program is bounded
by 100,800 seconds (28 hours). Failure stops the relevant advance and
does not authorize another configuration or tuning on final outcomes.

## Independent metadata acceptance audit

An external audit used source anchor
`5b34ff9edb8772a4b0f456a7b94c454e16579aa6` and original independent
problem construction to enumerate every new non-train case. It compared
all y/z cases against the existing public problem, scaling, and budget
helpers. Historical sources were rebuilt from their catalog/cohort
definitions without opening generated labels or learned artifacts.
The superseded M3 catalog reproduced its published SHA-256 exactly.

| Check | Complete result |
|---|---:|
| Catalog definitions and unique IDs | 752/752 |
| Train / fit-validation / screen-validation / final-ID / final-OOD | 528 / 32 / 48 / 96 / 48 |
| Base / expanded / specialist training memberships | 468 / 508 / 488 |
| Historical unique case IDs | 1,982 |
| Historical unique budget-insensitive fingerprints | 1,376 |
| Cross-role fingerprint intersections | 0 |
| New non-train / historical intersections | 0 |
| Matched OOD y-direction counterparts | 48/48 |
| New-role volumes shared with historical sources | 0 |
| Budget-variant negative acceptance cases | 2/2 correctly remain exposed |
| Solver calls / label artifacts opened | 0 / 0 |

The historical source union comprises 160 M0 v1 definitions, 160 M0
v2/M1 definitions, all 756 M2 definitions, all 96 M3 final designs,
and 970 B2 exposed/reserved definitions. Overlapping source memberships
are retained in the deduplicated ledger. All inherited training
fingerprints are explicitly historical; every new non-train role is
physically disjoint even when the iteration cap is ignored. Independent
checks verified each stratum, every source-case link/membership, final
pairing, all 360-update budgets, and null case initialization.
Two negative metadata cases changed the cap of a historical case and
a fit-validation case: both acquired different case IDs but retained
their original fingerprints and exposure membership.

Canonical metadata SHA-256 values were computed and rechecked against
the contract's exact byte and ordering rules:

```text
catalog  441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c
exposure 5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7
contract 452a6c1b3664e007a258a914877c935f333c1823f3ec3d977ee0d09583129af8
```

Generated catalog/ledger JSON and audit code/output remain outside Git.
The audit establishes metadata consistency and preregistration, not
uniform convergence, train-label availability, a working access adapter,
model feasibility, or final performance. Those require later slices.

## Validation and next slice

Required repository validation passed locked dependency sync, Ruff,
mypy (39 source files), all **374 Python tests** in `245.35 s`, and
diff checks before commit. The PR must pass all CI before merge.
No numerical tolerance changed and no
new external source or implementation was introduced.

The next independent slice is **B3.2: implement the frozen catalog,
training memberships, exposure fingerprints, and access boundary**.
Verify the exact hashes and role counts, reject budget variants crossing
roles, and test forbidden-role rejection before artifact access, without
solver execution. B3.3 then implements the guarded data path; B3.4
materializes/audits 560 labels and 48 screen references before Gate B3
can pass. Final evidence remains sealed through the B4 freeze.
