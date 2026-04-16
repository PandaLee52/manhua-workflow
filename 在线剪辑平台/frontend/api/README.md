# Vercel Serverless Functions

## ⚠️ 重要说明

此目录包含 **Vercel Serverless Functions** 示例，用于轻量级API端点。

### 为什么这些是示例？

**视频剪辑平台的核心功能（上传/处理/下载）无法在此部署**，原因：

| 限制 | Vercel Serverless | 视频处理需求 |
|------|------------------|-------------|
| 执行时间 | 10秒（免费）/ 60秒 | 需要几分钟 |
| 文件系统 | 无持久化存储 | 需要存储大文件 |
| 临时存储 | 512MB | 视频文件数百MB |
| 后台任务 | 不支持 | 需要Celery Worker |

### 可用的轻量级API

| 文件 | 功能 | 说明 |
|------|------|------|
| `api/health.js` | 健康检查 | 验证服务状态 |
| `api/bgm/search.js` | BGM搜索 | 简单的BGM查询 |

### 实际部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vercel                               │
│  ├── /api/health     → Serverless ✅                    │
│  ├── /api/bgm/search → Serverless ✅                    │
│  └── /* (前端)       → 静态托管 ✅                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ API调用
                      ▼
┌─────────────────────────────────────────────────────────┐
│               Railway / Render                          │
│  ├── Flask API (完整版)                                  │
│  ├── Celery Worker                                      │
│  └── Redis Broker                                       │
└─────────────────────────────────────────────────────────┘
```

## 使用方法

### 本地开发
```bash
cd 在线剪辑平台/frontend
vercel dev
```
访问 `http://localhost:3000/api/health`

### 部署到Vercel
```bash
vercel --prod
```

## 扩展Serverless Functions

如果需要添加更多轻量级API：

1. 在 `api/` 目录创建新文件
2. 命名规范：`api/[endpoint].js`
3. 导出默认的 async function

```javascript
// api/example.js
export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  // 处理请求
  const data = { message: 'Hello' };
  
  res.status(200).json({ success: true, data });
}
```

## Serverless 函数限制

| 资源 | Hobby | Pro |
|------|-------|-----|
| 执行时间 | 10秒 | 60秒 |
| 响应大小 | 4.5MB | 4.5MB |
| 并发 | 100 | 1000 |
| 带宽 | 100GB | 1TB |

## 建议

对于视频剪辑平台：

1. ✅ 使用 **Railway** 部署完整后端
2. ✅ 使用 **Vercel** 部署前端
3. ❌ 不要尝试将视频处理逻辑放入Serverless Functions

参考完整部署指南：`../deploy/VERCEL_DEPLOY.md`
