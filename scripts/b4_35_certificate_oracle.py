"""Independent exact algebra/represented-binary64 audit for eight public toys.

Imports no TopoLab, producer or certificate helper. No IO or real FEM.
The oracle uses elimination and rational inequalities, never candidate sqrt code.
"""

import math
from fractions import Fraction

FIELDS = {
    "U_plus",
    "r_plus",
    "m_minus",
    "C_s_minus",
    "sqrt_U_up",
    "sqrt_m_down",
    "residual_division_up",
    "B_plus",
    "normalized_B_plus",
    "residual_is_exact_zero",
    "unmodified_U_certified",
    "diagnostic_only",
}


def reference(raw, name):
    if name not in ("anchor", "current"):
        raise ValueError("only two named public points")
    a = [[[Fraction(s) for s in line] for line in k] for k in raw["unit_matrices"]]
    f = list(map(Fraction, raw["load"]))
    v = list(map(Fraction, raw["approximate_displacement"]))
    n = len(f)
    if not 1 <= n <= 2 or not 1 <= len(a) <= 3:
        raise ValueError("only bounded1x1/2x2 public systems")
    rho = list(map(Fraction, raw[name + "_density"]))
    star = list(map(Fraction, raw["anchor_density"]))

    def e(x):
        return (1 + 999 * x * x * x) / 1000

    def system(densities):
        result = [[Fraction(0) for _ in f] for _ in f]
        for k, x in zip(a, densities, strict=True):
            for i in range(n):
                for j in range(n):
                    result[i][j] += e(x) * k[i][j]
        return result

    def solution(k):
        # Independent elimination on the exact intended toy operator.
        equations = [line[:] + [rhs] for line, rhs in zip(k, f, strict=True)]
        for column in range(n):
            pivot = equations[column][column]
            if pivot <= 0:
                raise ValueError("positive toy pivot required")
            equations[column] = [x / pivot for x in equations[column]]
            for i in range(column + 1, n):
                coefficient = equations[i][column]
                equations[i] = [
                    x - coefficient * y
                    for x, y in zip(equations[i], equations[column], strict=True)
                ]
        x = [Fraction(0)] * n
        for i in reversed(range(n)):
            x[i] = equations[i][-1] - sum(equations[i][j] * x[j] for j in range(i + 1, n))
        return x

    def compliance(k):
        solved = solution(k)
        return sum(
            (force * displacement for force, displacement in zip(f, solved, strict=True)),
            Fraction(0),
        )

    g = [[sum((k[i][j] for k in a), Fraction(0)) for j in range(n)] for i in range(n)]
    lower = Fraction(raw["lower_G"])

    def psd(k):
        principal = [k[i][i] for i in range(n)]
        if n == 2:
            principal.append(k[0][0] * k[1][1] - k[0][1] * k[1][0])
        return all(x >= 0 for x in principal) and all(
            k[i][j] == k[j][i] for i in range(n) for j in range(n)
        )

    shifted = [[g[i][j] - (lower if i == j else 0) for j in range(n)] for i in range(n)]
    k_star = system(star)
    residual = [
        sum(
            (value * displacement for value, displacement in zip(line, v, strict=True)), Fraction(0)
        )
        - force
        for line, force in zip(k_star, f, strict=True)
    ]
    energy = []
    for k in a:
        product = [
            sum((entry * value for entry, value in zip(line, v, strict=True)), Fraction(0))
            for line in k
        ]
        energy.append(sum((x * y for x, y in zip(v, product, strict=True)), Fraction(0)))
    upper = sum(
        (e(old) * e(old) * q / e(new) for old, new, q in zip(star, rho, energy, strict=True)),
        Fraction(0),
    )
    return {
        "element_psd": all(psd(k) for k in a),
        "uniform_psd": psd(shifted) and lower > 0,
        "positive_moduli": all(e(x) > 0 for x in rho + star),
        "energy_nonnegative": all(q >= 0 for q in energy),
        "energy": energy,
        "upper": upper,
        "residual_squared": sum((x * x for x in residual), Fraction(0)),
        "coercivity": lower / 1000,
        "stored": Fraction(raw["stored_normalizer"]),
        "anchor_compliance": compliance(k_star),
        "compliance": compliance(system(rho)),
    }


def audit_point(raw, name, result):
    """Exact inequalities on all published intermediates, not a tolerance check."""
    ref = reference(raw, name)
    checks = {"closed_result_schema": set(result) == FIELDS}
    numeric = FIELDS - {"residual_is_exact_zero", "unmodified_U_certified", "diagnostic_only"}
    checks["finite_binary64_fields"] = all(
        type(result.get(key)) is float and math.isfinite(result[key]) for key in numeric
    )
    if not all(checks.values()):
        return checks, ref
    q = {key: Fraction.from_float(result[key]) for key in numeric}
    checks.update(
        {
            "intended_element_psd": ref["element_psd"],
            "uniform_intended_coercivity": ref["uniform_psd"],
            "same_positive_simp_moduli": ref["positive_moduli"],
            "nonnegative_exact_energy": ref["energy_nonnegative"],
            "same_authored_stored_normalizer": ref["stored"]
            == Fraction(11, 10) * ref["anchor_compliance"],
            "upper_energy_enclosed": q["U_plus"] >= ref["upper"] >= 0,
            "residual_norm_enclosed": q["r_plus"] >= 0
            and q["r_plus"] ** 2 >= ref["residual_squared"],
            "positive_uniform_lower": 0 < q["m_minus"] <= ref["coercivity"],
            "positive_same_stored_lower": 0 < q["C_s_minus"] <= ref["stored"],
            "sqrt_energy_up": q["sqrt_U_up"] >= 0 and q["sqrt_U_up"] ** 2 >= q["U_plus"],
            "sqrt_coercivity_down": q["sqrt_m_down"] > 0 and q["sqrt_m_down"] ** 2 <= q["m_minus"],
            "exact_zero_flag": result["residual_is_exact_zero"] is (ref["residual_squared"] == 0),
            "unmodified_bound_only_proved_zero": result["unmodified_U_certified"]
            is (ref["residual_squared"] == 0),
            "diagnostic_only_no_loss": result["diagnostic_only"] is True,
            "unmodified_certified_upper_if_zero": ref["residual_squared"] != 0
            or ref["upper"] >= ref["compliance"],
        }
    )
    if q["sqrt_m_down"] > 0:
        checks["residual_division_up"] = q["residual_division_up"] >= q["r_plus"] / q["sqrt_m_down"]
    else:
        checks["residual_division_up"] = False
    checks["final_square_up"] = q["B_plus"] >= (q["sqrt_U_up"] + q["residual_division_up"]) ** 2
    checks["actual_compliance_upper"] = q["B_plus"] >= ref["compliance"]
    checks["normalized_compliance_upper"] = (
        q["normalized_B_plus"] >= ref["compliance"] / ref["stored"]
    )
    checks["same_stored_outward_division"] = (
        q["C_s_minus"] > 0 and q["normalized_B_plus"] >= q["B_plus"] / q["C_s_minus"]
    )
    return checks, ref
