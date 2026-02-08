from __future__ import annotations

import pyg4ometry.geant4
from legendmeta import LegendMetadata
from pygeomhpges import make_hpge
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.metadata import PublicMetadataProxy
from pygeomscarf.utils import _place_pv


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

    for hpge in hpges:
        name = hpge["name"]
        z_pos = lar_height / 2.0 + hpge["pplus_pos_from_lar_center"]

        hpge_meta = meta.hardware.detectors.germanium.diodes[name]

        if hpge_meta.production.enrichment.val is None:
            hpge_meta["production"]["enrichment"]["val"] = 0.9

        hpge_lv = make_hpge(hpge_meta, reg)
        hpge_lv.pygeom_color_rgba = [1, 1, 1, 1]

        _place_pv(name, hpge_lv, lar_lv, z_pos, reg)

    return reg
