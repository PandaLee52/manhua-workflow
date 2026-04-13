import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin, isSupabaseConfigured } from '../../../../lib/supabase'

function verifyToken(token: string): { username: string } | null {
  if (!token || typeof token !== 'string') return null
  const parts = token.split(':')
  if (parts.length < 2) return null
  return { username: parts[0] }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // 检查 Supabase 是否配置
    if (!isSupabaseConfigured) {
      return NextResponse.json({ 
        error: '请先配置 Supabase 数据库',
        needsSetup: true 
      }, { status: 503 })
    }

    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: '未授权' }, { status: 401 })
    }

    const token = authHeader.substring(7)
    const user = verifyToken(token)
    if (!user) {
      return NextResponse.json({ error: '无效的token' }, { status: 401 })
    }

    const { id } = params
    const { data: project, error } = await supabaseAdmin
      .from('projects')
      .select('*')
      .eq('id', id)
      .eq('username', user.username)
      .single()

    if (!project) {
      return NextResponse.json({ error: '项目不存在' }, { status: 404 })
    }

    if (error) {
      console.error('Query error:', error)
      return NextResponse.json({ error: '查询失败' }, { status: 500 })
    }

    const projectData = typeof project.data === 'string' 
      ? JSON.parse(project.data) 
      : project.data

    return NextResponse.json({
      id: project.id,
      title: project.title,
      ...projectData
    })
  } catch (error) {
    console.error('Get project error:', error)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
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

    const { id } = params
    const { error } = await supabaseAdmin
      .from('projects')
      .delete()
      .eq('id', id)
      .eq('username', user.username)

    if (error) {
      console.error('Delete error:', error)
      return NextResponse.json({ error: '删除失败' }, { status: 500 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Delete project error:', error)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}
