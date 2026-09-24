# M2 catalog materialization validation

Date: 2026-09-24

Source revision: `d60b7492f4887d73876d1a90c856db7841f3b111`

Catalog ID:
`tlcatalog-m2-v1-af5b7fcffed5a070c3fc370a318605d3652e98c57b706f432203a7fd173fea12`

Manifest SHA-256:
`99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f`

## Scope and decision

This validation executed all 756 cases in the frozen M2 catalog through the guarded
production entrypoint. Labels and the recoverable checkpoint were written only to a
new external, untracked directory. No generated artifact is committed to TopoLab.

The materialization index reached `complete` with **746 succeeded and 10 failed**.
Every successful label and the complete index passed the artifact audit below. All
10 failures were deterministic non-convergence at the frozen 120-iteration limit;
seven failures belong to training, one to ID test, and two to OOD.

The pre-registered experiment requires 432 training labels and forbids post-hoc case
removal or a second M2 catalog. Increasing the iteration limit would change the case
identities and constitute a second catalog. Therefore **the M2 data gate does not
pass, fitting does not start, and learned-model expansion stops**. Uniform
initialization remains the operational default. This is a negative experiment
result, not an artifact-integrity failure.

## Entrypoint defect found before the final run

The first authorized execution used source revision
`85813c59f1f2ca8573c4761ec270b32b07e7ff2c`. It safely stopped after the first solve
because the incremental checkpoint constructor did not propagate the M2 index
version and the new manifest/version guard rejected the M0 default. That external
root contains one unreferenced label and an `in_progress` zero-entry index and is
excluded from every result in this report.

The defect was fixed with a regression test in
[PR #44](https://github.com/keith1117/TopoLab/pull/44). All 262 tests and both CI jobs
passed before merge. A new read-only plan from the clean merged revision produced the
manifest identity above, and the final execution used a fresh external root. No data
from the aborted attempt was reused.

## Fixed environment and execution

- Hardware: Apple M2, 8 logical cores, 8 GiB memory.
- Operating system: macOS 26.5, `arm64`.
- Python 3.12.10, NumPy 2.5.3, SciPy 1.18.1.
- `uv.lock` SHA-256:
  `34e089881d5601a4331cb26896413b9850d8ffc69f87eeaffda352d68db2111d`.
- Numerical thread environment variables were unset; the active numerical libraries
  used their environment-default thread policy.
- The Git worktree was clean. The entrypoint captured the exact source revision and
  rejected repository-internal output before solving.

The production command used the documented form with `--execute` and a fresh
external root named for the source revision. The full run took 3464.43 seconds wall
time, 3126.58 seconds user CPU, and 122.90 seconds system CPU. Process peak resident
set size was 251,723,776 bytes (240.06 MiB). These are single-machine observations,
not portable performance guarantees.

## Complete outcome

The pre-label split counts remained frozen and were not rebalanced.

| Partition | Planned | Succeeded | Failed |
|---|---:|---:|---:|
| Train | 432 | 425 | 7 |
| Validation | 36 | 36 | 0 |
| ID test | 36 | 35 | 1 |
| OOD | 252 | 250 | 2 |
| **Total** | **756** | **746** | **10** |

The complete index was reopened through `read_materialization_index`, and every
success was reopened through `read_label_artifact`. This rechecked canonical JSON,
manifest identity, artifact paths, byte lengths, SHA-256 digests, label schemas,
complete case payloads, source revision, environment, stored `float32` tensors, the
density-filter relation, physical volume, convergence metadata, and provenance.
The external root contains exactly the 746 referenced label files and one index;
there are no missing or unreferenced label files.

Aggregate successful-label checks were:

| Check | Observed result | Contract limit |
|---|---:|---:|
| Iterations | min 11, median 41, mean 45.5871, max 117 | at most 120 |
| Maximum terminal density change | `0.009996043921130737` | at most `0.01` |
| Maximum physical-volume absolute error | `1.044461017674081e-08` | at most `5e-3` |
| Compliance range | `0.002810828957043697` to `0.7757667753981936` | finite and positive |

The 746 label files contain 6,340,334 bytes. The complete canonical index contains
999,594 bytes and has SHA-256
`c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f`.
The full external directory occupies 8,876 KiB on disk.

Re-running the production command against the complete index generated no labels. It
reverified all successful artifacts, reproduced the 746/10 outcome, completed in
6.47 seconds, and left the index checksum unchanged. Its exit status remains nonzero
because the summary truthfully contains terminal failures.

## Failure diagnosis

All failed cases have target physical volume fraction `0.45`. A deterministic
read-only re-solve reproduced every failure at iteration 120. All terminal physical
volumes remained within approximately `9e-9` of the target, but terminal density
change was above the frozen `0.01` convergence tolerance.

| Split | Direction | Loaded-face `(y,z)` | Terminal density change | Case ID |
|---|---|---:|---:|---|
| Test | y | `(1,2)` | `0.015050465758360332` | `tlcase-v1-208428786bd5f2848382f53adde4daf7597fccff972137f570b363c4ce819429` |
| Train | y | `(0,2)` | `0.014945729295980925` | `tlcase-v1-24b747bb3124e5a73377d242f3495ba21eafcae733951d71825959df9cc5db46` |
| Train | y | `(0,1)` | `0.014945729295677501` | `tlcase-v1-30e4d8d6e46e95725d887bb2ea1358670b6652087dd247ef1b7c36ce54ddeede` |
| Train | y | `(5,2)` | `0.015050465758114084` | `tlcase-v1-7e3a39ed50f58afcaaa5dd1a629cfa50a7ec4cef6188cec0417770c99d2b3f72` |
| OOD | x | `(3,2)` | `0.01214422876308685` | `tlcase-v1-7f23d9d86e8a22ed9aa6d13d16fea2c85b5a87aa5d85ff16b94ee316d4b8b17f` |
| Train | y | `(6,2)` | `0.01494572929580662` | `tlcase-v1-a94c489359cea9ca6511cff800362deac849af8804fca28d90b889e6b8bb6dfe` |
| Train | y | `(1,1)` | `0.015050465758032927` | `tlcase-v1-ae72ada0ed6dc2623ce41a4da79c99ac4a01bc6a2953eef4e5c857616de98ade` |
| OOD | x | `(3,1)` | `0.01214422875275667` | `tlcase-v1-eea28c7df09bd6978a57a9b25eb163c5995fb22133f2cc25d8124f6f0a34f4a0` |
| Train | y | `(5,1)` | `0.015050465758323472` | `tlcase-v1-f9b7ae089d571f57c5b50cb1e78f7f5df8a433ff34d821794282d22fa86ba382` |
| Train | y | `(6,1)` | `0.014945729295975818` | `tlcase-v1-fc9cf47d23948ae3be2030824679ed3879ab85f3e7d300cf46878f1ad631b25f` |

The repeated values across symmetric locations support a numerical limit-cycle or
slow-convergence interpretation at this volume fraction. They do not justify
loosening the tolerance after observation. No failure was converted to a label.

## Gate result and next action

No tolerance was loosened, no iteration budget was increased, no case was removed,
no split was rebalanced, and no failed outcome was overwritten. The complete
materialization remains immutable evidence for the pre-registered M2 attempt.

Because the required 432-label training partition is incomplete, implementing the
M2 fitting, ensemble calibration, or final runner would not execute the frozen
experiment. Those steps are canceled. The next development slice should close the
release around the validated numerical/platform system, preserve the negative M1 and
M2 evidence, and retain uniform initialization as the supported operational path.
