# Documentation guide

TopoLab is in active v2 development. Uniform initialization remains the default;
learned acceleration and full flagship delivery require the later evidence Gates.
Start with [project status](project_status.md) for the current stopping boundary.

## Choose an entry point

| Purpose | Read |
|---|---|
| Run or understand the local application | [Getting started](getting_started.md), [recorded demo](demo.md), [architecture](architecture.md), [frontend](frontend.md) |
| Find the next permitted research slice | [Current status](project_status.md), [English v2 roadmap](planning/TopoLab_v2_development_roadmap.md) |
| Browse overall plans and preregistrations | [Planning index](planning/README.md) |
| Inspect positive and negative evidence | [Validation index](validation/README.md), [development history](development_history.md) |
| Change or contribute to the repository | [Contributing](../CONTRIBUTING.md), [repository policy](repository_policy.md), [agent instructions](../AGENTS.md) |
| Check implementation ownership | [Provenance](../PROVENANCE.md), [reference baseline](reference_baseline.md) |

## Implementation contracts

[Numerical conventions](numerical_conventions.md) freeze indexing, physics,
projection, termination and quality semantics. The [platform contract](platform_contract.md),
[persistence contract](run_persistence.md), [worker protocol](platform_worker_protocol.md)
and [run ownership](run_ownership.md) define execution and recovery boundaries.
[Development environment](development_environment.md) records the local setup.

The current formal ML program is defined by the [B3 experiment contract](b3_experiment_contract.md),
[training contract](b3_training_contract.md) and [screening contract](b3_screening_contract.md).
Later bounded interventions have their own [slice protocols](planning/README.md).
Historical [M0](ml_experiment_contract.md), [M1](m1_training_contract.md),
[M2](m2_experiment_contract.md) and [superseded M3](m3_preregistration.md) contracts
remain public evidence, each with its original outcome and exposure boundary.

## Document responsibilities

README is the stable public entry point. Current status records the latest result
and next slice. AGENTS.md records working constraints and the reading order. The
roadmap defines Gate order and remaining delivery conditions. Development history
preserves the chronology; protocols and validation reports preserve the experiment
commitments and evidence. Directory indices help readers find these records.

Update the current status and relevant indices when closing a slice. Add one
history entry, preserve the original protocols/results, and avoid copying the
same growing chronology into every document. Public claims change only after
the supporting Gate passes. See the [repository policy](repository_policy.md)
for the exact publication boundary.
