<template>
  <div class="progress-page page-container">
    <!-- 顶部导航 -->
    <header class="page-header glass-effect">
      <div class="header-content">
        <div class="header-left">
          <el-button text @click="$router.push('/editor')">
            <el-icon><ArrowLeft /></el-icon>
            返回编辑
          </el-button>
        </div>
        <h2 class="page-title">{{ projectName || '视频处理' }}</h2>
        <div class="header-right">
          <el-tag type="warning" v-if="status === 'processing'">
            <el-icon class="is-loading"><Loading /></el-icon>
            处理中
          </el-tag>
          <el-tag type="success" v-else-if="status === 'completed'">
            <el-icon><Check /></el-icon>
            处理完成
          </el-tag>
          <el-tag type="danger" v-else-if="status === 'error'">
            <el-icon><Close /></el-icon>
            处理失败
          </el-tag>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="progress-content">
      <div class="progress-main">
        <!-- 状态卡片 -->
        <div class="status-card">
          <!-- 动画圆环 -->
          <div class="progress-ring-container">
            <svg class="progress-ring" viewBox="0 0 200 200">
              <circle
                class="progress-ring-bg"
                cx="100"
                cy="100"
                r="90"
                fill="none"
                stroke-width="12"
              />
              <circle
                class="progress-ring-fill"
                cx="100"
                cy="100"
                r="90"
                fill="none"
                stroke-width="12"
                :stroke-dasharray="565.48"
                :stroke-dashoffset="progressOffset"
              />
            </svg>
            <div class="progress-percentage">
              <span class="percentage-number">{{ Math.round(progress) }}</span>
              <span class="percentage-symbol">%</span>
            </div>
          </div>

          <!-- 状态信息 -->
          <div class="status-info">
            <h2 class="status-title">{{ statusTitle }}</h2>
            <p class="status-desc">{{ statusDesc }}</p>
          </div>

          <!-- 预估时间 -->
          <div class="time-estimate" v-if="status === 'processing'">
            <el-icon><Timer /></el-icon>
            <span>预计剩余时间: <strong>{{ remainingTime }}</strong></span>
          </div>

          <!-- 错误信息 -->
          <div class="error-info" v-if="status === 'error' && errorMessage">
            <el-icon><WarningFilled /></el-icon>
            <span>{{ errorMessage }}</span>
          </div>
        </div>

        <!-- 处理阶段 -->
        <div class="stages-card">
          <h3 class="card-title">
            <el-icon><List /></el-icon>
            处理进度
          </h3>
          
          <div class="stages-list">
            <div
              v-for="(stage, index) in stages"
              :key="stage.id"
              class="stage-item"
              :class="{
                active: stage.status === 'processing',
                completed: stage.status === 'completed',
                pending: stage.status === 'pending',
                error: stage.status === 'error'
              }"
            >
              <div class="stage-indicator">
                <div class="indicator-icon">
                  <el-icon v-if="stage.status === 'completed'"><Check /></el-icon>
                  <el-icon v-else-if="stage.status === 'processing'" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else-if="stage.status === 'error'"><Close /></el-icon>
                  <span v-else>{{ index + 1 }}</span>
                </div>
                <div class="indicator-line" v-if="index < stages.length - 1"></div>
              </div>
              
              <div class="stage-content">
                <div class="stage-header">
                  <span class="stage-name">{{ stage.name }}</span>
                  <span class="stage-status-text">{{ stage.statusText }}</span>
                </div>
                <div class="stage-progress" v-if="stage.status === 'processing'">
                  <el-progress
                    :percentage="stage.progress"
                    :stroke-width="6"
                    :show-text="true"
                    :format="(val) => val + '%'"
                  />
                </div>
                <p class="stage-desc" v-if="stage.description">{{ stage.description }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 预览区域 -->
        <div class="preview-card" v-if="showPreview">
          <h3 class="card-title">
            <el-icon><VideoPlay /></el-icon>
            实时预览
          </h3>
          <div class="preview-area">
            <div class="preview-screen">
              <template v-if="status === 'completed' && downloadUrl">
                <video 
                  :src="downloadUrl" 
                  controls 
                  class="preview-video"
                />
              </template>
              <div v-else class="preview-placeholder">
                <el-icon :size="48"><Film /></el-icon>
                <p>视频生成中...</p>
                <p class="preview-hint">处理完成后可在预览区查看效果</p>
              </div>
            </div>
            <div class="preview-controls">
              <el-button-group>
                <el-button>
                  <el-icon><RefreshLeft /></el-icon>
                </el-button>
                <el-button type="primary">
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
                <el-button>
                  <el-icon><RefreshRight /></el-icon>
                </el-button>
              </el-button-group>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button size="large" @click="cancelProcessing" v-if="status === 'processing'">
            取消处理
          </el-button>
          <el-button size="large" @click="retryProcessing" v-if="status === 'error'">
            <el-icon><Refresh /></el-icon>
            重新开始
          </el-button>
          <el-button size="large" @click="goToEditor" v-if="status === 'error'">
            返回编辑
          </el-button>
          <el-button
            type="primary"
            size="large"
            :disabled="status === 'processing'"
            @click="goToDownload"
            v-if="status === 'completed'"
          >
            下载视频
            <el-icon><Download /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 侧边栏 -->
      <aside class="progress-sidebar">
        <div class="sidebar-card">
          <h4>项目信息</h4>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">项目名称</span>
              <span class="info-value">{{ projectName || '未命名项目' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">视频片段</span>
              <span class="info-value">{{ videoCount }} 个</span>
            </div>
            <div class="info-item">
              <span class="info-label">分镜剧本</span>
              <span class="info-value">{{ hasScript ? '已上传' : '未上传' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">背景音乐</span>
              <span class="info-value">{{ selectedBgmName || '未选择' }}</span>
            </div>
          </div>
        </div>

        <div class="sidebar-card">
          <h4>输出设置</h4>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">分辨率</span>
              <span class="info-value">{{ outputSettings.resolution }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">帧率</span>
              <span class="info-value">{{ outputSettings.frameRate }} fps</span>
            </div>
            <div class="info-item">
              <span class="info-label">格式</span>
              <span class="info-value">{{ outputSettings.format?.toUpperCase() || 'MP4' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">质量</span>
              <span class="info-value">{{ qualityLabel }}</span>
            </div>
          </div>
        </div>

        <div class="sidebar-card tips-card">
          <h4>
            <el-icon><InfoFilled /></el-icon>
            处理说明
          </h4>
          <ul>
            <li>AI正在分析剧本内容</li>
            <li>智能匹配视频片段与剧本</li>
            <li>自动添加转场和特效</li>
            <li>合成背景音乐和字幕</li>
            <li>最终渲染输出成品</li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import { startProcessing, getProcessingProgress, getDownloadUrl, cancelProcessing as cancelProcessApi } from '@/api/services/process.js'

const router = useRouter()
const store = useProjectStore()

// 响应式数据
const progress = ref(0)
const status = ref('processing')
const remainingTime = ref('--:--')
const timer = ref(null)
const taskId = ref('')
const errorMessage = ref('')
const downloadUrl = ref('')

// 处理阶段
const stages = ref([
  {
    id: 1,
    name: '上传素材',
    status: 'completed',
    progress: 100,
    statusText: '已完成',
    description: '视频片段和剧本上传成功'
  },
  {
    id: 2,
    name: 'AI剧本分析',
    status: 'processing',
    progress: 0,
    statusText: '处理中...',
    description: '正在解析剧本内容，提取关键场景'
  },
  {
    id: 3,
    name: '智能剪辑',
    status: 'pending',
    progress: 0,
    statusText: '等待中',
    description: 'AI正在匹配视频片段与场景描述'
  },
  {
    id: 4,
    name: '添加转场特效',
    status: 'pending',
    progress: 0,
    statusText: '等待中',
    description: '自动添加转场效果和视觉特效'
  },
  {
    id: 5,
    name: '音频合成',
    status: 'pending',
    progress: 0,
    statusText: '等待中',
    description: '合成背景音乐，设置淡入淡出'
  },
  {
    id: 6,
    name: '字幕生成',
    status: 'pending',
    progress: 0,
    statusText: '等待中',
    description: '根据剧本生成同步字幕'
  },
  {
    id: 7,
    name: '最终渲染',
    status: 'pending',
    progress: 0,
    statusText: '等待中',
    description: '渲染输出最终视频成品'
  }
])

// 计算属性
const projectName = computed(() => store.projectName)
const videoCount = computed(() => store.videoClips.length)
const hasScript = computed(() => !!store.scriptFile)
const selectedBgmName = computed(() => store.selectedBgm?.name || '')
const outputSettings = computed(() => store.outputSettings || {
  resolution: '1080p',
  frameRate: 30,
  format: 'mp4',
  quality: 'high'
})

const qualityLabel = computed(() => {
  const labels = { fast: '快速', standard: '标准', high: '高质量' }
  return labels[outputSettings.value.quality] || '标准'
})

const showPreview = computed(() => status.value === 'completed')

const statusTitle = computed(() => {
  switch (status.value) {
    case 'processing': return '正在处理中...'
    case 'completed': return '处理完成！'
    case 'error': return '处理失败'
    default: return '准备中...'
  }
})

const statusDesc = computed(() => {
  switch (status.value) {
    case 'processing': return 'AI正在努力处理您的视频，请稍候...'
    case 'completed': return '恭喜！您的视频已处理完成，可以下载了'
    case 'error': return '处理过程中遇到问题，请重试'
    default: return ''
  }
})

// 进度环
const circumference = 2 * Math.PI * 90
const progressOffset = computed(() => {
  return circumference - (progress.value / 100) * circumference
})

// 开始处理
const startVideoProcessing = async () => {
  try {
    ElMessage.info('正在提交处理任务...')
    
    // 准备处理参数
    const videoIds = store.videoClips
      .filter(clip => clip.serverId)
      .map(clip => clip.serverId)
    
    const processParams = {
      project_id: store.projectId || `project_${Date.now()}`,
      video_ids: videoIds,
      video_count: store.videoClips.length,
      config: {
        resolution: outputSettings.value.resolution || '1080p',
        frame_rate: outputSettings.value.frameRate || 30,
        format: outputSettings.value.format || 'mp4',
        quality: outputSettings.value.quality || 'high',
        bgm: store.selectedBgm ? {
          id: store.selectedBgm.id,
          name: store.selectedBgm.name,
          url: store.selectedBgm.url,
          volume: store.bgmVolume || 80,
          fade_in: store.bgmFadeIn || 2,
          fade_out: store.bgmFadeOut || 2
        } : null,
        subtitle: store.subtitleEnabled ? {
          enabled: true,
          style: store.subtitleStyle
        } : null,
        script_parsed: store.scriptParsedResult
      }
    }
    
    // 调用后端API
    const response = await startProcessing(processParams)
    
    if (response.success) {
      taskId.value = response.data?.task_id || response.task_id
      ElMessage.success('处理任务已提交')
      startPolling()
    } else {
      throw new Error(response.error || '提交处理任务失败')
    }
  } catch (error) {
    console.error('提交处理任务失败:', error)
    errorMessage.value = error.message || '提交处理任务失败'
    status.value = 'error'
    
    // 如果API调用失败，回退到模拟进度
    ElMessage.warning('后端API不可用，将使用模拟进度')
    startSimulateProgress()
  }
}

// 轮询进度
const startPolling = () => {
  const pollInterval = setInterval(async () => {
    if (status.value !== 'processing') {
      clearInterval(pollInterval)
      return
    }
    
    try {
      const response = await getProcessingProgress(taskId.value)
      
      if (response.success && response.data) {
        const data = response.data
        
        // 更新进度
        progress.value = data.progress || 0
        
        // 更新阶段
        updateStagesFromResponse(data)
        
        // 更新剩余时间
        if (data.estimated_time) {
          remainingTime.value = formatTime(data.estimated_time)
        }
        
        // 检查是否完成
        if (data.status === 'completed') {
          clearInterval(pollInterval)
          handleProcessingComplete(data)
        } else if (data.status === 'error') {
          clearInterval(pollInterval)
          handleProcessingError(data.error || '处理失败')
        }
        
        // 更新store
        store.processingProgress = progress.value
        store.processingStatus = status.value
      }
    } catch (error) {
      console.error('轮询进度失败:', error)
      // API调用失败时切换到模拟模式
      clearInterval(pollInterval)
      ElMessage.warning('无法获取真实进度，将使用模拟进度')
      startSimulateProgress()
    }
  }, 2000)
  
  timer.value = pollInterval
}

// 从API响应更新阶段
const updateStagesFromResponse = (data) => {
  const stageMap = {
    'parsing': 1,      // AI剧本分析
    'clipping': 2,     // 智能剪辑
    'transitions': 3,  // 添加转场特效
    'audio': 4,        // 音频合成
    'subtitle': 5,     // 字幕生成
    'rendering': 6     // 最终渲染
  }
  
  const currentStage = stageMap[data.current_stage] || 1
  
  for (let i = 0; i < stages.value.length; i++) {
    if (i < currentStage) {
      stages.value[i].status = 'completed'
      stages.value[i].progress = 100
      stages.value[i].statusText = '已完成'
    } else if (i === currentStage) {
      stages.value[i].status = 'processing'
      stages.value[i].progress = data.stage_progress || 0
      stages.value[i].statusText = '处理中...'
    } else {
      stages.value[i].status = 'pending'
      stages.value[i].progress = 0
      stages.value[i].statusText = '等待中'
    }
  }
}

// 格式化时间
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${String(secs).padStart(2, '0')}`
}

// 处理完成
const handleProcessingComplete = async (data) => {
  status.value = 'completed'
  progress.value = 100
  updateAllStagesComplete()
  ElMessage.success('视频处理完成！')
  
  // 获取下载链接
  if (data.output_url) {
    downloadUrl.value = data.output_url
    store.downloadUrl = data.output_url
  } else {
    try {
      const downloadResponse = await getDownloadUrl(taskId.value)
      if (downloadResponse.success && downloadResponse.data?.url) {
        downloadUrl.value = downloadResponse.data.url
        store.downloadUrl = downloadResponse.data.url
      }
    } catch (error) {
      console.error('获取下载链接失败:', error)
    }
  }
}

// 处理错误
const handleProcessingError = (error) => {
  status.value = 'error'
  errorMessage.value = error
  ElMessage.error(`处理失败: ${error}`)
}

// 所有阶段完成
const updateAllStagesComplete = () => {
  stages.value.forEach(stage => {
    stage.status = 'completed'
    stage.progress = 100
    stage.statusText = '已完成'
  })
}

// 模拟进度（API不可用时使用）
const startSimulateProgress = () => {
  let currentStage = 1
  
  const interval = setInterval(() => {
    if (status.value !== 'processing') {
      clearInterval(interval)
      return
    }
    
    if (progress.value >= 100) {
      clearInterval(interval)
      status.value = 'completed'
      updateAllStagesComplete()
      store.processingProgress = 100
      store.processingStatus = 'completed'
      ElMessage.success('视频处理完成！')
      return
    }
    
    progress.value += Math.random() * 3
    if (progress.value > 100) progress.value = 100
    
    // 更新阶段
    const stageIndex = Math.floor((progress.value / 100) * 7)
    if (stageIndex > currentStage && currentStage < 6) {
      stages.value[currentStage].status = 'completed'
      stages.value[currentStage].progress = 100
      stages.value[currentStage].statusText = '已完成'
      currentStage = stageIndex
      if (currentStage < 6) {
        stages.value[currentStage].status = 'processing'
        stages.value[currentStage].statusText = '处理中...'
      }
    }
    
    // 更新当前阶段进度
    const stageProgress = ((progress.value % 100) / 100) * 100
    if (stages.value[currentStage]) {
      stages.value[currentStage].progress = Math.min(stageProgress, 100)
    }
    
    // 更新剩余时间
    const remaining = Math.ceil((100 - progress.value) * 1.5)
    const mins = Math.floor(remaining / 60)
    const secs = remaining % 60
    remainingTime.value = `${mins}:${String(secs).padStart(2, '0')}`
    
    store.processingProgress = progress.value
  }, 500)
  
  timer.value = interval
}

// 取消处理
const cancelProcessingHandler = async () => {
  try {
    await ElMessageBox.confirm('确定要取消视频处理吗？取消后可以重新开始。', '提示', {
      confirmButtonText: '确定取消',
      cancelButtonText: '继续处理',
      type: 'warning'
    })
    
    if (timer.value) {
      clearInterval(timer.value)
    }
    
    // 尝试调用API取消
    if (taskId.value) {
      try {
        await cancelProcessApi(taskId.value)
      } catch (error) {
        console.error('API取消失败:', error)
      }
    }
    
    status.value = 'error'
    errorMessage.value = '用户取消处理'
    ElMessage.info('已取消处理')
  } catch {
    // 用户取消
  }
}

// 重新处理
const retryProcessing = () => {
  status.value = 'processing'
  progress.value = 0
  errorMessage.value = ''
  taskId.value = ''
  downloadUrl.value = ''
  
  // 重置阶段状态
  stages.value.forEach((stage, index) => {
    if (index === 0) {
      stage.status = 'completed'
      stage.progress = 100
    } else {
      stage.status = 'pending'
      stage.progress = 0
    }
  })
  
  startVideoProcessing()
}

const goToEditor = () => {
  router.push('/editor')
}

const goToDownload = () => {
  if (downloadUrl.value) {
    // 直接下载
    const link = document.createElement('a')
    link.href = downloadUrl.value
    link.download = `${store.projectName || '视频'}.mp4`
    link.click()
  } else {
    ElMessage.warning('下载链接不可用')
  }
}

onMounted(() => {
  store.processingStatus = 'processing'
  store.processingMessage = '正在处理视频...'
  
  // 先尝试真实API，如果失败则模拟
  startVideoProcessing()
})

onUnmounted(() => {
  if (timer.value) {
    clearInterval(timer.value)
  }
})
</script>

<style lang="scss" scoped>
.progress-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

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
}

.progress-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  padding: 24px 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.progress-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.status-card {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 16px;
  padding: 40px;
  text-align: center;
}

.progress-ring-container {
  position: relative;
  width: 200px;
  height: 200px;
  margin: 0 auto 24px;
}

.progress-ring {
  transform: rotate(-90deg);
  
  .progress-ring-bg {
    stroke: rgba(255, 255, 255, 0.1);
  }
  
  .progress-ring-fill {
    stroke: #409EFF;
    stroke-linecap: round;
    transition: stroke-dashoffset 0.5s ease;
  }
}

.progress-percentage {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  
  .percentage-number {
    font-size: 48px;
    font-weight: 700;
    color: #fff;
  }
  
  .percentage-symbol {
    font-size: 24px;
    color: rgba(255, 255, 255, 0.6);
  }
}

.status-info {
  margin-bottom: 16px;
  
  .status-title {
    font-size: 24px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 8px;
  }
  
  .status-desc {
    color: rgba(255, 255, 255, 0.6);
  }
}

.time-estimate {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.6);
  
  strong {
    color: #409EFF;
  }
}

.error-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #F56C6C;
  margin-top: 16px;
}

.stages-card,
.preview-card {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 16px;
  padding: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 24px;
}

.stages-list {
  display: flex;
  flex-direction: column;
}

.stage-item {
  display: flex;
  gap: 16px;
  padding-bottom: 24px;
  
  &:last-child {
    padding-bottom: 0;
  }
}

.stage-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  
  .indicator-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    z-index: 1;
  }
  
  .indicator-line {
    flex: 1;
    width: 2px;
    background: rgba(255, 255, 255, 0.1);
    margin-top: 8px;
  }
  
  .completed & .indicator-icon {
    background: #67C23A;
    color: #fff;
  }
  
  .active & .indicator-icon {
    background: #409EFF;
    color: #fff;
  }
  
  .error & .indicator-icon {
    background: #F56C6C;
    color: #fff;
  }
  
  .completed ~ .stage-item .indicator-line,
  .completed & .indicator-line {
    background: #67C23A;
  }
}

.stage-content {
  flex: 1;
  
  .stage-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  
  .stage-name {
    font-weight: 500;
    color: #fff;
  }
  
  .stage-status-text {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
  }
  
  .stage-progress {
    margin-bottom: 8px;
  }
  
  .stage-desc {
    color: rgba(255, 255, 255, 0.4);
    font-size: 14px;
  }
}

.preview-area {
  .preview-screen {
    background: #000;
    border-radius: 8px;
    aspect-ratio: 16/9;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  
  .preview-video {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
  
  .preview-placeholder {
    text-align: center;
    color: rgba(255, 255, 255, 0.4);
    
    p {
      margin-top: 8px;
    }
    
    .preview-hint {
      font-size: 14px;
    }
  }
  
  .preview-controls {
    margin-top: 16px;
    text-align: center;
  }
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.progress-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar-card {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 16px;
  padding: 24px;
  
  h4 {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 16px;
  }
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  
  .info-label {
    color: rgba(255, 255, 255, 0.6);
  }
  
  .info-value {
    color: #fff;
    font-weight: 500;
  }
}

.tips-card {
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    
    li {
      display: flex;
      align-items: center;
      gap: 8px;
      color: rgba(255, 255, 255, 0.6);
      font-size: 14px;
      margin-bottom: 8px;
      
      &::before {
        content: '';
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: #409EFF;
      }
    }
  }
}
</style>
