"""S1: a checked public certificate and held reader lease feed one verified buffer.

The existing bounded reader retains short-read/tuple/hash failures. This seam
never discovers sources, accepts serialized PASS, reopens a decoder's path, or
activates a formal/scientific role.
"""

import importlib.util
import os
import stat
import sys
from collections.abc import Mapping
from pathlib import Path


def plain(value):
    if isinstance(value, Mapping):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [plain(item) for item in value]
    return value


class VerifiedInput:
    """Consume each role-whitelisted member once, only while its actual lease holds."""

    def __init__(self, certificate, role, *, reader_lease=None):
        checker = sys.modules.get("p17_m2_content_verified_independent")
        if checker is None or not isinstance(certificate, checker.CheckedPublicInput):
            raise ValueError("UNVERIFIED_CERTIFICATE")
        self.certificate, self.role, self.lease = certificate, role, reader_lease
        self.binding = certificate.binding_for(role, reader_lease=reader_lease)
        if self.binding["scope"] != "PUBLIC_SOFTWARE_FIXTURE_ONLY":
            raise ValueError("PUBLIC_SCOPE_REQUIRED")
        spec = importlib.util.spec_from_file_location(
            "verified_buffer_source_helper", Path(__file__).with_name("p17_m2_input_export.py")
        )
        assert spec and spec.loader
        self.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helper)

        # The old helper's algorithm/identity is disclosed, never relabelled as an actor.
        class PrivateReader(self.helper.Reader):
            def _identity(self, stage, value):
                super()._identity(stage, value)
                if not (
                    stat.S_ISREG(value.st_mode)
                    and value.st_uid == os.geteuid()
                    and value.st_nlink == 1
                    and stat.S_IMODE(value.st_mode) == 0o600
                ):
                    raise ValueError("PRIVATE_SINGLE_LINK_MEMBER_REQUIRED")

        self.reader = PrivateReader(
            Path(self.binding["root"]),
            execution_identity=self.helper.LOCAL_IDENTITY,
            source_identity_checks=True,
        )
        self.members = {m["path"]: m for m in self.binding["manifest"]["members"]}
        self.identities = {r["path"]: r for r in self.binding["local_identity_rows"]}
        self.stopped = False
        self.failure = None

    def consume(self, member, decoder):
        if self.stopped:
            raise ValueError("STOP_NO_RETRY")
        try:
            self.certificate.binding_for(self.role, reader_lease=self.lease)
            if member not in self.binding["role_views"][self.role]:
                raise ValueError("ROLE_VIEW_DENIED")
            row = self.members[member]
            caps = {
                "checkpoint": (1048576, 12 * 1048576),
                "models": (1048576, 1048576),
                "nn-producer": (128 * 1024, 32 * 1048576),
                "nn-audit": (2 * 1048576, 256 * 1048576),
                "uniform-scalars": (65536, 65536),
            }
            each, total = caps[row["type"]]
            raw = self.reader.read(
                member,
                each,
                expected=row["sha256"],
                size=row["byte_size"],
                group=row["type"],
                total=total,
            )
            with self.reader.validation(member, "consumer_frozen_identity"):
                if self.reader.source_observations[-1] != plain(self.identities[member]):
                    raise ValueError("FROZEN_LOCAL_IDENTITY_CHANGED")
            with self.reader.validation(member, "consumer_decode_same_buffer"):
                self.certificate.binding_for(self.role, reader_lease=self.lease)
                value = decoder(raw)
                self.certificate.binding_for(self.role, reader_lease=self.lease)
                return value
        except Exception as error:
            self.stopped = True
            secondary = []
            try:
                self.certificate.stop_reader(self.role, reader_lease=self.lease)
            except Exception as recording_error:
                secondary.append(
                    {
                        "stage": "capability stop",
                        "type": type(recording_error).__name__,
                        "reason": str(recording_error),
                    }
                )
            self.failure = {
                "status": "STOP_NO_RETRY",
                "member": member,
                "error_type": type(error).__name__,
                "reason": str(error),
                "source_failures": self.reader.failures,
                "source_identities": self.reader.source_observations,
                "source_facts": self.reader.source_facts,
                "expected_identity": plain(self.identities.get(member)),
                "secondary_failures": secondary,
            }
            raise
