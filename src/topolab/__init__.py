"""TopoLab package."""

from topolab.api import create_app
from topolab.fem import (
    LinearStaticResult,
    assemble_global_stiffness,
    build_constrained_dofs,
    build_load_vector,
    hex8_element_stiffness,
    isotropic_elasticity_matrix,
    select_face_nodes,
    solve_linear_static,
)
from topolab.jobs import RunManager, RunNotFoundError, RunSnapshot, RunStatus
from topolab.mesh import Hex8Mesh, generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.problem import (
    FaceLoadDefinition,
    FixedFaceSupportDefinition,
    IterationResult,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
    TopologyResult,
    solve_problem,
)
from topolab.simp import (
    ComplianceResult,
    DensityFilter,
    OptimizationCancelledError,
    SimpConfig,
    SimpIteration,
    SimpResult,
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
    optimality_criteria_update,
    optimize_simp,
    simp_element_moduli,
)

__version__ = "0.2.0"

__all__ = [
    "Hex8Mesh",
    "LinearStaticResult",
    "ComplianceResult",
    "DensityFilter",
    "FaceLoad",
    "FaceLoadDefinition",
    "FixedFaceSupport",
    "FixedFaceSupportDefinition",
    "PointLoad",
    "PointLoadDefinition",
    "IterationResult",
    "MaterialDefinition",
    "MeshDefinition",
    "OptimizationCancelledError",
    "OptimizationDefinition",
    "RunManager",
    "RunNotFoundError",
    "RunSnapshot",
    "RunStatus",
    "SimpConfig",
    "SimpIteration",
    "SimpResult",
    "TopologyProblem",
    "TopologyResult",
    "apply_density_filter",
    "assemble_global_stiffness",
    "build_constrained_dofs",
    "build_load_vector",
    "backpropagate_density_gradient",
    "build_density_filter",
    "create_app",
    "evaluate_compliance",
    "generate_structured_hex8",
    "hex8_element_stiffness",
    "isotropic_elasticity_matrix",
    "optimality_criteria_update",
    "optimize_simp",
    "select_face_nodes",
    "simp_element_moduli",
    "solve_problem",
    "solve_linear_static",
]
