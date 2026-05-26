from __future__ import annotations

import math

from pyg4ometry.geant4 import Registry, solid

TWO_PI = 2 * math.pi
COPLANAR_SEPARATION_MM = 0.01

PEN_ENCLOSURES = {
    "bege": {
        "body_outer_r_mm": 38.5,
        "body_inner_r_mm": 37.0,
        "body_h_mm": 33.0,
        "flange_outer_r_mm": 44.5,
        "flange_inner_r_mm": 33.75,
        "flange_t_mm": 1.5,
        "cap_t_mm": 1.5,
        "z_offset_mm": 16.0,
    },
    "icpc": {
        "body_outer_r_mm": 40.5,
        "body_inner_r_mm": 39.0,
        "body_h_mm": 62.0,
        "flange_outer_r_mm": 44.5,
        "flange_inner_r_mm": 28.0,
        "flange_t_mm": 1.5,
        "cap_t_mm": 1.5,
        "borehole_r_mm": 5.0,
        "borehole_h_mm": 32.0,
        "z_offset_mm": 32.5,
    },
}


def build_pen_polycone(
    name: str,
    *,
    body_outer_r_mm: float,
    body_inner_r_mm: float,
    body_h_mm: float,
    flange_outer_r_mm: float,
    flange_inner_r_mm: float,
    flange_t_mm: float,
    cap_t_mm: float,
    borehole_r_mm: float | None = None,
    borehole_h_mm: float | None = None,
    registry: Registry,
    **_: object,
) -> solid.Union:
    """Build the PEN enclosure solid as a boolean union of cylindrical shells.

    The enclosure consists of a main cylindrical shell, top and bottom annular
    flanges, top and bottom solid caps, and optionally a borehole plug for ICPC
    detectors.

    Parameters
    ----------
    name
        Base name for all sub-solids added to the registry.
    body_outer_r_mm
        Outer radius of the main cylindrical shell in mm.
    body_inner_r_mm
        Inner radius of the main cylindrical shell in mm.
    body_h_mm
        Height of the main cylindrical shell in mm.
    flange_outer_r_mm
        Outer radius of the top and bottom flanges in mm.
    flange_inner_r_mm
        Inner radius of the top and bottom flanges in mm.
    flange_t_mm
        Thickness of each flange in mm.
    cap_t_mm
        Thickness of the top and bottom solid caps in mm.
    borehole_r_mm
        Radius of the ICPC borehole plug in mm. If None, no plug is added.
    borehole_h_mm
        Height of the ICPC borehole plug in mm. If None, no plug is added.
    registry
        The pyg4ometry registry to add all solids to.
    **_
        Absorbs extra keys from PEN_ENCLOSURES (e.g. z_offset_mm).
    """
    flange_half_thickness = flange_t_mm / 2.0
    cap_half_thickness = cap_t_mm / 2.0
    body_half_height = body_h_mm / 2.0

    body = solid.Tubs(
        f"{name}_body",
        body_inner_r_mm,
        body_outer_r_mm,
        body_h_mm,
        0,
        TWO_PI,
        registry=registry,
        lunit="mm",
    )

    flange_top = solid.Tubs(
        f"{name}_flange_top",
        flange_inner_r_mm,
        flange_outer_r_mm,
        flange_half_thickness,
        0,
        TWO_PI,
        registry=registry,
        lunit="mm",
    )

    flange_bot = solid.Tubs(
        f"{name}_flange_bot",
        flange_inner_r_mm,
        flange_outer_r_mm,
        flange_half_thickness,
        0,
        TWO_PI,
        registry=registry,
        lunit="mm",
    )

    cap_top = solid.Tubs(
        f"{name}_cap_top",
        0,
        body_outer_r_mm,
        cap_half_thickness,
        0,
        TWO_PI,
        registry=registry,
        lunit="mm",
    )

    cap_bot = solid.Tubs(
        f"{name}_cap_bot",
        0,
        body_outer_r_mm,
        cap_half_thickness,
        0,
        TWO_PI,
        registry=registry,
        lunit="mm",
    )

    shell = solid.Union(
        f"{name}_u_top",
        body,
        flange_top,
        [[0, 0, 0], [0, 0, body_half_height + flange_half_thickness + COPLANAR_SEPARATION_MM]],
        registry,
    )

    shell = solid.Union(
        f"{name}_u_bot",
        shell,
        flange_bot,
        [[0, 0, 0], [0, 0, -body_half_height - flange_half_thickness - COPLANAR_SEPARATION_MM]],
        registry,
    )

    shell = solid.Union(
        f"{name}_u_cap_top",
        shell,
        cap_top,
        [[0, 0, 0], [0, 0, body_half_height + flange_t_mm + cap_half_thickness + COPLANAR_SEPARATION_MM]],
        registry,
    )

    shell = solid.Union(
        f"{name}_u_cap_bot",
        shell,
        cap_bot,
        [[0, 0, 0], [0, 0, -body_half_height - flange_t_mm - cap_half_thickness - COPLANAR_SEPARATION_MM]],
        registry,
    )

    if borehole_r_mm is not None and borehole_h_mm is not None:
        borehole_half_height = borehole_h_mm / 2.0

        borehole_plug = solid.Tubs(
            f"{name}_borehole_plug",
            0,
            borehole_r_mm,
            borehole_half_height,
            0,
            TWO_PI,
            registry=registry,
            lunit="mm",
        )

        shell = solid.Union(
            f"{name}_u_borehole",
            shell,
            borehole_plug,
            [
                [0, 0, 0],
                [
                    0,
                    0,
                    -body_half_height
                    - flange_t_mm
                    - cap_t_mm
                    + borehole_half_height
                    + COPLANAR_SEPARATION_MM,
                ],
            ],
            registry,
        )

    return shell


def build_pen_enclosure(detector_type: str, registry: Registry) -> solid.Union:
    """Build the PEN enclosure solid for a given detector type.

    Parameters
    ----------
    detector_type
        The detector type, must be one of the keys in PEN_ENCLOSURES.
    registry
        The pyg4ometry registry to add all solids to.
    """
    if detector_type not in PEN_ENCLOSURES:
        msg = f"Unknown detector type '{detector_type}'. Available: {list(PEN_ENCLOSURES)}"
        raise KeyError(msg)

    return build_pen_polycone(
        detector_type,
        registry=registry,
        **PEN_ENCLOSURES[detector_type],
    )
