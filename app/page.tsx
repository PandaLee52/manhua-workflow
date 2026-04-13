'use client'
import { useState, useEffect } from 'react'

interface User {
  username: string
  createdAt: string
}

interface ParseResult {
  title: string
  format: string
  totalEpisodes: number
  totalScenes: number
  characters: Array<{name: string; description: string}>
  scenes: Array<any>
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
                        <div style={{padding:'16px',background:'var(--bg-tertiary)',borderRadius:'8px',fontFamily:'monospace',whiteSpace:'pre-wrap'}}>
                          {activeScene.imagePrompt || '暂无提示词'}
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

  const profiles = extractProfiles(content)
  const scenes = parseFirstPerson(lines, profiles)
  
  const charSet = new Set<string>()
  scenes.forEach(s => {
    s.characters.forEach((c: string) => charSet.add(c))
    if (s.dialogue) s.dialogue.forEach((d: any) => charSet.add(d.speaker))
  })

  const assets = extractAssets(scenes, profiles, content)

  return {
    title: title.trim(),
    format: 'firstPerson',
    totalEpisodes: Math.max(...scenes.map((s: any) => s.episode), 1),
    totalScenes: scenes.length,
    characters: Array.from(charSet).map(n => ({ name: n, description: profiles[n] || '剧中角色' })),
    scenes,
    assets,
    version: '4.0'
  }
}

function extractProfiles(content: string) {
  const profiles: Record<string, string> = {}
  const blockMatch = content.match(/主要人物[：:]?\s*\n([\s\S]+?)(?=主要场景|付费卡点|第\d+集|$)/)
  if (blockMatch) {
    const lines = blockMatch[1].split('\n')
    let currentName = '', currentDesc = ''
    lines.forEach(line => {
      const nameMatch = line.match(/(?:•|·)?\s*(.+?)[：:（(]/)
      if (nameMatch && nameMatch[1].length < 10) {
        if (currentName) profiles[currentName] = currentDesc
        currentName = nameMatch[1].trim()
        currentDesc = line.replace(nameMatch[0], '').trim()
      } else if (currentName && line.trim()) {
        currentDesc += line.trim()
      }
    })
    if (currentName) profiles[currentName] = currentDesc
  }
  return profiles
}

function parseFirstPerson(lines: string[], profiles: Record<string, string>) {
  const scenes: any[] = []
  let currentEpisode = 1, sceneId = 0
  let protagonist = '女主'
  Object.keys(profiles).forEach(n => { if (profiles[n].includes('女主')) protagonist = n })

  let currentScene: any = null
  let dialogueBuffer: any[] = []
  let lastSpeaker = protagonist
  const allChars = Object.keys(profiles)

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    const epMatch = line.match(/第(\d+)集/)
    if (epMatch) { currentEpisode = parseInt(epMatch[1]); continue }

    const sceneMatch = line.match(/场景[：:]\s*(.+)/)
    if (sceneMatch) {
      if (currentScene) {
        currentScene.dialogue = dialogueBuffer
        currentScene.imagePrompt = genPrompt(currentScene)
        scenes.push(currentScene)
        dialogueBuffer = []
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
        characters: [protagonist],
        dialogue: []
      }
      continue
    }

    if (!currentScene) continue

    const quotes = line.match(/[""「」]([^""「」]+)[""「」]/g)
    if (quotes) {
      quotes.forEach(q => {
        const text = q.replace(/[""「」]/g, '').trim()
        if (text.length > 2 && text.length < 150) {
          const speaker = inferSpeaker(line, protagonist, lastSpeaker, allChars, profiles)
          if (!currentScene.characters.includes(speaker)) currentScene.characters.push(speaker)
          dialogueBuffer.push({ speaker, text })
          lastSpeaker = speaker
        }
      })
    } else if (line.length > 15) {
      currentScene.description += (currentScene.description ? ' ' : '') + line
    }
  }

  if (currentScene) {
    currentScene.dialogue = dialogueBuffer
    currentScene.imagePrompt = genPrompt(currentScene)
    scenes.push(currentScene)
  }
  return scenes
}

function inferSpeaker(line: string, protagonist: string, lastSpeaker: string, allChars: string[], profiles: Record<string, string>) {
  const speakMatch = line.match(/(他|她)(?:说|道|低吼|冷笑)/)
  if (speakMatch) {
    const gender = speakMatch[1]
    for (const c of allChars) {
      const desc = profiles[c] || ''
      if (gender === '他' && (desc.includes('男') || desc.includes('公'))) return c
      if (gender === '她' && (desc.includes('女') || desc.includes('母'))) return c
    }
  }
  return lastSpeaker === protagonist ? protagonist : protagonist
}

function genPrompt(scene: any) {
  const shotMap: Record<string, string> = { '远景': 'wide shot', '全景': 'full shot', '中景': 'medium shot', '近景': 'close-up', '特写': 'extreme close-up' }
  const shot = shotMap[scene.shotType] || 'medium shot'
  const chars = scene.characters.slice(0, 2).join(' and ')
  const action = scene.description ? scene.description.slice(0, 60) : 'talking'
  return `${shot}, ${chars}, ${action}, ${scene.location}, cinematic lighting, photorealistic, 8k`
}

function extractAssets(scenes: any[], profiles: Record<string, string>, content: string) {
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
    const desc = profiles[name]
    const freq = charFreq[name] || 0
    const priority = freq >= 10 ? 'P0' : freq >= 5 ? 'P1' : 'P2'
    return { name, description: desc, frequency: freq, priority, prompts: genCharacterPrompts(name, desc) }
  }).sort((a, b) => b.frequency - a.frequency)

  Object.keys(charFreq).forEach(name => {
    if (!characters.find(c => c.name === name)) {
      const freq = charFreq[name]
      const priority = freq >= 10 ? 'P0' : freq >= 5 ? 'P1' : 'P2'
      characters.push({ name, description: '剧中角色', frequency: freq, priority, prompts: genCharacterPrompts(name, '剧中角色') })
    }
  })

  const locations = Object.keys(sceneFreq).map(loc => {
    const freq = sceneFreq[loc]
    const priority = freq >= 3 ? 'P0' : freq >= 2 ? 'P1' : 'P2'
    return { name: loc, frequency: freq, priority, prompts: genLocationPrompts(loc) }
  }).sort((a, b) => b.frequency - a.frequency)

  const props = extractProps(content)

  return { characters, locations, props }
}

function genCharacterPrompts(name: string, desc: string) {
  const ageMatch = desc.match(/(\d+)\s*岁/)
  const age = ageMatch ? ageMatch[1] : '25'

  const gender = desc.includes('女') || name.includes('婷') || name.includes('妈') || name.includes('妹') ? 'woman' : 'man'
  let ageDesc = 'young'
  if (parseInt(age) >= 40 && parseInt(age) < 60) ageDesc = 'middle-aged'
  if (parseInt(age) >= 60) ageDesc = 'elderly'

  let emotion = 'neutral expression'
  if (desc.includes('渣男') || desc.includes('PUA')) emotion = 'insincere smile, calculating eyes'
  else if (desc.includes('心机')) emotion = 'fake sweet smile'
  else if (desc.includes('护女') || desc.includes('开明')) emotion = 'kind and protective expression'
  else if (desc.includes('贪财') || desc.includes('无赖')) emotion = 'greedy and shameless expression'

  const basePrompt = `Chinese ${ageDesc} ${gender}, ${age} years old, ${emotion}, photorealistic, 8k`

  return {
    baseline: basePrompt,
    wedding: gender === 'woman' ?
      `Chinese bride, ${age} years old, wearing elegant white wedding dress, ${emotion}, wedding venue background, soft lighting, photorealistic, 8k` :
      `Chinese groom, ${age} years old, wearing black formal suit, ${emotion}, wedding venue background, dramatic lighting, photorealistic, 8k`
  }
}

function genLocationPrompts(loc: string) {
  const locMap: Record<string, string> = {
    '婚礼现场': 'Chinese wedding venue, hotel banquet hall, decorated with flowers and ribbons, stage with red carpet, warm romantic lighting, photorealistic, 8k',
    '婚礼后台': 'Hotel private room, simple interior, mirror and clothing rack, bridal dress hanging, soft indoor lighting, photorealistic, 8k',
    '酒店空包房': 'Hotel private dining room, empty round table, neutral indoor lighting, photorealistic, 8k',
    '警察局': 'Chinese police station interior, simple office setting, neutral fluorescent lighting, photorealistic, 8k',
    '家中客厅': 'Chinese middle-class home living room, comfortable sofa, warm homey atmosphere, soft evening lighting, photorealistic, 8k',
    '咖啡厅': 'Modern coffee shop interior, wooden tables, soft ambient lighting, cozy atmosphere, photorealistic, 8k'
  }

  const key = Object.keys(locMap).find(k => loc.includes(k))
  return { baseline: key ? locMap[key] : `${loc}, interior or exterior scene, photorealistic, 8k` }
}

function extractProps(content: string) {
  const propsKeywords = [
    { name: '遗像', pattern: /遗像|照片/, prompt: 'Framed portrait photo, black and white, memorial style, elegant frame, photorealistic, 8k' },
    { name: '婚纱', pattern: /婚纱|wedding dress/, prompt: 'Elegant white wedding dress, elaborate design, flowing fabric, soft lighting, photorealistic, 8k' },
    { name: '茶具', pattern: /茶|敬茶/, prompt: 'Chinese tea set, delicate porcelain cups and teapot, traditional style, soft lighting, photorealistic, 8k' }
  ]

  return propsKeywords.filter(p => p.pattern.test(content)).map(p => ({ name: p.name, prompt: p.prompt }))
}
