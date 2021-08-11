Setup the Package Dependencies
==================

By following the steps here, you would be able to install all the dependencies in your own Linux machine. (this have been tested on: Ubuntu 16.04 LST, with python 3.6 ).


-----


### Install System Level Libraries
``` shell
apt-get install build-essential libsqlite3-dev zlib1g-dev
apt-get install libgnutls28-dev
apt-get install libcurl4-openssl-dev
apt-get install protobuf-compiler python-pil python-lxml python-tk
```



### Install TensorFlow Object Detection API (from DeepVGI folks)
Here, we already put the folder into this repository. 

As alternative, you could also clone it by yourself. (Unecessary)
``` shell
git clone https://github.com/bobleegogogo/TF_objectdetection
```


### Create and Activate Virtual Environment
``` shell 
virtualenv -p python3.6 venv
source venv/bin/activate
```

### Install Python Libraries
**Either** get [requirements.txt](requirements.txt) from the repository and run
``` shell
export PYCURL_SSL_LIBRARY=gnutls
pip install -r requirements.txt
```

**or** run the installation manually
``` shell
export PYCURL_SSL_LIBRARY=gnutls
pip install --no-cache-dir pycurl
pip install pandas
pip install tensorflow==1.14.0
pip install tensorflow-gpu==1.14.0
pip install Cython
pip install jupyter
pip install matplotlib
pip install geopandas
```

### Install ohsome2label
``` shell
git clone git@github.com:GIScience/ohsome2label.git
cd ohsome2label
pip install .
```

### Install Tensorflow object detection API

First, you need to install COCO API

``` shell
cd cocoapi/PythonAPI
make
cp -r pycocotools <path_to_tensorflow_models>/models/research/
```
Then, you need to compile the protobuf

``` shell
# From models/research/
protoc object_detection/protos/*.proto --python_out=.
```
Then, add Libraries to PYTHONPATH

``` shell
# From models/research/
export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim
```
Tips: This command needs to run from every new terminal you start. If you wish to avoid running this manually, you can add it as a new line to the end of your ~/.bashrc file.



### Test Tensorflow
``` shell
python
import tensorflow as tf
hello = tf.constant('Hello, TensorFlow!')
sess = tf.Session()
print(sess.run(hello))
```
### Test Tensorflow Object Detection API
From folder models/research/, run:
``` shell
python object_detection/builders/model_builder_test.py
```


If everything works out, then you are ready for starting to build your own building detection model by following the rest of [README.md](README.md).
