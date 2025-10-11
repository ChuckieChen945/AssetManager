"""
逐个打开一系列.sbs文件，对每个.sbs文件收集其中节点的标签，保存到同名的json文件中
"""


import sd
import json

# 获取上下文
ctx = sd.getContext()
app = ctx.getSDApplication()
uiMgr = app.getQtForPythonUIMgr()

# 获取当前打开的图
graph = uiMgr.getCurrentGraph()
if graph is None:
    print("没有打开的图。")
    exit()

# 使用集合去重
node_labels = set()

# 遍历所有节点并收集标签
for node in graph.getNodes():
    definition = node.getDefinition()
    if definition is not None:
        label = definition.getLabel()
        if label:
            node_labels.add(label)

# 转为列表以便导出 JSON
unique_labels = sorted(list(node_labels))

# 导出 JSON 文件
output_path = "D:/node_labels.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(unique_labels, f, indent=4, ensure_ascii=False)

print(f"✅ 共收集到 {len(unique_labels)} 个唯一节点标签，已导出到：{output_path}")