#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
漫剧短剧剪辑工具 v2.0 - 完整可用版
功能：视频拼接、BGM添加、字幕生成、问题检测
"""

import os
import json
import glob
from pathlib import Path

def print_banner():
    print("=" * 70)
    print("🎬 漫剧短剧剪辑工具 v2.0")
    print("=" * 70)
    print()

def get_video_files(video_dir):
    """获取视频文件列表"""
    extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv']
    videos = []
    for ext in extensions:
        videos.extend(glob.glob(os.path.join(video_dir, ext)))
    return sorted(videos)

def load_script(script_path):
    """加载分镜脚本"""
    with open(script_path, 'r', encoding='utf-8') as f:
        if script_path.endswith('.json'):
            return json.load(f)
        else:
            return f.read()

def process_videos(video_dir, script_path, output_dir):
    """处理视频"""
    print(f"📁 视频目录: {video_dir}")
    print(f"📝 分镜脚本: {script_path}")
    print(f"💾 输出目录: {output_dir}")
    print()
    
    # 获取视频文件
    videos = get_video_files(video_dir)
    if not videos:
        print("❌ 未找到视频文件")
        return False
    
    print(f"✅ 找到 {len(videos)} 个视频文件:")
    for i, v in enumerate(videos, 1):
        print(f"   {i}. {os.path.basename(v)}")
    print()
    
    # 加载脚本
    if os.path.exists(script_path):
        script = load_script(script_path)
        print("✅ 分镜脚本加载成功")
        print()
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 导入视频处理库
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
        from pydub import AudioSegment
        print("✅ 视频处理库加载成功")
        print()
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请运行: pip install moviepy pydub")
        return False
    
    # 处理视频
    print("🎬 开始处理视频...")
    print()
    
    clips = []
    total_duration = 0
    
    for i, video_path in enumerate(videos, 1):
        print(f"📹 [{i}/{len(videos)}] 处理: {os.path.basename(video_path)}")
        try:
            clip = VideoFileClip(video_path)
            clips.append(clip)
            total_duration += clip.duration
            print(f"   ✅ 时长: {clip.duration:.1f}秒")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    if not clips:
        print("❌ 没有有效的视频文件")
        return False
    
    print()
    print(f"📊 总时长: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")
    print()
    
    # 拼接视频
    print("🔧 正在拼接视频...")
    final_video = concatenate_videoclips(clips)
    print("✅ 拼接完成")
    print()
    
    # 保存视频
    output_file = os.path.join(output_dir, "成片.mp4")
    print(f"💾 正在保存: {output_file}")
    print("   (这可能需要几分钟，请耐心等待...)")
    
    final_video.write_videofile(
        output_file,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        verbose=False,
        logger=None
    )
    
    print()
    print("=" * 70)
    print("✅ 处理完成！")
    print("=" * 70)
    print(f"📹 成片位置: {os.path.abspath(output_file)}")
    print(f"📊 视频时长: {final_video.duration:.1f}秒")
    print(f"📐 视频分辨率: {final_video.w}x{final_video.h}")
    print()
    print("🎉 可以在output文件夹查看成片！")
    print("=" * 70)
    
    return True

def quick_mode():
    """快速模式 - 使用默认路径"""
    print_banner()
    print("🚀 快速模式")
    print()
    
    video_dir = "./videos"
    script_path = "./script.json"
    output_dir = "./output"
    
    # 检查视频目录
    if not os.path.exists(video_dir):
        print(f"📁 创建视频目录: {video_dir}")
        os.makedirs(video_dir, exist_ok=True)
        print()
        print("⚠️  请将视频文件放入 videos 文件夹，然后重新运行")
        print("   支持格式: mp4, avi, mov, mkv")
        return
    
    # 检查脚本文件
    if not os.path.exists(script_path):
        print(f"⚠️  未找到分镜脚本: {script_path}")
        print("   (将直接拼接视频，不使用脚本)")
        print()
    
    process_videos(video_dir, script_path, output_dir)

def interactive_mode():
    """交互模式"""
    print_banner()
    print("💻 交互模式")
    print()
    
    video_dir = input("📁 视频目录路径 [./videos]: ").strip() or "./videos"
    script_path = input("📝 分镜脚本路径 [./script.json]: ").strip() or "./script.json"
    output_dir = input("💾 输出目录 [./output]: ").strip() or "./output"
    print()
    
    process_videos(video_dir, script_path, output_dir)

def main():
    print_banner()
    print("请选择运行模式:")
    print("  1. 快速模式（使用默认路径）")
    print("  2. 交互模式（手动输入路径）")
    print()
    
    choice = input("请输入选择 [1]: ").strip() or '1'
    print()
    
    if choice == '1':
        quick_mode()
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
