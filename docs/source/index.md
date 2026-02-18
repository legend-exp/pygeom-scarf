# Welcome to pygeomscarf's documentation!

Python package containing the Monte Carlo geometry implementation of the LEGEND
HPGe characterization test stand in SCARF.

This geometry can be used as an input to the
[remage](https://remage.readthedocs.io/en/stable/) simulation software.

This package is based on {doc}`pyg4ometry <pyg4ometry:index>`,
{doc}`legend-pygeom-hpges <legendhpges:index>` (implementation of HPGe
detectors) and {doc}`legend-pygeom-tools <pygeomtools:index>`.

## Installation

:::{important}

For using all its features, this package requires a working setup of
[`legend-metadata`](https://github.com/legend-exp/legend-metadata) (_private
repository_) before usage. A limited public geometry is also implemented.

:::

The latest tagged version and all its dependencies can be installed from PyPI:
`pip install pygeom-scarf`.

Alternatively, the packages's development version can be installed from a git
checkout: `pip install -e .` (in the directory of the git checkout).

## Usage as CLI tool

After installation, the CLI utility `pygeom-scarf` is provided on your `$PATH`.
This CLI utility is the primary way to interact with this package. For now, you
can find usage docs by running `pygeom-scarf -h`.

In the simplest case, you can create a usable geometry file with:

```
$ pygeom-scarf scarf.gdml
```

## Configuration

To include HPGe detectors, fibers or the calibration source in the geometry it
is possible to include a configuration file. This should have the following
format:

```yaml
hpges:
  - name: "V09999A" # name of the detector
    pplus_pos_from_lar_center: 0 # position from the center of the LAr

  # ... multiple HPGe's can be specified

source:
  pos_from_lar_center: 0 # position from the center of the LAr

fiber_shroud:
  mode: "simplified" # only mode supported for now
  height_in_mm: 1200
  radius_in_mm: 200
  center_pos_from_lar_center: 0

cavern:
  inner_radius_in_mm: 7000
  outer_radius_in_mm: 15000
```

::: note The cavern and fiber shroud implementation is very simplified. :::

Generally the detectors should be present in the LEGEND detectors database. In
addition, {func}`core.construct` supports passing a `TextDB` of additional
detector metadata.

This can also be passed to on the command line, the flag `--extra-detectors` can
be used to provide the path to a directory containing extra detector metadata
files. Similar to
[legend-detectors](https://github.com/legend-exp/legend-detectors/tree/main/germanium/diodes),
each detector should have a YAML configuration file named according to the
detector name.

```{toctree}
:maxdepth: 1
:caption: Development

Package API reference <api/modules>
```
