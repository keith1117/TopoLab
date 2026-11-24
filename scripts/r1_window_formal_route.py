"""Select the one input-cycle generation and track the shared caller bytes."""

import hashlib
from pathlib import Path

path = Path(__file__).resolve().with_name("formal_input_route.py")
raw = path.read_bytes()
digests = globals().get("entry_digests", {})
digests[str(path)] = hashlib.sha256(raw).hexdigest()
shared = {"__file__": str(path), "entry_digests": digests}
exec(compile(raw, str(path), "exec"), shared)
sibling = shared["sibling"]


def filer():
    wire = shared["filer"](
        repo=Path("/private/tmp/topolab-r1-window-20261123"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/formal-r1-window-20261123-formal"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.r1-window-20261123.v1",
        budget="d867948e0cf23b8a860a230be66fbedfc3c7cb5398168dada7fa71199fc2a35e",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-r1-window-20261123-a1"
        ),
        control_entry="r1_window_formal_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    wire.actor_prefix = lambda actor: "r1-window-formal-" + actor
    wire.protocol = "docs/planning/r1_window_formal_contract.json"
    return wire
