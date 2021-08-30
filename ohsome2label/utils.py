import os

import numpy as np
from requests import exceptions
from requests.models import HTTPError
from urllib3.util.retry import Retry
import requests
import time
import logging
import tqdm

from ohsome2label.tile import Tile, get_xy_bbox


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s]\t%(asctime)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[TqdmLoggingHandler()],
)


class RequestError(Exception):
    """Cannot download from that URL"""


def get_area(x, y):
    """Calculate the area of polygon

    param x: x coordinate array of the polygon
    param y: y coordinate array of the polygon
    """
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def retries_session(retries=0):
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def download(fpath, api, params={}, retries=0):
    """Download with url and params"""
    session = retries_session(retries)
    # if r.status_code == 200:
    try:
        r = session.get(url=api, params=params)
        if not r.raise_for_status():
            with open(fpath, "wb") as f:
                f.write(r.content)
        else:
            raise requests.exceptions.HTTPError
    except requests.exceptions.HTTPError as e:
        # log.error("Retry execced max time, please check API or try it later")
        log.warning(
            "Download error. %s\nPlease check your bboxes boundary or try it later" % e
        )
    except requests.exceptions.ConnectionError as e:
        # log.error("ConnectionError, please check API")
        log.warning("Connection error. %s" % e)


def download_osm(cfg, workspace):
    """Download osm according to config

    param cfg: config from config.yaml
    param workspace: workspace to store osm data
    """
    url = cfg.url
    params = {
        "bboxes": "{},{},{},{}".format(*cfg.bboxes),
        "time": cfg.timestamp,
        "types": cfg.types,
        "properties": cfg.properties,
    }
    tgt_dir = workspace.raw
    for tag in tqdm.tqdm(cfg.tags):
        fname = "{label}_{k}_{v}.geojson".format(
            label=tag["label"], k=tag["key"], v=tag["value"]
        )
        params["keys"] = tag["key"]
        params["values"] = tag["value"]
        fpath = os.path.join(tgt_dir, fname)
        download(fpath, url, params)


def download_img(cfg, workspace):
    """download satellite image
    different api has different RESTful api url,
    Now we support mapbox/sentinel/bing/custom
    For mapbox:
    http://a.tiles.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token={token}
    For sentinel:
    https://services.sentinel-hub.com/ogc/wms/{token}?showLogo=false&service=WMS&request=GetMap&layers=ALL-BAND&styles=&format=image%2Ftiff&transparent=1&version=1.1.1&maxcc=20&time=2015-01-01%2F2020-01-01&priority=mostRecent&height=256&width=256&srs=EPSG%3A3857&bbox={bbox}
    For bing:
    http://t0.tiles.virtualearth.net/tiles/a{q}.png?g=854&mkt=en-US&token={token}
    For custom, only support x,y,z and token in img_url


    param cfg: ohsome2label.config.o2l_config
    param workspace: ohsome2label.config.workspace
    """
    tgt_dir = workspace.img
    tile_list = os.path.join(workspace.other, "tile_list")
    tiles = []
    with open(tile_list, "r") as tl:
        tiles = [_.replace("\n", "") for _ in tl]
    api = cfg.img_api.lower()
    for tile in tqdm.tqdm(tiles):
        z, x, y = [int(_) for _ in tile.split(".")]
        tile = Tile(x, y, z)
        baseURL = cfg.img_url
        if api == "mapbox":
            url = baseURL.format(x=tile.x, y=tile.y, z=tile.z, token=cfg.token)
        elif api == "sentinel":
            bbox = "{},{},{},{}".format(*get_xy_bbox(tile))
            url = baseURL.format(token=cfg.token, bbox=bbox)
        elif api == "bing":
            quadkey = tile_coords_and_zoom_to_quadKey(int(x), int(y), int(z))
            url = baseURL.format(q=quadkey, token=cfg.token)
        elif api == "custom":
            if "token" in baseURL:
                url = baseURL.format(x=tile.x, y=tile.y, z=tile.z, token=cfg.token)
            else:
                url = baseURL.format(x=tile.x, y=tile.y, z=tile.z)

        if api == "sentinel":
            fname = "{0.z}.{0.x}.{0.y}.tiff".format(tile)
        else:
            fname = "{0.z}.{0.x}.{0.y}.png".format(tile)
        fpath = os.path.join(tgt_dir, fname)
        download(fpath, url)


def valid_coco():
    pass


def tile_coords_and_zoom_to_quadKey(x, y, zoom):
    """Create a quadkey for use with certain tileservers that use them.

    param x: x index
    param y: y index
    param zoom: zoom level
    """
    quadKey = ""
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (x & mask) != 0:
            digit += 1
        if (y & mask) != 0:
            digit += 2
        quadKey += str(digit)
    return quadKey
