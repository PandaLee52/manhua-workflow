<template>
  <div class="editor-page page-container">
    <!-- 顶部导航 -->
    <header class="page-header glass-effect">
      <div class="header-content">
        <div class="header-left">
          <el-button text @click="$router.push('/upload')">
            <el-icon><ArrowLeft /></el-icon>
            返回上传
          </el-button>
        </div>
        <h2 class="page-title">{{ projectName || '视频编辑' }}</h2>
        <div class="header-right">
          <el-button @click="saveProject">
            <el-icon><FolderOpened /></el-icon>
            保存项目
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
      <div class="step-item active">
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
    <div class="editor-content">
      <!-- 左侧：视频预览和时间轴 -->
      <div class="preview-section">
        <!-- 视频预览区 -->
        <div class="video-preview-area">
          <div class="preview-header">
            <span class="preview-title">
              <el-icon><VideoPlay /></el-icon>
              视频预览
            </span>
            <div class="preview-actions">
              <el-button-group>
                <el-button size="small" :type="previewQuality === '720p' ? 'primary' : ''" @click="previewQuality = '720p'">720P</el-button>
                <el-button size="small" :type="previewQuality === '1080p' ? 'primary' : ''" @click="previewQuality = '1080p'">1080P</el-button>
              </el-button-group>
            </div>
          </div>
          <div class="preview-screen">
            <!-- 视频元素 -->
            <video
              v-if="videoUrl"
              ref="videoRef"
              :src="videoUrl"
              :poster="videoPoster"
              @loadedmetadata="onLoadedMetadata"
              @timeupdate="onTimeUpdate"
              @play="isPlaying = true"
              @pause="isPlaying = false"
              @ended="isPlaying = false"
              class="preview-video"
            ></video>
            <!-- 占位符 -->
            <div v-else class="preview-placeholder">
              <el-icon :size="64"><VideoPlay /></el-icon>
              <p>视频预览区域</p>
              <p class="preview-hint">点击播放按钮预览编辑效果</p>
            </div>
            <!-- Canvas 框选层 -->
            <canvas
              ref="watermarkCanvasRef"
              class="watermark-canvas"
              :class="{ 'selecting': isSelectingWatermark }"
              @mousedown="handleCanvasMouseDown"
              @mousemove="handleCanvasMouseMove"
              @mouseup="handleCanvasMouseUp"
              @mouseleave="handleCanvasMouseUp"
            ></canvas>
            <!-- 视频控制栏 -->
            <div class="preview-controls">
              <div class="control-left">
                <el-button circle size="small" @click="videoRef && (videoRef.currentTime -= 5)">
                  <el-icon><RefreshLeft /></el-icon>
                </el-button>
                <el-button circle size="small" type="primary" @click="togglePlay">
                  <el-icon v-if="!isPlaying"><VideoPlay /></el-icon>
                  <el-icon v-else><VideoPause /></el-icon>
                </el-button>
                <el-button circle size="small" @click="videoRef && (videoRef.currentTime += 5)">
                  <el-icon><RefreshRight /></el-icon>
                </el-button>
              </div>
              <div class="control-center">
                <span class="time-display">{{ formatTime(currentTime) }}</span>
                <div class="progress-slider" @click="seekProgress">
                  <div class="progress-track">
                    <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                    <div class="progress-handle" :style="{ left: progressPercent + '%' }"></div>
                  </div>
                </div>
                <span class="time-display">{{ formatTime(videoDuration) }}</span>
              </div>
              <div class="control-right">
                <el-button circle size="small" @click="toggleMute">
                  <el-icon v-if="isMuted"><Mute /></el-icon>
                  <el-icon v-else><Volume /></el-icon>
                </el-button>
                <el-button circle size="small" @click="toggleFullscreen">
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 时间轴 -->
        <div class="timeline-area">
          <div class="timeline-header">
            <span class="timeline-title">
              <el-icon><Timer /></el-icon>
              时间轴
            </span>
            <div class="timeline-tools">
              <el-button-group>
                <el-button size="small" title="缩放">
                  <el-icon><ZoomIn /></el-icon>
                </el-button>
                <el-button size="small" title="适应屏幕">
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </el-button-group>
            </div>
          </div>
          <div class="timeline-content">
            <div class="timeline-ruler" :style="{ width: timelineWidth + 'px' }">
              <span v-for="mark in rulerMarks" :key="mark.label" class="ruler-mark" :style="{ position: 'absolute', left: mark.position + 'px' }">
                {{ mark.label }}
              </span>
            </div>
            <div class="timeline-tracks">
              <!-- 视频轨道 -->
              <div class="track video-track">
                <div class="track-label">视频</div>
                <div class="track-content" :style="{ width: timelineWidth + 'px' }">
                  <div
                    v-for="(clip, index) in videoClips"
                    :key="clip.id"
                    class="timeline-clip"
                    :style="{ width: getClipWidth(clip) + 'px', left: getClipOffset(index) + 'px' }"
                  >
                    <div class="clip-content">
                      <span class="clip-name">{{ clip.name }}</span>
                    </div>
                  </div>
                  <!-- 播放头 -->
                  <div class="playhead" :style="{ left: playheadPosition + 'px' }"></div>
                </div>
              </div>
              <!-- 音频轨道 -->
              <div class="track audio-track">
                <div class="track-label">音频</div>
                <div class="track-content">
                  <div class="timeline-clip audio-clip" :style="{ width: timelineWidth + 'px', left: '0px' }">
                    <div class="clip-content">
                      <el-icon><Music /></el-icon>
                      <span class="clip-name">{{ selectedBgm?.name || '背景音乐' }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 字幕轨道 -->
              <div class="track subtitle-track">
                <div class="track-label">字幕</div>
                <div class="track-content">
                  <div class="subtitle-markers">
                    <div class="subtitle-marker" style="left: 0px; width: 60px;"></div>
                    <div class="subtitle-marker" style="left: 80px; width: 45px;"></div>
                    <div class="subtitle-marker" style="left: 150px; width: 70px;"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：配置面板 -->
      <aside class="config-panel">
        <!-- 标签页 -->
        <el-tabs v-model="activeTab" class="config-tabs">
          <!-- BGM 配置 -->
          <el-tab-pane label="背景音乐" name="bgm">
            <template #label>
              <span class="tab-label">
                <el-icon><Music /></el-icon>
                背景音乐
              </span>
            </template>
            <div class="tab-content">
              <div class="search-box">
                <el-input
                  v-model="bgmSearchQuery"
                  placeholder="搜索音乐..."
                  :prefix-icon="Search"
                  clearable
                  @input="debouncedSearch"
                  @keyup.enter="performBgmSearch"
                />
                <el-button type="primary" @click="performBgmSearch" :loading="bgmLoading">
                  搜索
                </el-button>
              </div>
              
              <div class="bgm-categories">
                <el-radio-group v-model="bgmCategory" size="small">
                  <el-radio-button label="all">全部</el-radio-button>
                  <el-radio-button label="popular">热门</el-radio-button>
                  <el-radio-button label="bgm">背景</el-radio-button>
                  <el-radio-button label="rhythmic">节奏</el-radio-button>
                </el-radio-group>
              </div>

              <div class="bgm-list" v-loading="bgmLoading">
                <el-empty v-if="filteredBgms.length === 0 && !bgmLoading" description="暂无音乐，请搜索" />
                <div
                  v-else
                  v-for="bgm in filteredBgms"
                  :key="bgm.id"
                  class="bgm-item"
                  :class="{ selected: selectedBgm?.id === bgm.id }"
                  @click="selectBgm(bgm)"
                >
                  <div class="bgm-thumb">
                    <el-icon><VideoPlay /></el-icon>
                  </div>
                  <div class="bgm-info">
                    <p class="bgm-name">{{ bgm.name }}</p>
                    <p class="bgm-meta">{{ bgm.artist }} · {{ bgm.duration }}</p>
                  </div>
                  <div class="bgm-actions">
                    <el-button circle size="small" @click.stop="playBgmPreview(bgm)">
                      <el-icon><VideoPlay /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>

              <div class="bgm-settings" v-if="selectedBgm">
                <h4>音量设置</h4>
                <div class="setting-item">
                  <span>音乐音量</span>
                  <el-slider v-model="bgmVolume" :min="0" :max="100" />
                  <span class="setting-value">{{ bgmVolume }}%</span>
                </div>
                <div class="setting-item">
                  <span>淡入时长</span>
                  <el-slider v-model="bgmFadeIn" :min="0" :max="10" :step="0.5" />
                  <span class="setting-value">{{ bgmFadeIn }}s</span>
                </div>
                <div class="setting-item">
                  <span>淡出时长</span>
                  <el-slider v-model="bgmFadeOut" :min="0" :max="10" :step="0.5" />
                  <span class="setting-value">{{ bgmFadeOut }}s</span>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 字幕配置 -->
          <el-tab-pane label="字幕设置" name="subtitle">
            <template #label>
              <span class="tab-label">
                <el-icon><ChatLineRound /></el-icon>
                字幕设置
              </span>
            </template>
            <div class="tab-content">
              <div class="setting-group">
                <div class="setting-row">
                  <span>启用字幕</span>
                  <el-switch v-model="subtitleEnabled" />
                </div>
              </div>

              <div class="subtitle-preview">
                <div class="preview-box">
                  <p class="preview-subtitle">这是一行预览字幕</p>
                </div>
              </div>

              <div class="setting-group" v-if="subtitleEnabled">
                <h4>样式设置</h4>
                <div class="setting-item">
                  <span>字体大小</span>
                  <el-slider v-model="subtitleStyle.fontSize" :min="16" :max="40" />
                  <span class="setting-value">{{ subtitleStyle.fontSize }}px</span>
                </div>
                <div class="setting-item">
                  <span>字幕颜色</span>
                  <el-color-picker v-model="subtitleStyle.color" />
                </div>
                <div class="setting-item">
                  <span>字幕位置</span>
                  <el-select v-model="subtitleStyle.position">
                    <el-option label="底部" value="bottom" />
                    <el-option label="居中" value="center" />
                    <el-option label="顶部" value="top" />
                  </el-select>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 去水印设置 -->
          <el-tab-pane label="去水印" name="watermark">
            <template #label>
              <span class="tab-label">
                <el-icon><Delete /></el-icon>
                去水印
              </span>
            </template>
            <div class="tab-content">
              <el-alert
                title="框选水印区域"
                description="点击下方按钮，然后在视频预览区拖动鼠标框选水印位置"
                type="info"
                :closable="false"
                show-icon
              />
              
              <div class="watermark-actions">
                <el-button 
                  type="primary"
                  @click="startWatermarkSelection"
                >
                  {{ isSelectingWatermark ? '框选中...' : '开始框选' }}
                </el-button>
                <el-button @click="clearWatermarkRegions">
                  清空选区
                </el-button>
              </div>

              <!-- 已选区域列表 -->
              <div class="region-list" v-if="watermarkRegions.length > 0">
                <h4>已选区域 ({{ watermarkRegions.length }})</h4>
                <div 
                  v-for="(region, index) in watermarkRegions" 
                  :key="index"
                  class="region-item"
                >
                  <span class="region-index">区域 {{ index + 1 }}</span>
                  <span class="region-info">
                    x: {{ region.x }}, y: {{ region.y }}, 
                    {{ region.width }}×{{ region.height }}
                  </span>
                  <el-button 
                    size="small" 
                    type="danger" 
                    link
                    @click="removeRegion(index)"
                  >
                    删除
                  </el-button>
                </div>
              </div>

              <!-- 当前选区信息 -->
              <div class="current-selection" v-if="currentSelection">
                <h4>当前选区预览</h4>
                <div class="selection-info">
                  <span>x: {{ currentSelection.x }}</span>
                  <span>y: {{ currentSelection.y }}</span>
                  <span>宽度: {{ currentSelection.width }}</span>
                  <span>高度: {{ currentSelection.height }}</span>
                </div>
              </div>

              <!-- 模糊强度设置 -->
              <div class="setting-group">
                <h4>处理参数</h4>
                <div class="setting-item">
                  <span>模糊强度</span>
                  <el-slider v-model="watermarkBlur" :min="5" :max="50" />
                  <span class="setting-value">{{ watermarkBlur }}</span>
                </div>
              </div>

              <!-- 去除水印按钮 -->
              <el-button 
                type="success" 
                size="large" 
                :loading="processingWatermark"
                :disabled="watermarkRegions.length === 0"
                @click="applyWatermarkRemoval"
                class="apply-watermark-btn"
              >
                <el-icon><Check /></el-icon>
                去除水印
              </el-button>
            </div>
          </el-tab-pane>

          <!-- 输出配置 -->
          <el-tab-pane label="输出设置" name="output">
            <template #label>
              <span class="tab-label">
                <el-icon><Setting /></el-icon>
                输出设置
              </span>
            </template>
            <div class="tab-content">
              <div class="setting-group">
                <h4>视频参数</h4>
                <div class="setting-item">
                  <span>分辨率</span>
                  <el-select v-model="outputSettings.resolution">
                    <el-option label="720P (1280×720)" value="720p" />
                    <el-option label="1080P (1920×1080)" value="1080p" />
                    <el-option label="2K (2560×1440)" value="2k" />
                    <el-option label="4K (3840×2160)" value="4k" />
                  </el-select>
                </div>
                <div class="setting-item">
                  <span>帧率</span>
                  <el-select v-model="outputSettings.frameRate">
                    <el-option label="24 fps" :value="24" />
                    <el-option label="30 fps" :value="30" />
                    <el-option label="60 fps" :value="60" />
                  </el-select>
                </div>
                <div class="setting-item">
                  <span>输出格式</span>
                  <el-select v-model="outputSettings.format">
                    <el-option label="MP4" value="mp4" />
                    <el-option label="MOV" value="mov" />
                    <el-option label="AVI" value="avi" />
                    <el-option label="WebM" value="webm" />
                  </el-select>
                </div>
              </div>

              <div class="setting-group">
                <h4>输出质量</h4>
                <div class="quality-options">
                  <div
                    v-for="opt in qualityOptions"
                    :key="opt.value"
                    class="quality-option"
                    :class="{ selected: outputSettings.quality === opt.value }"
                    @click="outputSettings.quality = opt.value"
                  >
                    <span class="quality-name">{{ opt.label }}</span>
                    <span class="quality-desc">{{ opt.desc }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </aside>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-actions glass-effect">
      <div class="actions-content">
        <div class="project-info">
          <el-icon><VideoPlay /></el-icon>
          <span>{{ videoClips.length }} 个视频片段</span>
          <span class="divider">|</span>
          <span>预计时长 {{ estimatedDuration }}</span>
        </div>
        <div class="action-buttons">
          <el-button size="large" @click="$router.push('/upload')">
            上一步
          </el-button>
          <el-button type="primary" size="large" @click="startProcessing">
            <el-icon><Cpu /></el-icon>
            开始生成视频
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
import { searchBgm } from '@/api/services/bgm.js'

const router = useRouter()
const store = useProjectStore()

// 响应式数据
const activeTab = ref('bgm')
const previewQuality = ref('1080p')

// 视频预览相关
const videoRef = ref(null)
const videoUrl = ref('')
const videoPoster = ref('')
const isPlaying = ref(false)
const isMuted = ref(false)
const volume = ref(1)
const videoDuration = ref(0)
const currentTime = ref(0)
const bgmSearch = ref('')
const bgmCategory = ref('all')
const bgmVolume = ref(80)
const bgmFadeIn = ref(2)
const bgmFadeOut = ref(2)
const subtitleEnabled = ref(true)
const selectedBgm = ref(null)
const playingBgm = ref(null)
const bgmLoading = ref(false)

// BGM搜索状态
const bgmSearchQuery = ref('')

// 剧本解析结果
const parsedScript = ref(null)

const subtitleStyle = ref({
  fontSize: 24,
  color: '#ffffff',
  position: 'bottom'
})

const outputSettings = ref({
  resolution: '1080p',
  frameRate: 30,
  format: 'mp4',
  quality: 'high'
})

// 去水印相关状态
const isSelectingWatermark = ref(false)
const watermarkRegions = ref([])
const currentSelection = ref(null)
const watermarkBlur = ref(10)
const processingWatermark = ref(false)
const watermarkCanvasRef = ref(null)

// Canvas 绘制相关
let canvasCtx = null
let isDrawing = false
let startX = 0
let startY = 0

// BGM 列表
const bgmList = ref([
  { id: 1, name: '轻快节奏', artist: 'Studio One', duration: '3:24', url: '' },
  { id: 2, name: '励志背景', artist: 'Epic Music', duration: '2:58', url: '' },
  { id: 3, name: '柔和钢琴', artist: 'Relaxing', duration: '4:12', url: '' },
  { id: 4, name: '电子氛围', artist: 'Cyber Wave', duration: '3:45', url: '' },
  { id: 5, name: '自然之声', artist: 'Nature Sound', duration: '5:00', url: '' },
  { id: 6, name: '科技感配乐', artist: 'Tech Beats', duration: '3:30', url: '' },
])

// 质量选项
const qualityOptions = [
  { label: '快速', value: 'fast', desc: '生成速度快，适合测试' },
  { label: '标准', value: 'standard', desc: '平衡速度和质量' },
  { label: '高质量', value: 'high', desc: '最佳质量，推荐使用' },
]

// 计算属性
const projectName = computed(() => store.projectName)
const videoClips = computed(() => store.videoClips)

// 过滤BGM列表
const filteredBgms = computed(() => {
  let result = bgmList.value
  if (bgmSearchQuery.value) {
    result = result.filter(bgm => 
      bgm.name.toLowerCase().includes(bgmSearchQuery.value.toLowerCase()) ||
      bgm.artist.toLowerCase().includes(bgmSearchQuery.value.toLowerCase())
    )
  }
  if (bgmCategory.value !== 'all') {
    // 模拟分类筛选
    result = result.slice(0, 3)
  }
  return result
})

// 执行BGM搜索
const performBgmSearch = async () => {
  if (!bgmSearchQuery.value.trim()) {
    return
  }
  
  bgmLoading.value = true
  try {
    const response = await searchBgm({
      query: bgmSearchQuery.value,
      emotion: bgmCategory.value !== 'all' ? bgmCategory.value : '',
      limit: 20
    })
    
    if (response.success && response.data?.results) {
      bgmList.value = response.data.results.map((bgm, index) => ({
        id: bgm.id || index + 1,
        name: bgm.name || bgm.title || '未知音乐',
        artist: bgm.artist || bgm.composer || '未知艺术家',
        duration: bgm.duration || '0:00',
        url: bgm.url || bgm.preview_url || '',
        tags: bgm.tags || [],
        emotion: bgm.emotion || ''
      }))
      ElMessage.success(`找到 ${response.data.results.length} 首音乐`)
    }
  } catch (error) {
    console.error('BGM搜索失败:', error)
    ElMessage.warning('搜索失败，将显示默认列表')
  } finally {
    bgmLoading.value = false
  }
}

// 防抖搜索
let searchTimer = null
const debouncedSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    performBgmSearch()
  }, 500)
}

const estimatedDuration = computed(() => {
  const seconds = store.totalDuration || videoClips.value.length * 15
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${String(secs).padStart(2, '0')}`
})

// 时间轴相关状态变量
const timelineScale = ref(50) // 像素/秒

// 时间轴计算属性
const totalDuration = computed(() => 
  videoClips.value.reduce((sum, clip) => sum + (clip.duration || 15), 0)
)
const timelineWidth = computed(() => totalDuration.value * timelineScale.value)

// 时间刻度尺标记
const rulerMarks = computed(() => {
  const marks = []
  const interval = totalDuration.value > 300 ? 30 : totalDuration.value > 120 ? 15 : 5
  for (let i = 0; i <= totalDuration.value; i += interval) {
    marks.push({ position: i * timelineScale.value, label: formatTime(i) })
  }
  return marks
})

// 播放头位置
const playheadPosition = computed(() => currentTime.value * timelineScale.value)

// 片段宽度和偏移计算
const getClipWidth = (clip) => (clip.duration || 15) * timelineScale.value
const getClipOffset = (index) => {
  let offset = 0
  for (let i = 0; i < index; i++) {
    offset += getClipWidth(videoClips.value[i])
  }
  return offset
}

// 格式化时间（秒转为 mm:ss 或 hh:mm:ss）
const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// 视频预览方法
const onLoadedMetadata = () => {
  if (videoRef.value) {
    videoDuration.value = videoRef.value.duration
  }
}

const onTimeUpdate = () => {
  if (videoRef.value) {
    // 使用时间轴的 currentTime，保持同步
    // currentTime 已在模板中通过 videoRef 绑定
  }
}

const togglePlay = () => {
  if (!videoRef.value) return
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
}

const seekProgress = (event) => {
  if (!videoRef.value || videoDuration.value === 0) return
  const rect = event.currentTarget.getBoundingClientRect()
  const percent = (event.clientX - rect.left) / rect.width
  videoRef.value.currentTime = percent * videoDuration.value
}

const toggleMute = () => {
  if (!videoRef.value) return
  isMuted.value = !isMuted.value
  videoRef.value.muted = isMuted.value
}

const toggleFullscreen = () => {
  if (!videoRef.value) return
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    videoRef.value.requestFullscreen()
  }
}

const progressPercent = computed(() => {
  if (videoDuration.value === 0) return 0
  return (currentTime.value / videoDuration.value) * 100
})

// 保留旧的兼容方法
const clipWidth = computed(() => 100)

const clipOffset = (index) => {
  return index * (clipWidth.value + 10)
}

// 方法
const selectBgm = (bgm) => {
  selectedBgm.value = bgm
  store.selectBgm(bgm)
}

const playBgmPreview = (bgm) => {
  if (playingBgm.value?.id === bgm.id) {
    playingBgm.value = null
  } else {
    playingBgm.value = bgm
    ElMessage.success(`正在播放: ${bgm.name}`)
  }
}

const saveProject = () => {
  ElMessage.success('项目已保存')
}

const startProcessing = () => {
  // 保存所有配置
  store.bgmVolume = bgmVolume.value
  store.bgmFadeIn = bgmFadeIn.value
  store.bgmFadeOut = bgmFadeOut.value
  store.subtitleEnabled = subtitleEnabled.value
  store.subtitleStyle = subtitleStyle.value
  store.outputSettings = outputSettings.value
  
  router.push('/progress')
}

// ============ 去水印相关方法 ============

// 初始化 Canvas
const initCanvas = () => {
  if (!watermarkCanvasRef.value) return
  
  const canvas = watermarkCanvasRef.value
  const parent = canvas.parentElement
  if (!parent) return
  
  const rect = parent.getBoundingClientRect()
  canvas.width = rect.width
  canvas.height = rect.height
  canvasCtx = canvas.getContext('2d')
  
  // 绘制已选区域
  drawRegions()
}

// 绘制所有选区
const drawRegions = () => {
  if (!canvasCtx || !watermarkCanvasRef.value) return
  
  const canvas = watermarkCanvasRef.value
  canvasCtx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 绘制已保存的区域（半透明蓝色）
  watermarkRegions.value.forEach(region => {
    canvasCtx.fillStyle = 'rgba(64, 158, 255, 0.3)'
    canvasCtx.strokeStyle = '#409EFF'
    canvasCtx.lineWidth = 2
    canvasCtx.fillRect(region.x, region.y, region.width, region.height)
    canvasCtx.strokeRect(region.x, region.y, region.width, region.height)
  })
  
  // 绘制当前选区（半透明红色）
  if (currentSelection.value) {
    const sel = currentSelection.value
    canvasCtx.fillStyle = 'rgba(245, 108, 108, 0.3)'
    canvasCtx.strokeStyle = '#F56C6C'
    canvasCtx.lineWidth = 2
    canvasCtx.fillRect(sel.x, sel.y, sel.width, sel.height)
    canvasCtx.strokeRect(sel.x, sel.y, sel.width, sel.height)
  }
}

// 开始框选
const startWatermarkSelection = () => {
  isSelectingWatermark.value = !isSelectingWatermark.value
  
  if (isSelectingWatermark.value) {
    ElMessage.info('请在视频预览区拖动鼠标框选水印区域')
    // 初始化 Canvas
    setTimeout(initCanvas, 100)
  } else {
    currentSelection.value = null
    drawRegions()
  }
}

// Canvas 鼠标按下
const handleCanvasMouseDown = (e) => {
  if (!isSelectingWatermark.value) return
  
  const canvas = watermarkCanvasRef.value
  const rect = canvas.getBoundingClientRect()
  
  isDrawing = true
  startX = e.clientX - rect.left
  startY = e.clientY - rect.top
  
  currentSelection.value = { x: startX, y: startY, width: 0, height: 0 }
}

// Canvas 鼠标移动
const handleCanvasMouseMove = (e) => {
  if (!isDrawing || !isSelectingWatermark.value) return
  
  const canvas = watermarkCanvasRef.value
  const rect = canvas.getBoundingClientRect()
  
  const currentX = e.clientX - rect.left
  const currentY = e.clientY - rect.top
  
  // 计算选区（处理从右往左、从下往上拖动）
  currentSelection.value = {
    x: Math.min(startX, currentX),
    y: Math.min(startY, currentY),
    width: Math.abs(currentX - startX),
    height: Math.abs(currentY - startY)
  }
  
  drawRegions()
}

// Canvas 鼠标释放
const handleCanvasMouseUp = () => {
  if (!isDrawing) return
  
  isDrawing = false
  
  if (currentSelection.value && 
      currentSelection.value.width > 10 && 
      currentSelection.value.height > 10) {
    // 添加到选区列表
    watermarkRegions.value.push({ ...currentSelection.value })
    store.watermarkRegions = watermarkRegions.value
    ElMessage.success(`已添加选区 (${watermarkRegions.value.length})`)
  }
  
  currentSelection.value = null
  drawRegions()
}

// 清空所有选区
const clearWatermarkRegions = () => {
  watermarkRegions.value = []
  store.watermarkRegions = []
  currentSelection.value = null
  drawRegions()
  ElMessage.info('已清空所有选区')
}

// 删除单个选区
const removeRegion = (index) => {
  watermarkRegions.value.splice(index, 1)
  store.watermarkRegions = watermarkRegions.value
  drawRegions()
  ElMessage.info(`已删除选区 ${index + 1}`)
}

// 应用去水印
const applyWatermarkRemoval = async () => {
  if (watermarkRegions.value.length === 0) {
    ElMessage.warning('请先框选水印区域')
    return
  }
  
  processingWatermark.value = true
  
  try {
    // 保存水印配置到 store
    store.watermarkBlur = watermarkBlur.value
    store.watermarkRegions = watermarkRegions.value
    
    ElMessage.success('去水印配置已保存，将在处理时应用')
    
    // 退出框选模式
    isSelectingWatermark.value = false
    currentSelection.value = null
    drawRegions()
  } catch (error) {
    console.error('去水印配置失败:', error)
    ElMessage.error('去水印配置失败')
  } finally {
    processingWatermark.value = false
  }
}

onMounted(() => {
  // 初始化时从 store 恢复配置
  if (store.selectedBgm) {
    selectedBgm.value = store.selectedBgm
  }
  
  // 如果有视频URL，设置预览视频
  if (store.videoUrl) {
    videoUrl.value = store.videoUrl
  }
  bgmVolume.value = store.bgmVolume || 80
  bgmFadeIn.value = store.bgmFadeIn || 2
  bgmFadeOut.value = store.bgmFadeOut || 2
  subtitleEnabled.value = store.subtitleEnabled
  subtitleStyle.value = { ...store.subtitleStyle }
  outputSettings.value = { ...store.outputSettings }
  
  // 恢复去水印配置
  if (store.watermarkRegions) {
    watermarkRegions.value = store.watermarkRegions
  }
  if (store.watermarkBlur) {
    watermarkBlur.value = store.watermarkBlur
  }
  
  // 获取剧本解析结果
  if (store.scriptParsedResult) {
    parsedScript.value = store.scriptParsedResult
    ElMessage.info('已加载剧本解析结果')
  }
})
</script>

<style lang="scss" scoped>
.editor-page {
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
  padding: 0 24px;
  
  .header-content {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .page-title {
    font-size: 16px;
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
.editor-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 20px;
  padding: 0 20px 20px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

// 预览区
.preview-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

// 视频预览
.video-preview-area {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 12px;
  overflow: hidden;
  
  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    .preview-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 500;
    }
  }
  
  .preview-screen {
    position: relative;
    aspect-ratio: 16/9;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .preview-placeholder {
      text-align: center;
      color: #666;
      
      p {
        margin: 8px 0 0;
      }
      
      .preview-hint {
        font-size: 12px;
        color: #555;
      }
    }
    
    .preview-controls {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 12px 16px;
      background: linear-gradient(transparent, rgba(0,0,0,0.8));
      display: flex;
      align-items: center;
      gap: 16px;
      
      .control-left, .control-right {
        display: flex;
        gap: 8px;
      }
      
      .control-center {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 12px;
        
        .time-display {
          font-size: 12px;
          color: #888;
          font-variant-numeric: tabular-nums;
          min-width: 60px;
        }
        
        .progress-slider {
          flex: 1;
          
          .progress-track {
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
            position: relative;
            
            .progress-fill {
              height: 100%;
              background: #409EFF;
              border-radius: 2px;
            }
            
            .progress-handle {
              position: absolute;
              top: 50%;
              transform: translate(-50%, -50%);
              width: 12px;
              height: 12px;
              background: #fff;
              border-radius: 50%;
              cursor: pointer;
            }
          }
        }
      }
    }
  }
}

// 时间轴
.timeline-area {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 12px;
  overflow: hidden;
  
  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    .timeline-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 500;
    }
  }
  
  .timeline-content {
    padding: 16px;
  }
  
  .timeline-ruler {
    display: block;
    position: relative;
    padding-left: 0;
    margin-bottom: 12px;
    margin-left: 60px;
    height: 20px;
    
    .ruler-mark {
      position: absolute;
      font-size: 11px;
      color: #666;
      text-align: left;
      transform: translateX(-50%);
      
      &::before {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 50%;
        width: 1px;
        height: 6px;
        background: #444;
      }
    }
  }
  
  .timeline-tracks {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .track {
    display: flex;
    gap: 12px;
    
    .track-label {
      width: 48px;
      font-size: 12px;
      color: #888;
      text-align: right;
      padding-top: 4px;
      flex-shrink: 0;
    }
    
    .track-content {
      flex: 1;
      height: 48px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 6px;
      position: relative;
      overflow: hidden;
    }
  }
  
  .video-track .track-content {
    height: 48px;
  }
  
  .audio-track .track-content {
    height: 36px;
  }
  
  .subtitle-track .track-content {
    height: 24px;
  }
  
  .timeline-clip {
    position: absolute;
    top: 4px;
    height: calc(100% - 8px);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      filter: brightness(1.1);
      transform: scaleY(1.05);
    }
    
    .clip-content {
      padding: 4px 8px;
      height: 100%;
      display: flex;
      align-items: center;
      gap: 6px;
      overflow: hidden;
      
      .clip-name {
        font-size: 11px;
        color: #fff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
    
    &.audio-clip {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      width: 100%;
      left: 0;
      top: 0;
      height: 100%;
    }
  }
  
  .playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ff4444;
    z-index: 10;
    pointer-events: none;
    
    &::before {
      content: '';
      position: absolute;
      top: -4px;
      left: -5px;
      width: 0;
      height: 0;
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 8px solid #ff4444;
    }
  }
  
  playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ff4444;
    z-index: 10;
    pointer-events: none;
    
    &::before {
      content: '';
      position: absolute;
      top: -4px;
      left: -5px;
      width: 0;
      height: 0;
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 8px solid #ff4444;
    }
  }
  
  .subtitle-marker {
    position: absolute;
    top: 4px;
    height: calc(100% - 8px);
    background: rgba(255, 193, 7, 0.6);
    border-radius: 3px;
  }
}

// 配置面板
.config-panel {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 12px;
  overflow: hidden;
  
  @media (max-width: 1200px) {
    max-height: 500px;
  }
}

.config-tabs {
  height: 100%;
  
  :deep(.el-tabs__header) {
    margin: 0;
    background: rgba(0, 0, 0, 0.2);
    padding: 0 16px;
  }
  
  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }
  
  :deep(.el-tabs__item) {
    color: #888;
    height: 50px;
    line-height: 50px;
    
    &.is-active {
      color: #409EFF;
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: #409EFF;
  }
  
  :deep(.el-tabs__content) {
    padding: 16px;
    height: calc(100% - 50px);
    overflow-y: auto;
  }
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.tab-content {
  min-height: 300px;
}

// 搜索框
.search-box {
  margin-bottom: 16px;
}

// BGM 分类
.bgm-categories {
  margin-bottom: 16px;
  
  :deep(.el-radio-button__inner) {
    background: rgba(0, 0, 0, 0.3);
    border-color: rgba(255, 255, 255, 0.1);
    color: #888;
  }
  
  :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
    background: #409EFF;
    border-color: #409EFF;
    color: #fff;
  }
}

// BGM 列表
.bgm-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.bgm-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: rgba(64, 158, 255, 0.15);
  }
  
  &.selected {
    background: rgba(64, 158, 255, 0.2);
    border: 1px solid #409EFF;
  }
  
  .bgm-thumb {
    width: 40px;
    height: 40px;
    background: rgba(64, 158, 255, 0.2);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #409EFF;
  }
  
  .bgm-info {
    flex: 1;
    overflow: hidden;
    
    .bgm-name {
      font-size: 13px;
      margin: 0 0 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .bgm-meta {
      font-size: 11px;
      color: #888;
      margin: 0;
    }
  }
  
  .bgm-actions {
    :deep(.el-button) {
      width: 32px;
      height: 32px;
    }
  }
}

// BGM 设置
.bgm-settings {
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  
  h4 {
    font-size: 13px;
    margin: 0 0 12px;
    color: #888;
  }
  
  .setting-item {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    
    > span:first-child {
      font-size: 13px;
      color: #b0b0b0;
      min-width: 70px;
    }
    
    .setting-value {
      font-size: 12px;
      color: #409EFF;
      min-width: 40px;
      text-align: right;
    }
    
    :deep(.el-slider) {
      flex: 1;
    }
    
    :deep(.el-select) {
      flex: 1;
    }
  }
}

// 字幕设置
.setting-group {
  margin-bottom: 20px;
  
  h4 {
    font-size: 13px;
    color: #888;
    margin: 0 0 12px;
  }
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  
  span {
    font-size: 14px;
  }
}

.subtitle-preview {
  margin: 16px 0;
  
  .preview-box {
    background: #000;
    border-radius: 8px;
    padding: 40px 20px;
    text-align: center;
    
    .preview-subtitle {
      font-size: 18px;
      color: #fff;
      margin: 0;
      text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }
  }
}

// 输出设置
.quality-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quality-option {
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: rgba(64, 158, 255, 0.15);
  }
  
  &.selected {
    background: rgba(64, 158, 255, 0.2);
    border: 1px solid #409EFF;
  }
  
  .quality-name {
    display: block;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 4px;
  }
  
  .quality-desc {
    font-size: 12px;
    color: #888;
  }
}

// 底部操作栏
.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px;
  
  .actions-content {
    max-width: 1600px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .project-info {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    color: #888;
    
    .divider {
      color: #444;
    }
  }
  
  .action-buttons {
    display: flex;
    gap: 12px;
  }
}

// ============ 去水印相关样式 ============

// Canvas 框选层
.watermark-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
  
  &.selecting {
    pointer-events: auto;
    cursor: crosshair;
  }
}

// 去水印标签页样式
.watermark-actions {
  display: flex;
  gap: 12px;
  margin: 16px 0;
}

.region-list {
  margin: 16px 0;
  
  h4 {
    font-size: 13px;
    color: #888;
    margin: 0 0 12px;
  }
}

.region-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  margin-bottom: 8px;
  
  .region-index {
    font-size: 12px;
    color: #409EFF;
    font-weight: 500;
  }
  
  .region-info {
    flex: 1;
    font-size: 11px;
    color: #888;
    font-family: monospace;
  }
}

.current-selection {
  margin: 16px 0;
  
  h4 {
    font-size: 13px;
    color: #888;
    margin: 0 0 12px;
  }
}

.selection-info {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  
  span {
    font-size: 12px;
    color: #F56C6C;
    font-family: monospace;
  }
}

.apply-watermark-btn {
  width: 100%;
  margin-top: 16px;
}
</style>
