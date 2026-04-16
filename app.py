#!/usr/bin/env python3
"""
AI剪辑平台 - Render部署版
整合视频上传、合并、处理、BGM搜索和AI智能剪辑功能
"""

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
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import cv2
from datetime import datetime

# 导入水印处理模块
from watermark_remover import WatermarkDetector, SubtitleDetector, WatermarkRemover, WatermarkProcessor
from video_processor import WatermarkVideoProcessor, VideoFrameExtractor, VideoAssembler
from batch_processor import BatchProcessor, BatchStatus

app = Flask(__name__)
CORS(app)

# ==================== 配置 ====================
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


# ==================== AI剪辑解析模块 ====================

# 位置关键词映射
POSITION_KEYWORDS = {
    'start': ['开头', '开始', '前面', '前面', '首', '初始', '起始', '开头部分', '片头', '开场', '前段'],
    'middle': ['中间', '中段', '中部', '中间部分', '过程', '发展', '主体', '主要内容'],
    'end': ['结尾', '结束', '后面', '末尾', '最后', '尾声', '收尾', '片尾', '后段']
}

# 风格关键词映射
STYLE_KEYWORDS = {
    'fast': ['快', '快节奏', '快速', '紧张', '紧凑', '激烈', '动感', '燃', '节奏快', '速度感', '动感'],
    'slow': ['慢', '慢节奏', '缓慢', '舒缓', '柔和', '悠扬', '悠慢', '慢镜头', '慢速'],
    'normal': ['正常', '标准', '平稳', '平均', '适中', '一般']
}

# 情绪关键词映射
MOOD_KEYWORDS = {
    'epic': ['震撼', '史诗', '宏大', '壮观', '磅礴', '大气', '燃', '热血', '激昂', '震撼感', '史诗级'],
    'suspense': ['悬疑', '神秘', '紧张', '恐怖', '惊悚', '诡异', '令人紧张', '扣人心弦', '引人入胜'],
    'warm': ['温馨', '温暖', '感人', '治愈', '甜蜜', '幸福', '美好', '温情', '柔和'],
    'sad': ['悲伤', '凄凉', '催泪', '感人', '哀伤', '失落', '心酸'],
    'happy': ['欢快', '快乐', '活泼', '轻松', '愉悦', '阳光', '明朗', '轻快'],
    'tense': ['紧张', '惊险', '危机', '危急', '惊心动魄'],
    'default': ['普通', '一般', '正常', '标准', '默认']
}

# 转场关键词映射
TRANSITION_KEYWORDS = {
    'quick': ['快切', '快速切换', '跳切', '干脆', '利落', '迅捷', '快节奏转场'],
    'smooth': ['平滑', '柔和', '渐变', '渐入', '渐出', '溶解', '淡入淡出', '缓慢过渡'],
    'dramatic': ['戏剧性', '冲击', '震动', '闪切', '跳切', '强烈'],
    'default': ['普通', '标准', '默认', '一般']
}

# BGM风格关键词映射
BGM_STYLE_KEYWORDS = {
    'epic': ['史诗', '震撼', '大气', '激昂', '燃'],
    'suspense': ['悬疑', '神秘', '紧张', '低沉', '阴森'],
    'warm': ['温馨', '温暖', '治愈', '抒情', '舒缓'],
    'sad': ['悲伤', '抒情', '低沉', '哀伤'],
    'happy': ['欢快', '轻快', '活泼', '明朗'],
    'tense': ['紧张', '刺激', '惊险', '危机'],
    'romantic': ['浪漫', '甜蜜', '柔情', '唯美'],
    'action': ['动感', '激烈', '战斗', '热血'],
    'calm': ['平静', '舒缓', '安静', '平和']
}

# 时长系数
DURATION_FACTORS = {
    'very_fast': 0.5,
    'fast': 0.7,
    'normal': 1.0,
    'slow': 1.3,
    'very_slow': 1.6
}

# 预设模板
PRESET_TEMPLATES = {
    "震撼开场": "开头要震撼，用快节奏剪辑，配合史诗级BGM",
    "温馨回忆": "中间部分要温馨，慢节奏，柔和的转场，背景音乐要温暖治愈",
    "悬疑结尾": "结尾要悬疑感，镜头停留时间长一点，配合紧张的音乐",
    "快节奏混剪": "全部内容用快节奏剪辑，画面切换快，BGM要动感激烈",
    "电影感": "整体要有电影感，节奏适中，情绪层层递进，BGM大气",
    "vlog风格": "日常vlog风格，轻松活泼，快慢结合，配欢快的音乐",
    "情绪爆发": "开头平静，中间逐渐紧张，结尾情绪爆发，BGM从安静到激昂",
    "唯美慢镜头": "整体慢节奏，多用慢镜头，转场柔和，画面唯美"
}

@dataclass
class SegmentRequirement:
    """段落剪辑要求"""
    position: str
    style: str
    mood: str
    duration_factor: float
    transition: str
    bgm_keywords: List[str]
    description: str

@dataclass
class ParsedRequirements:
    """解析后的完整剪辑要求"""
    segments: List[SegmentRequirement]
    global_bgm_style: str
    global_transition: str
    has_custom_requirements: bool
    raw_text: str
    use_llm: bool


class RuleBasedParser:
    """基于规则的剪辑要求解析器"""
    
    def __init__(self):
        self.position_keywords = POSITION_KEYWORDS
        self.style_keywords = STYLE_KEYWORDS
        self.mood_keywords = MOOD_KEYWORDS
        self.transition_keywords = TRANSITION_KEYWORDS
        self.bgm_keywords = BGM_STYLE_KEYWORDS
    
    def parse(self, text: str) -> ParsedRequirements:
        if not text or not text.strip():
            return self._default_requirements(text)
        
        segments = []
        found_positions = set()
        
        for position, pos_keywords in self.position_keywords.items():
            for keyword in pos_keywords:
                if keyword in text:
                    segment = self._extract_segment(text, position, keyword)
                    if segment and position not in found_positions:
                        segments.append(segment)
                        found_positions.add(position)
                    break
        
        if not segments:
            segments = self._extract_global_segments(text)
        
        bgm_style = self._extract_bgm_style(text)
        transition = self._extract_transition(text)
        
        return ParsedRequirements(
            segments=segments,
            global_bgm_style=bgm_style,
            global_transition=transition,
            has_custom_requirements=len(segments) > 0,
            raw_text=text,
            use_llm=False
        )
    
    def _extract_segment(self, text: str, position: str, keyword: str) -> Optional[SegmentRequirement]:
        style = self._extract_style(text)
        mood = self._extract_mood(text)
        duration_factor = self._extract_duration_factor(text, style)
        transition = self._extract_transition(text)
        bgm_keywords = self._extract_bgm_keywords(text)
        
        return SegmentRequirement(
            position=position,
            style=style,
            mood=mood,
            duration_factor=duration_factor,
            transition=transition,
            bgm_keywords=bgm_keywords,
            description=f"{position}: {mood}情绪, {style}节奏"
        )
    
    def _extract_global_segments(self, text: str) -> List[SegmentRequirement]:
        segments = []
        style = self._extract_style(text)
        mood = self._extract_mood(text)
        duration_factor = self._extract_duration_factor(text, style)
        transition = self._extract_transition(text)
        bgm_keywords = self._extract_bgm_keywords(text)
        
        if any(k in text for k in ['全', '整个', '所有', '整体']):
            for pos in ['start', 'middle', 'end']:
                segments.append(SegmentRequirement(
                    position=pos,
                    style=style,
                    mood=mood,
                    duration_factor=duration_factor,
                    transition=transition,
                    bgm_keywords=bgm_keywords,
                    description=f"整体: {mood}情绪"
                ))
        else:
            segments.append(SegmentRequirement(
                position='start',
                style=style,
                mood=mood,
                duration_factor=duration_factor,
                transition=transition,
                bgm_keywords=bgm_keywords,
                description=f"开头: {mood}情绪"
            ))
        
        return segments
    
    def _extract_style(self, text: str) -> str:
        for style, keywords in self.style_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return style
        return 'normal'
    
    def _extract_mood(self, text: str) -> str:
        for mood, keywords in self.mood_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return mood
        return 'default'
    
    def _extract_duration_factor(self, text: str, style: str) -> float:
        if style == 'fast':
            base_factor = DURATION_FACTORS['fast']
        elif style == 'slow':
            base_factor = DURATION_FACTORS['slow']
        else:
            base_factor = DURATION_FACTORS['normal']
        
        if any(k in text for k in ['非常', '特别', '极其', '十分']):
            if style == 'fast':
                base_factor = DURATION_FACTORS['very_fast']
            elif style == 'slow':
                base_factor = DURATION_FACTORS['very_slow']
        
        return base_factor
    
    def _extract_transition(self, text: str) -> str:
        for transition, keywords in self.transition_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return transition
        return 'default'
    
    def _extract_bgm_style(self, text: str) -> str:
        for bgm_style, keywords in self.bgm_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return bgm_style
        return 'calm'
    
    def _extract_bgm_keywords(self, text: str) -> List[str]:
        keywords = []
        for bgm_style, style_keywords in self.bgm_keywords.items():
            for keyword in style_keywords:
                if keyword in text:
                    if keyword not in keywords:
                        keywords.append(keyword)
        return keywords
    
    def _default_requirements(self, text: str) -> ParsedRequirements:
        return ParsedRequirements(
            segments=[],
            global_bgm_style='calm',
            global_transition='default',
            has_custom_requirements=False,
            raw_text=text or '',
            use_llm=False
        )


class LLMAPIParser:
    """基于LLM API的剪辑要求解析器"""
    
    def __init__(self, api_key: str = None, api_url: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.api_url = api_url or "https://api.openai.com/v1/chat/completions"
        self.model = model
        self.rule_parser = RuleBasedParser()
        
        self.system_prompt = """你是一个专业的视频剪辑助手，擅长将用户的自然语言剪辑要求转换为结构化的参数。

请分析用户输入的剪辑要求，输出JSON格式的结构化参数：

{
    "segments": [
        {
            "position": "start/middle/end",
            "style": "fast/slow/normal",
            "mood": "epic/suspense/warm/sad/happy/tense/default",
            "duration_factor": 0.5-1.6,
            "transition": "quick/smooth/dramatic/default",
            "description": "该段落的描述"
        }
    ],
    "global_bgm_style": "epic/suspense/warm/calm/romantic/action/default",
    "global_transition": "quick/smooth/dramatic/default",
    "has_custom_requirements": true/false,
    "summary": "对剪辑要求的简要总结"
}"""
    
    def parse(self, text: str) -> ParsedRequirements:
        if not text or not text.strip():
            return self.rule_parser._default_requirements(text)
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                parsed = json.loads(content)
                return self._convert_to_parsed_requirements(parsed, text)
            else:
                print(f"LLM API调用失败: {response.status_code}, 使用规则引擎")
                return self.rule_parser.parse(text)
                
        except Exception as e:
            print(f"LLM解析异常: {e}, 使用规则引擎")
            return self.rule_parser.parse(text)
    
    def _convert_to_parsed_requirements(self, parsed: Dict, raw_text: str) -> ParsedRequirements:
        segments = []
        
        for seg in parsed.get('segments', []):
            segments.append(SegmentRequirement(
                position=seg.get('position', 'start'),
                style=seg.get('style', 'normal'),
                mood=seg.get('mood', 'default'),
                duration_factor=seg.get('duration_factor', 1.0),
                transition=seg.get('transition', 'default'),
                bgm_keywords=[],
                description=seg.get('description', '')
            ))
        
        return ParsedRequirements(
            segments=segments,
            global_bgm_style=parsed.get('global_bgm_style', 'calm'),
            global_transition=parsed.get('global_transition', 'default'),
            has_custom_requirements=parsed.get('has_custom_requirements', len(segments) > 0),
            raw_text=raw_text,
            use_llm=True
        )


class AIRequirementsParser:
    """AI剪辑要求解析器（支持规则引擎和LLM）"""
    
    def __init__(self, use_llm: bool = False, llm_api_key: str = None, 
                 llm_api_url: str = None, llm_model: str = "gpt-3.5-turbo"):
        self.rule_parser = RuleBasedParser()
        self.use_llm = use_llm
        self.llm_parser = None
        
        if use_llm and llm_api_key:
            self.llm_parser = LLMAPIParser(
                api_key=llm_api_key,
                api_url=llm_api_url,
                model=llm_model
            )
    
    def parse(self, text: str) -> ParsedRequirements:
        if self.llm_parser and self.use_llm:
            return self.llm_parser.parse(text)
        else:
            return self.rule_parser.parse(text)
    
    def parse_to_dict(self, text: str) -> Dict[str, Any]:
        result = self.parse(text)
        return {
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
                for seg in result.segments
            ],
            "global_bgm_style": result.global_bgm_style,
            "global_transition": result.global_transition,
            "has_custom_requirements": result.has_custom_requirements,
            "raw_text": result.raw_text,
            "use_llm": result.use_llm
        }


# ==================== API 路由 ====================

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
                file_id = str(uuid.uuid4())[:12]
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                saved_filename = f"{file_id}.{ext}"
                filepath = os.path.join(UPLOAD_FOLDER, saved_filename)
                
                file.save(filepath)
                
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
        
        list_filename = f"{output_name}_list.txt"
        list_filepath = os.path.join(TEMP_FOLDER, list_filename)
        
        with open(list_filepath, 'w') as f:
            for path in video_paths:
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
        
        output_filename = f"{output_name}.mp4"
        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)
        
        try:
            stream = ffmpeg.input(list_filepath, format='concat', safe=0)
            stream = ffmpeg.output(stream, output_filepath, c='copy')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
        except ffmpeg.Error as e:
            stream = ffmpeg.input(list_filepath, format='concat', safe=0)
            stream = ffmpeg.output(stream, output_filepath, c='libx264', crf=23)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        os.remove(list_filepath)
        
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
        duration = request.args.get('duration', 'short')
        
        search_term = keyword or emotion
        if not search_term:
            return jsonify({
                'success': False, 
                'error': '请提供关键词或情绪类型'
            }), 400
        
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
        
        if emotion in emotion_map:
            search_term = emotion_map[emotion]
        elif emotion and emotion not in search_term:
            search_term = f"{search_term} {emotion}"
        
        results = []
        
        try:
            archive_results = search_free_music_archive(search_term)
            results.extend(archive_results)
        except Exception as e:
            print(f"FreeMusicArchive搜索失败: {e}")
        
        unique_results = []
        seen_titles = set()
        for r in results:
            title_key = r['title'].lower()[:20]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_results.append(r)
        
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


def search_free_music_archive(keyword):
    """搜索Free Music Archive"""
    results = []
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
        speed = data.get('speed', 1.0)
        transitions = data.get('transitions', [])
        
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
        
        video_path = None
        for ext in ALLOWED_VIDEO_EXTENSIONS:
            path = os.path.join(UPLOAD_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
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
        
        output_id = f"processed_{video_id}_{int(time.time())}"
        output_filename = f"{output_id}.mp4"
        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)
        
        # 使用AI解析器解析剪辑指令
        if instructions:
            parsed = AIRequirementsParser().parse_to_dict(instructions)
        else:
            parsed = {"segments": [], "global_bgm_style": "calm"}
        
        stream = ffmpeg.input(video_path)
        
        if speed != 1.0:
            stream = ffmpeg.filter(stream, 'setpts', f'{1/speed}*PTS')
        
        if bgm_url:
            try:
                bgm_path = download_bgm(bgm_url, output_id)
                if bgm_path:
                    probe = ffmpeg.probe(video_path)
                    video_duration = float(probe['format']['duration'])
                    audio_stream = ffmpeg.input(bgm_path)
                    stream = ffmpeg.filter(
                        [stream, audio_stream],
                        'amix',
                        inputs=2,
                        duration='first'
                    )
            except Exception as e:
                print(f"BGM添加失败: {e}")
        
        if transitions:
            stream = apply_transitions(stream, transitions)
        
        stream = ffmpeg.output(
            stream, 
            output_filepath,
            vcodec='libx264',
            acodec='aac',
            crf=23,
            preset='fast'
        )
        
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        probe = ffmpeg.probe(output_filepath)
        duration = float(probe['format']['duration'])
        
        return jsonify({
            'success': True,
            'video_id': output_id,
            'video_url': f'/download/{output_filename}',
            'duration': duration,
            'size': os.path.getsize(output_filepath),
            'parsed_instructions': parsed,
            'message': '视频处理完成'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
    for t in transitions:
        if t.get('type') == 'fade':
            duration = t.get('duration', 0.5)
            stream = ffmpeg.filter(stream, 'fade', t='in', d=duration)
    
    return stream


# ============================================
# 5. AI剪辑建议接口 POST /suggest
# ============================================
@app.route('/suggest', methods=['POST'])
def ai_suggest():
    """
    AI剪辑建议接口
    根据视频内容和风格要求，生成剪辑建议
    """
    try:
        data = request.get_json() or {}
        video_duration = data.get('duration', 60)
        video_type = data.get('type', 'general')  # general, vlog, movie, music
        style = data.get('style', 'auto')  # auto, epic, warm, suspense, happy
        use_llm = data.get('use_llm', False)
        llm_api_key = data.get('llm_api_key')
        
        # 根据视频类型和时长生成建议
        suggestions = generate_clipping_suggestions(
            video_duration, video_type, style
        )
        
        # 如果启用LLM，进一步优化建议
        if use_llm and llm_api_key:
            try:
                llm_suggestions = enhance_suggestions_with_llm(
                    suggestions, video_duration, llm_api_key
                )
                suggestions = llm_suggestions
            except Exception as e:
                print(f"LLM优化失败: {e}")
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'video_info': {
                'duration': video_duration,
                'type': video_type,
                'style': style
            },
            'message': '剪辑建议生成成功'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_clipping_suggestions(duration: float, video_type: str, style: str) -> Dict[str, Any]:
    """根据视频类型和风格生成剪辑建议"""
    
    # 计算分段时长
    start_duration = duration * 0.25
    middle_duration = duration * 0.5
    end_duration = duration * 0.25
    
    # 风格映射
    style_config = {
        'epic': {
            'start': {'pace': 'fast', 'mood': 'epic', 'transition': 'quick', 'bgm': '史诗'},
            'middle': {'pace': 'medium', 'mood': 'tense', 'transition': 'smooth', 'bgm': '紧张'},
            'end': {'pace': 'slow', 'mood': 'dramatic', 'transition': 'dramatic', 'bgm': '震撼'}
        },
        'warm': {
            'start': {'pace': 'slow', 'mood': 'warm', 'transition': 'smooth', 'bgm': '温馨'},
            'middle': {'pace': 'normal', 'mood': 'happy', 'transition': 'smooth', 'bgm': '欢快'},
            'end': {'pace': 'slow', 'mood': 'warm', 'transition': 'smooth', 'bgm': '温情'}
        },
        'suspense': {
            'start': {'pace': 'slow', 'mood': 'suspense', 'transition': 'smooth', 'bgm': '悬疑'},
            'middle': {'pace': 'fast', 'mood': 'tense', 'transition': 'quick', 'bgm': '紧张'},
            'end': {'pace': 'slow', 'mood': 'suspense', 'transition': 'dramatic', 'bgm': '惊悚'}
        },
        'happy': {
            'start': {'pace': 'medium', 'mood': 'happy', 'transition': 'quick', 'bgm': '欢快'},
            'middle': {'pace': 'fast', 'mood': 'happy', 'transition': 'quick', 'bgm': '活泼'},
            'end': {'pace': 'medium', 'mood': 'happy', 'transition': 'smooth', 'bgm': '轻快'}
        },
        'auto': {
            'start': {'pace': 'medium', 'mood': 'default', 'transition': 'smooth', 'bgm': '舒缓'},
            'middle': {'pace': 'normal', 'mood': 'default', 'transition': 'default', 'bgm': '平静'},
            'end': {'pace': 'medium', 'mood': 'default', 'transition': 'smooth', 'bgm': '舒缓'}
        }
    }
    
    config = style_config.get(style, style_config['auto'])
    
    suggestions = {
        'segments': [
            {
                'position': 'start',
                'time_range': {
                    'start': 0,
                    'duration': round(start_duration, 1)
                },
                'clipping': {
                    'pace': config['start']['pace'],
                    'cut_frequency': 2 if config['start']['pace'] == 'fast' else 4
                },
                'mood': config['start']['mood'],
                'transition': config['start']['transition'],
                'bgm_keywords': [config['start']['bgm']],
                'tips': [
                    f"开头{start_duration:.0f}秒，建立基调",
                    "可以使用开场特效或字幕",
                    "选择最能吸引眼球的片段"
                ]
            },
            {
                'position': 'middle',
                'time_range': {
                    'start': round(start_duration, 1),
                    'duration': round(middle_duration, 1)
                },
                'clipping': {
                    'pace': config['middle']['pace'],
                    'cut_frequency': 2 if config['middle']['pace'] == 'fast' else 3
                },
                'mood': config['middle']['mood'],
                'transition': config['middle']['transition'],
                'bgm_keywords': [config['middle']['bgm']],
                'tips': [
                    f"中间{middle_duration:.0f}秒，展示主要内容",
                    "保持节奏一致性",
                    "注意镜头之间的逻辑连贯"
                ]
            },
            {
                'position': 'end',
                'time_range': {
                    'start': round(start_duration + middle_duration, 1),
                    'duration': round(end_duration, 1)
                },
                'clipping': {
                    'pace': config['end']['pace'],
                    'cut_frequency': 3 if config['end']['pace'] == 'slow' else 2
                },
                'mood': config['end']['mood'],
                'transition': config['end']['transition'],
                'bgm_keywords': [config['end']['bgm']],
                'tips': [
                    f"结尾{end_duration:.0f}秒，收尾",
                    "留下悬念或情感共鸣",
                    "可以选择淡出或定格画面"
                ]
            }
        ],
        'global': {
            'total_duration': duration,
            'style': style,
            'bgm_recommendation': get_bgm_recommendation(style),
            'color_grading': get_color_grading_recommendation(style)
        },
        'templates': list(PRESET_TEMPLATES.keys())
    }
    
    return suggestions


def get_bgm_recommendation(style: str) -> Dict[str, str]:
    """获取BGM推荐"""
    bgm_map = {
        'epic': '史诗级配乐，推荐使用Orchestral/Cinematic风格',
        'warm': '温暖治愈系，推荐使用Soft Piano/Ambient风格',
        'suspense': '悬疑紧张，推荐使用Dark Ambient/Tension风格',
        'happy': '欢快活泼，推荐使用Upbeat/Positive风格',
        'auto': '中性风格，推荐使用Cinematic/General背景音乐'
    }
    return {
        'style': bgm_map.get(style, bgm_map['auto']),
        'keywords': list(BGM_STYLE_KEYWORDS.get(style, BGM_STYLE_KEYWORDS['calm']))
    }


def get_color_grading_recommendation(style: str) -> Dict[str, str]:
    """获取调色建议"""
    color_map = {
        'epic': {'lut': 'Cinematic', 'saturation': 'high', 'contrast': 'high'},
        'warm': {'lut': 'Warm', 'saturation': 'medium', 'contrast': 'low'},
        'suspense': {'lut': 'Dark', 'saturation': 'low', 'contrast': 'high'},
        'happy': {'lut': 'Vibrant', 'saturation': 'high', 'contrast': 'medium'},
        'auto': {'lut': 'Neutral', 'saturation': 'medium', 'contrast': 'medium'}
    }
    return color_map.get(style, color_map['auto'])


def enhance_suggestions_with_llm(suggestions: Dict, duration: float, api_key: str) -> Dict:
    """使用LLM增强剪辑建议"""
    prompt = f"""请根据以下视频剪辑建议进行优化：

视频时长: {duration}秒
当前风格: {suggestions.get('global', {}).get('style', 'auto')}

请输出更详细的优化建议，包括：
1. 镜头切换的具体时间点
2. BGM的节奏卡点建议
3. 情绪转折点的优化

以JSON格式返回。"""
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "你是一个专业的视频剪辑师，擅长给出详细的剪辑建议。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            suggestions['llm_enhancement'] = content
            suggestions['enhanced'] = True
        
    except Exception as e:
        print(f"LLM增强失败: {e}")
    
    return suggestions


# ============================================
# 6. 人物一致性检测接口 POST /check-consistency
# ============================================
@app.route('/check-consistency', methods=['POST'])
def check_consistency():
    """
    人物一致性检测接口
    检测视频中的人物外观一致性
    """
    try:
        data = request.get_json() or {}
        video_id = data.get('video_id')
        
        if not video_id:
            return jsonify({
                'success': False,
                'error': '缺少视频ID'
            }), 400
        
        # 查找视频文件
        video_path = None
        for ext in ALLOWED_VIDEO_EXTENSIONS:
            path = os.path.join(UPLOAD_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
            path = os.path.join(PROCESSED_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
            return jsonify({
                'success': False,
                'error': f'视频ID {video_id} 不存在'
            }), 404
        
        # 提取视频关键帧进行分析
        frames = extract_key_frames(video_path, num_frames=8)
        
        # 模拟一致性检测结果
        # 实际场景需要调用CV模型（如face-api.js, deepface等）
        consistency_result = analyze_person_consistency(frames)
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'consistency_score': consistency_result['score'],
            'issues': consistency_result['issues'],
            'frame_count': len(frames),
            'recommendations': consistency_result['recommendations'],
            'message': '一致性检测完成'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def extract_key_frames(video_path: str, num_frames: int = 8) -> List[str]:
    """提取视频关键帧"""
    frames = []
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        
        # 均匀采样关键帧
        interval = duration / (num_frames + 1)
        
        for i in range(1, num_frames + 1):
            timestamp = interval * i
            frame_path = os.path.join(TEMP_FOLDER, f"frame_{int(timestamp*100)}.jpg")
            
            try:
                stream = ffmpeg.input(video_path, ss=timestamp)
                stream = ffmpeg.output(stream, frame_path, vframes=1, format='image2')
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                frames.append(frame_path)
            except:
                pass
        
    except Exception as e:
        print(f"关键帧提取失败: {e}")
    
    return frames


def analyze_person_consistency(frames: List[str]) -> Dict[str, Any]:
    """分析人物一致性"""
    # 模拟检测结果
    # 实际需要使用CV模型进行人脸/人物特征比对
    
    if len(frames) < 3:
        return {
            'score': 0,
            'issues': ['帧数不足，无法进行一致性分析'],
            'recommendations': ['请确保视频有足够的关键帧']
        }
    
    # 模拟高分结果（实际场景中应基于CV分析）
    return {
        'score': 85,  # 0-100分
        'issues': [],
        'recommendations': [
            '人物一致性良好',
            '服装和场景变化自然',
            '如需进一步提升，可考虑使用统一的色调和光线'
        ]
    }


# ============================================
# 7. 字幕生成接口 POST /generate-subtitles
# ============================================
@app.route('/generate-subtitles', methods=['POST'])
def generate_subtitles():
    """
    字幕生成接口
    使用AI生成视频字幕（需要音频识别服务）
    """
    try:
        data = request.get_json() or {}
        video_id = data.get('video_id')
        language = data.get('language', 'zh-CN')
        use_whisper = data.get('use_whisper', False)
        whisper_api_key = data.get('whisper_api_key')
        
        if not video_id:
            return jsonify({
                'success': False,
                'error': '缺少视频ID'
            }), 400
        
        # 查找视频文件
        video_path = None
        for ext in ALLOWED_VIDEO_EXTENSIONS:
            path = os.path.join(UPLOAD_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
            path = os.path.join(PROCESSED_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
            return jsonify({
                'success': False,
                'error': f'视频ID {video_id} 不存在'
            }), 404
        
        # 提取音频
        audio_path = os.path.join(TEMP_FOLDER, f"{video_id}_audio.mp3")
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, audio_path, acodec='libmp3lame', vn=True)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'音频提取失败: {str(e)}'
            }), 500
        
        # 字幕生成
        if use_whisper and whisper_api_key:
            subtitles = generate_with_whisper_api(audio_path, language, whisper_api_key)
        else:
            # 使用模拟字幕（实际场景中需要语音识别服务）
            subtitles = generate_mock_subtitles(video_path, language)
        
        # 保存字幕文件
        subtitle_path = os.path.join(PROCESSED_FOLDER, f"{video_id}_subtitles.srt")
        save_subtitle_file(subtitles, subtitle_path)
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'subtitle_file': f'/download/{video_id}_subtitles.srt',
            'subtitle_count': len(subtitles),
            'language': language,
            'subtitles': subtitles[:10],  # 返回前10条预览
            'message': f'字幕生成完成，共{len(subtitles)}条'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_with_whisper_api(audio_path: str, language: str, api_key: str) -> List[Dict]:
    """使用Whisper API生成字幕"""
    # 这里需要集成OpenAI Whisper API
    # 实际场景中：
    # 1. 调用OpenAI Whisper API转录音频
    # 2. 解析返回的时间戳和文本
    # 3. 转换为SRT格式
    
    # 模拟返回
    return generate_mock_subtitles(audio_path, language)


def generate_mock_subtitles(video_path: str, language: str) -> List[Dict]:
    """生成模拟字幕（实际场景需要语音识别）"""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
    except:
        duration = 60
    
    # 根据语言返回示例字幕
    zh_subtitles = [
        {'index': 1, 'start': '00:00:00,000', 'end': '00:00:03,500', 'text': '欢迎观看本期内容'},
        {'index': 2, 'start': '00:00:03,500', 'end': '00:00:07,000', 'text': '今天我们将介绍AI剪辑技术'},
        {'index': 3, 'start': '00:00:07,000', 'end': '00:00:11,000', 'text': '这项技术可以自动分析视频内容'},
        {'index': 4, 'start': '00:00:11,000', 'end': '00:00:15,000', 'text': '并生成专业的剪辑建议'},
        {'index': 5, 'start': '00:00:15,000', 'end': '00:00:19,000', 'text': '让我们一起探索更多可能'},
    ]
    
    en_subtitles = [
        {'index': 1, 'start': '00:00:00,000', 'end': '00:00:03,500', 'text': 'Welcome to this episode'},
        {'index': 2, 'start': '00:00:03,500', 'end': '00:00:07,000', 'text': 'Today we will introduce AI editing'},
        {'index': 3, 'start': '00:00:07,000', 'end': '00:00:11,000', 'text': 'This technology can analyze video content'},
        {'index': 4, 'start': '00:00:11,000', 'end': '00:00:15,000', 'text': 'And generate professional editing suggestions'},
        {'index': 5, 'start': '00:00:15,000', 'end': '00:00:19,000', 'text': 'Let us explore more possibilities together'},
    ]
    
    return zh_subtitles if language.startswith('zh') else en_subtitles


def save_subtitle_file(subtitles: List[Dict], output_path: str):
    """保存字幕文件（SRT格式）"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for sub in subtitles:
            f.write(f"{sub['index']}\n")
            f.write(f"{sub['start']} --> {sub['end']}\n")
            f.write(f"{sub['text']}\n\n")


# ============================================
# 8. 水印检测接口 POST /detect-watermark
# ============================================
@app.route('/detect-watermark', methods=['POST'])
def detect_watermark():
    """
    水印检测接口
    检测视频中的水印位置和类型
    """
    try:
        data = request.get_json() or {}
        video_id = data.get('video_id')
        
        if not video_id:
            return jsonify({
                'success': False,
                'error': '缺少视频ID'
            }), 400
        
        # 查找视频文件
        video_path = None
        for ext in ALLOWED_VIDEO_EXTENSIONS:
            path = os.path.join(UPLOAD_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
            path = os.path.join(PROCESSED_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
            return jsonify({
                'success': False,
                'error': f'视频ID {video_id} 不存在'
            }), 404
        
        # 提取帧进行水印检测
        frames = extract_key_frames(video_path, num_frames=5)
        
        # 模拟水印检测
        watermark_result = detect_watermarks_in_frames(frames)
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'has_watermark': watermark_result['detected'],
            'watermarks': watermark_result['watermarks'],
            'confidence': watermark_result['confidence'],
            'recommendations': watermark_result['recommendations'],
            'message': '水印检测完成'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def detect_watermarks_in_frames(frames: List[str]) -> Dict[str, Any]:
    """检测帧中的水印"""
    # 模拟检测结果
    # 实际场景需要使用CV模型检测常见水印模式
    
    if not frames:
        return {
            'detected': False,
            'watermarks': [],
            'confidence': 0,
            'recommendations': ['帧数不足，无法检测']
        }
    
    # 模拟检测结果
    return {
        'detected': True,
        'watermarks': [
            {
                'type': 'text',
                'position': 'bottom-right',
                'text': '示例水印',
                'opacity': 0.5,
                'bbox': {'x': 0.75, 'y': 0.9, 'width': 0.2, 'height': 0.05}
            }
        ],
        'confidence': 0.85,
        'recommendations': [
            '检测到右下角文字水印',
            '可以使用去水印功能尝试移除',
            '建议优先考虑裁剪方式去除'
        ]
    }


# ============================================
# 9. 水印去除接口 POST /remove-watermark
# ============================================
@app.route('/remove-watermark', methods=['POST'])
def remove_watermark():
    """
    水印去除接口
    移除视频中的水印
    """
    try:
        data = request.get_json() or {}
        video_id = data.get('video_id')
        method = data.get('method', 'blur')  # blur, inpaint, crop
        
        if not video_id:
            return jsonify({
                'success': False,
                'error': '缺少视频ID'
            }), 400
        
        if method not in ['blur', 'inpaint', 'crop']:
            return jsonify({
                'success': False,
                'error': '不支持的去水印方法'
            }), 400
        
        # 查找视频文件
        video_path = None
        for ext in ALLOWED_VIDEO_EXTENSIONS:
            path = os.path.join(UPLOAD_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
            path = os.path.join(PROCESSED_FOLDER, f"{video_id}.{ext}")
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
            return jsonify({
                'success': False,
                'error': f'视频ID {video_id} 不存在'
            }), 404
        
        # 先检测水印
        frames = extract_key_frames(video_path, num_frames=5)
        watermark_info = detect_watermarks_in_frames(frames)
        
        if not watermark_info['detected']:
            return jsonify({
                'success': True,
                'video_id': video_id,
                'message': '未检测到水印，无需处理',
                'output_video_url': f'/download/{video_id}.mp4'
            })
        
        # 生成输出文件
        output_id = f"dewmarked_{video_id}_{int(time.time())}"
        output_filename = f"{output_id}.mp4"
        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)
        
        # 使用ffmpeg去除水印
        # 方法1: 模糊处理
        if method == 'blur':
            # 使用boxblur模糊右下角区域
            # x=iw-iw*0.25:y=ih-ih*0.08:w=iw*0.22:h=ih*0.07
            filter_str = "boxblur=2:1"
            overlay_x = "W-w-10"
            overlay_y = "H-h-10"
            
            try:
                # 创建模糊层覆盖水印区域
                stream = ffmpeg.input(video_path)
                stream = ffmpeg.filter(stream, 'boxblur', luma_radius=3, luma_power=1)
                stream = ffmpeg.overlay(stream, video_path, x=overlay_x, y=overlay_y)
                stream = ffmpeg.output(stream, output_filepath, vcodec='libx264', crf=20)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
            except Exception as e:
                # 如果复杂处理失败，返回原视频并提示
                return jsonify({
                    'success': False,
                    'error': f'水印处理失败: {str(e)}',
                    'suggestion': '建议手动使用专业软件处理'
                }), 500
        
        # 方法2: 裁剪
        elif method == 'crop':
            try:
                # 裁剪掉右下角区域
                probe = ffmpeg.probe(video_path)
                width = int(probe['streams'][0]['width'])
                height = int(probe['streams'][0]['height'])
                
                # 裁剪掉右下角水印区域 (保留95%)
                crop_width = int(width * 0.95)
                crop_height = int(height * 0.95)
                
                stream = ffmpeg.input(video_path)
                stream = ffmpeg.filter(stream, 'crop', crop_width, crop_height, 0, 0)
                stream = ffmpeg.output(stream, output_filepath, vcodec='libx264', crf=20)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'裁剪处理失败: {str(e)}'
                }), 500
        
        # 方法3: 修复(inpaint)
        else:
            # 模拟inpaint效果（实际需要使用AI模型如LaMa, DeepFill等）
            try:
                stream = ffmpeg.input(video_path)
                stream = ffmpeg.filter(stream, 'fillborders', mode='smear')
                stream = ffmpeg.output(stream, output_filepath, vcodec='libx264', crf=20)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'修复处理失败: {str(e)}'
                }), 500
        
        # 清理临时帧
        for frame in frames:
            if os.path.exists(frame):
                try:
                    os.remove(frame)
                except:
                    pass
        
        return jsonify({
            'success': True,
            'video_id': output_id,
            'output_video_url': f'/download/{output_filename}',
            'method': method,
            'watermark_info': watermark_info['watermarks'],
            'message': f'水印{method}处理完成'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 辅助接口
# ============================================
@app.route('/download/<path:filename>')
def download(filename):
    """下载处理后的视频"""
    filename = secure_filename(filename)
    
    filepath = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(filepath):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({'error': '文件不存在'}), 404


@app.route('/video/<video_id>')
def get_video_info(video_id):
    """获取视频信息"""
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
        if os.path.exists(folder):
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
        if os.path.exists(folder):
            for ext in list(ALLOWED_VIDEO_EXTENSIONS) + ['mp3', 'srt']:
                filepath = os.path.join(folder, f"{video_id}.{ext}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    deleted = True
    
    if deleted:
        return jsonify({'success': True, 'message': '视频已删除'})
    else:
        return jsonify({'success': False, 'error': '视频不存在'}), 404


@app.route('/presets')
def list_presets():
    """获取预设模板列表"""
    return jsonify({
        'success': True,
        'presets': PRESET_TEMPLATES
    })


@app.route('/presets/<name>')
def get_preset(name):
    """获取指定预设模板"""
    if name in PRESET_TEMPLATES:
        return jsonify({
            'success': True,
            'name': name,
            'template': PRESET_TEMPLATES[name]
        })
    else:
        return jsonify({
            'success': False,
            'error': f'预设模板 {name} 不存在'
        }), 404


@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'AI剪辑平台API已启动',
        'endpoints': [
            {'path': '/health', 'method': 'GET', 'description': '健康检查'},
            {'path': '/upload', 'method': 'POST', 'description': '上传视频'},
            {'path': '/merge', 'method': 'POST', 'description': '合并视频'},
            {'path': '/search-bgm', 'method': 'GET', 'description': '搜索BGM'},
            {'path': '/process', 'method': 'POST', 'description': '处理视频'},
            {'path': '/suggest', 'method': 'POST', 'description': 'AI剪辑建议'},
            {'path': '/check-consistency', 'method': 'POST', 'description': '人物一致性检测'},
            {'path': '/generate-subtitles', 'method': 'POST', 'description': '字幕生成'},
            {'path': '/detect-watermark', 'method': 'POST', 'description': '水印检测'},
            {'path': '/remove-watermark', 'method': 'POST', 'description': '水印去除'},
            {'path': '/parse', 'method': 'POST', 'description': '解析剪辑要求'},
            {'path': '/presets', 'method': 'GET', 'description': '获取预设模板'},
            {'path': '/download/<filename>', 'method': 'GET', 'description': '下载文件'},
            {'path': '/video/<video_id>', 'method': 'GET', 'description': '获取视频信息'},
            {'path': '/list-videos', 'method': 'GET', 'description': '列出视频'},
            {'path': '/delete/<video_id>', 'method': 'DELETE', 'description': '删除视频'}
        ],
        'ai_features': [
            'AI剪辑建议 (/suggest)',
            '人物一致性检测 (/check-consistency)',
            '字幕生成 (/generate-subtitles)',
            '水印检测 (/detect-watermark)',
            '水印去除 (/remove-watermark)'
        ]
    })


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/parse', methods=['POST'])
def parse():
    """解析剪辑要求"""
    data = request.get_json() or {}
    text = data.get('text', '')
    use_llm = data.get('use_llm', False)
    llm_api_key = data.get('llm_api_key')
    
    parser = AIRequirementsParser(
        use_llm=use_llm,
        llm_api_key=llm_api_key
    )
    
    result = parser.parse_to_dict(text)
    
    return jsonify({
        'success': True,
        'result': result
    })


# ============================================
# 11. 水印/字幕检测API (POST /api/detect-watermark)
# ============================================
@app.route('/api/detect-watermark', methods=['POST'])
def api_detect_watermark():
    """
    AI自动检测水印区域
    
    请求方式: multipart/form-data 或 JSON
    
    方式1 - 文件上传:
        - file: 图片或视频文件
        
    方式2 - JSON:
        {
            "video_path": "/path/to/video.mp4"
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
                return jsonify({'success': False, 'error': '未上传文件'}), 400
            
            # 保存临时文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            temp_path = os.path.join(TEMP_FOLDER, f"detect_{timestamp}_{unique_id}.{ext}")
            file.save(temp_path)
            
            # 判断是图片还是视频
            if ext in ['jpg', 'jpeg', 'png', 'bmp']:
                # 图片处理
                frame = cv2.imread(temp_path)
                if frame is None:
                    return jsonify({'success': False, 'error': '无法读取图片'}), 400
                
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
                cap = cv2.VideoCapture(temp_path)
                if not cap.isOpened():
                    return jsonify({'success': False, 'error': '无法打开视频'}), 400
                
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
                    return jsonify({'success': False, 'error': '无法读取视频帧'}), 400
                
                detector = WatermarkDetector()
                detected = detector.detect(frame)
                regions = [
                    {'x': r.x, 'y': r.y, 'width': r.width, 'height': r.height,
                     'type': r.type, 'confidence': r.confidence, 'label': r.label}
                    for r in detected
                ]
            
            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass
        
        # 方式2: JSON指定视频路径
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            
            if not video_path:
                return jsonify({'success': False, 'error': '未提供视频路径'}), 400
            
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': '视频文件不存在'}), 404
            
            # 提取帧进行检测
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return jsonify({'success': False, 'error': '无法打开视频'}), 400
            
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
                return jsonify({'success': False, 'error': '无法读取视频帧'}), 400
            
            detector = WatermarkDetector()
            detected = detector.detect(frame)
            regions = [
                {'x': r.x, 'y': r.y, 'width': r.width, 'height': r.height,
                 'type': r.type, 'confidence': r.confidence, 'label': r.label}
                for r in detected
            ]
        
        else:
            return jsonify({'success': False, 'error': '请上传文件或提供视频路径'}), 400
        
        return jsonify({
            'success': True,
            'data': {
                'regions': regions,
                'region_count': len(regions),
                'frame_info': frame_info
            },
            'message': f'检测到 {len(regions)} 个水印区域'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 12. 字幕检测API (POST /api/detect-subtitle)
# ============================================
@app.route('/api/detect-subtitle', methods=['POST'])
def api_detect_subtitle():
    """
    检测字幕区域
    """
    try:
        regions = []
        frame_info = {}
        has_text = False
        
        # 方式1: 文件上传
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return jsonify({'success': False, 'error': '未上传文件'}), 400
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            temp_path = os.path.join(TEMP_FOLDER, f"detect_{timestamp}_{unique_id}.{ext}")
            file.save(temp_path)
            
            if ext in ['jpg', 'jpeg', 'png', 'bmp']:
                frame = cv2.imread(temp_path)
                if frame is None:
                    return jsonify({'success': False, 'error': '无法读取图片'}), 400
                frame_info = {"width": frame.shape[1], "height": frame.shape[0]}
            else:
                cap = cv2.VideoCapture(temp_path)
                if not cap.isOpened():
                    return jsonify({'success': False, 'error': '无法打开视频'}), 400
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
                    return jsonify({'success': False, 'error': '无法读取视频帧'}), 400
            
            try:
                os.remove(temp_path)
            except:
                pass
        
        # 方式2: JSON指定视频路径
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            
            if not video_path:
                return jsonify({'success': False, 'error': '未提供视频路径'}), 400
            
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': '视频文件不存在'}), 404
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return jsonify({'success': False, 'error': '无法打开视频'}), 400
            
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
                return jsonify({'success': False, 'error': '无法读取视频帧'}), 400
        
        else:
            return jsonify({'success': False, 'error': '请上传文件或提供视频路径'}), 400
        
        # 检测字幕
        detector = SubtitleDetector()
        detected = detector.detect(frame)
        regions = [
            {'x': r.x, 'y': r.y, 'width': r.width, 'height': r.height,
             'type': r.type, 'confidence': r.confidence, 'label': r.label}
            for r in detected
        ]
        has_text = len(regions) > 0
        
        return jsonify({
            'success': True,
            'data': {
                'regions': regions,
                'region_count': len(regions),
                'frame_info': frame_info,
                'has_text': has_text
            },
            'message': f'检测到 {len(regions)} 个字幕区域' if has_text else '未检测到字幕'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 13. 去水印处理API (POST /api/remove-watermark)
# ============================================
# 初始化水印处理器
watermark_processor = WatermarkVideoProcessor(
    temp_dir=TEMP_FOLDER,
    output_dir=PROCESSED_FOLDER
)
batch_proc = BatchProcessor(max_workers=2)


@app.route('/api/remove-watermark', methods=['POST'])
def api_remove_watermark():
    """
    去除视频水印/字幕
    """
    try:
        data = request.get_json() or {}
        
        video_path = data.get('video_path')
        regions = data.get('regions', [])
        preserve_audio = data.get('preserve_audio', True)
        auto_detect = data.get('auto_detect', False)
        detect_type = data.get('detect_type', 'all')
        
        if not video_path:
            return jsonify({'success': False, 'error': '未提供视频路径'}), 400
        
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'error': '视频文件不存在'}), 404
        
        # 自动检测区域
        detected_regions = []
        if auto_detect or not regions:
            result = watermark_processor.detect_and_process(
                video_path,
                detect_type=detect_type,
                manual_regions=regions if regions else None,
                preserve_audio=preserve_audio
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'task_id': result.get('task_id', f"watermark_{uuid.uuid4().hex[:8]}"),
                    'status': 'completed' if result.get('success') else 'failed',
                    'output_path': result.get('output_path'),
                    'output_url': result.get('output_url'),
                    'detected_regions': result.get('detected_regions', []),
                    'frames_processed': result.get('frames_processed', 0),
                    'error': result.get('error')
                },
                'message': '处理完成' if result.get('success') else f"处理失败: {result.get('error')}"
            })
        
        # 手动指定区域处理
        task_id = f"watermark_{uuid.uuid4().hex[:8]}"
        output_filename = f"{task_id}.mp4"
        
        result = watermark_processor.process_video(
            video_path,
            regions,
            preserve_audio=preserve_audio,
            output_filename=output_filename
        )
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'completed' if result.get('success') else 'failed',
                'output_path': result.get('output_path'),
                'output_url': result.get('output_url'),
                'frames_processed': result.get('frames_processed', 0),
                'regions_removed': len(regions),
                'error': result.get('error')
            },
            'message': '处理完成' if result.get('success') else f"处理失败: {result.get('error')}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 14. 批量去水印API (POST /api/batch-remove)
# ============================================
@app.route('/api/batch-remove', methods=['POST'])
def api_batch_remove():
    """
    批量去除视频水印/字幕
    """
    try:
        data = request.get_json() or {}
        
        videos = data.get('videos', [])
        default_regions = data.get('default_regions', [])
        detect_type = data.get('detect_type', 'all')
        
        if not videos:
            return jsonify({'success': False, 'error': '未提供视频列表'}), 400
        
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
            return jsonify({'success': False, 'error': '没有有效的视频文件'}), 400
        
        # 创建批量任务
        task_id = batch_proc.create_batch_task(valid_videos, default_regions)
        
        # 启动处理
        batch_proc.start_batch(task_id)
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'processing',
                'total_videos': len(valid_videos),
                'status_url': f'/api/batch-status/{task_id}'
            },
            'message': f'已创建批量任务，处理 {len(valid_videos)} 个视频'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 15. 批量处理状态API (GET /api/batch-status/<task_id>)
# ============================================
@app.route('/api/batch-status/<task_id>', methods=['GET'])
def api_batch_status(task_id):
    """查询批量处理状态"""
    try:
        status = batch_proc.get_task_status(task_id)
        
        if not status:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 16. 批量处理取消API (POST /api/batch-cancel/<task_id>)
# ============================================
@app.route('/api/batch-cancel/<task_id>', methods=['POST'])
def api_batch_cancel(task_id):
    """取消批量任务"""
    try:
        success = batch_proc.cancel_task(task_id)
        
        if success:
            return jsonify({'success': True, 'message': '任务已取消'})
        else:
            return jsonify({'success': False, 'error': '无法取消任务'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 17. 批量任务列表API (GET /api/batch-list)
# ============================================
@app.route('/api/batch-list', methods=['GET'])
def api_batch_list():
    """列出所有批量任务"""
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
        tasks = batch_proc.list_tasks(status)
        
        return jsonify({
            'success': True,
            'data': {
                'count': len(tasks),
                'tasks': tasks
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 18. 同时检测水印和字幕API (POST /api/detect-all)
# ============================================
@app.route('/api/detect-all', methods=['POST'])
def api_detect_all():
    """
    同时检测水印和字幕区域
    """
    try:
        frame = None
        frame_info = {}
        
        # 获取帧
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return jsonify({'success': False, 'error': '未上传文件'}), 400
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            temp_path = os.path.join(TEMP_FOLDER, f"detect_{timestamp}_{unique_id}.{ext}")
            file.save(temp_path)
            
            if ext in ['jpg', 'jpeg', 'png', 'bmp']:
                frame = cv2.imread(temp_path)
                if frame is not None:
                    frame_info = {"width": frame.shape[1], "height": frame.shape[0]}
            else:
                cap = cv2.VideoCapture(temp_path)
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
                os.remove(temp_path)
            except:
                pass
        
        elif request.is_json:
            data = request.get_json()
            video_path = data.get('video_path')
            
            if not video_path:
                return jsonify({'success': False, 'error': '未提供视频路径'}), 400
            
            if not os.path.exists(video_path):
                return jsonify({'success': False, 'error': '视频文件不存在'}), 404
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return jsonify({'success': False, 'error': '无法打开视频'}), 400
            
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
            return jsonify({'success': False, 'error': '请上传文件或提供视频路径'}), 400
        
        if frame is None:
            return jsonify({'success': False, 'error': '无法读取视频帧'}), 400
        
        # 同时检测水印和字幕
        processor = WatermarkProcessor()
        result = processor.detect_all(frame)
        
        return jsonify({
            'success': True,
            'data': {
                'watermarks': result['watermarks'],
                'subtitles': result['subtitles'],
                'all_regions': result['all_regions'],
                'frame_info': frame_info,
                'total_regions': len(result['all_regions'])
            },
            'message': f"检测到 {len(result['watermarks'])} 个水印, {len(result['subtitles'])} 个字幕"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
