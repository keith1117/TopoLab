"""Build and admit only the finite, synthetic R1 timing fixtures."""

import hashlib
import os
import sys
import time
from pathlib import Path

if __name__ == "__main__":
    # -I omits the script directory. Load frozen helpers directly from source.
    from types import ModuleType

    helper = Path(__file__).resolve().with_name("full60_input_loader.py")
    loader = ModuleType("full60_input_loader")
    loader.__file__ = str(helper)
    sys.modules[loader.__name__] = loader
    raw_loader = helper.read_bytes()
    exec(compile(raw_loader, str(helper), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(helper)] = hashlib.sha256(raw_loader).hexdigest()
    loader.install(require_locked_environment=True)
    sys.path.insert(0, str(helper.parent))

import r1_window_scope as scope
import staged_input_filer as custody


def paths(root):
    root = scope.public_root(root)
    return (
        Path(str(root) + "-source"),
        Path(str(root) + "-evidence") / "registration.json",
        Path(str(root) + "-evidence"),
    )


def build(root):
    import p17_m2_content_verified_public_fixture as fixture
    import p17_m2_input_export as producer
    import p17_m2_input_export_independent as checker
    import p17_m2_registered_input as registered
    import p17_m2_source_binding_independent as strict

    source, _, evidence = paths(root)
    os.umask(0o077)
    budget_raw = custody.read_private(scope.EVIDENCE / "owner-budget.json")
    custody.need(
        custody.sha(budget_raw) == scope.BUDGET
        and custody.read_private(Path(str(scope.EVIDENCE) + "-backup") / "owner-budget.json")
        == budget_raw
        and scope.START_MS <= time.time_ns() // 10**6 < scope.DIAGNOSTIC_END_MS,
        "diagnostic budget/clock differs",
    )
    for path in (evidence, Path(str(evidence) + "-backup")):
        path.mkdir(mode=0o700)
    contract, identity = fixture.create_sources(source, checker, window_scale=True)
    reader = producer.Reader(
        source, execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True
    )
    for row in strict.metadata_specs():
        reader.read(row["path"], row["max_bytes"])
    value = dict(
        schema="topolab.r1-window.public-registration.v1",
        source_root=str(source),
        source_observations=reader.source_observations,
        content_contract=contract,
        public_source_identity=identity,
    )
    registered.registration_bindings(value)
    raw = producer.canonical(value)
    for directory in (evidence, Path(str(evidence) + "-backup")):
        custody.write_private(directory / "registration.json", raw)
    return {
        "registration_sha256": custody.sha(raw),
        "source_root": str(source),
        "registered_metadata": len(reader.rows),
    }


def registration(root, expected):
    source, certificate, evidence = paths(root)
    raw = custody.read_private(certificate)
    custody.need(
        custody.sha(raw) == expected
        and all(
            custody.read_private(p / "registration.json") == raw
            for p in (evidence, Path(str(evidence) + "-backup"))
        ),
        "public registration pair",
    )
    value = custody.json.loads(raw)
    custody.need(
        custody.canonical(value) == raw
        and value["source_root"] == str(source)
        and value["schema"] == "topolab.r1-window.public-registration.v1",
        "public registration or source differs",
    )
    return value


def prepare(control, root, args):
    root = scope.public_root(root)
    digest = args.registration_certificate_sha
    custody.need(
        digest == args.registration_finalize_actual_sha
        and args.formal_registration_certificate_sha is None
        and args.formal_registration_finalize_actual_sha is None
        and args.public_source_plan is None
        and args.public_source_plan_sha is None
        and args.role is None
        and args.plan_sha is None,
        "public preparation pins",
    )
    value = registration(root, digest)
    source, certificate, _ = paths(root)
    plan = control.make_plan(root, value["content_contract"], value["public_source_identity"])
    plan.update(
        source_root=str(source), public_registration=dict(path=str(certificate), sha256=digest)
    )
    began = time.monotonic()
    root.mkdir(mode=0o700)
    control.base().put(root / "plan.json", plan)
    control.initial_lease(root, plan)
    control.finish_setup(root, plan, began=began)
    return dict(
        plan_sha256=custody.sha(custody.canonical(plan)),
        scope=control.REHEARSAL_SCOPE,
        formal_authority=False,
        source_stat_reads=0,
    )


def check(plan):
    root = scope.public_root(plan["root"])
    source, certificate, _ = paths(root)
    ref = plan["public_registration"]
    custody.need(
        plan["execution_identity"] == scope.PUBLIC_ID
        and plan["formal_authority"] is False
        and plan["scope"] == "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
        and plan["source_root"] == str(source)
        and plan["content_root"] == str(root / "content")
        and plan["backup_root"] == str(root / "backup-content")
        and ref["path"] == str(certificate),
        "public timing namespace differs",
    )
    value = registration(root, ref["sha256"])
    custody.need(
        plan["content_contract"] == value["content_contract"]
        and plan["public_source_identity"] == value["public_source_identity"]
        and plan["source_identity_policy"] == "topolab.source-identity.prebound-sha256.v1"
        and plan["role_order"] == list(custody.ROLES)
        and plan["contract_sha256"]
        == plan["source_tree"]["docs/planning/r1_window_public_contract.json"]
        and plan["contract_sha256"]
        == hashlib.sha256(
            (
                Path(__file__).resolve().parents[1] / "docs/planning/r1_window_public_contract.json"
            ).read_bytes()
        ).hexdigest(),
        "public timing source/plan binding",
    )
    return value


def programs(root):
    import build_staged_input_caller as builder
    import r1_window_public_route as route

    root = scope.public_root(root)
    wire = route.filer(root)
    _, certificate, evidence = paths(root)
    digest = custody.sha(custody.read_private(certificate))
    registration(root, digest)
    raw = (scope.CHECKOUT / "scripts/staged_input_actor.mjs").read_bytes()
    result = {}
    for actor in ("producer", "independent"):
        config = dict(
            repo=str(scope.CHECKOUT),
            evidence_root=str(evidence),
            execution_identity=scope.PUBLIC_ID,
            owner_budget_sha256=scope.BUDGET,
            author=actor,
            formal=False,
            root=str(root),
            event_prefix=wire.actor_prefix(actor),
            registration_certificate_sha=digest,
            registration_finalize_actual_sha=digest,
        )
        artifact = builder.build(config, raw, custody.sha(raw), wire=wire)
        wire.publish_pair(
            evidence / (wire.actor_prefix(actor) + "-program.json"), custody.canonical(artifact)
        )
        result[actor] = artifact["program_sha256"]
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("build", "programs"):
        raise SystemExit("usage: r1_window_public.py build|programs LITERAL_PUBLIC_ROOT")
    action = build if sys.argv[1] == "build" else programs
    print(custody.canonical(action(sys.argv[2])).decode(), end="")
