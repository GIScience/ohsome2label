# -------------------------------
# author: Hao Li, hao.li@uni-heidelberg.de
# data: 06.03.2021
# -------------------------------

r"""Convert raw Microsoft COCO dataset to TFRecord for object_detection.

1) Installation:
    pip install pycocotools-windows

2) For easy use of this script, Your coco dataset directory struture should like this :
    +Your coco dataset root
        +image
        +annotation
            -geococo.json


Example usage:
    python tf_record_from_coco.py --label_input= ./coco_repo
             --train_rd_path=data/train_xxx.record \
             --valid_rd_path=data/valid_xxx.record

    python tf_record_from_coco.py --label_input=.\tanzania --train_rd_path=tanzania\train.record --valid_rd_path=tanzania\valid.record

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from pycocotools.coco import COCO
from PIL import Image
from random import shuffle
import os, sys
import shutil
import numpy as np
import tensorflow.compat.v1 as tf
import logging
from os import makedirs
import shutil

import dataset_util

flags = tf.app.flags
flags.DEFINE_string('label_input', '', 'Root directory to image and annotation.')
flags.DEFINE_string('train_rd_path', '', 'Path to output train TFRecord')
flags.DEFINE_string('valid_rd_path', '', 'Path to output validate TFRecord')
FLAGS = flags.FLAGS


def clean_image(imgs_dir, preview_dir, annotations_filepath):
    """Clean image sets based on preview results.
    Args:
        imgs_dir: directories of coco images
        preview_dir: preselection of images samples
        annotations_filepath: file path of coco annotations file
    Return:
        no reture
    """
    coco = COCO(annotations_filepath)
    img_ids = coco.getImgIds()
    cat_ids = coco.getCatIds()

    for index, img_id in enumerate(img_ids):
        img_detail = coco.loadImgs(img_id)[0]
        img_path = os.path.join(imgs_dir, img_detail['file_name'])
        preview_path = os.path.join(preview_dir, img_detail['file_name'])
        if not os.path.isfile(preview_path):
            os.remove(img_path)


def load_coco_dection_dataset(imgs_dir, annotations_filepath):
    """Load data from dataset by pycocotools. This tools can be download from "http://mscoco.org/dataset/#download"
    Args:
        imgs_dir: directories of coco images
        annotations_filepath: file path of coco annotations file
    Return:
        coco_data: list of dictionary format information of each image
    """
    coco = COCO(annotations_filepath)
    img_ids = coco.getImgIds()
    cat_ids = coco.getCatIds()

    # if shuffle_img:
    #     shuffle(img_ids)

    coco_data = []

    nb_imgs = len(img_ids)
    for index, img_id in enumerate(img_ids):
        img_info = {}
        bboxes = []
        labels = []
        entity = []

        img_detail = coco.loadImgs(img_id)[0]
        pic_height = img_detail['height']
        pic_width = img_detail['width']

        ann_ids = coco.getAnnIds(imgIds=img_id, catIds=cat_ids)
        anns = coco.loadAnns(ann_ids)
        for ann in anns:
            bboxes_data = ann['bbox']
            cats = coco.loadCats(ann['category_id'])[0]["name"]
            bboxes_data = [bboxes_data[0] / float(pic_width), bboxes_data[1] / float(pic_height), \
                           bboxes_data[2] / float(pic_width), bboxes_data[3] / float(pic_height)]
            # the format of coco bounding boxs is [Xmin, Ymin, width, height]
            bboxes.append(bboxes_data)
            labels.append(ann['category_id'])
            entity.append(cats.encode('utf8'))

        img_path = os.path.join(imgs_dir, img_detail['file_name'])
        #preview_path = os.path.join(preview_dir, img_detail['file_name'])
        if os.path.isfile(img_path):
            img_bytes = tf.gfile.FastGFile(img_path, 'rb').read()
            img_info['pixel_data'] = img_bytes
            img_info['height'] = pic_height
            img_info['width'] = pic_width
            img_info['bboxes'] = bboxes
            img_info['labels'] = labels
            img_info['text'] = entity
            img_info['file'] = img_detail['file_name']
            coco_data.append(img_info)
    return coco_data


def dict_to_coco_example(img_data):
    """Convert python dictionary formath data of one image to tf.Example proto.
    Args:
        img_data: infomation of one image, inclue bounding box, labels of bounding box,\
            height, width, encoded pixel data.
    Returns:
        example: The converted tf.Example
    """
    bboxes = img_data['bboxes']
    xmin, xmax, ymin, ymax = [], [], [], []
    for bbox in bboxes:
        xmin.append(bbox[2])
        xmax.append(bbox[0])
        ymin.append(bbox[3])
        ymax.append(bbox[1])
    example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(img_data['height']),
        'image/width': dataset_util.int64_feature(img_data['width']),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmin),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmax),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymin),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymax),
        'image/object/class/label': dataset_util.int64_list_feature(img_data['labels']),
        'image/object/class/text': dataset_util.bytes_list_feature(img_data['text']),
        'image/encoded': dataset_util.bytes_feature(img_data['pixel_data']),
        'image/format': dataset_util.bytes_feature('jpeg'.encode('utf-8')),
        'image/object/class/file': dataset_util.bytes_feature(img_data['file'].encode('utf-8')),
    }))
    return example


def main(_):
    imgs_dir = os.path.join(FLAGS.label_input, 'images')
    preview_dir = os.path.join(FLAGS.label_input, 'preview')
    annotations_filepath = os.path.join(FLAGS.label_input, 'annotations', 'geococo.json')
    print("Convert coco val file to tf record")
    coco_data = load_coco_dection_dataset(imgs_dir, annotations_filepath)
    #clean_image(imgs_dir, preview_dir,
    #            annotations_filepath)  # optional funtion of delecting bad samples in the preview folder
    total_imgs = len(coco_data)
    split_index = int(total_imgs * 0.8)
    coco_data_train = coco_data[:split_index]
    coco_data_validation = coco_data[split_index:]
    train_dir = os.path.join(FLAGS.label_input, 'train')
    test_dir = os.path.join(FLAGS.label_input, 'test')
    if not os.path.isdir(train_dir):
        makedirs(train_dir)
    if not os.path.isdir(test_dir):
        makedirs(test_dir)

    for train_tile in coco_data_train:
        file = train_tile['file']
        tile_dir = os.path.join(imgs_dir, file)
        shutil.copy(tile_dir, train_dir)

    for valid_tile in coco_data_validation:
        file = valid_tile['file']
        tile_dir = os.path.join(imgs_dir, file)
        shutil.copy(tile_dir, test_dir)

    # write coco data to tf record
    with tf.python_io.TFRecordWriter(FLAGS.train_rd_path) as tfrecord_writer:
        for index, img_data in enumerate(coco_data_train):
            example = dict_to_coco_example(img_data)
            tfrecord_writer.write(example.SerializeToString())
        print("Converted in total {} images for training!".format(len(coco_data_train)))

    with tf.python_io.TFRecordWriter(FLAGS.valid_rd_path) as tfrecord_writer:
        for index, img_data in enumerate(coco_data_validation):
            example = dict_to_coco_example(img_data)
            tfrecord_writer.write(example.SerializeToString())

        print("Converted in total {} images for validating!".format(len(coco_data_validation)))


if __name__ == "__main__":
    tf.app.run()
