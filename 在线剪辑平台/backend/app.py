"""
在线剪辑平台 - Flask后端API服务
提供视频上传、剪辑处理、进度查询、成品下载的完整API
"""

import os
import io
import re
import uuid
import json
import time
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from typing import List, Dict, Any

import config
from tasks import app as celery_app, process_video_edit, status_store, search_bgm_by_tags, get_video_info
from ai_requirements import AIRequirementsParser, parse_requirements, parse_to_json, list_preset_templates, PRESET_TEMPLATES
from ai_features import (
    generate_srt_from_audio, simulate_subtitles, get_video_duration,
    generate_clipping_suggestions, enhanced_parse_instructions,
    detect_character_consistency, convert_to_srt_no_punct, remove_punctuation, format_srt_time
)

# ==================== Flask应用初始化 ====================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
CORS(app, resources={r"/api/*": {"origins": "*"}})

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


# ==================== AI字幕生成API ====================

@app.route('/generate-subtitles', methods=['POST'])
def generate_subtitles():
    """
    字幕生成接口
    接收视频文件，使用语音识别生成SRT格式字幕
    
    请求方式: multipart/form-data 或 JSON
    
    方式1 - 文件上传:
        - video: 视频文件
    
    方式2 - JSON:
        {
            "video_path": "/path/to/video.mp4",
            "use_whisper": true  // 可选，是否使用Whisper
        }
    
    返回:
    {
        "success": true,
        "data": {
            "srt_content": "...",  // SRT格式字幕（无标点）
            "segments": [...],
            "language": "zh",
            "duration": 120.5,
            "simulated": false
        }
    }
    """
    try:
        video_path = None
        use_whisper = True
        
        # 方式1: 文件上传
        if 'video' in request.files:
            file = request.files['video']
            if file.filename and allowed_video_file(file.filename):
                result = save_upload_file(file, prefix="subtitle_video")
                if result:
                    video_path = result["path"]
                    use_whisper = request.form.get('use_whisper', 'true').lower() != 'false'
        
        # 方式2: JSON
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            use_whisper = data.get('use_whisper', True)
        
        if not video_path:
            return api_response(success=False, error="未提供视频文件")
        
        if not os.path.exists(video_path):
            return api_response(success=False, error="视频文件不存在")
        
        # 生成字幕
        result = generate_srt_from_audio(video_path, use_whisper=use_whisper)
        
        if result.get("success"):
            return api_response(
                success=True,
                data={
                    "srt_content": result["srt_content"],
                    "segments": result.get("segments", []),
                    "language": result.get("language", "zh"),
                    "duration": result.get("duration", 0),
                    "simulated": result.get("simulated", False),
                    "subtitle_count": len(result.get("segments", []))
                },
                message="字幕生成成功"
            )
        else:
            return api_response(
                success=False,
                error=result.get("error", "字幕生成失败")
            )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/subtitles/srt', methods=['POST'])
def get_srt_content():
    """
    获取SRT格式字幕内容（用于预览）
    
    请求体:
    {
        "segments": [
            {"start": 0.0, "end": 3.0, "text": "你好"},
            ...
        ],
        "no_punctuation": true  // 是否去除标点
    }
    """
    try:
        data = request.get_json()
        segments = data.get('segments', [])
        no_punctuation = data.get('no_punctuation', True)
        
        if not segments:
            return api_response(success=False, error="未提供字幕片段")
        
        srt_lines = []
        for i, seg in enumerate(segments, 1):
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            text = seg.get('text', '')
            
            if no_punctuation:
                text = remove_punctuation(text)
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
            srt_lines.append(text)
            srt_lines.append("")
        
        srt_content = "\n".join(srt_lines)
        
        return api_response(
            success=True,
            data={
                "srt_content": srt_content,
                "segment_count": len(segments)
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== AI剪辑建议API ====================

@app.route('/suggest', methods=['POST'])
def ai_clipping_suggest():
    """
    AI剪辑建议接口
    根据视频内容描述生成剪辑建议
    
    请求体:
    {
        "content_description": "视频内容描述...",
        "episode_count": 1,        // 当前集数
        "is_first_episode": true,  // 是否是首集
        "total_duration": 90      // 视频总时长（秒）
    }
    
    返回:
    {
        "success": true,
        "data": {
            "duration": {
                "min": 60,
                "recommended": 120,
                "is_first_episode": true
            },
            "speed": {
                "base_rate": 1.25,
                "range": [1.2, 1.3]
            },
            "bgm": {
                "min_changes": 2,
                "suggested_positions": [...]
            },
            "segments": [...],
            "rhythm": {...},
            "transitions": [...],
            "emotions": [...]
        },
        "warnings": [...]
    }
    """
    try:
        data = request.get_json()
        
        content_description = data.get('content_description', '').strip()
        episode_count = data.get('episode_count', 1)
        is_first_episode = data.get('is_first_episode', False)
        total_duration = data.get('total_duration', 0)
        
        if not content_description:
            return api_response(success=False, error="内容描述不能为空")
        
        # 生成剪辑建议
        result = generate_clipping_suggestions(
            content_description=content_description,
            episode_count=episode_count,
            is_first_episode=is_first_episode,
            total_duration=total_duration
        )
        
        return api_response(
            success=True,
            data=result.get("suggestions", {}),
            warnings=result.get("warnings", []),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/suggest/validate', methods=['POST'])
def validate_clipping_params():
    """
    验证剪辑参数是否符合要求
    
    请求体:
    {
        "duration": 90,
        "episode_count": 1,
        "is_first_episode": false,
        "bgm_changes": 3,
        "speech_rate": 1.25
    }
    """
    try:
        data = request.get_json()
        
        duration = data.get('duration', 0)
        episode_count = data.get('episode_count', 1)
        is_first_episode = data.get('is_first_episode', False)
        bgm_changes = data.get('bgm_changes', 0)
        speech_rate = data.get('speech_rate', 1.0)
        
        warnings = []
        passed = True
        
        # 验证时长
        min_duration = 120 if is_first_episode else 60
        if duration < min_duration:
            warnings.append(f"⚠️ 时长不足：首集需≥{min_duration}秒，当前{duration}秒")
            passed = False
        else:
            warnings.append(f"✅ 时长合格：{duration}秒")
        
        # 验证BGM变换
        if bgm_changes < 2:
            warnings.append(f"⚠️ BGM变换不足：每集需≥2次，当前{bgm_changes}次")
            passed = False
        else:
            warnings.append(f"✅ BGM变换合格：{bgm_changes}次")
        
        # 验证语速
        if 1.2 <= speech_rate <= 1.3:
            warnings.append(f"✅ 语速合格：{speech_rate}倍")
        else:
            warnings.append(f"⚠️ 语速建议：控制在1.2-1.3倍，当前{speech_rate}倍")
        
        return api_response(
            success=True,
            data={
                "passed": passed,
                "checks": {
                    "duration": duration >= min_duration,
                    "bgm_changes": bgm_changes >= 2,
                    "speech_rate": 1.2 <= speech_rate <= 1.3
                },
                "warnings": warnings
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== 人物一致性检测API ====================

@app.route('/check-consistency', methods=['POST'])
def check_character_consistency():
    """
    人物一致性检测接口
    接收多帧图片或视频，检测人物特征一致性
    
    请求方式: multipart/form-data 或 JSON
    
    方式1 - 文件上传:
        - images: 多张图片文件
        - video: 视频文件（可选，将提取帧）
        - frame_count: 提取帧数量（默认8）
    
    方式2 - JSON:
        {
            "images": [
                {"url": "http://...", "frame_id": 1},
                {"path": "/path/to/image.jpg", "frame_id": 2}
            ],
            "video_path": "/path/to/video.mp4"  // 可选
        }
    
    返回:
    {
        "success": true,
        "data": {
            "consistency_score": 85.5,
            "is_consistent": true,
            "grade": "A 良好",
            "features": {
                "face_shape": {...},
                "skin_tone": {...}
            },
            "issues": [...],
            "recommendations": [...]
        }
    }
    """
    try:
        images = []
        video_path = None
        frame_count = 8
        
        # 方式1: 文件上传
        if 'images' in request.files:
            files = request.files.getlist('images')
            for i, file in enumerate(files):
                if file.filename:
                    result = save_upload_file(file, prefix="consistency_check")
                    if result:
                        images.append({
                            "path": result["path"],
                            "frame_id": i + 1
                        })
            
            # 视频帧提取（如果提供了视频）
            if 'video' in request.files:
                video_file = request.files['video']
                if video_file.filename and allowed_video_file(video_file.filename):
                    video_result = save_upload_file(video_file, prefix="consistency_video")
                    if video_result:
                        video_path = video_result["path"]
                        frame_count = int(request.form.get('frame_count', 8))
        
        # 方式2: JSON
        elif request.is_json:
            data = request.get_json()
            images = data.get('images', [])
            video_path = data.get('video_path')
            frame_count = data.get('frame_count', 8)
        
        if not images:
            return api_response(success=False, error="未提供图片文件")
        
        # 如果提供了视频，提取帧
        if video_path and os.path.exists(video_path):
            extracted_frames = extract_video_frames(video_path, frame_count)
            images.extend(extracted_frames)
        
        # 检测一致性
        result = detect_character_consistency(images)
        
        return api_response(
            success=result.get("success", False),
            data={
                "consistency_score": result.get("consistency_score", 0),
                "is_consistent": result.get("is_consistent", False),
                "grade": result.get("grade", "未知"),
                "features": result.get("features", {}),
                "issues": result.get("issues", []),
                "recommendations": result.get("recommendations", []),
                "checked_frames": result.get("checked_frames", len(images))
            },
            message="一致性检测完成" if result.get("success") else "检测失败"
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


def extract_video_frames(video_path: str, frame_count: int = 8) -> List[Dict]:
    """从视频中提取帧"""
    frames = []
    try:
        # 获取视频时长
        duration = get_video_duration(video_path)
        
        # 计算帧间隔
        interval = duration / (frame_count + 1)
        
        for i in range(1, frame_count + 1):
            timestamp = interval * i
            
            # 生成帧图片路径
            frame_path = video_path.replace('.mp4', f'_frame_{i}.jpg')
            frame_path = frame_path.replace('.mov', f'_frame_{i}.jpg')
            
            # 提取帧
            cmd = [
                'ffmpeg', '-y', '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1', '-q:v', '2',
                frame_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
            
            if os.path.exists(frame_path):
                frames.append({
                    "path": frame_path,
                    "frame_id": i,
                    "timestamp": timestamp
                })
        
    except Exception as e:
        print(f"提取视频帧失败: {e}")
    
    return frames


# ==================== 增强剪辑解析API ====================

@app.route('/parse', methods=['POST'])
def enhanced_parse():
    """
    增强AI剪辑解析接口
    支持更多剪辑指令：
    - 节奏控制（快/慢/渐变）
    - 转场效果（淡入淡出/闪白）
    - 情绪标签（紧张/温馨/悬疑）
    
    请求体:
    {
        "text": "剪辑要求文本...",
        "total_duration": 90  // 可选，视频总时长
    }
    
    返回:
    {
        "success": true,
        "data": {
            "instructions": {
                "rhythm": [...],
                "transitions": [...],
                "emotions": [...],
                "segments": [...],
                "effects": [...],
                "bgm": {...}
            },
            "summary": "..."
        }
    }
    """
    try:
        data = request.get_json()
        
        text = data.get('text', '').strip()
        total_duration = data.get('total_duration', 0)
        
        if not text:
            return api_response(success=False, error="剪辑要求不能为空")
        
        # 解析指令
        result = enhanced_parse_instructions(text, total_duration)
        
        return api_response(
            success=result.get("success", False),
            data={
                "instructions": result.get("instructions", {}),
                "summary": result.get("summary", ""),
                "raw_segments": result.get("raw_segments", [])
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


@app.route('/parse/quick', methods=['POST'])
def quick_parse():
    """
    快速剪辑解析（简化版）
    
    请求体:
    {
        "keywords": ["开头", "震撼", "快节奏", "结尾", "悬疑"]
    }
    """
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        
        if not keywords:
            return api_response(success=False, error="未提供关键词")
        
        # 快速组合为文本
        text = " ".join(keywords)
        result = enhanced_parse_instructions(text)
        
        return api_response(
            success=True,
            data={
                "keywords": keywords,
                "instructions": result.get("instructions", {}),
                "summary": result.get("summary", "")
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        return api_response(success=False, error=str(e))


# ==================== 去水印功能 API ====================

try:
    import cv2
    WATERMARK_CV2_AVAILABLE = True
except ImportError:
    WATERMARK_CV2_AVAILABLE = False

watermark_tasks = {}

@app.route('/api/watermark/upload', methods=['POST'])
def watermark_upload():
    """上传视频用于去水印"""
    try:
        if 'video' not in request.files:
            return api_response(success=False, error='No video file')
        file = request.files['video']
        if file.filename == '':
            return api_response(success=False, error='No file selected')
        
        task_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        video_path = config.UPLOAD_DIR / f"wm_{task_id}_{filename}"
        file.save(video_path)
        
        video_info = {}
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(video_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                for s in info.get('streams', []):
                    if s.get('codec_type') == 'video':
                        fps_str = s.get('r_frame_rate', '0/1')
                        fps = eval(fps_str) if '/' in fps_str else float(fps_str)
                        video_info = {'width': int(s.get('width', 0)), 'height': int(s.get('height', 0)),
                                      'duration': float(info.get('format', {}).get('duration', 0)), 'fps': round(fps, 2)}
                        break
        except: pass
        
        watermark_tasks[task_id] = {'video_path': str(video_path), 'output_path': None, 'regions': [], 'status': 'uploaded', 'video_info': video_info}
        return api_response(success=True, data={'task_id': task_id, 'video_info': video_info})
    except Exception as e:
        return api_response(success=False, error=str(e))

@app.route('/api/watermark/detect', methods=['POST'])
def watermark_detect():
    """检测水印区域"""
    try:
        data = request.json
        if not data or 'task_id' not in data:
            return api_response(success=False, error='task_id required')
        task_id = data['task_id']
        if task_id not in watermark_tasks:
            return api_response(success=False, error='Task not found')
        
        task = watermark_tasks[task_id]
        regions = []
        
        if WATERMARK_CV2_AVAILABLE:
            cap = cv2.VideoCapture(task['video_path'])
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                for i in range(1, min(6, total)):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(i * total / 6))
                    ret, frame = cap.read()
                    if not ret: continue
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(gray, 50, 150)
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
                    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
                    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    for c in contours:
                        x, y, w, h = cv2.boundingRect(c)
                        if w > width * 0.2 and w / max(h, 1) > 3 and 1000 < w * h < width * height * 0.2:
                            regions.append({'x': max(0, x - 10), 'y': max(0, y - 5), 'width': min(width - x, w + 20), 'height': min(height - y, h + 10)})
                cap.release()
        
        task['regions'] = regions
        task['status'] = 'detected'
        return api_response(success=True, data={'regions': regions, 'count': len(regions)})
    except Exception as e:
        return api_response(success=False, error=str(e))

@app.route('/api/watermark/remove', methods=['POST'])
def watermark_remove():
    """去除水印"""
    try:
        data = request.json
        if not data or 'task_id' not in data:
            return api_response(success=False, error='task_id required')
        task_id = data['task_id']
        if task_id not in watermark_tasks:
            return api_response(success=False, error='Task not found')
        
        task = watermark_tasks[task_id]
        regions = data.get('regions', task['regions'])
        if not regions:
            return api_response(success=False, error='No regions')
        
        output_path = config.OUTPUT_DIR / f"wm_{task_id}_output.mp4"
        task['status'] = 'processing'
        
        filters = []
        for r in regions:
            if isinstance(r, dict):
                x, y, w, h = r.get('x', 0), r.get('y', 0), r.get('width', 100), r.get('height', 50)
            elif isinstance(r, (list, tuple)) and len(r) >= 4:
                x, y, w, h = r[:4]
            else: continue
            filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
        
        cmd = ['ffmpeg', '-i', task['video_path'], '-vf', ','.join(filters), '-c:a', 'copy', '-y', str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            task['status'] = 'failed'
            return api_response(success=False, error=f'FFmpeg error')
        
        task['output_path'] = str(output_path)
        task['status'] = 'completed'
        return api_response(success=True, data={'task_id': task_id, 'status': 'completed', 'download_url': f'/api/watermark/download/{task_id}'})
    except Exception as e:
        return api_response(success=False, error=str(e))

@app.route('/api/watermark/download/<task_id>')
def watermark_download(task_id):
    """下载处理后的视频"""
    if task_id not in watermark_tasks:
        return api_response(success=False, error='Task not found')
    task = watermark_tasks[task_id]
    if task['status'] != 'completed' or not task['output_path']:
        return api_response(success=False, error='Not ready')
    return send_file(task['output_path'], mimetype='video/mp4', as_attachment=True)


# ==================== 主程序 ====================


# ==================== 前端静态文件服务 ====================

@app.route('/')
def serve_index():
    """返回前端首页"""
    static_dir = Path(__file__).parent.parent / 'static'
    return send_from_directory(static_dir, 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """返回前端静态资源"""
    static_dir = Path(__file__).parent.parent / 'static' / 'assets'
    return send_from_directory(static_dir, filename)

@app.route('/<path:path>')
def serve_spa(path):
    """SPA路由 - 所有未匹配的路由返回index.html"""
    static_dir = Path(__file__).parent.parent / 'static'
    file_path = static_dir / path
    if file_path.exists():
        return send_from_directory(static_dir, path)
    return send_from_directory(static_dir, 'index.html')


if __name__ == '__main__':
    print("=" * 50)
    print("AI智能剪辑平台 - 后端服务")
    print("=" * 50)
    print("API端点:")
    print("  [上传]")
    print("  POST /upload/videos   - 上传视频文件")
    print("  POST /upload/script   - 上传剧本")
    print("  [剪辑]")
    print("  POST /process         - 开始剪辑处理")
    print("  GET  /status/<task_id> - 查询进度")
    print("  GET  /download/<task_id> - 下载成片")
    print("  [BGM]")
    print("  POST /bgm/search      - 搜索BGM")
    print("  GET  /bgm/preview/<id> - 试听BGM")
    print("  [AI字幕]")
    print("  POST /generate-subtitles - 生成字幕")
    print("  POST /subtitles/srt   - 获取SRT格式")
    print("  [AI剪辑建议]")
    print("  POST /suggest          - AI剪辑建议")
    print("  POST /suggest/validate - 验证剪辑参数")
    print("  [人物一致性]")
    print("  POST /check-consistency - 检测人物一致性")
    print("  [增强解析]")
    print("  POST /parse            - 增强剪辑解析")
    print("  POST /parse/quick      - 快速解析")
    print("=" * 50)
    
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
