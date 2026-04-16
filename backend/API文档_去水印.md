# 视频去水印/字幕API文档

## 概述

本模块提供视频去水印和去字幕的完整AI功能，支持自动检测、手动框选和批量处理。

## API接口

### 1. 水印检测接口 POST /api/detect-watermark

AI自动检测画面中的水印区域。

**请求方式**: `multipart/form-data` 或 `JSON`

**参数**:

| 方式 | 参数 | 类型 | 说明 |
|------|------|------|------|
| 文件上传 | file | File | 图片或视频文件 |
| JSON | video_path | String | 服务器上的视频路径 |

**返回示例**:

```json
{
  "success": true,
  "data": {
    "regions": [
      {
        "x": 100,
        "y": 50,
        "width": 200,
        "height": 40,
        "type": "watermark",
        "confidence": 0.85,
        "label": "corner_watermark"
      }
    ],
    "region_count": 1,
    "frame_info": {
      "width": 1920,
      "height": 1080,
      "frame_count": 300
    }
  },
  "message": "检测到 1 个水印区域"
}
```

---

### 2. 字幕检测接口 POST /api/detect-subtitle

使用OCR技术检测视频底部的字幕区域。

**请求方式**: 同 `/api/detect-watermark`

**返回示例**:

```json
{
  "success": true,
  "data": {
    "regions": [
      {
        "x": 100,
        "y": 900,
        "width": 1720,
        "height": 80,
        "type": "subtitle",
        "confidence": 0.9,
        "label": "ocr_subtitle"
      }
    ],
    "region_count": 1,
    "frame_info": {
      "width": 1920,
      "height": 1080
    },
    "has_text": true
  },
  "message": "检测到 1 个字幕区域"
}
```

---

### 3. 一键检测接口 POST /api/detect-all

同时检测水印和字幕区域。

**请求方式**: 同 `/api/detect-watermark`

**返回示例**:

```json
{
  "success": true,
  "data": {
    "watermarks": [...],
    "subtitles": [...],
    "all_regions": [...],
    "frame_info": {...},
    "total_regions": 3
  },
  "message": "检测到 2 个水印, 1 个字幕"
}
```

---

### 4. 去水印接口 POST /api/remove-watermark

去除视频中的水印或字幕。

**请求方式**: `JSON`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| video_path | String | 是 | 视频文件路径 |
| regions | Array | 否 | 要去除的区域坐标 |
| preserve_audio | Boolean | 否 | 是否保留音频，默认true |
| auto_detect | Boolean | 否 | 是否自动检测，默认false |
| detect_type | String | 否 | 检测类型: watermark/subtitle/all |

**regions参数格式**:

```json
[
  {"x": 100, "y": 50, "width": 200, "height": 40},
  {"x": 0, "y": 900, "width": 1920, "height": 80}
]
```

**请求示例**:

```json
{
  "video_path": "/app/uploads/video_xxx.mp4",
  "regions": [
    {"x": 50, "y": 30, "width": 180, "height": 50},
    {"x": 0, "y": 950, "width": 1920, "height": 70}
  ],
  "preserve_audio": true
}
```

**返回示例**:

```json
{
  "success": true,
  "data": {
    "task_id": "watermark_abc123",
    "status": "completed",
    "output_path": "/app/output/watermark_abc123.mp4",
    "output_url": "/output/watermark_abc123.mp4",
    "frames_processed": 150,
    "regions_removed": 2
  },
  "message": "处理完成"
}
```

**自动检测示例**:

```json
{
  "video_path": "/app/uploads/video_xxx.mp4",
  "auto_detect": true,
  "detect_type": "all"
}
```

---

### 5. 批量处理接口 POST /api/batch-remove

批量处理多个视频。

**请求方式**: `JSON`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| videos | Array | 是 | 视频列表 |
| default_regions | Array | 否 | 默认去除区域 |
| detect_type | String | 否 | 检测类型 |

**videos格式**:

```json
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
  "default_regions": [
    {"x": 0, "y": 950, "width": 1920, "height": 70}
  ]
}
```

**返回示例**:

```json
{
  "success": true,
  "data": {
    "task_id": "batch_xyz789",
    "status": "processing",
    "total_videos": 2,
    "status_url": "/api/batch-status/batch_xyz789"
  },
  "message": "已创建批量任务，处理 2 个视频"
}
```

---

### 6. 批量状态查询 GET /api/batch-status/{task_id}

查询批量处理任务状态。

**返回示例**:

```json
{
  "success": true,
  "data": {
    "task_id": "batch_xyz789",
    "status": "processing",
    "progress": 50.0,
    "completed": 1,
    "failed": 0,
    "total": 2,
    "jobs": [
      {
        "job_id": "batch_xyz789_job_0",
        "video_path": "/path/to/video1.mp4",
        "status": "completed",
        "progress": 100.0
      },
      {
        "job_id": "batch_xyz789_job_1",
        "video_path": "/path/to/video2.mp4",
        "status": "processing",
        "progress": 30.0
      }
    ]
  }
}
```

---

### 7. 取消批量任务 POST /api/batch-cancel/{task_id}

取消正在处理的批量任务。

**返回示例**:

```json
{
  "success": true,
  "message": "任务已取消"
}
```

---

### 8. 批量任务列表 GET /api/batch-list

列出所有批量任务。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| status | String | 过滤状态 (pending/processing/completed/failed/cancelled) |

**返回示例**:

```json
{
  "success": true,
  "data": {
    "count": 2,
    "tasks": [
      {
        "task_id": "batch_xyz789",
        "status": "processing",
        "progress": 50.0,
        "total": 2,
        "created_at": "2024-01-15T10:30:00"
      }
    ]
  }
}
```

---

## 技术实现

### 检测算法

1. **水印检测 (WatermarkDetector)**
   - 角落位置检测：检测常见的Logo水印位置（四个角落、顶部居中、底部居中）
   - Logo图案检测：使用ORB特征检测和角点聚类
   - 半透明检测：边缘检测+低方差区域识别

2. **字幕检测 (SubtitleDetector)**
   - 位置检测：基于视频底部区域的启发式规则
   - OCR验证：使用Tesseract进行文字识别
   - 边缘检测：检测字幕下划线特征

3. **图像修复 (WatermarkRemover)**
   - OpenCV inpaint (TELEA算法)
   - 支持区域扩展和平滑

### 视频处理流程

1. 提取视频帧 (ffmpeg/OpenCV)
2. 对每一帧应用修复
3. 重新合成视频 (ffmpeg)
4. 保留原始音频轨道

---

## 使用示例

### Python调用示例

```python
import requests

# 1. 检测水印
response = requests.post(
    "https://your-domain.com/api/detect-watermark",
    files={"file": open("video.mp4", "rb")}
)
regions = response.json()["data"]["regions"]

# 2. 去除水印
response = requests.post(
    "https://your-domain.com/api/remove-watermark",
    json={
        "video_path": "/path/to/video.mp4",
        "regions": regions,
        "preserve_audio": True
    }
)
print(response.json()["data"]["output_url"])
```

### JavaScript调用示例

```javascript
// 1. 上传并检测
const formData = new FormData();
formData.append('file', videoFile);

const detectRes = await fetch('/api/detect-watermark', {
  method: 'POST',
  body: formData
});
const { regions } = await detectRes.json();

// 2. 去除水印
const removeRes = await fetch('/api/remove-watermark', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    video_path: '/path/to/video.mp4',
    regions: regions
  })
});
const { output_url } = await removeRes.json();
```

---

## 注意事项

1. **文件大小限制**: 默认500MB，可通过配置调整
2. **处理时间**: 根据视频长度和区域数量，处理时间可能较长
3. **音频保留**: 默认保留原始音频
4. **批量并发**: 默认2个并行处理任务
5. **临时文件**: 处理完成后自动清理临时文件
