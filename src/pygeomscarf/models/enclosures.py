from pyg4ometry.geant4 import solid
import math

PEN_ENCLOSURES = {

    "bege": dict(
        body_outer_r_mm   = 38.5,
        body_inner_r_mm   = 37.0,
        body_h_mm         = 33.0,

        flange_outer_r_mm = 44.5,
        flange_inner_r_mm = 33.75,
        flange_t_mm       = 1.5,

        cap_t_mm          = 1.5,

        z_offset_mm       = 16.0,   # = bege height / 2 = 32.0 / 2
    ),

    "icpc": dict(
        body_outer_r_mm   = 40.5,
        body_inner_r_mm   = 39.0,
        body_h_mm         = 62.0,

        flange_outer_r_mm = 44.5,
        flange_inner_r_mm = 28.0,
        flange_t_mm       = 1.5,

        cap_t_mm          = 1.5,

        borehole_r_mm     = 5.0,    # icpc geometry.borehole.radius_in_mm
        borehole_h_mm     = 32.0,   # icpc geometry.borehole.depth_in_mm

        z_offset_mm       = 32.5,   # = icpc height / 2 = 65.0 / 2
    ),
}

def build_pen_polycone(
    name,
    *,
    body_outer_r_mm,
    body_inner_r_mm,
    body_h_mm,

    flange_outer_r_mm,
    flange_inner_r_mm,
    flange_t_mm,

    cap_t_mm,

    borehole_r_mm   = None,   # ICPC only
    borehole_h_mm   = None,   # ICPC only

    registry,
    **_,                      # silently absorbs z_offset_mm and any future keys
):

    h   = body_h_mm
    t   = flange_t_mm
    t_c = cap_t_mm

    eps = 0.01

    #
    # Main cylindrical shell
    #

    body = solid.Tubs(
        f"{name}_body",
        body_inner_r_mm,
        body_outer_r_mm,
        h,
        0, 2 * math.pi,
        registry=registry,
        lunit="mm",
    )

    #
    # Top flange
    #

    flange_top = solid.Tubs(
        f"{name}_flange_top",
        flange_inner_r_mm,
        flange_outer_r_mm,
        t / 2.0,
        0, 2 * math.pi,
        registry=registry,
        lunit="mm",
    )

    #
    # Bottom flange
    #

    flange_bot = solid.Tubs(
        f"{name}_flange_bot",
        flange_inner_r_mm,
        flange_outer_r_mm,
        t / 2.0,
        0, 2 * math.pi,
        registry=registry,
        lunit="mm",
    )

    #
    # Top cap
    #

    cap_top = solid.Tubs(
        f"{name}_cap_top",
        0,
        body_outer_r_mm,
        t_c / 2.0,
        0, 2 * math.pi,
        registry=registry,
        lunit="mm",
    )

    #
    # Bottom cap
    #

    cap_bot = solid.Tubs(
        f"{name}_cap_bot",
        0,
        body_outer_r_mm,
        t_c / 2.0,
        0, 2 * math.pi,
        registry=registry,
        lunit="mm",
    )

    #
    # Assemble shell
    #

    shell = solid.Union(
        f"{name}_u_top",
        body, flange_top,
        [[0,0,0], [0, 0, h/2.0 + t/2.0 + eps]],
        registry,
    )

    shell = solid.Union(
        f"{name}_u_bot",
        shell, flange_bot,
        [[0,0,0], [0, 0, -h/2.0 - t/2.0 - eps]],
        registry,
    )

    shell = solid.Union(
        f"{name}_u_cap_top",
        shell, cap_top,
        [[0,0,0], [0, 0, h/2.0 + t + t_c/2.0 + eps]],
        registry,
    )

    shell = solid.Union(
        f"{name}_u_cap_bot",
        shell, cap_bot,
        [[0,0,0], [0, 0, -h/2.0 - t - t_c/2.0 - eps]],
        registry,
    )

    #
    # ICPC borehole plug — solid cylinder reaching up into the bore
    #

    if borehole_r_mm is not None and borehole_h_mm is not None:

        borehole_plug = solid.Tubs(
            f"{name}_borehole_plug",
            0,
            borehole_r_mm,
            borehole_h_mm / 2.0,
            0, 2 * math.pi,
            registry=registry,
            lunit="mm",
        )

        shell = solid.Union(
            f"{name}_u_borehole",
            shell, borehole_plug,
            [[0,0,0], [0, 0, -h/2.0 - t - t_c + borehole_h_mm/2.0 + eps]],
            registry,
        )

    return shell


def build_pen_enclosure(detector_type, registry):

    if detector_type not in PEN_ENCLOSURES:
        raise KeyError(f"Unknown detector type '{detector_type}'")

    return build_pen_polycone(
        detector_type,
        registry=registry,
        **PEN_ENCLOSURES[detector_type],
    )


def place_pen_enclosure(detector_type, pen_lv, mother_lv, registry):
    """
    Place the PEN enclosure logical volume into mother_lv,
    applying the z_offset_mm from the detector's parameter dict.
    """

    z_offset = PEN_ENCLOSURES[detector_type]["z_offset_mm"]

    physical.PhysicalVolume(
        [0, 0, 0],                  # no rotation
        [0, 0, z_offset],           # ← this is where z_offset_mm is actually used
        pen_lv,
        f"{detector_type}_pen_pv",
        mother_lv,
        registry,
    )