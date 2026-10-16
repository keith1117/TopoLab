"""Reproduce I1 ELF/call/frame facts from an explicitly hash-bound evidence set.

This independent offline reviewer never imports the primary inspector and never
executes a target ELF or accesses a network. A successful run is still UNKNOWN
for complete resource admission: initial stack P, kernel maps K, selected-host
pre-entry transients, merged identity and actual startup/exit require the review.

Inputs are fixed named I1 artifacts, not paths discovered from research records.
Only git cat-file of explicitly requested committed native source is executed;
lazy fetching, all Git transport protocols and fsmonitor are disabled. Artifacts,
source blobs, parser cardinalities, work states and outputs have explicit caps.
These caps are parser refusal conditions, never a native resource proof.
"""

import argparse
import hashlib
import json
import os
import pathlib
import re
import selectors
import shlex
import stat
import struct
import subprocess
import time

MAX_MANIFEST = 131072
MAX_SOURCE = 262144
MAX_OUTPUT = 16777216
MAX_FUNCTIONS = 512
MAX_INSTRUCTIONS = 65536
ROLES = {
    "query": ("query.c", "vectors.c", "readers.c", "query_main.c", "sha256.c"),
    "audit": ("audit.c", "audit_main.c", "sha256.c"),
    "controller": ("controller.c", "sealed_child.c", "sha256.c"),
}
LIMITS = {
    "build.json": 131072,
    "gcc-specs.txt": 262144,
    "hashes.h": 4096,
    "inspection.json": 262144,
}
for _role, _sources in ROLES.items():
    LIMITS["i1-" + _role] = 2097152
    for _suffix, _cap in (
        ("compiler.txt", 1048576),
        ("objdump.txt", 4194304),
        ("readelf.txt", 65536),
        ("nm.txt", 65536),
    ):
        LIMITS[_role + "-" + _suffix] = _cap
    LIMITS[_role + ".map"] = 262144
    for _source in (*_sources, "runtime.c"):
        LIMITS["i1-" + _role + "-" + _source[:-2] + ".su"] = 65536


def require(condition, message):
    if not condition:
        raise ValueError(str(message)[:400])


def hash256(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    require(isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value), "invalid SHA-256")
    return value


def read_fd_file(directory, name, cap):
    require(name in LIMITS, "unregistered artifact name")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
    try:
        info = os.fstat(fd)
        require(
            stat.S_ISREG(info.st_mode) and 0 <= info.st_size <= cap,
            "nonregular or oversized artifact",
        )
        with os.fdopen(fd, "rb", closefd=False) as stream:
            value = stream.read(cap + 1)
        require(
            len(value) == info.st_size and len(value) <= cap, "artifact changed or exceeded cap"
        )
        return value
    finally:
        os.close(fd)


def bounded_literal(path, cap):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(
            stat.S_ISREG(info.st_mode) and 0 <= info.st_size <= cap,
            "nonregular or oversized explicit file",
        )
        with os.fdopen(fd, "rb", closefd=False) as stream:
            value = stream.read(cap + 1)
        require(len(value) == info.st_size and len(value) <= cap, "file changed or cap exceeded")
        return value
    finally:
        os.close(fd)


def git_blob(repository, source, path):
    # No shell, hooks, diff/textconv, remote operation or payload-derived argv.
    expected = {
        "native/i1/" + n
        for n in (
            "query.c",
            "vectors.c",
            "readers.c",
            "query_main.c",
            "sha256.c",
            "audit.c",
            "audit_main.c",
            "controller.c",
            "sealed_child.c",
            "runtime.c",
            "start.S",
            "query.h",
            "audit.h",
            "runtime.h",
        )
    }
    require(path in expected, "unregistered committed source path")
    command = [
        "/usr/bin/git",
        "-C",
        str(repository),
        "-c",
        "protocol.allow=never",
        "-c",
        "core.fsmonitor=false",
        "cat-file",
        "blob",
        source + ":" + path,
    ]
    environment = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    child = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=environment
    )
    value = bytearray()
    try:
        require(child.stdout is not None, "missing Git pipe")
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 10
            while True:
                remaining = deadline - time.monotonic()
                require(remaining > 0, "Git source read timed out")
                require(selector.select(remaining), "Git source read timed out")
                chunk = os.read(child.stdout.fileno(), min(65536, MAX_SOURCE + 1 - len(value)))
                if not chunk:
                    break
                value.extend(chunk)
                require(len(value) <= MAX_SOURCE, "committed source exceeds cap")
        require(child.wait(timeout=1) == 0, "committed source unavailable; no fetch allowed")
        return bytes(value)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=1)
        if child.stdout is not None:
            child.stdout.close()


def load_evidence(args):
    require(re.fullmatch("[0-9a-f]{40}", args.source_sha), "explicit full source SHA required")
    require(
        args.evidence_dir.is_absolute() and args.repository.is_absolute(),
        "explicit absolute evidence/repository directory required",
    )
    raw = bounded_literal(args.identity_manifest, MAX_MANIFEST)
    require(hash256(raw) == digest(args.identity_sha256), "identity manifest hash mismatch")
    ident = json.loads(raw)
    require(
        isinstance(ident, dict) and ident.get("source_sha") == args.source_sha,
        "manifest source mismatch",
    )
    records = ident.get("files")
    require(isinstance(records, list) and len(records) == len(LIMITS), "wrong member count")
    # Open only the explicit directory and fixed basenames; never follow a manifest pointer.
    require(not args.evidence_dir.is_symlink(), "symlink evidence directory")
    directory = os.open(args.evidence_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    files = {}
    try:
        for record in records:
            require(isinstance(record, dict), "invalid member record")
            name = record.get("path")
            require(isinstance(name, str) and len(name) <= 4096, "invalid member path")
            path = pathlib.Path(name)
            require(
                path.parent in (pathlib.Path("."), args.evidence_dir),
                "manifest path outside explicit evidence directory",
            )
            require(path.name in LIMITS and path.name not in files, "unknown/duplicate member")
            size = record.get("bytes")
            require(type(size) is int and 0 <= size <= LIMITS[path.name], "invalid member size")
            value = read_fd_file(directory, path.name, LIMITS[path.name])
            require(
                len(value) == size and hash256(value) == digest(record.get("sha256")),
                "member length/hash mismatch: " + path.name,
            )
            files[path.name] = value
    finally:
        os.close(directory)
    require(set(files) == set(LIMITS), "incomplete evidence set")
    build = json.loads(files["build.json"])
    require(
        isinstance(build, dict) and set(build.get("roles", {})) == set(ROLES), "invalid build roles"
    )
    require(
        hash256(files["gcc-specs.txt"]) == build["gcc_builtin_specs_sha256"],
        "GCC specs hash mismatch",
    )
    require(
        hash256(files["hashes.h"]) == build["generated_hash_header_sha256"],
        "generated hash header mismatch",
    )
    for role, sources in ROLES.items():
        meta = build["roles"][role]
        expected = {
            "native/i1/" + n
            for n in (*sources, "runtime.c", "start.S", "query.h", "audit.h", "runtime.h")
        }
        require(set(meta["sources"]) == expected, "unexpected source/header set")
        for path, sha in meta["sources"].items():
            require(
                hash256(git_blob(args.repository, args.source_sha, path)) == digest(sha),
                "source/header differs from explicit commit",
            )
        require(
            set(meta["stack_files"])
            == {"i1-" + role + "-" + n[:-2] + ".su" for n in (*sources, "runtime.c")},
            "unexpected frame-file set",
        )
    return ident, files, build


def validate_elf_shape(value):
    require(len(value) >= 64 and value[:7] == b"\x7fELF\x02\x01\x01", "ELF identity")
    h = struct.unpack_from("<16sHHIQQQIHHHHHH", value)
    require(h[8] == 64 and h[9] == 56 and 1 <= h[10] <= 64, "ELF program header bounds")
    require(h[11] == 64 and 1 <= h[12] <= 128 and h[13] < h[12], "ELF section bounds")
    require(h[5] + h[9] * h[10] <= len(value), "program table outside file")
    require(h[6] + h[11] * h[12] <= len(value), "section table outside file")
    for i in range(h[10]):
        p = struct.unpack_from("<IIQQQQQQ", value, h[5] + i * h[9])
        require(p[2] + p[5] <= len(value), "segment outside file")
        require(p[6] <= 536870912 and p[3] + p[6] < 2**47, "segment cardinality cap")
        require(
            p[0] in (1, 4, 0x6474E551) and p[1] in (0, 4, 5, 6), "unreviewed segment type/flags"
        )
    for i in range(h[12]):
        s = struct.unpack_from("<IIQQQQIIQQ", value, h[6] + i * h[11])
        require(s[1] == 8 or s[4] + s[5] <= len(value), "section outside file")
        require(s[6] < h[12], "section link outside table")
        if s[2] & 4:
            require(s[1] == 1, "executable section must contain file bytes")
        if s[1] == 2:
            require(s[9] == 24 and s[5] % 24 == 0 and s[5] // 24 <= 4096, "symbol cardinality cap")


def arguments(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--repository", required=True, type=pathlib.Path)
    parser.add_argument("--evidence-dir", required=True, type=pathlib.Path)
    parser.add_argument("--identity-manifest", required=True, type=pathlib.Path)
    parser.add_argument("--identity-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    return parser, parser.parse_args()


def write_review(args, name, result):
    require(args.output_dir.is_absolute(), "absolute fresh output directory required")
    require(
        not args.output_dir.exists() and not args.output_dir.is_symlink(),
        "output directory must be fresh",
    )
    data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    require(len(data) <= MAX_OUTPUT, "output size cap")
    args.output_dir.mkdir(parents=False, exist_ok=False)
    directory = os.open(args.output_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(
            name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    finally:
        os.close(directory)
    print(
        json.dumps(
            {"status": "UNKNOWN_NOT_RESOURCE_ADMITTED", "file": name, "sha256": hash256(data)}
        )
    )


def cstring(b, off):
    require(0 <= off < len(b), "string offset")
    end = b.find(bytes([0]), off, min(len(b), off + 1024))
    require(end >= 0, "bounded string terminator")
    return b[off:end].decode()


def elf(b):
    validate_elf_shape(b)
    require(b[:7] == b"\x7fELF\x02\x01\x01", "independent structural condition line 9")
    h = struct.unpack_from("<16sHHIQQQIHHHHHH", b)
    require(h[1:4] == (2, 62, 1), "independent structural condition line 11")
    ph = [struct.unpack_from("<IIQQQQQQ", b, h[5] + i * h[9]) for i in range(h[10])]
    sh = [struct.unpack_from("<IIQQQQIIQQ", b, h[6] + i * h[11]) for i in range(h[12])]
    names = b[sh[h[13]][4] : sh[h[13]][4] + sh[h[13]][5]]
    sections = [(cstring(names, s[0]), s) for s in sh]
    symbols = []
    for _, s in sections:
        if s[1] != 2:
            continue
        strings = sh[s[6]]
        strings = b[strings[4] : strings[4] + strings[5]]
        require(s[9] == 24, "independent structural condition line 22")
        for off in range(s[4], s[4] + s[5], s[9]):
            n, info, other, ndx, value, size = struct.unpack_from("<IBBHQQ", b, off)
            symbols.append(
                dict(
                    name=cstring(strings, n),
                    type=info & 15,
                    binding=info >> 4,
                    section=ndx,
                    value=value,
                    size=size,
                    other=other,
                )
            )
    loads = [p for p in ph if p[0] == 1]
    pages = []
    for p in loads:
        require(p[5] <= p[6], "independent structural condition line 30")
        require(p[2] % 4096 == p[3] % 4096, "independent structural condition line 31")
        pages.append((p[3] // 4096, (p[3] + p[6] + 4095) // 4096))
    ex = [(n, s) for n, s in sections if s[2] & 4]
    forbidden = [p[0] for p in ph if p[0] in (2, 3, 7)]
    require(not forbidden, "independent structural condition line 35")
    require(
        not [s for n, s in sections if s[1] in (4, 9) and s[5]],
        "independent structural condition line 36",
    )
    require(
        not [s for s in symbols if s["name"] and s["section"] == 0],
        "independent structural condition line 37",
    )
    require(
        not [s for s in symbols if s["type"] in (6, 10)], "independent structural condition line 38"
    )
    require(
        [p[1] for p in ph if p[0] == 1685382481] == [6], "independent structural condition line 39"
    )
    union = 0
    previous_end = 0
    for start, end in sorted(pages):
        union += max(0, end - max(start, previous_end))
        previous_end = max(previous_end, end)
    return (h, ph, loads, sections, symbols, ex, union * 4096)


def sccs(graph):
    seen, order, reverse = (set(), [], {n: set() for n in graph})

    def visit(n):
        if n in seen:
            return
        seen.add(n)
        for d in graph[n]:
            visit(d)
        order.append(n)

    for n in graph:
        for d in graph[n]:
            reverse[d].add(n)
        visit(n)
    seen.clear()
    result = []

    def rev(n, group):
        if n in seen:
            return
        seen.add(n)
        group.append(n)
        for d in reverse[n]:
            rev(d, group)

    for n in reversed(order):
        group = []
        rev(n, group)
        if group:
            result.append(sorted(group))
    return result


def review_evidence(options):
    ident, files, build = load_evidence(options)
    result = {
        "source_sha": options.source_sha,
        "scope": "OFFLINE_ACTUAL_BINARY_FACTS_NOT_RESOURCE_ADMISSION",
        "inspection_json_used_as_oracle": False,
        "elf_executed": False,
        "roles": {},
    }
    for role, meta in build["roles"].items():
        b = files["i1-" + role]
        require(
            hashlib.sha256(b).hexdigest() == meta["sha256"] == ident["binaries"][role],
            "independent structural condition line 70",
        )
        for k, n in (
            ("compiler_trace_sha256", role + "-compiler.txt"),
            ("link_map_sha256", role + ".map"),
        ):
            require(
                hashlib.sha256(files[n]).hexdigest() == meta[k],
                "independent structural condition line 72",
            )
        for n, sha in meta["stack_files"].items():
            require(
                hashlib.sha256(files[n]).hexdigest() == sha,
                "independent structural condition line 74",
            )
        require(files[role + "-nm.txt"] == b"", "independent structural condition line 75")
        h, ph, loads, sections, symbols, ex, mapped = elf(b)
        require(
            mapped <= (67108864 if role == "controller" else 536870912),
            "role ELF mapped envelope exceeded",
        )
        funcs = sorted((dict(s) for s in symbols if s["type"] == 2), key=lambda s: s["value"])
        require(1 <= len(funcs) <= MAX_FUNCTIONS, "function cap")
        require(
            len({s["name"] for s in funcs}) == len(funcs),
            "independent structural condition line 79",
        )
        for i, f in enumerate(funcs):
            if not f["size"]:
                f["size"] = (
                    funcs[i + 1]["value"]
                    if i + 1 < len(funcs)
                    else max((s[3] + s[5] for _, s in ex))
                ) - f["value"]

        require(
            next((f["value"] for f in funcs if f["name"] == "_start"), None) == h[4],
            "entry does not equal named _start",
        )
        for index, function in enumerate(funcs):
            require(0 < function["size"] <= len(b), "invalid function size")
            require(
                any(
                    section[3] <= function["value"]
                    and function["value"] + function["size"] <= section[3] + section[5]
                    for _, section in ex
                ),
                "function outside executable section",
            )
            if index + 1 < len(funcs):
                require(
                    function["value"] + function["size"] <= funcs[index + 1]["value"],
                    "overlapping function symbols",
                )

        def function_at(addr, functions=funcs):
            return next(
                (f["name"] for f in functions if f["value"] <= addr < f["value"] + f["size"]), None
            )

        def file_offset(addr, size, segments=loads):
            p = next(p for p in segments if p[3] <= addr and addr + size <= p[3] + p[5])
            return p[2] + addr - p[3]

        graph = {f["name"]: set() for f in funcs}
        covered = set()
        branches = []
        syscalls = []
        indirect = []
        holes = []
        instructions = []
        lines = files[role + "-objdump.txt"].decode().splitlines()
        require(len(lines) <= MAX_INSTRUCTIONS + MAX_FUNCTIONS + 32, "disassembly line cap")
        for line in lines:
            require(len(line) <= 4096, "disassembly line length cap")
            m = re.match("\\s*([0-9a-f]+):\\s+((?:[0-9a-f]{2}[ \\t]+)+)(.*)$", line)
            if not m:
                continue
            addr = int(m[1], 16)
            code = bytes.fromhex(m[2])
            asm = m[3].strip()
            require(1 <= len(code) <= 15, "instruction byte length")
            off = file_offset(addr, len(code))
            require(b[off : off + len(code)] == code, "independent structural condition line 99")
            for a in range(addr, addr + len(code)):
                require(a not in covered, "independent structural condition line 101")
                covered.add(a)
            instructions.append((addr, code.hex(), asm))
            if not asm:
                continue
            op = asm.split()[0]
            source = function_at(addr)
            if op in ("syscall", "sysenter", "int"):
                syscalls.append([hex(addr), source, asm])
            if op.startswith("call") or op.startswith("j") or op.startswith("loop"):
                if "*" in asm:
                    indirect.append([hex(addr), source, asm])
                    continue
                m2 = re.match("\\S+\\s+([0-9a-f]+)\\b", asm)
                require(m2, (addr, asm))
                dest = int(m2[1], 16)
                target = function_at(dest)
                require(source is not None and target is not None, (addr, asm))
                require(
                    dest in covered or any((s[3] <= dest < s[3] + s[5] for _, s in ex)),
                    "independent structural condition line 114",
                )
                if op.startswith("call") or target != source:
                    graph[source].add(target)
                    branches.append([hex(addr), source, target, asm])
        for n, s in ex:
            missing = set(range(s[3], s[3] + s[5])) - covered
            if missing:
                holes.append({"section": n, "uncovered_byte_count": len(missing)})
        require(len(instructions) <= MAX_INSTRUCTIONS, "instruction cap")
        require(not holes, "independent structural condition line 121")
        require(not indirect, "independent structural condition line 122")
        starts = {a for a, _, _ in instructions}
        for _, _, _, asm in branches:
            require(int(asm.split()[1], 16) in starts, "branch target is not an instruction")
        frames = {}
        for n in meta["stack_files"]:
            for line in files[n].decode().splitlines():
                loc, amount, kind = line.split("\t")
                name = loc.rsplit(":", 1)[1]
                require(
                    kind in ("static", "dynamic,bounded") and 0 <= int(amount) <= 1048576,
                    "frame cap/kind",
                )
                matches = [
                    f["name"]
                    for f in funcs
                    if f["name"] == name or re.sub("\\.\\d+$", "", f["name"]) == name
                ]
                require(len(matches) == 1, (role, name, matches))
                name = matches[0]
                require(name not in frames, "independent structural condition line 135")
                frames[name] = {"bytes": int(amount), "kind": kind, "file": n}
        require(set(graph) - set(frames) == {"_start"}, "independent structural condition line 137")
        recursive = [g for g in sccs(graph) if len(g) > 1 or g[0] in graph[g[0]]]
        require(
            recursive == ([["value"]] if role == "query" else []),
            "independent structural condition line 139",
        )
        # Count every actual C function once, plus the parser's other17 instances.
        # Accepted depths0..16 and rejecting17 require independent source review.
        # Add128-byte red zone and8-byte return per instance even if GCC included
        # them already;39 covers entry alignment, scratch and call. These terms
        # are structural upper bounds, not guessed headroom or startup P/K.
        extra = 17 if role == "query" else 0
        instances = len(frames) + extra
        frame_sum = (
            sum(x["bytes"] for x in frames.values())
            + extra * frames.get("value", {"bytes": 0})["bytes"]
        )
        descent = 39 + frame_sum + instances * (128 + 8)
        page_growth = (descent + 4095) // 4096 * 4096
        trace = files[role + "-compiler.txt"].decode()
        object_sources = {}
        pending = None
        link_objects = None
        plugins = []
        default_flags = set()
        for line in trace.splitlines():
            if not (line.startswith(" /") or line.startswith(" as ")):
                continue
            args = shlex.split(line)
            exe = pathlib.Path(args[0]).name
            if exe == "cc1":
                source = [a for a in args[1:] if a.startswith("/") and a.endswith((".c", ".S"))]
                require(len(source) == 1, "independent structural condition line 158")
                pending = source[0]
                default_flags.update(
                    a
                    for a in args
                    if a
                    in (
                        "-D_FORTIFY_SOURCE=3",
                        "-fstack-clash-protection",
                        "-fcf-protection",
                        "-Wformat-security",
                    )
                )
            elif exe.endswith("-as") or exe == "as":
                require(pending, "independent structural condition line 162")
                obj = args[args.index("-o") + 1]
                object_sources[obj] = pending
                pending = None
            elif exe == "collect2":
                link_objects = [a for a in args if a.endswith(".o")]
                plugins = [a for a in args if "liblto_plugin.so" in a or "lto-wrapper" in a]
        require(
            link_objects and set(link_objects) == set(object_sources),
            "independent structural condition line 168",
        )
        map_objects = re.findall("^LOAD (\\S+)$", files[role + ".map"].decode(), re.M)
        require(map_objects == link_objects, "independent structural condition line 170")
        source_basenames = {
            pathlib.Path(p).name for p in meta["sources"] if p.endswith((".c", ".S"))
        }
        require(
            {pathlib.Path(p).name for p in object_sources.values()} == source_basenames,
            "independent structural condition line 172",
        )
        result["roles"][role] = {
            "binary_sha256": meta["sha256"],
            "elf_file_bytes": len(b),
            "entry": hex(h[4]),
            "load_page_union_bytes": mapped,
            "loads": [
                {
                    "flags": p[1],
                    "offset": p[2],
                    "address": p[3],
                    "filesz": p[5],
                    "memsz": p[6],
                    "align": p[7],
                }
                for p in loads
            ],
            "no_interp_dynamic_tls_relocation_undefined_ifunc": True,
            "objects": {
                s["name"]: {"bytes": s["size"], "address": hex(s["value"])}
                for s in symbols
                if s["type"] == 1 and s["size"]
            },
            "executable_byte_coverage": len(covered),
            "instruction_line_count": len(instructions),
            "indirect_branches": indirect,
            "syscall_sites": syscalls,
            "function_count": len(funcs),
            "direct_call_and_tail_graph": {k: sorted(v) for k, v in graph.items()},
            "interfunction_branches": branches,
            "recursive_components": recursive,
            "frames": frames,
            "stack_derivation": {
                "accepted_and_rejected_parser_max_instances": 18 if extra else 0,
                "counted_c_frame_instances": instances,
                "conservative_c_frames_sum_bytes": frame_sum,
                "abi_red_zone_plus_return_bytes_per_instance": 136,
                "entry_alignment_scratch_return_bytes": 39,
                "derived_descent_bytes": descent,
                "later_stack_page_growth_bytes": page_growth,
                "premises": (
                    "Executable bytes and direct graph checked; parser depth needs source review. "
                    "Frames include bounded adjustments; P/K/kernel startup remain unproved."
                ),
            },
            "object_source_trace": object_sources,
            "linked_objects": link_objects,
            "default_actual_flags": sorted(default_flags),
            "actual_plugin_arguments": plugins,
            "toolchain_origin_gap": "NONE_REPORTED_AVAILABILITY_NOT_INVOCATION"
            if all(
                n in build.get("compiler_components", {})
                for n in ("liblto_plugin.so", "lto-wrapper")
            )
            else "DEFAULT_PLUGIN_OR_AVAILABLE_WRAPPER_ORIGIN_NOT_BOUND",
        }
    for role in ("query", "audit"):
        text = files["hashes.h"].decode()
        match = re.search(role + "_hash\\[32\\]=\\{([^}]*)\\}", text)
        digest = bytes(int(x.strip(), 16) for x in match[1].split(",")).hex()
        require(digest == ident["binaries"][role], "independent structural condition line 197")
    result["generated_child_hashes_match_actual_binaries"] = True
    result["complete_resource_admission"] = "UNKNOWN_NOT_RESOURCE_ADMITTED"
    result["remaining_mandatory_terms"] = [
        "Merged all-CI-passed frozen identity",
        "Actual selected startup P/K/argv/env/cwd/selfhash/thread/core/exit",
        "Selected-host pre-entry kernel stack/mapping transient premises",
        "Complete simultaneous lifetime bound including carriers and fork/exec",
    ]
    if any(
        role["toolchain_origin_gap"] != "NONE_REPORTED_AVAILABILITY_NOT_INVOCATION"
        for role in result["roles"].values()
    ):
        result["remaining_mandatory_terms"].append("Default plugin/available wrapper origin gap")
    result["identity_manifest_sha256"] = options.identity_sha256
    return result


def main():
    parser, args = arguments(__doc__)
    try:
        result = review_evidence(args)
        write_review(args, "actual-elf-review.json", result)
    except (
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        OSError,
        StopIteration,
        struct.error,
        UnicodeError,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(2, "UNKNOWN_REVIEW_REJECTED: " + str(error)[:400] + "\n")


if __name__ == "__main__":
    main()
