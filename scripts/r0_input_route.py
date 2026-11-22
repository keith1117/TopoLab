"""Select the one R0-recovery generation and track the shared caller bytes."""

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
        repo=Path("/private/tmp/topolab-r0-read-20261122"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/r0-read-acceptance-20261122"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.r0-read-20261122.v1",
        budget="149fe42c5df8849c49d3cb39b62004a8b0d7d82bf3ce1c7bca131f24f9c0b666",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-r0-read-20261122-a1"
        ),
        control_entry="r0_input_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    return wire
