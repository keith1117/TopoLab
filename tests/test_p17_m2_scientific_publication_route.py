"""Publication checks use the acquisition's frozen authority before any admission."""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
PARENT = '/Users/keith1117/Library/Application Support/TopoLab-custody/'
GENERATIONS = {
    5: PARENT + 'p17-m2-local-input-version-v5-hash-bound-20261026',
    6: PARENT + 'p17-m2-local-input-version-v6-hash-bound-20261026',
    7: PARENT + 'p17-m2-local-input-version-v7-hash-bound-20261028',
}


def publication(monkeypatch):
    path = REPO / 'scripts/p17_m2_scientific_orchestration.py'
    spec = importlib.util.spec_from_file_location('scientific_publication_route_test', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    control = module.load('p17_m2_source_acquisition_control')
    observed = []
    monkeypatch.setattr(control, 'activation_readiness',
                        lambda authority: observed.append(authority) or {'main': '1' * 40})
    monkeypatch.setattr(module, 'scientific_runtime', lambda: {'public': 'memory-only seam'})
    monkeypatch.setattr(module, 'load', lambda name: control)
    return module, control, observed


@pytest.mark.parametrize('version', [5, 6, 7])
def test_publication_selects_exact_frozen_acquisition_authority(monkeypatch, version):
    module, control, observed = publication(monkeypatch)
    contract = {'acquisition': {'content_root': GENERATIONS[version] + '/content'},
                'source_freeze': {}}
    result = module.publication_metadata(contract, '2' * 64, 'resource-preflight')
    assert result['metadata_only'] is True
    assert len(observed) == 1
    if version == 7:
        assert observed[0]['execution_identity'] == (
            'topolab.v2.p17-m2-hash-bound-source-acquisition.v3'
        )
    else:
        assert observed[0]['execution_identity'] == (
            'topolab.v2.p17-m2-hash-bound-source-acquisition.v2'
        )
    expected = {5: control.FUNDED_AUTHORITY_RAW, 6: control.REMEDY_AUTHORITY_RAW,
                7: control.NEW_AUTHORITY_RAW}[version]
    assert control.base().canonical(observed[0]) == control.base().canonical(
        control.load('p17_m2_input_export').parse(expected))


@pytest.mark.parametrize('content', [
    '/private/tmp/unregistered/content',
    '/private/tmp/' + GENERATIONS[7].split('/')[-1] + '/content',
    GENERATIONS[7] + '/different-leaf',
    GENERATIONS[7] + '/content/',
    GENERATIONS[7] + '/../content',
    'relative/content',
    None,
])
def test_publication_rejects_unregistered_or_malformed_input_before_readiness(
    monkeypatch, content
):
    module, _, observed = publication(monkeypatch)
    with pytest.raises(ValueError):
        module.publication_metadata({'acquisition': {'content_root': content},
                                     'source_freeze': {}}, '2' * 64, 'resource-preflight')
    assert observed == []


@pytest.mark.parametrize('version,missing', [(7, 'NEW_AUTHORITY_RAW'),
                                           (6, 'REMEDY_AUTHORITY_RAW')])
def test_publication_never_falls_back_when_selected_authority_is_missing(
    monkeypatch, version, missing
):
    module, control, observed = publication(monkeypatch)
    monkeypatch.setattr(control, missing, None)
    with pytest.raises(ValueError):
        module.publication_metadata(
            {'acquisition': {'content_root': GENERATIONS[version] + '/content'},
             'source_freeze': {}}, '2' * 64, 'resource-preflight'
        )
    assert observed == []


def test_legacy_metadata_interface_without_acquisition_keeps_original_authority(monkeypatch):
    module, control, observed = publication(monkeypatch)
    module.publication_metadata({'source_freeze': {}}, '2' * 64, 'resource-preflight')
    assert control.base().canonical(observed[0]) == control.base().canonical(
        control.load('p17_m2_input_export').parse(control.FUNDED_AUTHORITY_RAW))
