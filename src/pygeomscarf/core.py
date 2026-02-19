from __future__ import annotations

import contextlib
import logging
from pathlib import Path

import dbetto
import numpy as np
import yaml
from git import GitCommandError
from legendmeta import LegendMetadata
from pyg4ometry import geant4
from pygeomhpges import make_hpge

log = logging.getLogger(__name__)


def construct(
    config: str | dict | Path | None = None,
    public_geometry: bool = False,
) -> geant4.Registry:
    # ------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------
    if isinstance(config, (str, Path)):
        config = dbetto.utils.load_dict(config)

    config = config if config is not None else {}

    # ------------------------------------------------------------
    # Metadata handling
    # ------------------------------------------------------------
    lmeta = None
    if public_geometry:
        with contextlib.suppress(GitCommandError):
            lmeta = LegendMetadata(lazy=True)
        if lmeta is None:
            log.warning("CONSTRUCTING GEOMETRY FROM PUBLIC DATA ONLY")

    # Local dummy geometry path
    local_geom_dir = (
        Path(__file__).parent / "configs" / "dummy_geom"
    )

    # ------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------
    reg = geant4.Registry()

    # ------------------------------------------------------------
    # World
    # ------------------------------------------------------------
    world_material = geant4.MaterialPredefined("G4_Galactic")
    world = geant4.solid.Box("world", 20, 20, 20, reg, "m")
    world_lv = geant4.LogicalVolume(world, world_material, "world", reg)
    reg.setWorld(world_lv)

    # ------------------------------------------------------------
    # Liquid Argon (minimal placeholder)
    # ------------------------------------------------------------
    lar_material = geant4.MaterialPredefined("G4_lAr")

    lar_radius = 2.0  # m
    lar_half_height = 2.0  # m

    lar_solid = geant4.solid.Tubs(
        "lar",
        0.0,
        lar_radius,
        lar_half_height,
        0.0,
        2 * np.pi,
        reg,
        "m",
    )

    lar_lv = geant4.LogicalVolume(lar_solid, lar_material, "lar", reg)

    geant4.PhysicalVolume(
        [0, 0, 0],
        [0, 0, 0, "m"],
        lar_lv,
        "lar",
        world_lv,
        reg,
    )

    # ------------------------------------------------------------
    # HPGe detectors (local or public)
    # ------------------------------------------------------------
    hpges = config.get("hpges")
    if hpges is not None:
        for hpge in hpges:
            name = hpge["name"]
            z_mm = hpge.get("pplus_pos_from_lar_center", 0.0)

            # ----------------------------------------
            # Load detector metadata
            # ----------------------------------------
            if public_geometry:
                if lmeta is None:
                    raise RuntimeError(
                        "Public geometry requested but LEGEND metadata "
                        "is unavailable"
                    )
                meta_dict = lmeta.hardware.detectors[name].to_dict()
            else:
                det_file = local_geom_dir / f"{name}.json"
                if not det_file.exists():
                    raise FileNotFoundError(
                        f"Local detector file not found: {det_file}"
                    )
                with open(det_file) as f:
                    meta_dict = yaml.safe_load(f)

            # ----------------------------------------
            # Build HPGe
            # ----------------------------------------
            hpge_lv = make_hpge(
                meta_dict,
                name=f"{name}_lv",
                registry=reg,
            )

            geant4.PhysicalVolume(
                [0, 0, 0],
                [0, 0, z_mm, "mm"],
                hpge_lv,
                f"{name}_pv",
                lar_lv,
                registry=reg,
            )

    return reg
