"""Independent B4.43 interval/IEEE audit; no candidate/shared-helper imports."""

import hashlib
import json
import math
import struct
from fractions import Fraction

FINGERPRINTS = {
    "exact-dyadic-signed-zero": "a56962f6c994c8297b5eee70f43c6905a6d29b350d7d3178d6e69ab4208873a4",
    "separate-unit-anchor": "bf4db3c33cec43842d0b9a513f4704980c1e8e962683cfd973411b3476e01c5b",
    "assembled-cancellation": "b732b157c81695edf2a294c2863fa6c8b348d4576e0ce7c22c6c62858c23a5a3",
    "both-triangles-retained": "2ba6deed086284f8a416b58950e5dfecd5340bc2668c0f45f8aa2909a0dcccda",
    "irrational-and-accepted-load": (
        "2efbb322150201ec7e1fa5b319cd5215d1dc51b524bbbf468798c3800c308c36"
    ),
    "rounded-residual-cancellation": (
        "87c84026627ba5e9f0d255a7853692814988c607116ab6500b7b84a133815c53"
    ),
    "scatter-overflow-stop": "cd014ef754b94e6dea87a0f75c8893591ef6ef4c0dae18b287cdb6cc6594a8e7",
    "load-underflow-stop": "5080b536b50ef6476bfd32cbe5a66f72dab136ed2ca946d5f72eb4e0c3d377e6",
    "residual-overflow-stop": "7d2b55862ab59488bfd0ebc89a4e58d2e7791a82e6d13e22ba528c3f14c46f9a",
    "residual-underflow-stop": "b37755f74a5bca801b9ce960e5fdc95e85f78b97af80743565584c05a144321f",
}
EXPECTED = {
    "exact-dyadic-signed-zero": "PASS",
    "separate-unit-anchor": "PASS",
    "assembled-cancellation": "PASS",
    "both-triangles-retained": "PASS",
    "irrational-and-accepted-load": "PASS",
    "rounded-residual-cancellation": "PASS",
    "scatter-overflow-stop": "STOP_ARITHMETIC",
    "load-underflow-stop": "STOP_ARITHMETIC",
    "residual-overflow-stop": "STOP_ARITHMETIC",
    "residual-underflow-stop": "STOP_ARITHMETIC",
}
RESULT_FIELDS = {
    "fixture_id",
    "status",
    "trace",
    "failure_stage",
    "reason",
    "arrays",
    "square_uppers",
    "bounds",
    "squares_are_upper_enclosures",
    "public_intended_only",
    "diagnostic_only",
    "real_fem_certified",
    "PSD_or_coercivity_certified",
    "loss_gradient_changed",
}
TRACE_FIELDS = {"stage", "op", "operand_hex", "result_hex", "intended_lower", "intended_upper"}
NORMS = (
    "beta_G",
    "beta_K",
    "beta_f",
    "beta_eval",
    "q_hat",
    "u_plus",
    "intended_residual",
    "symmetry_G",
    "symmetry_K",
)
STAGES = (*NORMS, "q_eval", "operator_solution", "with_operator", "r_plus")


class _Undecided(ValueError):
    pass


def _normal_or_zero(value):
    return math.isfinite(value) and (value == 0 or abs(value) >= float.fromhex("0x1p-1022"))


def _hex(text):
    if not isinstance(text, str):
        raise ValueError("hex string required")
    value = float.fromhex(text)
    if value.hex() != text:
        raise ValueError("canonical represented value required")
    return value


def _rational(text):
    if not isinstance(text, str) or len(text) > 4096:
        raise ValueError("bounded rational endpoint required")
    value = Fraction(text)
    if str(value) != text:
        raise ValueError("canonical exact endpoint required")
    return value


def _rn(exact, value, square_root=False):
    """Prove RN-even using rational adjacent midpoints, including range failures."""
    if math.isinf(value):
        boundary = Fraction(2**1024 - 2**970)
        return not square_root and (exact >= boundary if value > 0 else exact <= -boundary)
    if not math.isfinite(value):
        return False
    predecessor = math.nextafter(value, -math.inf)
    successor = math.nextafter(value, math.inf)
    center = Fraction(value)
    low = (
        (Fraction(predecessor) + center) / 2
        if math.isfinite(predecessor)
        else -Fraction(2**1024 - 2**970)
    )
    high = (
        (center + Fraction(successor)) / 2
        if math.isfinite(successor)
        else Fraction(2**1024 - 2**970)
    )
    even = not (struct.unpack(">Q", struct.pack(">d", value))[0] & 1)
    if square_root:
        return (
            exact >= 0
            and value >= 0
            and (low <= 0 or exact > low**2 or (even and exact == low**2))
            and (exact < high**2 or (even and exact == high**2))
        )
    return (exact > low or (even and exact == low)) and (exact < high or (even and exact == high))


def _zero_sign(op, inputs, exact):
    if op in ("mul", "div"):
        return math.copysign(1, inputs[0]) * math.copysign(1, inputs[1])
    if op == "sqrt":
        return math.copysign(1, inputs[0])
    if exact:
        return -1 if exact < 0 else 1
    if op in ("add", "sub"):
        right = -inputs[1] if op == "sub" else inputs[1]
        if inputs[0] == right == 0 and math.copysign(1, inputs[0]) == math.copysign(1, right) == -1:
            return -1
    return 1


class _Proof:
    def __init__(self):
        self.checks = {}
        self.roots = 0

    def check(self, name, predicate):
        assert name not in self.checks
        self.checks[name] = bool(predicate)
        if not predicate:
            raise ValueError(name)

    def root80(self, q):
        """Integer bisection with a fixed80-bit output grid; no math.isqrt/sqrt."""
        if q < 0:
            raise _Undecided("nonnegative sqrt premise unresolved")
        grid = 2**80
        scaled = q.numerator * 2**160 // q.denominator
        lo, hi = 0, 2 ** ((scaled.bit_length() + 1) // 2)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if mid * mid <= scaled:
                lo = mid
            else:
                hi = mid - 1
        lower = Fraction(lo, grid)
        upper = lower if lower * lower == q else lower + Fraction(1, grid)
        self.check(
            "root80_squared_endpoints_" + str(self.roots),
            lower**2 <= q <= upper**2 and q < (lower + Fraction(1, grid)) ** 2,
        )
        self.check(
            "root80_fixed_grid_" + str(self.roots),
            upper - lower in (0, Fraction(1, grid)) and (upper == lower) == (lower**2 == q),
        )
        self.roots += 1
        return lower, upper

    def operate(self, op, a, b=None):
        if op == "sqrt":
            return self.root80(a[0])[0], self.root80(a[1])[1]
        if op == "add":
            return a[0] + b[0], a[1] + b[1]
        if op == "sub":
            return a[0] - b[1], a[1] - b[0]
        if op == "div":
            if b[0] <= 0 <= b[1]:
                raise _Undecided("nonzero denominator premise unresolved")
            candidates = [x / y for x in a for y in b]
        else:
            candidates = [x * y for x in a for y in b]
        return min(candidates), max(candidates)

    def upward(self, name, raw, exact):
        value = _hex(raw)
        self.check(name + "_finite_normal", _normal_or_zero(value) and not (exact and value == 0))
        self.check(name + "_directed", Fraction(value) >= exact)
        self.check(
            name + "_minimal",
            exact == 0 and value == 0 or Fraction(math.nextafter(value, -math.inf)) < exact,
        )
        return Fraction(value)


def _square(entries):
    total = Fraction(0)
    for low, high in entries:
        total += max(low * low, high * high)
    return total


class _Stop(ValueError):
    def __init__(self, stage, reason):
        self.stage, self.reason = stage, reason


def _audit(fixture, result, proof):
    check = proof.check
    check("closed_result", isinstance(result, dict) and set(result) == RESULT_FIELDS)
    identifier = fixture["id"]
    encoded = (json.dumps(fixture, sort_keys=True, separators=(",", ":")) + "\n").encode()
    check(
        "authored_source",
        identifier in FINGERPRINTS
        and hashlib.sha256(encoded).hexdigest() == FINGERPRINTS[identifier],
    )
    check("same_identity", result["fixture_id"] == identifier)
    for name, expected in [
        ("squares_are_upper_enclosures", True),
        ("public_intended_only", True),
        ("diagnostic_only", True),
        ("real_fem_certified", False),
        ("PSD_or_coercivity_certified", False),
        ("loss_gradient_changed", False),
    ]:
        check(name, type(result[name]) is bool and result[name] is expected)
    trace = result["trace"]
    check("bounded_trace", isinstance(trace, list) and len(trace) <= 128)
    cursor = 0

    def step(stage, op, inputs, intended, leaf=None):
        nonlocal cursor
        row = trace[cursor]
        check("closed_trace_" + str(cursor), isinstance(row, dict) and set(row) == TRACE_FIELDS)
        check(
            "ordered_operands_" + str(cursor),
            row["stage"] == stage
            and row["op"] == op
            and row["operand_hex"] == [x.hex() for x in inputs],
        )
        check(
            "intended_interval_" + str(cursor),
            (_rational(row["intended_lower"]), _rational(row["intended_upper"])) == intended,
        )
        value = _hex(row["result_hex"])
        if leaf is not None:
            exact, nearest = Fraction(leaf), value.hex() == leaf.hex()
        elif op == "sqrt":
            exact = Fraction(inputs[0])
            nearest = _rn(exact, value, True)
        else:
            a, b = map(Fraction, inputs)
            exact = (
                a + b if op == "add" else a - b if op == "sub" else a * b if op == "mul" else a / b
            )
            nearest = _rn(exact, value)
        if value == 0 and leaf is None:
            nearest = nearest and math.copysign(1, value) == _zero_sign(op, inputs, exact)
        check("RN_even_operation_" + str(cursor), nearest)
        cursor += 1
        if not _normal_or_zero(value) or (exact and value == 0):
            raise _Stop(stage, "represented range failure")
        return value

    intervals, values = [], []
    try:
        for index, node in enumerate(fixture["nodes"]):
            op = node["op"]
            if op in ("integer", "bits"):
                leaf = (
                    float(node["value"])
                    if op == "integer"
                    else struct.unpack(">d", bytes.fromhex(node["value"]))[0]
                )
                target = (Fraction(leaf), Fraction(leaf))
            else:
                leaf = None
                args = [intervals[i] for i in node["args"]]
                target = proof.operate(op, args[0], None if op == "sqrt" else args[1])
            values.append(
                step(
                    "node:" + str(index),
                    op,
                    [values[i] for i in node.get("args", [])],
                    target,
                    leaf,
                )
            )
            intervals.append(target)
        n = len(fixture["u_bits"])
        arrays, targets = {}, {}
        for name in ("G", "K", "f"):
            width = 1 if name == "f" else n
            terms = (
                [[[root] for root in term] for term in fixture["f_terms"]]
                if name == "f"
                else fixture[name + "_terms"]
            )
            arrays[name], targets[name] = [], []
            for i in range(n):
                real_row, represented_row = [], []
                for j in range(width):
                    number, real_sum = 0.0, (Fraction(0), Fraction(0))
                    for k, matrix in enumerate(terms):
                        root = matrix[i][j]
                        real_sum = (
                            real_sum[0] + intervals[root][0],
                            real_sum[1] + intervals[root][1],
                        )
                        number = step(
                            f"{name}:{i}:{j}:{k}", "add", [number, values[root]], real_sum
                        )
                    real_row.append(real_sum)
                    represented_row.append(number)
                arrays[name].append(represented_row)
                targets[name].append(real_row)
        u = [struct.unpack(">d", bytes.fromhex(word))[0] for word in fixture["u_bits"]]
        exact_residual, rounded_residual, true_residual = [], [], []
        for i in range(n):
            number, rational, real_sum = 0.0, Fraction(0), (Fraction(0), Fraction(0))
            for j in range(n):
                q = Fraction(arrays["K"][i][j]) * Fraction(u[j])
                product = step(f"residual_mul:{i}:{j}", "mul", [arrays["K"][i][j], u[j]], (q, q))
                operation = Fraction(number) + Fraction(product)
                number = step(
                    f"residual_sum:{i}:{j}", "add", [number, product], (operation, operation)
                )
                rational += q
                endpoints = [x * Fraction(u[j]) for x in targets["K"][i][j]]
                real_sum = (real_sum[0] + min(endpoints), real_sum[1] + max(endpoints))
            operation = Fraction(number) - Fraction(arrays["f"][i][0])
            rounded_residual.append(
                step(
                    "residual_sub:" + str(i),
                    "sub",
                    [number, arrays["f"][i][0]],
                    (operation, operation),
                )
            )
            exact_residual.append(rational - Fraction(arrays["f"][i][0]))
            true_residual.append(
                (real_sum[0] - targets["f"][i][0][1], real_sum[1] - targets["f"][i][0][0])
            )
    except _Stop as exc:
        check("prescribed_status", EXPECTED[identifier] == result["status"] == "STOP_ARITHMETIC")
        check("full_stop_prefix", len(trace) == cursor)
        check("failure_stage", result["failure_stage"] == exc.stage)
        check("reason", result["reason"] == exc.reason)
        check(
            "no_invented_post_stop",
            all(result[k] is None for k in ("arrays", "square_uppers", "bounds")),
        )
        return
    check("prescribed_status", EXPECTED[identifier] == result["status"] == "PASS")
    check("complete_trace", len(trace) == cursor)
    check("no_failure", result["failure_stage"] is None and result["reason"] == "")
    expected_arrays = {
        name: [[x.hex() for x in row] for row in arrays[name]] for name in ("G", "K")
    }
    expected_arrays.update(
        f=[row[0].hex() for row in arrays["f"]],
        u=[x.hex() for x in u],
        r_arrays=[str(q) for q in exact_residual],
        r_hat=[x.hex() for x in rounded_residual],
    )
    check("ALL_exact_actual_arrays", result["arrays"] == expected_arrays)
    squares = {}
    for name in ("G", "K", "f"):
        entries = []
        for i, row in enumerate(arrays[name]):
            for j, value in enumerate(row):
                low, high = targets[name][i][j]
                entries.append((low - Fraction(value), high - Fraction(value)))
        squares["beta_" + name] = _square(entries)
    squares["beta_eval"] = sum(
        ((x - Fraction(y)) ** 2 for x, y in zip(exact_residual, rounded_residual, strict=True)),
        Fraction(0),
    )
    squares["q_hat"] = sum((Fraction(x) ** 2 for x in rounded_residual), Fraction(0))
    squares["u_plus"] = sum((Fraction(x) ** 2 for x in u), Fraction(0))
    squares["intended_residual"] = _square(true_residual)
    for name in ("G", "K"):
        squares["symmetry_" + name] = sum(
            (
                (Fraction(arrays[name][i][j]) - Fraction(arrays[name][j][i])) ** 2
                for i in range(n)
                for j in range(n)
            ),
            Fraction(0),
        )
    check(
        "closed_squares",
        isinstance(result["square_uppers"], dict) and set(result["square_uppers"]) == set(NORMS),
    )
    check(
        "closed_bounds", isinstance(result["bounds"], dict) and set(result["bounds"]) == set(STAGES)
    )
    upper = {}
    for name in NORMS:
        q = _rational(result["square_uppers"][name])
        check(name + "_independent_square", q == squares[name] and q >= 0)
        root = proof.root80(q)[1]
        upper[name] = proof.upward(name, result["bounds"][name], root)
        check(name + "_norm_bound", upper[name] ** 2 >= q)
    for name, target in [
        ("q_eval", upper["q_hat"] + upper["beta_eval"]),
        ("operator_solution", upper["beta_K"] * upper["u_plus"]),
    ]:
        upper[name] = proof.upward(name, result["bounds"][name], target)
    upper["with_operator"] = proof.upward(
        "with_operator",
        result["bounds"]["with_operator"],
        upper["q_eval"] + upper["operator_solution"],
    )
    upper["r_plus"] = proof.upward(
        "r_plus", result["bounds"]["r_plus"], upper["with_operator"] + upper["beta_f"]
    )
    check(
        "all_terms_retained",
        upper["r_plus"]
        >= upper["q_hat"]
        + upper["beta_eval"]
        + upper["beta_K"] * upper["u_plus"]
        + upper["beta_f"],
    )


def audit_case(fixture, result):
    """Independent exact predicates reject malformed/tampered results explicitly."""
    proof = _Proof()
    try:
        _audit(fixture, result, proof)
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError, OverflowError) as exc:
        proof.checks["audit_completed"] = False
        return {
            "passed": False,
            "checks": proof.checks,
            "error": type(exc).__name__ + ": " + str(exc),
        }
    proof.checks["audit_completed"] = True
    return {"passed": all(proof.checks.values()), "checks": proof.checks, "error": ""}
