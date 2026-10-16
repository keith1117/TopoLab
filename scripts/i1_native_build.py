"""Build the opt-in, freestanding I1 public software programs on Linux x86-64."""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native" / "i1"
FLAGS = (
    "-std=c11",
    "-O2",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-ffreestanding",
    "-fno-builtin",
    "-fno-tree-loop-distribute-patterns",
    "-fno-jump-tables",
    "-fno-tree-switch-conversion",
    "-fno-math-errno",
    "-ffp-contract=off",
    "-fno-stack-protector",
    "-fno-pie",
    "-fno-omit-frame-pointer",
    "-fstack-usage",
    "-fno-asynchronous-unwind-tables",
    "-static",
    "-nostdlib",
    "-no-pie",
    "-Wl,-z,noexecstack,--build-id=sha1",
)
ROLES = {
    "query": ("query.c", "vectors.c", "readers.c", "query_main.c", "sha256.c"),
    "audit": ("audit.c", "audit_main.c", "sha256.c"),
    "controller": ("controller.c", "sealed_child.c", "sha256.c"),
}


def build(destination: Path) -> dict[str, object]:
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("freestanding admission programs require Linux x86-64")
    compiler = "/usr/bin/gcc"
    if not Path(compiler).is_file():
        raise RuntimeError("the selected Ubuntu environment must provide GCC")
    build_env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "SOURCE_DATE_EPOCH": "0"}
    destination.mkdir(parents=True, exist_ok=False)
    components = {}
    for name in ("cc1", "as", "collect2", "ld"):
        reported = subprocess.check_output(
            [compiler, f"-print-prog-name={name}"], env=build_env, text=True
        ).strip()
        resolved = Path(shutil.which(reported, path=build_env["PATH"]) or reported).resolve()
        if not resolved.is_file() or not str(resolved).startswith(("/usr/", "/bin/", "/lib/")):
            raise RuntimeError(f"unregistered compiler component: {name}")
        components[name] = {
            "path": str(resolved),
            "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        }
    specs = subprocess.check_output([compiler, "-dumpspecs"], env=build_env)
    (destination / "gcc-specs.txt").write_bytes(specs)
    records = {}
    for role, files in ROLES.items():
        if role == "controller":
            lines = ["/* Generated from the two actual preceding binaries. */"]
            for name in ("query", "audit"):
                digest = records[name]["sha256"]
                values = ",".join(f"0x{digest[i : i + 2]}" for i in range(0, 64, 2))
                lines.append(f"static const unsigned char {name}_hash[32]={{{values}}};")
            (destination / "hashes.h").write_text("\n".join(lines) + "\n")
        binary = destination / f"i1-{role}"
        sources = [SOURCE / s for s in (*files, "runtime.c", "start.S")]
        headers = [SOURCE / s for s in ("query.h", "audit.h", "runtime.h")]
        command = [
            compiler,
            *FLAGS,
            "-v",
            f"-Wl,-Map={destination / (role + '.map')}",
            "-I",
            str(destination),
            *(str(s) for s in sources),
            "-o",
            str(binary),
        ]
        build_log = destination / f"{role}-compiler.txt"
        with build_log.open("xb") as log:
            subprocess.run(command, cwd=ROOT, env=build_env, stdout=log, stderr=log, check=True)
        records[role] = {
            "binary": binary.name,
            "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "argv": command,
            "compiler_trace_sha256": hashlib.sha256(build_log.read_bytes()).hexdigest(),
            "link_map_sha256": hashlib.sha256(
                (destination / f"{role}.map").read_bytes()
            ).hexdigest(),
            "stack_files": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(destination.glob(f"i1-{role}-*.su"))
            },
            "sources": {
                str(s.relative_to(ROOT)): hashlib.sha256(s.read_bytes()).hexdigest()
                for s in (*sources, *headers)
            },
        }
    record = {
        "schema": "topolab.i1.public-build.v1",
        "roles": records,
        "compiler_version": subprocess.check_output(
            [compiler, "--version"], env=build_env, text=True
        ),
        "build_environment": build_env,
        "compiler_components": components,
        "gcc_builtin_specs_sha256": hashlib.sha256(specs).hexdigest(),
        "compiler_trace_scope": (
            "actual -v commands, link map and frame hashes; "
            "no LTO/plugin requested; no third-party runtime linked"
        ),
        "compiler_binary": str(Path(compiler).resolve()),
        "compiler_sha256": hashlib.sha256(Path(compiler).resolve().read_bytes()).hexdigest(),
        "generated_hash_header_sha256": hashlib.sha256(
            (destination / "hashes.h").read_bytes()
        ).hexdigest(),
        "admission": "UNKNOWN_NOT_GRANTED",
        "scientific_access": False,
    }
    (destination / "build.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    build(parser.parse_args().destination.resolve())
