# AI功能增强API文档

## 概览

本API提供字幕生成、AI剪辑建议、人物一致性检测和增强剪辑解析功能。

---

## 1. 字幕生成接口

### POST /generate-subtitles

接收视频文件，使用语音识别生成SRT格式字幕（无标点）。

**请求方式**: `multipart/form-data` 或 `JSON`

**参数**:

| 方式 | 参数 | 类型 | 说明 |
|------|------|------|------|
| 文件上传 | `video` | File | 视频文件 |
| 文件上传 | `use_whisper` | String | 是否使用Whisper (默认true) |
| JSON | `video_path` | String | 视频文件路径 |
| JSON | `use_whisper` | Boolean | 是否使用Whisper |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "srt_content": "1\n00:00:00,000 --> 00:00:03,000\n你好\n\n2\n00:00:03,000 --> 00:00:06,000\n这是一个新的开始",
    "segments": [
      {"index": 1, "start": 0.0, "end": 3.0, "text": "你好"},
      {"index": 2, "start": 3.0, "end": 6.0, "text": "这是一个新的开始"}
    ],
    "language": "zh",
    "duration": 120.5,
    "simulated": false,
    "subtitle_count": 40
  },
  "message": "字幕生成成功"
}
```

**注意**: 
- 字幕内容自动去除标点符号
- Whisper不可用时自动回退到模拟模式

---

### POST /subtitles/srt

将字幕片段转换为SRT格式。

**请求体**:

```json
{
  "segments": [
    {"start": 0.0, "end": 3.0, "text": "你好，世界！"},
    {"start": 3.0, "end": 6.0, "text": "这是测试。"}
  ],
  "no_punctuation": true
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "srt_content": "1\n00:00:00,000 --> 00:00:03,000\n你好世界\n\n2\n00:00:03,000 --> 00:00:06,000\n这是测试",
    "segment_count": 2
  }
}
```

---

## 2. AI剪辑建议接口

### POST /suggest

根据视频内容描述生成AI剪辑建议。

**请求体**:

```json
{
  "content_description": "紧张刺激的战斗场景，男主角与敌人激烈追逐",
  "episode_count": 1,
  "is_first_episode": true,
  "total_duration": 120
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "duration": {
      "min": 60,
      "recommended": 120,
      "max": 180,
      "is_first_episode": true
    },
    "speed": {
      "base_rate": 1.25,
      "range": [1.2, 1.3],
      "fast_scenes": ["action", "chase", "confrontation"],
      "normal_scenes": ["dialogue", "narrative"]
    },
    "bgm": {
      "min_changes": 2,
      "max_changes": 5,
      "suggested_positions": [
        {"time_pct": 15, "action": "切换主BGM"},
        {"time_pct": 40, "action": "切换高潮BGM"}
      ],
      "styles": [{"style": "action_epic", "keywords": ["紧张", "激烈"]}],
      "intensity_curve": [...]
    },
    "segments": [
      {
        "position": "opening",
        "start_pct": 0,
        "end_pct": 15,
        "style": "fast",
        "mood": "紧张",
        "rhythm": "快节奏",
        "transition": "fade_in",
        "bgm_intensity": 0.8
      }
    ],
    "rhythm": {...},
    "transitions": {...},
    "emotions": [...]
  },
  "warnings": ["💡 建议：语速控制在1.2-1.3倍"]
}
```

---

### POST /suggest/validate

验证剪辑参数是否符合甲方要求。

**甲方要求**:
- 单集 ≥ 60秒，首集 ≥ 120秒
- 语速 1.2-1.3倍
- BGM变换 ≥ 2次/集

**请求体**:

```json
{
  "duration": 90,
  "episode_count": 1,
  "is_first_episode": false,
  "bgm_changes": 3,
  "speech_rate": 1.25
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "passed": true,
    "checks": {
      "duration": true,
      "bgm_changes": true,
      "speech_rate": true
    },
    "warnings": [
      "✅ 时长合格：90秒",
      "✅ BGM变换合格：3次",
      "✅ 语速合格：1.25倍"
    ]
  }
}
```

---

## 3. 人物一致性检测接口

### POST /check-consistency

检测多帧图片或视频中人物特征一致性。

**请求方式**: `multipart/form-data` 或 `JSON`

**参数**:

| 方式 | 参数 | 类型 | 说明 |
|------|------|------|------|
| 文件上传 | `images` | Files[] | 多张图片文件 |
| 文件上传 | `video` | File | 视频文件(可选) |
| 文件上传 | `frame_count` | Number | 提取帧数量(默认8) |
| JSON | `images` | Array | 图片列表 |
| JSON | `video_path` | String | 视频路径 |

**检测特征**:
- `face_shape`: 脸型
- `skin_tone`: 肤色
- `hair_color`: 发色
- `hair_style`: 发型
- `clothing`: 服装
- `expression`: 表情

**响应**:

```json
{
  "success": true,
  "data": {
    "consistency_score": 85.5,
    "is_consistent": true,
    "grade": "A 良好",
    "features": {
      "face_shape": {
        "consistency": 100,
        "dominant": "椭圆形",
        "values": [...]
      },
      "skin_tone": {...}
    },
    "issues": [
      {
        "feature": "hair_color",
        "severity": "medium",
        "consistency": 66.7,
        "dominant_value": "黑色",
        "outlier_values": ["棕色"],
        "affected_frames": [3],
        "description": "发色一致性67%，需要注意补色"
      }
    ],
    "recommendations": [
      "🔧 发色调整：对第[3]帧进行补色处理"
    ],
    "checked_frames": 5
  },
  "message": "一致性检测完成"
}
```

**评分等级**:
- A+ (≥95): 优秀
- A (≥85): 良好
- B (≥75): 合格
- C (≥60): 需改进
- D (<60): 不合格

---

## 4. 增强剪辑解析接口

### POST /parse

增强的剪辑指令解析，支持更多指令类型。

**支持的指令**:

#### 节奏控制

| 关键词 | 模式 | 速度 |
|--------|------|------|
| 快/快节奏 | fast | 1.3x |
| 慢/慢节奏 | slow | 0.8x |
| 渐快 | accelerate | 1.0→1.3 |
| 渐慢 | decelerate | 1.3→0.8 |
| 渐变 | gradual | 动态 |

#### 转场效果

| 关键词 | 类型 | 时长 |
|--------|------|------|
| 淡入 | fade_in | 0.5-1.5s |
| 淡出 | fade_out | 1.0-2.0s |
| 闪白 | flash_white | 0.1-0.3s |
| 闪黑 | flash_black | 0.1-0.3s |
| 黑场 | dip_to_black | 0.3-0.5s |
| 叠化 | cross_dissolve | 0.5-1.0s |
| 快切 | cut | 0.1-0.2s |
| 跳切 | jump_cut | 0 |

#### 情绪标签

| 关键词 | 情绪 | BGM风格 | 调色 |
|--------|------|---------|------|
| 紧张 | tension | action | 冷色调 |
| 温馨 | heartwarming | gentle | 暖色调 |
| 悬疑 | suspense | mystery | 暗色调 |
| 欢快 | happy | upbeat | 明亮 |
| 悲伤 | sad | emotional | 灰蓝 |
| 震撼 | epic | orchestral | 高对比 |
| 浪漫 | romantic | soft | 柔光 |

#### 特效

| 关键词 | 类型 | 参数 |
|--------|------|------|
| 慢动作 | slow_motion | 0.5x |
| 快动作 | fast_motion | 2.0x |
| 定格 | freeze_frame | 2s |
| 倒放 | reverse | - |
| 震动 | shake | medium |

**请求体**:

```json
{
  "text": "开头要震撼，快节奏，淡入淡出转场，紧张悬疑的情绪，最后来个定格画面",
  "total_duration": 120
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "instructions": {
      "rhythm": [
        {"type": "fast", "speed": 1.3, "description": "快节奏剪辑", "matched_keyword": "快节奏"}
      ],
      "transitions": [
        {"type": "fade_in", "duration": [0.5, 1.5], "description": "开场淡入", "matched_keyword": "淡入"},
        {"type": "fade_out", "duration": [1.0, 2.0], "description": "结尾淡出", "matched_keyword": "淡出"}
      ],
      "emotions": [
        {"tag": "紧张", "mood": "tension", "bgm_style": "action", "color_grading": "冷色调"},
        {"tag": "悬疑", "mood": "suspense", "bgm_style": "mystery", "color_grading": "暗色调"}
      ],
      "effects": [
        {"type": "freeze_frame", "params": {"duration": 2}, "description": "添加定格画面效果"}
      ],
      "segments": [...],
      "bgm": {...}
    },
    "summary": "节奏：快节奏剪辑；转场：开场淡入、结尾淡出；情绪：紧张、悬疑；特效：定格画面效果"
  }
}
```

---

### POST /parse/quick

快速剪辑解析（简化版）。

**请求体**:

```json
{
  "keywords": ["开头", "震撼", "快节奏", "结尾", "悬疑"]
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "keywords": ["开头", "震撼", "快节奏", "结尾", "悬疑"],
    "instructions": {...},
    "summary": "..."
  }
}
```

---

## 错误响应格式

```json
{
  "success": false,
  "error": "错误信息描述",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

## 使用示例

### Python示例

```python
import requests

# 字幕生成
response = requests.post(
    "http://your-api.com/generate-subtitles",
    files={"video": open("video.mp4", "rb")}
)
result = response.json()
print(result["data"]["srt_content"])

# AI剪辑建议
response = requests.post(
    "http://your-api.com/suggest",
    json={
        "content_description": "热血格斗场景",
        "episode_count": 1,
        "is_first_episode": True,
        "total_duration": 90
    }
)
result = response.json()
print(result["data"]["suggestions"])

# 人物一致性检测
response = requests.post(
    "http://your-api.com/check-consistency",
    files={"images": open("frame1.jpg", "rb")}
)
result = response.json()
print(f"一致性评分: {result['data']['consistency_score']}")

# 增强剪辑解析
response = requests.post(
    "http://your-api.com/parse",
    json={
        "text": "开头震撼快节奏，中间温馨慢节奏，结尾悬疑"
    }
)
result = response.json()
print(result["data"]["summary"])
```

---

## 甲方标准汇总

| 项目 | 要求 |
|------|------|
| 单集时长 | ≥ 60秒 |
| 首集时长 | ≥ 120秒 |
| 语速 | 1.2-1.3倍 |
| BGM变换 | ≥ 2次/集 |
| 字幕格式 | SRT，无标点 |
