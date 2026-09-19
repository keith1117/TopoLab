export type RunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export interface RunSummary {
  run_id: string;
  status: RunStatus;
  iteration: number;
  cancel_requested: boolean;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface RunPage {
  items: RunSummary[];
  next_cursor: string | null;
}

export interface IterationResult {
  iteration: number;
  compliance: number;
  volume_fraction: number;
  density_change: number;
  design_density: number[];
  physical_density: number[];
}

export interface TopologyResult {
  design_density: number[];
  physical_density: number[];
  compliance: number;
  displacements: number[];
  reactions: number[];
  history: IterationResult[];
  converged: boolean;
}

export interface MeshDefinition {
  element_counts: [number, number, number];
  lengths: [number, number, number];
}

export interface RunProblem {
  mesh: MeshDefinition;
}

export interface RunSnapshot extends RunSummary {
  problem: RunProblem;
  result: TopologyResult | null;
}
