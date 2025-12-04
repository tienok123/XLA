import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from utils.file_utils import save_results

# Tạo ảnh test
test_image = np.zeros((400, 600, 3), dtype=np.uint8)
cv2.rectangle(test_image, (50, 50), (200, 200), (0, 255, 0), 2)

# Tạo detection test
test_detections = [{
    'class': 'apple',
    'bbox': [50, 50, 200, 200],
    'size_px': 150,
    'size_category': 'Trung bình',
    'quality': 'chin',
    'quality_score': 0.8,
    'width': 150,
    'height': 150,
    'area': 22500
}]

# Tạo statistics test
test_stats = {
    'total': 1,
    'quality_counts': {'chin': 1},
    'size_counts': {'Trung bình': 1},
    'defect_rate': 0.0,
    'avg_quality_score': 0.8
}

# Tạo settings test
test_settings = {
    'product_type': 'apple',
    'confidence_threshold': 0.5
}

# Test save
print("🔄 Đang test lưu file...")
result = save_results(
    processed_image=test_image,
    detections=test_detections,
    statistics=test_stats,
    settings=test_settings,
    original_image_path=None
)

if result:
    print("✅ Test thành công!")
    for key, path in result.items():
        if path:
            print(f"   {key}: {path}")
else:
    print("❌ Test thất bại!")