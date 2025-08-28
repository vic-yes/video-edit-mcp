import numpy as np
import cv2



def sepia(clip):
    # sepia 转换矩阵
    sepia_filter = np.array([
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])

    sepia_frame = cv2.transform(clip, sepia_filter)
    return np.clip(sepia_frame, 0, 255).astype(np.uint8)