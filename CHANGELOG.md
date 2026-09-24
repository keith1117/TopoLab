# Changelog

## 1.0.0 — 2026-09-24

TopoLab 1.0.0 is the first complete research-software release.

### Included

- independently implemented and validated structured-Hex8 finite elements and 3D
  SIMP topology optimization;
- sparse assembly and solve with a reproducible four-scale performance benchmark;
- typed problem/result contracts, asynchronous in-process runs, cooperative
  cancellation, optional SQLite persistence, restart recovery, and run history;
- a React workspace for problem submission, history, convergence inspection, and
  interactive physical-density visualization; and
- versioned, leakage-safe warm-start data, training, evaluation, recovery, and
  provenance workflows.

### Evidence decisions

- Gates N1, N2, P1, and M0 passed.
- M1 did not establish learned acceleration: ID-test evidence was inconclusive and
  OOD evaluation was slower than uniform initialization with a 25% learned
  failure/fallback rate.
- M2 stopped before fitting because 10 of 756 cases failed its pre-registered data
  gate. Uniform initialization remains the operational default.

### Known limits

This release does not provide distributed or process-isolated workers,
authentication, optimizer checkpoint/resume, a hosted deployment, or a public online
demo. Sparse benchmark results do not establish universal platform scalability.
