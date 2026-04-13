'use client'
import { useState, useEffect } from 'react'

interface User {
  username: string
  createdAt: string
}

interface DialogueLine {
  speaker: string
  text: string
}

interface VideoSegment {
  duration: number
  shotType: string
  description: string
  characters: string[]
  hasDialogue: boolean
  dialogue?: DialogueLine[]
  videoPrompt: string
  voicePrompt?: string
}

interface ParseResult {
  title: string
  format: string
  totalEpisodes: number
  totalScenes: number
  characters: Array<{name: string; description: string; voiceStyle?: string}>
  scenes: Array<{
    id: number
    episode: number
    sceneNumber: string
    shotType: string
    type: string
    location: string
    description: string
    characters: string[]
    dialogue: DialogueLine[]
    videoSegments: VideoSegment[]
  }>
  assets: any
  version: string
}

interface SavedProject {
  id: string
  title: string
  createdAt: string
  updatedAt: string
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string>('')
  const [projects, setProjects] = useState<SavedProject[]>([])
  const [parseResult, setParseResult] = useState<ParseResult | null>(null)
  const [activeScene, setActiveScene] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('scene')
  const [activeMainTab, setActiveMainTab] = useState('script')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  // 检查登录状态
  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
    }
  }, [])

  // 加载项目列表
  useEffect(() => {
    if (user && token) {
      loadProjects()
    }
  }, [user, token])

  const loadProjects = async () => {
    try {
      const res = await fetch('/api/projects', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setProjects(data.projects || [])
      }
    } catch (err) {
      console.error('加载项目失败:', err)
    }
  }

  const handleFileUpload = async (file: File) => {
    setLoading(true)
    try {
      const text = await file.text()
      const result = parseScript(text)
      setParseResult(result)
      setMessage('解析成功！')
      
      // 自动保存项目
      await saveProject(result)
    } catch (err) {
      setMessage('解析失败: ' + (err as Error).message)
    }
    setLoading(false)
  }

  const saveProject = async (data: ParseResult) => {
    try {
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      })
      if (res.ok) {
        loadProjects()
      }
    } catch (err) {
      console.error('保存失败:', err)
    }
  }

  const loadProject = async (projectId: string) => {
    try {
      const res = await fetch(`/api/projects/${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setParseResult(data)
        setActiveMainTab('script')
      }
    } catch (err) {
      console.error('加载项目失败:', err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    setToken('')
    setParseResult(null)
  }

  if (!user) {
    return <LoginPage onLogin={(u, t) => { setUser(u); setToken(t) }} />
  }

  return (
    <div className="container">
      <header className="header">
        <h1>AI漫剧工作流平台 v4.0</h1>
        <div className="header-right">
          <span className="user-info">👤 {user.username}</span>
          <button className="btn btn-secondary" onClick={handleLogout}>退出</button>
        </div>
      </header>

      {message && <div style={{padding:'12px',background:'var(--bg-tertiary)',borderRadius:'6px',marginBottom:'20px'}}>{message}</div>}

      <div className="tab-group" style={{marginBottom:'20px'}}>
        <button className={`tab ${activeMainTab === 'projects' ? 'active' : ''}`} onClick={() => setActiveMainTab('projects')}>我的项目</button>
        <button className={`tab ${activeMainTab === 'script' ? 'active' : ''}`} onClick={() => setActiveMainTab('script')}>剧本解析</button>
        <button className={`tab ${activeMainTab === 'assets' ? 'active' : ''}`} onClick={() => setActiveMainTab('assets')}>核心资产</button>
      </div>

      {activeMainTab === 'projects' && (
        <div className="card">
          <div className="card-title">已保存的项目</div>
          <div className="scene-list">
            {projects.length === 0 ? (
              <div style={{textAlign:'center',color:'var(--text-secondary)',padding:'40px'}}>暂无项目，请上传剧本创建新项目</div>
            ) : (
              projects.map(p => (
                <div key={p.id} className="scene-item" onClick={() => loadProject(p.id)}>
                  <div className="scene-header">
                    <span className="scene-number">{p.title}</span>
                    <span className="scene-type">{new Date(p.updatedAt).toLocaleDateString()}</span>
                  </div>
                  <div className="scene-preview">点击加载项目</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeMainTab === 'script' && (
        parseResult ? (
          <>
            <div className="stats">
              <div className="stat-item"><div className="stat-value">{parseResult.totalEpisodes}</div><div className="stat-label">总集数</div></div>
              <div className="stat-item"><div className="stat-value">{parseResult.totalScenes}</div><div className="stat-label">总场景</div></div>
              <div className="stat-item"><div className="stat-value">{parseResult.characters.length}</div><div className="stat-label">角色总数</div></div>
              <div className="stat-item"><div className="stat-value">{parseResult.assets?.characters?.filter((c:any) => c.priority === 'P0').length || 0}</div><div className="stat-label">P0角色</div></div>
              <div className="stat-item"><div className="stat-value">{parseResult.assets?.locations?.filter((l:any) => l.priority === 'P0').length || 0}</div><div className="stat-label">P0场景</div></div>
            </div>

            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'20px'}}>
              <div>
                <h2 style={{fontSize:'20px',marginBottom:'4px'}}>《{parseResult.title}》</h2>
                <p style={{fontSize:'13px',color:'var(--text-secondary)'}}>{parseResult.format === 'firstPerson' ? '第一人称' : '标准'}格式</p>
              </div>
              <div className="action-bar">
                <button className="btn btn-secondary" onClick={() => { setParseResult(null); setActiveScene(null) }}>上传新剧本</button>
              </div>
            </div>

            <div className="main-content">
              <div className="card">
                <div className="card-title">分镜列表</div>
                <div className="scene-list">
                  {parseResult.scenes.map((s: any) => (
                    <div key={s.id} className={`scene-item ${activeScene?.id === s.id ? 'active' : ''}`} onClick={() => setActiveScene(s)}>
                      <div className="scene-header">
                        <span className="scene-number">S{s.sceneNumber}</span>
                        <span className="scene-type">{s.type}</span>
                      </div>
                      <div className="scene-preview">{s.location}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="content-area">
                {activeScene ? (
                  <>
                    <div className="content-title">第{activeScene.episode}集 - {activeScene.location}</div>
                    <div className="tab-group">
                      <button className={`tab ${activeTab === 'scene' ? 'active' : ''}`} onClick={() => setActiveTab('scene')}>分镜</button>
                      <button className={`tab ${activeTab === 'dialogue' ? 'active' : ''}`} onClick={() => setActiveTab('dialogue')}>台词</button>
                      <button className={`tab ${activeTab === 'prompt' ? 'active' : ''}`} onClick={() => setActiveTab('prompt')}>提示词</button>
                    </div>
                    <div>
                      {activeTab === 'scene' && (
                        <div style={{padding:'16px',background:'var(--bg-tertiary)',borderRadius:'8px'}}>
                          <p style={{marginBottom:'12px'}}><strong>场景：</strong>{activeScene.location}</p>
                          <p style={{marginBottom:'12px'}}><strong>角色：</strong>{activeScene.characters?.join('、')}</p>
                          <p><strong>描述：</strong>{activeScene.description || '暂无'}</p>
                        </div>
                      )}
                      {activeTab === 'dialogue' && (
                        <div>
                          {activeScene.dialogue?.map((d: any, i: number) => (
                            <div key={i} style={{padding:'12px',background:'var(--bg-tertiary)',borderRadius:'8px',marginBottom:'8px'}}>
                              <div style={{fontWeight:600,color:'var(--accent)',marginBottom:'4px'}}>{d.speaker}</div>
                              <div style={{color:'var(--text-secondary)'}}>"{d.text}"</div>
                            </div>
                          )) || <div style={{color:'var(--text-secondary)'}}>暂无台词</div>}
                        </div>
                      )}
                      {activeTab === 'prompt' && (
                        <div style={{padding:'8px'}}>
                          {activeScene.videoSegments?.length > 0 ? (
                            activeScene.videoSegments.map((seg: VideoSegment, idx: number) => (
                              <div key={idx} style={{marginBottom:'16px',padding:'12px',background:'var(--bg-tertiary)',borderRadius:'8px'}}>
                                <div style={{marginBottom:'8px',fontSize:'13px',color:'var(--text-secondary)'}}>
                                  📹 视频分段 {idx + 1} ({seg.duration}秒) - {seg.shotType}
                                </div>
                                <div style={{fontFamily:'monospace',fontSize:'12px',whiteSpace:'pre-wrap',marginBottom:'8px',color:'var(--text-primary)'}}>
                                  {seg.videoPrompt}
                                </div>
                                {seg.voicePrompt && (
                                  <div style={{padding:'8px',background:'var(--bg-primary)',borderRadius:'6px',fontFamily:'monospace',fontSize:'12px',whiteSpace:'pre-wrap',color:'#22c55e'}}>
                                    🎤 台词：{'\n'}{seg.voicePrompt}
                                  </div>
                                )}
                              </div>
                            ))
                          ) : (
                            <div style={{color:'var(--text-secondary)'}}>暂无提示词</div>
                          )}
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div style={{textAlign:'center',color:'var(--text-secondary)',padding:'60px'}}>请选择分镜查看详情</div>
                )}
              </div>

              <div className="card">
                <div className="card-title">核心角色</div>
                <div className="scene-list">
                  {parseResult.characters.slice(0, 10).map((c: any) => (
                    <div key={c.name} className="scene-item">
                      <div className="scene-header">
                        <span className="scene-number">{c.name}</span>
                      </div>
                      <div className="scene-preview">{c.description.slice(0, 30)}...</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="upload-area" onClick={() => document.getElementById('fileInput')?.click()}>
            <div style={{fontSize:'48px',marginBottom:'16px',opacity:0.6}}>📄</div>
            <p style={{fontSize:'18px',marginBottom:'8px'}}>点击上传剧本文件</p>
            <p style={{fontSize:'14px',color:'var(--text-secondary)',marginBottom:'16px'}}>支持 .txt / .md 格式</p>
            <p style={{fontSize:'13px',color:'var(--text-secondary)'}}>数据将自动保存到您的账户</p>
            <input id="fileInput" type="file" accept=".txt,.md" style={{display:'none'}} onChange={(e) => {
              if (e.target.files?.[0]) handleFileUpload(e.target.files[0])
            }} />
          </div>
        )
      )}

      {activeMainTab === 'assets' && parseResult?.assets && (
        <div>
          <div className="asset-section">
            <div className="asset-section-title">
              <span>🎭 角色资产</span>
            </div>
            <div className="asset-grid">
              {parseResult.assets.characters.map((c: any) => (
                <div key={c.name} className="asset-card">
                  <div className="asset-card-header">
                    <span className="asset-name">{c.name}</span>
                    <span className={`badge badge-${c.priority.toLowerCase()}`}>{c.priority}</span>
                  </div>
                  <div className="asset-desc">{c.description}</div>
                  <div className="asset-prompt-header">
                    <span>基准提示词</span>
                    <button className="copy-btn" onClick={() => navigator.clipboard.writeText(c.prompts.baseline)}>复制</button>
                  </div>
                  <div className="asset-prompt">{c.prompts.baseline}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="asset-section">
            <div className="asset-section-title">
              <span>🎬 场景资产</span>
            </div>
            <div className="asset-grid">
              {parseResult.assets.locations.map((l: any) => (
                <div key={l.name} className="asset-card">
                  <div className="asset-card-header">
                    <span className="asset-name">{l.name}</span>
                    <span className={`badge badge-${l.priority.toLowerCase()}`}>{l.priority}</span>
                  </div>
                  <div className="asset-prompt-header">
                    <span>提示词</span>
                    <button className="copy-btn" onClick={() => navigator.clipboard.writeText(l.prompts.baseline)}>复制</button>
                  </div>
                  <div className="asset-prompt">{l.prompts.baseline}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function LoginPage({ onLogin }: { onLogin: (user: User, token: string) => void }) {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    try {
      const res = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: isLogin ? 'login' : 'register',
          username,
          password
        })
      })

      const data = await res.json()
      
      if (res.ok) {
        localStorage.setItem('token', data.token)
        localStorage.setItem('user', JSON.stringify(data.user))
        onLogin(data.user, data.token)
      } else {
        setError(data.error || '操作失败')
      }
    } catch (err) {
      setError('网络错误，请重试')
    }
  }

  return (
    <div className="container">
      <div className="login-form">
        <h2>{isLogin ? '登录' : '注册'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">用户名</label>
            <input 
              className="form-input" 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required 
            />
          </div>
          <div className="form-group">
            <label className="form-label">密码</label>
            <input 
              className="form-input" 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </div>
          <button className="login-btn" type="submit">
            {isLogin ? '登录' : '注册'}
          </button>
          {error && <div className="error-msg">{error}</div>}
          <div style={{textAlign:'center',marginTop:'16px',fontSize:'13px',color:'var(--text-secondary)'}}>
            {isLogin ? '没有账号？' : '已有账号？'}
            <button type="button" onClick={() => setIsLogin(!isLogin)} style={{color:'var(--accent)',background:'none',border:'none',cursor:'pointer',marginLeft:'4px'}}>
              {isLogin ? '注册' : '登录'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function parseScript(content: string): ParseResult {
  const lines = content.split('\n').filter(l => l.trim())
  let title = '未命名剧本'
  const titleMatch = content.match(/《(.+?)》/)
  if (titleMatch) title = titleMatch[1]
  
  // 提取人物档案
  const profiles = extractProfilesV2(content)
  
  // 解析场景
  const scenes = parseScenesV2(lines, profiles)
  
  // 提取核心资产
  const assets = extractAssetsV2(scenes, profiles, content)
  
  // 收集所有角色
  const charSet = new Set<string>()
  scenes.forEach(s => {
    s.characters.forEach((c: string) => charSet.add(c))
    if (s.dialogue) s.dialogue.forEach((d: DialogueLine) => charSet.add(d.speaker))
  })
  
  return {
    title: title.trim(),
    format: 'manhua',
    totalEpisodes: Math.max(...scenes.map(s => s.episode), 1),
    totalScenes: scenes.length,
    characters: Array.from(charSet).map(n => ({ 
      name: n, 
      description: profiles[n]?.description || '剧中角色',
      voiceStyle: profiles[n]?.voiceStyle
    })),
    scenes,
    assets,
    version: '5.0'
  }
}

// 人物档案接口
interface ProfileV2 {
  name: string
  description: string
  gender: 'male' | 'female'
  age: number
  voiceStyle: string
}

// 提取人物档案 V2
function extractProfilesV2(content: string): Record<string, ProfileV2> {
  const profiles: Record<string, ProfileV2> = {}
  
  const blockMatch = content.match(/主要人物[：:]?\s*\n([\s\S]+?)(?=主要场景|付费卡点|第\d+集|$)/)
  
  if (blockMatch) {
    const lines = blockMatch[1].split('\n')
    let currentName = ''
    let currentDesc = ''
    
    lines.forEach(line => {
      const nameMatch = line.match(/(?:•|·|\d+[\.、])?\s*(.+?)[：:（(]/)
      if (nameMatch && nameMatch[1].length < 10) {
        if (currentName) {
          profiles[currentName] = parseProfileV2(currentName, currentDesc)
        }
        currentName = nameMatch[1].trim()
        currentDesc = line.replace(nameMatch[0], '').trim()
      } else if (currentName && line.trim()) {
        currentDesc += line.trim()
      }
    })
    
    if (currentName) {
      profiles[currentName] = parseProfileV2(currentName, currentDesc)
    }
  }
  
  return profiles
}

// 解析单个人物档案
function parseProfileV2(name: string, desc: string): ProfileV2 {
  const isFemale = desc.includes('女') || name.includes('婷') || name.includes('妈') || name.includes('妹') || name.includes('姐')
  const gender = isFemale ? 'female' : 'male'
  
  const ageMatch = desc.match(/(\d+)\s*岁/)
  const age = ageMatch ? parseInt(ageMatch[1]) : 25
  
  const voiceStyle = generateVoiceStyle(name, desc, gender, age)
  
  return { name, description: desc, gender, age, voiceStyle }
}

// 生成音色描述
function generateVoiceStyle(name: string, desc: string, gender: string, age: number): string {
  const styles: string[] = []
  
  if (age < 25) styles.push(gender === 'female' ? '少女音' : '少年音')
  else if (age < 40) styles.push(gender === 'female' ? '青年女声' : '青年男声')
  else if (age < 60) styles.push(gender === 'female' ? '中年女声' : '中年男声')
  else styles.push(gender === 'female' ? '老年女声' : '老年男声')
  
  if (desc.includes('冷') || desc.includes('高冷')) styles.push('冷漠冷淡')
  if (desc.includes('温柔') || desc.includes('善良')) styles.push('温柔温和')
  if (desc.includes('心机') || desc.includes('绿茶')) styles.push('虚伪甜腻')
  if (desc.includes('霸道') || desc.includes('总裁')) styles.push('霸道强势')
  if (desc.includes('渣男')) styles.push('油嘴滑舌')
  if (desc.includes('泼辣') || desc.includes('嚣张')) styles.push('尖锐刻薄')
  
  return styles.join('，') || (gender === 'female' ? '温柔女声' : '沉稳男声')
}

// 解析场景 V2
function parseScenesV2(lines: string[], profiles: Record<string, ProfileV2>) {
  const scenes: any[] = []
  let currentEpisode = 1
  let sceneId = 0
  let currentScene: any = null
  let descriptionBuffer: string[] = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    // 匹配集数
    const epMatch = line.match(/第(\d+)集/)
    if (epMatch) {
      currentEpisode = parseInt(epMatch[1])
      continue
    }
    
    // 匹配场景标记
    const sceneMatch = line.match(/场景[：:]\s*(.+)/)
    if (sceneMatch) {
      // 保存上一个场景
      if (currentScene) {
        currentScene.description = descriptionBuffer.join(' ')
        currentScene.videoSegments = generateVideoSegments(currentScene, profiles)
        scenes.push(currentScene)
        descriptionBuffer = []
      }
      
      sceneId++
      currentScene = {
        id: sceneId,
        episode: currentEpisode,
        sceneNumber: String(sceneId),
        shotType: '中景',
        type: '对话',
        location: sceneMatch[1].trim(),
        description: '',
        characters: [],
        dialogue: [],
        videoSegments: []
      }
      continue
    }
    
    if (!currentScene) continue
    
    // 匹配台词格式：**角色名**：台词
    const dialogueMatch = line.match(/\*\*(.+?)\*\*[：:]\s*(.+)/)
    if (dialogueMatch) {
      const speaker = dialogueMatch[1].trim()
      const text = dialogueMatch[2].trim()
      
      // 排除旁白/解说标记
      if (!['解说', '旁白', 'VO', '画外音'].includes(speaker)) {
        if (!currentScene.characters.includes(speaker)) {
          currentScene.characters.push(speaker)
        }
        currentScene.dialogue.push({ speaker, text })
      }
      continue
    }
    
    // 匹配简单格式：角色名：台词（无**标记）
    const simpleDialogueMatch = line.match(/^([^：:*]+)[：:]\s*(.+)/)
    if (simpleDialogueMatch && !line.includes('场景') && !line.includes('主要')) {
      const speaker = simpleDialogueMatch[1].trim()
      const text = simpleDialogueMatch[2].trim()
      
      // 只有当说话人在档案中时才认为是台词
      if (profiles[speaker] && !['解说', '旁白', 'VO', '画外音'].includes(speaker)) {
        if (!currentScene.characters.includes(speaker)) {
          currentScene.characters.push(speaker)
        }
        currentScene.dialogue.push({ speaker, text })
        continue
      }
    }
    
    // 匹配景别标记
    const shotMatch = line.match(/【(全景|远景|中景|近景|特写)】/)
    if (shotMatch) {
      currentScene.shotType = shotMatch[1]
      continue
    }
    
    // 匹配情绪/动作标记
    const emotionMatch = line.match(/（(.+?)）/)
    if (emotionMatch) {
      descriptionBuffer.push(emotionMatch[1])
      continue
    }
    
    // 其他文本作为场景描述
    if (line.length > 10 && !line.startsWith('解说') && !line.startsWith('旁白')) {
      descriptionBuffer.push(line)
    }
  }
  
  // 保存最后一个场景
  if (currentScene) {
    currentScene.description = descriptionBuffer.join(' ')
    currentScene.videoSegments = generateVideoSegments(currentScene, profiles)
    scenes.push(currentScene)
  }
  
  return scenes
}

// 生成视频分段（每段15秒）
function generateVideoSegments(scene: any, profiles: Record<string, ProfileV2>): VideoSegment[] {
  const segments: VideoSegment[] = []
  const DURATION_PER_SEGMENT = 15
  
  if (scene.dialogue.length > 0) {
    let currentSegment: VideoSegment = {
      duration: 0,
      shotType: scene.shotType,
      description: '',
      characters: [],
      hasDialogue: false,
      dialogue: [],
      videoPrompt: ''
    }
    
    for (const line of scene.dialogue) {
      const lineDuration = Math.max(3, Math.min(5, line.text.length * 0.3))
      
      if (currentSegment.duration + lineDuration <= DURATION_PER_SEGMENT) {
        currentSegment.duration += lineDuration
        currentSegment.dialogue!.push(line)
        currentSegment.hasDialogue = true
        if (!currentSegment.characters.includes(line.speaker)) {
          currentSegment.characters.push(line.speaker)
        }
      } else {
        if (currentSegment.duration > 0) {
          currentSegment.videoPrompt = generateVideoPromptV2(scene, currentSegment, profiles)
          currentSegment.voicePrompt = generateVoicePromptV2(currentSegment, profiles)
          segments.push(currentSegment)
        }
        
        currentSegment = {
          duration: lineDuration,
          shotType: scene.shotType,
          description: '',
          characters: [line.speaker],
          hasDialogue: true,
          dialogue: [line],
          videoPrompt: ''
        }
      }
    }
    
    if (currentSegment.duration > 0) {
      currentSegment.videoPrompt = generateVideoPromptV2(scene, currentSegment, profiles)
      currentSegment.voicePrompt = generateVoicePromptV2(currentSegment, profiles)
      segments.push(currentSegment)
    }
  } else {
    const description = scene.description || '角色在场景中'
    segments.push({
      duration: DURATION_PER_SEGMENT,
      shotType: scene.shotType,
      description: description,
      characters: scene.characters,
      hasDialogue: false,
      videoPrompt: generateVideoPromptV2(scene, {
        duration: DURATION_PER_SEGMENT,
        shotType: scene.shotType,
        description: description,
        characters: scene.characters,
        hasDialogue: false,
        videoPrompt: ''
      }, profiles)
    })
  }
  
  return segments
}

// 生成视频提示词（用于 Vidu/可灵）
function generateVideoPromptV2(scene: any, segment: VideoSegment, profiles: Record<string, ProfileV2>): string {
  const shotMap: Record<string, string> = {
    '远景': 'wide establishing shot',
    '全景': 'full body shot',
    '中景': 'medium shot',
    '近景': 'close-up shot',
    '特写': 'extreme close-up, face detail'
  }
  
  const shot = shotMap[segment.shotType] || 'medium shot'
  const chars = segment.characters.slice(0, 2).join(' and ') || 'character'
  const location = scene.location
  
  let prompt = `${shot}, ${chars}`
  
  if (segment.description) {
    prompt += `, ${segment.description.slice(0, 80)}`
  } else if (scene.description) {
    prompt += `, ${scene.description.slice(0, 80)}`
  }
  
  prompt += `, at ${location}`
  
  if (segment.hasDialogue && segment.dialogue && segment.dialogue.length > 0) {
    const firstLine = segment.dialogue[0]
    prompt += `, ${firstLine.speaker} speaking, lip-sync`
    
    const profile = profiles[firstLine.speaker]
    if (profile) {
      if (profile.description.includes('冷') || profile.description.includes('高冷')) {
        prompt += ', cold expression, slight frown'
      } else if (profile.description.includes('温柔')) {
        prompt += ', gentle smile, warm expression'
      } else if (profile.description.includes('愤怒') || profile.description.includes('生气')) {
        prompt += ', angry expression, intense gaze'
      }
    }
  }
  
  prompt += ', cinematic camera movement, professional lighting, photorealistic, 4K video'
  
  return prompt
}

// 生成语音提示词
function generateVoicePromptV2(segment: VideoSegment, profiles: Record<string, ProfileV2>): string | undefined {
  if (!segment.hasDialogue || !segment.dialogue || segment.dialogue.length === 0) {
    return undefined
  }
  
  const lines = segment.dialogue.map(d => {
    const profile = profiles[d.speaker]
    const voiceStyle = profile?.voiceStyle || '自然语气'
    return `【${d.speaker}(${voiceStyle})】：${d.text}`
  })
  
  return lines.join('\n')
}

// 提取核心资产 V2
function extractAssetsV2(scenes: any[], profiles: Record<string, ProfileV2>, content: string) {
  const charFreq: Record<string, number> = {}
  scenes.forEach(s => {
    s.characters.forEach((c: string) => { charFreq[c] = (charFreq[c] || 0) + 1 })
    if (s.dialogue) s.dialogue.forEach((d: any) => { charFreq[d.speaker] = (charFreq[d.speaker] || 0) + 1 })
  })
  
  const sceneFreq: Record<string, number> = {}
  scenes.forEach(s => {
    const loc = s.location || '未知'
    sceneFreq[loc] = (sceneFreq[loc] || 0) + 1
  })
  
  const characters = Object.keys(profiles).map(name => {
    const profile = profiles[name]
    const freq = charFreq[name] || 0
    const priority = freq >= 10 ? 'P0' : freq >= 5 ? 'P1' : 'P2'
    return {
      name,
      description: profile.description,
      gender: profile.gender,
      age: profile.age,
      voiceStyle: profile.voiceStyle,
      frequency: freq,
      priority,
      prompts: generateCharacterVideoPromptsV2(name, profile)
    }
  }).sort((a, b) => b.frequency - a.frequency)
  
  Object.keys(charFreq).forEach(name => {
    if (!characters.find(c => c.name === name)) {
      const freq = charFreq[name]
      const priority = freq >= 10 ? 'P0' : freq >= 5 ? 'P1' : 'P2'
      characters.push({
        name,
        description: '剧中角色',
        gender: 'male' as const,
        age: 25,
        voiceStyle: '自然语气',
        frequency: freq,
        priority,
        prompts: generateCharacterVideoPromptsV2(name, { name, description: '剧中角色', gender: 'male', age: 25, voiceStyle: '自然语气' })
      })
    }
  })
  
  const locations = Object.keys(sceneFreq).map(loc => {
    const freq = sceneFreq[loc]
    const priority = freq >= 3 ? 'P0' : freq >= 2 ? 'P1' : 'P2'
    return {
      name: loc,
      frequency: freq,
      priority,
      prompts: generateLocationVideoPromptsV2(loc)
    }
  }).sort((a, b) => b.frequency - a.frequency)
  
  const props = extractPropsV2(content)
  
  return { characters, locations, props }
}

// 生成角色视频提示词 V2
function generateCharacterVideoPromptsV2(name: string, profile: ProfileV2) {
  const ageDesc = profile.age < 30 ? 'young' : profile.age < 50 ? 'middle-aged' : 'elderly'
  const gender = profile.gender === 'female' ? 'woman' : 'man'
  
  const baseline = `medium shot, Chinese ${ageDesc} ${gender}, ${profile.age} years old, standing still, neutral expression, professional lighting, photorealistic, 4K video`
  
  const speaking = `close-up shot, Chinese ${ageDesc} ${gender}, ${profile.age} years old, speaking naturally, lip-sync movement, ${profile.voiceStyle}, professional lighting, 4K video`
  
  return { baseline, speaking }
}

// 生成场景视频提示词 V2
function generateLocationVideoPromptsV2(loc: string) {
  const locMap: Record<string, string> = {
    '婚礼现场': 'wide shot, Chinese wedding venue, hotel banquet hall, decorated with flowers, stage with red carpet, guests seated, warm romantic lighting, slow camera pan, 4K video',
    '婚礼后台': 'medium shot, hotel private room, bridal dress hanging on rack, mirror reflection, soft indoor lighting, static shot, 4K video',
    '家中客厅': 'wide shot, Chinese middle-class home living room, comfortable sofa, TV in background, warm homey atmosphere, evening light through window, 4K video',
    '咖啡厅': 'medium shot, modern coffee shop interior, wooden tables, ambient lighting, customers in background, slow camera movement, 4K video'
  }
  
  const key = Object.keys(locMap).find(k => loc.includes(k))
  return {
    baseline: key ? locMap[key] : `wide shot, ${loc}, interior scene, professional lighting, slow camera movement, 4K video`
  }
}

// 提取道具 V2
function extractPropsV2(content: string) {
  const propsKeywords = [
    { name: '遗像', pattern: /遗像|照片/, prompt: 'framed portrait photo on table, black and white, memorial style, soft lighting, 4K video' },
    { name: '婚纱', pattern: /婚纱|wedding dress/, prompt: 'elegant white wedding dress on hanger, flowing fabric, soft lighting, 4K video' },
    { name: '茶具', pattern: /茶|敬茶/, prompt: 'Chinese tea set on table, porcelain cups and teapot, steam rising, soft lighting, 4K video' }
  ]
  
  return propsKeywords.filter(p => p.pattern.test(content)).map(p => ({ name: p.name, prompt: p.prompt }))
}
