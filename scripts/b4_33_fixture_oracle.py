"""Independent exact oracle for eight authored public 1x1/2x2 systems.

No candidate/TopoLab imports, file IO or production entrypoint. Assembly,
equilibrium, compliance/adjoint and square-gap checks use rational arithmetic.
"""

from fractions import Fraction


def reference(raw):
    matrices = tuple(
        tuple(tuple(Fraction(x) for x in row) for row in k) for k in raw["unit_matrices"]
    )
    force = tuple(Fraction(x) for x in raw["load"])
    anchor = tuple(Fraction(x) for x in raw["anchor_density"])
    current = tuple(Fraction(x) for x in raw["current_density"])
    n = len(force)
    if n not in (1, 2) or not 1 <= len(matrices) <= 3:
        raise ValueError("bounded public fixture oracle only")

    def modulus(density):
        return Fraction(1, 1000) + Fraction(999, 1000) * density**3

    def assemble(density):
        return tuple(
            tuple(
                sum(
                    (modulus(x) * k[i][j] for k, x in zip(matrices, density, strict=True)),
                    Fraction(),
                )
                for j in range(n)
            )
            for i in range(n)
        )

    def solve(density):
        k = assemble(density)
        if n == 1:
            return (force[0] / k[0][0],)
        determinant = k[0][0] * k[1][1] - k[0][1] * k[1][0]
        return (
            (k[1][1] * force[0] - k[0][1] * force[1]) / determinant,
            (k[0][0] * force[1] - k[1][0] * force[0]) / determinant,
        )

    def quadratic(vector, element):
        product = [
            sum((entry * x for entry, x in zip(row, vector, strict=True)), Fraction())
            for row in element
        ]
        return sum((x * y for x, y in zip(vector, product, strict=True)), Fraction())

    u_star = solve(anchor)
    q_star = tuple(quadratic(u_star, k) for k in matrices)
    anchor_compliance = sum((f * u for f, u in zip(force, u_star, strict=True)), Fraction())
    coefficients = tuple(modulus(x) ** 2 * q for x, q in zip(anchor, q_star, strict=True))

    def upper(density):
        return sum((a / modulus(x) for a, x in zip(coefficients, density, strict=True)), Fraction())

    def upper_gradient(density):
        return tuple(
            -a * Fraction(2997, 1000) * x**2 / modulus(x) ** 2
            for a, x in zip(coefficients, density, strict=True)
        )

    def adjoint(density):
        u = solve(density)
        return tuple(
            -Fraction(2997, 1000) * x**2 * quadratic(u, k)
            for x, k in zip(density, matrices, strict=True)
        )

    u_current = solve(current)
    compliance = sum((f * u for f, u in zip(force, u_current, strict=True)), Fraction())
    squares = []
    for k, old, new in zip(matrices, anchor, current, strict=True):
        difference = tuple(
            modulus(old) / modulus(new) * a - b for a, b in zip(u_star, u_current, strict=True)
        )
        squares.append(modulus(new) * quadratic(difference, k))
    return {
        "anchor": anchor,
        "current": current,
        "u_star": u_star,
        "anchor_compliance": anchor_compliance,
        "stored_compliance": Fraction(11, 10) * anchor_compliance,
        "coefficients": coefficients,
        "upper": upper,
        "upper_gradient": upper_gradient,
        "anchor_adjoint": adjoint(anchor),
        "current_compliance": compliance,
        "gap_squares": tuple(squares),
        "modulus": modulus,
    }
