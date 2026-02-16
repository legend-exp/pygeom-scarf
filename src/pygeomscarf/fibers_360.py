from __future__ import annotations

import pyg4ometry.geant4 as g4
from pygeoml1000.fibers import FiberModuleData, ModuleFactorySingleFibers

__all__ = [
    "build_fiber_shroud",
    "build_fiber_shroud_from_config",
]


class _FiberContainerShim:
    """
    Minimal shim object required by pygeoml1000 to attach fiber modules
    to an already-existing Geant4 geometry.

    pygeoml1000 module factories expect a container object providing
    access to a registry, materials, a mother logical/physical volume,
    and selected metadata. In this use case, the detector geometry
    already exists, so this shim supplies only the required attributes
    without constructing a full geometry hierarchy.

    This class is internal and not part of the public API.
    """

    def __init__(self, registry, materials, hpge_string):
        self.registry = registry
        self.materials = materials
        self.runtime_config = {}

        # Metadata used by pygeoml1000
        self.special_metadata = type("", (), {})()
        self.special_metadata.hpge_string = hpge_string


def build_fiber_shroud(
    registry,
    lar_pv: g4.PhysicalVolume,
    hpge_string,
    materials,
):
    """
    Build a 360° LEGEND fiber shroud with SiPMs inside an existing
    LAr physical volume.

    Parameters
    ----------
    registry
        pyg4ometry registry used to store geometry volumes.
    lar_pv
        Physical volume of the LAr volume into which fibers are placed.
    hpge_string
        Identifier for the HPGe string associated with this shroud.
    materials
        Material dictionary passed to pygeoml1000.

    Returns
    -------
    dict[str, g4.PhysicalVolume]
        Dictionary mapping SiPM names to their physical volumes.
    """

    # ------------------------------------------------------------------
    # 1) Minimal container required by pygeoml1000
    # ------------------------------------------------------------------
    container = _FiberContainerShim(registry, materials, hpge_string)

    container.mother_lv = lar_pv.logicalVolume
    container.mother_pv = lar_pv
    container.mother_z_displacement = 0.0
    container.mother_x_displacement = 0.0

    # CRITICAL: attach new volumes to the existing LAr PV
    registry._world = lar_pv

    # ------------------------------------------------------------------
    # 2) Define fiber modules
    # ------------------------------------------------------------------
    modules = [
        FiberModuleData(
            barrel="inner",
            name=f"IB{i}",
            tpb_thickness=150,  # nm
            channel_top_name=f"sipm_top_{i}",
            channel_bottom_name=f"sipm_bot_{i}",
            channel_top_rawid=1000 + 2 * i,
            channel_bottom_rawid=1001 + 2 * i,
            string_id=str(i),
        )
        for i in range(6)
    ]

    # ------------------------------------------------------------------
    # 3) Fiber module factory
    # ------------------------------------------------------------------
    factory = ModuleFactorySingleFibers(
        radius_mm=50,
        fiber_length_mm=200,
        fiber_count_per_module=45,
        bend_radius_mm=None,
        number_of_modules=6,
        z_displacement_mm=100,
        materials=materials,
        registry=registry,
    )

    # ------------------------------------------------------------------
    # 4) Build fibers and SiPMs inside LAr
    # ------------------------------------------------------------------
    for module in modules:
        factory.create_module(module, container)

    # ------------------------------------------------------------------
    # 5) Collect SiPM physical volumes
    # ------------------------------------------------------------------

    return {
        pv.name: pv
        for pv in registry.physicalVolumeDict.values()
        if pv.name.startswith("sipm_")
    }


def build_fiber_shroud_from_config(
    registry,
    lar_pv: g4.PhysicalVolume,
    materials,
    config,
):
    """
    Build a 360° LEGEND fiber shroud using parameters from a config dict.
    """

    fiber_cfg = config["fibers"]

    # ------------------------------------------------------------------
    # 1) Minimal container
    # ------------------------------------------------------------------
    container = _FiberContainerShim(
        registry,
        materials,
        fiber_cfg["container"]["hpge_string"],
    )

    container.mother_lv = lar_pv.logicalVolume
    container.mother_pv = lar_pv
    container.mother_z_displacement = 0.0
    container.mother_x_displacement = 0.0

    registry._world = lar_pv

    # ------------------------------------------------------------------
    # 2) Fiber modules (from config)
    # ------------------------------------------------------------------
    mod_cfg = fiber_cfg["modules"]

    modules = []
    for i in range(mod_cfg["count"]):
        modules.append(
            FiberModuleData(
                barrel="inner",
                name=f"{mod_cfg['name_prefix']}{i}",
                tpb_thickness=mod_cfg["tpb_thickness_nm"],
                channel_top_name=f"{mod_cfg['channel_top_prefix']}{i}",
                channel_bottom_name=f"{mod_cfg['channel_bottom_prefix']}{i}",
                channel_top_rawid=mod_cfg["base_rawid"] + 2 * i,
                channel_bottom_rawid=mod_cfg["base_rawid"] + 2 * i + 1,
                string_id=str(i),
            )
        )

    # ------------------------------------------------------------------
    # 3) Fiber module factory (from config)
    # ------------------------------------------------------------------
    factory = ModuleFactorySingleFibers(
        materials=materials,
        registry=registry,
        **fiber_cfg["factory"],
    )

    # ------------------------------------------------------------------
    # 4) Build fibers and SiPMs
    # ------------------------------------------------------------------
    for module in modules:
        factory.create_module(module, container)

    # ------------------------------------------------------------------
    # 5) Collect SiPM physical volumes
    # ------------------------------------------------------------------
    return {
        pv.name: pv
        for pv in registry.physicalVolumeDict.values()
        if pv.name.startswith("sipm_")
    }
