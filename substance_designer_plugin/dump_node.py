import sd
import json
from sd.api.sdproperty import SDPropertyCategory

# 获取应用上下文
ctx = sd.getContext()
app = ctx.getSDApplication()
uiMgr = app.getQtForPythonUIMgr()

# 获取当前图
graph = uiMgr.getCurrentGraph()
if graph is None:
    print("没有打开的图")
    exit()

# 准备节点信息列表
nodes_data = []

# 遍历图中所有节点
for node in graph.getNodes():
    node_info = {
        "name": node.getIdentifier(),           # 节点唯一标识
        "label": node.getDefinition().getLabel(),  # 节点类型名称
        # "position": {"x": node.getPos().x, "y": node.getPos().y},  # 节点在图中的位置
        "inputs": [],                           # 输入连接
        "outputs": []                           # 输出连接
    }

    # 遍历节点的输入端口
    for input_plug in node.getProperties(SDPropertyCategory.Input):
        connections = []
        for conn in node.getPropertyConnections(input_plug):
            # FIXME: AttributeError: 'SDConnection' object has no attribute 'getNode'
            source_node = conn.getOutputPropertyNode()
            source_output = conn.getOutputProperty()
            if source_node and source_output:
                connections.append({
                    "source_node": source_node.getIdentifier(),
                    # FIXME: AttributeError: 'SDProperty' object has no attribute 'getIdentifier'
                    "source_output": source_output.getId()
                })
        node_info["inputs"].append({
            "plug_name": input_plug.getId(),
            "connections": connections
        })

    # 遍历节点的输出端口
    for output_plug in node.getProperties(SDPropertyCategory.Output):
        connections = []
        for conn in node.getPropertyConnections(output_plug):
            target_node = conn.getInputPropertyNode()
            target_input = conn.getInputProperty()
            if target_node and target_input:
                connections.append({
                    "target_node": target_node.getIdentifier(),
                    "target_input": target_input.getId()
                })
        node_info["outputs"].append({
            "plug_name": output_plug.getId(),
            "connections": connections
        })

    nodes_data.append(node_info)

# 将结果写入 JSON 文件
with open("D:/graph_export.json", "w") as f:
    json.dump(nodes_data, f, indent=4)

print("已将图节点和连接导出为 D:/graph_export.json")
