# 在线剪辑平台 Dockerfile - Render最佳实践
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件（利用缓存）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有文件
COPY . .

# 暴露端口（Render使用PORT环境变量）
EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# 使用gunicorn启动Flask（Render最佳实践）
CMD ["sh", "-c", "cd backend && gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 app:app"]
