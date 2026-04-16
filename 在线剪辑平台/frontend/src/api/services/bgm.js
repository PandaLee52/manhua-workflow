/**
 * BGM搜索服务
 */

import { get } from '../request.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 搜索背景音乐
 * @param {Object} params - 搜索参数
 * @param {string} params.query - 搜索关键词
 * @param {string} params.emotion - 情绪标签
 * @param {string[]} params.tags - 标签列表
 * @param {number} params.limit - 返回数量
 * @returns {Promise<Object>} 搜索结果
 */
export async function searchBgm(params = {}) {
  const { query = '', emotion = '', tags = [], limit = 20 } = params
  
  const response = await get(API_ENDPOINTS.SEARCH_BGM, {
    q: query,
    emotion,
    tags: tags.join(','),
    limit
  })
  
  return response
}

/**
 * 获取BGM详情
 * @param {string} bgmId - BGM ID
 * @returns {Promise<Object>} BGM详情
 */
export async function getBgmDetail(bgmId) {
  const response = await get(`/bgm/${bgmId}`)
  return response
}
