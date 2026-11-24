"""Replay the formal certificate from a sealed graph without entering its target."""

import hashlib
import sys
from pathlib import Path
from types import ModuleType

ENTRY = Path(__file__).resolve()
OLD = Path("/private/tmp/topolab-r1-window-20261123")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("historical", "candidate", "verify"):
        raise ValueError("choose historical, candidate or verify")
    historical = sys.argv[1] == "historical"
    scripts = OLD / "scripts" if historical else ENTRY.parent
    path = scripts / "full60_input_loader.py"
    loader = ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    raw = path.read_bytes()
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path)] = hashlib.sha256(raw).hexdigest()
    loader.loaded_source_sha256[str(ENTRY)] = hashlib.sha256(ENTRY.read_bytes()).hexdigest()
    loader.install(require_locked_environment=True)
    sys.path.insert(0, str(scripts))
    archive = loader.load(
        "certificate_replay_archive", ENTRY.with_name("certificate_replay_archive.py")
    )
    profiles = loader.load("p17_m2_input_continuation", scripts / "p17_m2_input_continuation.py")
    checker = profiles.profile("independent", profiles.WINDOW_FORMAL)
    bundle, events = archive.historical_inputs(checker)
    if historical:
        checker.audit_certificate(bundle, trusted_tool_events=events)
        raise ValueError("historical certificate unexpectedly passed")
    worker = loader.load("certificate_replay_proof", ENTRY.with_name("certificate_replay_proof.py"))
    print(worker.run(checker, bundle, events, publish=sys.argv[1] == "verify"), end="")


if __name__ == "__main__":
    main()
