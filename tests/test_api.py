import asyncio
from collections.abc import Callable
from threading import Event

import httpx2
from fastapi import FastAPI

from topolab.api import create_app
from topolab.jobs import RunManager, RunStatus
from topolab.problem import TopologyProblem, TopologyResult
from topolab.simp import OptimizationCancelledError, SimpIteration


def test_api_creates_and_reads_an_isolated_run() -> None:
    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, should_cancel, iteration_callback
        return _result()

    async def exercise(
        app: FastAPI,
        manager: RunManager,
    ) -> tuple[httpx2.Response, httpx2.Response]:
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.post("/runs", json=_problem_payload())
            run_id = response.json()["run_id"]
            completed = manager.wait(run_id, timeout=5.0)
            fetched = await client.get(f"/runs/{run_id}")
        assert completed.status is RunStatus.SUCCEEDED
        return response, fetched

    with RunManager(max_workers=1, runner=runner) as manager:
        app = create_app(manager)
        response, fetched = asyncio.run(exercise(app, manager))

    assert app.version == "0.3.0"
    assert response.status_code == 202
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "succeeded"
    assert fetched.json()["result"]["design_density"] == [0.5]


def test_api_cancels_a_running_run() -> None:
    started = Event()
    pause = Event()

    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, iteration_callback
        started.set()
        while not should_cancel():
            pause.wait(0.001)
        raise OptimizationCancelledError("optimization was cancelled")

    async def exercise(
        manager: RunManager,
    ) -> tuple[httpx2.Response, httpx2.Response, RunStatus]:
        transport = httpx2.ASGITransport(app=create_app(manager))
        async with httpx2.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            created = await client.post("/runs", json=_problem_payload())
            run_id = created.json()["run_id"]
            assert started.wait(timeout=2.0)
            cancelled = await client.post(f"/runs/{run_id}/cancel")
            completed = manager.wait(run_id, timeout=5.0)
            repeated = await client.post(f"/runs/{run_id}/cancel")
        return cancelled, repeated, completed.status

    with RunManager(max_workers=1, runner=runner) as manager:
        cancelled, repeated, status = asyncio.run(exercise(manager))

    assert cancelled.status_code == 200
    assert cancelled.json()["cancel_requested"] is True
    assert status is RunStatus.CANCELLED
    assert repeated.status_code == 409


def test_api_rejects_invalid_problems_and_unknown_runs() -> None:
    async def exercise(
        manager: RunManager,
    ) -> tuple[httpx2.Response, httpx2.Response, httpx2.Response]:
        transport = httpx2.ASGITransport(app=create_app(manager))
        async with httpx2.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            payload = _problem_payload()
            payload["supports"] = []
            invalid = await client.post("/runs", json=payload)
            missing = await client.get("/runs/missing")
            cancel_missing = await client.post("/runs/missing/cancel")
        return invalid, missing, cancel_missing

    with RunManager(max_workers=1) as manager:
        invalid, missing, cancel_missing = asyncio.run(exercise(manager))

    assert invalid.status_code == 422
    assert missing.status_code == 404
    assert cancel_missing.status_code == 404


def _problem_payload() -> dict[str, object]:
    return {
        "mesh": {
            "element_counts": [1, 1, 1],
            "lengths": [1.0, 1.0, 1.0],
        },
        "material": {
            "solid_modulus": 1000.0,
            "minimum_modulus": 1.0,
            "poisson_ratio": 0.3,
        },
        "supports": [
            {
                "axis": "x",
                "side": "min",
                "directions": ["x", "y", "z"],
            }
        ],
        "loads": [
            {
                "kind": "point",
                "node": 7,
                "direction": "y",
                "magnitude": -1.0,
            }
        ],
        "optimization": {
            "volume_fraction": 0.5,
            "filter_radius": 1.5,
            "minimum_density": 0.05,
            "max_iterations": 10,
        },
    }


def _result() -> TopologyResult:
    return TopologyResult(
        design_density=(0.5,),
        physical_density=(0.5,),
        compliance=1.0,
        displacements=(),
        reactions=(),
        history=(),
        converged=True,
    )
