"""Explicit 2026-11-21 whole4500 control entry; closed identities are never selected."""

import sys
import types
from pathlib import Path

path = Path(__file__).with_name("full60_input_loader.py")
loader = sys.modules.get("full60_input_loader")
if loader is None or Path(loader.__file__).resolve() != path.resolve():
    loader = types.ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    raw = path.read_bytes()
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path.resolve())] = loader.hashlib.sha256(raw).hexdigest()
entry = Path(__file__).resolve()
loader.loaded_source_sha256[str(entry)] = loader.hashlib.sha256(entry.read_bytes()).hexdigest()
loader.install(require_locked_environment=True)
profiles = loader.load("p17_m2_input_continuation", path.with_name("p17_m2_input_continuation.py"))
subject = profiles.profile("control", profiles.NOV21_INPUT)

if __name__ == "__main__":
    if sys.argv[1:] == ["--help"]:
        print("usage: input_control_20261121.py MODE --root ROOT [frozen arguments]")
        raise SystemExit(0)
    raise SystemExit(subject.main())
