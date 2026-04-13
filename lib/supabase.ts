import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

// 创建一个空的 mock 客户端用于开发环境
const createMockClient = (): SupabaseClient => {
  return createClient('https://placeholder.supabase.co', 'placeholder-key')
}

// 如果缺少环境变量，使用 mock 客户端
export const supabase = (supabaseUrl && supabaseAnonKey)
  ? createClient(supabaseUrl, supabaseAnonKey)
  : createMockClient()

// 服务端使用的客户端（使用service_role_key）
export const supabaseAdmin = (supabaseUrl && supabaseAnonKey)
  ? createClient(supabaseUrl, process.env.SUPABASE_SERVICE_ROLE_KEY || supabaseAnonKey)
  : createMockClient()

// 检查是否配置了 Supabase
export const isSupabaseConfigured = !!(supabaseUrl && supabaseAnonKey)
