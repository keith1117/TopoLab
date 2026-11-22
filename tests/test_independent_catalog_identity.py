"""B3 catalog identity uses deterministic public definitions, never artifact IO."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'independent_catalog_subject', REPO/'scripts/p17_m2_input_export_independent.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.fixture(scope='module')
def frozen_rich_catalog():
    # This generator contains only independently published TopoLab case metadata.
    # It performs no FEM, label/checkpoint read, artifact access or fitting.
    from topolab.b3_catalog import build_b3_case_catalog

    return build_b3_case_catalog().model_dump(mode='json')


def projected_independently(catalog):
    return dict(catalog_version=catalog['catalog_version'], entries=[dict(
        case_id=e['case']['case_id'], role=e['role'], source_case_id=e['source_case_id'],
        training_sets=e['training_sets']) for e in catalog['entries']])


def test_historical_public_catalog_and_unlinked_label_bytes_remain_frozen():
    catalog = dict(catalog_version='topolab.b3.catalog.v1', entries=[
        checker.public_label((12, 6, 3) if i < 432 else (24, 12, 6), i+1)['entry']
        for i in range(528)])
    raw = checker.canonical(catalog)
    assert len(raw) == 190760
    assert all(e['source_case_id'] is None for e in catalog['entries'])
    assert checker.digest(raw) == checker.PUBLIC_FIXTURE_CATALOG_HASH == (
        'ed724475bb260ea37ad7664d47833af38fe0862045ffa0b68a2dc1380686c594')
    assert checker.PUBLIC_FIXTURE_CATALOG_HASH != checker.CATALOG_HASH
    # Exact old PUBLIC raw is a separate schema boundary, never a formal catalog.
    with pytest.raises(ValueError, match='source link'):
        checker.catalog_identity_bytes(catalog)


def test_full_public_rich_catalog_matches_frozen_identity_without_mutating_raw(frozen_rich_catalog):
    rich = deepcopy(frozen_rich_catalog)
    before = checker.canonical(rich)
    identity = checker.catalog_identity_bytes(rich)
    assert checker.digest(identity) == (
        '441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c')
    assert identity == checker.canonical(projected_independently(rich))
    assert checker.digest(before) != checker.digest(identity)
    assert checker.canonical(rich) == before
    assert len(rich['entries']) == 752
    assert sum(e['role'] == 'train' for e in rich['entries']) == 528


@pytest.mark.parametrize('field', ['role', 'source_case_id', 'training_sets', 'case_id'])
def test_identity_changes_cannot_keep_frozen_pin(frozen_rich_catalog, field):
    rich = deepcopy(frozen_rich_catalog)
    entry = next(e for e in rich['entries'] if e['role'] == 'train')
    if field == 'role':
        entry.update(role='final_id', source_case_id=None, training_sets=[])
    elif field == 'source_case_id':
        entry[field] = 'tlcase-v1-'+'0'*64
    elif field == 'training_sets':
        entry[field] = ['expanded'] if entry[field] != ['expanded'] else ['specialist']
    else:
        entry['case']['case_id'] = 'tlcase-v1-'+'0'*64
    try:
        raw = checker.catalog_identity_bytes(rich)
    except ValueError:
        return
    assert checker.digest(raw) != checker.CATALOG_HASH


def test_nonidentity_content_stays_in_full_manifest_and_raw_integrity(frozen_rich_catalog):
    rich = deepcopy(frozen_rich_catalog)
    before = checker.canonical(rich)
    identity = checker.catalog_identity_bytes(rich)
    rich['entries'][0]['case']['problem']['material']['solid_modulus'] = 999.0
    assert checker.catalog_identity_bytes(rich) == identity
    assert checker.canonical(rich) != before


@pytest.mark.parametrize('damage', ['version', 'extra-root', 'duplicate', 'reverse', 'entry-fields',
    'case-type', 'role', 'members-order', 'members-duplicate', 'members-type', 'unlinked-train',
    'nontrain-members'])
def test_catalog_schema_and_identity_order_are_enforced(frozen_rich_catalog, damage):
    rich = deepcopy(frozen_rich_catalog)
    train = next(e for e in rich['entries'] if e['role'] == 'train')
    if damage == 'version':
        rich['catalog_version'] = 'other'
    elif damage == 'extra-root':
        rich['ignored'] = True
    elif damage == 'duplicate':
        rich['entries'].append(deepcopy(rich['entries'][0]))
    elif damage == 'reverse':
        rich['entries'].reverse()
    elif damage == 'entry-fields':
        train['ignored'] = True
    elif damage == 'case-type':
        train['case'] = train['case']['case_id']
    elif damage == 'role':
        train['role'] = 'unknown'
    elif damage == 'members-order':
        train['training_sets'] = ['specialist', 'base']
    elif damage == 'members-duplicate':
        train['training_sets'] = ['base', 'base']
    elif damage == 'members-type':
        train['training_sets'] = 'base'
    elif damage == 'unlinked-train':
        train['source_case_id'] = None
    else:
        entry = next(e for e in rich['entries'] if e['role'] != 'train')
        entry['training_sets'] = ['base']
    with pytest.raises(ValueError):
        checker.catalog_identity_bytes(rich)
