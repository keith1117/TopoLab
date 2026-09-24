# Run persistence and restart recovery

Status: **stable in v1.0.0**.

## Scope

`SqliteRunStore` adds an optional durable boundary beneath `RunManager`. One SQLite
row stores the immutable problem JSON, UTC creation/update timestamps, and the latest
run status, iteration, cancellation request, result JSON, and error. SQLAlchemy owns
schema creation and transaction handling; numerical arrays remain represented by the
frozen Pydantic problem/result contracts rather than ORM objects.

Persistence is explicit. Library callers pass a store to `RunManager`, while the API
factory accepts a database path:

```python
from topolab import RunManager, SqliteRunStore, create_app

# Library-owned manager and store:
store = SqliteRunStore("results/topolab.sqlite3")
manager = RunManager(store=store)

# Or API-owned manager and store:
app = create_app(database_path="results/topolab.sqlite3")
```

Supplying both an explicit manager and `database_path` is rejected because ownership
and shutdown would otherwise be ambiguous. Omitting both retains the v0.3.0 in-memory
behavior.

## Write boundary

The manager saves a complete record at each externally meaningful transition:

- before a newly submitted run is handed to the executor;
- when it starts running;
- after each optimizer iteration callback;
- when cancellation is requested; and
- when it reaches `succeeded`, `failed`, or `cancelled`.

Each save is one SQLite transaction. A successful result is therefore durable before
the corresponding terminal snapshot is returned by `wait`. Runs keep separate rows
and independently serialized result objects.

`created_at` is assigned once when a run is submitted. `updated_at` changes on each
persisted lifecycle transition and is returned as a timezone-aware UTC timestamp.
Databases created by the first persistence slice are upgraded in place by adding and
backfilling the two timestamp columns.

## Restart semantics

On construction, a manager with a store loads all existing records:

- `succeeded`, `failed`, and `cancelled` records retain their exact terminal state,
  progress, result, cancellation flag, and error;
- a persisted `queued` or `running` record means the previous process stopped before
  reaching a terminal state. It is atomically changed to `failed`, keeps its last
  iteration number, exposes no result, and records
  `RunInterruptedError: process exited before run reached a terminal state`.

The second rule avoids reporting abandoned work as still active. It is recovery of a
durable record, not automatic retry or numerical checkpoint/resume. A caller may
submit a new run from the persisted problem after making that retry decision explicit.

## Run history pagination

`GET /runs` returns a `RunPage` with summary `items` and `next_cursor`. Summaries omit
the potentially large numerical result arrays; callers fetch one full result through
`GET /runs/{run_id}`. Results are ordered newest first by `(created_at, run_id)`; the
run ID provides a deterministic tie-break when creation timestamps match. The default
page size is 20 and the accepted range is 1 through 100.

When more results exist, `next_cursor` is the final run ID in the current page. Passing
that value as `cursor` starts after the same record. Newer runs inserted between page
requests remain before the cursor and do not duplicate records on subsequent pages.
An unknown cursor returns HTTP `400`, while an invalid page size is rejected by request
validation with HTTP `422`.

## Current limits

- The schema has one built-in additive timestamp migration but no general migration
  framework yet.
- Startup still loads all run records into memory; pagination bounds the HTTP response,
  not database memory use. Filtering, search, deletion, and archival are not present.
- SQLite persistence does not provide process-isolated execution, distributed workers,
  authentication, quotas, or artifact storage.
- Optimizer checkpoint/resume is not implemented; interruption recovery deliberately
  terminates abandoned runs as failed.
- Database files and other run artifacts are ignored by Git and must not be committed.
