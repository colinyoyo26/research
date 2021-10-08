import tensorflow as tf
from tensorflow.keras.applications import nasnet
import numpy as np
from PIL import Image
import glob
import os
import sys

def load_datas(nr_imgs: int=sys.maxsize):
    ground_truth = []
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
    img_path = os.path.join(root_path, 'images/*JPEG')
    ground_truth_path = os.path.join(root_path, 'images/ILSVRC2012_devkit_t12/data/ILSVRC2012_validation_ground_truth.txt')
    
    with open(ground_truth_path) as f:
        for y in f:
            ground_truth.append(int(y))
        
    file_names = glob.glob(img_path)
    nr_imgs = min(nr_imgs, len(file_names))
    xs = []
    ys = []
    for i in range(nr_imgs):
        img = Image.open(file_names[i]).convert('RGB')
        img = np.array(img, dtype=np.float32)
        img = tf.image.resize_with_crop_or_pad(img, 224, 224)
        img = nasnet.preprocess_input(img).numpy()
        xs.append(img)
        ys.append(ground_truth[int(file_names[i][-10:-5])] - 1)
    return np.array(xs), np.array(ys)
