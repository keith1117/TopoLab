"""Wait for paired original returns within the single formal input acceptance grant."""

import hashlib
from pathlib import Path

if __name__ == "__main__":
    entry = Path(__file__).resolve()
    path = entry.with_name("cycle_r1_input_route.py")
    raw = path.read_bytes()
    route = {"__file__": str(path), "entry_digests": {
        str(entry): hashlib.sha256(entry.read_bytes()).hexdigest(),
        str(path): hashlib.sha256(raw).hexdigest(),
    }}
    exec(compile(raw, str(path), "exec"), route)
    wire = route["filer"]()
    window = route["sibling"]("cycle_input_window")
    route["sibling"]("staged_input_waiter", wire=wire, window=window).main()
