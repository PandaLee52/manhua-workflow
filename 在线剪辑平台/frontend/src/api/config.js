/**
 * API 配置文件
 * 配置后端服务器地址
 */

// 后端API地址
const API_BASE_URL = 'https://manhua-workflow-1.onrender.com'

// API端点配置
const API_ENDPOINTS = {
  // 健康检查
  HEALTH: '/health',
  
  // 视频上传
  UPLOAD: '/upload',
  
  // 剧本解析
  PARSE: '/parse',
  
  // 视频处理
  PROCESS: '/process',
  
  // 进度查询
  PROGRESS: '/progress',
  
  // BGM搜索
  SEARCH_BGM: '/search-bgm',
  
  // 下载
  DOWNLOAD: '/download'
}

export { API_BASE_URL, API_ENDPOINTS }
