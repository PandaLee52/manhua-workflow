# ========================================
# 在线剪辑平台 - Railway 部署配置
# ========================================

## Railway 简介
Railway 是一个现代化的 PaaS 平台，支持 Docker 部署，提供 $5 免费额度。

## 免费额度
- ✅ 注册送 $5 免费额度
- ✅ PostgreSQL 500MB 免费
- ✅ 自动 HTTPS
- ✅ GitHub 集成
- ✅ 自动睡眠省成本

## 部署步骤

### 1. 准备代码
确保项目包含以下文件：
- `Dockerfile` (在 deploy/ 目录下)
- `requirements.txt`
- `.gitignore` (包含 `__pycache__`, `.env`, `*.pyc`)

### 2. 创建 Railway 项目
1. 访问 https://railway.app
2. 使用 GitHub 账号登录
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择你的仓库

### 3. 配置服务
在 Railway 仪表盘中配置：

**Root Directory**: `deploy` (因为 Dockerfile 在 deploy 目录)

**Start Command** (如果需要覆盖):
```
gunicorn --bind 0.0.0.0:8000 --workers 2 app:app
```

### 4. 设置环境变量
在 Settings → Environment Variables 中添加：

```env
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
PORT=8000
```

### 5. 添加 PostgreSQL (可选)
1. 点击 "New" → "Database" → "PostgreSQL"
2. Railway 会自动设置 `DATABASE_URL`

### 6. 部署
- 推送代码到 GitHub
- Railway 会自动触发部署
- 查看 Logs 监控部署状态

### 7. 配置域名
1. 进入服务 → Settings → Networking
2. 点击 "Generate Domain"
3. 获得公共 URL: `https://your-app.up.railway.app`

## Railway CLI 部署 (可选)

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 进入项目目录
cd deploy

# 初始化项目
railway init

# 部署
railway up

# 查看日志
railway logs
```

## 成本优化建议

1. **启用睡眠模式**
   - 当服务 10 分钟无请求时会自动休眠
   - 下次请求时自动唤醒
   - 大幅节省成本

2. **监控使用量**
   - Railway 仪表盘显示实时用量
   - 避免超出免费额度

3. **Worker 按需启动**
   - 如果不需要后台任务，可以不部署 worker
   - 只部署主应用即可

## 故障排除

**Q: 部署失败**
- 检查 Dockerfile 语法
- 查看 Build Logs
- 确保 requirements.txt 包含所有依赖

**Q: 应用启动失败**
- 检查环境变量是否正确
- 查看 Runtime Logs
- 确认端口配置为 8000

**Q: 数据库连接失败**
- 确认 DATABASE_URL 格式正确
- 检查 PostgreSQL 是否就绪

## Railway vs 其他平台对比

| 特性 | Railway | Render | PythonAnywhere |
|------|---------|--------|----------------|
| 免费额度 | $5/月 | 750小时/月 | 免费Web应用 |
| Dockerfile | ✅ | ✅ | ❌ |
| PostgreSQL | $5/500MB | 免费(30天) | ❌ |
| 空闲休眠 | 10分钟后 | 15分钟后 | 否 |
| CLI 支持 | ✅ | ✅ | ✅ |
