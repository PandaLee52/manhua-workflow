# ========================================
# 在线剪辑平台 - 本地 Docker 部署
# ========================================

## 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM 可用

## 快速开始

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd 在线剪辑平台
```

### 2. 配置环境变量
```bash
# 创建 .env 文件
cat > .env << EOF
SECRET_KEY=your-production-secret-key-change-this
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/dbname
EOF
```

### 3. 启动服务
```bash
# 进入部署目录
cd deploy

# 构建并启动 (前台运行)
docker-compose up --build

# 或后台运行
docker-compose up --build -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f web
```

### 4. 访问应用
- 主应用: http://localhost:8000
- Redis: localhost:6379

## 常用命令

```bash
# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 重启服务
docker-compose restart

# 重新构建 (代码更新后)
docker-compose up --build -d

# 查看运行状态
docker-compose ps

# 进入容器 shell
docker-compose exec web bash

# 查看资源使用
docker stats
```

## 生产部署配置

### 使用 Docker Machine (单服务器)
```bash
# 创建 Docker Machine
docker-machine create --driver digitalocean --digitalocean-access-token $DO_TOKEN prod-server

# 激活环境
eval $(docker-machine env prod-server)

# 部署
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 获取服务器 IP
docker-machine ip prod-server
```

### 生产环境 docker-compose.prod.yml
```yaml
version: '3.8'

services:
  web:
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 app:app
  
  redis:
    restart: always
    command: redis-server --appendonly yes
  
  worker:
    restart: always
    deploy:
      replicas: 1
```

### Nginx 反向代理配置
```nginx
upstream video_platform {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://video_platform;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /app/static;
        expires 30d;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    # ... 同上 location 配置
}
```

### Let's Encrypt SSL 证书
```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

## 健康检查

```bash
# 检查主应用
curl http://localhost:8000/health

# 检查 Redis
docker-compose exec redis redis-cli ping

# 检查容器状态
docker-compose ps
```

## 日志管理

```bash
# 查看最近日志
docker-compose logs --tail=100

# 搜索日志
docker-compose logs | grep ERROR

# 导出日志
docker-compose logs > app.log
```

## 备份策略

```bash
# 备份 Redis 数据
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backup/

# 备份 PostgreSQL
docker-compose exec db pg_dump -U user dbname > backup.sql
```

## 性能优化

1. **使用 Docker 缓存**
   - 确保 `requirements.txt` 单独 COPY
   - 依赖层会被缓存

2. **多阶段构建**
   ```dockerfile
   # 构建阶段
   FROM python:3.11-slim as builder
   WORKDIR /app
   COPY requirements.txt .
   pip install --user -r requirements.txt
   
   # 运行阶段
   FROM python:3.11-slim
   WORKDIR /app
   COPY --from=builder /root/.local /root/.local
   COPY . .
   CMD ["gunicorn", "app:app"]
   ```

3. **资源限制**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
       reservations:
         memory: 512M
   ```

## 故障排除

**Q: 容器启动失败**
```bash
# 查看详细错误
docker-compose logs web

# 检查端口占用
lsof -i :8000

# 检查 Docker 状态
docker system df
```

**Q: Redis 连接失败**
```bash
# 检查 Redis 容器
docker-compose logs redis

# 手动测试连接
docker-compose exec redis redis-cli
```

**Q: 内存不足**
```bash
# 查看内存使用
docker stats

# 清理未使用资源
docker system prune -a
```
