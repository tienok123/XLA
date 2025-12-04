"""
Logic phân loại sản phẩm - PHIÊN BẢN SỬA LỖI
"""
import cv2
import numpy as np
from collections import defaultdict
from .config import (
    CLASSIFICATION_RULES,
    SIZE_CATEGORIES,
    QUALITY_COLORS_BGR,
    QUALITY_NAMES_VI,
    DEFAULT_SETTINGS,
    DEBUG_COLORS
)


class FruitClassifier:
    """Lớp phân loại trái cây với phân loại màu HSV cải tiến"""

    def __init__(self):
        self.rules = CLASSIFICATION_RULES
        self.size_categories = SIZE_CATEGORIES
        self.color_threshold = DEFAULT_SETTINGS['color_classification_threshold']

    def classify_quality(self, obj_img, class_name):
        """Phân loại chất lượng dựa trên màu sắc HSV - PHIÊN BẢN SỬA LỖI"""
        if class_name not in self.rules:
            if DEBUG_COLORS:
                print(f"⚠️  Class '{class_name}' không có trong rules")
            return 'unknown'

        try:
            # Kiểm tra ảnh đầu vào
            if obj_img is None or obj_img.size == 0:
                if DEBUG_COLORS:
                    print(f"⚠️  Ảnh rỗng cho class '{class_name}'")
                return 'unknown'

            # Chuyển đổi sang HSV
            hsv = cv2.cvtColor(obj_img, cv2.COLOR_BGR2HSV)

            # DEBUG: Tính giá trị HSV trung bình
            if DEBUG_COLORS:
                h_mean = np.mean(hsv[:, :, 0])
                s_mean = np.mean(hsv[:, :, 1])
                v_mean = np.mean(hsv[:, :, 2])
                print(f"\n🔍 DEBUG - {class_name}:")
                print(f"   Kích thước ảnh: {obj_img.shape}")
                print(f"   HSV trung bình: H={h_mean:.1f}, S={s_mean:.1f}, V={v_mean:.1f}")
                print(f"   H range: {hsv[:, :, 0].min():.1f}-{hsv[:, :, 0].max():.1f}")
                print(f"   S range: {hsv[:, :, 1].min():.1f}-{hsv[:, :, 1].max():.1f}")
                print(f"   V range: {hsv[:, :, 2].min():.1f}-{hsv[:, :, 2].max():.1f}")

            # Lấy quy tắc cho loại trái cây
            rules = self.rules[class_name]
            color_ranges = rules['color_ranges']

            # Tìm màu chiếm ưu thế
            max_ratio = 0
            best_quality = 'unknown'
            quality_ratios = {}

            for quality, ranges_list in color_ranges.items():
                # ranges_list là list các cặp (lower, upper)
                total_ratio = 0

                for ranges in ranges_list:
                    # ranges là một cặp (lower, upper)
                    lower, upper = ranges
                    lower_bound = np.array(lower, dtype=np.uint8)
                    upper_bound = np.array(upper, dtype=np.uint8)

                    # Tạo mask cho khoảng màu này
                    mask = cv2.inRange(hsv, lower_bound, upper_bound)

                    # Tính tỷ lệ pixel khớp
                    total_pixels = obj_img.shape[0] * obj_img.shape[1]
                    if total_pixels > 0:
                        matching_pixels = np.sum(mask > 0)
                        ratio = matching_pixels / total_pixels
                        total_ratio += ratio

                quality_ratios[quality] = total_ratio

                if total_ratio > max_ratio:
                    max_ratio = total_ratio
                    best_quality = quality

            # DEBUG: Hiển thị tỷ lệ các màu
            if DEBUG_COLORS:
                print(f"   Tỷ lệ các chất lượng:")
                for quality, ratio in sorted(quality_ratios.items(), key=lambda x: x[1], reverse=True):
                    if ratio > 0:
                        print(f"     {quality}: {ratio:.3f}")

            # Kiểm tra ngưỡng
            if max_ratio > self.color_threshold:
                if DEBUG_COLORS:
                    print(f"   ✅ Kết quả: {best_quality} (tỷ lệ: {max_ratio:.3f})")
                return best_quality
            else:
                if DEBUG_COLORS:
                    print(f"   ⚠️  Không đạt ngưỡng: {max_ratio:.3f} < {self.color_threshold}")

                # Fallback: Phân loại dựa trên Hue trung bình
                return self.classify_by_hue_average(hsv, class_name)

        except Exception as e:
            if DEBUG_COLORS:
                print(f"❌ Lỗi khi phân loại chất lượng: {e}")
                import traceback
                traceback.print_exc()
            return 'unknown'

    def classify_by_hue_average(self, hsv, class_name):
        """Phân loại dựa trên Hue trung bình (fallback)"""
        try:
            # Tính Hue trung bình (bỏ qua các pixel quá tối/sáng)
            mask_valid = (hsv[:, :, 1] > 30) & (hsv[:, :, 2] > 30) & (hsv[:, :, 2] < 220)
            if np.any(mask_valid):
                hue_mean = np.mean(hsv[mask_valid, 0])
            else:
                hue_mean = np.mean(hsv[:, :, 0])

            if DEBUG_COLORS:
                print(f"   🎨 Fallback - Hue trung bình: {hue_mean:.1f}")

            # Phân loại dựa trên Hue
            if class_name == 'tomato':
                if hue_mean < 20 or hue_mean > 160:
                    return 'chin'  # Đỏ
                elif 35 <= hue_mean < 85:
                    return 'xanh'  # Xanh lá
                elif 20 <= hue_mean < 35:
                    return 'trung_binh'  # Vàng-cam
                else:
                    return 'hong'  # Màu lạ

            elif class_name == 'apple':
                if hue_mean < 20 or hue_mean > 160:
                    return 'chin'  # Đỏ
                elif 35 <= hue_mean < 85:
                    return 'xanh'  # Xanh lá
                elif 20 <= hue_mean < 35:
                    return 'trung_binh'  # Vàng
                else:
                    return 'hong'

            elif class_name == 'banana':
                if 20 <= hue_mean < 35:
                    return 'chin'  # Vàng
                elif 35 <= hue_mean < 85:
                    return 'xanh'  # Xanh lá
                elif hue_mean < 20 or hue_mean > 160:
                    return 'hong'  # Đỏ/nâu
                else:
                    return 'trung_binh'

            elif class_name == 'orange':
                if 5 <= hue_mean < 25:
                    return 'chin'  # Cam
                elif 35 <= hue_mean < 85:
                    return 'xanh'  # Xanh lá
                elif hue_mean < 5 or hue_mean > 160:
                    return 'hong'  # Đỏ đậm
                else:
                    return 'trung_binh'

            return 'unknown'

        except Exception as e:
            if DEBUG_COLORS:
                print(f"❌ Lỗi fallback: {e}")
            return 'unknown'

    def classify_size(self, size_px):
        """Phân loại theo kích thước"""
        for category, specs in self.size_categories.items():
            if specs['min'] <= size_px < specs['max']:
                return specs['label']
        return 'Không xác định'

    def calculate_quality_score(self, obj_img):
        """Tính điểm chất lượng tổng thể"""
        try:
            if obj_img.size == 0:
                return 0.5

            score = 0.5  # Điểm cơ bản

            # 1. Đánh giá độ tương phản
            gray = cv2.cvtColor(obj_img, cv2.COLOR_BGR2GRAY)
            contrast = gray.std()
            if contrast > 60:
                score += 0.2
            elif contrast > 40:
                score += 0.1
            elif contrast < 20:
                score -= 0.1

            # 2. Đánh giá độ sáng
            brightness = gray.mean()
            if 120 < brightness < 180:
                score += 0.2
            elif 80 < brightness < 220:
                score += 0.1
            elif brightness < 50 or brightness > 230:
                score -= 0.1

            # 3. Đánh giá độ bão hòa màu
            hsv = cv2.cvtColor(obj_img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1].mean()
            if saturation > 100:
                score += 0.1
            elif saturation < 30:
                score -= 0.1

            # 4. Đánh giá màu sắc trung bình
            hue_mean = np.mean(hsv[:, :, 0])
            # Màu "tươi" (đỏ, cam, vàng) có điểm cao hơn
            if (hue_mean < 25 or hue_mean > 160):  # Đỏ
                score += 0.1
            elif 20 <= hue_mean < 35:  # Vàng-cam
                score += 0.15

            # Giới hạn trong khoảng 0-1
            return max(0.0, min(1.0, score))

        except Exception as e:
            if DEBUG_COLORS:
                print(f"Lỗi tính điểm chất lượng: {e}")
            return 0.5

    def get_quality_color_bgr(self, quality):
        """Lấy màu BGR dựa trên chất lượng"""
        return QUALITY_COLORS_BGR.get(quality, (128, 128, 128))

    def get_quality_name_vi(self, quality):
        """Lấy tên tiếng Việt của chất lượng"""
        return QUALITY_NAMES_VI.get(quality, 'Không xác định')

    def analyze_object(self, obj_img, class_name, bbox, enable_quality=True, enable_size=True):
        """Phân tích chi tiết một đối tượng"""
        x1, y1, x2, y2 = bbox

        # Tính kích thước
        width = x2 - x1
        height = y2 - y1
        size_px = max(width, height)

        # Phân loại
        size_category = self.classify_size(size_px) if enable_size else 'Không xác định'
        quality = self.classify_quality(obj_img, class_name) if enable_quality else 'unknown'
        quality_score = self.calculate_quality_score(obj_img)

        return {
            'class': class_name,
            'bbox': bbox,
            'size_px': size_px,
            'size_category': size_category,
            'quality': quality,
            'quality_score': quality_score,
            'width': width,
            'height': height,
            'area': width * height
        }