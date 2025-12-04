"""
Visualization helpers
"""
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from io import BytesIO
from PIL import Image


def draw_bounding_boxes(image, detections, show_labels=True, show_scores=True):
    """Vẽ bounding boxes và labels lên ảnh"""
    result = image.copy()

    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])

        # Lấy màu dựa trên chất lượng
        from core.config import QUALITY_COLORS_BGR
        color = QUALITY_COLORS_BGR.get(det['quality'], (128, 128, 128))

        # Vẽ bounding box
        thickness = max(1, int(min(image.shape[:2]) / 300))
        cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)

        if show_labels:
            # Tạo label
            label = f"{det['class']}"
            if det['quality'] != 'unknown':
                label += f" {det['quality']}"
            if det['size_category'] != 'Không xác định':
                label += f" {det['size_category']}"
            if show_scores:
                label += f" ({det['quality_score']:.2f})"

            # Tính font scale dựa trên kích thước ảnh
            font_scale = min(image.shape[:2]) / 1000
            font_scale = max(0.4, min(1.0, font_scale))

            # Vẽ background cho label
            (label_width, label_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )
            cv2.rectangle(result,
                          (x1, y1 - label_height - 5),
                          (x1 + label_width, y1),
                          color, -1)

            # Vẽ label
            cv2.putText(result, label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale, (255, 255, 255), thickness)

    return result


def create_heatmap(image, detections, grid_size=20):
    """Tạo heatmap cho vị trí phát hiện"""
    h, w = image.shape[:2]

    # Tạo grid
    grid_h = h // grid_size
    grid_w = w // grid_size

    # Khởi tạo heatmap
    heatmap = np.zeros((grid_h, grid_w), dtype=np.float32)

    for det in detections:
        x1, y1, x2, y2 = det['bbox']

        # Tính center point
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Map to grid
        grid_x = int(center_x * grid_w / w)
        grid_y = int(center_y * grid_h / h)

        # Ensure within bounds
        grid_x = max(0, min(grid_w - 1, grid_x))
        grid_y = max(0, min(grid_h - 1, grid_y))

        # Add weight based on quality score
        weight = det['quality_score']
        heatmap[grid_y, grid_x] += weight

    # Normalize heatmap
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()

    return heatmap


def plot_statistics(detections, output_path=None):
    """Tạo biểu đồ thống kê"""
    if not detections:
        return None

    from utils.statistics import calculate_statistics
    stats = calculate_statistics(detections)

    # Tạo figure với nhiều subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Thống Kê Phân Loại Sản Phẩm', fontsize=16, fontweight='bold')

    # 1. Biểu đồ phân bố chất lượng
    ax1 = axes[0, 0]
    if stats['quality_counts']:
        qualities = list(stats['quality_counts'].keys())
        counts = list(stats['quality_counts'].values())

        # Map colors
        from core.config import QUALITY_COLORS
        colors = [QUALITY_COLORS.get(q, '#808080') for q in qualities]

        ax1.bar(qualities, counts, color=colors)
        ax1.set_title('Phân Bố Chất Lượng')
        ax1.set_xlabel('Chất lượng')
        ax1.set_ylabel('Số lượng')
        ax1.tick_params(axis='x', rotation=45)

        # Thêm số trên các cột
        for i, v in enumerate(counts):
            ax1.text(i, v, str(v), ha='center', va='bottom')

    # 2. Biểu đồ phân bố kích thước
    ax2 = axes[0, 1]
    if stats['size_counts']:
        sizes = list(stats['size_counts'].keys())
        size_counts = list(stats['size_counts'].values())

        ax2.pie(size_counts, labels=sizes, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Phân Bố Kích Thước')
        ax2.axis('equal')

    # 3. Biểu đồ điểm chất lượng
    ax3 = axes[1, 0]
    if stats['quality_scores']:
        scores = stats['quality_scores']
        ax3.hist(scores, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.set_title('Phân Phối Điểm Chất Lượng')
        ax3.set_xlabel('Điểm chất lượng')
        ax3.set_ylabel('Tần suất')
        ax3.axvline(stats['avg_quality_score'], color='red', linestyle='--',
                    label=f'TB: {stats["avg_quality_score"]:.2f}')
        ax3.legend()

    # 4. Biểu đồ kích thước
    ax4 = axes[1, 1]
    if stats['size_values']:
        sizes = stats['size_values']
        ax4.scatter(range(len(sizes)), sizes, alpha=0.6, c='green')
        ax4.axhline(y=stats['size_stats']['mean'], color='red', linestyle='--',
                    label=f'TB: {stats["size_stats"]["mean"]:.1f}px')
        ax4.set_title('Phân Bố Kích Thước (px)')
        ax4.set_xlabel('Thứ tự sản phẩm')
        ax4.set_ylabel('Kích thước (px)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

    # Điều chỉnh layout
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path
    else:
        # Convert to PIL Image
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        # Get the RGBA buffer from the figure
        buf = canvas.buffer_rgba()
        image = Image.fromarray(buf)

        plt.close()
        return image


def create_dashboard_image(stats, output_path=None):
    """Tạo ảnh dashboard tổng hợp"""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Title
    fig.suptitle('Dashboard Thống Kê - Hệ Thống Phân Loại', fontsize=18, fontweight='bold')

    # 1. Tổng quan
    ax1 = axes[0, 0]
    overview_text = f"""
    TỔNG QUAN
    =========
    • Tổng SP: {stats['total']}
    • Điểm TB: {stats['avg_quality_score']:.2f}
    • Tỷ lệ hỏng: {stats['defect_rate']:.1f}%
    • SP chất lượng: {stats['quality_good']}
    """
    ax1.text(0.1, 0.5, overview_text, fontsize=12, verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax1.set_axis_off()
    ax1.set_title('Tổng Quan', fontweight='bold')

    # 2. Chất lượng (pie chart)
    ax2 = axes[0, 1]
    if stats['quality_counts']:
        labels = list(stats['quality_counts'].keys())
        sizes = list(stats['quality_counts'].values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

        ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Phân Bố Chất Lượng', fontweight='bold')
        ax2.axis('equal')

    # 3. Kích thước (bar chart)
    ax3 = axes[0, 2]
    if stats['size_counts']:
        categories = list(stats['size_counts'].keys())
        values = list(stats['size_counts'].values())

        bars = ax3.bar(categories, values, color='lightgreen')
        ax3.set_title('Phân Bố Kích Thước', fontweight='bold')
        ax3.set_xlabel('Loại kích thước')
        ax3.set_ylabel('Số lượng')

        # Thêm giá trị trên các cột
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{int(height)}', ha='center', va='bottom')

    # 4. Điểm chất lượng (histogram)
    ax4 = axes[1, 0]
    if stats['quality_scores']:
        ax4.hist(stats['quality_scores'], bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        ax4.set_title('Phân Phối Điểm Chất Lượng', fontweight='bold')
        ax4.set_xlabel('Điểm số')
        ax4.set_ylabel('Tần suất')
        ax4.grid(True, alpha=0.3)

        # Thêm đường trung bình
        ax4.axvline(stats['avg_quality_score'], color='red', linestyle='--',
                    label=f'TB: {stats["avg_quality_score"]:.2f}')
        ax4.legend()

    # 5. Kích thước phân bố (scatter)
    ax5 = axes[1, 1]
    if stats['size_values']:
        x = range(len(stats['size_values']))
        y = stats['size_values']

        ax5.scatter(x, y, alpha=0.6, c='orange', s=30)
        ax5.axhline(y=stats['size_stats']['mean'], color='blue', linestyle='--',
                    label=f'TB: {stats["size_stats"]["mean"]:.1f}px')
        ax5.set_title('Phân Bố Kích Thước', fontweight='bold')
        ax5.set_xlabel('Thứ tự SP')
        ax5.set_ylabel('Kích thước (px)')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

    # 6. Chất lượng theo điểm (box plot)
    ax6 = axes[1, 2]
    if stats.get('quality_scores'):
        ax6.boxplot(stats['quality_scores'], vert=False)
        ax6.set_title('Phân Tán Điểm Chất Lượng', fontweight='bold')
        ax6.set_xlabel('Điểm số')
        ax6.set_yticks([1])
        ax6.set_yticklabels(['Chất lượng'])
        ax6.grid(True, alpha=0.3)

    # Điều chỉnh layout
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    else:
        # Convert to PIL Image
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = canvas.buffer_rgba()
        image = Image.fromarray(buf)
        plt.close()
        return image


def create_comparison_chart(data_list, labels, chart_type='bar', output_path=None):
    """Tạo biểu đồ so sánh nhiều bộ dữ liệu"""
    if not data_list or len(data_list) != len(labels):
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_type == 'bar':
        x = np.arange(len(data_list[0]))
        width = 0.8 / len(data_list)

        for i, data in enumerate(data_list):
            offset = (i - len(data_list) / 2) * width
            ax.bar(x + offset, data, width, label=labels[i])

        ax.set_xticks(x)
        ax.set_xticklabels([f'SP {j + 1}' for j in range(len(data_list[0]))])
        ax.legend()
        ax.set_title('So Sánh Chất Lượng Giữa Các Mẫu')

    elif chart_type == 'line':
        for i, data in enumerate(data_list):
            ax.plot(data, marker='o', label=labels[i])

        ax.legend()
        ax.set_title('Xu Hướng Chất Lượng')
        ax.set_xlabel('Thứ tự mẫu')
        ax.set_ylabel('Điểm chất lượng')
        ax.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    else:
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = canvas.buffer_rgba()
        image = Image.fromarray(buf)
        plt.close()
        return image