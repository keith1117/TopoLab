"""B4.43 finite public assembly/residual diagnostics; no FEM or solver integration."""

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType

from topolab.intended_representation import (
    MIN_NORMAL,
    ExpressionNode,
    Interval,
    RepresentationScopeError,
    _bits,
    _closed_object,
    _interval,
    _node,
    _scalar,
    _sqrt_grid,
    _up,
)

BUNDLE_VERSION = "topolab.b4_43.public-assembled-residual-bundle.v1"
ROLE = "public-assembled-residual-software"
SOURCE_MAIN = "23558c4d2767e2a56cb2f5d12293800ac2d81fa5"
# Frozen authored fingerprints are filled from the preregistered text, not outputs.
BUNDLE_SHA256 = "cc81a29684fba07c58a48a0ca9be3e80efa8fd88b5019cc95af5783d648bec64"
FIXTURE_SHA256 = MappingProxyType(
    {
        "exact-dyadic-signed-zero": (
            "a56962f6c994c8297b5eee70f43c6905a6d29b350d7d3178d6e69ab4208873a4"
        ),
        "separate-unit-anchor": "bf4db3c33cec43842d0b9a513f4704980c1e8e962683cfd973411b3476e01c5b",
        "assembled-cancellation": (
            "b732b157c81695edf2a294c2863fa6c8b348d4576e0ce7c22c6c62858c23a5a3"
        ),
        "both-triangles-retained": (
            "2ba6deed086284f8a416b58950e5dfecd5340bc2668c0f45f8aa2909a0dcccda"
        ),
        "irrational-and-accepted-load": (
            "2efbb322150201ec7e1fa5b319cd5215d1dc51b524bbbf468798c3800c308c36"
        ),
        "rounded-residual-cancellation": (
            "87c84026627ba5e9f0d255a7853692814988c607116ab6500b7b84a133815c53"
        ),
        "scatter-overflow-stop": "cd014ef754b94e6dea87a0f75c8893591ef6ef4c0dae18b287cdb6cc6594a8e7",
        "load-underflow-stop": "5080b536b50ef6476bfd32cbe5a66f72dab136ed2ca946d5f72eb4e0c3d377e6",
        "residual-overflow-stop": (
            "7d2b55862ab59488bfd0ebc89a4e58d2e7791a82e6d13e22ba528c3f14c46f9a"
        ),
        "residual-underflow-stop": (
            "b37755f74a5bca801b9ce960e5fdc95e85f78b97af80743565584c05a144321f"
        ),
    }
)
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
        or space != "authored-assembly-space:" + identifier
        or origin != "original-public-scalar-contributions"
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
    binding: Mapping[str, str],
    reader: Callable[[], bytes],
) -> PublicAssemblyFixture:
    """Deny all other source/role/space/fixture identities BEFORE callback bytes."""
    if (
        set(binding) != {"version", "role", "fixture_id", "sha256", "source_main", "free_space"}
        or any(type(value) is not str for value in binding.values())
        or binding["version"] != BUNDLE_VERSION
        or binding["role"] != ROLE
        or binding["fixture_id"] not in FIXTURE_SHA256
        or binding["sha256"] != BUNDLE_SHA256
        or binding["source_main"] != SOURCE_MAIN
        or binding["free_space"] != "authored-assembly-space:" + binding["fixture_id"]
    ):
        raise RepresentationScopeError("DENY_BEFORE_BYTES", "unregistered public assembly binding")
    raw = reader()
    if (
        type(raw) is not bytes
        or len(raw) > 32768
        or hashlib.sha256(raw).hexdigest() != BUNDLE_SHA256
    ):
        raise RepresentationScopeError("STOP_BINDING", "changed public bytes")
    bundle = json.loads(raw, object_pairs_hook=_closed_object)
    if not isinstance(bundle, dict) or set(bundle) != {
        "version",
        "role",
        "source_main",
        "fixtures",
    }:
        raise RepresentationScopeError("STOP_SCHEMA", "closed public bundle required")
    if (bundle["version"], bundle["role"], bundle["source_main"]) != (
        BUNDLE_VERSION,
        ROLE,
        SOURCE_MAIN,
    ):
        raise RepresentationScopeError("STOP_BINDING", "changed source/role")
    rows = bundle["fixtures"]
    if (
        not isinstance(rows, list)
        or len(rows) != 10
        or any(not isinstance(row, dict) for row in rows)
    ):
        raise RepresentationScopeError("STOP_SCHEMA", "complete public panel required")
    fixtures = [validate_public_fixture(row) for row in rows]
    if tuple(f.fixture_id for f in fixtures) != tuple(FIXTURE_SHA256):
        raise RepresentationScopeError("STOP_BINDING", "changed ordered public panel")
    return next(f for f in fixtures if f.fixture_id == binding["fixture_id"])


def _square(entries: list[Interval]) -> Fraction:
    return sum((max(abs(low), abs(high)) ** 2 for low, high in entries), Fraction(0))


def enclose_assembled_residual(fixture: PublicAssemblyFixture) -> dict[str, object]:
    """Run the single registered scalar program, preserving every partial stop."""
    _check(fixture)
    trace: list[dict[str, object]] = []
    stage = "node:0"
    receipt: dict[str, object] = {
        "fixture_id": fixture.fixture_id,
        "status": "PASS",
        "trace": trace,
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
                exact_product = Fraction(actual["K"][row][col]) * Fraction(u[col])
                stage = f"residual_mul:{row}:{col}"
                product = binary(
                    "mul", actual["K"][row][col], u[col], (exact_product, exact_product)
                )
                stage = f"residual_sum:{row}:{col}"
                exact_operation = Fraction(accumulator) + Fraction(product)
                accumulator = binary(
                    "add", accumulator, product, (exact_operation, exact_operation)
                )
                exact_sum += exact_product
                target_sum = _interval(
                    "add",
                    target_sum,
                    _interval("mul", targets["K"][row][col], (Fraction(u[col]), Fraction(u[col]))),
                )
            stage = "residual_sub:" + str(row)
            exact_operation = Fraction(accumulator) - Fraction(actual["f"][row][0])
            r_hat.append(
                binary("sub", accumulator, actual["f"][row][0], (exact_operation, exact_operation))
            )
            r_arrays.append(exact_sum - Fraction(actual["f"][row][0]))
            intended_residual.append(_interval("sub", target_sum, targets["f"][row][0]))
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
        upper: dict[str, float] = {}
        for name, q in squares.items():
            stage = "norm:" + name
            upper[name] = _up(_sqrt_grid(q)[1])
        for name, left, right, op in [
            ("q_eval", "q_hat", "beta_eval", "add"),
            ("operator_solution", "beta_K", "u_plus", "mul"),
            ("with_operator", "q_eval", "operator_solution", "add"),
            ("r_plus", "with_operator", "beta_f", "add"),
        ]:
            stage = "bound:" + name
            a, b = Fraction(upper[left]), Fraction(upper[right])
            upper[name] = _up(a * b if op == "mul" else a + b)
        receipt["arrays"] = {
            **{name: [[x.hex() for x in row] for row in actual[name]] for name in ("G", "K")},
            "f": [row[0].hex() for row in actual["f"]],
            "u": [x.hex() for x in u],
            "r_arrays": [str(x) for x in r_arrays],
            "r_hat": [x.hex() for x in r_hat],
        }
        receipt["square_uppers"] = {name: str(q) for name, q in squares.items()}
        receipt["bounds"] = {name: x.hex() for name, x in upper.items()}
    except RepresentationScopeError as exc:
        receipt.update(status=exc.status, failure_stage=stage, reason=exc.reason)
    return receipt
