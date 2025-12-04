"""
Cấu hình và constants cho ứng dụng - PHIÊN BẢN SỬA LỖI
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / 'data' / 'models'
OUTPUTS_DIR = BASE_DIR / 'data' / 'outputs'

# Tạo thư mục nếu chưa tồn tại
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Model settings
MODEL_NAME = 'yolov8n.pt'
MODEL_PATH = MODELS_DIR / MODEL_NAME

# Màu sắc phân loại (HEX)
QUALITY_COLORS = {
    'xanh': '#32CD32',      # Xanh lá - LimeGreen
    'chin': '#FF4500',      # Đỏ cam - OrangeRed
    'hong': '#8B4513',      # Nâu - SaddleBrown
    'tot': '#008000',       # Tốt - xanh đậm - Green
    'trung_binh': '#FFA500', # Trung bình - cam - Orange
    'kem': '#A52A2A',       # Kém - nâu đỏ - Brown
    'unknown': '#808080'    # Không xác định - xám
}

# Màu BGR cho OpenCV (B, G, R)
QUALITY_COLORS_BGR = {
    'xanh': (50, 205, 50),      # Xanh lá
    'chin': (0, 69, 255),       # Đỏ cam
    'hong': (19, 69, 139),      # Nâu
    'tot': (0, 128, 0),         # Tốt
    'trung_binh': (0, 165, 255), # Trung bình
    'kem': (42, 42, 165),       # Kém
    'unknown': (128, 128, 128)  # Không xác định
}

# Kích thước phân loại (pixel)
SIZE_CATEGORIES = {
    'nho': {'min': 0, 'max': 30, 'label': 'Nhỏ'},
    'trung_binh': {'min': 30, 'max': 60, 'label': 'Trung bình'},
    'to': {'min': 60, 'max': 100, 'label': 'To'},
    'rat_to': {'min': 100, 'max': 200, 'label': 'Rất to'}
}

# ============================================================================
# QUY TẮC PHÂN LOẠI MÀU SẮC THEO HSV - SỬA LỖI CẤU TRÚC
# ============================================================================

CLASSIFICATION_RULES = {

    # ==================== TÁO ====================
    'apple': {
        'color_ranges': {
            'xanh': [  # TÁO XANH - Một khoảng
                [(35, 40, 40), (85, 255, 220)]
            ],
            'chin': [  # TÁO CHÍN (đỏ, hồng) - Ba khoảng
                [(0, 50, 50), (10, 255, 255)],    # Đỏ tươi
                [(170, 50, 50), (179, 255, 255)], # Đỏ đậm
                [(150, 40, 40), (170, 255, 220)]  # Hồng ngả đỏ
            ],
            'hong': [  # TÁO HỎNG (nâu, thâm) - Ba khoảng
                [(10, 20, 20), (30, 150, 150)],   # Vàng-nâu nhạt
                [(0, 0, 0), (179, 50, 80)],       # Tối
                [(0, 0, 80), (179, 30, 150)]      # Xám, ít màu
            ],
            'trung_binh': [  # TÁO CHƯA CHÍN HẲN - Hai khoảng
                [(20, 40, 40), (35, 255, 220)],   # Vàng-xanh
                [(85, 30, 40), (120, 255, 200)]   # Xanh dương nhạt
            ]
        }
    },

    # ==================== CHUỐI ====================
    'banana': {
        'color_ranges': {
            'xanh': [  # CHUỐI XANH - Một khoảng
                [(35, 40, 40), (85, 255, 220)]
            ],
            'chin': [  # CHUỐI CHÍN (vàng) - Hai khoảng
                [(20, 50, 100), (30, 255, 255)],  # Vàng tươi
                [(15, 40, 80), (25, 255, 220)]    # Vàng nhạt
            ],
            'hong': [  # CHUỐI HỎNG (nâu, đen) - Ba khoảng
                [(0, 30, 30), (15, 200, 150)],    # Nâu-vàng
                [(0, 0, 0), (179, 50, 80)],       # Đen, tối
                [(0, 0, 80), (179, 30, 150)]      # Xám
            ],
            'trung_binh': [  # CHUỐI CHƯA CHÍN HẲN - Hai khoảng
                [(25, 40, 40), (35, 255, 200)],   # Xanh-vàng
                [(85, 30, 40), (120, 200, 180)]   # Phản chiếu xanh
            ]
        }
    },

    # ==================== CAM ====================
    'orange': {
        'color_ranges': {
            'xanh': [  # CAM XANH - Một khoảng
                [(35, 40, 40), (85, 255, 220)]
            ],
            'chin': [  # CAM CHÍN (cam) - Ba khoảng
                [(5, 50, 80), (15, 255, 255)],    # Cam tươi
                [(0, 50, 80), (10, 255, 220)],    # Cam-đỏ
                [(15, 40, 80), (25, 255, 220)]    # Cam-vàng
            ],
            'hong': [  # CAM HỎNG (nâu, thâm) - Ba khoảng
                [(0, 20, 20), (10, 150, 150)],    # Nâu đỏ
                [(10, 20, 20), (25, 150, 150)],   # Nâu vàng
                [(0, 0, 0), (179, 50, 80)]        # Tối
            ],
            'trung_binh': [  # CAM CHƯA CHÍN HẲN - Hai khoảng
                [(20, 40, 40), (35, 255, 200)],   # Vàng-xanh
                [(25, 40, 40), (35, 255, 180)]    # Vàng nhạt
            ]
        }
    }
}

# Ánh xạ tên tiếng Việt
PRODUCT_NAMES_VI = {
    'tomato': 'Cà chua',
    'apple': 'Táo',
    'banana': 'Chuối',
    'orange': 'Cam'
}

# Ánh xạ chất lượng tiếng Việt
QUALITY_NAMES_VI = {
    'xanh': 'Xanh',
    'chin': 'Chín',
    'hong': 'Hỏng',
    'tot': 'Tốt',
    'trung_binh': 'Trung bình',
    'kem': 'Kém',
    'unknown': 'Không xác định'
}

# Sản phẩm nông nghiệp được hỗ trợ
AGRICULTURAL_PRODUCTS = ['apple', 'banana', 'orange', 'tomato']

# Cài đặt mặc định
DEFAULT_SETTINGS = {
    'confidence_threshold': 0.5,
    'enable_quality_analysis': True,
    'enable_size_analysis': True,
    'selected_product': 'tomato',
    'auto_download_model': True,
    'color_classification_threshold': 0.15  # Ngưỡng phân loại màu (15%)
}

# ============================================================================
# HÀM TIỆN ÍCH CHO PHÂN LOẠI MÀU
# ============================================================================

def get_hsv_description(h, s, v):
    """Mô tả màu sắc từ giá trị HSV"""
    descriptions = []

    # Mô tả Hue (Màu sắc)
    if h < 15 or h > 165:
        descriptions.append("Đỏ")
    elif 15 <= h < 25:
        descriptions.append("Cam")
    elif 25 <= h < 35:
        descriptions.append("Vàng cam")
    elif 35 <= h < 45:
        descriptions.append("Vàng")
    elif 45 <= h < 75:
        descriptions.append("Xanh lá")
    elif 75 <= h < 105:
        descriptions.append("Xanh dương")
    elif 105 <= h < 135:
        descriptions.append("Tím")
    elif 135 <= h < 165:
        descriptions.append("Hồng")

    # Mô tả Saturation (Độ bão hòa)
    if s < 30:
        descriptions.append("Nhạt")
    elif 30 <= s < 100:
        descriptions.append("Trung bình")
    elif 100 <= s < 180:
        descriptions.append("Đậm")
    else:
        descriptions.append("Rất đậm")

    # Mô tả Value (Độ sáng)
    if v < 50:
        descriptions.append("Tối")
    elif 50 <= v < 150:
        descriptions.append("Bình thường")
    elif 150 <= v < 200:
        descriptions.append("Sáng")
    else:
        descriptions.append("Rất sáng")

    return " ".join(descriptions)

# ============================================================================
# CẤU HÌNH DEBUG VÀ HIỂN THỊ
# ============================================================================

DEBUG_COLORS = True  # Bật/tắt debug màu sắc

if DEBUG_COLORS:
    print("\n" + "="*60)
    print("CẤU HÌNH PHÂN LOẠI MÀU HSV - ĐÃ SỬA LỖI")
    print("="*60)

    for product, rules in CLASSIFICATION_RULES.items():
        print(f"\n📦 {PRODUCT_NAMES_VI.get(product, product).upper()}:")
        for quality, ranges in rules['color_ranges'].items():
            print(f"   {QUALITY_NAMES_VI.get(quality, quality)}:")
            for lower, upper in ranges:
                print(f"      {lower} -> {upper}")

    print("\n📊 MÀU SẮC PHÂN LOẠI:")
    for quality, color in QUALITY_COLORS.items():
        print(f"   {QUALITY_NAMES_VI.get(quality, quality):12s}: {color}")

    print("="*60 + "\n")