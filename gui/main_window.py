"""
Cửa sổ chính của ứng dụng - KHÔNG có xử lý video
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import os
from datetime import datetime

from core import DetectionModel, FruitClassifier, DEFAULT_SETTINGS
from core.config import PRODUCT_NAMES_VI, AGRICULTURAL_PRODUCTS
from processing import ImageProcessor, preprocess_image
from gui.styles import configure_styles
from gui.components import ImageCanvas, StatisticsPanel, ProgressDialog
from utils import save_results, calculate_statistics


class FruitDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Đếm Và Phân Loại Sản Phẩm Nông Nghiệp")
        self.root.geometry("1400x800")

        # Cấu hình style
        configure_styles()

        # Khởi tạo các thành phần
        self.model = DetectionModel()
        self.classifier = FruitClassifier()
        self.image_processor = ImageProcessor(self.model, self.classifier)

        # Biến lưu trữ
        self.image_path = None
        self.processed_image = None  # Ảnh OpenCV
        self.pil_image = None        # Ảnh PIL để hiển thị
        self.detection_results = []
        self.current_stats = {}

        # Cài đặt
        self.settings = DEFAULT_SETTINGS.copy()

        # Thiết lập UI
        self.setup_ui()

        # Tải mô hình
        self.load_model()

        # Thanh trạng thái
        self.update_status("Sẵn sàng - Hệ thống phân loại sản phẩm nông nghiệp")

    def load_model(self):
        """Tải mô hình YOLO"""
        self.update_status("Đang tải mô hình YOLO...")
        if not self.model.load():
            messagebox.showerror("Lỗi", "Không thể tải mô hình. Ứng dụng có thể không hoạt động đúng.")
        else:
            self.update_status("Mô hình đã sẵn sàng")

    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Cấu hình grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Tiêu đề
        title_label = ttk.Label(
            main_frame,
            text="🌱 HỆ THỐNG ĐẾM VÀ PHÂN LOẠI SẢN PHẨM NÔNG NGHIỆP",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Tạo các thành phần UI
        self.create_control_frame(main_frame)
        self.create_image_frame(main_frame)
        self.create_results_frame(main_frame)

        # Thanh trạng thái
        self.status_bar = ttk.Label(
            main_frame,
            text="",
            style='Status.TLabel',
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    def create_control_frame(self, parent):
        """Tạo frame điều khiển bên trái"""
        self.control_frame = ttk.LabelFrame(parent, text="ĐIỀU KHIỂN & CÀI ĐẶT", padding="15")
        self.control_frame.grid(row=1, column=0, sticky=(tk.N, tk.S), padx=(0, 10))

        # Biến
        self.product_var = tk.StringVar(value=self.settings['selected_product'])
        self.quality_var = tk.BooleanVar(value=self.settings['enable_quality_analysis'])
        self.size_var = tk.BooleanVar(value=self.settings['enable_size_analysis'])
        self.confidence_var = tk.DoubleVar(value=self.settings['confidence_threshold'])

        # Phần chọn loại sản phẩm
        ttk.Label(self.control_frame, text="Loại sản phẩm:", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))

        products = [

            ("Táo", "apple"),
            ("Chuối", "banana"),
            ("Cam", "orange"),
            ("Tự động phát hiện", "auto")
        ]

        for text, value in products:
            ttk.Radiobutton(
                self.control_frame,
                text=text,
                variable=self.product_var,
                value=value
            ).pack(anchor=tk.W, pady=2)

        # Phân loại theo chất lượng
        ttk.Label(self.control_frame, text="Phân loại chất lượng:",
                 style='Header.TLabel').pack(anchor=tk.W, pady=(10, 5))

        ttk.Checkbutton(
            self.control_frame,
            text="Phân loại xanh/chín/hỏng",
            variable=self.quality_var
        ).pack(anchor=tk.W, pady=2)

        # Phân loại theo kích thước
        ttk.Checkbutton(
            self.control_frame,
            text="Phân loại theo kích thước",
            variable=self.size_var
        ).pack(anchor=tk.W, pady=2)

        # Ngưỡng tin cậy
        ttk.Label(self.control_frame, text="Ngưỡng tin cậy:",
                 style='Header.TLabel').pack(anchor=tk.W, pady=(10, 5))

        self.confidence_var.trace('w', self.on_confidence_change)
        confidence_scale = ttk.Scale(
            self.control_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.confidence_var,
            length=180
        )
        confidence_scale.pack(fill=tk.X, pady=5)

        self.conf_label = ttk.Label(self.control_frame,
                                   text=f"{self.confidence_var.get():.2f}",
                                   style='Stat.TLabel')
        self.conf_label.pack()

        # Các nút điều khiển
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        buttons = [
            ("📁 TẢI ẢNH", self.load_image),
            ("🔍 PHÂN TÍCH", self.analyze_image),
            ("📊 THỐNG KÊ", self.show_statistics),
            ("💾 LƯU KẾT QUẢ", self.save_results),
            ("⚙️ TIỀN XỬ LÝ", self.preprocess_image),
            ("🔄 RESET", self.reset_app),
            ("❌ THOÁT", self.root.quit)
        ]

        for text, command in buttons:
            btn = ttk.Button(
                btn_frame,
                text=text,
                command=command,
                style='Primary.TButton'
            )
            btn.pack(pady=3, fill=tk.X)

    def on_confidence_change(self, *args):
        """Xử lý thay đổi ngưỡng tin cậy"""
        self.conf_label.config(text=f"{self.confidence_var.get():.2f}")

    def create_image_frame(self, parent):
        """Tạo frame hiển thị ảnh"""
        self.image_frame = ttk.LabelFrame(parent, text="HÌNH ẢNH", padding="10")
        self.image_frame.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5)

        # Canvas hiển thị ảnh
        self.image_canvas = ImageCanvas(self.image_frame)
        self.canvas = self.image_canvas.get_canvas()
        self.canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Frame điều khiển ảnh
        img_control_frame = ttk.Frame(self.image_frame)
        img_control_frame.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)

        # Nút reset view
        ttk.Button(
            img_control_frame,
            text="⟲ Reset View",
            command=self.image_canvas.reset_view,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        # Thông tin ảnh
        self.image_info = ttk.Label(img_control_frame, text="Chưa có ảnh nào được tải")
        self.image_info.pack(side=tk.LEFT, padx=20)

        # Cấu hình resize
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)

    def create_results_frame(self, parent):
        """Tạo frame kết quả"""
        self.result_frame = ttk.LabelFrame(parent, text="KẾT QUẢ PHÂN TÍCH CHI TIẾT", padding="10")
        self.result_frame.grid(row=1, column=2, sticky=(tk.N, tk.S, tk.E, tk.W), padx=(5, 0))

        # Tạo notebook (tab)
        self.notebook = ttk.Notebook(self.result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab phân loại
        self.create_classification_tab()

        # Tab thống kê
        self.create_statistics_tab()

        # Tab tổng quan
        self.create_overview_tab()

        # Cấu hình resize
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)

    def create_classification_tab(self):
        """Tạo tab phân loại"""
        class_tab = ttk.Frame(self.notebook)
        self.notebook.add(class_tab, text="Phân loại")

        # Treeview
        columns = ('STT', 'Loại SP', 'Chất lượng', 'Kích thước', 'Điểm số', 'Kích thước(px)')
        self.class_tree = ttk.Treeview(class_tab, columns=columns, show='headings', height=15)

        # Đặt độ rộng cột
        col_widths = [50, 100, 100, 100, 80, 100]
        for col, width in zip(columns, col_widths):
            self.class_tree.heading(col, text=col)
            self.class_tree.column(col, width=width, anchor='center')

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(class_tab, orient=tk.VERTICAL, command=self.class_tree.yview)
        h_scrollbar = ttk.Scrollbar(class_tab, orient=tk.HORIZONTAL, command=self.class_tree.xview)
        self.class_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout
        self.class_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Cấu hình grid weights
        class_tab.columnconfigure(0, weight=1)
        class_tab.rowconfigure(0, weight=1)

    def create_statistics_tab(self):
        """Tạo tab thống kê"""
        stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(stats_tab, text="Thống kê")

        # Text widget với scrollbar
        self.stats_text = scrolledtext.ScrolledText(
            stats_tab,
            width=40,
            height=20,
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Thêm nút copy
        btn_frame = ttk.Frame(stats_tab)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(
            btn_frame,
            text="📋 Copy",
            command=self.copy_statistics,
            width=10
        ).pack(side=tk.RIGHT)

    def create_overview_tab(self):
        """Tạo tab tổng quan"""
        overview_tab = ttk.Frame(self.notebook)
        self.notebook.add(overview_tab, text="Tổng quan")

        # Tạo panel thống kê
        self.stats_panel = StatisticsPanel(overview_tab)
        frame = self.stats_panel.get_frame()
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Thêm các thống kê
        self.stats_panel.add_statistic('total', 'Tổng số sản phẩm:', 0, 0, color='dark blue')
        self.stats_panel.add_statistic('quality_good', 'Sản phẩm chất lượng:', 1, 0, color='green')
        self.stats_panel.add_statistic('defect_rate', 'Tỷ lệ hỏng:', 2, 0, color='red')
        self.stats_panel.add_statistic('avg_score', 'Điểm chất lượng TB:', 3, 0, color='orange')

        # Phân bố kích thước
        ttk.Label(frame, text="Phân bố kích thước:",
                 font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))

        self.size_stats_text = tk.Text(frame, width=40, height=6, font=('Arial', 9))
        self.size_stats_text.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5)

        # Phân bố chất lượng
        ttk.Label(frame, text="Phân bố chất lượng:",
                 font=('Arial', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))

        self.quality_stats_text = tk.Text(frame, width=40, height=6, font=('Arial', 9))
        self.quality_stats_text.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5)

    def load_image(self):
        """Tải ảnh từ file"""
        file_types = [
            ('Image files', '*.jpg *.jpeg *.png *.bmp *.tiff'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('PNG files', '*.png'),
            ('All files', '*.*')
        ]

        file_path = filedialog.askopenfilename(
            title="Chọn ảnh",
            filetypes=file_types
        )

        if file_path:
            self.image_path = file_path
            self.processed_image = None
            self.detection_results = []

            # Hiển thị ảnh
            if self.image_canvas.display_image(file_path):
                # Lấy thông tin file
                file_size = os.path.getsize(file_path) / 1024  # KB
                file_info = (
                    f"File: {os.path.basename(file_path)} | "
                    f"Size: {file_size:.1f} KB"
                )
                self.image_info.config(text=file_info)
                self.update_status(f"Đã tải ảnh: {os.path.basename(file_path)}")

                # Xóa kết quả cũ
                self.clear_results()
            else:
                messagebox.showerror("Lỗi", "Không thể tải ảnh. Vui lòng thử lại.")

    def clear_results(self):
        """Xóa kết quả cũ"""
        # Xóa treeview
        for item in self.class_tree.get_children():
            self.class_tree.delete(item)

        # Xóa text widgets
        self.stats_text.delete(1.0, tk.END)
        self.size_stats_text.delete(1.0, tk.END)
        self.quality_stats_text.delete(1.0, tk.END)

        # Reset statistics panel
        self.stats_panel.update_statistic('total', '0')
        self.stats_panel.update_statistic('quality_good', '0')
        self.stats_panel.update_statistic('defect_rate', '0%')
        self.stats_panel.update_statistic('avg_score', '0.00')

    def preprocess_image(self):
        """Tiền xử lý ảnh"""
        if not self.image_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải ảnh trước!")
            return

        try:
            self.update_status("Đang tiền xử lý ảnh...")

            # Tiền xử lý
            processed_cv2 = preprocess_image(self.image_path)
            self.processed_image = processed_cv2

            # Chuyển sang PIL để hiển thị
            processed_rgb = cv2.cvtColor(processed_cv2, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(processed_rgb)

            # Hiển thị
            self.image_canvas.display_pil_image(pil_image)

            self.update_status("Đã tiền xử lý ảnh thành công")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Tiền xử lý thất bại: {str(e)}")
            self.update_status("Lỗi khi tiền xử lý")

    def analyze_image(self):
        """Phân tích và phân loại sản phẩm"""
        if not self.image_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải ảnh trước!")
            return

        if not self.model.is_loaded():
            messagebox.showerror("Lỗi", "Mô hình chưa được tải!")
            return

        # Hiển thị dialog tiến trình
        progress = ProgressDialog(self.root, "Đang phân tích ảnh...")

        try:
            # Lấy cài đặt
            settings = {
                'confidence': self.confidence_var.get(),
                'product_type': self.product_var.get(),
                'enable_quality': self.quality_var.get(),
                'enable_size': self.size_var.get()
            }

            progress.update_message("Đang phát hiện đối tượng...")

            # Phân tích ảnh
            result = self.image_processor.analyze(
                self.image_path,
                self.processed_image,
                settings
            )

            if not result or 'detections' not in result:
                raise ValueError("Không có kết quả phát hiện")

            # Cập nhật kết quả
            self.processed_image = result['processed_image']
            self.detection_results = result['detections']

            # Chuyển sang PIL để hiển thị
            processed_rgb = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(processed_rgb)

            progress.update_message("Đang cập nhật giao diện...")

            # Hiển thị ảnh đã xử lý
            self.image_canvas.display_pil_image(pil_image)

            # Cập nhật UI
            self.update_results_table()
            self.update_statistics()

            total_count = len(self.detection_results)
            self.update_status(f"Đã phân tích {total_count} sản phẩm")

            progress.update_message("Phân tích hoàn tất!")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Phân tích thất bại: {str(e)}")
            self.update_status("Lỗi khi phân tích")

        finally:
            progress.close()

    def update_results_table(self):
        """Cập nhật bảng kết quả phân loại"""
        # Xóa dữ liệu cũ
        for item in self.class_tree.get_children():
            self.class_tree.delete(item)

        # Thêm dữ liệu mới
        for i, result in enumerate(self.detection_results, 1):
            # Lấy tên tiếng Việt
            class_name_vi = PRODUCT_NAMES_VI.get(result['class'], result['class'])
            quality_vi = self.classifier.get_quality_name_vi(result['quality'])

            # Tạo tag cho màu nền
            tag = f"quality_{result['quality']}"
            self.class_tree.tag_configure(tag,
                background=self.get_quality_color_hex(result['quality']))

            # Chèn dữ liệu
            self.class_tree.insert('', 'end', values=(
                i,
                class_name_vi,
                quality_vi,
                result['size_category'],
                f"{result['quality_score']:.2f}",
                f"{result['size_px']:.0f}"
            ), tags=(tag,))

    def get_quality_color_hex(self, quality):
        """Lấy màu hex từ chất lượng"""
        from core.config import QUALITY_COLORS
        return QUALITY_COLORS.get(quality, '#FFFFFF')

    def update_statistics(self):
        """Cập nhật thống kê"""
        if not self.detection_results:
            return

        # Tính toán thống kê
        self.current_stats = calculate_statistics(self.detection_results)

        # Cập nhật statistics panel
        self.stats_panel.update_statistic('total', self.current_stats['total'])
        self.stats_panel.update_statistic('quality_good',
            self.current_stats.get('quality_good', 0))
        self.stats_panel.update_statistic('defect_rate',
            f"{self.current_stats.get('defect_rate', 0):.1f}%")
        self.stats_panel.update_statistic('avg_score',
            f"{self.current_stats.get('avg_quality_score', 0):.2f}")

        # Cập nhật phân bố kích thước
        self.size_stats_text.delete(1.0, tk.END)
        if 'size_counts' in self.current_stats:
            for size, count in self.current_stats['size_counts'].items():
                percentage = (count / self.current_stats['total'] * 100) if self.current_stats['total'] > 0 else 0
                self.size_stats_text.insert(tk.END,
                    f"{size}: {count} ({percentage:.1f}%)\n")

        # Cập nhật phân bố chất lượng
        self.quality_stats_text.delete(1.0, tk.END)
        if 'quality_counts' in self.current_stats:
            for quality, count in self.current_stats['quality_counts'].items():
                quality_vi = self.classifier.get_quality_name_vi(quality)
                percentage = (count / self.current_stats['total'] * 100) if self.current_stats['total'] > 0 else 0
                self.quality_stats_text.insert(tk.END,
                    f"{quality_vi}: {count} ({percentage:.1f}%)\n")

        # Cập nhật tab thống kê
        stats_text = self.generate_statistics_text()
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    def generate_statistics_text(self):
        """Tạo văn bản thống kê"""
        if not self.current_stats:
            return "Chưa có dữ liệu thống kê"

        stats = self.current_stats

        text = "=" * 50 + "\n"
        text += "THỐNG KÊ PHÂN LOẠI SẢN PHẨM\n"
        text += "=" * 50 + "\n\n"

        text += f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"Tổng số sản phẩm: {stats['total']}\n"
        text += f"Loại sản phẩm: {PRODUCT_NAMES_VI.get(self.product_var.get(), self.product_var.get())}\n\n"

        if 'quality_counts' in stats and stats['quality_counts']:
            text += "--- PHÂN LOẠI THEO CHẤT LƯỢNG ---\n"
            for quality, count in sorted(stats['quality_counts'].items()):
                quality_vi = self.classifier.get_quality_name_vi(quality)
                percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                text += f"  {quality_vi:15s}: {count:3d} ({percentage:5.1f}%)\n"

        if 'size_counts' in stats and stats['size_counts']:
            text += "\n--- PHÂN LOẠI THEO KÍCH THƯỚC ---\n"
            for size, count in sorted(stats['size_counts'].items()):
                percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                text += f"  {size:15s}: {count:3d} ({percentage:5.1f}%)\n"

        text += f"\n--- TỔNG HỢP ---\n"
        text += f"  Điểm chất lượng TB: {stats.get('avg_quality_score', 0):.2f}/1.0\n"
        text += f"  Tỷ lệ hỏng:        {stats.get('defect_rate', 0):.1f}%\n"
        text += f"  Sản phẩm chất lượng: {stats.get('quality_good', 0)}/{stats['total']}\n"

        return text

    def copy_statistics(self):
        """Copy thống kê vào clipboard"""
        stats_text = self.stats_text.get(1.0, tk.END).strip()
        if stats_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(stats_text)
            self.update_status("Đã copy thống kê vào clipboard")

    def show_statistics(self):
        """Hiển thị thống kê chi tiết"""
        if not self.detection_results:
            messagebox.showinfo("Thông tin", "Chưa có dữ liệu thống kê")
            return

        # Chuyển sang tab thống kê
        self.notebook.select(1)

    def save_results(self):
        """Lưu kết quả phân tích - ĐÃ SỬA LỖI TRÙNG TÊN"""
        try:
            # DEBUG: Kiểm tra dữ liệu
            print("\n" + "=" * 50)
            print("🔄 DEBUG: Kiểm tra dữ liệu trước khi lưu")
            print("=" * 50)
            print(f"1. processed_image is None: {self.processed_image is None}")
            print(f"2. has detection_results: {hasattr(self, 'detection_results')}")
            if hasattr(self, 'detection_results'):
                print(f"3. detection_results type: {type(self.detection_results)}")
                print(f"4. detection_results length: {len(self.detection_results) if self.detection_results else 0}")
            print("=" * 50)

            # KIỂM TRA ĐIỀU KIỆN
            if self.processed_image is None:
                messagebox.showwarning("Cảnh báo", "Chưa có ảnh nào được xử lý! Vui lòng tải và phân tích ảnh trước.")
                return

            if not hasattr(self, 'detection_results') or self.detection_results is None:
                messagebox.showwarning("Cảnh báo", "Chưa có kết quả phân tích! Vui lòng nhấn 'PHÂN TÍCH' trước.")
                return

            if len(self.detection_results) == 0:
                messagebox.showwarning("Cảnh báo", "Không có sản phẩm nào được phát hiện!")
                return

            # Lấy cài đặt
            from datetime import datetime
            settings = {
                'product_type': self.product_var.get(),
                'quality_analysis': self.quality_var.get(),
                'size_analysis': self.size_var.get(),
                'confidence_threshold': float(self.confidence_var.get()),
                'timestamp': datetime.now().isoformat()
            }

            # Kiểm tra statistics
            if not hasattr(self, 'current_stats') or not self.current_stats:
                from utils.statistics import calculate_statistics
                self.current_stats = calculate_statistics(self.detection_results)
                print(f"✅ Đã tính toán statistics: {self.current_stats.get('total', 0)} sản phẩm")

            # QUAN TRỌNG: Import đúng hàm từ utils với alias khác
            from utils.file_utils import save_results as save_to_files

            print("📤 Đang gọi hàm lưu kết quả...")
            saved_files = save_to_files(
                processed_image=self.processed_image,
                detections=self.detection_results,
                statistics=self.current_stats,
                settings=settings,
                original_image_path=self.image_path
            )

            if saved_files:
                import os
                file_count = len([v for v in saved_files.values() if v])
                success_msg = f"✅ Đã lưu thành công {file_count} file!"

                # Lấy thư mục lưu từ file đầu tiên
                first_file = next((v for v in saved_files.values() if v), None)
                if first_file:
                    folder = os.path.dirname(first_file)
                    success_msg += f"\n\n📁 Thư mục: {folder}"

                    # Liệt kê các file đã lưu
                    success_msg += "\n📄 Các file đã lưu:"
                    for key, path in saved_files.items():
                        if path and os.path.exists(path):
                            file_name = os.path.basename(path)
                            file_size = os.path.getsize(path) / 1024  # KB
                            success_msg += f"\n• {file_name} ({file_size:.1f} KB)"

                messagebox.showinfo("Thành công", success_msg)
                self.update_status(f"Đã lưu {file_count} file kết quả")

            else:
                self.update_status("⚠️ Không lưu được file (có thể người dùng đã hủy)")

        except Exception as e:
            error_msg = f"Lỗi khi lưu file: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Lỗi", error_msg)
            self.update_status("❌ Lỗi khi lưu file")

    def reset_app(self):
        """Reset ứng dụng"""
        self.image_path = None
        self.processed_image = None
        self.detection_results = []
        self.current_stats = {}

        # Reset image canvas
        self.image_canvas.canvas.delete("all")
        self.image_info.config(text="Chưa có ảnh nào được tải")

        # Clear results
        self.clear_results()

        self.update_status("Đã reset hệ thống")

    def update_status(self, message):
        """Cập nhật thanh trạng thái"""
        self.status_bar.config(text=message)
        self.root.update()