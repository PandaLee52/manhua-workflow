/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 允许API路由写入文件
  serverRuntimeConfig: {
    PROJECT_ROOT: __dirname
  }
}

module.exports = nextConfig
