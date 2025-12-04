"""
Core module cho hệ thống phát hiện và phân loại trái cây
"""

from .detection_model import DetectionModel
from .classification import FruitClassifier
from .config import (
    QUALITY_COLORS,
    QUALITY_COLORS_BGR,
    SIZE_CATEGORIES,
    CLASSIFICATION_RULES,
    AGRICULTURAL_PRODUCTS,
    PRODUCT_NAMES_VI,
    QUALITY_NAMES_VI,
    DEFAULT_SETTINGS
)

__version__ = "1.0.0"
__author__ = "Hệ Thống Phân Loại Nông Sản"

__all__ = [
    'DetectionModel',
    'FruitClassifier',
    'QUALITY_COLORS',
    'QUALITY_COLORS_BGR',
    'SIZE_CATEGORIES',
    'CLASSIFICATION_RULES',
    'AGRICULTURAL_PRODUCTS',
    'PRODUCT_NAMES_VI',
    'QUALITY_NAMES_VI',
    'DEFAULT_SETTINGS'
]