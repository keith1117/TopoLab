"""Independent B4.49 exact proof; no candidate, producer, TopoLab or shared import."""

import math
import struct
from fractions import Fraction


class _RangeStop(Exception):
    pass


class Proof:
    def __init__(self, result, journal=None):
        self.result = result
        self.journal = journal
        self.position = 0
        self.predicates = 0
        self.rn_proofs = 0
        self.root_proofs = 0
        self.seen_bounds = set()
        self.seen_squares = set()

    def check(self, condition, label):
        self.predicates += 1
        if not condition:
            raise ValueError("independent proof failed: " + label)

    def start(self, stage):
        if self.journal:
            self.journal("before", {"stage": stage, "kind": "independent-proof"})

    def end(self, stage):
        if self.journal:
            self.journal("after", {"stage": stage, "predicates": self.predicates})

    def row(self, stage, mode):
        self.check(self.position < len(self.result["trace"]), "complete trace prefix")
        value = self.result["trace"][self.position]
        self.position += 1
        self.check(value["stage"] == stage and value["mode"] == mode, "fixed trace order")
        return value

    def rounded(self, stage, exact, mode="up"):
        self.start(stage)
        row = self.row(stage, mode)
        self.check(
            set(row) == {"stage", "mode", "exact", "nearest_hex", "result_hex", "accepted"},
            "closed round fields",
        )
        self.check(row["exact"] == str(exact), "independently reconstructed exact operation")
        nearest = float.fromhex(row["nearest_hex"])
        self.check(nearest.hex() == row["nearest_hex"], "canonical nearest")
        if math.isinf(nearest):
            threshold = Fraction(2**1024 - 2**970)
            valid_rn = exact >= threshold if nearest > 0 else exact <= -threshold
        else:
            self.check(math.isfinite(nearest), "finite nearest or proven infinity")
            previous, following = (
                math.nextafter(nearest, -math.inf),
                math.nextafter(nearest, math.inf),
            )
            low = (
                (Fraction(previous) + Fraction(nearest)) / 2
                if math.isfinite(previous)
                else -Fraction(2**1024 - 2**970)
            )
            high = (
                (Fraction(following) + Fraction(nearest)) / 2
                if math.isfinite(following)
                else Fraction(2**1024 - 2**970)
            )
            even = (struct.unpack(">Q", struct.pack(">d", nearest))[0] & 1) == 0
            valid_rn = (exact > low or (even and exact == low)) and (
                exact < high or (even and exact == high)
            )
            if exact == 0:
                self.check(row["nearest_hex"] == "0x0.0p+0", "registered zero sign")
        self.check(valid_rn, "independent adjacent midpoint RN-even proof")
        self.rn_proofs += 1
        value = nearest
        if math.isfinite(value):
            if mode == "up" and Fraction(value) < exact:
                value = math.nextafter(value, math.inf)
            elif mode == "down" and Fraction(value) > exact:
                value = math.nextafter(value, -math.inf)
        self.check(row["result_hex"] == value.hex(), "minimal directed represented result")
        accepted = math.isfinite(value) and (value == 0 or abs(value) >= 2.0**-1022)
        accepted = bool(accepted and not (exact and value == 0))
        self.check(
            type(row["accepted"]) is bool and row["accepted"] == accepted, "executed versus domain"
        )
        if accepted:
            self.check(self.result["bounds"][stage] == value.hex(), "retained round field")
            self.seen_bounds.add(stage)
        else:
            self.check(stage not in self.result["bounds"], "failed raw result never accepted bound")
        self.end(stage)
        if not accepted:
            raise _RangeStop(stage)
        return Fraction(value)

    def root(self, stage, square, upper=True):
        self.start(stage + ":grid")
        row = self.row(stage + ":grid", "fixed80")
        self.check(set(row) == {"stage", "mode", "exact", "lower", "upper"}, "closed grid fields")
        self.check(row["exact"] == str(square) and square >= 0, "root square reconstructed")
        scaled_numerator = square.numerator << 160
        denominator = square.denominator
        low, high = 0, 1 << ((scaled_numerator.bit_length() + 1) // 2 + 1)
        while low + 1 < high:
            middle = (low + high) // 2
            if middle * middle * denominator <= scaled_numerator:
                low = middle
            else:
                high = middle
        left = Fraction(low, 1 << 80)
        right = left if left * left == square else Fraction(low + 1, 1 << 80)
        self.check(left * left <= square <= right * right, "independent squared endpoints")
        self.check(left == right or right - left == Fraction(1, 1 << 80), "fixed grid adjacency")
        self.check(row["lower"] == str(left) and row["upper"] == str(right), "grid result identity")
        self.root_proofs += 1
        self.end(stage + ":grid")
        return self.rounded(stage, right if upper else left, "up" if upper else "down")

    def norm(self, stage, values):
        self.start(stage + ":squared")
        square = sum((v**2 for v in values), Fraction(0))
        self.check(
            self.result["square_uppers"][stage] == str(square), "complete independent norm square"
        )
        self.seen_squares.add(stage)
        self.end(stage + ":squared")
        return self.root(stage, square)


def _dot(left, right):
    answer = Fraction(0)
    for x, y in zip(left, right, strict=True):
        answer += x * y
    return answer


def _matrix_psd(matrix):
    if len(matrix) == 1:
        return matrix[0][0] >= 0
    a, b = matrix[0]
    c, d = matrix[1]
    return b == c and a >= 0 and d >= 0 and a * d - b * c >= 0


def _solve_energy(matrix, force):
    if len(force) == 1:
        return force[0] ** 2 / matrix[0][0]
    a, b = matrix[0]
    c, d = matrix[1]
    determinant = a * d - b * c
    solution = [
        (d * force[0] - b * force[1]) / determinant,
        (a * force[1] - c * force[0]) / determinant,
    ]
    return _dot(force, solution)


def audit(fixture, result, expected_status, journal=None):
    p = Proof(result, journal)
    p.start("closed-result-and-input")
    basic = {
        "id",
        "status",
        "trace",
        "arrays",
        "square_uppers",
        "bounds",
        "diagnostic_only",
        "public_intended_only",
        "real_fem_certified",
        "loss_gradient_changed",
        "unmodified_U_certified",
        "failure_stage",
        "reason",
        "public_coercivity_certified",
    }
    p.check(
        set(result) == basic | ({"beta_G_retained"} if result["status"] == "PASS" else set()),
        "closed result schema",
    )
    p.check(result["id"] == fixture["id"], "case identity")
    p.check(
        result["diagnostic_only"] is True
        and result["public_intended_only"] is True
        and result["real_fem_certified"] is False
        and result["loss_gradient_changed"] is False,
        "immutable scope flags",
    )
    p.check(len(result["trace"]) <= 400, "frozen trace cap")
    p.end("closed-result-and-input")
    status, arrays = "PASS", {}
    normalizer = fixture["normalizer"]
    try:
        if normalizer["force_id"] != fixture["force_id"] or normalizer["space"] != fixture["space"]:
            status = "STOP_NORMALIZER_IDENTITY"
            raise _RangeStop("identity")
        elements = [[[Fraction(v) for v in row] for row in x] for x in fixture["elements"]]
        p.start("independent-element-minors")
        psd = all(_matrix_psd(x) for x in elements)
        p.check(type(psd) is bool, "element PSD decision")
        p.end("independent-element-minors")
        if not psd:
            status = "STOP_PSD"
            raise _RangeStop("element-PSD")
        n = len(fixture["force"])
        p.start("independent-intended-operator-and-factor-bookkeeping")
        moduli = [
            Fraction(1, 1000) + Fraction(999, 1000) * Fraction(v) ** 3 for v in fixture["rho"]
        ]
        g = [[sum(x[i][j] for x in elements) for j in range(n)] for i in range(n)]
        kp = [
            [sum(x[i][j] * e for x, e in zip(elements, moduli, strict=True)) for j in range(n)]
            for i in range(n)
        ]
        a0 = [[Fraction(v) for v in row] for row in fixture["A0"]]

        def bits(word):
            return Fraction(struct.unpack(">d", bytes.fromhex(word))[0])

        ah = [[bits(v) for v in row] for row in fixture["A_hat_bits"]]
        y = [[bits(v) for v in row] for row in fixture["Y_bits"]]
        columns0, columnsh = list(zip(*a0, strict=True)), list(zip(*ah, strict=True))
        gram0 = [[_dot(left, right) for right in columns0] for left in columns0]
        gramh = [[_dot(left, right) for right in columnsh] for left in columnsh]

        def flatten(x):
            return [v for row in x for v in row]

        def subtract(x, z):
            return [a - b for a, b in zip(flatten(x), flatten(z), strict=True)]

        factor_errors = {
            "d0_plus": subtract(g, gram0),
            "d1_plus": subtract(gram0, gramh),
            "complete_delta_plus": subtract(g, gramh),
            "e_plus": subtract(a0, ah),
        }
        p.end("independent-intended-operator-and-factor-bookkeeping")
        d0 = p.norm("d0_plus", factor_errors["d0_plus"])
        p.norm("d1_plus", factor_errors["d1_plus"])
        p.norm("complete_delta_plus", factor_errors["complete_delta_plus"])
        error = p.norm("e_plus", factor_errors["e_plus"])
        a = p.norm("a_plus", flatten(a0))
        cross = p.rounded("cross_plus", 2 * a * error)
        square = p.rounded("factor_square_plus", error**2)
        representation = p.rounded("representation_plus", cross + square)
        delta = p.rounded("delta_plus", d0 + representation)
        eta = p.norm(
            "eta_plus",
            [Fraction(i == j) - _dot(y[i], columnsh[j]) for i in range(n) for j in range(n)],
        )
        magnitude = p.norm("M_plus", flatten(y))
        if eta >= 1 or magnitude <= 0:
            status = "STOP_ETA"
            raise _RangeStop("eta-M")
        one = p.rounded("one_minus_eta_minus", 1 - eta, "down")
        ratio = p.rounded("ratio_minus", one / magnitude, "down")
        factor = p.rounded("factor_lower_minus", ratio**2, "down")
        lower = p.rounded("lower_G_minus", factor - delta, "down")
        if lower <= 0:
            p.check(
                _matrix_psd(g) and _solve_energy(g, [Fraction(v) for v in fixture["force"]]) > 0,
                "conservative stop remains positive intended operator",
            )
            status = "STOP_COERCIVITY"
            raise _RangeStop("positive-conservative")
        emin = p.rounded("E_min_minus", Fraction(1, 1000), "down")
        m = p.rounded("m_minus", emin * lower, "down")
        p.check(m > 0, "positive directed uniform bound")
        shifted = [[g[i][j] - (lower if i == j else 0) for j in range(n)] for i in range(n)]
        p.check(_matrix_psd(shifted), "direct intended G-lower*I PSD independent certificate")
        p.check(
            _matrix_psd([[kp[i][j] - (m if i == j else 0) for j in range(n)] for i in range(n)]),
            "direct K-m*I PSD",
        )
        actual = {}
        for label in ("G", "K_star"):
            matrix = [[Fraction(0)] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    for k, element in enumerate(elements):
                        term = p.rounded(f"{label}:entry:{i}:{j}:{k}", element[i][j], "rn")
                        if label == "K_star":
                            modulus = p.rounded(f"{label}:modulus:{i}:{j}:{k}", Fraction(1), "rn")
                            term = p.rounded(f"{label}:product:{i}:{j}:{k}", term * modulus, "rn")
                        matrix[i][j] = p.rounded(
                            f"{label}:sum:{i}:{j}:{k}", matrix[i][j] + term, "rn"
                        )
            actual[label] = matrix
        force = [Fraction(v) for v in fixture["force"]]
        fh = [p.rounded(f"force:{i}", v, "rn") for i, v in enumerate(force)]
        u = list(map(bits, fixture["u_bits"]))
        rh = []
        for i in range(n):
            total = Fraction(0)
            for j in range(n):
                term = p.rounded(f"residual:product:{i}:{j}", actual["K_star"][i][j] * u[j], "rn")
                total = p.rounded(f"residual:sum:{i}:{j}", total + term, "rn")
            rh.append(p.rounded(f"residual:subtract:{i}", total - fh[i], "rn"))
        p.start("independent-assembly-residual-error-bookkeeping")
        ra = [_dot(row, u) - f for row, f in zip(actual["K_star"], fh, strict=True)]
        ri = [_dot(row, u) - f for row, f in zip(g, force, strict=True)]

        def hexes(x):
            return [float(v).hex() for v in x]

        arrays = {
            "G": [hexes(row) for row in actual["G"]],
            "K_star": [hexes(row) for row in actual["K_star"]],
            "f_hat": hexes(fh),
            "r_hat": hexes(rh),
            "r_arrays": list(map(str, ra)),
            "intended_residual": list(map(str, ri)),
            "intended_G": [list(map(str, row)) for row in g],
            "intended_K": [list(map(str, row)) for row in kp],
        }
        errors = {
            "beta_G": subtract(g, actual["G"]),
            "beta_K": subtract(g, actual["K_star"]),
            "beta_f": [x - z for x, z in zip(force, fh, strict=True)],
            "beta_eval": [x - z for x, z in zip(rh, ra, strict=True)],
            "symmetry_G": [
                actual["G"][i][j] - actual["G"][j][i] for i in range(n) for j in range(n)
            ],
            "symmetry_K_star": [
                actual["K_star"][i][j] - actual["K_star"][j][i] for i in range(n) for j in range(n)
            ],
        }
        p.end("independent-assembly-residual-error-bookkeeping")
        beta_g = p.norm("beta_G", errors["beta_G"])
        beta_k = p.norm("beta_K", errors["beta_K"])
        beta_f = p.norm("beta_f", errors["beta_f"])
        beta_eval = p.norm("beta_eval", errors["beta_eval"])
        q = p.norm("q_hat", rh)
        unorm = p.norm("u_plus", u)
        p.norm("intended_residual_plus", ri)
        for label in ("G", "K_star"):
            p.norm("symmetry_" + label, errors["symmetry_" + label])
        q_eval = p.rounded("q_eval", q + beta_eval)
        operator = p.rounded("operator_solution", beta_k * unorm)
        with_operator = p.rounded("with_operator", q_eval + operator)
        r_plus = p.rounded("r_plus", with_operator + beta_f)
        p.check(r_plus**2 >= _dot(ri, ri), "direct intended residual transfer proof")
        energy = sum(
            (
                _dot(u, [_dot(row, u) for row in matrix]) / modulus
                for matrix, modulus in zip(elements, moduli, strict=True)
            ),
            Fraction(0),
        )
        arrays["U_tilde"] = str(energy)
        u_plus = p.rounded("U_plus", energy)
        cs = Fraction(normalizer["value"])
        if cs <= 0:
            status = "STOP_NORMALIZER"
            raise _RangeStop("C_s")
        p.check(
            cs == Fraction(11, 10) * _solve_energy(g, force),
            "SAME authored stored denominator proof",
        )
        cs_minus = p.rounded("C_s_minus", cs, "down")
        sqrt_u = p.root("sqrt_U_plus", u_plus)
        sqrt_m = p.root("sqrt_m_minus", m, False)
        p.check(sqrt_m > 0, "positive fixed-grid sqrt denominator")
        residual = p.rounded("residual_term_plus", r_plus / sqrt_m)
        energy_sum = p.rounded("energy_sum_plus", sqrt_u + residual)
        bound = p.rounded("B_plus", energy_sum**2)
        normalized = p.rounded("normalized_B_plus", bound / cs_minus)
        compliance = _solve_energy(kp, force)
        p.check(compliance <= bound, "independent exact compliance <= corrected diagnostic")
        p.check(compliance / cs <= normalized, "independent SAME-normalized compliance enclosure")
        p.check(
            result["unmodified_U_certified"] == (not any(ri)), "nonzero residual never certifies U"
        )
        p.check(result["beta_G_retained"] == float(beta_g).hex(), "separate beta_G retained")
    except _RangeStop:
        if status == "PASS":
            status = "STOP_RANGE"
        p.check(result["unmodified_U_certified"] is False, "stopped unmodified energy unproved")
    p.start("independent-case-completion")
    p.check(status == expected_status == result["status"], "independent expected classification")
    p.check(p.position == len(result["trace"]), "no forged/unexecuted suffix")
    p.check(p.seen_bounds == set(result["bounds"]), "no missing/unknown bound")
    p.check(p.seen_squares == set(result["square_uppers"]), "both errors/all norm fields complete")
    p.check(arrays == result["arrays"], "independent intended/represented arrays and energy")
    p.check(result["public_coercivity_certified"] == (status == "PASS"), "integrated public scope")
    p.check((result["reason"] is None) == (status == "PASS"), "retained stop reason")
    p.check((result["failure_stage"] is None) == (status == "PASS"), "retained failure stage")
    if status != "PASS":
        p.check(
            result["failure_stage"]
            == (result["trace"][-1]["stage"] if result["trace"] else "identity-or-PSD"),
            "exact stopped stage identity",
        )
    p.check(
        type(result["unmodified_U_certified"]) is bool
        and type(result["public_coercivity_certified"]) is bool,
        "closed certificate boolean types",
    )
    p.end("independent-case-completion")
    return {
        "passed": True,
        "id": fixture["id"],
        "status": status,
        "predicates": p.predicates,
        "RN_even_proofs": p.rn_proofs,
        "fixed80_root_proofs": p.root_proofs,
    }
