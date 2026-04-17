# 在线剪辑平台后端配置

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
BACKEND_DIR = Path(__file__).parent

# 存储目录
UPLOAD_DIR = BACKEND_DIR / "uploads"
OUTPUT_DIR = BACKEND_DIR / "output"
TEMP_DIR = BACKEND_DIR / "temp"

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ==================== Flask配置 ====================

FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT") or os.environ.get("PORT", 8890))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# 文件上传配置 - 支持大文件
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_SCRIPT_SIZE = 10 * 1024 * 1024  # 10MB

# 允许的文件扩展名
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', 'm4v'}
ALLOWED_SCRIPT_EXTENSIONS = {'txt', 'md', 'json', 'docx', 'pdf'}

# ==================== Celery配置 ====================

# Redis连接
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_URL = os.environ.get("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Celery配置
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600  # 1小时超时
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # 防止任务丢失

# ==================== FFmpeg配置 ====================

FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "ffmpeg")
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", "ffprobe")

# 视频处理配置
VIDEO_OUTPUT_FORMAT = "mp4"
VIDEO_CODEC = "libx264"
VIDEO_CRF = 23  # 质量参数，越低质量越好
VIDEO_PRESET = "medium"  # 编码速度
VIDEO_FPS = 24

# 音频配置
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"
BGM_VOLUME = 0.25  # BGM音量 (0.0-1.0)
VOICE_VOLUME = 1.0  # 原音音量
AUDIO_FADE_IN = 1.0  # 淡入时长(秒)
AUDIO_FADE_OUT = 2.0  # 淡出时长(秒)

# ==================== BGM音乐库配置 ====================

BGM_LIBRARY_PATH = BASE_DIR / "bgm_library.json"
BGM_LOCAL_DIR = BASE_DIR / "bgm_files"

# 情绪标签到BGM标签映射
EMOTION_TO_BGM_TAGS = {
    '悬疑': ['mystery', 'suspense', 'dark', 'thriller', 'tension'],
    '紧张': ['action', 'intense', 'epic', 'battle', 'fight', 'chase'],
    '欢快': ['happy', 'upbeat', 'positive', 'fun', 'cheerful', 'romantic'],
    '悲伤': ['sad', 'melancholy', 'emotional', 'piano', 'heartbreak'],
    '震撼': ['epic', 'dramatic', 'powerful', 'orchestral', 'cinematic'],
    '温馨': ['heartwarming', 'gentle', 'peaceful', 'soft', 'healing'],
    '默认': ['background', 'ambient', 'cinematic']
}

# ==================== 文件清理配置 ====================

# 文件保留时间（秒）- 24小时
FILE_RETENTION_TIME = 24 * 60 * 60

# 自动清理间隔（秒）- 1小时
CLEANUP_INTERVAL = 60 * 60

# ==================== 任务状态配置 ====================

TASK_STATUS = {
    'PENDING': 'pending',      # 等待中
    'PROCESSING': 'processing', # 处理中
    'SUCCESS': 'success',      # 成功
    'FAILURE': 'failure',      # 失败
    'RETRY': 'retry'           # 重试中
}

# 任务阶段
PROCESS_STAGES = {
    'UPLOAD': '上传文件',
    'PARSE_SCRIPT': '解析剧本',
    'ANALYZE': '情绪分析',
    'SEARCH_BGM': '搜索BGM',
    'CONCATENATE': '拼接视频',
    'ADD_AUDIO': '添加音频',
    'EXPORT': '导出成片',
    'COMPLETE': '完成'
}

# ==================== 工具函数 ====================

def allowed_file(filename, allowed_set):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def get_api_status():
    """获取API服务状态"""
    import subprocess
    
    status = {
        'ffmpeg': False,
        'redis': False,
        'celery': False
    }
    
    # 检查FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        status['ffmpeg'] = result.returncode == 0
    except Exception:
        pass
    
    # 检查Redis
    try:
        import redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_connect_timeout=2)
        r.ping()
        status['redis'] = True
    except Exception:
        pass
    
    return status
