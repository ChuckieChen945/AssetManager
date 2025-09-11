""" Substance Painter 插件: 用于从 AppData/Roaming/Adobe/Adobe Substance 3D Painter/previews  批量提取 .spsm 文件的缩略图
"""

from pathlib import Path
import shutil
import struct
import time

import substance_painter.resource as spr
import substance_painter.ui
from PySide6 import QtWidgets

plugin_widgets = []
"""Keep track of added ui elements for cleanup"""

# Substance Painter 的预览目录
PREVIEW_DIR = Path.home() / "AppData/Roaming/Adobe/Adobe Substance 3D Painter/previews"

def repair_webp(input_file_path, output_file_path):
    """
    修复具有错误头偏移的 .webp 文件。
    """
    try:
        data = Path(input_file_path).read_bytes()
        riff_marker = b"RIFF"
        riff_start_index = data.find(riff_marker)

        if riff_start_index == -1:
            print(f"❌ 未找到 'RIFF' 标记: {input_file_path}")
            return False

        valid_data = data[riff_start_index:]
        new_filesize = len(valid_data) - 8
        new_filesize_bytes = struct.pack("<I", new_filesize)
        final_data = valid_data[:4] + new_filesize_bytes + valid_data[8:]
        Path(output_file_path).write_bytes(final_data)

        print(f"✅ 修复完成: {output_file_path}")
        return True

    except Exception as e:
        print(f"❌ 修复失败 {input_file_path}: {e}")
        return False


def clear_previews():
    """清理 Substance Painter 的预览目录"""
    if PREVIEW_DIR.exists():
        for f in PREVIEW_DIR.iterdir():
            try:
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)
            except Exception as e:
                print(f"⚠️ 删除预览文件失败 {f}: {e}")


def get_new_preview():
    """
    在预览目录中查找生成的缩略图。
    - Substance Painter 在 import 后会生成 1-2 个文件:
      - cache_data （缓存）
      - 另一个 .webp 文件（就是缩略图）
    """
    for i in range(10):  # 最多等待 10 秒
        previews = list(PREVIEW_DIR.iterdir())
        previews = [p for p in previews if p.is_file() and p.name != "cache_data"]
        if len(previews) > 1:
            return None  # 出现多个预览文件，无法确定
        if previews:
            return previews[0]
        time.sleep(1)
    return None


def start_plugin():
    """插件启动"""
    folder = QtWidgets.QFileDialog.getExistingDirectory(
        None, "选择包含 .spsm 的文件夹", str(Path.home())
    )
    if not folder:
        return

    folder_path = Path(folder)
    spsm_files = list(folder_path.glob("*.spsm"))

    if not spsm_files:
        QtWidgets.QMessageBox.information(None, "提示", "所选文件夹下没有找到 .spsm 文件")
        return

    for spsm_file in spsm_files:
        try:
            print(f"\n📦 正在处理: {spsm_file.name}")

            # 1. 清理旧预览
            clear_previews()

            # 2. 导入资源（触发 Substance Painter 生成缩略图）
            resource = spr.import_session_resource(str(spsm_file), spr.Usage.SMART_MATERIAL)
            # 生成缩略图
            resource.reset_preview()

            # # 3. 获取新缩略图
            preview_file = get_new_preview()
            if not preview_file:
                print(f"❌ 未生成缩略图，请尝试重启软件: {spsm_file.name}")
                continue

            # 4. 修复缩略图并保存到同目录
            output_file = spsm_file.with_suffix(".webp")
            repair_webp(preview_file, output_file)

        except Exception as e:
            print(f"❌ 处理 {spsm_file.name} 出错: {e}")


def close_plugin():
    """插件关闭时清理 UI"""
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)
    plugin_widgets.clear()


if __name__ == "__main__":
    start_plugin()
