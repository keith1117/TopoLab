"""A1 bridge uses temporary public receipts; no original or custody IO."""

import importlib.util
import os
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]


def subject():
    path = REPO/'scripts/input_cycle_proof.py'
    spec = importlib.util.spec_from_file_location('declared_cycle_proof', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unbound_old_receipt_cannot_execute_historical_code(monkeypatch):
    module = subject()
    monkeypatch.setattr(module, '_compile', lambda *_: pytest.fail('unbound code executed'))
    with pytest.raises(ValueError, match='historical|SHA|buffer'):
        module.verify_history(b'{}\n', b'{}\n', b'{}\n', b'{}\n', sources={})


def test_fixed_new_cli_has_own_identity_and_no_old_entry():
    module = subject()
    assert module.verify_args() == [
        '/usr/bin/timeout', '-k', '2', '290', module.PYTHON, '-I',
        str(module.REPO/'scripts/input_cycle_proof.py'), 'verify']
    assert module.IDENTITY.endswith('.cycle-20261123-a1.v1')
    assert module.PREVIOUS_MAIN == '2a8e88b85d80b570b384ea923ef3fd312286cb8b'


def history_fixture(module, monkeypatch, damage=None):
    """Synthetic receipt pins are explicitly patched; published software is read only."""
    sources = module._sources()
    old = module._compile(sources[module.OLD_WORKER], 'declared_old_validator', module.OLD_WORKER)
    wire = module._wire()
    first = old.START+100
    claim = dict(schema='topolab.catalog-offline-claim.v1', slot=3, actor=module.AUTHOR,
                 argv=old.verify_args(3), repo=str(old.REPO), source_main=module.PREVIOUS_MAIN,
                 worker_sha256=module.SOURCE_PINS[module.OLD_WORKER], charge_FULL=300,
                 budget_sha256=old.BUDGET, claimed_ms=first-1)
    claim_raw = module.canonical(claim)
    entry = dict(slot=3, started_ms=first+1, claim_sha256=module.sha(claim_raw))
    if damage == 'old-entry':
        entry['claim_sha256'] = '0'*64
    entry_raw = module.canonical(entry)
    proof = dict(archive_sha256=old.ARCHIVE, previous_unit_actual_sha256=old.UNIT_ACTUAL,
                 compared_independent_refs=7, exporter_registry_refs=40,
                 original_bootstrap_buffers_replayed=0, original_metadata_buffers_replayed=1,
                 public_catalog_entries=752, sealed_train_entries_compared=528,
                 full_public_catalog_sha256=old.FULL_CATALOG,
                 constructed_fit_sha256=old.FIXTURE_FIT,
                 expected_catalog_identity=old.CATALOG, new_original_reads=0,
                 b3_entry='ACCEPTED_B3_SECTION',
                 identity_mutation=dict(identity_sha256='f'*64,
                                        outcome='embedded manifest/catalog differs'),
                 nonidentity_mutation=dict(identity_sha256=old.CATALOG,
                                           new_raw_sha256='e'*64, outcome='ACCEPTED_B3_SECTION',
                                           old_raw_pin_rejected='source SHA differs'))
    if damage == 'old-counter':
        proof['original_bootstrap_buffers_replayed'] = 7
    if damage == 'old-counter-bool':
        proof['new_original_reads'] = False
    if damage == 'old-negative-control':
        proof['nonidentity_mutation']['old_raw_pin_rejected'] = 'ACCEPTED_B3_SECTION'
    report = dict(schema='topolab.catalog-offline-report.v1', status=old.SUCCESS, slot=3,
                  execution_identity=old.IDENTITY, budget_sha256=old.BUDGET,
                  repo=str(old.REPO), source_main=module.PREVIOUS_MAIN,
                  authority_sha256=module.SOURCE_PINS[module.OLD_PROTOCOL],
                  worker_sha256=module.SOURCE_PINS[module.OLD_WORKER],
                  checker_sha256=module.SOURCE_PINS[module.CHECKER],
                  claim_sha256=module.sha(claim_raw), entered_sha256=module.sha(entry_raw),
                  started_ms=first+1, ended_ms=first+2, self_rss_bytes=1234, proof=proof)
    if damage == 'old-main':
        report['source_main'] = 'a'*40
    if damage == 'old-source-claim':
        report['checker_sha256'] = '0'*64
    raw = module.canonical(report)
    request = dict(cmd=wire.literal_command(old.verify_args(3)), workdir=str(old.REPO),
                   max_output_tokens=5000)
    result = dict(exit_code=0,
                  output=module.canonical(old.verify_return(3, module.sha(raw))).decode())
    if damage == 'old-exit-bool':
        result['exit_code'] = False
    if damage == 'old-exit-one':
        result['exit_code'] = 1
    if damage == 'old-stdout':
        result['output'] = '{}\n'
    actual = dict(schema=wire.ACTUAL_SCHEMA, author=module.AUTHOR, argv=old.verify_args(3),
                  request=request, responses=[dict(tool='exec_command', arguments=request,
                      requested_ms=first, returned_ms=first+3, result=result)])
    if damage == 'old-actual-author':
        actual['author'] = '/root'
    if damage == 'old-late':
        actual['responses'][0]['returned_ms'] = first+300000
    actual_raw = module.canonical(actual)
    monkeypatch.setattr(module, 'PREVIOUS_PACKAGE_SHA', module.sha(raw))
    monkeypatch.setattr(module, 'PREVIOUS_ACTUAL_SHA', module.sha(actual_raw))
    monkeypatch.setattr(module, 'PREVIOUS_CLAIM_SHA', module.sha(claim_raw))
    return raw, actual_raw, claim_raw, entry_raw, sources


def test_historical_bridge_compiles_same_pinned_checker_without_old_entry(monkeypatch):
    module = subject()
    report, actual, claim, entry, sources = history_fixture(module, monkeypatch)
    value = module.verify_history(report, actual, claim, entry, sources=sources)
    assert value['previous_catalog_source_main'] == module.PREVIOUS_MAIN
    assert value['current_checker_sha256'] == module.SOURCE_PINS[module.CHECKER]
    assert value['current_checker_same_bytes_as_historical'] is True
    assert value['new_complete_R0_acceptance'] is False
    assert value['old_verifier_entry_calls'] == value['new_original_reads'] == 0


@pytest.mark.parametrize('damage', ['old-entry', 'old-counter', 'old-counter-bool',
    'old-negative-control', 'old-main', 'old-source-claim', 'old-exit-bool', 'old-exit-one',
    'old-stdout', 'old-actual-author', 'old-late'])
def test_historical_raw_semantics_are_independent_of_claimed_pass(monkeypatch, damage):
    module = subject()
    report, actual, claim, entry, sources = history_fixture(module, monkeypatch, damage)
    with pytest.raises(ValueError):
        module.verify_history(report, actual, claim, entry, sources=sources)


def test_changed_historical_code_is_denied_before_compile(monkeypatch):
    module = subject()
    report, actual, claim, entry, sources = history_fixture(module, monkeypatch)
    sources[module.CHECKER] += b'\n'
    monkeypatch.setattr(module, '_compile', lambda *_: pytest.fail('unbound code compiled'))
    with pytest.raises(ValueError, match='source SHA'):
        module.verify_history(report, actual, claim, entry, sources=sources)


def test_source_digest_records_the_actual_compiled_buffer(monkeypatch):
    module = subject()
    loader = ModuleType('full60_input_loader')
    loader.loaded_source_sha256 = {}
    monkeypatch.setitem(module.sys.modules, 'full60_input_loader', loader)
    raw = b'MODULE_SOURCE_SHA256="later-file-claim"\n'
    value = module._compile(raw, 'declared_source_only_fixture', 'scripts/declared-fixture.py')
    assert value.compiled_sha256 == value.MODULE_SOURCE_SHA256 == module.sha(raw)
    assert loader.loaded_source_sha256[str(module.SOURCE_CHECKOUT/'scripts/declared-fixture.py')]
    assert value.MODULE_SOURCE_SHA256 != 'later-file-claim'


def readiness_fixture(module, monkeypatch, tmp_path):
    old_report, old_actual, old_claim, old_entry, sources = history_fixture(module, monkeypatch)
    history = module.verify_history(old_report, old_actual, old_claim, old_entry, sources=sources)
    monkeypatch.setattr(module, 'E', tmp_path/'a1')
    monkeypatch.setattr(module, 'CAMPAIGN', tmp_path/'campaign')
    campaign, attempt = b'{"declared":"campaign"}\n', b'{"declared":"attempt1"}\n'
    monkeypatch.setattr(module, 'CAMPAIGN_SHA', module.sha(campaign))
    monkeypatch.setattr(module, 'ATTEMPT_SHA', module.sha(attempt))
    monkeypatch.setattr(module, 'MODULE_SOURCE_SHA256', '9'*64)
    monkeypatch.setattr(module, '_executed_sha', lambda: '9'*64)
    wire = module._wire()
    policy = dict(execution_identity=module.IDENTITY,
                  cycle_verification_paths=dict(package=str(module.E/module.PACKAGE),
                                                 actual=str(module.E/module.ACTUAL)),
                  campaign_budget=dict(path=str(module.CAMPAIGN/'campaign-budget.json'),
                                       sha256=module.CAMPAIGN_SHA),
                  new_input_budget=dict(path=str(module.CAMPAIGN/'attempt-1-budget.json'),
                                        sha256=module.ATTEMPT_SHA),
                  prior_catalog=module.prior_catalog())
    tree = {module.WIRE: module.SOURCE_PINS[module.WIRE], module.PROTOCOL: 'b'*64,
            module.WORKER: module.MODULE_SOURCE_SHA256,
            module.CHECKER: module.SOURCE_PINS[module.CHECKER]}
    first = module.START+100
    claim = dict(schema='topolab.input-cycle-offline-claim.v1', slot=1, actor=module.AUTHOR,
                 argv=module.verify_args(), repo=str(module.REPO), source_main='d'*40,
                 worker_sha256=tree[module.WORKER], budget_sha256=module.CAMPAIGN_SHA,
                 attempt_budget_sha256=module.ATTEMPT_SHA, charge_FULL=300, claimed_ms=first-1)
    claim_raw = module.canonical(claim)
    entry = dict(slot=1, execution_identity=module.IDENTITY, started_ms=first+1,
                 claim_sha256=module.sha(claim_raw))
    report = dict(schema='topolab.input-cycle-offline-report.v1', status=module.SUCCESS, slot=1,
                  execution_identity=module.IDENTITY, budget_sha256=module.CAMPAIGN_SHA,
                  attempt_budget_sha256=module.ATTEMPT_SHA, claim_sha256=module.sha(claim_raw),
                  entered_sha256=module.sha(module.canonical(entry)), started_ms=first+1,
                  ended_ms=first+2, self_rss_bytes=2000, source_main='d'*40, repo=str(module.REPO),
                  authority_sha256=tree[module.PROTOCOL], worker_sha256=tree[module.WORKER],
                  checker_sha256=tree[module.CHECKER], history=history,
                  previous_claim_base64=module.base64.b64encode(old_claim).decode(),
                  previous_entered_base64=module.base64.b64encode(old_entry).decode())
    raw = module.canonical(report)
    request = dict(cmd=wire.literal_command(module.verify_args()), workdir=str(module.REPO),
                   max_output_tokens=5000)
    actual = dict(schema=wire.ACTUAL_SCHEMA, author=module.AUTHOR, argv=module.verify_args(),
                  request=request, responses=[dict(tool='exec_command', arguments=request,
                     requested_ms=first, returned_ms=first+3, result=dict(exit_code=0,
                     output=module.canonical(module.verify_return(module.sha(raw))).decode()))])
    records = {(str(module.E), 'prior-catalog-report.json'): old_report,
               (str(module.E), 'prior-catalog-actual.json'): old_actual,
               (str(module.CAMPAIGN), 'campaign-budget.json'): campaign,
               (str(module.CAMPAIGN), 'attempt-1-budget.json'): attempt}

    def pair(root, name, expected=None):
        raw = records[(str(root), name)]
        module.need(expected is None or module.sha(raw) == expected, 'fixture pair SHA differs')
        return raw

    monkeypatch.setattr(module, 'pair', pair)

    def save():
        raw = module.canonical(report)
        actual['responses'][0]['result']['output'] = module.canonical(
            module.verify_return(module.sha(raw))).decode()
        for root, name, value in ((module.E, module.PACKAGE, report),
                                 (module.E, module.ACTUAL, actual),
                                 (module.CAMPAIGN, 'offline-01-claim.json', claim),
                                 (module.CAMPAIGN, 'offline-01-entered.json', entry)):
            records[(str(root), name)] = module.canonical(value)

    save()
    return policy, tree, report, actual, claim, entry, save


def test_new_return_binds_new_head_budget_and_history_without_git_or_old_roles(
        monkeypatch, tmp_path):
    module = subject()
    policy, tree, *_ = readiness_fixture(module, monkeypatch, tmp_path)
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *_a, **_k: pytest.fail('Git ran'))
    value = module.verified_readiness(policy, tree)
    assert value['source_main'] == 'd'*40
    assert value['previous_catalog_source_main'] == module.PREVIOUS_MAIN
    assert value['source_main'] != value['previous_catalog_source_main']
    assert value['verified_returned_ms'] == module.START+103


def test_verify_cli_connects_only_the_registered_receipt_outputs_in_a_mock(monkeypatch, tmp_path):
    module = subject()
    policy, tree, report, _actual, _claim, _entry, _save = readiness_fixture(
        module, monkeypatch, tmp_path)
    publication = {key: report[key] for key in (
        'source_main', 'repo', 'authority_sha256', 'worker_sha256', 'checker_sha256')}
    monkeypatch.setattr(module, 'current_publication', lambda: publication)
    original_read, original_pair = module._read, module.pair
    monkeypatch.setattr(module, '_read', lambda path:
                        module.canonical(policy) if path == module.REPO/module.PROTOCOL
                        else original_read(path))

    def pair(root, name, expected=None):
        if root == module.PREVIOUS and name in ('offline-03-claim.json', 'offline-03-entered.json'):
            field = 'previous_claim_base64' if 'claim' in name else 'previous_entered_base64'
            raw = module.base64.b64decode(report[field], validate=True)
            assert expected is None or module.sha(raw) == expected
            return raw
        return original_pair(root, name, expected)

    monkeypatch.setattr(module, 'pair', pair)
    writes = []

    def save(root, name, value):
        writes.append((root, name, value))
        return module.sha(module.canonical(value))

    monkeypatch.setattr(module, '_save', save)
    clock = iter([module.START+101, module.START+102])
    monkeypatch.setattr(module.time, 'time_ns', lambda: next(clock)*1_000_000)
    monkeypatch.setattr(module, 'sys',
                        SimpleNamespace(platform='darwin', modules=module.sys.modules))
    monkeypatch.setattr(module.resource, 'getrusage', lambda _: SimpleNamespace(ru_maxrss=123456))
    value = module.verify_cli()
    assert [(root, name) for root, name, _ in writes] == [
        (module.CAMPAIGN, 'offline-01-entered.json'), (module.E, module.PACKAGE)]
    assert value == module.verify_return(module.sha(module.canonical(writes[1][2])))
    assert writes[1][2]['history']['new_complete_R0_acceptance'] is False
    assert writes[1][2]['checker_sha256'] == tree[module.CHECKER]


@pytest.mark.parametrize('damage', ['new-worker', 'new-checker', 'new-protocol', 'new-head-old',
    'new-slot-bool', 'new-rss-bool', 'new-clock', 'new-history', 'new-budget', 'old-claim-buffer',
    'actual-actor', 'actual-exit', 'actual-stdout', 'policy-path', 'claim-slot-bool',
    'new-history-bool', 'entered-slot-bool'])
def test_new_readiness_refuses_mixed_or_fabricated_metadata(monkeypatch, tmp_path, damage):
    module = subject()
    policy, tree, report, actual, claim, entry, save = readiness_fixture(
        module, monkeypatch, tmp_path)
    if damage in ('new-worker', 'new-checker', 'new-protocol'):
        report[{'new-worker': 'worker_sha256', 'new-checker': 'checker_sha256',
                'new-protocol': 'authority_sha256'}[damage]] = '0'*64
    elif damage == 'new-head-old':
        report['source_main'] = claim['source_main'] = module.PREVIOUS_MAIN
    elif damage == 'new-slot-bool':
        report['slot'] = True
    elif damage == 'new-rss-bool':
        report['self_rss_bytes'] = True
    elif damage == 'new-clock':
        report['ended_ms'] += 100
    elif damage == 'new-history':
        report['history'] = deepcopy(report['history'])
        report['history']['new_complete_R0_acceptance'] = True
    elif damage == 'new-history-bool':
        report['history'] = deepcopy(report['history'])
        report['history']['old_verifier_entry_calls'] = False
    elif damage == 'new-budget':
        report['attempt_budget_sha256'] = '0'*64
    elif damage == 'old-claim-buffer':
        report['previous_claim_base64'] = module.base64.b64encode(b'{}\n').decode()
    elif damage == 'actual-actor':
        actual['author'] = '/root'
    elif damage == 'actual-exit':
        actual['responses'][0]['result']['exit_code'] = False
    elif damage == 'policy-path':
        policy['cycle_verification_paths']['package'] = '/unregistered/report.json'
    elif damage == 'claim-slot-bool':
        claim['slot'] = True
    elif damage == 'entered-slot-bool':
        entry['slot'] = True
        report['entered_sha256'] = module.sha(module.canonical(entry))
    save()
    if damage == 'actual-stdout':
        raw = module.parse(module.pair(module.E, module.ACTUAL))
        raw['responses'][0]['result']['output'] = '{}\n'
        original = module.pair
        monkeypatch.setattr(module, 'pair', lambda root, name, expected=None:
                            module.canonical(raw) if name == module.ACTUAL
                            else original(root, name, expected))
    with pytest.raises(ValueError):
        module.verified_readiness(policy, tree)


@pytest.mark.parametrize('kind', ['link', 'hardlink', 'fifo'])
def test_metadata_reader_refuses_nonregular_or_aliased_objects(tmp_path, kind):
    module = subject()
    original = tmp_path/'original.json'
    original.write_bytes(b'{}\n')
    bad = tmp_path/'bad.json'
    if kind == 'link':
        bad.symlink_to(original)
    elif kind == 'hardlink':
        os.link(original, bad)
    else:
        os.mkfifo(bad, 0o600)
    with pytest.raises((ValueError, OSError)):
        module._read(bad)


def test_paired_writer_is_exclusive_and_preserves_first_raw_bytes(tmp_path, monkeypatch):
    module = subject()
    root = tmp_path/'evidence'
    peer = root.with_name(root.name+'-backup')
    for folder in (root, peer):
        folder.mkdir(mode=0o700)
    monkeypatch.setattr(module, 'E', root)
    first = {'declared': 'public receipt'}
    pin = module._save(root, module.PACKAGE, first)
    assert pin == module.sha(module.canonical(first))
    assert (root/module.PACKAGE).read_bytes() == (peer/module.PACKAGE).read_bytes()
    assert (root/module.PACKAGE).stat().st_ino != (peer/module.PACKAGE).stat().st_ino
    with pytest.raises(FileExistsError):
        module._save(root, module.PACKAGE, {'replacement': True})
    assert (root/module.PACKAGE).read_bytes() == module.canonical(first)
    with pytest.raises(ValueError, match='namespace'):
        module._save(root, '../elsewhere.json', first)


@pytest.mark.parametrize('wrong', [False, True])
def test_actual_loader_registry_supplies_source_hash_without_module_self_claim(monkeypatch, wrong):
    module = subject()
    loader = ModuleType('full60_input_loader')
    loader.loaded_source_sha256 = {str(module.SOURCE_CHECKOUT/module.WORKER): 'a'*64}
    monkeypatch.setitem(module.sys.modules, 'full60_input_loader', loader)
    if wrong:
        module.MODULE_SOURCE_SHA256 = 'b'*64
        with pytest.raises(ValueError, match='compiled verifier'):
            module._executed_sha()
    else:
        assert module._executed_sha() == 'a'*64
