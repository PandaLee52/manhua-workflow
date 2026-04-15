# Vercel 部署指南

## 方案概述

采用**前后端分离部署**架构：

| 组件 | 部署平台 | 理由 |
|------|---------|------|
| 前端 (Vue 3) | **Vercel** | 静态托管免费、CDN加速、自动SSL |
| 后端 (Flask) | **Railway/Render** | 支持长时任务、文件系统、Worker进程 |

## 为什么不用纯Vercel Serverless？

❌ **Vercel Serverless Functions 限制**：
- 执行时间：10秒（ hobby ）/ 60秒（pro）
- 无持久化文件系统
- 临时存储512MB
- 不适合视频处理（FFmpeg需要长时运行）

✅ **推荐方案优势**：
- Railway/Render支持持久化存储和后台Worker
- 可以运行FFmpeg长时间处理视频
- 支持Celery + Redis异步任务队列

---

## 部署步骤

### 第一步：部署后端（Railway）

#### 1.1 准备Railway账号
1. 访问 [Railway.app](https://railway.app) 注册账号
2. 使用GitHub登录更方便

#### 1.2 创建项目
```bash
# 方式1: Railway控制台创建
# 1. New Project → Deploy from GitHub repo
# 2. 选择你的后端仓库

# 方式2: 使用Railway CLI
npm install -g @railway/cli
railway login
railway init
```

#### 1.3 配置环境变量
在Railway控制台的Variables中添加：

```
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

CELERY_BROKER_URL=redis://:your-redis-password@your-redis-host:6379/0
CELERY_RESULT_BACKEND=redis://:your-redis-password@your-redis-host:6379/0

FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe

FLASK_ENV=production
FLASK_DEBUG=false
```

#### 1.4 配置Redis（使用Upstash）
1. 注册 [Upstash](https://upstash.com)（免费Redis）
2. 获取Redis连接信息
3. 填入Railway环境变量

#### 1.5 部署
```bash
railway up
```

Railway会自动检测Python项目并安装依赖。

#### 1.6 获取后端URL
部署成功后，Railway会提供类似：
```
https://video-editor.up.railway.app
```

---

### 第二步：部署前端（Vercel）

#### 2.1 准备Vercel账号
1. 访问 [Vercel.com](https://vercel.com) 注册
2. 使用GitHub登录

#### 2.2 导入项目
```bash
# 安装Vercel CLI
npm install -g vercel

# 登录
vercel login

# 进入前端目录
cd 在线剪辑平台/frontend

# 部署
vercel
```

#### 2.3 配置环境变量
在Vercel控制台或部署时设置：

| 变量名 | 值 |
|--------|-----|
| `VITE_API_BASE_URL` | 你的Railway后端URL（如 `https://video-editor.up.railway.app`） |

#### 2.4 自定义域名（可选）
1. Vercel控制台 → Settings → Domains
2. 添加你的域名
3. 配置DNS记录

---

### 第三步：更新前端API配置

#### 3.1 创建 `frontend/.env.production`
```bash
VITE_API_BASE_URL=https://video-editor.up.railway.app
```

#### 3.2 构建时注入
```bash
cd 在线剪辑平台/frontend
vercel env add VITE_API_BASE_URL
```

---

## 备选方案：Render部署后端

### 为什么选Render？
- 有免费额度（750小时/月）
- 支持Docker
- 支持后台Worker

### Render部署步骤

#### 1. 创建 render.yaml
项目已有：`在线剪辑平台/deploy/render.yaml`

#### 2. 在Render控制台创建
1. New → Blueprint
2. 连接GitHub仓库
3. Render会自动读取 `render.yaml`

#### 3. 配置环境变量
同Railway配置

---

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户浏览器                            │
└─────────────────────┬─────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    Vercel CDN                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Vue 3 前端 (静态资源)                     │   │
│  │  • 自动HTTPS                                     │   │
│  │  • 全球CDN加速                                   │   │
│  │  • 边缘节点部署                                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬─────────────────────────────────┘
                      │ API请求 (CORS)
                      ▼
┌─────────────────────────────────────────────────────────┐
│               Railway / Render 后端                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Flask API   │  │  Celery      │  │   Redis      │ │
│  │  (Web)       │  │  (Worker)    │  │  (Broker)    │ │
│  │  :10000      │  │  :10001      │  │  :6379       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │         文件系统 (持久化存储)                      │   │
│  │  • /app/uploads/  (用户上传)                      │   │
│  │  • /app/output/   (处理结果)                      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 成本估算

### Vercel (前端)
| 套餐 | 价格 | 带宽 | 说明 |
|------|------|------|------|
| Hobby | **免费** | 100GB/月 | 个人项目足够 |
| Pro | $20/月 | 1TB/月 | 团队/商业项目 |

### Railway (后端)
| 资源 | Hobby | Starter |
|------|-------|---------|
| 计算 | 500小时/月 | $5/月 |
| 内存 | 512MB | 512MB |
| 磁盘 | 1GB | 10GB |
| Redis | $0 (Upstash免费) | $5/月 |

### Upstash Redis
| 套餐 | 价格 | 说明 |
|------|------|------|
| Free | **免费** | 10K命令/天 |
| Pay as you go | $0.2/10K | 按量付费 |

### 总成本
- **最低配置（免费）**：$0/月
  - Vercel Hobby (免费)
  - Railway Hobby (500小时)
  - Upstash Free (10K命令/天)

---

## 常见问题

### Q: Vercel rewrites不生效？
A: `vercel.json` 中的rewrites在hobby套餐有限制。请改用环境变量配置API地址。

### Q: 视频上传失败？
A: 检查Railway后端的文件大小限制，确保 `MAX_CONTENT_LENGTH` 配置足够。

### Q: CORS跨域错误？
A: Flask后端已配置CORS，允许所有来源。如仍有问题，检查后端日志。

### Q: Celery任务不执行？
A: 确保Redis连接正常，Celery Worker正在运行。

---

## 一键部署脚本

### 部署前端到Vercel
```bash
cd 在线剪辑平台/frontend
vercel --prod
```

### 查看部署状态
```bash
vercel ls
vercel logs <deployment-url>
```

---

## 监控和维护

### Vercel Analytics
控制台 → Analytics 查看访问量、性能指标

### Railway日志
```bash
railway logs
railway status
```

### 健康检查
```bash
curl https://your-backend.railway.app/api/health
```

---

## 下一步

1. 部署后端到Railway
2. 获取后端URL
3. 部署前端到Vercel
4. 配置环境变量
5. 测试完整流程
