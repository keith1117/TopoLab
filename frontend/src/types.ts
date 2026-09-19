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

export type Axis = "x" | "y" | "z";
export type FaceSide = "min" | "max";
export type Direction = Axis | 0 | 1 | 2;

export interface MaterialDefinition {
  solid_modulus: number;
  minimum_modulus: number;
  poisson_ratio: number;
}

export interface FixedFaceSupportDefinition {
  axis: Axis;
  side: FaceSide;
  directions: Direction[];
}

export interface FaceLoadDefinition {
  kind: "face";
  axis: Axis;
  side: FaceSide;
  direction: Direction;
  total: number;
}

export interface PointLoadDefinition {
  kind: "point";
  node: number;
  direction: Direction;
  magnitude: number;
}

export interface OptimizationDefinition {
  volume_fraction: number;
  filter_radius: number;
  penalty: number;
  minimum_density: number;
  move_limit: number;
  convergence_tolerance: number;
  max_iterations: number;
}

export interface TopologyProblem {
  mesh: MeshDefinition;
  material: MaterialDefinition;
  supports: FixedFaceSupportDefinition[];
  loads: (FaceLoadDefinition | PointLoadDefinition)[];
  optimization: OptimizationDefinition;
  initial_density: number[] | null;
}

export interface RunSnapshot extends RunSummary {
  problem: TopologyProblem;
  result: TopologyResult | null;
}
