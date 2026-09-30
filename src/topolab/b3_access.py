"""Consumer-specific B3 metadata and byte-read guards for later artifact adapters."""

import hashlib
from collections.abc import Callable, Iterable
from typing import Literal

from pydantic import model_validator

from topolab.b3_catalog import (
    B3CatalogEntry,
    B3TrainingSet,
    Sha256,
    build_b3_case_catalog,
    physical_fingerprint,
)
from topolab.experiment import ExperimentCase
from topolab.problem import ContractModel

type B3Consumer = Literal[
    "planning", "data_audit", "fitting", "screen", "nearest_neighbor", "final_query"
]
type B3ArtifactKind = Literal["label", "reference", "outcome"]


class B3ArtifactReference(ContractModel):
    """Verified reference metadata; the guard never discovers paths or opens files."""

    catalog_sha256: Literal["441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c"] = (
        "441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c"
    )
    exposure_sha256: Literal["5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7"] = (
        "5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7"
    )
    kind: B3ArtifactKind
    entry: B3CatalogEntry
    artifact_sha256: Sha256
    origins: tuple[ExperimentCase, ...]

    @model_validator(mode="after")
    def validate_origin(self) -> "B3ArtifactReference":
        expected = {e.case.case_id: e for e in build_b3_case_catalog().entries}
        if expected.get(self.entry.case.case_id) != self.entry:
            raise ValueError("artifact entry differs from its frozen catalog assignment")
        if not self.origins:
            raise ValueError("artifact must declare its physical case origin")
        origin_ids = tuple(origin.case_id for origin in self.origins)
        if origin_ids != tuple(sorted(set(origin_ids))):
            raise ValueError("artifact origins must be sorted and unique")
        for origin in self.origins:
            if physical_fingerprint(origin) != self.entry.physical_fingerprint:
                raise ValueError("derived artifact crosses a physical exposure boundary")
            if origin.case_id != self.entry.case.case_id:
                raise ValueError("historical or changed-budget artifacts are not B3 inputs")
        return self


class B3Access(ContractModel):
    """One frozen consumer scope; all metadata checks precede the supplied opener."""

    consumer: B3Consumer
    training_set: B3TrainingSet | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "B3Access":
        if (self.consumer == "fitting") != (self.training_set is not None):
            raise ValueError("only fitting requires a training_set")
        return self

    def case_entries(self) -> tuple[B3CatalogEntry, ...]:
        """Read permitted definitions; planning may inspect all preregistered cases."""

        entries = build_b3_case_catalog().entries
        if self.consumer == "planning":
            return entries
        return tuple(e for e in entries if self._permits_case(e))

    def _permits_case(self, entry: B3CatalogEntry) -> bool:
        if self.consumer == "data_audit":
            return entry.role in ("train", "fit_validation", "screen_validation")
        if self.consumer == "fitting":
            if entry.role == "train":
                return self.training_set in entry.training_sets
            if entry.role == "fit_validation":
                return self.training_set != "specialist" or (
                    entry.case.problem.loads[0].direction == "y"
                    and entry.case.problem.optimization.volume_fraction == 0.5951
                )
            return False
        if self.consumer == "nearest_neighbor":
            return entry.role == "train"
        if self.consumer == "screen":
            return entry.role == "screen_validation"
        if self.consumer == "final_query":
            return entry.role in ("final_id", "final_ood")
        return False

    def reference_metadata(self, reference: B3ArtifactReference) -> B3ArtifactReference:
        """Inspect a verified reference without obtaining artifact bytes."""

        # Reparse to reject model_copy/model_construct bypasses at the read boundary.
        verified = B3ArtifactReference.model_validate(reference.model_dump(mode="json"))
        if self.consumer != "planning" and not self._permits_case(verified.entry):
            raise PermissionError("artifact role or membership is forbidden for this consumer")
        return verified

    def _authorize_bytes(self, reference: B3ArtifactReference) -> B3ArtifactReference:
        verified = self.reference_metadata(reference)
        role, kind = verified.entry.role, verified.kind
        allowed = (
            self.consumer == "data_audit"
            and (
                (kind == "label" and role in ("train", "fit_validation"))
                or (kind == "reference" and role == "screen_validation")
            )
            or self.consumer in ("fitting", "nearest_neighbor")
            and kind == "label"
            or self.consumer in ("screen", "final_query")
            and kind == "outcome"
        )
        if not allowed:
            raise PermissionError("artifact bytes are forbidden for this consumer")
        return verified

    def read_artifact(
        self, reference: B3ArtifactReference, opener: Callable[[B3ArtifactReference], bytes]
    ) -> bytes:
        """Authorize before calling a storage adapter and verify its returned checksum."""

        verified = self._authorize_bytes(reference)
        if self.consumer == "nearest_neighbor":
            raise PermissionError("nearest_neighbor requires the complete train population")
        return self._read_verified(verified, opener)

    @staticmethod
    def _read_verified(
        verified: B3ArtifactReference, opener: Callable[[B3ArtifactReference], bytes]
    ) -> bytes:
        contents = opener(verified)
        if hashlib.sha256(contents).hexdigest() != verified.artifact_sha256:
            raise ValueError("artifact bytes do not match the reference checksum")
        return contents

    def read_population(
        self,
        references: Iterable[B3ArtifactReference],
        kind: B3ArtifactKind,
        opener: Callable[[B3ArtifactReference], bytes],
    ) -> tuple[bytes, ...]:
        """Require the complete permitted population before opening its first artifact."""

        references = tuple(self._authorize_bytes(ref) for ref in references)
        expected = {
            entry.case.case_id
            for entry in self.case_entries()
            if (kind == "label" and entry.role in ("train", "fit_validation"))
            or (kind == "reference" and entry.role == "screen_validation")
            or kind == "outcome"
        }
        actual = tuple(ref.entry.case.case_id for ref in references)
        if (
            not expected
            or any(ref.kind != kind for ref in references)
            or len(actual) != len(set(actual))
            or set(actual) != expected
        ):
            raise ValueError("artifact population must match every permitted case exactly")
        return tuple(
            self._read_verified(ref, opener)
            for ref in sorted(references, key=lambda r: r.entry.case.case_id)
        )
