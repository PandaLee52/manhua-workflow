#!/usr/bin/env python3
"""AI剪辑平台 - Render部署版"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import uuid
import json
import requests
import ffmpeg
from werkzeug.utils import secure_filename
import subprocess
import time

app = Flask(__name__)
CORS(app)

# 配置
UPLOAD_FOLDER = '/tmp/video_uploads'
PROCESSED_FOLDER = '/tmp/video_processed'
TEMP_FOLDER = '/tmp/temp'
BGM_CACHE = '/tmp/bgm_cache'

# 确保目录存在
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, TEMP_FOLDER, BGM_CACHE]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_audio(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

# ============================================
# 1. 视频上传接口 POST /upload
# ============================================
@app.route('/upload', methods=['POST'])
def upload():
    """接收多视频文件上传，返回文件ID列表"""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400
        
        uploaded_ids = []
        file_info = {}
        
        for file in files:
            if file and allowed_video(file.filename):
                # 生成唯一文件ID
                file_id = str(uuid.uuid4())[:12]
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                saved_filename = f"{file_id}.{ext}"
                filepath = os.path.join(UPLOAD_FOLDER, saved_filename)
                
                # 保存文件
                file.save(filepath)
                
                # 获取视频信息
                try:
                    probe = ffmpeg.probe(filepath)
                    duration = float(probe['format']['duration'])
                    video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
                    width = int(video_stream['width']) if video_stream else 0
                    height = int(video_stream['height']) if video_stream else 0
                except Exception as e:
                    duration = 0
                    width, height = 0, 0
                
                uploaded_ids.append(file_id)
                file_info[file_id] = {
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'duration': duration,
                    'resolution': f"{width}x{height}"
                }
            else:
                return jsonify({
                    'success': False, 
                    'error': f'不支持的文件格式: {file.filename}'
                }), 400
        
        return jsonify({
            'success': True,
            'file_ids': uploaded_ids,
            'files': file_info,
            'message': f'成功上传 {len(uploaded_ids)} 个文件'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# 2. 视频拼接接口 POST /merge
# ============================================
@app.route('/merge', methods=['POST'])
def merge():
    """接收视频ID列表，使用ffmpeg拼接视频，返回合并后视频URL"""
    try:
        data = request.get_json() or {}
        video_ids = data.get('video_ids', [])
        output_name = data.get('output_name', f'merged_{int(time.time())}')
        
        if not video_ids or len(video_ids) < 2:
            return jsonify({
                'success': False, 
                'error': '至少需要2个视频ID'
            }), 400
        
        # 查找视频文件
        video_paths = []
        for vid in video_ids:
            found = False
            for ext in ALLOWED_VIDEO_EXTENSIONS:
                path = os.path.join(UPLOAD_FOLDER, f"{vid}.{ext}")
                if os.path.exists(path):
                    video_paths.append(path)
                    found = True
                    break
            if not found:
                return jsonify({
                    'success': False, 
                    'error': f'视频ID {vid} 不存在'
                }), 404
        
        # 创建合并列表文件
        list_filename = f"{output_name}_list.txt"
        list_filepath = os.path.join(TEMP_FOLDER, list_filename)
        
        with open(list_filepath, 'w') as f:
            for path in video_paths:
                # 转义路径中的单引号
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
        
        # 输出文件
        output_filename = f"{output_name}.mp4"
        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)
        
        # 执行ffmpeg合并
        try:
            stream = ffmpeg.input(list_filepath, format='concat', safe=0)
            stream = ffmpeg.output(stream, output_filepath, c='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
        except ffmpeg.Error as e:
            # 如果copy模式失败，尝试重新编码模式
            stream = ffmpeg.input(list_filepath, format='concat', safe=0)
            stream = ffmpeg.output(stream, output_filepath, c='libx264', crf=23)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        # 清理临时文件
        os.remove(list_filepath)
        
        # 获取输出视频信息
        probe = ffmpeg.probe(output_filepath)
        duration = float(probe['format']['duration'])
        
        return jsonify({
            'success': True,
            'video_id': output_name,
            'video_url': f'/download/{output_name}.mp4',
            'duration': duration,
            'size': os.path.getsize(output_filepath),
            'message': f'成功合并 {len(video_ids)} 个视频'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# 3. BGM搜索接口 GET /search-bgm
# ============================================
@app.route('/search-bgm', methods=['GET'])
def search_bgm():
    """接收关键词，联网搜索免费音乐，返回音乐URL列表"""
    try:
        keyword = request.args.get('keyword', '')
        emotion = request.args.get('emotion', '')
        duration = request.args.get('duration', 'short')  # short, medium, long
        
        # 合并关键词
        search_term = keyword or emotion
        if not search_term:
            return jsonify({
                'success': False, 
                'error': '请提供关键词或情绪类型'
            }), 400
        
        # 情绪关键词映射
        emotion_map = {
            '悬疑': 'mystery suspense dark',
            '紧张': 'tension action dramatic',
            '欢快': 'happy upbeat positive',
            '悲伤': 'sad emotional melancholy',
            '温馨': 'warm gentle peaceful',
            '史诗': 'epic cinematic orchestral',
            '浪漫': 'romantic love soft',
            '恐怖': 'horror scary dark',
            '搞笑': 'comedy funny playful'
        }
        
        # 如果是情绪词，转换为搜索关键词
        if emotion in emotion_map:
            search_term = emotion_map[emotion]
        elif emotion and emotion not in search_term:
            search_term = f"{search_term} {emotion}"
        
        # 时长参数
        duration_filter = {
            'short': '10-30',
            'medium': '30-120',
            'long': '120-300'
        }
        
        results = []
        
        # 方法1: 搜索Pixabay音乐
        try:
            pixabay_results = search_pixabay_music(search_term, duration)
            results.extend(pixabay_results)
        except Exception as e:
            print(f"Pixabay搜索失败: {e}")
        
        # 方法2: 搜索Freesound
        try:
            freesound_results = search_freesound(search_term, duration)
            results.extend(freesound_results)
        except Exception as e:
            print(f"Freesound搜索失败: {e}")
        
        # 方法3: 搜索免费音乐档案
        try:
            archive_results = search_free_music_archive(search_term)
            results.extend(archive_results)
        except Exception as e:
            print(f"FreeMusicArchive搜索失败: {e}")
        
        # 去重（基于标题相似度）
        unique_results = []
        seen_titles = set()
        for r in results:
            title_key = r['title'].lower()[:20]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_results.append(r)
        
        # 限制返回数量
        unique_results = unique_results[:20]
        
        if not unique_results:
            return jsonify({
                'success': True,
                'keyword': search_term,
                'results': [],
                'message': '未找到匹配的BGM，请尝试其他关键词'
            })
        
        return jsonify({
            'success': True,
            'keyword': search_term,
            'count': len(unique_results),
            'results': unique_results,
            'message': f'找到 {len(unique_results)} 个匹配的BGM'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def search_pixabay_music(keyword, duration='short'):
    """搜索Pixabay免费音乐"""
    results = []
    
    # 尝试使用Pixabay API (需要API key，这里使用公开搜索)
    # 注意: Pixabay API需要密钥，这里使用备用方案
    
    # 使用CC0 Music搜索
    search_url = f"https://pixabay.com/api/?key=&q={keyword}&media_type=music"
    
    # 如果没有API key，返回示例数据
    # 实际使用需要申请API key: https://pixabay.com/api/docs/
    
    return results

def search_freesound(keyword, duration='short'):
    """搜索Freesound音效库"""
    results = []
    
    # Freesound API (需要API key)
    # https://freesound.org/apiv2/apply/
    
    # 公开搜索端点
    search_url = f"https://freesound.org/search/?q={keyword}&f=type:mp3"
    
    # 返回结构化数据（实际使用时需要解析HTML或使用API）
    # 这里返回模拟数据，实际环境请申请Freesound API key
    
    return results

def search_free_music_archive(keyword):
    """搜索Free Music Archive"""
    results = []
    
    # Free Music Archive API
    api_url = f"https://freemusicarchive.org/api/get/tracks.json?genre_id=38&title={keyword}"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for track in data.get('dataset', [])[:10]:
                results.append({
                    'title': track.get('track_title', 'Unknown'),
                    'artist': track.get('artist_name', 'Unknown'),
                    'url': track.get('track_url', ''),
                    'duration': int(track.get('track_duration', 0)),
                    'source': 'FreeMusicArchive',
                    'license': 'CC BY'
                })
    except Exception as e:
        print(f"FMA搜索错误: {e}")
    
    return results

# ============================================
# 4. 视频处理接口 POST /process
# ============================================
@app.route('/process', methods=['POST'])
def process():
    """接收视频ID + 剪辑要求，AI解析并应用剪辑效果，返回处理后视频"""
    try:
        data = request.get_json() or {}
        video_id = data.get('video_id')
        instructions = data.get('instructions', '')
        bgm_url = data.get('bgm_url')
        speed = data.get('speed', 1.0)  # 播放速度
        transitions = data.get('transitions', [])  # 转场效果
        
        if not video_id:
            return jsonify({
                'success': False, 
                'error': '缺少视频ID'
            }), 400
        
        if not instructions and not bgm_url and speed == 1.0:
            return jsonify({
                'success': False, 
                'error': '没有提供剪辑指令'
            }), 400
        
        # 查找视频文件
        video_path = None
        for ext in ALLOWED_VIDEO_EXTENSIONS:
            path = os.path.join(UPLOAD_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
            # 尝试在processed目录查找
            for ext in ALLOWED_VIDEO_EXTENSIONS:
                path = os.path.join(PROCESSED_FOLDER, f"{video_id}.{ext}")
                if os.path.exists(path):
                    video_path = path
                    break
        
        if not video_path:
            return jsonify({
                'success': False, 
                'error': f'视频ID {video_id} 不存在'
            }), 404
        
        # 生成输出文件名
        output_id = f"processed_{video_id}_{int(time.time())}"
        output_filename = f"{output_id}.mp4"
        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)
        
        # 解析剪辑指令
        parsed_instructions = parse_instructions(instructions)
        
        # 构建ffmpeg命令
        stream = ffmpeg.input(video_path)
        
        # 应用速度调整
        if speed != 1.0:
            stream = ffmpeg.filter(stream, 'setpts', f'{1/speed}*PTS')
        
        # 下载并添加BGM
        if bgm_url:
            try:
                bgm_path = download_bgm(bgm_url, output_id)
                if bgm_path:
                    # 获取视频时长
                    probe = ffmpeg.probe(video_path)
                    video_duration = float(probe['format']['duration'])
                    
                    # 混合音频
                    audio_stream = ffmpeg.input(bgm_path)
                    stream = ffmpeg.filter(
                        [stream, audio_stream],
                        'amix',
                        inputs=2,
                        duration='first'
                    )
            except Exception as e:
                print(f"BGM添加失败: {e}")
        
        # 应用转场效果
        if transitions:
            stream = apply_transitions(stream, transitions)
        
        # 输出
        stream = ffmpeg.output(
            stream, 
            output_filepath,
            vcodec='libx264',
            acodec='aac',
            crf=23,
            preset='fast'
        )
        
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        # 获取输出视频信息
        probe = ffmpeg.probe(output_filepath)
        duration = float(probe['format']['duration'])
        
        return jsonify({
            'success': True,
            'video_id': output_id,
            'video_url': f'/download/{output_filename}',
            'duration': duration,
            'size': os.path.getsize(output_filepath),
            'instructions_applied': parsed_instructions,
            'message': '视频处理完成'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_instructions(instructions):
    """解析剪辑指令"""
    parsed = []
    
    instruction_keywords = {
        '开头': ['开头', '开始', '开场', '前面'],
        '中间': ['中间', '过程', '发展'],
        '结尾': ['结尾', '结束', '收尾', '最后'],
        '节奏': ['节奏', '快', '慢', '加速', '减速'],
        '情绪': ['情绪', '紧张', '温馨', '悬疑', '欢快']
    }
    
    for key, keywords in instruction_keywords.items():
        for kw in keywords:
            if kw in instructions:
                parsed.append(f"{key}: {kw}")
                break
    
    return parsed if parsed else ['通用剪辑']

def download_bgm(url, output_id):
    """下载BGM到本地"""
    bgm_filename = f"{output_id}_bgm.mp3"
    bgm_path = os.path.join(BGM_CACHE, bgm_filename)
    
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code == 200:
            with open(bgm_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return bgm_path
    except Exception as e:
        print(f"BGM下载失败: {e}")
    
    return None

def apply_transitions(stream, transitions):
    """应用转场效果"""
    # 目前支持淡入淡出
    for t in transitions:
        if t.get('type') == 'fade':
            duration = t.get('duration', 0.5)
            stream = ffmpeg.filter(stream, 'fade', t='in', d=duration)
    
    return stream

# ============================================
# 辅助接口
# ============================================
@app.route('/download/<path:filename>')
def download(filename):
    """下载处理后的视频"""
    # 防止路径遍历
    filename = secure_filename(filename)
    
    # 检查processed目录
    filepath = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(filepath):
        # 检查upload目录
        filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/video/<video_id>')
def get_video_info(video_id):
    """获取视频信息"""
    # 查找视频文件
    for ext in ALLOWED_VIDEO_EXTENSIONS:
        path = os.path.join(UPLOAD_FOLDER, f"{video_id}.{ext}")
        if os.path.exists(path):
            try:
                probe = ffmpeg.probe(path)
                return jsonify({
                    'success': True,
                    'video_id': video_id,
                    'duration': float(probe['format']['duration']),
                    'size': os.path.getsize(path),
                    'format': probe['format']['format_name']
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        path = os.path.join(PROCESSED_FOLDER, f"{video_id}.{ext}")
        if os.path.exists(path):
            try:
                probe = ffmpeg.probe(path)
                return jsonify({
                    'success': True,
                    'video_id': video_id,
                    'duration': float(probe['format']['duration']),
                    'size': os.path.getsize(path),
                    'format': probe['format']['format_name']
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': '视频不存在'}), 404

@app.route('/list-videos')
def list_videos():
    """列出所有已上传的视频"""
    videos = []
    
    for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
        for filename in os.listdir(folder):
            if any(filename.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS):
                filepath = os.path.join(folder, filename)
                video_id = os.path.splitext(filename)[0]
                
                try:
                    probe = ffmpeg.probe(filepath)
                    videos.append({
                        'video_id': video_id,
                        'filename': filename,
                        'duration': float(probe['format']['duration']),
                        'size': os.path.getsize(filepath),
                        'folder': os.path.basename(folder)
                    })
                except:
                    videos.append({
                        'video_id': video_id,
                        'filename': filename,
                        'duration': 0,
                        'size': os.path.getsize(filepath),
                        'folder': os.path.basename(folder)
                    })
    
    return jsonify({
        'success': True,
        'count': len(videos),
        'videos': videos
    })

@app.route('/delete/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """删除视频"""
    deleted = False
    
    for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, BGM_CACHE]:
        for ext in list(ALLOWED_VIDEO_EXTENSIONS) + ['mp3']:
            filepath = os.path.join(folder, f"{video_id}.{ext}")
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted = True
    
    if deleted:
        return jsonify({'success': True, 'message': '视频已删除'})
    else:
        return jsonify({'success': False, 'error': '视频不存在'}), 404

# ============================================
# 原有接口保持兼容
# ============================================
@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'AI剪辑平台API已启动',
        'endpoints': [
            '/health',
            '/parse',
            '/upload',
            '/merge',
            '/search-bgm',
            '/process',
            '/download/<filename>',
            '/video/<video_id>',
            '/list-videos',
            '/delete/<video_id>'
        ]
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/parse', methods=['POST'])
def parse():
    data = request.get_json() or {}
    text = data.get('text', '')
    
    result = []
    if '开头' in text and '震撼' in text:
        result.append('开头: 震撼快节奏')
    if '中间' in text and '温馨' in text:
        result.append('中间: 温馨慢节奏')
    if '结尾' in text and '悬疑' in text:
        result.append('结尾: 悬疑风格')
    
    return jsonify({'success': True, 'instructions': result})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
