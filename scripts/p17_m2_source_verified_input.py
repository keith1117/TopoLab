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


B1_IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.receipt-20261126-b1.v1"
B1_ISSUER_MODULE = "p17_m2_source_acquisition_independent_receipt_formal_20261126_b1"
B1_PLAN = "d26d69bb62ff1488e12a52f2872f07ce00eac92eb4bd30413b53925411d4f739"
B1_VERSION = "94e1ccdd7629cfbb697797da4235351c1fdefbcde8c40085dd0876ab3b6b23a7"


def historical_b1_issuer(certificate):
    """Only the local replay of the sealed B1 returns can attest a historical object."""
    history = sys.modules.get("scientific_b1_history")
    check = getattr(history, "historical_issuer", None)
    expected = Path(__file__).with_name("scientific_b1_history.py").resolve()
    if (history is None or getattr(history, "__file__", None) is None
            or Path(history.__file__).resolve() != expected
            or getattr(check, "__globals__", None) is not vars(history)
            or getattr(check, "__code__", None) is None
            or Path(check.__code__.co_filename).resolve() != expected):
        return None
    return check(certificate)


def checked_acquisition_issuer(certificate, historical=None):
    """Recognize only opaque certificates from the registered live issuers."""
    if type(certificate).__module__ == B1_ISSUER_MODULE:
        return historical_b1_issuer(certificate)
    historical = historical or sys.modules.get("p17_m2_source_acquisition_independent")
    if historical is not None and isinstance(certificate, historical.CheckedAcquisitionInput):
        return historical
    for suffix, identity in (
            ('_staged_20261121',
             'topolab.v2.p17-m2-registered-source-acquisition.staged-20261121.v1'),
            ('_nov21', 'topolab.v2.p17-m2-registered-source-acquisition.20261121.v1'),
            ('_full60_20261116', 'topolab.v2.p17-m2-registered-source-acquisition.20261116.v1'),
            ('_prospective_v27', 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v3'),
            ('_prospective_v31', 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v4'),
            ('_prospective_v33', 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v5'),
            ('_prospective_v35', 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v6')):
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
