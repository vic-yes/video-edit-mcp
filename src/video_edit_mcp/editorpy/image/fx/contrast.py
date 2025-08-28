import numpy as np


def contrast(clip, factor):
    return clip.fl_image(lambda pic: 
        (np.mean(pic, axis=(0, 1)) + factor * (pic.astype(np.float32) - np.mean(pic, axis=(0, 1))))
        .clip(0, 255).astype(np.uint8))