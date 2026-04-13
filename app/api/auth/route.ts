import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '../../../lib/supabase'
import crypto from 'crypto'

interface User {
  id: string
  username: string
  password_hash: string
  created_at: string
}

function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password).digest('hex')
}

function generateToken(username: string): string {
  const timestamp = Date.now()
  const random = crypto.randomBytes(16).toString('hex')
  return `${username}:${timestamp}:${random}`
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, username, password } = body

    if (!username || !password) {
      return NextResponse.json({ error: '用户名和密码不能为空' }, { status: 400 })
    }

    if (username.length < 3 || password.length < 6) {
      return NextResponse.json({ error: '用户名至少3位，密码至少6位' }, { status: 400 })
    }

    if (action === 'register') {
      // 检查用户是否存在
      const { data: existingUser, error: checkError } = await supabaseAdmin
        .from('users')
        .select('username')
        .eq('username', username)
        .single()

      if (existingUser) {
        return NextResponse.json({ error: '用户名已存在' }, { status: 400 })
      }

      // 创建新用户
      const { data: newUser, error: insertError } = await supabaseAdmin
        .from('users')
        .insert({
          username,
          password_hash: hashPassword(password),
          created_at: new Date().toISOString()
        })
        .select()
        .single()

      if (insertError) {
        console.error('Insert error:', insertError)
        return NextResponse.json({ error: '注册失败，请重试' }, { status: 500 })
      }

      const token = generateToken(username)
      
      return NextResponse.json({
        token,
        user: { username, createdAt: newUser.created_at }
      })
    }

    if (action === 'login') {
      // 查找用户
      const { data: user, error: findError } = await supabaseAdmin
        .from('users')
        .select('*')
        .eq('username', username)
        .single()

      if (!user || user.password_hash !== hashPassword(password)) {
        return NextResponse.json({ error: '用户名或密码错误' }, { status: 401 })
      }

      const token = generateToken(username)
      return NextResponse.json({
        token,
        user: { username, createdAt: user.created_at }
      })
    }

    return NextResponse.json({ error: '无效的操作' }, { status: 400 })
  } catch (error) {
    console.error('Auth error:', error)
    return NextResponse.json({ error: '服务器错误' }, { status: 500 })
  }
}
