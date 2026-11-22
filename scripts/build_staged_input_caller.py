"""Freeze one staged actor program for actual functions.exec; no role is executed here."""

import argparse
import json
import re
import types
from pathlib import Path

SOURCE_CHECKOUT = Path(__file__).resolve().parents[1]
RUNTIME_REPO = Path("/private/tmp/topolab-staged-input-20261121")
path = SOURCE_CHECKOUT / "scripts/staged_input_filer.py"
wire = types.ModuleType("staged_input_wire_for_builder")
wire.__file__ = str(path)
exec(compile(path.read_bytes(), str(path), "exec"), wire.__dict__)


def build(config, source, expected_sha, *, wire=wire):
    wire.need(
        type(source) is bytes and len(source) <= 128 * 1024 and wire.sha(source) == expected_sha,
        "complete reviewed actor buffer SHA required",
    )
    wire.need(
        config.get("repo") == str(wire.RUNTIME_REPO)
        and config.get("evidence_root") == str(wire.EVIDENCE)
        and config.get("execution_identity") == wire.IDENTITY
        and config.get("owner_budget_sha256") == wire.BUDGET_SHA,
        "fixed staged runtime/identity/budget differs",
    )
    wire.need(
        config.get("author") in ("producer", "independent")
        and type(config.get("formal")) is bool
        and config.get("root") in wire.ROOTS
        and config.get("root") == (wire.FORMAL if config["formal"] else wire.PUBLIC)
        and re.fullmatch("[A-Za-z0-9_-]{1,80}", config.get("event_prefix", "")),
        "new actor/root qualification differs",
    )
    wire.need(
        all(
            isinstance(config.get(key), str) and re.fullmatch("[a-f0-9]{64}", config[key])
            for key in (
                "registration_certificate_sha",
                "registration_finalize_actual_sha",
                "formal_registration_certificate_sha",
                "formal_registration_finalize_actual_sha",
            )
        ),
        "four actual registration pins required",
    )
    if config["formal"]:
        wire.need(
            config["registration_certificate_sha"] == config["formal_registration_certificate_sha"]
            and config["registration_finalize_actual_sha"]
            == config["formal_registration_finalize_actual_sha"],
            "formal metadata pins differ",
        )
    text = source.decode("utf-8")
    wire.need(
        not re.search(r"^\s*import\s", text, re.MULTILINE), "standalone reviewed actor required"
    )
    factory = re.sub(r"^export (?=(?:async )?function|const)", "", text, flags=re.MULTILINE)
    factory += "\nreturn {executeActor,qualify};"
    key = "staged-input-" + config["event_prefix"] + "-" + config["author"]
    program = (
        "\n".join(
            [
                "const actor = new Function(" + json.dumps(factory) + ")();",
                "const config = actor.qualify(" + json.dumps(config) + ");",
                """const dispatch=async(tool,args)=>{
 if(!['exec_command','write_stdin'].includes(tool))throw Error('unregistered original tool');
 const requested_ms=Date.now();
 const result=await tools[tool](args);
 return {tool,arguments:args,requested_ms,returned_ms:Date.now(),result};
};""",
                "const result=await actor.executeActor(config,dispatch);",
                "store(" + json.dumps(key) + ",result);",
                """text({status:result.status,author:config.author,root:config.root,
 original_tool_rows:result.raw.length,own_future_return:'NOT_CLAIMED',
 final_acceptance:'REQUIRES_SEPARATE_ACTUAL_RETURN_AND_INPUT_AUDIT'});""",
            ]
        )
        + "\n"
    )
    return dict(
        schema="topolab.staged-input-actor-program.v1",
        execution_identity=wire.IDENTITY,
        owner_budget_sha256=wire.BUDGET_SHA,
        state="SOFTWARE_PROGRAM_NOT_EXECUTION_AUTHORITY",
        config=config,
        actor_sha256=expected_sha,
        program_sha256=wire.sha(program.encode()),
        result_store_key=key,
        program=program,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("config", "config-sha256", "actor-sha256", "output", "emit", "artifact-sha256"):
        parser.add_argument("--" + field)
    parser.add_argument("--formal-only", action="store_true")
    args = parser.parse_args()
    selected = wire
    if args.formal_only:
        import runpy

        route = runpy.run_path(str(SOURCE_CHECKOUT / "scripts/formal_input_route.py"))
        selected = route["filer"]()
    if args.emit:
        selected.need(
            isinstance(args.artifact_sha256, str)
            and re.fullmatch("[a-f0-9]{64}", args.artifact_sha256),
            "strict external artifact SHA256 required before emit",
        )
        value = selected.paired_actual(dict(path=args.emit, sha256=args.artifact_sha256))
        selected.need(
            value.get("schema") == "topolab.staged-input-actor-program.v1"
            and value.get("execution_identity") == selected.IDENTITY
            and selected.sha(value["program"].encode()) == value["program_sha256"],
            "frozen actor artifact differs",
        )
        print(json.dumps(value, separators=(",", ":")))
        return
    selected.need(
        all((args.config, args.config_sha256, args.actor_sha256, args.output)),
        "complete freeze arguments required",
    )
    config, _ = selected.read_json(selected.evidence_path(args.config), args.config_sha256)
    source = (SOURCE_CHECKOUT / "scripts/staged_input_actor.mjs").read_bytes()
    artifact = build(config, source, args.actor_sha256, wire=selected)
    result = selected.publish_pair(args.output, selected.canonical(artifact))
    selected.need(
        result["status"] == "PAIRED_PERSISTED",
        "frozen software artifact pair incomplete: " + str(result),
    )
    print(
        json.dumps(
            dict(result, program_sha256=artifact["program_sha256"], execution_authority=False),
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
