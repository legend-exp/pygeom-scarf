from __future__ import annotations

import numpy as np
import pint
import pyg4ometry.geant4
import pygeomoptics
from legendmeta import LegendMetadata
from pyg4ometry import geant4
from pygeomhpges import make_hpge
from pygeomtools.detectors import RemageDetectorInfo
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.metadata import PublicMetadataProxy
from pygeomscarf.utils import _place_pv

u = pint.get_application_registry()

FIBER_DIM = 1
TPB_THICKNESS_UM = 1


def set_germanium_reflectivity(hpge: geant4.PhysicalVolume, reg: geant4.Registry, lar_name: str = "lar"):
    """Set the reflectivity of the germanium surfaces.

    Parameters
    ----------
    hpge
        The physical volume of the HPGe detector, to set the reflectivity for.
    reg
        The registry to add the reflectivity to.
    lar_name
        The name of the liquid argon physical volume, to set the reflectivity with respect to.

    """
    _to_germanium = geant4.solid.OpticalSurface(
        "surface_to_germanium",
        finish="ground",
        model="unified",
        surf_type="dielectric_metal",
        value=0.3,
        registry=reg,
    )

    pygeomoptics.germanium.pyg4_germanium_attach_reflectivity(_to_germanium, reg)

    lar_pv = reg.physicalVolumeDict[lar_name]
    geant4.BorderSurface(
        "bsurface_lar_ge_" + hpge.name,
        lar_pv,
        hpge,
        _to_germanium,
        reg,
    )
    return reg


def build_fiber_shroud(
    mats: LegendMaterialRegistry,
    reg: geant4.Registry,
    shroud_height: float = 1000,
    shroud_radius: float = 115,
):
    """Build the fiber shroud.

    Parameters
    ----------
    shroud_height
        The height of the fiber shroud in mm.
    shroud_radius
        The radius of the fiber shroud in mm.
    reg
        The registry to add the fiber shroud to.
    """
    coating_dim = FIBER_DIM + 2 * TPB_THICKNESS_UM / 1e3

    coating = geant4.solid.Tubs(
        "tpb_coating",
        shroud_radius - coating_dim / 2,
        shroud_radius + coating_dim / 2,
        shroud_height,
        0,
        2 * np.pi,
        reg,
        "mm",
        nslice=720,
    )

    coating_lv = geant4.LogicalVolume(coating, mats.tpb_on_fibers, "tpb_coating", reg)

    core = geant4.solid.Tubs(
        "fiber_core",
        shroud_radius - FIBER_DIM / 2,
        shroud_radius + FIBER_DIM / 2,
        shroud_height,
        0,
        2 * np.pi,
        reg,
        "mm",
        nslice=720,
    )
    core_lv = geant4.LogicalVolume(core, mats.ps_fibers, "fiber_core", reg)

    # place the core
    _place_pv("fiber_core", core_lv, coating_lv, 0, reg)

    reg.physicalVolumeDict["fiber_core"].pygeom_active_detector = RemageDetectorInfo("optical", 100, {})

    coating_lv.pygeom_color_rgba = [0, 1, 0.165, 0.07]
    return coating_lv


def set_tpb_surface(tpb_name: str, lar_name: str, reg: geant4.Registry):
    """Set the tpb optical properties.

    Parameters
    ----------
    tpb_name
        The name of the TPB physical volume, to set the optical properties for.
    lar_name
        The name of the liquid argon physical volume, to set the optical properties with respect to
    reg
        The registry to add the optical properties to.
    """
    lar_to_tpb = geant4.solid.OpticalSurface(
        "surface_lar_to_tpb",
        finish="ground",
        model="unified",
        surf_type="dielectric_dielectric",
        value=0.3,  # rad. converted from 0.5, probably a GLISUR smoothness parameter, in MaGe.
        registry=reg,
    )

    lar_pv = reg.physicalVolumeDict[lar_name]
    tpb_pv = reg.physicalVolumeDict[tpb_name]

    geant4.BorderSurface(
        "bsurface_lar_tpb_" + tpb_name,
        lar_pv,
        tpb_pv,
        lar_to_tpb,
        reg,
    )

    geant4.BorderSurface(
        "bsurface_tpb_lar_" + tpb_name,
        tpb_pv,
        lar_pv,
        lar_to_tpb,
        reg,
    )


def set_fiber_core_surface(tpb_name: str, core_name: str, reg: geant4.Registry):
    """Set the fiber core surface (to make sensitive).

    This is important to allow the fiber core to act as a sensitive detector.

    Parameters
    ----------
    tpb_name
        The name of the TPB physical volume.
    core_name
        The name of the fiber core physical volume.
    reg
        The registry to add the optical properties to.
    """
    _to_fiber_core = geant4.solid.OpticalSurface(
        "surface_to_fiber_core",
        finish="ground",
        model="unified",
        surf_type="dielectric_metal",
        value=0.05,
        registry=reg,
    )
    λ = np.array([100, 280, 310, 350, 400, 435, 505, 525, 595, 670][::-1]) * u.nm

    with u.context("sp"):
        _to_fiber_core.addVecPropertyPint("EFFICIENCY", λ.to("eV"), np.ones_like(λ))
        _to_fiber_core.addVecPropertyPint("REFLECTIVITY", λ.to("eV"), np.zeros_like(λ))

    core_pv = reg.physicalVolumeDict[core_name]
    tpb_pv = reg.physicalVolumeDict[tpb_name]

    geant4.BorderSurface("bsurface_tpb_fiber", tpb_pv, core_pv, _to_fiber_core, reg)


def build_strings(
    lar_lv: pyg4ometry.geant4.LogicalVolume,
    hpges: list,
    mats: LegendMaterialRegistry,
    meta: LegendMetadata | PublicMetadataProxy,
    reg: pyg4ometry.geant4.Registry,
    lar_height: float,
    fiber_shroud: dict | None = None,
) -> pyg4ometry.geant4.Registry:
    """Build the strings and place them into the registry.

    Parameters
    ----------
    lar_lv
        The logical volume of the liquid argon, to place the strings inside.
    hpges
        A mapping containing the HPGe detector information, including their names and positions.

        Should have the following structure:

        .. code-block:: yaml

            - name: "V09999A
                position_from_cryostat_bottom_in_mm: 120
            - name: "V09999B
                position_from_cryostat_bottom_in_mm: 230
    mats
        The material registry to use for constructing the strings.
    meta
        The metadata to use for constructing the strings.
    reg
        The registry to add the strings to.

    fiber_shroud
        A dictionary containing the fiber shroud information, including its mode
        (e.g. "simplified" or "detailed"), height, radius and position from the bottom of the cryostat.
        Should have the following structure:

        .. code-block:: yaml

            mode: "simplified"  # or "detailed"
            height_in_mm: 1200
            radius_in_mm: 200
            center_pos_from_cryostat_bottom_in_mm: 120

    """

    for uid, hpge in enumerate(hpges):
        name = hpge["name"]
        z_pos = lar_height / 2.0 + hpge["pplus_pos_from_lar_center"]

        hpge_meta = meta.hardware.detectors.germanium.diodes[name]

        if hpge_meta.production.enrichment.val is None:
            hpge_meta["production"]["enrichment"]["val"] = 0.9

        hpge_lv = make_hpge(hpge_meta, reg)
        hpge_lv.pygeom_color_rgba = [1, 1, 1, 1]

        _place_pv(name, hpge_lv, lar_lv, z_pos, reg)

        pv = reg.physicalVolumeDict[name]
        pv.pygeom_active_detector = RemageDetectorInfo("germanium", uid, hpge_meta)

        # set reflectivity
        reg = set_germanium_reflectivity(pv, reg, lar_name="lar")

    if fiber_shroud is not None:
        shroud_lv = build_fiber_shroud(
            mats=mats,
            reg=reg,
        )
        _place_pv(
            "fiber_shroud",
            shroud_lv,
            lar_lv,
            lar_height / 2.0 + fiber_shroud["center_pos_from_lar_center"],
            reg,
        )

        set_tpb_surface(tpb_name="fiber_shroud", lar_name="lar", reg=reg)
        set_fiber_core_surface(core_name="fiber_core", tpb_name="fiber_shroud", reg=reg)

    return reg
