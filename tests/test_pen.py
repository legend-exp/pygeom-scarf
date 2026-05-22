from __future__ import annotations

import pygeomtools.geometry
import pytest
from pyg4ometry import geant4
from pyg4ometry.geant4 import LogicalVolume, PhysicalVolume, Registry, solid

from pygeomscarf.models.enclosures import (
    PEN_ENCLOSURES,
    build_pen_enclosure,
    build_pen_polycone,
)


def _make_world(reg):
    """Helper: minimal world volume to place enclosures in."""
    world_s = solid.Box("world_solid", 400, 400, 400, reg, "mm")
    world_l = LogicalVolume(world_s, geant4.MaterialPredefined("G4_Galactic"), "world_lv", reg)
    reg.setWorld(world_l)
    return world_l


@pytest.mark.parametrize("det_type", ["bege", "icpc"])
def test_pen_polycone_builds(det_type):
    reg = Registry()
    s = build_pen_polycone(det_type, registry=reg, **PEN_ENCLOSURES[det_type])
    assert s is not None
    assert f"{det_type}_solid" in reg.solidDict


@pytest.mark.parametrize("det_type", ["bege", "icpc"])
def test_pen_enclosure_wrapper(det_type):
    reg = Registry()
    assert build_pen_enclosure(det_type, reg) is not None


@pytest.mark.parametrize(
    ("det_type", "det_r", "det_h"),
    [
        ("bege", 37.0, 32.0),
        ("icpc", 39.0, 65.0),
    ],
)
def test_pen_fits_detector(det_type, det_r, det_h):
    p = PEN_ENCLOSURES[det_type]
    # wall thickness must be positive
    assert p["outer_r_mm"] > p["inner_r_mm"]
    # inner radius must match detector radius (tight fit by design)
    assert p["inner_r_mm"] <= det_r
    # enclosure wraps detector partially — cavity just needs to be positive
    assert p["height_mm"] - 2 * p["cap_thickness_mm"] > 0


def test_pen_cap_too_thick_raises():
    reg = Registry()
    with pytest.raises(ValueError, match="cap_thickness_mm"):
        build_pen_polycone(
            "bad",
            inner_r_mm=37.5,
            outer_r_mm=39.0,
            height_mm=2.0,
            cap_thickness_mm=1.5,
            face_outer_r_mm=50.0,
            face_bore_r_mm=33.75,
            registry=reg,
        )


def test_pen_unknown_type_raises():
    with pytest.raises(KeyError):
        build_pen_enclosure("unknown", Registry())


@pytest.mark.parametrize("det_type", ["bege", "icpc"])
def test_pen_registry_sanity(det_type):
    """Place enclosure in a world volume and run pygeomtools sanity check."""
    reg = Registry()
    world_l = _make_world(reg)

    pen_s = build_pen_polycone(det_type, registry=reg, **PEN_ENCLOSURES[det_type])
    pen_l = LogicalVolume(pen_s, geant4.MaterialPredefined("G4_POLYETHYLENE"), f"{det_type}_pen_lv", reg)
    PhysicalVolume([0, 0, 0], [0, 0, 0], pen_l, f"{det_type}_pen_pv", world_l, reg)

    pygeomtools.geometry.check_registry_sanity(reg, reg)
