"""Source-only entry for the independently scheduled sealed-control verifier."""

import argparse
import hashlib
import sys
from pathlib import Path
from types import ModuleType

ENTRY = Path(__file__).resolve()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("verify", "released"))
    parser.add_argument("slots", type=int, nargs="+")
    args = parser.parse_args()
    path = ENTRY.with_name("full60_input_loader.py")
    raw = path.read_bytes()
    loader = ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path)] = hashlib.sha256(raw).hexdigest()
    loader.loaded_source_sha256[str(ENTRY)] = hashlib.sha256(ENTRY.read_bytes()).hexdigest()
    loader.install(require_locked_environment=True)
    sys.path.insert(0, str(ENTRY.parent))
    proof = loader.load("child_readiness_proof", ENTRY.with_name("child_readiness_proof.py"))
    result = (proof.verify_released(args.slots) if args.mode == "released"
              else proof.verify(args.slots))
    print(proof.canonical(result).decode(), end="")


if __name__ == "__main__":
    main()
