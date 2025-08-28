import cv2
import numpy as np


def emboss(frame):
    kernel = np.array([[-2, -1, 0],
                      [-1,  1, 1],
                      [ 0,  1, 2]])
    emboss_frame = cv2.filter2D(frame, -1, kernel)
    return cv2.addWeighted(emboss_frame, 0.5, frame, 0.5, 0)