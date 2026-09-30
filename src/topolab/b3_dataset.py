"""B3 data provenance, terminal labels, and mandatory screening references."""

import hashlib
from typing import Annotated, Literal

import numpy as np
from pydantic import ConfigDict, Field, model_validator

from topolab.b2_4_labels import (
    StoredDesignState,
    _validate_terminal_state,
    audit_stored_design,
    solve_uniform_terminal,
    store_terminal_design,
)
from topolab.b3_catalog import (
    B3_CATALOG_SHA256,
    B3_CONTRACT_SHA256,
    B3_EXPOSURE_SHA256,
    B3CaseCatalog,
    B3CatalogEntry,
    Sha256,
    build_b3_case_catalog,
    canonical_metadata_bytes,
)
from topolab.baselines import validate_refinement_quality
from topolab.dataset import DatasetEnvironment
from topolab.problem import ContractModel, IterationCallback, TopologyResult

B3_LOCK_SHA256 = "9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292"
B3_NUMERICAL_ANCHOR = "5b34ff9edb8772a4b0f456a7b94c454e16579aa6"
B3_DATA_SECONDS = 14_400.0
B3_DATA_RSS_BYTES = 2_147_483_648
type Revision = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
type NonnegativeSeconds = Annotated[float, Field(ge=0.0)]


class B3DataRuntime(ContractModel):
    """Non-sensitive CPU execution metadata for the frozen Apple label stage."""

    os_family: Literal["Darwin"] = "Darwin"
    os_version: Annotated[str, Field(min_length=1)]
    machine: Literal["arm64"] = "arm64"
    cpu: Literal["Apple M2"] = "Apple M2"
    memory_bytes: Annotated[int, Field(strict=True, gt=0)]
    torch_version: Annotated[str, Field(min_length=1)]
    blas_threads: Literal[1] = 1
    torch_intraop_threads: Literal[1] = 1
    torch_interop_threads: Literal[8] = 8


class B3DataContext(ContractModel):
    """Bindings shared by every regenerated label, reference, and data index."""

    model_config = ConfigDict(revalidate_instances="always")
    experiment_version: Literal["topolab.b3.experiment.v1"] = "topolab.b3.experiment.v1"
    solver_policy: Literal["topolab.simp.physical_plateau.v1"] = "topolab.simp.physical_plateau.v1"
    numerical_source_anchor: Revision = B3_NUMERICAL_ANCHOR
    contract_sha256: Sha256 = B3_CONTRACT_SHA256
    catalog_sha256: Sha256 = B3_CATALOG_SHA256
    exposure_sha256: Sha256 = B3_EXPOSURE_SHA256
    source_revision: Revision
    source_tree_clean: Literal[True] = True
    environment: DatasetEnvironment
    runtime: B3DataRuntime

    @model_validator(mode="after")
    def validate_frozen_bindings(self) -> "B3DataContext":
        expected = (B3_NUMERICAL_ANCHOR, B3_CONTRACT_SHA256, B3_CATALOG_SHA256, B3_EXPOSURE_SHA256)
        if (
            self.numerical_source_anchor,
            self.contract_sha256,
            self.catalog_sha256,
            self.exposure_sha256,
        ) != expected:
            raise ValueError("B3 data context differs from frozen experiment bindings")
        if (
            self.environment.python_version != "3.12.10"
            or self.environment.lockfile_sha256 != B3_LOCK_SHA256
        ):
            raise ValueError("B3 data requires the frozen Python and lockfile")
        return self


class B3DatasetManifest(ContractModel):
    """Complete public catalog with exactly 608 permitted data-stage tasks."""

    model_config = ConfigDict(revalidate_instances="always")
    manifest_version: Literal["topolab.b3.dataset.v1"] = "topolab.b3.dataset.v1"
    split_contract_version: Literal["topolab.b3.split.v1"] = "topolab.b3.split.v1"
    context: B3DataContext
    catalog: B3CaseCatalog

    @classmethod
    def from_context(cls, context: B3DataContext) -> "B3DatasetManifest":
        return cls(context=context, catalog=build_b3_case_catalog())

    def data_entries(self) -> tuple[B3CatalogEntry, ...]:
        return tuple(
            e
            for e in self.catalog.entries
            if e.role in ("train", "fit_validation", "screen_validation")
        )

    def sha256(self) -> str:
        return hashlib.sha256(canonical_metadata_bytes(self.model_dump(mode="json"))).hexdigest()


class B3UniformRecord(ContractModel):
    """Full-precision solver state, independent of the serialized float32 target."""

    model_config = ConfigDict(revalidate_instances="always")
    context: B3DataContext
    manifest_sha256: Sha256
    entry: B3CatalogEntry
    initialization: Literal["projected_float32_uniform"] = "projected_float32_uniform"
    result: TopologyResult

    @model_validator(mode="after")
    def validate_record(self) -> "B3UniformRecord":
        manifest = B3DatasetManifest.from_context(self.context)
        if self.manifest_sha256 != manifest.sha256():
            raise ValueError("record manifest identity does not match its context")
        if self.entry not in manifest.data_entries():
            raise ValueError("B3 cannot generate final or reassigned case artifacts")
        _validate_terminal_state(self.entry.case, self.result)
        count = int(np.prod(self.entry.case.problem.mesh.element_counts))
        dofs = 3 * int(np.prod(np.asarray(self.entry.case.problem.mesh.element_counts) + 1))
        vectors = (
            self.result.displacements,
            self.result.reactions,
            *(
                v
                for state in self.result.history
                for v in (state.design_density, state.physical_density)
            ),
        )
        if len(self.result.displacements) != dofs or len(self.result.reactions) != dofs:
            raise ValueError("full-precision displacement/reaction sizes differ from the mesh")
        if any(
            len(state.design_density) != count or len(state.physical_density) != count
            for state in self.result.history
        ):
            raise ValueError("full-precision history sizes differ from the mesh")
        if any(not np.all(np.isfinite(v)) for v in vectors):
            raise ValueError("full-precision record contains non-finite values")
        settings = self.entry.case.problem.optimization
        mesh = self.entry.case.problem.mesh
        # Reconstruct all filtered states without a FEM solve during schema parsing.
        from topolab.mesh import generate_structured_hex8
        from topolab.simp import apply_density_filter, build_density_filter

        density_filter = build_density_filter(
            generate_structured_hex8(*mesh.element_counts, lengths=mesh.lengths),
            settings.filter_radius,
        )
        previous = None
        physical_changes = []
        for position, state in enumerate(self.result.history, 1):
            if (
                state.iteration != position
                or not np.isfinite(state.compliance)
                or state.compliance <= 0
                or not np.isfinite(state.density_change)
                or state.density_change < 0
            ):
                raise ValueError("full-precision history metrics or order are invalid")
            design = np.asarray(state.design_density, dtype=np.float64)
            physical = np.asarray(state.physical_density, dtype=np.float64)
            if np.any(design < settings.minimum_density) or np.any(design > 1.0):
                raise ValueError("full-precision design exceeds density bounds")
            filtered = apply_density_filter(density_filter, design)
            if not np.array_equal(filtered, physical):
                raise ValueError("full-precision physical density differs from its filter")
            if not np.isclose(state.volume_fraction, np.mean(physical), rtol=0.0, atol=1e-12):
                raise ValueError("full-precision volume violates its state or quality boundary")
            if previous is not None:
                physical_changes.append(float(np.max(np.abs(physical - previous))))
            previous = physical
        last = self.result.history[-1]
        if abs(last.volume_fraction - settings.volume_fraction) > 0.005:
            raise ValueError("full-precision terminal volume violates quality")
        if last.density_change > settings.convergence_tolerance:
            if len(self.result.history) < 11:
                raise ValueError("physical-plateau record lacks its eleven-state witness")
            old = self.result.history[-11].compliance
            relative = (old - last.compliance) / old
            if (
                max(physical_changes[-10:]) > settings.convergence_tolerance
                or not 0.0 <= relative <= 2e-4
            ):
                raise ValueError("full-precision state fails the frozen physical-plateau stop")
        return self


class B3LabelRecord(B3UniformRecord):
    """New B3 terminal-design label with separately audited serialized-state metrics."""

    kind: Literal["label"] = "label"
    label_version: Literal["topolab.b3.label.v1"] = "topolab.b3.label.v1"
    stored: StoredDesignState

    @model_validator(mode="after")
    def validate_target(self) -> "B3LabelRecord":
        if self.entry.role not in ("train", "fit_validation"):
            raise ValueError("B3 labels require a train or fit-validation role")
        if self.stored.case != self.entry.case:
            raise ValueError("stored target and physical case differ")
        if self.stored.iterations != len(self.result.history):
            raise ValueError("stored iteration count differs from full-precision result")
        if self.stored.terminal_density_change != self.result.history[-1].density_change:
            raise ValueError("stored density change differs from full-precision result")
        expected = np.asarray(self.result.design_density, dtype=np.float32)
        if not np.array_equal(np.asarray(self.stored.design_density), expected.astype(np.float64)):
            raise ValueError("stored target differs from float32 terminal design")
        return self


class B3ReferenceRecord(B3UniformRecord):
    """Mandatory screen uniform reference, with no fitting-target payload."""

    kind: Literal["reference"] = "reference"
    reference_version: Literal["topolab.b3.uniform-reference.v1"] = (
        "topolab.b3.uniform-reference.v1"
    )

    @model_validator(mode="after")
    def validate_reference_role(self) -> "B3ReferenceRecord":
        if self.entry.role != "screen_validation":
            raise ValueError("B3 uniform references require the screening role")
        return self


type B3DataRecord = Annotated[B3LabelRecord | B3ReferenceRecord, Field(discriminator="kind")]


def generate_b3_record(
    manifest: B3DatasetManifest,
    entry: B3CatalogEntry,
    *,
    iteration_callback: IterationCallback | None = None,
) -> B3DataRecord:
    """Generate only an exact permitted entry, rejecting before solver execution."""

    manifest = B3DatasetManifest.model_validate(manifest.model_dump(mode="json"))
    verified = B3CatalogEntry.model_validate(entry.model_dump(mode="json"))
    if verified not in manifest.data_entries():
        raise PermissionError("case is outside the B3 label/reference population")
    result = solve_uniform_terminal(verified.case, iteration_callback=iteration_callback)
    if verified.role == "screen_validation":
        return B3ReferenceRecord(
            context=manifest.context,
            manifest_sha256=manifest.sha256(),
            entry=verified,
            result=result,
        )
    return B3LabelRecord(
        context=manifest.context,
        manifest_sha256=manifest.sha256(),
        entry=verified,
        result=result,
        stored=store_terminal_design(verified.case, result),
    )


def audit_b3_record(record: B3DataRecord) -> None:
    """Independently re-solve full-precision and serialized terminal states."""

    validate_refinement_quality(record.entry.case, record.result, None)
    if isinstance(record, B3LabelRecord):
        audit_stored_design(record.stored)
