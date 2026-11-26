"""Select the registered receipt generation and track the shared caller bytes."""

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
        repo=Path("/private/tmp/topolab-receipt-20261126-b1"),
        evidence=Path("/Users/keith1117/Documents/TopoLab-data/receipt-20261126-b1-formal"),
        identity="topolab.v2.p17-m2-registered-source-acquisition.receipt-20261126-b1.v1",
        budget="6b6cbf793c6415125d68d031c822f5e9a44eb819247756cf77c921f9e8ea49dd",
        target=(
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-receipt-20261126-b1"
        ),
        control_entry="receipt_formal_control.py",
    )
    wire.return_projection = sibling("r0_caller_receipt").project
    wire.actor_prefix = lambda actor: "receipt-formal-" + actor
    wire.protocol = "docs/planning/receipt_formal_contract.json"

    def audit_readiness_dispatch():
        entry = wire.RUNTIME_REPO / "scripts/receipt_formal_registered.py"
        subject = runpy.run_path(str(entry))["subject"]
        policy = subject.authority()
        verifier = subject.control.load("paired_readiness_independent")
        tree = subject.control.source_freeze(wire.IDENTITY)
        return verifier.audit_dispatch(
            policy, tree, wire.protocol, wire.RUNTIME_REPO, entry.name, wire.EVIDENCE
        )

    wire.audit_readiness_dispatch = audit_readiness_dispatch
    return wire
