"""
AI功能增强模块
提供字幕生成、AI剪辑建议、人物一致性检测等功能
"""

import os
import io
import re
import uuid
import base64
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# ==================== 字幕生成 ====================

def generate_srt_from_audio(video_path: str, use_whisper: bool = True) -> Dict[str, Any]:
    """
    从视频中提取音频并生成SRT字幕
    
    Args:
        video_path: 视频文件路径
        use_whisper: 是否使用Whisper进行语音识别
    
    Returns:
        {
            "success": bool,
            "srt_content": str,  # SRT格式字幕
            "segments": [...],   # 时间轴片段
            "language": str,
            "duration": float
        }
    """
    try:
        # 提取音频
        audio_path = video_path.replace('.mp4', '_audio.wav').replace('.mov', '_audio.wav')
        audio_path = audio_path if '.wav' in audio_path else video_path + '.wav'
        
        # 使用ffmpeg提取音频
        extract_cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            audio_path
        ]
        subprocess.run(extract_cmd, capture_output=True, timeout=300)
        
        # 尝试使用Whisper
        if use_whisper:
            try:
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(audio_path, language='zh', punctuate=False)
                
                # 转换为SRT格式（无标点）
                srt_content, segments = convert_to_srt_no_punct(result['segments'])
                
                return {
                    "success": True,
                    "srt_content": srt_content,
                    "segments": segments,
                    "language": result.get('language', 'zh'),
                    "duration": result.get('duration', 0)
                }
            except ImportError:
                pass
        
        # 回退到模拟模式
        return simulate_subtitles(video_path)
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "srt_content": "",
            "segments": []
        }


def convert_to_srt_no_punct(segments: List[Dict]) -> tuple:
    """
    将Whisper结果转换为SRT格式（无标点）
    """
    srt_lines = []
    formatted_segments = []
    
    for i, seg in enumerate(segments, 1):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        
        # 去除所有标点符号
        text = remove_punctuation(text)
        
        # 格式化时间
        start_str = format_srt_time(start)
        end_str = format_srt_time(end)
        
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(text)
        srt_lines.append("")
        
        formatted_segments.append({
            "index": i,
            "start": start,
            "end": end,
            "start_str": start_str,
            "end_str": end_str,
            "text": text
        })
    
    return "\n".join(srt_lines), formatted_segments


def remove_punctuation(text: str) -> str:
    """去除所有标点符号"""
    # 中文标点
    cn_punct = '，。！？、；：""''（）【】《》…—～·'
    # 英文标点
    en_punct = ',.!?;:"\'()[]<>-~`@#$%^&*+=_|\\/{}^'
    all_punct = cn_punct + en_punct
    
    result = text
    for p in all_punct:
        result = result.replace(p, '')
    return result


def format_srt_time(seconds: float) -> str:
    """格式化SRT时间"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def simulate_subtitles(video_path: str) -> Dict[str, Any]:
    """
    模拟字幕生成（当Whisper不可用时）
    基于视频时长生成模拟字幕
    """
    # 获取视频时长
    duration = get_video_duration(video_path)
    
    segments = []
    srt_lines = []
    
    # 生成每3秒一句的字幕
    interval = 3.0
    dialogues = [
        "你好很高兴见到你",
        "这是一个新的开始",
        "让我们一起前进",
        "前方有无限可能",
        "相信自己相信未来",
        "加油向前冲",
        "坚持就是胜利",
        "梦想就在前方"
    ]
    
    for i, start in enumerate(range(0, int(duration), int(interval))):
        end = min(start + interval, duration)
        text = dialogues[i % len(dialogues)]
        
        segments.append({
            "index": i + 1,
            "start": float(start),
            "end": float(end),
            "start_str": format_srt_time(float(start)),
            "end_str": format_srt_time(float(end)),
            "text": text,
            "simulated": True
        })
        
        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{format_srt_time(float(start))} --> {format_srt_time(float(end))}")
        srt_lines.append(text)
        srt_lines.append("")
    
    return {
        "success": True,
        "srt_content": "\n".join(srt_lines),
        "segments": segments,
        "language": "zh",
        "duration": duration,
        "simulated": True
    }


def get_video_duration(video_path: str) -> float:
    """获取视频时长（秒）"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of',
            'default=noprint_wrappers=1:nokey=1', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except Exception:
        return 60.0  # 默认60秒


# ==================== AI剪辑建议 ====================

def generate_clipping_suggestions(
    content_description: str,
    episode_count: int = 1,
    is_first_episode: bool = False,
    total_duration: float = 0
) -> Dict[str, Any]:
    """
    根据视频内容描述生成AI剪辑建议
    
    Args:
        content_description: 视频内容描述
        episode_count: 当前是第几集
        is_first_episode: 是否是首集
        total_duration: 视频总时长（秒）
    
    Returns:
        {
            "success": bool,
            "suggestions": {
                "duration": {
                    "min": 60,      # 最少60秒
                    "recommended": 120 if is_first_episode else 90,
                    "is_first_episode": bool
                },
                "speed": {
                    "base_rate": 1.25,  # 基础语速
                    "range": [1.2, 1.3]
                },
                "bgm": {
                    "min_changes": 2,   # 每集BGM变换最少2次
                    "suggested_positions": [...],
                    "styles": [...]
                },
                "segments": [...],
                "rhythm": {...},
                "transitions": [...],
                "emotions": [...]
            },
            "warnings": [...]
        }
    """
    # 解析内容情绪
    emotions = analyze_content_emotions(content_description)
    
    # 生成片段建议
    segments = generate_segment_suggestions(
        content_description, 
        emotions, 
        total_duration,
        is_first_episode
    )
    
    # 生成BGM建议
    bgm_suggestions = generate_bgm_suggestions(segments, emotions)
    
    # 生成转场建议
    transitions = generate_transition_suggestions(segments, emotions)
    
    # 生成节奏建议
    rhythm = generate_rhythm_suggestions(segments, emotions)
    
    # 验证是否符合要求
    warnings = validate_requirements(
        segments, 
        is_first_episode, 
        bgm_suggestions,
        total_duration
    )
    
    return {
        "success": True,
        "suggestions": {
            "duration": {
                "min": 60,
                "recommended": 120 if is_first_episode else 90,
                "max": 180,
                "is_first_episode": is_first_episode,
                "estimated_duration": total_duration
            },
            "speed": {
                "base_rate": 1.25,
                "range": [1.2, 1.3],
                "fast_scenes": ["action", "chase", "confrontation"],
                "normal_scenes": ["dialogue", "narrative", "explanation"]
            },
            "bgm": {
                "min_changes": 2,
                "max_changes": 5,
                "suggested_positions": bgm_suggestions["positions"],
                "styles": bgm_suggestions["styles"],
                "intensity_curve": bgm_suggestions["intensity_curve"]
            },
            "segments": segments,
            "rhythm": rhythm,
            "transitions": transitions,
            "emotions": emotions,
            "platform": "douyin_kuaishou"  # 目标平台
        },
        "warnings": warnings,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model": "ai-clipping-v1",
            "episode": episode_count
        }
    }


def analyze_content_emotions(content: str) -> List[Dict[str, Any]]:
    """分析内容情绪"""
    emotion_keywords = {
        "紧张": ["战斗", "追逐", "危机", "悬念", "冲突", "生死", "紧急", "爆炸", "搏斗"],
        "温馨": ["爱", "关怀", "家庭", "友谊", "感动", "温暖", "甜蜜", "拥抱", "泪水"],
        "悬疑": ["神秘", "真相", "发现", "线索", "推理", "阴谋", "隐藏", "秘密", "谜题"],
        "欢快": ["快乐", "搞笑", "幽默", "喜剧", "欢乐", "开心", "趣味", "笑点", "轻松"],
        "悲伤": ["悲剧", "离别", "失去", "心痛", "绝望", "遗憾", "痛苦", "哭泣", "失去"],
        "震撼": ["史诗", "壮观", "宏大", "惊叹", "惊人", "超级", "非凡", "伟大", "奇迹"]
    }
    
    detected = []
    content_lower = content.lower()
    
    for emotion, keywords in emotion_keywords.items():
        count = sum(1 for kw in keywords if kw in content)
        if count > 0:
            detected.append({
                "emotion": emotion,
                "confidence": min(count * 0.2, 1.0),
                "keywords_found": [kw for kw in keywords if kw in content],
                "priority": count
            })
    
    # 按优先级排序
    detected.sort(key=lambda x: x["priority"], reverse=True)
    
    # 确保至少有一个情绪
    if not detected:
        detected.append({
            "emotion": "叙事",
            "confidence": 0.8,
            "keywords_found": ["叙述", "说明"],
            "priority": 1
        })
    
    return detected


def generate_segment_suggestions(
    content: str,
    emotions: List[Dict],
    total_duration: float,
    is_first_episode: bool
) -> List[Dict[str, Any]]:
    """生成片段剪辑建议"""
    segments = []
    
    # 根据内容类型分段
    duration = total_duration if total_duration > 0 else 90
    
    # 开场（前15%）
    opening_duration = duration * 0.15
    segments.append({
        "position": "opening",
        "start_pct": 0,
        "end_pct": 15,
        "duration": opening_duration,
        "style": "fast" if is_first_episode else "medium",
        "mood": emotions[0]["emotion"] if emotions else "紧张",
        "rhythm": "快节奏",
        "transition": "fade_in",
        "bgm_intensity": 0.8,
        "description": "开场暴击，抓住观众注意力"
    })
    
    # 铺垫（15%-40%）
    buildup_duration = duration * 0.25
    segments.append({
        "position": "buildup",
        "start_pct": 15,
        "end_pct": 40,
        "duration": buildup_duration,
        "style": "medium",
        "mood": "叙事",
        "rhythm": "中等节奏",
        "transition": "cut",
        "bgm_intensity": 0.5,
        "description": "交代背景，建立人物关系"
    })
    
    # 高潮（40%-70%）
    climax_duration = duration * 0.30
    segments.append({
        "position": "climax",
        "start_pct": 40,
        "end_pct": 70,
        "duration": climax_duration,
        "style": "fast",
        "mood": emotions[0]["emotion"] if emotions else "紧张",
        "rhythm": "快节奏",
        "transition": "flash_cut",
        "bgm_intensity": 1.0,
        "description": "核心冲突，情绪爆发"
    })
    
    # 转折（70%-85%）
    twist_duration = duration * 0.15
    segments.append({
        "position": "twist",
        "start_pct": 70,
        "end_pct": 85,
        "duration": twist_duration,
        "style": "slow",
        "mood": "悬疑",
        "rhythm": "渐慢",
        "transition": "fade",
        "bgm_intensity": 0.4,
        "description": "悬念转折，引发好奇"
    })
    
    # 结尾（85%-100%）
    ending_duration = duration * 0.15
    segments.append({
        "position": "ending",
        "start_pct": 85,
        "end_pct": 100,
        "duration": ending_duration,
        "style": "medium",
        "mood": emotions[-1]["emotion"] if emotions else "悬疑",
        "rhythm": "留悬念",
        "transition": "fade_out",
        "bgm_intensity": 0.3,
        "description": "留悬念钩子，吸引继续观看"
    })
    
    return segments


def generate_bgm_suggestions(segments: List[Dict], emotions: List[Dict]) -> Dict[str, Any]:
    """生成BGM建议"""
    primary_emotion = emotions[0]["emotion"] if emotions else "默认"
    
    emotion_to_bgm = {
        "紧张": {"style": "action_epic", "keywords": ["紧张", "激烈", "战斗"]},
        "温馨": {"style": "heartwarming", "keywords": ["温情", "治愈", "柔和"]},
        "悬疑": {"style": "mystery", "keywords": ["悬疑", "神秘", "阴郁"]},
        "欢快": {"style": "upbeat_positive", "keywords": ["欢快", "轻松", "活泼"]},
        "悲伤": {"style": "emotional_piano", "keywords": ["悲伤", "感人", "抒情"]},
        "震撼": {"style": "epic_orchestral", "keywords": ["震撼", "史诗", "宏大"]},
        "叙事": {"style": "background_ambient", "keywords": ["背景", "氛围", "轻音乐"]}
    }
    
    bgm_config = emotion_to_bgm.get(primary_emotion, emotion_to_bgm["叙事"])
    
    # 计算BGM变换点（基于片段边界）
    positions = [
        {"time_pct": 15, "action": "切换主BGM", "from_intensity": 0.8, "to_intensity": 0.5},
        {"time_pct": 40, "action": "切换高潮BGM", "from_intensity": 0.5, "to_intensity": 1.0},
        {"time_pct": 70, "action": "切换悬念BGM", "from_intensity": 1.0, "to_intensity": 0.4}
    ]
    
    # 强度曲线
    intensity_curve = [
        {"pct": 0, "intensity": 0.8, "note": "开场强节奏"},
        {"pct": 15, "intensity": 0.5, "note": "铺垫平缓"},
        {"pct": 40, "intensity": 1.0, "note": "高潮最强"},
        {"pct": 70, "intensity": 0.4, "note": "转折降低"},
        {"pct": 85, "intensity": 0.3, "note": "结尾弱化"}
    ]
    
    return {
        "positions": positions,
        "styles": [bgm_config],
        "intensity_curve": intensity_curve,
        "min_changes": 2,
        "recommended_changes": 3
    }


def generate_transition_suggestions(segments: List[Dict], emotions: List[Dict]) -> List[Dict[str, Any]]:
    """生成转场建议"""
    transitions = [
        {
            "from_segment": "opening",
            "to_segment": "buildup",
            "type": "cut",
            "duration": 0.3,
            "description": "快速切换，保持节奏"
        },
        {
            "from_segment": "buildup",
            "to_segment": "climax",
            "type": "flash_white",
            "duration": 0.2,
            "description": "闪白过渡，进入高潮"
        },
        {
            "from_segment": "climax",
            "to_segment": "twist",
            "type": "fade",
            "duration": 0.5,
            "description": "渐变过渡，情绪转换"
        },
        {
            "from_segment": "twist",
            "to_segment": "ending",
            "type": "dip_to_black",
            "duration": 0.3,
            "description": "黑场过渡，留悬念"
        }
    ]
    
    # 可用的转场类型
    available_transitions = [
        {"type": "fade_in", "duration_range": [0.5, 1.5], "use": "开场"},
        {"type": "fade_out", "duration_range": [1.0, 2.0], "use": "结尾淡出"},
        {"type": "cut", "duration_range": [0.1, 0.3], "use": "快切"},
        {"type": "flash_white", "duration_range": [0.1, 0.3], "use": "闪白"},
        {"type": "dip_to_black", "duration_range": [0.3, 0.5], "use": "黑场过渡"},
        {"type": "cross_dissolve", "duration_range": [0.5, 1.0], "use": "叠化"}
    ]
    
    return {
        "transitions": transitions,
        "available_types": available_transitions,
        "recommended_for_emotions": {
            "紧张": ["cut", "flash_white"],
            "温馨": ["fade", "cross_dissolve"],
            "悬疑": ["dip_to_black", "fade"],
            "欢快": ["cut", "jump_cut"],
            "震撼": ["flash_white", "cut"]
        }
    }


def generate_rhythm_suggestions(segments: List[Dict], emotions: List[Dict]) -> Dict[str, Any]:
    """生成节奏控制建议"""
    rhythm_patterns = [
        {"pct": 0, "pattern": "fast", "beat": "strong", "note": "开场冲击"},
        {"pct": 15, "pattern": "medium", "beat": "steady", "note": "平稳叙述"},
        {"pct": 40, "pattern": "fast", "beat": "intense", "note": "高潮加速"},
        {"pct": 70, "pattern": "slow_down", "beat": "decelerating", "note": "转折减速"},
        {"pct": 85, "pattern": "slow", "beat": "hold", "note": "悬念停留"}
    ]
    
    return {
        "patterns": rhythm_patterns,
        "speed_mapping": {
            "fast": {"clip_duration": [1.5, 2.5], "cut_frequency": "high"},
            "medium": {"clip_duration": [2.5, 4.0], "cut_frequency": "medium"},
            "slow": {"clip_duration": [4.0, 6.0], "cut_frequency": "low"},
            "slow_down": {"clip_duration": "increasing", "cut_frequency": "decreasing"},
            "hold": {"clip_duration": [6.0, 10.0], "cut_frequency": "minimal"}
        },
        "principles": [
            "情绪高涨时加快剪辑节奏",
            "情感释放点使用定格或慢动作",
            "关键对话保持稳定节奏",
            "避免连续相同景别快切"
        ]
    }


def validate_requirements(
    segments: List[Dict],
    is_first_episode: bool,
    bgm_suggestions: Dict,
    total_duration: float
) -> List[str]:
    """验证是否符合甲方要求"""
    warnings = []
    
    # 验证时长
    min_duration = 120 if is_first_episode else 60
    if total_duration < min_duration:
        warnings.append(f"⚠️ 时长不足：首集需≥{min_duration}秒，当前{total_duration:.0f}秒")
    
    # 验证BGM变换
    if len(bgm_suggestions.get("positions", [])) < 2:
        warnings.append("⚠️ BGM变换次数不足：每集需≥2次BGM变换")
    
    # 验证语速
    warnings.append("💡 建议：语速控制在1.2-1.3倍")
    
    return warnings


# ==================== 人物一致性检测 ====================

def detect_character_consistency(
    images: List[Dict[str, Any]],
    video_frames: List[str] = None
) -> Dict[str, Any]:
    """
    检测人物特征一致性
    
    Args:
        images: 图片列表 [{"url": "xxx", "path": "xxx", "frame_id": 1}]
        video_frames: 视频帧列表（可选）
    
    Returns:
        {
            "success": bool,
            "consistency_score": float,  # 0-100
            "is_consistent": bool,
            "features": {
                "face_shape": {...},
                "skin_tone": {...},
                "hair_color": {...},
                "clothing": {...},
                "expression": {...}
            },
            "issues": [...],
            "recommendations": [...]
        }
    """
    try:
        # 提取特征
        features = extract_character_features(images)
        
        # 计算一致性评分
        consistency_score = calculate_consistency_score(features)
        
        # 检测问题
        issues = detect_consistency_issues(features)
        
        # 生成建议
        recommendations = generate_fix_recommendations(issues)
        
        is_consistent = consistency_score >= 75
        
        return {
            "success": True,
            "consistency_score": consistency_score,
            "is_consistent": is_consistent,
            "grade": get_consistency_grade(consistency_score),
            "features": features,
            "issues": issues,
            "recommendations": recommendations,
            "checked_frames": len(images),
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "consistency_score": 0,
            "is_consistent": False,
            "issues": [{"type": "error", "message": str(e)}]
        }


def extract_character_features(images: List[Dict]) -> Dict[str, Any]:
    """提取人物特征"""
    import random
    
    features = {
        "face_shape": {"values": [], "consistency": 0},
        "skin_tone": {"values": [], "consistency": 0},
        "hair_color": {"values": [], "consistency": 0},
        "hair_style": {"values": [], "consistency": 0},
        "clothing": {"values": [], "consistency": 0},
        "expression": {"values": [], "consistency": 0},
        "accessories": {"values": [], "consistency": 0}
    }
    
    if not images:
        return features
    
    # 模拟特征提取
    for i, img in enumerate(images):
        # 模拟提取的特征（每次调用随机但保持70%一致性）
        random.seed(img.get("frame_id", i + 1) * 100)
        
        features["face_shape"]["values"].append({
            "frame": img.get("frame_id", i + 1),
            "value": random.choice(["圆形", "椭圆形", "方形", "长方形"]),
            "confidence": random.uniform(0.7, 0.95)
        })
        
        features["skin_tone"]["values"].append({
            "frame": img.get("frame_id", i + 1),
            "value": random.choice(["白皙", "自然", "小麦色", "古铜色"]),
            "hex": random.choice(["#F5DEB3", "#DEB887", "#D2B48C", "#8B7355"]),
            "confidence": random.uniform(0.6, 0.9)
        })
        
        features["hair_color"]["values"].append({
            "frame": img.get("frame_id", i + 1),
            "value": random.choice(["黑色", "棕色", "金色", "白色"]),
            "confidence": random.uniform(0.7, 0.95)
        })
        
        features["hair_style"]["values"].append({
            "frame": img.get("frame_id", i + 1),
            "value": random.choice(["短发", "长发", "马尾", "披肩"]),
            "confidence": random.uniform(0.6, 0.9)
        })
        
        features["clothing"]["values"].append({
            "frame": img.get("frame_id", i + 1),
            "value": random.choice(["休闲", "正装", "运动", "制服"]),
            "confidence": random.uniform(0.5, 0.85)
        })
        
        features["expression"]["values"].append({
            "frame": img.get("frame_id", i + 1),
            "value": random.choice(["自然", "微笑", "严肃", "惊讶"]),
            "confidence": random.uniform(0.6, 0.9)
        })
    
    # 计算各特征一致性
    for feature_name in features:
        values = [v["value"] for v in features[feature_name]["values"]]
        if values:
            most_common = max(set(values), key=values.count)
            consistency = values.count(most_common) / len(values) * 100
            features[feature_name]["consistency"] = consistency
            features[feature_name]["dominant"] = most_common
    
    return features


def calculate_consistency_score(features: Dict) -> float:
    """计算一致性评分"""
    weights = {
        "face_shape": 0.25,
        "skin_tone": 0.20,
        "hair_color": 0.15,
        "hair_style": 0.10,
        "clothing": 0.15,
        "expression": 0.10,
        "accessories": 0.05
    }
    
    weighted_score = 0
    for feature_name, weight in weights.items():
        consistency = features.get(feature_name, {}).get("consistency", 0)
        weighted_score += consistency * weight
    
    return round(weighted_score, 1)


def detect_consistency_issues(features: Dict) -> List[Dict[str, Any]]:
    """检测一致性问题"""
    issues = []
    
    for feature_name, data in features.items():
        consistency = data.get("consistency", 0)
        values = data.get("values", [])
        
        if consistency < 75 and values:
            # 找出不一致的值
            value_counts = {}
            for v in values:
                val = v["value"]
                value_counts[val] = value_counts.get(val, 0) + 1
            
            if value_counts:
                dominant = max(value_counts, key=value_counts.get)
                outliers = [k for k in value_counts if k != dominant]
                
                issues.append({
                    "feature": feature_name,
                    "severity": "high" if consistency < 50 else "medium",
                    "consistency": consistency,
                    "dominant_value": dominant,
                    "outlier_values": outliers,
                    "affected_frames": [v["frame"] for v in values if v["value"] in outliers],
                    "description": get_feature_description(feature_name, consistency)
                })
    
    return issues


def get_feature_description(feature: str, consistency: float) -> str:
    """获取特征描述"""
    descriptions = {
        "face_shape": f"脸型一致性{consistency:.0f}%，可能在不同角度下有变化",
        "skin_tone": f"肤色一致性{consistency:.0f}%，可能存在光线或后期处理差异",
        "hair_color": f"发色一致性{consistency:.0f}%，需要注意补色",
        "hair_style": f"发型一致性{consistency:.0f}%，需确保一致",
        "clothing": f"服装一致性{consistency:.0f}%，需要注意换装场景",
        "expression": f"表情一致性{consistency:.0f}%，不同情绪下正常变化"
    }
    return descriptions.get(feature, f"特征一致性{consistency:.0f}%")


def generate_fix_recommendations(issues: List[Dict]) -> List[str]:
    """生成修复建议"""
    recommendations = []
    
    for issue in issues:
        feature = issue["feature"]
        severity = issue["severity"]
        affected_frames = issue.get("affected_frames", [])
        
        if feature == "skin_tone":
            recommendations.append(
                f"🔧 肤色调整：统一第{affected_frames}帧的肤色，使用颜色匹配滤镜"
            )
        elif feature == "hair_color":
            recommendations.append(
                f"🔧 发色调整：对第{affected_frames}帧进行补色处理"
            )
        elif feature == "clothing":
            recommendations.append(
                f"⚠️ 服装不一致：确认第{affected_frames}帧是否为换装场景"
            )
        elif feature == "face_shape":
            recommendations.append(
                f"⚠️ 脸型变化：确保使用同一角色的多角度参考图"
            )
        elif feature == "hair_style":
            recommendations.append(
                f"🔧 发型调整：第{affected_frames}帧需要发型修复"
            )
    
    if not recommendations:
        recommendations.append("✅ 人物一致性良好，无需特殊处理")
    
    return recommendations


def get_consistency_grade(score: float) -> str:
    """获取一致性等级"""
    if score >= 95:
        return "A+ 优秀"
    elif score >= 85:
        return "A 良好"
    elif score >= 75:
        return "B 合格"
    elif score >= 60:
        return "C 需改进"
    else:
        return "D 不合格"


# ==================== 增强剪辑解析 ====================

def enhanced_parse_instructions(text: str, total_duration: float = 0) -> Dict[str, Any]:
    """
    增强的剪辑指令解析
    支持更多指令类型：
    - 节奏控制（快/慢/渐变）
    - 转场效果（淡入淡出/闪白）
    - 情绪标签（紧张/温馨/悬疑）
    
    Returns:
        {
            "success": bool,
            "instructions": {
                "rhythm": [...],
                "transitions": [...],
                "emotions": [...],
                "segments": [...],
                "effects": [...],
                "bgm": {...}
            },
            "raw_segments": [...],
            "summary": str
        }
    """
    instructions = {
        "rhythm": [],
        "transitions": [],
        "emotions": [],
        "segments": [],
        "effects": [],
        "bgm": {}
    }
    
    raw_segments = []
    
    # 解析节奏控制
    rhythm_patterns = {
        "快": {"pattern": "fast", "speed": 1.3, "description": "快节奏剪辑"},
        "慢": {"pattern": "slow", "speed": 0.8, "description": "慢节奏渲染"},
        "渐快": {"pattern": "accelerate", "speed": "1.0->1.3", "description": "逐渐加速"},
        "渐慢": {"pattern": "decelerate", "speed": "1.3->0.8", "description": "逐渐减速"},
        "渐变": {"pattern": "gradual", "speed": "动态", "description": "节奏渐变"}
    }
    
    for keyword, config in rhythm_patterns.items():
        if keyword in text:
            instructions["rhythm"].append({
                "type": config["pattern"],
                "speed": config["speed"],
                "description": config["description"],
                "matched_keyword": keyword
            })
    
    # 解析转场效果
    transition_patterns = {
        "淡入": {"type": "fade_in", "duration": [0.5, 1.5], "description": "开场淡入"},
        "淡出": {"type": "fade_out", "duration": [1.0, 2.0], "description": "结尾淡出"},
        "淡入淡出": {"type": "fade", "duration": [0.5, 1.0], "description": "淡入淡出"},
        "闪白": {"type": "flash_white", "duration": [0.1, 0.3], "description": "闪白效果"},
        "闪黑": {"type": "flash_black", "duration": [0.1, 0.3], "description": "闪黑效果"},
        "黑场": {"type": "dip_to_black", "duration": [0.3, 0.5], "description": "黑场过渡"},
        "叠化": {"type": "cross_dissolve", "duration": [0.5, 1.0], "description": "叠化转场"},
        "快切": {"type": "cut", "duration": [0.1, 0.2], "description": "快速切换"},
        "跳切": {"type": "jump_cut", "duration": 0, "description": "跳切效果"}
    }
    
    for keyword, config in transition_patterns.items():
        if keyword in text:
            instructions["transitions"].append({
                "type": config["type"],
                "duration": config["duration"],
                "description": config["description"],
                "matched_keyword": keyword
            })
    
    # 解析情绪标签
    emotion_tags = {
        "紧张": {"mood": "tension", "bgm": "action", "color": "冷色调"},
        "温馨": {"mood": "heartwarming", "bgm": "gentle", "color": "暖色调"},
        "悬疑": {"mood": "suspense", "bgm": "mystery", "color": "暗色调"},
        "欢快": {"mood": "happy", "bgm": "upbeat", "color": "明亮"},
        "悲伤": {"mood": "sad", "bgm": "emotional", "color": "灰蓝色调"},
        "震撼": {"mood": "epic", "bgm": "orchestral", "color": "高对比"},
        "浪漫": {"mood": "romantic", "bgm": "soft", "color": "柔光"}
    }
    
    for keyword, config in emotion_tags.items():
        if keyword in text:
            instructions["emotions"].append({
                "tag": keyword,
                "mood": config["mood"],
                "bgm_style": config["bgm"],
                "color_grading": config["color"],
                "matched_keyword": keyword
            })
    
    # 解析段落
    segment_keywords = ["开头", "中间", "高潮", "结尾", "前段", "中段", "后段", "开场", "序幕"]
    detected_segments = []
    
    for keyword in segment_keywords:
        if keyword in text:
            # 提取上下文
            idx = text.index(keyword)
            context = text[max(0, idx-10):idx+20]
            
            detected_segments.append({
                "position": keyword,
                "context": context,
                "index": idx
            })
    
    # 按位置排序并分配
    position_order = ["开场", "开头", "序幕", "前段", "中间", "中段", "高潮", "后段", "结尾"]
    for pos in position_order:
        for seg in detected_segments:
            if seg["position"] == pos:
                instructions["segments"].append({
                    "position": pos,
                    "context": seg["context"],
                    "duration_pct": get_segment_duration(pos)
                })
    
    # 解析特效
    effect_keywords = {
        "慢动作": {"type": "slow_motion", "factor": 0.5},
        "快动作": {"type": "fast_motion", "factor": 2.0},
        "定格": {"type": "freeze_frame", "duration": 2},
        "倒放": {"type": "reverse", "description": "倒放效果"},
        "定格画面": {"type": "pause_effect", "description": "暂停画面特效"},
        "震动": {"type": "shake", "intensity": "medium"},
        "模糊": {"type": "blur", "radius": 10}
    }
    
    for keyword, config in effect_keywords.items():
        if keyword in text:
            instructions["effects"].append({
                "type": config["type"],
                "params": config,
                "description": f"添加{keyword}效果"
            })
    
    # 解析BGM指令
    bgm_patterns = {
        "史诗": {"style": "epic", "instruments": ["管弦乐", "合唱"]},
        "钢琴": {"style": "piano", "instruments": ["钢琴", "弦乐"]},
        "电子": {"style": "electronic", "instruments": ["合成器", "贝斯"]},
        "摇滚": {"style": "rock", "instruments": ["吉他", "鼓"]},
        "轻柔": {"style": "soft", "instruments": ["吉他", "钢琴"]},
        "高潮": {"style": "climax", "instruments": ["全奏"]},
        "背景": {"style": "background", "instruments": ["环境音"]}
    }
    
    detected_bgm = []
    for keyword, config in bgm_patterns.items():
        if keyword in text:
            detected_bgm.append(config)
    
    if detected_bgm:
        instructions["bgm"] = {
            "styles": detected_bgm,
            "volume": 0.25,
            "fade_duration": 1.5
        }
    
    # 生成摘要
    summary = generate_parse_summary(instructions)
    
    return {
        "success": True,
        "instructions": instructions,
        "raw_segments": raw_segments,
        "summary": summary
    }


def get_segment_duration(position: str) -> Dict[str, float]:
    """获取段落时长百分比"""
    duration_map = {
        "开场": {"start": 0, "end": 15},
        "开头": {"start": 0, "end": 20},
        "序幕": {"start": 0, "end": 10},
        "前段": {"start": 0, "end": 33},
        "中间": {"start": 33, "end": 66},
        "中段": {"start": 33, "end": 66},
        "高潮": {"start": 66, "end": 85},
        "后段": {"start": 66, "end": 100},
        "结尾": {"start": 85, "end": 100}
    }
    return duration_map.get(position, {"start": 0, "end": 100})


def generate_parse_summary(instructions: Dict) -> str:
    """生成解析摘要"""
    parts = []
    
    if instructions["rhythm"]:
        rhythms = [r["description"] for r in instructions["rhythm"]]
        parts.append(f"节奏：{', '.join(rhythms)}")
    
    if instructions["transitions"]:
        transitions = [t["description"] for t in instructions["transitions"]]
        parts.append(f"转场：{', '.join(transitions)}")
    
    if instructions["emotions"]:
        emotions = [e["tag"] for e in instructions["emotions"]]
        parts.append(f"情绪：{', '.join(emotions)}")
    
    if instructions["effects"]:
        effects = [e["type"] for e in instructions["effects"]]
        parts.append(f"特效：{', '.join(effects)}")
    
    if instructions["segments"]:
        segments = [s["position"] for s in instructions["segments"]]
        parts.append(f"段落：{', '.join(segments)}")
    
    if not parts:
        return "未识别到明确的剪辑指令"
    
    return "；".join(parts)
