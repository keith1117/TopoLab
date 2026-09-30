# A2.2 durable run ownership and recovery

Status: **versioned A2.2 platform contract**. The public problem/result schema,
run states, HTTP routes and numerical solver are unchanged. This contract
supersedes the v1.0.0 startup rule for queued and running rows.

## Claim and fencing

Every `RunManager` has a new random owner ID. A queued row is persisted without
an owner. Before execution, one manager atomically changes that row from queued
to running, sets its owner ID and a UTC lease deadline. Only that owner may write
progress or a terminal result, and only before the lease expires. A competing
claim or stale terminal write changes no row. The owner ID is cleared at terminal
state. Numerical workers never write SQLite.

The local lease is 10 seconds and the manager renews it every second, independent
of optimization iteration callbacks. This covers a long sparse solve that emits
no progress. Cancellation is stored atomically: queued work becomes cancelled;
running work records the request, which its owner relays to the worker at the
next heartbeat. A child worker also cancels when its manager input pipe closes.
Progress writes preserve an already persisted cancellation request. If a
remote cancellation commits before a success result, the terminal write
atomically records `cancelled` without a result.

## Recovery

At startup and during the heartbeat loop, a manager checks expired ownership.
An unowned or expired running row becomes failed with the existing
`RunInterruptedError` text, retains its last committed iteration and has no
result. It is never replayed because A2.3 has not defined an optimizer
checkpoint. An unowned queued row is eligible for one new atomic claim under
its original run ID. A live run with an unexpired lease is left to its owner.
The manager polls the active queue, so a surviving manager can also discover
queued work left by another API process. Terminal records remain immutable to
stale owners. API reads refresh records owned by another manager.

Custom `RunStore` implementations must provide the atomic claim, renewal,
fenced write, cancellation and expiry operations in the updated protocol.
`SqliteRunStore.save` is now insert-only for historical/imported records;
updates to an existing run must pass through the ownership operations.

Worker exit without a valid terminal message fails the claimed run immediately.
An API crash cannot write a terminal state; after its lease expires, a later
manager records failure. These are job-record recovery rules, not numerical
checkpoint/resume. No job is automatically rerun after an interrupted solve.

## Schema migrations

SQLite `PRAGMA user_version` records the applied schema version. One immediate
transaction applies ordered migrations: version 1 creates or backfills UTC
timestamps on historical run rows; version 2 adds nullable owner and lease
columns. Opening a newer or structurally inconsistent schema fails rather than
silently changing it. Existing v1.0.0 databases have `user_version=0` and are
upgraded in place. Migration code lives in `topolab.run_migrations`; new changes
must add a numbered step there instead of an inline store upgrade.

## Remaining A2 work

A2.2 gives local workers durable record ownership. Optimizer checkpoint/resume,
bounded runtime and artifact sizes, and cancellation after resume remain A2.3
and A2.4 work. Gate A2 therefore remains open. This platform change does not
alter the B3 data Gate or permit an ML acceleration claim.
