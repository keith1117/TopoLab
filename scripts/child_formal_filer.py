"""File this certificate attempt in its own evidence pair."""

import hashlib
import sys
from pathlib import Path

if __name__ == "__main__":
    entry = Path(__file__).resolve()
    path = entry.with_name("child_formal_route.py")
    raw = path.read_bytes()
    route = {
        "__file__": str(path),
        "entry_digests": {
            str(entry): hashlib.sha256(entry.read_bytes()).hexdigest(),
            str(path): hashlib.sha256(raw).hexdigest(),
        },
    }
    exec(compile(raw, str(path), "exec"), route)
    wire = route["filer"]()
    route["sibling"]("cycle_filing_intent").dispatch(wire, route["sibling"], sys.argv[1:])
