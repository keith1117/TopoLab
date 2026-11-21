"""Rebuild the public fixture locally and time the R1 exporter and independent comparison.

Run with the locked environment: uv run python scripts/benchmark_public_input_r1.py.
All inputs and results are created in one new private temporary directory.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import p17_m2_content_verified_independent as public
import p17_m2_content_verified_public_fixture as fixture
import p17_m2_homotopy as storage
import p17_m2_input_export as producer
import p17_m2_input_export_independent as independent
import p17_m2_local_input_independent as local
import p17_m2_source_acquisition_control as acquisition

REPO = Path(__file__).resolve().parents[1]
WIRE_CONTRACT = REPO / "docs/planning/registered_input_20261121_contract.json"
WIRE_SHA = "b49a5542b34a74bb4209ba736acfc7b414eed90afc7d95f212f0fd9b6d4b5ba2"
REGISTRY_SHA = "5166e5e4d95e690463fd1684467eca147cd7aa7c2d3cbc41422b61f9968bd56b"
POLICY = producer.PREBOUND_SHA256_POLICY


def benchmark():
    contract_sha = producer.sha(WIRE_CONTRACT.read_bytes())
    producer.need(contract_sha == WIRE_SHA, "retained acquisition contract differs")
    parent = "/private/tmp" if sys.platform == "darwin" else "/tmp"
    root = Path(tempfile.mkdtemp(prefix="topolab-r1-benchmark-", dir=parent))
    print(f"Public software evidence: {root}", file=sys.stderr, flush=True)
    source, output = root / "source", root / "export"
    output.mkdir(mode=0o700)
    began = time.monotonic()
    contract, identity = fixture.create_sources(source, independent)
    r0 = producer.Reader(
        source, execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True
    )
    registry = producer.register(r0, contract)
    registry_bytes = producer.canonical(registry)
    producer.need(producer.sha(registry_bytes) == REGISTRY_SHA, "retained public registry differs")
    checked = public.independent_r0(source, contract, registry, r0.source_observations, identity)
    producer.need(checked["source_registry_sha256"] == REGISTRY_SHA, "independent registry differs")

    # Keep the benchmark binding distinct from every executable acquisition plan.
    binding = {
        "scope": "FRESH_SYNTHETIC_PUBLIC_SOFTWARE_ONLY",
        "source": str(source),
        "output": str(output),
        "source_registry_sha256": REGISTRY_SHA,
        "contract_sha256": contract_sha,
    }
    wire = producer.canonical(binding)
    producer.new_file(root / "benchmark-binding.json", wire)
    started = time.monotonic()
    # Use the same per-write namespace guard, fsync journal and local readback as R1.
    transport = acquisition.AcquisitionTransport(output, producer.sha(wire))
    content = transport.new_content(output / "content", registry, contract_sha)
    content.write("source_registry.json", registry_bytes)
    reader = producer.Reader(
        source,
        acquisition.base().FailureJournal(output / "source-read-journal.jsonl"),
        execution_identity=producer.LOCAL_IDENTITY,
        source_identity_checks=True,
        source_identity_policy=POLICY,
    )
    producer.export(reader, registry, contract, content.root, local_content=content)
    exported = time.monotonic()
    closed = content.finish()
    finished = time.monotonic()

    source_check = independent.OnceReader(
        source,
        558,
        852 * independent.MIB,
        source_identity_checks=True,
        source_identity_policy=POLICY,
    )
    export_check = independent.OnceReader(content.root, 1070, 301 * independent.MIB)
    comparison = independent.audit_exports(source_check, export_check, registry)
    expected = local.identity_table(reader.source_observations, 558, source_identity_policy=POLICY)
    actual = local.identity_table(source_check.observations, 558, source_identity_policy=POLICY)
    independent.compare_words(expected, actual)
    verified = local.audit_local_content(
        content.root, closed["manifest"], registry, closed["local_identity_rows"], contract_sha
    )
    independent.require(verified["version_id"] == closed["version_id"], "version differs")
    audited = time.monotonic()
    result = {
        "scope": binding["scope"],
        "root": str(root),
        "source_registry_sha256": REGISTRY_SHA,
        "contract_sha256": contract_sha,
        "source_bytes": sum(row["byte_size"] for row in reader.rows),
        "producer_reads": len(reader.rows),
        "independent_reads": len(source_check.observations),
        "manifest_members": len(closed["manifest"]["members"]),
        "independently_verified_members": verified["new_member_reads"],
        "compared_fields": comparison["compared_scalar_fields"],
        "version_id": closed["version_id"],
        "seconds": {
            "prepare_and_r0": started - began,
            "export": exported - started,
            "finish": finished - exported,
            "independent": audited - finished,
        },
    }
    storage.atomic_new(root / "result.json", result)
    return result


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("usage: python scripts/benchmark_public_input_r1.py")
    os.umask(0o077)
    print(json.dumps(benchmark(), sort_keys=True))
