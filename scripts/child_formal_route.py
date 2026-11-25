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
        repo=Path("/private/tmp/topolab-child-20261125"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/child-20261125-formal"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.child-20261125.v1",
        budget="8693ffd9e9555a5247c2569c0d4f97331fbc7f6237dce25e2a80012c7f1c26dd",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-child-20261125-a1"
        ),
        control_entry="child_formal_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    wire.actor_prefix = lambda actor: "child-formal-" + actor
    wire.protocol = "docs/planning/child_formal_contract.json"
    return wire
