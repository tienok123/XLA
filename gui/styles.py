"""
Style và theme cho ứng dụng
"""
import tkinter as tk
from tkinter import ttk


def configure_styles():
    """Cấu hình styles cho ứng dụng"""
    style = ttk.Style()

    # Sử dụng theme mặc định
    try:
        style.theme_use('clam')
    except:
        pass

    # Custom styles
    style.configure('Title.TLabel',
                    font=('Arial', 16, 'bold'),
                    foreground='dark green')

    style.configure('Header.TLabel',
                    font=('Arial', 10, 'bold'),
                    foreground='dark blue')

    style.configure('Status.TLabel',
                    font=('Arial', 9),
                    foreground='gray30')

    style.configure('Primary.TButton',
                    font=('Arial', 9, 'bold'),
                    padding=5)

    style.configure('Secondary.TButton',
                    font=('Arial', 9),
                    padding=3)

    style.configure('Success.TLabel',
                    font=('Arial', 10),
                    foreground='green')

    style.configure('Warning.TLabel',
                    font=('Arial', 10),
                    foreground='orange')

    style.configure('Error.TLabel',
                    font=('Arial', 10),
                    foreground='red')

    # Configure notebook style
    style.configure('TNotebook', padding=5)
    style.configure('TNotebook.Tab', padding=[10, 5], font=('Arial', 9))

    # Configure treeview
    style.configure('Treeview',
                    font=('Arial', 9),
                    rowheight=25)
    style.configure('Treeview.Heading',
                    font=('Arial', 9, 'bold'))

    # Configure scrollbars
    style.configure('Vertical.TScrollbar',
                    arrowsize=12,
                    width=12)
    style.configure('Horizontal.TScrollbar',
                    arrowsize=12,
                    height=12)


def create_color_tags(text_widget):
    """Tạo color tags cho text widget"""
    # Xóa tags cũ nếu có
    for tag in text_widget.tag_names():
        text_widget.tag_delete(tag)

    # Tạo tags mới
    colors = {
        'title': ('#2E86C1', ('Arial', 12, 'bold')),
        'header': ('#1ABC9C', ('Arial', 11, 'bold')),
        'success': ('#27AE60', ('Arial', 10)),
        'warning': ('#F39C12', ('Arial', 10)),
        'error': ('#E74C3C', ('Arial', 10)),
        'info': ('#3498DB', ('Arial', 10)),
        'highlight': ('#F7DC6F', ('Arial', 10, 'bold')),
        'data': ('#2C3E50', ('Consolas', 10)),
        'stat': ('#8E44AD', ('Arial', 10, 'bold'))
    }

    for tag_name, (color, font) in colors.items():
        text_widget.tag_configure(tag_name, foreground=color, font=font)

    return text_widget.tag_names()


def apply_window_style(window):
    """Áp dụng style cho cửa sổ"""
    # Đặt màu nền
    window.configure(bg='#f0f0f0')

    # Cấu hình grid weights
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    return window


def create_rounded_button(parent, text, command, **kwargs):
    """Tạo nút bo tròn"""
    bg_color = kwargs.get('bg', '#4CAF50')
    fg_color = kwargs.get('fg', 'white')
    font = kwargs.get('font', ('Arial', 10, 'bold'))
    width = kwargs.get('width', 15)
    height = kwargs.get('height', 1)
    radius = kwargs.get('radius', 10)

    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg=fg_color,
        font=font,
        width=width,
        height=height,
        relief='flat',
        bd=0,
        cursor='hand2'
    )

    # Tạo hiệu ứng hover
    def on_enter(e):
        button['bg'] = '#45a049'

    def on_leave(e):
        button['bg'] = bg_color

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

    return button