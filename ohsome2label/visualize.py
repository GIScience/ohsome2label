import os

import numpy as np
from PIL import Image


def load_image(infilename):
    img = Image.open(infilename)
    img.load()
    data = np.asarray(img)
    return data


def visualize_combined(workspace, num):
    img_dir = workspace.img
    label_dir = workspace.label
    preview_dir = workspace.preview
    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir)
    fileist = [file for file in os.listdir(img_dir) if file.endswith(".png")]
    num = num if num <= len(fileist) else len(fileist)
    print(num)
    for i in range(num):
        file = fileist[i]
        f_img = os.path.join(img_dir, file)
        f_label = os.path.join(label_dir, file)
        imagery = load_image(f_img)
        label = load_image(f_label)
        combined = np.hstack((imagery, label))
        combined_image = Image.fromarray(combined)
        f_preview = os.path.join(preview_dir, file)
        combined_image.save(f_preview)


def visualize_overlay(workspace, num):
    img_dir = workspace.img
    label_dir = workspace.label
    preview_dir = workspace.preview
    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir)
    fileist = [file for file in os.listdir(img_dir) if file.endswith(".png")]
    num = num if num <= len(fileist) else len(fileist)
    for i in range(num):
        file = fileist[i]
        f_img = os.path.join(img_dir, file)
        f_label = os.path.join(label_dir, file)
        imagery = Image.open(f_img)
        label = Image.open(f_label)
        background = imagery.convert("RGBA")
        overlay = label.convert("RGBA")
        overlay_image = Image.blend(background, overlay, 0.5)
        f_preview = os.path.join(preview_dir, file)
        overlay_image.save(f_preview)
