import os

from pykwalify.core import Core

from ohsome2label.tile import Bbox, expand_bbox, tiles


class ConfigFileException(Exception):
    """only can parse yaml config!
    """


class Config(object):
    def __init__(self, conf):
        self._config = conf

    def get_property(self, section, property_name):
        """get property from yaml config file"""
        if section not in self._config.keys():
            return None
        elif property_name not in self._config[section].keys():
            return None
        return self._config[section][property_name]


class o2l_config(Config):
    @property
    def name(self):
        """get project name"""
        return self.get_property("project", "name")

    @property
    def workspace(self):
        """get project workspace"""
        return self.get_property("project", "workspace")

    @property
    def project_time(self):
        """get the create time of project"""
        return self.get_property("project", "project_time")

    @property
    def task(self):
        """get type of deep learning task"""
        return self.get_property("project", "task")

    @property
    def api(self):
        """get api"""
        return self.get_property("osm", "api")

    @property
    def url(self):
        """get api rul"""
        return self.get_property("osm", "url")

    @property
    def bboxes(self):
        """get bounding box of research area"""
        bboxes = self.get_property("osm", "bboxes")
        bbox = [float(c) for c in str(bboxes)[1:-1].split(",")]
        w = min(bbox[::2])
        e = max(bbox[::2])
        n = max(bbox[1::2])
        s = min(bbox[1::2])
        bbox = expand_bbox(Bbox(w, s, e, n), self.zoom)
        return bbox

    @property
    def op_bbox(self):
        _bbox = self.bboxes
        op_bbox = [
            round(_bbox.south, 4),
            round(_bbox.west, 4),
            round(_bbox.north, 4),
            round(_bbox.east, 4),
        ]
        return str(op_bbox)[1:-1]

    @property
    def tags(self):
        """get {label:, key, value} format tags"""
        return self.get_property("osm", "tags")

    @property
    def timestamp(self):
        """get osm data timestamp"""
        return self.get_property("osm", "timestamp")

    @property
    def properties(self):
        """get osm data property """
        return self.get_property("osm", "properties")

    @property
    def types(self):
        return self.get_property("osm", "types")

    @property
    def img_api(self):
        """get image api"""
        return self.get_property("image", "img_api")

    @property
    def token(self):
        """get image api token"""
        return self.get_property("image", "api_token")

    @property
    def zoom(self):
        """get zoom level"""
        return self.get_property("image", "zoom")

    @property
    def tiles(self):
        bboxes = self.get_property("osm", "bboxes")
        bbox = [float(c) for c in str(bboxes)[1:-1].split(",")]
        w = min(bbox[::2])
        e = max(bbox[::2])
        n = max(bbox[1::2])
        s = min(bbox[1::2])
        bbox = Bbox(w, s, e, n)
        return list(tiles(bbox, self.zoom))


class Parser(object):
    """Config Parser, parse yaml config and return o2l_config"""

    def __init__(self, config_path, schema_path):
        self.config_path = config_path
        self.schema_path = schema_path

    def parse(self):
        """parse yaml config"""
        if self.schema_path.split(".")[-1].lower() != "yaml":
            raise ConfigFileException("Only support YAML schema!")
        if self.config_path.split(".")[-1].lower() != "yaml":
            raise ConfigFileException("Only support YAML config!")
        c = Core(self.config_path, [self.schema_path])
        c.validate()
        return o2l_config(c.source)


class workspace(object):
    """Workspace for ohsome2label"""

    def __init__(self, root):
        self.workspace = root
        self.img = os.path.join(self.workspace, "image")
        self.anno = os.path.join(self.workspace, "annotation")
        self.other = os.path.join(self.workspace, "other")
        self.label = os.path.join(self.workspace, "label")
        self.preview = os.path.join(self.workspace, "preview")
        self.raw = os.path.join(self.other, "raw")
        self.tile = os.path.join(self.other, "tile")
        self.quality = os.path.join(self.other, "quality")
        for directory in self.__dict__:
            path = self.__dict__[directory]
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)


def main():
    from ohsome2label import tile

    cfg = r"./config/config.yaml"
    schema = r"./config/schema.yaml"
    p = Parser(cfg, schema)
    config = p.parse()
    print(tile.Bbox(*config.bboxes))


if __name__ == "__main__":
    main()
