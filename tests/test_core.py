from __future__ import annotations

import os

public_geom = os.getenv("LEGEND_METADATA", "") == ""


def test_import():
    import pygeomscarf  # noqa: F401
