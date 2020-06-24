"""
A wrapper for overpass api using config.yaml as source data.
Query overpass dataset and convert to geojson.
For OSM polygon feature, read more on https://github.com/tyrasd/osm-polygon-features
Assume that the input osm and output geojson only contains polygon and multipolygon
The polygon assumption is satified by the query in overpass
For general osm to geojson, visit https://github.com/tyrasd/osmtogeojson
Or use python package osm2geojson
However osm2geojson will miss some geometry compared to the overpass result.
Author: Zhaoyan Wu
"""
import json
import os
from collections import defaultdict

import geojson
import requests
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

_polygon_features_file = os.path.join(
    os.path.dirname(__file__), "polygon-features.json"
)

with open(_polygon_features_file, "r", encoding="utf-8") as f:
    _polygon_features = json.load(f)


def is_polygon_feature(key, value):
    keys = {feat["key"]: i for i, feat in enumerate(_polygon_features)}
    if key not in keys:
        return False

    feat = _polygon_features[keys[key]]
    if feat["polygon"] == "all":
        return True
    elif feat["polygon"] == "whitelist":
        if value in feat["values"]:
            return True
        else:
            return False
    elif feat["polygon"] == "blacklist":
        if value in feat["values"]:
            return False
        else:
            return True

    return False


def get_properties(elem, timestamp):
    """generate properties of output geojson feature"""
    properties = {}
    properties["@osmId"] = "{}/{}".format(elem["type"], elem["id"])
    properties["@snapshotTimestamp"] = timestamp
    properties.update(elem.get("tags", {}))
    return properties


def way_to_geometry(way):
    coords = [(coord["lon"], coord["lat"]) for coord in way["geometry"]]
    if coords[0] == coords[-1]:
        return geojson.Polygon([coords])
    else:
        print("way/{} is not a polygon".format(way["id"]))
        return None


def make_ring(parts):
    for j, other in enumerate(parts):
        if other == []:
            continue
        for i, part in enumerate(parts):
            if part == [] or part == other:
                continue
            if part[-1] == other[0]:
                part.extend(other[1:])
                other.clear()
                break
            elif part[-1] == other[-1]:
                part.extend(other[-2::-1])
                other.clear()
                break
            elif part[0] == other[0]:
                part[0:0] = other[-1:0:-1]
                other.clear()
                break
            elif part[0] == other[-1]:
                part[0:0] = other[:-1]
                other.clear()
                break
    return [part for part in parts if part != []]


def rel_to_geometry(rel):
    outers = []
    part_outers = []
    inners = []
    part_inners = []

    for member in rel["members"]:
        is_polygon = False

        if member["type"] == "way":
            coords = [(coord["lon"], coord["lat"]) for coord in member["geometry"]]
            if coords[-1] == coords[0]:
                is_polygon = True

            if member["role"] == "outer":
                if is_polygon:
                    outers.append(Polygon(coords))
                else:
                    part_outers.append(coords)
            elif member["role"] == "inner":
                if is_polygon:
                    inners.append(Polygon(coords))
                else:
                    part_inners.append(coords)
            else:
                print("check rel/{}, member's role is ilegal".format(rel["id"]))
                return None
        elif member["type"] == "relation":
            print("Not support rel member")
            continue
        else:
            print("Only support way member")
            continue

    part_outers = make_ring(part_outers)
    part_inners = make_ring(part_inners)
    for part in part_outers:
        if part[0] == part[-1]:
            outers.append(Polygon(part))
        else:
            print("rel/{} outer is not complete".format(rel["id"]))
            continue

    for part in part_inners:
        if part[0] == part[-1]:
            inners.append(Polygon(part))
        else:
            print("member is not a polygon")

    if len(outers) == 0:
        print("outer is None, wrong")
        return None

    polys = []
    for outer in outers:
        poly = [list(outer.exterior.coords)]
        for inner in inners:
            if outer.contains(inner):
                poly.append(list(orient(inner, sign=-1).exterior.coords))

        polys.append(poly)

    geometry = geojson.MultiPolygon(polys)

    return geometry


def osm_to_geojson(osm, date):
    """ Convert osm json to geojson.
        The input osm is produced by overpass_ql with "out geom;"
    """
    way_features = []
    rel_features = []
    timestamp = date
    elems = osm["elements"]

    for elem in elems:
        properties = get_properties(elem, timestamp)
        if elem["type"] == "way":
            geometry = way_to_geometry(elem)
            if geometry is None:
                continue
            feature = geojson.Feature(geometry=geometry, properties=properties)
            way_features.append(feature)
        elif elem["type"] == "relation":
            geometry = rel_to_geometry(elem)
            if geometry is None:
                continue
            feature = geojson.Feature(geometry=geometry, properties=properties)
            way_features.append(feature)

    features = rel_features + way_features

    return geojson.FeatureCollection(features)


class overpass(object):
    """overpass api"""

    def __init__(self, endpoint="", settings=None, statements=None, out="geom"):
        if endpoint == "":
            self._endpoint = "https://lz4.overpass-api.de/api/interpreter"
        else:
            self._endpoint = endpoint
        if settings is None:
            self._settings = []
        else:
            self._settings = list(settings)
        if statements is None:
            self._statements = []
        else:
            self._statements = list(statements)

        self._out = out

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, endpoint):
        """set endpoint"""
        self._endpoint = endpoint

    @property
    def out(self):
        return self._out

    @endpoint.setter
    def endpoint(self, out):
        """set out format"""
        self._out = out

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, settings):
        """set settings"""
        self._settings = list(settings)

    def add_settings(self, *args):
        """add setting for overpass ql

        :param args:list of settings, in format of '[key:value]'
        """
        for arg in args:
            if arg not in self._settings:
                self._settings.append(arg)

    def remove_settings(self, *args):
        """remove setting for overpass ql

        :param args:list of settings, in format of '[key:value]'
        """
        for arg in args:
            if arg in self._settings:
                self._settings.remove(arg)

    @property
    def statements(self):
        return self._statements

    @statements.setter
    def statements(self, statements):
        self._statements = list(statements)

    def add_statements(self, *args):
        """add statements for overpass ql

        :param args:list of statements
        """
        for arg in args:
            if arg not in self._statements:
                self._statements.append(arg)

    def remove_statements(self, *args):
        """remove setting for overpass ql

        :param args:list of statements
        """
        for arg in args:
            if arg in self._statements:
                self._statements.remove(arg)

    def query(self):
        settings = "".join(self._settings) + ";"
        statements = "(" + ";".join(self._statements) + ";);"
        statements += "out {};".format(self._out)
        overpass_ql = {"data": "".join([settings, statements])}
        try:
            r = requests.post(self.endpoint, data=overpass_ql)
        except requests.exceptions.Timeout:
            print(r.url)
            raise Exception

        return r


def overpass_download(cfg, workspace, url=""):
    op = overpass(endpoint=url)
    op.add_settings("[out:json]")
    op.add_settings("[timeout:3600]")
    op.add_settings("[maxsize:1073741824]")
    op.add_settings("[bbox:{}]".format(cfg.op_bbox))
    date = "{}T00:00:00Z".format(cfg.timestamp)
    op.add_settings("[date:'{}']".format(date))
    tgt_dir = workspace.raw
    fpath = os.path.join(tgt_dir, "overpass_query.geojson")

    kvs = defaultdict(set)
    for tag in cfg.tags:
        value = tag.get("value", "")
        if value:
            kvs[tag["key"]].add(value)
        else:
            kvs[tag["key"]] = set(".")

    for key in kvs:
        query = '~"^{}$"~"({})"'.format(key, "|".join(kvs[key]))
        op.add_statements("way[{}]".format(query))
        op.add_statements("rel[{}]".format(query))
    mf = osm_to_geojson(op.query().json(), date)
    if mf is not None:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(mf, f, indent=2)
