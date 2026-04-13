# 🚀 AI漫剧工作流平台 - 快速部署指南

## 第一步：注册Supabase（5分钟）

### 1. 访问并注册
- 网址：https://supabase.com
- 点击 "Start your project"
- 使用GitHub登录（推荐）或邮箱注册

### 2. 创建组织
- Organization name: `manhua-workflow`
- 点击 "Create organization"

### 3. 创建项目
- Project name: `manhua-workflow`
- Database password: 自己设置并记住
- Region: **Northeast Asia (Tokyo)**
- 点击 "Create new project"
- 等待1-2分钟

### 4. 获取API密钥
创建完成后：
1. 点击左侧 **"Settings"**（齿轮图标）
2. 点击 **"API"**
3. 复制以下内容：
   - **Project URL**：类似 `https://xxxxxxxx.supabase.co`
   - **anon public**：一长串以 `eyJ` 开头的字符串
   - **service_role**：点击 "Reveal" 显示，复制这个密钥

### 5. 初始化数据库
1. 点击左侧 **"SQL Editor"**
2. 点击 **"New query"**
3. 复制 `supabase-init.sql` 文件的全部内容
4. 粘贴到编辑器
5. 点击 **"Run"** 执行
6. 看到 "Success. No rows returned" 表示成功

---

## 第二步：推送代码到GitHub（3分钟）

### 方式A：使用GitHub网页版（推荐）

1. 访问 https://github.com/new
2. Repository name: `manhua-workflow`
3. 选择 **Private**（私有）或 Public
4. 点击 **"Create repository"**
5. 点击 **"uploading an existing file"**
6. 拖拽 `manhua-workflow-full` 文件夹内的所有文件
7. 点击 **"Commit changes"**

### 方式B：使用命令行

```bash
cd manhua-workflow-full

# 初始化Git
git init
git add .
git commit -m "AI漫剧工作流平台v4.0 - 支持永久保存"

# 推送到GitHub（先在GitHub创建仓库）
git remote add origin https://github.com/YOUR_USERNAME/manhua-workflow.git
git branch -M main
git push -u origin main
```

---

## 第三步：部署到Vercel（2分钟）

### 1. 登录Vercel
- 网址：https://vercel.com
- 使用GitHub登录

### 2. 导入项目
1. 点击 **"Add New" → "Project"**
2. 选择你的GitHub仓库 `manhua-workflow`
3. 点击 **"Import"**

### 3. 配置环境变量（重要！）
在部署前，先配置环境变量：

1. 展开 **"Environment Variables"**
2. 添加以下3个变量：

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | 你的Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | 你的anon public key |
| `SUPABASE_SERVICE_ROLE_KEY` | 你的service_role key |

3. 点击 **"Add"** 确认每个变量

### 4. 开始部署
1. 点击 **"Deploy"**
2. 等待2-3分钟
3. 看到庆祝动画表示部署成功

### 5. 访问应用
- Vercel会提供一个地址：`https://manhua-workflow.vercel.app`
- 点击 **"Visit"** 访问

---

## 第四步：测试使用

### 1. 登录你的账号
- 用户名：`lqmandme`
- 密码：`PhosphoR`

### 2. 上传测试剧本
- 准备一个 .txt 或 .md 格式的剧本文件
- 拖拽或点击上传
- 系统会自动解析并保存

### 3. 验证数据持久化
- 上传剧本后，刷新页面
- 数据应该仍然存在
- 点击"我的项目"查看历史

### 4. 邀请团队成员
- 把Vercel地址分享给团队成员
- 他们可以注册自己的账号
- 每个人只能看到自己的项目

---

## ⚠️ 常见问题

### Q1：数据库初始化失败
**解决**：
- 确保复制了完整的SQL内容
- 检查是否有语法错误
- 尝试分段执行SQL语句

### Q2：环境变量配置错误
**解决**：
- 确认3个变量都已添加
- 检查变量名是否完全正确（区分大小写）
- 重新部署项目：Settings → Deployments → Redeploy

### Q3：登录失败
**解决**：
- 确认SQL初始化成功
- 检查密码是否正确（PhosphoR）
- 清除浏览器缓存重试

### Q4：数据没有保存
**解决**：
- 检查Vercel环境变量配置
- 查看Vercel部署日志是否有错误
- 确认Supabase服务正常运行

---

## 📊 数据库结构

### users表（用户）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 用户ID |
| username | VARCHAR(50) | 用户名（唯一） |
| password_hash | VARCHAR(64) | SHA256密码哈希 |
| created_at | TIMESTAMP | 创建时间 |

### projects表（项目）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(32) | 项目ID |
| title | VARCHAR(200) | 项目标题 |
| data | JSONB | 剧本数据 |
| username | VARCHAR(50) | 所属用户 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

## 🎯 成功标志

✅ Supabase项目创建成功
✅ 数据库表初始化成功
✅ GitHub仓库创建成功
✅ Vercel环境变量配置成功
✅ 部署成功并获得访问地址
✅ 能够登录 lqmandme 账号
✅ 上传剧本后刷新数据仍存在

---

## 📞 需要帮助？

如果在任何步骤遇到问题：
1. 检查上述常见问题
2. 查看Vercel部署日志
3. 查看Supabase日志
4. 把错误信息发给我

---

**预计总时间**：10-15分钟
**总成本**：$0（完全免费）
**支持用户**：5人团队无压力

祝你部署顺利！🎉
