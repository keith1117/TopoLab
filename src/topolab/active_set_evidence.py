"""In-memory independent affine certificates; no candidate or artifact imports."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

VERSION = "topolab.active-set-evidence.v1"
MAX_PIECES = 256
STEPS = (1e-4, 2e-4)


class IncompleteEvidence(ValueError):
    """The supplied evidence cannot prove the complete unchanged map."""


class UndefinedDerivative(IncompleteEvidence):
    """No strictly interior pointwise derivative can be selected."""


def _rational(value: float | Fraction) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if not math.isfinite(value):
        raise IncompleteEvidence("nonfinite evidence")
    return Fraction(value)


def _inputs(
    raw: Sequence[float],
    weights: Sequence[float],
    cotangent: Sequence[float],
    volume: float,
    minimum: float,
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...], tuple[Fraction, ...], Fraction, Fraction]:
    z, w, g = (tuple(_rational(v) for v in vector) for vector in (raw, weights, cotangent))
    v, lower = _rational(volume), _rational(minimum)
    if (
        not z
        or len(z) != len(w)
        or len(z) != len(g)
        or any(x < 0 or x > 1 for x in z)
        or any(x <= 0 for x in w)
        or abs(float(sum(w)) - 1) > 1e-12
        or not 0 < lower < v < 1
    ):
        raise IncompleteEvidence("matching finite vectors, positive weights and volume required")
    return z, w, g, v, lower


@dataclass(frozen=True, slots=True)
class Piece:
    start: Fraction
    end: Fraction
    partition: tuple[int, ...]  # -1 lower, 0 free, 1 upper


@dataclass(frozen=True, slots=True)
class CertifiedPiece:
    piece: Piece
    offset_start: Fraction
    offset_end: Fraction
    offset_slope: Fraction
    value_slope: Fraction
    design_start: tuple[Fraction, ...]
    design_end: tuple[Fraction, ...]
    weighted_residuals: tuple[Fraction, Fraction]


def _affine(
    z: tuple[Fraction, ...],
    w: tuple[Fraction, ...],
    g: tuple[Fraction, ...],
    d: tuple[Fraction, ...],
    volume: Fraction,
    minimum: Fraction,
    piece: Piece,
) -> CertifiedPiece:
    p = piece.partition
    if len(p) != len(z) or any(type(k) is not int or k not in (-1, 0, 1) for k in p):
        raise IncompleteEvidence("invalid complete partition")
    free = [i for i, k in enumerate(p) if k == 0]
    denominator = sum((w[i] for i in free), Fraction())
    if denominator <= 0:
        raise UndefinedDerivative("no positive free denominator")
    intercept = (
        volume
        - sum(
            (w[i] * (minimum if k == -1 else 1 if k == 1 else z[i]) for i, k in enumerate(p)),
            Fraction(),
        )
    ) / denominator
    slope = -sum((w[i] * d[i] for i in free), Fraction()) / denominator
    endpoints: list[tuple[Fraction, ...]] = []
    for t in (piece.start, piece.end, (piece.start + piece.end) / 2):
        shifted = tuple(x + t * di + intercept + t * slope for x, di in zip(z, d, strict=True))
        interior = piece.start < t < piece.end
        for k, q in zip(p, shifted, strict=True):
            valid = q <= minimum if k == -1 else q >= 1 if k == 1 else minimum <= q <= 1
            if not valid or (interior and (q == minimum or q == 1)):
                raise IncompleteEvidence("partition invalid or persistently degenerate on piece")
        endpoints.append(
            tuple(
                minimum if k == -1 else Fraction(1) if k == 1 else q
                for k, q in zip(p, shifted, strict=True)
            )
        )
    residuals = tuple(
        sum((wi * xi for wi, xi in zip(w, x, strict=True)), Fraction()) - volume
        for x in endpoints[:2]
    )
    if any(residuals):
        raise IncompleteEvidence("affine volume identity failed")
    return CertifiedPiece(
        piece,
        intercept + piece.start * slope,
        intercept + piece.end * slope,
        slope,
        sum((g[i] * (d[i] + slope) for i in free), Fraction()),
        endpoints[0],
        endpoints[1],
        (residuals[0], residuals[1]),
    )


def _gradient(
    w: tuple[Fraction, ...], g: tuple[Fraction, ...], p: tuple[int, ...]
) -> tuple[float, ...]:
    denominator = sum((wi for wi, k in zip(w, p, strict=True) if k == 0), Fraction())
    total = sum((gi for gi, k in zip(g, p, strict=True) if k == 0), Fraction())
    if denominator <= 0:
        raise UndefinedDerivative("no positive free denominator")
    return tuple(
        float(gi - wi * total / denominator) if k == 0 else 0.0
        for wi, gi, k in zip(w, g, p, strict=True)
    )


@dataclass(frozen=True, slots=True)
class PointReference:
    weights: tuple[float, ...]
    volume: float
    design: tuple[float, ...]
    offset: float
    gradient: tuple[float, ...]
    partition: tuple[int, ...]
    kink_margin: float


def certify_pointwise(
    raw: Sequence[float],
    weights: Sequence[float],
    cotangent: Sequence[float],
    volume: float,
    minimum: float,
    proposed_offset: float,
) -> PointReference:
    """Derive and prove a root; the proposed offset only proposes its partition."""
    z, w, g, v, lower = _inputs(raw, weights, cotangent, volume, minimum)
    proposed = tuple(x + _rational(proposed_offset) for x in z)
    if any(min(abs(q - lower), abs(q - 1)) <= _rational(1e-10) for q in proposed):
        raise UndefinedDerivative("proposed central state is at a kink")
    p = tuple(-1 if q < lower else 1 if q > 1 else 0 for q in proposed)
    zero = Fraction()
    proof = _affine(z, w, g, tuple(zero for _ in z), v, lower, Piece(zero, zero, p))
    shifted = tuple(x + proof.offset_start for x in z)
    margin = min(min(abs(q - lower), abs(q - 1)) for q in shifted)
    if margin <= _rational(1e-10):
        raise UndefinedDerivative("independent root is at a central kink")
    return PointReference(
        tuple(weights),
        volume,
        tuple(float(x) for x in proof.design_start),
        float(proof.offset_start),
        _gradient(w, g, p),
        p,
        float(margin),
    )


@dataclass(frozen=True, slots=True)
class PointWitness:
    design: tuple[float, ...]
    physical: tuple[float, ...]
    gradient: tuple[float, ...]
    offset: float
    kink_margin: float
    weighted_residual: float
    physical_residual: float
    value: float
    compliance: float
    torch_value: float
    torch_gradient: tuple[float, ...]


def _close(a: float, b: float, rtol: float = 0, atol: float = 0) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= atol + rtol * abs(b)


def _vectors(a: Sequence[float], b: Sequence[float], rtol: float, atol: float) -> bool:
    return len(a) == len(b) and all(_close(x, y, rtol, atol) for x, y in zip(a, b, strict=True))


def check_pointwise(
    reference: PointReference,
    witness: PointWitness,
    *,
    weights: Sequence[float],
    independent_physical: Sequence[float],
    independent_value: float,
    independent_compliance: float,
    volume: float,
) -> tuple[bool, ...]:
    """Retain every predicate; the caller independently certifies physical/FEM origin."""
    if tuple(weights) != reference.weights or volume != reference.volume:
        raise IncompleteEvidence("pointwise physical-volume context differs from certified root")
    weighted = (
        math.fsum(w * x for w, x in zip(weights, witness.design, strict=True)) - volume
        if len(weights) == len(witness.design)
        else math.nan
    )
    physical = (
        math.fsum(witness.physical) / len(witness.physical) - volume
        if witness.physical
        else math.nan
    )
    return (
        _vectors(witness.design, reference.design, 0, 2e-11),
        len(witness.physical) == len(reference.design)
        and _vectors(witness.physical, independent_physical, 0, 2e-11),
        _vectors(witness.gradient, reference.gradient, 1e-9, 1e-10),
        _close(witness.offset, reference.offset, atol=2e-11),
        _close(witness.kink_margin, reference.kink_margin, atol=2e-11),
        _close(weighted, 0, atol=1e-12),
        _close(physical, 0, atol=1e-12),
        _close(witness.weighted_residual, weighted, atol=1e-12),
        _close(witness.physical_residual, physical, atol=1e-12),
        _close(math.fsum(witness.gradient), 0, atol=1e-10),
        witness.kink_margin > 1e-10,
        _close(witness.value, independent_value, 1e-9, 1e-10),
        _close(witness.compliance, independent_compliance, 1e-9),
        _close(witness.torch_value, witness.value) and witness.torch_value == witness.value,
        _vectors(witness.torch_gradient, witness.gradient, 0, 0),
    )


@dataclass(frozen=True, slots=True)
class IntervalReference:
    step: float
    direction: tuple[float, ...]
    pieces: tuple[CertifiedPiece, ...]
    transitions: tuple[tuple[int, ...], ...]
    signed_increment: Fraction
    secant: float
    central_gradient: tuple[float, ...]


def certify_interval(
    raw: Sequence[float],
    direction: Sequence[float],
    weights: Sequence[float],
    cotangent: Sequence[float],
    volume: float,
    minimum: float,
    step: float,
    pieces: Sequence[Piece],
) -> IntervalReference:
    """Prove every affine piece over all of [-h,h], with no tolerated gaps."""
    z, w, g, v, lower = _inputs(raw, weights, cotangent, volume, minimum)
    d = tuple(_rational(x) for x in direction)
    if len(d) != len(z) or step not in STEPS or not 0 < len(pieces) <= MAX_PIECES:
        raise IncompleteEvidence("original step, matching direction and at most 256 pieces needed")
    h = _rational(step)
    if any(
        x - h * di < 0 or x - h * di > 1 or x + h * di < 0 or x + h * di > 1
        for x, di in zip(z, d, strict=True)
    ):
        raise IncompleteEvidence("raw interval leaves candidate input bounds")
    cursor = -h
    proofs: list[CertifiedPiece] = []
    transitions: list[tuple[int, ...]] = []
    for piece in pieces:
        if (
            not isinstance(piece.start, Fraction)
            or not isinstance(piece.end, Fraction)
            or piece.start != cursor
            or not piece.start < piece.end <= h
        ):
            raise IncompleteEvidence("incomplete, overlapping or unordered exact interval coverage")
        proof = _affine(z, w, g, d, v, lower, piece)
        if proofs:
            prior = proofs[-1]
            if prior.piece.partition == piece.partition:
                raise IncompleteEvidence("redundant partition split")
            if prior.design_end != proof.design_start or prior.offset_end != proof.offset_start:
                raise IncompleteEvidence("discontinuous transition")
            changed = tuple(
                i
                for i, (a, b) in enumerate(zip(prior.piece.partition, piece.partition, strict=True))
                if a != b
            )
            if any(proof.design_start[i] not in (lower, Fraction(1)) for i in changed):
                raise IncompleteEvidence("transition lacks bound contact")
            transitions.append(changed)
        proofs.append(proof)
        cursor = piece.end
    if cursor != h:
        raise IncompleteEvidence("missing interval suffix")
    increment = sum((p.value_slope * (p.piece.end - p.piece.start) for p in proofs), Fraction())
    endpoint_increment = sum(
        (
            gi * (b - a)
            for gi, a, b in zip(g, proofs[0].design_start, proofs[-1].design_end, strict=True)
        ),
        Fraction(),
    )
    if increment != endpoint_increment:
        raise IncompleteEvidence("signed piece integral differs from endpoint increment")
    central = next((p for p in proofs if p.piece.start < 0 < p.piece.end), None)
    if central is None:
        raise UndefinedDerivative("central breakpoint has no selected derivative")
    q = tuple(x + central.offset_start - central.piece.start * central.offset_slope for x in z)
    if any(min(abs(x - lower), abs(x - 1)) <= _rational(1e-10) for x in q):
        raise UndefinedDerivative("central interval state is at a kink")
    return IntervalReference(
        step,
        tuple(direction),
        tuple(proofs),
        tuple(transitions),
        increment,
        float(increment / (2 * h)),
        _gradient(w, g, central.piece.partition),
    )


@dataclass(frozen=True, slots=True)
class IntervalChecks:
    passed: bool
    crossing: bool
    predicates: tuple[bool, ...]
    legacy_mask_passed: bool
    legacy_fd_passed: bool


def check_interval(
    reference: IntervalReference,
    direction: Sequence[float],
    step: float,
    minus_value: float,
    plus_value: float,
    central_derivative: float,
    *,
    legacy_mask_passed: bool,
    legacy_fd_passed: bool,
) -> IntervalChecks:
    if step != reference.step or tuple(direction) != reference.direction:
        raise IncompleteEvidence("retained original step and direction must match certificate")
    if type(legacy_mask_passed) is not bool or type(legacy_fd_passed) is not bool:
        raise IncompleteEvidence("unknown legacy predicates cannot be reclassified")
    actual = (plus_value - minus_value) / (2 * step)
    crossing = bool(reference.transitions)
    expected = (
        reference.secant
        if crossing
        else math.fsum(x * d for x, d in zip(reference.central_gradient, direction, strict=True))
    )
    error = abs(actual - expected) / max(abs(actual), abs(expected), 1e-8)
    conditions = (
        math.isfinite(error) and error <= 1e-4,
        _close(plus_value - minus_value, float(reference.signed_increment), 1e-12, 1e-12),
        crossing or _close(central_derivative, expected, 1e-9, 1e-10),
    )
    return IntervalChecks(
        all(conditions), crossing, conditions, legacy_mask_passed, legacy_fd_passed
    )
