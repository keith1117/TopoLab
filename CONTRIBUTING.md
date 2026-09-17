# Contributing

TopoLab is currently an individual portfolio and research-software project.

Before opening a change:

1. keep external code outside this repository unless its license and attribution are
   documented in `PROVENANCE.md`;
2. add or update a numerical test before changing established behavior;
3. run `uv run ruff check .`, `uv run mypy src`, and `uv run pytest`;
4. keep commits scoped to one verifiable change;
5. do not use `validated`, `scalable`, or `accelerated` in project claims before the
   corresponding planning gate is satisfied.
