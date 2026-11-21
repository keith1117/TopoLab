"""Freeze an actual tools dispatcher from reviewed code; never execute an input role.

The program belongs in functions.exec. Each author runs their own frozen program;
all exec/poll calls retain their original request, response and UTC endpoints.
Generating this software artifact is not metadata/input execution authority.
"""

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path

# CI may read reviewed source from a different checkout. Generated commands still
# target only the contract's exact production runtime; a checkout grants no target access.
SOURCE_CHECKOUT = Path(__file__).resolve().parents[1]
RUNTIME_REPO = Path("/private/tmp/topolab-meta-input-20261121")
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data/metadata-input-acceptance-20261121")
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.20261121.v1"
BUDGET_SHA = "9200b495ea726459094868265e6cf61b3364e10515a91e815db2baa95dbc0d47"
SOURCE_FILES = ("full60_input_actual_boundary.mjs", "full60_input_cohort.mjs")


def need(condition, reason):
    if not condition:
        raise ValueError("NOV21_CALLER_FREEZE: " + reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def admitted(path):
    value = Path(path)
    need(
        value.is_absolute()
        and ".." not in value.parts
        and value.is_relative_to(EVIDENCE)
        and value != EVIDENCE,
        "NEW artifact namespace",
    )
    return value


def read_once(path, expected, maximum=1024**2):
    path = admitted(path)
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            need(
                stat.S_ISREG(before.st_mode)
                and before.st_nlink == 1
                and stat.S_IMODE(before.st_mode) == 0o600
                and before.st_size <= maximum,
                "private bounded caller artifact required",
            )
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        closing = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_mode", "st_nlink")
        need(
            all(
                getattr(before, key) == getattr(after, key) == getattr(closing, key)
                for key in fields
            )
            and len(raw) == before.st_size
            and sha(raw) == expected,
            "caller artifact raw/closing/SHA differs",
        )
        return raw
    finally:
        os.close(directory)


def publish(path, raw):
    output = admitted(path)
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in output.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(
            output.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        with os.fdopen(fd, "wb") as stream:
            need(stream.write(raw) == len(raw), "complete frozen program write required")
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory)
    finally:
        os.close(directory)
    return output


def build(config, sources, source_pins):
    need(
        set(sources) == set(source_pins) == set(SOURCE_FILES)
        and all(
            type(raw) is bytes and len(raw) <= 128 * 1024 and sha(raw) == source_pins[name]
            for name, raw in sources.items()
        ),
        "complete exact source buffers required",
    )
    need(
        config.get("execution_identity") == IDENTITY
        and config.get("repo") == str(RUNTIME_REPO)
        and config.get("evidence_root") == str(EVIDENCE)
        and config.get("owner_budget_sha256") == BUDGET_SHA,
        "NEW exact identity/runtime/budget configuration required",
    )
    need(
        config.get("author") in ("producer", "independent")
        and type(config.get("formal")) is bool
        and re.fullmatch("[A-Za-z0-9_-]{1,100}", config.get("event_prefix", "")),
        "fixed separate author and unique event prefix required",
    )
    gate = config.get("metadata_gate", {})
    pins = [
        gate.get(kind, {}).get(key)
        for kind in ("public", "formal")
        for key in ("certificate_sha256", "finalize_actual_sha256")
    ]
    need(
        all(isinstance(value, str) and re.fullmatch("[a-f0-9]{64}", value) for value in pins),
        "BOTH metadata certificate/finalizer pins required",
    )
    # Only the public ESM export keyword is removed; module bodies and decisions
    # stay byte-bound to the reviewed input. The factories have no module imports.
    factories = {}
    for name, raw in sources.items():
        text = raw.decode("utf-8")
        need(not re.search(r"^\s*import\s", text, re.MULTILINE), "standalone module required")
        factories[name] = re.sub(
            r"^export (?=(?:async )?function|const)", "", text, flags=re.MULTILINE
        )
    boundary = factories[SOURCE_FILES[0]] + "\nreturn {createActualBoundary,qualification20261121};"
    cohort = factories[SOURCE_FILES[1]] + "\nreturn {executeOwned};"
    key = "input-20261121-" + config["event_prefix"] + "-" + config["author"]
    lines = [
        "const boundaryModule = new Function(" + json.dumps(boundary) + ")();",
        "const cohortModule = new Function(" + json.dumps(cohort) + ")();",
        "const config = boundaryModule.qualification20261121(" + json.dumps(config) + ");",
        """const dispatch=async(tool,args)=>{
 if(!['exec_command','write_stdin'].includes(tool))throw Error('unregistered actual tool');
 const requested_ms=Date.now();
 const result=await tools[tool](args);
 return {tool,arguments:args,requested_ms,returned_ms:Date.now(),result};
};""",
        "const boundary=boundaryModule.createActualBoundary(dispatch,config);",
        "const result=await cohortModule.executeOwned(config,boundary);",
        "store(" + json.dumps(key) + ",{result,raw:boundary.raw,packets:boundary.packets});",
        """text({status:result.status,author:config.author,root:config.root,
 original_tool_rows:boundary.raw.length,own_future_return:'NOT_CLAIMED',
 final_acceptance:'REQUIRES_SEPARATE_ACTUAL_RETURN_AND_INPUT_AUDIT'});""",
    ]
    program = "\n".join(lines) + "\n"
    return dict(
        schema="topolab.actual-input-caller-program.20261121.v1",
        execution_identity=IDENTITY,
        owner_budget_sha256=BUDGET_SHA,
        state="FROZEN_SOFTWARE_PROGRAM_NOT_EXECUTION_AUTHORITY",
        config=config,
        source_sha256=source_pins,
        program_sha256=sha(program.encode()),
        result_store_key=key,
        program=program,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config")
    parser.add_argument("--config-sha256")
    parser.add_argument("--output")
    parser.add_argument("--boundary-sha256")
    parser.add_argument("--cohort-sha256")
    parser.add_argument("--emit")
    parser.add_argument("--artifact-sha256")
    args = parser.parse_args()
    os.umask(0o077)
    if args.emit:
        value = json.loads(read_once(args.emit, args.artifact_sha256))
        need(
            value.get("schema") == "topolab.actual-input-caller-program.20261121.v1"
            and sha(value["program"].encode()) == value["program_sha256"],
            "program SHA differs",
        )
        print(json.dumps(value, separators=(",", ":")))
        return
    need(
        all(
            (args.config, args.config_sha256, args.output, args.boundary_sha256, args.cohort_sha256)
        ),
        "complete freeze arguments required",
    )
    config = json.loads(read_once(args.config, args.config_sha256, 262144))
    sources = {name: (SOURCE_CHECKOUT / "scripts" / name).read_bytes() for name in SOURCE_FILES}
    value = build(
        config,
        sources,
        dict(zip(SOURCE_FILES, (args.boundary_sha256, args.cohort_sha256), strict=True)),
    )
    raw = canonical(value)
    output = publish(args.output, raw)
    print(
        json.dumps(
            dict(
                path=str(output),
                sha256=sha(raw),
                bytes=len(raw),
                program_sha256=value["program_sha256"],
                execution_authority=False,
            )
        )
    )


if __name__ == "__main__":
    main()
