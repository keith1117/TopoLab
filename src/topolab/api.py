"""Minimal FastAPI adapter for TopoLab optimization runs."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from topolab.jobs import (
    RunCursorError,
    RunManager,
    RunNotFoundError,
    RunPage,
    RunSnapshot,
)
from topolab.persistence import SqliteRunStore
from topolab.problem import TopologyProblem


def create_app(
    run_manager: RunManager | None = None,
    *,
    database_path: str | Path | None = None,
) -> FastAPI:
    """Create an API backed by one explicit run manager."""

    if run_manager is not None and database_path is not None:
        raise ValueError("database_path cannot be combined with run_manager")
    owned_store = None if database_path is None else SqliteRunStore(database_path)
    manager = RunManager(store=owned_store) if run_manager is None else run_manager
    owns_manager = run_manager is None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        del app
        try:
            yield
        finally:
            if owns_manager:
                manager.shutdown()
            if owned_store is not None:
                owned_store.close()

    app = FastAPI(title="TopoLab", version="1.0.0", lifespan=lifespan)

    @app.post(
        "/runs",
        response_model=RunSnapshot,
        status_code=HTTPStatus.ACCEPTED,
    )
    def create_run(problem: TopologyProblem) -> RunSnapshot:
        return manager.submit(problem)

    @app.get("/runs", response_model=RunPage)
    def list_runs(
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        cursor: str | None = None,
    ) -> RunPage:
        try:
            return manager.list_runs(limit=limit, cursor=cursor)
        except RunCursorError as error:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="invalid run cursor",
            ) from error

    @app.get("/runs/{run_id}", response_model=RunSnapshot)
    def get_run(run_id: str) -> RunSnapshot:
        return _get_or_404(manager, run_id)

    @app.post("/runs/{run_id}/cancel", response_model=RunSnapshot)
    def cancel_run(run_id: str) -> RunSnapshot:
        try:
            accepted = manager.cancel(run_id)
        except RunNotFoundError as error:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="run not found",
            ) from error
        if not accepted:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="run is already terminal",
            )
        return manager.get(run_id)

    return app


def _get_or_404(manager: RunManager, run_id: str) -> RunSnapshot:
    try:
        return manager.get(run_id)
    except RunNotFoundError as error:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="run not found",
        ) from error
