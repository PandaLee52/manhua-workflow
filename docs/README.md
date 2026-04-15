# AI智能剪辑平台

## 🌐 在线访问

### GitHub Pages（前端）
**地址：** https://pandalee52.github.io/manhua-workflow/

启用步骤：
1. 访问仓库 Settings → Pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 "main" → "/docs"
4. 点击 Save
5. 等待几分钟后访问上方地址

---

## 📦 完整功能

| 功能 | 状态 |
|------|------|
| 多视频上传 | ✅ |
| 分镜剧本上传 | ✅ |
| 智能BGM搜索 | ✅ |
| BGM试听选择 | ✅ |
| 实时处理进度 | ✅ |
| 成片下载 | ✅ |

---

## 🚀 部署方式

### 方式1：GitHub Pages（前端预览）
- 完全免费
- 仅前端界面，后端需另外部署

### 方式2：Render（完整后端）
- 免费额度：750小时/月
- 支持Flask后端

### 方式3：本地运行
```bash
# 下载工具包
# 解压后进入 backend 目录
pip install -r requirements.txt
python app.py
```

---

## 📂 项目结构

```
manhua-workflow/
├── docs/                    # GitHub Pages前端
│   └── index.html
├── 在线剪辑平台/
│   ├── backend/            # Flask后端API
│   ├── frontend/           # Vue3前端
│   └── deploy/             # 部署配置
└── 自动剪辑工作流/          # 离线版工具
```
