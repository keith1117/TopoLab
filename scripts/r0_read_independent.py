"""Verify retained single-file R0 observations without reopening their business URL.

The CLI derives publication pins from clean software bytes. Replay APIs receive
those trusted pins separately; a producer's publication fields are never authority.
Diagnostic self RSS excludes the timeout and preflight git processes. Formal Native
resource admission remains a separate, unchanged gate.
"""

import argparse
import base64
import hashlib
import json
import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path('/private/tmp/topolab-r0-read-20261122')
OLD_REPO = Path('/private/tmp/topolab-formal-input-20261122')
E = Path('/Users/keith1117/Documents/TopoLab-data/r0-read-acceptance-20261122')
B = E.with_name(E.name + '-backup')
SOURCE = '/Users/keith1117/Documents/TopoLab-data'
UNIT = 'b4-30-z-reflection-repair-v2/sentinel/reference/units/0011.json'
CASE_ID = 'tlcase-v1-c38b3eb15df4c6805bc187e068b1f160d1bd5af03173f2e7be29b8db5523c5c4'
IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.r0-read-20261122.v1'
BUDGET_SHA = '149fe42c5df8849c49d3cb39b62004a8b0d7d82bf3ce1c7bca131f24f9c0b666'
EXPECTED_SHA = 'b75b1942e547a027744bc08f5b70a001cfc309804d00f04f983bc9236e774802'
CERT_SHA = '56a7ef886ba8c634eb505004f0498d739c45cafa4bd63d925e424f92811da167'
CERT_ACTUAL_SHA = 'c1709f92c3ed9544b49ebe428714e50f2685b1ff95d2d02a340dcdd47b7204b5'
CERT_E = E.parent / 'metadata-input-acceptance-20261121'
CERTIFICATE = CERT_E / 'formal-metadata-certificate-a1.json'
CERT_ACTUAL = CERT_E / 'metadata-formal-a1/finalize-result-raw-actual-call.json'
PYTHON = ('/Library/Frameworks/Python.framework/Versions/3.12/Resources/'
          'Python.app/Contents/MacOS/Python')
PYTHON_SHA = '93d04da16de15e537a76fa1278accf982dd35ff1107e06460433315512eb381f'
BASELINE_SHA = 'b50ec93413981bd07420147a9901b0c8ccaa45373ee08a3671891c7dbaa2f6ab'
BASELINE_MAIN = '26dd6294e29e2488890c89eb79a818f8dcfed74a'
PROTOCOL = 'docs/planning/r0_read_input_contract.json'
POINTS = ('declared', 'before', 'after', 'closing')
PHYSICAL = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns')
POLICY = 'topolab.source-identity.prebound-sha256.v1'
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')
ACTUAL_SCHEMA = 'topolab.v2.m2-strict-source-binding.actual-call.v1'
START_MS, END_MS = 1795333814731, 1795420214731
SF_DATALESS, CAP, RSS_CAP = 0x40000000, 16 * 1024**2, 4 * 1024**3


def need(ok, message):
    if not ok:
        raise ValueError('R0_READ_STOP: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                       allow_nan=False) + '\n').encode('ascii')


def parse(raw):
    need(type(raw) is bytes and 0 < len(raw) <= CAP, 'bounded raw metadata required')

    def pairs(items):
        answer = {}
        for key, value in items:
            need(key not in answer, 'duplicate metadata key')
            answer[key] = value
        return answer

    def invalid(_word):
        raise ValueError('R0_READ_STOP: nonfinite metadata')

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def digest_word(value, count=64):
    return (isinstance(value, str) and len(value) == count
            and all(x in '0123456789abcdef' for x in value))


def literal_command(argv):
    return 'exec ' + shlex.join(['env', *(k + '=1' for k in THREADS), *argv])


def terminal(packet, argv, *, author='/root', cwd, window=(START_MS, END_MS), full=300):
    need(isinstance(packet, dict) and packet.get('schema') == ACTUAL_SCHEMA
         and packet.get('author') == author and packet.get('argv') == argv,
         'original actor/argv differs')
    request = packet.get('request', {})
    need(request.get('cmd') == literal_command(argv) and request.get('workdir') == cwd
         and 'prefix_rule' not in request, 'literal original request differs')
    rows = packet.get('responses')
    need(type(rows) is list and 1 <= len(rows) <= 65, 'bounded original rows required')
    prior, session = None, None
    for index, row in enumerate(rows):
        result, args = row.get('result', {}), row.get('arguments', {})
        need(integer(row.get('requested_ms')) and integer(row.get('returned_ms'))
             and row['requested_ms'] <= row['returned_ms']
             and (prior is None or prior <= row['requested_ms'])
             and isinstance(result.get('output'), str), 'original clocks/output missing')
        need(not any(s in result['output'] for s in (
            'Warning: truncated output', 'tokens truncated'))
             and (result.get('original_token_count') is None
                  or (integer(result['original_token_count'])
                      and integer(args.get('max_output_tokens', 10000), 1)
                      and result['original_token_count'] <= args.get('max_output_tokens', 10000))),
             'incomplete original output')
        if not index:
            need(row.get('tool') == 'exec_command' and args == request,
                 'original first request differs')
        else:
            need(row.get('tool') == 'write_stdin' and integer(args.get('session_id'), 1)
                 and args['session_id'] == session and args.get('chars', '') == ''
                 and integer(args.get('yield_time_ms', 5000), 5000)
                 and args.get('yield_time_ms', 5000) <= 30000, 'unowned original poll')
        if index < len(rows) - 1:
            need(integer(result.get('session_id'), 1) and result.get('exit_code') is None
                 and (session is None or session == result['session_id']), 'changed live session')
            session = result['session_id']
        else:
            need(type(result.get('exit_code')) is int and result['exit_code'] == 0
                 and result.get('session_id') is None, 'original terminal0 missing')
        prior = row['returned_ms']
    first = rows[0]['requested_ms']
    need(window[0] <= first <= prior <= window[1]
         and (full is None or prior - first + 10000 <= full * 1000),
         'original return outside fixed window/FULL')
    return first, prior, ''.join(x['result']['output'] for x in rows).encode('utf-8')


def _point(value, anchor):
    need(type(value) is dict and set(value) == set(PHYSICAL)
         and all(integer(value.get(k)) for k in PHYSICAL)
         and all(value[k] == anchor[k] for k in PHYSICAL[:-1]),
         'registered physical point differs')
    return value


def verify_observation(receipt_raw, actual_raw, claim_raw, *, expected_publication,
                       expected_registration):
    """Check one original read using separately derived source-publication pins."""
    receipt, packet, claim = parse(receipt_raw), parse(actual_raw), parse(claim_raw)
    pub = expected_publication
    need(type(pub) is dict and digest_word(pub.get('source_main'), 40)
         and all(digest_word(pub.get(k)) for k in ('authority_sha256', 'worker_sha256'))
         and pub.get('repo') in (str(REPO), str(OLD_REPO)), 'trusted software pins required')
    slot, purpose = receipt.get('slot'), receipt.get('purpose')
    need(integer(slot, 1) and slot <= 12 and purpose in ('diagnostic', 'candidate')
         and receipt.get('schema') == 'topolab.r0-read-observation.v1'
         and receipt.get('execution_identity') == IDENTITY and receipt.get('status') == 'COMPLETE'
         and receipt.get('error') is None and receipt.get('budget_sha256') == BUDGET_SHA
         and receipt.get('source_root') == SOURCE and receipt.get('relative_path') == UNIT
         and receipt.get('registration_sha256') == CERT_SHA
         and all(receipt.get(k) == pub[k] for k in pub if k != 'repo'),
         'complete fixed observation and publication required')
    worker = str(REPO / 'scripts/r0_read_observation.py')
    if purpose == 'diagnostic':
        worker = str(E / 'baseline-r0-observation.py')
        need(pub['repo'] == str(OLD_REPO) and pub['source_main'] == BASELINE_MAIN
             and pub['worker_sha256'] == BASELINE_SHA, 'fixed baseline software differs')
    else:
        need(pub['repo'] == str(REPO), 'candidate source checkout differs')
    argv = ['/usr/bin/timeout', '-k', '2', '290', PYTHON, '-I', worker,
            '--slot', str(slot), '--purpose', purpose]
    need(claim.get('schema') == 'topolab.r0-read-claim.v1' and claim.get('slot') == slot
         and type(claim['slot']) is int and claim.get('purpose') == purpose
         and claim.get('relative_path') == UNIT and claim.get('charge_FULL') == 300
         and type(claim['charge_FULL']) is int and claim.get('budget_sha256') == BUDGET_SHA
         and claim.get('actor') == '/root' and claim.get('argv') == argv
         and all(claim.get(k) == pub[k] for k in pub)
         and receipt.get('claim_sha256') == sha(claim_raw), 'original one-use claim differs')
    first, last, output = terminal(packet, argv, cwd=pub['repo'])
    need(integer(claim.get('claimed_ms')) and START_MS <= claim['claimed_ms'] <= first,
         'claim did not precede original observation')
    need(output == canonical(dict(schema='topolab.r0-read-return.v1', slot=slot,
         status='COMPLETE', receipt_sha256=sha(receipt_raw), own_future_return='NOT_CLAIMED')),
         'original receipt return differs')
    registration = expected_registration
    need(type(registration) is dict and set(registration) == {'byte_size', 'sha256', 'declared'}
         and registration.get('byte_size') == 490 and type(registration['byte_size']) is int
         and registration.get('sha256') == EXPECTED_SHA, 'certified registration required')
    anchor = registration['declared']
    _point(anchor, anchor)
    need(receipt.get('registration') == registration
         and type(receipt['registration']['byte_size']) is int, 'registration anchor differs')
    facts = receipt.get('reader_facts', {})
    ref = dict(path=UNIT, byte_size=490, sha256=EXPECTED_SHA)
    need(facts.get('schema') == 'topolab.v2.m2-input-read-failure.v1'
         and facts.get('execution_identity') == 'topolab.v2.p17-m2-local-input-version.v1'
         and facts.get('path') == UNIT and type(facts.get('attempt_ordinal')) is int
         and facts['attempt_ordinal'] == 1 and facts.get('stage') == 'canonical_json'
         and facts.get('identity_policy') == POLICY and facts.get('expected_sha256') == EXPECTED_SHA
         and facts.get('registered_preread_anchor') == anchor and facts.get('source') == ref
         and type(facts.get('returned_bytes')) is int and facts['returned_bytes'] == 490
         and facts.get('changed_fields') == [] and 'status' not in facts,
         'one complete registered Reader sequence required')
    points = {k: _point(facts.get(k), anchor) for k in POINTS}
    changes = {k: points[k]['st_mtime_ns'] - points['declared']['st_mtime_ns']
               for k in POINTS[1:]}
    need(facts.get('mtime_changes') == changes
         and all(type(x) is int for x in facts['mtime_changes'].values()),
         'original timestamp deltas differ')
    expected_row = dict(ref, **points, identity_policy=POLICY,
                        expected_sha256=EXPECTED_SHA, mtime_changes=changes)
    need(receipt.get('source_observations') == [expected_row],
         'exact same-buffer observation row differs')
    try:
        raw = base64.b64decode(receipt.get('raw_b64', ''), validate=True)
    except (TypeError, ValueError) as error:
        raise ValueError('R0_READ_STOP: invalid captured bytes') from error
    need(len(raw) == 490 and sha(raw) == EXPECTED_SHA, 'complete registered raw bytes differ')
    value = parse(raw)
    need(canonical(value) == raw and value.get('version') == 'topolab.b4.unit.v1'
         and value.get('unit') == CASE_ID and digest_word(value.get('context_sha256'))
         and digest_word(value.get('previous_sha256')) and isinstance(value.get('payload'), dict),
         'captured canonical unit naming differs')
    trace = receipt.get('open_identity_trace')
    need(type(trace) is list and len(trace) == 4
         and [x.get('stage') for x in trace] == list(POINTS)
         and all(integer(x.get('mono_ns')) and integer(x.get('flags'))
                 and integer(x.get('blocks')) for x in trace)
         and all(a['mono_ns'] <= b['mono_ns'] for a, b in zip(trace, trace[1:], strict=False)),
         'four original stat flags/blocks trace required')
    start, end, elapsed = (receipt.get(k) for k in (
        'read_start_ns', 'read_end_ns', 'read_elapsed_ns'))
    need(all(integer(x) for x in (start, end, elapsed))
         and first * 10**6 <= start <= end <= last * 10**6
         and elapsed <= (last - first) * 10**6
         and 0 <= trace[-1]['mono_ns'] - trace[0]['mono_ns'] <= elapsed,
         'original read clocks differ')
    runtime = receipt.get('runtime', {})
    need(runtime.get('python') == PYTHON and runtime.get('python_sha256') == PYTHON_SHA
         and runtime.get('orig_argv') == argv[4:] and type(runtime.get('isolated')) is int
         and runtime['isolated'] == 1 and runtime.get('cwd') == pub['repo']
         and runtime.get('platform') == 'darwin'
         and runtime.get('threads') == {k: '1' for k in THREADS}, 'actual locked runtime differs')
    rss = receipt.get('rss_self_bytes')
    need(integer(rss, 1) and rss <= RSS_CAP and receipt.get('helper_records') == [],
         'diagnostic RSS or unreviewed helper differs')
    return dict(slot=slot, purpose=purpose, **pub, original_T0_ms=first, original_T1_ms=last,
                returned_bytes=490, raw_sha256=sha(raw), receipt_sha256=sha(receipt_raw),
                actual_sha256=sha(actual_raw), claim_sha256=sha(claim_raw), trace=trace,
                registration_anchor_sha256=sha(canonical(registration)), known_FULL=300,
                rss_measured_bytes=rss, excluded_wrapper_and_preflight_git_RSS='UNKNOWN')


def verify_repeats(proofs):
    need(type(proofs) is list and 2 <= len(proofs) <= 12, 'two candidate observations required')
    need(len({p['slot'] for p in proofs}) == len(proofs)
         and all(p['purpose'] == 'candidate' for p in proofs), 'duplicate/noncandidate proof')
    first = proofs[0]
    for previous, proof in zip([None, *proofs[:-1]], proofs, strict=True):
        need(all(proof[k] == first[k] for k in (
            'source_main', 'authority_sha256', 'worker_sha256', 'repo', 'raw_sha256',
            'registration_anchor_sha256'))
             and (previous is None or (previous['slot'] < proof['slot']
                  and previous['original_T1_ms'] <= proof['original_T0_ms']))
             and all(not x['flags'] & SF_DATALESS for x in proof['trace'][2:]),
             'repeated release/order/materialization differs')
    need(all(not x['flags'] & SF_DATALESS for x in proofs[-1]['trace']),
         'last observation remains dataless')
    return dict(accepted_slots=[p['slot'] for p in proofs],
                observations_sha256=sha(canonical(proofs)),
                **{k: first[k] for k in ('source_main', 'authority_sha256', 'worker_sha256',
                   'registration_anchor_sha256')})


def registration_references():
    return dict(certificate=dict(path=str(CERTIFICATE), sha256=CERT_SHA),
                finalize_actual=dict(path=str(CERT_ACTUAL), sha256=CERT_ACTUAL_SHA))


def registration_anchor(certificate_raw, actual_raw):
    """Derive this anchor from exact, previously accepted formal certificate bytes."""
    need(type(certificate_raw) is bytes and type(actual_raw) is bytes
         and sha(certificate_raw) == CERT_SHA and sha(actual_raw) == CERT_ACTUAL_SHA,
         'previously accepted registration raw pins differ')
    envelope, actual = parse(certificate_raw), parse(actual_raw)
    cert = envelope['core_bundle']['certificate']
    rows = cert.get('source_observations')
    need(cert.get('scope') == 'FORMAL_STRICT_BINDING_REGISTRATION_ONLY'
         and cert.get('registered_context', {}).get('source_root') == SOURCE
         and type(rows) is list and len(rows) == 23
         and len({x['path'] for x in rows}) == 23, 'exact accepted 23-file registration required')
    match = [x for x in rows if x.get('path') == UNIT]
    need(len(match) == 1 and type(match[0].get('declared')) is dict
         and set(match[0]['declared']) == set(PHYSICAL)
         and all(match[0].get(k) == match[0]['declared'] for k in POINTS)
         and all(type(match[0][k][f]) is int for k in POINTS for f in PHYSICAL)
         and match[0].get('sha256') == EXPECTED_SHA
         and type(match[0].get('byte_size')) is int and match[0]['byte_size'] == 490,
         'registered certificate single-file anchor differs')
    # These immutable actual bytes were accepted under their own historical identity.
    # No embedded plan, original source or custody path is followed here.
    rows = actual.get('responses')
    need(actual.get('schema') == ACTUAL_SCHEMA and actual.get('author') == '/root'
         and type(rows) is list and rows
         and type(rows[-1].get('result', {}).get('exit_code')) is int
         and rows[-1]['result']['exit_code'] == 0
         and rows[-1]['result'].get('session_id') is None,
         'historical accepted registration actual terminal differs')
    return dict(byte_size=490, sha256=EXPECTED_SHA, declared=dict(match[0]['declared']))


def decode_buffer(value):
    need(isinstance(value, str) and 0 < len(value) <= (CAP + 2) // 3 * 4,
         'bounded original base64 required')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError('R0_READ_STOP: original buffer encoding differs') from error
    need(0 < len(raw) <= CAP, 'original decoded metadata cap')
    return raw


def verify_package(raw, expected_sha, *, expected_publication, certificate_raw,
                   registration_actual_raw):
    need(sha(raw) == expected_sha, 'verification package raw SHA differs')
    package = parse(raw)
    need(type(package) is dict and set(package) == {
        'schema', 'purpose', 'registration', 'publication', 'observations'}
         and package['schema'] == 'topolab.r0-read-verification-package.v1'
         and package['purpose'] == 'candidate'
         and package['registration'] == registration_references()
         and package['publication'] == expected_publication,
         'candidate package authority differs')
    anchor = registration_anchor(certificate_raw, registration_actual_raw)
    entries = package['observations']
    need(type(entries) is list and 2 <= len(entries) <= 12,
         'bounded candidate observations required')
    proofs = []
    for entry in entries:
        need(type(entry) is dict and set(entry) == {
            'slot', 'claim_raw_b64', 'receipt_raw_b64', 'actual_raw_b64'}
             and integer(entry['slot'], 1), 'exact original observation buffers required')
        proof = verify_observation(decode_buffer(entry['receipt_raw_b64']),
            decode_buffer(entry['actual_raw_b64']), decode_buffer(entry['claim_raw_b64']),
            expected_publication=expected_publication, expected_registration=anchor)
        need(entry['slot'] == proof['slot'], 'original slot label differs')
        proofs.append(proof)
    summary = verify_repeats(proofs)
    need(summary['registration_anchor_sha256'] == sha(canonical(anchor)),
         'candidate proof and certified anchor differ')
    return dict(status='PASS_R0_REPEAT_CANDIDATE_VERIFICATION', package_sha256=expected_sha,
                budget_sha256=BUDGET_SHA, **summary, source_reads=0, target_reads=0,
                own_future_return='NOT_CLAIMED')


def read_metadata(path):
    """Bound metadata-only reads, including no-follow ancestors and closing identity."""
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'literal metadata path required')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and before.st_uid == os.getuid() and 0 < before.st_size <= CAP,
                 'owned bounded regular metadata required')
            raw = stream.read(before.st_size + 1)
            after = os.fstat(stream.fileno())
        closing = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        keys = (*PHYSICAL, 'st_mode', 'st_uid', 'st_nlink', 'st_ctime_ns')
        need(len(raw) == before.st_size and all(
            getattr(before, k) == getattr(after, k) == getattr(closing, k) for k in keys),
             'metadata stable closing identity differs')
        return raw, (before.st_dev, before.st_ino)
    finally:
        os.close(directory)


def read_pair(path, peer):
    first, a = read_metadata(path)
    second, b = read_metadata(peer)
    need(first == second and a != b, 'independent metadata pair differs')
    need(all(stat.S_IMODE(Path(p).lstat().st_mode) == 0o600 for p in (path, peer)),
         'private proof metadata mode differs')
    return first


def _registration_pair():
    peer = CERT_E.with_name(CERT_E.name + '-backup')
    return (read_pair(CERTIFICATE, peer / CERTIFICATE.relative_to(CERT_E)),
            read_pair(CERT_ACTUAL, peer / CERT_ACTUAL.relative_to(CERT_E)))


def verification_paths():
    return dict(package=str(E / 'r0-read-verification-a1.json'),
                actual=str(E / 'r0-read-verification-actual-a1.json'))


def verified_readiness(policy, tree):
    """Replay the I-owned actual verification before preparation or activation."""
    paths = verification_paths()
    need(policy.get('execution_identity') == IDENTITY
         and policy.get('r0_read_verification_paths') == paths
         and policy.get('new_input_budget') == dict(
             path=str(E / 'owner-budget-registration.json'), sha256=BUDGET_SHA),
         'new R0 proof policy differs')
    package_raw = read_pair(paths['package'], B / Path(paths['package']).name)
    actual_raw = read_pair(paths['actual'], B / Path(paths['actual']).name)
    package, actual = parse(package_raw), parse(actual_raw)
    pub = dict(source_main=package['publication']['source_main'], repo=str(REPO),
               authority_sha256=tree[PROTOCOL],
               worker_sha256=tree['scripts/r0_read_observation.py'])
    certificate, registration_actual = _registration_pair()
    summary = verify_package(package_raw, sha(package_raw), expected_publication=pub,
                             certificate_raw=certificate,
                             registration_actual_raw=registration_actual)
    argv = [PYTHON, '-I', str(REPO / 'scripts/r0_read_independent.py'), 'verify',
            '--package', paths['package'], '--package-sha256', sha(package_raw)]
    started, ended, output = terminal(actual, argv, author='/root/full60_independent',
                                      cwd=str(REPO), full=None)
    need(output == canonical(summary), 'original independent verification stdout differs')
    observations = package['observations']
    for entry in observations:
        original = parse(decode_buffer(entry['actual_raw_b64']))['responses']
        need(original[-1]['returned_ms'] <= started,
             'independent verification preceded original observation return')
    return dict(package=dict(path=paths['package'], sha256=sha(package_raw)),
                actual=dict(path=paths['actual'], sha256=sha(actual_raw)),
                **{k: summary[k] for k in ('source_main', 'authority_sha256', 'worker_sha256',
                   'accepted_slots', 'observations_sha256', 'registration_anchor_sha256')},
                verified_returned_ms=ended)


def current_publication():
    """Derive software pins; the official fresh protected-main gate remains mandatory."""
    need(Path.cwd() == REPO, 'literal software checkout required')

    def git(*words):
        return subprocess.run(['git', *words], cwd=REPO, check=True,
                              capture_output=True, timeout=30).stdout

    need(not git('status', '--porcelain=v1', '-uall').strip(), 'clean published software required')
    head = git('rev-parse', 'HEAD').decode().strip()
    pins = {}
    for key, path in (('authority_sha256', PROTOCOL),
                      ('worker_sha256', 'scripts/r0_read_observation.py')):
        raw, _identity = read_metadata(REPO / path)
        need(raw == git('show', head + ':' + path), 'executed and committed software differ')
        pins[key] = sha(raw)
    return dict(source_main=head, repo=str(REPO), **pins)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['verify'])
    parser.add_argument('--package', required=True)
    parser.add_argument('--package-sha256', required=True)
    args = parser.parse_args()
    need(sys.flags.isolated == 1 and args.package == verification_paths()['package']
         and digest_word(args.package_sha256),
         'fixed package path/SHA required')
    raw = read_pair(args.package, B / Path(args.package).name)
    certificate, actual = _registration_pair()
    summary = verify_package(raw, args.package_sha256, expected_publication=current_publication(),
                             certificate_raw=certificate, registration_actual_raw=actual)
    print(canonical(summary).decode(), end='')


MODULE_SOURCE_SHA256 = sha(Path(__file__).read_bytes())

if __name__ == '__main__':
    main()
