"""
使用hython执行
遍历eagle中的hip文件，将其导出houdini2chat的py脚本
"""

import hou
from pathlib import Path
import requests
from typing import List, Optional

BASE_URL = "http://localhost:41595/api"
LIBRARY_PATH = Path(r"F:\eagle_librarys\Illusion.library\images")
HDA_PATH = Path(r"D:\scoop\apps\houdini2chat\current\sop_rendermagix.houdini_2_chat.0.1.0.hdalc")

prompt = """Example Prompts:
You are a SideFx Houdini Expert and Helpful assistant, looking at pseudo-code representation of a Houdini Network.
Visualize the Node Network by reflecting on the branch connections, loops, vex wrangles, and node definition.
Can you explain the purpose of this Network and its key components in Full Details?
Can you break it down as smaller logical functions, with inputs/outputs/purpose for each.
Think of the (animated) visual output of each function and describe it.\n"""

failed_hips = []  # 全局收集失败的 HIP 文件


def log(msg: str):
    print(msg)


def safe_request(url: str, params: dict):
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "success":
            return data.get("data", [])
        log(f"❌ API 返回错误: {data}")
        return []
    except Exception as e:
        log(f"❌ 请求失败: {e}")
        return []


def list_items_in_folder(folder_id: str) -> List[dict]:
    return safe_request(f"{BASE_URL}/item/list", {"folders": folder_id, "limit": 10000, "offset": 0})


def load_hip_file(hip_path: Path) -> bool:
    try:
        hou.hipFile.load(str(hip_path), suppress_save_prompt=True, ignore_load_warnings=True)
        log(f"✅ 加载 HIP: {hip_path.name}")
        return True
    except Exception as e:
        log(f"❌ 加载 HIP 失败: {hip_path.name} ({e})")
        return False


def install_hda(hda_path: Path):
    try:
        hou.hda.installFile(str(hda_path))
        log(f"✅ 加载 HDA: {hda_path.name}")
    except Exception as e:
        log(f"❌ 加载 HDA 失败: {e}")


def press_export_button(node: hou.Node):
    for parm_name in ["export_network"]:
        parm = node.parm(parm_name)
        if parm:
            try:
                parm.pressButton()
                log(f"  🚀 按钮 {parm_name} 执行成功")
            except Exception as e:
                log(f"  ❌ 按钮 {parm_name} 执行失败: {e}")
            break


def process_geo_node(node: hou.Node):
    if node.type().name() != "geo":
        return
    h2c_node = node.node("houdini_2_chat")
    if not h2c_node:
        try:
            h2c_node = node.createNode("houdini_2_chat")
            log(f"  ➕ 创建节点: {h2c_node.path()}")
        except hou.OperationFailed as e:
            log(f"  ❌ 创建节点失败: {e}")
            return
    press_export_button(h2c_node)


def process_hip_folder(info_dir: Path):
    if not info_dir.exists() or not info_dir.is_dir():
        return

    hip_files = list(info_dir.glob("*.hip"))
    if not hip_files:
        log(f"❌ 未找到 HIP 文件: {info_dir}")
        return

    for hip_file in hip_files:
        if not load_hip_file(hip_file):
            failed_hips.append(str(hip_file))
            continue

        install_hda(HDA_PATH)

        obj = hou.node("/obj")
        if obj:
            for node in obj.children():
                process_geo_node(node)


def post_process(info_dir: Path):
    for py_file in info_dir.rglob("*.py"):
        try:
            with open(py_file, "r+", encoding="utf-8") as f:
                code = f.read().replace("认准淘宝店铺：CG资源站\n", "").replace(prompt, "")
                f.seek(0)
                f.write(code)
                f.truncate()
        except Exception as e:
            log(f"❌ 后处理失败: {py_file} ({e})")


def main():
    folder_id = "METEXKIEN5Q7P"
    items = list_items_in_folder(folder_id)
    for item in items:
        item_id = item.get("id")
        info_dir = LIBRARY_PATH / f"{item_id}.info"
        try:
            process_hip_folder(info_dir)
            post_process(info_dir)
        except Exception as e:
            log(f"❌ 处理目录失败: {info_dir} ({e})")
            continue

    if failed_hips:
        log("\n❌ 以下 HIP 文件处理失败：")
        for f in failed_hips:
            log(f"  - {f}")
    else:
        log("\n✅ 所有 HIP 文件处理完成")


if __name__ == "__main__":
    main()
