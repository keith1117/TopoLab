# A2.1 local process worker validation

Date: 2026-09-30 (America/New_York)

Status: **A2.1 implementation passed local validation.** Gate A2 remains open.
This slice establishes the [versioned worker protocol](../platform_worker_protocol.md)
without changing the SIMP solver or the public problem/result and HTTP contracts.

## Scope and evidence

The default `RunManager` supervises one separate local Python process per active
run, with the existing bounded `max_workers=2` default. It sends a validated
`TopologyProblem` as JSON, accepts a child PID, strictly increasing iteration
events, and one validated terminal result. The manager alone writes progress and
terminal state to SQLite. A worker-reported exception, malformed event, or missing
terminal event fails that run without admitting an unverified result. Cancellation
travels over the same serialized channel and remains cooperative between SIMP
iterations. Injected custom runners retain the prior in-process test path.

New tests exercise a real child PID, complete numerical progress and result
round-trip, wrong-version and extra-field rejection, child-side cancellation,
manager-side cancellation after process launch, and unexpected child exit while
another run succeeds. Existing API, run-state, and SQLite persistence tests also
run against the new default process path. No production B3 label, model, or final
case is accessed by these tests.

The local environment is macOS arm64, Python 3.12.10, with dependencies from
the unchanged `uv.lock`. `uv sync --dev --locked`, Ruff, mypy (47 source files),
the full pytest suite (**566 passed in 278.97 seconds**), and `git diff --check`
passed before commit. No numerical tolerance or termination convention changed.

## Remaining boundary and next slice

SQLite still has no durable worker owner or lease. An API restart retains the
existing rule that marks previously queued/running rows failed; there is no
automatic claim recovery or optimizer resume. A2.1 does not satisfy Gate A2 or
authorize a process-recovery claim. A2.2 will add durable ownership and recovery,
including duplicate-claim and crash tests and a proper schema migration path.
Later A2.3 owns optimizer checkpoint/resume. Uniform initialization remains the
operational default; B4/B5 still determine any learned acceleration claim.
