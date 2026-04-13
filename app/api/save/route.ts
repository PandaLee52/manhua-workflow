import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '../../../lib/supabase'
import crypto from 'crypto'

function verifyToken(token: string): { username: string } | null {
  if (!token || typeof token !== 'string') return null
  const parts = token.split(':')
  if (parts.length < 2) return null
  return { username: parts[0] }
}

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: '未授权' }, { status: 401 })
    }

    const token = authHeader.substring(7)
    const user = verifyToken(token)
    if (!user) {
      return NextResponse.json({ error: '无效的token' }, { status: 401 })
    }

    const body = await request.json()
    const { title, data } = body

    if (!title) {
      return NextResponse.json({ error: '项目标题不能为空' }, { status: 400 })
    }

    const projectId = crypto.randomBytes(16).toString('hex')
    const now = new Date().toISOString()

    const { error: insertError } = await supabaseAdmin
      .from('projects')
      .insert({
        id: projectId,
        title,
        data: JSON.stringify(data),
        username: user.username,
        created_at: now,
        updated_at: now
      })

    if (insertError) {
      console.error('Insert error:', insertError)
      return NextResponse.json({ error: '保存失败' }, { status: 500 })
    }

    return NextResponse.json({ 
      id: projectId, 
      title,
      updatedAt: now 
    })
  } catch (error) {
    console.error('Save project error:', error)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}
