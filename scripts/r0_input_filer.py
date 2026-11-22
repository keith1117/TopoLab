"""File actual returns for the single R0 read recovery grant."""

import hashlib
from pathlib import Path

if __name__ == "__main__":
    entry = Path(__file__).resolve()
    path = entry.with_name("r0_input_route.py")
    raw = path.read_bytes()
    route = {"__file__": str(path), "entry_digests": {
        str(entry): hashlib.sha256(entry.read_bytes()).hexdigest(),
        str(path): hashlib.sha256(raw).hexdigest(),
    }}
    exec(compile(raw, str(path), "exec"), route)
    route["filer"]().main()
