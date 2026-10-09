"""One B4.39 scalar QR construction for ten authored public systems only.

No path IO, actual FEM, production, loss/gradient change or witness search.
"""

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

BUNDLE_VERSION = "topolab.b4_39.public-fixed-construction-bundle.v1"
ROLE = "public-fixed-construction-software"
SOURCE_MAIN = "d576a9f1f2c5e5980353deb48951c35307acb126"
BUNDLE_SHA256 = "1d4e87fb13a7f96049cd3db53d824949c27f755210165329084728b5518246ad"
SQRT_BITS = 80
TRACE_LIMIT = 1024
FIXTURE_SHA256 = MappingProxyType(
    {
        "constructed-scalar": "113724b5d519b06a1f9a0a9abe8ded0448f69dde2f17a4d3eb9cf884e871496c",
        "constructed-third": "eaa94b89b3545ab4a873991b53d6e0afd279671a916dfebed05d1a45d47a5c8c",
        "constructed-tall-scalar": (
            "c2cb71df642bf6442628e5bf49d0b9ea7b122d6d2ad5a82dd21bafc8bfb212bf"
        ),
        "constructed-singular-elements": (
            "27c4bae1207afe7ca48f386519871bb4d39d19ffa19ca0cf7ce52d86d04b1ae5"
        ),
        "constructed-coupled": "7197367a89c14827c9470a6379c39d24cb1af8d03c07da98b06f271e24368009",
        "intended-stack-positive-error": (
            "4563f4e06cddac9cc1a4e5a43919da1d8700ec303ac602abb30a6451d97e8d2e"
        ),
        "intended-stack-negative-error": (
            "fc4e3e96d3d9b721c3fe10178b0462d364a6746726c46aeec975b11fa1ff2753"
        ),
        "rank-deficient-construction-stop": (
            "61e24cffdd3c94180edfaa5797fedb2a6154ff4e63c487ca8905a079301ba284"
        ),
        "positive-conservative-construction-stop": (
            "faf4cdfce20e14c4bc7d98fdca1f5e1f81d90e604e5f56a32eb8d41a4b3dd47e"
        ),
        "indefinite-element-construction-stop": (
            "f6226472f50fcd2c47194cec4f3f791543aabc9b50eecde36c01aa87d184e10f"
        ),
    }
)
RationalMatrix = tuple[tuple[Fraction, ...], ...]
FloatMatrix = tuple[tuple[float, ...], ...]


class ConstructionScopeError(ValueError):
    """A failed schema, identity or arithmetic premise stops this fixed construction."""


def _closed_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConstructionScopeError("STOP_SCHEMA: duplicate field")
        result[key] = value
    return result


def _rational(raw: object) -> Fraction:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise ConstructionScopeError("STOP_SCHEMA: bounded rational string required")
    try:
        return Fraction(raw)
    except (ValueError, ZeroDivisionError) as exc:
        raise ConstructionScopeError("STOP_SCHEMA: finite rational required") from exc


def _matrix(raw: object) -> RationalMatrix:
    if not isinstance(raw, list) or not 1 <= len(raw) <= 3:
        raise ConstructionScopeError("STOP_SCHEMA: bounded matrix required")
    result = []
    for row in raw:
        if not isinstance(row, list) or not 1 <= len(row) <= 2:
            raise ConstructionScopeError("STOP_SCHEMA: bounded row required")
        result.append(tuple(_rational(x) for x in row))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class PublicConstructionFixture:
    fixture_id: str
    matrices: tuple[RationalMatrix, ...]
    intended_stack: RationalMatrix
    free_space: str
    stack_space: str
    dirichlet: str
    operator_origin: str

    def payload(self) -> dict[str, object]:
        return {
            "id": self.fixture_id,
            "unit_matrices": [[[str(x) for x in row] for row in k] for k in self.matrices],
            "intended_stack": [[str(x) for x in row] for row in self.intended_stack],
            "free_space": self.free_space,
            "stack_space": self.stack_space,
            "dirichlet": self.dirichlet,
            "operator_origin": self.operator_origin,
        }


def _check_fixture(f: PublicConstructionFixture) -> None:
    if type(f.matrices) is not tuple or not 1 <= len(f.matrices) <= 3:
        raise ConstructionScopeError("STOP_SCHEMA: immutable bounded elements required")
    for matrix in (*f.matrices, f.intended_stack):
        if (
            type(matrix) is not tuple
            or not 1 <= len(matrix) <= 3
            or any(
                type(row) is not tuple
                or not 1 <= len(row) <= 2
                or any(type(x) is not Fraction for x in row)
                for row in matrix
            )
        ):
            raise ConstructionScopeError("STOP_SCHEMA: immutable rational matrices required")
    m, n = len(f.intended_stack), len(f.intended_stack[0])
    if (
        m < n
        or any(len(row) != n for row in f.intended_stack)
        or any(len(k) != n or any(len(row) != n for row in k) for k in f.matrices)
    ):
        raise ConstructionScopeError("STOP_SCHEMA: SAME bounded dimensions required")
    if (
        f.fixture_id not in FIXTURE_SHA256
        or f.free_space != "public-free-space:" + f.fixture_id
        or f.stack_space != f.free_space
        or f.dirichlet != "homogeneous-zero"
        or f.operator_origin != "authored-exact-rational-public-system"
    ):
        raise ConstructionScopeError("STOP_BINDING: SAME intended public space required")
    encoded = (json.dumps(f.payload(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(encoded).hexdigest() != FIXTURE_SHA256[f.fixture_id]:
        raise ConstructionScopeError("STOP_BINDING: changed public fixture")


def validate_public_fixture(raw: Mapping[str, object]) -> PublicConstructionFixture:
    if set(raw) != {
        "id",
        "unit_matrices",
        "intended_stack",
        "free_space",
        "stack_space",
        "dirichlet",
        "operator_origin",
    }:
        raise ConstructionScopeError("STOP_SCHEMA: closed fixture required")
    values = [raw[k] for k in ("id", "free_space", "stack_space", "dirichlet", "operator_origin")]
    if any(not isinstance(x, str) for x in values):
        raise ConstructionScopeError("STOP_SCHEMA: literal identities required")
    identifier, space, stack_space, support, origin = values
    assert isinstance(identifier, str) and isinstance(space, str)
    assert isinstance(stack_space, str) and isinstance(support, str) and isinstance(origin, str)
    elements = raw["unit_matrices"]
    if not isinstance(elements, list) or not 1 <= len(elements) <= 3:
        raise ConstructionScopeError("STOP_SCHEMA: bounded elements required")
    f = PublicConstructionFixture(
        identifier,
        tuple(_matrix(k) for k in elements),
        _matrix(raw["intended_stack"]),
        space,
        stack_space,
        support,
        origin,
    )
    _check_fixture(f)
    return f


def read_public_fixture(
    binding: Mapping[str, str],
    reader: Callable[[], bytes],
) -> PublicConstructionFixture:
    """Deny all unregistered bindings before reading the literal public bundle."""
    if (
        set(binding) != {"version", "role", "fixture_id", "sha256", "source_main", "free_space"}
        or binding["version"] != BUNDLE_VERSION
        or binding["role"] != ROLE
        or binding["source_main"] != SOURCE_MAIN
        or binding["fixture_id"] not in FIXTURE_SHA256
        or binding["sha256"] != BUNDLE_SHA256
        or binding["free_space"] != "public-free-space:" + binding["fixture_id"]
    ):
        raise ConstructionScopeError("DENY_BEFORE_BYTES: unregistered binding")
    raw = reader()
    if (
        type(raw) is not bytes
        or len(raw) > 16384
        or hashlib.sha256(raw).hexdigest() != BUNDLE_SHA256
    ):
        raise ConstructionScopeError("STOP_BINDING: changed public bytes")
    data = json.loads(raw, object_pairs_hook=_closed_object)
    if not isinstance(data, dict) or set(data) != {
        "version",
        "role",
        "source_main",
        "material",
        "fixtures",
    }:
        raise ConstructionScopeError("STOP_SCHEMA: closed public bundle required")
    if (
        data["version"] != BUNDLE_VERSION
        or data["role"] != ROLE
        or data["source_main"] != SOURCE_MAIN
        or data["material"] != {"E_0": "1", "E_min": "1/1000", "p": 3}
    ):
        raise ConstructionScopeError("STOP_BINDING: SAME material/source required")
    rows = data["fixtures"]
    if not isinstance(rows, list) or len(rows) != 10 or any(not isinstance(x, dict) for x in rows):
        raise ConstructionScopeError("STOP_SCHEMA: complete ten-system panel required")
    fixtures = [validate_public_fixture(row) for row in rows]
    if tuple(f.fixture_id for f in fixtures) != tuple(FIXTURE_SHA256):
        raise ConstructionScopeError("STOP_BINDING: SAME ordered panel required")
    return next(f for f in fixtures if f.fixture_id == binding["fixture_id"])


@dataclass(frozen=True, slots=True)
class Operation:
    op: str
    left: str
    right: str
    result: str


class _Recorder:
    def __init__(self) -> None:
        self.trace: list[Operation] = []

    def run(self, op: str, left: float | Fraction, right: float | None = None) -> float:
        if len(self.trace) >= TRACE_LIMIT:
            raise ConstructionScopeError("STOP_CONSTRUCTION: trace limit")
        lhs = str(left) if type(left) is Fraction else float(left).hex()
        rhs = "" if right is None else right.hex()
        try:
            x = float(left)
            if op == "round":
                value = x
            elif op == "sqrt":
                value = math.sqrt(x)
            elif op == "neg":
                value = -x
            elif op == "add" and right is not None:
                value = x + right
            elif op == "sub" and right is not None:
                value = x - right
            elif op == "mul" and right is not None:
                value = x * right
            elif op == "div" and right is not None:
                value = x / right
            else:
                raise ConstructionScopeError("STOP_CONSTRUCTION: unknown operation")
        except (OverflowError, ValueError, ZeroDivisionError) as exc:
            self.trace.append(Operation(op, lhs, rhs, "ERROR:" + type(exc).__name__))
            raise ConstructionScopeError("STOP_CONSTRUCTION: arithmetic exception") from exc
        self.trace.append(Operation(op, lhs, rhs, value.hex()))
        if not math.isfinite(value):
            raise ConstructionScopeError("STOP_CONSTRUCTION: nonfinite arithmetic")
        return value


def _fixed_qr(a: FloatMatrix, rec: _Recorder) -> tuple[FloatMatrix, FloatMatrix, FloatMatrix]:
    """The frozen ascending scalar reflectors, sign convention and backward substitution."""
    m, n = len(a), len(a[0])
    work = [list(row) for row in a]
    qt = [[float(i == j) for j in range(m)] for i in range(m)]
    op = rec.run
    for k in range(n):
        sigma = 0.0
        for i in range(k, m):
            sigma = op("add", sigma, op("mul", work[i][k], work[i][k]))
        norm = op("sqrt", sigma)
        if norm == 0:
            raise ConstructionScopeError("STOP_CONSTRUCTION: zero column norm")
        alpha = op("neg", math.copysign(norm, work[k][k]))
        v = [work[i][k] for i in range(k, m)]
        v[0] = op("sub", v[0], alpha)
        denominator = 0.0
        for x in v:
            denominator = op("add", denominator, op("mul", x, x))
        if denominator == 0:
            raise ConstructionScopeError("STOP_CONSTRUCTION: zero reflector denominator")
        beta = op("div", 2.0, denominator)
        for target, columns in ((work, range(k, n)), (qt, range(m))):
            for j in columns:
                dot = 0.0
                for i in range(k, m):
                    dot = op("add", dot, op("mul", v[i - k], target[i][j]))
                scale = op("mul", beta, dot)
                for i in range(k, m):
                    target[i][j] = op("sub", target[i][j], op("mul", v[i - k], scale))
    r = [[work[i][j] if j >= i else 0.0 for j in range(n)] for i in range(n)]
    qt = qt[:n]
    for i in range(n):
        if r[i][i] == 0:
            raise ConstructionScopeError("STOP_CONSTRUCTION: zero diagonal")
        if r[i][i] < 0:
            r[i] = [op("neg", x) for x in r[i]]
            qt[i] = [op("neg", x) for x in qt[i]]
    y = [[0.0] * m for _ in range(n)]
    for s in range(m):
        for i in reversed(range(n)):
            dot = 0.0
            for j in range(i + 1, n):
                dot = op("add", dot, op("mul", r[i][j], y[j][s]))
            y[i][s] = op("div", op("sub", qt[i][s], dot), r[i][i])
    return tuple(map(tuple, qt)), tuple(map(tuple, r)), tuple(map(tuple, y))


def _psd(k: RationalMatrix) -> bool:
    n = len(k)
    return (
        all(k[i][j] == k[j][i] for i in range(n) for j in range(n))
        and all(k[i][i] >= 0 for i in range(n))
        and (n == 1 or k[0][0] * k[1][1] >= k[0][1] ** 2)
    )


def _sqrt_enclosure(q: Fraction) -> tuple[Fraction, Fraction]:
    if type(q) is not Fraction or q < 0:
        raise ConstructionScopeError("STOP_ERROR: nonnegative exact sqrt required")
    grid = 1 << SQRT_BITS
    root = math.isqrt(q.numerator * grid * grid // q.denominator)
    low = Fraction(root, grid)
    return low, low if low * low == q else Fraction(root + 1, grid)


def _outward(q: Fraction, *, upper: bool) -> float:
    try:
        result = float(q)
    except OverflowError as exc:
        raise ConstructionScopeError("STOP_ERROR: binary64 overflow") from exc
    if not math.isfinite(result):
        raise ConstructionScopeError("STOP_ERROR: finite binary64 endpoint required")
    if (Fraction.from_float(result) < q) if upper else (Fraction.from_float(result) > q):
        result = math.nextafter(result, math.inf if upper else -math.inf)
    if not math.isfinite(result):
        raise ConstructionScopeError("STOP_ERROR: outward overflow")
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


def _lower_bound(delta: float, eta: float, norm: float) -> CoercivityBound:
    if any(type(x) is not float or not math.isfinite(x) or x < 0 for x in (delta, eta, norm)):
        raise ConstructionScopeError("STOP_ERROR: nonnegative finite bounds required")
    if eta >= 1 or norm <= 0:
        raise ConstructionScopeError("STOP_WITNESS: eta>=1 or M<=0")
    q = Fraction.from_float
    gap = _outward(1 - q(eta), upper=False)
    ratio = _outward(q(gap) / q(norm), upper=False)
    factor = _outward(q(ratio) ** 2, upper=False)
    lower = _outward(q(factor) - q(delta), upper=False)
    material = _outward(Fraction(1, 1000), upper=False)
    global_lower = _outward(q(material) * q(lower), upper=False)
    if min(gap, ratio, factor, lower, material, global_lower) <= 0:
        raise ConstructionScopeError("STOP_COERCIVITY: nonpositive directed lower bound")
    return CoercivityBound(delta, eta, norm, gap, ratio, factor, lower, material, global_lower)


def _norm_squares(f: PublicConstructionFixture, a: FloatMatrix, y: FloatMatrix) -> dict[str, str]:
    n, m = len(y), len(a)
    names = ("intended_to_stack", "stack_to_represented", "complete_operator", "left_residual")
    totals = {name: Fraction() for name in names}
    for i in range(n):
        for j in range(n):
            g = sum((k[i][j] for k in f.matrices), Fraction())
            g0 = sum((row[i] * row[j] for row in f.intended_stack), Fraction())
            ga = sum((Fraction(row[i]) * Fraction(row[j]) for row in a), Fraction())
            ya = sum((Fraction(y[i][r]) * Fraction(a[r][j]) for r in range(m)), Fraction())
            for name, entry in zip(
                names, (g - g0, g0 - ga, g - ga, Fraction(i == j) - ya), strict=True
            ):
                totals[name] += entry**2
    totals["witness"] = sum((Fraction(x) ** 2 for row in y for x in row), Fraction())
    return {name: str(value) for name, value in totals.items()}


@dataclass(frozen=True, slots=True)
class ConstructionEvidence:
    fixture_id: str
    status: str
    A_hat: FloatMatrix | None
    Q_transpose_hat: FloatMatrix | None
    R_hat: FloatMatrix | None
    Y_hat: FloatMatrix | None
    trace: tuple[Operation, ...]
    error_squares: tuple[tuple[str, str], ...] | None
    certificate: CoercivityBound | None
    error: str | None


def construct_public_witness(fixture: PublicConstructionFixture) -> ConstructionEvidence:
    """Construct once, certify SAME intended public G, or retain an explicit stop."""
    _check_fixture(fixture)
    rec = _Recorder()
    a = qt = r = y = None
    squares = None
    bound = None
    error = None
    status = "PASS"
    try:
        if any(not _psd(k) for k in fixture.matrices):
            raise ConstructionScopeError("STOP_PSD: intended element PSD not proved")
        a = tuple(tuple(rec.run("round", x) for x in row) for row in fixture.intended_stack)
        qt, r, y = _fixed_qr(a, rec)
        values = _norm_squares(fixture, a, y)
        squares = tuple(values.items())
        upper = [
            _outward(_sqrt_enclosure(Fraction(values[k]))[1], upper=True)
            for k in ("complete_operator", "left_residual", "witness")
        ]
        bound = _lower_bound(*upper)
    except ConstructionScopeError as exc:
        error = str(exc)
        status = error.split(":", 1)[0]
    return ConstructionEvidence(
        fixture.fixture_id, status, a, qt, r, y, tuple(rec.trace), squares, bound, error
    )
