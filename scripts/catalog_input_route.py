"""Select the one catalog-verification generation and track the shared caller bytes."""

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
        repo=Path("/private/tmp/topolab-catalog-r0-20261122"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/catalog-r0-acceptance-20261122"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.catalog-20261122.v1",
        budget="985ad9aa67a4cbdc8a5c36cadbf4c7920f39559c57e2115a98e902d17d31c11f",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-catalog-r0-20261122-a1"
        ),
        control_entry="catalog_input_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    return wire
