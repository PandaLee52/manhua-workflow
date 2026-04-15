# ========================================
# 在线剪辑平台 - Render 部署配置
# ========================================

## Render 简介
Render 是一个功能全面的 PaaS 平台，免费层支持 Web 服务和 PostgreSQL。

## 免费额度
- ✅ 750 小时/月 Free Web 服务
- ✅ 1 个 Free PostgreSQL (1GB, 30天后过期)
- ✅ 自动 HTTPS
- ✅ GitHub 集成
- ⚠️ 15分钟空闲后休眠

## 重要限制
- **休眠问题**: 免费服务 15 分钟无请求会休眠，下次请求需要 30-60 秒唤醒
- **数据库过期**: Free PostgreSQL 30 天后过期，需手动续期
- **单数据库限制**: 每个工作区只能有 1 个 Free PostgreSQL

## 部署步骤

### 1. 创建 Render 账号
1. 访问 https://render.com
2. 使用 GitHub 登录
3. 授权访问仓库

### 2. 部署 Web 服务
1. 点击 "New +" → "Web Service"
2. 选择 GitHub 仓库
3. 配置服务：

| 配置项 | 值 |
|--------|-----|
| Name | `video-platform` |
| Region | Oregon (或最近区域) |
| Branch | `main` |
| Root Directory | `deploy` (如果 Dockerfile 在 deploy 目录) |
| Runtime | `Docker` |
| Instance Type | `Free` |

4. 设置环境变量：

```env
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
PORT=10000
```

5. 点击 "Create Web Service"

### 3. 部署 PostgreSQL (可选)
1. 点击 "New +" → "PostgreSQL"
2. 配置：

| 配置项 | 值 |
|--------|-----|
| Name | `video-db` |
| Database | `video_platform` |
| Plan | `Free` |

3. 创建后复制 `Internal Database URL`

4. 返回 Web 服务，添加环境变量：

```env
DATABASE_URL=<粘贴 PostgreSQL Internal Database URL>
```

### 4. 初始化数据库
1. 进入 Web 服务 → "Shell" 标签
2. 运行数据库迁移：

```bash
flask db upgrade
# 或
python -c "from app import db; db.create_all()"
```

### 5. 配置自定义域名 (可选)
1. 进入服务 → Settings → Custom Domains
2. 添加你的域名
3. 按提示配置 DNS

## Render Blueprint (推荐)

创建 `render.yaml` 实现一键部署：

```yaml
services:
  - type: web
    name: video-platform
    dockerfilePath: ./deploy/Dockerfile
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: video-db
          property: connectionString

databases:
  - name: video-db
    databaseName: video_platform
    plan: free
```

部署命令：
```bash
render blueprint render.yaml
```

## 故障排除

**Q: 服务休眠后访问很慢**
- 这是免费层的限制，无法完全避免
- 可以考虑升级到 paid 实例 ($7/月不断开)

**Q: PostgreSQL 过期**
- Render 会提前 7 天发邮件提醒
- 在数据库页面点击 "Upgrade" 选择付费计划
- 或创建新数据库并更新环境变量

**Q: 部署失败**
- 检查 Dockerfile 语法
- 查看 Build Logs
- 确保 Python 版本兼容

## 成本对比

| 方案 | 月费用 | 说明 |
|------|--------|------|
| Free | $0 | 750小时，15分钟休眠 |
| Starter | $7/月 | 不断开，适合生产 |
| Plus | $25/月 | 2GB RAM，高并发 |
