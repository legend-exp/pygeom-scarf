from __future__ import annotations

import contextlib
import logging

import dbetto
from git import GitCommandError
from legendmeta import LegendMetadata
from pyg4ometry import geant4
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.cryo import build_cryostat
from pygeomscarf.metadata import PublicMetadataProxy

log = logging.getLogger(__name__)


def construct(
    config: str | dict | None = None,
    public_geometry: bool = False,
    plot_cryostat: bool = False,
) -> geant4.Registry:
    """Construct the SCARF geometry and return the registry containing the world volume.

    Parameters
    ----------
    config
      configuration dictionary (or file containing it) defining relevant
      parameters of the geometry.
    plot_cryostat
        if true, the cryostat will be plotted.
    public_geometry
      if true, uses the public geometry metadata instead of the LEGEND-internal
      legend-metadata.
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
        lmeta = PublicMetadataProxy()

    config = config if config is not None else {}

    reg = geant4.Registry()
    mats = LegendMaterialRegistry(reg)

    # Create the world volume
    world_material = geant4.MaterialPredefined("G4_Galactic")
    world = geant4.solid.Box("world", 20, 20, 20, reg, "m")
    world_lv = geant4.LogicalVolume(world, world_material, "world", reg)
    reg.setWorld(world_lv)

    # build the cryostat
    return build_cryostat(world_lv, reg, mats, plot=plot_cryostat)
