"""Collect new ELF/stack/call-closure evidence; never issue independent admission."""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMITS = {"query": 512 * 1024**2, "audit": 512 * 1024**2, "controller": 64 * 1024**2}
EXPECTED_SOURCES = {
    "query": {"query.c", "vectors.c", "readers.c", "query_main.c", "sha256.c"},
    "audit": {"audit.c", "audit_main.c", "sha256.c"},
    "controller": {"controller.c", "sealed_child.c", "sha256.c"},
}


def elf_loads(raw: bytes) -> dict[str, object]:
    if len(raw) < 64 or raw[:7] != b"\x7fELF\x02\x01\x01":
        raise ValueError("expected ELF64 little-endian")
    fields = struct.unpack_from("<16sHHIQQQIHHHHHH", raw)
    if fields[1:3] != (2, 62):
        raise ValueError("expected static x86-64 executable")
    offset, size, count = fields[5], fields[9], fields[10]
    if size != 56 or not 1 <= count <= 32 or offset + size * count > len(raw):
        raise ValueError("invalid ELF program headers")
    intervals = []
    headers = []
    for i in range(count):
        kind, flags, file_offset, address, _, file_size, memory_size, alignment = (
            struct.unpack_from("<IIQQQQQQ", raw, offset + i * size)
        )
        if kind in (2, 3, 7):
            raise ValueError("dynamic/TLS/interpreter segment is not in the I1 runtime closure")
        if kind == 1:
            if file_size > memory_size or file_offset + file_size > len(raw) or flags & 3 == 3:
                raise ValueError("invalid or writable-executable LOAD")
            start, end = address // 4096 * 4096, (address + memory_size + 4095) // 4096 * 4096
            intervals.append((start, end))
            headers.append(
                {
                    "start": start,
                    "end": end,
                    "flags": flags,
                    "file_bytes": file_size,
                    "memory_bytes": memory_size,
                    "alignment": alignment,
                }
            )
        if kind == 0x6474E551 and flags & 1:
            raise ValueError("executable stack")
    if not intervals:
        raise ValueError("no LOAD segments")
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return {"mapped_load_bytes": sum(b - a for a, b in merged), "load_segments": headers}


def inspect(directory: Path) -> dict[str, object]:
    if (
        platform.system() != "Linux"
        or platform.machine() != "x86_64"
        or os.sysconf("SC_PAGESIZE") != 4096
    ):
        raise RuntimeError("selected Linux x86-64/4096-byte-page environment required")
    build = json.loads((directory / "build.json").read_text())
    records = {}
    for role in LIMITS:
        binary = directory / f"i1-{role}"
        raw = binary.read_bytes()
        if hashlib.sha256(raw).hexdigest() != build["roles"][role]["sha256"]:
            raise ValueError("build identity changed")
        loads = elf_loads(raw)
        if len(raw) > 2097152 or loads["mapped_load_bytes"] > LIMITS[role]:
            raise ValueError("binary exceeds its fixed implementation envelope")
        expected_sources = {
            "native/i1/" + name
            for name in EXPECTED_SOURCES[role]
            | {"runtime.c", "start.S", "query.h", "audit.h", "runtime.h"}
        }
        if set(build["roles"][role]["sources"]) != expected_sources:
            raise ValueError("unregistered source/header path")
        for source, expected in build["roles"][role]["sources"].items():
            if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != expected:
                raise ValueError("native source changed after build")
        if (
            role == "controller"
            and hashlib.sha256((directory / "hashes.h").read_bytes()).hexdigest()
            != build["generated_hash_header_sha256"]
        ):
            raise ValueError("generated child identity header changed")
        for name, expected in build["roles"][role]["stack_files"].items():
            if (
                Path(name).name != name
                or not name.startswith(f"i1-{role}-")
                or not name.endswith(".su")
            ):
                raise ValueError("unregistered compiler-frame path")
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
                raise ValueError("compiler-frame identity changed")
        for name, key in (
            (f"{role}.map", "link_map_sha256"),
            (f"{role}-compiler.txt", "compiler_trace_sha256"),
        ):
            if (
                hashlib.sha256((directory / name).read_bytes()).hexdigest()
                != build["roles"][role][key]
            ):
                raise ValueError("compiler/link-map identity changed")
        evidence = {}
        for tool, arguments in (
            ("readelf", ["-lW"]),
            ("nm", ["--undefined-only"]),
            ("objdump", ["-drwC"]),
        ):
            executable = shutil.which(tool)
            if executable is None:
                raise RuntimeError(f"missing {tool}")
            text = subprocess.check_output([executable, *arguments, str(binary)], text=True)
            name = f"{role}-{tool}.txt"
            (directory / name).write_text(text)
            evidence[tool] = {
                "path": name,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "tool_sha256": hashlib.sha256(Path(executable).resolve().read_bytes()).hexdigest(),
            }
            if tool == "nm" and text.strip():
                raise ValueError("unresolved runtime helper")
            if tool == "objdump" and re.search(r"\bcallq?\s+\*|\bjmpq?\s+\*", text):
                raise ValueError("indirect code target requires a separate closure")
        stack = []
        for path in sorted(directory.glob(f"i1-{role}-*.su")):
            for line in path.read_text().splitlines():
                origin, amount, qualifier = line.rsplit("\t", 2)
                stack.append({"origin": origin, "bytes": int(amount), "kind": qualifier})
        if not stack or any(s["kind"] not in ("static", "dynamic,bounded") for s in stack):
            raise ValueError("missing or unbounded individual compiler stack records")
        # Sum every function frame conservatively. This still needs independent
        # call-graph/startup/stack-growth proof; it is not a complete certificate.
        value_frames = [
            s["bytes"]
            for s in stack
            if s["origin"].split("\t")[-1].split(":")[-1].startswith("value")
        ]
        frame_sum = sum(s["bytes"] for s in stack) + 17 * max(value_frames, default=0) + 39
        records[role] = {
            **loads,
            "individual_frames": stack,
            "conservative_frame_sum_bytes": frame_sum,
            "entry_alignment_save_and_call_bytes": 15 + 16 + 8,
            "evidence": evidence,
            "source_binary_runtime_complete_bound": "UNKNOWN_PENDING_INDEPENDENT_REVIEW",
        }
    record = {
        "schema": "topolab.i1.public-elf-inspection.v1",
        "roles": records,
        "kernel_release": platform.release(),
        "os_release": Path("/etc/os-release").read_text(),
        "runner_image": {n: os.environ.get(n, "UNKNOWN") for n in ("ImageOS", "ImageVersion")},
        "whole_role_4GiB_admission": "UNKNOWN_NOT_GRANTED",
        "unresolved_terms": [
            "independent source-to-binary result for registered audit role",
            "complete startup/auxiliary mappings",
            "source-to-binary call-graph and recursion/stack-growth closure",
            "all fork/exec/sealed-carrier/error/exit overlap",
        ],
        "scientific_input_reads": 0,
        "caveat": (
            "ELF/compiler-frame evidence is partial; no snapshot or monitor substitutes "
            "for a complete independent allocation/lifetime proof."
        ),
    }
    (directory / "inspection.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    inspect(parser.parse_args().directory.resolve())
