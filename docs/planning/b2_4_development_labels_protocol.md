# B2.4 complete development-label protocol

Status: frozen before full 522-case execution. B2.3's 61/61 sentinel is a
development feasibility result, not a complete label gate. B2.5 fitting is
conditional on this independent data gate.

## Population and version boundary

Use only the committed B2.2 development case/split catalog. Include all 432
small train, 36 small validation, 36 large train, and 18 large validation
cases. Each of the 18 `(direction, volume)` strata retains its original
split and physical small/large pair. Rebuild every case with an explicit
240-update maximum under the unchanged
`topolab.simp.physical_plateau.v1` solver. Keep the B2.2 source case ID,
new physical case ID, and B2.3 `tlcase-b23-v1-*` result ID. Use the
`topolab.b2_3.label.v1` label identity already reserved in B2.3. The B2.4
dataset plan, manifest, index, and artifact formats are separately versioned.
No historical M2 or B2.2 density label is valid under this identity.

The canonical SHA-256 over the full ordered 522-row mapping, policy, maximum,
and label version is
`015ab799be88a5fef763720b2e1c58281dc17aea67c61435bcb87d254f64169c`.
Record the clean committed
source revision, Python/NumPy/SciPy versions, and `uv.lock` SHA-256 in the
external manifest. A tracked-dirty checkout or an output root inside the
repository is invalid. The two existing user-owned untracked note files are
not inputs. Run BLAS/OpenMP/VECLIB/MKL/BLIS with one thread. Artifacts and
checkpoints stay outside Git and are written atomically; resume verifies
manifest identity and every already indexed artifact.

## Per-label contract and quality

Use a projected uniform start. Store exact float32 final design and filtered
physical density in x-fast `(1,z,y,x)` order. Store the full normalized
absolute compliance derivative with respect to **design** density at the
stored physical state, including the density-filter transpose. Divide by
the within-case mean, clip to `[0.25,4]`, and divide by the clipped mean.
The resulting weights are training targets' loss weights, never inference
inputs. Store the full case, split, scale, direction, volume, provenance,
iterations, stop reason, compliance, and physical volume. Each artifact has
a SHA-256 reference in the external index. The index retains every failure.

For every case require a converged terminal state consistent with its final
history row, at most 240 updates, finite positive compliance, filtered
physical-volume error `<= 0.005`, and independent re-solve agreement within
relative `1e-9` at the solver's full-precision terminal state. Re-solve the
stored float32 physical state separately and store that compliance so later
audits compare the exact persisted state within relative `1e-9`. Validate
stored float32 density/filter consistency and
positive finite sensitivity weights. Audit all 522 artifact checksums,
identities, split/stratum/shape counts, and independent numerical quality
from the completed index. Any missing, failed, corrupt, or mismatched case
fails the complete data gate; no case can be dropped or relabeled.

## Resource and leakage Gate

The complete 522-case generation and audit must take no more than **two
hours total wall time** and **1 GiB peak process RSS** on the declared local
machine. Record per-case and total cost, artifact bytes, environment, and
checksum evidence. An interrupted run may resume from verified artifacts,
but all execution segments count toward the cumulative budget. If the cap
is exceeded, stop and report a failed gate under this plan. Test/OOD labels
and outcomes, new final-cohort evidence, and model fitting remain sealed.
The Gate establishes complete development data only, not learned speedup.
