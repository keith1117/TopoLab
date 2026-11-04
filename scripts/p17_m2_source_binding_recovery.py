"""Metadata-only recovery of a closed, successful strict23 source core.

New software/native return evidence is separate from the captured source policy.
No source path in a captured buffer is opened by this module.
"""

import argparse
import json
import os
import re
import sys
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = 'docs/planning/p17_m2_source_binding_certificate_recovery_v4_protocol.json'
AUTHORITY = REPO / PROTOCOL_PATH
IDENTITY = 'topolab.v2.p17-binding-certificate-recovery.20261104.v4'
SCOPE = 'STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY'
RECOVERY_SCOPE = SCOPE
ROLE = 'binding-certificate-auditor'
PLAN_SCHEMA = 'topolab.v2.m2-strict-source-binding.metadata-plan.v1'
ENVELOPE_SCHEMA = 'topolab.v2.m2-strict-source-binding.recovered-result.v1'
FUTURE = 'NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION'


def load(name):
    import importlib.util
    path = REPO / 'scripts' / (name + '.py')
    old = sys.modules.get(name)
    if old is not None and Path(old.__file__).resolve() == path:
        return old
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError('RECOVERY: published helper unavailable')
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def need(condition, reason):
    if not condition:
        raise ValueError('RECOVERY: ' + reason)


def canonical(value):
    return load('p17_m2_source_binding').canonical(value)


def sha(raw):
    return load('p17_m2_source_binding').sha(raw)


def authority():
    value = json.loads(AUTHORITY.read_bytes())
    need(value['execution_identity'] == IDENTITY and value['scope'] == SCOPE,
         'new recovery policy identity differs')
    return value


def replay_core(bundle, kind):
    """Re-audit captured complete five-role evidence without source-path IO."""
    need(kind in ('public', 'formal'), 'literal captured core kind required')
    pin = authority()['captured_cores'][kind]
    need(sha(canonical(bundle)) == pin['sha256']
         and bundle['plan']['context'] == pin['context']
         and str(Path(bundle['plan']['root']) / 'certificate-bundle.json') == pin['path'],
         'captured successful core/context pin differs')
    return load('p17_m2_source_binding').replay_bundle(bundle)


def source_freeze():
    frozen = load('p17_m2_source_binding').source_freeze(2, window2=True)
    frozen['scripts/p17_m2_source_binding_recovery.py'] = sha(Path(__file__).read_bytes())
    frozen[PROTOCOL_PATH] = sha(AUTHORITY.read_bytes())
    for name in ('scripts/p17_m2_source_acquisition_control.py',
                 'scripts/p17_m2_source_acquisition_independent.py',
                 'scripts/p17_m2_registered_input.py',
                 'docs/planning/p17_m2_registered_input_v2_protocol.json',
                 'scripts/p17_m2_scientific_orchestration.py'):
        frozen[name] = sha((REPO / name).read_bytes())
    return frozen


def read_ref(reference, maximum=32 * 1024**2):
    need(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}
         and isinstance(reference['sha256'], str)
         and re.fullmatch('[0-9a-f]{64}', reference['sha256']), 'literal metadata pin required')
    return load('p17_m2_source_binding').read_metadata(
        Path(reference['path']), maximum, expected=reference['sha256'])[0]



def capture_ref(reference, maximum=32 * 1024**2):
    value, raw = load('p17_m2_source_binding').read_metadata(
        Path(reference['path']), maximum, expected=reference['sha256'])
    return {'reference': deepcopy(reference), 'raw': raw.decode('utf-8'), 'value': value}


def captured_value(capture, value_key='value'):
    need(isinstance(capture, dict) and isinstance(capture.get('raw'), str)
         and isinstance(capture.get('reference'), dict), 'captured raw metadata required')
    reference = capture['reference']
    need(set(reference) == {'path', 'sha256'}
         and isinstance(reference['sha256'], str)
         and re.fullmatch('[0-9a-f]{64}', reference['sha256'])
         and sha(capture['raw'].encode('utf-8')) == reference['sha256'],
         'captured reference/raw SHA differs')
    value = json.loads(capture['raw'])
    need(value == capture.get(value_key), 'captured raw/report buffer differs')
    return value


def budget_readiness():
    policy = authority()
    captures = {key: capture_ref(policy[key]) for key in (
        'budget', 'budget_review', 'software_activation', 'registration_actual',
        'prior_failed_metadata_closure', 'prior_failed_metadata_closure_actual')}
    _captured_budget(captures)
    need(time.time_ns() <= policy['limits']['global_deadline_ms'] * 10**6,
         'finite recovery global deadline unavailable')
    return captures


def _captured_budget(captures):
    """Bind the new V22 authority to original registration and failed-old closure."""
    policy = authority()
    keys = ('budget', 'budget_review', 'software_activation', 'registration_actual',
            'prior_failed_metadata_closure', 'prior_failed_metadata_closure_actual')
    need(isinstance(captures, dict) and set(captures) == set(keys),
         'complete captured V22 budget evidence required')
    values = {}
    for key in keys:
        need(captures[key].get('reference') == policy[key], 'captured budget reference differs')
        values[key] = captured_value(captures[key])
    budget, activation = values['budget'], values['software_activation']
    need(budget.get('schema') == 'topolab.owner.NEW-unstarted-input-closure-coordination-repair.v22'
         and budget.get('NEW_each_seconds') == {
             'software_preparation': 7200, 'publication_only': 7200,
             'formal_metadata_and_result': 1200}
         and budget.get('NEW_each_nested_dispatches') == {
             'software': 192, 'publication': 128, 'formal_metadata': 64, 'total': 384}
         and budget.get('source_registration_new_original_reads') == 0
         and budget.get('source_registration_new_Foundation_helpers') == 0
         and budget.get('coordination_seconds_max_UNCHANGED') == 240
         and budget.get('ROOT_I_original_hard_deadline_ms_UNCHANGED')
             == policy['limits']['global_deadline_ms'],
         'new finite V22 budget or unchanged scientific/resource boundary differs')
    review = values['budget_review']
    need(review.get('author') == policy['actors']['independent']
         and str(review.get('status', '')).startswith('PASS_'),
         'independent V22 budget review differs')
    registration = values['registration_actual']
    event = registration.get('event', {})
    result = event.get('result', {})
    need(event.get('tool') == 'exec_command'
         and type(event.get('requested_ms')) is int
         and event['requested_ms'] <= event.get('returned_ms', -1)
         and result.get('exit_code') == 0 and result.get('session_id') is None
         and result.get('output') == str(len(captures['budget']['raw'].encode('utf-8')))
         + ' ' + policy['budget']['sha256'] + chr(10)
         and registration.get('grant_sha256') == policy['budget']['sha256']
         and registration.get('activation_starts_at') == event['returned_ms'],
         'original V22 registration return differs')
    need(activation.get('execution_identity') == IDENTITY
         and activation.get('budget_reference') == policy['budget']
         and activation.get('started_ms') == event['returned_ms']
         == policy['limits']['software_start_ms']
         and activation.get('deadline_ms') == event['returned_ms'] + 7200000
         == policy['limits']['software_deadline_ms']
         and activation.get('global_deadline_ms') == policy['limits']['global_deadline_ms'],
         'new software activation must follow its original registration return')
    closure = values['prior_failed_metadata_closure']
    need(closure.get('status') == 'CLOSED_FAILED_PUBLIC_CERTIFICATE_NOT_PREPARATION_COMPLETE',
         'old failed input/public/closed allowances must never become preparation PASS')
    actual = values['prior_failed_metadata_closure_actual']
    need(budget.get('old_failed_closing_actual') == actual
         and activation.get('old_V16_V20_closing_actual') == actual
         and activation.get('old_closing_is_FAILED_never_PASS') is True,
         'new V22 authority must bind the complete actual failed-old return')
    _, ended = exact_actual(actual, actual['argv'], policy['actors']['producer'],
                            cwd=policy['prior_failed_metadata_closure_cwd'])
    output = ''.join(row['result']['output'] for row in actual['responses'])
    summary = json.loads(output)
    need(summary.get('status') == closure['status']
         and summary.get('sha256') == policy['prior_failed_metadata_closure']['sha256']
         and summary.get('paths', [None])[0] == policy['prior_failed_metadata_closure']['path']
         and summary.get('input_accepted') is False and summary.get('P17') == 'UNREPAIRED'
         and output.encode('utf-8') == canonical(summary)
         and ended < activation['started_ms'],
         'failed-only original closure stdout/chronology differs')
    return values


def review_readiness(standards_sha, spec_sha):
    policy, reports = authority(), {}
    for axis, expected in [('standards', standards_sha), ('spec', spec_sha)]:
        need(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected),
             'fresh review SHA required')
        reference = {'path': policy['review_paths'][axis], 'sha256': expected}
        captured = capture_ref(reference)
        report = captured['value']
        need(report.get('status') == 'PASS' and report.get('open_findings') == []
             and report.get('author') == policy['review_authors'][axis]
             and report.get('execution_identity') == IDENTITY
             and report.get('reviewed_source_tree') == source_freeze(),
             'fresh different-author review/source freeze differs')
        reports[axis] = {'reference': reference, 'report': report, 'raw': captured['raw']}
    return reports


def _root(kind, attempt):
    need(kind in ('public', 'formal') and type(attempt) is int and attempt == 1,
         'NEW recovery attempt2 closed unused; primary attempt1 only')
    policy = authority()
    return Path(policy['primary_public_root'] if kind == 'public'
                else policy['targets']['formal'][0])


def _context(kind):
    policy = authority()
    return {'execution_identity': IDENTITY, 'scope': SCOPE, 'attempt': 1,
            'source_root': str(Path(policy['captured_cores'][kind]['path']).parent),
            'authority_sha256': sha(AUTHORITY.read_bytes()), 'source_tree': source_freeze(),
            'actors': policy['actors']}


def write_new(path, value):
    """Create metadata under a held no-follow parent; never replace prior evidence."""
    core = load('p17_m2_source_binding')
    path, raw = Path(path), canonical(value)
    core.metadata_path_guard(path)
    parent = core.source_parent(path.parent, 'unused')
    try:
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        with os.fdopen(descriptor, 'wb') as stream:
            need(stream.write(raw) == len(raw), 'metadata short write')
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return sha(raw)


def _verify_terminal(actual, *, earliest_ms=None, latest_ms=None):
    """Validate original external returns; no serialized PASS establishes a return."""
    need(isinstance(actual, dict) and isinstance(actual.get('responses'), list)
         and 1 <= len(actual['responses']) <= 17, 'original terminal actual packet required')
    previous, session = None, None
    for index, row in enumerate(actual['responses']):
        result = row.get('result', {})
        need(type(row.get('requested_ms')) is int and type(row.get('returned_ms')) is int
             and row['requested_ms'] <= row['returned_ms']
             and (previous is None or previous <= row['requested_ms'])
             and isinstance(result.get('output'), str), 'actual clock/output incomplete')
        need('Warning: truncated output' not in result['output']
             and 'tokens truncated' not in result['output']
             and (result.get('original_token_count') is None
                  or result['original_token_count'] <= row.get('arguments', {}).get(
                      'max_output_tokens', 10000)), 'truncated actual return rejected')
        if index == 0:
            need(row.get('tool') == 'exec_command'
                 and row.get('arguments') == actual.get('request'),
                 'original actual request differs')
        else:
            arguments = row.get('arguments', {})
            need(row.get('tool') == 'write_stdin' and session is not None
                 and arguments.get('session_id') == session
                 and arguments.get('chars', '') == ''
                 and 0 < arguments.get('yield_time_ms', 5000) <= 30000,
                 'unowned/nonempty actual poll')
        if index < len(actual['responses']) - 1:
            need(type(result.get('session_id')) is int and result.get('exit_code') is None,
                 'nonterminal session differs')
            need(session is None or session == result['session_id'], 'actual session changed')
            session = result['session_id']
        else:
            need(type(result.get('exit_code')) is int and result['exit_code'] == 0
                 and result.get('session_id') is None, 'actual successful terminal missing')
        previous = row['returned_ms']
    first, last = actual['responses'][0]['requested_ms'], previous
    need((earliest_ms is None or earliest_ms <= first)
         and (latest_ms is None or last <= latest_ms), 'actual return outside fixed window')
    return first, last


def _publication_shape(value):
    need(isinstance(value, dict) and isinstance(value.get('main'), str)
         and re.fullmatch('[0-9a-f]{40}', value['main'])
         and type(value.get('main_CI_run')) is int, 'exact protected-main publication missing')
    jobs = value.get('jobs', [])
    need({'quality', 'frontend', 'clean-linux-smoke', 'i1-native-software'} <= {
        row['name'] for row in jobs if row.get('status') == 'completed'
        and row.get('conclusion') == 'success'}, 'all four exact-main CI jobs required')
    rules = value.get('protection', {})
    need(rules.get('required_status_checks', {}).get('strict') is True
         and rules.get('enforce_admins', {}).get('enabled') is True
         and rules.get('allow_force_pushes', {}).get('enabled') is False
         and rules.get('allow_deletions', {}).get('enabled') is False,
         'protected main required')
    return value


def publication_readiness():
    """Four real bounded GH GETs with complete successful or failed raw prefix."""
    observations = []
    try:
        return _publication_readiness(observations)
    except BaseException as error:
        error.recovery_publication_failure = deepcopy(observations)
        raise


def _publication_readiness(observations):
    import subprocess

    def command(argv):
        before = time.time_ns()
        try:
            result = subprocess.run(argv, cwd=REPO,
                env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'},
                capture_output=True, timeout=30, check=False)
        except BaseException as error:
            observations.append({'argv': argv, 'requested_ns': before,
                'returned_ns': time.time_ns(), 'error_type': type(error).__name__,
                'error_reason': str(error),
                'partial_stdout_hex': (getattr(error, 'stdout', None) or b'').hex(),
                'partial_stderr_hex': (getattr(error, 'stderr', None) or b'').hex()})
            raise
        after = time.time_ns()
        observation = {'argv': argv, 'requested_ns': before, 'returned_ns': after,
                       'exit_code': result.returncode, 'stdout': result.stdout.decode('utf-8'),
                       'stderr': result.stderr.decode('utf-8')}
        observations.append(observation)
        need(result.returncode == 0 and len(result.stdout) <= 2 * 1024**2,
             'bounded publication command failed')
        return result.stdout

    need(not command(['git', '--no-optional-locks', 'status', '--porcelain=v1', '-uall']).strip(),
         'clean published recovery main required')
    head = command(['git', 'rev-parse', 'HEAD']).decode().strip()

    def github(endpoint):
        return json.loads(command(['gh', 'api', 'repos/keith1117/TopoLab/' + endpoint]))

    branch = github('branches/main')
    need(branch['commit']['sha'] == head and branch.get('protected') is True,
         'fresh remote protected main differs')
    protection = github('branches/main/protection')
    runs = github('actions/runs?head_sha=' + head + '&branch=main&per_page=100')['workflow_runs']
    success = next((row for row in runs if row.get('head_sha') == head
                    and row.get('head_branch') == 'main' and row.get('status') == 'completed'
                    and row.get('conclusion') == 'success'), None)
    need(success is not None, 'completed successful exact-main run required')
    jobs = github('actions/runs/' + str(success['id']) + '/jobs?per_page=100')['jobs']
    value = {'main': head, 'tree': branch['commit']['commit']['tree']['sha'],
             'main_CI_run': success['id'], 'jobs': jobs, 'protection': protection,
             'source_tree': source_freeze(), 'api_observations': observations,
             'main_endpoint': 'branches/main', 'main_shape_adapter':
             'branch.commit.sha/tree read explicitly; not claimed commits/main'}
    _publication_shape(value)
    need({'quality', 'frontend', 'clean-linux-smoke'} <= set(
        protection['required_status_checks']['contexts'])
         and protection.get('required_conversation_resolution', {}).get('enabled') is True,
         'required protected release checks differ')
    return value


def activation_readiness(expected_sha):
    policy = authority()
    reference = {'path': policy['preparation_proofs']['recovery_activation_path'],
                 'sha256': expected_sha}
    capture = capture_ref(reference)
    activation = _captured_activation(capture['value'], capture['raw'], expected_sha,
                                     source_freeze())
    need(activation['started_ms'] <= time.time_ns() // 10**6
         and time.time_ns() // 10**6 + 300000 <= activation['deadline_ms'],
         'actual publication closure/complete recovery suffix unavailable')
    return activation


def finalize_summary(plan, certificate, proof, result_sha):
    paths = authority()['certificate_paths'][plan['kind']][plan['recovery_attempt'] - 1]
    return {'status': 'STRICT23_CAPTURED_CORE_AND_NEW_METADATA_RETURN_ACCEPTED',
            'scope': SCOPE, 'captured_scope': certificate['scope'],
            'execution_identity': IDENTITY, 'paths': paths, 'sha256': result_sha,
            'bindings': 23, 'new_source_reads': 0, 'new_Foundation_helpers': 0,
            'auditor_T1': proof['T1'], 'input_acceptance': False, 'B_C_admission': False,
            'own_future_return': FUTURE}


def exact_actual(packet, argv, author, *, cwd=None):
    core = load('p17_m2_source_binding')
    need(packet.get('schema') == 'topolab.v2.m2-strict-source-binding.actual-call.v1'
         and packet.get('author') == author and packet.get('argv') == argv
         and packet.get('request', {}).get('cmd') == core.literal_command(argv)
         and packet['request'].get('workdir') == (str(REPO) if cwd is None else cwd),
         'original actual literal caller/command differs')
    return _verify_terminal(packet)


def public_readiness(attempt, expected_sha, actual_sha):
    need(type(attempt) is int and attempt == 1,
         'NEW public recovery attempt2 closed unused; primary attempt1 only')
    envelope, _ = certificate_pair('public', attempt, expected_sha)
    certificate, proof = verify_result_envelope(envelope)
    plan = envelope['metadata_plan']
    need(plan['context']['source_tree'] == source_freeze(),
         'public recovery software differs from current published freeze')
    need(certificate['scope'] == load('p17_m2_source_binding').PUBLIC_SCOPE,
         'public captured core required')
    argv = [plan['runtime']['python'], '-I',
            str(REPO / 'scripts/p17_m2_source_binding_recovery.py'),
            'finalize-result', '--plan', str(Path(plan['root']) / 'plan.json'),
            '--plan-sha', sha(canonical(plan))]
    reference = {'path': str(Path(plan['root']) / 'finalize-result-raw-actual-call.json'),
                 'sha256': actual_sha}
    actual = read_ref(reference)
    first, last = exact_actual(actual, argv, authority()['actors']['producer'])
    need(proof['T1'] <= first / 1000 <= last / 1000
         and last <= authority()['limits']['software_deadline_ms'],
         'public final return outside actual software/native suffix')
    returned = ''.join(row['result']['output'] for row in actual['responses']).encode('utf-8')
    need(returned == canonical(finalize_summary(plan, certificate, proof, expected_sha)),
         'actual public finalize stdout differs from exact accepted pair')
    return {'envelope_sha256': expected_sha, 'auditor_T1': proof['T1'],
            'finalize_actual': actual, 'finalize_actual_reference': reference,
            'finalize_actual_raw': capture_ref(reference)['raw'],
            'envelope': envelope, 'envelope_raw': canonical(envelope).decode('ascii')}


def preflight_argv(attempt, public_sha, finalize_actual_sha, standards_sha, spec_sha,
                   activation_sha):
    _root('public', attempt)
    return [load('p17_m2_source_binding').runtime()['python'], '-I',
            str(REPO / 'scripts/p17_m2_source_binding_recovery.py'), 'preflight',
            '--attempt', str(attempt), '--public-certificate-sha', public_sha,
            '--finalize-actual-sha', finalize_actual_sha, '--standards-sha', standards_sha,
            '--spec-sha', spec_sha, '--activation-sha', activation_sha]


def preflight(attempt, public_sha, finalize_actual_sha, *, standards_sha, spec_sha,
              activation_sha):
    _root('public', attempt)
    policy = authority()
    reviews = review_readiness(standards_sha, spec_sha)
    budget = budget_readiness()
    activation = activation_readiness(activation_sha)
    public = public_readiness(attempt, public_sha, finalize_actual_sha)
    need(public['finalize_actual']['responses'][-1]['returned_ms']
         <= activation['software_closure_actual']['responses'][-1]['returned_ms'],
         'software closure precedes actual public final return')
    publication = publication_readiness()
    runtime = load('p17_m2_source_binding').runtime()
    need(runtime['isolated'] == 1 and runtime['cwd'] == str(REPO)
         and runtime['threads'] == load('p17_m2_source_binding').THREADS,
         'actual independent isolated preflight runtime required')
    value = {'schema': 'topolab.v2.m2-strict-source-binding.recovery-preflight.v1',
             'author': policy['actors']['independent'], 'execution_identity': IDENTITY,
             'scope': SCOPE, 'source_tree': source_freeze(),
             'authority_sha256': sha(AUTHORITY.read_bytes()), 'runtime': runtime,
             'public_certificate_sha256': public_sha, 'public_recovery_attempt': attempt,
             'public_result': public, 'main': publication['main'],
             'main_CI_run': publication['main_CI_run'], 'publication': publication,
             'budget': policy['budget'], 'budget_evidence': budget,
             'reviews': reviews, 'activation': activation,
             'activation_raw': capture_ref({'path': policy['preparation_proofs'][
                 'recovery_activation_path'], 'sha256': activation_sha})['raw'],
             'activation_sha256': activation_sha, 'observed_unix_ns': time.time_ns(),
             'preflight_argv': preflight_argv(attempt, public_sha, finalize_actual_sha,
                 standards_sha, spec_sha, activation_sha), 'own_future_return': FUTURE,
             'original_source_reads': 0, 'Foundation_helpers': 0,
             'input_acceptance': False, 'B_C_admission': False}
    path = Path(policy['preparation_proofs']['preflight_path'])
    result_sha = write_new(path, value)
    return {'status': 'INDEPENDENT_RECOVERY_PREFLIGHT_OBSERVED_ACTUAL_RETURN_REQUIRED',
            'path': str(path), 'sha256': result_sha, 'execution_identity': IDENTITY,
            'public_recovery_attempt': attempt, 'own_future_return': FUTURE}


def formal_readiness(public_sha, preflight_sha, preflight_return_sha, activation_sha):
    policy = authority()
    proofs = policy['preparation_proofs']
    preflight = read_ref({'path': proofs['preflight_path'], 'sha256': preflight_sha})
    actual = read_ref({'path': proofs['preflight_actual_path'], 'sha256': preflight_return_sha})
    need(preflight.get('schema') == 'topolab.v2.m2-strict-source-binding.recovery-preflight.v1'
         and type(preflight.get('public_recovery_attempt')) is int
         and preflight['public_recovery_attempt'] == 1
         and preflight.get('author') == policy['actors']['independent']
         and preflight.get('execution_identity') == IDENTITY and preflight.get('scope') == SCOPE
         and preflight.get('source_tree') == source_freeze()
         and preflight.get('authority_sha256') == sha(AUTHORITY.read_bytes())
         and preflight.get('public_certificate_sha256') == public_sha
         and preflight.get('runtime') == load('p17_m2_source_binding').runtime(),
         'new independent preflight/source/runtime differs')
    need(actual.get('author') == policy['actors']['independent']
         and actual.get('preflight_sha256') == preflight_sha, 'preflight actual binding differs')
    attempt = preflight['public_recovery_attempt']
    public = preflight['public_result']
    argv = preflight_argv(attempt, public_sha, public['finalize_actual_reference']['sha256'],
        preflight['reviews']['standards']['reference']['sha256'],
        preflight['reviews']['spec']['reference']['sha256'], activation_sha)
    need(preflight['preflight_argv'] == argv, 'preflight literal argv differs')
    first, returned = exact_actual(
        actual['actual_call'], argv, policy['actors']['independent'])
    summary = {'status': 'INDEPENDENT_RECOVERY_PREFLIGHT_OBSERVED_ACTUAL_RETURN_REQUIRED',
              'path': proofs['preflight_path'], 'sha256': preflight_sha,
              'execution_identity': IDENTITY, 'public_recovery_attempt': attempt,
              'own_future_return': FUTURE}
    need(''.join(row['result']['output'] for row in actual['actual_call']['responses']).encode(
        'utf-8') == canonical(summary), 'actual preflight stdout/proof SHA differs')
    need(first <= preflight['observed_unix_ns'] // 10**6 <= returned,
         'preflight actual return predates observation')
    public_readiness(attempt, public_sha, public['finalize_actual_reference']['sha256'])
    publication = publication_readiness()
    need(preflight.get('main') == publication['main']
         and preflight.get('main_CI_run') == publication['main_CI_run'],
         'fresh exact main differs from independent preflight')
    activation = activation_readiness(activation_sha)
    need(preflight['activation_sha256'] == activation_sha
         and preflight['activation'] == activation, 'actual recovery activation changed')
    return {'preflight': preflight, 'preflight_actual': actual, 'publication': publication,
            'activation': activation, 'activation_sha256': activation_sha,
            'public_certificate_sha256': public_sha, 'public_auditor_T1': public['auditor_T1'],
            'preflight_reference': {'path': proofs['preflight_path'], 'sha256': preflight_sha},
            'preflight_raw': capture_ref({'path': proofs['preflight_path'],
                'sha256': preflight_sha})['raw'],
            'preflight_actual_reference': {'path': proofs['preflight_actual_path'],
                'sha256': preflight_return_sha},
            'preflight_actual_raw': capture_ref({'path': proofs['preflight_actual_path'],
                'sha256': preflight_return_sha})['raw'],
            'activation_raw': capture_ref({'path': proofs['recovery_activation_path'],
                'sha256': activation_sha})['raw']}


def prepare(kind, attempt=1, *, standards_sha=None, spec_sha=None,
            public_certificate_sha=None, preflight_sha=None, preflight_return_sha=None,
            activation_sha=None):
    """Prepare one fixed new metadata attempt and return its exact small command table."""
    core, policy = load('p17_m2_source_binding'), authority()
    root = _root(kind, attempt)
    reviews = review_readiness(standards_sha, spec_sha)
    budget = budget_readiness()
    runtime = core.runtime()
    need(runtime['isolated'] == 1 and runtime['cwd'] == str(REPO)
         and runtime['threads'] == core.THREADS, 'isolated locked single-thread runtime required')
    entry = {'budget': policy['budget'], 'budget_evidence': budget,
             'reviews': reviews, 'old_source_access': False,
             'old_scene_write': False}
    if kind == 'formal':
        entry['formal'] = formal_readiness(public_certificate_sha, preflight_sha,
                                          preflight_return_sha, activation_sha)
    pin = policy['captured_cores'][kind]
    bundle = read_ref({'path': pin['path'], 'sha256': pin['sha256']})
    replay_core(bundle, kind)
    started = time.time_ns()
    limit = (policy['limits']['software_deadline_ms'] if kind == 'public'
             else entry['formal']['activation']['deadline_ms']) * 10**6
    need(started + 300 * 10**9 <= min(limit, policy['limits']['global_deadline_ms'] * 10**6),
         'complete immutable recovery window unavailable')
    context = _context(kind)
    deadline = datetime.fromtimestamp((started + 300 * 10**9) / 10**9, UTC).isoformat()
    plan = {'schema': PLAN_SCHEMA, 'root': str(root), 'context': context,
            'runtime': runtime, 'kind': kind, 'recovery_attempt': attempt,
            'captured_core_context': deepcopy(bundle['plan']['context']),
            'bundle': {'path': pin['path'], 'sha256': pin['sha256']},
            'role_order': [ROLE], 'roles': {ROLE: {'author': policy['actors']['independent'],
                'FULL': 120, 'timeout': 110, 'argv': core.role_argv(
                    root, 'payload', '@PLAN_SHA256@', ROLE, runtime['python'],
                    execution_identity=IDENTITY)}},
            'started_unix_ns': started, 'deadline_unix_ns': started + 300 * 10**9,
            'actor_activation_UTC_seconds': started / 10**9, 'actor_window_seconds': 300,
            'actor_deadlines_UTC': {key: deadline.replace('+00:00', 'Z') for key in
                                    ('exporter', 'independent')}, 'entry': entry}
    # No target stat/open/mkdir occurs before every admission dependency above.
    parent = core.source_parent(root.parent, 'unused')
    try:
        os.mkdir(root.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    plan_sha = write_new(root / 'plan.json', plan)
    native = load('p17_m2_source_binding_native')
    commands = {mode: {'argv': native.argv_for(plan, mode, ROLE),
                       'cmd': core.literal_command(native.argv_for(plan, mode, ROLE))}
                for mode in ('supervise', 'record')}
    return {'root': str(root), 'plan_path': str(root / 'plan.json'), 'plan_sha256': plan_sha,
            'execution_identity': IDENTITY, 'scope': SCOPE, 'role': ROLE,
            'author': policy['actors']['independent'], 'actor_start_ms': started // 10**6,
            'deadline_ms': plan['deadline_unix_ns'] // 10**6, 'FULL': 120,
            'reserve_seconds': 60, 'window_seconds': 300, 'commands': commands}



def _captured_activation(activation, raw, expected_sha, tree):
    policy = authority()
    captured_value({'reference': {'path': policy['preparation_proofs'][
        'recovery_activation_path'], 'sha256': expected_sha}, 'raw': raw, 'value': activation})
    need(activation.get('schema') == 'topolab.v2.m2-strict-source-binding.recovery-activation.v1'
         and activation.get('execution_identity') == IDENTITY
         and activation.get('software_source_tree') == tree
         and type(activation.get('started_ms')) is int
         and activation.get('deadline_ms') == activation['started_ms'] + 1200000
         and activation['deadline_ms'] <= policy['limits']['global_deadline_ms'],
         'captured activation schema/source/fixed clock differs')
    closure = activation['software_closure_actual']
    _, ended = exact_actual(closure, closure['argv'], policy['actors']['producer'])
    publication_closure = activation['publication_closure_actual']
    publication_start, publication_end = exact_actual(publication_closure,
        publication_closure['argv'], policy['actors']['producer'])
    need(ended <= publication_start <= publication_end
         <= ended + policy['publication_only']['seconds_each'] * 1000
         and publication_end == activation['started_ms']
         and policy['limits']['software_start_ms'] <= ended
         <= policy['limits']['software_deadline_ms'],
         'captured software closure actual does not establish activation')
    return activation


def _captured_public(public, expected_sha, tree):
    envelope = public.get('envelope')
    need(isinstance(envelope, dict), 'captured full public envelope required')
    plan = envelope['metadata_plan']
    attempt = plan['recovery_attempt']
    _root('public', attempt)
    need(plan['kind'] == 'public' and plan['context']['source_tree'] == tree,
         'captured public software freeze differs')
    paths = authority()['certificate_paths']['public'][attempt - 1]
    captured_value({'reference': {'path': paths[0], 'sha256': expected_sha},
                    'raw': public.get('envelope_raw'), 'value': envelope})
    certificate, audit = verify_result_envelope(envelope)
    reference = public['finalize_actual_reference']
    need(reference['path'] == str(Path(plan['root']) / 'finalize-result-raw-actual-call.json'),
         'captured public finalize path differs')
    actual = captured_value({'reference': reference, 'raw': public.get('finalize_actual_raw'),
                             'value': public['finalize_actual']})
    argv = [plan['runtime']['python'], '-I',
            str(REPO / 'scripts/p17_m2_source_binding_recovery.py'), 'finalize-result',
            '--plan', str(Path(plan['root']) / 'plan.json'),
            '--plan-sha', sha(canonical(plan))]
    first, last = exact_actual(actual, argv, authority()['actors']['producer'])
    need(audit['T1'] <= first / 1000 <= last / 1000
         and last <= authority()['limits']['software_deadline_ms']
         and ''.join(row['result']['output'] for row in actual['responses']).encode('utf-8')
         == canonical(finalize_summary(plan, certificate, audit, expected_sha)),
         'captured public own actual return/stdout differs')
    need(public.get('auditor_T1') == audit['T1'] and public.get('envelope_sha256') == expected_sha,
         'captured public audit/hash summary differs')
    return last


def _captured_formal(admitted, context, runtime):
    policy, proofs = authority(), authority()['preparation_proofs']
    need(isinstance(admitted, dict), 'captured formal entry required')
    reference = admitted['preflight_reference']
    need(reference['path'] == proofs['preflight_path'], 'captured preflight path differs')
    preflight = captured_value({'reference': reference, 'raw': admitted['preflight_raw'],
                                'value': admitted['preflight']})
    need(preflight.get('schema') == 'topolab.v2.m2-strict-source-binding.recovery-preflight.v1'
         and type(preflight.get('public_recovery_attempt')) is int
         and preflight['public_recovery_attempt'] == 1
         and preflight.get('author') == policy['actors']['independent']
         and preflight.get('execution_identity') == IDENTITY and preflight.get('scope') == SCOPE
         and preflight.get('source_tree') == context['source_tree']
         and preflight.get('authority_sha256') == context['authority_sha256']
         and preflight.get('runtime') == runtime and preflight.get('budget') == policy['budget'],
         'captured formal preflight full schema/policy differs')
    _captured_budget(preflight.get('budget_evidence'))
    for axis in ('standards', 'spec'):
        report = captured_value(preflight['reviews'][axis], 'report')
        need(report.get('status') == 'PASS' and report.get('open_findings') == []
             and report.get('author') == policy['review_authors'][axis]
             and report.get('execution_identity') == IDENTITY
             and report.get('reviewed_source_tree') == context['source_tree']
             and preflight['reviews'][axis]['reference']['path'] == policy['review_paths'][axis],
             'captured preflight review differs')
    public_sha = admitted['public_certificate_sha256']
    need(preflight.get('public_certificate_sha256') == public_sha,
         'captured public certificate reference differs')
    public = preflight['public_result']
    public_end = _captured_public(public, public_sha, context['source_tree'])
    actual_reference = admitted['preflight_actual_reference']
    need(actual_reference['path'] == proofs['preflight_actual_path'],
         'captured preflight actual path differs')
    actual = captured_value({'reference': actual_reference,
        'raw': admitted['preflight_actual_raw'], 'value': admitted['preflight_actual']})
    need(actual.get('author') == policy['actors']['independent']
         and actual.get('preflight_sha256') == reference['sha256'],
         'captured preflight actual SHA/author differs')
    argv = [runtime['python'], '-I', str(REPO / 'scripts/p17_m2_source_binding_recovery.py'),
        'preflight', '--attempt', str(preflight['public_recovery_attempt']),
        '--public-certificate-sha', public_sha, '--finalize-actual-sha',
        public['finalize_actual_reference']['sha256'], '--standards-sha',
        preflight['reviews']['standards']['reference']['sha256'], '--spec-sha',
        preflight['reviews']['spec']['reference']['sha256'], '--activation-sha',
        admitted['activation_sha256']]
    need(preflight['preflight_argv'] == argv, 'captured preflight argv differs')
    first, last = exact_actual(actual['actual_call'], argv, policy['actors']['independent'])
    summary = {'status': 'INDEPENDENT_RECOVERY_PREFLIGHT_OBSERVED_ACTUAL_RETURN_REQUIRED',
        'path': proofs['preflight_path'], 'sha256': reference['sha256'],
        'execution_identity': IDENTITY,
        'public_recovery_attempt': preflight['public_recovery_attempt'],
        'own_future_return': FUTURE}
    need(first <= preflight['observed_unix_ns'] // 10**6 <= last
         and ''.join(row['result']['output'] for row in actual['actual_call'][
             'responses']).encode('utf-8') == canonical(summary),
         'captured preflight complete actual stdout/clock differs')
    activation = _captured_activation(admitted['activation'], admitted['activation_raw'],
        admitted['activation_sha256'], context['source_tree'])
    need(preflight.get('activation_sha256') == admitted['activation_sha256']
         and preflight.get('activation') == activation
         and preflight.get('activation_raw') == admitted['activation_raw']
         and public_end <= activation['software_closure_actual']['responses'][-1][
             'returned_ms'] <= activation['started_ms'] <= first <= last
         <= activation['deadline_ms'],
         'captured activation/public/preflight chronology differs')
    _publication_shape(preflight['publication'])
    _publication_shape(admitted['publication'])
    need(preflight['main'] == preflight['publication']['main'] == admitted['publication']['main']
         and preflight['main_CI_run'] == preflight['publication']['main_CI_run']
         == admitted['publication']['main_CI_run'], 'captured exact-main publication differs')


def _plan_shape(plan, *, historical=False):
    policy = authority()
    kind, attempt = plan.get('kind'), plan.get('recovery_attempt')
    need(plan.get('schema') == PLAN_SCHEMA and plan.get('root') == str(_root(kind, attempt))
         and plan.get('role_order') == [ROLE], 'recovery plan/root/role inventory differs')
    context = plan['context']
    need(set(context) == {'execution_identity', 'scope', 'attempt', 'source_root',
                          'authority_sha256', 'source_tree', 'actors'}
         and context['execution_identity'] == IDENTITY and context['scope'] == SCOPE
         and type(context['attempt']) is int and context['attempt'] == 1
         and context['authority_sha256'] == sha(AUTHORITY.read_bytes())
         and context['actors'] == policy['actors']
         and context['source_root'] == str(Path(policy['captured_cores'][kind]['path']).parent),
         'new recovery context must not relabel captured source identity')
    tree = context['source_tree']
    need(isinstance(tree, dict) and set(tree) == set(source_freeze())
         and all(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)
                 for value in tree.values()), 'complete recovery software freeze differs')
    if not historical:
        need(context == _context(kind), 'current recovery source freeze differs')
    expected = policy['captured_cores'][kind]
    need(plan.get('captured_core_context') == expected['context']
         and plan.get('bundle') == {'path': expected['path'], 'sha256': expected['sha256']},
         'captured core context/pin differs')
    runtime = plan['runtime']
    expected_role = {'author': policy['actors']['independent'], 'FULL': 120, 'timeout': 110,
                     'argv': load('p17_m2_source_binding').role_argv(
                         plan['root'], 'payload', '@PLAN_SHA256@', ROLE, runtime['python'],
                         execution_identity=IDENTITY)}
    need(plan['roles'] == {ROLE: expected_role}
         and type(plan['started_unix_ns']) is int and type(plan['deadline_unix_ns']) is int
         and plan['deadline_unix_ns'] - plan['started_unix_ns'] == 300 * 10**9
         and plan['actor_activation_UTC_seconds'] == plan['started_unix_ns'] / 10**9
         and type(plan['actor_window_seconds']) is int and plan['actor_window_seconds'] == 300,
         'immutable recovery native cap/window differs')
    entry = plan['entry']
    need(entry.get('budget') == policy['budget'] and entry.get('old_source_access') is False
         and entry.get('old_scene_write') is False, 'new finite metadata entry differs')
    _captured_budget(entry.get('budget_evidence'))
    for axis in ('standards', 'spec'):
        report = captured_value(entry['reviews'][axis], 'report')
        reference = entry['reviews'][axis]['reference']
        need(reference['path'] == policy['review_paths'][axis]
             and report.get('author') == policy['review_authors'][axis]
             and report.get('execution_identity') == IDENTITY
             and report.get('status') == 'PASS' and report.get('open_findings') == []
             and report.get('reviewed_source_tree') == tree,
             'captured fresh review differs from new software freeze')
    need('remedy' not in entry, 'NEW recovery remedy closed unused; primary only')
    if kind == 'formal':
        _captured_formal(entry['formal'], context, runtime)
        admitted = entry['formal']
        preflight = admitted['preflight']
        need(preflight['source_tree'] == tree and preflight['execution_identity'] == IDENTITY
             and preflight['scope'] == SCOPE and preflight['authority_sha256']
             == context['authority_sha256'], 'formal preflight policy differs')
        activation = admitted['activation']
        need(activation['software_source_tree'] == tree
             and plan['deadline_unix_ns'] <= activation['deadline_ms'] * 10**6,
             'formal native window exceeds new activated result stage')
    else:
        need(plan['deadline_unix_ns'] <= policy['limits']['software_deadline_ms'] * 10**6,
             'public recovery outside fixed software stage')
    need(plan['deadline_unix_ns'] <= policy['limits']['global_deadline_ms'] * 10**6,
         'recovery beyond unchanged global hard limit')
    return plan


def load_plan(path, expected_sha):
    path = Path(path)
    targets = [str(_root(kind, 1)) for kind in ('public', 'formal')]
    need(path.is_absolute() and '..' not in path.parts and path.name == 'plan.json'
         and str(path.parent) in targets, 'exact active primary recovery plan root required')
    plan, _ = load('p17_m2_source_binding').read_metadata(
        path, 16 * 1024**2, expected=expected_sha, canonical_required=True)
    _plan_shape(plan, historical=True)
    need(plan['root'] == str(path.parent), 'literal recovery plan/root differs')
    return plan


def admit_plan(plan, role):
    _plan_shape(plan)
    core = load('p17_m2_source_binding')
    need(role == ROLE and plan['runtime'] == core.runtime()
         and plan['runtime']['isolated'] == 1 and plan['runtime']['cwd'] == str(REPO)
         and plan['runtime']['threads'] == core.THREADS,
         'actual isolated recovery runtime differs')
    need(plan['started_unix_ns'] <= time.time_ns() <= plan['deadline_unix_ns'],
         'immutable metadata recovery role window expired')
    budget_readiness()
    bundle = read_ref(plan['bundle'])
    replay_core(bundle, plan['kind'])
    return plan


class Transport(load('p17_m2_source_binding_native').MetadataTransport):
    """One metadata-only native auditor; no source child or old role predecessor."""

    def predecessor(self, root, plan, role):
        need(Path(root) == self.root and plan == self.plan, 'recovery transport plan differs')
        admit_plan(plan, role)

    def namespace_check(self, root, **kwargs):
        need(Path(root) == self.root and str(root) == str(_root(
            self.plan['kind'], self.plan['recovery_attempt'])), 'recovery namespace differs')
        core = load('p17_m2_source_binding')
        base = load('p17_m2_content_verified_control')
        parent = core.source_parent(Path(root), 'unused')
        try:
            before = os.fstat(parent)
            result = base._namespace_snapshot(parent,
                additional_bytes=kwargs.get('additional_bytes', 0),
                additional_files=kwargs.get('additional_files', 0), evidence=True)
            closing = core.source_parent(Path(root), 'unused')
            try:
                after = os.fstat(closing)
                need((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino),
                     'recovery namespace root identity changed')
            finally:
                os.close(closing)
            limits = authority()['limits']
            need(result['count'] + kwargs.get('additional_files', 0) <= limits['namespace_files']
                 and result['size'] + kwargs.get('additional_bytes', 0)
                 <= limits['namespace_bytes'],
                 'bounded recovery metadata inventory exceeded')
            return result
        finally:
            os.close(parent)

    def put(self, path, value):
        literal = os.fspath(path)
        need(isinstance(literal, str) and Path(literal).is_absolute()
             and not any(part in ('.', '..') for part in literal.split('/')),
             'literal recovery writer path cannot contain dot segments')
        path = Path(literal)
        load('p17_m2_source_binding').metadata_path_guard(path)
        need(path.is_relative_to(self.root), 'recovery write outside one new attempt')
        self.namespace_check(self.root, additional_bytes=len(canonical(value)), additional_files=1)
        return load('p17_m2_content_verified_control').put(path, value)


def payload(plan, role):
    stage = 'recovery_admission'
    try:
        admit_plan(plan, role)
        load('p17_m2_source_binding_native').assert_payload_launch(plan, role)
        stage = 'captured_core_replay'
        certificate = replay_core(read_ref(plan['bundle']), plan['kind'])
        write_new(Path(plan['root']) / (ROLE + '-output.json'), certificate)
        return certificate
    except BaseException as error:
        return {'schema': 'topolab.v2.m2-strict-source-binding.recovery-failure.v1',
                'status': 'STOP_NO_RETRY', 'execution_identity': IDENTITY, 'stage': stage,
                'role': role, 'original_source_reads': 0, 'Foundation_helpers': 0,
                'registered_context': plan.get('context'),
                'captured_core_context': plan.get('captured_core_context'),
                'recovery_attempt': plan.get('recovery_attempt'),
                **load('p17_m2_source_binding').error_context(error)}


def verify_result_envelope(envelope):
    """Audit the NEW auditor's native lifetime and both actual external returns."""
    need(envelope.get('schema') == ENVELOPE_SCHEMA
         and envelope.get('own_future_return') == FUTURE, 'new recovered envelope required')
    plan = _plan_shape(envelope['metadata_plan'], historical=True)
    bundle = envelope['core_bundle']
    certificate = replay_core(bundle, plan['kind'])
    need(plan['captured_core_context'] == bundle['plan']['context']
         and plan['bundle']['sha256'] == sha(canonical(bundle)),
         'new auditor/captured strict core binding differs')
    evidence = load('p17_m2_content_verified_control').evidence_json(
        envelope['metadata_evidence'], decode=True)
    proof = load('p17_m2_source_binding_native').audit_role(
        plan, ROLE, evidence, envelope['metadata_events'])
    need(proof.get('full_role_evidence_accepted') is True
         and evidence['inner_evidence']['log'] == canonical(certificate)
         and proof['T0'] >= max(row['T1'] for row in certificate['native_role_audits'].values()),
         'new independent actual native/return or captured buffer differs')
    return certificate, proof


def verify_registration(envelope, finalize_actual, *, kind='formal'):
    """Verify pre-read registration evidence; this function never reads a source."""
    need(kind in ('public', 'formal'), 'literal registration kind required')
    certificate, proof = verify_result_envelope(envelope)
    plan = envelope['metadata_plan']
    scope = ('PUBLIC_STRICT_BINDING_REGISTRATION_ONLY' if kind == 'public'
             else 'FORMAL_STRICT_BINDING_REGISTRATION_ONLY')
    need(plan['kind'] == kind and certificate['scope'] == scope
         and plan['context']['source_tree'] == source_freeze(),
         'registration kind/scope/current published software differs')
    argv = [plan['runtime']['python'], '-I',
            str(Path(plan['runtime']['cwd']) / 'scripts/p17_m2_source_binding_recovery.py'),
            'finalize-result', '--plan', str(Path(plan['root']) / 'plan.json'),
            '--plan-sha', sha(canonical(plan))]
    first, last = exact_actual(finalize_actual, argv, authority()['actors']['producer'])
    limit = (authority()['limits']['software_deadline_ms'] if kind == 'public'
             else plan['entry']['formal']['activation']['deadline_ms'])
    stdout = ''.join(row['result']['output'] for row in finalize_actual['responses'])
    need(proof['T1'] <= first / 1000 <= last / 1000 and last <= limit
         and stdout.encode('utf-8') == canonical(finalize_summary(
             plan, certificate, proof, sha(canonical(envelope)))),
         'registration finalize actual return/stdout or immutable deadline differs')
    return certificate, proof


def certificate_pair(kind, attempt, expected_sha):
    import stat
    _root(kind, attempt)
    paths = [Path(path) for path in authority()['certificate_paths'][kind][attempt - 1]]
    buffers, identities = [], []
    for path in paths:
        value, raw = load('p17_m2_source_binding').read_metadata(
            path, 40 * 1024**2, expected=expected_sha, canonical_required=True)
        info = path.lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
             and stat.S_IMODE(info.st_mode) == 0o600, 'private ordinary certificate required')
        buffers.append((value, raw))
        identities.append((info.st_dev, info.st_ino))
    need(buffers[0][1] == buffers[1][1] and identities[0] != identities[1],
         'independent byte-identical certificate copies required')
    return buffers[0][0], paths


def finalize(plan):
    _plan_shape(plan)
    policy, root = authority(), Path(plan['root'])
    deadline = (policy['limits']['software_deadline_ms'] if plan['kind'] == 'public'
                else plan['entry']['formal']['activation']['deadline_ms'])
    need(time.time_ns() // 10**6 <= min(deadline, policy['limits']['global_deadline_ms']),
         'fixed new recovery result deadline expired')
    core, native = load('p17_m2_source_binding'), load('p17_m2_source_binding_native')
    bundle = read_ref(plan['bundle'])
    events = core.read_metadata(root / (ROLE + '-events.json'), 2 * 1024**2,
                                canonical_required=True)[0]
    evidence = native.role_evidence(root, sha(canonical(plan)), ROLE)
    envelope = {'schema': ENVELOPE_SCHEMA, 'core_bundle': bundle, 'metadata_plan': plan,
                'metadata_events': events,
                'metadata_evidence': load('p17_m2_content_verified_control').evidence_json(
                    evidence),
                'own_future_return': FUTURE}
    certificate, proof = verify_result_envelope(envelope)
    paths = list(map(Path, policy['certificate_paths'][plan['kind']][plan['recovery_attempt'] - 1]))
    hashes = [write_new(path, envelope) for path in paths]
    need(hashes[0] == hashes[1], 'recovered certificate copy bytes differ')
    certificate_pair(plan['kind'], plan['recovery_attempt'], hashes[0])
    return finalize_summary(plan, certificate, proof, hashes[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'supervise', 'run', 'record', 'payload',
        'file-actual-event', 'accept-role', 'show-commands', 'finalize-result', 'preflight'))
    parser.add_argument('--kind', choices=('public', 'formal'))
    parser.add_argument('--attempt', type=int, choices=(1,), default=1)
    for key in ('plan', 'plan-sha', 'role', 'events-sha', 'packet', 'packet-sha', 'event-mode',
                'standards-sha', 'spec-sha', 'public-certificate-sha', 'preflight-sha',
                'preflight-return-sha', 'activation-sha', 'finalize-actual-sha'):
        parser.add_argument('--' + key)
    args = parser.parse_args()
    if args.mode == 'prepare':
        result = prepare(args.kind, args.attempt, standards_sha=args.standards_sha,
            spec_sha=args.spec_sha, public_certificate_sha=args.public_certificate_sha,
            preflight_sha=args.preflight_sha, preflight_return_sha=args.preflight_return_sha,
            activation_sha=args.activation_sha)
    elif args.mode == 'preflight':
        result = preflight(args.attempt, args.public_certificate_sha, args.finalize_actual_sha,
            standards_sha=args.standards_sha, spec_sha=args.spec_sha,
            activation_sha=args.activation_sha)
    elif args.mode in ('supervise', 'run', 'record'):
        return load('p17_m2_source_binding_native').main()
    else:
        plan = load_plan(args.plan, args.plan_sha)
        core = load('p17_m2_source_binding')
        if args.mode == 'payload':
            result = payload(plan, args.role)
        elif args.mode == 'file-actual-event':
            result = core.file_actual_event(plan, args.role, args.event_mode,
                                           args.packet, args.packet_sha)
        elif args.mode == 'accept-role':
            result = core.accept_role(plan, args.role, args.events_sha)
        elif args.mode == 'show-commands':
            native = load('p17_m2_source_binding_native')
            result = {ROLE: {mode: {'argv': native.argv_for(plan, mode, ROLE),
                'cmd': core.literal_command(native.argv_for(plan, mode, ROLE))}
                for mode in ('supervise', 'record')}}
        else:
            result = finalize(plan)
    print(canonical(result).decode(), end='')
    return 1 if result.get('status') == 'STOP_NO_RETRY' else 0


if __name__ == '__main__':
    os.umask(0o077)
    try:
        raise SystemExit(main())
    except BaseException as error:
        if isinstance(error, SystemExit):
            raise
        print(canonical({'status': 'STOP_NO_RETRY', 'stage': 'recovery_control',
            'original_source_reads': 0,
            'publication_failure': getattr(error, 'recovery_publication_failure', None),
            **load('p17_m2_source_binding').error_context(error)}).decode(), end='')
        raise SystemExit(1) from error
