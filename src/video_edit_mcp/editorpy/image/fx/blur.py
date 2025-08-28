import cv2


def blur(clip, kernel_size=(15, 15)):
    blurred_frame = cv2.GaussianBlur(clip, kernel_size, sigmaX=2, sigmaY=2)
    return blurred_frame