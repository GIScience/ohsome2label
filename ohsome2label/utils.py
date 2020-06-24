import os

import numpy as np
import requests
from tqdm import tqdm

from ohsome2label.tile import Tile, get_xy_bbox


class RequestError(Exception):
    """Cannot download from that URL"""


def get_area(x, y):
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def download(fpath, api, params={}, retry=5):
    """Download with url and params"""
    with requests.get(api, params) as r:
        if r.status_code == 200:
            with open(fpath, "wb") as f:
                f.write(r.content)
        elif retry > 0:
            retry -= 1
            download(fpath, api, params, retry)
        else:
            print(r.url)
            raise RequestError("Request Error {}".format(r.status_code))


def download_osm(cfg, workspace):
    url = cfg.url
    params = {
        "bboxes": "{},{},{},{}".format(*cfg.bboxes),
        "time": cfg.timestamp,
        "types": cfg.types,
        "properies": cfg.properties,
    }
    tgt_dir = workspace.raw
    for tag in tqdm(cfg.tags):
        fname = "{label}_{k}_{v}.geojson".format(
            label=tag["label"], k=tag["key"], v=tag["value"]
        )
        params["keys"] = tag["key"]
        params["values"] = tag["value"]
        fpath = os.path.join(tgt_dir, fname)
        download(fpath, url, params)


def download_img(cfg, workspace):
    tgt_dir = workspace.img
    tiles = os.listdir(workspace.label)
    api = cfg.img_api.lower()
    for tile in tqdm(tiles):
        z, x, y = tile.split(".")[0:3]
        tile = Tile(x, y, z)
        if api == "google":
            url = "https://mt0.google.com/vt/lyrs=s?x={0.x}&y={0.y}&z={0.z}".format(
                tile
            )
        elif api == "mapbox":
            baseURL = (
                "http://a.tiles.mapbox.com/v4/mapbox.satellite/"
                "{z}/{x}/{y}.jpg?access_token={token}"
            )
            url = baseURL.format(x=tile.x, y=tile.y, z=tile.z, token=cfg.token)
        elif api == "sentinel":
            baseURL = "https://services.sentinel-hub.com/ogc/wms/{token}?showLogo=false&service=WMS&request=GetMap&layers=ALL-BAND&styles=&format=image%2Ftiff&transparent=1&version=1.1.1&maxcc=20&time=2015-01-01%2F2020-01-01&priority=mostRecent&height=256&width=256&srs=EPSG%3A3857&bbox={bbox}"
            bbox = "{},{},{},{}".format(*get_xy_bbox(tile))
            url = baseURL.format(token=cfg.token, bbox=bbox)
        elif api == "bing":
            baseURL = "http://t0.tiles.virtualearth.net/tiles/a{q}.png?g=854&mkt=en-US&token={token}"
            quadkey = tile_coords_and_zoom_to_quadKey(int(x), int(y), int(z))
            url = baseURL.format(q=quadkey, token=cfg.token)

        if api == "sentinel":
            fname = "{0.z}.{0.x}.{0.y}.tiff".format(tile)
        else:
            fname = "{0.z}.{0.x}.{0.y}.png".format(tile)
        fpath = os.path.join(tgt_dir, fname)
        download(fpath, url)


def valid_coco():
    pass

def tile_coords_and_zoom_to_quadKey(x, y, zoom):
    """Create a quadkey for use with certain tileservers that use them."""
    quadKey = ''
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (x & mask) != 0:
            digit += 1
        if (y & mask) != 0:
            digit += 2
        quadKey += str(digit)
    return quadKey
