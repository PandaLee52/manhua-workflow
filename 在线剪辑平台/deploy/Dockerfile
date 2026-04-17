# 在线剪辑平台 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制所有文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 切换工作目录到backend，这样相对导入可以正常工作
WORKDIR /app
CMD ["python", "backend/app.py"]
