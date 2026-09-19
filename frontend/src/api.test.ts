import { afterEach, describe, expect, it, vi } from "vitest";

import { cancelRun, createRun, listRuns } from "./api";
import type { RunSnapshot, TopologyProblem } from "./types";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("API client", () => {
  it("posts one JSON problem to the run endpoint", async () => {
    const problem = sampleProblem();
    const created = sampleSnapshot(problem);
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(created), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(createRun(problem)).resolves.toEqual(created);
    expect(fetchMock).toHaveBeenCalledWith("/runs", {
      method: "POST",
      body: JSON.stringify(problem),
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });
  });

  it("posts a cancellation request for an encoded run identifier", async () => {
    const cancelled = {
      ...sampleSnapshot(sampleProblem()),
      run_id: "run/with space",
      status: "cancelled" as const,
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(cancelled), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(cancelRun("run/with space")).resolves.toEqual(cancelled);
    expect(fetchMock).toHaveBeenCalledWith("/runs/run%2Fwith%20space/cancel", {
      method: "POST",
      headers: { Accept: "application/json" },
    });
  });

  it("formats FastAPI validation locations into a readable error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({
        detail: [{ loc: ["body", "loads", 0, "total"], msg: "Input should not be 0" }],
      }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    ));

    await expect(listRuns()).rejects.toThrow(
      "loads → 0 → total: Input should not be 0",
    );
  });
});

function sampleProblem(): TopologyProblem {
  return {
    mesh: { element_counts: [1, 1, 1], lengths: [1, 1, 1] },
    material: {
      solid_modulus: 1000,
      minimum_modulus: 1,
      poisson_ratio: 0.3,
    },
    supports: [{
      axis: "x",
      side: "min",
      directions: ["x", "y", "z"],
    }],
    loads: [{
      kind: "face",
      axis: "x",
      side: "max",
      direction: "y",
      total: -1,
    }],
    optimization: {
      volume_fraction: 0.5,
      filter_radius: 1.5,
      penalty: 3,
      minimum_density: 0.05,
      move_limit: 0.2,
      convergence_tolerance: 0.01,
      max_iterations: 10,
    },
    initial_density: null,
  };
}

function sampleSnapshot(problem: TopologyProblem): RunSnapshot {
  return {
    run_id: "created-run",
    status: "queued",
    iteration: 0,
    cancel_requested: false,
    error: null,
    created_at: "2026-09-19T12:00:00Z",
    updated_at: "2026-09-19T12:00:00Z",
    problem,
    result: null,
  };
}
