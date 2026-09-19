import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getRun, listRuns } from "./api";
import { App } from "./App";
import type { RunSnapshot, RunSummary } from "./types";

const plotlyMocks = vi.hoisted(() => ({
  purge: vi.fn(),
  react: vi.fn(),
}));

vi.mock("./api", () => ({
  listRuns: vi.fn(),
  getRun: vi.fn(),
}));

vi.mock("plotly.js-gl3d-dist-min", () => ({
  default: {
    purge: plotlyMocks.purge,
    react: plotlyMocks.react,
  },
}));

const listRunsMock = vi.mocked(listRuns);
const getRunMock = vi.mocked(getRun);

describe("App", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders an empty history", async () => {
    listRunsMock.mockResolvedValue({ items: [], next_cursor: null });

    render(<App />);

    expect(await screen.findByText("No runs yet")).toBeInTheDocument();
    expect(screen.getByText("Submitted optimization jobs will appear here in UTC order."))
      .toBeInTheDocument();
  });

  it("appends the next cursor page", async () => {
    listRunsMock
      .mockResolvedValueOnce({
        items: [summary("run-one"), summary("run-two")],
        next_cursor: "run-two",
      })
      .mockResolvedValueOnce({
        items: [summary("run-three")],
        next_cursor: null,
      });

    render(<App />);
    await screen.findByText("run-one");

    fireEvent.click(screen.getByRole("button", { name: "Load more runs" }));

    expect(await screen.findByText("run-three")).toBeInTheDocument();
    expect(listRunsMock).toHaveBeenNthCalledWith(2, "run-two");
    expect(
      screen.queryByRole("button", { name: "Load more runs" }),
    ).not.toBeInTheDocument();
  });

  it("loads one full result on selection", async () => {
    const run = summary("result-a");
    listRunsMock.mockResolvedValue({ items: [run], next_cursor: null });
    getRunMock.mockResolvedValue(snapshot(run));

    render(<App />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Open run result-a" }),
    );

    expect(await screen.findByText("42.125")).toBeInTheDocument();
    expect(screen.getByText("50.00% volume")).toBeInTheDocument();
    expect(getRunMock).toHaveBeenCalledWith("result-a");
  });

  it("reveals the detail panel after a small-screen selection", async () => {
    const run = summary("mobile-result");
    const scrollIntoView = vi.fn();
    window.matchMedia = vi.fn().mockReturnValue({ matches: true });
    Element.prototype.scrollIntoView = scrollIntoView;
    listRunsMock.mockResolvedValue({ items: [run], next_cursor: null });
    getRunMock.mockResolvedValue(snapshot(run));

    render(<App />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Open run mobile-result" }),
    );

    await screen.findByText("42.125");
    await waitFor(() => expect(scrollIntoView).toHaveBeenCalledOnce());
  });

  it("labels persisted timestamps in UTC", async () => {
    listRunsMock.mockResolvedValue({
      items: [summary("utc-run")],
      next_cursor: null,
    });

    render(<App />);

    expect((await screen.findAllByText(/UTC/)).length).toBeGreaterThan(0);
  });

  it("renders and filters the final physical density field", async () => {
    const run = summary("density-result");
    listRunsMock.mockResolvedValue({ items: [run], next_cursor: null });
    getRunMock.mockResolvedValue(
      snapshot(run, [0.1, 0.2, 0.7, 0.8], [2, 2, 1]),
    );

    render(<App />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Open run density-result" }),
    );

    expect(
      await screen.findByRole("heading", { name: "3D density" }),
    ).toBeInTheDocument();
    expect(screen.getByText("2 × 2 × 1 elements")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: /showing 2 of 4 elements/ }),
    ).toBeInTheDocument();
    await waitFor(() => expect(plotlyMocks.react).toHaveBeenCalledOnce());
    expect(plotlyMocks.react.mock.calls[0]?.[3]).toMatchObject({
      modeBarButtonsToRemove: ["sendChartToCloud"],
    });

    fireEvent.change(screen.getByRole("slider", { name: /Density threshold/ }), {
      target: { value: "0.75" },
    });

    expect(screen.getByText("ρ ≥ 0.75")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: /showing 1 of 4 elements/ }),
    ).toBeInTheDocument();
    await waitFor(() => expect(plotlyMocks.react).toHaveBeenCalledTimes(2));

    fireEvent.change(screen.getByRole("slider", { name: /Density threshold/ }), {
      target: { value: "1" },
    });
    expect(
      screen.getByText("No elements meet this threshold"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/drag to rotate/),
    ).not.toBeInTheDocument();
  });

  it("shows a recoverable history error", async () => {
    listRunsMock.mockRejectedValueOnce(new Error("backend unavailable"));
    listRunsMock.mockResolvedValueOnce({ items: [], next_cursor: null });

    render(<App />);

    expect(await screen.findByText("Could not load runs")).toBeInTheDocument();
    expect(screen.getByText("backend unavailable")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await waitFor(() => expect(listRunsMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("No runs yet")).toBeInTheDocument();
  });
});

function summary(runId: string): RunSummary {
  return {
    run_id: runId,
    status: "succeeded",
    iteration: 7,
    cancel_requested: false,
    error: null,
    created_at: "2026-09-18T05:00:00Z",
    updated_at: "2026-09-18T05:01:00Z",
  };
}

function snapshot(
  run: RunSummary,
  density: number[] = [0.5],
  elementCounts: [number, number, number] = [1, 1, 1],
): RunSnapshot {
  return {
    ...run,
    problem: {
      mesh: {
        element_counts: elementCounts,
        lengths: elementCounts.map(Number) as [number, number, number],
      },
    },
    result: {
      design_density: density,
      physical_density: density,
      compliance: 42.125,
      displacements: [],
      reactions: [],
      converged: true,
      history: [
        {
          iteration: 7,
          compliance: 42.125,
          volume_fraction: 0.5,
          density_change: 0.0025,
          design_density: density,
          physical_density: density,
        },
      ],
    },
  };
}
