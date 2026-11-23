"""File the second attempt in its own evidence pair."""

import hashlib
import sys
from pathlib import Path

if __name__ == "__main__":
    entry = Path(__file__).resolve()
    path = entry.with_name("cycle_r1_input_route.py")
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
    route["sibling"]("cycle_input_filer").dispatch(wire, sys.argv[1:])
