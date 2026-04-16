# 读取文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除重复的 currentTime 声明（只删除第二个，即时间轴相关部分的）
# 找到 "const currentTime = ref(0)" 后面的 "// 时间轴计算属性" 并删除重复的 currentTime
old_code = """// 时间轴相关状态变量
const timelineScale = ref(50) // 像素/秒
const currentTime = ref(0)

// 时间轴计算属性"""

new_code = """// 时间轴相关状态变量
const timelineScale = ref(50) // 像素/秒

// 时间轴计算属性"""

content = content.replace(old_code, new_code)

# 写回文件
with open('/root/manhua-workflow/在线剪辑平台/frontend/src/views/EditorPage.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！")
