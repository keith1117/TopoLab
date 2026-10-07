"""Exact finite certificates for the unchanged clipped-volume equation."""

import math
from collections.abc import Sequence
from fractions import Fraction

from topolab.active_set_evidence import MAX_PIECES, STEPS, IncompleteEvidence, Piece


def _number(value: float) -> Fraction:
    if not math.isfinite(value):
        raise IncompleteEvidence("finite trace inputs required")
    return Fraction(float(value))


def _root(z: tuple[Fraction, ...], w: tuple[Fraction, ...], v: Fraction, m: Fraction) -> Fraction:
    events: dict[Fraction, Fraction] = {}
    for x, weight in zip(z, w, strict=True):
        for boundary, delta in ((m - x, weight), (1 - x, -weight)):
            events[boundary] = events.get(boundary, Fraction()) + delta
    points = sorted(events)
    total = m * sum(w)
    mass = events[points[0]]
    for left, right in zip(points, points[1:], strict=False):
        next_total = total + mass * (right - left)
        if mass > 0 and total <= v <= next_total:
            offset = left + (v - total) / mass
            if not any(m < x + offset < 1 for x in z):
                raise IncompleteEvidence("ambiguous root without strict free mass")
            return offset
        if mass == 0 and total == v:
            raise IncompleteEvidence("volume root has a plateau")
        total = next_total
        mass += events[right]
    raise IncompleteEvidence("no interior exact volume root")


def _forward(
    shifted: tuple[Fraction, ...],
    direction: tuple[Fraction, ...],
    weights: tuple[Fraction, ...],
    minimum: Fraction,
) -> tuple[int, ...]:
    strict = [i for i, q in enumerate(shifted) if minimum < q < 1]
    lower = [i for i, q in enumerate(shifted) if q == minimum]
    upper = [i for i, q in enumerate(shifted) if q == 1]
    active = strict + upper
    mass = sum((weights[i] for i in active), Fraction())
    moment = sum((weights[i] * direction[i] for i in active), Fraction())
    events: dict[Fraction, tuple[Fraction, Fraction]] = {}
    for indices, sign in ((lower, 1), (upper, -1)):
        for i in indices:
            key = -direction[i]
            dw, db = events.get(key, (Fraction(), Fraction()))
            events[key] = (dw + sign * weights[i], db + sign * weights[i] * direction[i])
    left: Fraction | None = None
    velocity: Fraction | None = None
    for right in [*sorted(events), None]:
        if mass == 0 and moment == 0:
            raise IncompleteEvidence("ambiguous one-sided volume constraint")
        if mass > 0:
            proposal = -moment / mass
            if proposal == left or proposal == right:
                raise IncompleteEvidence("persistent one-sided bound contact")
            if (left is None or left < proposal) and (right is None or proposal < right):
                velocity = proposal
                break
        if right is not None:
            dw, db = events[right]
            mass += dw
            moment += db
        left = right
    if velocity is None:
        raise IncompleteEvidence("no unique forward partition")
    partition = []
    for q, d in zip(shifted, direction, strict=True):
        speed = d + velocity
        if q == minimum:
            partition.append(0 if speed > 0 else -1)
        elif q == 1:
            partition.append(0 if speed < 0 else 1)
        else:
            partition.append(-1 if q < minimum else 1 if q > 1 else 0)
    return tuple(partition)


def trace_interval(
    raw: Sequence[float],
    direction: Sequence[float],
    weights: Sequence[float],
    volume: float,
    minimum: float,
    step: float,
) -> tuple[Piece, ...]:
    """Generate every open affine piece, with exact simultaneous contacts."""
    if step not in STEPS or not 1 <= len(raw) <= 1728:
        raise IncompleteEvidence("original step and bounded vector size required")
    z, d, w = (tuple(_number(x) for x in values) for values in (raw, direction, weights))
    v, m, h = _number(volume), _number(minimum), _number(step)
    if (
        len(d) != len(z)
        or len(w) != len(z)
        or any(x <= 0 for x in w)
        or abs(float(sum(w)) - 1) > 1e-12
        or not 0 < m < v < 1
        or any(
            not 0 <= x - h * di <= 1 or not 0 <= x + h * di <= 1 for x, di in zip(z, d, strict=True)
        )
    ):
        raise IncompleteEvidence("invalid raw interval or physical-volume context")
    cursor = -h
    offset = _root(tuple(x + cursor * di for x, di in zip(z, d, strict=True)), w, v, m)
    partition = _forward(
        tuple(x + cursor * di + offset for x, di in zip(z, d, strict=True)), d, w, m
    )
    pieces: list[Piece] = []
    while cursor < h:
        if len(pieces) >= MAX_PIECES:
            raise IncompleteEvidence("complete trace exceeds frozen 256-piece bound")
        free = [i for i, k in enumerate(partition) if k == 0]
        mass = sum((w[i] for i in free), Fraction())
        if mass <= 0:
            raise IncompleteEvidence("no positive piece free denominator")
        intercept = (
            v
            - sum(
                (
                    wi * (m if k == -1 else 1 if k == 1 else x)
                    for x, wi, k in zip(z, w, partition, strict=True)
                ),
                Fraction(),
            )
        ) / mass
        velocity = -sum((w[i] * d[i] for i in free), Fraction()) / mass
        end = h
        for x, di, k in zip(z, d, partition, strict=True):
            speed = di + velocity
            if (k == -1 and speed <= 0) or (k == 1 and speed >= 0) or speed == 0:
                continue
            bound = m if k == -1 or (k == 0 and speed < 0) else Fraction(1)
            contact = (bound - x - intercept) / speed
            if cursor < contact < end:
                end = contact
        pieces.append(Piece(cursor, end, partition))
        if end < h:
            updated = _forward(
                tuple(
                    x + end * di + intercept + end * velocity for x, di in zip(z, d, strict=True)
                ),
                d,
                w,
                m,
            )
            if updated == partition:
                raise IncompleteEvidence("contact does not determine a new partition")
            partition = updated
        cursor = end
    return tuple(pieces)
