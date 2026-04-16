# 视频去水印/字幕AI模块
# 提供水印检测、字幕检测、区域去除功能
# 注意: cv2/PIL/pytesseract 为可选依赖，免费层不可用时会提供模拟实现

# 可选依赖
try:
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None
    Image = None
    pytesseract = None

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetectedRegion:
    """检测到的区域"""
    x: int
    y: int
    width: int
    height: int
    type: str  # 'watermark' | 'subtitle' | 'manual'
    confidence: float = 1.0
    label: str = ""

class WatermarkDetector:
    """水印检测器 - 使用OpenCV检测固定位置的重复图案"""
    
    def __init__(self):
        if not CV2_AVAILABLE:
            logger.warning("WatermarkDetector: cv2不可用，功能受限")
        self.min_watermark_width = 50
        self.min_watermark_height = 20
        self.confidence_threshold = 0.6
        
    def detect(self, frame) -> List[DetectedRegion]:
        """
        检测视频帧中的水印区域
        
        Args:
            frame: BGR格式的视频帧
            
        Returns:
            检测到的水印区域列表
            
        Raises:
            RuntimeError: 当cv2不可用时
        """
        if not CV2_AVAILABLE:
            raise RuntimeError(
                "水印检测功能不可用: cv2/OpenCV未安装\n"
                "如需使用此功能，请在有OpenCV环境中运行"
            )
        
        regions = []
        
        # 1. 检测固定位置水印（角落和边缘）
        corner_regions = self._detect_corner_watermarks(frame)
        regions.extend(corner_regions)
        
        # 2. 检测重复图案水印（Logo水印）
        logo_regions = self._detect_logo_watermark(frame)
        regions.extend(logo_regions)
        
        # 3. 检测半透明水印
        transparent_regions = self._detect_transparent_watermark(frame)
        regions.extend(transparent_regions)
        
        return self._merge_overlapping_regions(regions)
    
    def _detect_corner_watermarks(self, frame) -> List[DetectedRegion]:
        """检测角落固定位置的水印"""
        regions = []
        h, w = frame.shape[:2]
        
        # 常见水印位置区域
        candidate_regions = [
            # 左上角
            (0, 0, w // 4, h // 6),
            # 右上角
            (w * 3 // 4, 0, w // 4, h // 6),
            # 左下角（字幕区域）
            (0, h - h // 5, w // 3, h // 5),
            # 右下角
            (w * 2 // 3, h - h // 6, w // 3, h // 6),
            # 底部居中（字幕）
            (w // 6, h - h // 6, w * 2 // 3, h // 6),
            # 顶部居中
            (w // 4, 0, w // 2, h // 8),
        ]
        
        for x, y, cw, ch in candidate_regions:
            roi = frame[y:y+ch, x:x+cw]
            if self._is_watermark_region(roi):
                regions.append(DetectedRegion(
                    x=x, y=y, width=cw, height=ch,
                    type='watermark',
                    confidence=0.7,
                    label='corner_watermark'
                ))
        
        return regions
    
    def _detect_logo_watermark(self, frame) -> List[DetectedRegion]:
        """检测Logo类型水印（重复出现的小区域）"""
        regions = []
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 使用模板匹配检测重复图案
        # 由于不知道具体模板，这里使用特征检测
        orb = cv2.ORB_create()
        keypoints, descriptors = orb.detectAndCompute(gray, None)
        
        # 找到角点（可能是Logo边界）
        corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=10)
        
        if corners is not None:
            # 聚类角点找出水印区域
            corner_points = corners.reshape(-1, 2)
            clusters = self._cluster_points(corner_points, eps=30)
            
            for cluster in clusters:
                if len(cluster) > 5:  # 多个角点聚类
                    xs = [p[0] for p in cluster]
                    ys = [p[1] for p in cluster]
                    x, y = int(np.min(xs)), int(np.min(ys))
                    cw, ch = int(np.max(xs) - x), int(np.max(ys) - y)
                    
                    if (self.min_watermark_width <= cw <= frame.shape[1] // 3 and
                        self.min_watermark_height <= ch <= frame.shape[0] // 4):
                        regions.append(DetectedRegion(
                            x=x, y=y, width=cw, height=ch,
                            type='watermark',
                            confidence=0.65,
                            label='logo_watermark'
                        ))
        
        return regions
    
    def _detect_transparent_watermark(self, frame) -> List[DetectedRegion]:
        """检测半透明水印"""
        regions = []
        h, w = frame.shape[:2]
        
        # 转换到LAB色彩空间检测低对比度区域
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # 使用边缘检测找水印边缘
        edges = cv2.Canny(l_channel, 50, 150)
        
        # 形态学操作连接边缘
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # 找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            area = cw * ch
            
            # 过滤太大或太小的区域
            if (self.min_watermark_width <= cw <= w // 3 and
                self.min_watermark_height <= ch <= h // 4 and
                area < (w * h) // 20):
                
                # 检查是否是半透明区域（方差较小）
                roi = frame[y:y+ch, x:x+cw]
                if np.std(roi) < 50:  # 低方差表示可能是水印
                    regions.append(DetectedRegion(
                        x=x, y=y, width=cw, height=ch,
                        type='watermark',
                        confidence=0.6,
                        label='transparent_watermark'
                    ))
        
        return regions
    
    def _is_watermark_region(self, roi) -> bool:
        """判断ROI是否可能是水印区域"""
        if roi.size == 0:
            return False
        
        # 计算颜色方差（Logo水印通常颜色单一）
        std_dev = np.std(roi)
        
        # 水印通常对比度较低或颜色均匀
        return std_dev < 80 or (np.mean(roi) > 200 and std_dev < 30)
    
    def _cluster_points(self, points, eps: float = 30) -> List:
        """简单的距离聚类"""
        clusters = []
        used = set()
        
        for i, p in enumerate(points):
            if i in used:
                continue
                
            cluster = [p]
            used.add(i)
            
            for j, q in enumerate(points):
                if j in used:
                    continue
                if np.linalg.norm(p - q) < eps:
                    cluster.append(q)
                    used.add(j)
            
            clusters.append(np.array(cluster))
        
        return clusters
    
    def _merge_overlapping_regions(self, regions: List[DetectedRegion], iou_threshold: float = 0.5) -> List[DetectedRegion]:
        """合并重叠的区域"""
        if not regions:
            return []
        
        merged = []
        used = set()
        
        for i, reg1 in enumerate(regions):
            if i in used:
                continue
            
            # 找出所有与reg1重叠的区域
            overlap_group = [reg1]
            used.add(i)
            
            for j, reg2 in enumerate(regions):
                if j in used:
                    continue
                if self._compute_iou(reg1, reg2) > iou_threshold:
                    overlap_group.append(reg2)
                    used.add(j)
            
            # 合并为一个区域
            xs = [r.x for r in overlap_group]
            ys = [r.y for r in overlap_group]
            x2s = [r.x + r.width for r in overlap_group]
            y2s = [r.y + r.height for r in overlap_group]
            
            merged.append(DetectedRegion(
                x=min(xs), y=min(ys),
                width=max(x2s) - min(xs),
                height=max(y2s) - min(ys),
                type='watermark',
                confidence=np.mean([r.confidence for r in overlap_group]),
                label='merged_watermark'
            ))
        
        return merged
    
    def _compute_iou(self, reg1: DetectedRegion, reg2: DetectedRegion) -> float:
        """计算两个区域的IoU"""
        x1 = max(reg1.x, reg2.x)
        y1 = max(reg1.y, reg2.y)
        x2 = min(reg1.x + reg1.width, reg2.x + reg2.width)
        y2 = min(reg1.y + reg1.height, reg2.y + reg2.height)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        union = reg1.width * reg1.height + reg2.width * reg2.height - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def get_common_positions(self, frame_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """
        返回常见水印位置（不依赖cv2）
        用于手动去除时参考
        """
        h, w = frame_shape
        return [
            {"name": "左上角", "x": 0, "y": 0, "width": w // 4, "height": h // 6},
            {"name": "右上角", "x": w * 3 // 4, "y": 0, "width": w // 4, "height": h // 6},
            {"name": "左下角", "x": 0, "y": h - h // 5, "width": w // 3, "height": h // 5},
            {"name": "右下角", "x": w * 2 // 3, "y": h - h // 6, "width": w // 3, "height": h // 6},
            {"name": "底部居中", "x": w // 6, "y": h - h // 6, "width": w * 2 // 3, "height": h // 6},
            {"name": "顶部居中", "x": w // 4, "y": 0, "width": w // 2, "height": h // 8},
        ]


class SubtitleDetector:
    """字幕检测器 - 使用OCR检测视频底部文字区域"""
    
    def __init__(self):
        if not CV2_AVAILABLE:
            logger.warning("SubtitleDetector: cv2/pytesseract不可用，功能受限")
        self.subtitle_height_ratio = 0.15  # 字幕区域占画面高度的最大比例
        self.subtitle_y_offset = 0.75  # 字幕通常在画面75%以下
        self.min_text_height = 15  # 最小文字高度
        
    def detect(self, frame) -> List[DetectedRegion]:
        """
        检测视频帧中的字幕区域
        
        Args:
            frame: BGR格式的视频帧
            
        Returns:
            检测到的字幕区域列表
            
        Raises:
            RuntimeError: 当cv2/pytesseract不可用时
        """
        if not CV2_AVAILABLE:
            raise RuntimeError(
                "字幕检测功能不可用: cv2或pytesseract未安装\n"
                "如需使用此功能，请在有OpenCV和Tesseract环境中运行"
            )
        
        regions = []
        h, w = frame.shape[:2]
        
        # 1. 基于位置检测（底部区域）
        position_regions = self._detect_by_position(frame)
        regions.extend(position_regions)
        
        # 2. 基于OCR检测
        ocr_regions = self._detect_by_ocr(frame)
        regions.extend(ocr_regions)
        
        # 3. 基于边缘检测（字幕通常有下划线或边框）
        edge_regions = self._detect_by_edge(frame)
        regions.extend(edge_regions)
        
        # 合并结果
        merged = self._merge_nearby_regions(regions)
        
        return merged
    
    def _detect_by_position(self, frame) -> List[DetectedRegion]:
        """基于位置检测字幕区域"""
        regions = []
        h, w = frame.shape[:2]
        
        # 常见的字幕位置
        subtitle_y = int(h * self.subtitle_y_offset)
        subtitle_h = int(h * self.subtitle_height_ratio)
        
        # 底部居中区域
        regions.append(DetectedRegion(
            x=w // 6, y=subtitle_y,
            width=w * 2 // 3, height=subtitle_h,
            type='subtitle',
            confidence=0.5,
            label='position_subtitle'
        ))
        
        # 底部全宽区域
        regions.append(DetectedRegion(
            x=0, y=int(h * 0.85),
            width=w, height=int(h * 0.15),
            type='subtitle',
            confidence=0.4,
            label='bottom_bar'
        ))
        
        return regions
    
    def _detect_by_ocr(self, frame) -> List[DetectedRegion]:
        """使用OCR检测字幕"""
        regions = []
        h, w = frame.shape[:2]
        
        try:
            # 转换为RGB格式（PIL格式）
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # 设置只检测水平文字
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789！？。，、""''（）【】…—·:;.,!?"'
            
            # 获取文字块位置
            data = pytesseract.image_to_data(pil_image, config=custom_config, output_type=pytesseract.Output.DICT)
            
            n_boxes = len(data['level'])
            text_regions = []
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text and int(data['conf'][i]) > 30:
                    x, y, w_box, h_box = (
                        int(data['left'][i]),
                        int(data['top'][i]),
                        int(data['width'][i]),
                        int(data['height'][i])
                    )
                    
                    # 过滤太小或位置不合理的区域
                    if h_box >= self.min_text_height and y > frame.shape[0] * 0.6:
                        text_regions.append((x, y, w_box, h_box, text))
            
            # 合并相邻的文字区域
            if text_regions:
                merged_regions = self._merge_text_regions(text_regions, frame.shape[1])
                
                for x, y, cw, ch in merged_regions:
                    regions.append(DetectedRegion(
                        x=x, y=y, width=cw, height=ch,
                        type='subtitle',
                        confidence=0.8,
                        label='ocr_subtitle'
                    ))
                    
        except Exception as e:
            logger.warning(f"OCR检测失败: {e}")
        
        return regions
    
    def _detect_by_edge(self, frame) -> List[DetectedRegion]:
        """基于边缘检测字幕"""
        regions = []
        h, w = frame.shape[:2]
        
        # 转换到灰度
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 只检查底部区域
        bottom_region = gray[int(h * 0.7):, :]
        
        # 水平线检测（字幕通常有下划线）
        hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
        detected_horizontal = cv2.morphologyEx(bottom_region, cv2.MORPH_OPEN, hori_kernel)
        
        # 找水平线
        contours, _ = cv2.findContours(detected_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            # 水平线特征
            if cw > 100 and ch < 5:
                absolute_y = int(h * 0.7) + y - 30  # 字幕通常在横线上方
                if absolute_y < int(h * 0.85) and absolute_y > int(h * 0.5):
                    regions.append(DetectedRegion(
                        x=max(0, x - 20), y=max(0, absolute_y),
                        width=min(w, cw + 40), height=40,
                        type='subtitle',
                        confidence=0.6,
                        label='underline_subtitle'
                    ))
        
        return regions
    
    def _merge_text_regions(self, text_regions: List, frame_width: int) -> List[Tuple]:
        """合并相邻的文字区域"""
        if not text_regions:
            return []
        
        # 按y坐标分组
        lines = {}
        for x, y, w, h, text in text_regions:
            line_key = y // 30  # 同一行文字
            if line_key not in lines:
                lines[line_key] = []
            lines[line_key].append((x, y, w, h))
        
        merged = []
        for line_y, boxes in lines.items():
            if len(boxes) >= 1:
                # 合并同一行的所有文字框
                xs = [b[0] for b in boxes]
                ys = [b[1] for b in boxes]
                x2s = [b[0] + b[2] for b in boxes]
                y2s = [b[1] + b[3] for b in boxes]
                
                merged.append((
                    max(0, min(xs) - 20),
                    max(0, min(ys) - 10),
                    min(frame_width, max(x2s) + 20) - max(0, min(xs) - 20),
                    max(y2s) - min(ys) + 20
                ))
        
        return merged
    
    def _merge_nearby_regions(self, regions: List[DetectedRegion]) -> List[DetectedRegion]:
        """合并相近的区域"""
        if not regions:
            return []
        
        # 按置信度排序
        sorted_regions = sorted(regions, key=lambda r: r.confidence, reverse=True)
        
        merged = []
        used = set()
        
        for i, reg in enumerate(sorted_regions):
            if i in used:
                continue
            
            # 找所有与当前区域相近的
            group = [reg]
            used.add(i)
            
            for j, other in enumerate(sorted_regions[i+1:], i+1):
                if j in used:
                    continue
                # 检查y轴是否接近（同一水平位置）
                if abs(reg.y - other.y) < 50:
                    group.append(other)
                    used.add(j)
            
            # 合并
            xs = [r.x for r in group]
            ys = [r.y for r in group]
            x2s = [r.x + r.width for r in group]
            y2s = [r.y + r.height for r in group]
            
            merged.append(DetectedRegion(
                x=min(xs), y=min(ys),
                width=max(x2s) - min(xs),
                height=max(y2s) - min(ys),
                type='subtitle',
                confidence=np.mean([r.confidence for r in group]),
                label='merged_subtitle'
            ))
        
        return merged


class WatermarkRemover:
    """水印去除器 - 使用图像修复技术"""
    
    def __init__(self):
        if not CV2_AVAILABLE:
            logger.warning("WatermarkRemover: cv2不可用，功能受限")
        self.inpaint_method = cv2.INPAINT_TELEA if CV2_AVAILABLE else None  # TELEA算法，效果更好
        # cv2.INPAINT_NS  # Navier-Stokes算法，速度更快
    
    def remove(self, frame, regions: List[DetectedRegion], expand: int = 5):
        """
        去除水印/字幕
        
        Args:
            frame: 输入视频帧
            regions: 要去除的区域列表
            expand: 区域扩展像素数
            
        Returns:
            处理后的视频帧
            
        Raises:
            RuntimeError: 当cv2不可用时
        """
        if not CV2_AVAILABLE:
            raise RuntimeError(
                "水印去除功能不可用: cv2/OpenCV未安装\n"
                "如需使用此功能，请在有OpenCV环境中运行"
            )
        
        result = frame.copy()
        
        for region in regions:
            # 扩展区域
            x = max(0, region.x - expand)
            y = max(0, region.y - expand)
            x2 = min(frame.shape[1], region.x + region.width + expand)
            y2 = min(frame.shape[0], region.y + region.height + expand)
            
            # 创建掩码
            mask = np.zeros(result.shape[:2], dtype=np.uint8)
            mask[y:y2, x:x2] = 255
            
            # 形态学操作优化掩码
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            
            # 图像修复
            result = cv2.inpaint(result, mask, 3, self.inpaint_method)
        
        return result
    
    def remove_by_coords(self, frame, coords: List[List[int]]):
        """
        根据坐标去除区域
        
        Args:
            frame: 输入视频帧
            coords: [[x, y, width, height], ...]
            
        Returns:
            处理后的视频帧
        """
        regions = [
            DetectedRegion(x=c[0], y=c[1], width=c[2], height=c[3], type='manual')
            for c in coords
        ]
        return self.remove(frame, regions)


class WatermarkProcessor:
    """视频水印处理主类"""
    
    def __init__(self):
        if CV2_AVAILABLE:
            self.detector = WatermarkDetector()
            self.subtitle_detector = SubtitleDetector()
            self.remover = WatermarkRemover()
        else:
            # 保存未初始化的状态，后续调用会检测
            self.detector = None
            self.subtitle_detector = None
            self.remover = None
            logger.warning(
                "WatermarkProcessor: OpenCV依赖不可用，水印功能受限\n"
                "可用的降级功能:\n"
                "  - get_common_positions(): 获取常见水印位置供参考"
            )
        
    def detect_watermark(self, frame) -> List[Dict[str, Any]]:
        """检测水印"""
        if self.detector is None:
            raise RuntimeError("水印检测不可用: OpenCV未安装")
        regions = self.detector.detect(frame)
        return [self._region_to_dict(r) for r in regions]
    
    def detect_subtitle(self, frame) -> List[Dict[str, Any]]:
        """检测字幕"""
        if self.subtitle_detector is None:
            raise RuntimeError("字幕检测不可用: OpenCV未安装")
        regions = self.subtitle_detector.detect(frame)
        return [self._region_to_dict(r) for r in regions]
    
    def detect_all(self, frame) -> Dict[str, Any]:
        """同时检测水印和字幕"""
        if self.detector is None or self.subtitle_detector is None:
            raise RuntimeError("检测功能不可用: OpenCV未安装")
        watermark_regions = self.detector.detect(frame)
        subtitle_regions = self.subtitle_detector.detect(frame)
        
        return {
            "watermarks": [self._region_to_dict(r) for r in watermark_regions],
            "subtitles": [self._region_to_dict(r) for r in subtitle_regions],
            "all_regions": [self._region_to_dict(r) for r in watermark_regions + subtitle_regions]
        }
    
    def remove_regions(self, frame, regions: List[Dict]) -> Any:
        """去除指定区域"""
        if self.remover is None:
            raise RuntimeError("水印去除不可用: OpenCV未安装")
        detected_regions = [
            DetectedRegion(
                x=r['x'], y=r['y'],
                width=r['width'], height=r['height'],
                type=r.get('type', 'manual'),
                confidence=r.get('confidence', 1.0),
                label=r.get('label', '')
            )
            for r in regions
        ]
        return self.remover.remove(frame, detected_regions)
    
    def get_common_positions(self, frame_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """
        获取常见水印位置（不依赖cv2）
        可用于手动去除时的参考坐标
        """
        detector = WatermarkDetector()
        return detector.get_common_positions(frame_shape)
    
    def _region_to_dict(self, region: DetectedRegion) -> Dict[str, Any]:
        """将DetectedRegion转为字典"""
        return {
            'x': region.x,
            'y': region.y,
            'width': region.width,
            'height': region.height,
            'type': region.type,
            'confidence': region.confidence,
            'label': region.label
        }


# 全局处理器实例
processor = WatermarkProcessor()


def is_cv2_available() -> bool:
    """检查OpenCV是否可用"""
    return CV2_AVAILABLE


def detect_watermark_from_frame(frame) -> List[Dict[str, Any]]:
    """从帧检测水印的便捷函数"""
    return processor.detect_watermark(frame)


def detect_subtitle_from_frame(frame) -> List[Dict[str, Any]]:
    """从帧检测字幕的便捷函数"""
    return processor.detect_subtitle(frame)


def remove_watermark_from_frame(frame, coords: List[List[int]]):
    """从帧去除水印的便捷函数"""
    return processor.remover.remove_by_coords(frame, coords)


def get_common_watermark_positions(frame_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
    """
    获取常见水印位置（不依赖OpenCV）
    返回可供参考的标准水印坐标
    """
    return processor.get_common_positions(frame_shape)
