import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '../../../lib/supabase'

function verifyToken(token: string): { username: string } | null {
  if (!token || typeof token !== 'string') return null
  const parts = token.split(':')
  if (parts.length < 2) return null
  return { username: parts[0] }
}

export async function GET(request: NextRequest) {
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

    const { data: projects, error } = await supabaseAdmin
      .from('projects')
      .select('id, title, created_at, updated_at')
      .eq('username', user.username)
      .order('updated_at', { ascending: false })

    if (error) {
      console.error('Query error:', error)
      return NextResponse.json({ error: '查询失败' }, { status: 500 })
    }

    return NextResponse.json({ 
      projects: projects.map(p => ({
        id: p.id,
        title: p.title,
        createdAt: p.created_at,
        updatedAt: p.updated_at
      }))
    })
  } catch (error) {
    console.error('Get projects error:', error)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}
