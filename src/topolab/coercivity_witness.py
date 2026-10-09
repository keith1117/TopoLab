"""B4.37 diagnostic coercivity witnesses for ten fixed rational public systems.

No real FEM, factor construction, solver, loss/gradient, path IO or production.
"""

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

BUNDLE_VERSION = "topolab.b4_37.public-coercivity-bundle.v1"
BUNDLE_SHA256 = "b7d3d0566312d66f8c020116bc6ffd25e4e27c5e9671ee6d3a5ab928d28a89b6"
SOURCE_MAIN = "71b11bae7c450e46e5e79ed148d35a1e1b2be045"
ROLE = "public-coercivity-software"
SQRT_BITS = 80
FIXTURE_SHA256 = MappingProxyType(
    {
        "scalar-exact": "c7d67dfc94272759adc78ebeb1bbeeeb75b5941e6caf9f164fd9f41305982077",
        "scalar-intended-plus": "6aa057d51802ede389ad11497f3a894cb496a5a35a6ac5bcdc95efd7b449ce9a",
        "scalar-intended-minus": "84c4746a272894156f10c46c1304e81c81473aa5b265763ed544c8b718ddf215",
        "rectangular-singular-elements": (
            "bb38e572c618796a8347235c8f545f458e2e8cab333ade6479bae53794e81bea"
        ),
        "coupled-intended-error": (
            "9cf5f49969f22a45f0080f80066d86087a1204cccf3f14a1c77b1480cf941b62"
        ),
        "imperfect-left-inverse": (
            "4eee7889adabaa9ba26272e7804f08a553431b1af8a52b9ed0ee8ee950ccbbdb"
        ),
        "zero-witness": "72d1e9f7dc6dd019a1ac37e63b73ac4e16382990d2d11478feb6d860a2f0230c",
        "eta-boundary": "b2fbf57be826da9ffd1bd3e14ae230aa3aeee0cbe5972a89d3d25a569344f37d",
        "positive-but-conservative-stop": (
            "ae8513d3ba34259d9c3426a4964a0935403dd3bee4b5a49615b1c577e7f68dbb"
        ),
        "indefinite-element-stop": (
            "f0474cdf4213c20359f0bc4ffca8c010fc6ea183c943c92260b0d4f700978a9d"
        ),
    }
)
Matrix = tuple[tuple[Fraction, ...], ...]


class WitnessScopeError(ValueError):
    """Closed schema, identity, premise or arithmetic failure: stop."""


def _rational(raw: object) -> Fraction:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise WitnessScopeError("STOP_SCHEMA: finite rational string required")
    try:
        return Fraction(raw)
    except (ValueError, ZeroDivisionError) as exc:
        raise WitnessScopeError("STOP_SCHEMA: finite rational string required") from exc


def _matrix(raw: object) -> Matrix:
    if not isinstance(raw, list) or not 1 <= len(raw) <= 3:
        raise WitnessScopeError("STOP_SCHEMA: bounded rational matrix required")
    parsed = []
    for row in raw:
        if not isinstance(row, list) or not 1 <= len(row) <= 3:
            raise WitnessScopeError("STOP_SCHEMA: bounded rational row required")
        parsed.append(tuple(_rational(x) for x in row))
    return tuple(parsed)


def _psd(k: Matrix) -> bool:
    n = len(k)
    return (
        n in (1, 2)
        and all(len(row) == n for row in k)
        and all(k[i][j] == k[j][i] for i in range(n) for j in range(n))
        and all(k[i][i] >= 0 for i in range(n))
        and (n == 1 or k[0][0] * k[1][1] >= k[0][1] ** 2)
    )


@dataclass(frozen=True, slots=True)
class PublicWitness:
    fixture_id: str
    matrices: tuple[Matrix, ...]
    energy_factor: Matrix
    left_inverse_witness: Matrix
    free_space: str
    factor_space: str
    witness_space: str
    dirichlet: str
    operator_origin: str

    def payload(self) -> dict[str, object]:
        return {
            "id": self.fixture_id,
            "unit_matrices": [[[str(x) for x in row] for row in k] for k in self.matrices],
            "energy_factor": [[str(x) for x in row] for row in self.energy_factor],
            "left_inverse_witness": [[str(x) for x in row] for row in self.left_inverse_witness],
            "free_space": self.free_space,
            "factor_space": self.factor_space,
            "witness_space": self.witness_space,
            "dirichlet": self.dirichlet,
            "operator_origin": self.operator_origin,
        }


def _check_fixture(fixture: PublicWitness) -> None:
    if type(fixture.matrices) is not tuple or not 1 <= len(fixture.matrices) <= 3:
        raise WitnessScopeError("STOP_SCHEMA: immutable bounded intended elements required")
    for matrix in (*fixture.matrices, fixture.energy_factor, fixture.left_inverse_witness):
        if (
            type(matrix) is not tuple
            or not 1 <= len(matrix) <= 3
            or any(
                type(row) is not tuple
                or not 1 <= len(row) <= 3
                or any(type(x) is not Fraction for x in row)
                for row in matrix
            )
        ):
            raise WitnessScopeError("STOP_SCHEMA: immutable exact rational matrices required")
    m, n = len(fixture.energy_factor), len(fixture.energy_factor[0])
    if (
        n not in (1, 2)
        or m < n
        or any(len(row) != n for row in fixture.energy_factor)
        or len(fixture.left_inverse_witness) != n
        or any(len(row) != m for row in fixture.left_inverse_witness)
        or any(len(k) != n or any(len(row) != n for row in k) for k in fixture.matrices)
    ):
        raise WitnessScopeError("STOP_SCHEMA: SAME bounded dimensions required")
    if (
        fixture.fixture_id not in FIXTURE_SHA256
        or fixture.free_space != "public-free-space:" + fixture.fixture_id
        or fixture.factor_space != fixture.free_space
        or fixture.witness_space != fixture.free_space
        or fixture.dirichlet != "homogeneous-zero"
        or fixture.operator_origin != "authored-exact-rational-public-system"
    ):
        raise WitnessScopeError("STOP_BINDING: SAME intended public space required")
    canonical = (
        json.dumps(fixture.payload(), sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    if hashlib.sha256(canonical).hexdigest() != FIXTURE_SHA256[fixture.fixture_id]:
        raise WitnessScopeError("STOP_BINDING: changed public fixture")


def validate_public_fixture(raw: Mapping[str, object]) -> PublicWitness:
    if set(raw) != {
        "id",
        "unit_matrices",
        "energy_factor",
        "left_inverse_witness",
        "free_space",
        "factor_space",
        "witness_space",
        "dirichlet",
        "operator_origin",
    }:
        raise WitnessScopeError("STOP_SCHEMA: closed fixture schema required")
    strings = [
        raw[k]
        for k in (
            "id",
            "free_space",
            "factor_space",
            "witness_space",
            "dirichlet",
            "operator_origin",
        )
    ]
    if any(not isinstance(x, str) for x in strings):
        raise WitnessScopeError("STOP_SCHEMA: literal identities required")
    matrices = raw["unit_matrices"]
    if not isinstance(matrices, list) or not 1 <= len(matrices) <= 3:
        raise WitnessScopeError("STOP_SCHEMA: bounded intended elements required")
    # Explicit casts above give runtime validation; values are narrowed individually below.
    identifier, space, factor_space, witness_space, support, origin = strings
    assert isinstance(identifier, str) and isinstance(space, str)
    assert isinstance(factor_space, str) and isinstance(witness_space, str)
    assert isinstance(support, str) and isinstance(origin, str)
    result = PublicWitness(
        identifier,
        tuple(_matrix(k) for k in matrices),
        _matrix(raw["energy_factor"]),
        _matrix(raw["left_inverse_witness"]),
        space,
        factor_space,
        witness_space,
        support,
        origin,
    )
    _check_fixture(result)
    return result


def _closed_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise WitnessScopeError("STOP_SCHEMA: duplicate JSON field")
        result[key] = value
    return result


def read_public_fixture(binding: Mapping[str, str], reader: Callable[[], bytes]) -> PublicWitness:
    """Authorize only the literal frozen public bundle, denying before callback bytes."""
    if (
        set(binding) != {"version", "role", "fixture_id", "sha256", "source_main", "free_space"}
        or binding["version"] != BUNDLE_VERSION
        or binding["role"] != ROLE
        or binding["source_main"] != SOURCE_MAIN
        or binding["fixture_id"] not in FIXTURE_SHA256
        or binding["sha256"] != BUNDLE_SHA256
        or binding["free_space"] != "public-free-space:" + binding["fixture_id"]
    ):
        raise WitnessScopeError("DENY_BEFORE_BYTES: unregistered binding")
    raw = reader()
    if (
        not isinstance(raw, bytes)
        or len(raw) > 16384
        or hashlib.sha256(raw).hexdigest() != BUNDLE_SHA256
    ):
        raise WitnessScopeError("STOP_BINDING: public bytes do not match frozen digest")
    decoded = json.loads(raw, object_pairs_hook=_closed_object)
    if not isinstance(decoded, dict) or set(decoded) != {
        "version",
        "role",
        "source_main",
        "material",
        "fixtures",
    }:
        raise WitnessScopeError("STOP_SCHEMA: closed public bundle required")
    if (
        decoded["version"] != BUNDLE_VERSION
        or decoded["role"] != ROLE
        or decoded["source_main"] != SOURCE_MAIN
        or decoded["material"] != {"E_0": "1", "E_min": "1/1000", "p": 3}
    ):
        raise WitnessScopeError("STOP_BINDING: SAME material/source required")
    rows = decoded["fixtures"]
    if not isinstance(rows, list) or len(rows) != 10 or any(not isinstance(x, dict) for x in rows):
        raise WitnessScopeError("STOP_SCHEMA: ten complete public systems required")
    fixtures = [validate_public_fixture(row) for row in rows]
    if tuple(x.fixture_id for x in fixtures) != tuple(FIXTURE_SHA256):
        raise WitnessScopeError("STOP_BINDING: SAME complete ordered public panel required")
    return next(x for x in fixtures if x.fixture_id == binding["fixture_id"])


def _sqrt_enclosure(value: Fraction) -> tuple[Fraction, Fraction]:
    if type(value) is not Fraction or value < 0:
        raise WitnessScopeError("STOP_ERROR: nonnegative exact sqrt required")
    scale = 1 << SQRT_BITS
    floor = math.isqrt(value.numerator * scale**2 // value.denominator)
    low = Fraction(floor, scale)
    return low, low if low**2 == value else Fraction(floor + 1, scale)


def _outward(value: Fraction, *, upper: bool) -> float:
    if type(value) is not Fraction:
        raise WitnessScopeError("STOP_ERROR: exact endpoint required")
    try:
        result = float(value)
    except OverflowError as exc:
        raise WitnessScopeError("STOP_ERROR: binary64 overflow") from exc
    if not math.isfinite(result):
        raise WitnessScopeError("STOP_ERROR: finite binary64 required")
    represented = Fraction.from_float(result)
    if (upper and represented < value) or (not upper and represented > value):
        result = math.nextafter(result, math.inf if upper else -math.inf)
    if not math.isfinite(result):
        raise WitnessScopeError("STOP_ERROR: outward endpoint overflow")
    return result


@dataclass(frozen=True, slots=True)
class CoercivityBound:
    delta_plus: float
    eta_plus: float
    M_plus: float
    one_minus_eta_minus: float
    ratio_minus: float
    factor_lower_minus: float
    lower_G_minus: float
    E_min_minus: float
    m_global_minus: float
    public_intended_only: bool = True
    diagnostic_only: bool = True
    real_fem_certified: bool = False


def _lower_bound(delta: float, eta: float, norm: float, e_min: Fraction) -> CoercivityBound:
    if (
        any(type(x) is not float or not math.isfinite(x) or x < 0 for x in (delta, eta, norm))
        or type(e_min) is not Fraction
        or e_min <= 0
    ):
        raise WitnessScopeError(
            "STOP_ERROR: nonnegative finite norm bounds/positive material required"
        )
    if eta >= 1 or norm <= 0:
        raise WitnessScopeError("STOP_WITNESS: eta>=1 or M<=0")
    q = Fraction.from_float
    gap = _outward(1 - q(eta), upper=False)
    ratio = _outward(q(gap) / q(norm), upper=False)
    factor = _outward(q(ratio) ** 2, upper=False)
    lower = _outward(q(factor) - q(delta), upper=False)
    material = _outward(e_min, upper=False)
    if gap <= 0 or ratio <= 0 or lower <= 0 or material <= 0:
        raise WitnessScopeError("STOP_COERCIVITY: nonpositive directed lower bound")
    global_lower = _outward(q(material) * q(lower), upper=False)
    if global_lower <= 0:
        raise WitnessScopeError("STOP_COERCIVITY: nonpositive represented global lower bound")
    return CoercivityBound(delta, eta, norm, gap, ratio, factor, lower, material, global_lower)


def certify_public_witness(fixture: PublicWitness) -> CoercivityBound:
    """Enclose the one frozen factor/witness on SAME intended public elements."""
    _check_fixture(fixture)
    if any(not _psd(k) for k in fixture.matrices):
        raise WitnessScopeError("STOP_PSD: SAME intended symmetric element PSD not proved")
    a, y = fixture.energy_factor, fixture.left_inverse_witness
    m, n = len(a), len(y)
    delta_squared = Fraction()
    eta_squared = Fraction()
    for i in range(n):
        for j in range(n):
            intended = sum((k[i][j] for k in fixture.matrices), Fraction())
            factor = sum((a[r][i] * a[r][j] for r in range(m)), Fraction())
            left_product = sum((y[i][r] * a[r][j] for r in range(m)), Fraction())
            delta_squared += (intended - factor) ** 2
            eta_squared += (Fraction(int(i == j)) - left_product) ** 2
    norm_squared = sum((x**2 for row in y for x in row), Fraction())
    upper = [
        _outward(_sqrt_enclosure(x)[1], upper=True)
        for x in (delta_squared, eta_squared, norm_squared)
    ]
    return _lower_bound(upper[0], upper[1], upper[2], Fraction(1, 1000))
