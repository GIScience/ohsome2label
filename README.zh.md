
# ohsome2label

[![lifecycle](https://img.shields.io/badge/lifecycle-experimental-green.svg)](https://www.tidyverse.org/lifecycle/#experimental) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
<img src="img/logo.png" width="200" />
</p>

**README** | [English](https://github.com/GIScience/ohsome2label/blob/master/README.md) | **简体中文** |

### 基于OpenStreetMap历史数据生成机器学习训练样本

ohsome2label 为卫星机器学习应用提供了灵活的样本准备工具。

- **自定义对象** - 用户自定义感兴趣的地理范围、时间标签，通过请求[ohsome API](https://api.ohsome.org/)，下载全历史OSM数据。
- **多种卫星影像支持** - 用户可以通过不同的影像API下载不同的卫星影像。
- **无缝训练** - 训练样本标注使用[Microsoft COCO](http://cocodataset.org/#format-data) 格式，可以无缝地应用于模型训练。
- **OSM数据质量评估(开发中)** - 通过分析OSM历史数据，提供内在OSM数据质量评估，用于定制更优的训练数据。

程序的输出支持多种流行的机器学习任务（如对象检测、语义分割或实例分割）。

### 依赖

* python 3.6

### 安装

 
 ``` 
 pip install ohsome2label
 ```

### 配置

如果你并不熟悉[OpenStreetMap](https://www.openstreetmap.org)，那么我们建议你先对其进行一些了解，因为本应用的矢量是基于OSM的。在开始使用ohsome2label之前，你必须定制所需要的参数配置，例如目标矩形框等。
我们提供了一个示例配置[config.yaml](config/config.yaml)。以下是详细说明：
 
```yaml

project:
  name: HD_landuse
  workspace: ./example_result
  project_time: 2020-05-18
  task: segmentation

osm:
  api: ohsome
  url: https://api.ohsome.org/v1/elements/geometry
  bboxes: [8.625,49.3711,8.7334,49.4397]
  tags:
    - {'label': 'urban', 'key': 'landuse', 'value': 'residential'}
    - {'label': 'urban', 'key': 'landuse', 'value': 'garages'}
    - {'label': 'industry', 'key': 'landuse', 'value': 'railway'}
    - {'label': 'industry', 'key': 'landuse', 'value': 'industrial'}

  timestamp: 2019-10-20
  types: polygon

image:
  img_api: bing
  img_url: http://t0.tiles.virtualearth.net/tiles/a{q}.png?g=854&mkt=en-US&token={token}
  api_token : 'YOUR OWN API TOKEN'
  zoom: 16

```

| 模块 | 参数 | 描述 |
| -- | -- | -- |
| **project** | `name` | 项目名称； |
| **project** | `workspace` | 工作空间，用于储存项目数据； |
| **project** | `project_time` | 项目创建时间； |
| **project** | `task` | 你想进行的机器学习任务，目前支持`object detection`, `segmentation`； |
| **osm** | `api` | 下载OSM数据的API，目前支持`ohsome`, `overpass`； |
| **osm** | `url` | OSM数据API相对应的API请求网址，`https://api.ohsome.org/v1/elements/geometry`, `https://lz4.overpass-api.de/api/interpreter`； |
| **osm** | `bboxes` | 目标区域的矩形框，形式为`[xmin, ymin, xmax, ymin]`, x为经度，y为维度，地图投影为WGS84； |
| **osm** | `tags` | 每个`tags`条目包含`label`, `key`和`value`三个部分，其中`label`是用户自定的名称，每个`label`可以对应多个`key`，`value`键值对，也就是目标OSM要素的键值对。若`value`为空则表示检索所有具有对应key的osm数据； |
| **osm** | `timestamp` | 所要检索的OSM历史数据的时间戳，时间戳格式为`年-月-日`； |
| **osm** | `types` | 地理对象的集合类型，现在仅支持`polygon`类型 |
| **image** | `image_api` | 卫星影象服务。现在支持`bing`,`mapbox`, `sentinel`； |
| **image** | `image_url` | 对应的影像服务地址； |
| **image** | `api_token` | 影像服务的api密钥，详情请见[`bing`](https://www.bingmapsportal.com/), [`mapbox`](https://docs.mapbox.com/help/how-mapbox-works/access-tokens/), [`sentinel`](https://services.sentinel-hub.com/oauth/auth?client_id=30cf1d69-af7e-4f3a-997d-0643d660a478&redirect_uri=https%3A%2F%2Fapps.sentinel-hub.com%2Fdashboard%2FoauthCallback.html&scope=&response_type=token&state=%252F)； |
| **image** | `zoom` | 卫星影像的缩放级别。['缩放级别'](https://wiki.openstreetmap.org/wiki/Zoom_levels)会影响影像的空间分辨率。 |

### 命令行功能

在准备好[config.yaml](config/config.yaml)后，通过下面的命令行功能，ohsome2label可以进行OSM训练数据的生成。
默认的配置文件路径为当前路径下的`config`文件夹中的`config.yaml`,对应的有一个验证文件`schema.yaml`用于验证配置文件的正确性，你也可以通过```  ohsome2label --config path/to/config.yaml --schema /path/to/schema.yaml function ``` 来制定配置文件的位置。
#### 帮助

使用`--help`来查看`ohsome2label`命令行功能的摘要
 
 ```bash
$ ohsome2label --help
-------------------------
Usage: ohsome2label [OPTIONS] COMMAND [ARGS]...

  Generate training label for deep learning via ohsomeAPI

Options:
  -v, --verbose
  --config PATH
  --schema PATH
  --help         Show this message and exit.

Commands:
  image      Download satellite image
  label      Generate tile
  printcfg   Print project config
  quality    Generate OSM quality figure
  vector     Download vector OSM data from ohsomeAPI
  visualize  Visualize of training samples


```

#### OSM矢量下载

通过[ohsome API](https://api.ohsome.org/)下载你所需的OSM历史矢量数据，返回的结果形式是geojson。

```bash
$ ohsome2label vector
-------------------------
Options:
  -v, --verbose
  --config PATH
  --schema PATH
-------------------------
Download OSM historical data into dir:

.\path\to\workspace\other\raw

```

#### 标注生成

根据所需的缩放级别，对下载后的OSM数据进行标注。不同的`ML_task`会有不同形式的标注, 例如，针对`object detection`会生成矩形框标注, `instance segmentation`则会生成对象掩模（mask）。

```bash
$ ohsome2label label
-------------------------
Options:
  -v, --verbose
  --config PATH
  --schema PATH
-------------------------

Tile the OSM data into given zoom level: 14

24it [00:00, 119.13it/s]


```

#### 影像下载

基于之前生成的标注结果，下载相应的卫星影象数据。

不同的`image_api`会有不同的`image_url`:

- Bing: `http://t0.tiles.virtualearth.net/tiles/a{q}.png?g=854&mkt=en-US&token={token}` 
- Mapbox: `http://a.tiles.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token={token}` 
- Sentinel: `https://services.sentinel-hub.com/ogc/wms/{token}?showLogo=false&service=WMS&request=GetMap&layers=ALL-BAND&styles=&format=image%2Ftiff&transparent=1&version=1.1.1&maxcc=20&time=2015-01-01%2F2020-01-01&priority=mostRecent&height=256&width=256&srs=EPSG%3A3857&bbox={bbox}` 
- Custom API: 仅支持在`image_url`中指定x,y,z和token。

```bash
$ ohsome2label image 
-------------------------
Options:
  -v, --verbose
  --config PATH
  --schema PATH
-------------------------
Start download satellite image!

100%|███████████████████████████████████| 24/24 [00:03<00:00,  6.57it/s]


```

#### 预览可视化

预览生成的OSM标注影像以及下载的卫星影象。该命令接受如下的参数：
- `-n` 或 `--num`: 预览瓦片的数量(默认为`50`)。
- `-t` 或 `--type`: 预览的形式，目前支持`combined`和`overlay`(默认为`combined`) 。


```bash
$ ohsome2label visualize -n 10
-------------------------
Options:
  -v, --verbose
  --config PATH
  --schema PATH
-------------------------
start visualize 10 pictures!

Visualization mode: combined the satellite image with OpenStreetMap features.


```
在默认示例中，将获得海德堡有关urban和industry的土地利用类别的训练样本。

<p align="center">
<img src="img/example.png" width="600" />
</p>

#### 数据质量

根据历史OSM数据生成内在质量指示，从而深入了解OSM训练样本的内在质量。
```bash
ohsome2label quality
-------------------------
Options:
  -v, --verbose
  --config PATH
  --schema PATH
-------------------------
100%|███████████████████████████████████| 3/3 [01:48<00:00, 36.24s/it]

```
作为默认的海德堡示例的示例，我们提供了三个内在质量指标：1. OSM多边形要素区域的密度（每平方公里内的OSM多边形面积）； 2. OSM多边形要素数量的密度（每平方公里内的OSM元素数） 3. OSM用户的密度（每平方公里内的贡献者数量。

<p align="center">
<img src="img/area_density.jpg" width="600" />
</p>

#### 输出配置

用户可以使用`printcfg`来查看该项目的配置。

```bash
$ ohsome2label printcfg
-------------------------
Options:
  -v, --verbose
  --config PATH
  --schema PATH
-------------------------
# # # # # # # # # # #  CONFIG  # # # # # # # # # # #
{'_config': {'image': {'api_token': '', 'img_api': 'bing', 'zoom': 16},
             'osm': {'api': 'ohsome',
                     'bboxes': [8.625, 49.3711, 8.7334, 49.4397],
                     'tags': [{'key': 'landuse',
                               'label': 'urban',
                               'value': 'residential'},
                              {'key': 'landuse',
                               'label': 'urban',
                               'value': 'garages'},
                              {'key': 'landuse',
                               'label': 'industry',
                               'value': 'railway'},
                              {'key': 'landuse',
                               'label': 'industry',
                               'value': 'industrial'}],
                     'timestamp': datetime.date(2019, 10, 20),
                     'types': 'polygon',
                     'url': 'https://api.ohsome.org/v1/elements/geometry'},
             'project': {'name': 'HD_landuse',
                         'project_time': datetime.date(2020, 5, 18),
                         'task': 'segmentation',
                         'workspace': './example_result'}}}

# # # # # # # # # # # #  END  # # # # # # # # # # # #

```


### 致谢

本应用大量依赖于[Ohsome API](https://api.ohsome.org)，且本应用的想法受到了[label-maker](https://github.com/developmentseed/label-maker)出色工作的启发，最后我们还要感谢OSM志愿者的贡献！
- 2012-09-12后发布的OSM数据的使用遵循[ODbL 1.0](https://opendatacommons.org/licenses/odbl/)协议，在那之前的OSM数据的使用则遵循[CC-BY-SA 2.0](https://planet.osm.org/cc-by-sa/)协议。
