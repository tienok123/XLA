"""
Các thành phần UI tái sử dụng
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class ImageCanvas:
    """Canvas hiển thị ảnh với chức năng zoom và pan"""

    def __init__(self, parent, width=700, height=450):
        self.canvas = tk.Canvas(parent, bg='gray90', width=width, height=height)
        self.image = None
        self.tk_image = None
        self.original_image = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # Bind mouse events
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-1>", self.stop_pan)

        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False

    def display_image(self, image_path):
        """Hiển thị ảnh từ file path"""
        try:
            self.original_image = Image.open(image_path)
            self.image = self.original_image.copy()
            self.update_display()
            return True
        except Exception as e:
            print(f"Lỗi hiển thị ảnh: {e}")
            return False

    def display_pil_image(self, pil_image):
        """Hiển thị ảnh từ PIL Image"""
        try:
            self.original_image = pil_image
            self.image = self.original_image.copy()
            self.update_display()
            return True
        except Exception as e:
            print(f"Lỗi hiển thị ảnh PIL: {e}")
            return False

    def update_display(self):
        """Cập nhật hiển thị ảnh"""
        if self.image:
            # Resize ảnh theo scale
            width = int(self.image.width * self.scale)
            height = int(self.image.height * self.scale)
            resized = self.image.resize((width, height), Image.Resampling.LANCZOS)

            # Chuyển sang ImageTk
            self.tk_image = ImageTk.PhotoImage(resized)

            # Xóa và vẽ lại
            self.canvas.delete("all")
            self.canvas.create_image(
                self.offset_x + self.canvas.winfo_width() // 2,
                self.offset_y + self.canvas.winfo_height() // 2,
                image=self.tk_image,
                anchor=tk.CENTER
            )

    def zoom(self, event):
        """Zoom ảnh với mouse wheel"""
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= scale_factor
        self.scale = max(0.1, min(5.0, self.scale))  # Giới hạn scale
        self.update_display()

    def start_pan(self, event):
        """Bắt đầu pan"""
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.is_panning = True

    def pan(self, event):
        """Pan ảnh"""
        if self.is_panning and self.image:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.offset_x += dx
            self.offset_y += dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.update_display()

    def stop_pan(self, event):
        """Dừng pan"""
        self.is_panning = False

    def reset_view(self):
        """Reset view về mặc định"""
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update_display()

    def get_canvas(self):
        """Lấy canvas widget"""
        return self.canvas


class StatisticsPanel:
    """Panel hiển thị thống kê"""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.variables = {}
        self.labels = {}

    def add_statistic(self, name, label_text, row, column=0, **kwargs):
        """Thêm một thống kê"""
        # Label
        label = ttk.Label(self.frame, text=label_text, font=('Arial', 10))
        label.grid(row=row, column=column, sticky=tk.W, padx=5, pady=2)

        # Value label
        var = tk.StringVar(value="0")
        value_label = ttk.Label(self.frame, textvariable=var,
                                font=('Arial', 10, 'bold'),
                                foreground=kwargs.get('color', 'dark green'))
        value_label.grid(row=row, column=column + 1, sticky=tk.W, padx=5, pady=2)

        self.variables[name] = var
        self.labels[name] = (label, value_label)

        return var

    def update_statistic(self, name, value):
        """Cập nhật giá trị thống kê"""
        if name in self.variables:
            self.variables[name].set(str(value))

    def set_color(self, name, color):
        """Đặt màu cho thống kê"""
        if name in self.labels:
            _, value_label = self.labels[name]
            value_label.configure(foreground=color)

    def get_frame(self):
        """Lấy frame"""
        return self.frame


class ProgressDialog:
    """Dialog hiển thị tiến trình"""

    def __init__(self, parent, title="Đang xử lý..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x100")
        self.dialog.resizable(False, False)

        # Center dialog
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Label
        self.label = ttk.Label(self.dialog, text=title, font=('Arial', 10))
        self.label.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate', length=250)
        self.progress.pack(pady=10)

        # Start progress
        self.progress.start(10)

        # Prevent closing
        self.dialog.protocol("WM_DELETE_WINDOW", self.do_nothing)

    def update_message(self, message):
        """Cập nhật thông báo"""
        self.label.config(text=message)
        self.dialog.update()

    def close(self):
        """Đóng dialog"""
        self.progress.stop()
        self.dialog.grab_release()
        self.dialog.destroy()

    def do_nothing(self):
        """Không làm gì khi đóng"""
        pass


class ToolTip:
    """Tạo tooltip cho widget"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = self.y = 0

        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        """Hiển thị tooltip"""
        if self.tip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID,
                         borderwidth=1, font=("Arial", "9"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        """Ẩn tooltip"""
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None