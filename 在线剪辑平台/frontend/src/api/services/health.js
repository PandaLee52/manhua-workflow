/**
 * 健康检查服务
 */

import { get } from '../request.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 检查后端服务状态
 * @returns {Promise<Object>} 服务状态信息
 */
export async function checkHealth() {
  try {
    const response = await get(API_ENDPOINTS.HEALTH)
    return response
  } catch (error) {
    console.error('健康检查失败:', error)
    throw error
  }
}
