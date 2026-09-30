# B3.2 frozen catalog and access boundary

Date: 2026-09-30 (America/New_York)

Status: **B3.2 implementation Gate passed.** The exact B3 metadata
contracts and consumer access guards are implemented and tested.
The [B3.1 contract](../b3_experiment_contract.md) is byte-for-byte
unchanged. **Gate B3 data remains pending** its complete materialization
and numerical/provenance audit. Uniform remains the operational default;
this slice establishes no learned acceleration result.

## Implementation and independent identity check

`topolab.b3_catalog` constructs the complete normalized problems,
case roles, original 240-update source links, train memberships, and
historical ledger without invoking solver, encoding, training, or
artifact I/O. Historical grids are reconstructed from the repository's
published case rules; the production module imports no experiment script.
The complete M3 catalog must match its original published SHA-256 before
its 96 final definitions enter the ledger. Failed and unopened reserved
B2.17/B2.18 cases and both B2.10 iteration budgets remain included.

The new implementation's canonical catalog and ledger bytes were
compared directly with the independent external B3.1 audit files;
both matched exactly. Their hashes, strict serialization, immutable
metadata envelopes, full JSON round trips, and the unchanged contract
hash are also repository regression checks:

```text
catalog  441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c
exposure 5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7
contract 452a6c1b3664e007a258a914877c935f333c1823f3ec3d977ee0d09583129af8
```

| Metadata check | Result |
|---|---:|
| Total case definitions | 752 |
| Train / fit-validation / screen-validation / final-ID / final-OOD | 528 / 32 / 48 / 96 / 48 |
| Base / expanded / specialist memberships | 468 / 508 / 488 |
| Small / large train definitions | 432 / 96 |
| Historical unique case IDs / physical fingerprints | 1,982 / 1,376 |
| Cross-role physical intersections | 0 |
| Non-train / historical physical intersections | 0 |
| Matched x-OOD / y-ID counterparts | 48 / 48 |
| New-slice solver calls / generated artifacts read | 0 / 0 |

Fingerprinting reparses the complete problem through `ExperimentCase`,
retains all physical fields and null initialization, and removes only
`optimization.max_iterations`. Budget aliases retain exposure even when
their case IDs change. Catalog construction and deserialization reject
incorrect fingerprints, roles, budgets, source IDs, memberships, missing
or duplicate cases, and changed hashes. Nested instances are revalidated,
including copies that bypass a model's normal constructor.

## Access and derived-origin checks

`topolab.b3_access` accepts verified reference metadata and an explicit
storage callback. It validates roles/memberships and every declared
physical origin before invoking that callback, then verifies the
returned bytes against their SHA-256. A reference must match the full
frozen assignment and exact B3 case identity. Missing or foreign physical
origins, historical 240-update origins, and changed-budget origins are
rejected. Per-case tensors, repeats, trajectories, or augmentations
therefore cannot acquire a different access role through reference metadata.

| Consumer | Guard behavior |
|---|---|
| Planning | All case/reference metadata; no artifact bytes |
| Data audit | 560 train/fit-validation labels and 48 screen uniform references |
| Fitting and epoch selection | Requested train membership plus fit-validation labels; specialist validation restricted to its four fixed metric cases |
| Nearest neighbor | Exact complete population of 528 train labels; individual reads, missing labels, duplicates, and other roles rejected |
| Screen and candidate selection | Screen metadata and outcome records; label/reference bytes rejected |
| Final query | Final definitions and outcome records; label/reference bytes rejected |

Population reads validate the entire metadata population before the
first callback and return bytes in canonical case-ID order. Fitting,
NN, and data-audit population sizes are fixed by their permitted cases.
The NN consumer cannot open one label through the individual-read API.
There is no root creation, path discovery, real materialization, or
implicit access to historical labels in this implementation.

## Tests, scope, and next slice

The 125 focused tests include 90 consumer/role/kind combinations,
checksum failures, train-membership exclusions, all specialist validation
cases, exact NN/data-audit populations, forged/derived metadata and
before-open callback spies. A cold-process test replaces solver,
encoding, and filesystem operations with failing spies during metadata
construction. Independent B3.1 byte comparison also passed.

Required validation passed locked dependency sync, Ruff, mypy (41
source files), all **499 Python tests** in `249.39 s`, and diff checks
before commit. The PR must pass all CI before merge.
No numerical tolerance, stopping policy, solver implementation, contract,
model, or historical outcome changed. Generated audit/catalog/ledger
files remain outside Git. Real artifact content/provenance validation,
materializer wiring and stage/freeze authorization remain the work of
their respective later slices; synthetic bytes are not numerical labels.

The next independent slice is **B3.3: B3 label/reference artifact
contracts and guarded materializer**. B3.4 then executes and independently
audits all 560 labels and 48 screening references before Gate B3 can pass.
B4 fitting/screen/freeze and B5 final evidence remain separate slices.
