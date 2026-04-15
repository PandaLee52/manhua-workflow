#!/usr/bin/env python3
"""
在线剪辑平台 - API测试脚本
测试所有API端点
"""

import os
import sys
import time
import json
import tempfile
import requests
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8890"
TIMEOUT = 30

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, passed, message=""):
    """打印测试结果"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  [{status}] {name}")
    if message and not passed:
        print(f"       {Colors.YELLOW}{message}{Colors.RESET}")

def test_health():
    """测试健康检查"""
    print(f"\n{Colors.BLUE}[1] 健康检查{Colors.RESET}")
    
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        data = r.json()
        
        passed = r.status_code == 200 and data.get("success") == True
        print_test("GET /api/health", passed, data.get("error") if not passed else "")
        
        if data.get("data"):
            print(f"       服务: {data['data'].get('service')}")
            print(f"       版本: {data['data'].get('version')}")
            status = data['data'].get('api_status', {})
            print(f"       FFmpeg: {'✓' if status.get('ffmpeg') else '✗'}")
            print(f"       Redis: {'✓' if status.get('redis') else '✗'}")
        
        return passed
    except Exception as e:
        print_test("GET /api/health", False, str(e))
        return False

def test_upload_video():
    """测试视频上传"""
    print(f"\n{Colors.BLUE}[2] 视频上传{Colors.RESET}")
    
    # 创建临时视频文件（模拟）
    try:
        # 尝试找一个测试视频文件
        test_files = list(Path(".").glob("**/*.mp4"))[:1]
        
        if test_files:
            video_path = str(test_files[0])
            print(f"       使用测试文件: {video_path}")
        else:
            # 创建一个小的测试文件（作为占位符）
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b'\x00\x00\x00\x1c\x66\x74\x79\x70')  # MP4文件头
                video_path = f.name
            print(f"       创建占位测试文件")
        
        with open(video_path, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/upload/videos",
                files={"videos": f},
                timeout=TIMEOUT
            )
        
        data = r.json()
        passed = r.status_code == 200 and data.get("success") == True
        print_test("POST /upload/videos", passed, data.get("error") if not passed else "")
        
        if passed:
            videos = data.get("data", {}).get("videos", [])
            print(f"       上传数量: {len(videos)}")
            video_id = videos[0].get("id") if videos else None
            return video_id
        
        return None
        
    except Exception as e:
        print_test("POST /upload/videos", False, str(e))
        return None
    finally:
        # 清理临时文件
        if 'video_path' in locals() and os.path.exists(video_path):
            try:
                os.unlink(video_path)
            except:
                pass

def test_upload_script():
    """测试剧本上传"""
    print(f"\n{Colors.BLUE}[3] 剧本上传{Colors.RESET}")
    
    try:
        script_content = """
## 第1集：意外相遇

**场景**：繁华都市街道

| 镜头 | 景别 | 画面 | 动作 | 台词 |
|------|------|------|------|------|
| 1-1 | 全景 | 城市全景 | 镜头缓慢推进 | （解说）在这个繁忙的都市... |
| 1-2 | 近景 | 咖啡店门口 | 女主推门而入 | 又是忙碌的一天... |
"""
        
        r = requests.post(
            f"{BASE_URL}/upload/script",
            json={"content": script_content, "name": "测试剧本"},
            timeout=TIMEOUT
        )
        
        data = r.json()
        passed = r.status_code == 200 and data.get("success") == True
        print_test("POST /upload/script", passed, data.get("error") if not passed else "")
        
        if passed:
            script_id = data.get("data", {}).get("id")
            print(f"       剧本ID: {script_id}")
            return script_id
        
        return None
        
    except Exception as e:
        print_test("POST /upload/script", False, str(e))
        return None

def test_search_bgm():
    """测试BGM搜索"""
    print(f"\n{Colors.BLUE}[4] BGM搜索{Colors.RESET}")
    
    try:
        # 按情绪搜索
        r = requests.post(
            f"{BASE_URL}/bgm/search",
            json={"emotion": "震撼", "limit": 3},
            timeout=TIMEOUT
        )
        
        data = r.json()
        passed = r.status_code == 200 and data.get("success") == True
        print_test("POST /bgm/search (震撼)", passed, data.get("error") if not passed else "")
        
        if passed:
            results = data.get("data", {}).get("results", [])
            print(f"       找到BGM: {len(results)}")
            for bgm in results[:3]:
                print(f"       - {bgm.get('name')} ({bgm.get('duration')}s)")
            bgm_id = results[0].get("id") if results else None
            return bgm_id
        
        return None
        
    except Exception as e:
        print_test("POST /bgm/search", False, str(e))
        return None

def test_process(video_ids, script_id=None, bgm_id=None):
    """测试剪辑处理"""
    print(f"\n{Colors.BLUE}[5] 剪辑处理{Colors.RESET}")
    
    if not video_ids:
        print_test("POST /process", False, "没有视频文件")
        return None
    
    try:
        payload = {"video_ids": video_ids}
        if script_id:
            payload["script_id"] = script_id
        if bgm_id:
            payload["bgm_id"] = bgm_id
        
        r = requests.post(
            f"{BASE_URL}/process",
            json=payload,
            timeout=TIMEOUT
        )
        
        data = r.json()
        passed = r.status_code == 200 and data.get("success") == True
        print_test("POST /process", passed, data.get("error") if not passed else "")
        
        if passed:
            task_id = data.get("data", {}).get("task_id")
            print(f"       任务ID: {task_id}")
            return task_id
        
        return None
        
    except Exception as e:
        print_test("POST /process", False, str(e))
        return None

def test_status(task_id):
    """测试状态查询"""
    print(f"\n{Colors.BLUE}[6] 状态查询{Colors.RESET}")
    
    if not task_id:
        print_test("GET /status/{id}", False, "没有任务ID")
        return None
    
    try:
        # 多次查询
        for i in range(3):
            r = requests.get(f"{BASE_URL}/status/{task_id}", timeout=TIMEOUT)
            data = r.json()
            
            if data.get("success"):
                status = data.get("data", {}).get("status")
                progress = data.get("data", {}).get("progress", 0)
                print(f"       查询 {i+1}: status={status}, progress={progress*100:.0f}%")
                
                if status in ["SUCCESS", "FAILURE"]:
                    return status
            
            time.sleep(1)
        
        print_test("GET /status/{id}", True)
        return "PROCESSING"
        
    except Exception as e:
        print_test("GET /status/{id}", False, str(e))
        return None

def test_stats():
    """测试统计接口"""
    print(f"\n{Colors.BLUE}[7] 平台统计{Colors.RESET}")
    
    try:
        r = requests.get(f"{BASE_URL}/stats", timeout=TIMEOUT)
        data = r.json()
        
        passed = r.status_code == 200 and data.get("success") == True
        print_test("GET /stats", passed, data.get("error") if not passed else "")
        
        if passed:
            stats = data.get("data", {})
            files = stats.get("files", {})
            storage = stats.get("storage", {})
            print(f"       视频: {files.get('videos')}, 剧本: {files.get('scripts')}")
            print(f"       存储: {storage.get('total_size_mb')} MB")
        
        return passed
        
    except Exception as e:
        print_test("GET /stats", False, str(e))
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("在线剪辑平台 - API测试")
    print("=" * 50)
    print(f"测试地址: {BASE_URL}")
    
    results = {}
    
    # 执行测试
    results["health"] = test_health()
    results["video_id"] = test_upload_video()
    results["script_id"] = test_upload_script()
    results["bgm_id"] = test_search_bgm()
    results["task_id"] = test_process(
        [results["video_id"]] if results["video_id"] else None,
        results.get("script_id"),
        results.get("bgm_id")
    )
    
    if results["task_id"]:
        results["task_status"] = test_status(results["task_id"])
    
    results["stats"] = test_stats()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    if results["video_id"]:
        print(f"  视频ID: {results['video_id']}")
    if results["script_id"]:
        print(f"  剧本ID: {results['script_id']}")
    if results["bgm_id"]:
        print(f"  BGM ID: {results['bgm_id']}")
    if results["task_id"]:
        print(f"  任务ID: {results['task_id']}")
        print(f"  任务状态: {results.get('task_status', 'unknown')}")
    
    passed = sum(1 for k, v in results.items() if v and k not in ["task_status"])
    total = len([k for k in results if k != "task_status"])
    
    print(f"\n  通过: {passed}/{total}")
    print("=" * 50)

if __name__ == "__main__":
    main()
