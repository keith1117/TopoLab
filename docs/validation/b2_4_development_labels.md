# B2.4 complete development-label materialization and data Gate

Date: 2026-09-25

Status: **B2.4 complete data Gate passed.** All **522/522** versioned
development labels were generated and audited under the fixed 240-update
physical-plateau policy. This permits the separate B2.5 prototype-fitting
slice. It does not establish learned acceleration, reopen historical M1/M2
results, or satisfy the v2 ML delivery Gate.

## Frozen plan and source boundary

The [pre-execution protocol](../planning/b2_4_development_labels_protocol.md)
fixes the full B2.2 development population and the B2.3 budget repair.
Read-only plan version `topolab.b2_4.dataset.v1` has canonical SHA-256
`015ab799be88a5fef763720b2e1c58281dc17aea67c61435bcb87d254f64169c`.
The external plan JSON at `/tmp/topolab-b24-plan.json` has file SHA-256
`36f9875103d0cda8ac23845a42b7b50556e4b2300bf67ef8c614afd24e3a0530`.
Each row binds its B2.2 source case, new 240-update physical case, B2.3
`tlcase-b23-v1-*` result identity, split, scale, direction, and volume.
All 522 physical case IDs and result IDs are unique; the 61 B2.3 sentinel
identities are a subset with identical result IDs. No test/OOD case or label
entered the plan.

The production run used clean tracked revision
`7f4d0f6a1512b5be8f6ea192430608108bafe2cc` on Apple arm64, macOS 26.5,
Python 3.12.10, NumPy 2.5.3, and SciPy 1.18.1. The locked `uv.lock` SHA-256
was `9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
OpenMP, BLAS, VECLIB, MKL, and BLIS threads were set to one. Only the
committed M2 case/split metadata was read. Generated labels, the checkpoint,
and run summaries stayed in `/tmp/topolab-b24-labels` and `/tmp`, outside Git.

## Complete outcome and resource audit

| Development partition | Required | Generated and audited |
|---|---:|---:|
| Small train | 432 | 432 |
| Small validation | 36 | 36 |
| Large train | 36 | 36 |
| Large validation | 18 | 18 |
| **Total** | **522** | **522** |

Small cases used 240.58 s and large cases used 878.90 s of per-case time;
checkpoint overhead is included in the 1,120.49 s generation wall time.
All 18 `(direction, volume)` strata have exactly 29 cases, 261 per direction.
No case failed or was dropped. All 522 stored artifacts have distinct
checksum-addressed references and total **10,934,319 bytes** of label JSON.
The external index has SHA-256
`dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244`.
The external summary JSON has SHA-256
`8c079559848b63431ff720b0327e884ea10184f32483186f6bfde25a375c8ea2`.

The executor independently re-solved every full-precision terminal state
before serialization and each persisted float32 physical state during the
final audit. It recomputed the stored sensitivity weights through the filter
transpose, verified 522 artifact checksums and identities, and checked all
split/stratum/mesh counts. All 522 converged within 240 updates; the largest
iteration count was **170**. There were 444 design-maximum and 78 physical-
plateau stops. Largest filtered physical-volume error was
`1.0413e-8`, below `0.005`; the independent compliance tolerance was relative
`1e-9`. The frozen 61 B2.3 sentinels retained **61/61 identical stop
iterations and result IDs**. The largest relative compliance difference to
their earlier full-precision metadata was `1.70e-8`, consistent with the
explicit float32 persisted-state re-solve; the stop iterations did not change.

Total generation plus final audit took **1,149.58 s (19.16 min)**, including
29.09 s for the audit, versus the frozen 7,200 s limit. Peak process RSS was
**422,051,840 bytes (402.5 MiB)** versus the 1 GiB limit. These are one
single-thread local-machine measurements, not cross-platform performance
claims. The immutable external index retains every case-level cost, result,
stop reason, and checksum for later B2.5 fitting; its 522 label artifacts
are required inputs, not repository contents.

## Gate, validation, and next slice

**B2.4 passes the complete development-data Gate.** This resolves the
missing-label blocker that followed B2.2's 53/61 failure and B2.3's bounded
repair. It does not establish that the learned candidate will be faster or
even quality-feasible. Historical M1/M2 negative evidence remains unchanged.
The next independent slice is **B2.5**: use only these verified train and
validation labels to fit the predeclared same-architecture unweighted control
and sensitivity-weighted candidate at seeds `17, 29, 43`, with deterministic
shape-bucketed batches and equal exposure. Then screen all 54 exposed
validation cases at both scales under matched 240-update uniform references,
counting inference, projection, rejection, refinement, and fallback. B3 final
cohort registration remains conditional on that prototype screen.

Before the source commit, locked offline `uv sync --dev --locked`, Ruff,
`mypy src`, full `pytest` (**287 passed**), and Git diff checks passed.
Additional focused tests cover plan/sentinel identities, float32 round-trip,
independent sensitivity audit, corrupted artifacts, and changed case IDs.
No fitting, model weights, test/OOD label read, or final evidence occurred.
