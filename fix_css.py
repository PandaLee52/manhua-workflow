# 读取文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 timeline-clip 和 playhead 样式
old_styles = """  .timeline-clip {
    position: absolute;
    top: 4px;
    height: calc(100% - 8px);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    
  }
  
  .playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ff4444;
    z-index: 10;
    pointer-events: none;
    
    &::before {
      content: '';
      position: absolute;
      top: -4px;
      left: -5px;
      width: 0;
      height: 0;
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 8px solid #ff4444;
    }
  }
    
    
    &:hover {
      filter: brightness(1.1);
      transform: scaleY(1.05);
    }
    
    .clip-content {
      padding: 4px 8px;
      height: 100%;
      display: flex;
      align-items: center;
      gap: 6px;
      overflow: hidden;
      
      .clip-name {
        font-size: 11px;
        color: #fff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
    
    &.audio-clip {
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
  }"""

new_styles = """  .timeline-clip {
    position: absolute;
    top: 4px;
    height: calc(100% - 8px);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      filter: brightness(1.1);
      transform: scaleY(1.05);
    }
    
    .clip-content {
      padding: 4px 8px;
      height: 100%;
      display: flex;
      align-items: center;
      gap: 6px;
      overflow: hidden;
      
      .clip-name {
        font-size: 11px;
        color: #fff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
    
    &.audio-clip {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      width: 100%;
      left: 0;
      top: 0;
      height: 100%;
    }
  }
  
  .playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ff4444;
    z-index: 10;
    pointer-events: none;
    
    &::before {
      content: '';
      position: absolute;
      top: -4px;
      left: -5px;
      width: 0;
      height: 0;
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 8px solid #ff4444;
    }
  }"""

content = content.replace(old_styles, new_styles)

# 写回文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print("CSS修复完成！")
