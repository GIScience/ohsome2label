"""Note:
Difference between Slippy Map tile and Tile Map Service
For Slippy Map tile:
X goes from 0 (left edge is 180 °W) to 2zoom
Y goes from 0 (top edge is 85.0511 °N) to 2zoom

For Tile Map Service:
X is the same with slippy map tile
Y increases with the y-coordinate of the spatial reference system
In other words, tile (0,0) is placed at the bottom left of the map

All function in this file is based on the Slippy Map tile system
You can use SMT2TMS() function
To calculate the tile number in TMS according to the tile number in SMT
"""
import math
from collections import namedtuple

ELLIPSOID = 6378137.0
XMAX = YMAX = math.pi * ELLIPSOID
XMIN = YMIN = -XMAX
LATMAX = math.degrees(2 * math.atan(math.exp(YMAX / ELLIPSOID)) - 0.5 * math.pi)
LATMIN = -LATMAX


Tile = namedtuple("Tile", ["x", "y", "z"])
LngLat = namedtuple("LngLat", ["lng", "lat"])
Bbox = namedtuple("Bbox", ["west", "south", "east", "north"])
BboxXY = namedtuple("BboxXY", ["xmin", "ymin", "xmax", "ymax"])


class InvalidTransform(Exception):
    """ Right now only support transform between EPSG:4326 and EPSG:3857 """


def truncate(lon, lat):
    """truncate the longitude and latitude.

    :param lon: longitude
    :param lat: latitude

    :return: truncated longitude and latitude
    """
    if lon > 180.0:
        lon = 180.0
    elif lon < -180.0:
        lon = -180.0

    if lat > LATMAX:
        lat = LATMAX
    elif lat < LATMIN:
        lat = LATMIN
    return lon, lat


def truncate_xy(x, y):
    """truncate the x/y coordinate according to the EPSG:3857 definition

    :param x: x coordinate
    :param y: y coordinate
    :return: truncated coordinate
    """
    if x > XMAX:
        x = XMAX
    elif x < XMIN:
        x = XMIN

    if y > YMAX:
        y = YMAX
    elif y < YMIN:
        y = YMIN
    return x, y


def xy(lon, lat):
    """Convert EPSG:4326 to EPSG:3857.

    :param lon: longitude
    :param lat: latitude
    :return: EPSG:3857 coordinate
    """
    lon, lat = truncate(lon, lat)
    x = ELLIPSOID * math.radians(lon)
    y = ELLIPSOID * math.log(math.tan((0.25 * math.pi) + (0.5 * math.radians(lat))))
    return x, y


def lnglat(x, y):
    """Convert EPSG:3857 to EPSG:4326.

    :param x: x coordinate
    :param y: y coordinate
    :return: EPSG:4326 coordinate
    """
    x, y = truncate_xy(x, y)
    lon = math.degrees(x / ELLIPSOID)
    lat = math.degrees(2 * math.atan(math.exp(y / ELLIPSOID)) - 0.5 * math.pi)
    lon, lat = truncate(lon, lat)
    return LngLat(lon, lat)


def xy_to_tile(x, y, zoom):
    """Convert EPSG:4326 coordinate to tile index

    :param x:
    :param y:
    :param zoom:
    :return: tile index
    """
    n = 1 << zoom
    tx = int(0.5 * n * (x - XMIN) / XMAX)
    ty = int(0.5 * n * (YMAX - y) / YMAX)
    return Tile(tx, ty, zoom)


def lnglat_to_tile(lon, lat, zoom):
    """Get the tile which contains longitude and latitude.

    :param lon: longitude
    :param lat: latitude
    :param zoom: zoom level
    :return: tile tuple
    """
    lon, lat = truncate(lon, lat)
    n = 1 << zoom
    tx = int((lon + 180.0) / 360.0 * n)
    ty = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return Tile(tx, ty, zoom)


def smt_tms(tile):
    """Convert slippy map tile to tile map service tile.

    :param tile: tile tuple
    :return: tile tuple
    """
    n = 1 << tile.z
    y = n - tile.y - 1
    return Tile(tile.x, y, tile.z)


def top_left(tile):
    """Get the top left coordinate of a tile.

    :param tile: tile tuple
    :return: top left coordinate in EPSG:3857
    """
    n = 1 << tile.z
    x = 2 * XMAX * tile.x / n - XMAX
    y = YMAX - 2 * YMAX * tile.y / n
    return x, y


def west_north(tile):
    """Get the west north lnglat of a tile.

    :param tile: tile tuple
    :return: west north lnglat in EPSG:4326
    """
    x, y = top_left(tile)
    return lnglat(x, y)


def get_bbox(tile):
    """get the bounding box of a tile in LngLat.

    :param tile: tile tuple
    :return: LngLat bounding box of a tile
    :rtype: Bbox
    """
    west, north = west_north(tile)
    east, south = west_north(Tile(tile.x + 1, tile.y + 1, tile.z))
    return Bbox(west, south, east, north)


def get_xy_bbox(tile):
    """get the bounding box of a tile.

    :param tile: tile tuple
    :return: bounding box of a tile
    :rtype: BboxXY
    """
    xmin, ymax = top_left(tile)
    xmax, ymin = top_left(Tile(tile.x + 1, tile.y + 1, tile.z))
    return BboxXY(xmin, ymin, xmax, ymax)


def xy_tiles(bbox, zoom):
    """Get the tile range of a bounding bbox.

    :param bbox: bounding box
    :param zoom: zoom level
    :return: generator of the tile in a bounding box
    """
    min_tx, min_ty = xy_to_tile(bbox.xmin, bbox.ymin, zoom)
    max_tx, max_ty = xy_to_tile(bbox.xmax, bbox.ymax, zoom)
    for x in range(min_tx, max_tx):
        for y in range(min_ty, max_ty):
            # return the generator of the tile
            yield Tile(x, y, zoom)


def tiles(bbox, zoom):
    """Get the tile range of a lnglat bounding bbox.

    :param bbox: bounding box in lnglat
    :param zoom: zoom level
    :return: generator of the tile in a lnglat bounding box
    """
    min_tx, min_ty, _ = lnglat_to_tile(bbox.west, bbox.north, zoom)
    max_tx, max_ty, _ = lnglat_to_tile(bbox.east, bbox.south, zoom)
    for x in range(min_tx, max_tx):
        for y in range(min_ty, max_ty):
            # return the generator of the tile
            yield Tile(x, y, zoom)


def xy_expand_bbox(bbox, zoom):
    """Expand bounding box cover all related tile in EPSG:3857

    :param bbox: bounding box
    :param zoom: zoom level
    :return: expanded bounding box
    """
    xmin, ymin = top_left(xy_to_tile(bbox.xmin, bbox.ymin, zoom))
    _ = xy_to_tile(bbox.xmax, bbox.ymax, zoom)
    xmax, ymax = top_left(Tile(_.x + 1, _.y + 1, _.z))
    return BboxXY(xmin, ymin, xmax, ymax)


def expand_bbox(bbox, zoom):
    """Expand bounding box cover all related tile in lnglat

    :param bbox: bounding box
    :param zoom: zoom level
    :return: expanded bounding box
    """
    west, north = west_north(lnglat_to_tile(bbox.west, bbox.north, zoom))
    _ = lnglat_to_tile(bbox.east, bbox.south, zoom)
    east, south = west_north(Tile(_.x + 1, _.y + 1, _.z))
    return Bbox(west, south, east, north)


def tile_get_transform(tile, nx=256, ny=256):
    """Calculate geoTransform for rasterizing the tile

    :param tile: tile tuple
    :param nx: tile width pixel size
    :param ny: tile height pixel size
    """
    rect = get_xy_bbox(tile)
    resx = (rect.xmax - rect.xmin) / float(nx - 1)
    resy = (rect.ymax - rect.ymin) / float(ny - 1)
    transform = (rect.xmin, resx, 0, rect.ymax, 0, -resy)
    return transform


def bbox_get_transform(bbox, nx=256, ny=256):
    """Calculate geoTransform for bbox

    :param bbox: bounding box 
    :param nx: tile width pixel size
    :param ny: tile height pixel size
    """
    resx = (bbox.xmax - bbox.xmin) / float(nx - 1)
    resy = (bbox.ymax - bbox.ymin) / float(ny - 1)
    transform = (bbox.xmin, resx, 0, bbox.ymax, 0, -resy)
    return transform


def apply_transform(coords, trans):
    """transform coordinates according"""
    coords = [((x - trans[0]) / trans[1], (y - trans[3]) / trans[5]) for x, y in coords]
    return coords
