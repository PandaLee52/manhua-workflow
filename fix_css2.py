# 读取文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 timeline-clip 样式的开始和结束位置
start_idx = None
end_idx = None
brace_count = 0
in_timeline_clip = False

for i, line in enumerate(lines):
    if '.timeline-clip {' in line:
        start_idx = i
        in_timeline_clip = True
        brace_count = 0
    
    if in_timeline_clip:
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0 and start_idx is not None and i > start_idx:
            end_idx = i
            break

print(f"Found timeline-clip at lines {start_idx+1} to {end_idx+1}")

# 构建新的 timeline-clip 样式
new_timeline_clip = """  .timeline-clip {
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
  }
"""

# 替换内容
new_lines = lines[:start_idx] + [new_timeline_clip] + lines[end_idx+1:]

# 写回文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("CSS修复完成！")
