"""Start the independent public timing audit from source in the isolated checkout."""
import hashlib
import sys
from pathlib import Path
from types import ModuleType

if __name__ == "__main__":
    entry = Path(__file__).resolve()
    path = entry.with_name("full60_input_loader.py")
    loader = ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    raw = path.read_bytes()
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path)] = hashlib.sha256(raw).hexdigest()
    loader.loaded_source_sha256[str(entry)] = hashlib.sha256(entry.read_bytes()).hexdigest()
    loader.install(require_locked_environment=True)
    sys.path.insert(0, str(entry.parent))
    worker = loader.load("r1_window_proof", entry.with_name("r1_window_proof.py"))
    worker.main()
