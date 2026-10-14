"""B4.49 finite public combined diagnostic; no real FEM, solve, or path IO."""

import hashlib
import json
import math
import re
import struct
from collections.abc import Callable, Mapping
from fractions import Fraction
from types import MappingProxyType
from typing import Any

VERSION = "topolab.b4_49.public-combined-diagnostic-certificate.v1"
SOURCE_MAIN = "a3a237fa79e35477f10f0874e5c71d7fa39c9f36"
ROLE = "b4-49-public-combined-software"
FINGERPRINTS: Mapping[str, str] = MappingProxyType(
    {
        "combined-balanced-scalar": (
            "db91b867ced9752ef37c9bdf991d330c2817ab571c1c5e6a803da74be321d52b"
        ),
        "combined-coupled-anchor": (
            "c6cc5167f0205d06a994170665d1c9175ed184bad8eaa0fac46afa9a607b9816"
        ),
        "combined-rounded-zero-residual": (
            "36dfee3b48fe56a1ec2f4c0730dd5ef307df7f46cfe4982a170727b674aaa742"
        ),
        "combined-nondyadic-assembly": (
            "014ffbc3137703ffb7cf8ba93d11e3a277c440209bf89f18f40ed75c00333ec5"
        ),
        "combined-singular-elements": (
            "6ab5d958176631956e0b30d16fae85519e9b462d6375367054c1c05ca4c36bba"
        ),
        "combined-indefinite-element": (
            "a5cb3cfacb482f44ee8459719b6a12c575fd057ad5d0ac1147a78d3323a4f9be"
        ),
        "combined-eta-boundary": (
            "1a26cf8b60a6ad3221092863aef814a4ec3ea9924897564a3f7070c807050d27"
        ),
        "combined-positive-conservative": (
            "4ef9dd9d2e4770bdf336b03fbc36e0d5dd474c23c758efac770679d2d29f7295"
        ),
        "combined-nonpositive-normalizer": (
            "cdc8d94b7611e961d15e6dd6bd45f7193e13e98606087cac51bd960b1d94feae"
        ),
        "combined-wrong-normalizer-force": (
            "c8e0c9a1641fedb6a3af155ac6c3cf97d71480e3d9870ee701489f3feb31e149"
        ),
        "combined-energy-overflow": (
            "34684193a9ef2a334a0be1fe517daa9075f9b74d9d8b7bb937d796909c8388fb"
        ),
        "combined-residual-subnormal": (
            "1fd450cc21ed5d2a2db2e1d49ffd43caad357c5fb00664a70cb88767ee603c70"
        ),
    }
)
MIN_NORMAL = float.fromhex("0x1p-1022")
Journal = Callable[[str, dict[str, Any]], None]


class CertificateStop(ValueError):
    def __init__(self, status: str, reason: str) -> None:
        self.status = status
        super().__init__(reason)


def _closed(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CertificateStop("STOP_SCHEMA", "duplicate field")
        result[key] = value
    return result


def _rational(value: Any) -> Fraction:
    if type(value) is not str or len(value) > 4096:
        raise CertificateStop("STOP_SCHEMA", "bounded canonical rational required")
    try:
        number = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise CertificateStop("STOP_SCHEMA", "invalid rational") from exc
    if str(number) != value:
        raise CertificateStop("STOP_SCHEMA", "noncanonical rational")
    return number


def _word(value: Any) -> float:
    if type(value) is not str or not re.fullmatch("[0-9a-f]{16}", value):
        raise CertificateStop("STOP_SCHEMA", "accepted IEEE word required")
    number = struct.unpack(">d", bytes.fromhex(value))[0]
    if not math.isfinite(number) or (number and abs(number) < MIN_NORMAL):
        raise CertificateStop("STOP_SCHEMA", "normal or zero IEEE input required")
    return float(number)


def _matrix(value: Any, rows: int, cols: int, bits: bool = False) -> list[list[Fraction]]:
    if type(value) is not list or len(value) != rows:
        raise CertificateStop("STOP_SCHEMA", "matrix row count")
    result = []
    for row in value:
        if type(row) is not list or len(row) != cols:
            raise CertificateStop("STOP_SCHEMA", "matrix column count")
        result.append([Fraction(_word(x)) if bits else _rational(x) for x in row])
    return result


def load_registered(
    identifier: str, callback: Callable[[], bytes], grant: dict[str, str]
) -> dict[str, Any]:
    """Reject closed identity bindings before the callback may provide bytes."""
    expected = {
        "id": identifier,
        "sha256": FINGERPRINTS.get(identifier, "UNREGISTERED"),
        "role": ROLE,
        "version": VERSION,
        "source_main": SOURCE_MAIN,
        "space": "b4-49-public-space:" + identifier,
    }
    if identifier not in FINGERPRINTS or grant != expected:
        raise CertificateStop("STOP_BINDING", "closed registered identity required before bytes")
    raw = callback()
    if type(raw) is not bytes or len(raw) > 32768:
        raise CertificateStop("STOP_SCHEMA", "bounded public fixture bytes")
    if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise CertificateStop("STOP_BINDING", "changed public fixture bytes")

    def nonfinite(text: str) -> Any:
        raise CertificateStop("STOP_SCHEMA", "nonfinite JSON: " + text)

    try:
        value = json.loads(raw, object_pairs_hook=_closed, parse_constant=nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CertificateStop("STOP_SCHEMA", "invalid JSON") from exc
    validate(value, identifier)
    return dict(value)


def validate(value: Any, identifier: str) -> None:
    fields = {
        "id",
        "origin",
        "space",
        "force_id",
        "elements",
        "A0",
        "A_hat_bits",
        "Y_bits",
        "force",
        "u_bits",
        "rho",
        "anchor_rho",
        "normalizer",
    }
    if type(value) is not dict or set(value) != fields:
        raise CertificateStop("STOP_SCHEMA", "closed fixture schema")
    if (
        value["id"] != identifier
        or value["origin"] != "original-authored-b4-49-public-only"
        or value["space"] != "b4-49-public-space:" + identifier
        or value["force_id"] != "b4-49-force:" + identifier
    ):
        raise CertificateStop("STOP_SCHEMA", "fixture identity")
    if type(value["force"]) is not list or len(value["force"]) not in (1, 2):
        raise CertificateStop("STOP_SCHEMA", "one or two free DOFs")
    n = len(value["force"])
    if type(value["elements"]) is not list or not 1 <= len(value["elements"]) <= 3:
        raise CertificateStop("STOP_SCHEMA", "one to three elements")
    for matrix in value["elements"]:
        _matrix(matrix, n, n)
    for name in ("rho", "anchor_rho"):
        if type(value[name]) is not list or len(value[name]) != len(value["elements"]):
            raise CertificateStop("STOP_SCHEMA", "same element densities")
        if any(not 0 <= _rational(x) <= 1 for x in value[name]):
            raise CertificateStop("STOP_SCHEMA", "density domain")
    if value["anchor_rho"] != ["1"] * len(value["elements"]):
        raise CertificateStop("STOP_SCHEMA", "fixed anchor density")
    if type(value["A0"]) is not list or not n <= len(value["A0"]) <= 3:
        raise CertificateStop("STOP_SCHEMA", "fixed factor dimensions")
    m = len(value["A0"])
    _matrix(value["A0"], m, n)
    _matrix(value["A_hat_bits"], m, n, True)
    _matrix(value["Y_bits"], n, m, True)
    if type(value["u_bits"]) is not list or len(value["u_bits"]) != n:
        raise CertificateStop("STOP_SCHEMA", "same supplied solution dimension")
    for word in value["u_bits"]:
        _word(word)
    for force in value["force"]:
        _rational(force)
    normalizer = value["normalizer"]
    if type(normalizer) is not dict or set(normalizer) != {"force_id", "space", "value", "kind"}:
        raise CertificateStop("STOP_SCHEMA", "closed SAME stored normalizer")
    if any(type(normalizer[k]) is not str for k in normalizer):
        raise CertificateStop("STOP_SCHEMA", "normalizer literal fields")
    if normalizer["kind"] != "SAME_AUTHORED_STORED_CS":
        raise CertificateStop("STOP_SCHEMA", "stored denominator kind")
    _rational(normalizer["value"])


def _psd(matrix: list[list[Fraction]]) -> bool:
    if any(matrix[i][j] != matrix[j][i] for i in range(len(matrix)) for j in range(len(matrix))):
        return False
    if any(matrix[i][i] < 0 for i in range(len(matrix))):
        return False
    return len(matrix) == 1 or matrix[0][0] * matrix[1][1] >= matrix[0][1] ** 2


def _gram(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    n = len(matrix[0])
    return [
        [sum((row[i] * row[j] for row in matrix), Fraction()) for j in range(n)] for i in range(n)
    ]


def _square(values: list[Fraction]) -> Fraction:
    return sum((x * x for x in values), Fraction())


def _intended_operators(
    elements: list[list[list[Fraction]]], moduli: list[Fraction]
) -> tuple[list[list[Fraction]], list[list[Fraction]]]:
    n = len(elements[0])
    g = [[sum((x[i][j] for x in elements), Fraction()) for j in range(n)] for i in range(n)]
    kp = [
        [
            sum((e * x[i][j] for e, x in zip(moduli, elements, strict=True)), Fraction())
            for j in range(n)
        ]
        for i in range(n)
    ]
    return g, kp


def _residual_errors(
    g: list[list[Fraction]],
    represented: dict[str, list[list[float]]],
    f: list[Fraction],
    fh: list[float],
    u: list[float],
    rhat: list[float],
) -> dict[str, list[Fraction]]:
    n = len(f)
    ra = [
        sum((Fraction(represented["K_star"][i][j]) * Fraction(u[j]) for j in range(n)), Fraction())
        - Fraction(fh[i])
        for i in range(n)
    ]
    ri = [sum((g[i][j] * Fraction(u[j]) for j in range(n)), Fraction()) - f[i] for i in range(n)]
    answer = {
        "r_arrays": ra,
        "intended_residual": ri,
        "beta_G": [g[i][j] - Fraction(represented["G"][i][j]) for i in range(n) for j in range(n)],
        "beta_K": [
            g[i][j] - Fraction(represented["K_star"][i][j]) for i in range(n) for j in range(n)
        ],
        "beta_f": [x - Fraction(z) for x, z in zip(f, fh, strict=True)],
        "beta_eval": [Fraction(x) - z for x, z in zip(rhat, ra, strict=True)],
        "q_hat": list(map(Fraction, rhat)),
        "u_plus": list(map(Fraction, u)),
    }
    for label in ("G", "K_star"):
        answer["symmetry_" + label] = [
            Fraction(represented[label][i][j]) - Fraction(represented[label][j][i])
            for i in range(n)
            for j in range(n)
        ]
    return answer


class _Circuit:
    def __init__(self, journal: Journal | None) -> None:
        self.journal = journal
        self.trace: list[dict[str, Any]] = []
        self.bounds: dict[str, str] = {}
        self.squares: dict[str, str] = {}

    def event(self, phase: str, data: dict[str, Any]) -> None:
        if self.journal:
            self.journal(phase, data)

    def block(self, name: str, callback: Callable[[], Any]) -> Any:
        self.event("before", {"stage": name, "kind": "exact-block"})
        result = callback()
        self.event("after", {"stage": name, "completed": True})
        return result

    def rounded(
        self,
        name: str,
        exact: Fraction,
        mode: str = "up",
        native: tuple[str, float, float] | None = None,
    ) -> float:
        if len(self.trace) >= 400:
            raise CertificateStop("STOP_SCOPE", "registered trace cap")
        self.event("before", {"stage": name, "kind": mode, "exact": str(exact)})
        try:
            if native is None:
                nearest = float(exact)
            elif native[0] == "mul":
                nearest = native[1] * native[2]
            elif native[0] == "add":
                nearest = native[1] + native[2]
            else:
                nearest = native[1] - native[2]
        except OverflowError:
            nearest = math.copysign(math.inf, -1.0 if exact < 0 else 1.0)
        value = nearest
        if math.isfinite(value):
            if mode == "up" and Fraction(value) < exact:
                value = math.nextafter(value, math.inf)
            if mode == "down" and Fraction(value) > exact:
                value = math.nextafter(value, -math.inf)
        accepted = math.isfinite(value) and not (value and abs(value) < MIN_NORMAL)
        accepted = bool(accepted and not (exact and value == 0))
        row = {
            "stage": name,
            "mode": mode,
            "exact": str(exact),
            "nearest_hex": nearest.hex(),
            "result_hex": value.hex(),
            "accepted": accepted,
        }
        self.trace.append(row)
        self.event("after", row)
        if not accepted:
            raise CertificateStop("STOP_RANGE", "executed raw range result at " + name)
        self.bounds[name] = value.hex()
        return value

    def root(self, name: str, squared: Fraction, upper: bool = True) -> float:
        self.event("before", {"stage": name + ":grid", "kind": "fixed80", "exact": str(squared)})
        if squared < 0:
            raise CertificateStop("STOP_SIGN", "negative radicand")
        grid = 1 << 80
        floor = math.isqrt((squared.numerator * grid * grid) // squared.denominator)
        low = Fraction(floor, grid)
        high = low if low * low == squared else Fraction(floor + 1, grid)
        row = {
            "stage": name + ":grid",
            "mode": "fixed80",
            "exact": str(squared),
            "lower": str(low),
            "upper": str(high),
        }
        self.trace.append(row)
        self.event("after", row)
        return self.rounded(name, high if upper else low, "up" if upper else "down")

    def norm(self, name: str, values: list[Fraction]) -> float:
        squared = self.block(name + ":squared", lambda: _square(values))
        self.squares[name] = str(squared)
        return self.root(name, squared)


def evaluate(fixture: dict[str, Any], journal: Journal | None = None) -> dict[str, Any]:
    """Evaluate one registered system with the fixed diagnostic recipe."""
    c = _Circuit(journal)
    arrays: dict[str, Any] = {}
    result: dict[str, Any] = {
        "id": fixture.get("id"),
        "status": "UNKNOWN_NOT_WRITTEN",
        "trace": c.trace,
        "arrays": arrays,
        "square_uppers": c.squares,
        "bounds": c.bounds,
        "diagnostic_only": True,
        "public_intended_only": True,
        "real_fem_certified": False,
        "loss_gradient_changed": False,
        "unmodified_U_certified": False,
        "failure_stage": None,
        "reason": None,
    }
    try:
        validate(fixture, str(fixture.get("id")))
        raw = (json.dumps(fixture, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
        if hashlib.sha256(raw).hexdigest() != FINGERPRINTS.get(str(fixture["id"])):
            raise CertificateStop("STOP_BINDING", "mutated or unregistered prepared system")
        # Snapshot the accepted authored values before any external journal callback.
        fixture = json.loads(raw)
        normalizer = fixture["normalizer"]
        if normalizer["space"] != fixture["space"] or normalizer["force_id"] != fixture["force_id"]:
            raise CertificateStop(
                "STOP_NORMALIZER_IDENTITY", "different space or force denominator"
            )
        n = len(fixture["force"])
        elements = [_matrix(x, n, n) for x in fixture["elements"]]
        psd = c.block("intended-element-PSD", lambda: all(_psd(x) for x in elements))
        if not psd:
            raise CertificateStop("STOP_PSD", "intended element PSD required")
        moduli = c.block(
            "intended-SIMP",
            lambda: [
                Fraction(1, 1000) + Fraction(999, 1000) * _rational(x) ** 3 for x in fixture["rho"]
            ],
        )
        g, kp = c.block("intended-operators", lambda: _intended_operators(elements, moduli))
        a0 = _matrix(fixture["A0"], len(fixture["A0"]), n)
        ah = _matrix(fixture["A_hat_bits"], len(a0), n, True)
        y = _matrix(fixture["Y_bits"], n, len(a0), True)
        gram0, gramh = c.block("both-Gram-errors", lambda: (_gram(a0), _gram(ah)))

        def flat(matrix: list[list[Fraction]]) -> list[Fraction]:
            return [v for row in matrix for v in row]

        def difference(left: list[list[Fraction]], right: list[list[Fraction]]) -> list[Fraction]:
            return [left[i][j] - right[i][j] for i in range(len(left)) for j in range(len(left[0]))]

        witness_errors = c.block(
            "representation-error-vectors",
            lambda: {
                "d0_plus": difference(g, gram0),
                "d1_plus": difference(gram0, gramh),
                "complete_delta_plus": difference(g, gramh),
                "e_plus": difference(a0, ah),
            },
        )
        d0 = c.norm("d0_plus", witness_errors["d0_plus"])
        c.norm("d1_plus", witness_errors["d1_plus"])
        c.norm("complete_delta_plus", witness_errors["complete_delta_plus"])
        e = c.norm("e_plus", witness_errors["e_plus"])
        a = c.norm("a_plus", flat(a0))
        cross = c.rounded("cross_plus", 2 * Fraction(a) * Fraction(e))
        e2 = c.rounded("factor_square_plus", Fraction(e) ** 2)
        representation = c.rounded("representation_plus", Fraction(cross) + Fraction(e2))
        delta = c.rounded("delta_plus", Fraction(d0) + Fraction(representation))
        eta_values = c.block(
            "left-inverse-defect",
            lambda: [
                Fraction(i == j) - sum((y[i][k] * ah[k][j] for k in range(len(ah))), Fraction())
                for i in range(n)
                for j in range(n)
            ],
        )
        eta = c.norm("eta_plus", eta_values)
        m_witness = c.norm("M_plus", flat(y))
        if eta >= 1 or m_witness <= 0:
            raise CertificateStop("STOP_ETA", "eta<1 and M>0 required")
        one = c.rounded("one_minus_eta_minus", 1 - Fraction(eta), "down")
        ratio = c.rounded("ratio_minus", Fraction(one) / Fraction(m_witness), "down")
        factor = c.rounded("factor_lower_minus", Fraction(ratio) ** 2, "down")
        lower = c.rounded("lower_G_minus", Fraction(factor) - Fraction(delta), "down")
        if lower <= 0:
            raise CertificateStop(
                "STOP_COERCIVITY", "nonpositive directed bound; no singularity claim"
            )
        emin = c.rounded("E_min_minus", Fraction(1, 1000), "down")
        m = c.rounded("m_minus", Fraction(emin) * Fraction(lower), "down")
        if m <= 0:
            raise CertificateStop("STOP_COERCIVITY", "nonpositive uniform lower bound")

        represented: dict[str, list[list[float]]] = {}
        for label in ("G", "K_star"):
            actual = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    for k, element in enumerate(elements):
                        entry = c.rounded(f"{label}:entry:{i}:{j}:{k}", element[i][j], "rn")
                        if label == "K_star":
                            modulus = c.rounded(f"{label}:modulus:{i}:{j}:{k}", Fraction(1), "rn")
                            term = c.rounded(
                                f"{label}:product:{i}:{j}:{k}",
                                Fraction(entry) * Fraction(modulus),
                                "rn",
                                ("mul", entry, modulus),
                            )
                        else:
                            term = entry
                        previous = actual[i][j]
                        actual[i][j] = c.rounded(
                            f"{label}:sum:{i}:{j}:{k}",
                            Fraction(previous) + Fraction(term),
                            "rn",
                            ("add", previous, term),
                        )
            represented[label] = actual
        f = [_rational(x) for x in fixture["force"]]
        fh = [c.rounded(f"force:{i}", v, "rn") for i, v in enumerate(f)]
        u = [_word(x) for x in fixture["u_bits"]]
        rhat = []
        for i in range(n):
            total = 0.0
            for j in range(n):
                entry, solution = represented["K_star"][i][j], u[j]
                product = c.rounded(
                    f"residual:product:{i}:{j}",
                    Fraction(entry) * Fraction(solution),
                    "rn",
                    ("mul", entry, solution),
                )
                previous = total
                total = c.rounded(
                    f"residual:sum:{i}:{j}",
                    Fraction(previous) + Fraction(product),
                    "rn",
                    ("add", previous, product),
                )
            force = fh[i]
            rhat.append(
                c.rounded(
                    f"residual:subtract:{i}",
                    Fraction(total) - Fraction(force),
                    "rn",
                    ("sub", total, force),
                )
            )
        errors = c.block(
            "assembly-residual-error-bookkeeping",
            lambda: _residual_errors(g, represented, f, fh, u, rhat),
        )
        ra, ri = errors["r_arrays"], errors["intended_residual"]
        arrays.update(
            {
                "G": [[x.hex() for x in row] for row in represented["G"]],
                "K_star": [[x.hex() for x in row] for row in represented["K_star"]],
                "f_hat": [x.hex() for x in fh],
                "r_hat": [x.hex() for x in rhat],
                "r_arrays": list(map(str, ra)),
                "intended_residual": list(map(str, ri)),
                "intended_G": [[str(x) for x in row] for row in g],
                "intended_K": [[str(x) for x in row] for row in kp],
            }
        )
        beta_g = c.norm("beta_G", errors["beta_G"])
        beta_k = c.norm("beta_K", errors["beta_K"])
        beta_f = c.norm("beta_f", errors["beta_f"])
        beta_eval = c.norm("beta_eval", errors["beta_eval"])
        q = c.norm("q_hat", errors["q_hat"])
        unorm = c.norm("u_plus", errors["u_plus"])
        c.norm("intended_residual_plus", ri)
        for label in ("G", "K_star"):
            c.norm("symmetry_" + label, errors["symmetry_" + label])
        q_eval = c.rounded("q_eval", Fraction(q) + Fraction(beta_eval))
        operator = c.rounded("operator_solution", Fraction(beta_k) * Fraction(unorm))
        with_operator = c.rounded("with_operator", Fraction(q_eval) + Fraction(operator))
        r_plus = c.rounded("r_plus", Fraction(with_operator) + Fraction(beta_f))
        energy = c.block(
            "SAME-anchor-reciprocal-energy",
            lambda: sum(
                (
                    sum(
                        (
                            Fraction(u[i]) * matrix[i][j] * Fraction(u[j])
                            for i in range(n)
                            for j in range(n)
                        ),
                        Fraction(),
                    )
                    / modulus
                    for matrix, modulus in zip(elements, moduli, strict=True)
                ),
                Fraction(),
            ),
        )
        arrays["U_tilde"] = str(energy)
        u_upper = c.rounded("U_plus", energy)
        cs = _rational(normalizer["value"])
        if cs <= 0:
            raise CertificateStop("STOP_NORMALIZER", "positive SAME stored denominator required")
        cs_lower = c.rounded("C_s_minus", cs, "down")
        su = c.root("sqrt_U_plus", Fraction(u_upper))
        sm = c.root("sqrt_m_minus", Fraction(m), False)
        if sm <= 0:
            raise CertificateStop("STOP_COERCIVITY", "fixed-grid positive sqrt lower required")
        residual_term = c.rounded("residual_term_plus", Fraction(r_plus) / Fraction(sm))
        energy_sum = c.rounded("energy_sum_plus", Fraction(su) + Fraction(residual_term))
        bound = c.rounded("B_plus", Fraction(energy_sum) ** 2)
        c.rounded("normalized_B_plus", Fraction(bound) / Fraction(cs_lower))
        result["status"] = "PASS"
        result["unmodified_U_certified"] = not any(ri)
        result["public_coercivity_certified"] = True
        result["beta_G_retained"] = beta_g.hex()
    except CertificateStop as exc:
        result["status"] = exc.status
        result["failure_stage"] = c.trace[-1]["stage"] if c.trace else "identity-or-PSD"
        result["reason"] = str(exc)
        result["public_coercivity_certified"] = False
    return result
