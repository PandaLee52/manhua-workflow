import { NextResponse } from 'next/server'

// 使用 PostgreSQL 连接池来执行 SQL
export async function GET() {
  const connectionString = process.env.DATABASE_URL || 
    'postgresql://postgres:LqmandPanda0324@db.wclohnrhypczeckgkqbx.supabase.co:5432/postgres'
  
  try {
    // 动态导入 pg
    const { Pool } = await import('pg')
    const pool = new Pool({ connectionString, ssl: { rejectUnauthorized: false } })
    
    const client = await pool.connect()
    
    await client.query(`
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
      CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
    `)
    
    const result = await client.query("SELECT table_name FROM information_schema.tables WHERE table_name = 'characters'")
    
    client.release()
    await pool.end()
    
    return NextResponse.json({ 
      success: true, 
      message: 'characters 表创建成功',
      table: result.rows[0]
    })
    
  } catch (error: any) {
    return NextResponse.json({ 
      success: false, 
      error: error.message 
    }, { status: 500 })
  }
}
