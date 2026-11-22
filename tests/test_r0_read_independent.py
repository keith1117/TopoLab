"""Independent receipt checks use synthetic buffers, never a business source URL."""

import base64
import importlib.util
import os
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]


def subject():
    path = REPO / 'scripts/r0_read_independent.py'
    spec = importlib.util.spec_from_file_location('r0_receipt_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def anchor_for(module):
    return dict(byte_size=490, sha256=module.EXPECTED_SHA,
                declared=dict(st_dev=7, st_ino=11, st_size=490, st_mtime_ns=12345678))


def fixture(module, monkeypatch, *, slot=1, purpose='candidate'):
    value = dict(version='topolab.b4.unit.v1', context_sha256='a' * 64,
                 unit=module.CASE_ID, previous_sha256='b' * 64,
                 payload=dict(sha256='c' * 64, byte_size=123), fixture_padding='')
    value['fixture_padding'] = 'x' * (490 - len(module.canonical(value)))
    raw = module.canonical(value)
    assert len(raw) == 490
    monkeypatch.setattr(module, 'EXPECTED_SHA', module.sha(raw))
    point = anchor_for(module)['declared']
    registration = dict(byte_size=490, sha256=module.EXPECTED_SHA, declared=point)
    ref = dict(path=module.UNIT, byte_size=490, sha256=module.EXPECTED_SHA)
    changes = dict(before=0, after=0, closing=0)
    facts = dict(schema='topolab.v2.m2-input-read-failure.v1',
                 execution_identity='topolab.v2.p17-m2-local-input-version.v1',
                 attempt_ordinal=1, path=module.UNIT, stage='canonical_json',
                 declared=point, before=point, after=point, closing=point,
                 returned_bytes=490, changed_fields=[], identity_policy=module.POLICY,
                 expected_sha256=module.EXPECTED_SHA, mtime_changes=changes,
                 registered_preread_anchor=point, source=ref)
    row = dict(ref, **{k: point for k in module.POINTS}, identity_policy=module.POLICY,
               expected_sha256=module.EXPECTED_SHA, mtime_changes=changes)
    publication = dict(source_main='d' * 40, authority_sha256='e' * 64,
                       worker_sha256='f' * 64, repo=str(module.REPO))
    worker = str(module.REPO / 'scripts/r0_read_observation.py')
    before = module.START_MS + slot * 10000
    argv = ['/usr/bin/timeout', '-k', '2', '290', module.PYTHON, '-I', worker,
            '--slot', str(slot), '--purpose', purpose]
    claim = dict(schema='topolab.r0-read-claim.v1', slot=slot, purpose=purpose,
                 **publication, budget_sha256=module.BUDGET_SHA, relative_path=module.UNIT,
                 charge_FULL=300, actor='/root', claimed_ms=before - 1, argv=argv)
    claim_raw = module.canonical(claim)
    receipt = dict(schema='topolab.r0-read-observation.v1', slot=slot, purpose=purpose,
                   execution_identity=module.IDENTITY, **publication,
                   budget_sha256=module.BUDGET_SHA, source_root=module.SOURCE,
                   relative_path=module.UNIT, registration=registration,
                   registration_sha256=module.CERT_SHA, reader_facts=facts,
                   source_observations=[row], raw_b64=base64.b64encode(raw).decode(),
                   open_identity_trace=[dict(stage=stage, mono_ns=1000000 + n * 100000,
                                             flags=64, blocks=8)
                                        for n, stage in enumerate(module.POINTS)],
                   read_start_ns=before * 10**6 + 10**6,
                   read_end_ns=before * 10**6 + 2 * 10**6,
                   read_elapsed_ns=10**6, status='COMPLETE', error=None,
                   helper_records=[], claim_sha256=module.sha(claim_raw),
                   rss_self_bytes=140000000,
                   runtime=dict(python=module.PYTHON, python_sha256=module.PYTHON_SHA,
                                orig_argv=argv[4:], isolated=1, cwd=str(module.REPO),
                                platform='darwin', threads={k: '1' for k in module.THREADS},
                                lock_sha256='a' * 64, os_release='declared-fixture'))
    return publication, claim, receipt


def wires(module, publication, claim, receipt, *, damage=None):
    claim_raw, receipt_raw = module.canonical(claim), module.canonical(receipt)
    before = module.START_MS + claim['slot'] * 10000
    request = dict(cmd=module.literal_command(claim['argv']), workdir=publication['repo'],
                   login=False, yield_time_ms=1000, max_output_tokens=6000)
    summary = dict(schema='topolab.r0-read-return.v1', slot=claim['slot'],
                   status=receipt['status'], receipt_sha256=module.sha(receipt_raw),
                   own_future_return='NOT_CLAIMED')
    packet = dict(schema=module.ACTUAL_SCHEMA, author='/root', argv=claim['argv'],
                  request=request, responses=[dict(tool='exec_command', arguments=request,
                      requested_ms=before, returned_ms=before + 5,
                      result=dict(exit_code=0, output=module.canonical(summary).decode()))])
    if damage:
        damage(packet)
    return claim_raw, receipt_raw, module.canonical(packet)


def test_complete_single_registered_read_accepts_exact_raw_observations(monkeypatch):
    module = subject()
    publication, claim, receipt = fixture(module, monkeypatch)
    c, r, a = wires(module, publication, claim, receipt)
    proof = module.verify_observation(r, a, c, expected_publication=publication,
                                      expected_registration=anchor_for(module))
    assert proof['slot'] == 1 and proof['known_FULL'] == 300
    assert proof['returned_bytes'] == 490 and proof['rss_measured_bytes'] == 140000000
    assert proof['raw_sha256'] == module.EXPECTED_SHA


@pytest.mark.parametrize('damage', [
    'STOP', 'after', 'closing', 'short', 'raw-sha', 'source', 'anchor', 'float-stat',
    'bool-size', 'observation', 'extra-row', 'flags-order', 'flags-type', 'mtime-delta',
    'source-main', 'worker', 'claim-sha', 'late-claim', 'read-clock', 'rss', 'helper',
    'partial-bytecount', 'stage'])
def test_incomplete_or_mixed_receipt_cannot_establish_single_read(monkeypatch, damage):
    module = subject()
    pub, claim, receipt = fixture(module, monkeypatch)
    if damage == 'STOP':
        receipt.update(status='STOP', error=dict(type='TimeoutError', reason='Errno60'))
    elif damage in ('after', 'closing'):
        receipt['reader_facts'][damage] = None
    elif damage == 'short':
        receipt['raw_b64'] = base64.b64encode(b'short').decode()
    elif damage == 'raw-sha':
        receipt['raw_b64'] = base64.b64encode(b'x' * 490).decode()
    elif damage == 'source':
        receipt['relative_path'] = 'second-source.json'
    elif damage == 'anchor':
        receipt['registration']['declared'] = dict(anchor_for(module)['declared'], st_ino=999)
    elif damage == 'float-stat':
        receipt['reader_facts']['after'] = dict(anchor_for(module)['declared'], st_mtime_ns=1.0)
    elif damage == 'bool-size':
        receipt['reader_facts']['returned_bytes'] = True
    elif damage == 'observation':
        receipt['source_observations'][0] = dict(receipt['source_observations'][0], sha256='0'*64)
    elif damage == 'extra-row':
        receipt['source_observations'].append(deepcopy(receipt['source_observations'][0]))
    elif damage == 'flags-order':
        receipt['open_identity_trace'].reverse()
    elif damage == 'flags-type':
        receipt['open_identity_trace'][0]['flags'] = False
    elif damage == 'mtime-delta':
        receipt['reader_facts']['mtime_changes']['after'] = 3
    elif damage == 'source-main':
        receipt['source_main'] = '0' * 40
    elif damage == 'worker':
        receipt['worker_sha256'] = '0' * 64
    elif damage == 'claim-sha':
        receipt['claim_sha256'] = '0' * 64
    elif damage == 'late-claim':
        claim['claimed_ms'] += 100
        receipt['claim_sha256'] = module.sha(module.canonical(claim))
    elif damage == 'read-clock':
        receipt['read_end_ns'] += 300 * 10**9
    elif damage == 'rss':
        receipt['rss_self_bytes'] = 4 * 1024**3 + 1
    elif damage == 'helper':
        receipt['helper_records'] = [{'exit_code': 0, 'rss_bytes': 1}]
    elif damage == 'partial-bytecount':
        receipt['reader_facts']['returned_bytes'] = None
    elif damage == 'stage':
        receipt['reader_facts']['stage'] = 'bounded_read'
    c, r, a = wires(module, pub, claim, receipt)
    with pytest.raises(ValueError):
        module.verify_observation(r, a, c, expected_publication=pub,
                                  expected_registration=anchor_for(module))


@pytest.mark.parametrize('damage', ['exit-bool', 'live', 'late', 'truncated', 'stdout', 'cmd'])
def test_original_external_return_is_a_required_separate_fact(monkeypatch, damage):
    module = subject()
    pub, claim, receipt = fixture(module, monkeypatch)

    def corrupt(packet):
        row = packet['responses'][0]
        if damage == 'exit-bool':
            row['result']['exit_code'] = False
        elif damage == 'live':
            row['result'].update(exit_code=None, session_id=100)
        elif damage == 'late':
            row['returned_ms'] += 291000
        elif damage == 'truncated':
            row['result']['output'] = 'Warning: truncated output\n'
        elif damage == 'stdout':
            row['result']['output'] = '{}\n'
        else:
            packet['request']['cmd'] = 'echo fabricated'

    c, r, a = wires(module, pub, claim, receipt, damage=corrupt)
    with pytest.raises(ValueError):
        module.verify_observation(r, a, c, expected_publication=pub,
                                  expected_registration=anchor_for(module))


def test_repeat_gate_requires_two_distinct_candidate_slots_and_last_fully_materialized(monkeypatch):
    module = subject()
    proofs = []
    for slot in (3, 4):
        pub, claim, receipt = fixture(module, monkeypatch, slot=slot)
        if slot == 3:
            for trace in receipt['open_identity_trace'][:2]:
                trace['flags'] |= module.SF_DATALESS
                trace['blocks'] = 0
        c, r, a = wires(module, pub, claim, receipt)
        proofs.append(module.verify_observation(r, a, c, expected_publication=pub,
                                                expected_registration=anchor_for(module)))
    assert module.verify_repeats(proofs)['accepted_slots'] == [3, 4]
    for bad in ([proofs[0]], [proofs[0], proofs[0]], list(reversed(proofs))):
        with pytest.raises(ValueError):
            module.verify_repeats(bad)
    last = deepcopy(proofs[1])
    last['trace'][0]['flags'] |= module.SF_DATALESS
    with pytest.raises(ValueError):
        module.verify_repeats([proofs[0], last])


def test_metadata_parser_refuses_duplicate_keys_and_nonfinite_words():
    module = subject()
    for raw in (b'{"a":1,"a":2}\n', b'{"a":NaN}\n'):
        with pytest.raises(ValueError):
            module.parse(raw)


def package_fixture(module, monkeypatch):
    fixture(module, monkeypatch)
    anchor = anchor_for(module)
    row = dict(path=module.UNIT, byte_size=490, sha256=module.EXPECTED_SHA,
               **{key: anchor['declared'] for key in module.POINTS})
    cert = dict(core_bundle=dict(certificate=dict(
        scope='FORMAL_STRICT_BINDING_REGISTRATION_ONLY', registered_context=dict(
            source_root=module.SOURCE), source_observations=[row, *[
                dict(row, path=f'declared-fixture-{n}') for n in range(22)]])))
    cert_raw = module.canonical(cert)
    old_actual = module.canonical(dict(schema=module.ACTUAL_SCHEMA, author='/root',
        responses=[dict(result=dict(exit_code=0, session_id=None))]))
    monkeypatch.setattr(module, 'CERT_SHA', module.sha(cert_raw))
    monkeypatch.setattr(module, 'CERT_ACTUAL_SHA', module.sha(old_actual))
    entries = []
    for slot in (3, 4):
        pub, claim, receipt = fixture(module, monkeypatch, slot=slot)
        c, r, a = wires(module, pub, claim, receipt)
        entries.append(dict(slot=slot, **{name: base64.b64encode(raw).decode() for name, raw in (
            ('claim_raw_b64', c), ('receipt_raw_b64', r), ('actual_raw_b64', a))}))
    package = dict(schema='topolab.r0-read-verification-package.v1', purpose='candidate',
                   registration=module.registration_references(), publication=pub,
                   observations=entries)
    return package, pub, cert_raw, old_actual


def test_package_derives_anchor_from_exact_certificate_and_retains_original_buffers(monkeypatch):
    module = subject()
    package, pub, certificate, actual = package_fixture(module, monkeypatch)
    raw = module.canonical(package)
    summary = module.verify_package(raw, module.sha(raw), expected_publication=pub,
        certificate_raw=certificate, registration_actual_raw=actual)
    assert summary['accepted_slots'] == [3, 4]
    assert summary['status'] == 'PASS_R0_REPEAT_CANDIDATE_VERIFICATION'
    assert summary['source_reads'] == summary['target_reads'] == 0
    assert module.registration_anchor(certificate, actual) == anchor_for(module)


@pytest.mark.parametrize('damage', ['certificate', 'registration-actual', 'pub', 'duplicate',
    'slot-bool', 'slot-label', 'extra-buffer', 'unknown-pointer', 'diagnostic', 'empty'])
def test_package_cannot_promote_unbound_or_self_asserted_receipts(monkeypatch, damage):
    module = subject()
    package, pub, cert, actual = package_fixture(module, monkeypatch)
    if damage == 'certificate':
        cert += b' '
    elif damage == 'registration-actual':
        actual += b' '
    elif damage == 'pub':
        package['publication']['source_main'] = '0' * 40
        pub = dict(pub, source_main='d' * 40)
    elif damage == 'duplicate':
        package['observations'][1] = deepcopy(package['observations'][0])
    elif damage == 'slot-bool':
        package['observations'][0]['slot'] = True
    elif damage == 'slot-label':
        package['observations'][0]['slot'] = 1
    elif damage == 'extra-buffer':
        package['observations'][0]['ignored_raw_b64'] = 'e30K'
    elif damage == 'unknown-pointer':
        package['registration']['certificate']['path'] = '/unapproved-certificate.json'
    elif damage == 'diagnostic':
        package['purpose'] = 'diagnostic'
    else:
        package['observations'] = []
    raw = module.canonical(package)
    with pytest.raises(ValueError):
        module.verify_package(raw, module.sha(raw), expected_publication=pub,
            certificate_raw=cert, registration_actual_raw=actual)


def readiness_fixture(module, monkeypatch):
    package, pub, cert, old_actual = package_fixture(module, monkeypatch)
    raw = module.canonical(package)
    paths = module.verification_paths()
    argv = [module.PYTHON, '-I', str(module.REPO / 'scripts/r0_read_independent.py'), 'verify',
            '--package', paths['package'], '--package-sha256', module.sha(raw)]
    summary = module.verify_package(raw, module.sha(raw), expected_publication=pub,
        certificate_raw=cert, registration_actual_raw=old_actual)
    request = dict(cmd=module.literal_command(argv), workdir=str(module.REPO))
    packet = dict(schema=module.ACTUAL_SCHEMA, author='/root/full60_independent', argv=argv,
                  request=request, responses=[dict(tool='exec_command', arguments=request,
                    requested_ms=module.START_MS+100000, returned_ms=module.START_MS+101000,
                    result=dict(exit_code=0, output=module.canonical(summary).decode()))])
    def paired(path, peer):
        assert Path(path).name == Path(peer).name and Path(peer).parent == module.B
        return raw if path == paths['package'] else module.canonical(packet)
    monkeypatch.setattr(module, 'read_pair', paired)
    monkeypatch.setattr(module, '_registration_pair', lambda: (cert, old_actual))
    policy = dict(execution_identity=module.IDENTITY, r0_read_verification_paths=paths,
                  new_input_budget=dict(path=str(module.E/'owner-budget-registration.json'),
                                        sha256=module.BUDGET_SHA))
    tree = {module.PROTOCOL: pub['authority_sha256'],
            'scripts/r0_read_observation.py': pub['worker_sha256']}
    return policy, tree, packet


def test_readiness_requires_original_independent_terminal_before_formal_admission(monkeypatch):
    module = subject()
    policy, tree, packet = readiness_fixture(module, monkeypatch)
    proof = module.verified_readiness(policy, tree)
    assert proof['accepted_slots'] == [3, 4]
    assert proof['verified_returned_ms'] == packet['responses'][-1]['returned_ms']
    assert proof['actual']['path'] == module.verification_paths()['actual']


@pytest.mark.parametrize('damage', ['stdout', 'actor', 'exit', 'early', 'tree', 'policy'])
def test_readiness_refuses_future_self_verified_or_wrong_source_proof(monkeypatch, damage):
    module = subject()
    policy, tree, packet = readiness_fixture(module, monkeypatch)
    if damage == 'stdout':
        packet['responses'][0]['result']['output'] = '{}\n'
    elif damage == 'actor':
        packet['author'] = '/root'
    elif damage == 'exit':
        packet['responses'][0]['result']['exit_code'] = False
    elif damage == 'early':
        packet['responses'][0]['requested_ms'] = module.START_MS + 1
    elif damage == 'tree':
        tree['scripts/r0_read_observation.py'] = '0' * 64
    else:
        policy['new_input_budget']['sha256'] = '0' * 64
    with pytest.raises(ValueError):
        module.verified_readiness(policy, tree)


def test_metadata_pairs_require_original_owned_ordinary_bytes(tmp_path):
    module = subject()
    a, b = tmp_path/'primary.json', tmp_path/'backup.json'
    for p in (a, b):
        p.write_bytes(b'{"synthetic":true}\n')
        p.chmod(0o600)
    assert module.read_pair(a, b) == a.read_bytes()
    b.chmod(0o644)
    with pytest.raises(ValueError, match='mode'):
        module.read_pair(a, b)
    b.unlink()
    os.link(a, b)
    with pytest.raises(ValueError, match='owned|pair'):
        module.read_pair(a, b)


def test_metadata_reader_refuses_symlink_fifo_and_over_cap_without_content_read(tmp_path):
    module = subject()
    a = tmp_path/'regular.json'
    a.write_bytes(b'{}\n')
    symlink = tmp_path/'link.json'
    symlink.symlink_to(a)
    with pytest.raises(OSError):
        module.read_metadata(symlink)
    fifo = tmp_path/'not-a-regular-file'
    os.mkfifo(fifo)
    with pytest.raises(ValueError, match='regular'):
        module.read_metadata(fifo)
    with a.open('wb') as stream:
        stream.truncate(module.CAP+1)
    with pytest.raises(ValueError, match='bounded'):
        module.read_metadata(a)


def test_cli_derives_software_pins_from_committed_and_current_bytes(tmp_path, monkeypatch):
    module = subject()
    monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.chdir(tmp_path)
    paths = {module.PROTOCOL: b'{"synthetic":"authority"}\n',
             'scripts/r0_read_observation.py': b'# synthetic worker\n'}
    for name, raw in paths.items():
        p = tmp_path/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)

    def git(argv, **kwargs):
        assert kwargs['capture_output'] and kwargs['check'] and kwargs['timeout'] == 30
        if argv[1] == 'status':
            return SimpleNamespace(stdout=b'')
        if argv[1] == 'rev-parse':
            return SimpleNamespace(stdout=('a'*40+'\n').encode())
        return SimpleNamespace(stdout=paths[argv[2].split(':',1)[1]])

    monkeypatch.setattr(module.subprocess, 'run', git)
    expected = module.current_publication()
    assert expected['source_main'] == 'a'*40
    assert expected['worker_sha256'] == module.sha(paths['scripts/r0_read_observation.py'])
    candidate = tmp_path/'scripts/r0_read_observation.py'
    candidate.write_bytes(b'# changed despite fake clean status\n')
    with pytest.raises(ValueError, match='committed'):
        module.current_publication()
