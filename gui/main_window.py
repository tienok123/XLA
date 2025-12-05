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
from core.config import PRODUCT_NAMES_VI
from processing import ImageProcessor
from gui.styles import configure_styles
from gui.components import ImageCanvas, ProgressDialog
from utils import save_results


class FruitDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Đếm Và Phân Loại Sản Phẩm Nông Nghiệp")
        self.root.geometry("1400x800")

        # Tạo menu bar
        self.create_menu_bar()

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

        # Cài đặt
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings['enable_preprocessing'] = True

        # Thiết lập UI
        self.setup_ui()

        # Tải mô hình
        self.load_model()

        # Thanh trạng thái
        self.update_status("Sẵn sàng - Hệ thống phân loại sản phẩm nông nghiệp")

    def create_menu_bar(self):
        """Tạo thanh menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Tải ảnh...", command=self.load_image, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Lưu kết quả...", command=self.save_results, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.quit, accelerator="Ctrl+Q")

        # Menu Xử lý
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Xử lý", menu=process_menu)
        process_menu.add_command(label="Phân tích ảnh", command=self.analyze_image, accelerator="F5")
        process_menu.add_command(label="Tiền xử lý ảnh...", command=self.show_preprocessing_preview)
        process_menu.add_separator()
        process_menu.add_command(label="Reset", command=self.reset_app, accelerator="Ctrl+R")

        # Menu Cài đặt
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Cài đặt", menu=settings_menu)

        # Submenu tiền xử lý
        preprocess_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Tiền xử lý ảnh", menu=preprocess_menu)

        # Các biến cho menu tiền xử lý
        self.preprocess_vars = {
            'resize': tk.BooleanVar(value=True),
            'enhance_contrast': tk.BooleanVar(value=True),
            'denoise': tk.BooleanVar(value=True),
            'sharpen': tk.BooleanVar(value=False),
            'normalize': tk.BooleanVar(value=True)
        }

        preprocess_menu.add_checkbutton(label="Resize ảnh", variable=self.preprocess_vars['resize'],
                                       command=self.update_preprocessing_config)
        preprocess_menu.add_checkbutton(label="Tăng cường tương phản", variable=self.preprocess_vars['enhance_contrast'],
                                       command=self.update_preprocessing_config)
        preprocess_menu.add_checkbutton(label="Khử nhiễu", variable=self.preprocess_vars['denoise'],
                                       command=self.update_preprocessing_config)
        preprocess_menu.add_checkbutton(label="Làm sắc nét", variable=self.preprocess_vars['sharpen'],
                                       command=self.update_preprocessing_config)
        preprocess_menu.add_checkbutton(label="Chuẩn hóa", variable=self.preprocess_vars['normalize'],
                                       command=self.update_preprocessing_config)

        # Menu Trợ giúp
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        help_menu.add_command(label="Hướng dẫn sử dụng", command=self.show_help)
        help_menu.add_command(label="Về ứng dụng", command=self.show_about)

        # Phím tắt
        self.root.bind('<Control-o>', lambda e: self.load_image())
        self.root.bind('<Control-s>', lambda e: self.save_results())
        self.root.bind('<Control-r>', lambda e: self.reset_app())
        self.root.bind('<F5>', lambda e: self.analyze_image())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def update_preprocessing_config(self):
        """Cập nhật cấu hình tiền xử lý"""
        config = {key: var.get() for key, var in self.preprocess_vars.items()}
        self.image_processor.set_preprocessing_config(**config)
        self.update_status("Đã cập nhật cấu hình tiền xử lý")

    def show_help(self):
        """Hiển thị hướng dẫn sử dụng"""
        help_text = """
        HƯỚNG DẪN SỬ DỤNG
        
        1. TẢI ẢNH
           • Nhấn "Tải ảnh" hoặc Ctrl+O
           • Chọn ảnh từ máy tính
           
        2. PHÂN TÍCH ẢNH
           • Nhấn "Phân tích" hoặc F5
           • Chờ hệ thống xử lý
           
        3. XEM KẾT QUẢ
           • Tab "Phân loại": Xem chi tiết từng sản phẩm
           • Tab "Thống kê": Xem tổng quan và báo cáo
           
        4. TIỀN XỬ LÝ ẢNH
           • Bật/tắt trong menu Cài đặt
           • Xem preview: Menu Xử lý → Tiền xử lý ảnh
           
        5. LƯU KẾT QUẢ
           • Nhấn "Lưu kết quả" hoặc Ctrl+S
           • Kết quả được lưu tự động vào thư mục output/
        """
        messagebox.showinfo("Hướng dẫn sử dụng", help_text)

    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        about_text = """
        HỆ THỐNG ĐẾM VÀ PHÂN LOẠI SẢN PHẨM NÔNG NGHIỆP
        
        Phiên bản: 2.0
        Tính năng:
        • Phát hiện và phân loại trái cây tự động
        • Đánh giá chất lượng (xanh/chín/hỏng)
        • Phân loại theo kích thước
        • Tiền xử lý ảnh thông minh
        • Xuất báo cáo chi tiết
        
        © 2024 - Phát triển bởi AI AgriTech Team
        """
        messagebox.showinfo("Về ứng dụng", about_text)

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
        self.preprocess_var = tk.BooleanVar(value=True)

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

        # Tiền xử lý ảnh
        ttk.Label(self.control_frame, text="Tiền xử lý ảnh:",
                 style='Header.TLabel').pack(anchor=tk.W, pady=(10, 5))

        ttk.Checkbutton(
            self.control_frame,
            text="Bật tiền xử lý ảnh",
            variable=self.preprocess_var
        ).pack(anchor=tk.W, pady=2)

        # Nút xem trước tiền xử lý
        ttk.Button(
            self.control_frame,
            text="👁️ Xem trước tiền xử lý",
            command=self.show_preprocessing_preview,
            style='Secondary.TButton',
            width=20
        ).pack(pady=5, fill=tk.X)

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
            ("📊 XEM THỐNG KÊ", self.show_statistics),
            ("💾 LƯU KẾT QUẢ", self.save_results),
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

        # Nút xem ảnh gốc/ảnh đã xử lý
        self.toggle_img_btn = ttk.Button(
            img_control_frame,
            text="🔄 Xem ảnh gốc",
            command=self.toggle_original_processed,
            width=15
        )
        self.toggle_img_btn.pack(side=tk.LEFT, padx=5)
        self.showing_original = True

        # Thông tin ảnh
        self.image_info = ttk.Label(img_control_frame, text="Chưa có ảnh nào được tải")
        self.image_info.pack(side=tk.LEFT, padx=20)

        # Cấu hình resize
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)

    def toggle_original_processed(self):
        """Chuyển đổi giữa xem ảnh gốc và ảnh đã xử lý"""
        if not self.image_path:
            return

        if self.showing_original:
            # Hiển thị ảnh đã xử lý
            if self.processed_image is not None:
                processed_rgb = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(processed_rgb)
                self.image_canvas.display_pil_image(pil_image)
                self.toggle_img_btn.config(text="🔄 Xem ảnh gốc")
                self.showing_original = False
        else:
            # Hiển thị ảnh gốc
            self.image_canvas.display_image(self.image_path)
            self.toggle_img_btn.config(text="🔄 Xem ảnh đã xử lý")
            self.showing_original = True

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

    def create_classification_tab(self):
        """Tạo tab phân loại"""
        class_tab = ttk.Frame(self.notebook)
        self.notebook.add(class_tab, text="Phân loại")

        # Treeview
        columns = ('STT', 'Loại SP', 'Chất lượng', 'Điểm số')
        self.class_tree = ttk.Treeview(class_tab, columns=columns, show='headings', height=15)

        # Đặt độ rộng cột
        col_widths = [50, 150, 150, 100]
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
        """Tạo tab thống kê đơn giản"""
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

        ttk.Button(
            btn_frame,
            text="📄 Xuất ra file",
            command=self.export_statistics,
            width=12
        ).pack(side=tk.RIGHT, padx=5)

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
            self.showing_original = True

            # Hiển thị ảnh
            if self.image_canvas.display_image(file_path):
                # Lấy thông tin file
                file_size = os.path.getsize(file_path) / 1024  # KB
                img = Image.open(file_path)
                width, height = img.size
                file_info = (
                    f"File: {os.path.basename(file_path)} | "
                    f"Size: {file_size:.1f} KB | "
                    f"Dimensions: {width}×{height}"
                )
                self.image_info.config(text=file_info)
                self.update_status(f"Đã tải ảnh: {os.path.basename(file_path)}")

                # Xóa kết quả cũ
                self.clear_results()

                # Cập nhật nút toggle
                self.toggle_img_btn.config(state='normal' if self.processed_image else 'disabled')
            else:
                messagebox.showerror("Lỗi", "Không thể tải ảnh. Vui lòng thử lại.")

    def clear_results(self):
        """Xóa kết quả cũ"""
        # Xóa treeview
        for item in self.class_tree.get_children():
            self.class_tree.delete(item)

        # Xóa text widgets
        self.stats_text.delete(1.0, tk.END)

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
                'enable_size': self.size_var.get(),
                'enable_preprocessing': self.preprocess_var.get()
            }

            progress.update_message("Đang tiền xử lý ảnh...")

            # Phân tích ảnh
            result = self.image_processor.analyze(
                self.image_path,
                None,  # Không dùng processed_image
                settings
            )

            if not result or 'detections' not in result:
                raise ValueError("Không có kết quả phát hiện")

            # Cập nhật kết quả
            self.processed_image = result['processed_image']
            self.detection_results = result['detections']

            progress.update_message("Đang cập nhật giao diện...")

            # Hiển thị ảnh đã xử lý
            processed_rgb = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(processed_rgb)
            self.image_canvas.display_pil_image(pil_image)

            # Cập nhật trạng thái toggle button
            self.toggle_img_btn.config(state='normal', text="🔄 Xem ảnh gốc")
            self.showing_original = False

            # Cập nhật UI
            self.update_results_table()
            self.update_statistics()

            # Tính số lượng từng loại
            class_counts = {}
            for result in self.detection_results:
                class_name = result['class']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            total_count = len(self.detection_results)
            class_info = []
            for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
                class_name_vn = PRODUCT_NAMES_VI.get(class_name, class_name)
                percentage = (count / total_count * 100) if total_count > 0 else 0
                class_info.append(f"{class_name_vn}: {count} ({percentage:.1f}%)")

            self.update_status(f"Đã phân tích {total_count} sản phẩm. " + " | ".join(class_info))

            progress.update_message("Phân tích hoàn tất!")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Phân tích thất bại: {str(e)}")
            self.update_status("Lỗi khi phân tích")
            import traceback
            traceback.print_exc()

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
                f"{result['quality_score']:.2f}"
            ), tags=(tag,))

    def get_quality_color_hex(self, quality):
        """Lấy màu hex từ chất lượng"""
        from core.config import QUALITY_COLORS
        return QUALITY_COLORS.get(quality, '#FFFFFF')

    def update_statistics(self):
        """Cập nhật thống kê đơn giản"""
        if not self.detection_results:
            return

        # Tính toán thống kê cơ bản
        total = len(self.detection_results)

        # Đếm theo loại sản phẩm
        class_counts = {}
        quality_counts = {}

        for result in self.detection_results:
            # Loại sản phẩm
            class_name = result['class']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

            # Chất lượng
            quality = result['quality']
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        # Tính điểm chất lượng trung bình
        total_score = sum(result['quality_score'] for result in self.detection_results)
        avg_score = total_score / total if total > 0 else 0

        # Đếm sản phẩm chất lượng (chín/tốt)
        quality_good = quality_counts.get('ripe', 0) + quality_counts.get('good', 0)
        defect_count = quality_counts.get('bad', 0) + quality_counts.get('rotten', 0)
        defect_rate = (defect_count / total * 100) if total > 0 else 0

        # Lưu thống kê cho sử dụng sau
        self.current_stats = {
            'total': total,
            'class_counts': class_counts,
            'quality_counts': quality_counts,
            'avg_quality_score': avg_score,
            'quality_good': quality_good,
            'defect_rate': defect_rate
        }

        # Tạo văn bản thống kê
        stats_text = self.generate_statistics_text()

        # Hiển thị
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    def generate_statistics_text(self):
        """Tạo văn bản thống kê chi tiết"""
        if not hasattr(self, 'current_stats') or not self.current_stats:
            return "Chưa có dữ liệu thống kê"

        stats = self.current_stats
        total = stats.get('total', 0)
        class_counts = stats.get('class_counts', {})
        quality_counts = stats.get('quality_counts', {})

        text = "=" * 60 + "\n"
        text += "THỐNG KÊ PHÂN LOẠI SẢN PHẨM\n"
        text += "=" * 60 + "\n\n"

        text += f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"Tổng số sản phẩm: {total}\n"
        text += f"Số loại sản phẩm: {len(class_counts)}\n"
        text += f"Loại sản phẩm chính: {PRODUCT_NAMES_VI.get(self.product_var.get(), self.product_var.get())}\n\n"

        # THỐNG KÊ CHI TIẾT TỪNG LOẠI
        if class_counts:
            text += "=" * 60 + "\n"
            text += "THỐNG KÊ CHI TIẾT TỪNG LOẠI SẢN PHẨM\n"
            text += "=" * 60 + "\n\n"

            for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
                class_name_vn = PRODUCT_NAMES_VI.get(class_name, class_name)
                percentage = (count / total * 100) if total > 0 else 0
                text += f"【{class_name_vn.upper()}】\n"
                text += f"  Số lượng: {count} ({percentage:.1f}%)\n"

                # Tính chất lượng cho từng loại
                class_detections = [d for d in self.detection_results if d['class'] == class_name]
                if class_detections:
                    # Đếm chất lượng trong loại này
                    class_quality_counts = {}
                    class_total_score = 0

                    for det in class_detections:
                        quality = det['quality']
                        class_quality_counts[quality] = class_quality_counts.get(quality, 0) + 1
                        class_total_score += det['quality_score']

                    # Hiển thị chất lượng
                    if class_quality_counts:
                        text += "  Chất lượng:\n"
                        for quality, q_count in sorted(class_quality_counts.items()):
                            quality_vi = self.classifier.get_quality_name_vi(quality)
                            q_percentage = (q_count / count * 100) if count > 0 else 0
                            text += f"    • {quality_vi:<10}: {q_count:3d} ({q_percentage:5.1f}%)\n"

                    # Điểm trung bình của loại này
                    class_avg_score = class_total_score / count if count > 0 else 0
                    text += f"  Điểm chất lượng TB: {class_avg_score:.2f}/1.0\n"

                text += "\n"

        # TỔNG HỢP CHẤT LƯỢNG
        if quality_counts:
            text += "=" * 60 + "\n"
            text += "TỔNG HỢP PHÂN LOẠI THEO CHẤT LƯỢNG\n"
            text += "=" * 60 + "\n"

            for quality, count in sorted(quality_counts.items()):
                quality_vi = self.classifier.get_quality_name_vi(quality)
                percentage = (count / total * 100) if total > 0 else 0
                text += f"  {quality_vi:<15}: {count:3d} ({percentage:5.1f}%)\n"

        # CHỈ SỐ TỔNG QUAN
        text += "\n" + "=" * 60 + "\n"
        text += "CHỈ SỐ TỔNG QUAN\n"
        text += "=" * 60 + "\n"

        text += f"  Tổng số sản phẩm:          {total:3d}\n"
        text += f"  Số loại sản phẩm:          {len(class_counts):3d}\n"
        text += f"  Sản phẩm chất lượng:       {stats.get('quality_good', 0):3d}\n"
        text += f"  Tỷ lệ hỏng:                {stats.get('defect_rate', 0):5.1f}%\n"
        text += f"  Điểm chất lượng trung bình: {stats.get('avg_quality_score', 0):5.2f}/1.0\n"

        # KẾT LUẬN
        text += "\n" + "=" * 60 + "\n"
        text += "KẾT LUẬN\n"
        text += "=" * 60 + "\n"

        defect_rate = stats.get('defect_rate', 0)
        if defect_rate < 5:
            text += "✅ CHẤT LƯỢNG TỐT\n"
            text += "   • Tỷ lệ hỏng thấp (<5%)\n"
            text += "   • Sản phẩm đạt yêu cầu xuất khẩu\n"
            text += "   • Có thể đóng gói và phân phối ngay\n"
        elif defect_rate < 20:
            text += "⚠️  CHẤT LƯỢNG TRUNG BÌNH\n"
            text += "   • Tỷ lệ hỏng vừa phải (5-20%)\n"
            text += "   • Cần kiểm tra và phân loại lại\n"
            text += "   • Có thể sử dụng cho thị trường nội địa\n"
        else:
            text += "❌ CHẤT LƯỢNG KÉM\n"
            text += "   • Tỷ lệ hỏng cao (>20%)\n"
            text += "   • Cần xử lý và loại bỏ sản phẩm hỏng\n"
            text += "   • Không đạt tiêu chuẩn phân phối\n"

        # Đề xuất xử lý theo số lượng từng loại
        text += "\n" + "-" * 40 + "\n"
        text += "ĐỀ XUẤT XỬ LÝ:\n"
        text += "-" * 40 + "\n"

        if class_counts:
            for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
                class_name_vn = PRODUCT_NAMES_VI.get(class_name, class_name)
                text += f"• {class_name_vn}: {count} sản phẩm\n"

        text += "\n" + "=" * 60 + "\n"
        text += f"Báo cáo được tạo lúc: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
        text += "Hệ thống phân loại sản phẩm nông nghiệp\n"
        text += "=" * 60

        return text

    def copy_statistics(self):
        """Copy thống kê vào clipboard"""
        stats_text = self.stats_text.get(1.0, tk.END).strip()
        if stats_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(stats_text)
            self.update_status("Đã copy thống kê vào clipboard")

    def export_statistics(self):
        """Xuất thống kê ra file text"""
        if not hasattr(self, 'current_stats') or not self.current_stats:
            messagebox.showwarning("Cảnh báo", "Chưa có dữ liệu thống kê để xuất!")
            return

        # Đề xuất tên file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"thong_ke_phan_loai_{timestamp}.txt"

        file_path = filedialog.asksaveasfilename(
            title="Lưu thống kê ra file",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_filename
        )

        if file_path:
            try:
                stats_text = self.stats_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(stats_text)

                self.update_status(f"Đã xuất thống kê ra file: {os.path.basename(file_path)}")
                messagebox.showinfo("Thành công", f"Đã lưu thống kê vào:\n{file_path}")

            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu file: {str(e)}")

    def save_results(self):
        """Lưu kết quả phân tích"""
        try:
            if self.processed_image is None:
                messagebox.showwarning("Cảnh báo", "Chưa có ảnh nào được xử lý! Vui lòng tải và phân tích ảnh trước.")
                return

            if not hasattr(self, 'detection_results') or not self.detection_results:
                messagebox.showwarning("Cảnh báo", "Chưa có kết quả phân tích! Vui lòng nhấn 'PHÂN TÍCH' trước.")
                return

            # Lấy cài đặt
            settings = {
                'product_type': self.product_var.get(),
                'quality_analysis': self.quality_var.get(),
                'size_analysis': self.size_var.get(),
                'preprocessing': self.preprocess_var.get(),
                'confidence_threshold': float(self.confidence_var.get()),
                'timestamp': datetime.now().isoformat()
            }

            # Lưu kết quả
            saved_files = save_results(
                processed_image=self.processed_image,
                detections=self.detection_results,
                settings=settings,
                original_image_path=self.image_path
            )

            if saved_files:
                file_count = len([v for v in saved_files.values() if v])
                messagebox.showinfo("Thành công", f"Đã lưu thành công {file_count} file kết quả!")
                self.update_status(f"Đã lưu {file_count} file kết quả")
            else:
                self.update_status("Không lưu được file kết quả")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi lưu file: {str(e)}")
            self.update_status("Lỗi khi lưu file")

    def show_preprocessing_preview(self):
        """Hiển thị preview tiền xử lý ảnh"""
        if not self.image_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải ảnh trước!")
            return

        try:
            # Lấy ảnh preview
            previews = self.image_processor.get_preview_images(self.image_path)

            if previews:
                # Tạo cửa sổ mới
                preview_window = tk.Toplevel(self.root)
                preview_window.title("So sánh trước/sau tiền xử lý")
                preview_window.geometry("1000x700")

                # Tiêu đề
                title_label = ttk.Label(
                    preview_window,
                    text="SO SÁNH TRƯỚC/SAU TIỀN XỬ LÝ ẢNH",
                    style='Title.TLabel',
                    font=('Arial', 14, 'bold')
                )
                title_label.pack(pady=10)

                # Chuyển ảnh comparison sang PIL để hiển thị
                comparison_rgb = cv2.cvtColor(previews['comparison'], cv2.COLOR_BGR2RGB)
                comparison_pil = Image.fromarray(comparison_rgb)

                # Hiển thị
                img_label = ttk.Label(preview_window)
                img_label.pack(padx=10, pady=10)

                # Scale ảnh để vừa cửa sổ
                display_pil = comparison_pil.copy()
                max_size = (900, 500)
                display_pil.thumbnail(max_size, Image.Resampling.LANCZOS)

                img_tk = ImageTk.PhotoImage(display_pil)
                img_label.config(image=img_tk)
                img_label.image = img_tk

                # Thêm thông tin
                info_frame = ttk.Frame(preview_window)
                info_frame.pack(pady=10)

                info_text = (
                    f"Kích thước gốc: {previews['original'].shape[1]}×{previews['original'].shape[0]} pixels\n"
                    f"Kích thước sau xử lý: {previews['processed'].shape[1]}×{previews['processed'].shape[0]} pixels\n"
                    f"Tỷ lệ: {previews['original'].shape[1]/previews['processed'].shape[1]:.2f}:1"
                )

                info_label = ttk.Label(info_frame, text=info_text, justify=tk.CENTER)
                info_label.pack()

                # Thông tin các bước xử lý
                steps_frame = ttk.LabelFrame(preview_window, text="CÁC BƯỚC TIỀN XỬ LÝ ĐƯỢC ÁP DỤNG", padding=10)
                steps_frame.pack(pady=10, padx=20, fill=tk.X)

                steps_text = []
                for step, enabled in self.preprocess_vars.items():
                    if enabled.get():
                        step_name = {
                            'resize': 'Resize ảnh về kích thước phù hợp',
                            'enhance_contrast': 'Tăng cường tương phản (CLAHE)',
                            'denoise': 'Khử nhiễu (Non-local Means)',
                            'sharpen': 'Làm sắc nét (Unsharp Mask)',
                            'normalize': 'Chuẩn hóa cường độ pixel'
                        }.get(step, step)
                        steps_text.append(f"✓ {step_name}")

                if steps_text:
                    for step in steps_text:
                        ttk.Label(steps_frame, text=step).pack(anchor=tk.W, pady=2)
                else:
                    ttk.Label(steps_frame, text="Không có bước tiền xử lý nào được bật").pack()

                # Nút đóng
                ttk.Button(
                    preview_window,
                    text="Đóng",
                    command=preview_window.destroy,
                    width=20
                ).pack(pady=20)

            else:
                messagebox.showerror("Lỗi", "Không thể tạo preview tiền xử lý")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo preview: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_statistics(self):
        """Hiển thị thống kê chi tiết"""
        if not self.detection_results:
            messagebox.showinfo("Thông tin", "Chưa có dữ liệu thống kê")
            return

        # Tính toán số lượng từng loại
        class_counts = {}
        for result in self.detection_results:
            class_name = result['class']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        # Tạo message hiển thị nhanh
        message = "📊 THỐNG KÊ SỐ LƯỢNG TỪNG LOẠI\n"
        message += "=" * 40 + "\n"

        total = len(self.detection_results)
        for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
            class_name_vn = PRODUCT_NAMES_VI.get(class_name, class_name)
            percentage = (count / total * 100) if total > 0 else 0
            message += f"• {class_name_vn:<10}: {count:3d} ({percentage:5.1f}%)\n"

        message += "=" * 40 + "\n"
        message += f"Tổng số: {total} sản phẩm\n"
        message += f"Số loại: {len(class_counts)} loại"

        # Hiển thị popup
        messagebox.showinfo("Thống kê nhanh", message)

        # Chuyển sang tab thống kê
        self.notebook.select(1)

    def reset_app(self):
        """Reset ứng dụng"""
        self.image_path = None
        self.processed_image = None
        self.detection_results = []
        self.showing_original = True

        # Reset image canvas
        self.image_canvas.canvas.delete("all")
        self.image_info.config(text="Chưa có ảnh nào được tải")

        # Reset toggle button
        self.toggle_img_btn.config(state='disabled', text="🔄 Xem ảnh gốc")

        # Clear results
        self.clear_results()

        self.update_status("Đã reset hệ thống")

    def update_status(self, message):
        """Cập nhật thanh trạng thái"""
        self.status_bar.config(text=message)
        self.root.update()


# Chạy ứng dụng
if __name__ == "__main__":
    root = tk.Tk()
    app = FruitDetectionApp(root)
    root.mainloop()