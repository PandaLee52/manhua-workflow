# AI智能剪辑平台 - 前端项目

## 项目概述

这是一个专业的在线视频剪辑平台前端界面，采用了现代、简洁的设计风格，参考了剪映/PR等专业剪辑软件的设计理念。

## 功能特点

### 完整的工作流程
1. **首页** - 项目介绍、功能展示、价格方案
2. **上传页** - 视频片段和分镜剧本上传，支持拖拽
3. **编辑页** - 视频预览、时间轴、BGM选择、字幕设置、输出配置
4. **进度页** - 实时处理进度展示
5. **下载页** - 多格式下载、社交平台分享

### 交互特性
- ✅ 拖拽上传文件
- ✅ 批量上传支持
- ✅ 实时进度动画
- ✅ 响应式设计
- ✅ 毛玻璃效果
- ✅ 平滑过渡动画

## 技术栈

- **框架**: Vue 3 + Element Plus
- **构建工具**: Vite
- **样式**: SCSS
- **路由**: Vue Router
- **状态管理**: Pinia

## 快速开始

### 方式一：直接预览（推荐）

直接用浏览器打开 `在线剪辑平台.html` 文件即可预览完整功能。

```bash
# macOS
open ./在线剪辑平台/frontend/在线剪辑平台.html

# Windows
start ./在线剪辑平台/frontend/在线剪辑平台.html

# Linux
xdg-open ./在线剪辑平台/frontend/在线剪辑平台.html
```

### 方式二：本地开发服务器

```bash
# 进入前端目录
cd ./在线剪辑平台/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

### 方式三：打包构建

```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 项目结构

```
frontend/
├── package.json          # 项目配置
├── vite.config.js       # Vite 配置
├── index.html           # 入口 HTML
├── src/
│   ├── main.js         # 应用入口
│   ├── App.vue         # 根组件
│   ├── router/
│   │   └── index.js   # 路由配置
│   ├── stores/
│   │   └── project.js  # Pinia 状态管理
│   ├── views/
│   │   ├── HomePage.vue      # 首页
│   │   ├── UploadPage.vue    # 上传页
│   │   ├── EditorPage.vue    # 编辑页
│   │   ├── ProgressPage.vue  # 进度页
│   │   └── DownloadPage.vue # 下载页
│   └── assets/
│       └── styles/
│           └── main.scss     # 全局样式
└── 在线剪辑平台.html    # 可直接预览的完整HTML
```

## 设计规范

### 配色方案
- **主色**: `#409EFF` (Element Plus 蓝)
- **成功**: `#67C23A` (绿色)
- **警告**: `#E6A23C` (橙色)
- **危险**: `#F56C6C` (红色)
- **背景**: `#1a1a2e` ~ `#16213e` (深蓝渐变)
- **卡片**: `rgba(15, 52, 96, 0.8)` (半透明蓝)

### 字体
- 主字体: PingFang SC, Microsoft YaHei, Helvetica Neue, Helvetica, Arial, sans-serif

### 圆角
- 小元素: `8px`
- 卡片: `12px ~ 16px`
- 按钮: `8px`

## 响应式断点

- **桌面**: `> 1200px` - 双栏布局
- **平板**: `768px ~ 1200px` - 自适应布局
- **手机**: `< 768px` - 单栏布局

## 浏览器兼容性

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 后续扩展

- 对接后端 API 实现真实上传和处理
- 添加用户认证系统
- 实现项目保存和加载功能
- 添加更多视频编辑功能（剪辑、滤镜等）
- 支持更多输出格式和分辨率

## License

MIT
