from __future__ import annotations

import copy
from importlib import resources

from dbetto import AttrsDict, TextDB


class PublicMetadataProxy:
    """Provides proxies to transparently replace legend hardware metadata with sample data."""

    def __init__(self):
        dummy = TextDB(resources.files("pygeomhades") / "configs" / "dummy_geom")

        self.hardware = AttrsDict({"detectors": {"germanium": {"diodes": _DiodeProxy(dummy)}}})


class _DiodeProxy:
    def __init__(self, dummy_detectors: TextDB):
        self.dummy_detectors = dummy_detectors

    def __getitem__(self, det_name: str) -> AttrsDict:
        det = self.dummy_detectors[det_name[0] + "99000A"]
        m = copy.copy(det)
        m.name = det_name
        m.production.order = 0
        m.production.slice = "A"
        return m
