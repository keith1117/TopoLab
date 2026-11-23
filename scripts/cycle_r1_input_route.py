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
        repo=Path("/private/tmp/topolab-input-cycle-20261123-a2"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/input-cycle-20261123-a2"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a2.v1",
        budget="6f4168eb23d191629a98c42c469933e0016a1ba2090c521995fc0eeb606a06de",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-input-cycle-20261123-a2"
        ),
        control_entry="cycle_r1_input_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    return wire
