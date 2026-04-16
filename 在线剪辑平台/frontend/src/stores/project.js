import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProjectStore = defineStore('project', () => {
  // 项目基本信息
  const projectName = ref('')
  const projectId = ref('')
  
  // 视频片段列表
  const videoClips = ref([])
  
  // 分镜剧本
  const scriptFile = ref(null)
  const scriptContent = ref('')
  const scriptParsedResult = ref(null) // 剧本解析结果
  
  // BGM 配置
  const selectedBgm = ref(null)
  const bgmVolume = ref(80)
  const bgmFadeIn = ref(2)
  const bgmFadeOut = ref(2)
  
  // 字幕配置
  const subtitleEnabled = ref(true)
  const subtitleStyle = ref({
    fontSize: 24,
    color: '#ffffff',
    background: 'rgba(0,0,0,0.7)',
    position: 'bottom' // top, bottom, center
  })
  
  // 输出配置
  const outputSettings = ref({
    resolution: '1080p',
    frameRate: 30,
    format: 'mp4',
    quality: 'high'
  })
  
  // 去水印配置
  const watermarkRegions = ref([])
  const watermarkBlur = ref(10)
  
  // 处理进度
  const processingProgress = ref(0)
  const processingStatus = ref('idle') // idle, uploading, processing, completed, error
  const processingMessage = ref('')
  
  // 下载链接
  const downloadUrl = ref('')
  
  // 计算总时长
  const totalDuration = computed(() => {
    return videoClips.value.reduce((sum, clip) => sum + (clip.duration || 0), 0)
  })
  
  // 添加视频片段
  const addVideoClip = (clip) => {
    videoClips.value.push({
      id: Date.now() + Math.random(),
      ...clip,
      order: videoClips.value.length
    })
  }
  
  // 移除视频片段
  const removeVideoClip = (id) => {
    videoClips.value = videoClips.value.filter(clip => clip.id !== id)
  }
  
  // 重新排序
  const reorderClips = (newOrder) => {
    videoClips.value = newOrder.map((id, index) => {
      const clip = videoClips.value.find(c => c.id === id)
      return { ...clip, order: index }
    })
  }
  
  // 设置剧本
  const setScript = (file, content = '') => {
    scriptFile.value = file
    scriptContent.value = content
  }
  
  // 选择 BGM
  const selectBgm = (bgm) => {
    selectedBgm.value = bgm
  }
  
  // 重置项目
  const resetProject = () => {
    projectName.value = ''
    projectId.value = ''
    videoClips.value = []
    scriptFile.value = null
    scriptContent.value = ''
    scriptParsedResult.value = null
    selectedBgm.value = null
    bgmVolume.value = 80
    bgmFadeIn.value = 2
    bgmFadeOut.value = 2
    watermarkRegions.value = []
    watermarkBlur.value = 10
    processingProgress.value = 0
    processingStatus.value = 'idle'
    processingMessage.value = ''
    downloadUrl.value = ''
  }
  
  return {
    projectName,
    projectId,
    videoClips,
    scriptFile,
    scriptContent,
    scriptParsedResult,
    selectedBgm,
    bgmVolume,
    bgmFadeIn,
    bgmFadeOut,
    subtitleEnabled,
    subtitleStyle,
    outputSettings,
    watermarkRegions,
    watermarkBlur,
    processingProgress,
    processingStatus,
    processingMessage,
    downloadUrl,
    totalDuration,
    addVideoClip,
    removeVideoClip,
    reorderClips,
    setScript,
    selectBgm,
    resetProject
  }
})
