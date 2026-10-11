"""Independent B4.41 exact interval/IEEE audit; no candidate imports or path IO."""

import hashlib
import json
import math
import struct
from fractions import Fraction

RESULT_FIELDS = {
    "fixture_id",
    "status",
    "trace",
    "failure_node",
    "reason",
    "A_hat",
    "square_uppers",
    "bounds",
    "squares_are_upper_enclosures",
    "public_intended_only",
    "diagnostic_only",
    "real_fem_certified",
    "PSD_or_coercivity_certified",
}
TRACE_FIELDS = {"node", "op", "operand_hex", "result_hex", "intended_lower", "intended_upper"}
NORMS = ("e", "a", "d0", "d1", "complete")
STAGES = (*NORMS, "cross", "square", "change", "delta")
EXPECTED = {
    "exact-dyadic": "PASS",
    "accepted-bit-division": "PASS",
    "irrational-sqrt-two": "PASS",
    "inverse-sqrt-three": "PASS",
    "coupled-irrational": "PASS",
    "positive-structural-error": "PASS",
    "negative-structural-error": "PASS",
    "rounded-cancellation-retained": "PASS",
    "inconclusive-radicand-stop": "STOP_SIGN",
    "inconclusive-denominator-stop": "STOP_SIGN",
    "binary64-overflow-stop": "STOP_ARITHMETIC",
    "binary64-underflow-stop": "STOP_ARITHMETIC",
}
FINGERPRINTS = {
    "exact-dyadic": "83b9fe55e40e01d480a9698e8eb896dce3e15ac5b139935f827e80b83ad01661",
    "accepted-bit-division": "42ae28e927b7c5853b5fd2195caf81120581c66a833d2ea2f0447d424721cd76",
    "irrational-sqrt-two": "73083c1ca9cfacf62f3ca9257fe303e96e2312e1aca4f89a929bd8980ec31cce",
    "inverse-sqrt-three": "b34f383ba8c65444fe11056d038546d387c90a614d71b0a58b2967a87ba81706",
    "coupled-irrational": "4f362cc76b9b8b34366d897548629ff9d4285ba81e37d251bcce3761f292971c",
    "positive-structural-error": "754f4007b3f3816c5b2b8e2b3f5ee8a8b29d14fbcfa5dc58e613805bd922456f",
    "negative-structural-error": "59198ca1916278891d0329687ebf63973fe3c5fafc81203a836cbc7374fd197d",
    "rounded-cancellation-retained": (
        "3da78ffa0108859b6616d44eccf242c4d9e4d154c1d2439f4f8793a197efbc0a"
    ),
    "inconclusive-radicand-stop": (
        "5ffe43afec0c8a0b6609dbf75ad16f77e0d3d6fc1030c233d29bdd0ec2d7c9e2"
    ),
    "inconclusive-denominator-stop": (
        "ce6eb16db340b194fbbe5c075183693facf74ee764dcb7f4aca492b9c5c45cff"
    ),
    "binary64-overflow-stop": "45f1d8ae8ad0b6cfb527949e012217a2ea3f7719329e80d5716fff6acd8f772e",
    "binary64-underflow-stop": "7919773ee688b06ed0248b9c42683c9524f694f8f6fcc5b7e34127bf4fe53619",
}


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
    ]:
        check(name, type(result[name]) is bool and result[name] is expected)
    trace = result["trace"]
    check("bounded_trace", isinstance(trace, list) and len(trace) <= 64)
    intervals, values = [], []
    stop = None
    for index, node in enumerate(fixture["nodes"]):
        op = node["op"]
        operands = [values[i] for i in node.get("args", [])]
        try:
            if op in ("integer", "bits"):
                raw_value = (
                    float(node["value"])
                    if op == "integer"
                    else struct.unpack(">d", bytes.fromhex(node["value"]))[0]
                )
                intended = Fraction(raw_value)
                interval = intended, intended
            else:
                roots = [intervals[i] for i in node["args"]]
                interval = proof.operate(op, roots[0], None if op == "sqrt" else roots[1])
        except _Undecided as exc:
            stop = ("STOP_SIGN", index, str(exc))
            break
        step = trace[index]
        check("closed_step_" + str(index), isinstance(step, dict) and set(step) == TRACE_FIELDS)
        check(
            "ordered_operands_" + str(index),
            type(step["node"]) is int
            and step["node"] == index
            and step["op"] == op
            and step["operand_hex"] == [x.hex() for x in operands],
        )
        check(
            "intended_interval_" + str(index),
            (_rational(step["intended_lower"]), _rational(step["intended_upper"])) == interval,
        )
        value = _hex(step["result_hex"])
        if op in ("integer", "bits"):
            exact = intended
            nearest = value.hex() == raw_value.hex()
        elif op == "sqrt":
            exact = Fraction(operands[0])
            nearest = _rn(exact, value, True)
        else:
            left, right = map(Fraction, operands)
            if op == "add":
                exact = left + right
            elif op == "sub":
                exact = left - right
            elif op == "mul":
                exact = left * right
            else:
                exact = left / right
            nearest = _rn(exact, value)
        if value == 0 and op not in ("integer", "bits"):
            nearest = nearest and math.copysign(1, value) == _zero_sign(op, operands, exact)
        check("RN_even_node_" + str(index), nearest)
        if not _normal_or_zero(value) or (exact and value == 0):
            stop = ("STOP_ARITHMETIC", index, "represented range failure")
            break
        intervals.append(interval)
        values.append(value)
    check("prescribed_status", result["status"] == EXPECTED[identifier])
    if stop:
        check("complete_stop_prefix", len(trace) == stop[1] + (stop[0] == "STOP_ARITHMETIC"))
        check(
            "failed_node", type(result["failure_node"]) is int and result["failure_node"] == stop[1]
        )
        check("stopping_premise", (result["status"], result["reason"]) == (stop[0], stop[2]))
        check(
            "no_invented_post_stop_values",
            all(result[k] is None for k in ("A_hat", "square_uppers", "bounds")),
        )
        return
    check("complete_program", len(trace) == len(fixture["nodes"]))
    check("no_failure", result["failure_node"] is None and result["reason"] == "")
    a = [[values[root] for root in row] for row in fixture["A0"]]
    check("same_represented_factor", result["A_hat"] == [[x.hex() for x in row] for row in a])
    squared = {
        "e": _square(
            [
                proof.operate("sub", intervals[root], (Fraction(x), Fraction(x)))
                for row, numbers in zip(fixture["A0"], a, strict=True)
                for root, x in zip(row, numbers, strict=True)
            ]
        ),
        "a": sum((Fraction(x) ** 2 for row in a for x in row), Fraction(0)),
    }
    parts = {"d0": [], "d1": [], "complete": []}
    n = len(fixture["G"])
    for col in range(n):
        for row in range(n):
            true_gram = Fraction(0), Fraction(0)
            float_gram = Fraction(0)
            for k, roots in enumerate(fixture["A0"]):
                true_gram = proof.operate(
                    "add",
                    true_gram,
                    proof.operate("mul", intervals[roots[row]], intervals[roots[col]]),
                )
                float_gram += Fraction(a[k][row]) * Fraction(a[k][col])
            target = intervals[fixture["G"][row][col]]
            parts["d0"].append(proof.operate("sub", target, true_gram))
            parts["d1"].append(proof.operate("sub", true_gram, (float_gram, float_gram)))
            parts["complete"].append(proof.operate("sub", target, (float_gram, float_gram)))
    squared.update({key: _square(entries) for key, entries in parts.items()})
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
        check(name + "_independent_squared_enclosure", q == squared[name] and q >= 0)
        high = proof.root80(q)[1]
        upper[name] = proof.upward(name, result["bounds"][name], high)
        check(name + "_norm_bound", upper[name] ** 2 >= q)
    targets = {"cross": 2 * upper["a"] * upper["e"], "square": upper["e"] ** 2}
    for name, target in targets.items():
        upper[name] = proof.upward(name, result["bounds"][name], target)
    upper["change"] = proof.upward(
        "change", result["bounds"]["change"], upper["cross"] + upper["square"]
    )
    upper["delta"] = proof.upward("delta", result["bounds"]["delta"], upper["d0"] + upper["change"])
    check(
        "gram_expansion_bound",
        upper["delta"] >= upper["d0"] + 2 * upper["a"] * upper["e"] + upper["e"] ** 2,
    )


def audit_case(fixture, result):
    """Return explicit failed predicates on every malformed or tampered receipt."""
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
