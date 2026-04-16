<template>
  <div class="download-page page-container">
    <!-- 顶部导航 -->
    <header class="page-header glass-effect">
      <div class="header-content">
        <div class="header-left">
          <el-button text @click="$router.push('/progress')">
            <el-icon><ArrowLeft /></el-icon>
            返回进度
          </el-button>
        </div>
        <h2 class="page-title">{{ projectName || '成品下载' }}</h2>
        <div class="header-right">
          <el-button @click="createNewProject">
            <el-icon><Plus /></el-icon>
            新建项目
          </el-button>
        </div>
      </div>
    </header>

    <!-- 步骤指示器 -->
    <div class="step-bar">
      <div class="step-item completed">
        <div class="step-dot"></div>
        <span>上传素材</span>
      </div>
      <div class="step-line completed"></div>
      <div class="step-item completed">
        <div class="step-dot"></div>
        <span>编辑配置</span>
      </div>
      <div class="step-line completed"></div>
      <div class="step-item active">
        <div class="step-dot"></div>
        <span>下载成品</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="download-content">
      <div class="download-main">
        <!-- 成功提示 -->
        <div class="success-card">
          <div class="success-icon">
            <el-icon><CircleCheckFilled /></el-icon>
          </div>
          <h2>视频生成成功！</h2>
          <p>您的视频已处理完成，可以下载到本地或分享到各大平台</p>
        </div>

        <!-- 视频预览 -->
        <div class="preview-card">
          <div class="preview-header">
            <span class="preview-title">
              <el-icon><Film /></el-icon>
              视频预览
            </span>
            <div class="preview-actions">
              <el-button size="small" @click="toggleFavorite">
                <el-icon>
                  <Star v-if="!isFavorite" />
                  <StarFilled v-else />
                </el-icon>
                {{ isFavorite ? '已收藏' : '收藏' }}
              </el-button>
              <el-button size="small" @click="shareVideo">
                <el-icon><Share /></el-icon>
                分享
              </el-button>
            </div>
          </div>
          <div class="preview-screen">
            <video
              ref="videoPlayer"
              class="video-player"
              :src="videoUrl"
              controls
            ></video>
            <div class="play-overlay" v-if="!isPlaying && !videoUrl" @click="playVideo">
              <div class="play-button">
                <el-icon :size="48"><VideoPlay /></el-icon>
              </div>
            </div>
          </div>
          <div class="video-info-bar">
            <div class="info-left">
              <span class="video-title">{{ projectName || 'AI生成视频' }}.{{ outputSettings.format }}</span>
              <span class="video-meta">{{ outputSettings.resolution }} · {{ outputSettings.frameRate }}fps · {{ fileSize }}</span>
            </div>
            <div class="info-right">
              <el-button circle @click="toggleMute">
                <el-icon><MuteOrLoud /></el-icon>
              </el-button>
              <el-button circle @click="toggleFullscreen">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 下载选项 -->
        <div class="download-options-card">
          <h3>
            <el-icon><Download /></el-icon>
            下载选项
          </h3>
          
          <div class="options-grid">
            <!-- 当前版本 -->
            <div class="option-item primary" :class="{ selected: selectedFormat === 'mp4' }" @click="selectFormat('mp4')">
              <div class="option-icon">
                <el-icon :size="32"><VideoPlay /></el-icon>
              </div>
              <div class="option-info">
                <span class="option-name">MP4 高清版</span>
                <span class="option-desc">{{ outputSettings.resolution }} · 推荐下载</span>
              </div>
              <div class="option-size">{{ fileSize }}</div>
              <div class="option-badge">当前</div>
            </div>

            <!-- 其他格式 -->
            <div class="option-item" :class="{ selected: selectedFormat === 'mov' }" @click="selectFormat('mov')">
              <div class="option-icon">
                <el-icon :size="32"><Film /></el-icon>
              </div>
              <div class="option-info">
                <span class="option-name">MOV 格式</span>
                <span class="option-desc">适合专业剪辑软件</span>
              </div>
              <div class="option-size">{{ otherFileSize }}</div>
            </div>

            <div class="option-item" :class="{ selected: selectedFormat === 'webm' }" @click="selectFormat('webm')">
              <div class="option-icon">
                <el-icon :size="32"><Connection /></el-icon>
              </div>
              <div class="option-info">
                <span class="option-name">WebM 格式</span>
                <span class="option-desc">适合网页嵌入</span>
              </div>
              <div class="option-size">{{ webmSize }}</div>
            </div>

            <div class="option-item" :class="{ selected: selectedFormat === 'gif' }" @click="selectFormat('gif')">
              <div class="option-icon">
                <el-icon :size="32"><Picture /></el-icon>
              </div>
              <div class="option-info">
                <span class="option-name">GIF 动图</span>
                <span class="option-desc">适合聊天分享</span>
              </div>
              <div class="option-size">{{ gifSize }}</div>
            </div>
          </div>

          <!-- 下载按钮 -->
          <div class="download-actions">
            <el-button type="primary" size="large" @click="downloadVideo" :loading="downloading">
              <el-icon><Download /></el-icon>
              下载视频
            </el-button>
            <el-button size="large" @click="copyLink">
              <el-icon><Link /></el-icon>
              复制链接
            </el-button>
          </div>

          <!-- 批量下载 -->
          <div class="batch-download">
            <el-checkbox v-model="includeSubtitle">包含字幕文件 (.srt)</el-checkbox>
            <el-checkbox v-model="includeThumbnail">包含封面图 (.jpg)</el-checkbox>
          </div>
        </div>

        <!-- 分享区域 -->
        <div class="share-card">
          <h3>
            <el-icon><Share /></el-icon>
            分享到平台
          </h3>
          
          <div class="share-platforms">
            <div class="platform-item" @click="shareTo('douyin')">
              <div class="platform-icon dy">
                <svg viewBox="0 0 24 24" width="28" height="28">
                  <path fill="currentColor" d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                </svg>
              </div>
              <span>抖音</span>
            </div>
            <div class="platform-item" @click="shareTo('kuaishou')">
              <div class="platform-icon ks">
                <svg viewBox="0 0 24 24" width="28" height="28">
                  <path fill="currentColor" d="M16 8h2c1.1 0 2 .9 2 2v2c0 1.1-.9 2-2 2h-2v-6zm-8 6H4c-1.1 0-2-.9-2-2V8c0-1.1.9-2 2-2h4v8zm2-6h4v2h-4V8z"/>
                </svg>
              </div>
              <span>快手</span>
            </div>
            <div class="platform-item" @click="shareTo('bilibili')">
              <div class="platform-icon bl">
                <svg viewBox="0 0 24 24" width="28" height="28">
                  <path fill="currentColor" d="M17.813 4.653h.854c1.51.054 2.769.578 3.773 1.574 1.004.995 1.524 2.249 1.56 3.76v7.36c-.036 1.51-.556 2.769-1.56 3.773s-2.262 1.524-3.773 1.56H5.333c-1.51-.036-2.769-.556-3.773-1.56S.036 18.858 0 17.347v-7.36c.036-1.511.556-2.765 1.56-3.76 1.004-.996 2.262-1.52 3.773-1.574h.774l-1.174-1.12a1.234 1.234 0 0 1-.373-.906c0-.356.124-.659.373-.907l.027-.027c.267-.249.573-.373.92-.373.347 0 .653.124.92.373L9.653 4.44c.071.071.134.142.187.213h4.267a.836.836 0 0 1 .16-.213l2.853-2.747c.267-.249.573-.373.92-.373.347 0 .662.151.929.4.267.249.391.551.391.907 0 .355-.124.657-.373.906zM12 9.667c-1.334 0-2.44.445-3.307 1.333-.867.889-1.307 1.96-1.32 3.214v2.787c.013 1.253.453 2.324 1.32 3.213.867.889 1.973 1.333 3.307 1.333 1.333 0 2.439-.444 3.306-1.333.867-.889 1.307-1.96 1.32-3.213v-2.787c-.013-1.253-.453-2.325-1.32-3.214-.867-.888-1.973-1.333-3.306-1.333zm-1.106 4.973c.32.356.481.76.481 1.213 0 .453-.16.857-.481 1.213-.32.356-.72.533-1.2.533-.48 0-.88-.178-1.2-.533-.32-.356-.48-.76-.48-1.213 0-.453.16-.857.48-1.213.32-.356.72-.533 1.2-.533.48 0 .88.178 1.2.533zm3.6 1.213c0 .453-.16.857-.48 1.213-.32.356-.72.533-1.2.533-.48 0-.88-.178-1.2-.533-.32-.356-.48-.76-.48-1.213 0-.453.16-.857.48-1.213.32-.356.72-.533 1.2-.533.48 0 .88.178 1.2.533.32.356.48.76.48 1.213z"/>
                </svg>
              </div>
              <span>B站</span>
            </div>
            <div class="platform-item" @click="shareTo('weibo')">
              <div class="platform-icon wb">
                <svg viewBox="0 0 24 24" width="28" height="28">
                  <path fill="currentColor" d="M10.098 20c-4.612 0-8.363-2.222-8.363-4.963 0-1.442 1.012-3.104 2.757-4.522 2.327-1.89 5.107-2.42 7.196-1.372.448.227.89.342 1.32.342.39 0 .726-.202.926-.553.03-.053.76-1.39 2.702-1.39 1.47 0 2.798.62 3.743 1.746.874 1.04 1.34 2.393 1.34 3.893 0 3.19-3.034 5.82-10.621 5.82zm6.012-10.29c-1.086-1.086-2.53-1.68-4.12-1.68-1.588 0-3.032.594-4.12 1.68-.346.346-.595.74-.776 1.172h-.012s-.09-.014-.19-.014c-1.57 0-2.84 1.27-2.84 2.84 0 1.57 1.27 2.84 2.84 2.84 1.57 0 2.84-1.27 2.84-2.84 0-.25-.036-.492-.1-.728h2.98c.91 0 1.65-.74 1.65-1.65 0-.89-.71-1.616-1.59-1.65h-.46c-.19-.43-.43-.825-.77-1.17l-.01-.01z"/>
                </svg>
              </div>
              <span>微博</span>
            </div>
            <div class="platform-item" @click="shareTo('xiaohongshu')">
              <div class="platform-icon xhs">
                <svg viewBox="0 0 24 24" width="28" height="28">
                  <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                </svg>
              </div>
              <span>小红书</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 侧边栏 -->
      <aside class="download-sidebar">
        <div class="sidebar-card">
          <h4>视频信息</h4>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">文件名</span>
              <span class="info-value">{{ projectName || '未命名' }}.{{ selectedFormat }}</span>
            </div>
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
              <span class="info-value">{{ selectedFormat.toUpperCase() }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">文件大小</span>
              <span class="info-value">{{ currentFileSize }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">时长</span>
              <span class="info-value">{{ videoDuration }}</span>
            </div>
          </div>
        </div>

        <div class="sidebar-card">
          <h4>视频统计</h4>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ videoClips.length }}</span>
              <span class="stat-label">片段数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ subtitleCount }}</span>
              <span class="stat-label">字幕条</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ transitionCount }}</span>
              <span class="stat-label">转场数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ effectCount }}</span>
              <span class="stat-label">特效数</span>
            </div>
          </div>
        </div>

        <div class="sidebar-card actions-card">
          <h4>快捷操作</h4>
          <div class="action-list">
            <el-button class="action-btn" @click="downloadVideo">
              <el-icon><Download /></el-icon>
              下载视频
            </el-button>
            <el-button class="action-btn" @click="copyLink">
              <el-icon><Link /></el-icon>
              复制链接
            </el-button>
            <el-button class="action-btn" @click="createNewProject">
              <el-icon><Plus /></el-icon>
              新建项目
            </el-button>
          </div>
        </div>

        <div class="sidebar-card tips-card">
          <h4>
            <el-icon><InfoFilled /></el-icon>
            温馨提示
          </h4>
          <ul>
            <li>视频可在7天内重复下载</li>
            <li>支持多种格式导出</li>
            <li>建议使用高画质版本</li>
            <li>可同时下载字幕文件</li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDownloadUrl } from '@/api/services/process.js'

const router = useRouter()
const store = useProjectStore()

// 响应式数据
const videoPlayer = ref(null)
const isPlaying = ref(false)
const isFavorite = ref(false)
const isMuted = ref(false)
const selectedFormat = ref('mp4')
const includeSubtitle = ref(true)
const includeThumbnail = ref(false)
const downloading = ref(false)
const actualDownloadUrl = ref('')

// 文件大小
const fileSize = ref('128.5 MB')
const otherFileSize = ref('135.2 MB')
const webmSize = ref('98.3 MB')
const gifSize = ref('45.6 MB')
const videoDuration = ref('5:12')

// 计算属性
const projectName = computed(() => store.projectName)
const videoClips = computed(() => store.videoClips)
const outputSettings = computed(() => store.outputSettings)
const videoUrl = computed(() => actualDownloadUrl.value || store.downloadUrl || '')

const subtitleCount = computed(() => 24)
const transitionCount = computed(() => 8)
const effectCount = computed(() => 5)

const currentFileSize = computed(() => {
  const sizes = {
    mp4: fileSize.value,
    mov: otherFileSize.value,
    webm: webmSize.value,
    gif: gifSize.value
  }
  return sizes[selectedFormat.value] || fileSize.value
})

// 方法
const playVideo = () => {
  if (videoPlayer.value) {
    videoPlayer.value.play()
    isPlaying.value = true
  }
}

const toggleMute = () => {
  if (videoPlayer.value) {
    videoPlayer.value.muted = !videoPlayer.value.muted
    isMuted.value = videoPlayer.value.muted
  }
}

const toggleFullscreen = () => {
  if (videoPlayer.value) {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      videoPlayer.value.requestFullscreen()
    }
  }
}

const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  ElMessage.success(isFavorite.value ? '已添加到收藏' : '已取消收藏')
}

const shareVideo = () => {
  ElMessage.info('分享功能开发中...')
}

const shareTo = (platform) => {
  const platformNames = {
    douyin: '抖音',
    kuaishou: '快手',
    bilibili: 'B站',
    weibo: '微博',
    xiaohongshu: '小红书'
  }
  ElMessage.success(`即将分享到 ${platformNames[platform]}...`)
}

const selectFormat = (format) => {
  selectedFormat.value = format
}

const downloadVideo = async () => {
  downloading.value = true
  
  try {
    // 如果已有下载链接，直接下载
    let downloadLink = actualDownloadUrl.value || store.downloadUrl
    
    // 如果没有，尝试获取
    if (!downloadLink) {
      ElMessage.info('正在获取下载链接...')
      try {
        const response = await getDownloadUrl(store.projectId || 'default')
        if (response.success && response.data?.url) {
          downloadLink = response.data.url
          actualDownloadUrl.value = downloadLink
        }
      } catch (error) {
        console.error('获取下载链接失败:', error)
        ElMessage.warning('无法获取下载链接，请稍后重试')
        downloading.value = false
        return
      }
    }
    
    // 执行下载
    const link = document.createElement('a')
    link.href = downloadLink
    link.download = `${projectName.value || '视频'}.${selectedFormat.value}`
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('视频下载已开始！')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败，请稍后重试')
  } finally {
    downloading.value = false
  }
}

// 获取下载信息
const fetchDownloadInfo = async () => {
  if (store.downloadUrl) {
    actualDownloadUrl.value = store.downloadUrl
    return
  }
  
  try {
    const response = await getDownloadUrl(store.projectId || 'default')
    if (response.success && response.data) {
      actualDownloadUrl.value = response.data.url || ''
      if (response.data.file_size) {
        fileSize.value = response.data.file_size
      }
      if (response.data.duration) {
        videoDuration.value = response.data.duration
      }
    }
  } catch (error) {
    console.error('获取下载信息失败:', error)
    // 使用默认值继续
  }
}

onMounted(() => {
  fetchDownloadInfo()
})

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(videoUrl.value || window.location.href)
    ElMessage.success('链接已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

const createNewProject = async () => {
  try {
    await ElMessageBox.confirm('确定要创建新项目吗？当前项目将保存在云端。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    store.resetProject()
    router.push('/upload')
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss" scoped>
.download-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
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
}

// 步骤条
.step-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  gap: 0;
  
  .step-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #888;
    
    .step-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
    }
    
    &.active, &.completed {
      color: #409EFF;
      
      .step-dot {
        background: #409EFF;
      }
    }
    
    &.completed .step-dot {
      background: #67C23A;
    }
  }
  
  .step-line {
    width: 60px;
    height: 2px;
    background: rgba(255, 255, 255, 0.1);
    margin: 0 12px;
    
    &.completed {
      background: #67C23A;
    }
  }
}

// 主内容区
.download-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px;
  width: 100%;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.download-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

// 成功卡片
.success-card {
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.15) 0%, rgba(82, 196, 26, 0.05) 100%);
  border: 1px solid rgba(103, 194, 58, 0.3);
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  
  .success-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 20px;
    background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    
    .el-icon {
      font-size: 40px;
    }
  }
  
  h2 {
    font-size: 28px;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 14px;
    color: #888;
  }
}

// 预览卡片
.preview-card {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 16px;
  overflow: hidden;
  
  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    .preview-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 500;
    }
    
    .preview-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .preview-screen {
    position: relative;
    aspect-ratio: 16/9;
    background: #000;
    
    .video-player {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    
    .play-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.3);
      cursor: pointer;
      
      .play-button {
        width: 80px;
        height: 80px;
        background: rgba(64, 158, 255, 0.9);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        transition: transform 0.3s;
        
        &:hover {
          transform: scale(1.1);
        }
      }
    }
  }
  
  .video-info-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: rgba(0, 0, 0, 0.3);
    
    .info-left {
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .video-title {
        font-size: 14px;
        font-weight: 500;
      }
      
      .video-meta {
        font-size: 12px;
        color: #888;
      }
    }
    
    .info-right {
      display: flex;
      gap: 8px;
    }
  }
}

// 下载选项卡片
.download-options-card {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 16px;
  padding: 24px;
  
  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    margin: 0 0 20px;
  }
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
  
  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  
  &:hover {
    background: rgba(64, 158, 255, 0.1);
  }
  
  &.selected {
    border-color: #409EFF;
    background: rgba(64, 158, 255, 0.15);
  }
  
  &.primary {
    .option-icon {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
  }
  
  .option-icon {
    width: 48px;
    height: 48px;
    background: rgba(64, 158, 255, 0.2);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #409EFF;
  }
  
  .option-info {
    flex: 1;
    
    .option-name {
      display: block;
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 4px;
    }
    
    .option-desc {
      font-size: 12px;
      color: #888;
    }
  }
  
  .option-size {
    font-size: 13px;
    color: #888;
    font-variant-numeric: tabular-nums;
  }
  
  .option-badge {
    position: absolute;
    top: -8px;
    right: 12px;
    background: #409EFF;
    color: #fff;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
  }
}

.download-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  
  .el-button {
    flex: 1;
    height: 48px;
    font-size: 16px;
  }
}

.batch-download {
  display: flex;
  gap: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

// 分享卡片
.share-card {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 16px;
  padding: 24px;
  
  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    margin: 0 0 20px;
  }
}

.share-platforms {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.platform-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.2s;
  
  &:hover {
    transform: translateY(-4px);
  }
  
  .platform-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    transition: filter 0.2s;
    
    &:hover {
      filter: brightness(1.1);
    }
    
    &.dy { background: #000; }
    &.ks { background: #FF4906; }
    &.bl { background: #FB7299; }
    &.wb { background: #E6162D; }
    &.xhs { background: #FE2C55; }
  }
  
  span {
    font-size: 12px;
    color: #888;
  }
}

// 侧边栏
.download-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
  
  @media (max-width: 1024px) {
    display: none;
  }
}

.sidebar-card {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 16px;
  padding: 20px;
  
  h4 {
    font-size: 14px;
    margin: 0 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .info-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .info-label {
      font-size: 13px;
      color: #888;
    }
    
    .info-value {
      font-size: 13px;
    }
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  
  .stat-item {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    
    .stat-value {
      display: block;
      font-size: 20px;
      font-weight: 600;
      color: #409EFF;
      margin-bottom: 4px;
    }
    
    .stat-label {
      font-size: 12px;
      color: #888;
    }
  }
}

.actions-card {
  .action-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .action-btn {
    width: 100%;
    justify-content: flex-start;
    padding-left: 16px;
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
      padding: 8px 0;
      font-size: 13px;
      color: #888;
      
      &::before {
        content: '';
        width: 6px;
        height: 6px;
        background: #409EFF;
        border-radius: 50%;
      }
    }
  }
}
</style>
