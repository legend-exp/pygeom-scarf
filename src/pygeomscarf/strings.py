from __future__ import annotations

import pyg4ometry.geant4
import pygeomoptics
from legendmeta import LegendMetadata
from pyg4ometry import geant4
from pygeomhpges import make_hpge
from pygeomtools.detectors import RemageDetectorInfo
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.metadata import PublicMetadataProxy
from pygeomscarf.utils import _place_pv


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

    return reg
