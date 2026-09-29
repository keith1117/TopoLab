# B2.27 middle-volume large-grid y/z position labels

Date: 2026-09-29 (America/New_York)

Status: **the frozen B2.27 development-label Gate passed.** All 60/60
new uniform labels converged and passed independent quality, identity,
resource, and artifact audits: 40 train and 20 validation, split evenly
between y and z. No model was fitted and no learned speed was measured.
Uniform initialization remains the operational default; B3 and final
evidence remain closed.

## Frozen scope and exposure

The [B2.27 protocol](../planning/b2_27_middle_volume_labels_protocol.md)
fixed plan SHA-256
`29dbfd3ba1c16667c1ba241cc9ad6586bfc26b99a34df882c170fce51fcf00d0`
and bound B2.26's complete screen-index SHA-256
`05fa1f1e825060b144db0cbab728dfe98e3785594fce42ff7aad85e26813307a`.
The read-only plan, materialization, and audit ran from clean committed
source revision `1c26baf77b603af83505582adefe447d8f370618` with one
CPU/BLAS thread and an external artifact root. The exposure ledger
blocked 838 earlier exposed or reserved physical case IDs. None of the
M2 held-out/OOD or final evidence was opened.

The 60 cases use the `(24,12,6)` mesh, negative y/z x-max point loads,
the ten-position interior small-grid pattern doubled into large-grid
node coordinates, and previously unused volumes `0.5175,0.5275,0.5425`.
The two outer volumes give 40 future train labels; `0.5275` gives 20
future validation labels. Each direction has 20 train and ten
validation cases. Every new result has a B2.27 identity linked to its
own 120-update source case. The 240-update physical-plateau label solver,
B2.4 artifact schema, convergence and quality thresholds were unchanged.

## Complete materialization and independent audit

| Measure | Audited result | Frozen Gate |
|---|---:|---:|
| Successful labels | 60/60; train 40, validation 20; y/z 30 each | 60/60 and exact split/direction counts |
| Terminal stop | 56 physical-plateau, 4 design-max; maximum 167 updates | Valid converged stop within 240 updates |
| Maximum physical-volume error | `1.0914065762257508e-08` | `<=0.005` |
| Compliance | Positive and finite in all 60 cases | Positive and finite |
| Total elapsed | `965.1750665830332 s` | `<=3600 s` |
| Peak RSS | `358,465,536 B` | `<1 GiB` |

The slowest case took `31.54057854099665 s`. The 60 label artifacts
contained `5,155,554` bytes. The label-index SHA-256 is
`aa422ab98f9ca102c55cea991ff679b6b5b703abcb4b5456424fbb8878ca1d35`.
There were no failed case IDs. No case was dropped or moved between
splits after observing its result.

The runner's read-only audit reloaded every artifact and rechecked the
byte hash, provenance, stored-state compliance, volume, and sensitivity.
A separate external audit independently checked the frozen plan and
source binding, all ordered case and 120-update source identities,
canonical artifact bytes, 60 numerical labels, position/volume/split
membership, resource caps, and Gate calculation. It reproduced the same
index hash and pass decision. Generated labels, index, and audit code
remain outside Git.

## Decision and next slice

B2.27 establishes feasible, disjoint middle-volume large-grid y/z
position labels. It does not establish that a model trained on them
improves terminal quality or fully charged speed. **B2.28** is the next
independent slice: freeze one bounded training intervention using the
40 new train labels, keep the 20 validation labels separate, and run
a physically disjoint development screen with the unchanged quality
and complete fallback charges. A separate confirmation is still
required before B3 or any acceleration claim.

## Repository validation

The protocol and runner were committed after `uv sync --dev --locked`,
Ruff, mypy on `src`, all 366 Python tests, and `git diff --check` passed.
The required checks are repeated before committing this report.
