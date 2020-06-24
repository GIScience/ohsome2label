# ohsome2label


### Historical OpenStreetMap Objects to Machine Learning Training Samples

The **ohsome2label** offers a flexible label preparation tool for satellite machine learning applications.

- **Customized Object** - user-defined geospatial objects are retrieved and extracted from OpenStreetMap full-history data by requesting [ohsome](https://api.ohsome.org/v0.9/swagger-ui.html) web API. 
- **Various Satellite Images** - user could downloads corresponding satellite imagery tiles from different data providers.
- **Seamless Training** - object labels together with images would be packaged and converted to [Microsoft COCO](http://cocodataset.org/#format-data) .json format to provide a seamleass connection to further model training.

The output package could support directly training of popular machine learning tasks (e.g., object detection, semantic segmentation, instance segmentation etc,). 

### Package Dependencies

* python 3.6

### Installation
 ``` 
 pip install ohsome2label
 ```
### Acknowledgements

The package relies heavily on the [OpenStreetMap History Data Analysis Framework](https://github.com/GIScience/oshdb) under the [ohsome](https://api.ohsome.org) API. The idea of this package has been inspired by the excellent work of [label-maker](https://github.com/developmentseed/label-maker). Last but not lease, we would like to thanks for the contributions of OpenStreetMap volunteer to make this happen.
- OpenStreetMap historical data is licensed under the [ODbL](https://opendatacommons.org/licenses/odbl/) by the [OpenStreetMap Foundation](https://wiki.osmfoundation.org/wiki/Main_Page) (OSMF). 
