"""
GUI module cho hệ thống phát hiện và phân loại trái cây
"""

from .main_window import FruitDetectionApp
from .components import (
    ImageCanvas,
    StatisticsPanel,
    ProgressDialog,
    ToolTip
)
from .styles import (
    configure_styles,
    create_color_tags,
    apply_window_style,
    create_rounded_button
)

__all__ = [
    'FruitDetectionApp',
    'ImageCanvas',
    'StatisticsPanel',
    'ProgressDialog',
    'ToolTip',
    'configure_styles',
    'create_color_tags',
    'apply_window_style',
    'create_rounded_button'
]