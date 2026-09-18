# Run persistence and restart recovery

Status: **implemented after v0.3.0 and provisional until the next platform release**.

## Scope

`SqliteRunStore` adds an optional durable boundary beneath `RunManager`. One SQLite
row stores the immutable problem JSON and the latest run status, iteration,
cancellation request, result JSON, and error. SQLAlchemy owns schema creation and
transaction handling; numerical arrays remain represented by the frozen Pydantic
problem/result contracts rather than ORM objects.

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

## Current limits

- The schema is created directly and has no migration framework yet.
- Startup loads all run records into memory; pagination and archival are not present.
- The HTTP surface still requires a known run ID and has no list endpoint.
- SQLite persistence does not provide process-isolated execution, distributed workers,
  authentication, quotas, or artifact storage.
- Optimizer checkpoint/resume is not implemented; interruption recovery deliberately
  terminates abandoned runs as failed.
- Database files and other run artifacts are ignored by Git and must not be committed.
