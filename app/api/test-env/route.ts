import { NextResponse } from 'next/server'

export async function GET() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  
  return NextResponse.json({
    url: url ? '已配置' : '未配置',
    urlValue: url ? url.substring(0, 30) + '...' : null,
    anonKey: anonKey ? '已配置 (长度: ' + anonKey.length + ')' : '未配置',
    serviceKey: serviceKey ? '已配置 (长度: ' + serviceKey.length + ')' : '未配置',
    isConfigured: !!(url && anonKey)
  })
}
