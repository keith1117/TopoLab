# B4.1 fixed fitting and artifact audit

Date: 2026-10-01 (America/New_York)

Status: **implementation verification complete; production fitting pending
the clean merged runner revision.** The [B3 experiment contract](../b3_experiment_contract.md)
and [B3.4 passed data receipt](b3_4_data_gate.md) are unchanged. This first
PR implements the [fitting boundary](../b3_training_contract.md), without a
production fit, screening query, primary selection or final artifact access.

The implementation uses the fixed four recipes and three seeds, existing
thirteen-channel input and context CNN, terminal-design labels and AdamW
recipe. Exact label memberships are checked before byte reads. B3 checkpoint
selection gives each physical case equal weight, independently of its voxel
count; historical B2 fitting and outcomes keep their original definitions.

Synthetic tests verify exact 468/508/508/488 train and 32/32/32/4 selection
populations, weight counts, pure-shape one-exposure batches, the equal-case
MSE denominator, deterministic initialization/shuffle, earliest strict ties,
RNG restoration, exact B3.4 receipt enforcement, checksum/provenance rejection,
history termination, complete membership before opening labels, immutable
prefix/charges, pending-fit recovery, hard-crash accounting, writer exclusion,
resource/epoch stops, permanent failures and side-effect-free planning.
The tests never read production B3 label bytes or fit production cases.

Locked sync, Ruff, mypy (51 source files), all **600 Python tests** in
**352.58 seconds**, and diff checks passed before the runner commit. No
numerical tolerance changes. After this runner PR passes CI and merges, this same
B4.1 slice executes the twelve fits and supplements this report with the
complete independent artifact/selection/resource audit. The next independent
slice after B4.1 completion is **B4.2: the fixed 48-case, 720-outcome
development screen, prospective primary selection and freeze audit**.
Gate B4 and the later final acceleration Gates remain open.
