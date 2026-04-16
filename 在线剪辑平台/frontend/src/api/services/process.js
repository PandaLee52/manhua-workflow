/**
 * 视频处理服务
 */

import { post, get } from '../request.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 开始视频处理
 * @param {Object} params - 处理参数
 * @param {string} params.projectId - 项目ID
 * @param {Object[]} params.videoIds - 视频ID列表
 * @param {Object} params.config - 处理配置（BGM、字幕等）
 * @returns {Promise<Object>} 处理任务信息
 */
export async function startProcessing(params) {
  const response = await post(API_ENDPOINTS.PROCESS, params)
  return response
}

/**
 * 获取处理进度
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 进度信息
 */
export async function getProcessingProgress(taskId) {
  const response = await get(API_ENDPOINTS.PROGRESS, { task_id: taskId })
  return response
}

/**
 * 获取下载链接
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 下载信息
 */
export async function getDownloadUrl(taskId) {
  const response = await get(API_ENDPOINTS.DOWNLOAD, { task_id: taskId })
  return response
}

/**
 * 取消处理任务
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 取消结果
 */
export async function cancelProcessing(taskId) {
  const response = await post('/cancel', { task_id: taskId })
  return response
}
