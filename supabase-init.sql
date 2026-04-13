-- AI漫剧工作流平台数据库初始化脚本 v7.0
-- 在Supabase SQL Editor中执行此脚本

-- 1. 创建用户表
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(64) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 创建项目表
CREATE TABLE IF NOT EXISTS projects (
  id VARCHAR(32) PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  data JSONB NOT NULL,
  username VARCHAR(50) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. P0-2: 创建角色表
CREATE TABLE IF NOT EXISTS characters (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  voice_style TEXT DEFAULT '青年女声',
  appearance_tags TEXT[] DEFAULT '{}',
  front_view_url TEXT DEFAULT '',
  side_view_url TEXT DEFAULT '',
  three_quarter_view_url TEXT DEFAULT '',
  feature_code TEXT DEFAULT '',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_username ON projects(username);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
CREATE INDEX IF NOT EXISTS idx_characters_created_at ON characters(created_at DESC);

-- 5. 插入预设用户账号
-- 用户名: lqmandme
-- 密码: PhosphoR
-- SHA256哈希: 7d7a16b9f8c9aa3e29407ac380cf6b6d463dc7647f499be20b719d179ac048de
INSERT INTO users (username, password_hash, created_at)
VALUES (
  'lqmandme',
  '7d7a16b9f8c9aa3e29407ac380cf6b6d463dc7647f499be20b719d179ac048de',
  NOW()
)
ON CONFLICT (username) DO NOTHING;

-- 6. 启用RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE characters ENABLE ROW LEVEL SECURITY;

-- 7. 创建RLS策略

-- 用户只能查看自己的数据
CREATE POLICY "Users can view own data" ON users
  FOR SELECT USING (username = current_user);

-- 项目：允许所有认证用户访问自己的项目
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT USING (username = current_user);

CREATE POLICY "Users can insert own projects" ON projects
  FOR INSERT WITH CHECK (username = current_user);

CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE USING (username = current_user);

CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE USING (username = current_user);

-- 角色：允许用户管理自己的角色
CREATE POLICY "Users can view own characters" ON characters
  FOR SELECT USING (user_id = current_user);

CREATE POLICY "Users can insert own characters" ON characters
  FOR INSERT WITH CHECK (user_id = current_user);

CREATE POLICY "Users can update own characters" ON characters
  FOR UPDATE USING (user_id = current_user);

CREATE POLICY "Users can delete own characters" ON characters
  FOR DELETE USING (user_id = current_user);

-- 8. 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 以下是针对已有数据库的增量更新脚本（如果上面的完整脚本执行失败）
-- 如果角色表已存在，请单独执行以下语句
-- ============================================================

-- 添加角色表（如果不存在）
-- DO $$
-- BEGIN
--   IF NOT EXISTS (SELECT FROM pg_table WHERE tablename = 'characters') THEN
--     CREATE TABLE characters (
--       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--       user_id TEXT NOT NULL,
--       name TEXT NOT NULL,
--       description TEXT DEFAULT '',
--       voice_style TEXT DEFAULT '青年女声',
--       appearance_tags TEXT[] DEFAULT '{}',
--       front_view_url TEXT DEFAULT '',
--       side_view_url TEXT DEFAULT '',
--       three_quarter_view_url TEXT DEFAULT '',
--       feature_code TEXT DEFAULT '',
--       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
--     );
--   END IF;
-- END $$;

-- 为角色表创建索引（如果不存在）
-- CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
-- CREATE INDEX IF NOT EXISTS idx_characters_created_at ON characters(created_at DESC);

-- 为角色表启用RLS（如果未启用）
-- ALTER TABLE characters ENABLE ROW LEVEL SECURITY;

-- 为角色表创建RLS策略（如果不存在）
-- CREATE POLICY "Users can view own characters" ON characters
--   FOR SELECT USING (user_id = current_user);
-- CREATE POLICY "Users can insert own characters" ON characters
--   FOR INSERT WITH CHECK (user_id = current_user);
-- CREATE POLICY "Users can update own characters" ON characters
--   FOR UPDATE USING (user_id = current_user);
-- CREATE POLICY "Users can delete own characters" ON characters
--   FOR DELETE USING (user_id = current_user);
