from pyg4ometry import geant4

from pygeomscarf.core import construct


def test_construct_uses_local_geometry():
    config = {
        "hpges": [
            {"name": "V99000A"}
        ]
    }

    reg = construct(
        config=config,
        public_geometry=False,
    )

    assert isinstance(reg, geant4.Registry)

    # All logical volumes by name
    lv_names = {lv.name for lv in reg.logicalVolumeDict.values()}

    # World must exist
    assert "world" in lv_names

    # HPGe logical volume must exist
    assert "V99000A_lv" in lv_names
