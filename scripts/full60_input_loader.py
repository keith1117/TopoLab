"""Source-only imports for the explicitly selected NEW input process tree.

Installed by neutral entries before importing any TopoLab module. Valid timestamp
bytecode is not authority for frozen source. Historical entry points retain their
existing loaders; this bootstrap grants no role, path or input access.
"""

import hashlib
import importlib
import importlib.machinery
import importlib.util
import site
import sys
import tomllib
from pathlib import Path

loaded_source_sha256 = {}


def install(*, require_locked_environment=False):
    def source_code(loader, fullname):
        raw = loader.get_data(loader.path)
        loaded_source_sha256[str(Path(loader.path).resolve())] = hashlib.sha256(raw).hexdigest()
        return compile(raw, loader.path, "exec", dont_inherit=True)

    importlib.machinery.SourceFileLoader.get_code = source_code
    sys.dont_write_bytecode = True
    if not require_locked_environment:
        return  # Pure source-loader fixtures grant no live runtime admission.
    repo = Path(__file__).resolve().parents[1]
    packages = (repo / ".venv" / "lib" / "python3.12" / "site-packages").resolve()
    if not packages.is_dir():
        raise ValueError("NEW locked checkout environment is unavailable")
    for name in ("numpy", "scipy", "pydantic", "torch"):
        loaded = sys.modules.get(name)
        if loaded is not None and not Path(loaded.__file__).resolve().is_relative_to(packages):
            raise ValueError("NEW runtime already loaded outside locked checkout: " + name)
    # Install the source hook before .pth execution and exclude global third-party
    # search paths. Any added editable path remains behind the locked site.
    sys.path[:] = [p for p in sys.path if "site-packages" not in Path(p).parts]
    site.addsitedir(str(packages))
    sys.path.remove(str(packages))
    sys.path.insert(0, str(packages))
    versions = {
        p["name"]: p["version"] for p in tomllib.loads((repo / "uv.lock").read_text())["package"]
    }
    for name in ("numpy", "scipy", "pydantic"):
        module = importlib.import_module(name)
        if (
            not Path(module.__file__).resolve().is_relative_to(packages)
            or module.__version__ != versions[name]
        ):
            raise ValueError("NEW locked dependency origin/version differs: " + name)


def load(name, path):
    path = Path(path).resolve()
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() == path:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("NEW source-only module unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_loaded(repo, frozen):
    for relative, expected in frozen.items():
        observed = loaded_source_sha256.get(str((Path(repo) / relative).resolve()))
        if observed is not None and observed != expected:
            raise ValueError("NEW executed source differs from frozen bytes: " + relative)
