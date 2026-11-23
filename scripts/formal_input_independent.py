"""Replay admitted public bytes under their historical independent source only.

This adapter grants no source/target IO or old role allowance. Historical imports
are temporary, source-pinned, read-only, and cannot launch subprocesses.
"""

import builtins
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import sysconfig
from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

OLD_REPO = Path('/private/tmp/topolab-staged-input-20261121')
EVIDENCE = Path('/Users/keith1117/Documents/TopoLab-data/formal-input-20261122')
R0_EVIDENCE = EVIDENCE.parent / 'r0-read-acceptance-20261122'
CATALOG_EVIDENCE = EVIDENCE.parent / 'catalog-r0-acceptance-20261122'
CYCLE_EVIDENCE = EVIDENCE.parent / 'input-cycle-20261123-a1'
CYCLE_R1_EVIDENCE = EVIDENCE.parent / 'input-cycle-20261123-a2'
CYCLE_FILING_EVIDENCE = EVIDENCE.parent / 'input-cycle-20261123-a3'
DATA = EVIDENCE.parent
OLD_IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.staged-20261121.v1'
OLD_ROOT = '/private/tmp/topolab-public-staged-input-20261121-a1'
OLD_MAIN = '259766dbe6ee1598a6100e58fe2b669fd2907841'
TREE_SHA = 'd66a910c78d6abf6ae5df81b0bd9d306ee9350c4b17acaf72580dcaadfffcecb'
PLAN_SHA = '6c72973b963c9ab744458fcc4dc64c2c7b8d7315b2cc75a6b5fd46250a2f4d71'
VERSION = 'c9ad14f2ca9c5e4d6859aa22dead7f98ef2ebd8ce8c24debf94ed1b634a8bd73'
BUNDLE_SHA = 'b5ffbe59de881707a2794118470c8c01fdef62e8860b668d91c9b312c3bb8f53'
ACTUAL_SHA = '46a1f6ae72925c9bf28bb6eb57f7221999b9095d6d6244e220d8a31a573ca72b'
ROLES = ('independent-public-check', 'exporter-r0', 'independent-r0',
         'exporter-r1', 'independent-r1', 'shared-closeout')
CAP = 16 * 1024**2
_VERIFIED = {}


def need(ok, reason):
    if not ok:
        raise ValueError('FORMAL_HISTORY_STOP: ' + reason)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def expected_prior(evidence_root=None):
    evidence_root = EVIDENCE if evidence_root is None else Path(evidence_root)
    need(evidence_root in (EVIDENCE, R0_EVIDENCE, CATALOG_EVIDENCE, CYCLE_EVIDENCE,
                          CYCLE_R1_EVIDENCE, CYCLE_FILING_EVIDENCE),
         'fixed historical evidence namespace differs')
    return dict(identity=OLD_IDENTITY, root=OLD_ROOT, source_main=OLD_MAIN,
                source_tree_sha256=TREE_SHA, plan_sha256=PLAN_SHA,
                version_id=VERSION, member_count=1071,
                bundle=dict(path=str(evidence_root / 'prior-public-bundle.json'),
                            sha256=BUNDLE_SHA),
                actual=dict(path=str(evidence_root / 'prior-public-certificate-actual.json'),
                            sha256=ACTUAL_SHA))


def parse(raw):
    def pairs(items):
        answer = {}
        for key, value in items:
            need(key not in answer, 'duplicate metadata key')
            answer[key] = value
        return answer

    def invalid(_):
        raise ValueError('FORMAL_HISTORY_STOP: nonfinite metadata')

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def _milliseconds(seconds):
    result = Decimal(str(seconds)) * 1000
    need(result.is_finite() and result == result.to_integral_value(),
         'original milliseconds differ')
    return int(result)


def _terminal(packet, argv):
    import shlex

    command = 'exec ' + shlex.join(['env', *(k + '=1' for k in (
        'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
        'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')), *argv])
    need(packet.get('schema') == 'topolab.v2.m2-strict-source-binding.actual-call.v1'
         and packet.get('author') == '/root' and packet.get('argv') == argv
         and packet.get('request', {}).get('cmd') == command
         and packet['request'].get('workdir') == str(OLD_REPO),
         'historical original command/actor differs')
    rows = packet.get('responses')
    need(type(rows) is list and 1 <= len(rows) <= 17, 'bounded original responses required')
    previous, session = None, None
    for index, row in enumerate(rows):
        result, args = row.get('result', {}), row.get('arguments', {})
        need(type(row.get('requested_ms')) is int and type(row.get('returned_ms')) is int
             and row['requested_ms'] <= row['returned_ms']
             and (previous is None or previous <= row['requested_ms'])
             and type(result.get('output')) is str
             and 'Warning: truncated output' not in result['output']
             and 'tokens truncated' not in result['output']
             and (result.get('original_token_count') is None
                  or result['original_token_count'] <= args.get('max_output_tokens', 10000)),
             'historical original clock/output incomplete')
        if not index:
            need(row.get('tool') == 'exec_command' and args == packet['request'],
                 'historical first request differs')
        else:
            need(row.get('tool') == 'write_stdin' and type(args.get('session_id')) is int
                 and args['session_id'] == session and args.get('chars', '') == ''
                 and type(args.get('yield_time_ms', 5000)) is int
                 and 0 < args.get('yield_time_ms', 5000) <= 30000,
                 'historical unowned poll')
        if index < len(rows) - 1:
            need(type(result.get('session_id')) is int and result.get('exit_code') is None
                 and (session is None or session == result['session_id']),
                 'historical session changed')
            session = result['session_id']
        else:
            need(type(result.get('exit_code')) is int and result['exit_code'] == 0
                 and result.get('session_id') is None, 'historical original terminal0 missing')
        previous = row['returned_ms']
    return rows[0]['requested_ms'], previous, ''.join(r['result']['output'] for r in rows).encode()


def _read(path):
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
                 'bounded owned historical metadata required')
            raw = stream.read(before.st_size + 1)
            after = os.fstat(stream.fileno())
        closing = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        keys = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns',
                'st_uid', 'st_mode', 'st_nlink')
        need(len(raw) == before.st_size and all(
            getattr(before, k) == getattr(after, k) == getattr(closing, k) for k in keys),
            'historical metadata changed')
        return raw
    finally:
        os.close(directory)


@contextmanager
def _historical_view(tree, python):
    """Confine historical replay to software/explicit receipt roots, restoring state."""
    buffers = {}
    for relative, digest in tree.items():
        path = Path(relative)
        need(not path.is_absolute() and '..' not in path.parts
             and path.parts[0] in ('scripts', 'docs', 'pyproject.toml', 'uv.lock'),
             'historical software whitelist differs')
        raw = _read(OLD_REPO / path)
        need(sha(raw) == digest, 'historical software SHA differs: ' + relative)
        buffers[relative] = raw
    prefixes = ('p17_m2_', 'full60_', 'staged_')
    saved_modules = {k: v for k, v in sys.modules.items() if k.startswith(prefixes)}
    saved_path, saved_code = list(sys.path), importlib.machinery.SourceFileLoader.get_code
    saved_bytecode = sys.dont_write_bytecode
    for name in saved_modules:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(OLD_REPO / 'scripts'))
    # The active source-only loader may import a not-yet-loaded standard module.
    # These are software roots, never an extension to either business namespace.
    current_repo = Path(__file__).resolve().parents[1]
    standard = tuple({Path(sysconfig.get_path(key)) for key in ('stdlib', 'platstdlib')})
    allowed = [OLD_REPO, current_repo / '.venv/lib/python3.12/site-packages']
    for name in ('staged-input-acceptance-20261121', 'metadata-input-acceptance-20261121',
                 'exporter-r1-throughput-20261121'):
        allowed += [DATA / name, DATA / (name + '-backup')]
    fd_paths = {}
    old_open, old_close, old_dup, old_stat = os.open, os.close, os.dup, os.stat
    old_io, old_builtin, old_scan, old_list, old_popen = (
        io.open, builtins.open, os.scandir, os.listdir, subprocess.Popen)

    def literal(path, dir_fd=None):
        if isinstance(path, int):
            need(path in fd_paths, 'unregistered historical descriptor')
            return fd_paths[path]
        path = Path(path)
        if not path.is_absolute():
            path = (fd_paths[dir_fd] if dir_fd is not None else Path.cwd()) / path
        need('..' not in path.parts, 'historical relative escape')
        return path

    def admit(path, *, directory=False):
        standard_library = any(path.is_relative_to(root)
            and not {'site-packages', 'dist-packages'} & set(path.relative_to(root).parts)
            for root in standard)
        need(path == Path(python) or any(path.is_relative_to(p) for p in allowed)
             or standard_library or (directory and any(
                 p.is_relative_to(path) for p in (*allowed, *standard, Path(python)))),
             'historical business/source/target IO denied: ' + str(path))

    def opened(path, flags, mode=0o777, *, dir_fd=None):
        full = literal(path, dir_fd)
        need(not flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR | os.O_TRUNC | os.O_APPEND),
             'historical write denied')
        admit(full, directory=bool(flags & os.O_DIRECTORY))
        fd = old_open(path, flags, mode, dir_fd=dir_fd)
        fd_paths[fd] = full
        return fd

    def closed(fd):
        fd_paths.pop(fd, None)
        return old_close(fd)

    def duplicated(fd):
        copied = old_dup(fd)
        fd_paths[copied] = literal(fd)
        return copied

    def stated(path, *, dir_fd=None, **kwargs):
        admit(literal(path, dir_fd), directory=True)
        return old_stat(path, dir_fd=dir_fd, **kwargs)

    def stream(path, mode='r', *args, **kwargs):
        if isinstance(path, int):
            return old_io(path, mode, *args, **kwargs)
        full = literal(path)
        admit(full)
        need(not any(c in mode for c in 'wax+'), 'historical stream write denied')
        if full.is_relative_to(OLD_REPO) and str(full.relative_to(OLD_REPO)) in buffers:
            raw = buffers[str(full.relative_to(OLD_REPO))]
            return io.BytesIO(raw) if 'b' in mode else io.StringIO(raw.decode())
        return old_io(path, mode, *args, **kwargs)

    def scan(path='.'):
        full = literal(path)
        need(full.is_relative_to(OLD_REPO), 'historical business directory scan denied')
        return old_scan(path)

    def listing(path='.'):
        full = literal(path)
        need(full.is_relative_to(OLD_REPO), 'historical business directory list denied')
        return old_list(path)

    def code(loader, _name):
        path = Path(loader.path)
        if path.is_relative_to(OLD_REPO):
            relative = str(path.relative_to(OLD_REPO))
            need(relative in buffers, 'unfrozen historical executable denied')
            return compile(buffers[relative], str(path), 'exec', dont_inherit=True)
        return saved_code(loader, _name)

    def no_process(*_args, **_kwargs):
        raise ValueError('FORMAL_HISTORY_STOP: historical subprocess/GH/Native denied')

    try:
        os.open, os.close, os.dup, os.stat = opened, closed, duplicated, stated
        io.open = builtins.open = stream
        os.scandir, os.listdir, subprocess.Popen = scan, listing, no_process
        importlib.machinery.SourceFileLoader.get_code = code
        sys.dont_write_bytecode = True
        yield buffers
    finally:
        os.open, os.close, os.dup, os.stat = old_open, old_close, old_dup, old_stat
        io.open, builtins.open = old_io, old_builtin
        os.scandir, os.listdir, subprocess.Popen = old_scan, old_list, old_popen
        importlib.machinery.SourceFileLoader.get_code = saved_code
        sys.dont_write_bytecode = saved_bytecode
        sys.path[:] = saved_path
        for name in list(sys.modules):
            if name.startswith(prefixes):
                sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


def _replay_historical(accepted):
    plan = accepted['bundle']['plan']
    with _historical_view(plan['source_tree'], plan['runtime']['python']):
        name = 'p17_m2_input_continuation'
        spec = importlib.util.spec_from_file_location(name, OLD_REPO / 'scripts' / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        old = module.profile('independent', OLD_IDENTITY)
        serializer = module.profile('control', OLD_IDENTITY).base()
        decoded = serializer.evidence_json(accepted, decode=True)
        old.audit_certificate(decoded['bundle'], trusted_tool_events=decoded['events'])


def verify_prior_public(prior, bundle_raw, actual_raw):
    """Require exact admitted bytes and all original checks; never a producer PASS."""
    need(type(prior) is dict and prior in (
        expected_prior(), expected_prior(R0_EVIDENCE), expected_prior(CATALOG_EVIDENCE),
        expected_prior(CYCLE_EVIDENCE), expected_prior(CYCLE_R1_EVIDENCE),
        expected_prior(CYCLE_FILING_EVIDENCE))
         and type(prior.get('member_count')) is int, 'fixed prior_public differs')
    need(type(bundle_raw) is bytes and type(actual_raw) is bytes
         and 0 < len(bundle_raw) <= CAP and 0 < len(actual_raw) <= CAP
         and sha(bundle_raw) == BUNDLE_SHA and sha(actual_raw) == ACTUAL_SHA,
         'prior public raw buffer/SHA differs')
    key = sha(canonical(prior))
    if key in _VERIFIED:
        return deepcopy(_VERIFIED[key])
    accepted, actual = parse(bundle_raw), parse(actual_raw)
    need(type(accepted) is dict and set(accepted) == {'bundle', 'events'},
         'prior complete public buffer required')
    bundle, plan = accepted['bundle'], accepted['bundle']['plan']
    need(plan['execution_identity'] == OLD_IDENTITY and plan['root'] == OLD_ROOT
         and plan['runtime']['cwd'] == str(OLD_REPO)
         and plan['scope'] == 'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY'
         and plan['formal_authority'] is False and sha(canonical(plan)) == PLAN_SHA
         and type(plan['source_tree']) is dict and len(plan['source_tree']) == 74
         and sha(canonical(plan['source_tree'])) == TREE_SHA
         and bundle['version_id'] == VERSION and len(bundle['manifest']['members']) == 1071
         and set(bundle['roles']) == set(ROLES)
         and set(accepted['events']) == {*ROLES, 'final-filing', 'lease-release'},
         'prior identity/plan/tree/version/inventory differs')
    argv = [plan['runtime']['python'], '-I', str(OLD_REPO / 'scripts/staged_input_control.py'),
            'certify-rehearsal', '--root', OLD_ROOT, '--plan-sha', PLAN_SHA,
            '--role', 'certificate']
    first, last, stdout = _terminal(actual, argv)
    expected = dict(scope=plan['scope'], formal_authority=False, source_input_accepted=False,
                    formal_or_scientific_admission=False, B_C_admission=False,
                    member_count=1071, version_id=VERSION)
    need(stdout == canonical(expected)
         and first >= max(_milliseconds(row['end_seconds'])
                          for events in accepted['events'].values() for row in events)
         and last <= plan['whole_end_ms'], 'prior certificate original return differs')
    _replay_historical(accepted)
    result = dict(public_end_ms=last, public_start_ms=first, public_plan=plan,
                  source_tree_sha256=TREE_SHA, member_count=1071, version_id=VERSION,
                  historical_identity=OLD_IDENTITY, historical_main=OLD_MAIN,
                  new_source_reads=0, new_named_roles=0)
    _VERIFIED[key] = deepcopy(result)
    return result


MODULE_SOURCE_SHA256 = sha(Path(__file__).read_bytes())
