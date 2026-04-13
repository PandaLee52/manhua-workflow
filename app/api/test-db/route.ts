import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function GET() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  
  if (!url || !serviceKey) {
    return NextResponse.json({ error: '环境变量未配置' })
  }
  
  try {
    const supabase = createClient(url, serviceKey)
    
    // 测试查询 users 表
    const { data, error, count } = await supabase
      .from('users')
      .select('*', { count: 'exact' })
    
    if (error) {
      return NextResponse.json({
        error: '查询失败',
        details: error.message,
        code: error.code
      })
    }
    
    return NextResponse.json({
      success: true,
      userCount: count,
      users: data?.map(u => ({ username: u.username, created_at: u.created_at }))
    })
  } catch (err: any) {
    return NextResponse.json({
      error: '异常',
      message: err.message
    })
  }
}
