"""
Substance Painter 插件.

用于从 AppData/Roaming/Adobe/Adobe Substance 3D Painter/previews
批量提取 .spsm/.sbsar 文件的缩略图
"""

import shutil
import struct
import time
from pathlib import Path

import substance_painter.resource as spr
import substance_painter.ui
from PySide6 import QtWidgets

plugin_widgets = []

# Substance Painter 的预览目录
PREVIEW_DIR = Path.home() / "AppData/Roaming/Adobe/Adobe Substance 3D Painter/previews"


def repair_webp(input_file_path, output_file_path) -> bool:
    """修复具有错误头偏移的 .webp 文件."""
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


def clear_previews() -> None:
    """清理 Substance Painter 的预览目录."""
    if PREVIEW_DIR.exists():
        for f in PREVIEW_DIR.iterdir():
            try:
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)
            except Exception as e:
                print(f"⚠️ 删除预览文件失败 {f}: {e}")


def get_new_preview(resource: spr.Resource, timeout=10, retry_if_multiple=True) -> None | Path:
    """在预览目录中查找生成的缩略图，优化逻辑以提高成功率"""

    def get_preview_files():
        return [p for p in PREVIEW_DIR.iterdir() if p.is_file() and p.name != "cache_data"]

    clear_previews()
    resource.reset_preview()

    for _ in range(timeout):
        previews = get_preview_files()
        if len(previews) == 1:
            return previews[0]

        if len(previews) > 1:
            print("⚠️ 出现多个预览文件，无法确定正确缩略图")
            break

        time.sleep(1)

    # 超时后重试一次（可选）
    if retry_if_multiple:
        print("⏳ 尝试再次生成")
        clear_previews()
        resource.reset_preview()
        for _ in range(timeout):
            previews = get_preview_files()
            if len(previews) == 1:
                return previews[0]

            if len(previews) > 1:
                print("⚠️ 出现多个预览文件，无法确定正确缩略图")
                return None

    print("❌ 未生成缩略图")
    return None


def start_plugin() -> None:
    """插件启动"""
    folder = QtWidgets.QFileDialog.getExistingDirectory(
        None,
        "选择包含 .spsm/.sbsar 的文件夹",
        str(Path.home()),
    )
    if not folder:
        return

    folder_path = Path(folder)
    spsm_files = list(folder_path.glob("**/*.spsm"))
    sbsar_files = list(folder_path.glob("**/*.sbsar"))
    sppr_files = list(folder_path.glob("**/*.sppr"))
    all_files = spsm_files + sbsar_files + sppr_files

    if not all_files:
        QtWidgets.QMessageBox.information(None, "提示", "所选文件夹下没有找到 .spsm/.sbsar 文件")
        return

    processed_files = []
    skipped_files = []

    for file_path in all_files:
        output_file = file_path.with_suffix(".webp")
        if output_file.exists():
            print(f"⚠️ 已存在缩略图，跳过: {file_path.name}")
            skipped_files.append(file_path.name)
            continue

        try:
            print(f"\n📦 正在处理: {file_path.name}")
            if file_path.suffix.lower() == ".sbsar":
                usage = spr.Usage.BASE_MATERIAL
            elif file_path.suffix.lower() == ".sppr":
                usage = spr.Usage.BRUSH
            else:
                usage = spr.Usage.SMART_MATERIAL
            resource = spr.import_session_resource(str(file_path), usage)
            preview_file = get_new_preview(resource)
            if not preview_file:
                print(f"❌ 未生成缩略图: {file_path}")
                skipped_files.append(file_path.name)
                continue
            repair_webp(preview_file, output_file)
            processed_files.append(file_path.name)
        except Exception as e:
            print(f"❌ 处理 {file_path} 出错: {e}")
            skipped_files.append(file_path.name)

    QtWidgets.QMessageBox.information(
        None,
        "处理完成",
        f"✅ 成功生成: {len(processed_files)} 文件\n⚠️ 跳过/失败: {len(skipped_files)} 文件",
    )


def close_plugin():
    """插件关闭时清理 UI"""
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)
    plugin_widgets.clear()


if __name__ == "__main__":
    start_plugin()
