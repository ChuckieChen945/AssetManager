"""
逐个打开一系列.sbs文件，对每个.sbs文件收集其中节点的标签，保存到同名的json文件中
"""

import sd
import os
import json

# ========== 可自定义区域 ==========
input_folder = r"D:/temp"   # 改成你的.sbs文件所在文件夹
output_folder = r"D:/temp"
# =================================

# 获取上下文
ctx = sd.getContext()
app = ctx.getSDApplication()
sdMgr = app.getPackageMgr()

# 确保输出目录存在
os.makedirs(output_folder, exist_ok=True)

# 遍历目录中的所有 .sbs 文件
for file_name in os.listdir(input_folder):
    if not file_name.lower().endswith(".sbs"):
        continue

    sbs_path = os.path.join(input_folder, file_name)
    print(f"📂 正在处理文件：{sbs_path}")

    # 打开 .sbs 包
    pkg = sdMgr.loadUserPackage(sbs_path)
    if pkg is None:
        print(f"⚠️ 无法打开：{sbs_path}")
        continue

    # 遍历包内的所有图（graph）
    for resource in pkg.getChildrenResources(True):
        if "Graph" in resource.getClassName():
            graph = resource
            node_labels = set()

            # 遍历图内的节点
            for node in graph.getNodes():
                definition = node.getDefinition()
                if definition is not None:
                    label = definition.getLabel()
                    if label:
                        node_labels.add(label)

            # 转为列表以便导出 JSON
            unique_labels = sorted(list(node_labels))

            # 输出 JSON 文件路径：使用 sbs 文件名 + 图名
            base_name = os.path.splitext(file_name)[0]
            graph_name = graph.getIdentifier()  # 或 graph.getLabel()
            output_path = os.path.join(output_folder, f"{base_name}_{graph_name}.json")

            # 导出 JSON 文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(unique_labels, f, indent=4, ensure_ascii=False)

            print(f"✅ {file_name} - {graph_name}：共收集到 {len(unique_labels)} 个唯一节点标签，已导出到：{output_path}")

    sdMgr.unloadUserPackage(pkg)

print("🎉 全部文件处理完成。")
