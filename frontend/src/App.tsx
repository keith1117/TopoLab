import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getRun, listRuns } from "./api";
import { DensityVisualization } from "./DensityVisualization";
import type { RunSnapshot, RunStatus, RunSummary } from "./types";

const STATUS_LABELS: Record<RunStatus, string> = {
  queued: "Queued",
  running: "Running",
  succeeded: "Succeeded",
  failed: "Failed",
  cancelled: "Cancelled",
};

export function App() {
  const detailPanelRef = useRef<HTMLElement>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<RunSnapshot | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const loadInitialRuns = useCallback(async () => {
    setIsInitialLoading(true);
    setListError(null);
    setSelectedId(null);
    setDetail(null);
    setDetailError(null);
    try {
      const page = await listRuns();
      setRuns(page.items);
      setNextCursor(page.next_cursor);
    } catch (error) {
      setRuns([]);
      setNextCursor(null);
      setListError(errorMessage(error));
    } finally {
      setIsInitialLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadInitialRuns();
  }, [loadInitialRuns]);

  const loadMore = async () => {
    if (!nextCursor || isLoadingMore) {
      return;
    }
    setIsLoadingMore(true);
    setListError(null);
    try {
      const page = await listRuns(nextCursor);
      setRuns((current) => [...current, ...page.items]);
      setNextCursor(page.next_cursor);
    } catch (error) {
      setListError(errorMessage(error));
    } finally {
      setIsLoadingMore(false);
    }
  };

  const openRun = async (runId: string) => {
    setSelectedId(runId);
    setDetail(null);
    setDetailError(null);
    setIsDetailLoading(true);
    try {
      setDetail(await getRun(runId));
      if (window.matchMedia?.("(max-width: 980px)")?.matches) {
        requestAnimationFrame(() => {
          detailPanelRef.current?.scrollIntoView?.({
            behavior: "smooth",
            block: "start",
          });
        });
      }
    } catch (error) {
      setDetailError(errorMessage(error));
    } finally {
      setIsDetailLoading(false);
    }
  };

  const counts = useMemo(() => summarizeStatuses(runs), [runs]);

  return (
    <div className="app-shell">
      <header className="hero">
        <nav className="topbar" aria-label="Product">
          <div className="brand-lockup">
            <span className="brand-mark" aria-hidden="true">
              TL
            </span>
            <div>
              <strong>TopoLab</strong>
              <span>Optimization workspace</span>
            </div>
          </div>
          <div className="contract-state">
            <span className="contract-dot" aria-hidden="true" />
            Persistent run history
          </div>
        </nav>

        <div className="hero-copy">
          <div>
            <p className="eyebrow">Structured 3D SIMP · Operations</p>
            <h1>Run history, without the noise.</h1>
            <p className="hero-description">
              Inspect solver progress and terminal results through the frozen
              TopoLab platform contract.
            </p>
          </div>
          <button
            className="refresh-button"
            type="button"
            onClick={() => void loadInitialRuns()}
            disabled={isInitialLoading}
          >
            <span aria-hidden="true">↻</span>
            {isInitialLoading ? "Refreshing" : "Refresh runs"}
          </button>
        </div>

        <div className="metric-strip" aria-label="Loaded run summary">
          <Metric label="Loaded" value={runs.length} />
          <Metric label="Active" value={counts.active} tone="blue" />
          <Metric label="Succeeded" value={counts.succeeded} tone="green" />
          <Metric label="Needs attention" value={counts.attention} tone="red" />
        </div>
      </header>

      <main className="workspace">
        <section className="panel history-panel" aria-labelledby="history-title">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Operations log</p>
              <h2 id="history-title">Optimization runs</h2>
            </div>
            <span className="page-note">Newest first</span>
          </div>

          {listError && (
            <ErrorNotice
              title="Could not load runs"
              message={listError}
              actionLabel="Try again"
              onAction={() => void loadInitialRuns()}
            />
          )}

          {isInitialLoading ? (
            <RunListSkeleton />
          ) : listError && runs.length === 0 ? null : runs.length === 0 ? (
            <div className="empty-state">
              <span className="empty-glyph" aria-hidden="true">
                ∅
              </span>
              <h3>No runs yet</h3>
              <p>Submitted optimization jobs will appear here in UTC order.</p>
            </div>
          ) : (
            <div className="run-list">
              <div className="run-list-header" aria-hidden="true">
                <span>Status</span>
                <span>Run ID</span>
                <span>Iteration</span>
                <span>Updated</span>
              </div>
              {runs.map((run) => (
                <button
                  className="run-row"
                  data-selected={selectedId === run.run_id}
                  key={run.run_id}
                  type="button"
                  aria-label={`Open run ${run.run_id}`}
                  aria-pressed={selectedId === run.run_id}
                  onClick={() => void openRun(run.run_id)}
                >
                  <StatusBadge status={run.status} />
                  <span className="run-id" title={run.run_id}>
                    {shortId(run.run_id)}
                  </span>
                  <span className="iteration-value">
                    <small>Iteration</small>
                    {run.iteration.toLocaleString()}
                  </span>
                  <span className="time-value">
                    <small>Updated</small>
                    {formatTimestamp(run.updated_at)}
                  </span>
                  <span className="row-arrow" aria-hidden="true">
                    →
                  </span>
                </button>
              ))}
              {nextCursor && (
                <button
                  className="load-more-button"
                  type="button"
                  onClick={() => void loadMore()}
                  disabled={isLoadingMore}
                >
                  {isLoadingMore ? "Loading…" : "Load more runs"}
                </button>
              )}
            </div>
          )}
        </section>

        <aside
          className="panel detail-panel"
          aria-labelledby="detail-title"
          ref={detailPanelRef}
        >
          <div className="panel-heading detail-heading">
            <div>
              <p className="section-kicker">Inspection</p>
              <h2 id="detail-title">Run detail</h2>
            </div>
            {detail && <StatusBadge status={detail.status} />}
          </div>

          {!selectedId ? (
            <div className="detail-placeholder">
              <div className="axis-cube" aria-hidden="true">
                <span>x</span>
                <span>y</span>
                <span>z</span>
              </div>
              <h3>Select a run</h3>
              <p>Choose a row to inspect its latest solver state and result.</p>
            </div>
          ) : isDetailLoading ? (
            <DetailSkeleton />
          ) : detailError ? (
            <ErrorNotice title="Could not load detail" message={detailError} />
          ) : detail ? (
            <RunDetail run={detail} />
          ) : null}
        </aside>

        {detail?.result && (
          <section
            className="panel density-panel"
            aria-labelledby="density-title"
          >
            <div className="panel-heading density-heading">
              <div>
                <p className="section-kicker">Final physical field</p>
                <h2 id="density-title">3D density</h2>
              </div>
              <span className="mesh-chip">
                {detail.problem.mesh.element_counts.join(" × ")} elements
              </span>
            </div>
            <DensityVisualization
              key={detail.run_id}
              density={detail.result.physical_density}
              mesh={detail.problem.mesh}
            />
          </section>
        )}
      </main>

      <footer>
        <span>TopoLab platform · post-P1</span>
        <span>UTC timestamps · cursor pagination · physical density</span>
      </footer>
    </div>
  );
}

function RunDetail({ run }: { run: RunSnapshot }) {
  const result = run.result;
  const lastIteration = result?.history.at(-1);

  return (
    <div className="detail-content">
      <div className="identity-block">
        <span>Run identifier</span>
        <code>{run.run_id}</code>
      </div>

      <dl className="detail-times">
        <div>
          <dt>Created</dt>
          <dd>{formatTimestamp(run.created_at)}</dd>
        </div>
        <div>
          <dt>Last update</dt>
          <dd>{formatTimestamp(run.updated_at)}</dd>
        </div>
      </dl>

      {run.error && (
        <div className="solver-error" role="alert">
          <strong>Solver message</strong>
          <p>{run.error}</p>
        </div>
      )}

      {result ? (
        <>
          <div className="result-grid">
            <ResultMetric
              label="Compliance"
              value={formatScientific(result.compliance)}
            />
            <ResultMetric
              label="Converged"
              value={result.converged ? "Yes" : "No"}
            />
            <ResultMetric
              label="Elements"
              value={result.physical_density.length.toLocaleString()}
            />
            <ResultMetric
              label="Iterations"
              value={run.iteration.toLocaleString()}
            />
          </div>

          <div className="state-card">
            <div>
              <span>Final state</span>
              <strong>
                {lastIteration
                  ? `${(lastIteration.volume_fraction * 100).toFixed(2)}% volume`
                  : "Result available"}
              </strong>
            </div>
            {lastIteration && (
              <div>
                <span>Density change</span>
                <strong>{formatScientific(lastIteration.density_change)}</strong>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="pending-result">
          <span className="pending-pulse" aria-hidden="true" />
          <div>
            <strong>{terminalWithoutResult(run.status)}</strong>
            <p>Latest recorded iteration: {run.iteration.toLocaleString()}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number;
  tone?: "neutral" | "blue" | "green" | "red";
}) {
  return (
    <div className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
    </div>
  );
}

function ResultMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="result-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusBadge({ status }: { status: RunStatus }) {
  return (
    <span className={`status-badge status-${status}`}>
      <span aria-hidden="true" />
      {STATUS_LABELS[status]}
    </span>
  );
}

function ErrorNotice({
  title,
  message,
  actionLabel,
  onAction,
}: {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="error-notice" role="alert">
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
      {actionLabel && onAction && (
        <button type="button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}

function RunListSkeleton() {
  return (
    <div className="skeleton-list" aria-label="Loading run history">
      {[0, 1, 2, 3].map((item) => (
        <span key={item} />
      ))}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="detail-skeleton" aria-label="Loading run detail">
      <span />
      <span />
      <span />
    </div>
  );
}

function summarizeStatuses(runs: RunSummary[]) {
  return runs.reduce(
    (counts, run) => {
      if (run.status === "queued" || run.status === "running") {
        counts.active += 1;
      } else if (run.status === "succeeded") {
        counts.succeeded += 1;
      } else {
        counts.attention += 1;
      }
      return counts;
    },
    { active: 0, succeeded: 0, attention: 0 },
  );
}

function shortId(runId: string) {
  return runId.length > 12 ? `${runId.slice(0, 8)}…${runId.slice(-4)}` : runId;
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date(value));
}

function formatScientific(value: number) {
  if (value === 0) {
    return "0";
  }
  if (Math.abs(value) >= 0.01 && Math.abs(value) < 10_000) {
    return value.toLocaleString(undefined, { maximumSignificantDigits: 6 });
  }
  return value.toExponential(3);
}

function terminalWithoutResult(status: RunStatus) {
  if (status === "failed") {
    return "Run failed without a result";
  }
  if (status === "cancelled") {
    return "Run was cancelled";
  }
  return "Result pending";
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected request failure";
}
