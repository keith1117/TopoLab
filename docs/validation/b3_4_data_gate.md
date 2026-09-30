# B3.4 complete production data audit

Date: 2026-09-30 (America/New_York)

Status: **Gate B3 passed.** All 560 production labels and 48 screening
uniform references passed complete numerical, provenance, availability and
resource audits. No model was fitted and no final artifact was generated or
opened. This data Gate permits later fitting; it does not establish acceleration.

## Frozen identity and execution

The [B3.1 experiment contract](../b3_experiment_contract.md) is unchanged.
The data program contains exactly 528 training labels, 32 fit-validation
labels and 48 screening uniform references. All 608 tasks start from uniform
initialization and retain the 360-update cap, projected float32 initialization,
physical-plateau stopping policy, physical-volume tolerance `0.005` and
independent compliance tolerance `rtol=1e-9, atol=0`. No case is replaced,
imputed or given a changed termination budget.

| Identity | SHA-256 / revision |
|---|---|
| Clean merged label source | `cc151b014f9034ccc7093ef592021003d7dec252` |
| Numerical anchor | `5b34ff9edb8772a4b0f456a7b94c454e16579aa6` |
| Frozen experiment contract | `452a6c1b3664e007a258a914877c935f333c1823f3ec3d977ee0d09583129af8` |
| Exact 752-case catalog | `441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c` |
| Historical exposure ledger | `5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7` |
| Locked environment | `9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292` |
| Actual data manifest | `9c4018d730d39beef548ffd6477458ca785ae440cbf37d6ed7c1de65a8102ac9` |

The source was checked out separately at the merged revision with no tracked
or untracked source changes. A metadata-only plan confirmed the manifest
before execution and did not create the output root. The subsequent single
execution used a previously nonexistent external root:
`/Users/keith1117/Documents/TopoLab-data/b3-v1-data`.
All labels were regenerated from uniform, including historically exposed
training definitions; no historical label artifact was reused.

Runtime: Apple M2 CPU, arm64, Darwin 25.5.0, 8 GiB host RAM, Python 3.12.10,
NumPy 2.5.3, SciPy 1.18.1, Torch 2.14.0, Pydantic 2.13.5 and Safetensors 0.8.0.
All four BLAS/OpenMP thread variables were 1, Torch intra-op threads were 1,
and inter-op threads were 8. Runtime and source identity are embedded in every
artifact and the materialization manifest. Generated artifacts remain outside
Git, including receipts, audit code, full traces and stored float32 vectors.

The production command, run from the clean source checkout, was:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src \
UV_PROJECT_ENVIRONMENT=/Users/keith1117/Documents/TopoLab/.venv \
UV_CACHE_DIR=/tmp/topolab-uv-cache \
/usr/bin/time -l /Users/keith1117/.local/bin/uv run --no-sync python \
-m topolab.b3_dataset_cli \
--output-root /Users/keith1117/Documents/TopoLab-data/b3-v1-data --execute
```

The locked environment was synchronized before this command. `--no-sync`
reuses that environment while `PYTHONPATH=src` loads numerical implementation
from the recorded clean checkout. The output root uses the single-writer
lock and immutable canonical outcome prefix implemented in B3.3.

## Independent acceptance method

The production CLI independently audits every retained terminal outcome.
A separate streamed audit then checks the complete population against the
metadata-only B3.1 catalog and exposure receipts, using independent case-ID
and physical-fingerprint calculations. It verifies all 752 definitions,
the 1,376 historical fingerprints, training memberships, unchanged budgets,
role disjointness and zero historical intersections for new roles.

The supplemental audit reads each artifact through the authorization guard,
checks byte count, content hash, canonical schema, source/manifest bindings,
and exact case-to-outcome pairing. The physical artifact path population must
equal the 608 successful references exactly. Final-ID and final-OOD remain
definitions only, with no generated or opened final artifact.

Numerical acceptance is recomputed from the published SIMP and elasticity
equations using TopoLab's independently implemented FEM primitives, without
calling the production label or compliance audit functions. The supplemental
audit reassembles stiffness and solves full-precision and serialized float32
physical states separately. It checks terminal and history consistency,
finite values, density bounds, filtered physical vectors, physical volume,
state ordering and the eleven-state witness for a physical plateau.

Sensitivity weights are independently reconstructed from the element strain
energy, SIMP derivative and transposed density filter, with the frozen
absolute-gradient normalization, `[0.25,4]` clipping, second normalization
and float32 conversion. Stored design, physical and sensitivity vectors must
match exactly and have `(1,nz,ny,nx)` shape. Full-precision reference compliance
and float32-state compliance remain distinct measurements.

## Complete outcomes and resources

| Role | Small mesh | Large mesh | Complete audit |
|---|---:|---:|---:|
| Train labels | 432 | 96 | 528/528 |
| Fit-validation labels | 16 | 16 | 32/32 |
| Screening uniform references | 24 | 24 | 48/48 |
| Total | 472 | 136 | **608/608** |

All frozen mesh/direction/volume strata match their required counts.
Training memberships contain exactly 468 base, 508 expanded and 488
specialist labels within the 528-label union; these overlapping memberships
are not additional data tasks. Small training has 24 cases per direction
and each of nine volumes. Large training has two base cases per direction
and volume, plus ten y cases at each specialist volume and ten cases per
direction at each of the two generalist expansion volumes. Fit-validation
has two and screening has three cases per mesh/direction/volume cell.

There are **zero failed, missing, replaced or unaudited tasks** and zero
final artifacts. The exact 608-file artifact population totals **772,490,763
bytes**. The canonical outcome prefix, all byte hashes and immutable
case/provenance pairings passed both audits.

| Numerical check | Complete-population result |
|---|---:|
| Design-change terminal rule | 448 cases |
| Physical-plateau terminal rule | 160 cases |
| Maximum updates | 280, below the frozen 360 cap |
| Maximum full-precision physical-volume error | `9.973395387330442e-9` |
| Maximum stored float32 physical-volume error | `1.0914065762257508e-8` |
| Maximum independently re-solved full-state compliance relative error | `0.0` |
| Maximum independently re-solved stored-state compliance relative error | `0.0` |
| Float32 design/filter/sensitivity equality | 560/560 labels, exact |

The largest full-state versus float32-state compliance difference was
`2.6949885423954902e-8` relative. Each state passed its own independent
compliance check at `rtol=1e-9`; the two precisions are not compared as if
they were the same state. No tolerance or numerical policy changed.

| Resource component | Seconds |
|---|---:|
| Production execution and CLI audit, internal charge | 4,502.418036 |
| Measured whole-command overhead added to the index | 3.331964 |
| Independent two-grid numerical precheck | 4.43 |
| Supplemental audit, charged elapsed time | 805.173116 |
| Conservative launch/final-flush/metadata allowance | 10.0 |
| **Final cumulative charge** | **5,325.353116 / 14,400** |

The whole production command measured `4,505.75 s`, and the supplemental
audit's whole command measured `806.78 s`. All three whole-command profiles
sum to `5,316.96 s`, below the final cumulative
charge by `8.393116 s`. Peak RSS is **500,154,368 bytes (476.984 MiB)**,
including the independently checked profile maxima, below the frozen
**2,147,483,648-byte** cap. No restart, integrity failure or resource failure
occurred. All extra audit costs accumulate in the same append-only index;
the generation-only receipt and final index intentionally have different
hashes while their original outcomes remain unchanged.

All receipts and the supplemental audit source are preserved externally in
`/Users/keith1117/Documents/TopoLab-data/b3-v1-data/audit_receipts`.
`resource_floor_and_receipts.json` binds the profile comparison and receipt
hashes. The complete audit JSON retains all 608 compact case measurements
and every frozen stratum count.

| Evidence | SHA-256 |
|---|---|
| Metadata-only plan | `31e49681dd1acca118949a115bd105bc55cd0c901c4be4621064ca3aabab3644` |
| Generation/CLI-audit index | `b16384dc18503880cbf66476357492fa10f505a14a88bf91e67e49efc0998ee4` |
| Generation summary | `e3d1b5b85701058bf0322d3d9bff6c321573644615dda5f3d1b97fb615db31a0` |
| Supplemental audit source | `1b2501112c0655952730dae7aa5aa80533d46f27c776975b88f6b5d427485d13` |
| Complete independent audit receipt | `c21212fdf900167ddec87c91e971e519d3d8c58ffa1187494ba18e8624fd3173` |
| Final charged materialization index | `b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26` |

## Verification and next slice

Required locked sync, Ruff, mypy (45 source files), all **561 Python tests**
in **268.29 seconds**, and diff checks passed before commit. This slice
changes only the validation report, provenance and project-status documents;
the frozen experiment contract, numerical implementation and tolerances are
unchanged. The PR must pass all CI before merge.

The next independent slice follows roadmap step 37: **A2.1 worker protocol**,
a minimal serialized manager/worker boundary using a separate local process.
A2.2 durable ownership and recovery follows it. B4 fitting and screening may
begin after Gate B3 passes; B5 final evaluation also requires A2.1 and A2.2.
This slice generates data and audits quality; later Gates must establish
same-quality end-to-end acceleration. Uniform remains the operational default.
