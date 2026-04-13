# AI漫剧工作流平台v4.0 - 部署指南

## 方案B：Vercel + 文件存储（推荐，0成本）

### 前提条件
- Vercel账号（免费）
- Git账号（GitHub/GitLab/Bitbucket）

### 部署步骤

#### 1. 推送代码到GitHub
```bash
cd manhua-workflow-full
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/manhua-workflow.git
git push -u origin main
```

#### 2. 在Vercel导入项目
1. 访问 https://vercel.com
2. 点击 "Add New" → "Project"
3. 选择GitHub仓库（需要授权）
4. 点击 "Import"

#### 3. 配置环境变量（无需配置）
当前版本使用文件系统存储，不需要环境变量

#### 4. 部署
点击 "Deploy" 按钮，等待部署完成（约2-3分钟）

#### 5. 获取访问地址
部署成功后，Vercel会提供一个类似以下的地址：
```
https://manhua-workflow-full.vercel.app
```

### ⚠️ 重要提示

**关于数据持久化**：
- 当前方案使用Vercel的Serverless Functions和文件系统存储
- **限制**：Vercel的Serverless环境是临时的，每次重新部署时data/目录会被清空
- **解决方案**：建议升级到Vercel Pro版（$20/月）并使用Vercel Postgres或连接外部数据库

**免费替代方案（数据会丢失）**：
- 适合测试和演示
- 数据仅在部署期间有效
- 重新部署后数据会重置

---

## 方案C：Vercel + Supabase（推荐生产环境，0成本但有限额）

### 优势
- Supabase提供免费数据库（500MB）
- 用户数据永久保存
- 支持多用户并发

### 需要修改的文件

#### 1. 安装依赖
```bash
npm install @supabase/supabase-js
```

#### 2. 创建环境变量
在Vercel项目设置中添加以下环境变量：
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
```

#### 3. 修改API路由
替换 `app/api/auth/route.ts`、`app/api/save/route.ts`、`app/api/projects/route.ts` 中的文件存储逻辑，使用Supabase客户端。

**示例代码**（app/api/auth/route.ts）：
```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// 替换文件读写为Supabase查询
// getUsers() → supabase.from('users').select('*')
// saveUsers() → supabase.from('users').upsert(data)
```

---

## 方案D：Coze Code（当前测试中）

### 问题
- 部署时提示 ".coze file not exist"
- 需要特定配置格式

### 当前状态
- ✅ 项目创建成功（ID: 7628072088519114788）
- ❌ 部署失败
- 🔄 待解决：需要Coze团队提供正确的.coze文件格式

---

## 快速测试（本地运行）

### 1. 安装依赖
```bash
cd manhua-workflow-full
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```

### 3. 访问
打开浏览器访问 http://localhost:3000

### 4. 测试用户系统
- 注册账号（至少3位用户名，6位密码）
- 登录
- 上传剧本
- 查看保存的项目

---

## 使用说明

### 用户功能
1. **注册/登录**：创建账号，密码会加密存储
2. **上传剧本**：支持.txt和.md格式
3. **自动保存**：解析后的剧本会自动保存到账户
4. **查看历史**：在"我的项目"中查看所有项目
5. **加载项目**：点击历史项目加载数据
6. **核心资产**：查看角色、场景、道具及生图提示词

### 多用户支持
- 每个用户只能访问自己的项目
- 用户之间数据隔离
- 支持最多5人团队使用

---

## 数据结构

### 用户（users.json）
```json
{
  "username1": {
    "username": "username1",
    "passwordHash": "sha256加密后的密码",
    "createdAt": "2026-04-13T10:00:00.000Z"
  }
}
```

### 项目（projects.json）
```json
{
  "projectId1": {
    "id": "projectId1",
    "title": "剧本标题",
    "username": "username1",
    "data": { /* 解析后的完整数据 */ },
    "createdAt": "2026-04-13T10:00:00.000Z",
    "updatedAt": "2026-04-13T10:00:00.000Z"
  }
}
```

---

## 下一步优化

### 1. 数据持久化（优先级P0）
- 集成Supabase或其他免费数据库
- 确保数据永久保存

### 2. 权限管理（优先级P1）
- 支持团队共享项目
- 添加角色权限（管理员/编辑/查看）

### 3. 数据分析（优先级P2）
- 统计用户使用频率
- 分析常用剧本格式
- 提供优化建议

### 4. 导出功能（优先级P1）
- 导出项目为JSON
- 导出核心资产为Markdown
- 导出分镜脚本

---

## 成本估算

### Vercel（免费版）
- ✅ 无限带宽
- ✅ 100GB存储
- ✅ 100小时Serverless Functions/月
- ⚠️ 数据持久化限制

### Vercel Pro（$20/月）
- ✅ 持久化存储
- ✅ 1000小时Serverless Functions/月
- ✅ 团队协作功能

### Supabase（免费版）
- ✅ 500MB数据库
- ✅ 2GB存储
- ✅ 50,000次API调用/月
- ⚠️ 超出后按量计费

### 总成本（免费方案）
- Vercel免费版：$0
- Supabase免费版：$0
- 域名（可选）：$10-15/年（可选）

**结论**：免费方案足够支持5人团队使用

---

## 技术支持

如有问题，请检查：
1. Node.js版本 >= 18
2. npm版本 >= 9
3. 网络连接正常
4. Vercel/Supabase账号状态正常

---

*最后更新：2026-04-13*
*版本：v4.0*
