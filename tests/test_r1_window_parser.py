"""Preserve the JSON admission boundary on dense, partially transcribed labels."""
import math
import runpy
from pathlib import Path

import pytest

parse = runpy.run_path(str(Path(__file__).parents[1] / "scripts/p17_m2_input_export.py"))["parse"]


@pytest.mark.parametrize("raw", [b"1e999", b'{"ignored":[[1e999]]}', b'{"x":1,"x":2}',
                                 b'{"ignored":NaN}', b"[" * 65 + b"0" + b"]" * 65])
def test_dense_parser_rejects_invalid_or_unbounded_values(raw):
    with pytest.raises(ValueError):
        parse(raw)


def test_dense_parser_preserves_signed_zero_and_depth_boundary():
    assert math.copysign(1, parse(b"[-0.0]")[0]) == -1
    assert parse(b"[" * 64 + b"1" + b"]" * 64)
