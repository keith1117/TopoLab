"""Bind the accepted historical B3 return to the new A1 software release.

This is metadata replay and same-buffer source comparison. It never starts an
old verifier, reopens a business file, or claims a new complete R0 acceptance.
"""

import argparse
import base64
import hashlib
import json
import os
import resource
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

SOURCE_CHECKOUT = Path(__file__).resolve().parents[1]
REPO = Path('/private/tmp/topolab-input-cycle-20261123')
DATA = Path('/Users/keith1117/Documents/TopoLab-data')
CAMPAIGN = DATA/'input-cycle-20261123'
E = DATA/'input-cycle-20261123-a1'
PREVIOUS = DATA/'catalog-r0-acceptance-20261122'
IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a1.v1'
AUTHOR = '/root/full60_independent'
PROTOCOL = 'docs/planning/input_cycle_a1_contract.json'
WORKER = 'scripts/input_cycle_proof.py'
CHECKER = 'scripts/p17_m2_input_export_independent.py'
OLD_WORKER = 'scripts/catalog_input_offline.py'
WIRE = 'scripts/r0_read_independent.py'
OLD_PROTOCOL = 'docs/planning/catalog_input_contract.json'
PREVIOUS_MAIN = '2a8e88b85d80b570b384ea923ef3fd312286cb8b'
CAMPAIGN_SHA = '9ab62a69584a1ec2179b7fb9bd13a7b23a5564bcd8413a34f5ecb5f99d3c848b'
ATTEMPT_SHA = 'ebfe2a88f7c838a08bbc5e7f04c7978dd446b552c9e3db206b3a044dec580862'
PREVIOUS_PACKAGE_SHA = '8a306ba388fdb19d58826a5e83c8df011ede3ca0547053a83521ba8ce889fdc1'
PREVIOUS_ACTUAL_SHA = 'ee4839d8ff4464c24f2a5e4c33a37b495ec069a48ce39838c82d517729a770ea'
PREVIOUS_CLAIM_SHA = '750bd303dbcb9f8d5b2e390a1ab1d72731dcfeea98e92995076a483856747cdf'
SOURCE_PINS = {
    CHECKER: '19a146ce8788dcc05ac089cb8badc8d04f16b2ae21e6625a8b3fdbf9e95c5198',
    OLD_WORKER: '98b3d8085886c1835774e03401dbf8b03beed47fba64f467072a658eac114949',
    WIRE: 'b7a1bd2eed09fd469c1740096a337eb0c31269663713615d7c08bc8d715a8f40',
    OLD_PROTOCOL: 'ce7981cb3b60f70bd37568a0d2d226e6a6adcf1592d838d2ef95049e1cd50fc5',
}
PYTHON = ('/Library/Frameworks/Python.framework/Versions/3.12/Resources/'
          'Python.app/Contents/MacOS/Python')
START, END = 1795403546212, 1795576346212
PACKAGE, ACTUAL = 'cycle-offline-report-a1.json', 'cycle-offline-actual-a1.json'
SUCCESS = 'PASS_CURRENT_RELEASE_REUSES_VERIFIED_B3'
CAP = 16*1024**2
MODULE_SOURCE_SHA256 = None  # Filled by the actual source-buffer compiler/loader.


def need(ok, reason):
    if not ok:
        raise ValueError('INPUT_CYCLE_PROOF_STOP: '+reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                       allow_nan=False)+'\n').encode('ascii')


def parse(raw):
    need(type(raw) is bytes and 0 < len(raw) <= CAP, 'bounded metadata buffer required')

    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate metadata key')
            result[key] = value
        return result

    def invalid(_):
        raise ValueError('INPUT_CYCLE_PROOF_STOP: nonfinite metadata')

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def _directory(path):
    need(path.is_absolute() and '..' not in path.parts, 'literal absolute metadata path required')
    folder = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in path.parts[1:]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=folder)
            os.close(folder)
            folder = child
        return folder
    except BaseException:
        os.close(folder)
        raise


def _read(path):
    path = Path(path)
    folder = _directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
        try:
            before = os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                 and before.st_nlink == 1 and 0 < before.st_size <= CAP,
                 'bounded owned single-link software/metadata file required')
            chunks, count = [], 0
            while count <= before.st_size:
                block = os.read(fd, min(65536, before.st_size+1-count))
                if not block:
                    break
                chunks.append(block)
                count += len(block)
            def identity(value):
                return tuple(getattr(value, key) for key in (
                    'st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns',
                    'st_nlink', 'st_mode', 'st_uid'))

            need(count == before.st_size and identity(os.fstat(fd)) == identity(before)
                 and identity(os.stat(path.name, dir_fd=folder, follow_symlinks=False))
                 == identity(before),
                 'software/metadata physical identity changed')
            return b''.join(chunks)
        finally:
            os.close(fd)
    finally:
        os.close(folder)


def _compile(raw, name, relative):
    path = SOURCE_CHECKOUT/relative
    module = ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    module.compiled_sha256 = module.MODULE_SOURCE_SHA256 = sha(raw)
    loader = sys.modules.get('full60_input_loader')
    if loader is not None:
        loader.loaded_source_sha256[str(path)] = sha(raw)
    return module


def _sources():
    sources = {name: _read(SOURCE_CHECKOUT/name) for name in SOURCE_PINS}
    need(all(sha(raw) == SOURCE_PINS[name] for name, raw in sources.items()),
         'historical/current source SHA differs')
    return sources


def _wire():
    raw = _read(SOURCE_CHECKOUT/WIRE)
    need(sha(raw) == SOURCE_PINS[WIRE], 'receipt-reader source SHA differs')
    return _compile(raw, 'cycle_receipt_reader', WIRE)


def _executed_sha():
    loader = sys.modules.get('full60_input_loader')
    observed = (getattr(loader, 'loaded_source_sha256', {}).get(str(SOURCE_CHECKOUT/WORKER))
                if loader is not None else None)
    result = MODULE_SOURCE_SHA256 if MODULE_SOURCE_SHA256 is not None else observed
    need(type(result) is str and len(result) == 64
         and (observed is None or observed == result), 'actual compiled verifier SHA unavailable')
    return result


def pair(root, name, expected=None):
    root = Path(root)
    wire = _wire()
    raw = wire.read_pair(root/name, root.with_name(root.name+'-backup')/name)
    need(expected is None or sha(raw) == expected, 'paired metadata SHA differs: '+name)
    return raw


def prior_catalog():
    return dict(source_main=PREVIOUS_MAIN,
                package=dict(path=str(E/'prior-catalog-report.json'), sha256=PREVIOUS_PACKAGE_SHA),
                actual=dict(path=str(E/'prior-catalog-actual.json'), sha256=PREVIOUS_ACTUAL_SHA))


def verify_history(report_raw, actual_raw, claim_raw, entered_raw, *, sources):
    """Receipt/source replay; old program entrypoints are never called."""
    need(all(type(raw) is bytes and 0 < len(raw) <= CAP
             for raw in (report_raw, actual_raw, claim_raw, entered_raw)),
         'bounded historical receipt buffer required')
    need(sha(report_raw) == PREVIOUS_PACKAGE_SHA and sha(actual_raw) == PREVIOUS_ACTUAL_SHA
         and sha(claim_raw) == PREVIOUS_CLAIM_SHA, 'historical raw receipt SHA differs')
    need(type(sources) is dict and set(sources) == set(SOURCE_PINS)
         and all(type(raw) is bytes and sha(raw) == SOURCE_PINS[name]
                 for name, raw in sources.items()), 'historical source SHA differs')
    report, actual, claim, entry = map(parse, (report_raw, actual_raw, claim_raw, entered_raw))
    need(sha(entered_raw) == report['entered_sha256'], 'historical entered receipt differs')
    wire = _compile(sources[WIRE], 'cycle_historical_wire', WIRE)
    old = _compile(sources[OLD_WORKER], 'cycle_historical_catalog', OLD_WORKER)
    previous = _compile(sources[CHECKER], 'cycle_previous_checker', CHECKER)
    current = _compile(sources[CHECKER], 'cycle_current_checker', CHECKER)
    old.independent_wire = lambda: wire
    first, last, output = wire.terminal(actual, old.verify_args(3), author=AUTHOR,
                                         cwd=str(old.REPO), window=(old.START, old.END))
    need(report['schema'] == 'topolab.catalog-offline-report.v1'
         and report['status'] == old.SUCCESS and report['execution_identity'] == old.IDENTITY
         and report['budget_sha256'] == old.BUDGET and report['repo'] == str(old.REPO)
         and type(report['slot']) is int and report['slot'] == 3
         and report['source_main'] == PREVIOUS_MAIN
         and report['worker_sha256'] == old.compiled_sha256 == SOURCE_PINS[OLD_WORKER]
         and report['checker_sha256'] == previous.compiled_sha256 == current.compiled_sha256
         and report['authority_sha256'] == SOURCE_PINS[OLD_PROTOCOL]
         and report['claim_sha256'] == sha(claim_raw)
         and claim == old.verify_claim(3, claim_raw, report)
         and entry == dict(slot=3, started_ms=report['started_ms'], claim_sha256=sha(claim_raw))
         and wire.integer(report['started_ms']) and wire.integer(report['ended_ms'])
         and claim['claimed_ms'] <= first <= report['started_ms'] <= report['ended_ms'] <= last
         and wire.integer(report['self_rss_bytes'], 1) and report['self_rss_bytes'] <= 4*1024**3
         and output == canonical(old.verify_return(3, sha(report_raw))),
         'historical identity, source, clocks or original return differs')
    old.validate_proof(report['proof'])
    for key in ('compared_independent_refs', 'exporter_registry_refs',
                'original_bootstrap_buffers_replayed', 'original_metadata_buffers_replayed',
                'public_catalog_entries', 'sealed_train_entries_compared', 'new_original_reads'):
        need(type(report['proof'][key]) is int, 'historical proof integer type differs')
    return dict(previous_catalog_source_main=PREVIOUS_MAIN,
                previous_catalog_package_sha256=sha(report_raw),
                previous_catalog_actual_sha256=sha(actual_raw),
                previous_catalog_worker_sha256=old.compiled_sha256,
                previous_catalog_checker_sha256=previous.compiled_sha256,
                historical_source_sha256=dict(SOURCE_PINS),
                historical_b3_controls_sha256=sha(canonical(report['proof'])),
                previous_verified_returned_ms=last,
                current_checker_sha256=current.compiled_sha256,
                current_checker_same_bytes_as_historical=True,
                historical_receipt_replay=True, old_verifier_entry_calls=0,
                new_original_reads=0, new_complete_R0_acceptance=False)


def verify_args():
    return ['/usr/bin/timeout', '-k', '2', '290', PYTHON, '-I', str(REPO/WORKER), 'verify']


def verify_return(report_sha):
    return dict(schema='topolab.input-cycle-offline-return.v1', slot=1, status=SUCCESS,
                report_sha256=report_sha, own_future_return='NOT_CLAIMED')


def _policy(policy):
    need(policy.get('execution_identity') == IDENTITY
         and policy.get('cycle_verification_paths')
         == dict(package=str(E/PACKAGE), actual=str(E/ACTUAL))
         and policy.get('campaign_budget')
         == dict(path=str(CAMPAIGN/'campaign-budget.json'), sha256=CAMPAIGN_SHA)
         and policy.get('new_input_budget')
         == dict(path=str(CAMPAIGN/'attempt-1-budget.json'), sha256=ATTEMPT_SHA)
         and policy.get('prior_catalog') == prior_catalog(), 'A1 proof policy differs')
    pair(CAMPAIGN, 'campaign-budget.json', CAMPAIGN_SHA)
    pair(CAMPAIGN, 'attempt-1-budget.json', ATTEMPT_SHA)


def _claim(raw, publication):
    claim = parse(raw)
    need(claim == dict(schema='topolab.input-cycle-offline-claim.v1', slot=1, actor=AUTHOR,
                       argv=verify_args(), repo=str(REPO), source_main=publication['source_main'],
                       worker_sha256=publication['worker_sha256'], budget_sha256=CAMPAIGN_SHA,
                       attempt_budget_sha256=ATTEMPT_SHA, charge_FULL=300,
                       claimed_ms=claim.get('claimed_ms'))
         and type(claim['slot']) is int and type(claim['charge_FULL']) is int
         and type(claim['claimed_ms']) is int and START <= claim['claimed_ms'] <= END,
         'A1 independent offline claim differs')
    return claim


def _save(root, name, value):
    need((root, name) in ((CAMPAIGN, 'offline-01-entered.json'), (E, PACKAGE)),
         'fixed offline receipt namespace required')
    raw = canonical(value)
    need(len(raw) <= CAP, 'offline report exceeds fixed wire cap')
    for directory in (root, root.with_name(root.name+'-backup')):
        parent = _directory(directory)
        try:
            owner = os.fstat(parent)
            need(owner.st_uid == os.getuid() and stat.S_IMODE(owner.st_mode) == 0o700,
                 'private owned receipt directory required')
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=parent)
            try:
                count = 0
                while count < len(raw):
                    written = os.write(fd, raw[count:])
                    need(written > 0, 'partial offline receipt write')
                    count += written
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(parent)
        finally:
            os.close(parent)
    need(pair(root, name, sha(raw)) == raw, 'offline receipt pair differs')
    return sha(raw)


def current_publication():
    need(SOURCE_CHECKOUT == REPO and Path.cwd() == REPO
         and Path(sys.executable).resolve() == Path(PYTHON)
         and sys.flags.isolated == 1, 'published physical isolated checkout required')

    def git(*args):
        return subprocess.check_output(['git', *args], cwd=REPO, timeout=20)

    head = git('rev-parse', 'HEAD').decode().strip()
    need(_wire().digest_word(head, 40) and git('branch', '--show-current').strip() == b'main'
         and head == git('rev-parse', 'origin/main').decode().strip()
         and not git('status', '--porcelain=v1', '-uall').strip(), 'clean exact main required')
    for name, pin in SOURCE_PINS.items():
        raw = _read(REPO/name)
        need(sha(raw) == pin and raw == git('show', PREVIOUS_MAIN+':'+name)
             and raw == git('show', head+':'+name), 'historical published source differs')
    publication = dict(source_main=head, repo=str(REPO))
    for key, name in (('authority_sha256', PROTOCOL), ('worker_sha256', WORKER),
                      ('checker_sha256', CHECKER)):
        raw = _read(REPO/name)
        need(raw == git('show', head+':'+name), 'new published source differs')
        publication[key] = sha(raw)
    need(publication['worker_sha256'] == _executed_sha(), 'executed new verifier differs')
    return publication


def verify_cli():
    publication = current_publication()
    _policy(parse(_read(REPO/PROTOCOL)))
    claim_raw = pair(CAMPAIGN, 'offline-01-claim.json')
    claim = _claim(claim_raw, publication)
    start = time.time_ns()//1_000_000
    need(claim['claimed_ms'] <= start < END, 'A1 verifier start outside original window')
    entry = dict(slot=1, execution_identity=IDENTITY, started_ms=start, claim_sha256=sha(claim_raw))
    entry_sha = _save(CAMPAIGN, 'offline-01-entered.json', entry)
    old_claim = pair(PREVIOUS, 'offline-03-claim.json', PREVIOUS_CLAIM_SHA)
    old_entry = pair(PREVIOUS, 'offline-03-entered.json')
    history = verify_history(pair(E, 'prior-catalog-report.json', PREVIOUS_PACKAGE_SHA),
                             pair(E, 'prior-catalog-actual.json', PREVIOUS_ACTUAL_SHA),
                             old_claim, old_entry, sources=_sources())
    end = time.time_ns()//1_000_000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    need(sys.platform == 'darwin' and type(rss) is int and 0 < rss <= 4*1024**3
         and start <= end <= END and end-start <= 290000, 'A1 verifier resource window differs')
    report = dict(schema='topolab.input-cycle-offline-report.v1', status=SUCCESS, slot=1,
                  execution_identity=IDENTITY, budget_sha256=CAMPAIGN_SHA,
                  attempt_budget_sha256=ATTEMPT_SHA, claim_sha256=sha(claim_raw),
                  entered_sha256=entry_sha, started_ms=start, ended_ms=end, self_rss_bytes=rss,
                  previous_claim_base64=base64.b64encode(old_claim).decode(),
                  previous_entered_base64=base64.b64encode(old_entry).decode(), history=history,
                  **publication)
    return verify_return(_save(E, PACKAGE, report))


def verified_readiness(policy, tree):
    """Replay the new I-owned original return; no Git/GH, original or target IO."""
    _policy(policy)
    wire = _wire()
    need(wire.compiled_sha256 == tree[WIRE], 'executed new receipt reader differs')
    report_raw, actual_raw = pair(E, PACKAGE), pair(E, ACTUAL)
    report, actual = parse(report_raw), parse(actual_raw)
    claim_raw, entered_raw = pair(CAMPAIGN, 'offline-01-claim.json'), pair(
        CAMPAIGN, 'offline-01-entered.json')
    claim, entry = _claim(claim_raw, report), parse(entered_raw)
    first, last, output = wire.terminal(actual, verify_args(), author=AUTHOR, cwd=str(REPO),
                                         window=(START, END))
    old_claim = base64.b64decode(report['previous_claim_base64'], validate=True)
    old_entry = base64.b64decode(report['previous_entered_base64'], validate=True)
    history = verify_history(pair(E, 'prior-catalog-report.json', PREVIOUS_PACKAGE_SHA),
                             pair(E, 'prior-catalog-actual.json', PREVIOUS_ACTUAL_SHA),
                             old_claim, old_entry, sources=_sources())
    need(report['schema'] == 'topolab.input-cycle-offline-report.v1'
         and report['status'] == SUCCESS and report['execution_identity'] == IDENTITY
         and type(report['slot']) is int and report['slot'] == 1
         and report['budget_sha256'] == CAMPAIGN_SHA
         and report['attempt_budget_sha256'] == ATTEMPT_SHA
         and report['repo'] == str(REPO) and wire.digest_word(report['source_main'], 40)
         and report['source_main'] != PREVIOUS_MAIN
         and report['authority_sha256'] == tree[PROTOCOL]
         and report['worker_sha256'] == tree[WORKER] == _executed_sha()
         and report['checker_sha256'] == tree[CHECKER] == history['current_checker_sha256']
         and report['claim_sha256'] == sha(claim_raw)
         and report['entered_sha256'] == sha(entered_raw)
         and type(entry.get('slot')) is int
         and entry == dict(slot=1, execution_identity=IDENTITY, started_ms=report['started_ms'],
                           claim_sha256=sha(claim_raw))
         and wire.integer(report['started_ms']) and wire.integer(report['ended_ms'])
         and claim['claimed_ms'] <= first <= report['started_ms'] <= report['ended_ms'] <= last
         and history['previous_verified_returned_ms'] <= first
         and wire.integer(report['self_rss_bytes'], 1) and report['self_rss_bytes'] <= 4*1024**3
         and canonical(report['history']) == canonical(history)
         and output == canonical(verify_return(sha(report_raw))),
         'A1 report/source/history/original return differs')
    return dict(package=dict(path=str(E/PACKAGE), sha256=sha(report_raw)),
                actual=dict(path=str(E/ACTUAL), sha256=sha(actual_raw)),
                source_main=report['source_main'], previous_catalog_source_main=PREVIOUS_MAIN,
                authority_sha256=report['authority_sha256'], worker_sha256=report['worker_sha256'],
                checker_sha256=report['checker_sha256'],
                previous_catalog_package_sha256=PREVIOUS_PACKAGE_SHA,
                previous_catalog_actual_sha256=PREVIOUS_ACTUAL_SHA, slot=1,
                verified_returned_ms=last)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['verify'])
    parser.parse_args()
    source = _read(Path(__file__).absolute())
    compiled = _compile(source, 'input_cycle_proof_runtime', WORKER)
    print(canonical(compiled.verify_cli()).decode(), end='')
