"""B4.33 finite public-toy algebra. No production input, solve or integration."""

import hashlib
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import cast

BUNDLE_VERSION = "topolab.b4_33.public-toy-bundle.v1"
BUNDLE_SHA256 = "6b3efc8da6343461dda299206d26bdf47143cd1a110439d5eba7a8788a3acdd0"
ROLE = "public-toy-software"
STEPS = (1e-4, 2e-4)
FIXTURE_SHA256 = MappingProxyType(
    {
        "single-soften": "00ce9585a1931dcac0b7ca38d8875ffacb989e52556a46cd04cc9076f2275094",
        "single-stiffen": "e62b33f2bec736fad14077a39312bbe104cfcfd5f16c46d4ad3fa0af4693a49c",
        "parallel-two": "d432e669948c32db51b7e3be2f58a41fb87b13fd4ed4b9e5ae3453b82ed7c628",
        "series-two": "2547479d80bd55a17139625fa2fabd328ee036817e3bfc37ff5bedf2e11243e0",
        "coupled-two": "fbccca65b9434dfe5ffdeec2eef9ab05708f885181cc7de4004e6f5290c3abc5",
        "common-modulus-ratio": "40b5a35df5d6267fe24648a2ec1c617ba0ad5898216eecc7631a225be3d1ae3b",
        "zero-energy-element": "36dcd1717493428b697ddc1b143212d83d48c83ae2e23076414b2d63e365f5ed",
        "three-element-coupling": (
            "d9ccec9b9255dbe04db0301663fb100a0"
            "ed1e499afb1c9339e6e9e676daf7a61"
        ),
    }
)
Matrix = tuple[tuple[Fraction, ...], ...]


class SoftwareScopeError(ValueError):
    """Invalid, unbound or uncertified public software input; stop acceptance."""


def _vector(raw: object, limit: int) -> tuple[Fraction, ...]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= limit:
        raise SoftwareScopeError("bounded rational vector required")
    if any(not isinstance(x, str) or len(x) > 128 for x in raw):
        raise SoftwareScopeError("finite rational strings required")
    try:
        return tuple(Fraction(x) for x in raw)
    except (ValueError, ZeroDivisionError) as exc:
        raise SoftwareScopeError("finite rational strings required") from exc


@dataclass(frozen=True, slots=True)
class ToyFixture:
    fixture_id: str
    matrices: tuple[Matrix, ...]
    load: tuple[Fraction, ...]
    anchor_density: tuple[Fraction, ...]
    current_density: tuple[Fraction, ...]
    dirichlet: str = "homogeneous-zero"
    solid_modulus: Fraction = Fraction(1)
    minimum_modulus: Fraction = Fraction(1, 1000)
    penalty: int = 3
    normalizer_scale: Fraction = Fraction(11, 10)

    def payload(self) -> dict[str, object]:
        return {
            "id": self.fixture_id,
            "unit_matrices": [[[str(x) for x in row] for row in m] for m in self.matrices],
            "load": [str(x) for x in self.load],
            "anchor_density": [str(x) for x in self.anchor_density],
            "current_density": [str(x) for x in self.current_density],
            "dirichlet": self.dirichlet,
        }


def _modulus(fixture: ToyFixture, rho: Fraction) -> Fraction:
    return fixture.minimum_modulus + (fixture.solid_modulus - fixture.minimum_modulus) * rho**3


def _check_fixture(fixture: ToyFixture) -> Matrix:
    vectors = (fixture.load, fixture.anchor_density, fixture.current_density)
    if any(type(v) is not tuple or any(type(x) is not Fraction for x in v) for v in vectors):
        raise SoftwareScopeError("immutable exact rational vectors required")
    if (
        type(fixture.matrices) is not tuple
        or any(
            type(m) is not tuple
            or any(type(row) is not tuple or any(type(x) is not Fraction for x in row) for row in m)
            for m in fixture.matrices
        )
        or any(
            type(x) is not Fraction
            for x in (fixture.solid_modulus, fixture.minimum_modulus, fixture.normalizer_scale)
        )
        or type(fixture.penalty) is not int
    ):
        raise SoftwareScopeError("immutable exact rational material and matrices required")
    n, count = len(fixture.load), len(fixture.matrices)
    if not 1 <= n <= 2 or not 1 <= count <= 3 or not any(fixture.load):
        raise SoftwareScopeError("bounded free system and nonzero load required")
    if fixture.dirichlet != "homogeneous-zero":
        raise SoftwareScopeError("homogeneous zero Dirichlet required")
    if not 0 < fixture.minimum_modulus < fixture.solid_modulus:
        raise SoftwareScopeError("positive moduli required")
    if (fixture.solid_modulus, fixture.minimum_modulus, fixture.penalty) != (
        Fraction(1),
        Fraction(1, 1000),
        3,
    ):
        raise SoftwareScopeError("frozen material required")
    if fixture.normalizer_scale != Fraction(11, 10):
        raise SoftwareScopeError("frozen stored-normalizer scale required")
    for rho in (fixture.anchor_density, fixture.current_density):
        if len(rho) != count or any(not 0 < x <= 1 for x in rho):
            raise SoftwareScopeError("positive matching physical density required")
    for m in fixture.matrices:
        if len(m) != n or any(len(row) != n for row in m):
            raise SoftwareScopeError("matching element dimensions required")
        if any(m[i][j] != m[j][i] for i in range(n) for j in range(n)):
            raise SoftwareScopeError("symmetric elements required")
        if any(m[i][i] < 0 for i in range(n)) or (n == 2 and m[0][0] * m[1][1] < m[0][1] ** 2):
            raise SoftwareScopeError("positive semidefinite elements required")
    assembled = tuple(
        tuple(
            sum(
                (
                    _modulus(fixture, rho) * m[i][j]
                    for rho, m in zip(fixture.anchor_density, fixture.matrices, strict=True)
                ),
                Fraction(),
            )
            for j in range(n)
        )
        for i in range(n)
    )
    if assembled[0][0] <= 0 or (
        n == 2 and assembled[0][0] * assembled[1][1] <= assembled[0][1] ** 2
    ):
        raise SoftwareScopeError("assembled free SPD required")
    raw = (json.dumps(fixture.payload(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256.get(fixture.fixture_id):
        raise SoftwareScopeError("changed or unknown public fixture identity")
    return assembled


def validate_public_fixture(payload: Mapping[str, object]) -> ToyFixture:
    if set(payload) != {
        "id",
        "unit_matrices",
        "load",
        "anchor_density",
        "current_density",
        "dirichlet",
    }:
        raise SoftwareScopeError("closed fixture schema required")
    identifier, support = payload["id"], payload["dirichlet"]
    if not isinstance(identifier, str) or not isinstance(support, str):
        raise SoftwareScopeError("literal fixture identity and support required")
    load = _vector(payload["load"], 2)
    matrices = payload["unit_matrices"]
    if not isinstance(matrices, list) or not 1 <= len(matrices) <= 3:
        raise SoftwareScopeError("at most three element matrices required")
    parsed: list[Matrix] = []
    for matrix in matrices:
        if not isinstance(matrix, list) or len(matrix) != len(load):
            raise SoftwareScopeError("matching matrix dimensions required")
        parsed.append(tuple(_vector(row, len(load)) for row in matrix))
    fixture = ToyFixture(
        identifier,
        tuple(parsed),
        load,
        _vector(payload["anchor_density"], 3),
        _vector(payload["current_density"], 3),
        support,
    )
    _check_fixture(fixture)
    return fixture


def _closed_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SoftwareScopeError("duplicate JSON field")
        result[key] = value
    return result


def read_public_fixture(binding: Mapping[str, str], reader: Callable[[], bytes]) -> ToyFixture:
    """Allow only the literal authored public bundle; deny other roles before bytes."""
    if (
        set(binding) != {"version", "role", "fixture_id", "sha256"}
        or binding["version"] != BUNDLE_VERSION
        or binding["role"] != ROLE
        or binding["fixture_id"] not in FIXTURE_SHA256
        or binding["sha256"] != BUNDLE_SHA256
    ):
        raise SoftwareScopeError("unregistered role/schema/identity/hash; no byte access")
    raw = reader()
    if (
        not isinstance(raw, bytes)
        or len(raw) > 16384
        or hashlib.sha256(raw).hexdigest() != BUNDLE_SHA256
    ):
        raise SoftwareScopeError("public bundle bytes do not match frozen hash")
    decoded: object = json.loads(raw, object_pairs_hook=_closed_object)
    if not isinstance(decoded, dict) or set(decoded) != {
        "version",
        "role",
        "modulus",
        "normalizer_scale",
        "fixtures",
    }:
        raise SoftwareScopeError("closed public bundle schema required")
    bundle = cast(dict[str, object], decoded)
    if (
        bundle["version"] != BUNDLE_VERSION
        or bundle["role"] != ROLE
        or bundle["modulus"] != {"E_0": "1", "E_min": "1/1000", "p": 3}
        or bundle["normalizer_scale"] != "11/10"
    ):
        raise SoftwareScopeError("frozen public bundle material/normalizer required")
    rows = bundle["fixtures"]
    if not isinstance(rows, list) or len(rows) != 8 or any(not isinstance(x, dict) for x in rows):
        raise SoftwareScopeError("eight complete public fixtures required")
    fixtures = [validate_public_fixture(x) for x in rows]
    if tuple(x.fixture_id for x in fixtures) != tuple(FIXTURE_SHA256):
        raise SoftwareScopeError("complete ordered public fixture identities required")
    return next(x for x in fixtures if x.fixture_id == binding["fixture_id"])


@dataclass(frozen=True, slots=True)
class ToyReciprocalEnergy:
    """Immutable toy coefficients; floating outputs are not real-state bound certificates."""

    fixture: ToyFixture
    exact_displacement: tuple[Fraction, ...]
    stored_compliance: Fraction
    coefficients: tuple[Fraction, ...] = field(init=False)

    def __post_init__(self) -> None:
        assembled = _check_fixture(self.fixture)
        u, fixture = self.exact_displacement, self.fixture
        if (
            type(u) is not tuple
            or len(u) != len(fixture.load)
            or any(type(x) is not Fraction for x in u)
        ):
            raise SoftwareScopeError("exact rational displacement certificate required")
        if any(
            sum((k * x for k, x in zip(row, u, strict=True)), Fraction()) != force
            for row, force in zip(assembled, fixture.load, strict=True)
        ):
            raise SoftwareScopeError("UNCERTIFIED_STOP: exact equilibrium required")
        compliance = sum((f * x for f, x in zip(fixture.load, u, strict=True)), Fraction())
        if (
            type(self.stored_compliance) is not Fraction
            or self.stored_compliance <= 0
            or self.stored_compliance != fixture.normalizer_scale * compliance
        ):
            raise SoftwareScopeError("fixed positive stored-normalizer certificate required")
        coefficients = tuple(
            _modulus(fixture, rho) ** 2
            * sum((u[i] * m[i][j] * u[j] for i in range(len(u)) for j in range(len(u))), Fraction())
            for rho, m in zip(fixture.anchor_density, fixture.matrices, strict=True)
        )
        object.__setattr__(self, "coefficients", coefficients)

    def value_gradient(
        self, density: Sequence[float], *, normalized: bool = True
    ) -> tuple[float, tuple[float, ...]]:
        rho = tuple(float(x) for x in density)
        if len(rho) != len(self.coefficients) or any(
            not math.isfinite(x) or not 0 < x <= 1 for x in rho
        ):
            raise SoftwareScopeError("finite matching positive physical density required")
        current = tuple(float(x) for x in self.fixture.current_density)
        points = {current, tuple(float(x) for x in self.fixture.anchor_density)}
        for i in range(len(current)):
            for step in STEPS:
                for sign in (-1, 1):
                    changed = list(current)
                    changed[i] += sign * step
                    points.add(tuple(changed))
        if rho not in points:
            raise SoftwareScopeError("outside frozen public software point panel")
        moduli = tuple(0.001 + 0.999 * x**3 for x in rho)
        value = math.fsum(float(a) / e for a, e in zip(self.coefficients, moduli, strict=True))
        gradient = tuple(
            -float(a) * 3 * 0.999 * x**2 / e**2
            for a, x, e in zip(self.coefficients, rho, moduli, strict=True)
        )
        scale = float(self.stored_compliance) if normalized else 1.0
        return value / scale, tuple(x / scale for x in gradient)


def prepare_toy_anchor(
    fixture: ToyFixture, exact_displacement: Sequence[Fraction], stored_compliance: Fraction
) -> ToyReciprocalEnergy:
    return ToyReciprocalEnergy(fixture, tuple(exact_displacement), stored_compliance)
