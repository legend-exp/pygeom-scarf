from __future__ import annotations


def test_cli():
    from pygeomscarf.cli import _parse_cli_args

    args, _config = _parse_cli_args([])
    assert args is not None
