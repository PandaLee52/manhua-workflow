# 视频去水印处理模块
# 使用ffmpeg和OpenCV处理视频帧

import cv2
import numpy as np
import subprocess
import os
import uuid
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class VideoFrameExtractor:
    """视频帧提取器"""
    
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_frames(self, video_path: str, output_dir: Optional[str] = None, 
                      fps: float = 1.0, start_time: float = 0, 
                      duration: Optional[float] = None) -> List[str]:
        """
        从视频提取帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            fps: 提取帧率
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            
        Returns:
            帧文件路径列表
        """
        if output_dir is None:
            output_dir = self.temp_dir / f"frames_{uuid.uuid4().hex[:8]}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用ffmpeg提取帧
        output_pattern = str(output_dir / "frame_%06d.png")
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", str(start_time),
            "-fps_mode", "fps",
            "-vf", f"fps={fps}",
        ]
        
        if duration:
            cmd.extend(["-t", str(duration)])
        
        cmd.extend([
            "-q:v", "2",  # JPEG质量
            "-y",  # 覆盖输出
            output_pattern
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.warning(f"ffmpeg提取帧失败: {result.stderr}")
                # 备用方案：使用OpenCV
                return self._extract_frames_cv2(video_path, output_dir, fps, start_time, duration)
        except Exception as e:
            logger.warning(f"ffmpeg提取帧异常: {e}")
            return self._extract_frames_cv2(video_path, output_dir, fps, start_time, duration)
        
        # 获取提取的帧文件
        frames = sorted(output_dir.glob("frame_*.png"))
        return [str(f) for f in frames]
    
    def _extract_frames_cv2(self, video_path: str, output_dir: Path,
                           fps: float, start_time: float, 
                           duration: Optional[float]) -> List[str]:
        """使用OpenCV提取帧（备用方案）"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        # 设置开始位置
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
        
        # 计算帧间隔
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = max(1, int(video_fps / fps))
        
        frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 检查时长限制
            if duration and frame_count * frame_interval / video_fps > duration:
                break
            
            if frame_count % frame_interval == 0:
                output_path = output_dir / f"frame_{len(frames):06d}.png"
                cv2.imwrite(str(output_path), frame)
                frames.append(str(output_path))
            
            frame_count += 1
        
        cap.release()
        return frames
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC))
        }
        
        cap.release()
        return info


class VideoFrameProcessor:
    """视频帧处理器 - 处理单帧或多帧"""
    
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def process_frame(self, frame: np.ndarray, regions: List[Dict]) -> np.ndarray:
        """处理单帧，去除指定区域"""
        from watermark_remover import WatermarkRemover, DetectedRegion
        
        remover = WatermarkRemover()
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
        return remover.remove(frame, detected_regions)
    
    def process_frames_batch(self, frame_paths: List[str], regions: List[Dict],
                             output_dir: Optional[str] = None,
                             workers: int = 4) -> List[str]:
        """
        批量处理帧
        
        Args:
            frame_paths: 输入帧路径列表
            regions: 要去除的区域列表
            output_dir: 输出目录
            workers: 并行处理线程数
            
        Returns:
            处理后的帧路径列表
        """
        if output_dir is None:
            output_dir = self.temp_dir / f"processed_{uuid.uuid4().hex[:8]}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_paths = []
        
        def process_single_frame(input_path: str) -> Tuple[str, str]:
            """处理单帧"""
            frame = cv2.imread(input_path)
            if frame is None:
                return input_path, None
            
            processed = self.process_frame(frame, regions)
            
            output_path = output_dir / Path(input_path).name
            cv2.imwrite(str(output_path), processed)
            
            return input_path, str(output_path)
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_single_frame, fp): fp for fp in frame_paths}
            
            for future in as_completed(futures):
                input_path, output_path = future.result()
                if output_path:
                    output_paths.append(output_path)
        
        # 按文件名排序
        output_paths.sort()
        return output_paths


class VideoAssembler:
    """视频组装器 - 将处理后的帧合成为视频"""
    
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def assemble_video(self, frame_dir: str, output_path: str, 
                       fps: float = 30, codec: str = "libx264",
                       quality: int = 23) -> str:
        """
        将帧合成为视频
        
        Args:
            frame_dir: 帧目录
            output_path: 输出视频路径
            fps: 输出视频帧率
            codec: 视频编码器
            quality: 视频质量 (0-51, 越小越好)
            
        Returns:
            输出视频路径
        """
        frame_dir = Path(frame_dir)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用ffmpeg合成视频
        cmd = [
            "ffmpeg", "-framerate", str(fps),
            "-i", str(frame_dir / "frame_%06d.png"),
            "-c:v", codec,
            "-crf", str(quality),
            "-pix_fmt", "yuv420p",
            "-y",  # 覆盖输出
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error(f"ffmpeg合成视频失败: {result.stderr}")
                # 备用方案：使用OpenCV
                self._assemble_video_cv2(frame_dir, output_path, fps)
        except Exception as e:
            logger.error(f"ffmpeg合成视频异常: {e}")
            self._assemble_video_cv2(frame_dir, output_path, fps)
        
        return str(output_path)
    
    def _assemble_video_cv2(self, frame_dir: Path, output_path: Path, fps: float):
        """使用OpenCV合成视频（备用方案）"""
        frames = sorted(frame_dir.glob("*.png"))
        
        if not frames:
            raise ValueError(f"帧目录为空: {frame_dir}")
        
        # 读取第一帧获取尺寸
        first_frame = cv2.imread(str(frames[0]))
        if first_frame is None:
            raise ValueError(f"无法读取第一帧: {frames[0]}")
        
        h, w = first_frame.shape[:2]
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
        
        for frame_path in frames:
            frame = cv2.imread(str(frame_path))
            if frame is not None:
                writer.write(frame)
        
        writer.release()
    
    def assemble_with_audio(self, frame_dir: str, audio_path: str, 
                           output_path: str, fps: float = 30) -> str:
        """将帧合成为视频并保留音频"""
        # 先合成视频
        video_no_audio = self.temp_dir / f"video_no_audio_{uuid.uuid4().hex[:8]}.mp4"
        self.assemble_video(frame_dir, str(video_no_audio), fps)
        
        # 合并音频
        cmd = [
            "ffmpeg",
            "-i", str(video_no_audio),
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-y",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error(f"合并音频失败: {result.stderr}")
                # 如果失败，返回无音频版本
                import shutil
                shutil.copy(str(video_no_audio), str(output_path))
        except Exception as e:
            logger.error(f"合并音频异常: {e}")
            import shutil
            shutil.copy(str(video_no_audio), str(output_path))
        
        # 清理临时文件
        try:
            os.remove(str(video_no_audio))
        except:
            pass
        
        return str(output_path)


class WatermarkVideoProcessor:
    """视频去水印主处理类"""
    
    def __init__(self, temp_dir: str = "./temp", output_dir: str = "./output"):
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.extractor = VideoFrameExtractor(str(self.temp_dir))
        self.frame_processor = VideoFrameProcessor(str(self.temp_dir))
        self.assembler = VideoAssembler(str(self.temp_dir))
    
    def process_video(self, video_path: str, regions: List[Dict],
                     preserve_audio: bool = True,
                     output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        处理视频，去除水印/字幕
        
        Args:
            video_path: 输入视频路径
            regions: 要去除的区域列表
            preserve_audio: 是否保留音频
            output_filename: 输出文件名
            
        Returns:
            处理结果信息
        """
        # 生成输出文件名
        if output_filename is None:
            output_filename = f"processed_{uuid.uuid4().hex[:8]}.mp4"
        output_path = self.output_dir / output_filename
        
        # 获取视频信息
        video_info = self.extractor.get_video_info(video_path)
        
        # 创建临时目录
        session_id = uuid.uuid4().hex[:8]
        frame_dir = self.temp_dir / f"frames_{session_id}"
        processed_dir = self.temp_dir / f"processed_{session_id}"
        frame_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. 提取帧
            logger.info("正在提取视频帧...")
            frame_paths = self.extractor.extract_frames(video_path, str(frame_dir), fps=1.0)
            
            if not frame_paths:
                raise ValueError("无法提取视频帧")
            
            # 2. 处理帧
            logger.info(f"正在处理 {len(frame_paths)} 帧...")
            processed_paths = self.frame_processor.process_frames_batch(
                frame_paths, regions, str(processed_dir)
            )
            
            # 重命名处理后的帧以匹配序号
            for i, path in enumerate(processed_paths):
                new_path = processed_dir / f"frame_{i+1:06d}.png"
                os.rename(path, new_path)
            
            processed_paths = [str(processed_dir / f"frame_{i+1:06d}.png") 
                             for i in range(len(processed_paths))]
            
            # 3. 合成视频
            logger.info("正在合成视频...")
            if preserve_audio:
                output_path = self.assembler.assemble_with_audio(
                    str(processed_dir),
                    video_path,
                    str(output_path),
                    fps=video_info['fps']
                )
            else:
                output_path = self.assembler.assemble_video(
                    str(processed_dir),
                    str(output_path),
                    fps=video_info['fps']
                )
            
            return {
                "success": True,
                "output_path": str(output_path),
                "output_url": f"/output/{output_path.name}",
                "frames_processed": len(processed_paths),
                "video_info": video_info,
                "regions_removed": len(regions)
            }
            
        except Exception as e:
            logger.error(f"处理视频失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # 清理临时文件
            self._cleanup_temp(frame_dir)
            self._cleanup_temp(processed_dir)
    
    def detect_and_process(self, video_path: str, detect_type: str = "all",
                          manual_regions: Optional[List[Dict]] = None,
                          preserve_audio: bool = True) -> Dict[str, Any]:
        """
        自动检测并处理视频
        
        Args:
            video_path: 输入视频路径
            detect_type: 检测类型 ("watermark", "subtitle", "all")
            manual_regions: 手动指定的区域
            preserve_audio: 是否保留音频
            
        Returns:
            检测和处理结果
        """
        from watermark_remover import WatermarkDetector, SubtitleDetector
        
        # 创建临时目录
        session_id = uuid.uuid4().hex[:8]
        sample_dir = self.temp_dir / f"sample_{session_id}"
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 提取少量帧进行检测
            frame_paths = self.extractor.extract_frames(video_path, str(sample_dir), fps=0.5)
            
            if not frame_paths:
                raise ValueError("无法提取视频帧")
            
            # 读取一个样本帧
            sample_frame = cv2.imread(frame_paths[0])
            
            if sample_frame is None:
                raise ValueError("无法读取样本帧")
            
            # 检测区域
            detected_regions = []
            
            if detect_type in ["watermark", "all"]:
                detector = WatermarkDetector()
                detected_regions.extend(detector.detect(sample_frame))
            
            if detect_type in ["subtitle", "all"]:
                detector = SubtitleDetector()
                detected_regions.extend(detector.detect(sample_frame))
            
            # 添加手动区域
            if manual_regions:
                detected_regions.extend(manual_regions)
            
            regions_dict = [
                {
                    'x': r.x if hasattr(r, 'x') else r['x'],
                    'y': r.y if hasattr(r, 'y') else r['y'],
                    'width': r.width if hasattr(r, 'width') else r['width'],
                    'height': r.height if hasattr(r, 'height') else r['height'],
                    'type': r.type if hasattr(r, 'type') else r.get('type', 'manual'),
                    'confidence': r.confidence if hasattr(r, 'confidence') else r.get('confidence', 1.0),
                    'label': r.label if hasattr(r, 'label') else r.get('label', '')
                }
                for r in detected_regions
            ]
            
            # 处理视频
            result = self.process_video(video_path, regions_dict, preserve_audio)
            result['detected_regions'] = regions_dict
            
            return result
            
        except Exception as e:
            logger.error(f"检测处理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self._cleanup_temp(sample_dir)
    
    def _cleanup_temp(self, temp_dir: Path):
        """清理临时目录"""
        try:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")


# 全局处理器实例
video_processor = WatermarkVideoProcessor()
