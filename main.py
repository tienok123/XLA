"""
File chính khởi chạy ứng dụng - CHỈ xử lý ảnh
"""
import tkinter as tk
import sys
import os

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import FruitDetectionApp


def main():
    """Hàm chính khởi chạy ứng dụng"""
    try:
        # Tạo cửa sổ chính
        root = tk.Tk()

        # Tạo ứng dụng
        print("🚀 Đang khởi động hệ thống phân loại sản phẩm nông nghiệp...")
        app = FruitDetectionApp(root)

        # Đặt icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'agriculture.ico')
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
                print("✅ Đã tải icon ứng dụng")
        except:
            print("⚠️  Không thể tải icon, sử dụng icon mặc định")

        print("✅ Ứng dụng đã sẵn sàng!")
        print("📸 Chức năng: Phân tích ảnh trái cây")

        print("-" * 50)

        # Chạy ứng dụng
        root.mainloop()

    except Exception as e:
        print(f"❌ Lỗi khởi động ứng dụng: {e}")
        import traceback
        traceback.print_exc()

        # Hiển thị thông báo lỗi
        error_window = tk.Tk()
        error_window.title("Lỗi Khởi Động Ứng Dụng")

        tk.Label(error_window, text="❌ LỖI KHỞI ĐỘNG ỨNG DỤNG",
                font=('Arial', 14, 'bold'), fg='red').pack(pady=10)

        tk.Label(error_window, text=f"Chi tiết lỗi: {str(e)}",
                font=('Arial', 10)).pack(pady=5, padx=20)

        tk.Label(error_window, text="Vui lòng kiểm tra:\n"
                "1. Đã cài đặt các thư viện cần thiết\n"
                "2. Kết nối internet để tải mô hình\n"
                "3. Cấu hình hệ thống đủ mạnh",
                font=('Arial', 10), justify=tk.LEFT).pack(pady=10, padx=20)

        tk.Button(error_window, text="Thoát", command=error_window.quit,
                 width=15).pack(pady=10)

        error_window.mainloop()


if __name__ == "__main__":
    main()