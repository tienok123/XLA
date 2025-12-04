"""
Tiện ích xử lý file
"""
import os
import json
import cv2
import numpy as np
from datetime import datetime
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from pathlib import Path

from core.config import OUTPUTS_DIR, PRODUCT_NAMES_VI, QUALITY_NAMES_VI


def save_results(processed_image, detections, statistics, settings, original_image_path=None):
    """
    Lưu kết quả phân tích ảnh: ảnh processed, JSON, báo cáo, Excel, overlay
    PHIÊN BẢN SỬA LỖI JSON SERIALIZATION
    """
    try:
        # 1. Kiểm tra ảnh đã xử lý
        if processed_image is None or processed_image.size == 0:
            messagebox.showwarning("Cảnh báo", "Không có ảnh đã xử lý để lưu!")
            return None

        # 2. Kiểm tra kết quả detection
        if not detections or len(detections) == 0:
            messagebox.showwarning("Cảnh báo", "Không có kết quả phát hiện để lưu!")
            return None

        # 3. Tạo timestamp và base_name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"fruit_analysis_{timestamp}"

        # 4. Chọn thư mục lưu
        output_dir = filedialog.askdirectory(
            title="Chọn thư mục lưu kết quả",
            initialdir=str(OUTPUTS_DIR)
        )
        if not output_dir:
            return None
        os.makedirs(output_dir, exist_ok=True)

        results = {}

        # 5. Lưu ảnh đã xử lý
        image_path = os.path.join(output_dir, f"{base_name}_processed.jpg")
        if not cv2.imwrite(image_path, processed_image):
            raise ValueError(f"Không thể lưu ảnh: {image_path}")
        results['image_path'] = image_path
        print(f"✅ Đã lưu ảnh: {image_path}")

        # 6. Lưu ảnh gốc nếu có
        if original_image_path and os.path.exists(original_image_path):
            import shutil
            original_copy_path = os.path.join(output_dir, f"{base_name}_original.jpg")
            shutil.copy2(original_image_path, original_copy_path)
            results['original_image_path'] = original_copy_path
            print(f"✅ Đã lưu ảnh gốc: {original_copy_path}")

        # 7. Lưu JSON (ĐÃ SỬA LỖI SERIALIZATION)
        json_path = os.path.join(output_dir, f"{base_name}_data.json")

        # Chuyển đổi tất cả numpy types sang Python types
        import numpy as np

        def convert_for_json(obj):
            """Chuyển đổi numpy types cho JSON serialization"""
            if isinstance(obj, (np.integer, np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_for_json(value) for key, value in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_for_json(item) for item in obj]
            else:
                return obj

        # Tạo dữ liệu JSON với conversion
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'total_count': len(detections),
            'settings': convert_for_json(settings),
            'detections': [],
            'statistics': convert_for_json(statistics),
            'file_info': {
                'image_file': os.path.basename(image_path),
                'json_file': os.path.basename(json_path),
                'report_file': f"{base_name}_report.txt"
            }
        }

        # Thêm detections với conversion
        for i, det in enumerate(detections, 1):
            # Lấy giá trị với fallback
            bbox = det.get('bbox', [0, 0, 0, 0])
            bbox = [convert_for_json(x) for x in bbox]

            det_info = {
                'id': i,
                'class': str(det.get('class', 'unknown')),
                'class_vn': str(PRODUCT_NAMES_VI.get(det.get('class', 'unknown'), det.get('class', 'unknown'))),
                'quality': str(det.get('quality', 'unknown')),
                'quality_vn': str(QUALITY_NAMES_VI.get(det.get('quality', 'unknown'), det.get('quality', 'unknown'))),
                'size_category': str(det.get('size_category', 'Không xác định')),
                'size_px': convert_for_json(det.get('size_px', 0)),
                'quality_score': convert_for_json(det.get('quality_score', 0)),
                'bbox': {
                    'x1': bbox[0],
                    'y1': bbox[1],
                    'x2': bbox[2],
                    'y2': bbox[3]
                },
                'width': convert_for_json(det.get('width', 0)),
                'height': convert_for_json(det.get('height', 0)),
                'area': convert_for_json(det.get('area', 0))
            }
            results_data['detections'].append(det_info)

        # Chuyển đổi toàn bộ trước khi lưu
        results_data = convert_for_json(results_data)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        results['json_path'] = json_path
        print(f"✅ Đã lưu JSON: {json_path}")

        # 8. Lưu báo cáo text
        report_path = os.path.join(output_dir, f"{base_name}_report.txt")
        generate_report(report_path, detections, statistics, settings)
        results['report_path'] = report_path
        print(f"✅ Đã lưu báo cáo: {report_path}")

        # 9. Lưu Excel nếu pandas có
        try:
            import pandas as pd
            excel_path = os.path.join(output_dir, f"{base_name}_data.xlsx")
            if export_to_excel(detections, statistics, excel_path):
                results['excel_path'] = excel_path
                print(f"✅ Đã lưu Excel: {excel_path}")
        except ImportError:
            print("⚠️ Pandas không được cài đặt, bỏ qua export Excel")

        # 10. Tạo overlay
        try:
            overlay_path = os.path.join(output_dir, f"{base_name}_overlay.jpg")
            if create_overlay_image(processed_image, detections, overlay_path):
                results['overlay_path'] = overlay_path
                print(f"✅ Đã lưu overlay: {overlay_path}")
        except Exception as e:
            print(f"⚠️ Không tạo được overlay: {e}")

        # 11. Thông báo thành công
        file_count = len([k for k in results.keys() if k.endswith('_path')])
        messagebox.showinfo(
            "Thành công",
            f"✅ Đã lưu {file_count} file kết quả vào:\n{output_dir}"
        )

        return results

    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")
        return None

def generate_report(file_path, detections, statistics, settings):
    """Tạo báo cáo text"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("BÁO CÁO PHÂN TÍCH SẢN PHẨM NÔNG NGHIỆP\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Loại sản phẩm: {PRODUCT_NAMES_VI.get(settings.get('product_type', 'auto'), settings.get('product_type', 'auto'))}\n")
        f.write(f"Ngưỡng tin cậy: {settings.get('confidence_threshold', 0.5):.2f}\n")
        f.write(f"Phân loại chất lượng: {'Bật' if settings.get('quality_analysis', True) else 'Tắt'}\n")
        f.write(f"Phân loại kích thước: {'Bật' if settings.get('size_analysis', True) else 'Tắt'}\n")
        f.write(f"Tổng số sản phẩm: {len(detections)}\n\n")

        f.write("CHI TIẾT PHÂN LOẠI:\n")
        f.write("-" * 40 + "\n")
        f.write(f"{'STT':>4} {'Loại SP':<12} {'Chất lượng':<15} {'Kích thước':<15} {'Điểm số':<10} {'Size(px)':<10}\n")
        f.write("-" * 80 + "\n")

        for i, result in enumerate(detections, 1):
            class_name = PRODUCT_NAMES_VI.get(result['class'], result['class'])
            quality_name = QUALITY_NAMES_VI.get(result['quality'], result['quality'])
            f.write(f"{i:4d} {class_name:<12} {quality_name:<15} {result['size_category']:<15} "
                   f"{result['quality_score']:<10.2f} {result['size_px']:<10.0f}\n")

        f.write("\nTHỐNG KÊ TỔNG HỢP:\n")
        f.write("-" * 40 + "\n")

        if 'quality_counts' in statistics:
            f.write("Phân bố chất lượng:\n")
            for quality, count in statistics['quality_counts'].items():
                quality_vn = QUALITY_NAMES_VI.get(quality, quality)
                percentage = (count / len(detections) * 100) if detections else 0
                f.write(f"  {quality_vn:<15}: {count:3d} ({percentage:5.1f}%)\n")

        if 'size_counts' in statistics:
            f.write("\nPhân bố kích thước:\n")
            for size, count in statistics['size_counts'].items():
                percentage = (count / len(detections) * 100) if detections else 0
                f.write(f"  {size:<15}: {count:3d} ({percentage:5.1f}%)\n")

        f.write("\nCHỈ SỐ CHẤT LƯỢNG:\n")
        f.write("-" * 40 + "\n")
        f.write(f"  Điểm chất lượng trung bình: {statistics.get('avg_quality_score', 0):.2f}/1.0\n")
        f.write(f"  Tỷ lệ hỏng: {statistics.get('defect_rate', 0):.1f}%\n")
        f.write(f"  Sản phẩm chất lượng: {statistics.get('quality_good', 0)}/{len(detections)}\n")
        f.write(f"  Tỷ lệ chất lượng: {(statistics.get('quality_good', 0)/len(detections)*100) if detections else 0:.1f}%\n")

        f.write("\nKẾT LUẬN:\n")
        f.write("-" * 40 + "\n")
        defect_rate = statistics.get('defect_rate', 0)
        if defect_rate < 5:
            f.write("  ✅ Chất lượng tốt, tỷ lệ hỏng thấp\n")
        elif defect_rate < 20:
            f.write("  ⚠️  Chất lượng trung bình, cần kiểm tra\n")
        else:
            f.write("  ❌ Chất lượng kém, tỷ lệ hỏng cao\n")

        f.write(f"\n{'='*60}\n")
        f.write("Hệ thống phân loại sản phẩm nông nghiệp\n")
        f.write("Phiên bản 1.0.0\n")


def export_to_excel(detections, statistics, excel_path):
    """Xuất dữ liệu sang Excel"""
    try:
        import pandas as pd

        # Tạo DataFrame cho detections
        detection_data = []
        for i, det in enumerate(detections, 1):
            detection_data.append({
                'STT': i,
                'Loại_SP': PRODUCT_NAMES_VI.get(det['class'], det['class']),
                'Class_English': det['class'],
                'Chất_lượng': QUALITY_NAMES_VI.get(det['quality'], det['quality']),
                'Quality_English': det['quality'],
                'Kích_thước': det['size_category'],
                'Size_px': det['size_px'],
                'Điểm_chất_lượng': det['quality_score'],
                'Width': det['width'],
                'Height': det['height'],
                'Area': det['area'],
                'X1': det['bbox'][0],
                'Y1': det['bbox'][1],
                'X2': det['bbox'][2],
                'Y2': det['bbox'][3]
            })

        df_detections = pd.DataFrame(detection_data)

        # Tạo DataFrame cho statistics
        stats_data = []
        if 'quality_counts' in statistics:
            for quality, count in statistics['quality_counts'].items():
                stats_data.append({
                    'Chỉ_số': 'Chất_lượng',
                    'Loại': QUALITY_NAMES_VI.get(quality, quality),
                    'Số_lượng': count,
                    'Tỷ_lệ': f"{(count/len(detections)*100) if detections else 0:.1f}%"
                })

        if 'size_counts' in statistics:
            for size, count in statistics['size_counts'].items():
                stats_data.append({
                    'Chỉ_số': 'Kích_thước',
                    'Loại': size,
                    'Số_lượng': count,
                    'Tỷ_lệ': f"{(count/len(detections)*100) if detections else 0:.1f}%"
                })

        df_stats = pd.DataFrame(stats_data)

        # Tạo tổng hợp
        summary_data = [{
            'Tổng_số_SP': len(detections),
            'Điểm_TB': statistics.get('avg_quality_score', 0),
            'Tỷ_lệ_hỏng': f"{statistics.get('defect_rate', 0):.1f}%",
            'SP_chất_lượng': statistics.get('quality_good', 0)
        }]
        df_summary = pd.DataFrame(summary_data)

        # Ghi ra Excel
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_detections.to_excel(writer, sheet_name='Chi_tiết', index=False)
            df_stats.to_excel(writer, sheet_name='Thống_kê', index=False)
            df_summary.to_excel(writer, sheet_name='Tổng_hợp', index=False)

            # Điều chỉnh độ rộng cột
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 30)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        return True

    except Exception as e:
        print(f"Lỗi export Excel: {e}")
        return False


def export_to_pdf(detections, statistics, pdf_path):
    """Xuất dữ liệu sang PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph("BÁO CÁO PHÂN TÍCH SẢN PHẨM NÔNG NGHIỆP", title_style))
        story.append(Spacer(1, 20))

        # Thông tin chung
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )

        story.append(Paragraph(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Paragraph(f"Tổng số sản phẩm: {len(detections)}", info_style))
        story.append(Spacer(1, 20))

        # Tạo table cho detections (chỉ 10 dòng đầu)
        if detections:
            table_data = [['STT', 'Loại SP', 'Chất lượng', 'Kích thước', 'Điểm số']]
            for i, det in enumerate(detections[:10], 1):
                table_data.append([
                    str(i),
                    PRODUCT_NAMES_VI.get(det['class'], det['class']),
                    QUALITY_NAMES_VI.get(det['quality'], det['quality']),
                    det['size_category'],
                    f"{det['quality_score']:.2f}"
                ])

            if len(detections) > 10:
                table_data.append(['...', '...', '...', '...', '...'])
                table_data.append(['Tổng', f'{len(detections)} SP', '', '', ''])

            table = Table(table_data, colWidths=[40, 80, 80, 80, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(table)
            story.append(Spacer(1, 20))

        # Thống kê
        if statistics:
            stats_text = f"""
            <b>THỐNG KÊ TỔNG HỢP:</b><br/>
            • Điểm chất lượng trung bình: {statistics.get('avg_quality_score', 0):.2f}/1.0<br/>
            • Tỷ lệ hỏng: {statistics.get('defect_rate', 0):.1f}%<br/>
            • Sản phẩm chất lượng: {statistics.get('quality_good', 0)}/{len(detections)}<br/>
            """
            story.append(Paragraph(stats_text, styles['Normal']))

        # Kết luận
        conclusion = """
        <br/><br/>
        <b>KẾT LUẬN:</b><br/>
        Báo cáo được tạo tự động bởi hệ thống phân loại sản phẩm nông nghiệp.<br/>
        Kết quả có thể được sử dụng để đánh giá chất lượng và ra quyết định.<br/>
        """
        story.append(Paragraph(conclusion, styles['Normal']))

        # Build PDF
        doc.build(story)
        return True

    except Exception as e:
        print(f"Lỗi export PDF: {e}")
        return False


def create_overlay_image(image, detections, output_path):
    """Tạo ảnh overlay với thông tin chi tiết"""
    try:
        overlay = image.copy()
        h, w = image.shape[:2]

        # Thêm watermark
        cv2.putText(overlay, f"Total: {len(detections)}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(overlay, datetime.now().strftime("%Y-%m-%d %H:%M"),
                   (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imwrite(output_path, overlay)
        return True
    except Exception as e:
        print(f"Lỗi tạo overlay: {e}")
        return False


def load_results(json_path):
    """Tải kết quả từ file JSON"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Lỗi tải file JSON: {e}")
        return None


def get_file_size(file_path):
    """Lấy kích thước file"""
    try:
        size_bytes = os.path.getsize(file_path)
        # Chuyển đổi sang đơn vị phù hợp
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    except:
        return "Unknown"


def list_output_files(output_dir=None):
    """Liệt kê các file kết quả trong thư mục"""
    if output_dir is None:
        output_dir = OUTPUTS_DIR

    results = []
    try:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(('.jpg', '.png', '.json', '.txt', '.xlsx', '.pdf')):
                    file_path = os.path.join(root, file)
                    file_info = {
                        'name': file,
                        'path': file_path,
                        'size': get_file_size(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')
                    }
                    results.append(file_info)

        # Sắp xếp theo thời gian sửa đổi (mới nhất trước)
        results.sort(key=lambda x: x['modified'], reverse=True)
        return results

    except Exception as e:
        print(f"Lỗi liệt kê file: {e}")
        return []


def convert_numpy_types(obj):
    """Chuyển đổi numpy types sang Python native types cho JSON serialization"""
    import numpy as np

    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj