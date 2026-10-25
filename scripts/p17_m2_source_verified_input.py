"""S1 accepts only independently audited NEW source-acquisition capabilities."""

import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "source_acquisition_verified_buffer", Path(__file__).with_name("p17_m2_verified_input.py")
)
assert spec and spec.loader
buffer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(buffer)


class VerifiedAcquisitionInput(buffer.VerifiedInput):
    """Use the existing same-buffer, short-read/tuple/hash/STOP reader unchanged."""

    def __init__(self, certificate, role, *, reader_lease=None):
        checker = sys.modules.get("p17_m2_source_acquisition_independent")
        if checker is None or not isinstance(certificate, checker.CheckedAcquisitionInput):
            raise ValueError("UNVERIFIED_SOURCE_CERTIFICATE")
        binding = certificate.binding_for(role, reader_lease=reader_lease)
        if binding["scope"] not in (checker.REHEARSAL_SCOPE, checker.FORMAL_SCOPE):
            raise ValueError("SOURCE_ACQUISITION_SCOPE_REQUIRED")
        self._initialize(certificate, role, reader_lease, binding)
