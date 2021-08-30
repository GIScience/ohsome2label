import os

import click
import logging

from ohsome2label.config import Config, Parser, workspace
from ohsome2label.label import gen_label, get_tile_list
from ohsome2label.overpass import overpass_download
from ohsome2label.utils import download_osm, download_img
from ohsome2label.logger import TqdmLoggingHandler
from ohsome2label.visualize import visualize_combined, visualize_overlay
from ohsome2label.quality import get_osm_quality

pass_config = click.make_pass_decorator(Config, ensure=True)


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s]\t%(asctime)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[TqdmLoggingHandler()],
)
log = logging.getLogger(__name__)


class CliConfig(object):
    def __init__(self, verbose, config, schema):
        self.verbose = False
        self.config = config
        self.schema = schema
        self.o2l_cfg = Parser(config, schema).parse()
        self.workspace = workspace(self.o2l_cfg.workspace)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--verbose", "-v", is_flag=True, default=False)
@click.option("--config", type=click.Path(exists=True), default="config/config.yaml")
@click.option("--schema", type=click.Path(exists=True), default="config/schema.yaml")
# @pass_config
@click.pass_context
def cli(ctx, verbose, config, schema):
    """
    Generate training label for deep learning via ohsomeAPI
    """
    cfg = CliConfig(verbose, config, schema)
    ctx.obj = cfg


@cli.command(help="Download vector OSM data from ohsomeAPI")
@click.pass_obj
def vector(config):
    log.info(
        "Download OSM historical data into dir:\n{}".format(
            os.path.abspath(config.workspace.raw)
        )
    )
    cfg = config.o2l_cfg
    workspace = config.workspace
    api = cfg.api
    if api == "ohsome":
        download_osm(cfg, workspace)
    elif api == "overpass":
        overpass_download(cfg, workspace)


@cli.command(help="Clip osm data into tile contains desired label")
@click.pass_obj
def tile(config):
    cfg = config.o2l_cfg
    workspace = config.workspace
    log.info("Tile the OSM data into given zoom level: {}".format(cfg.zoom))
    get_tile_list(cfg, workspace)


@cli.command(help="Generate label")
@click.pass_obj
def label(config):
    cfg = config.o2l_cfg
    workspace = config.workspace
    log.info("Tile the OSM data into given zoom level: {}".format(cfg.zoom))
    gen_label(cfg, workspace)


@cli.command(help="Download satellite image")
@click.pass_obj
def image(config):
    cfg = config.o2l_cfg
    if config.verbose:
        pass  # add output later
    log.info("Start download satellite image!")
    download_img(cfg, config.workspace)


@cli.command(help="Visualize of training samples")
@click.option("--num", "-n", type=int, default=10)
@click.option("--type", "-t", type=str, default="combined")
# @pass_config
@click.pass_obj
def visualize(config, num, type):
    cfg = config.o2l_cfg
    workspace = config.workspace
    if config.verbose:
        pass  # add output later
    log.info("start visualize {} pictures in {} type!".format(num, type))
    if type == "combined":
        visualize_combined(workspace, num)
        log.info(
            "Visualization mode: combined the satellite image with OpenStreetMap features."
        )
    else:
        if type == "overlay":
            visualize_overlay(workspace, num)
            log.info(
                "Visualization mode: overlay the satellite image with OpenStreetMap features."
            )
        else:
            pass
            log.error(
                "Wrong visualization type {}. Please check your type!".format(type)
            )


@cli.command(help="Generate OSM quality figure")
# @pass_config
@click.pass_obj
def quality(config):
    cfg = config.o2l_cfg
    workspace = config.workspace
    get_osm_quality(cfg, workspace)


@cli.command(help="Print project config")
# @pass_config
@click.pass_obj
def printcfg(cfg):
    import pprint

    pprint.pprint(cfg.o2l_cfg.__dict__)
