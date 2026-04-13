import './globals.css'

export const metadata = {
  title: 'AI漫剧工作流平台',
  description: '智能剧本解析 · 核心资产提取 · 生图提示词生成',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}
