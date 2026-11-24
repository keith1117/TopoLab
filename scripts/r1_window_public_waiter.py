"""Run one owned public timing caller operation."""

import hashlib
import sys
from pathlib import Path

if __name__ == "__main__":
    entry = Path(__file__).resolve()
    route = entry.with_name("r1_window_public_route.py")
    raw = route.read_bytes()
    bindings = {
        "__file__": str(route),
        "entry_digests": {
            str(route): hashlib.sha256(raw).hexdigest(),
            str(entry): hashlib.sha256(entry.read_bytes()).hexdigest(),
        },
    }
    exec(compile(raw, str(route), "exec"), bindings)
    bindings["main"]("waiter", entry, sys.argv[1:])
