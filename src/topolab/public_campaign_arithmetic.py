"""Fresh B4.47 public arithmetic; standalone stdlib, durable operation hook.

Own B4.41/B4.43 equations/conventions only; no real FEM or historical retry.
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

SQRT_BITS = 80
MIN_NORMAL = float.fromhex("0x1p-1022")
Interval = tuple[Fraction, Fraction]
BUNDLE_VERSION = "topolab.b4_47.fresh-public-arithmetic-campaign.v1"
ROLE = "fresh-public-arithmetic-software"
SOURCE_MAIN = "491c0bb45e6f8990e23d27890b871946b775af0e"
FIXTURE_SHA256 = MappingProxyType(
    {
        "fresh-dyadic-signed-zero": (
            "8400cbcfffa8699fe9239f6f9294ab7a633f8ceef63ff7aa2dcf62b5fc591a3d"
        ),
        "fresh-half-lost-in-assembly": (
            "888105efcb25adc4097bdb661affff1d49bfd3e80695fe66aa9f953fe7a6cbeb"
        ),
        "fresh-symmetric-target-two-triangles": (
            "b814877a14ec29420b11acada171ae54d85d3f11861142872620d179b00510a4"
        ),
        "fresh-irrational-accepted-force": (
            "c1c2f4129ede0048725babfed650ffdc8df17f16810d4d0ce710f4da49210ace"
        ),
        "fresh-zero-rounded-nonzero-intended": (
            "fda58eb7568bbd699c4651755bf041de3135f04782d52bef17b5f3bba0a72096"
        ),
        "fresh-negative-radicand-stop": (
            "4fc7eb9d7ef83e29149bd0e6bae4a70e4cb65ec0dc59c13ca974ffc5bc899e93"
        ),
        "fresh-dependent-denominator-stop": (
            "fa68333713c346d0a1fde2c7d55b5f18e95256041d071f94ac5d72ed1d2c869f"
        ),
        "fresh-node-overflow-stop": (
            "2ff666cfbda68e13c6f5dbdb643560fa2ccbc3fe90e9d75aeccb78c48b666948"
        ),
        "fresh-node-subnormal-stop": (
            "856e8d9ca5d5cfd0530b08dd68089f9126bdecf9a3ba9507152fd2e3ec5a475e"
        ),
        "fresh-node-underflow-stop": (
            "648400d25cb7b00449eaaa36f225700826c0e7e68cd68361c41799290e33d00b"
        ),
    }
)
FIXTURE_PATHS = MappingProxyType(
    {
        "fresh-dyadic-signed-zero": "tests/fixtures/b4_47/fresh-dyadic-signed-zero.json",
        "fresh-half-lost-in-assembly": "tests/fixtures/b4_47/fresh-half-lost-in-assembly.json",
        "fresh-symmetric-target-two-triangles": (
            "tests/fixtures/b4_47/fresh-symmetric-target-two-triangles.json"
        ),
        "fresh-irrational-accepted-force": (
            "tests/fixtures/b4_47/fresh-irrational-accepted-force.json"
        ),
        "fresh-zero-rounded-nonzero-intended": (
            "tests/fixtures/b4_47/fresh-zero-rounded-nonzero-intended.json"
        ),
        "fresh-negative-radicand-stop": "tests/fixtures/b4_47/fresh-negative-radicand-stop.json",
        "fresh-dependent-denominator-stop": (
            "tests/fixtures/b4_47/fresh-dependent-denominator-stop.json"
        ),
        "fresh-node-overflow-stop": "tests/fixtures/b4_47/fresh-node-overflow-stop.json",
        "fresh-node-subnormal-stop": "tests/fixtures/b4_47/fresh-node-subnormal-stop.json",
        "fresh-node-underflow-stop": "tests/fixtures/b4_47/fresh-node-underflow-stop.json",
    }
)


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


MatrixTerms = tuple[tuple[tuple[int, ...], ...], ...]
VectorTerms = tuple[tuple[int, ...], ...]
FIELDS = {"id", "free_space", "origin", "nodes", "G_terms", "K_terms", "f_terms", "u_bits"}


@dataclass(frozen=True, slots=True)
class PublicAssemblyFixture:
    fixture_id: str
    free_space: str
    origin: str
    nodes: tuple[ExpressionNode, ...]
    G_terms: MatrixTerms
    K_terms: MatrixTerms
    f_terms: VectorTerms
    u_bits: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "id": self.fixture_id,
            "free_space": self.free_space,
            "origin": self.origin,
            "nodes": [node.payload() for node in self.nodes],
            "G_terms": [[list(row) for row in term] for term in self.G_terms],
            "K_terms": [[list(row) for row in term] for term in self.K_terms],
            "f_terms": [list(term) for term in self.f_terms],
            "u_bits": list(self.u_bits),
        }


def _indices(raw: object, width: int, nodes: int) -> tuple[int, ...]:
    if (
        not isinstance(raw, list)
        or len(raw) != width
        or any(type(i) is not int or not 0 <= i < nodes for i in raw)
    ):
        raise RepresentationScopeError("STOP_SCHEMA", "bounded SAME root indices required")
    return tuple(raw)


def _terms(raw: object, n: int, nodes: int) -> MatrixTerms:
    if not isinstance(raw, list) or not 1 <= len(raw) <= 3:
        raise RepresentationScopeError("STOP_SCHEMA", "one to three contribution matrices required")
    terms = []
    for matrix in raw:
        if not isinstance(matrix, list) or len(matrix) != n:
            raise RepresentationScopeError("STOP_SCHEMA", "SAME square contribution required")
        terms.append(tuple(_indices(row, n, nodes) for row in matrix))
    return tuple(terms)


def validate_public_fixture(raw: Mapping[str, object]) -> PublicAssemblyFixture:
    if set(raw) != FIELDS:
        raise RepresentationScopeError("STOP_SCHEMA", "closed assembly fixture required")
    identifier, space, origin = (raw[k] for k in ("id", "free_space", "origin"))
    nodes, u, force = (raw[k] for k in ("nodes", "u_bits", "f_terms"))
    if (
        not isinstance(identifier, str)
        or not isinstance(space, str)
        or not isinstance(origin, str)
        or not isinstance(nodes, list)
        or not 1 <= len(nodes) <= 64
        or not isinstance(u, list)
        or not 1 <= len(u) <= 2
        or any(not isinstance(word, str) for word in u)
        or not isinstance(force, list)
        or not 1 <= len(force) <= 3
    ):
        raise RepresentationScopeError(
            "STOP_SCHEMA", "bounded literals/solution/contributions required"
        )
    words = tuple(str(word) for word in u)
    for word in words:
        _bits(word)
    fixture = PublicAssemblyFixture(
        identifier,
        space,
        origin,
        tuple(_node(node, index) for index, node in enumerate(nodes)),
        _terms(raw["G_terms"], len(u), len(nodes)),
        _terms(raw["K_terms"], len(u), len(nodes)),
        tuple(_indices(row, len(u), len(nodes)) for row in force),
        words,
    )
    encoded = (json.dumps(fixture.payload(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    if (
        fixture.fixture_id not in FIXTURE_SHA256
        or space != "b4-47-public-space:" + identifier
        or origin != "fresh-original-public-contributions-b4-47"
        or hashlib.sha256(encoded).hexdigest() != FIXTURE_SHA256[identifier]
    ):
        raise RepresentationScopeError("STOP_BINDING", "changed authored SAME fixture")
    return fixture


def _check(fixture: PublicAssemblyFixture) -> None:
    if (
        type(fixture) is not PublicAssemblyFixture
        or type(fixture.nodes) is not tuple
        or any(
            type(node) is not ExpressionNode or type(node.args) is not tuple
            for node in fixture.nodes
        )
        or type(fixture.u_bits) is not tuple
        or type(fixture.f_terms) is not tuple
        or any(type(row) is not tuple for row in fixture.f_terms)
        or any(
            type(terms) is not tuple
            or any(
                type(matrix) is not tuple or any(type(row) is not tuple for row in matrix)
                for matrix in terms
            )
            for terms in (fixture.G_terms, fixture.K_terms)
        )
    ):
        raise RepresentationScopeError("STOP_SCHEMA", "immutable fixture required")
    validate_public_fixture(fixture.payload())


def read_public_fixture(
    binding: Mapping[str, str], reader: Callable[[], bytes]
) -> PublicAssemblyFixture:
    """Reject every other role/path/identity BEFORE callback input bytes."""
    if (
        set(binding)
        != {"version", "role", "fixture_id", "sha256", "source_main", "free_space", "path"}
        or any(type(value) is not str for value in binding.values())
        or binding["version"] != BUNDLE_VERSION
        or binding["role"] != ROLE
        or binding["fixture_id"] not in FIXTURE_SHA256
        or binding["sha256"] != FIXTURE_SHA256[binding["fixture_id"]]
        or binding["source_main"] != SOURCE_MAIN
        or binding["free_space"] != "b4-47-public-space:" + binding["fixture_id"]
        or binding["path"] != FIXTURE_PATHS[binding["fixture_id"]]
    ):
        raise RepresentationScopeError("DENY_BEFORE_BYTES", "unregistered fresh public binding")
    raw = reader()
    if (
        type(raw) is not bytes
        or len(raw) > 32768
        or hashlib.sha256(raw).hexdigest() != binding["sha256"]
    ):
        raise RepresentationScopeError("STOP_BINDING", "changed fresh fixture bytes")
    value = json.loads(raw, object_pairs_hook=_closed_object)
    if not isinstance(value, dict):
        raise RepresentationScopeError("STOP_SCHEMA", "closed fixture required")
    return validate_public_fixture(value)


def _square(entries: list[Interval]) -> Fraction:
    return sum((max(abs(low), abs(high)) ** 2 for low, high in entries), Fraction(0))


def enclose_assembled_residual(
    fixture: PublicAssemblyFixture,
    journal: Callable[[str, dict[str, object]], None] | None = None,
) -> dict[str, object]:
    """Run the single registered scalar program, preserving every partial stop."""
    _check(fixture)
    trace: list[dict[str, object]] = []
    stage = "node:0"
    operations: list[dict[str, object]] = []
    receipt: dict[str, object] = {
        "fixture_id": fixture.fixture_id,
        "status": "PASS",
        "trace": trace,
        "operations": operations,
        "failure_stage": None,
        "reason": "",
        "arrays": None,
        "square_uppers": None,
        "bounds": None,
        "squares_are_upper_enclosures": True,
        "public_intended_only": True,
        "diagnostic_only": True,
        "real_fem_certified": False,
        "PSD_or_coercivity_certified": False,
        "loss_gradient_changed": False,
    }

    def event(phase: str, details: dict[str, object] | None = None) -> None:
        row: dict[str, object] = {"phase": phase, "stage": stage, "details": details or {}}
        if journal is not None:
            journal(phase, row)  # BEFORE any protected operation for phase=before.
        operations.append(row)

    def record(
        op: str, operands: list[float], value: float, interval: Interval, nonzero: bool
    ) -> float:
        trace.append(
            {
                "stage": stage,
                "op": op,
                "operand_hex": [x.hex() for x in operands],
                "result_hex": value.hex(),
                "intended_lower": str(interval[0]),
                "intended_upper": str(interval[1]),
            }
        )
        event("after", {"scalar_trace": trace[-1]})
        if (
            not math.isfinite(value)
            or (nonzero and value == 0)
            or (value and abs(value) < MIN_NORMAL)
        ):
            raise RepresentationScopeError("STOP_ARITHMETIC", "represented range failure")
        return value

    def binary(op: str, left: float, right: float, interval: Interval) -> float:
        a, b = Fraction(left), Fraction(right)
        exact = a + b if op == "add" else a - b if op == "sub" else a * b
        value = left + right if op == "add" else left - right if op == "sub" else left * right
        return record(op, [left, right], value, interval, bool(exact))

    try:
        intervals: list[Interval] = []
        values: list[float] = []
        for index, node in enumerate(fixture.nodes):
            stage = "node:" + str(index)
            event("before", {"op": node.op})
            if node.op in ("integer", "bits"):
                q = Fraction(node.value) if type(node.value) is int else Fraction(_bits(node.value))
                intended = (q, q)
            else:
                intended = _interval(
                    node.op,
                    intervals[node.args[0]],
                    None if node.op == "sqrt" else intervals[node.args[1]],
                )
            value, nonzero = _scalar(node, values)
            values.append(record(node.op, [values[i] for i in node.args], value, intended, nonzero))
            intervals.append(intended)
        n = len(fixture.u_bits)
        actual: dict[str, list[list[float]]] = {}
        targets: dict[str, list[list[Interval]]] = {}
        force_terms = tuple(tuple((i,) for i in term) for term in fixture.f_terms)
        for name, terms, width in [
            ("G", fixture.G_terms, n),
            ("K", fixture.K_terms, n),
            ("f", force_terms, 1),
        ]:
            actual[name], targets[name] = [], []
            for row in range(n):
                numbers, intended_row = [], []
                for col in range(width):
                    accumulator = 0.0
                    intended = (Fraction(0), Fraction(0))
                    for index, term in enumerate(terms):
                        stage = f"{name}:{row}:{col}:{index}"
                        root = term[row][col]
                        event("before", {"op": "add"})
                        intended = _interval("add", intended, intervals[root])
                        accumulator = binary("add", accumulator, values[root], intended)
                    numbers.append(accumulator)
                    intended_row.append(intended)
                actual[name].append(numbers)
                targets[name].append(intended_row)
        u = [_bits(word) for word in fixture.u_bits]
        r_arrays: list[Fraction] = []
        r_hat: list[float] = []
        intended_residual: list[Interval] = []
        for row in range(n):
            accumulator = 0.0
            exact_sum = Fraction(0)
            target_sum = (Fraction(0), Fraction(0))
            for col in range(n):
                stage = f"residual_mul:{row}:{col}"
                event("before", {"op": "mul"})
                exact_product = Fraction(actual["K"][row][col]) * Fraction(u[col])
                product = binary(
                    "mul", actual["K"][row][col], u[col], (exact_product, exact_product)
                )
                stage = f"residual_sum:{row}:{col}"
                event("before", {"op": "add"})
                exact_operation = Fraction(accumulator) + Fraction(product)
                accumulator = binary(
                    "add", accumulator, product, (exact_operation, exact_operation)
                )
                stage = f"residual_exact:{row}:{col}"
                event("before", {"op": "exact-residual-bookkeeping"})
                exact_sum += exact_product
                target_sum = _interval(
                    "add",
                    target_sum,
                    _interval("mul", targets["K"][row][col], (Fraction(u[col]), Fraction(u[col]))),
                )
                event(
                    "after",
                    {"exact_sum": str(exact_sum), "target_sum": [str(x) for x in target_sum]},
                )
            stage = "residual_sub:" + str(row)
            event("before", {"op": "sub"})
            exact_operation = Fraction(accumulator) - Fraction(actual["f"][row][0])
            r_hat.append(
                binary("sub", accumulator, actual["f"][row][0], (exact_operation, exact_operation))
            )
            stage = "residual_exact_final:" + str(row)
            event("before", {"op": "exact-residual-bookkeeping"})
            r_arrays.append(exact_sum - Fraction(actual["f"][row][0]))
            intended_residual.append(_interval("sub", target_sum, targets["f"][row][0]))
            event(
                "after",
                {
                    "r_arrays": str(r_arrays[-1]),
                    "intended_residual": [str(x) for x in intended_residual[-1]],
                },
            )
        stage = "exact_errors"
        event("before", {"op": "exact-squared-errors"})
        squares = {
            "beta_" + name: _square(
                [
                    _interval("sub", target, (Fraction(x), Fraction(x)))
                    for target_row, number_row in zip(targets[name], actual[name], strict=True)
                    for target, x in zip(target_row, number_row, strict=True)
                ]
            )
            for name in ("G", "K", "f")
        }
        squares.update(
            {
                "beta_eval": sum(
                    ((exact - Fraction(x)) ** 2 for exact, x in zip(r_arrays, r_hat, strict=True)),
                    Fraction(0),
                ),
                "q_hat": sum((Fraction(x) ** 2 for x in r_hat), Fraction(0)),
                "u_plus": sum((Fraction(x) ** 2 for x in u), Fraction(0)),
                "intended_residual": _square(intended_residual),
            }
        )
        for name in ("G", "K"):
            squares["symmetry_" + name] = sum(
                (
                    (Fraction(actual[name][i][j]) - Fraction(actual[name][j][i])) ** 2
                    for i in range(n)
                    for j in range(n)
                ),
                Fraction(0),
            )
        event("after", {"squares": {name: str(q) for name, q in squares.items()}})
        upper: dict[str, float] = {}
        for name, q in squares.items():
            stage = "norm:" + name
            event("before", {"op": "sqrt80-up"})
            root_upper = _sqrt_grid(q)[1]
            upper[name] = _up(root_upper)
            event(
                "after",
                {"square": str(q), "sqrt_upper": str(root_upper), "result_hex": upper[name].hex()},
            )
        for name, left, right, op in [
            ("q_eval", "q_hat", "beta_eval", "add"),
            ("operator_solution", "beta_K", "u_plus", "mul"),
            ("with_operator", "q_eval", "operator_solution", "add"),
            ("r_plus", "with_operator", "beta_f", "add"),
        ]:
            stage = "bound:" + name
            event("before", {"op": op + "-up"})
            a, b = Fraction(upper[left]), Fraction(upper[right])
            exact_transfer = a * b if op == "mul" else a + b
            upper[name] = _up(exact_transfer)
            event("after", {"exact_transfer": str(exact_transfer), "result_hex": upper[name].hex()})
        receipt["arrays"] = {
            **{name: [[x.hex() for x in row] for row in actual[name]] for name in ("G", "K")},
            "f": [row[0].hex() for row in actual["f"]],
            "u": [x.hex() for x in u],
            "r_arrays": [str(x) for x in r_arrays],
            "r_hat": [x.hex() for x in r_hat],
            "intended_residual_intervals": [
                [str(x) for x in interval] for interval in intended_residual
            ],
        }
        receipt["square_uppers"] = {name: str(q) for name, q in squares.items()}
        receipt["bounds"] = {name: x.hex() for name, x in upper.items()}
    except RepresentationScopeError as exc:
        event("failure", {"status": exc.status, "reason": exc.reason})
        receipt.update(status=exc.status, failure_stage=stage, reason=exc.reason)
    return receipt
