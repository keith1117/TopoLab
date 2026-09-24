# Contributing

TopoLab is currently an individual portfolio and research-software project.

Before opening a change:

1. keep external code outside this repository unless its license and attribution are
   documented in `PROVENANCE.md`;
2. add or update a numerical test before changing established behavior;
3. run `uv sync --dev --locked`, `uv run ruff check .`, `uv run mypy src`,
   `uv run pytest`, and the frontend checks when that workspace is affected;
4. keep commits scoped to one verifiable change;
5. scope `validated` to the tested numerical behaviors, scope benchmark claims to the
   recorded environment, and do not claim universal scalability or learned
   acceleration without new gate evidence.
