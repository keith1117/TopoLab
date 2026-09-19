import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConvergenceVisualization } from "./ConvergenceVisualization";
import type { IterationResult } from "./types";

const plotlyMocks = vi.hoisted(() => ({
  purge: vi.fn(),
  react: vi.fn(),
}));

vi.mock("plotly.js-basic-dist-min", () => ({
  default: {
    purge: plotlyMocks.purge,
    react: plotlyMocks.react,
  },
}));

describe("ConvergenceVisualization", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("maps state-consistent history into three aligned traces", async () => {
    render(
      <ConvergenceVisualization
        history={history()}
        targetVolumeFraction={0.4}
        convergenceTolerance={0.01}
      />,
    );

    expect(
      screen.getByRole("img", { name: /across 3 recorded states/ }),
    ).toBeInTheDocument();
    expect(screen.getByText("-40.00%")).toBeInTheDocument();
    expect(screen.getByText("40.00%")).toBeInTheDocument();
    expect(screen.getByText("target 40.00%")).toBeInTheDocument();

    await waitFor(() => expect(plotlyMocks.react).toHaveBeenCalledOnce());
    const [, traces, layout, config] = plotlyMocks.react.mock.calls[0] ?? [];
    expect(traces).toEqual(expect.arrayContaining([
      expect.objectContaining({
        name: "Compliance",
        x: [1, 2, 3],
        y: [100, 75, 60],
        xaxis: "x",
        yaxis: "y",
      }),
      expect.objectContaining({
        name: "Volume fraction",
        y: [50, 42, 40],
        xaxis: "x2",
        yaxis: "y2",
      }),
      expect.objectContaining({
        name: "Density change",
        y: [0.2, 0.08, 0.009],
        xaxis: "x3",
        yaxis: "y3",
      }),
    ]));
    expect(layout).toMatchObject({
      shapes: [
        expect.objectContaining({ yref: "y2", y0: 40, y1: 40 }),
        expect.objectContaining({ yref: "y3", y0: 0.01, y1: 0.01 }),
      ],
      annotations: [
        expect.objectContaining({ yref: "y2", text: "Target 40.00%" }),
        expect.objectContaining({ yref: "y3", text: "Tolerance 0.01" }),
      ],
      yaxis2: expect.objectContaining({ range: [35, 45] }),
      xaxis3: expect.objectContaining({ dtick: 1 }),
    });
    expect(config).toMatchObject({
      responsive: true,
      modeBarButtonsToRemove: ["sendChartToCloud", "select2d", "lasso2d"],
      toImageButtonOptions: { filename: "topolab-convergence" },
    });
  });

  it("shows an explicit empty state without rendering Plotly", () => {
    render(
      <ConvergenceVisualization
        history={[]}
        targetVolumeFraction={0.4}
        convergenceTolerance={0.01}
      />,
    );

    expect(screen.getByText("No iteration history recorded")).toBeInTheDocument();
    expect(plotlyMocks.react).not.toHaveBeenCalled();
  });
});

function history(): IterationResult[] {
  return [
    state(1, 100, 0.5, 0.2),
    state(2, 75, 0.42, 0.08),
    state(3, 60, 0.4, 0.009),
  ];
}

function state(
  iteration: number,
  compliance: number,
  volumeFraction: number,
  densityChange: number,
): IterationResult {
  return {
    iteration,
    compliance,
    volume_fraction: volumeFraction,
    density_change: densityChange,
    design_density: [],
    physical_density: [],
  };
}
