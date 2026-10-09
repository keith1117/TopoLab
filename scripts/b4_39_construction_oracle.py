"""Independent B4.39 rational/IEEE audit; no candidate imports, IO or solver."""

import math
import struct
from fractions import Fraction

RESULT_FIELDS = {
    "fixture_id",
    "status",
    "A_hat",
    "Q_transpose_hat",
    "R_hat",
    "Y_hat",
    "trace",
    "error_squares",
    "certificate",
    "error",
}
CERTIFICATE_FIELDS = {
    "delta_plus",
    "eta_plus",
    "M_plus",
    "one_minus_eta_minus",
    "ratio_minus",
    "factor_lower_minus",
    "lower_G_minus",
    "E_min_minus",
    "m_global_minus",
    "public_intended_only",
    "diagnostic_only",
    "real_fem_certified",
}
FLAGS = {"public_intended_only", "diagnostic_only", "real_fem_certified"}


def _nearest(exact, value, *, sqrt=False):
    """Prove an RN-even result by exact adjacent midpoints, not a floating residual."""
    if not math.isfinite(value):
        return False
    prior, later = math.nextafter(value, -math.inf), math.nextafter(value, math.inf)
    if not math.isfinite(prior) or not math.isfinite(later):
        return False  # These extreme endpoints are outside the fixed public panel.
    center = Fraction(value)
    lower = (Fraction(prior) + center) / 2
    upper = (center + Fraction(later)) / 2
    even = struct.unpack(">Q", struct.pack(">d", value))[0] & 1 == 0
    if sqrt:
        if exact < 0 or value < 0:
            return False
        low_ok = lower <= 0 or exact > lower**2 or (even and exact == lower**2)
        high_ok = exact < upper**2 or (even and exact == upper**2)
    else:
        low_ok = exact > lower or (even and exact == lower)
        high_ok = exact < upper or (even and exact == upper)
    return low_ok and high_ok


class _TraceAudit:
    def __init__(self, trace):
        if not isinstance(trace, (tuple, list)) or len(trace) > 1024:
            raise ValueError("closed bounded trace required")
        self.trace = trace
        self.cursor = 0
        self.checks = {}

    def step(self, kind, left, right=None):
        entry = self.trace[self.cursor]
        if not isinstance(entry, dict) or set(entry) != {"op", "left", "right", "result"}:
            raise ValueError("closed operation required")
        lhs = str(left) if type(left) is Fraction else left.hex()
        rhs = "" if right is None else right.hex()
        if (entry["op"], entry["left"], entry["right"]) != (kind, lhs, rhs):
            raise ValueError("fixed operation order or operands differ")
        value = float.fromhex(entry["result"])
        a = Fraction(left)
        if kind in ("round", "sqrt"):
            exact = a
        elif kind == "neg":
            exact = -a
        elif kind == "add":
            exact = a + Fraction(right)
        elif kind == "sub":
            exact = a - Fraction(right)
        elif kind == "mul":
            exact = a * Fraction(right)
        elif kind == "div":
            exact = a / Fraction(right)
        else:
            raise ValueError("unknown operation")
        ok = _nearest(exact, value, sqrt=kind == "sqrt")
        if kind == "neg":
            ok = ok and value.hex() == (-left).hex()
        if value == 0:
            if kind in ("mul", "div"):
                sign = math.copysign(1, left) * math.copysign(1, right)
            elif kind == "round" or kind == "sqrt":
                sign = -1 if exact < 0 else 1
            elif kind == "neg":
                sign = -math.copysign(1, left)
            elif exact != 0:
                sign = -1 if exact < 0 else 1
            else:
                effective_right = -right if kind == "sub" else right
                sign = (
                    -1
                    if left == effective_right == 0
                    and (math.copysign(1, left) == math.copysign(1, effective_right) == -1)
                    else 1
                )
            ok = ok and math.copysign(1, value) == sign
        self.checks["RN_even_operation_" + str(self.cursor)] = bool(ok)
        self.cursor += 1
        if not ok:
            raise ValueError("operation fails exact RN-even midpoint certificate")
        return value


def _reconstruct(stack, trace):
    """Independent fixed-program replay using certified recorded values, no float sqrt."""
    proof = _TraceAudit(trace)
    operate = proof.step
    a = [[operate("round", Fraction(entry)) for entry in row] for row in stack]
    height, width = len(a), len(a[0])
    reduced = [row[:] for row in a]
    transforms = [[float(row == col) for col in range(height)] for row in range(height)]
    stop = None
    triangular = inverse = thin = None
    for col in range(width):
        entries = [reduced[row][col] for row in range(col, height)]
        norm_square = 0.0
        for entry in entries:
            product = operate("mul", entry, entry)
            norm_square = operate("add", norm_square, product)
        length = operate("sqrt", norm_square)
        if length == 0:
            stop = "STOP_CONSTRUCTION"
            break
        signed = math.copysign(length, entries[0])
        reflection = operate("neg", signed)
        entries[0] = operate("sub", entries[0], reflection)
        divisor = 0.0
        for entry in entries:
            product = operate("mul", entry, entry)
            divisor = operate("add", divisor, product)
        if divisor == 0:
            stop = "STOP_CONSTRUCTION"
            break
        multiplier = operate("div", 2.0, divisor)
        for matrix, begin, end in ((reduced, col, width), (transforms, 0, height)):
            for other in range(begin, end):
                inner = 0.0
                for index, entry in enumerate(entries, col):
                    product = operate("mul", entry, matrix[index][other])
                    inner = operate("add", inner, product)
                coefficient = operate("mul", multiplier, inner)
                for index, entry in enumerate(entries, col):
                    correction = operate("mul", entry, coefficient)
                    matrix[index][other] = operate("sub", matrix[index][other], correction)
    if stop is None:
        triangular = [
            [reduced[row][col] if row <= col else 0.0 for col in range(width)]
            for row in range(width)
        ]
        thin = transforms[:width]
        for row in range(width):
            if triangular[row][row] == 0:
                stop = "STOP_CONSTRUCTION"
                break
            if triangular[row][row] < 0:
                triangular[row] = [operate("neg", entry) for entry in triangular[row]]
                thin[row] = [operate("neg", entry) for entry in thin[row]]
        if stop is None:
            inverse = [[0.0 for _ in range(height)] for _ in range(width)]
            for col in range(height):
                for row in range(width - 1, -1, -1):
                    correction = 0.0
                    for other in range(row + 1, width):
                        product = operate("mul", triangular[row][other], inverse[other][col])
                        correction = operate("add", correction, product)
                    numerator = operate("sub", thin[row][col], correction)
                    inverse[row][col] = operate("div", numerator, triangular[row][row])
    if proof.cursor != len(trace):
        raise ValueError("extra operations after fixed construction or stop")
    return a, thin, triangular, inverse, stop, proof.checks


def _principal(matrix):
    n = len(matrix)
    return (
        all(matrix[i][j] == matrix[j][i] for i in range(n) for j in range(n))
        and all(matrix[i][i] >= 0 for i in range(n))
        and (n == 1 or matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0] >= 0)
    )


def _gram(rows):
    columns = list(zip(*rows, strict=True))
    return [
        [sum((a * b for a, b in zip(x, y, strict=True)), Fraction(0)) for y in columns]
        for x in columns
    ]


def _same_matrix(recorded, expected):
    if recorded is None or expected is None:
        return recorded is expected
    return (
        isinstance(recorded, (list, tuple))
        and len(recorded) == len(expected)
        and all(
            isinstance(x, (list, tuple))
            and len(x) == len(y)
            and all(type(a) is float and a.hex() == b.hex() for a, b in zip(x, y, strict=True))
            for x, y in zip(recorded, expected, strict=True)
        )
    )


def _grid_ceiling(q):
    # Independent integer binary search, rather than candidate math.isqrt.
    grid = 2**80
    target = q.numerator * grid * grid // q.denominator
    lo, hi = 0, 2 ** ((target.bit_length() + 1) // 2 + 1)
    while hi - lo > 1:
        mid = (hi + lo) // 2
        if mid * mid <= target:
            lo = mid
        else:
            hi = mid
    floor = Fraction(lo, grid)
    return floor if floor * floor == q else Fraction(lo + 1, grid)


def _directed(value, exact, *, upper):
    if type(value) is not float or not math.isfinite(value):
        return False
    q = Fraction(value)
    neighbor = math.nextafter(value, -math.inf if upper else math.inf)
    return (
        (q >= exact and Fraction(neighbor) < exact)
        if upper
        else (q <= exact and Fraction(neighbor) > exact)
    )


def audit_case(raw, result):
    """Independently certify the complete construction/error/bound or exact stop."""
    checks = {"closed_result_schema": isinstance(result, dict) and set(result) == RESULT_FIELDS}
    ref = {}
    if not checks["closed_result_schema"]:
        return checks, ref
    checks["same_public_identity"] = result["fixture_id"] == raw["id"]
    checks["same_public_space"] = (
        raw["free_space"] == raw["stack_space"] == "public-free-space:" + raw["id"]
        and raw["dirichlet"] == "homogeneous-zero"
    )
    elements = [[[Fraction(x) for x in row] for row in k] for k in raw["unit_matrices"]]
    n = len(elements[0])
    g = [[sum((k[i][j] for k in elements), Fraction(0)) for j in range(n)] for i in range(n)]
    psd = all(_principal(k) for k in elements)
    ref.update(G=g, element_psd=psd)
    if not psd:
        checks["PSD_stop_before_construction"] = (
            result["status"] == "STOP_PSD"
            and result["trace"] in ([], ())
            and all(
                result[k] is None
                for k in (
                    "A_hat",
                    "Q_transpose_hat",
                    "R_hat",
                    "Y_hat",
                    "error_squares",
                    "certificate",
                )
            )
            and isinstance(result["error"], str)
            and result["error"].startswith("STOP_PSD:")
        )
        checks["summed_G_positive_does_not_replace_element_PSD"] = _principal(g) and (
            g[0][0] > 0 and (n == 1 or g[0][0] * g[1][1] > g[0][1] ** 2)
        )
        ref["exact_disposition"] = "STOP_PSD"
        return checks, ref
    try:
        a, qt, r, y, stop, arithmetic = _reconstruct(raw["intended_stack"], result["trace"])
        checks.update(arithmetic)
        checks["fixed_trace_complete"] = True
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, ZeroDivisionError):
        checks["fixed_trace_complete"] = False
        return checks, ref
    for key, expected in zip(
        ("A_hat", "Q_transpose_hat", "R_hat", "Y_hat"), (a, qt, r, y), strict=True
    ):
        checks["same_constructed_" + key] = _same_matrix(result[key], expected)
    if stop:
        checks["zero_pivot_stop_preserves_partial_trace"] = (
            result["status"] == stop
            and result["certificate"] is result["error_squares"] is None
            and isinstance(result["error"], str)
            and result["error"].startswith(stop + ":")
        )
        ref["exact_disposition"] = stop
        return checks, ref
    a0 = [[Fraction(x) for x in row] for row in raw["intended_stack"]]
    ga0 = _gram(a0)
    ga = _gram([[Fraction(x) for x in row] for row in a])
    ya = [
        [
            sum((Fraction(x) * Fraction(z) for x, z in zip(row, col, strict=True)), Fraction(0))
            for col in zip(*a, strict=True)
        ]
        for row in y
    ]
    differences = {
        "intended_to_stack": [g[i][j] - ga0[i][j] for i in range(n) for j in range(n)],
        "stack_to_represented": [ga0[i][j] - ga[i][j] for i in range(n) for j in range(n)],
        "complete_operator": [g[i][j] - ga[i][j] for i in range(n) for j in range(n)],
        "left_residual": [Fraction(i == j) - ya[i][j] for i in range(n) for j in range(n)],
        "witness": [Fraction(x) for row in y for x in row],
    }
    squares = {
        key: sum((x * x for x in values), Fraction(0)) for key, values in differences.items()
    }
    ref.update(error_squares=squares)
    entries = result["error_squares"]
    checks["closed_error_components"] = isinstance(entries, (tuple, list)) and len(entries) == 5
    if checks["closed_error_components"]:
        try:
            received = {key: Fraction(value) for key, value in entries}
            checks["all_intended_error_components_exact"] = (
                received == squares and len(received) == 5
            )
        except (ValueError, TypeError):
            checks["all_intended_error_components_exact"] = False
    stop_bound = squares["witness"] > 0 and (
        squares["complete_operator"] >= (1 / squares["witness"]) ** 2
    )
    disposition = "STOP_COERCIVITY" if stop_bound else "PASS"
    ref["exact_disposition"] = disposition
    checks["independent_disposition"] = result["status"] == disposition
    if stop_bound:
        checks["conservative_stop_not_singularity"] = (
            g[0][0] > 0 and g[1][1] > 0 and g[0][0] * g[1][1] > g[0][1] ** 2
        )
        checks["bound_stop_retains_error_no_certificate"] = (
            result["certificate"] is None
            and isinstance(result["error"], str)
            and result["error"].startswith("STOP_COERCIVITY:")
        )
        return checks, ref
    c = result["certificate"]
    checks["closed_certificate_schema"] = isinstance(c, dict) and set(c) == CERTIFICATE_FIELDS
    if not checks["closed_certificate_schema"]:
        return checks, ref
    numeric = CERTIFICATE_FIELDS - FLAGS
    checks["finite_binary64_endpoints"] = all(
        type(c[k]) is float and math.isfinite(c[k]) for k in numeric
    )
    if not checks["finite_binary64_endpoints"]:
        return checks, ref
    q = {key: Fraction(c[key]) for key in numeric}
    checks["intended_element_PSD_separate"] = psd
    for field, square in (
        ("delta_plus", "complete_operator"),
        ("eta_plus", "left_residual"),
        ("M_plus", "witness"),
    ):
        checks[field + "_fixed80_outward"] = _directed(
            c[field], _grid_ceiling(squares[square]), upper=True
        )
        checks[field + "_exact_norm_upper"] = q[field] >= 0 and q[field] ** 2 >= squares[square]
    checks["strict_eta_and_M"] = 0 <= q["eta_plus"] < 1 and q["M_plus"] > 0
    if not checks["strict_eta_and_M"]:
        return checks, ref
    for field, exact in (
        ("one_minus_eta_minus", 1 - q["eta_plus"]),
        ("ratio_minus", q["one_minus_eta_minus"] / q["M_plus"]),
        ("factor_lower_minus", q["ratio_minus"] ** 2),
        ("lower_G_minus", q["factor_lower_minus"] - q["delta_plus"]),
        ("E_min_minus", Fraction(1, 1000)),
        ("m_global_minus", q["E_min_minus"] * q["lower_G_minus"]),
    ):
        checks[field + "_strict_directed_lower"] = q[field] > 0 and _directed(
            c[field], exact, upper=False
        )
    shifted = [
        [g[i][j] - (q["lower_G_minus"] if i == j else 0) for j in range(n)] for i in range(n)
    ]
    checks["SAME_intended_G_lower_bound_PSD"] = _principal(shifted)
    checks["diagnostic_public_only_no_real_certificate"] = (
        c["public_intended_only"] is True
        and c["diagnostic_only"] is True
        and c["real_fem_certified"] is False
        and result["error"] is None
    )
    return checks, ref
