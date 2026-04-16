# 读取文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并修复孤立的样式代码
# 这些应该被删除，因为它们是旧的 timeline-clip 样式残留
old_orphaned = """  }
    
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
  }
  
  .subtitle-marker {"""

new_orphaned = """  }
  
  .subtitle-marker {"""

content = content.replace(old_orphaned, new_orphaned)

# 写回文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print("CSS最终修复完成！")
