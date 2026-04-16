/**
 * Vercel Serverless Functions 示例
 * 用于概念验证 - 实际视频处理仍需部署到Railway/Render
 */

// ==================== 健康检查 ====================
// 访问: /api/health

export default function handler(req, res) {
  res.status(200).json({
    success: true,
    data: {
      service: "在线剪辑平台 API",
      version: "1.0.0",
      status: "running",
      serverless: true,
      timestamp: new Date().toISOString()
    }
  });
}
