@echo off
chcp 65001 >nul
echo ========================================
echo    漫剧短剧剪辑工具 - 一键启动
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b
)

echo ✅ Python已安装
echo.

REM 检查依赖
echo 🔍 检查依赖...
python -c "import moviepy" 2>nul
if errorlevel 1 (
    echo 📦 正在安装依赖...
    pip install moviepy pydub pillow numpy
    echo.
)

echo ✅ 依赖检查完成
echo.

REM 创建必要目录
if not exist "videos" mkdir videos
if not exist "output" mkdir output

echo 📁 目录结构:
echo    videos/  - 放入视频文件
echo    output/  - 输出成片
echo.

REM 检查视频文件
dir /b videos\*.mp4 videos\*.avi videos\*.mov 2>nul | findstr /r ".*" >nul
if errorlevel 1 (
    echo ⚠️  videos文件夹为空，请先放入视频文件
    echo.
    explorer videos
    pause
    exit /b
)

echo 🚀 启动剪辑工具...
echo.
python 剪辑工具.py

echo.
pause
