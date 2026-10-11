"""B4.41 intended-versus-represented enclosures for twelve authored public DAGs.

No path IO, FEM, PSD/coercivity certification, witness construction or integration.
"""

import hashlib
import json
import math
import re
import struct
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

BUNDLE_VERSION = "topolab.b4_41.public-intended-representation-bundle.v1"
ROLE = "public-intended-representation-software"
SOURCE_MAIN = "b4a1ed231abafadcdea46876a15d25e47e607b30"
BUNDLE_SHA256 = "f6f770bd282f8bdfc1ef93b9b1fe8ea38a06a13c9d1499dc8266e591e4b4ffe5"
SQRT_BITS = 80
MIN_NORMAL = float.fromhex("0x1p-1022")
FIXTURE_SHA256 = MappingProxyType(
    {
        "exact-dyadic": "83b9fe55e40e01d480a9698e8eb896dce3e15ac5b139935f827e80b83ad01661",
        "accepted-bit-division": "42ae28e927b7c5853b5fd2195caf81120581c66a833d2ea2f0447d424721cd76",
        "irrational-sqrt-two": "73083c1ca9cfacf62f3ca9257fe303e96e2312e1aca4f89a929bd8980ec31cce",
        "inverse-sqrt-three": "b34f383ba8c65444fe11056d038546d387c90a614d71b0a58b2967a87ba81706",
        "coupled-irrational": "4f362cc76b9b8b34366d897548629ff9d4285ba81e37d251bcce3761f292971c",
        "positive-structural-error": (
            "754f4007b3f3816c5b2b8e2b3f5ee8a8b29d14fbcfa5dc58e613805bd922456f"
        ),
        "negative-structural-error": (
            "59198ca1916278891d0329687ebf63973fe3c5fafc81203a836cbc7374fd197d"
        ),
        "rounded-cancellation-retained": (
            "3da78ffa0108859b6616d44eccf242c4d9e4d154c1d2439f4f8793a197efbc0a"
        ),
        "inconclusive-radicand-stop": (
            "5ffe43afec0c8a0b6609dbf75ad16f77e0d3d6fc1030c233d29bdd0ec2d7c9e2"
        ),
        "inconclusive-denominator-stop": (
            "ce6eb16db340b194fbbe5c075183693facf74ee764dcb7f4aca492b9c5c45cff"
        ),
        "binary64-overflow-stop": (
            "45f1d8ae8ad0b6cfb527949e012217a2ea3f7719329e80d5716fff6acd8f772e"
        ),
        "binary64-underflow-stop": (
            "7919773ee688b06ed0248b9c42683c9524f694f8f6fcc5b7e34127bf4fe53619"
        ),
    }
)
Interval = tuple[Fraction, Fraction]
RootMatrix = tuple[tuple[int, ...], ...]
FloatMatrix = tuple[tuple[float, ...], ...]


class RepresentationScopeError(ValueError):
    """Reject unregistered/schema input or a failed finite arithmetic premise."""

    def __init__(self, status: str, reason: str) -> None:
        super().__init__(status + ": " + reason)
        self.status = status
        self.reason = reason


def _closed_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RepresentationScopeError("STOP_SCHEMA", "duplicate field")
        result[key] = value
    return result


def _bits(word: object) -> float:
    if not isinstance(word, str) or not re.fullmatch(r"[0-9a-f]{16}", word):
        raise RepresentationScopeError("STOP_SCHEMA", "canonical IEEE word required")
    value = struct.unpack(">d", bytes.fromhex(word))[0]
    assert isinstance(value, float)
    if not math.isfinite(value) or (value != 0 and abs(value) < MIN_NORMAL):
        raise RepresentationScopeError("STOP_SCHEMA", "finite normal input or signed zero required")
    return value


@dataclass(frozen=True, slots=True)
class ExpressionNode:
    op: str
    value: int | str | None = None
    args: tuple[int, ...] = ()

    def payload(self) -> dict[str, object]:
        if self.op in ("integer", "bits"):
            return {"op": self.op, "value": self.value}
        return {"op": self.op, "args": list(self.args)}


def _node(raw: object, index: int) -> ExpressionNode:
    if not isinstance(raw, dict) or not isinstance(raw.get("op"), str):
        raise RepresentationScopeError("STOP_SCHEMA", "closed expression node required")
    op = raw["op"]
    if op in ("integer", "bits"):
        if set(raw) != {"op", "value"}:
            raise RepresentationScopeError("STOP_SCHEMA", "closed leaf required")
        value = raw["value"]
        if op == "integer":
            if type(value) is not int or abs(value) > 2**53:
                raise RepresentationScopeError("STOP_SCHEMA", "exact bounded integer required")
        else:
            _bits(value)
            assert isinstance(value, str)
        return ExpressionNode(op, value)
    args = raw.get("args")
    if (
        op not in ("add", "sub", "mul", "div", "sqrt")
        or set(raw) != {"op", "args"}
        or not isinstance(args, list)
        or len(args) != (1 if op == "sqrt" else 2)
        or any(type(a) is not int or not 0 <= a < index for a in args)
    ):
        raise RepresentationScopeError("STOP_SCHEMA", "bounded topological operation required")
    return ExpressionNode(op, args=tuple(args))


def _roots(raw: object, nodes: int) -> RootMatrix:
    if (
        not isinstance(raw, list)
        or not 1 <= len(raw) <= 3
        or any(
            not isinstance(row, list)
            or not 1 <= len(row) <= 2
            or any(type(i) is not int or not 0 <= i < nodes for i in row)
            for row in raw
        )
    ):
        raise RepresentationScopeError("STOP_SCHEMA", "bounded matrix root indices required")
    return tuple(tuple(row) for row in raw)


@dataclass(frozen=True, slots=True)
class PublicRepresentationFixture:
    fixture_id: str
    free_space: str
    operator_origin: str
    nodes: tuple[ExpressionNode, ...]
    factor_roots: RootMatrix
    operator_roots: RootMatrix

    def payload(self) -> dict[str, object]:
        return {
            "id": self.fixture_id,
            "free_space": self.free_space,
            "operator_origin": self.operator_origin,
            "nodes": [node.payload() for node in self.nodes],
            "A0": [list(row) for row in self.factor_roots],
            "G": [list(row) for row in self.operator_roots],
        }


def _check(f: PublicRepresentationFixture) -> None:
    if any(type(x) is not str for x in (f.fixture_id, f.free_space, f.operator_origin)):
        raise RepresentationScopeError("STOP_SCHEMA", "immutable literal identity required")
    if type(f.nodes) is not tuple or not 1 <= len(f.nodes) <= 64:
        raise RepresentationScopeError("STOP_SCHEMA", "immutable bounded nodes required")
    for index, node in enumerate(f.nodes):
        if (
            type(node) is not ExpressionNode
            or type(node.args) is not tuple
            or _node(node.payload(), index) != node
        ):
            raise RepresentationScopeError("STOP_SCHEMA", "immutable canonical node required")
    for roots in (f.factor_roots, f.operator_roots):
        if type(roots) is not tuple or any(type(row) is not tuple for row in roots):
            raise RepresentationScopeError("STOP_SCHEMA", "immutable matrix required")
        _roots([list(row) for row in roots], len(f.nodes))
    m, n = len(f.factor_roots), len(f.factor_roots[0])
    g = f.operator_roots
    if (
        m < n
        or any(len(row) != n for row in f.factor_roots)
        or len(g) != n
        or any(len(row) != n for row in g)
        or any(g[i][j] != g[j][i] for i in range(n) for j in range(n))
    ):
        raise RepresentationScopeError("STOP_SCHEMA", "SAME symmetric-root dimensions required")
    if (
        f.fixture_id not in FIXTURE_SHA256
        or f.free_space != "authored-expression-space:" + f.fixture_id
        or f.operator_origin != "original-public-scalar-expression"
    ):
        raise RepresentationScopeError("STOP_BINDING", "SAME authored space required")
    raw = (json.dumps(f.payload(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256[f.fixture_id]:
        raise RepresentationScopeError("STOP_BINDING", "changed authored fixture")


def validate_public_fixture(raw: Mapping[str, object]) -> PublicRepresentationFixture:
    if set(raw) != {"id", "free_space", "operator_origin", "nodes", "A0", "G"}:
        raise RepresentationScopeError("STOP_SCHEMA", "closed fixture required")
    identifier, space, origin = (raw[k] for k in ("id", "free_space", "operator_origin"))
    nodes = raw["nodes"]
    if (
        not all(isinstance(x, str) for x in (identifier, space, origin))
        or not isinstance(nodes, list)
        or not 1 <= len(nodes) <= 64
    ):
        raise RepresentationScopeError("STOP_SCHEMA", "bounded literal fixture required")
    assert isinstance(identifier, str) and isinstance(space, str) and isinstance(origin, str)
    f = PublicRepresentationFixture(
        identifier,
        space,
        origin,
        tuple(_node(node, i) for i, node in enumerate(nodes)),
        _roots(raw["A0"], len(nodes)),
        _roots(raw["G"], len(nodes)),
    )
    _check(f)
    return f


def read_public_fixture(
    binding: Mapping[str, str],
    reader: Callable[[], bytes],
) -> PublicRepresentationFixture:
    """Reject all other roles and identities BEFORE callback bytes."""
    if (
        set(binding) != {"version", "role", "fixture_id", "sha256", "source_main", "free_space"}
        or any(type(x) is not str for x in binding.values())
        or binding["version"] != BUNDLE_VERSION
        or binding["role"] != ROLE
        or binding["fixture_id"] not in FIXTURE_SHA256
        or binding["sha256"] != BUNDLE_SHA256
        or binding["source_main"] != SOURCE_MAIN
        or binding["free_space"] != "authored-expression-space:" + binding["fixture_id"]
    ):
        raise RepresentationScopeError("DENY_BEFORE_BYTES", "unregistered public binding")
    raw = reader()
    if (
        type(raw) is not bytes
        or len(raw) > 32768
        or hashlib.sha256(raw).hexdigest() != BUNDLE_SHA256
    ):
        raise RepresentationScopeError("STOP_BINDING", "changed public bytes")
    data = json.loads(raw, object_pairs_hook=_closed_object)
    if not isinstance(data, dict) or set(data) != {"version", "role", "source_main", "fixtures"}:
        raise RepresentationScopeError("STOP_SCHEMA", "closed public bundle required")
    if (data["version"], data["role"], data["source_main"]) != (BUNDLE_VERSION, ROLE, SOURCE_MAIN):
        raise RepresentationScopeError("STOP_BINDING", "changed source role")
    rows = data["fixtures"]
    if not isinstance(rows, list) or len(rows) != 12 or any(not isinstance(r, dict) for r in rows):
        raise RepresentationScopeError("STOP_SCHEMA", "complete public panel required")
    fixtures = [validate_public_fixture(row) for row in rows]
    if tuple(f.fixture_id for f in fixtures) != tuple(FIXTURE_SHA256):
        raise RepresentationScopeError("STOP_BINDING", "changed ordered panel")
    return next(f for f in fixtures if f.fixture_id == binding["fixture_id"])


def _sqrt_grid(q: Fraction) -> Interval:
    if type(q) is not Fraction or q < 0:
        raise RepresentationScopeError("STOP_SIGN", "nonnegative sqrt premise unresolved")
    grid = 1 << SQRT_BITS
    integer = math.isqrt(q.numerator * grid * grid // q.denominator)
    low = Fraction(integer, grid)
    return low, low if low * low == q else Fraction(integer + 1, grid)


def _interval(op: str, a: Interval, b: Interval | None = None) -> Interval:
    if op == "sqrt":
        return _sqrt_grid(a[0])[0], _sqrt_grid(a[1])[1]
    assert b is not None
    if op == "add":
        return a[0] + b[0], a[1] + b[1]
    if op == "sub":
        return a[0] - b[1], a[1] - b[0]
    if op == "div":
        if b[0] <= 0 <= b[1]:
            raise RepresentationScopeError("STOP_SIGN", "nonzero denominator premise unresolved")
        b = (1 / b[1], 1 / b[0])
    products = tuple(x * y for x in a for y in b)
    return min(products), max(products)


def _up(q: Fraction) -> float:
    try:
        value = float(q)
    except OverflowError as exc:
        raise RepresentationScopeError("STOP_ARITHMETIC", "outward overflow") from exc
    if not math.isfinite(value) or (q != 0 and value == 0) or (value and abs(value) < MIN_NORMAL):
        raise RepresentationScopeError("STOP_ARITHMETIC", "outward range failure")
    if Fraction(value) < q:
        value = math.nextafter(value, math.inf)
    if not math.isfinite(value) or (value and abs(value) < MIN_NORMAL):
        raise RepresentationScopeError("STOP_ARITHMETIC", "outward range failure")
    return value


def _scalar(node: ExpressionNode, values: list[float]) -> tuple[float, bool]:
    if node.op == "integer":
        assert type(node.value) is int
        return float(node.value), node.value != 0
    if node.op == "bits":
        value = _bits(node.value)
        return value, value != 0
    a = values[node.args[0]]
    if node.op == "sqrt":
        return math.sqrt(a), a != 0
    b = values[node.args[1]]
    if node.op == "add":
        return a + b, Fraction(a) + Fraction(b) != 0
    if node.op == "sub":
        return a - b, Fraction(a) - Fraction(b) != 0
    if node.op == "mul":
        return a * b, Fraction(a) * Fraction(b) != 0
    return a / b, Fraction(a) / Fraction(b) != 0


@dataclass(frozen=True, slots=True)
class NodeTrace:
    node: int
    op: str
    operand_hex: tuple[str, ...]
    result_hex: str
    intended_lower: Fraction
    intended_upper: Fraction

    def payload(self) -> dict[str, object]:
        return {
            "node": self.node,
            "op": self.op,
            "operand_hex": list(self.operand_hex),
            "result_hex": self.result_hex,
            "intended_lower": str(self.intended_lower),
            "intended_upper": str(self.intended_upper),
        }


@dataclass(frozen=True, slots=True)
class RepresentationResult:
    fixture_id: str
    status: str
    trace: tuple[NodeTrace, ...]
    failure_node: int | None = None
    reason: str = ""
    A_hat: FloatMatrix | None = None
    square_uppers: tuple[tuple[str, Fraction], ...] | None = None
    bounds: tuple[tuple[str, float], ...] | None = None

    def payload(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "status": self.status,
            "trace": [step.payload() for step in self.trace],
            "failure_node": self.failure_node,
            "reason": self.reason,
            "A_hat": None if self.A_hat is None else [[x.hex() for x in row] for row in self.A_hat],
            "square_uppers": None
            if self.square_uppers is None
            else {k: str(q) for k, q in self.square_uppers},
            "bounds": None if self.bounds is None else {k: x.hex() for k, x in self.bounds},
            "squares_are_upper_enclosures": True,
            "public_intended_only": True,
            "diagnostic_only": True,
            "real_fem_certified": False,
            "PSD_or_coercivity_certified": False,
        }


def _square_upper(entries: list[Interval]) -> Fraction:
    return sum((max(abs(low), abs(high)) ** 2 for low, high in entries), Fraction(0))


def _errors(
    f: PublicRepresentationFixture,
    intervals: list[Interval],
    a: FloatMatrix,
) -> tuple[tuple[tuple[str, Fraction], ...], tuple[tuple[str, float], ...]]:
    n = len(f.operator_roots)
    factor_error = [
        _interval("sub", intervals[root], (Fraction(value), Fraction(value)))
        for roots, values in zip(f.factor_roots, a, strict=True)
        for root, value in zip(roots, values, strict=True)
    ]
    structural, representation, complete = [], [], []
    for i in range(n):
        for j in range(n):
            gram = (Fraction(0), Fraction(0))
            represented = Fraction(0)
            for k, roots in enumerate(f.factor_roots):
                gram = _interval(
                    "add", gram, _interval("mul", intervals[roots[i]], intervals[roots[j]])
                )
                represented += Fraction(a[k][i]) * Fraction(a[k][j])
            target = intervals[f.operator_roots[i][j]]
            exact_gram = (represented, represented)
            structural.append(_interval("sub", target, gram))
            representation.append(_interval("sub", gram, exact_gram))
            complete.append(_interval("sub", target, exact_gram))
    squares = {
        "e": _square_upper(factor_error),
        "a": sum((Fraction(x) ** 2 for row in a for x in row), Fraction(0)),
        "d0": _square_upper(structural),
        "d1": _square_upper(representation),
        "complete": _square_upper(complete),
    }
    upper = {key: _up(_sqrt_grid(q)[1]) for key, q in squares.items()}
    upper["cross"] = _up(2 * Fraction(upper["a"]) * Fraction(upper["e"]))
    upper["square"] = _up(Fraction(upper["e"]) ** 2)
    upper["change"] = _up(Fraction(upper["cross"]) + Fraction(upper["square"]))
    upper["delta"] = _up(Fraction(upper["d0"]) + Fraction(upper["change"]))
    return tuple(squares.items()), tuple(upper.items())


def enclose_representation(f: PublicRepresentationFixture) -> RepresentationResult:
    """Run only the registered public program, preserving every partial stop."""
    _check(f)
    intervals: list[Interval] = []
    values: list[float] = []
    trace: list[NodeTrace] = []
    index = 0
    try:
        for index, node in enumerate(f.nodes):
            if node.op in ("integer", "bits"):
                if node.op == "integer":
                    assert type(node.value) is int
                    q = Fraction(node.value)
                else:
                    q = Fraction(_bits(node.value))
                assert type(q) is Fraction
                bounds = (q, q)
            else:
                bounds = _interval(
                    node.op,
                    intervals[node.args[0]],
                    None if node.op == "sqrt" else intervals[node.args[1]],
                )
            operands = tuple(values[i].hex() for i in node.args)
            try:
                value, nonzero = _scalar(node, values)
            except (ValueError, OverflowError, ZeroDivisionError) as exc:
                trace.append(
                    NodeTrace(index, node.op, operands, "ERROR:" + type(exc).__name__, *bounds)
                )
                raise RepresentationScopeError(
                    "STOP_ARITHMETIC", "represented arithmetic exception"
                ) from exc
            trace.append(NodeTrace(index, node.op, operands, value.hex(), *bounds))
            if (
                not math.isfinite(value)
                or (nonzero and value == 0)
                or (value and abs(value) < MIN_NORMAL)
            ):
                raise RepresentationScopeError("STOP_ARITHMETIC", "represented range failure")
            intervals.append(bounds)
            values.append(value)
        a = tuple(tuple(values[i] for i in row) for row in f.factor_roots)
        squares, upper = _errors(f, intervals, a)
        return RepresentationResult(
            f.fixture_id, "PASS", tuple(trace), A_hat=a, square_uppers=squares, bounds=upper
        )
    except RepresentationScopeError as exc:
        return RepresentationResult(f.fixture_id, exc.status, tuple(trace), index, exc.reason)
