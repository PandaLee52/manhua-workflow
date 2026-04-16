/**
 * 视频上传服务
 */

import { postFormData, post } from '../request.js'
import { API_ENDPOINTS } from '../config.js'

/**
 * 上传视频文件
 * @param {File} file - 视频文件
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<Object>} 上传结果
 */
export async function uploadVideo(file, onProgress) {
  const formData = new FormData()
  formData.append('video', file)
  
  const response = await postFormData(API_ENDPOINTS.UPLOAD, formData, onProgress)
  return response
}

/**
 * 上传多个视频文件
 * @param {File[]} files - 视频文件数组
 * @param {Function} onProgress - 总进度回调
 * @param {Function} onFileProgress - 单文件进度回调
 * @returns {Promise<Object[]>} 上传结果数组
 */
export async function uploadVideos(files, onProgress, onFileProgress) {
  const results = []
  let completed = 0
  
  for (const file of files) {
    const result = await uploadVideo(file, (percent) => {
      const totalProgress = Math.round(
        ((completed * 100 + percent) / files.length)
      )
      onProgress?.(totalProgress)
      onFileProgress?.(file.name, percent)
    })
    results.push(result)
    completed++
  }
  
  return results
}

/**
 * 上传剧本文件
 * @param {File} file - 剧本文件
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<Object>} 上传结果
 */
export async function uploadScript(file, onProgress) {
  const formData = new FormData()
  formData.append('script', file)
  
  const response = await postFormData('/upload-script', formData, onProgress)
  return response
}

/**
 * 解析剧本内容
 * @param {string} content - 剧本文本内容
 * @returns {Promise<Object>} 解析结果
 */
export async function parseScript(content) {
  const response = await post(API_ENDPOINTS.PARSE, { content })
  return response
}
