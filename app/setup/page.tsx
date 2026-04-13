'use client'
import { useState } from 'react'

export default function SetupPage() {
  const [copied, setCopied] = useState(false)
  
  const sql = `-- 创建角色资产表
CREATE TABLE IF NOT EXISTS characters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  voice_style TEXT,
  appearance_tags TEXT[],
  front_view_url TEXT,
  side_view_url TEXT,
  three_quarter_view_url TEXT,
  feature_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE characters DISABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);`

  const handleCopy = () => {
    navigator.clipboard.writeText(sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      padding: '40px 20px',
      color: '#fff',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '28px', marginBottom: '24px' }}>🔧 数据库初始化</h1>
        
        <div style={{ background: 'rgba(255,193,7,0.1)', border: '1px solid rgba(255,193,7,0.3)', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>⚠️ 首次使用需要执行以下步骤</p>
          <p style={{ margin: 0, opacity: 0.8 }}>复制 SQL → 打开 SQL Editor → 粘贴执行</p>
        </div>

        <pre style={{ background: '#0d1117', borderRadius: '8px', padding: '16px', marginBottom: '24px', overflow: 'auto', fontSize: '13px' }}>
          {sql}
        </pre>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button onClick={handleCopy} style={{ background: copied ? '#10b981' : '#3b82f6', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: '8px', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' }}>
            {copied ? '✓ 已复制' : '📋 复制 SQL'}
          </button>
          
          <a href="https://supabase.com/dashboard/project/wclohnrhypczeckgkqbx/sql/new" target="_blank" style={{ background: '#10b981', color: '#fff', padding: '12px 24px', borderRadius: '8px', textDecoration: 'none', fontSize: '16px', fontWeight: 'bold' }}>
            🚀 打开 SQL Editor
          </a>
          
          <a href="/" style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', padding: '12px 24px', borderRadius: '8px', textDecoration: 'none', fontSize: '16px' }}>
            ← 返回主页
          </a>
        </div>
      </div>
    </div>
  )
}
