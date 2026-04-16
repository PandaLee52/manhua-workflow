"""
在线剪辑平台 - Flask后端API服务
提供视频上传、剪辑处理、进度查询、成品下载的完整API
"""

import os
import json
import time
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

import config
from tasks import app as celery_app, process_video_edit, status_store, search_bgm_by_tags, get_video_info
from ai_requirements import AIRequirementsParser, parse_requirements, parse_to_json, list_preset_templates, PRESET_TEMPLATES

# ==================== Flask应用初始化 ====================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / 'static'

# 静态文件服务路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    """服务静态文件"""
    return send_from_directory(str(STATIC_DIR), filename)

@app.route('/')
def index():
    """首页"""
    return send_from_directory(str(STATIC_DIR), 'index.html')

@app.route('/<path:filename>')
def spa_router(filename):
    """SPA路由 - 支持前端路由"""
    file_path = STATIC_DIR / filename
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(STATIC_DIR), filename)
    return send_from_directory(str(STATIC_DIR), 'index.html')

# 确保目录存在
config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 工具函数 ====================

def api_response(success=True, data=None, message="", error=None, **kwargs):
    """统一API响应格式"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "message": message,
        **kwargs
    }
    if data is not None:
        response["data"] = data
    if error:
        response["error"] = error
    return jsonify(response)


def allowed_video_file(filename):
    """检查是否为允许的视频文件"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_VIDEO_EXTENSIONS


def allowed_script_file(filename):
    """检查是否为允许的剧本文件"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_SCRIPT_EXTENSIONS


def save_upload_file(file, prefix="file"):
    """保存上传的文件"""
    if not file or not file.filename:
        return None
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    filename = f"{prefix}_{timestamp}_{unique_id}.{ext}" if ext else f"{prefix}_{timestamp}_{unique_id}"
    
    filepath = config.UPLOAD_DIR / filename
    file.save(filepath)
    
    return {
        "id": f"{prefix}_{unique_id}",
        "filename": filename,
        "original_name": file.filename,
        "path": str(filepath),
        "size": os.path.getsize(filepath)
    }


# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    api_status = config.get_api_status()
    
    return api_response(
        success=True,
        data={
            "service": "在线剪辑平台",
            "version": "1.0.0",
            "status": "running",
            "api_status": api_status,
            "directories": {
                "upload": str(config.UPLOAD_DIR),
                "output": str(config.OUTPUT_DIR),
                "temp": str(config.TEMP_DIR)
            }
        }
    )


# ==================== 视频上传API ====================

@app.route('/upload/videos', methods=['POST'])
def upload_videos():
    """
    上传多个视频片段
    
    请求方式: multipart/form-data
    参数:
        - videos: 多个视频文件 (field name相同)
        - 或 files[]: 多个视频文件 (数组格式)
    
    返回:
        {
            "success": true,
            "data": {
                "count": 3,
                "videos": [
                    {"id": "video_xxx", "filename": "...", "size": 12345},
                    ...
                ]
            }
        }
    """
    try:
        # 支持两种上传格式
        files = []
        
        # 格式1: 多个同名文件
        if 'videos' in request.files:
            video_files = request.files.getlist('videos')
            files.extend(video_files)
        
        # 格式2: files[] 数组
        if 'files[]' in request.files:
            video_files = request.files.getlist('files[]')
            files.extend(video_files)
        
        # 格式3: 多个单独的file字段
        for key in request.files:
            if key.startswith('file'):
                video_files = request.files.getlist(key)
                files.extend(video_files)
        
        if not files:
            return api_response(success=False, error="未上传任何文件")
        
        # 保存文件
        uploaded_videos = []
        errors = []
        
        for file in files:
            if not file.filename:
                continue
            
            if not allowed_video_file(file.filename):
                errors.append({
                    "filename": file.filename,
                    "error": "不支持的文件格式"
                })
                continue
            
            result = save_upload_file(file, prefix="video")
            if result:
                # 获取视频信息
                video_info = get_video_info(result["path"])
                uploaded_videos.append({
                    **result,
                    "duration": video_info.get('duration', 0) if video_info else 0,
                    "width": video_info.get('width', 0) if video_info else 0,
                    "height": video_info.get('height', 0) if video_info else 0
                })
        
        if not uploaded_videos:
            return api_response(
                success=False, 
                error=f"所有文件上传失败: {errors}"
            )
        
        return api_response(
            success=True,
            data={
                "count": len(uploaded_videos),
                "videos": uploaded_videos,
                "errors": errors if errors else None
            },
            message=f"成功上传 {len(uploaded_videos)} 个视频"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/upload/script', methods=['POST'])
def upload_script():
    """
    上传分镜剧本
    
    请求方式: multipart/form-data 或 JSON
    
    方式1 - 文件上传:
        - script_file: 剧本文件 (txt/md/json/docx/pdf)
    
    方式2 - JSON上传:
        {
            "content": "剧本内容...",
            "name": "剧本名称（可选）"
        }
    
    返回:
        {
            "success": true,
            "data": {
                "id": "script_xxx",
                "filename": "...",
                "content_preview": "前200字符..."
            }
        }
    """
    try:
        script_data = None
        
        # 方式1: 文件上传
        if 'script_file' in request.files:
            file = request.files['script_file']
            if file.filename and allowed_script_file(file.filename):
                result = save_upload_file(file, prefix="script")
                if result:
                    # 读取内容预览
                    with open(result["path"], 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    script_data = {
                        **result,
                        "content_preview": content[:200] + "..." if len(content) > 200 else content,
                        "content_length": len(content)
                    }
            else:
                return api_response(success=False, error="不支持的文件格式")
        
        # 方式2: JSON上传
        elif request.is_json:
            data = request.get_json()
            content = data.get('content', '').strip()
            name = data.get('name', 'script')
            
            if not content:
                return api_response(success=False, error="剧本内容不能为空")
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"script_{timestamp}_{unique_id}.txt"
            filepath = config.UPLOAD_DIR / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            script_data = {
                "id": f"script_{unique_id}",
                "filename": filename,
                "name": name,
                "path": str(filepath),
                "size": len(content),
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "content_length": len(content)
            }
        
        else:
            return api_response(success=False, error="未提供剧本内容")
        
        if not script_data:
            return api_response(success=False, error="剧本上传失败")
        
        return api_response(
            success=True,
            data=script_data,
            message="剧本上传成功"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== 剪辑要求API ====================

@app.route('/upload/requirements', methods=['POST'])
def upload_requirements():
    """
    上传/保存剪辑要求
    
    请求方式: JSON
    
    请求体:
    {
        "requirements_text": "开头要震撼，快节奏...",  // 剪辑要求文本
        "name": "我的剪辑要求（可选）"
    }
    
    返回:
    {
        "success": true,
        "data": {
            "id": "req_xxx",
            "filename": "requirements_xxx.txt",
            "parsed_result": { ... },  // AI解析结果
            "has_custom_requirements": true
        }
    }
    """
    try:
        data = request.get_json()
        
        requirements_text = data.get('requirements_text', '').strip()
        name = data.get('name', 'requirements')
        
        if not requirements_text:
            return api_response(success=False, error="剪辑要求不能为空")
        
        # 解析剪辑要求
        parsed_result = parse_requirements(requirements_text)
        
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"requirements_{timestamp}_{unique_id}.txt"
        filepath = config.UPLOAD_DIR / filename
        
        # 保存原始文本和解析结果
        save_content = {
            "original": requirements_text,
            "parsed": parsed_result.__dict__ if hasattr(parsed_result, '__dict__') else parsed_result,
            "created_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(save_content, ensure_ascii=False, indent=2))
        
        return api_response(
            success=True,
            data={
                "id": f"req_{unique_id}",
                "filename": filename,
                "name": name,
                "path": str(filepath),
                "size": os.path.getsize(filepath),
                "parsed_result": parsed_result.__dict__ if hasattr(parsed_result, '__dict__') else parsed_result,
                "has_custom_requirements": parsed_result.has_custom_requirements if hasattr(parsed_result, 'has_custom_requirements') else True
            },
            message="剪辑要求保存成功"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/parse-requirements', methods=['POST'])
def api_parse_requirements():
    """
    解析剪辑要求（用于前端预览）
    
    请求方式: JSON
    
    请求体:
    {
        "requirements_text": "开头要震撼，快节奏...",
        "total_duration": 60,  // 可选，视频总时长
        "use_llm": false  // 可选，是否使用LLM增强
    }
    
    返回:
    {
        "success": true,
        "data": {
            "raw_text": "...",
            "segments": [...],
            "global_bgm_style": "...",
            "global_transition": "...",
            "has_custom_requirements": true,
            "clipping_params": { ... }  // 可选，详细剪辑参数
        }
    }
    """
    try:
        data = request.get_json()
        
        requirements_text = data.get('requirements_text', '').strip()
        total_duration = data.get('total_duration', 60)
        use_llm = data.get('use_llm', False)
        
        if not requirements_text:
            return api_response(success=False, error="剪辑要求不能为空")
        
        # 解析剪辑要求
        parser = AIRequirementsParser(use_llm=use_llm)
        parsed_result = parser.parse(requirements_text)
        
        # 获取详细剪辑参数
        clipping_params = parser.get_clipping_params(requirements_text, total_duration)
        
        return api_response(
            success=True,
            data={
                "raw_text": parsed_result.raw_text,
                "segments": [
                    {
                        "position": seg.position,
                        "style": seg.style,
                        "mood": seg.mood,
                        "duration_factor": seg.duration_factor,
                        "transition": seg.transition,
                        "bgm_keywords": seg.bgm_keywords,
                        "description": seg.description
                    }
                    for seg in parsed_result.segments
                ],
                "global_bgm_style": parsed_result.global_bgm_style,
                "global_transition": parsed_result.global_transition,
                "has_custom_requirements": parsed_result.has_custom_requirements,
                "use_llm": parsed_result.use_llm,
                "clipping_params": clipping_params
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/requirements/presets', methods=['GET'])
def get_requirements_presets():
    """
    获取剪辑要求预设模板列表
    
    返回:
    {
        "success": true,
        "data": {
            "presets": {
                "震撼开场": "开头要震撼，用快节奏剪辑，配合史诗级BGM",
                ...
            }
        }
    }
    """
    return api_response(
        success=True,
        data={
            "presets": PRESET_TEMPLATES
        }
    )


# ==================== 剪辑处理API ====================

@app.route('/process', methods=['POST'])
def start_process():
    """
    开始剪辑处理
    
    请求方式: JSON
    
    请求体:
    {
        "video_ids": ["video_xxx", "video_yyy", ...],  // 必需，视频ID列表
        "script_id": "script_xxx",  // 可选，剧本ID
        "bgm_id": "bgm_001",  // 可选，BGM ID
        "requirements_text": "开头要震撼，快节奏...",  // 可选，AI剪辑要求
        "requirements_id": "req_xxx",  // 可选，已保存的剪辑要求ID
        "options": {  // 可选，其他选项
            "bgm_volume": 0.25,  // BGM音量
            "voice_volume": 1.0,  // 原音音量
            "fade_out": 2.0,  // 淡出时长
            "use_llm": false  // 是否使用LLM增强解析
        }
    }
    
    返回:
    {
        "success": true,
        "data": {
            "task_id": "task_xxx",
            "status": "pending"
        }
    }
    """
    try:
        data = request.get_json()
        
        # 获取参数
        video_ids = data.get('video_ids', [])
        script_id = data.get('script_id')
        bgm_id = data.get('bgm_id')
        requirements_text = data.get('requirements_text', '')
        requirements_id = data.get('requirements_id')
        options = data.get('options', {})
        
        # 参数验证
        if not video_ids:
            return api_response(success=False, error="未提供视频文件")
        
        # 验证视频文件是否存在
        existing_videos = []
        for vid in video_ids:
            # 查找文件（可能扩展名不同）
            video_files = list(config.UPLOAD_DIR.glob(f"video_*_{vid}.*"))
            for vf in video_files:
                existing_videos.append(str(vf))
                break
        
        if not existing_videos:
            return api_response(success=False, error="未找到视频文件")
        
        # 如果提供了requirements_id，读取保存的剪辑要求
        if requirements_id and not requirements_text:
            req_files = list(config.UPLOAD_DIR.glob(f"*_{requirements_id}.txt"))
            for req_file in req_files:
                try:
                    with open(req_file, 'r', encoding='utf-8') as f:
                        req_data = json.load(f)
                        requirements_text = req_data.get('original', '')
                except Exception:
                    pass
        
        # 生成任务ID
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        # 初始化任务状态
        status_store.set_status(task_id, {
            'task_id': task_id,
            'status': 'PENDING',
            'progress': 0,
            'stage': 'UPLOAD',
            'message': '任务已创建，等待处理...',
            'video_count': len(existing_videos),
            'has_requirements': bool(requirements_text),
            'requirements_preview': requirements_text[:100] if requirements_text else '',
            'created_at': datetime.now().isoformat()
        })
        
        # 提交异步任务（包含requirements参数）
        process_video_edit.apply_async(
            args=[task_id, video_ids, script_id, bgm_id, options, requirements_text],
            task_id=task_id
        )
        
        return api_response(
            success=True,
            data={
                "task_id": task_id,
                "status": "pending",
                "status_url": f"/status/{task_id}",
                "download_url": f"/download/{task_id}",
                "has_requirements": bool(requirements_text)
            },
            message="任务已提交"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    查询处理进度
    
    返回:
    {
        "success": true,
        "data": {
            "task_id": "task_xxx",
            "status": "processing",  // pending/processing/success/failure
            "progress": 0.65,
            "stage": "CONCATENATE",
            "message": "正在拼接视频...",
            "output_url": null  // 处理完成后返回下载链接
        }
    }
    """
    try:
        # 从Redis获取状态
        status = status_store.get_status(task_id)
        
        if not status:
            return api_response(success=False, error="任务不存在或已过期")
        
        return api_response(
            success=True,
            data=status
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/download/<task_id>', methods=['GET'])
def download_result(task_id):
    """
    下载成片
    
    返回: 
        - 成功: 文件流
        - 失败: JSON错误信息
    """
    try:
        # 获取任务状态
        status = status_store.get_status(task_id)
        
        if not status:
            return api_response(success=False, error="任务不存在或已过期")
        
        if status.get('status') != 'SUCCESS':
            return api_response(
                success=False, 
                error=f"任务尚未完成，当前状态: {status.get('status', 'unknown')}"
            )
        
        output_file = status.get('output_file')
        
        if not output_file or not os.path.exists(output_file):
            return api_response(success=False, error="输出文件不存在")
        
        # 返回文件下载
        return send_file(
            output_file,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f"{task_id}_final.mp4"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== BGM搜索API ====================

@app.route('/bgm/search', methods=['POST'])
def search_bgm():
    """
    搜索BGM
    
    请求方式: JSON
    
    请求体:
    {
        "tags": ["epic", "dramatic"],  // 搜索标签
        "emotion": "震撼",  // 或指定情绪
        "limit": 10  // 返回数量限制
    }
    
    返回:
    {
        "success": true,
        "data": {
            "results": [
                {
                    "id": "bgm_001",
                    "name": "Epic Adventure",
                    "artist": "Composer A",
                    "duration": 180,
                    "mood_tags": ["epic", "dramatic"],
                    "category": "震撼",
                    "preview_url": "/bgm/preview/bgm_001"
                },
                ...
            ]
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        # 获取搜索条件
        tags = data.get('tags', [])
        emotion = data.get('emotion')
        limit = data.get('limit', 10)
        
        # 如果指定了情绪，转换为标签
        if emotion and emotion in config.EMOTION_TO_BGM_TAGS:
            tags = tags + config.EMOTION_TO_BGM_TAGS[emotion]
        
        # 搜索BGM
        results = search_bgm_by_tags(tags, limit)
        
        return api_response(
            success=True,
            data={
                "count": len(results),
                "results": results
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/bgm/preview/<bgm_id>', methods=['GET'])
def preview_bgm(bgm_id):
    """
    试听BGM
    
    返回:
        - 成功: 音频文件流
        - 失败: JSON错误信息
    """
    try:
        # 模拟BGM文件（实际项目中应该从BGM库获取）
        # 先检查本地BGM目录
        bgm_path = config.BGM_LOCAL_DIR / f"{bgm_id}.mp3"
        
        if not bgm_path.exists():
            # 返回错误
            return api_response(
                success=False, 
                error=f"BGM文件不存在: {bgm_id}"
            )
        
        return send_file(
            str(bgm_path),
            mimetype='audio/mpeg',
            as_attachment=False
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== 文件管理API ====================

@app.route('/files/list', methods=['GET'])
def list_files():
    """
    列出上传的文件
    
    查询参数:
        - type: 文件类型 (video/script/all, 默认all)
        - limit: 返回数量限制
    """
    try:
        file_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 100))
        
        files = []
        
        for filepath in config.UPLOAD_DIR.glob('*'):
            if filepath.is_file():
                stat = filepath.stat()
                file_info = {
                    "id": filepath.stem,
                    "filename": filepath.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                # 判断文件类型
                ext = filepath.suffix.lower()
                if ext in config.ALLOWED_VIDEO_EXTENSIONS:
                    file_info["type"] = "video"
                elif ext in config.ALLOWED_SCRIPT_EXTENSIONS:
                    file_info["type"] = "script"
                else:
                    file_info["type"] = "other"
                
                # 过滤类型
                if file_type == 'all' or file_info["type"] == file_type:
                    files.append(file_info)
        
        # 按修改时间排序
        files.sort(key=lambda x: x['modified_at'], reverse=True)
        
        return api_response(
            success=True,
            data={
                "count": len(files),
                "files": files[:limit]
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/files/delete', methods=['POST'])
def delete_file():
    """
    删除上传的文件
    
    请求体:
    {
        "filename": "video_xxx.mp4"  // 或
        "id": "video_xxx"
    }
    """
    try:
        data = request.get_json()
        
        filename = data.get('filename')
        file_id = data.get('id')
        
        if not filename and not file_id:
            return api_response(success=False, error="未提供文件名或ID")
        
        # 查找文件
        deleted = False
        for filepath in config.UPLOAD_DIR.glob('*'):
            if filepath.is_file():
                if filename and filepath.name == filename:
                    filepath.unlink()
                    deleted = True
                    break
                elif file_id and file_id in filepath.stem:
                    filepath.unlink()
                    deleted = True
                    break
        
        if deleted:
            return api_response(success=True, message="文件删除成功")
        else:
            return api_response(success=False, error="文件不存在")
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== 统计API ====================

@app.route('/stats', methods=['GET'])
def get_stats():
    """获取平台统计信息"""
    try:
        # 统计文件
        video_count = len(list(config.UPLOAD_DIR.glob('*.mp4'))) + \
                      len(list(config.UPLOAD_DIR.glob('*.avi'))) + \
                      len(list(config.UPLOAD_DIR.glob('*.mov')))
        script_count = len(list(config.UPLOAD_DIR.glob('*.txt')))
        output_count = len(list(config.OUTPUT_DIR.glob('*.mp4')))
        
        # 统计存储
        upload_size = sum(f.stat().st_size for f in config.UPLOAD_DIR.glob('*') if f.is_file())
        output_size = sum(f.stat().st_size for f in config.OUTPUT_DIR.glob('*') if f.is_file())
        
        return api_response(
            success=True,
            data={
                "files": {
                    "videos": video_count,
                    "scripts": script_count,
                    "outputs": output_count,
                    "total": video_count + script_count + output_count
                },
                "storage": {
                    "upload_size_mb": round(upload_size / 1024 / 1024, 2),
                    "output_size_mb": round(output_size / 1024 / 1024, 2),
                    "total_size_mb": round((upload_size + output_size) / 1024 / 1024, 2)
                },
                "config": {
                    "max_upload_size": config.MAX_CONTENT_LENGTH / 1024 / 1024,
                    "retention_time_hours": config.FILE_RETENTION_TIME / 3600
                }
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== 视频去水印/字幕API ====================

import cv2
from watermark_remover import WatermarkDetector, SubtitleDetector, WatermarkProcessor
from video_processor import WatermarkVideoProcessor, VideoFrameExtractor
from batch_processor import BatchProcessor, BatchStatus

# 初始化处理器
watermark_processor = WatermarkVideoProcessor(
    temp_dir=str(config.TEMP_DIR),
    output_dir=str(config.OUTPUT_DIR)
)
batch_proc = BatchProcessor(max_workers=2)


@app.route('/api/detect-watermark', methods=['POST'])
def detect_watermark():
    """
    AI自动检测水印区域
    
    请求方式: multipart/form-data 或 JSON
    
    方式1 - 文件上传:
        - file: 图片或视频文件
        
    方式2 - JSON:
        {
            "video_path": "/path/to/video.mp4"  // 服务器上的视频路径
        }
    
    返回:
    {
        "success": true,
        "data": {
            "regions": [
                {"x": 100, "y": 50, "width": 200, "height": 40, "type": "watermark", "confidence": 0.85, "label": "corner_watermark"},
                ...
            ],
            "frame_info": {"width": 1920, "height": 1080}
        }
    }
    """
    try:
        regions = []
        frame_info = {}
        
        # 方式1: 文件上传
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return api_response(success=False, error="未上传文件")
            
            # 保存临时文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            temp_path = config.TEMP_DIR / f"detect_{timestamp}_{unique_id}.{ext}"
            file.save(str(temp_path))
            
            # 判断是图片还是视频
            if ext in ['jpg', 'jpeg', 'png', 'bmp']:
                # 图片处理
                frame = cv2.imread(str(temp_path))
                if frame is None:
                    return api_response(success=False, error="无法读取图片")
                
                frame_info = {"width": frame.shape[1], "height": frame.shape[0]}
                detector = WatermarkDetector()
                detected = detector.detect(frame)
                regions = [
                    {'x': r.x, 'y': r.y, 'width': r.width, 'height': r.height,
                     'type': r.type, 'confidence': r.confidence, 'label': r.label}
                    for r in detected
                ]
            else:
                # 视频处理 - 提取一帧进行检测
                cap = cv2.VideoCapture(str(temp_path))
                if not cap.isOpened():
                    return api_response(success=False, error="无法打开视频")
                
                frame_info = {
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                }
                
                # 读取中间帧
                frame_no = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ret, frame = cap.read()
                cap.release()
                
                if not ret or frame is None:
                    return api_response(success=False, error="无法读取视频帧")
                
                detector = WatermarkDetector()
                detected = detector.detect(frame)
                regions = [
                    {'x': r.x, 'y': r.y, 'width': r.width, 'height': r.height,
                     'type': r.type, 'confidence': r.confidence, 'label': r.label}
                    for r in detected
                ]
            
            # 清理临时文件
            try:
                temp_path.unlink()
            except:
                pass
        
        # 方式2: JSON指定视频路径
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            
            if not video_path:
                return api_response(success=False, error="未提供视频路径")
            
            if not os.path.exists(video_path):
                return api_response(success=False, error="视频文件不存在")
            
            # 提取帧进行检测
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return api_response(success=False, error="无法打开视频")
            
            frame_info = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS)
            }
            
            # 读取中间帧
            frame_no = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return api_response(success=False, error="无法读取视频帧")
            
            detector = WatermarkDetector()
            detected = detector.detect(frame)
            regions = [
                {'x': r.x, 'y': r.y, 'width': r.width, 'height': r.height,
                 'type': r.type, 'confidence': r.confidence, 'label': r.label}
                for r in detected
            ]
        
        else:
            return api_response(success=False, error="请上传文件或提供视频路径")
        
        return api_response(
            success=True,
            data={
                "regions": regions,
                "region_count": len(regions),
                "frame_info": frame_info
            },
            message=f"检测到 {len(regions)} 个水印区域"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/detect-subtitle', methods=['POST'])
def detect_subtitle():
    """
    检测字幕区域
    
    请求方式: 同 /api/detect-watermark
    
    返回:
    {
        "success": true,
        "data": {
            "regions": [
                {"x": 100, "y": 900, "width": 1720, "height": 80, "type": "subtitle", "confidence": 0.9, "label": "ocr_subtitle"},
                ...
            ],
            "frame_info": {"width": 1920, "height": 1080},
            "has_text": true
        }
    }
    """
    try:
        regions = []
        frame_info = {}
        has_text = False
        
        # 方式1: 文件上传
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return api_response(success=False, error="未上传文件")
            
            # 保存临时文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            temp_path = config.TEMP_DIR / f"detect_{timestamp}_{unique_id}.{ext}"
            file.save(str(temp_path))
            
            if ext in ['jpg', 'jpeg', 'png', 'bmp']:
                frame = cv2.imread(str(temp_path))
                if frame is None:
                    return api_response(success=False, error="无法读取图片")
                
                frame_info = {"width": frame.shape[1], "height": frame.shape[0]}
            else:
                cap = cv2.VideoCapture(str(temp_path))
                if not cap.isOpened():
                    return api_response(success=False, error="无法打开视频")
                
                frame_info = {
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                }
                
                frame_no = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ret, frame = cap.read()
                cap.release()
                
                if not ret or frame is None:
                    return api_response(success=False, error="无法读取视频帧")
            
            try:
                temp_path.unlink()
            except:
                pass
        
        # 方式2: JSON指定视频路径
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            
            if not video_path:
                return api_response(success=False, error="未提供视频路径")
            
            if not os.path.exists(video_path):
                return api_response(success=False, error="视频文件不存在")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return api_response(success=False, error="无法打开视频")
            
            frame_info = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS)
            }
            
            frame_no = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return api_response(success=False, error="无法读取视频帧")
        
        else:
            return api_response(success=False, error="请上传文件或提供视频路径")
        
        # 检测字幕
        detector = SubtitleDetector()
        detected = detector.detect(frame)
        regions = [
            {'x': r.x, 'y': r.y, 'width': r.width, 'height': r.height,
             'type': r.type, 'confidence': r.confidence, 'label': r.label}
            for r in detected
        ]
        has_text = len(regions) > 0
        
        return api_response(
            success=True,
            data={
                "regions": regions,
                "region_count": len(regions),
                "frame_info": frame_info,
                "has_text": has_text
            },
            message=f"检测到 {len(regions)} 个字幕区域" if has_text else "未检测到字幕"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/remove-watermark', methods=['POST'])
def remove_watermark():
    """
    去除视频水印/字幕
    
    请求方式: JSON
    
    请求体:
    {
        "video_path": "/path/to/video.mp4",  // 服务器上的视频路径
        "regions": [  // 要去除的区域
            {"x": 100, "y": 50, "width": 200, "height": 40},
            {"x": 0, "y": 900, "width": 1920, "height": 80}
        ],
        "preserve_audio": true,  // 是否保留音频，默认true
        "auto_detect": false,    // 是否自动检测，默认false
        "detect_type": "all"     // 检测类型: watermark/subtitle/all
    }
    
    返回:
    {
        "success": true,
        "data": {
            "task_id": "watermark_xxx",
            "status": "processing",
            "output_path": "/output/watermark_xxx.mp4",
            "detected_regions": [...]  // 如果auto_detect为true
        }
    }
    """
    try:
        data = request.get_json()
        
        video_path = data.get('video_path')
        regions = data.get('regions', [])
        preserve_audio = data.get('preserve_audio', True)
        auto_detect = data.get('auto_detect', False)
        detect_type = data.get('detect_type', 'all')
        
        if not video_path:
            return api_response(success=False, error="未提供视频路径")
        
        if not os.path.exists(video_path):
            return api_response(success=False, error="视频文件不存在")
        
        # 自动检测区域
        detected_regions = []
        if auto_detect or not regions:
            result = watermark_processor.detect_and_process(
                video_path,
                detect_type=detect_type,
                manual_regions=regions if regions else None,
                preserve_audio=preserve_audio
            )
            
            return api_response(
                success=True,
                data={
                    "task_id": result.get('task_id', f"watermark_{uuid.uuid4().hex[:8]}"),
                    "status": "completed" if result.get('success') else "failed",
                    "output_path": result.get('output_path'),
                    "output_url": result.get('output_url'),
                    "detected_regions": result.get('detected_regions', []),
                    "frames_processed": result.get('frames_processed', 0),
                    "error": result.get('error')
                },
                message="处理完成" if result.get('success') else f"处理失败: {result.get('error')}"
            )
        
        # 手动指定区域处理
        task_id = f"watermark_{uuid.uuid4().hex[:8]}"
        output_filename = f"{task_id}.mp4"
        
        result = watermark_processor.process_video(
            video_path,
            regions,
            preserve_audio=preserve_audio,
            output_filename=output_filename
        )
        
        return api_response(
            success=True,
            data={
                "task_id": task_id,
                "status": "completed" if result.get('success') else "failed",
                "output_path": result.get('output_path'),
                "output_url": result.get('output_url'),
                "frames_processed": result.get('frames_processed', 0),
                "regions_removed": len(regions),
                "error": result.get('error')
            },
            message="处理完成" if result.get('success') else f"处理失败: {result.get('error')}"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/batch-remove', methods=['POST'])
def batch_remove():
    """
    批量去除视频水印/字幕
    
    请求方式: JSON
    
    请求体:
    {
        "videos": [
            {
                "video_path": "/path/to/video1.mp4",
                "regions": [{"x": 100, "y": 50, "width": 200, "height": 40}]
            },
            {
                "video_path": "/path/to/video2.mp4"
            }
        ],
        "default_regions": [{"x": 0, "y": 900, "width": 1920, "height": 80}],  // 默认区域
        "detect_type": "all"  // watermark/subtitle/all
    }
    
    返回:
    {
        "success": true,
        "data": {
            "task_id": "batch_xxx",
            "status": "processing",
            "total_videos": 2,
            "status_url": "/api/batch-status/batch_xxx"
        }
    }
    """
    try:
        data = request.get_json()
        
        videos = data.get('videos', [])
        default_regions = data.get('default_regions', [])
        detect_type = data.get('detect_type', 'all')
        
        if not videos:
            return api_response(success=False, error="未提供视频列表")
        
        # 验证视频
        valid_videos = []
        for v in videos:
            video_path = v.get('video_path')
            if video_path and os.path.exists(video_path):
                valid_videos.append({
                    "video_path": video_path,
                    "regions": v.get('regions', default_regions)
                })
        
        if not valid_videos:
            return api_response(success=False, error="没有有效的视频文件")
        
        # 创建批量任务
        task_id = batch_processor.create_batch_task(valid_videos, default_regions)
        
        # 启动处理
        batch_processor.start_batch(task_id)
        
        return api_response(
            success=True,
            data={
                "task_id": task_id,
                "status": "processing",
                "total_videos": len(valid_videos),
                "status_url": f"/api/batch-status/{task_id}"
            },
            message=f"已创建批量任务，处理 {len(valid_videos)} 个视频"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/batch-status/<task_id>', methods=['GET'])
def batch_status(task_id):
    """
    查询批量处理状态
    
    返回:
    {
        "success": true,
        "data": {
            "task_id": "batch_xxx",
            "status": "processing",  // pending/processing/completed/failed/cancelled
            "progress": 50.0,
            "completed": 1,
            "failed": 0,
            "total": 2,
            "jobs": [...]
        }
    }
    """
    try:
        status = batch_processor.get_task_status(task_id)
        
        if not status:
            return api_response(success=False, error="任务不存在")
        
        return api_response(
            success=True,
            data=status
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/batch-cancel/<task_id>', methods=['POST'])
def batch_cancel(task_id):
    """取消批量任务"""
    try:
        success = batch_processor.cancel_task(task_id)
        
        if success:
            return api_response(success=True, message="任务已取消")
        else:
            return api_response(success=False, error="无法取消任务")
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/batch-list', methods=['GET'])
def batch_list():
    """
    列出所有批量任务
    
    查询参数:
        - status: 过滤状态 (pending/processing/completed/failed/cancelled)
    """
    try:
        status_filter = request.args.get('status')
        
        status_map = {
            'pending': BatchStatus.PENDING,
            'processing': BatchStatus.PROCESSING,
            'completed': BatchStatus.COMPLETED,
            'failed': BatchStatus.FAILED,
            'cancelled': BatchStatus.CANCELLED
        }
        
        status = status_map.get(status_filter) if status_filter else None
        tasks = batch_processor.list_tasks(status)
        
        return api_response(
            success=True,
            data={
                "count": len(tasks),
                "tasks": tasks
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/api/detect-all', methods=['POST'])
def detect_all():
    """
    同时检测水印和字幕区域
    
    请求方式: 同 /api/detect-watermark
    
    返回:
    {
        "success": true,
        "data": {
            "watermarks": [...],
            "subtitles": [...],
            "all_regions": [...],
            "frame_info": {...}
        }
    }
    """
    try:
        frame = None
        frame_info = {}
        
        # 复用detect_watermark的逻辑获取帧
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return api_response(success=False, error="未上传文件")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            temp_path = config.TEMP_DIR / f"detect_{timestamp}_{unique_id}.{ext}"
            file.save(str(temp_path))
            
            if ext in ['jpg', 'jpeg', 'png', 'bmp']:
                frame = cv2.imread(str(temp_path))
                if frame is not None:
                    frame_info = {"width": frame.shape[1], "height": frame.shape[0]}
            else:
                cap = cv2.VideoCapture(str(temp_path))
                if cap.isOpened():
                    frame_info = {
                        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    }
                    frame_no = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                    ret, frame = cap.read()
                    cap.release()
            
            try:
                temp_path.unlink()
            except:
                pass
        
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            
            if not video_path:
                return api_response(success=False, error="未提供视频路径")
            
            if not os.path.exists(video_path):
                return api_response(success=False, error="视频文件不存在")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return api_response(success=False, error="无法打开视频")
            
            frame_info = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS)
            }
            
            frame_no = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            cap.release()
        
        else:
            return api_response(success=False, error="请上传文件或提供视频路径")
        
        if frame is None:
            return api_response(success=False, error="无法读取视频帧")
        
        # 同时检测水印和字幕
        processor = WatermarkProcessor()
        result = processor.detect_all(frame)
        
        return api_response(
            success=True,
            data={
                "watermarks": result['watermarks'],
                "subtitles": result['subtitles'],
                "all_regions": result['all_regions'],
                "frame_info": frame_info,
                "total_regions": len(result['all_regions'])
            },
            message=f"检测到 {len(result['watermarks'])} 个水印, {len(result['subtitles'])} 个字幕"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== 错误处理 ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    """文件过大错误"""
    return api_response(
        success=False,
        error=f"文件过大，最大支持 {config.MAX_CONTENT_LENGTH / 1024 / 1024}MB"
    ), 413


@app.errorhandler(404)
def not_found(error):
    """404错误"""
    return api_response(success=False, error="接口不存在"), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误"""
    return api_response(success=False, error="服务器内部错误"), 500


# ==================== 主程序 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("在线剪辑平台 - 后端API服务")
    print("=" * 50)
    print(f"服务地址: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"上传目录: {config.UPLOAD_DIR}")
    print(f"输出目录: {config.OUTPUT_DIR}")
    print("=" * 50)
    print("API端点:")
    print("  POST /upload/videos   - 上传视频文件")
    print("  POST /upload/script   - 上传剧本")
    print("  POST /process         - 开始剪辑处理")
    print("  GET  /status/<task_id> - 查询进度")
    print("  GET  /download/<task_id> - 下载成片")
    print("  POST /bgm/search      - 搜索BGM")
    print("  GET  /bgm/preview/<id> - 试听BGM")
    print("=" * 50)
    
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
