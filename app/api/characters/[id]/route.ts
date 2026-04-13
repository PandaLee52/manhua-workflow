import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin, isSupabaseConfigured } from '../../../../lib/supabase'

// 更新单个角色
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
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
    const { id } = params
    const body = await request.json()

    // 验证角色所属用户
    const { data: existing } = await supabaseAdmin
      .from('characters')
      .select('user_id')
      .eq('id', id)
      .single()

    if (!existing) {
      return NextResponse.json({ error: '角色不存在' }, { status: 404 })
    }

    if (existing.user_id !== username) {
      return NextResponse.json({ error: '无权限修改此角色' }, { status: 403 })
    }

    const { 
      name, description, voice_style, appearance_tags, 
      front_view_url, side_view_url, three_quarter_view_url, 
      feature_code 
    } = body

    const { data, error } = await supabaseAdmin
      .from('characters')
      .update({
        name: name || undefined,
        description: description || '',
        voice_style: voice_style || undefined,
        appearance_tags: appearance_tags || [],
        front_view_url: front_view_url || '',
        side_view_url: side_view_url || '',
        three_quarter_view_url: three_quarter_view_url || '',
        feature_code: feature_code || ''
      })
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error('更新角色失败:', error)
      return NextResponse.json({ error: '更新失败' }, { status: 500 })
    }

    return NextResponse.json({ success: true, character: data })
  } catch (err) {
    console.error('更新角色失败:', err)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}

// 删除单个角色
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
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
    const { id } = params

    // 验证角色所属用户
    const { data: existing } = await supabaseAdmin
      .from('characters')
      .select('user_id')
      .eq('id', id)
      .single()

    if (!existing) {
      return NextResponse.json({ error: '角色不存在' }, { status: 404 })
    }

    if (existing.user_id !== username) {
      return NextResponse.json({ error: '无权限删除此角色' }, { status: 403 })
    }

    const { error } = await supabaseAdmin
      .from('characters')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('删除角色失败:', error)
      return NextResponse.json({ error: '删除失败' }, { status: 500 })
    }

    return NextResponse.json({ success: true })
  } catch (err) {
    console.error('删除角色失败:', err)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}
