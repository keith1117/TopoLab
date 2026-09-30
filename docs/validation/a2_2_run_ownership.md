# A2.2 durable run ownership and recovery validation

Date: 2026-09-30 (America/New_York)

Status: **A2.2 implementation passed local validation.** Gate A2 remains open
until optimizer checkpoint/resume and resource/cancellation bounds are verified.
The [ownership contract](../run_ownership.md) supersedes the v1.0.0 startup
handling of queued and running rows. No numerical solver convention changed.

## Acceptance boundary

SQLite records a manager owner and UTC lease for a running job. The queued to
running transition is a single conditional update. Progress and terminal writes
require the same owner and an unexpired lease; failed claims and stale writes
change no row. A one-second heartbeat renews a ten-second lease independently
of optimizer iterations and relays persisted cancellation requests. A worker
whose manager pipe closes cancels cooperatively.

After an API crash, a restarted manager retains unexpired ownership, then
records an interrupted running job as failed once its lease expires. It never
replays a partial optimization. Queued records can be claimed and executed
once under their existing run ID. A child crash without a terminal event is
persisted as failure immediately. A surviving manager polls active records so
it can discover queued work left by another API process.

The prior inline timestamp upgrade has been replaced by ordered, transactional
SQLite migrations. Tests cover a pre-timestamp database, version-2 schema,
idempotent reopening, and rejection of a newer unknown schema.

## Tests and limits

Focused tests exercise duplicate claims, stale write fencing, lease renewal
across a long silent runner, queued recovery, cancellation from another
manager, a real API process exit, a killed numerical worker, and worker
cancellation on manager-pipe EOF. A deterministic race test confirms that
progress cannot erase a remote cancellation and that it wins over a later
success write. Existing API, persistence, run lifecycle,
and numerical tests remain part of the full required suite. Test databases
and process artifacts remain outside Git.

On the local macOS arm64/Python 3.12.10 environment, locked `uv sync`, Ruff,
mypy (48 source files), `git diff --check`, and the full **578-test** pytest
suite passed. The full suite took **300.99 seconds**. No numerical tolerance,
termination rule, B3 label, checkpoint, or final evidence changed.

The default executor remains bounded at two concurrent local workers. A2.2
does not add an optimizer checkpoint, numerical resume, distributed compute,
runtime cap, artifact-size cap or broader platform Gate A2 claim. B3 data and
its outcome identities are untouched; uniform remains the operational default.

The next independent slice is **B4.1: twelve fixed CPU fits and artifact audit**
under the passed B3 data Gate. Later B4 screening and B5 final evidence retain
their frozen access and stopping rules.
