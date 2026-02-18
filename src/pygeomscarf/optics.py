from __future__ import annotations

import pint
import pyg4ometry.geant4 as g4
from pygeomtools.materials import BaseMaterialRegistry
from pygeomtools.materials import cached_property as pg_cached_property

from pygeomoptics import fibers, lar, pen, tpb



u = pint.get_application_registry()


class OpticalMaterialRegistry(BaseMaterialRegistry):
    def __init__(self, g4_registry: g4.Registry):
        self.lar_temperature = 88.8 * u.K
        super().__init__(g4_registry)
        self._build_surfaces()

    def _build_surfaces(self):
        self.surfaces = type("Surfaces", (), {})()

        # -------------------------
        # LAr → TPB
        # -------------------------
        self.surfaces.lar_to_tpb = g4.solid.OpticalSurface(
            name="os_lar_tpb",
            model="unified",
            finish="ground",
            surf_type="dielectric_dielectric",
            value=1.0,
            registry=self.g4_registry,
        )
        self.surfaces.lar_to_tpb.addConstProperty("SIGMA_ALPHA", 0.2)
        self.surfaces.lar_to_tpb.addConstProperty("DIFFUSELOBECONSTANT", 0.7)
        self.surfaces.lar_to_tpb.addConstProperty("SPECULARLOBECONSTANT", 0.2)
        self.surfaces.lar_to_tpb.addConstProperty("SPECULARSPIKECONSTANT", 0.1)
        self.surfaces.lar_to_tpb.addConstProperty("BACKSCATTERCONSTANT", 0.0)

        # -------------------------
        # LAr → SiPM (PDE)
        # -------------------------
        self.surfaces.to_sipm_silicon = g4.solid.OpticalSurface(
            name="os_lar_sipm",
            model="unified",
            finish="polished",
            surf_type="dielectric_metal",
            value=0,
            registry=self.g4_registry,
        )

        # Photon energies in eV (ascending)
        energies = [
            0.5,  # IR
            1.24,  # 1000 nm  (turn on)
            3.10,  # 400 nm   (turn off)
            6.0,  # deep UV
        ]

        # Quantum efficiency (PDE)
        qe = [
            0.0,  # below 1000 nm
            1.0,  # fully sensitive
            1.0,  # fully sensitive
            0.0,  # above 400 nm
        ]

        # Reflection
        reflectivity = [0.0, 0.0, 0.0, 0.0]

        self.surfaces.to_sipm_silicon.addVecProperty("EFFICIENCY", energies, qe)
        self.surfaces.to_sipm_silicon.addVecProperty("REFLECTIVITY", energies, reflectivity)

    @pg_cached_property
    def liquidargon(self) -> g4.Material:
        _lar = g4.Material(
            name="liquid_argon",
            density=1.390,
            number_of_components=1,
            state="liquid",
            temperature=float(self.lar_temperature.m_as(u.kelvin)),
            pressure=1.0e5,
            registry=self.g4_registry,
        )
        _lar.add_element_natoms(self.get_element("Ar"), natoms=1)
        lar.pyg4_lar_attach_rindex(_lar, self.g4_registry)
        lar.pyg4_lar_attach_attenuation(
            lar_mat=_lar,
            reg=self.g4_registry,
            lar_temperature=self.lar_temperature,
            lar_dielectric_method="cern2020",
            attenuation_method_or_length="legend200-llama",
            rayleigh_enabled_or_length=True,
            absorption_enabled_or_length=True,
        )
        lar.pyg4_lar_attach_scintillation(_lar, self.g4_registry, flat_top_yield=1000 / u.MeV)
        return _lar

    @pg_cached_property
    def pmma(self) -> g4.Material:
        _pmma = g4.Material(
            name="pmma",
            density=1.2,
            number_of_components=3,
            registry=self.g4_registry,
        )
        _pmma.add_element_natoms(self.get_element("H"), natoms=8)
        _pmma.add_element_natoms(self.get_element("C"), natoms=5)
        _pmma.add_element_natoms(self.get_element("O"), natoms=2)
        fibers.pyg4_fiber_cladding1_attach_rindex(_pmma, self.g4_registry)
        return _pmma

    @pg_cached_property
    def pmma_out(self) -> g4.Material:
        _pmma_out = g4.Material(
            name="pmma_cl2",
            density=1.2,
            number_of_components=3,
            registry=self.g4_registry,
        )
        _pmma_out.add_element_natoms(self.get_element("H"), natoms=8)
        _pmma_out.add_element_natoms(self.get_element("C"), natoms=5)
        _pmma_out.add_element_natoms(self.get_element("O"), natoms=2)
        fibers.pyg4_fiber_cladding2_attach_rindex(_pmma_out, self.g4_registry)
        return _pmma_out

    @pg_cached_property
    def ps_fibers(self) -> g4.Material:
        _ps_fibers = g4.Material(
            name="ps_fibers",
            density=1.05,
            number_of_components=2,
            registry=self.g4_registry,
        )
        _ps_fibers.add_element_natoms(self.get_element("H"), natoms=8)
        _ps_fibers.add_element_natoms(self.get_element("C"), natoms=8)
        fibers.pyg4_fiber_core_attach_rindex(_ps_fibers, self.g4_registry)
        fibers.pyg4_fiber_core_attach_absorption(_ps_fibers, self.g4_registry)
        fibers.pyg4_fiber_core_attach_wls(_ps_fibers, self.g4_registry)
        fibers.pyg4_fiber_core_attach_scintillation(_ps_fibers, self.g4_registry)

        return _ps_fibers

    def _tpb(self, name: str) -> g4.Material:
        t = g4.Material(
            name=name,
            density=1.08,
            number_of_components=2,
            state="solid",
            registry=self.g4_registry,
        )
        t.add_element_natoms(self.get_element("H"), natoms=22)
        t.add_element_natoms(self.get_element("C"), natoms=28)
        tpb.pyg4_tpb_attach_rindex(t, self.g4_registry)
        tpb.pyg4_tpb_attach_wls(t, self.g4_registry)
        return t

    @pg_cached_property
    def tpb_on_fibers(self) -> g4.Material:
        m = g4.Material(
            name="tpb_on_fibers",
            density=1.08,
            number_of_components=2,
            state="solid",
            registry=self.g4_registry,
        )
        m.add_element_natoms(self.get_element("H"), natoms=22)
        m.add_element_natoms(self.get_element("C"), natoms=28)

        tpb.pyg4_tpb_attach_rindex(m, self.g4_registry)
        tpb.pyg4_tpb_attach_wls(m, self.g4_registry)
        return m

    @pg_cached_property
    def os_fibers(self) -> g4.solid.OpticalSurface:
        return g4.solid.OpticalSurface(
            name="os_fibers",
            model="unified",
            finish="polished",
            surf_type="dielectric_dielectric",
            value=1.0,
            registry=self.g4_registry,
        )

    @pg_cached_property
    def pen(self) -> g4.Material:
        m = g4.Material(
            name="PEN",
            density=1.30,
            number_of_components=3,
            state="solid",
            temperature=88.15,
            registry=self.g4_registry,
        )
        m.add_element_natoms(self.get_element("C"), natoms=14)
        m.add_element_natoms(self.get_element("H"), natoms=10)
        m.add_element_natoms(self.get_element("O"), natoms=4)
        pen.pyg4_pen_attach_rindex(m, self.g4_registry)
        pen.pyg4_pen_attach_attenuation(m, self.g4_registry)
        pen.pyg4_pen_attach_wls(m, self.g4_registry)
        pen.pyg4_pen_attach_scintillation(m, self.g4_registry)
        return m

    @pg_cached_property
    def metal_silicon(self):
        m = g4.Material(
            name="metal_silicon",
            density=2.33,
            number_of_components=1,
            registry=self.g4_registry,
        )
        m.add_element_natoms(self.get_element("Si"), 1)
        return m

    @pg_cached_property
    def metal_copper(self):
        m = g4.Material(
            name="metal_copper",
            density=8.96,
            number_of_components=1,
            registry=self.g4_registry,
        )
        m.add_element_natoms(self.get_element("Cu"), 1)
        return m

