"""
Tính toán thống kê
"""
from collections import Counter, defaultdict
import numpy as np


def calculate_statistics(detections):
    """Tính toán thống kê từ kết quả phát hiện"""
    if not detections:
        return {'total': 0, 'message': 'Không có dữ liệu'}

    total_count = len(detections)

    # 1. Đếm theo chất lượng
    quality_counts = Counter([r['quality'] for r in detections])

    # 2. Đếm theo kích thước
    size_counts = Counter([r['size_category'] for r in detections])

    # 3. Tính tỷ lệ hỏng
    defect_count = quality_counts.get('hong', 0) + quality_counts.get('kem', 0)
    defect_rate = (defect_count / total_count * 100) if total_count > 0 else 0

    # 4. Tính điểm chất lượng trung bình
    quality_scores = [r['quality_score'] for r in detections]
    avg_quality_score = np.mean(quality_scores) if quality_scores else 0

    # 5. Sản phẩm chất lượng (tốt + chín)
    quality_good = quality_counts.get('tot', 0) + quality_counts.get('chin', 0)

    # 6. Tính toán phân phối kích thước
    size_values = [r['size_px'] for r in detections]
    size_stats = {
        'min': min(size_values) if size_values else 0,
        'max': max(size_values) if size_values else 0,
        'mean': np.mean(size_values) if size_values else 0,
        'std': np.std(size_values) if len(size_values) > 1 else 0,
        'median': np.median(size_values) if size_values else 0
    }

    # 7. Phân tích theo loại sản phẩm
    product_stats = defaultdict(lambda: {'count': 0, 'qualities': Counter(), 'sizes': Counter()})
    for det in detections:
        product = det['class']
        product_stats[product]['count'] += 1
        product_stats[product]['qualities'][det['quality']] += 1
        product_stats[product]['sizes'][det['size_category']] += 1

    # 8. Tính hệ số biến thiên (CV) cho kích thước
    cv_size = (size_stats['std'] / size_stats['mean'] * 100) if size_stats['mean'] > 0 else 0

    # 9. Tính điểm chất lượng theo nhóm
    quality_group_scores = defaultdict(list)
    for det in detections:
        quality_group_scores[det['quality']].append(det['quality_score'])

    avg_scores_by_quality = {}
    for quality, scores in quality_group_scores.items():
        avg_scores_by_quality[quality] = np.mean(scores) if scores else 0

    return {
        'total': total_count,
        'quality_counts': quality_counts,
        'size_counts': size_counts,
        'defect_count': defect_count,
        'defect_rate': defect_rate,
        'avg_quality_score': float(avg_quality_score),
        'quality_good': quality_good,
        'quality_good_rate': (quality_good / total_count * 100) if total_count > 0 else 0,
        'size_stats': size_stats,
        'product_stats': dict(product_stats),
        'cv_size': float(cv_size),
        'avg_scores_by_quality': avg_scores_by_quality,
        'quality_scores': [float(score) for score in quality_scores],
        'size_values': [float(size) for size in size_values],

        # Thêm các chỉ số phụ
        'quality_distribution': {
            quality: {
                'count': count,
                'percentage': (count / total_count * 100) if total_count > 0 else 0,
                'avg_score': avg_scores_by_quality.get(quality, 0)
            }
            for quality, count in quality_counts.items()
        },

        'size_distribution': {
            size: {
                'count': count,
                'percentage': (count / total_count * 100) if total_count > 0 else 0
            }
            for size, count in size_counts.items()
        }
    }


def generate_statistics_report(detections, settings=None):
    """Tạo báo cáo thống kê chi tiết"""
    if settings is None:
        settings = {}

    stats = calculate_statistics(detections)

    report = {
        'summary': {
            'total_products': stats['total'],
            'defect_rate': stats['defect_rate'],
            'avg_quality_score': stats['avg_quality_score'],
            'quality_good_rate': stats['quality_good_rate']
        },

        'quality_analysis': {
            'distribution': stats['quality_distribution'],
            'defect_details': {
                'total_defects': stats['defect_count'],
                'defect_rate': stats['defect_rate'],
                'hong_count': stats['quality_counts'].get('hong', 0),
                'kem_count': stats['quality_counts'].get('kem', 0)
            }
        },

        'size_analysis': {
            'distribution': stats['size_distribution'],
            'statistics': stats['size_stats'],
            'cv_size': stats['cv_size'],
            'size_variability': 'Thấp' if stats['cv_size'] < 20 else
                               'Trung bình' if stats['cv_size'] < 40 else 'Cao'
        },

        'product_analysis': stats.get('product_stats', {}),

        'recommendations': generate_recommendations(stats)
    }

    return report


def generate_recommendations(stats):
    """Tạo khuyến nghị dựa trên thống kê"""
    recommendations = []

    # Kiểm tra chất lượng
    if stats['defect_rate'] > 20:
        recommendations.append({
            'type': 'warning',
            'message': 'Tỷ lệ hỏng cao (>20%). Cần kiểm tra lại quy trình bảo quản.',
            'suggestion': '• Kiểm tra điều kiện bảo quản\n• Phân loại kỹ hơn trước khi đóng gói'
        })
    elif stats['defect_rate'] > 10:
        recommendations.append({
            'type': 'warning',
            'message': 'Tỷ lệ hỏng ở mức trung bình (10-20%).',
            'suggestion': '• Theo dõi chất lượng thường xuyên\n• Cải thiện quy trình phân loại'
        })
    else:
        recommendations.append({
            'type': 'success',
            'message': 'Tỷ lệ hỏng thấp (<10%). Chất lượng tốt.',
            'suggestion': '• Duy trì quy trình hiện tại\n• Tiếp tục giám sát chất lượng'
        })

    # Kiểm tra điểm chất lượng trung bình
    if stats['avg_quality_score'] < 0.5:
        recommendations.append({
            'type': 'warning',
            'message': 'Điểm chất lượng trung bình thấp.',
            'suggestion': '• Cải thiện chất lượng nguyên liệu\n• Tối ưu hóa quy trình xử lý'
        })

    # Kiểm tra độ đồng đều kích thước
    if stats.get('cv_size', 0) > 40:
        recommendations.append({
            'type': 'warning',
            'message': 'Độ đồng đều kích thước thấp.',
            'suggestion': '• Phân loại theo kích thước kỹ hơn\n• Tiêu chuẩn hóa kích thước sản phẩm'
        })

    # Thêm khuyến nghị chung
    recommendations.append({
        'type': 'info',
        'message': 'Tổng quan chất lượng',
        'suggestion': f'• Sản phẩm chất lượng: {stats["quality_good"]}/{stats["total"]} ({stats["quality_good_rate"]:.1f}%)\n• Điểm TB: {stats["avg_quality_score"]:.2f}/1.0'
    })

    return recommendations


def calculate_batch_statistics(batch_results):
    """Tính thống kê cho batch nhiều ảnh"""
    all_detections = []
    image_stats = []

    for result in batch_results:
        if 'result' in result and 'detections' in result['result']:
            detections = result['result']['detections']
            all_detections.extend(detections)

            # Thống kê cho từng ảnh
            img_stats = calculate_statistics(detections)
            img_stats['image_path'] = result['image_path']
            image_stats.append(img_stats)

    # Tổng hợp thống kê toàn batch
    batch_stats = calculate_statistics(all_detections)

    # Thêm thống kê về các ảnh
    if image_stats:
        total_images = len(image_stats)
        avg_per_image = batch_stats['total'] / total_images if total_images > 0 else 0

        batch_stats.update({
            'total_images': total_images,
            'avg_detections_per_image': avg_per_image,
            'image_stats': image_stats,
            'images_with_detections': sum(1 for s in image_stats if s['total'] > 0),
            'max_detections_image': max((s['total'] for s in image_stats), default=0),
            'min_detections_image': min((s['total'] for s in image_stats), default=0)
        })

    return batch_stats


def calculate_confidence_intervals(data, confidence=0.95):
    """Tính khoảng tin cậy"""
    import numpy as np
    from scipy import stats

    if len(data) < 2:
        return {'mean': np.mean(data) if data else 0, 'ci_lower': 0, 'ci_upper': 0}

    mean = np.mean(data)
    std = np.std(data, ddof=1)
    n = len(data)

    # Tính t-value
    t_value = stats.t.ppf((1 + confidence) / 2, n - 1)

    # Tính margin of error
    margin = t_value * (std / np.sqrt(n))

    return {
        'mean': float(mean),
        'ci_lower': float(mean - margin),
        'ci_upper': float(mean + margin),
        'margin': float(margin)
    }