"""Control entry for the November 23 formal input acceptance contract."""

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
# Registration helpers use bare imports from this frozen source directory.
sys.path.insert(0, str(path.parent))
profiles = loader.load("p17_m2_input_continuation", path.with_name("p17_m2_input_continuation.py"))
subject = profiles.profile("control", profiles.CYCLE_R1_INPUT)

if __name__ == "__main__":
    if sys.argv[1:] == ["--help"]:
        print("usage: cycle_r1_input_control.py MODE --root ROOT [frozen arguments]")
        raise SystemExit(0)
    raise SystemExit(subject.main())
