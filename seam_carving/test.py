import cv2
import numpy as np

img1 = cv2.imread('result.jpg')
img2 = cv2.imread('image_result.png')

print(np.sum(img1-img2))