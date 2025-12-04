"""
Quản lý mô hình YOLO
"""
import os
import tkinter.messagebox as messagebox
from ultralytics import YOLO
from .config import MODEL_PATH, DEFAULT_SETTINGS


class DetectionModel:
    """Lớp quản lý mô hình phát hiện YOLO"""

    def __init__(self):
        self.model = None
        self.model_name = None
        self.class_names = {}

    def load(self, model_path=None):
        """Tải mô hình YOLO"""
        try:
            if model_path and os.path.exists(model_path):
                self.model = YOLO(model_path)
                self.model_name = os.path.basename(model_path)
            else:
                # Thử tải mô hình mặc định
                try:
                    self.model = YOLO('yolov8n.pt')
                    self.model_name = 'yolov8n.pt'
                except:
                    # Tải từ ultralytics hub
                    self.model = YOLO('yolov8n.pt')
                    self.model_name = 'yolov8n.pt'

            if self.model:
                self.class_names = self.model.names
                print(f"✅ Mô hình {self.model_name} đã được tải thành công!")
                print(f"   Số lớp: {len(self.class_names)}")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Lỗi khi tải mô hình: {e}")

            if DEFAULT_SETTINGS['auto_download_model']:
                try:
                    messagebox.showinfo("Thông báo",
                        "Đang tải mô hình YOLO từ internet. Vui lòng chờ...")
                    self.model = YOLO('yolov8n.pt')
                    self.model_name = 'yolov8n.pt'
                    self.class_names = self.model.names
                    return True
                except:
                    messagebox.showerror("Lỗi",
                        "Không thể tải mô hình. Vui lòng kiểm tra kết nối internet.")
                    return False
            else:
                messagebox.showerror("Lỗi",
                    "Không thể tải mô hình. Vui lòng kiểm tra đường dẫn.")
                return False

    def predict(self, image, confidence=0.5):
        """Dự đoán trên ảnh"""
        if self.model is None:
            raise ValueError("Mô hình chưa được tải!")

        try:
            results = self.model(image, conf=confidence, verbose=False)
            return results[0] if results else None
        except Exception as e:
            print(f"Lỗi khi dự đoán: {e}")
            return None

    def get_class_names(self):
        """Lấy tên các lớp"""
        return self.class_names

    def is_agricultural_product(self, class_name):
        """Kiểm tra xem có phải sản phẩm nông nghiệp không"""
        from .config import AGRICULTURAL_PRODUCTS
        return class_name in AGRICULTURAL_PRODUCTS

    def is_loaded(self):
        """Kiểm tra xem mô hình đã được tải chưa"""
        return self.model is not None

    def get_supported_products(self):
        """Lấy danh sách sản phẩm được hỗ trợ"""
        from .config import AGRICULTURAL_PRODUCTS
        return AGRICULTURAL_PRODUCTS