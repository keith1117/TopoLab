"""Run one public first role with the released transport, sampler and receipt binder."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

ENTRY = Path(__file__).resolve()
ENTRY_DIGEST = globals().get("ENTRY_DIGEST")
W = ENTRY.parents[1]
HISTORY = Path("/private/tmp/topolab-certificate-20261124")
E = Path("/Users/keith1117/Documents/TopoLab-data/child-20261125")
OLD = E.parent / "certificate-20261124"
ROLE = "independent-public-check"
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
BUDGET = "8693ffd9e9555a5247c2569c0d4f97331fbc7f6237dce25e2a80012c7f1c26dd"
SCRIPTS = ("child_public_control.py", "child_public_schedule.mjs", "certificate_replay_proof.py")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def source_loader(path):
    raw = path.read_bytes()
    loader = ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path.resolve())] = digest(raw)
    return loader


def entry(root):
    match = re.fullmatch(r"/private/tmp/topolab-public-child-20261125-a([1-9]|1[0-8])", str(root))
    need(match and root.resolve() == root, "literal diagnostic root required")
    name = f"public-{match[1]}-entry.json"
    claim = paired(E, name)
    budget = paired(E, "owner-budget.json")
    value = json.loads(claim)
    need(
        digest(budget) == BUDGET
        and value["budget_sha256"] == BUDGET
        and value["root"] == str(root)
        and value["slot"] == int(match[1])
        and value["mode"] in ("baseline", "candidate", "negative", "released")
        and value["start_ms"]
        <= time.time_ns() // 10**6
        <= value["end_ms"]
        <= json.loads(budget)["diagnostic_end_ms"],
        "public claim or deadline differs",
    )
    return value


def paired(directory, name):
    p = directory / name
    q = directory.with_name(directory.name + "-backup") / name
    raw = p.read_bytes()
    need(
        p.is_file()
        and q.is_file()
        and not p.is_symlink()
        and not q.is_symlink()
        and not p.samefile(q)
        and raw == q.read_bytes(),
        "paired control differs: " + name,
    )
    return raw


def install_trace(root):
    """Observe creation inside this payload only. The observer creates no processes."""
    stream = (root / "process-trace.jsonl").open("x", buffering=1)
    seq = 0

    def write(kind, **fields):
        nonlocal seq
        seq += 1
        stream.write(
            json.dumps(
                dict(
                    kind=kind,
                    seq=seq,
                    time_ns=time.time_ns(),
                    pid=os.getpid(),
                    ppid=os.getppid(),
                    pgid=os.getpgrp(),
                    **fields,
                ),
                sort_keys=True,
            )
            + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())

    def audit(event, args):
        if event not in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.system", "os.fork"):
            return
        frame = sys._getframe(1)
        stack = []
        while frame is not None and len(stack) < 40:
            stack.append([frame.f_code.co_filename, frame.f_code.co_name, frame.f_lineno])
            frame = frame.f_back
        if event in ("subprocess.Popen", "os.posix_spawn", "os.exec"):
            exe, argv = os.fsdecode(args[0]), args[1]
            cwd = os.fsdecode(args[2]) if event == "subprocess.Popen" and args[2] else os.getcwd()
            resolved = shutil.which(exe) if "/" not in exe else os.path.abspath(exe)
            write(
                "spawn",
                api=event,
                executable=resolved or exe,
                argv=[os.fsdecode(x) for x in argv],
                cwd=cwd,
                stack=stack,
            )
        else:
            write("spawn", api=event, executable=None, argv=[], cwd=os.getcwd(), stack=stack)

    original = subprocess.Popen.__init__

    def observed(self, *args, **kwargs):
        original(self, *args, **kwargs)
        write("spawn-return", child_pid=self.pid)

    sys.addaudithook(audit)
    subprocess.Popen.__init__ = observed
    write("trace-start", observer_processes=0)
    return write


def role_freeze():
    import p17_m2_input_continuation as profiles

    profile = profiles.profile("control", profiles.CHILD_FORMAL)
    return profile.source_freeze(profiles.CHILD_FORMAL)


def software(base, claim):
    names = dict(base())
    if claim["mode"] != "baseline":
        names.update({"freeze/" + path: expected for path, expected in role_freeze().items()})
        need(
            names["freeze/scripts/child_public_schedule.mjs"] == claim["driver_sha256"]
            and names["freeze/scripts/staged_input_actor.mjs"] == claim["scheduler_sha256"],
            "scheduled driver bytes differ from frozen software",
        )
    for name in SCRIPTS:
        names["candidate/" + name] = digest((W / "scripts" / name).read_bytes())
    names["public-entry"] = digest(json.dumps(claim, sort_keys=True).encode())
    return names


def historical_inputs():
    policy = json.loads((HISTORY / "docs/planning/certificate_formal_contract.json").read_bytes())
    data = json.loads(
        paired(OLD.with_name(OLD.name + "-formal"), "input-preparation-closure-a1.json")
    )
    return policy, data["source_tree"]


def check_readiness(claim, observe, plan, loader):
    """Use only closed controls. The historical result grants no reader or activation."""
    policy, tree = historical_inputs()
    if claim["mode"] == "baseline":
        # The historical graph is closed. Exercise its actual stateless proof
        # checker on the sealed inputs, inside this fresh public role.
        import certificate_replay_proof as proof

        result = proof.verified_readiness(policy, tree)
        observe(
            "readiness",
            scope="RELEASED_HISTORICAL_PROOF",
            sha256=result["package"]["sha256"],
            proof_sha256=digest(Path(proof.__file__).read_bytes()),
        )
    else:
        import certificate_replay_proof as proof

        result = proof.verified_readiness(policy, tree)
        need(
            result["source_main"] == "671a21b3d47fae16610e13884993abee5bee8e12"
            and result["package"]["sha256"]
            == "133553193c411d565860c0a04ac81b65f8bad47152d1b89caa88e28ee3b75c81"
            and proof.checkout_commit(W) == claim["checkout_head"],
            "release proof differs",
        )
        path = Path(proof.__file__).resolve()
        compiled = loader.loaded_source_sha256[str(path)]
        tree = plan["source_tree"]
        need(
            path == W / "scripts/certificate_replay_proof.py"
            and compiled
            == tree["candidate/certificate_replay_proof.py"]
            == tree["freeze/scripts/certificate_replay_proof.py"]
            == digest(path.read_bytes())
            and ENTRY_DIGEST
            == tree["candidate/child_public_control.py"]
            == tree["freeze/scripts/child_public_control.py"]
            and loader.loaded_source_sha256[str(W / "scripts/full60_input_loader.py")]
            == tree["freeze/scripts/full60_input_loader.py"]
            and proof.checkout_commit(W) == claim["checkout_head"],
            "public checkout or executed proof differs",
        )
        observe(
            "readiness",
            scope="VERIFIED_PRIOR_RELEASE_AND_CANDIDATE_BYTES",
            sha256=result["package"]["sha256"],
            proof_sha256=compiled,
            actual_sha256=result["actual"]["sha256"],
            checkout_head=claim["checkout_head"],
        )
        if claim["mode"] == "released":
            import p17_m2_input_continuation as profiles

            registered = profiles.profile("registered", profiles.CHILD_FORMAL)
            policy = registered.authority()
            ready, raw_sha = registered.readiness_inputs(policy)
            need(
                ready["child_verification"]["source_main"] == claim["checkout_head"]
                and ready["execution_identity"] == profiles.CHILD_FORMAL,
                "released first-role readiness differs",
            )
            preflight = Path(policy["independent_preflight_actual_path"])
            proof_ref = ready["child_verification"]
            frozen = {
                key.removeprefix("freeze/"): value
                for key, value in tree.items()
                if key.startswith("freeze/")
            }
            observe(
                "released-readiness",
                readiness_sha256=raw_sha,
                new_proof_package_sha256=proof_ref["package"]["sha256"],
                new_proof_actual_sha256=proof_ref["actual"]["sha256"],
                source_main=proof_ref["source_main"],
                software_tree_sha256=digest(registered.producer.canonical(frozen)),
                preflight_actual_sha256=digest(paired(preflight.parent, preflight.name)),
            )
        if claim["mode"] == "negative":
            subprocess.run(["/bin/sleep", "3"], check=True)


def file_original(base, root, mode, plan_sha, argv):
    import staged_input_filer as wire

    folder = root.with_name(root.name + "-evidence") / "caller"
    raw = (folder / (mode + "-actual.json")).read_bytes()
    packet = json.loads(raw)
    expected = argv(root, mode, plan_sha, ROLE)
    first, last, code = wire.validate_terminal(packet, expected, "/root", str(Path.cwd()))
    stdout = "".join(row["result"]["output"] for row in packet["responses"]).encode()
    need(code == 0, "failed original role command")
    pending = base.read_json(root / "receipts" / (ROLE + "-pending.json"))
    need(
        pending["plan_sha256"] == plan_sha
        and pending["external_argv"][0 if mode == "supervise" else 1] == expected,
        "pending command differs",
    )
    event = dict(
        event_id=packet["event_id"],
        author="/root",
        argv=expected,
        raw_packet_sha256=digest(raw),
        exit_code=code,
        complete=True,
        start_seconds=first / 1000,
        end_seconds=last / 1000,
        wall_seconds=(last - first) / 1000,
        clock_domain="functions.exec.Date.now.UTC-seconds",
        observed_pending_sha256=digest(base.canonical(pending)),
    )
    if mode == "record":
        record = base.read_json(root / "receipts" / (ROLE + "-wire.json"))
        need(stdout == base.canonical(record), "original REC bytes differ")
        event["observed_completion_sha256"] = digest(base.canonical(record["completion"]))
        prior = base.read_json(root / (ROLE + "-supervise-actual-event.json"))
        need(prior["end_seconds"] <= event["start_seconds"], "overlapping events")
        base.put(root / (ROLE + "-events.json"), [prior, event])
    else:
        need(
            json.loads(stdout) == {"status": "PENDING_EXTERNAL_EXIT", "controller_exit": 0},
            "original SUP bytes differ",
        )
    base.put(root / (ROLE + "-" + mode + "-actual-event.json"), event)
    print(base.canonical(dict(status="ACTUAL_EVENT_FILED", mode=mode)).decode(), end="")


def main():
    args = argparse.ArgumentParser()
    args.add_argument(
        "mode",
        choices=(
            "prepare-public",
            "supervise",
            "run",
            "payload",
            "record",
            "bind",
            "file-supervise",
            "file-record",
        ),
    )
    args.add_argument("--root", required=True, type=Path)
    args.add_argument("--plan-sha")
    args.add_argument("--role", choices=(ROLE,))
    a = args.parse_args()
    os.umask(0o077)
    claim = entry(a.root)
    checkout = HISTORY if claim["mode"] == "baseline" else W
    need(
        sys.flags.isolated and sys.executable == PYTHON and Path.cwd() == checkout,
        "fixture runtime",
    )
    observe = install_trace(a.root) if a.mode == "payload" else None
    loader = source_loader(checkout / "scripts/full60_input_loader.py")
    loader.install(require_locked_environment=True)
    sys.path.insert(0, str(checkout / "scripts"))
    base = loader.load(
        "child_public_native_control", checkout / "scripts/p17_m2_content_verified_control.py"
    )
    # This isolated public module uses its normal plan, dispatch and independent
    # binder. Bind only its entry and public role body to the new fixture.
    old_freeze, old_payload = base.source_freeze, base.payload_body
    base.source_freeze = lambda: software(old_freeze, claim)

    def argv(root, mode, plan_sha, role):
        return [
            PYTHON,
            "-I",
            str(ENTRY),
            mode,
            "--root",
            str(root),
            "--plan-sha",
            plan_sha,
            "--role",
            role,
        ]

    def body(root, plan, role):
        need(role == ROLE and observe is not None, "first public role required")
        result = old_payload(root, plan, role)
        check_readiness(claim, observe, plan, loader)
        observe(
            "trace-complete", plan_sha256=digest(base.canonical(plan)), entry_sha256=ENTRY_DIGEST
        )
        return result

    base.argv_for = argv
    base.payload_body = body
    if a.mode.startswith("file-"):
        base.checked(a.root, a.plan_sha)
        file_original(base, a.root, a.mode.removeprefix("file-"), a.plan_sha, argv)
        return 0
    return base.main()


if __name__ == "__main__":
    source = ENTRY.read_bytes()
    scope = {
        "__name__": "child_public_entry",
        "__file__": str(ENTRY),
        "ENTRY_DIGEST": digest(source),
    }
    exec(compile(source, str(ENTRY), "exec"), scope)
    raise SystemExit(scope["main"]())
