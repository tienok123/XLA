"""
Tiền xử lý ảnh
"""
import cv2
import numpy as np
from skimage import exposure
import warnings

warnings.filterwarnings('ignore')


def preprocess_image(image_path):
    """Tiền xử lý ảnh để cải thiện chất lượng phân tích"""
    # Đọc ảnh
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Không thể đọc ảnh: {image_path}")

    original = image.copy()

    # 1. Chuyển đổi màu BGR -> LAB để bảo tồn độ sáng
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # 2. Cân bằng histogram trên kênh L (độ sáng)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)

    # 3. Merge lại và chuyển về BGR
    lab_eq = cv2.merge([l_eq, a, b])
    image = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)

    # 4. Giảm nhiễu với median filter
    image = cv2.medianBlur(image, 3)

    # 5. Tăng cường độ tương phản toàn cục
    image = exposure.adjust_gamma(image, gamma=0.8)

    # 6. Tăng cường độ bão hòa màu
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Tăng saturation
    s = cv2.multiply(s, 1.2)
    s = np.clip(s, 0, 255).astype(np.uint8)

    # Tăng value (độ sáng) nhẹ
    v = cv2.multiply(v, 1.1)
    v = np.clip(v, 0, 255).astype(np.uint8)

    hsv_enhanced = cv2.merge([h, s, v])
    image = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)

    # 7. Làm sắc nét với unsharp mask
    gaussian = cv2.GaussianBlur(image, (0, 0), 2.0)
    image = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)

    # 8. Điều chỉnh white balance đơn giản
    image = simple_white_balance(image)

    # 9. Giảm noise lần cuối
    image = cv2.bilateralFilter(image, 9, 75, 75)

    return image


def simple_white_balance(image):
    """Điều chỉnh white balance đơn giản"""
    # Chuyển sang LAB
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Clip và scale kênh a và b
    a = np.clip(a, 0, 255).astype(np.uint8)
    b = np.clip(b, 0, 255).astype(np.uint8)

    # Merge lại
    lab_balanced = cv2.merge([l, a, b])
    balanced = cv2.cvtColor(lab_balanced, cv2.COLOR_LAB2BGR)

    return balanced


def enhance_contrast(image):
    """Tăng cường độ tương phản"""
    # Chuyển sang YUV
    yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    y, u, v = cv2.split(yuv)

    # Cân bằng histogram trên kênh Y
    y_eq = cv2.equalizeHist(y)

    # Merge lại
    yuv_eq = cv2.merge([y_eq, u, v])
    enhanced = cv2.cvtColor(yuv_eq, cv2.COLOR_YUV2BGR)

    return enhanced


def reduce_noise(image, method='bilateral'):
    """Giảm nhiễu ảnh"""
    if method == 'bilateral':
        # Bilateral filter - giữ biên
        return cv2.bilateralFilter(image, 9, 75, 75)
    elif method == 'gaussian':
        # Gaussian blur
        return cv2.GaussianBlur(image, (5, 5), 0)
    elif method == 'median':
        # Median filter - tốt cho salt & pepper noise
        return cv2.medianBlur(image, 3)
    else:
        return image


def adjust_brightness(image, alpha=1.0, beta=0):
    """Điều chỉnh độ sáng và độ tương phản"""
    # alpha: contrast (1.0-3.0)
    # beta: brightness (0-100)
    adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return adjusted


def resize_image(image, max_size=1024):
    """Resize ảnh giữ nguyên tỷ lệ"""
    h, w = image.shape[:2]

    if max(h, w) <= max_size:
        return image

    ratio = max_size / max(h, w)
    new_h, new_w = int(h * ratio), int(w * ratio)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized