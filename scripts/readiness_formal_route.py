"""Select the registered readiness generation and track the shared caller bytes."""

import hashlib
import runpy
from pathlib import Path

path = Path(__file__).resolve().with_name("formal_input_route.py")
raw = path.read_bytes()
digests = globals().get("entry_digests", {})
digests[str(path)] = hashlib.sha256(raw).hexdigest()
shared = {"__file__": str(path), "entry_digests": digests}
exec(compile(raw, str(path), "exec"), shared)
sibling = shared["sibling"]


def filer():
    wire = shared["filer"](
        repo=Path("/private/tmp/topolab-readiness-20261126"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/readiness-20261126-a1-formal"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.readiness-20261126-a1.v1",
        budget="640b7726526afdb5ea161ccfbb83fa9f3cf56d7f764561eaf892716b18118581",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-readiness-20261126-a1"
        ),
        control_entry="readiness_formal_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    wire.actor_prefix = lambda actor: "readiness-formal-" + actor
    wire.protocol = "docs/planning/readiness_formal_contract.json"

    def audit_readiness_dispatch():
        entry = wire.RUNTIME_REPO / "scripts/readiness_formal_registered.py"
        subject = runpy.run_path(str(entry))["subject"]
        policy = subject.authority()
        verifier = subject.control.load("paired_readiness_independent")
        tree = subject.control.source_freeze(wire.IDENTITY)
        return verifier.audit_dispatch(
            policy, tree, wire.protocol, wire.RUNTIME_REPO, entry.name, wire.EVIDENCE
        )

    wire.audit_readiness_dispatch = audit_readiness_dispatch
    return wire
