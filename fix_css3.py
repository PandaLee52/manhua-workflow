# 读取文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并删除重复的 playhead 定义
# 找到两个 playhead 定义之间的内容
import re

# 使用正则表达式删除重复的 playhead 定义
# 保留第一个 playhead 定义和其所有内容（包括 &::before 部分）
pattern = r'(\.playhead \{[^}]*\}'

# 找到所有 playhead 块
playhead_matches = list(re.finditer(r'\.playhead \{', content))
print(f"找到 {len(playhead_matches)} 个 playhead 定义")

if len(playhead_matches) >= 2:
    # 找到第二个 playhead 开始的位置
    second_start = playhead_matches[1].start()
    
    # 找到第一个 playhead 结束的位置（在第二个开始之前）
    # 我们需要找到第一个 playhead 块的结束位置
    first_playhead_start = playhead_matches[0].start()
    
    # 查找从第一个 playhead 开始到第二个 playhead 开始的中间内容
    between = content[first_playhead_start:second_start]
    
    # 找到第一个 playhead 的完整块（匹配的花括号）
    brace_count = 0
    end_pos = first_playhead_start
    for i, char in enumerate(content[first_playhead_start:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        end_pos = first_playhead_start + i + 1
        if brace_count == 0:
            break
    
    # 删除第二个 playhead 及其内容
    second_playhead_start = playhead_matches[1].start()
    
    # 找到第二个 playhead 的结束位置
    brace_count = 0
    second_end_pos = second_playhead_start
    for i, char in enumerate(content[second_playhead_start:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        second_end_pos = second_playhead_start + i + 1
        if brace_count == 0:
            break
    
    # 删除重复的 playhead 定义
    content = content[:second_playhead_start] + content[second_end_pos:]
    
    print(f"已删除重复的 playhead 定义")

# 写回文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！")
