import { useEffect, useMemo, useRef, useState } from "react";
import type { Config, Data, Layout } from "plotly.js-dist-min";

import { buildDensitySurface } from "./densityMesh";
import type { MeshDefinition } from "./types";

const DEFAULT_THRESHOLD = 0.3;

interface DensityVisualizationProps {
  density: readonly number[];
  mesh: MeshDefinition;
}

export function DensityVisualization({
  density,
  mesh,
}: DensityVisualizationProps) {
  const graphRef = useRef<HTMLDivElement>(null);
  const [threshold, setThreshold] = useState(DEFAULT_THRESHOLD);
  const [renderState, setRenderState] = useState<"idle" | "loading" | "ready">(
    "idle",
  );
  const [renderError, setRenderError] = useState<string | null>(null);
  const surfaceResult = useMemo(() => {
    try {
      return {
        error: null,
        surface: buildDensitySurface(
          mesh.element_counts,
          mesh.lengths,
          density,
          threshold,
        ),
      };
    } catch (error) {
      return {
        error: errorMessage(error),
        surface: null,
      };
    }
  }, [density, mesh.element_counts, mesh.lengths, threshold]);

  useEffect(() => {
    const graph = graphRef.current;
    const surface = surfaceResult.surface;
    if (!graph || !surface || surface.visibleElements === 0) {
      setRenderState("idle");
      return;
    }

    let disposed = false;
    let plotly: typeof import("plotly.js-gl3d-dist-min").default | null = null;
    setRenderState("loading");
    setRenderError(null);

    void import("plotly.js-gl3d-dist-min")
      .then(async (module) => {
        plotly = module.default;
        await plotly.react(
          graph,
          [meshTrace(surface)],
          plotLayout(),
          plotConfig(),
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
  }, [surfaceResult.surface]);

  if (surfaceResult.error) {
    return (
      <div className="density-error" role="alert">
        <strong>Density field unavailable</strong>
        <p>{surfaceResult.error}</p>
      </div>
    );
  }

  const surface = surfaceResult.surface;
  if (!surface) {
    return null;
  }

  return (
    <div className="density-visualization">
      <div className="density-toolbar">
        <label htmlFor="density-threshold">
          <span>
            Density threshold
            <small>Hide elements below this physical density.</small>
          </span>
          <output htmlFor="density-threshold">ρ ≥ {threshold.toFixed(2)}</output>
        </label>
        <input
          id="density-threshold"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={threshold}
          onChange={(event) => setThreshold(Number(event.target.value))}
        />
        <div className="density-counts" aria-live="polite">
          <strong>{surface.visibleElements.toLocaleString()}</strong>
          <span>of {surface.totalElements.toLocaleString()} elements shown</span>
        </div>
      </div>

      {surface.visibleElements === 0 ? (
        <div className="density-empty">
          <span aria-hidden="true">ρ</span>
          <strong>No elements meet this threshold</strong>
          <p>Lower the density threshold to reveal the final physical field.</p>
        </div>
      ) : (
        <div className="density-stage">
          <div
            ref={graphRef}
            className="density-plot"
            role="img"
            aria-label={`Interactive 3D physical density field showing ${surface.visibleElements} of ${surface.totalElements} elements`}
          />
          {renderState === "loading" && (
            <div className="density-loading" role="status">
              Preparing 3D field…
            </div>
          )}
          {renderError && (
            <div className="density-render-error" role="alert">
              Could not render the 3D field: {renderError}
            </div>
          )}
        </div>
      )}
      {surface.visibleElements > 0 && (
        <p className="density-note">
          Final filtered physical density · drag to rotate · scroll to zoom
        </p>
      )}
    </div>
  );
}

function meshTrace(surface: ReturnType<typeof buildDensitySurface>): Data {
  return {
    type: "mesh3d",
    x: surface.x,
    y: surface.y,
    z: surface.z,
    i: surface.i,
    j: surface.j,
    k: surface.k,
    intensity: surface.intensity,
    intensitymode: "vertex",
    cmin: 0,
    cmax: 1,
    colorscale: [
      [0, "#dbe8ff"],
      [0.35, "#73a4ff"],
      [0.7, "#2767dc"],
      [1, "#102d62"],
    ],
    flatshading: true,
    opacity: 0.98,
    showscale: true,
    hovertemplate:
      "x %{x:.3g}<br>y %{y:.3g}<br>z %{z:.3g}<br>ρ %{intensity:.3f}<extra></extra>",
    colorbar: {
      title: { text: "Density ρ", font: { color: "#33425a", size: 11 } },
      thickness: 12,
      len: 0.68,
      outlinewidth: 0,
      tickfont: { color: "#5f6f84", size: 10 },
    },
    lighting: {
      ambient: 0.62,
      diffuse: 0.72,
      fresnel: 0.08,
      roughness: 0.82,
      specular: 0.12,
    },
    lightposition: { x: 120, y: 180, z: 220 },
  };
}

function plotLayout(): Partial<Layout> {
  const axis = {
    backgroundcolor: "rgba(0, 0, 0, 0)",
    color: "#718096",
    gridcolor: "#d9e0e8",
    showbackground: false,
    zerolinecolor: "#c5ceda",
  } as const;
  return {
    autosize: true,
    margin: { t: 16, r: 22, b: 12, l: 22 },
    paper_bgcolor: "rgba(0, 0, 0, 0)",
    plot_bgcolor: "rgba(0, 0, 0, 0)",
    font: { family: "system-ui, sans-serif", color: "#33425a" },
    scene: {
      aspectmode: "data",
      camera: { eye: { x: 1.55, y: 1.55, z: 1.18 } },
      xaxis: { ...axis, title: { text: "x" } },
      yaxis: { ...axis, title: { text: "y" } },
      zaxis: { ...axis, title: { text: "z" } },
    },
    showlegend: false,
    uirevision: "topolab-density-camera",
  };
}

function plotConfig(): Partial<Config> {
  return {
    displaylogo: false,
    modeBarButtonsToRemove: ["sendChartToCloud"],
    responsive: true,
    scrollZoom: true,
    toImageButtonOptions: {
      filename: "topolab-density",
      format: "png",
      scale: 2,
    },
  };
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected visualization failure";
}
