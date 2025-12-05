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

        # Các bước tiền xử lý mặc định
        self.preprocessing_steps = {
            'resize': True,
            'enhance_contrast': True,
            'denoise': True,
            'sharpen': False,
            'normalize': True
        }

    def set_preprocessing_config(self, **kwargs):
        """Cấu hình các bước tiền xử lý"""
        for key, value in kwargs.items():
            if key in self.preprocessing_steps:
                self.preprocessing_steps[key] = value

    def preprocess_image(self, image, target_size=(800, 600)):
        """Áp dụng các bước tiền xử lý ảnh"""
        processed = image.copy()

        # 1. Resize ảnh (giữ tỷ lệ)
        if self.preprocessing_steps['resize'] and target_size:
            h, w = processed.shape[:2]
            target_w, target_h = target_size

            # Tính tỷ lệ và resize
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)

            # Sử dụng INTER_AREA cho downsampling, INTER_LINEAR cho upsampling
            if scale < 1.0:
                interpolation = cv2.INTER_AREA
            else:
                interpolation = cv2.INTER_LINEAR

            processed = cv2.resize(processed, (new_w, new_h), interpolation=interpolation)

        # 2. Tăng cường độ tương phản (CLAHE - Adaptive Histogram Equalization)
        if self.preprocessing_steps['enhance_contrast']:
            # Chuyển sang LAB color space
            lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # Áp dụng CLAHE cho kênh L (độ sáng)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)

            # Merge lại và chuyển về BGR
            lab_enhanced = cv2.merge([l_enhanced, a, b])
            processed = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        # 3. Khử nhiễu (Non-local Means Denoising)
        if self.preprocessing_steps['denoise']:
            # Áp dụng cho ảnh màu
            processed = cv2.fastNlMeansDenoisingColored(
                processed,
                None,
                h=10,        # Độ mạnh lọc nhiễu
                hColor=10,   # Độ mạnh lọc nhiễu màu
                templateWindowSize=7,
                searchWindowSize=21
            )

        # 4. Làm sắc nét (Unsharp Masking)
        if self.preprocessing_steps['sharpen']:
            # Tạo bộ lọc làm sắc nét
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            processed = cv2.filter2D(processed, -1, kernel)

        # 5. Chuẩn hóa cường độ pixel
        if self.preprocessing_steps['normalize']:
            # Chuyển sang float32
            processed = processed.astype(np.float32) / 255.0

            # Chuẩn hóa mean và std
            mean = np.mean(processed, axis=(0, 1, 2))
            std = np.std(processed, axis=(0, 1, 2))
            processed = (processed - mean) / (std + 1e-8)

            # Scale về khoảng [0, 1] và chuyển về uint8
            processed = np.clip(processed, -3, 3)  # Cắt bỏ ngoại lệ
            processed = (processed - processed.min()) / (processed.max() - processed.min() + 1e-8)
            processed = (processed * 255).astype(np.uint8)

        return processed

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

        # Tiền xử lý ảnh (nếu được bật trong settings)
        if settings.get('enable_preprocessing', True):
            image = self.preprocess_image(image)

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

    def get_preview_images(self, image_path):
        """Tạo ảnh preview trước/sau tiền xử lý"""
        # Đọc ảnh gốc
        original = cv2.imread(image_path)
        if original is None:
            return None

        # Áp dụng tiền xử lý
        processed = self.preprocess_image(original.copy())

        # Tạo side-by-side comparison
        h_orig, w_orig = original.shape[:2]
        h_proc, w_proc = processed.shape[:2]

        # Resize về cùng chiều cao
        if h_orig != h_proc:
            scale = h_proc / h_orig
            new_width = int(w_orig * scale)
            original_resized = cv2.resize(original, (new_width, h_proc))
        else:
            original_resized = original

        # Nối ảnh
        comparison = np.hstack([original_resized, processed])

        # Thêm tiêu đề
        title_height = 50
        comparison_with_title = np.zeros((h_proc + title_height,
                                        comparison.shape[1], 3),
                                       dtype=np.uint8)
        comparison_with_title[title_height:] = comparison

        # Vẽ tiêu đề
        cv2.putText(comparison_with_title, "BEFORE",
                   (w_orig//2 - 100, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(comparison_with_title, "AFTER",
                   (w_orig + w_proc//2 - 100, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        return {
            'original': original,
            'processed': processed,
            'comparison': comparison_with_title
        }

    def preprocess(self, image_path):
        """Tiền xử lý ảnh (cho tương thích ngược)"""
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