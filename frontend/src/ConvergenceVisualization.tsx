import { useEffect, useMemo, useRef, useState } from "react";
import type { Config, Data, Layout, Shape } from "plotly.js-dist-min";

import type { IterationResult } from "./types";

interface ConvergenceVisualizationProps {
  history: readonly IterationResult[];
  targetVolumeFraction: number;
  convergenceTolerance: number;
}

export function ConvergenceVisualization({
  history,
  targetVolumeFraction,
  convergenceTolerance,
}: ConvergenceVisualizationProps) {
  const graphRef = useRef<HTMLDivElement>(null);
  const [renderState, setRenderState] = useState<"idle" | "loading" | "ready">(
    "idle",
  );
  const [renderError, setRenderError] = useState<string | null>(null);
  const summary = useMemo(() => summarizeHistory(history), [history]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph || history.length === 0) {
      setRenderState("idle");
      return;
    }

    let disposed = false;
    let plotly: typeof import("plotly.js-basic-dist-min").default | null = null;
    setRenderState("loading");
    setRenderError(null);

    void import("plotly.js-basic-dist-min")
      .then(async (module) => {
        plotly = module.default;
        await plotly.react(
          graph,
          convergenceTraces(history),
          convergenceLayout(history, targetVolumeFraction, convergenceTolerance),
          convergenceConfig(),
        );
        if (disposed) {
          plotly.purge(graph);
          return;
        }
        setRenderState("ready");
      })
      .catch((error: unknown) => {
        if (!disposed) {
          setRenderError(errorMessage(error));
          setRenderState("idle");
        }
      });

    return () => {
      disposed = true;
      plotly?.purge(graph);
    };
  }, [history, targetVolumeFraction, convergenceTolerance]);

  if (!summary) {
    return (
      <div className="convergence-empty">
        <span aria-hidden="true">↘</span>
        <strong>No iteration history recorded</strong>
        <p>This result does not contain post-update states to plot.</p>
      </div>
    );
  }

  return (
    <div className="convergence-visualization">
      <div className="convergence-summary">
        <SummaryMetric
          label="Recorded states"
          value={history.length.toLocaleString()}
        />
        <SummaryMetric
          label="Compliance change"
          value={formatPercent(summary.complianceChange)}
        />
        <SummaryMetric
          label="Final volume"
          value={`${(summary.final.volume_fraction * 100).toFixed(2)}%`}
          note={`target ${(targetVolumeFraction * 100).toFixed(2)}%`}
        />
        <SummaryMetric
          label="Final density change"
          value={formatScientific(summary.final.density_change)}
          note={`tolerance ${formatScientific(convergenceTolerance)}`}
        />
      </div>

      <div className="convergence-stage">
        <div
          ref={graphRef}
          className="convergence-plot"
          role="img"
          aria-label={`Convergence history across ${history.length} recorded states; final compliance ${summary.final.compliance}; final volume fraction ${summary.final.volume_fraction}; final density change ${summary.final.density_change}`}
        />
        {renderState === "loading" && (
          <div className="convergence-loading" role="status">
            Preparing convergence history…
          </div>
        )}
        {renderError && (
          <div className="convergence-render-error" role="alert">
            Could not render convergence history: {renderError}
          </div>
        )}
      </div>
      <p className="convergence-note">
        Post-update states · hover to compare exact iteration values
      </p>
    </div>
  );
}

function SummaryMetric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <div className="convergence-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}

function convergenceTraces(history: readonly IterationResult[]): Data[] {
  const iterations = history.map((state) => state.iteration);
  const common = {
    type: "scatter" as const,
    mode: "lines+markers" as const,
    x: iterations,
    marker: { size: 5 },
    line: { width: 2 },
  };
  return [
    {
      ...common,
      name: "Compliance",
      y: history.map((state) => state.compliance),
      xaxis: "x",
      yaxis: "y",
      line: { color: "#2f6fed", width: 2.2 },
      marker: { color: "#2f6fed", size: 5 },
      hovertemplate: "Iteration %{x}<br>Compliance %{y:.6g}<extra></extra>",
    },
    {
      ...common,
      name: "Volume fraction",
      y: history.map((state) => state.volume_fraction * 100),
      xaxis: "x2",
      yaxis: "y2",
      line: { color: "#14866d", width: 2.2 },
      marker: { color: "#14866d", size: 5 },
      hovertemplate: "Iteration %{x}<br>Volume %{y:.3f}%<extra></extra>",
    },
    {
      ...common,
      name: "Density change",
      y: history.map((state) => state.density_change),
      xaxis: "x3",
      yaxis: "y3",
      line: { color: "#b46e16", width: 2.2 },
      marker: { color: "#b46e16", size: 5 },
      hovertemplate: "Iteration %{x}<br>Density change %{y:.6g}<extra></extra>",
    },
  ];
}

function convergenceLayout(
  history: readonly IterationResult[],
  targetVolumeFraction: number,
  convergenceTolerance: number,
): Partial<Layout> {
  const targetVolumePercent = targetVolumeFraction * 100;
  const xAxis = {
    domain: [0, 1] as [number, number],
    gridcolor: "#e1e6ec",
    linecolor: "#cbd4df",
    mirror: true,
    showline: true,
    zeroline: false,
  };
  const yAxis = {
    gridcolor: "#e1e6ec",
    linecolor: "#cbd4df",
    mirror: true,
    showline: true,
    zeroline: false,
    fixedrange: false,
  };
  return {
    autosize: true,
    height: 620,
    margin: { t: 18, r: 34, b: 52, l: 86 },
    paper_bgcolor: "rgba(0, 0, 0, 0)",
    plot_bgcolor: "rgba(0, 0, 0, 0)",
    font: { family: "system-ui, sans-serif", color: "#46556b", size: 11 },
    hovermode: "x unified",
    showlegend: false,
    xaxis: {
      ...xAxis,
      anchor: "y",
      showticklabels: false,
    },
    yaxis: {
      ...yAxis,
      domain: [0.72, 1],
      title: { text: "Compliance", standoff: 10 },
      tickformat: ".4~g",
    },
    xaxis2: {
      ...xAxis,
      anchor: "y2",
      matches: "x",
      showticklabels: false,
    },
    yaxis2: {
      ...yAxis,
      domain: [0.36, 0.64],
      title: { text: "Volume (%)", standoff: 10 },
      range: volumeAxisRange(targetVolumePercent),
      ticksuffix: "%",
      tickformat: ".2f",
    },
    xaxis3: {
      ...xAxis,
      anchor: "y3",
      matches: "x",
      title: { text: "Iteration", standoff: 8 },
      dtick: integerTick(iterationSpan(history)),
    },
    yaxis3: {
      ...yAxis,
      domain: [0, 0.28],
      title: { text: "Density change", standoff: 10 },
      tickformat: ".3~g",
    },
    shapes: referenceLines(targetVolumeFraction, convergenceTolerance),
    annotations: [
      {
        x: 1,
        xref: "paper",
        xanchor: "right",
        y: targetVolumePercent,
        yref: "y2",
        yshift: 9,
        text: `Target ${targetVolumePercent.toFixed(2)}%`,
        showarrow: false,
        font: { color: "#14866d", size: 10 },
      },
      {
        x: 1,
        xref: "paper",
        xanchor: "right",
        y: convergenceTolerance,
        yref: "y3",
        yshift: 9,
        text: `Tolerance ${formatScientific(convergenceTolerance)}`,
        showarrow: false,
        font: { color: "#9a5b12", size: 10 },
      },
    ],
    uirevision: "topolab-convergence",
  };
}

function volumeAxisRange(targetPercent: number): [number, number] {
  const lower = Math.max(0, targetPercent - 5);
  const upper = Math.min(100, targetPercent + 5);
  if (lower === 0) {
    return [0, 10];
  }
  if (upper === 100) {
    return [90, 100];
  }
  return [lower, upper];
}

function iterationSpan(history: readonly IterationResult[]): number {
  const first = history.at(0);
  const final = history.at(-1);
  return first && final ? final.iteration - first.iteration : 0;
}

function integerTick(span: number): number {
  if (span <= 12) {
    return 1;
  }
  return Math.ceil(span / 10);
}

function referenceLines(
  targetVolumeFraction: number,
  convergenceTolerance: number,
): Partial<Shape>[] {
  return [
    {
      type: "line",
      xref: "paper",
      x0: 0,
      x1: 1,
      yref: "y2",
      y0: targetVolumeFraction * 100,
      y1: targetVolumeFraction * 100,
      line: { color: "#14866d", dash: "dot", width: 1.4 },
    },
    {
      type: "line",
      xref: "paper",
      x0: 0,
      x1: 1,
      yref: "y3",
      y0: convergenceTolerance,
      y1: convergenceTolerance,
      line: { color: "#b46e16", dash: "dot", width: 1.4 },
    },
  ];
}

function convergenceConfig(): Partial<Config> {
  return {
    displaylogo: false,
    modeBarButtonsToRemove: ["sendChartToCloud", "select2d", "lasso2d"],
    responsive: true,
    scrollZoom: false,
    toImageButtonOptions: {
      filename: "topolab-convergence",
      format: "png",
      scale: 2,
    },
  };
}

function summarizeHistory(history: readonly IterationResult[]) {
  const first = history.at(0);
  const final = history.at(-1);
  if (!first || !final) {
    return null;
  }
  const complianceChange = first.compliance === 0
    ? null
    : (final.compliance / first.compliance - 1) * 100;
  return { complianceChange, final };
}

function formatPercent(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatScientific(value: number) {
  if (value === 0) {
    return "0";
  }
  if (Math.abs(value) >= 0.01 && Math.abs(value) < 10_000) {
    return value.toLocaleString(undefined, { maximumSignificantDigits: 5 });
  }
  return value.toExponential(2);
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected visualization failure";
}
