"""Fixed November 22 formal-only caller configuration."""

import hashlib
import types
from pathlib import Path

REPO = Path("/private/tmp/topolab-formal-input-20261122")
DIR = Path(__file__).resolve().parent
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data/formal-input-20261122")
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.formal-20261122.v1"
BUDGET = "96c2a727428bb7d30c8d2c00dee43c1f42c7f55b73660959cc51c8c33db33f7b"
TARGET = ("/Users/keith1117/Library/Application Support/TopoLab-custody/"
          "p17-m2-formal-input-20261122-a1")


SOURCE_DIGESTS = globals().get('entry_digests', {})


def sibling(name, **bindings):
    path = DIR / (name + ".py")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    raw = path.read_bytes()
    SOURCE_DIGESTS[str(path.resolve())] = hashlib.sha256(raw).hexdigest()
    module.__dict__.update(bindings)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def filer():
    module = sibling("staged_input_filer")
    module.SOURCE_DIGESTS = SOURCE_DIGESTS
    module.RUNTIME_REPO = REPO
    module.EVIDENCE = EVIDENCE
    module.BACKUP = EVIDENCE.with_name(EVIDENCE.name + "-backup")
    module.IDENTITY = IDENTITY
    module.BUDGET_SHA = BUDGET
    module.FORMAL = TARGET
    module.ROOTS = (TARGET,)
    module.CONTROL_ENTRY = "formal_input_control.py"
    return module
