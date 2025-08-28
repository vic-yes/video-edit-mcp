import numpy as np


def saturation(clip, factor):
    return clip.fl_image(lambda pic: 
        (np.dot(pic[..., :3], [0.2989, 0.5870, 0.1140])[:, :, np.newaxis] + 
         factor * (pic.astype(np.float32) - np.dot(pic[..., :3], [0.2989, 0.5870, 0.1140])[:, :, np.newaxis]))
        .clip(0, 255).astype(np.uint8))