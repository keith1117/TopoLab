"""Literal paths and scopes for the once-authorized post-B1 native run."""

import re
from pathlib import Path

IDENTITY = "native-bc-entry-20261126-r2"
FORMAL_ROOT = Path("/private/tmp/topolab-native-bc-run-20261126-r2")
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data") / IDENTITY
PUBLIC = re.compile(r"/private/tmp/topolab-native-bc-public-20261126-r2-[a-z0-9][a-z0-9-]{0,47}")
HISTORICAL = "d30c33b198099c09ee9c1fb7bbc14f43f8cf1676"
PLAN = "d26d69bb62ff1488e12a52f2872f07ce00eac92eb4bd30413b53925411d4f739"
VERSION = "94e1ccdd7629cfbb697797da4235351c1fdefbcde8c40085dd0876ab3b6b23a7"


def scope(root):
    if str(root) == str(FORMAL_ROOT):
        return "PROTECTED_MAIN"
    if PUBLIC.fullmatch(str(root)):
        return "ENGINEERING_PUBLIC"
    raise ValueError("unregistered post-B1 scientific root")


def public_contract_path(root):
    if scope(root) != "ENGINEERING_PUBLIC":
        raise ValueError("registered public fixture required")
    return Path(str(root) + ".contract.json")


def is_public_contract_path(path):
    name = str(path)
    return name.endswith(".contract.json") and PUBLIC.fullmatch(name[: -len(".contract.json")])
