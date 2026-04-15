# ========================================
# 在线剪辑平台 - 完整部署指南
# ========================================

## 平台对比总结

| 平台 | 免费额度 | Dockerfile | 数据库 | 休眠 | 推荐度 |
|------|----------|------------|--------|------|--------|
| **Railway** | $5/月 | ✅ | $5/500MB | 10分钟 | ⭐⭐⭐⭐⭐ |
| **Render** | 750小时/月 | ✅ | 免费30天 | 15分钟 | ⭐⭐⭐⭐ |
| **PythonAnywhere** | 免费 | ❌ | ❌ | 否 | ⭐⭐ |
| **Vercel** | Hobby层 | ⚠️ 限制多 | ❌ | Serverless | ⭐⭐⭐ |
| **Fly.io** | $5试用 | ✅ | $5/256MB | 可配置 | ⭐⭐⭐⭐ |
| **自托管** | 成本高 | ✅ | 完全控制 | 否 | ⭐⭐⭐⭐⭐ |

---

## 推荐方案

### 🥇 首选: Railway
**理由**:
- $5 免费额度，小型应用几乎免费
- 对新手最友好，自动检测配置
- 支持 Docker，灵活部署
- PostgreSQL 和 Redis 一键部署

**适合场景**:
- 个人项目/作品集
- 小型 MVP
- 学习/测试环境

### 🥈 备选: Render
**理由**:
- 完全免费 (需要接受休眠限制)
- 功能全面，PostgreSQL 免费
- 支持 Blueprint 一键部署

**适合场景**:
- 预算极低的项目
- 短期演示
- 需要完整数据库的项目

### 🥉 自托管 (Docker)
**理由**:
- 完全控制，无任何限制
- 无厂商锁定
- 可运行在任何 VPS

**适合场景**:
- 生产环境
- 有服务器资源的团队
- 需要高定制化

---

## 一、Railway 详细部署

### 步骤 1: 准备项目结构
```
video-platform/
├── deploy/
│   ├── Dockerfile          # 主 Dockerfile
│   ├── Dockerfile.worker   # Worker Dockerfile
│   └── docker-compose.yml  # 本地开发用
├── app/
│   ├── __init__.py
│   ├── routes.py
│   └── ...
├── requirements.txt
├── .gitignore
└── .env.example
```

### 步骤 2: Railway 部署
1. 上传代码到 GitHub
2. 访问 railway.app
3. New Project → Deploy from GitHub
4. 选择仓库
5. 设置 Root Directory: `deploy`
6. 添加环境变量
7. 部署完成，自动生成 URL

### 步骤 3: 添加数据库
1. New → Database → PostgreSQL
2. 复制 DATABASE_URL 到环境变量
3. 运行迁移

---

## 二、Render 详细部署

### 步骤 1: 创建 Web Service
1. dashboard.render.com
2. New → Web Service
3. 连接 GitHub 仓库
4. 配置:
   - Root Directory: `deploy`
   - Runtime: Docker
   - Instance: Free

### 步骤 2: 环境变量
```
FLASK_ENV=production
SECRET_KEY=<生成随机密钥>
PORT=10000
```

### 步骤 3: PostgreSQL (可选)
1. New → PostgreSQL
2. 复制连接字符串
3. 添加到 Web Service 环境变量

---

## 三、自托管详细部署

### 服务器要求
- 1GB+ RAM
- 10GB+ 磁盘
- Ubuntu 20.04+

### 快速部署脚本
```bash
#!/bin/bash
# deploy.sh

# 安装 Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 拉取代码
git clone <your-repo> /opt/video-platform
cd /opt/video-platform

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 启动服务
cd deploy
docker-compose up -d

# 配置 Nginx
cp nginx.conf /etc/nginx/sites-available/video-platform
ln -s /etc/nginx/sites-available/video-platform /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# 配置 SSL
certbot --nginx -d your-domain.com
```

---

## 四、环境变量参考

### 必需
```env
FLASK_ENV=production
SECRET_KEY=<长度32+的随机字符串>
PORT=8000
```

### 可选
```env
# 数据库
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# 文件存储
AWS_ACCESS_KEY_ID=<AWS密钥>
AWS_SECRET_ACCESS_KEY=<AWS密钥>
AWS_S3_BUCKET=<S3桶名>

# API 密钥
OPENAI_API_KEY=<OpenAI密钥>
STRIPE_API_KEY=<Stripe密钥>
```

### 生成安全密钥
```bash
# Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32
```

---

## 五、域名配置

### DNS 设置
```
# A 记录
@    A    <服务器IP>

# CNAME 记录 (如果用子域)
www  CNAME your-app.railway.app
api  CNAME your-app.railway.app
```

### SSL 证书
- Railway/Render: 自动配置
- 自托管: Let's Encrypt

---

## 六、监控与日志

### 健康检查端点
```python
@app.route('/health')
def health():
    return {'status': 'ok', 'version': '1.0.0'}
```

### 日志聚合 (可选)
```yaml
# docker-compose.yml 添加
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 七、CI/CD 自动化

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        uses: railwayHQ/railway-deploy-action@v1
        with:
          token: ${{ secrets.RAILWAY_TOKEN }}
          project: ${{ secrets.RAILWAY_PROJECT_ID }}
```

---

## 八、常见问题

### Q: 如何选择数据库?
- **无状态应用**: 不需要数据库，使用内存/S3 存储
- **小型项目**: SQLite (Railway 不支持，需要 PostgreSQL)
- **生产环境**: PostgreSQL

### Q: 如何处理文件上传?
- 小文件 (<5MB): 直接存储到服务器
- 大文件: 建议使用 S3/MinIO
- 视频处理: 使用云存储 + CDN

### Q: 如何降低成本?
1. 选择 Railway $5 套餐
2. 启用自动睡眠
3. 优化 Docker 镜像大小
4. 使用更小的实例类型

### Q: 如何处理冷启动?
- Railway/Render: 接受 30-60 秒冷启动
- 重要应用: 升级到付费实例
- 或使用 Cron 定时 ping

---

## 九、联系与支持

如有问题，请提交 Issue 或参考各平台文档:
- Railway: https://docs.railway.app
- Render: https://render.com/docs
- Docker: https://docs.docker.com
