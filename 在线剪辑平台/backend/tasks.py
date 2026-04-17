"""
在线剪辑平台 - Celery异步任务模块
处理视频剪辑的长时间任务
"""

import os
import re
import json
import time
import uuid
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from celery import Celery
from celery.signals import task_prerun, task_postrun, worker_ready

# 导入配置
try:
    from backend import config
except ImportError:
    import config

# 导入AI剪辑要求解析模块
try:
    from backend.ai_requirements import AIRequirementsParser, parse_requirements
except ImportError:
    from ai_requirements import AIRequirementsParser, parse_requirements

# ==================== Celery应用初始化 ====================

app = Celery(
    'video_edit_tasks',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=['tasks']
)

# Celery配置
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=config.CELERY_TASK_TIME_LIMIT,
    worker_prefetch_multiplier=config.CELERY_WORKER_PREFETCH_MULTIPLIER,
    result_expires=3600,  # 结果保留1小时
)


# ==================== 任务状态存储 ====================

class TaskStatusStore:
    """任务状态存储器（使用Redis）"""
    
    def __init__(self):
        self.redis_client = None
        self._connect_redis()
    
    def _connect_redis(self):
        """连接Redis"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            print(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def set_status(self, task_id: str, status_data: Dict):
        """保存任务状态"""
        if self.redis_client:
            try:
                key = f"task:{task_id}"
                self.redis_client.setex(
                    key,
                    config.FILE_RETENTION_TIME,
                    json.dumps(status_data, ensure_ascii=False)
                )
            except Exception as e:
                print(f"保存任务状态失败: {e}")
    
    def get_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        if self.redis_client:
            try:
                key = f"task:{task_id}"
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                print(f"获取任务状态失败: {e}")
        return None
    
    def update_progress(self, task_id: str, progress: float, stage: str, message: str = ""):
        """更新任务进度"""
        status = self.get_status(task_id) or {}
        status.update({
            'progress': progress,
            'stage': stage,
            'message': message,
            'updated_at': datetime.now().isoformat()
        })
        self.set_status(task_id, status)


# 全局状态存储实例
status_store = TaskStatusStore()


# ==================== FFmpeg工具函数 ====================

def check_ffmpeg():
    """检查FFmpeg是否可用"""
    try:
        subprocess.run([config.FFMPEG_PATH, '-version'], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def get_video_info(video_path: str) -> Optional[Dict]:
    """获取视频信息"""
    if not os.path.exists(video_path):
        return None
    
    try:
        cmd = [
            config.FFPROBE_PATH, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            video_stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
            
            return {
                'duration': float(info.get('format', {}).get('duration', 0)),
                'width': int(video_stream.get('width', 0)) if video_stream else 0,
                'height': int(video_stream.get('height', 0)) if video_stream else 0,
                'fps': eval(video_stream.get('r_frame_rate', '24')) if video_stream else 24,
                'codec': video_stream.get('codec_name', 'unknown') if video_stream else 'unknown',
                'size': int(info.get('format', {}).get('size', 0))
            }
    except Exception as e:
        print(f"获取视频信息失败: {e}")
    
    return None


def concatenate_videos(video_paths: List[str], output_path: str, 
                       progress_callback=None) -> bool:
    """拼接多个视频"""
    if not video_paths:
        return False
    
    if progress_callback:
        progress_callback(0.1, "准备拼接视频...")
    
    try:
        # 创建临时文件列表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            for path in video_paths:
                safe_path = path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
            list_file = f.name
        
        if progress_callback:
            progress_callback(0.3, "正在拼接视频...")
        
        # FFmpeg拼接
        cmd = [
            config.FFMPEG_PATH, '-y', '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',  # 直接复制流，不重新编码
            '-an',  # 无音频
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # 清理临时文件
        try:
            os.unlink(list_file)
        except Exception:
            pass
        
        if result.returncode == 0 and os.path.exists(output_path):
            if progress_callback:
                progress_callback(0.5, "视频拼接完成")
            return True
        
        print(f"FFmpeg拼接失败: {result.stderr}")
        return False
        
    except Exception as e:
        print(f"视频拼接异常: {e}")
        return False


def add_bgm_to_video(video_path: str, bgm_path: str, output_path: str,
                     bgm_volume: float = 0.25, fade_out: float = 2.0,
                     progress_callback=None) -> bool:
    """为视频添加BGM"""
    if not os.path.exists(video_path) or not os.path.exists(bgm_path):
        return False
    
    if progress_callback:
        progress_callback(0.6, "正在添加BGM...")
    
    try:
        # 获取视频和BGM时长
        video_info = get_video_info(video_path)
        video_duration = video_info.get('duration', 60) if video_info else 60
        
        # 构建FFmpeg命令
        cmd = [
            config.FFMPEG_PATH, '-y',
            '-i', video_path,
            '-i', bgm_path,
            '-filter_complex',
            f'[1:a]volume={bgm_volume},afade=t=out:st={video_duration - fade_out}:d={fade_out}[bgm];'
            f'[0:a]volume={config.VOICE_VOLUME}[voice];'
            f'[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]',
            '-map', '0:v',
            '-map', '[aout]',
            '-c:v', 'copy',
            '-c:a', config.AUDIO_CODEC,
            '-b:a', config.AUDIO_BITRATE,
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0 and os.path.exists(output_path):
            if progress_callback:
                progress_callback(0.9, "BGM添加完成")
            return True
        
        print(f"添加BGM失败: {result.stderr}")
        return False
        
    except Exception as e:
        print(f"添加BGM异常: {e}")
        return False


# ==================== 情绪分析 ====================

def analyze_script_emotion(script_text: str) -> Dict:
    """分析剧本情绪"""
    EMOTION_KEYWORDS = {
        '悬疑': ['神秘', '谜团', '线索', '真相', '隐藏', '秘密', '阴谋', '推理',
                 '嫌疑', '凶手', '破案', '追查', '疑点', '诡异', '离奇'],
        '紧张': ['战斗', '激烈', '危机', '逃亡', '追逐', '爆炸', '枪战', '打斗',
                 '生死', '威胁', '紧急', '危难', '搏斗', '对峙', '决战'],
        '欢快': ['快乐', '开心', '幸福', '喜悦', '欢乐', '愉快', '甜蜜', '美好',
                 '约会', '派对', '庆祝', '搞笑', '幽默', '撒娇'],
        '悲伤': ['眼泪', '哭泣', '痛苦', '悲伤', '难过', '伤心', '绝望', '失落',
                 '孤独', '离别', '分手', '失去', '心痛', '哀伤'],
        '震撼': ['震惊', '震撼', '惊人', '史诗', '宏大', '壮观', '磅礴', '逆转',
                 '反转', '逆袭', '爆发', '巅峰', '传奇', '王者'],
        '温馨': ['温暖', '温馨', '感动', '治愈', '关怀', '亲情', '友情', '爱情',
                 '家庭', '陪伴', '守护', '信任', '理解', '包容']
    }
    
    emotion_counts = {emotion: 0 for emotion in EMOTION_KEYWORDS.keys()}
    
    lines = script_text.split('\n')
    for line in lines:
        line_lower = line.lower()
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in line_lower:
                    emotion_counts[emotion] += 1
    
    # 计算得分
    scores = {}
    for emotion, count in emotion_counts.items():
        scores[emotion] = count * 10 + count * count * 2
    
    primary_emotion = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else '默认'
    total = sum(emotion_counts.values()) or 1
    distribution = {e: round(c / total * 100, 1) for e, c in emotion_counts.items()}
    
    return {
        'primary_emotion': primary_emotion,
        'emotion_scores': scores,
        'emotion_distribution': distribution,
        'bgm_tags': config.EMOTION_TO_BGM_TAGS.get(primary_emotion, config.EMOTION_TO_BGM_TAGS['默认'])
    }


# ==================== BGM搜索 ====================

def search_bgm_by_tags(tags: List[str], limit: int = 10) -> List[Dict]:
    """根据标签搜索BGM"""
    # 模拟BGM搜索结果
    # 实际项目中应该连接真实的BGM库
    results = []
    
    sample_bgm = [
        {"id": "bgm_001", "name": "Epic Adventure", "artist": "Composer A", 
         "duration": 180, "mood_tags": ["epic", "dramatic", "cinematic"], "category": "震撼"},
        {"id": "bgm_002", "name": "Mystery Night", "artist": "Composer B",
         "duration": 150, "mood_tags": ["mystery", "suspense", "dark"], "category": "悬疑"},
        {"id": "bgm_003", "name": "Happy Day", "artist": "Composer C",
         "duration": 120, "mood_tags": ["happy", "upbeat", "positive"], "category": "欢快"},
        {"id": "bgm_004", "name": "Tender Moment", "artist": "Composer D",
         "duration": 200, "mood_tags": ["heartwarming", "gentle", "soft"], "category": "温馨"},
        {"id": "bgm_005", "name": "Action Rush", "artist": "Composer E",
         "duration": 140, "mood_tags": ["action", "intense", "battle"], "category": "紧张"},
    ]
    
    for track in sample_bgm:
        score = 0
        for tag in tags:
            tag_lower = tag.lower()
            for track_tag in track['mood_tags']:
                if tag_lower in track_tag or track_tag in tag_lower:
                    score += 1
        
        if score > 0 or not tags:
            results.append({
                **track,
                'match_score': score,
                'preview_url': f"/bgm/preview/{track['id']}"
            })
    
    # 按匹配度排序
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return results[:limit]


# ==================== Celery异步任务 ====================

@app.task(bind=True, name='tasks.process_video_edit')
def process_video_edit(self, task_id: str, video_ids: List[str], 
                       script_id: str = None, bgm_id: str = None,
                       options: Dict = None, requirements_text: str = ""):
    """
    处理视频剪辑任务
    
    Args:
        task_id: 任务ID
        video_ids: 视频文件ID列表
        script_id: 剧本ID（可选）
        bgm_id: BGM ID（可选）
        options: 其他选项
        requirements_text: AI剪辑要求文本（可选）
    """
    options = options or {}
    requirements_parsed = None  # AI解析后的剪辑要求
    
    # 初始化任务状态
    status_store.update_progress(task_id, 0, 'PROCESSING', '开始处理...')
    
    try:
        # 阶段0: 解析AI剪辑要求（如果提供）
        if requirements_text:
            use_llm = options.get('use_llm', False)
            parser = AIRequirementsParser(use_llm=use_llm)
            requirements_parsed = parser.parse(requirements_text)
            
            status_store.update_progress(task_id, 0.05, 'PARSE_REQUIREMENTS', 
                f"AI解析剪辑要求: {requirements_parsed.global_bgm_style}风格, "
                f"{len(requirements_parsed.segments)}个段落")
        
        # 阶段1: 获取视频文件
        status_store.update_progress(task_id, 0.1, 'UPLOAD', '准备视频文件...')
        video_paths = []
        for vid in video_ids:
            video_path = config.UPLOAD_DIR / f"video_{vid}.mp4"
            if video_path.exists():
                video_paths.append(str(video_path))
        
        if not video_paths:
            raise Exception("未找到视频文件")
        
        # 阶段2: 解析剧本（如果提供）
        script_text = ""
        emotion_result = {'primary_emotion': '默认', 'bgm_tags': ['background']}
        
        if script_id:
            status_store.update_progress(task_id, 0.2, 'PARSE_SCRIPT', '解析剧本...')
            script_path = config.UPLOAD_DIR / f"script_{script_id}.txt"
            if script_path.exists():
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_text = f.read()
                
                # 分析情绪
                emotion_result = analyze_script_emotion(script_text)
                status_store.update_progress(task_id, 0.3, 'ANALYZE', 
                    f"情绪分析完成: {emotion_result['primary_emotion']}")
        
        # 阶段3: 应用AI剪辑要求（如果有）
        if requirements_parsed and requirements_parsed.has_custom_requirements:
            status_store.update_progress(task_id, 0.35, 'APPLY_REQUIREMENTS', 
                f"应用AI剪辑要求: {len(requirements_parsed.segments)}个段落设置")
            
            # 根据AI解析结果调整处理参数
            # 例如：调整镜头时长、应用特定转场等
            # 这部分需要根据实际的FFmpeg命令来调整
        
        # 阶段4: 拼接视频
        status_store.update_progress(task_id, 0.4, 'CONCATENATE', '正在拼接视频...')
        
        output_filename = f"{task_id}_concat.mp4"
        concat_output = config.TEMP_DIR / output_filename
        
        def concat_progress(progress, message):
            status_store.update_progress(task_id, 0.4 + progress * 0.2, 'CONCATENATE', message)
        
        concat_success = concatenate_videos(
            video_paths, 
            str(concat_output),
            progress_callback=concat_progress
        )
        
        if not concat_success:
            raise Exception("视频拼接失败")
        
        # 阶段5: 添加BGM
        final_output = config.OUTPUT_DIR / f"{task_id}_final.mp4"
        
        # 确定BGM风格：优先使用AI解析的BGM风格，其次使用情绪分析结果
        bgm_style = None
        if requirements_parsed:
            bgm_style = requirements_parsed.global_bgm_style
        elif emotion_result.get('bgm_tags'):
            bgm_style = emotion_result['bgm_tags'][0]
        
        if bgm_id:
            status_store.update_progress(task_id, 0.7, 'ADD_AUDIO', '添加BGM...')
            
            # 模拟BGM文件路径（实际项目中应该从BGM库获取）
            bgm_path = config.BGM_LOCAL_DIR / f"{bgm_id}.mp3"
            
            if bgm_path.exists():
                def audio_progress(progress, message):
                    status_store.update_progress(task_id, 0.7 + progress * 0.2, 'ADD_AUDIO', message)
                
                add_bgm_success = add_bgm_to_video(
                    str(concat_output),
                    str(bgm_path),
                    str(final_output),
                    bgm_volume=options.get('bgm_volume', config.BGM_VOLUME),
                    progress_callback=audio_progress
                )
                
                if not add_bgm_success:
                    # BGM添加失败，复制无BGM版本
                    shutil.copy(str(concat_output), str(final_output))
            else:
                # BGM文件不存在，使用无BGM版本
                shutil.copy(str(concat_output), str(final_output))
        else:
            shutil.copy(str(concat_output), str(final_output))
        
        # 阶段5: 完成
        status_store.update_progress(task_id, 1.0, 'COMPLETE', '处理完成')
        
        # 构建AI解析结果摘要
        ai_result_summary = None
        if requirements_parsed:
            ai_result_summary = {
                "has_custom_requirements": requirements_parsed.has_custom_requirements,
                "segment_count": len(requirements_parsed.segments),
                "global_bgm_style": requirements_parsed.global_bgm_style,
                "global_transition": requirements_parsed.global_transition,
                "segments": [
                    {
                        "position": seg.position,
                        "mood": seg.mood,
                        "style": seg.style,
                        "duration_factor": seg.duration_factor
                    }
                    for seg in requirements_parsed.segments
                ]
            }
        
        # 更新最终状态
        status_store.set_status(task_id, {
            'task_id': task_id,
            'status': 'SUCCESS',
            'progress': 1.0,
            'stage': 'COMPLETE',
            'message': '处理完成',
            'output_file': str(final_output),
            'output_url': f"/download/{task_id}",
            'emotion_result': emotion_result,
            'ai_requirements': ai_result_summary,
            'created_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat()
        })
        
        # 清理临时文件
        try:
            if concat_output.exists():
                concat_output.unlink()
        except Exception:
            pass
        
        return {
            'success': True,
            'task_id': task_id,
            'output_file': str(final_output),
            'output_url': f"/download/{task_id}"
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"任务处理失败: {error_msg}")
        
        status_store.set_status(task_id, {
            'task_id': task_id,
            'status': 'FAILURE',
            'progress': 0,
            'stage': 'ERROR',
            'message': f"处理失败: {error_msg}",
            'error': error_msg,
            'created_at': datetime.now().isoformat(),
            'failed_at': datetime.now().isoformat()
        })
        
        return {
            'success': False,
            'task_id': task_id,
            'error': error_msg
        }


@app.task(name='tasks.cleanup_old_files')
def cleanup_old_files():
    """清理过期文件"""
    current_time = time.time()
    
    for directory in [config.UPLOAD_DIR, config.TEMP_DIR]:
        if directory.exists():
            for file_path in directory.glob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > config.FILE_RETENTION_TIME:
                        try:
                            file_path.unlink()
                            print(f"已删除过期文件: {file_path}")
                        except Exception as e:
                            print(f"删除文件失败: {file_path}, {e}")


# ==================== 定时任务 ====================

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置定时任务"""
    # 每小时清理一次过期文件
    sender.add_periodic_task(
        config.CLEANUP_INTERVAL,
        cleanup_old_files.s(),
        name='cleanup-old-files'
    )
