# Render.com 部署指南

## 方式A: 使用 Render Blueprint（推荐）

### 前提条件
1. 安装 Render CLI: `npm install -g @render/cloud`
2. 登录 Render: `render login`

### 部署命令
```bash
cd 在线剪辑平台/deploy
render blueprint render.yaml
```

### 注意事项
- Blueprint 会自动创建所有服务
- 免费版有休眠限制（15分钟无活动会休眠）

---

## 方式B: 手动部署（当前任务使用）

### 步骤

1. **访问 Render Dashboard**
   - 打开 https://dashboard.render.com
   - 使用 GitHub 账号登录

2. **创建 Web Service**
   - 点击 "New" → "Web Service"
   - 连接 GitHub 仓库: `PandaLee52/manhua-workflow`

3. **配置参数**
   | 参数 | 值 |
   |------|-----|
   | Name | manhua-editor |
   | Root Directory | 在线剪辑平台/backend |
   | Region | Oregon |
   | Branch | main |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn app:app --bind 0.0.0.0:8000` |
   | Instance Type | Free |

4. **环境变量**（可选添加）
   - `FLASK_ENV=production`
   - `SECRET_KEY=your-secret-key`

5. **部署完成**
   - 获取服务URL: `https://manhua-editor.onrender.com`
   - 访问 `/health` 检查API状态

---

## 健康检查

部署完成后，访问以下端点验证服务：

```
https://manhua-editor.onrender.com/health
```

预期响应:
```json
{
  "status": "ok",
  "service": "在线剪辑平台",
  "timestamp": "2024-..."
}
```

---

## 免费版限制

- 每月 750 小时（足够个人使用）
- 15 分钟无活动后进入休眠
- 首次请求会触发冷启动（约 30 秒）
- 数据库/Redis 需要额外配置（可选）

---

## 更新部署

当代码推送到 GitHub 后，Render 会自动重新部署。

如需手动触发：
```bash
render deploy --service=manhua-editor
```
