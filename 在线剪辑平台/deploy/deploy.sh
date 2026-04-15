#!/bin/bash
# =========================================
# 在线剪辑平台 - 一键部署脚本
# =========================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   在线剪辑平台 - 一键部署脚本${NC}"
echo -e "${GREEN}=========================================${NC}"

# 检测平台
detect_platform() {
    if command -v railway &> /dev/null; then
        echo "detected: railway"
        deploy_railway
    elif [ -n "$RENDER" ]; then
        echo "detected: render"
        deploy_render
    elif command -v docker &> /dev/null; then
        echo "detected: docker"
        deploy_docker
    else
        echo -e "${RED}未检测到支持的部署工具${NC}"
        echo "请安装以下工具之一:"
        echo "  - Railway CLI: npm install -g @railway/cli"
        echo "  - Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
}

# Railway 部署
deploy_railway() {
    echo -e "${YELLOW}使用 Railway 部署...${NC}"
    
    railway login
    railway init
    railway up
    
    echo -e "${GREEN}Railway 部署完成!${NC}"
    echo "运行 'railway logs' 查看日志"
    echo "运行 'railway open' 打开控制台"
}

# Render 部署 (使用 Blueprint)
deploy_render() {
    echo -e "${YELLOW}使用 Render Blueprint 部署...${NC}"
    
    if ! command -v render &> /dev/null; then
        echo -e "${RED}请先安装 Render CLI:${NC}"
        echo "npm install -g @render/render-cli"
        exit 1
    fi
    
    render blueprints apply deploy/render.yaml
    
    echo -e "${GREEN}Render 部署完成!${NC}"
}

# Docker 部署
deploy_docker() {
    echo -e "${YELLOW}使用 Docker 部署...${NC}"
    
    cd deploy
    
    # 检查 docker-compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}请安装 docker-compose:${NC}"
        echo "https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 复制环境变量示例
    if [ ! -f .env ]; then
        echo -e "${YELLOW}创建 .env 文件...${NC}"
        cp ../.env.example .env 2>/dev/null || true
        echo -e "${YELLOW}请编辑 .env 文件配置环境变量${NC}"
    fi
    
    # 构建并启动
    echo -e "${YELLOW}构建并启动服务...${NC}"
    docker-compose up --build -d
    
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}   Docker 部署完成!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo -e "应用地址: ${YELLOW}http://localhost:8000${NC}"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --railway    使用 Railway 部署"
    echo "  --render     使用 Render 部署"
    echo "  --docker     使用 Docker 部署"
    echo "  --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 自动检测平台"
    echo "  $0 --railway    # 强制使用 Railway"
    echo "  $0 --docker     # 强制使用 Docker"
}

# 主逻辑
case "${1:-}" in
    --railway)
        deploy_railway
        ;;
    --render)
        deploy_render
        ;;
    --docker)
        deploy_docker
        ;;
    --help)
        show_help
        ;;
    *)
        detect_platform
        ;;
esac
