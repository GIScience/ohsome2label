import requests
from datetime import date, timedelta
import matplotlib
import matplotlib.pyplot as plt
from urllib.parse import urljoin
from ohsome2label.config import o2l_config, workspace, Parser
from tqdm import tqdm
import os


def generate_filter(tag):
    """generate filter for OHSOME Aggregation API

    Args:
        tag (dict): label tag

    Returns:
        str: OHSOME Aggregation filter
    """
    filters = ["geometry:polygon"]
    k = tag.get("key")
    v = tag.get("value", "")
    if v:
        filters.append("{}={}".format(k, v))
    else:
        filters.append("{k}=* and {k}!=no".format(k=k))
    return " and ".join(filters)


def get_osm_quality(cfg: o2l_config, workspace: workspace):
    """Draw OSM intrinsic quality figure according to OHSOMEAPI

    Args:
        cfg (o2l_config): ohsome2label config
        workspace (workspace): ohsome2label workspace
    """
    url = cfg.url
    end_time = cfg.timestamp
    start_time = end_time - timedelta(days=365 * 3 + 1)
    start_time = date(2012, 1, 1) if start_time < date(2012, 1, 1) else start_time
    delta = "P6M"
    data = {
        "bboxes": "{},{},{},{}".format(*cfg.bboxes),
        "format": "json",
        "time": "{}/{}/{}".format(start_time, end_time, delta),
        "filter": "",
    }
    quality_items = {
        "area_density": "../elements/area/density",
        "count_density": "../elements/count/density",
        "user_density": "../users/count/density",
    }
    for item in tqdm(quality_items):
        fname = os.path.join(workspace.quality, item + ".jpg")
        api = urljoin(url, quality_items[item])
        res = {}
        x = []
        for tag in cfg.tags:
            label = tag["label"]
            k = tag["key"]
            v = tag.get("value", "")

            data["filter"] = generate_filter(tag)
            response = requests.post(api, data=data)
            r_json = response.json()

            if "groupByResult" in r_json:
                result = r_json["groupByResult"][0]["result"]
            elif "result" in r_json:
                result = r_json["result"]

            if len(x) != len(result):
                for r in result:
                    if "timestamp" in r:
                        x.append(r["timestamp"][2:7])
                    elif "fromTimestamp" in r:
                        x.append(r["fromTimestamp"][2:7])

            if len(res.get(label, list())):
                _result = [r["value"] for r in result]
                res[label] = [ori + r for ori, r in zip(res[label], _result)]
            else:
                res[label] = [r["value"] for r in result]

        for y in res:
            plt.plot(x, res[y], label=y)
        plt.title(item)
        plt.ylabel("density")
        plt.xlabel("time")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.savefig(fname, bbox_inches="tight")
        plt.close()

        with open(fname.replace("jpg", "txt"), "w") as f:
            f.write(str(x) + "\n")
            f.write(str(res) + "\n")
