"""Literal paths and scopes for the once-authorized post-B1 native run."""

import re
from pathlib import Path

IDENTITY = "native-bc-entry-20261126-r2"
ATTEMPT = "native-bc-entry-20261127-r5"
FORMAL_ROOT = Path("/private/tmp/topolab-native-bc-run-20261127-r5")
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data") / ATTEMPT
# The owner settled the scope of the historical instructions before registration.
OWNER_RULING = {
    "sealed_contract": "B4.51",
    "old_AGENTS_exhausted_quotas_and_R1_only_apply_to": "sealed B4.51 only",
    "owner_decision": (
        "我明确确认，旧 AGENTS.md 中配额耗尽和仅限 R1 的条款只约束已封存的 B4.51 合同。"
        "请把这项裁定写入新合同，沿用 B1 证书，重新执行一次正式 B（FULL 180 秒）。"
        "独立核验通过后，直接将 C 生产预约提交平台正常审批，"
        "C 上限 14,580 计费秒，分项不可互借。"
        "C 完整通过后按原授权继续 H/17 新样本独立确认并归档，无需逐关再问。"
    ),
    "registration_sha256": "888db56946589f6921267380c7f6928c1e21f4c00edf48a145442108281cc0ac",
    "R4_denial_sha256": "11bbca6db6d4275c3c1085b7e867a4efe0d6cbadab7478a47b2212dab8b0b878",
}
# R2 and R3 acquired these leases. R4 stopped before acquiring one.
PREDECESSOR_LEASES = [{
    "suffix": ".cooperative-reader.lease",
    "record_sha256": "32fc008fa75302eb991931eb8623f44dab90fbd290d01389f4f2f573cc269abf",
    "identity_sha256": "0d7331527abb163b1ecba8ae46ee3d55ffbd5db32ccfd98ef7edf734f90d384f",
    "terminal_audit_sha256": "3f0ac0377e7fc80a482ea41c5562919e34c14f529720317093699024c002878e",
}, {
    "suffix": ".r3.cooperative-reader.lease",
    "record_sha256": "f6023af892a9772d3dec8b9db066e513690a34cf7464ecd20601384be5ae536f",
    "identity_sha256": "3b108613b2b9193d1efa57a57bbd9340c9ce976080dcfcb398f03726dfbb6ebe",
    "terminal_ledger_sha256": "a455e0bef0476a31951dd2e44cd47c34c9abf2c9918f3d8a6da17d30ecf336c6",
}]
PUBLIC = re.compile(r"/private/tmp/topolab-native-bc-public-20261127-r5-[a-z0-9][a-z0-9-]{0,47}")
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


def row_fixture(root):
    """Derive the public exercise solely from its registered literal root."""
    if PUBLIC.fullmatch(str(root)):
        for mode in ("rows-positive", "rows-failure", "rows-prerow"):
            if str(root).endswith("-" + mode):
                return mode
    return None
