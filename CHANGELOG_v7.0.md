# AI漫剧工作流平台 v7.0 更新说明

## P0-1: 剧本格式标准化输出

### 功能实现
1. **场景头部格式标准化**
   - 支持格式：`场景序号-序号 时段 内/外 地点`
   - 示例：`1-1 日 外 校门口`

2. **符号规范自动识别**
   - `△` = 动作描述（Action）
   - `OS` = 内心独白（Over Shoulder）
   - `VO` = 画外音（Voice Over）
   - 旁白自动归类为 VO

3. **台词格式标准化**
   - 基础格式：`角色名：台词`
   - 带情绪：`角色名（情绪）：台词`
   - 带动作：`角色名（情绪 动作）：台词`

4. **导出功能**
   - 新增"导出标准化剧本"按钮
   - 一键下载标准化格式 .txt 文件

### 代码改动
- `parseScenesV2()` 函数增强
- 新增 `parseSceneHeader()` 函数
- 新增 `generateStandardFormat()` 函数
- 新增 `exportStandardFormat()` 导出函数

---

## P0-2: 角色资产库系统

### 功能实现
1. **角色管理 CRUD**
   - 创建角色
   - 编辑角色
   - 删除角色
   - 列表展示

2. **角色三视图管理**
   - 正脸视图
   - 侧脸视图
   - 3/4侧脸视图
   - 图片上传区域（UI预留）

3. **角色特征码**
   - 自动生成特征码
   - 格式：`char:角色名,tags:标签,salt:随机值`
   - 用于 AI 生图角色一致性

4. **音色绑定**
   - 支持选择音色风格
   - 少女音/青年女声/中年女声/老年女声
   - 少年音/青年男声/中年男声/老年男声

### API 路由
- `GET /api/characters` - 获取角色列表
- `POST /api/characters` - 创建角色
- `PUT /api/characters/[id]` - 更新角色
- `DELETE /api/characters/[id]` - 删除角色

### 数据库扩展
```sql
CREATE TABLE characters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  voice_style TEXT DEFAULT '青年女声',
  appearance_tags TEXT[] DEFAULT '{}',
  front_view_url TEXT DEFAULT '',
  side_view_url TEXT DEFAULT '',
  three_quarter_view_url TEXT DEFAULT '',
  feature_code TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 数据库更新

### 需要在 Supabase SQL Editor 执行

复制 `supabase-init.sql` 内容到 Supabase SQL Editor 执行。

如已有 `characters` 表，请执行增量更新：
```sql
-- 添加索引
CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
CREATE INDEX IF NOT EXISTS idx_characters_created_at ON characters(created_at DESC);

-- 启用 RLS
ALTER TABLE characters ENABLE ROW LEVEL SECURITY;

-- 创建策略
CREATE POLICY "Users can view own characters" ON characters FOR SELECT USING (user_id = current_user);
CREATE POLICY "Users can insert own characters" ON characters FOR INSERT WITH CHECK (user_id = current_user);
CREATE POLICY "Users can update own characters" ON characters FOR UPDATE USING (user_id = current_user);
CREATE POLICY "Users can delete own characters" ON characters FOR DELETE USING (user_id = current_user);
```

---

## UI 变更

### 新增 Tab
- **角色资产库** - 第四个主 Tab

### 角色卡片组件
- 三视图展示网格
- 特征码显示区
- 音色标签
- 外貌标签

### 模态框
- 新建角色弹窗
- 编辑角色弹窗
- 表单验证

---

## 文件清单

| 文件路径 | 变更类型 | 说明 |
|---------|---------|------|
| `app/page.tsx` | 修改 | P0-1, P0-2 功能实现 |
| `app/globals.css` | 修改 | 角色资产库样式 |
| `app/api/characters/route.ts` | 新增 | 角色 CRUD API |
| `app/api/characters/[id]/route.ts` | 新增 | 单个角色编辑/删除 |
| `supabase-init.sql` | 修改 | 添加 characters 表 |
| `package.json` | 修改 | 版本号更新至 7.0.0 |

---

## 部署说明

1. 代码推送到 GitHub 后，Vercel 会自动部署
2. 部署完成后需更新 Supabase 数据库
3. 访问 https://manhua-workflow-full.vercel.app 验证功能
