from __future__ import annotations

import copy

from dbetto import AttrsDict, TextDB
from legendtestdata import LegendTestData


class PublicMetadataProxy:
    """Provides proxies to transparently replace legend hardware metadata with sample data."""

    def __init__(self):
        ldata = LegendTestData()

        dummy = TextDB(ldata.get_path("legend/metadata/hardware/detectors/germanium/diodes"))

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
