from __future__ import annotations

import copy

from dbetto import AttrsDict, TextDB
from legendtestdata import LegendTestData


class PublicMetadataProxy:
    """Provides proxies to transparently replace legend hardware metadata with sample data."""

    def __init__(self, dets):
        ldata = LegendTestData()
        dummy = TextDB(ldata.get_path("legend/metadata/hardware/detectors/germanium/diodes"))
        self.hardware = AttrsDict(
            {"detectors": {"germanium": {"diodes": {det: diode_proxy(det, dummy) for det in dets}}}}
        )


def diode_proxy(det_name: str, dummy_detectors: TextDB) -> AttrsDict:
    det = dummy_detectors[det_name[0] + "99000A"]
    m = copy.copy(det)
    m.name = det_name
    m.production.order = 0
    m.production.slice = "A"

    return m
