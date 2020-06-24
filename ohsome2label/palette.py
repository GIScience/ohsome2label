""" create palette for burning tile"""
import random
import json
import os


class palette:
    """palette for burning tile."""

    def __init__(self, tags=None, path="colors"):
        self.path = path
        if tags is None:
            self.load()
        else:
            self.count = len(tags)
            self._colors = {}

            if os.path.exists(self.path):
                self.load()
            else:
                _label = []
                if len(tags) == 1:
                    color = "#FFFFFF"
                    self._colors[tags[0]["label"]] = color
                else:
                    for tag in tags:
                        if tag["label"] not in _label:
                            _label.append(tag["label"])
                    for label in _label:
                        color = self.generate()
                        while color in self._colors.values():
                            color = self.generate()
                        self._colors[label] = color
                self.dump()

    def generate(self):
        """generate a random color"""
        # hex(16777215) = FFFFFF
        # not include #000000
        hex_color = "%06x" % random.randint(1, 0xFFFFFF)
        return "#" + str(hex_color)

    def color(self, label):
        """get palette colors"""
        return self._colors[str(label)]

    def load(self, path=''):
        if path == '':
            path = self.path
        with open(path, "r") as f:
            self._colors = json.load(f)

    def dump(self):
        with open(self.path, "w") as f:
            f.write(json.dumps(self._colors))
