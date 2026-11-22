"""Small original command returns that bind the complete native record or binder result."""

import hashlib


def project(mode, role, plan_sha, value, raw):
    if mode not in ("record", "bind"):
        raise ValueError("unregistered compact return")
    return dict(
        schema="topolab.r0-read.native-return.v1",
        mode=mode,
        role=role,
        plan_sha256=plan_sha,
        record_bytes=len(raw),
        record_sha256=hashlib.sha256(raw).hexdigest(),
        status=value.get("status"),
        evidence_complete=value.get("evidence_complete"),
        full_role_evidence_accepted=value.get("full_role_evidence_accepted"),
        metadata_evidence_accepted=value.get("metadata_evidence_accepted"),
    )
