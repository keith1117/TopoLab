"""Exhaustive exact small public fixtures, independently of the certificate checker.

This is a software oracle, bounded to six coordinates. It has no file IO or
production CLI and imports neither TopoLab nor the candidate/checker functions.
"""

from fractions import Fraction
from itertools import product


def enumerate_pieces(raw, direction, weights, volume, minimum, step):
    z, d, w = [tuple(Fraction(x) for x in values) for values in (raw, direction, weights)]
    n = len(z)
    if not 1 <= n <= 6:
        raise ValueError("public fixture oracle supports at most six coordinates")
    v, m, h = map(Fraction, (volume, minimum, step))
    found = []
    for labels in product((-1, 0, 1), repeat=n):
        active = [i for i in range(n) if labels[i] == 0]
        if not active:
            continue
        mass = sum(w[i] for i in active)
        a = (
            v
            - sum(w[i] * m for i in range(n) if labels[i] == -1)
            - sum(w[i] for i in range(n) if labels[i] == 1)
            - sum(w[i] * z[i] for i in active)
        ) / mass
        b = -sum(w[i] * d[i] for i in active) / mass
        inequalities = []
        for i, label in enumerate(labels):
            q, slope = z[i] + a, d[i] + b
            if label <= 0:
                inequalities.append((m - q, -slope) if label == -1 else (q - m, slope))
            if label >= 0:
                inequalities.append((q - 1, slope) if label == 1 else (1 - q, -slope))
        low, high = -h, h
        valid = True
        for constant, slope in inequalities:
            if slope > 0:
                low = max(low, -constant / slope)
            elif slope < 0:
                high = min(high, -constant / slope)
            elif constant <= 0:
                valid = False
        if valid and low < high:
            ends = []
            for t in (low, high):
                ends.append(
                    tuple(max(m, min(Fraction(1), z[i] + d[i] * t + a + b * t)) for i in range(n))
                )
            found.append((low, high, labels, ends[0], ends[1]))
    return sorted(found)
