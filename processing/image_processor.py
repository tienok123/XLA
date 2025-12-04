"""
Xử lý ảnh và phân tích
"""
import cv2
import numpy as np
from core.config import AGRICULTURAL_PRODUCTS
from processing.preprocessing import preprocess_image


class ImageProcessor:
    """Lớp xử lý ảnh"""

    def __init__(self, detection_model, classifier):
        self.model = detection_model
        self.classifier = classifier

    def analyze(self, image_path, processed_image=None, settings=None):
        """Phân tích ảnh"""
        if settings is None:
            settings = {}

        # Đọc ảnh
        if processed_image is not None:
            image = processed_image.copy()
        else:
            image = cv2.imread(image_path)

        if image is None:
            raise ValueError("Không thể đọc ảnh")

        # Dự đoán với YOLO
        confidence = settings.get('confidence', 0.5)
        results = self.model.predict(image, confidence)

        if results is None:
            raise ValueError("Không có kết quả từ mô hình")

        # Xử lý kết quả
        processed = image.copy()
        detections = []

        product_type = settings.get('product_type', 'auto')
        enable_quality = settings.get('enable_quality', True)
        enable_size = settings.get('enable_size', True)

        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            cls = int(box.cls[0].cpu().numpy())
            class_name = results.names[cls]

            # Kiểm tra loại sản phẩm
            is_agri_product = class_name in AGRICULTURAL_PRODUCTS

            if (product_type == 'auto' and is_agri_product and conf > confidence) or \
               (product_type != 'auto' and class_name == product_type and conf > confidence):

                # Cắt ảnh đối tượng
                obj_img = image[int(y1):int(y2), int(x1):int(x2)]

                if obj_img.size > 0:
                    # Phân tích đối tượng
                    analysis = self.classifier.analyze_object(
                        obj_img, class_name, (x1, y1, x2, y2),
                        enable_quality, enable_size
                    )

                    detections.append(analysis)

                    # Vẽ bounding box
                    color = self.classifier.get_quality_color_bgr(analysis['quality'])
                    thickness = max(1, int(min(image.shape[:2]) / 300))
                    cv2.rectangle(processed,
                                (int(x1), int(y1)),
                                (int(x2), int(y2)),
                                color, thickness)

                    # Thêm nhãn
                    label = f"{class_name} {analysis['quality']}"
                    if enable_size:
                        label += f" {analysis['size_category']}"

                    font_scale = min(image.shape[:2]) / 1000
                    font_scale = max(0.5, min(1.0, font_scale))

                    cv2.putText(processed, label,
                              (int(x1), int(y1) - 10),
                              cv2.FONT_HERSHEY_SIMPLEX,
                              font_scale, color, thickness)

                    # Thông tin kích thước và điểm số
                    if enable_size:
                        info_text = f"Size: {analysis['size_px']:.0f}px"
                        cv2.putText(processed, info_text,
                                  (int(x1), int(y2) + 20),
                                  cv2.FONT_HERSHEY_SIMPLEX,
                                  font_scale * 0.8, color, thickness - 1)

        return {
            'processed_image': processed,
            'detections': detections,
            'original_image': image,
            'settings': settings
        }

    def preprocess(self, image_path):
        """Tiền xử lý ảnh"""
        return preprocess_image(image_path)

    def batch_process(self, image_paths, settings=None):
        """Xử lý hàng loạt ảnh"""
        if settings is None:
            settings = {}

        results = []
        for image_path in image_paths:
            try:
                result = self.analyze(image_path, None, settings)
                results.append({
                    'image_path': image_path,
                    'result': result
                })
            except Exception as e:
                print(f"Lỗi xử lý {image_path}: {e}")
                results.append({
                    'image_path': image_path,
                    'error': str(e)
                })

        return results