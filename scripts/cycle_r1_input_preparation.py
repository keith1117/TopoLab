"""Retain the formal input acceptance readiness proof and its original return."""

import argparse
import hashlib
import runpy
import sys
from pathlib import Path

ENTRY = Path(__file__).resolve()
ENTRY_SHA256 = hashlib.sha256(ENTRY.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("retain", "readiness"))
    args = parser.parse_args()
    if not sys.flags.isolated or Path.cwd() != ENTRY.parents[1]:
        raise ValueError("preparation requires the isolated checkout interpreter")
    subject = runpy.run_path(str(ENTRY.with_name("cycle_r1_registered_input.py")))["subject"]
    loader = sys.modules["full60_input_loader"]
    loader.loaded_source_sha256[str(ENTRY)] = ENTRY_SHA256
    shared = loader.load("staged_input_preparation", ENTRY.with_name("staged_input_preparation.py"))
    print(subject.producer.canonical(shared.prepare(subject, args.mode, entry=ENTRY)).decode(),
          end="")


if __name__ == "__main__":
    main()
