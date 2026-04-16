<template>
  <div class="upload-page page-container">
    <!-- 顶部导航 -->
    <header class="page-header glass-effect">
      <div class="header-content">
        <div class="header-left">
          <el-button text @click="$router.push('/')">
            <el-icon><ArrowLeft /></el-icon>
            返回首页
          </el-button>
        </div>
        <h2 class="page-title">上传素材</h2>
        <div class="header-right">
          <span class="step-indicator">步骤 1/3</span>
        </div>
      </div>
    </header>

    <!-- 步骤指示器 -->
    <div class="step-bar">
      <div class="step-item active">
        <div class="step-dot"></div>
        <span>上传素材</span>
      </div>
      <div class="step-line"></div>
      <div class="step-item">
        <div class="step-dot"></div>
        <span>编辑配置</span>
      </div>
      <div class="step-line"></div>
      <div class="step-item">
        <div class="step-dot"></div>
        <span>下载成品</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="upload-content">
      <div class="upload-main">
        <!-- 项目名称 -->
        <div class="project-name-section">
          <el-input
            v-model="projectName"
            placeholder="请输入项目名称"
            size="large"
            :prefix-icon="Edit"
            class="project-input"
          />
        </div>

        <!-- 视频上传区 -->
        <div class="upload-section">
          <div class="section-header">
            <h3>
              <el-icon><VideoPlay /></el-icon>
              视频片段上传
            </h3>
            <span class="section-tip">支持 MP4、MOV、AVI 格式，单个文件最大 500MB</span>
          </div>
          
          <div
            class="upload-zone"
            :class="{ dragover: videoDragover }"
            @dragover.prevent="videoDragover = true"
            @dragleave="videoDragover = false"
            @drop.prevent="handleVideoDrop"
            @click="triggerVideoUpload"
          >
            <el-upload
              ref="videoUploadRef"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleVideoChange"
              :multiple="true"
              accept="video/*"
              class="video-upload-trigger"
            >
              <div class="upload-icon">
                <el-icon :size="48"><Upload /></el-icon>
              </div>
              <p class="upload-text">拖拽视频文件到此处，或<span>点击上传</span></p>
              <p class="upload-hint">支持批量上传，建议上传与剧本匹配的视频片段</p>
            </el-upload>
          </div>

          <!-- 视频列表 -->
          <div v-if="videoClips.length > 0" class="video-list">
            <div class="list-header">
              <span>已上传 {{ videoClips.length }} 个视频</span>
              <el-button text type="danger" @click="clearAllVideos">
                <el-icon><Delete /></el-icon>
                清空全部
              </el-button>
            </div>
            <div class="video-items">
              <div
                v-for="(clip, index) in videoClips"
                :key="clip.id"
                class="video-item"
                draggable="true"
                @dragstart="handleDragStart(index)"
                @dragover.prevent="handleDragOver(index)"
                @dragend="handleDragEnd"
              >
                <div class="drag-handle">
                  <el-icon><Rank /></el-icon>
                </div>
                <div class="video-thumb">
                  <el-icon :size="32"><VideoPlay /></el-icon>
                </div>
                <div class="video-info">
                  <p class="video-name">{{ clip.name }}</p>
                  <p class="video-meta">{{ formatFileSize(clip.size) }} · {{ clip.duration || '未知时长' }}</p>
                </div>
                <div class="video-status" :class="clip.status">
                  <el-progress
                    v-if="clip.status === 'uploading'"
                    :percentage="clip.progress || 0"
                    :stroke-width="3"
                    :show-text="false"
                    width="40"
                    type="circle"
                  />
                  <el-icon v-else-if="clip.status === 'uploading'"><Loading /></el-icon>
                  <el-icon v-else-if="clip.status === 'done'"><Check /></el-icon>
                  <el-icon v-else-if="clip.status === 'error'" color="#F56C6C"><Close /></el-icon>
                  <span v-else-if="clip.status === 'done'">就绪</span>
                </div>
                <el-button
                  class="remove-btn"
                  text
                  type="danger"
                  @click.stop="removeVideo(clip.id)"
                >
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 剧本上传区 -->
        <div class="upload-section">
          <div class="section-header">
            <h3>
              <el-icon><Document /></el-icon>
              分镜剧本上传
            </h3>
            <span class="section-tip">支持 TXT、DOCX 格式，剧本将用于AI智能剪辑</span>
          </div>
          
          <div
            class="upload-zone script-zone"
            :class="{ dragover: scriptDragover, 'has-file': scriptFile }"
            @dragover.prevent="scriptDragover = true"
            @dragleave="scriptDragover = false"
            @drop.prevent="handleScriptDrop"
            @click="triggerScriptUpload"
          >
            <template v-if="!scriptFile">
              <el-upload
                ref="scriptUploadRef"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleScriptChange"
                accept=".txt,.docx"
              >
                <div class="upload-icon">
                  <el-icon :size="48"><Document /></el-icon>
                </div>
                <p class="upload-text">拖拽剧本文件到此处，或<span>点击上传</span></p>
                <p class="upload-hint">上传分镜剧本，AI将根据剧本内容智能剪辑</p>
              </el-upload>
            </template>
            <template v-else>
              <div class="file-preview">
                <el-icon :size="48" color="#67C23A"><DocumentChecked /></el-icon>
                <p class="file-name">{{ scriptFile.name }}</p>
                <p class="file-size">{{ formatFileSize(scriptFile.size) }}</p>
                <el-button type="primary" plain @click.stop="viewScript">
                  <el-icon><View /></el-icon>
                  预览内容
                </el-button>
                <el-button type="danger" plain @click.stop="removeScript">
                  <el-icon><Delete /></el-icon>
                  移除
                </el-button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 侧边栏 -->
      <aside class="upload-sidebar">
        <div class="sidebar-card">
          <h4>上传须知</h4>
          <ul>
            <li>
              <el-icon><Check /></el-icon>
              视频建议使用横屏 16:9 或竖屏 9:16 格式
            </li>
            <li>
              <el-icon><Check /></el-icon>
              视频清晰度越高，输出质量越好
            </li>
            <li>
              <el-icon><Check /></el-icon>
              剧本格式建议包含场景描述和对话内容
            </li>
            <li>
              <el-icon><Check /></el-icon>
              可以先上传少量视频测试效果
            </li>
          </ul>
        </div>

        <div class="sidebar-card tips-card">
          <h4>快速开始</h4>
          <p>准备好您的素材了吗？上传视频片段和剧本后，我们将开始智能剪辑。</p>
          <div class="quick-tips">
            <div class="tip-item">
              <span class="tip-num">1</span>
              <span>上传 3-10 个视频片段</span>
            </div>
            <div class="tip-item">
              <span class="tip-num">2</span>
              <span>上传分镜剧本</span>
            </div>
            <div class="tip-item">
              <span class="tip-num">3</span>
              <span>点击下一步开始编辑</span>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-actions glass-effect">
      <div class="actions-content">
        <el-button size="large" @click="$router.push('/')">
          上一步
        </el-button>
        <el-button
          type="primary"
          size="large"
          :disabled="!canProceed"
          @click="goToEditor"
        >
          下一步：编辑配置
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 剧本预览对话框 -->
    <el-dialog
      v-model="showScriptPreview"
      title="剧本预览"
      width="700px"
      class="script-preview-dialog"
    >
      <div class="script-preview-content">
        <pre>{{ scriptPreviewContent }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import { checkHealth } from '@/api/services/health.js'
import { uploadVideos, parseScript } from '@/api/services/upload.js'

const router = useRouter()
const store = useProjectStore()

// API连接状态
const apiConnected = ref(false)
const apiChecking = ref(true)

// 响应式数据
const projectName = ref('')
const videoClips = ref([])
const scriptFile = ref(null)
const scriptPreviewContent = ref('')
const videoDragover = ref(false)
const scriptDragover = ref(false)
const showScriptPreview = ref(false)
const draggedIndex = ref(-1)

// 上传状态
const uploadProgress = ref(0)
const isUploading = ref(false)

// 上传引用
const videoUploadRef = ref(null)
const scriptUploadRef = ref(null)

// 检查API连接
onMounted(async () => {
  try {
    await checkHealth()
    apiConnected.value = true
    ElMessage.success('已连接到后端服务')
  } catch (error) {
    apiConnected.value = false
    ElMessage.warning('无法连接到后端服务，将使用本地模式')
  } finally {
    apiChecking.value = false
  }
})

// 计算属性
const canProceed = computed(() => {
  return projectName.value.trim() && videoClips.value.length > 0
})

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化时长（秒转 MM:SS 或 HH:MM:SS）
const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hrs > 0) {
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

// 触发视频上传
const triggerVideoUpload = () => {
  videoUploadRef.value?.handleClick()
}

// 触发剧本上传
const triggerScriptUpload = () => {
  if (!scriptFile.value) {
    scriptUploadRef.value?.handleClick()
  }
}

// 处理视频文件变化
const handleVideoChange = async (file, fileList) => {
  const videoFile = {
    id: Date.now() + Math.random(),
    name: file.name,
    size: file.size,
    file: file.raw,
    url: URL.createObjectURL(file.raw),
    status: 'uploading',
    progress: 0,
    duration: ''
  }
  
  videoClips.value.push(videoFile)
  
  // 如果已连接API，则执行真实上传
  if (apiConnected.value) {
    try {
      await uploadSingleVideo(videoFile)
    } catch (error) {
      console.error('上传失败:', error)
      ElMessage.error(`视频 ${file.name} 上传失败`)
      const clip = videoClips.value.find(c => c.id === videoFile.id)
      if (clip) {
        clip.status = 'error'
      }
    }
  } else {
    // 模拟上传完成（离线模式）
    setTimeout(() => {
      const clip = videoClips.value.find(c => c.id === videoFile.id)
      if (clip) {
        clip.status = 'done'
        clip.progress = 100
        clip.duration = '00:' + String(Math.floor(Math.random() * 60)).padStart(2, '0') + ':' + String(Math.floor(Math.random() * 60)).padStart(2, '0')
      }
    }, 1500)
  }
}

// 上传单个视频
const uploadSingleVideo = async (videoFile) => {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    // 后端API期望字段名为 'videos'（支持多文件数组格式）
    formData.append('files', videoFile.file)
    formData.append('project_name', projectName.value || '未命名项目')
    
    const xhr = new XMLHttpRequest()
    // 使用相对路径，后端路由为 /upload/videos
    const apiUrl = '/upload'
    
    xhr.open('POST', apiUrl)
    
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100)
        const clip = videoClips.value.find(c => c.id === videoFile.id)
        if (clip) {
          clip.progress = percent
        }
      }
    }
    
    xhr.onload = () => {
      const clip = videoClips.value.find(c => c.id === videoFile.id)
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText)
          if (response.success) {
            // 从后端返回的 videos 数组中获取第一个视频的信息
            const videoInfo = response.data?.videos?.[0]
            if (clip) {
              clip.status = 'done'
              clip.progress = 100
              clip.serverId = videoInfo?.id || videoInfo?.filename
              clip.duration = videoInfo?.duration ? formatDuration(videoInfo.duration) : clip.duration
            }
            resolve(response)
          } else {
            // 后端返回失败
            const errorMsg = response.error || response.message || '未知错误'
            if (clip) {
              clip.status = 'error'
            }
            reject(new Error(`上传失败: ${errorMsg}`))
          }
        } catch (e) {
          console.error('解析响应失败:', e)
          if (clip) {
            clip.status = 'error'
          }
          reject(new Error('解析服务器响应失败'))
        }
      } else {
        // HTTP错误，尝试解析错误信息
        let errorMsg = `HTTP错误: ${xhr.status}`
        try {
          const errorResponse = JSON.parse(xhr.responseText)
          if (errorResponse.error) {
            errorMsg = errorResponse.error
          } else if (errorResponse.message) {
            errorMsg = errorResponse.message
          }
        } catch {}
        
        if (clip) {
          clip.status = 'error'
        }
        reject(new Error(errorMsg))
      }
    }
    
    xhr.onerror = () => {
      const clip = videoClips.value.find(c => c.id === videoFile.id)
      if (clip) {
        clip.status = 'error'
      }
      reject(new Error('网络连接失败，请检查网络或后端服务是否可用'))
    }
    
    xhr.send(formData)
  })
}

// 处理视频拖放
const handleVideoDrop = (e) => {
  videoDragover.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('video/'))
  files.forEach(file => {
    handleVideoChange({ name: file.name, size: file.size, raw: file }, [])
  })
}

// 处理剧本拖放
const handleScriptDrop = (e) => {
  scriptDragover.value = false
  const file = e.dataTransfer.files[0]
  if (file && (file.name.endsWith('.txt') || file.name.endsWith('.docx'))) {
    handleScriptChange({ name: file.name, size: file.size, raw: file })
  } else {
    ElMessage.warning('请上传 TXT 或 DOCX 格式的剧本文件')
  }
}

// 处理剧本文件变化
const handleScriptChange = (file) => {
  scriptFile.value = {
    name: file.name,
    size: file.size,
    raw: file.raw
  }
  
  // 读取剧本内容
  const reader = new FileReader()
  reader.onload = (e) => {
    scriptPreviewContent.value = e.target.result
  }
  reader.readAsText(file.raw)
}

// 移除视频
const removeVideo = (id) => {
  videoClips.value = videoClips.value.filter(v => v.id !== id)
}

// 清空所有视频
const clearAllVideos = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有已上传的视频吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    videoClips.value = []
  } catch {
    // 用户取消
  }
}

// 移除剧本
const removeScript = () => {
  scriptFile.value = null
  scriptPreviewContent.value = ''
}

// 预览剧本
const viewScript = () => {
  showScriptPreview.value = true
}

// 拖拽排序 - 开始
const handleDragStart = (index) => {
  draggedIndex.value = index
}

// 拖拽排序 - 经过
const handleDragOver = (index) => {
  if (draggedIndex.value === -1 || draggedIndex.value === index) return
  
  const draggedItem = videoClips.value[draggedIndex.value]
  videoClips.value.splice(draggedIndex.value, 1)
  videoClips.value.splice(index, 0, draggedItem)
  draggedIndex.value = index
}

// 拖拽排序 - 结束
const handleDragEnd = () => {
  draggedIndex.value = -1
}

// 前往编辑页
const goToEditor = async () => {
  if (!canProceed.value) {
    ElMessage.warning('请输入项目名称并上传至少一个视频')
    return
  }
  
  // 保存到 store
  store.projectName = projectName.value
  store.videoClips = videoClips.value
  // 设置视频预览URL
  if (videoClips.value.length > 0 && videoClips.value[0].url) {
    store.videoUrl = videoClips.value[0].url
  }
  
  // 如果有剧本且已连接API，尝试解析
  if (scriptFile.value && apiConnected.value) {
    try {
      ElMessage.info('正在解析剧本...')
      const parseResult = await parseScript(scriptPreviewContent.value)
      store.scriptParsedResult = parseResult
      ElMessage.success('剧本解析完成')
    } catch (error) {
      console.error('剧本解析失败:', error)
      ElMessage.warning('剧本解析失败，将使用原始内容')
    }
  }
  
  if (scriptFile.value) {
    store.setScript(scriptFile.value, scriptPreviewContent.value)
  }
  
  router.push('/editor')
}
</script>

<style lang="scss" scoped>
.upload-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-bottom: 80px;
}

// 顶部导航
.page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0 40px;
  
  .header-content {
    max-width: 1400px;
    margin: 0 auto;
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .page-title {
    font-size: 18px;
    font-weight: 600;
  }
  
  .step-indicator {
    color: #409EFF;
    font-weight: 500;
  }
}

// 步骤条
.step-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px 40px;
  gap: 0;
  
  .step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    
    .step-dot {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #666;
        transition: all 0.3s;
      }
    }
    
    span {
      font-size: 14px;
      color: #888;
    }
    
    &.active {
      .step-dot {
        background: #409EFF;
        
        &::after {
          background: #fff;
        }
      }
      
      span {
        color: #409EFF;
      }
    }
  }
  
  .step-line {
    width: 100px;
    height: 2px;
    background: rgba(255, 255, 255, 0.1);
    margin: 0 20px;
    margin-bottom: 24px;
  }
}

// 主内容区
.upload-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 40px 40px;
  width: 100%;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.upload-main {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

// 项目名称
.project-name-section {
  .project-input {
    :deep(.el-input__wrapper) {
      height: 56px;
      font-size: 16px;
    }
  }
}

// 上传区块
.upload-section {
  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    
    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
    }
    
    .section-tip {
      font-size: 14px;
      color: #888;
    }
  }
}

// 上传区域
.upload-zone {
  transition: all 0.3s;
  
  &.script-zone {
    min-height: 200px;
  }
  
  &.has-file {
    background: rgba(103, 194, 58, 0.1);
    border-color: #67C23A;
  }
  
  .upload-icon {
    color: #409EFF;
    margin-bottom: 16px;
  }
  
  .upload-text {
    font-size: 16px;
    margin-bottom: 8px;
    
    span {
      color: #409EFF;
      cursor: pointer;
    }
  }
  
  .upload-hint {
    font-size: 14px;
    color: #888;
  }
}

.video-upload-trigger {
  width: 100%;
}

// 文件预览
.file-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  
  .file-name {
    font-size: 16px;
    font-weight: 500;
  }
  
  .file-size {
    font-size: 14px;
    color: #888;
  }
  
  .el-button {
    margin-top: 8px;
  }
}

// 视频列表
.video-list {
  margin-top: 24px;
  
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px 8px 0 0;
    font-size: 14px;
    color: #888;
  }
  
  .video-items {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-top: none;
    border-radius: 0 0 8px 8px;
    overflow: hidden;
  }
}

.video-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(15, 52, 96, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  cursor: grab;
  transition: background 0.2s;
  
  &:hover {
    background: rgba(15, 52, 96, 0.5);
  }
  
  &:last-child {
    border-bottom: none;
  }
  
  &:active {
    cursor: grabbing;
  }
  
  .drag-handle {
    color: #666;
    cursor: grab;
  }
  
  .video-thumb {
    width: 64px;
    height: 48px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #888;
  }
  
  .video-info {
    flex: 1;
    
    .video-name {
      font-size: 14px;
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .video-meta {
      font-size: 12px;
      color: #888;
    }
  }
  
  .video-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    
    &.uploading {
      color: #409EFF;
    }
    
    &.done {
      color: #67C23A;
    }
  }
  
  .remove-btn {
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  &:hover .remove-btn {
    opacity: 1;
  }
}

// 侧边栏
.upload-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
  
  @media (max-width: 1024px) {
    display: none;
  }
}

.sidebar-card {
  background: rgba(15, 52, 96, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 24px;
  
  h4 {
    font-size: 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    
    li {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 8px 0;
      font-size: 14px;
      color: #b0b0b0;
      line-height: 1.5;
      
      .el-icon {
        color: #67C23A;
        flex-shrink: 0;
        margin-top: 2px;
      }
    }
  }
}

.tips-card {
  p {
    font-size: 14px;
    color: #888;
    line-height: 1.6;
    margin-bottom: 20px;
  }
  
  .quick-tips {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .tip-item {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    color: #b0b0b0;
    
    .tip-num {
      width: 24px;
      height: 24px;
      background: rgba(64, 158, 255, 0.2);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      color: #409EFF;
      font-weight: 600;
    }
  }
}

// 底部操作栏
.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 40px;
  
  .actions-content {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
  }
}

// 剧本预览
.script-preview-content {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
  
  pre {
    margin: 0;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-wrap: break-word;
    color: #b0b0b0;
  }
}
</style>
