# A2.1 local worker protocol

Status: **versioned A2.1 platform contract**. This adds a process boundary to
the existing `RunManager` lifecycle. It does not change the numerical solver,
problem/result schema, run states, or restart policy.

## Transport and ownership

The default manager starts one local Python process per active run, bounded by
`max_workers` (default 2). A manager thread supervises that process. The manager
alone owns run IDs, state transitions, timestamps, SQLite writes, and the public
API. The worker receives one complete `TopologyProblem` and owns only its private
numerical arrays. An explicitly injected `runner` remains an in-process adapter
for tests and embedding callers.

Messages are one UTF-8 JSON object per line on the child's standard input and
output. Every message has `version: "topolab.a2.worker.v1"`, `kind`, and `run_id`.
Unknown fields, versions, kinds, invalid problem/result contracts, and mismatched
run IDs are rejected. No Python object is unpickled across the boundary.

| Direction | Kind | Payload |
|---|---|---|
| Manager → worker | `start` | Complete immutable `problem`; first and only start |
| Manager → worker | `cancel` | Cooperative cancellation request |
| Worker → manager | `started` | Child PID, required before progress or terminal event |
| Worker → manager | `progress` | Strictly increasing post-update iteration number |
| Worker → manager | `succeeded` | Complete validated `TopologyResult` |
| Worker → manager | `failed` | Exception type and concise message |
| Worker → manager | `cancelled` | No result |

The worker emits exactly one terminal event and exits with status 0. The manager
persists each progress update and terminal state before returning its snapshot.
An invalid event, unexpected EOF, or nonzero worker exit marks that run failed;
the manager does not report an unverified result. A cancellation request reaches
the worker through standard input and is observed between solver iterations.
An active sparse solve may finish before cancellation takes effect, as in the
existing public lifecycle contract.

## Boundary of this slice

Queued work remains in the bounded manager executor. SQLite still records a
single latest run row; on API restart, previously queued/running rows are
marked failed under the existing v1.0.0 rule. There is no durable ownership,
lease, heartbeat, duplicate-claim protocol, automatic retry, or optimizer
checkpoint. A2.2 will own durable claims and recovery; A2.3 will separately
define optimizer checkpoint/resume. The numerical core remains independent of
Web, queue, and worker transport code.
