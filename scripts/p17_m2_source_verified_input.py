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


def checked_acquisition_issuer(certificate, historical=None):
    """Recognize only opaque certificates from the registered live issuers."""
    historical = historical or sys.modules.get("p17_m2_source_acquisition_independent")
    if historical is not None and isinstance(certificate, historical.CheckedAcquisitionInput):
        return historical
    for suffix, identity in (
            ('_prospective_v27', 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v3'),
            ('_prospective_v31', 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v4'),
            ('_prospective_v33', 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v5')):
        prospective = sys.modules.get("p17_m2_source_acquisition_independent" + suffix)
        if (prospective is not None
                and Path(prospective.__file__).resolve() == Path(__file__).with_name(
                    'p17_m2_source_acquisition_independent.py').resolve()
                and prospective.REGISTERED_IDENTITY == identity
                and isinstance(certificate, prospective.CheckedAcquisitionInput)
                and certificate._binding.get('verified_plan', {}).get(
                    'execution_identity') == identity):
            return prospective
    return None


class VerifiedAcquisitionInput(buffer.VerifiedInput):
    """Use the existing same-buffer, short-read/tuple/hash/STOP reader unchanged."""

    def __init__(self, certificate, role, *, reader_lease=None):
        checker = checked_acquisition_issuer(certificate)
        if checker is None:
            raise ValueError("UNVERIFIED_SOURCE_CERTIFICATE")
        binding = certificate.binding_for(role, reader_lease=reader_lease)
        if binding["scope"] not in (checker.REHEARSAL_SCOPE, checker.FORMAL_SCOPE):
            raise ValueError("SOURCE_ACQUISITION_SCOPE_REQUIRED")
        self._initialize(certificate, role, reader_lease, binding)
