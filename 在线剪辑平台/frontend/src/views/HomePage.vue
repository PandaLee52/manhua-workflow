<template>
  <div class="home-page">
    <!-- 导航栏 -->
    <header class="navbar glass-effect">
      <div class="navbar-content">
        <div class="logo">
          <el-icon :size="32" color="#409EFF"><VideoPlay /></el-icon>
          <span class="logo-text">AI智能剪辑</span>
        </div>
        <nav class="nav-links">
          <a href="#features" class="nav-link">功能特点</a>
          <a href="#workflow" class="nav-link">工作流程</a>
          <a href="#pricing" class="nav-link">价格方案</a>
        </nav>
        <el-button type="primary" @click="$router.push('/upload')">
          立即开始
        </el-button>
      </div>
    </header>

    <!-- 英雄区域 -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-badge">
          <el-icon><Lightning /></el-icon>
          <span>新一代AI剪辑体验</span>
        </div>
        <h1 class="hero-title">
          <span class="gradient-text">智能剪辑</span>
          <br />让视频创作更简单
        </h1>
        <p class="hero-desc">
          告别繁琐的剪辑流程，AI智能分析剧本，自动匹配素材，<br class="hide-mobile" />
          一键生成专业级视频作品
        </p>
        <div class="hero-actions">
          <button class="gradient-btn primary-btn" @click="$router.push('/upload')">
            <el-icon><Upload /></el-icon>
            上传素材开始
          </button>
          <button class="secondary-btn">
            <el-icon><VideoCamera /></el-icon>
            查看演示
          </button>
        </div>
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-number">10万+</span>
            <span class="stat-label">用户信赖</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">5分钟</span>
            <span class="stat-label">平均出片时间</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">99.9%</span>
            <span class="stat-label">服务稳定性</span>
          </div>
        </div>
      </div>
      <div class="hero-visual">
        <div class="preview-window">
          <div class="window-header">
            <div class="window-dot red"></div>
            <div class="window-dot yellow"></div>
            <div class="window-dot green"></div>
            <span class="window-title">视频预览</span>
          </div>
          <div class="window-content">
            <div class="video-timeline">
              <div class="timeline-track">
                <div class="timeline-clip" style="width: 25%; background: #667eea;"></div>
                <div class="timeline-clip" style="width: 30%; background: #764ba2;"></div>
                <div class="timeline-clip" style="width: 20%; background: #f093fb;"></div>
                <div class="timeline-clip" style="width: 25%; background: #4facfe;"></div>
              </div>
            </div>
            <div class="video-controls">
              <el-icon :size="20"><VideoPlay /></el-icon>
              <div class="progress-bar">
                <div class="progress-fill"></div>
              </div>
              <span class="time-display">02:34 / 05:12</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特点 -->
    <section id="features" class="features-section">
      <div class="section-header">
        <h2 class="section-title">为什么选择我们</h2>
        <p class="section-desc">强大的AI能力，让视频剪辑变得前所未有的简单</p>
      </div>
      <div class="features-grid">
        <div class="feature-card custom-card">
          <div class="feature-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <el-icon :size="32"><MagicStick /></el-icon>
          </div>
          <h3>AI智能剪辑</h3>
          <p>基于深度学习算法，智能分析剧本内容，自动匹配合适的镜头和节奏</p>
        </div>
        <div class="feature-card custom-card">
          <div class="feature-icon" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <el-icon :size="32"><Timer /></el-icon>
          </div>
          <h3>极速处理</h3>
          <p>云端GPU加速渲染，5分钟即可完成一部高质量短片的制作</p>
        </div>
        <div class="feature-card custom-card">
          <div class="feature-icon" style="background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);">
            <el-icon :size="32"><Music /></el-icon>
          </div>
          <h3>海量BGM库</h3>
          <p>内置10万+正版背景音乐，智能节奏匹配，让视频更具感染力</p>
        </div>
        <div class="feature-card custom-card">
          <div class="feature-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <el-icon :size="32"><ChatDotRound /></el-icon>
          </div>
          <h3>智能字幕</h3>
          <p>AI自动识别语音生成字幕，支持多种样式定制，一键添加</p>
        </div>
        <div class="feature-card custom-card">
          <div class="feature-icon" style="background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);">
            <el-icon :size="32"><Crop /></el-icon>
          </div>
          <h3>多格式导出</h3>
          <p>支持多种分辨率和格式导出，满足抖音、快手、B站等平台需求</p>
        </div>
        <div class="feature-card custom-card">
          <div class="feature-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <el-icon :size="32"><CloudUpload /></el-icon>
          </div>
          <h3>云端存储</h3>
          <p>所有项目云端保存，随时随地访问，再也不用担心文件丢失</p>
        </div>
      </div>
    </section>

    <!-- 工作流程 -->
    <section id="workflow" class="workflow-section">
      <div class="section-header">
        <h2 class="section-title">简单四步，创作精彩</h2>
        <p class="section-desc">清晰的创作流程，让每一步都轻松上手</p>
      </div>
      <div class="workflow-steps">
        <div class="workflow-step">
          <div class="step-number">01</div>
          <div class="step-content">
            <div class="step-icon">
              <el-icon :size="36"><Upload /></el-icon>
            </div>
            <h3>上传素材</h3>
            <p>上传视频片段和分镜剧本，支持批量上传和拖拽排序</p>
          </div>
        </div>
        <div class="step-connector">
          <div class="connector-line"></div>
          <el-icon><ArrowRight /></el-icon>
        </div>
        <div class="workflow-step">
          <div class="step-number">02</div>
          <div class="step-content">
            <div class="step-icon">
              <el-icon :size="36"><Edit /></el-icon>
            </div>
            <h3>编辑配置</h3>
            <p>选择背景音乐、设置字幕样式、调整输出参数</p>
          </div>
        </div>
        <div class="step-connector">
          <div class="connector-line"></div>
          <el-icon><ArrowRight /></el-icon>
        </div>
        <div class="workflow-step">
          <div class="step-number">03</div>
          <div class="step-content">
            <div class="step-icon">
              <el-icon :size="36"><Cpu /></el-icon>
            </div>
            <h3>AI处理</h3>
            <p>智能分析、自动剪辑、实时预览处理进度</p>
          </div>
        </div>
        <div class="step-connector">
          <div class="connector-line"></div>
          <el-icon><ArrowRight /></el-icon>
        </div>
        <div class="workflow-step">
          <div class="step-number">04</div>
          <div class="step-content">
            <div class="step-icon">
              <el-icon :size="36"><Download /></el-icon>
            </div>
            <h3>下载成品</h3>
            <p>一键下载高清视频，支持多平台尺寸导出</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 价格方案 -->
    <section id="pricing" class="pricing-section">
      <div class="section-header">
        <h2 class="section-title">灵活的价格方案</h2>
        <p class="section-desc">选择最适合您的方案，开始您的创作之旅</p>
      </div>
      <div class="pricing-grid">
        <div class="pricing-card custom-card">
          <div class="pricing-header">
            <h3>免费版</h3>
            <div class="price">
              <span class="currency">¥</span>
              <span class="amount">0</span>
              <span class="period">/月</span>
            </div>
          </div>
          <ul class="pricing-features">
            <li><el-icon color="#67C23A"><Check /></el-icon> 每月5次剪辑</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 720p视频输出</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 基础BGM库</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 1GB云存储</li>
            <li class="disabled"><el-icon color="#909399"><Close /></el-icon> 高级特效</li>
            <li class="disabled"><el-icon color="#909399"><Close /></el-icon> 优先处理</li>
          </ul>
          <el-button class="pricing-btn">立即试用</el-button>
        </div>
        <div class="pricing-card custom-card popular">
          <div class="popular-tag">最受欢迎</div>
          <div class="pricing-header">
            <h3>专业版</h3>
            <div class="price">
              <span class="currency">¥</span>
              <span class="amount">99</span>
              <span class="period">/月</span>
            </div>
          </div>
          <ul class="pricing-features">
            <li><el-icon color="#67C23A"><Check /></el-icon> 无限次剪辑</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 4K视频输出</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 全BGM库</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 50GB云存储</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 高级特效</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 优先处理</li>
          </ul>
          <el-button type="primary" class="pricing-btn">立即开通</el-button>
        </div>
        <div class="pricing-card custom-card">
          <div class="pricing-header">
            <h3>企业版</h3>
            <div class="price">
              <span class="currency">¥</span>
              <span class="amount">399</span>
              <span class="period">/月</span>
            </div>
          </div>
          <ul class="pricing-features">
            <li><el-icon color="#67C23A"><Check /></el-icon> 无限次剪辑</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 8K视频输出</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 全BGM库</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 无限云存储</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> API接口调用</li>
            <li><el-icon color="#67C23A"><Check /></el-icon> 专属客服</li>
          </ul>
          <el-button class="pricing-btn">联系销售</el-button>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-brand">
          <div class="logo">
            <el-icon :size="28" color="#409EFF"><VideoPlay /></el-icon>
            <span class="logo-text">AI智能剪辑</span>
          </div>
          <p>让视频创作更简单</p>
        </div>
        <div class="footer-links">
          <div class="link-group">
            <h4>产品</h4>
            <a href="#">功能介绍</a>
            <a href="#">最新更新</a>
            <a href="#">使用教程</a>
          </div>
          <div class="link-group">
            <h4>支持</h4>
            <a href="#">帮助中心</a>
            <a href="#">常见问题</a>
            <a href="#">联系客服</a>
          </div>
          <div class="link-group">
            <h4>合作</h4>
            <a href="#">企业服务</a>
            <a href="#">API接口</a>
            <a href="#">合作伙伴</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2024 AI智能剪辑平台 版权所有</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

// 导航栏
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 0 40px;
  
  .navbar-content {
    max-width: 1400px;
    margin: 0 auto;
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .logo-text {
      font-size: 20px;
      font-weight: 600;
      color: #fff;
    }
  }
  
  .nav-links {
    display: flex;
    gap: 40px;
    
    .nav-link {
      color: #b0b0b0;
      text-decoration: none;
      font-size: 15px;
      transition: color 0.3s;
      
      &:hover {
        color: #409EFF;
      }
    }
  }
}

// 英雄区域
.hero {
  padding: 160px 40px 100px;
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  align-items: center;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
    padding: 120px 20px 60px;
    gap: 60px;
  }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(64, 158, 255, 0.15);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 20px;
  color: #409EFF;
  font-size: 14px;
  margin-bottom: 24px;
}

.hero-title {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 24px;
  
  .gradient-text {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  @media (max-width: 768px) {
    font-size: 36px;
  }
}

.hero-desc {
  font-size: 18px;
  color: #b0b0b0;
  line-height: 1.8;
  margin-bottom: 40px;
  
  .hide-mobile {
    @media (max-width: 768px) {
      display: none;
    }
  }
  
  @media (max-width: 768px) {
    font-size: 16px;
  }
}

.hero-actions {
  display: flex;
  gap: 20px;
  margin-bottom: 60px;
  
  .primary-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    padding: 14px 32px;
  }
  
  .secondary-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 32px;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: #fff;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      border-color: #409EFF;
      background: rgba(64, 158, 255, 0.1);
    }
  }
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 40px;
  
  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .stat-number {
      font-size: 28px;
      font-weight: 700;
      color: #fff;
    }
    
    .stat-label {
      font-size: 14px;
      color: #b0b0b0;
    }
  }
  
  .stat-divider {
    width: 1px;
    height: 40px;
    background: rgba(255, 255, 255, 0.1);
  }
}

// 预览窗口
.hero-visual {
  @media (max-width: 1024px) {
    display: none;
  }
}

.preview-window {
  background: rgba(15, 52, 96, 0.6);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  .window-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: rgba(0, 0, 0, 0.3);
    
    .window-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      
      &.red { background: #ff5f57; }
      &.yellow { background: #febc2e; }
      &.green { background: #28c840; }
    }
    
    .window-title {
      margin-left: auto;
      font-size: 13px;
      color: #b0b0b0;
    }
  }
  
  .window-content {
    padding: 20px;
  }
}

.video-timeline {
  .timeline-track {
    height: 60px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    display: flex;
    overflow: hidden;
  }
  
  .timeline-clip {
    height: 100%;
    transition: all 0.3s;
    
    &:hover {
      filter: brightness(1.2);
    }
  }
}

.video-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  color: #fff;
  
  .progress-bar {
    flex: 1;
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    
    .progress-fill {
      width: 50%;
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      border-radius: 2px;
    }
  }
  
  .time-display {
    font-size: 13px;
    color: #b0b0b0;
    font-variant-numeric: tabular-nums;
  }
}

// 功能区域
.features-section {
  padding: 100px 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
  
  .section-title {
    font-size: 40px;
    font-weight: 700;
    margin-bottom: 16px;
    
    @media (max-width: 768px) {
      font-size: 28px;
    }
  }
  
  .section-desc {
    font-size: 18px;
    color: #b0b0b0;
  }
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
  
  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.feature-card {
  padding: 32px;
  
  .feature-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    margin-bottom: 20px;
  }
  
  h3 {
    font-size: 20px;
    margin-bottom: 12px;
  }
  
  p {
    font-size: 15px;
    color: #b0b0b0;
    line-height: 1.7;
  }
}

// 工作流程
.workflow-section {
  padding: 100px 40px;
  background: rgba(15, 52, 96, 0.3);
}

.workflow-steps {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 20px;
  
  @media (max-width: 1024px) {
    flex-wrap: wrap;
    gap: 40px;
  }
}

.workflow-step {
  flex: 1;
  max-width: 220px;
  text-align: center;
  
  .step-number {
    font-size: 48px;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
  }
  
  .step-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 16px;
    background: rgba(64, 158, 255, 0.15);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #409EFF;
  }
  
  h3 {
    font-size: 18px;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 14px;
    color: #b0b0b0;
    line-height: 1.6;
  }
}

.step-connector {
  display: flex;
  align-items: center;
  padding-top: 60px;
  color: rgba(255, 255, 255, 0.2);
  
  .connector-line {
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  }
  
  @media (max-width: 1024px) {
    display: none;
  }
}

// 价格方案
.pricing-section {
  padding: 100px 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
  max-width: 1100px;
  margin: 0 auto;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
    max-width: 400px;
  }
}

.pricing-card {
  padding: 40px;
  position: relative;
  
  &.popular {
    border: 2px solid #409EFF;
    transform: scale(1.05);
    
    @media (max-width: 1024px) {
      transform: none;
    }
  }
  
  .popular-tag {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 6px 20px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
  }
  
  .pricing-header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 30px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    h3 {
      font-size: 20px;
      margin-bottom: 16px;
    }
    
    .price {
      .currency {
        font-size: 20px;
        vertical-align: top;
      }
      
      .amount {
        font-size: 48px;
        font-weight: 700;
      }
      
      .period {
        font-size: 14px;
        color: #b0b0b0;
      }
    }
  }
  
  .pricing-features {
    list-style: none;
    padding: 0;
    margin: 0 0 30px;
    
    li {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 0;
      font-size: 15px;
      
      &.disabled {
        color: #666;
      }
    }
  }
  
  .pricing-btn {
    width: 100%;
    height: 48px;
    font-size: 16px;
  }
}

// 页脚
.footer {
  background: rgba(0, 0, 0, 0.3);
  padding: 60px 40px 30px;
  
  .footer-content {
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 60px;
    
    @media (max-width: 768px) {
      grid-template-columns: 1fr;
      gap: 40px;
    }
  }
  
  .footer-brand {
    .logo {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
      
      .logo-text {
        font-size: 18px;
        font-weight: 600;
        color: #fff;
      }
    }
    
    p {
      color: #666;
      font-size: 14px;
    }
  }
  
  .footer-links {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 40px;
    
    @media (max-width: 640px) {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .link-group {
      h4 {
        font-size: 16px;
        margin-bottom: 16px;
      }
      
      a {
        display: block;
        color: #888;
        text-decoration: none;
        font-size: 14px;
        padding: 6px 0;
        transition: color 0.3s;
        
        &:hover {
          color: #409EFF;
        }
      }
    }
  }
  
  .footer-bottom {
    max-width: 1200px;
    margin: 40px auto 0;
    padding-top: 30px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    
    p {
      color: #666;
      font-size: 14px;
    }
  }
}
</style>
