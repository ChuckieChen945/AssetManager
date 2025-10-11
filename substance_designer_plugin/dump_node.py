"""
导出 Substance Designer 图节点和连接信息
在substance designer中运行
"""

import sd
import json
from sd.api.sdproperty import SDPropertyCategory

# 获取上下文
ctx = sd.getContext()
app = ctx.getSDApplication()
uiMgr = app.getQtForPythonUIMgr()

# 获取当前打开的图
graph = uiMgr.getCurrentGraph()
if graph is None:
    print("没有打开的图。")
    exit()

graph_data = {}

for node in graph.getNodes():
    node_id = node.getIdentifier()
    node_label = node.getDefinition().getLabel()

    node_info = {
        "type": node_label,
    }

    # 输入连接
    inputs = {}
    for input_plug in node.getProperties(SDPropertyCategory.Input):
        connections = []
        for conn in node.getPropertyConnections(input_plug):
            source_node = conn.getOutputPropertyNode()
            source_output = conn.getOutputProperty()
            if source_node and source_output:
                connections.append({
                    "node": source_node.getIdentifier(),
                    "output": source_output.getId()
                })
        if connections:
            inputs[input_plug.getId()] = connections

    # 输出连接
    outputs = {}
    for output_plug in node.getProperties(SDPropertyCategory.Output):
        connections = []
        for conn in node.getPropertyConnections(output_plug):
            target_node = conn.getInputPropertyNode()
            target_input = conn.getInputProperty()
            if target_node and target_input:
                connections.append({
                    "node": target_node.getIdentifier(),
                    "input": target_input.getId()
                })
        if connections:
            outputs[output_plug.getId()] = connections

    if inputs:
        node_info["inputs"] = inputs
    if outputs:
        node_info["outputs"] = outputs

    graph_data[node_id] = node_info

# 导出 JSON
output_path = "D:/graph_export.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=4, ensure_ascii=False)

print(f"✅ 图节点和连接信息已导出到：{output_path}")
