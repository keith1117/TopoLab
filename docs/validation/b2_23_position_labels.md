# B2.23 large-y position coverage and label feasibility

Date: 2026-09-29 (America/New_York)

Status: **the frozen B2.23 development-label Gate passed.** All 30/30 new
large-mesh y-direction uniform labels converged and passed independent
quality and artifact audits: 20 train and 10 validation. This slice did not
fit a model or measure learned acceleration. Uniform initialization remains
the operational default; B3 and final evidence remain closed.

## Frozen scope and exposure

The [B2.23 protocol](../planning/b2_23_position_labels_protocol.md) fixed
plan SHA-256
`d7ca55687e1f92fdd113991228f95e589242df8ba2ab112fe0c2153b36595a72`
and bound B2.22 screen-index SHA-256
`62ffe463c863f5ff57b88687a5cc9aeb0abf5261087335f4e790e5f3b3f58632`.
The read-only plan, label run, and audit used clean merged source revision
`63b879f9097cf80fd4d797acbf0ec9deb38d3f2b`, one CPU/BLAS thread,
and an external artifact root. The exposure ledger blocked 760 previously
exposed or reserved physical case identities. No M2 held-out/OOD or new
final case was opened.

The existing large-mesh y training subset at volume `>=0.55` held only
four cases at four load positions: `(0,0)`, `(8,0)`, `(2,4)`, `(12,6)` in
large-mesh node coordinates. The B2.22 screen position `(8,2)` failed for
all three specialists and was absent from those training positions;
`(2,4)` passed for all three and was present. This is a coverage
association, not a demonstrated cause of the quality gap.

The new labels use the `(24,12,6)` mesh, negative y load, and ten fixed
interior positions at each of three unused volumes: `0.5585` and
`0.5985` for train (20 cases), `0.5785` for validation (10 cases).
The combined high-volume large-y training-position set now contains
13 distinct positions, including `(8,2)`. Case identities, volumes,
positions, splits, source mappings, solver budget, and checks were fixed
before generation. The 240-update physical-plateau solver and B2.4
terminal-label schema and numerical quality rules were unchanged.

## Complete materialization and audit

| Measure | Audited result | Frozen Gate |
|---|---:|---:|
| Successful labels | 30/30; train 20, validation 10 | 30/30 with exact split |
| Terminal stop | 30 physical-plateau stops; max 156 updates | Valid stop within 240 updates |
| Maximum physical-volume error | `8.424692277131385e-09` | `<=0.005` |
| Compliance | Positive and finite in all 30 cases | Positive and finite |
| Total elapsed | `768.5510693750111 s` | `<=3600 s` |
| Peak RSS | `284,622,848 B` | `<1 GiB` |

The slowest case took `40.59008737502154 s`. The 30 label artifacts
contained `2,560,314` bytes. The committed-source label-index SHA-256 is
`ca1060430f11dc6e3aec497b3297a33191686e9d410c5202bec4d65278cae850`.
There were no failed case IDs. Every case remained in its frozen split;
none was removed or relabeled after seeing its result.

The runner's read-only audit reloaded every artifact and checked the
byte hashes, label schema, convergence, compliance, physical volume, and
sensitivity. A separate external audit independently rechecked the plan,
source and context binding, ordered identities, split/volume/position
membership, canonical artifact bytes, all 30 numerical labels, resource
caps, and Gate calculation. It reproduced the same index hash and pass
decision. Generated labels, index, logs, and audit script remain outside
Git.

## Decision and next slice

B2.23 establishes that the fixed position-coverage expansion can be
materialized within its quality and resource bounds. It does not show
that a model trained on the added labels improves terminal quality or
fully charged speed. The next independent slice is **B2.24**, a bounded
training intervention using the 20 new train labels and ten independent
validation labels. Freeze its model/training change, checkpoint rule,
quality and cost Gate, and physically disjoint fresh development screen
before fitting or opening outcomes. A later, separate confirmation is
still required before B3; no acceleration claim follows from this data
Gate.

## Repository validation

The protocol and runner were committed after `uv sync --dev --locked`,
Ruff, mypy on `src`, all 354 Python tests, and `git diff --check` passed.
The required checks are repeated before committing this report.
