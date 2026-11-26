"""Select the single closeout generation and track the shared caller bytes."""

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
        repo=Path("/private/tmp/topolab-closeout-20261125"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/closeout-20261125-formal"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.closeout-20261125.v1",
        budget="9afb732330236b115a42621441c5b5e7d019c05ce02d1154cd14902dde64b577",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-closeout-20261125-a1"
        ),
        control_entry="closeout_formal_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    wire.actor_prefix = lambda actor: "closeout-formal-" + actor
    wire.protocol = "docs/planning/closeout_formal_contract.json"
    return wire
