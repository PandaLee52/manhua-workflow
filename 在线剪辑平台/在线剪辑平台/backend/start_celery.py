#!/usr/bin/env python3
"""
在线剪辑平台 - Celery Worker启动脚本
用于独立启动异步任务处理器
"""

import os
import sys
import subprocess
import signal

# 项目目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

def signal_handler(signum, frame):
    """处理终止信号"""
    print("\n正在停止Celery Worker...")
    sys.exit(0)

def main():
    print("=" * 50)
    print("在线剪辑平台 - Celery Worker")
    print("=" * 50)
    print("工作目录:", PROJECT_DIR)
    print("日志级别: INFO")
    print("池类型: solo (单进程)")
    print("=" * 50)
    print("")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动Celery
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "tasks",
        "worker",
        "--loglevel=INFO",
        "--pool=solo",
        "--concurrency=1"
    ]
    
    print("执行命令:", " ".join(cmd))
    print("")
    print("按 Ctrl+C 停止 Worker")
    print("-" * 50)
    
    try:
        subprocess.run(cmd, cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        print("\nWorker已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
