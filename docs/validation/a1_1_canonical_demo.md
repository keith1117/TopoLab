# A1.1 canonical local demo validation

Date: 2026-09-24

Slice decision: **PASS**

Parent release: `v1.0.0` (`6b61a92`)

## Scope

This slice adds one versioned public `TopologyProblem` JSON input and a narrow local
CLI that submits it through the existing `RunManager`. It writes a complete run
snapshot to an external directory and prints a compact terminal summary. No numerical
convention, optimizer setting default, API route, persistence schema, worker model,
or ML experiment changed. Gate A1 as a whole remains open until packaging, clean
Linux smoke, and presentation work are complete.

## Frozen demo input

- Version: `canonical-demo.v1`
- File: `src/topolab/examples/canonical_demo_v1.json`
- SHA-256: `b55812661104e1941c131e279db7145d567802bae5c5baa47df30c4732bb7d09`
- Mesh: `4 x 2 x 2` unit Hex8 elements, with the `x=min` face fixed in all directions
- Load: `-1 N` in `y` at node 44, located at `(4, 2, 2)` under the frozen x-fast indexing
- Material: `E_0=1000 Pa`, `E_min=1 Pa`, `nu=0.3`
- SIMP: target physical volume `0.5`, filter radius `1.5`, penalty `3`, minimum density
  `0.05`, move limit `0.2`, convergence tolerance `0.01`, at most `60` iterations

The JSON contains only fields accepted by the frozen public `TopologyProblem`
contract. The same object can be posted unchanged to `POST /runs`.

## Evidence

The documented command was run from the repository root on macOS arm64 with the
locked Python 3.12.10 environment:

```bash
PYTHONPATH=src uv run --locked python -m topolab.demo \
  --output-dir /private/tmp/topolab-a1-demo-smoke
```

The command exited `0`. It printed run ID
`a30dd2b3f1604bdab078e406bfaa357a`, status `succeeded`, `converged=true`,
compliance `0.08167931393462045`, physical volume fraction `0.5000000069447507`,
and an absolute snapshot path under `/private/tmp/topolab-a1-demo-smoke/`. The saved
snapshot had 16 history states, a matching iteration count, and 16 final physical
density values. The observed volume error was about `6.95e-9`, below the existing
`5e-3` small-case acceptance bound. These scalar values describe this run; the tests
assert contract and acceptance properties rather than bitwise cross-platform equality.

Automated tests cover the versioned input's public-contract round trip, complete
CLI solve and snapshot round trip, and refusal to put an output below a Git root.
The build audit found both `topolab/demo.py` and the JSON input in the source
distribution and wheel. Generated snapshots and build products are ignored and were
not added to Git.

| Check | Result |
|---|---|
| `uv sync --dev --locked` | Passed |
| `uv run ruff check .` | Passed |
| `uv run mypy src` | Passed, 27 source files |
| `uv run pytest` | Passed, 265 tests including 3 new demo tests |
| `uv build` | Passed; sdist and wheel contain the demo module and JSON |
| `git diff --check` | Passed |

## Limits

The CLI is a local single-run demonstration. It uses the current in-process job
manager and does not provide a hosted demo, process isolation, checkpoint/resume,
resource quotas, or general performance evidence. The output path is external to
Git; it is not a durable artifact service.
