# Development environment baseline

Recorded on 2026-09-17 for reproducibility and future performance reporting.

## Local machine

- Model: MacBook Air (Mac14,2)
- Chip: Apple M2
- CPU cores: 8 (4 performance, 4 efficiency)
- Memory: 8 GB
- Operating system: macOS 26.5, Darwin 25.5.0
- Architecture: Apple Silicon (`arm64`)

## Toolchain

- Python: 3.12.10
- Environment and lockfile: uv 0.11.15
- Source control: Apple Git 2.39.2

Exact Python dependencies are recorded in `uv.lock`.

The first reproducible sparse assembly/solve measurements on this machine are recorded
in [`validation/sparse_solver_benchmark.md`](validation/sparse_solver_benchmark.md).

## Resource implications

This machine is sufficient for repository development, unit tests, small reference
meshes, and initial sparse benchmarks. The 8 GB memory limit must be reported with
performance results and will constrain dense matrices and large 3D datasets. Larger
benchmark cases and ML training may use a temporary remote CPU/GPU only after local
correctness gates pass; remote hardware results must be reported separately.

Serial numbers, hardware UUIDs, usernames, and other device identifiers are
intentionally excluded.
