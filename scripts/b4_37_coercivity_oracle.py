"""Independent exact audit for B4.37's authored public operators/witnesses.

No candidate/TopoLab/producer imports, IO, sqrt algorithm, FEM or solver.
"""

import math
from fractions import Fraction

FIELDS = {
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


def reference(raw):
    elements = [[[Fraction(s) for s in line] for line in k] for k in raw["unit_matrices"]]
    a = [[Fraction(s) for s in line] for line in raw["energy_factor"]]
    y = [[Fraction(s) for s in line] for line in raw["left_inverse_witness"]]
    n, m = len(y), len(a)
    if not 1 <= n <= 2 or not n <= m <= 3 or not 1 <= len(elements) <= 3:
        raise ValueError("bounded public dimensions required")

    def principal(k):
        diagonal = all(k[i][i] >= 0 for i in range(n))
        determinant = n == 1 or k[0][0] * k[1][1] - k[1][0] * k[0][1] >= 0
        return (
            diagonal
            and determinant
            and all(
                left == right
                for line, column in zip(k, zip(*k, strict=True), strict=True)
                for left, right in zip(line, column, strict=True)
            )
        )

    intended = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for k in elements:
        for i, line in enumerate(k):
            for j, entry in enumerate(line):
                intended[i][j] += entry
    columns = list(zip(*a, strict=True))
    gram = [
        [sum((v * w for v, w in zip(col, other, strict=True)), Fraction(0)) for other in columns]
        for col in columns
    ]
    ya = [
        [sum((v * w for v, w in zip(line, col, strict=True)), Fraction(0)) for col in columns]
        for line in y
    ]
    difference = [intended[i][j] - gram[i][j] for i in range(n) for j in range(n)]
    residual = [Fraction(i == j) - ya[i][j] for i in range(n) for j in range(n)]
    delta2 = sum((v * v for v in difference), Fraction(0))
    eta2 = sum((v * v for v in residual), Fraction(0))
    norm2 = sum((v * v for line in y for v in line), Fraction(0))
    element_psd = all(principal(k) for k in elements)
    if not element_psd:
        disposition = "STOP_PSD"
    elif eta2 >= 1 or norm2 == 0:
        disposition = "STOP_WITNESS"
    elif eta2 == 0 and (1 / norm2) ** 2 <= delta2:
        # Even ideal upper endpoints cannot produce a positive bound for this fixed witness.
        disposition = "STOP_COERCIVITY"
    else:
        disposition = "PASS"
    return {
        "G": intended,
        "delta_squared": delta2,
        "eta_squared": eta2,
        "norm_squared": norm2,
        "element_psd": element_psd,
        "exact_disposition": disposition,
        "same_space": raw["free_space"]
        == raw["factor_space"]
        == raw["witness_space"]
        == "public-free-space:" + raw["id"],
    }


def audit_case(raw, result):
    """Audit all represented endpoints with exact inequalities, including prescribed stops."""
    ref = reference(raw)
    checks = {
        "closed_case_schema": set(result) == {"fixture_id", "status", "certificate", "error"},
        "same_public_fixture": result.get("fixture_id") == raw["id"],
        "same_restricted_spaces": ref["same_space"],
        "independent_disposition": result.get("status") == ref["exact_disposition"],
    }
    if ref["exact_disposition"] != "PASS":
        checks["stop_has_no_certificate"] = result.get("certificate") is None
        checks["stop_retains_explicit_error"] = isinstance(result.get("error"), str) and result[
            "error"
        ].startswith(ref["exact_disposition"] + ":")
        if ref["exact_disposition"] == "STOP_COERCIVITY":
            g = ref["G"]
            checks["conservative_stop_G_still_positive"] = (
                g[0][0] > 0 and g[1][1] > 0 and g[0][0] * g[1][1] > g[0][1] ** 2
            )
        return checks, ref
    certificate = result.get("certificate")
    checks["closed_certificate_schema"] = (
        isinstance(certificate, dict) and set(certificate) == FIELDS
    )
    if not checks["closed_certificate_schema"]:
        return checks, ref
    numeric = FIELDS - FLAGS
    checks["finite_binary64_endpoints"] = all(
        type(certificate.get(k)) is float and math.isfinite(certificate[k]) for k in numeric
    )
    if not checks["finite_binary64_endpoints"]:
        return checks, ref
    q = {k: Fraction.from_float(certificate[k]) for k in numeric}
    checks.update(
        {
            "accepted_has_no_error": result["error"] is None,
            "intended_element_psd_separate": ref["element_psd"],
            "public_intended_only": certificate["public_intended_only"] is True,
            "diagnostic_only": certificate["diagnostic_only"] is True,
            "no_real_certificate": certificate["real_fem_certified"] is False,
            "intended_operator_error_norm_upper": q["delta_plus"] >= 0
            and q["delta_plus"] ** 2 >= ref["delta_squared"],
            "left_inverse_residual_norm_upper": 0 <= q["eta_plus"] < 1
            and q["eta_plus"] ** 2 >= ref["eta_squared"],
            "witness_norm_upper": q["M_plus"] > 0 and q["M_plus"] ** 2 >= ref["norm_squared"],
            "subtraction_lower": 0 < q["one_minus_eta_minus"] <= 1 - q["eta_plus"],
            "square_lower": 0 < q["factor_lower_minus"] <= q["ratio_minus"] ** 2,
            "operator_error_subtracted": 0
            < q["lower_G_minus"]
            <= q["factor_lower_minus"] - q["delta_plus"],
            "same_material_lower": 0 < q["E_min_minus"] <= Fraction(1, 1000),
            "positive_uniform_global_lower": 0
            < q["m_global_minus"]
            <= q["E_min_minus"] * q["lower_G_minus"],
        }
    )
    checks["division_lower"] = q["M_plus"] > 0 and (
        0 < q["ratio_minus"] <= q["one_minus_eta_minus"] / q["M_plus"]
    )
    g, lower = ref["G"], q["lower_G_minus"]
    diagonals = [g[i][i] - lower for i in range(len(g))]
    checks["intended_G_minus_lower_I_psd"] = all(v >= 0 for v in diagonals) and (
        len(g) == 1 or diagonals[0] * diagonals[1] >= g[0][1] * g[1][0]
    )
    return checks, ref
