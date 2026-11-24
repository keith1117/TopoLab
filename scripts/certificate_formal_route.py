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
        repo=Path("/private/tmp/topolab-certificate-20261124"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/certificate-20261124-formal"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.certificate-20261124.v1",
        budget="7ae3b524775086003d636d15e747333bdc7c9abd96ea34ea67f9f6e0cf999595",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-certificate-20261124-a1"
        ),
        control_entry="certificate_formal_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    wire.actor_prefix = lambda actor: "certificate-formal-" + actor
    wire.protocol = "docs/planning/certificate_formal_contract.json"
    return wire
