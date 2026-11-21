"""Explicit NEW metadata entry; closed historical roles retain their defaults."""

import hashlib
import json
import os
import sys
import traceback
import types
from pathlib import Path

INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261121.v1"
RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261121.v1"


def bootstrap(*, require_locked_environment=True):
    """Install raw-source loading before the first TopoLab import."""
    path = Path(__file__).with_name("full60_input_loader.py").resolve()
    raw = path.read_bytes()
    loader = types.ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    exec(compile(raw, str(path), "exec", dont_inherit=True), loader.__dict__)
    loader.loaded_source_sha256[str(path)] = hashlib.sha256(raw).hexdigest()
    own_path = Path(__file__).resolve()
    loader.loaded_source_sha256[str(own_path)] = hashlib.sha256(own_path.read_bytes()).hexdigest()
    loader.install(require_locked_environment=require_locked_environment)
    profiles = loader.load("p17_m2_input_continuation",
                           path.with_name("p17_m2_input_continuation.py"))
    if profiles.NOV21_INPUT != INPUT or profiles.NOV21_RECOVERY != RECOVERY:
        raise ValueError("NEW metadata entry identity differs")
    subject = profiles.profile("recovery", INPUT)
    if subject.IDENTITY != RECOVERY:
        raise ValueError("NEW metadata selected another execution identity")
    subject.enable_new_metadata_mode()
    return subject


def main():
    os.umask(0o077)
    try:
        return bootstrap().main()
    except BaseException as error:
        if isinstance(error, SystemExit):
            raise
        print(json.dumps({
            "status": "STOP_NO_RETRY", "execution_identity": RECOVERY,
            "stage": "new_metadata_control", "original_source_reads": 0,
            "Foundation_helpers": 0,
            "primary_error": {"type": type(error).__name__, "reason": str(error),
                              "traceback": "".join(traceback.format_exception(error))},
            "publication_failure": getattr(error, "recovery_publication_failure", None),
            "own_future_return": "NOT_CLAIMED",
        }, sort_keys=True, separators=(",", ":"), allow_nan=False), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
