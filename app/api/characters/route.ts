import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin, isSupabaseConfigured } from '../../../lib/supabase'

// 获取用户角色列表
export async function GET(request: NextRequest) {
  try {
    if (!isSupabaseConfigured) {
      return NextResponse.json({ 
        error: '数据库未配置',
        characters: [] 
      }, { status: 503 })
    }

    const authHeader = request.headers.get('Authorization')
    if (!authHeader) {
      return NextResponse.json({ error: '未授权' }, { status: 401 })
    }

    const token = authHeader.replace('Bearer ', '')
    const username = token.split(':')[0]

    const { data, error } = await supabaseAdmin
      .from('characters')
      .select('*')
      .eq('user_id', username)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('查询角色失败:', error)
      return NextResponse.json({ error: '查询失败', characters: [] }, { status: 500 })
    }

    return NextResponse.json({ characters: data || [] })
  } catch (err) {
    console.error('获取角色列表失败:', err)
    return NextResponse.json({ error: '服务器错误', characters: [] }, { status: 500 })
  }
}

// 创建新角色
export async function POST(request: NextRequest) {
  try {
    if (!isSupabaseConfigured) {
      return NextResponse.json({ error: '数据库未配置' }, { status: 503 })
    }

    const authHeader = request.headers.get('Authorization')
    if (!authHeader) {
      return NextResponse.json({ error: '未授权' }, { status: 401 })
    }

    const token = authHeader.replace('Bearer ', '')
    const username = token.split(':')[0]
    const body = await request.json()

    const { name, description, voice_style, appearance_tags, feature_code } = body

    if (!name) {
      return NextResponse.json({ error: '角色名称不能为空' }, { status: 400 })
    }

    const { data, error } = await supabaseAdmin
      .from('characters')
      .insert({
        user_id: username,
        name,
        description: description || '',
        voice_style: voice_style || '青年女声',
        appearance_tags: appearance_tags || [],
        feature_code: feature_code || '',
        front_view_url: '',
        side_view_url: '',
        three_quarter_view_url: ''
      })
      .select()
      .single()

    if (error) {
      console.error('创建角色失败:', error)
      return NextResponse.json({ error: '创建失败' }, { status: 500 })
    }

    return NextResponse.json({ success: true, character: data })
  } catch (err) {
    console.error('创建角色失败:', err)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}
