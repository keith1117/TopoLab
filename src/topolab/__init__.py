"""TopoLab package."""

from topolab.fem import (
    LinearStaticResult,
    assemble_global_stiffness,
    hex8_element_stiffness,
    isotropic_elasticity_matrix,
    solve_linear_static,
)
from topolab.mesh import Hex8Mesh, generate_structured_hex8

__version__ = "0.0.0"

__all__ = [
    "Hex8Mesh",
    "LinearStaticResult",
    "assemble_global_stiffness",
    "generate_structured_hex8",
    "hex8_element_stiffness",
    "isotropic_elasticity_matrix",
    "solve_linear_static",
]
