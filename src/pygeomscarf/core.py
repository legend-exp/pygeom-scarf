from __future__ import annotations

import contextlib
import logging
from importlib import resources

import dbetto
from git import GitCommandError
from legendmeta import LegendMetadata
from pyg4ometry import geant4
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.cavern import construct_cavern
from pygeomscarf.cryo import build_cryostat
from pygeomscarf.metadata import PublicMetadataProxy
from pygeomscarf.source import build_source
from pygeomscarf.strings import build_strings
from pygeomscarf.utils import merge_configs

log = logging.getLogger(__name__)


def construct(
    config: str | dict | None = None,
    public_geometry: bool = False,
    plot_cryostat: bool = False,
    extra_detectors: dbetto.TextDB | None = None,
) -> geant4.Registry:
    """Construct the SCARF geometry and return the registry containing the world volume.

    Parameters
    ----------
    config
      configuration dictionary (or file containing it) defining relevant
      parameters of the geometry.

      This should have the following structure:

        .. code-block:: yaml

            hpges:
                - name: "V09999A
                    pplus_pos_from_lar_center: 120
                - name: "V09999B
                    pplus_pos_from_lar_center: 230

            source:
                pos_from_lar_center: 150

            fiber_shroud:
                mode: "simplified"  # or "detailed"
                height_in_mm: 1200
                radius_in_mm: 200
                center_pos_from_lar_center: 120
            cavern:
                inner_radius_in_mm: 5000
                outer_radius_in_mm: 12000

        - If the ``hpges`` key is present, the geometry will include HPGe detectors, which will be placed at the specified positions (in mm) from the bottom of the cryostat.
        - The ``source`` key can be used to place a source at a specified position from the bottom of the cryostat.
        - Similarly, the ``fiber_shroud`` key can be used to include a fiber shroud in the geometry, with the specified mode (e.g. "simplified" or "detailed"), height, radius and position from the bottom of the cryostat.

    plot_cryostat
        if true, the cryostat will be plotted.
    public_geometry
      if true, uses the public geometry metadata instead of the LEGEND-internal
      legend-metadata.
    extra_detectors
        If provided, should be a TextDB object containing extra detector metadata, for example detectors not from LEGEND.
    """
    if isinstance(config, str):
        config = dbetto.utils.load_dict(config)

    lmeta = None
    if not public_geometry:
        with contextlib.suppress(GitCommandError):
            lmeta = LegendMetadata(lazy=True)

    # require user action to construct a testdata-only geometry (i.e. to avoid accidental creation of "wrong"
    # geometries by LEGEND members).
    if lmeta is None and not public_geometry:
        msg = "cannot construct geometry from public testdata only, if not explicitly instructed"
        raise RuntimeError(msg)

    if lmeta is None:
        msg = "CONSTRUCTING GEOMETRY FROM PUBLIC DATA ONLY"
        log.warning(msg)

        # get a list of detectors
        hpges = config.get("hpges", []) if config is not None else []
        dets = [
            hpge["name"] for hpge in hpges if extra_detectors is None or hpge["name"] not in extra_detectors
        ]

        lmeta = PublicMetadataProxy(dets)

    det_meta = merge_configs(
        dbetto.AttrsDict(dict(lmeta.hardware.detectors.germanium.diodes)), extra_detectors
    )

    config = config if config is not None else {}

    # extract the dimensions of the cryostat
    cryostat_meta = dbetto.AttrsDict(
        dbetto.utils.load_dict(resources.files("pygeomscarf") / "configs" / "cryostat.yaml")
    )

    hpges = config.get("hpges", {})

    reg = geant4.Registry()
    mats = LegendMaterialRegistry(reg)

    # Create the world volume
    world_material = geant4.MaterialPredefined("G4_Galactic")
    world = geant4.solid.Box("world", 50, 50, 50, reg, "m")
    world_lv = geant4.LogicalVolume(world, world_material, "world", reg)
    reg.setWorld(world_lv)

    # build the cryostat, extract the height of the LAr volume
    # this is used to align the HPGe strings to the center of the lar
    reg = build_cryostat(cryostat_meta, world_lv, reg, mats, plot=plot_cryostat)
    lar_lv = reg.logicalVolumeDict["lar"]

    # the height of the LAr
    lar_height = (
        cryostat_meta.inner.lower.height_in_mm + cryostat_meta.inner.upper.height_in_mm
    ) - cryostat_meta.gas_argon.height_in_mm

    # the offset between the lar volume and the world
    lar_offset = (
        cryostat_meta.inner.lower.thickness_in_mm
        - (cryostat_meta.inner.lower.height_in_mm + cryostat_meta.inner.upper.height_in_mm) / 2.0
    )
    # place the hpge and fibers
    reg = build_strings(
        lar_lv,
        hpges,
        mats,
        det_meta,
        reg,
        lar_height=lar_height,
        fiber_shroud=config.get("fiber_shroud", None),
    )

    # source
    if "source" in config:
        reg = build_source(
            world_lv,
            radius=cryostat_meta.outer.radius_in_mm + cryostat_meta.lead.air_gap_in_mm / 2.0,
            z_pos=config["source"]["pos_from_lar_center"] + lar_height / 2 + lar_offset,
            reg=reg,
        )

    if "cavern" in config:
        reg = construct_cavern(
            world_lv=world_lv,
            mat=mats.rock,
            inner_radius=config["cavern"]["inner_radius_in_mm"],
            outer_radius=config["cavern"]["outer_radius_in_mm"],
            reg=reg,
        )

    return reg
