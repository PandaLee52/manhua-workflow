# 批量视频处理模块
# 支持多视频批量去水印/字幕

import uuid
import time
import threading
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class BatchStatus(Enum):
    """批处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchJob:
    """批处理任务"""
    job_id: str
    video_path: str
    output_path: str
    regions: List[Dict]
    status: BatchStatus = BatchStatus.PENDING
    progress: float = 0.0
    created_at: str = ""
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class BatchTask:
    """批量处理任务"""
    task_id: str
    jobs: List[BatchJob] = field(default_factory=list)
    status: BatchStatus = BatchStatus.PENDING
    progress: float = 0.0
    completed: int = 0
    failed: int = 0
    created_at: str = ""
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.tasks: Dict[str, BatchTask] = {}
        self.lock = threading.Lock()
        
    def create_batch_task(self, videos: List[Dict[str, Any]], 
                         regions: Optional[List[Dict]] = None) -> str:
        """
        创建批量处理任务
        
        Args:
            videos: 视频列表 [{"video_path": "...", "regions": [...]}]
            regions: 默认区域列表
            
        Returns:
            任务ID
        """
        task_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        jobs = []
        for i, video_info in enumerate(videos):
            job_id = f"{task_id}_job_{i}"
            video_path = video_info.get("video_path")
            
            if not video_path:
                continue
            
            # 优先级：视频特定区域 > 默认区域
            job_regions = video_info.get("regions", regions or [])
            
            output_filename = f"batch_{task_id}_{i}.mp4"
            
            jobs.append(BatchJob(
                job_id=job_id,
                video_path=video_path,
                output_path=output_filename,
                regions=job_regions
            ))
        
        with self.lock:
            self.tasks[task_id] = BatchTask(
                task_id=task_id,
                jobs=jobs
            )
        
        return task_id
    
    def start_batch(self, task_id: str, 
                   progress_callback: Optional[Callable] = None) -> bool:
        """
        启动批量处理
        
        Args:
            task_id: 任务ID
            progress_callback: 进度回调函数
            
        Returns:
            是否成功启动
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            if task.status != BatchStatus.PENDING:
                return False
            
            task.status = BatchStatus.PROCESSING
        
        # 在后台线程启动处理
        thread = threading.Thread(target=self._process_batch, args=(task_id, progress_callback))
        thread.daemon = True
        thread.start()
        
        return True
    
    def _process_batch(self, task_id: str, 
                       progress_callback: Optional[Callable] = None):
        """后台处理批量任务"""
        from video_processor import WatermarkVideoProcessor
        
        processor = WatermarkVideoProcessor()
        
        with self.lock:
            task = self.tasks[task_id]
            jobs = task.jobs.copy()
        
        total_jobs = len(jobs)
        completed = 0
        failed = 0
        
        def process_job(job: BatchJob) -> BatchJob:
            """处理单个任务"""
            try:
                from video_processor import WatermarkVideoProcessor
                proc = WatermarkVideoProcessor()
                
                result = proc.process_video(
                    job.video_path,
                    job.regions,
                    output_filename=job.output_path
                )
                
                job.status = BatchStatus.COMPLETED
                job.progress = 100.0
                job.result = result
                job.completed_at = datetime.now().isoformat()
                
            except Exception as e:
                job.status = BatchStatus.FAILED
                job.error = str(e)
                logger.error(f"处理任务 {job.job_id} 失败: {e}")
            
            return job
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(process_job, job): job for job in jobs}
            
            for future in as_completed(futures):
                job = future.result()
                completed += 1
                
                if job.status == BatchStatus.FAILED:
                    failed += 1
                
                # 更新任务进度
                with self.lock:
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        task.completed = completed
                        task.failed = failed
                        task.progress = (completed / total_jobs) * 100
                
                # 调用进度回调
                if progress_callback:
                    try:
                        progress_callback(task_id, task.progress, completed, total_jobs)
                    except:
                        pass
        
        # 标记任务完成
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = BatchStatus.COMPLETED if failed < total_jobs else BatchStatus.FAILED
                task.completed_at = datetime.now().isoformat()
                task.progress = 100.0
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self.lock:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": task.progress,
                "completed": task.completed,
                "failed": task.failed,
                "total": len(task.jobs),
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "jobs": [
                    {
                        "job_id": job.job_id,
                        "video_path": job.video_path,
                        "output_path": job.output_path,
                        "status": job.status.value,
                        "progress": job.progress,
                        "error": job.error,
                        "result": job.result
                    }
                    for job in task.jobs
                ]
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            if task.status == BatchStatus.PROCESSING:
                task.status = BatchStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                return True
            
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
            return False
    
    def list_tasks(self, status: Optional[BatchStatus] = None) -> List[Dict[str, Any]]:
        """列出所有任务"""
        with self.lock:
            tasks_list = list(self.tasks.values())
        
        if status:
            tasks_list = [t for t in tasks_list if t.status == status]
        
        return [
            {
                "task_id": t.task_id,
                "status": t.status.value,
                "progress": t.progress,
                "total": len(t.jobs),
                "created_at": t.created_at
            }
            for t in tasks_list
        ]


# 全局批量处理器
batch_processor = BatchProcessor(max_workers=2)
