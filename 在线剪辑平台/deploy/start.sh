#!/bin/bash
# 启动脚本 - 确保静态文件正确

cd /app

# 检查static目录
if [ ! -d "static" ]; then
    echo "ERROR: static目录不存在"
    exit 1
fi

echo "静态文件列表:"
ls -la static/

echo "启动服务..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 backend.app:app
