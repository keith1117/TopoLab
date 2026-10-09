"""B4.35 diagnostic enclosures for eight authored rational toys only.

No real FEM, solve, loss/gradient, path access or production certificate.
"""

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

BUNDLE_VERSION = "topolab.b4_35.public-certificate-bundle.v1"
BUNDLE_SHA256 = "9b16325b155f918b3537162f606121fd074b9729ebd4011b624fafc923f76a36"
SOURCE_MAIN = "e2ebb5121f28df4f9df0f3295e390c042b146785"
ROLE = "public-certificate-software"
SQRT_BITS = 80
FIXTURE_SHA256 = MappingProxyType(
    {
        "single-exact": "afa991416e9c8e9aa4c270e7449f08dac13e7c893144b20cbfd3994b834482a4",
        "single-tiny-residual": "16b2c334a44a002f171adc49441358715790c3e7b82a936ee2e18e8abf8ce14a",
        "single-overbalanced": "4686b5095a7d493ce04fca27b3b6467cc1d0b9f6961a0d4508e88712afa4f1e9",
        "coupled-singular-elements": (
            "16daac62a9c3c96d21c944bf74c5bf99d28ee03619887bc3bce5b2e8d1619f21"
        ),
        "zero-energy-element": "8837380accc2fca19210ee18525b603fa236a3bb2341f6fdc92210c314263712",
        "three-element-coupling": (
            "8b227370640fec1172c3aa854a8ae927ff"
            "e472b5d2893be27afcc6f2e9412d2a"
        ),
        "ill-conditioned-positive": (
            "31e46911be82a9262bdecb774da6a15efbfc746e25f3740efaaa72d7a6acaaca"
        ),
        "nonbinary-rational-operator": (
            "e1dd9d42036c3457de59db24d0b8ff26abaf7537950b8bd9b719433755549be6"
        ),
    }
)
Matrix = tuple[tuple[Fraction, ...], ...]
Vector = tuple[Fraction, ...]


class CertificateScopeError(ValueError):
    """Unknown, unbound or uncertified toy: stop dependent acceptance."""


def _rational(raw: object) -> Fraction:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise CertificateScopeError("finite rational string required")
    try:
        return Fraction(raw)
    except (ValueError, ZeroDivisionError) as exc:
        raise CertificateScopeError("finite rational string required") from exc


def _vector(raw: object, limit: int) -> Vector:
    if not isinstance(raw, list) or not 1 <= len(raw) <= limit:
        raise CertificateScopeError("bounded rational vector required")
    return tuple(_rational(x) for x in raw)


def _psd(matrix: Matrix) -> bool:
    n = len(matrix)
    if n not in (1, 2) or any(len(row) != n for row in matrix):
        return False
    if any(matrix[i][j] != matrix[j][i] for i in range(n) for j in range(n)):
        return False
    return all(matrix[i][i] >= 0 for i in range(n)) and (
        n == 1 or matrix[0][0] * matrix[1][1] >= matrix[0][1] ** 2
    )


@dataclass(frozen=True, slots=True)
class PublicFixture:
    fixture_id: str
    matrices: tuple[Matrix, ...]
    load: Vector
    anchor_density: Vector
    current_density: Vector
    displacement: Vector
    lower_G: Fraction
    stored_normalizer: Fraction
    dirichlet: str

    def payload(self) -> dict[str, object]:
        return {
            "id": self.fixture_id,
            "unit_matrices": [[[str(x) for x in row] for row in k] for k in self.matrices],
            "load": [str(x) for x in self.load],
            "anchor_density": [str(x) for x in self.anchor_density],
            "current_density": [str(x) for x in self.current_density],
            "approximate_displacement": [str(x) for x in self.displacement],
            "lower_G": str(self.lower_G),
            "stored_normalizer": str(self.stored_normalizer),
            "dirichlet": self.dirichlet,
        }


def _check_fixture(fixture: PublicFixture) -> None:
    vectors = (fixture.load, fixture.anchor_density, fixture.current_density, fixture.displacement)
    if any(type(v) is not tuple or any(type(x) is not Fraction for x in v) for v in vectors):
        raise CertificateScopeError("immutable exact rational vectors required")
    if (
        type(fixture.matrices) is not tuple
        or any(
            type(k) is not tuple
            or any(type(row) is not tuple or any(type(x) is not Fraction for x in row) for row in k)
            for k in fixture.matrices
        )
        or type(fixture.lower_G) is not Fraction
        or type(fixture.stored_normalizer) is not Fraction
    ):
        raise CertificateScopeError("immutable exact operators and scalars required")
    n, count = len(fixture.load), len(fixture.matrices)
    if n not in (1, 2) or not 1 <= count <= 3 or not any(fixture.load):
        raise CertificateScopeError("bounded free system with nonzero load required")
    if len(fixture.displacement) != n or fixture.dirichlet != "homogeneous-zero":
        raise CertificateScopeError("same dimensions and homogeneous zero Dirichlet required")
    for density in (fixture.anchor_density, fixture.current_density):
        if len(density) != count or any(not 0 < x <= 1 for x in density):
            raise CertificateScopeError("same positive physical density required")
    if any(len(k) != n or not _psd(k) for k in fixture.matrices):
        raise CertificateScopeError("same intended symmetric PSD elements required")
    if fixture.lower_G <= 0 or fixture.stored_normalizer <= 0:
        raise CertificateScopeError("positive prescribed lower_G and SAME normalizer required")
    shifted = tuple(
        tuple(
            sum((k[i][j] for k in fixture.matrices), Fraction())
            - (fixture.lower_G if i == j else Fraction())
            for j in range(n)
        )
        for i in range(n)
    )
    if not _psd(shifted):
        raise CertificateScopeError("prescribed G-lower_G*I is not certified PSD")
    raw = (json.dumps(fixture.payload(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256.get(fixture.fixture_id):
        raise CertificateScopeError("unknown or changed public fixture identity")


def validate_public_fixture(raw: Mapping[str, object]) -> PublicFixture:
    if set(raw) != {
        "id",
        "unit_matrices",
        "load",
        "anchor_density",
        "current_density",
        "approximate_displacement",
        "lower_G",
        "stored_normalizer",
        "dirichlet",
    }:
        raise CertificateScopeError("closed fixture schema required")
    identifier, support = raw["id"], raw["dirichlet"]
    if not isinstance(identifier, str) or not isinstance(support, str):
        raise CertificateScopeError("literal identity and support required")
    load = _vector(raw["load"], 2)
    matrices = raw["unit_matrices"]
    if not isinstance(matrices, list) or not 1 <= len(matrices) <= 3:
        raise CertificateScopeError("bounded intended elements required")
    parsed: list[Matrix] = []
    for matrix in matrices:
        if not isinstance(matrix, list) or len(matrix) != len(load):
            raise CertificateScopeError("same operator dimensions required")
        parsed.append(tuple(_vector(row, len(load)) for row in matrix))
    result = PublicFixture(
        identifier,
        tuple(parsed),
        load,
        _vector(raw["anchor_density"], 3),
        _vector(raw["current_density"], 3),
        _vector(raw["approximate_displacement"], 2),
        _rational(raw["lower_G"]),
        _rational(raw["stored_normalizer"]),
        support,
    )
    _check_fixture(result)
    return result


def _closed_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateScopeError("duplicate JSON field")
        result[key] = value
    return result


def read_public_fixture(binding: Mapping[str, str], reader: Callable[[], bytes]) -> PublicFixture:
    """Grant only frozen public bytes after exact source/role/schema/ID/hash checks."""
    if (
        set(binding) != {"version", "role", "fixture_id", "sha256", "source_main"}
        or binding["version"] != BUNDLE_VERSION
        or binding["role"] != ROLE
        or binding["source_main"] != SOURCE_MAIN
        or binding["fixture_id"] not in FIXTURE_SHA256
        or binding["sha256"] != BUNDLE_SHA256
    ):
        raise CertificateScopeError("DENY_BEFORE_BYTES: unregistered binding")
    raw = reader()
    if (
        not isinstance(raw, bytes)
        or len(raw) > 16384
        or hashlib.sha256(raw).hexdigest() != BUNDLE_SHA256
    ):
        raise CertificateScopeError("public bytes do not match frozen digest")
    decoded = json.loads(raw, object_pairs_hook=_closed_object)
    if not isinstance(decoded, dict) or set(decoded) != {
        "version",
        "role",
        "source_main",
        "material",
        "fixtures",
    }:
        raise CertificateScopeError("closed public bundle required")
    if (
        decoded["version"] != BUNDLE_VERSION
        or decoded["role"] != ROLE
        or decoded["source_main"] != SOURCE_MAIN
        or decoded["material"] != {"E_0": "1", "E_min": "1/1000", "p": 3}
    ):
        raise CertificateScopeError("same public material/source required")
    rows = decoded["fixtures"]
    if not isinstance(rows, list) or len(rows) != 8 or any(not isinstance(x, dict) for x in rows):
        raise CertificateScopeError("eight complete public systems required")
    fixtures = [validate_public_fixture(x) for x in rows]
    if tuple(x.fixture_id for x in fixtures) != tuple(FIXTURE_SHA256):
        raise CertificateScopeError("same complete ordered fixture population required")
    return next(x for x in fixtures if x.fixture_id == binding["fixture_id"])


def _sqrt_enclosure(value: Fraction) -> tuple[Fraction, Fraction]:
    if type(value) is not Fraction or value < 0:
        raise CertificateScopeError("nonnegative exact sqrt input required")
    scale = 1 << SQRT_BITS
    floor = math.isqrt(value.numerator * scale**2 // value.denominator)
    low = Fraction(floor, scale)
    high = low if low**2 == value else Fraction(floor + 1, scale)
    return low, high


def _outward(value: Fraction, *, upper: bool) -> float:
    if type(value) is not Fraction:
        raise CertificateScopeError("exact endpoint required")
    try:
        result = float(value)
    except OverflowError as exc:
        raise CertificateScopeError("binary64 endpoint overflow") from exc
    if not math.isfinite(result):
        raise CertificateScopeError("finite binary64 endpoint required")
    represented = Fraction.from_float(result)
    if (upper and represented < value) or (not upper and represented > value):
        result = math.nextafter(result, math.inf if upper else -math.inf)
    if not math.isfinite(result):
        raise CertificateScopeError("outward endpoint overflow")
    return result


@dataclass(frozen=True, slots=True)
class DiagnosticBound:
    U_plus: float
    r_plus: float
    m_minus: float
    C_s_minus: float
    sqrt_U_up: float
    sqrt_m_down: float
    residual_division_up: float
    B_plus: float
    normalized_B_plus: float
    residual_is_exact_zero: bool
    unmodified_U_certified: bool
    diagnostic_only: bool = True


def _bound(
    upper: Fraction, residual_squared: Fraction, coercivity: Fraction, stored: Fraction
) -> DiagnosticBound:
    if upper < 0 or residual_squared < 0 or coercivity <= 0 or stored <= 0:
        raise CertificateScopeError("nonnegative energies and positive lower bounds required")
    u_plus = _outward(upper, upper=True)
    r_plus = _outward(_sqrt_enclosure(residual_squared)[1], upper=True)
    m_minus, c_minus = _outward(coercivity, upper=False), _outward(stored, upper=False)
    if m_minus <= 0 or c_minus <= 0:
        raise CertificateScopeError("positive represented lower bounds required")
    su = _outward(_sqrt_enclosure(Fraction.from_float(u_plus))[1], upper=True)
    sm = _outward(_sqrt_enclosure(Fraction.from_float(m_minus))[0], upper=False)
    if sm <= 0:
        raise CertificateScopeError("fixed-grid sqrt lower bound is zero; STOP")
    ratio = _outward(Fraction.from_float(r_plus) / Fraction.from_float(sm), upper=True)
    square = (Fraction.from_float(su) + Fraction.from_float(ratio)) ** 2
    bound = _outward(square, upper=True)
    normalized = _outward(Fraction.from_float(bound) / Fraction.from_float(c_minus), upper=True)
    zero = residual_squared == 0
    return DiagnosticBound(
        u_plus, r_plus, m_minus, c_minus, su, sm, ratio, bound, normalized, zero, zero
    )


def certify_public_point(fixture: PublicFixture, density: Vector) -> DiagnosticBound:
    """Revalidate unchanged toy identity and enclose only its two fixed points."""
    _check_fixture(fixture)
    if type(density) is not tuple or any(type(x) is not Fraction for x in density):
        raise CertificateScopeError("fixed exact rational point required")
    if density not in (fixture.anchor_density, fixture.current_density):
        raise CertificateScopeError("outside finite anchor/current panel")
    moduli = tuple(Fraction(1, 1000) + Fraction(999, 1000) * x**3 for x in density)
    anchor_moduli = tuple(
        Fraction(1, 1000) + Fraction(999, 1000) * x**3 for x in fixture.anchor_density
    )
    u, n = fixture.displacement, len(fixture.load)
    energies = tuple(
        sum((u[i] * k[i][j] * u[j] for i in range(n) for j in range(n)), Fraction())
        for k in fixture.matrices
    )
    upper = sum(
        (old**2 * q / new for old, q, new in zip(anchor_moduli, energies, moduli, strict=True)),
        Fraction(),
    )
    residual = tuple(
        sum(
            (
                old * k[i][j] * u[j]
                for old, k in zip(anchor_moduli, fixture.matrices, strict=True)
                for j in range(n)
            ),
            Fraction(),
        )
        - fixture.load[i]
        for i in range(n)
    )
    return _bound(
        upper,
        sum((x**2 for x in residual), Fraction()),
        Fraction(1, 1000) * fixture.lower_G,
        fixture.stored_normalizer,
    )
