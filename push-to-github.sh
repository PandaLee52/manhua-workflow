#!/bin/bash
# GitHub推送脚本 - 请在manhua-workflow-full目录下执行

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "AI漫剧工作流平台v4.0 - 支持永久保存和多用户协作"

# 设置主分支
git branch -M main

# 添加远程仓库（请替换为你的用户名）
git remote add origin https://github.com/PandaLee52/manhua-workflow.git

# 推送到GitHub
git push -u origin main

echo "✅ 代码已成功推送到GitHub！"
echo "仓库地址: https://github.com/PandaLee52/manhua-workflow"
