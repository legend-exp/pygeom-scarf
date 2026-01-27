from __future__ import annotations

import pyg4ometry.geant4 as g4
from pygeoml1000.fibers import FiberModuleData, ModuleFactorySingleFibers

__all__ = ["build_fiber_shroud"]


class _DummyContainer:
    """
    Minimal container object required by pygeoml1000 to attach
    fiber modules to an existing geometry.

    This is an internal helper and not part of the public API.
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
    container = _DummyContainer(registry, materials, hpge_string)

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

    return {pv.name: pv for pv in registry.physicalVolumeDict.values() if pv.name.startswith("sipm_")}
