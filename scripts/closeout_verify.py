"""Source-only independent closeout proof entry; never a Native role."""

import argparse
import hashlib
import sys
from pathlib import Path
from types import ModuleType

ENTRY = Path(__file__).resolve()


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("mode", choices=("verify",))
    parser.add_argument("slots", type=int, nargs=3)
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
    proof = loader.load("closeout_readiness_proof", ENTRY.with_name("closeout_readiness_proof.py"))
    print(proof.canonical(proof.verify(args.slots)).decode(), end="")


if __name__ == "__main__":
    main()
