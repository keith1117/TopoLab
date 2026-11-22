"""Replay the closed B3 failure against the frozen catalog, using no original source paths."""

import argparse
import base64
import hashlib
import io
import json
import resource
import subprocess
import sys
import tarfile
import tempfile
import time
from contextlib import contextmanager
from copy import deepcopy
from functools import cache
from pathlib import Path
from types import ModuleType

REPO = Path("/private/tmp/topolab-catalog-r0-20261122")
E = Path("/Users/keith1117/Documents/TopoLab-data/catalog-r0-acceptance-20261122")
PREVIOUS = E.parent / "r0-read-acceptance-20261122"
PROTOCOL = "docs/planning/catalog_input_contract.json"
WORKER = "scripts/catalog_input_offline.py"
CHECKER = "scripts/p17_m2_input_export_independent.py"
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.catalog-20261122.v1"
BUDGET = "985ad9aa67a4cbdc8a5c36cadbf4c7920f39559c57e2115a98e902d17d31c11f"
ARCHIVE = "648e114821ca2dc1ca77dd1f37a57967216d68de40af14137141ee9e58e32d51"
INDEX = "d8df27c26a83e409fcd19c619a0e1e3b8410dd44d2050cd4fc0f7702a59e0549"
AUDIT = "39384e3191be43ee6020cf56bf02bee7223df06fb711317cc29ba89a38c928e6"
CATALOG = "441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c"
UNIT_PACKAGE = "664edec58a06b5517d487f3b87b5f9b24063d6c20ab82f44b7ae8b95a2a3b1b2"
UNIT_ACTUAL = "3193a2d4936e3b9385bf021d5dfd85b6836491b30ea10c6bfc0007578557b335"
FULL_CATALOG = "99632dfb017714503ebe24bcb0eac6751f0246a178dfdb9f06f9e97005dcc0d6"
FIXTURE_FIT = "76fb2a4b2b96d62ef336e96736f3da3d1fdb24ed6e211cf97385de644be6dcb6"
FIT = "b3-v1-fits/b3_training.json"
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
MODULE_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def need(ok, reason):
    if not ok:
        raise ValueError("CATALOG_OFFLINE_STOP: " + reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def module(path, expected=None):
    raw = path.read_bytes()
    digest = sha(raw)
    need(expected is None or digest == expected, "compiled source SHA differs: " + path.name)
    result = ModuleType(path.stem)
    result.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), result.__dict__)
    result.compiled_sha256 = digest
    return result


def pair(root, name, expected=None):
    wire = independent_wire()
    raw = wire.read_pair(root / name, root.with_name(root.name + "-backup") / name)
    need(expected is None or sha(raw) == expected, "retained SHA differs: " + name)
    return raw


def archived_controls():
    index = json.loads(pair(PREVIOUS, "formal-generated-controls-index-a1.json", INDEX))
    raw = pair(PREVIOUS, "formal-generated-controls-a1.tar.gz", ARCHIVE)
    controls = {}
    selected = {"registry.json", "plan.json", "independent-r0-failure.json", "r0-source-rows.json"}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for entry in archive:
            if entry.name in selected:
                length, digest = index["members"][entry.name]
                need(
                    entry.isfile() and 0 < length == entry.size <= 16 * 1024**2,
                    "bounded generated control required",
                )
                data = archive.extractfile(entry).read(length + 1)
                need(
                    entry.name not in controls and len(data) == length and sha(data) == digest,
                    "archived generated control differs",
                )
                controls[entry.name] = json.loads(data)
    need(set(controls) == selected, "missing sealed controls")
    return controls


def original_rows(controls, checker):
    failure = controls["independent-r0-failure.json"]
    registry = controls["registry.json"]
    rows = controls["r0-source-rows.json"]
    reader = failure["independent_context"]["readers"]["source"]
    need(
        failure["reason"] == "embedded manifest/catalog differs"
        and len(rows) == len(registry["metadata"]) == 40
        and reader["attempts"] == len(reader["source_identities"]) == len(reader["rows"]) == 7,
        "prior formal stop/progress differs",
    )
    registered = {row["path"]: row for row in registry["metadata"]}
    need(len(registered) == len({r["path"] for r in rows}) == 40, "distinct metadata paths")
    for i, row in enumerate(rows):
        ref = {key: row[key] for key in ("path", "byte_size", "sha256")}
        need(ref == registered.get(row["path"]), "exporter file reference differs")
        if i < 7:
            other = reader["source_identities"][i]
            need(
                reader["rows"][i] == ref and all(other[k] == v for k, v in ref.items()),
                "independent path, length or SHA differs",
            )
            for point in ("declared", "before", "after", "closing"):
                need(
                    all(row[point][k] == other[point][k] for k in ("st_dev", "st_ino", "st_size")),
                    "independent physical observations differ",
                )
    # The previous unit package has original bytes for item 34 only.
    package = json.loads(pair(PREVIOUS, "r0-read-verification-a1.json", UNIT_PACKAGE))
    actual = json.loads(pair(PREVIOUS, "r0-read-verification-actual-a1.json", UNIT_ACTUAL))
    out = json.loads("".join(r["result"]["output"] for r in actual["responses"]))
    need(
        out["status"] == "PASS_R0_REPEAT_CANDIDATE_VERIFICATION"
        and out["package_sha256"] == UNIT_PACKAGE
        and out["accepted_slots"] == [3, 4]
        and actual["responses"][-1]["result"]["exit_code"] == 0,
        "prior unit actual differs",
    )
    for entry in package["observations"]:
        obs = json.loads(base64.b64decode(entry["receipt_raw_b64"], validate=True))
        unit = base64.b64decode(obs["raw_b64"], validate=True)
        need(
            obs["relative_path"] == rows[33]["path"]
            and checker.reference(obs["relative_path"], unit) == registered[rows[33]["path"]]
            and checker.canonical(checker.parse(unit)) == unit,
            "archived unit bytes differ",
        )
    need(
        json.loads(pair(PREVIOUS, "independent-r0-stop-audit-a1.json", AUDIT))["status"]
        == "VERIFIED_STOP_NO_RETRY_NO_VERSION_CERTIFICATE",
        "prior audit differs",
    )


def trial_fit(checker, registry, catalog):
    # Only this test index and its container are synthesized. Their hashes are measured below.
    frozen_train = {x["case_id"]: x for x in registry["labels"]}
    train = [entry for entry in catalog["entries"] if entry["role"] == "train"]
    need(
        len(train) == len(frozen_train) == 528
        and all(
            checker.canonical(entry)
            == checker.canonical(frozen_train[entry["case"]["case_id"]]["entry"])
            for entry in train
        ),
        "publicly rebuilt catalog differs from sealed train entries",
    )
    context = {"source_revision": registry["labels"][0]["source_revision"]}
    manifest = {"context": context, "catalog": catalog}
    manifest_sha = sha(checker.canonical(manifest))
    outcomes = []
    for entry in train:
        saved = frozen_train[entry["case"]["case_id"]]
        ref = saved["artifact"]
        artifact = dict(
            relative_path=ref["path"].removeprefix("b3-v1-data/"),
            byte_size=ref["byte_size"],
            source_revision=saved["source_revision"],
            manifest_sha256=manifest_sha,
            access=dict(entry=entry, kind="label", artifact_sha256=ref["sha256"]),
        )
        outcomes.append(dict(entry=entry, status="succeeded", artifact=artifact))
    data = dict(manifest=manifest, manifest_sha256=manifest_sha, entries=outcomes)
    fit_context = dict(data_index=data, data_index_sha256=sha(checker.canonical(data)))
    fits = dict(
        index_version="topolab.b3.training-index.v1",
        context=fit_context,
        context_sha256=sha(checker.canonical(fit_context)),
    )
    return checker.canonical(fits), fit_context["data_index_sha256"]


def run_b3_entry(checker, raw, index_digest, expected_fit):
    class B3Complete(Exception):
        pass

    class ThroughB3(checker.OnceReader):
        @contextmanager
        def validation(self, relative, stage="source_validation"):
            with super().validation(relative, stage):
                yield
            if relative == FIT and stage == "source_validation":
                raise B3Complete

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder).resolve()
        fixture = root / FIT
        fixture.parent.mkdir()
        fixture.write_bytes(raw)
        reader = ThroughB3(
            root,
            1,
            16 * 1024**2,
            source_identity_checks=True,
            source_identity_policy=checker.PREBOUND_SHA256_POLICY,
        )
        spec = dict(relative_path=FIT, max_bytes=16 * 1024**2, expected_sha256=expected_fit)
        # This is a fresh standalone checker instance. Only the synthetic *data-index* pin changes.
        checker.B3_DATA_HASH = index_digest
        need(checker.CATALOG_HASH == CATALOG, "published catalog identity pin changed")
        try:
            checker.build_registry(
                reader, {"R0": {"literal_bootstrap_files": [spec]}}, selection_before_reference=True
            )
        except B3Complete:
            need(len(reader.table) == len(reader.observations) == 1, "fixture closing missing")
            return "ACCEPTED_B3_SECTION"
        except ValueError as error:
            return str(error)
    raise ValueError("B3 checkpoint was not reached")


def git_blob(head, path):
    return subprocess.check_output(["git", "show", head + ":" + path], cwd=REPO, timeout=20)


def replay(repo, pub):
    checker = module(repo / CHECKER, pub["checker_sha256"])
    loader_path = "scripts/full60_input_loader.py"
    loader = module(repo / loader_path, sha(git_blob(pub["source_main"], loader_path)))
    loader.install(require_locked_environment=True)
    sys.path.insert(0, str(repo / "src"))
    from topolab import b3_catalog

    need(
        Path(b3_catalog.__file__).resolve() == repo / "src/topolab/b3_catalog.py",
        "catalog builder outside the published checkout",
    )

    controls = archived_controls()
    original_rows(controls, checker)
    catalog = b3_catalog.build_b3_case_catalog().model_dump(mode="json")
    source_dir = repo / "src"
    imported = {
        Path(k).relative_to(repo).as_posix(): digest
        for k, digest in loader.loaded_source_sha256.items()
        if Path(k).is_relative_to(source_dir)
    }
    need(
        "src/topolab/b3_catalog.py" in imported
        and all(
            digest == sha(git_blob(pub["source_main"], path)) for path, digest in imported.items()
        ),
        "executed catalog builder or imported source differs from publication",
    )
    full = sha(checker.canonical(catalog))
    need(len(catalog["entries"]) == 752 and full == FULL_CATALOG, "full catalog fixture differs")
    raw, data_sha = trial_fit(checker, controls["registry.json"], catalog)
    stock = run_b3_entry(checker, raw, data_sha, sha(raw))
    summary = dict(
        archive_sha256=ARCHIVE,
        previous_unit_actual_sha256=UNIT_ACTUAL,
        compared_independent_refs=7,
        exporter_registry_refs=40,
        original_bootstrap_buffers_replayed=0,
        original_metadata_buffers_replayed=1,
        public_catalog_entries=752,
        sealed_train_entries_compared=528,
        full_public_catalog_sha256=full,
        expected_catalog_identity=CATALOG,
        constructed_fit_sha256=sha(raw),
        b3_entry=stock,
        new_original_reads=0,
    )
    need(
        stock == "ACCEPTED_B3_SECTION" and sha(checker.catalog_identity_bytes(catalog)) == CATALOG,
        "fixed B3 entry rejected",
    )
    for is_identity in (True, False):
        changed = deepcopy(catalog)
        # The held-out row keeps all 528 genuine training entries intact.
        row = next(x for x in changed["entries"] if x["role"] != "train")
        if is_identity:
            row["role"] = (
                "screen_validation" if row["role"] == "fit_validation" else "fit_validation"
            )
        else:
            row["physical_fingerprint"] = "0" * 64
        new_raw, new_sha = trial_fit(checker, controls["registry.json"], changed)
        need(sha(new_raw) != sha(raw), "raw byte mutation missing")
        outcome = run_b3_entry(checker, new_raw, new_sha, sha(new_raw))
        identity_sha = sha(checker.catalog_identity_bytes(changed))
        if is_identity:
            need(
                identity_sha != CATALOG and outcome == "embedded manifest/catalog differs",
                "changed identity accepted",
            )
            summary["identity_mutation"] = dict(identity_sha256=identity_sha, outcome=outcome)
        else:
            stale = run_b3_entry(checker, new_raw, new_sha, sha(raw))
            need(
                identity_sha == CATALOG and outcome == stock and stale == "source SHA differs",
                "nonidentity/raw SHA gates differ",
            )
            summary["nonidentity_mutation"] = dict(
                identity_sha256=identity_sha,
                new_raw_sha256=sha(new_raw),
                outcome=outcome,
                old_raw_pin_rejected=stale,
            )
    return summary


START, END = 1795381083469, 1795467483469
AUTHOR = "/root/full60_independent"
SUCCESS = "PASS_ARCHIVED_REFERENCES_AND_B3_ENTRY"
PACKAGE = "catalog-offline-package-a1.json"
ACTUAL = "catalog-offline-actual-a1.json"


@cache
def independent_wire():
    return module(Path(__file__).resolve().with_name("r0_read_independent.py"))


def verify_args(slot):
    need(type(slot) is int and slot in (3, 4), "candidate slot required")
    return [
        "/usr/bin/timeout",
        "-k",
        "2",
        "290",
        PYTHON,
        "-I",
        str(REPO / WORKER),
        "verify",
        "--slot",
        str(slot),
    ]


def verify_claim(slot, raw, publication):
    wire = independent_wire()
    claim = wire.parse(raw)
    need(
        claim
        == dict(
            schema="topolab.catalog-offline-claim.v1",
            slot=slot,
            actor=AUTHOR,
            argv=verify_args(slot),
            repo=str(REPO),
            source_main=publication["source_main"],
            worker_sha256=publication["worker_sha256"],
            charge_FULL=300,
            budget_sha256=BUDGET,
            claimed_ms=claim.get("claimed_ms"),
        )
        and wire.integer(claim["claimed_ms"])
        and START <= claim["claimed_ms"] <= END,
        "offline claim differs",
    )
    return claim


def validate_proof(proof):
    # These two public-fixture digests come from the retained, pre-repair replay.
    need(
        all(
            proof.get(k) == value
            for k, value in dict(
                archive_sha256=ARCHIVE,
                previous_unit_actual_sha256=UNIT_ACTUAL,
                compared_independent_refs=7,
                exporter_registry_refs=40,
                original_bootstrap_buffers_replayed=0,
                original_metadata_buffers_replayed=1,
                public_catalog_entries=752,
                sealed_train_entries_compared=528,
                full_public_catalog_sha256=FULL_CATALOG,
                constructed_fit_sha256=FIXTURE_FIT,
                expected_catalog_identity=CATALOG,
                new_original_reads=0,
                b3_entry="ACCEPTED_B3_SECTION",
            ).items()
        ),
        "offline replay coverage differs",
    )
    a, b = proof["identity_mutation"], proof["nonidentity_mutation"]
    wire = independent_wire()
    need(
        wire.digest_word(a["identity_sha256"])
        and a["identity_sha256"] != CATALOG
        and a["outcome"] == "embedded manifest/catalog differs"
        and b["identity_sha256"] == CATALOG
        and wire.digest_word(b["new_raw_sha256"])
        and b["new_raw_sha256"] != FIXTURE_FIT
        and b["outcome"] == "ACCEPTED_B3_SECTION"
        and b["old_raw_pin_rejected"] == "source SHA differs",
        "mutation controls differ",
    )


def published_source():
    need(
        Path.cwd() == REPO
        and Path(sys.executable).resolve() == Path(PYTHON)
        and sys.flags.isolated == 1,
        "published isolated checkout required",
    )

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=20)

    head = git("rev-parse", "HEAD").decode().strip()
    need(
        git("branch", "--show-current").strip() == b"main"
        and head == git("rev-parse", "origin/main").decode().strip()
        and not git("status", "--porcelain=v1", "-uall").strip(),
        "clean exact main required",
    )
    result = dict(source_main=head, repo=str(REPO))
    for key, path in (
        ("authority_sha256", PROTOCOL),
        ("worker_sha256", WORKER),
        ("checker_sha256", CHECKER),
    ):
        raw = (REPO / path).read_bytes()
        need(raw == git("show", head + ":" + path), "published bytes differ")
        result[key] = sha(raw)
    need(result["worker_sha256"] == MODULE_SOURCE_SHA256, "executed worker differs")
    return result


def verify_return(slot, report_sha):
    return dict(
        schema="topolab.catalog-offline-return.v1",
        slot=slot,
        status=SUCCESS,
        report_sha256=report_sha,
        own_future_return="NOT_CLAIMED",
    )


def verify_cli(slot):
    pub = published_source()
    wire = independent_wire()
    need(
        wire.compiled_sha256 == sha(git_blob(pub["source_main"], "scripts/r0_read_independent.py")),
        "executed receipt reader differs",
    )
    pair(E, "owner-budget-registration.json", BUDGET)
    prefix = f"offline-{slot:02d}-"
    claim_raw = pair(E, prefix + "claim.json")
    claim = verify_claim(slot, claim_raw, pub)
    started = time.time_ns() // 1_000_000
    need(claim["claimed_ms"] <= started < END, "claim clock differs")
    filer = "scripts/staged_input_filer.py"
    writer = module(REPO / filer, sha(git_blob(pub["source_main"], filer))).write_private

    def save(suffix, value):
        raw = wire.canonical(value)
        for dest in (E, E.with_name(E.name + "-backup")):
            writer(dest / (prefix + suffix + ".json"), raw)
        return sha(pair(E, prefix + suffix + ".json"))

    entry = dict(slot=slot, started_ms=started, claim_sha256=sha(claim_raw))
    entry_sha = save("entered", entry)
    proof = replay(REPO, pub)
    validate_proof(proof)
    ended = time.time_ns() // 1_000_000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    need(
        sys.platform == "darwin"
        and 0 < rss <= 4 * 1024**3
        and started <= ended <= END
        and ended - started <= 290000,
        "offline resource window differs",
    )
    report = dict(
        schema="topolab.catalog-offline-report.v1",
        status=SUCCESS,
        slot=slot,
        execution_identity=IDENTITY,
        budget_sha256=BUDGET,
        claim_sha256=sha(claim_raw),
        entered_sha256=entry_sha,
        started_ms=started,
        ended_ms=ended,
        self_rss_bytes=rss,
        proof=proof,
        **pub,
    )
    return verify_return(slot, save("report", report))


def verified_readiness(policy, tree):
    wire = independent_wire()
    need(
        wire.compiled_sha256 == tree["scripts/r0_read_independent.py"],
        "executed receipt reader differs",
    )
    paths = dict(package=str(E / PACKAGE), actual=str(E / ACTUAL))
    need(
        policy.get("execution_identity") == IDENTITY
        and policy.get("catalog_verification_paths") == paths
        and policy.get("new_input_budget")
        == dict(path=str(E / "owner-budget-registration.json"), sha256=BUDGET),
        "offline policy differs",
    )
    pair(E, "owner-budget-registration.json", BUDGET)
    package_raw, actual_raw = pair(E, PACKAGE), pair(E, ACTUAL)
    report, actual = wire.parse(package_raw), wire.parse(actual_raw)
    slot = report["slot"]
    argv = verify_args(slot)
    prefix = f"offline-{slot:02d}-"
    need(
        package_raw == pair(E, prefix + "report.json")
        and actual_raw == pair(E, prefix + "actual.json"),
        "original slot records differ",
    )
    claim_raw, entry_raw = pair(E, prefix + "claim.json"), pair(E, prefix + "entered.json")
    claim = verify_claim(slot, claim_raw, report)
    entry = wire.parse(entry_raw)
    first, last, output = wire.terminal(
        actual, argv, author=AUTHOR, cwd=str(REPO), window=(START, END)
    )
    start, end = report["started_ms"], report["ended_ms"]
    need(
        report.get("schema") == "topolab.catalog-offline-report.v1"
        and report["status"] == SUCCESS
        and report["execution_identity"] == IDENTITY
        and report["budget_sha256"] == BUDGET
        and report["repo"] == str(REPO)
        and wire.digest_word(report["source_main"], 40)
        and report["authority_sha256"] == tree[PROTOCOL]
        and report["worker_sha256"] == tree[WORKER] == MODULE_SOURCE_SHA256
        and report["checker_sha256"] == tree[CHECKER]
        and report["claim_sha256"] == sha(claim_raw)
        and report["entered_sha256"] == sha(entry_raw)
        and entry == dict(slot=slot, started_ms=start, claim_sha256=sha(claim_raw))
        and wire.integer(start)
        and wire.integer(end)
        and claim["claimed_ms"] <= first <= start <= end <= last
        and wire.integer(report["self_rss_bytes"], 1)
        and report["self_rss_bytes"] <= 4 * 1024**3
        and output == wire.canonical(verify_return(slot, sha(package_raw))),
        "published offline verification/actual differs",
    )
    validate_proof(report["proof"])
    return dict(
        package=dict(path=paths["package"], sha256=sha(package_raw)),
        actual=dict(path=paths["actual"], sha256=sha(actual_raw)),
        **{
            k: report[k]
            for k in ("source_main", "authority_sha256", "worker_sha256", "checker_sha256")
        },
        slot=slot,
        verified_returned_ms=last,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["verify"])
    parser.add_argument("--slot", required=True, type=int, choices=[3, 4])
    args = parser.parse_args()
    print(independent_wire().canonical(verify_cli(args.slot)).decode(), end="")
