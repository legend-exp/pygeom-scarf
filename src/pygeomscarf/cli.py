from __future__ import annotations

import argparse
import logging

from dbetto import utils
from pyg4ometry import config as meshconfig
from pygeomtools import geometry, write_pygeom

from . import _version, core

log = logging.getLogger(__name__)


def dump_gdml_cli(argv: list[str] | None = None) -> None:
    args, config = _parse_cli_args(argv)

    logging.basicConfig()
    if args.verbose:
        logging.getLogger("pygeomscarf").setLevel(logging.DEBUG)
    if args.debug:
        logging.root.setLevel(logging.DEBUG)

    vis_scene = {}
    if isinstance(args.visualize, str):
        vis_scene = utils.load_dict(args.visualize)

    if vis_scene.get("fine_mesh", False) or args.check_overlaps:
        meshconfig.setGlobalMeshSliceAndStack(100)

    registry = core.construct(
        config=config,
        public_geometry=args.public_geom,
    )

    if args.print_volumes:
        geometry.print_volumes(registry, args.print_volumes)

    if args.check_overlaps:
        msg = "checking for overlaps"
        log.info(msg)
        registry.worldVolume.checkOverlaps(recursive=True)

    # commit auxvals, and write to GDML file if requested.
    if args.filename is not None:
        log.info("exporting GDML geometry to %s", args.filename)
    write_pygeom(registry, args.filename)

    if args.visualize:
        log.info("visualizing...")
        from pygeomtools import viewer

        viewer.visualize(registry, vis_scene)


def _parse_cli_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, dict]:
    parser = argparse.ArgumentParser(
        prog="pygeom-scarf",
        description="%(prog)s command line interface",
    )

    # global options
    parser.add_argument(
        "--version",
        action="version",
        help="""Print %(prog)s version and exit""",
        version=_version.__version__,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="""Increase the program verbosity""",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="""Increase the program verbosity to maximum""",
    )
    parser.add_argument(
        "--visualize",
        "-V",
        nargs="?",
        const=True,
        help="""Open a VTK visualization of the generated geometry (with optional scene file)""",
    )
    parser.add_argument(
        "--check-overlaps",
        action="store_true",
        help="""Check for overlaps with pyg4ometry (note: this might not be accurate)""",
    )
    parser.add_argument(
        "--print-volumes",
        action="store",
        choices=("logical", "physical", "detector"),
        help="""Print a list of logical or physical volume names (from the pyg4ometry registry)""",
    )

    # options for geometry generation.
    #
    # geometry options can also be specified in the config file, so the "default" argument of the argparse
    # options cannot be used - we need to distinguish between an unspecified option and an explicitly set
    # default option.
    geom_opts = parser.add_argument_group("geometry options")
    geom_opts.add_argument(
        "--public-geom",
        action="store_true",
        default=None,
        help="""Create a geometry from public testdata only.""",
    )
    geom_opts.add_argument(
        "--config",
        action="store",
        help="""Select a config file to read geometry config from.""",
    )

    parser.add_argument(
        "filename",
        default=None,
        nargs="?",
        help="""File name for the output GDML geometry.""",
    )

    args = parser.parse_args(argv)

    config = {}
    if args.config is not None:
        config = utils.load_dict(args.config)

    # also load geometry options from config file.
    _config_or_cli_arg(args, config, "public_geom", False)

    if not args.visualize and args.filename == "":
        parser.error("no output file and no visualization specified")

    return args, config


def _config_or_cli_arg(args: argparse.Namespace, config: dict, name: str, default) -> None:
    """Fallback of cli args, to config file, and to default value (in this order)."""
    val_cfg = config.get(name)
    val_attrs = getattr(args, name, None)
    val = val_cfg if val_attrs is None else val_attrs
    val = default if val is None else val
    setattr(args, name, val)
