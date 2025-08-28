import cv2
import numpy as np


def sharpen(clip):
    kernel = np.array([[-1, -1, -1],
                      [-1,  9, -1],
                      [-1, -1, -1]])
    return cv2.filter2D(clip, -1, kernel)