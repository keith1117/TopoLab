"""Independent, bounded observations of the newly admitted public metadata.

The caller admits a literal staged source and prebound candidate/index first.
This module neither discovers a source nor executes a registration/input role.
"""

import hashlib
import os
import re
import stat
from copy import deepcopy
from pathlib import Path

CANDIDATE_SHA256 = '2a30ad2fb1c43aa42c7edbcaa3b2affe7a9e70a449a6a064a51085f3f57e2357'
INDEX_SHA256 = '185ae72128ff9dcb869ebf2697c2aff09a46c5821547b4d29dd88d187ca445af'
PHYSICAL = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns')
POINT = (*PHYSICAL, 'st_uid', 'st_nlink', 'st_mode')
OBSERVATIONS = ('declared', 'before', 'after', 'closing')
ROW_KEYS = {'path', 'physical', 'sha256', *OBSERVATIONS}
REFERENCE = 'b4-30-z-reflection-repair-v2/sentinel/reference/'
SPECS = (
    (REFERENCE + 'progress.json', 1048576),
    (REFERENCE + 'summary.json', 1048576),
    *((f'b4-5-weighted-terminal/fit/units/{i:04d}.json', 32768) for i in range(3)),
    *((REFERENCE + f'units/{i:04d}.json', 32768) for i in range(18)),
)


def need(ok, reason):
    if not ok:
        raise ValueError('STAGED_INDEPENDENT_STOP: ' + reason)


def metadata_specs():
    """Independent derivation: two reference roots, three W and18 reference units."""
    return [{'path': name, 'max_bytes': cap} for name, cap in SPECS]


def _expectations(expected):
    need(type(expected) is dict and set(expected) == {name for name, _ in SPECS},
         'exact23 prebound paths required')
    answer = {}
    for name, cap in SPECS:
        pair = expected[name]
        need(type(pair) in (tuple, list) and len(pair) == 2,
             'prebound size/SHA pair required: ' + name)
        size, digest = pair
        need(type(size) is int and 0 < size <= cap
             and type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest),
             'bounded exact size/SHA required: ' + name)
        answer[name] = (size, digest)
    return answer


def _point(info):
    return {key: getattr(info, key) for key in POINT}


def _file(info, size):
    need(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
         and info.st_nlink == 1 and info.st_size == size,
         'owned regular single-link exact-size file required')


def _identity(info):
    return info.st_dev, info.st_ino, info.st_mode, info.st_uid


def _directory(info):
    return (*_identity(info), info.st_nlink, info.st_mtime_ns, info.st_ctime_ns)


def _open_root(source):
    """Open every literal ancestor without following a link; retain its identity."""
    need(isinstance(source, Path) and source.is_absolute()
         and '..' not in source.parts and not str(source).startswith('//'),
         'literal absolute source path required')
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    chain = [_identity(os.fstat(directory))]
    try:
        for part in source.parts[1:]:
            declared = os.stat(part, dir_fd=directory, follow_symlinks=False)
            need(stat.S_ISDIR(declared.st_mode), 'nofollow source directory required')
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            try:
                current = os.fstat(child)
                need(_identity(declared) == _identity(current),
                     'source directory changed during open')
            except BaseException:
                os.close(child)
                raise
            os.close(directory)
            directory = child
            chain.append(_identity(current))
        need(os.fstat(directory).st_uid == os.getuid(), 'source owner differs')
        return directory, chain
    except BaseException:
        os.close(directory)
        raise


def _parent(root, name):
    directory = os.dup(root)
    chain = [_directory(os.fstat(directory))]
    try:
        for part in Path(name).parts[:-1]:
            declared = os.stat(part, dir_fd=directory, follow_symlinks=False)
            need(stat.S_ISDIR(declared.st_mode) and declared.st_uid == os.getuid(),
                 'owned nofollow metadata directory required')
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            try:
                current = os.fstat(child)
                need(_directory(declared) == _directory(current),
                     'metadata directory changed during open')
            except BaseException:
                os.close(child)
                raise
            os.close(directory)
            directory = child
            chain.append(_directory(current))
        return directory, chain
    except BaseException:
        os.close(directory)
        raise


def scan(source: Path, expected: dict, *, availability: bool):
    """Observe exactly23 prebound files; availability opens/stat only, never reads."""
    need(type(availability) is bool, 'availability must be an exact bool')
    expected = _expectations(expected)
    root, root_chain = _open_root(source)
    original_root = _directory(os.fstat(root))
    rows = []
    current = None
    try:
        for name, cap in SPECS:
            current = {'path': name, 'sha256': None}
            size, digest = expected[name]
            parent, parents = _parent(root, name)
            try:
                leaf = Path(name).name
                declared = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
                current['declared'] = _point(declared)
                _file(declared, size)
                descriptor = os.open(leaf, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                                     dir_fd=parent)
                try:
                    before = os.fstat(descriptor)
                    current['before'] = _point(before)
                    _file(before, size)
                    need(_point(before) == _point(declared)
                         and before.st_ctime_ns == declared.st_ctime_ns,
                         'file changed before read')
                    actual_sha = None
                    if not availability:
                        sha, count = hashlib.sha256(), 0
                        while True:
                            chunk = os.read(descriptor, min(65536, cap + 1 - count))
                            if not chunk:
                                break
                            count += len(chunk)
                            need(count <= cap and count <= size, 'file byte cap exceeded')
                            sha.update(chunk)
                        need(count == size, 'real EOF/declared byte count differs')
                        actual_sha = sha.hexdigest()
                        current['sha256'] = actual_sha
                        need(actual_sha == digest, 'prebound SHA differs')
                    after = os.fstat(descriptor)
                    current['after'] = _point(after)
                    _file(after, size)
                    need(_point(after) == _point(before)
                         and after.st_ctime_ns == before.st_ctime_ns,
                         'file changed during read')
                    current_root, current_chain = _open_root(source)
                    try:
                        need(current_chain == root_chain
                             and _directory(os.fstat(current_root)) == original_root,
                             'current source directory differs')
                        closing_parent, closing_parents = _parent(current_root, name)
                        try:
                            need(closing_parents == parents
                                 and _directory(os.fstat(parent)) == parents[-1],
                                 'current metadata directory differs')
                            closing = os.stat(leaf, dir_fd=closing_parent, follow_symlinks=False)
                            current['closing'] = _point(closing)
                            _file(closing, size)
                            need(_point(closing) == _point(after)
                                 and closing.st_ctime_ns == after.st_ctime_ns,
                                 'current metadata path differs')
                        finally:
                            os.close(closing_parent)
                    finally:
                        os.close(current_root)
                    rows.append({'path': name,
                                 'physical': {key: getattr(after, key) for key in PHYSICAL},
                                 'declared': _point(declared), 'before': _point(before),
                                 'after': _point(after), 'closing': _point(closing),
                                 'sha256': actual_sha})
                    current = None
                finally:
                    os.close(descriptor)
            finally:
                os.close(parent)
        return rows
    except BaseException as error:
        error.binding_prefix = deepcopy(rows + ([] if current is None else [current]))
        raise
    finally:
        os.close(root)


def _rows(expected, rows, availability):
    need(type(rows) is list and len(rows) == 23, 'exact23 observation rows required')
    for (name, _), row in zip(SPECS, rows, strict=True):
        need(type(row) is dict and set(row) == ROW_KEYS and row['path'] == name,
             'ordered unique observation path/fields differ')
        physical = row['physical']
        need(type(physical) is dict and set(physical) == set(PHYSICAL)
             and all(type(physical[key]) is int for key in PHYSICAL)
             and physical['st_dev'] >= 0 and physical['st_ino'] > 0
             and physical['st_mtime_ns'] >= 0 and physical['st_size'] == expected[name][0],
             'physical exact integer tuple differs')
        previous = None
        for key in OBSERVATIONS:
            point = row[key]
            need(type(point) is dict and set(point) == set(POINT)
                 and all(type(point[k]) is int for k in POINT)
                 and {k: point[k] for k in PHYSICAL} == physical
                 and point['st_uid'] == os.getuid() and point['st_nlink'] == 1
                 and 0 <= point['st_mode'] <= 0o177777 and stat.S_ISREG(point['st_mode'])
                 and (previous is None or point == previous),
                 'original observation point/owner/type/identity differs')
            previous = point
        need(row['sha256'] is None if availability else row['sha256'] == expected[name][1],
             'availability/read SHA differs')
    return rows


def compare(expected, availability_a, availability_b, producer, independent):
    """Accept complete original observations only, never fill a missing point."""
    expected = _expectations(expected)
    groups = [_rows(expected, rows, is_availability) for rows, is_availability in (
        (availability_a, True), (availability_b, True), (producer, False), (independent, False))]
    for index in range(23):
        baseline = groups[0][index]
        need(all(all(row[index][key] == baseline[key] for key in ('physical', *OBSERVATIONS))
                 for row in groups[1:]), 'independent availability/reader observations disagree')
    return deepcopy(independent)
