"""Single public registration of the fixed staged source. No source path CLI."""

import os
import sys
import time
from pathlib import Path

# A CLI starts with -I. Load published Python source ahead of any timestamp pyc.
if __name__ == "__main__":
    import types

    loader_path = Path(__file__).with_name("full60_input_loader.py")
    loader = types.ModuleType("staged_binding_loader")
    loader.__file__ = str(loader_path)
    exec(compile(loader_path.read_bytes(), str(loader_path), "exec"), loader.__dict__)
    loader.install()
    sys.path.insert(0, str(loader_path.parent))

import p17_m2_resource_control as resources
import p17_m2_source_binding_recovery as recovery
import staged_binding_source as producer
import staged_public_binding_independent as independent
from p17_m2_input_export import canonical, need, parse, sha
from p17_m2_input_export_independent import audit_native_record
from p17_m2_source_binding import literal_command
from staged_binding_evidence import (
    FIELDS,
    REPO,
    RUNTIME,
    B,
    E,
    bounded,
    pair,
    policy,
    receipt,
    replay_historical,
    verified_formal_registration,
    write_new,
    write_pair,
)

__all__ = ["verified_registration", "verified_formal_registration"]
ROOT = E / "binding"
ENTRY = RUNTIME / "scripts/staged_public_binding.py"
PYTHON = str(RUNTIME / ".venv/bin/python")
SCOPE = "STAGED_LOCAL_PUBLIC_STRICT23_ONLY"
ROLES = tuple(policy()["role_order"])
CORE = ROLES[:-1]
PREP_END = 1795326000000
GLOBAL_END = 1795351200000
CERT = "public-registration-a1.json"


def now():
    return time.time_ns() // 1000000


def sources():
    # Freeze the exact scripts and authorities used by these two linked graphs.
    paths = [p for p in (REPO / "scripts").iterdir() if p.suffix in (".py", ".mjs")]
    paths += sorted((REPO / "docs/planning").glob("*.json"))
    paths += list((REPO / "tests").glob("test_staged*"))
    paths += [
        REPO / "pyproject.toml",
        REPO / "uv.lock",
        REPO / "docs/planning/staged_source_input_acceptance.md",
    ]
    return {str(p.relative_to(REPO)): sha(p.read_bytes()) for p in sorted(paths)}


def software():
    value = parse(pair(E, "software-main-freeze.json"))
    need(
        value["budget_sha256"] == policy()["owner_budget_sha256"] and value["sources"] == sources(),
        "published staged source closure differs",
    )
    budget = parse(pair(E, "owner-budget-registration.json", value["budget_sha256"]))
    grant = policy()
    need(
        budget["source"] == grant["source"]
        and grant["source"]
        == (
            "/Users/keith1117/Library/Application Support/TopoLab-public-fixtures/"
            "exporter-r1-20261121-v1/source"
        )
        and grant["candidate_sha256"] == independent.CANDIDATE_SHA256
        and grant["index_sha256"] == independent.INDEX_SHA256
        and budget["new_named_FULL_cap"] == 9120
        and budget["registration"]["attempts"] == 1
        and budget["registration"]["full"] == dict(zip(ROLES, grant["FULL"], strict=True)),
        "public source or named reservation differs from owner grant",
    )
    recovery._publication_shape(value["publication"])
    need(set(value["reviews"]) == {"standards", "spec"}, "both component reviews required")
    reviewers = set()
    for kind, pin in value["reviews"].items():
        review = parse(pair(E, "review-" + kind + ".json", pin))
        need(
            review["verdict"] == "PASS"
            and review["sources_sha256"] == sha(canonical(value["sources"]))
            and review["review_axis"] == kind
            and review["reviewer"]
            in (
                "/root/containment_spec",
                "/root/containment_standards",
                "/root/full60_independent",
            ),
            "current independent review differs",
        )
        reviewers.add(review["reviewer"])
    need(len(reviewers) == 2, "separate review authors required")
    return value


def args(action, *more):
    return [PYTHON, "-I", str(ENTRY), action, *more]


def outer(role, start):
    return [
        "/usr/bin/time",
        "-l",
        "-o",
        str(ROOT / (role + ".outer.time")),
        *args("supervise", role, str(start)),
    ]


def actual(name, author, command):
    raw = pair(E, "binding/" + name + "-actual.json")
    packet = parse(raw)
    first, last = recovery._verify_terminal(packet)
    argv = command(first)
    need(
        packet["schema"] == "topolab.staged-binding.actual.v1"
        and packet["argv"] == argv
        and packet["author"] == author
        and packet["request"]["cmd"] == literal_command(argv)
        and packet["request"]["workdir"] == str(RUNTIME),
        "actual command/author differs",
    )
    output = "".join(row["result"]["output"] for row in packet["responses"]).encode("utf-8")
    return first, last, parse(output), sha(raw)


def preflight():
    snapshot = software()
    latest = recovery.publication_readiness()
    need(
        latest["main"] == snapshot["publication"]["main"]
        and latest["tree"] == snapshot["publication"]["tree"],
        "independent latest-main preflight differs",
    )
    need(now() <= PREP_END, "software preflight outside preparation window")
    return {
        "software": sha(canonical(snapshot)),
        "main": latest["main"],
        "main_CI_run": latest["main_CI_run"],
        "historical": replay_historical(),
        "original_reads": 0,
        "registration_reads": 0,
    }


def check_preflight():
    snap = software()
    t0, t1, value, pin = actual("preflight", policy()["actors"][1], lambda _: args("preflight"))
    need(
        1795293600000 <= t0 <= t1 <= PREP_END
        and t1 - t0 <= 300000
        and value["main"] == snap["publication"]["main"]
        and value["main_CI_run"] == snap["publication"]["main_CI_run"]
        and value["software"] == sha(canonical(snap))
        and value["historical"]["bindings"] == 23
        and value["historical"]["pins"] == policy()["old_formal_admission"],
        "preflight original return differs",
    )
    return t1, pin


def prepare(start):
    t1, pin = check_preflight()
    need(
        t1 <= start <= now() <= start + 120000
        and start <= PREP_END
        and start + (3600 + 9000 + 7200) * 1000 <= GLOBAL_END,
        "registration or successor time unavailable",
    )
    plan = {
        "id": policy()["schema"],
        "attempt": 1,
        "preflight": pin,
        "core_start_ms": start,
        "core_end_ms": start + 1800000,
        "source": policy()["source"],
        "budget": policy()["owner_budget_sha256"],
    }
    pin = write_pair("binding/plan.json", plan)
    write_pair("binding/source-lease-held.json", {"state": "HELD", "plan_sha256": pin})
    return {"sha256": pin}


def admitted_plan():
    p = parse(pair(E, "binding/plan.json"))
    first, pin = check_preflight()
    need(
        p["id"] == policy()["schema"]
        and p["preflight"] == pin
        and p["attempt"] == 1
        and p["budget"] == policy()["owner_budget_sha256"]
        and p["source"] == policy()["source"]
        and first <= p["core_start_ms"] <= PREP_END
        and p["core_end_ms"] == p["core_start_ms"] + 1800000
        and p["core_start_ms"] + 19800000 <= GLOBAL_END,
        "registration plan differs",
    )
    held = parse(pair(E, "binding/source-lease-held.json"))
    need(held == {"state": "HELD", "plan_sha256": sha(canonical(p))}, "new source lease differs")
    started, returned, result, _ = actual("prepare", "/root", lambda t: args("prepare", str(t)))
    need(
        started == p["core_start_ms"]
        and started <= returned <= started + 120000
        and result == {"sha256": sha(canonical(p))},
        "prepare original return differs",
    )
    return dict(p, prepared_ms=returned)


def plan_window(role, prior, p):
    start = prior[-1]["returned_ms"] if prior else p["prepared_ms"]
    end = p["core_end_ms"] if role in CORE else prior[4]["returned_ms"] + 1800000
    return start, end


def role_report(role):
    index = ROLES.index(role)
    first, last, out, actual_sha = actual(role, policy()["actors"][index], lambda t: outer(role, t))
    directory = ROOT / "native" / role
    command_raw = bounded(directory / "command.json")[0]
    native = parse(command_raw)
    wire = bounded(ROOT / (role + ".json"))[0]
    log = bounded(directory / "command.log")[0]
    profile = bounded(directory / "command.time")[0]
    outer_raw = bounded(ROOT / (role + ".outer.time"))[0]
    native_outer = resources.native(outer_raw.decode(), "darwin")
    expected = {"role": role, "record_sha256": sha(command_raw), "result_sha256": sha(wire)}
    # Replay each original wait4, timer profile, sample and group membership.
    # The immutable stdout binds the record bytes; its PASS field alone is insufficient.
    need(0 < len(native["helpers"]) <= 1300, "bounded sampler inventory required")
    helper_profiles = {}
    for i, helper in enumerate(native["helpers"]):
        name = f"sampler-{i}.time"
        helper_profiles[name] = bounded(directory / name)[0]
        need(receipt(directory / f"sampler-{i}.json") == helper, "sampler record differs")
    audited = audit_native_record(
        native,
        profile=profile,
        log=log,
        helper_profiles=helper_profiles,
        expected_role=role,
        expected_argv=args("payload", role),
        platform="darwin",
    )
    # Replace the in-command controller high-water with the larger observed
    # controller high-water through final exit when the outer profile observed one.
    peak = audited["inner_empirical_RSS_bytes"] + max(
        0, native_outer["rss_bytes"] - native["controller_rss_peak_bytes"]
    )
    need(
        out == expected
        and native["measurement_scope"] == SCOPE
        and native["measurement_execution_identity"] == policy()["schema"]
        and native["limit_bytes"] == resources.LIMIT
        and peak <= resources.LIMIT
        and parse(log) == {"role": role, "result_sha256": sha(wire)},
        "named native exit or output differs",
    )
    cap = policy()["outer_role_seconds"][index] * 1000
    need(
        max(
            (last - first) / 1000 + 10,
            native_outer["wall_seconds"] + 10,
            audited["inner_minimum_charge_seconds"],
        )
        <= cap / 1000,
        "named external return outside role budget",
    )
    return {
        "role": role,
        "requested_ms": first,
        "returned_ms": last,
        "actual_sha256": actual_sha,
        "wire_sha256": sha(wire),
        "record_sha256": sha(command_raw),
        "outer_sha256": sha(outer_raw),
        "rss_bytes": peak,
        "FULL": policy()["FULL"][index],
    }


def previous(until, plan=None):
    plan = admitted_plan() if plan is None else plan
    result = []
    for role in ROLES[:until]:
        report = role_report(role)
        start, end = plan_window(role, result, plan)
        need(
            start <= report["requested_ms"] <= report["returned_ms"] <= end,
            "registration role dependency or actual clock differs",
        )
        result.append(report)
    return result


def live_window(role, start):
    i = ROLES.index(role)
    plan = admitted_plan()
    prior = previous(i, plan)
    floor, end = plan_window(role, prior, plan)
    cap = policy()["outer_role_seconds"][i] * 1000
    need(
        floor <= start <= now() < start + cap <= end <= GLOBAL_END - 7200000,
        "role window or predecessor unavailable",
    )
    return start + cap, prior


def observations():
    expected = producer.expectations()
    rows = [receipt(ROOT / (r + ".json"))["rows"] for r in ROLES[:4]]
    independent.compare(expected, *rows)
    return [
        dict(
            path=r["path"],
            byte_size=r["physical"]["st_size"],
            sha256=r["sha256"],
            **{
                point: {k: r[point][k] for k in FIELDS}
                for point in ("declared", "before", "after", "closing")
            },
        )
        for r in rows[2]
    ]


def payload(role):
    claim = receipt(ROOT / (role + ".dispatch.json"))
    _, prior = live_window(role, claim["requested_ms"])
    marker = receipt(ROOT / "native" / role / "pending.json")
    need(
        marker["argv"] == args("payload", role)
        and marker["controller_pid"] == claim["pid"]
        and marker["measurement_scope"] == SCOPE,
        "payload requires its native controller",
    )
    write_new(ROOT / (role + ".started.json"), {"pid": os.getpid(), "started_ms": now()})
    if role in ROLES[:4]:
        reader = independent if role in (ROLES[1], ROLES[3]) else producer
        rows = reader.scan(
            producer.check_candidate(), producer.expectations(), availability=role in ROLES[:2]
        )
        result = {"role": role, "rows": rows}
    else:
        rows = observations()
        lease = lease_release(prior[:4])
        if role == ROLES[4]:
            write_pair("binding/source-lease-release.json", lease)
        need(parse(pair(E, "binding/source-lease-release.json")) == lease, "release differs")
        result = {
            "role": role,
            "observations_sha256": sha(canonical(rows)),
            "bindings": len(rows),
            "prior": prior,
            "release_sha256": sha(canonical(lease)),
        }
    return {"role": role, "result_sha256": write_new(ROOT / (role + ".json"), result)}


def lease_release(readers):
    need(len(readers) == 4, "missing original public readers")
    return {
        "state": "RELEASED",
        "held_sha256": sha(pair(E, "binding/source-lease-held.json")),
        "reader_actual_sha256": [r["actual_sha256"] for r in readers],
    }


def reserve_role(role):
    # Reserve before the external timer can open its output. Existing roles and
    # partial failures always keep their original profile and dispatch record.
    started = now()
    _, prior = live_window(role, started)
    need(not any(ROOT.glob("*-STOP.json")), "retained stop closes registration")
    need(not os.path.lexists(ROOT / (role + ".outer.time")), "existing outer profile")
    reservation = {
        "role": role,
        "reserved_ms": started,
        "predecessor": prior[-1]["actual_sha256"] if prior else None,
    }
    return {"reservation_sha256": write_new(ROOT / (role + ".reservation.json"), reservation)}


def supervise(role, start):
    held = receipt(ROOT / (role + ".reservation.json"))
    need(
        held["role"] == role and held["reserved_ms"] <= start <= held["reserved_ms"] + 30000,
        "fresh in-scope reservation required",
    )
    end, _ = live_window(role, start)
    write_new(ROOT / (role + ".dispatch.json"), {"pid": os.getpid(), "requested_ms": start})
    timeout = (end - now()) / 1000 - policy()["per_role_return_margin_seconds"]
    need(timeout > 0, "no native return reserve")
    record = resources.invoke(
        ROOT / "native",
        role,
        args("payload", role),
        timeout=timeout,
        measurement_scope=SCOPE,
        measurement_execution_identity=policy()["schema"],
    )
    need(
        record["exit_code"] == 0 and record["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED",
        "native registration stopped: " + str(record["software_result"]),
    )
    wire = bounded(ROOT / (role + ".json"))[0]
    return {
        "role": role,
        "record_sha256": sha(bounded(ROOT / "native" / role / "command.json")[0]),
        "result_sha256": sha(wire),
    }


def certificate():
    reports = previous(len(ROLES))
    rows = observations()
    lease = lease_release(reports[:4])
    need(parse(pair(E, "binding/source-lease-release.json")) == lease, "release evidence differs")
    for i in (4, 5):
        close = receipt(ROOT / (ROLES[i] + ".json"))
        need(
            close
            == {
                "role": ROLES[i],
                "observations_sha256": sha(canonical(rows)),
                "bindings": 23,
                "prior": reports[:i],
                "release_sha256": sha(canonical(lease)),
            },
            "registration closure differs",
        )
    ctx = {
        "source_root": policy()["source"],
        "execution_identity": policy()["schema"],
        "attempt": 1,
        "scope": SCOPE,
        "actors": {"producer": policy()["actors"][0], "independent": policy()["actors"][1]},
        "authority_sha256": sha(canonical(software())),
    }
    return {
        "core_bundle": {"certificate": {"registered_context": ctx, "source_observations": rows}},
        "actual_roles": reports,
        "public_reads_each": 23,
        "source_lease": "RELEASED",
        "named_FULL": sum(r["FULL"] for r in reports),
    }


def summary(cert):
    return {
        "status": "STAGED_PUBLIC_STRICT23_ACCEPTED",
        "bindings": 23,
        "certificate_sha256": sha(canonical(cert)),
        "paths": [str(E / CERT), str(B / CERT)],
    }


def finalize():
    cert = certificate()
    last = cert["actual_roles"][-1]["returned_ms"]
    need(
        last <= now() <= cert["actual_roles"][4]["returned_ms"] + 1800000,
        "registration finalization outside result window",
    )
    write_pair(CERT, cert)
    return summary(cert)


def verified_registration(*, certificate_raw=None, finalize_actual_raw=None):
    """Replay complete actual execution without reopening the registered source."""
    cert = certificate()
    stored = pair(E, CERT)
    final = pair(E, "binding/finalize-actual.json")
    need(
        stored == canonical(cert)
        and (certificate_raw is None or stored == certificate_raw)
        and (finalize_actual_raw is None or final == finalize_actual_raw),
        "public certificate differs",
    )
    first, last, result, pin = actual("finalize", "/root", lambda _: args("finalize"))
    need(
        pin == sha(final)
        and result == summary(cert)
        and cert["actual_roles"][-1]["returned_ms"]
        <= first
        <= last
        <= cert["actual_roles"][4]["returned_ms"] + 1800000,
        "public finalizer return differs",
    )
    record = cert["core_bundle"]["certificate"]
    return record["registered_context"], record["source_observations"]


def main(argv):
    os.umask(0o077)
    need(
        REPO == RUNTIME
        and Path.cwd() == RUNTIME
        and sys.platform == "darwin"
        and sys.flags.isolated
        and all(os.environ.get(k) == v for k, v in resources.ENVIRONMENT.items()),
        "literal registered host, isolated runtime and thread environment required",
    )
    match argv:
        case ["preflight"]:
            return preflight()
        case ["prepare", start]:
            return prepare(int(start))
        case ["reserve", role] if role in ROLES:
            return reserve_role(role)
        case ["supervise", role, start] if role in ROLES:
            return supervise(role, int(start))
        case ["payload", role] if role in ROLES:
            return payload(role)
        case ["finalize"]:
            return finalize()
        case _:
            raise ValueError("unregistered staged command")


if __name__ == "__main__":
    try:
        print(canonical(main(sys.argv[1:])).decode(), end="", flush=True)
    except Exception as error:
        failure = {
            "type": type(error).__name__,
            "reason": str(error),
            "prefix": getattr(error, "binding_prefix", []),
        }
        print(canonical(failure).decode(), end="", flush=True)
        raise SystemExit(1) from error
