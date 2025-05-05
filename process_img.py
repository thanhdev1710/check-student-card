from fastapi import UploadFile
import cv2
import numpy as np

# ----- Image processing utilities -----
def read_image(uploaded_file: UploadFile) -> np.ndarray | None:
    try:
        image_data = uploaded_file.file.read()
        img_array = np.frombuffer(image_data, dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except:
        return None

def resize_if_needed(image: np.ndarray, max_dim: int = 800) -> np.ndarray:
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        return cv2.resize(image, (int(w * scale), int(h * scale)))
    return image

def is_image_clear(image: np.ndarray, threshold: float = 120) -> bool:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    return sharpness >= threshold

def enhance_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 10
    )
