/**
 * BGM搜索API示例
 * 访问: /api/bgm/search
 * 
 * 注意：这是简化版本，实际BGM搜索应调用后端API
 */

// 模拟BGM数据库
const BGM_DATABASE = [
  { id: "bgm_001", name: "Epic Adventure", artist: "Composer A", duration: 180, mood: "震撼", tags: ["epic", "dramatic"] },
  { id: "bgm_002", name: "Calm Morning", artist: "Composer B", duration: 240, mood: "平静", tags: ["calm", "peaceful"] },
  { id: "bgm_003", name: "Action Rush", artist: "Composer C", duration: 150, mood: "紧张", tags: ["action", "intense"] },
  { id: "bgm_004", name: "Romantic Sunset", artist: "Composer D", duration: 200, mood: "浪漫", tags: ["romantic", "soft"] },
  { id: "bgm_005", name: "Dark Mystery", artist: "Composer E", duration: 180, mood: "悬疑", tags: ["mystery", "dark"] },
];

export default async function handler(req, res) {
  // 只允许POST请求
  if (req.method !== 'POST') {
    return res.status(405).json({ 
      success: false, 
      error: '只支持POST请求' 
    });
  }

  try {
    const { tags = [], emotion, limit = 10 } = req.body;
    
    let results = [...BGM_DATABASE];
    
    // 按情绪过滤
    if (emotion) {
      results = results.filter(bgm => 
        bgm.mood.includes(emotion) || 
        bgm.tags.some(tag => tag.includes(emotion.toLowerCase()))
      );
    }
    
    // 按标签过滤
    if (tags.length > 0) {
      results = results.filter(bgm =>
        tags.some(tag => bgm.tags.includes(tag.toLowerCase()))
      );
    }
    
    // 返回结果
    res.status(200).json({
      success: true,
      data: {
        count: results.length,
        results: results.slice(0, limit)
      }
    });
    
  } catch (error) {
    res.status(500).json({
      success: false,
      error: '服务器错误: ' + error.message
    });
  }
}
