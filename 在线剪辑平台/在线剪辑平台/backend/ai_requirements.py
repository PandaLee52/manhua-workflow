"""
AI剪辑要求理解模块
将自然语言剪辑要求解析为结构化参数
支持规则引擎和LLM API两种模式
"""

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


# ==================== 配置和常量 ====================

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

# 时长系数（用于调整镜头时长）
DURATION_FACTORS = {
    'very_fast': 0.5,
    'fast': 0.7,
    'normal': 1.0,
    'slow': 1.3,
    'very_slow': 1.6
}


# ==================== 数据类 ====================

@dataclass
class SegmentRequirement:
    """段落剪辑要求"""
    position: str  # start, middle, end
    style: str  # fast, slow, normal
    mood: str  # epic, suspense, warm, etc.
    duration_factor: float  # 时长系数
    transition: str  # quick, smooth, dramatic
    bgm_keywords: List[str]  # BGM关键词
    description: str  # 原始描述

@dataclass
class ParsedRequirements:
    """解析后的完整剪辑要求"""
    segments: List[SegmentRequirement]
    global_bgm_style: str  # 全局BGM风格
    global_transition: str  # 全局转场
    has_custom_requirements: bool  # 是否有自定义要求
    raw_text: str  # 原始输入文本
    use_llm: bool  # 是否需要LLM增强


# ==================== 规则引擎 ====================

class RuleBasedParser:
    """基于规则的剪辑要求解析器"""
    
    def __init__(self):
        self.position_keywords = POSITION_KEYWORDS
        self.style_keywords = STYLE_KEYWORDS
        self.mood_keywords = MOOD_KEYWORDS
        self.transition_keywords = TRANSITION_KEYWORDS
        self.bgm_keywords = BGM_STYLE_KEYWORDS
    
    def parse(self, text: str) -> ParsedRequirements:
        """解析自然语言剪辑要求"""
        if not text or not text.strip():
            return self._default_requirements(text)
        
        segments = []
        found_positions = set()
        
        # 检测段落要求
        for position, pos_keywords in self.position_keywords.items():
            for keyword in pos_keywords:
                if keyword in text:
                    # 提取该段落的要求
                    segment = self._extract_segment(text, position, keyword)
                    if segment and position not in found_positions:
                        segments.append(segment)
                        found_positions.add(position)
                    break
        
        # 如果没有找到明确的段落要求，尝试提取全局要求
        if not segments:
            segments = self._extract_global_segments(text)
        
        # 提取BGM风格
        bgm_style = self._extract_bgm_style(text)
        
        # 提取转场风格
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
        """提取单个段落的要求"""
        # 提取风格
        style = self._extract_style(text)
        
        # 提取情绪
        mood = self._extract_mood(text)
        
        # 提取时长系数
        duration_factor = self._extract_duration_factor(text, style)
        
        # 提取转场
        transition = self._extract_transition(text)
        
        # 提取BGM关键词
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
        """提取全局段落要求（没有明确位置时）"""
        segments = []
        style = self._extract_style(text)
        mood = self._extract_mood(text)
        duration_factor = self._extract_duration_factor(text, style)
        transition = self._extract_transition(text)
        bgm_keywords = self._extract_bgm_keywords(text)
        
        # 根据内容判断影响范围
        if any(k in text for k in ['全', '整个', '所有', '整体']):
            # 影响全部
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
            # 只影响开头
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
        """提取剪辑风格"""
        for style, keywords in self.style_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return style
        return 'normal'
    
    def _extract_mood(self, text: str) -> str:
        """提取情绪氛围"""
        for mood, keywords in self.mood_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return mood
        return 'default'
    
    def _extract_duration_factor(self, text: str, style: str) -> float:
        """提取时长系数"""
        # 根据风格确定基础系数
        if style == 'fast':
            base_factor = DURATION_FACTORS['fast']
        elif style == 'slow':
            base_factor = DURATION_FACTORS['slow']
        else:
            base_factor = DURATION_FACTORS['normal']
        
        # 检查是否有额外的强调词
        if any(k in text for k in ['非常', '特别', '极其', '十分']):
            if style == 'fast':
                base_factor = DURATION_FACTORS['very_fast']
            elif style == 'slow':
                base_factor = DURATION_FACTORS['very_slow']
        
        return base_factor
    
    def _extract_transition(self, text: str) -> str:
        """提取转场风格"""
        for transition, keywords in self.transition_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return transition
        return 'default'
    
    def _extract_bgm_style(self, text: str) -> str:
        """提取BGM风格"""
        for bgm_style, keywords in self.bgm_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return bgm_style
        return 'calm'
    
    def _extract_bgm_keywords(self, text: str) -> List[str]:
        """提取BGM相关关键词"""
        keywords = []
        for bgm_style, style_keywords in self.bgm_keywords.items():
            for keyword in style_keywords:
                if keyword in text:
                    if keyword not in keywords:
                        keywords.append(keyword)
        return keywords
    
    def _default_requirements(self, text: str) -> ParsedRequirements:
        """默认要求"""
        return ParsedRequirements(
            segments=[],
            global_bgm_style='calm',
            global_transition='default',
            has_custom_requirements=False,
            raw_text=text or '',
            use_llm=False
        )


# ==================== LLM API解析器 ====================

class LLMAPIParser:
    """基于LLM API的剪辑要求解析器"""
    
    def __init__(self, api_key: str = None, api_url: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.api_url = api_url or "https://api.openai.com/v1/chat/completions"
        self.model = model
        self.rule_parser = RuleBasedParser()
        
        # LLM提示词
        self.system_prompt = """你是一个专业的视频剪辑助手，擅长将用户的自然语言剪辑要求转换为结构化的参数。

请分析用户输入的剪辑要求，输出JSON格式的结构化参数：

{
    "segments": [
        {
            "position": "start/middle/end",  // 段落位置
            "style": "fast/slow/normal",  // 剪辑节奏
            "mood": "epic/suspense/warm/sad/happy/tense/default",  // 情绪氛围
            "duration_factor": 0.5-1.6,  // 时长系数，fast时<1，slow时>1
            "transition": "quick/smooth/dramatic/default",  // 转场风格
            "description": "该段落的描述"
        }
    ],
    "global_bgm_style": "epic/suspense/warm/calm/romantic/action/default",  // 全局BGM风格
    "global_transition": "quick/smooth/dramatic/default",  // 全局转场风格
    "has_custom_requirements": true/false,  // 是否有明确的剪辑要求
    "summary": "对剪辑要求的简要总结"
}

注意事项：
1. 如果用户没有指定段落位置，根据情绪/节奏推断影响范围
2. 时长系数：very_fast=0.5, fast=0.7, normal=1.0, slow=1.3, very_slow=1.6
3. 如果用户没有提到BGM或转场，使用默认值
4. 尽量从用户描述中提取具体的镜头时长、情绪、节奏等信息"""
    
    def parse(self, text: str) -> ParsedRequirements:
        """使用LLM解析剪辑要求"""
        if not text or not text.strip():
            return self.rule_parser._default_requirements(text)
        
        try:
            import requests
            
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
                
                # 解析JSON结果
                parsed = json.loads(content)
                return self._convert_to_parsed_requirements(parsed, text)
            else:
                # API调用失败，使用规则引擎
                print(f"LLM API调用失败: {response.status_code}, 使用规则引擎")
                return self.rule_parser.parse(text)
                
        except Exception as e:
            print(f"LLM解析异常: {e}, 使用规则引擎")
            return self.rule_parser.parse(text)
    
    def _convert_to_parsed_requirements(self, parsed: Dict, raw_text: str) -> ParsedRequirements:
        """将LLM解析结果转换为ParsedRequirements"""
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


# ==================== 主解析器 ====================

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
        """解析剪辑要求"""
        if self.llm_parser and self.use_llm:
            # 优先使用LLM
            return self.llm_parser.parse(text)
        else:
            # 使用规则引擎
            return self.rule_parser.parse(text)
    
    def parse_to_dict(self, text: str) -> Dict[str, Any]:
        """解析并返回字典格式"""
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
    
    def get_clipping_params(self, text: str, total_duration: float = 60) -> Dict[str, Any]:
        """
        获取完整的剪辑参数，用于实际视频剪辑
        
        Args:
            text: 剪辑要求文本
            total_duration: 视频总时长（秒）
        
        Returns:
            包含具体剪辑参数的字典
        """
        result = self.parse(text)
        
        # 默认分段比例
        segment_ratios = {
            'start': 0.25,  # 开头25%
            'middle': 0.5,  # 中间50%
            'end': 0.25     # 结尾25%
        }
        
        clipping_params = {
            "segments": [],
            "global": {
                "bgm_style": result.global_bgm_style,
                "transition": result.global_transition
            }
        }
        
        for seg in result.segments:
            position = seg.position
            
            # 计算该段落的时间范围
            start_ratio = sum(list(segment_ratios.values())[:list(segment_ratios.keys()).index(position)])
            duration_ratio = segment_ratios.get(position, 0.25)
            
            segment_params = {
                "position": position,
                "time_range": {
                    "start_ratio": start_ratio,
                    "duration_ratio": duration_ratio,
                    "estimated_seconds": total_duration * duration_ratio * seg.duration_factor
                },
                "style": {
                    "clipping_speed": "fast" if seg.duration_factor < 1 else ("slow" if seg.duration_factor > 1 else "normal"),
                    "duration_factor": seg.duration_factor
                },
                "mood": seg.mood,
                "transition": seg.transition,
                "bgm_keywords": seg.bgm_keywords,
                "description": seg.description
            }
            
            clipping_params["segments"].append(segment_params)
        
        return clipping_params


# ==================== 预设模板 ====================

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


# ==================== 便捷函数 ====================

def parse_requirements(text: str, use_llm: bool = False, **kwargs) -> ParsedRequirements:
    """
    解析剪辑要求（便捷函数）
    
    Args:
        text: 剪辑要求文本
        use_llm: 是否使用LLM增强
        **kwargs: 传递给LLM解析器的参数
    
    Returns:
        ParsedRequirements对象
    """
    parser = AIRequirementsParser(use_llm=use_llm, **kwargs)
    return parser.parse(text)


def parse_to_json(text: str, use_llm: bool = False, **kwargs) -> str:
    """解析剪辑要求并返回JSON字符串"""
    parser = AIRequirementsParser(use_llm=use_llm, **kwargs)
    return json.dumps(parser.parse_to_dict(text), ensure_ascii=False, indent=2)


def get_preset_template(name: str) -> Optional[str]:
    """获取预设模板"""
    return PRESET_TEMPLATES.get(name)


def list_preset_templates() -> Dict[str, str]:
    """列出所有预设模板"""
    return PRESET_TEMPLATES.copy()
