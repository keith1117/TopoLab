"""Explicit synthetic B3 contract fixtures; these are never production labels."""

from functools import lru_cache

import numpy as np
import pytest

from topolab.b2_4_labels import store_terminal_design
from topolab.b3_dataset import (
    B3_LOCK_SHA256,
    B3DataContext,
    B3DataRuntime,
    B3DatasetManifest,
    B3LabelRecord,
    B3ReferenceRecord,
)
from topolab.dataset import DatasetEnvironment
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import generate_structured_hex8
from topolab.model import FixedFaceSupport, PointLoad
from topolab.problem import IterationResult, TopologyResult
from topolab.simp import apply_density_filter, build_density_filter, evaluate_compliance


@pytest.fixture(scope="session")
def b3_manifest():  # type: ignore[no-untyped-def]
    return B3DatasetManifest.from_context(
        B3DataContext(
            source_revision="a" * 40,
            environment=DatasetEnvironment(
                python_version="3.12.10",
                numpy_version="2.5.3",
                scipy_version="1.18.1",
                lockfile_sha256=B3_LOCK_SHA256,
            ),
            runtime=B3DataRuntime(
                os_version="synthetic-test-host",
                memory_bytes=16 * 1024**3,
                torch_version="2.14.0",
            ),
        )
    )


@pytest.fixture(scope="session")
def b3_record_factory(b3_manifest):  # type: ignore[no-untyped-def]
    @lru_cache
    def make(entry):  # type: ignore[no-untyped-def]
        # One independently solved uniform state, with a synthetic convergence receipt.
        # No optimization, dataset generation, or development/final outcome is claimed.
        problem = entry.case.problem
        mesh = generate_structured_hex8(*problem.mesh.element_counts, lengths=problem.mesh.lengths)
        design = np.full(mesh.element_dofs.shape[0], problem.optimization.volume_fraction)
        physical = apply_density_filter(
            build_density_filter(mesh, problem.optimization.filter_radius), design
        )
        load = problem.loads[0]
        constrained = build_constrained_dofs(mesh, [FixedFaceSupport(axis="x", side="min")])
        analysis = evaluate_compliance(
            mesh,
            physical,
            build_load_vector(
                mesh,
                [PointLoad(node=load.node, direction=load.direction, magnitude=load.magnitude)],
            ),
            constrained,
            solid_modulus=problem.material.solid_modulus,
            minimum_modulus=problem.material.minimum_modulus,
            poisson_ratio=problem.material.poisson_ratio,
            penalty=problem.optimization.penalty,
        )
        state = IterationResult(
            iteration=1,
            compliance=analysis.compliance,
            volume_fraction=float(np.mean(physical)),
            density_change=0.0,
            design_density=tuple(design),
            physical_density=tuple(physical),
        )
        result = TopologyResult(
            design_density=state.design_density,
            physical_density=state.physical_density,
            compliance=state.compliance,
            displacements=tuple(analysis.displacements),
            reactions=tuple(analysis.reactions),
            history=(state,),
            converged=True,
        )
        fields = dict(
            context=b3_manifest.context,
            manifest_sha256=b3_manifest.sha256(),
            entry=entry,
            result=result,
        )
        if entry.role == "screen_validation":
            return B3ReferenceRecord(**fields)
        return B3LabelRecord(**fields, stored=store_terminal_design(entry.case, result))

    return make


@pytest.fixture(scope="session")
def b3_label(b3_manifest, b3_record_factory):  # type: ignore[no-untyped-def]
    entry = next(
        e
        for e in b3_manifest.catalog.for_role("train")
        if e.case.problem.mesh.element_counts == (12, 6, 3)
    )
    return b3_record_factory(entry)


@pytest.fixture(scope="session")
def b3_reference(b3_manifest, b3_record_factory):  # type: ignore[no-untyped-def]
    entry = next(
        e
        for e in b3_manifest.catalog.for_role("screen_validation")
        if e.case.problem.mesh.element_counts == (12, 6, 3)
    )
    return b3_record_factory(entry)
