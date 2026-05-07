import cv2
import numpy as np
from scipy.fftpack import dct, idct

# قراءة الصورة
img = cv2.imread("image.jpg", 0)

# تحويلها float
img = np.float32(img)

print("Image chargée :", img.shape)
