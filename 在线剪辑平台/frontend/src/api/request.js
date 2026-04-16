/**
 * HTTP 请求工具
 * 基于 fetch API 封装
 */

import { API_BASE_URL } from './config.js'

/**
 * 通用请求方法
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求配置
 * @returns {Promise<Object>} 响应数据
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  }
  
  // 如果是FormData，不设置Content-Type
  if (options.body instanceof FormData) {
    delete defaultOptions.headers['Content-Type']
  }
  
  try {
    const response = await fetch(url, defaultOptions)
    
    // 解析响应
    const contentType = response.headers.get('content-type')
    let data
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }
    
    // 检查响应状态
    if (!response.ok) {
      const errorMsg = data?.error || data?.message || `请求失败: ${response.status}`
      throw new Error(errorMsg)
    }
    
    return data
  } catch (error) {
    console.error('API请求错误:', error)
    throw error
  }
}

/**
 * GET 请求
 */
export async function get(endpoint, params = {}) {
  const queryString = new URLSearchParams(params).toString()
  const url = queryString ? `${endpoint}?${queryString}` : endpoint
  return request(url, { method: 'GET' })
}

/**
 * POST 请求
 */
export async function post(endpoint, data = {}) {
  return request(endpoint, {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

/**
 * POST FormData 请求（用于文件上传）
 */
export async function postFormData(endpoint, formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const url = `${API_BASE_URL}${endpoint}`
    
    xhr.open('POST', url)
    
    // 上传进度回调
    if (onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100)
          onProgress(percent)
        }
      }
    }
    
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText)
          resolve(data)
        } catch {
          resolve(xhr.responseText)
        }
      } else {
        try {
          const data = JSON.parse(xhr.responseText)
          reject(new Error(data?.error || data?.message || `上传失败: ${xhr.status}`))
        } catch {
          reject(new Error(`上传失败: ${xhr.status}`))
        }
      }
    }
    
    xhr.onerror = () => {
      reject(new Error('网络连接失败'))
    }
    
    xhr.send(formData)
  })
}

export { request }
