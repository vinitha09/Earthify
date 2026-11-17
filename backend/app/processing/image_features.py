import cv2
import numpy as np
from PIL import Image

def extract_image_features(image: Image.Image) -> dict:
    rgb = np.asarray(image.convert("RGB").resize((128, 128)), dtype=np.uint8)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    return {
        "rgb_mean": (rgb.mean((0, 1)) / 255).round(4).tolist(),
        "brightness": round(float(gray.mean() / 255), 4),
        "colour_variation": round(float(rgb.std() / 255), 4),
        "texture": round(float(cv2.Laplacian(gray, cv2.CV_32F).var() / 2000), 4),
        "green_fraction": round(float(np.mean((hsv[:, :, 0] > 25) & (hsv[:, :, 0] < 95)
                                                & (hsv[:, :, 1] > 45))), 4),
        "bright_low_saturation_fraction": round(float(np.mean((hsv[:, :, 2] > 180)
                                                                & (hsv[:, :, 1] < 50))), 4),
    }
