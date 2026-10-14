"""Independent fresh B4.47 interval/IEEE audit; no candidate/shared-helper imports."""

import hashlib
import json
import math
import struct
from fractions import Fraction

FINGERPRINTS = {
    "fresh-dyadic-signed-zero": "8400cbcfffa8699fe9239f6f9294ab7a633f8ceef63ff7aa2dcf62b5fc591a3d",
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
    "fresh-node-overflow-stop": "2ff666cfbda68e13c6f5dbdb643560fa2ccbc3fe90e9d75aeccb78c48b666948",
    "fresh-node-subnormal-stop": "856e8d9ca5d5cfd0530b08dd68089f9126bdecf9a3ba9507152fd2e3ec5a475e",
    "fresh-node-underflow-stop": "648400d25cb7b00449eaaa36f225700826c0e7e68cd68361c41799290e33d00b",
}
EXPECTED = {
    "fresh-dyadic-signed-zero": "PASS",
    "fresh-half-lost-in-assembly": "PASS",
    "fresh-symmetric-target-two-triangles": "PASS",
    "fresh-irrational-accepted-force": "PASS",
    "fresh-zero-rounded-nonzero-intended": "PASS",
    "fresh-negative-radicand-stop": "STOP_SIGN",
    "fresh-dependent-denominator-stop": "STOP_SIGN",
    "fresh-node-overflow-stop": "STOP_ARITHMETIC",
    "fresh-node-subnormal-stop": "STOP_ARITHMETIC",
    "fresh-node-underflow-stop": "STOP_ARITHMETIC",
}
RESULT_FIELDS = {
    "fixture_id",
    "status",
    "trace",
    "operations",
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
    def __init__(self, journal=None):
        self.journal = journal
        self.operations = 0
        self.after_details = {}
        self.checks = {}
        self.roots = 0

    def event(self, phase, name):
        if self.journal is not None:
            self.journal(phase, {"stage": name, "phase": phase})
        if phase == "after":
            self.operations += 1

    def check(self, name, predicate):
        assert name not in self.checks
        self.checks[name] = bool(predicate)
        if not predicate:
            raise ValueError(name)

    def root80(self, q):
        """Integer bisection with a fixed80-bit output grid; no math.isqrt/sqrt."""
        self.event("before", "root80:" + str(self.roots))
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
        self.event("after", "root80:" + str(self.roots))
        self.roots += 1
        return lower, upper

    def operate(self, op, a, b=None):
        stage = "interval:" + str(self.operations)
        self.event("before", stage)
        if op == "sqrt":
            result = self.root80(a[0])[0], self.root80(a[1])[1]
            self.event("after", stage)
            return result
        if op == "add":
            result = a[0] + b[0], a[1] + b[1]
            self.event("after", stage)
            return result
        if op == "sub":
            result = a[0] - b[1], a[1] - b[0]
            self.event("after", stage)
            return result
        if op == "div":
            if b[0] <= 0 <= b[1]:
                raise _Undecided("nonzero denominator premise unresolved")
            candidates = [x / y for x in a for y in b]
        else:
            candidates = [x * y for x in a for y in b]
        result = min(candidates), max(candidates)
        self.event("after", stage)
        return result

    def upward(self, name, raw, exact):
        self.event("before", "upward:" + name)
        value = _hex(raw)
        self.check(name + "_finite_normal", _normal_or_zero(value) and not (exact and value == 0))
        self.check(name + "_directed", Fraction(value) >= exact)
        self.check(
            name + "_minimal",
            exact == 0 and value == 0 or Fraction(math.nextafter(value, -math.inf)) < exact,
        )
        self.event("after", "upward:" + name)
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
    check("bounded_trace", isinstance(trace, list) and len(trace) <= 256)
    cursor = 0

    def step(stage, op, inputs, intended, leaf=None):
        nonlocal cursor
        proof.event("before", "RN:" + stage)
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
        proof.after_details[stage] = {
            "scalar_trace": {
                "stage": stage,
                "op": op,
                "operand_hex": [x.hex() for x in inputs],
                "result_hex": value.hex(),
                "intended_lower": str(intended[0]),
                "intended_upper": str(intended[1]),
            }
        }
        cursor += 1
        proof.event("after", "RN:" + stage)
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
                proof.after_details[f"residual_exact:{i}:{j}"] = {
                    "exact_sum": str(rational),
                    "target_sum": [str(x) for x in real_sum],
                }
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
            proof.after_details["residual_exact_final:" + str(i)] = {
                "r_arrays": str(exact_residual[-1]),
                "intended_residual": [str(x) for x in true_residual[-1]],
            }
    except _Undecided as exc:
        proof.event("failure", "expected-sign-stop")
        check("prescribed_status", EXPECTED[identifier] == result["status"] == "STOP_SIGN")
        check("full_stop_prefix", len(trace) == cursor)
        check("failure_stage", result["failure_stage"] == "node:" + str(index))
        check("reason", result["reason"] == str(exc))
        check(
            "no_invented_post_stop",
            all(result[k] is None for k in ("arrays", "square_uppers", "bounds")),
        )
        _journal_proof(fixture, result, proof)
        return
    except _Stop as exc:
        check("prescribed_status", EXPECTED[identifier] == result["status"] == "STOP_ARITHMETIC")
        check("full_stop_prefix", len(trace) == cursor)
        check("failure_stage", result["failure_stage"] == exc.stage)
        check("reason", result["reason"] == exc.reason)
        check(
            "no_invented_post_stop",
            all(result[k] is None for k in ("arrays", "square_uppers", "bounds")),
        )
        _journal_proof(fixture, result, proof)
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
        intended_residual_intervals=[[str(x) for x in interval] for interval in true_residual],
    )
    check("ALL_exact_actual_arrays", result["arrays"] == expected_arrays)
    proof.event("before", "exact-squared-errors")
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
    proof.event("after", "exact-squared-errors")
    proof.after_details["exact_errors"] = {"squares": {k: str(v) for k, v in squares.items()}}
    upper = {}
    for name in NORMS:
        q = _rational(result["square_uppers"][name])
        check(name + "_independent_square", q == squares[name] and q >= 0)
        root = proof.root80(q)[1]
        upper[name] = proof.upward(name, result["bounds"][name], root)
        check(name + "_norm_bound", upper[name] ** 2 >= q)
        proof.after_details["norm:" + name] = {
            "square": str(q),
            "sqrt_upper": str(root),
            "result_hex": _hex(result["bounds"][name]).hex(),
        }
    for name, target in [
        ("q_eval", upper["q_hat"] + upper["beta_eval"]),
        ("operator_solution", upper["beta_K"] * upper["u_plus"]),
    ]:
        upper[name] = proof.upward(name, result["bounds"][name], target)
        proof.after_details["bound:" + name] = {
            "exact_transfer": str(target),
            "result_hex": _hex(result["bounds"][name]).hex(),
        }
    upper["with_operator"] = proof.upward(
        "with_operator",
        result["bounds"]["with_operator"],
        upper["q_eval"] + upper["operator_solution"],
    )
    upper["r_plus"] = proof.upward(
        "r_plus", result["bounds"]["r_plus"], upper["with_operator"] + upper["beta_f"]
    )
    for name, target in [
        ("with_operator", upper["q_eval"] + upper["operator_solution"]),
        ("r_plus", upper["with_operator"] + upper["beta_f"]),
    ]:
        proof.after_details["bound:" + name] = {
            "exact_transfer": str(target),
            "result_hex": _hex(result["bounds"][name]).hex(),
        }
    check(
        "all_terms_retained",
        upper["r_plus"]
        >= upper["q_hat"]
        + upper["beta_eval"]
        + upper["beta_K"] * upper["u_plus"]
        + upper["beta_f"],
    )
    _journal_proof(fixture, result, proof)


def _journal_proof(fixture, result, proof):
    """Verify complete candidate operation order without importing its code."""
    proof.event("before", "candidate-journal-proof")
    rows = result["operations"]
    proof.check("bounded_operation_journal", isinstance(rows, list) and len(rows) <= 600)
    active = None
    before_stages, after_stages = [], []
    for index, row in enumerate(rows):
        proof.check(
            "closed_journal_" + str(index),
            isinstance(row, dict) and set(row) == {"phase", "stage", "details"},
        )
        phase, stage = row["phase"], row["stage"]
        proof.check("journal_details_type_" + str(index), isinstance(row["details"], dict))
        if phase == "before":
            proof.check("journal_before_order_" + str(index), active is None)
            active = stage
            before_stages.append(stage)
            if stage.startswith("node:"):
                op = fixture["nodes"][int(stage.split(":")[1])]["op"]
            elif stage.startswith(("G:", "K:", "f:", "residual_sum:")):
                op = "add"
            elif stage.startswith("residual_mul:"):
                op = "mul"
            elif stage.startswith("residual_sub:"):
                op = "sub"
            elif stage.startswith(("residual_exact:", "residual_exact_final:")):
                op = "exact-residual-bookkeeping"
            elif stage == "exact_errors":
                op = "exact-squared-errors"
            elif stage.startswith("norm:"):
                op = "sqrt80-up"
            else:
                op = "mul-up" if stage == "bound:operator_solution" else "add-up"
            proof.check("closed_before_details_" + str(index), row["details"] == {"op": op})
        elif phase == "after":
            proof.check("journal_after_order_" + str(index), active == stage)
            active = None
            after_stages.append(stage)
            proof.check(
                "ALL_independent_after_details_" + str(index),
                row["details"] == proof.after_details[stage],
            )
        else:
            proof.check(
                "journal_failure_" + str(index),
                phase == "failure"
                and index == len(rows) - 1
                and stage == result["failure_stage"]
                and row["details"] == {"status": result["status"], "reason": result["reason"]},
            )
            active = None
    expected = ["node:" + str(i) for i in range(len(fixture["nodes"]))]
    n = len(fixture["u_bits"])
    for name in ("G", "K", "f"):
        for i in range(n):
            for j in range(1 if name == "f" else n):
                for k in range(len(fixture[name + "_terms"])):
                    expected.append(f"{name}:{i}:{j}:{k}")
    for i in range(n):
        for j in range(n):
            expected.extend(
                [f"residual_mul:{i}:{j}", f"residual_sum:{i}:{j}", f"residual_exact:{i}:{j}"]
            )
        expected.extend([f"residual_sub:{i}", f"residual_exact_final:{i}"])
    expected += (
        ["exact_errors"]
        + ["norm:" + name for name in NORMS]
        + ["bound:" + name for name in STAGES[len(NORMS) :]]
    )
    if result["status"] == "PASS":
        proof.check("ALL_before_after_stages", before_stages == after_stages == expected)
    else:
        end = expected.index(result["failure_stage"]) + 1
        proof.check("ALL_stop_stages", before_stages == expected[:end])
        scalar_failed_completed = result["status"] == "STOP_ARITHMETIC" and result[
            "failure_stage"
        ] in [t["stage"] for t in result["trace"]]
        proof.check(
            "stop_after_stages",
            after_stages == expected[: end if scalar_failed_completed else end - 1],
        )
    proof.check("no_pending_operation_after_known_stop", active is None)
    proof.event("after", "candidate-journal-proof")


def audit_case(fixture, result, journal=None):
    """Independent exact predicates reject malformed/tampered results explicitly."""
    proof = _Proof(journal)
    try:
        _audit(fixture, result, proof)
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError, OverflowError) as exc:
        proof.event("failure", "audit_failed")
        proof.checks["audit_completed"] = False
        return {
            "passed": False,
            "checks": proof.checks,
            "error": type(exc).__name__ + ": " + str(exc),
        }
    proof.checks["audit_completed"] = True
    return {
        "passed": all(proof.checks.values()),
        "checks": proof.checks,
        "error": "",
        "RN_even_proofs": sum(k.startswith("RN_even_operation_") for k in proof.checks),
        "proof_operations_completed": proof.operations,
    }
