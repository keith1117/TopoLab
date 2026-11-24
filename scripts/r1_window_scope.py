"""Literal public-fixture paths and independent clocks for the R1 timing contract."""

from pathlib import Path

CHECKOUT = Path("/private/tmp/topolab-r1-window-20261123")
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data/formal-r1-window-20261123")
BUDGET = "d867948e0cf23b8a860a230be66fbedfc3c7cb5398168dada7fa71199fc2a35e"
PUBLIC_ID = "topolab.v2.p17-m2-registered-source-acquisition.r1-window-public-20261123.v1"
FORMAL_ID = "topolab.v2.p17-m2-registered-source-acquisition.r1-window-20261123.v1"
PUBLIC = tuple(Path(f"/private/tmp/topolab-public-r1-window-20261123-a{i}") for i in range(1, 7))
FORMAL = Path(
    "/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-r1-window-20261123-a1"
)
START_MS = 1795476230895
DIAGNOSTIC_END_MS = START_MS + 12 * 3600000
END_MS = 1795670630895


def public_root(root):
    path = Path(root)
    if path not in PUBLIC:
        raise ValueError("unregistered public timing root")
    return path
