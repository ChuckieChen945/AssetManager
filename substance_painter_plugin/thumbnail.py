"""
Substance Painter 插件

批量提取 .spsm / .sbsar / .sppr 文件的缩略图
需手动安装 libwebp
scoop install main/libwebp
"""

import shutil
import struct
import subprocess
import time
from pathlib import Path
import zipfile
import logging

import substance_painter.resource as spr
import substance_painter.ui
from PySide6 import QtWidgets

# ================== 常量配置 ==================

# 支持的图片扩展名
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

# Substance Painter 预览目录
PREVIEW_DIR = Path.home() / "AppData/Roaming/Adobe/Adobe Substance 3D Painter/previews"

# 文件后缀与对应的 usage 类型
SUFFIX_USAGE_MAP = {
    ".sbsar": spr.Usage.BASE_MATERIAL,
    ".sppr": spr.Usage.BRUSH,
    ".spsm": spr.Usage.SMART_MATERIAL,
    ".spmsk": spr.Usage.SMART_MASK,
}

plugin_widgets = []


# ================== 日志工具 ==================

def log_info(msg: str) -> None:
    print(f"✅ {msg}")
    # logging.info(msg)


def log_warn(msg: str) -> None:
    print(f"⚠️ {msg}")
    # logging.warning(msg)


def log_error(msg: str) -> None:
    print(f"❌ {msg}")
    # logging.error(msg)


# ================== 工具函数 ==================


def extract_single_image(zip_path: Path) -> bool:
    """
    使用 7z 从 .sbsar (zip 格式) 文件中提取单张图片。
    仅当压缩包里有且只有一张图片时才会成功。
    不弹出控制台窗口。
    """
    try:
        # 1. 列出压缩包内容
        result = subprocess.run(
            ["7z", "l", str(zip_path)],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = result.stdout
        images = []
        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            filename = parts[-1]
            if Path(filename).suffix.lower() in IMAGE_EXTS:
                images.append(filename)
        if len(images) != 1:
            return False
        image_file = images[0]
        output_path = zip_path.with_suffix(Path(image_file).suffix.lower())
        # 2. 解压目标文件到指定目录
        subprocess.run(
            ["7z", "e", str(zip_path), image_file, f"-o{zip_path.parent}", "-y"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        # 3. 重命名为和 zip 一致的文件名
        extracted_file = zip_path.parent / Path(image_file).name
        if extracted_file.exists():
            extracted_file.rename(output_path)
        log_info(f"已提取图片到: {output_path}")
        return True
    except Exception as e:
        log_error(f"提取失败 {zip_path}: {e}")
        return False


def repair_webp(input_file_path: Path, output_file_path: Path) -> bool:
    """
    修复具有错误头偏移的 .webp 文件。
    自动调用 libwebp 的 dwebp 工具修复 webp 文件。
    """
    try:
        data = input_file_path.read_bytes()
        riff_start_index = data.find(b"RIFF")
        if riff_start_index == -1:
            log_error(f"未找到 'RIFF' 标记: {input_file_path}")
            return False
        valid_data = data[riff_start_index:]
        new_size = len(valid_data) - 8
        new_data = valid_data[:4] + struct.pack("<I", new_size) + valid_data[8:]
        temp_webp = output_file_path.with_suffix(".temp.webp")
        temp_webp.write_bytes(new_data)
        # 调用 dwebp 修复
        result = subprocess.run(
            ["dwebp", str(temp_webp), "-o", str(output_file_path.with_suffix(".png"))],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        temp_webp.unlink(missing_ok=True)
        if result.returncode == 0:
            log_info(f"修复完成: {output_file_path.with_suffix('.png')}")
            return True
        else:
            log_error(f"dwebp 修复失败: {input_file_path}")
            return False
    except Exception as e:
        log_error(f"修复失败 {input_file_path}: {e}")
        return False


def clear_previews() -> None:
    """清理 Substance Painter 的预览目录。"""
    if not PREVIEW_DIR.exists():
        return
    for f in PREVIEW_DIR.iterdir():
        try:
            if f.is_file():
                f.unlink()
            else:
                shutil.rmtree(f)
        except Exception as e:
            log_warn(f"删除预览文件失败 {f}: {e}")


def get_new_preview(resource: spr.Resource, timeout: int = 10, retry: bool = True) -> Path | None:
    """
    在预览目录中查找生成的缩略图。
    比较文件创建时间，确保是新生成的。
    """

    def get_preview_files():
        return [p for p in PREVIEW_DIR.iterdir() if p.is_file() and p.name != "cache_data"]

    def try_generate():
        clear_previews()
        start_time = time.time()
        resource.reset_preview()
        for _ in range(timeout):
            previews = get_preview_files()
            if len(previews) == 1:
                preview = previews[0]
                # 检查文件创建时间
                # substance painter 的python版本不能用 .stat().st_birthtime
                ctime = preview.stat().st_ctime
                if ctime >= start_time:
                    return preview
                else:
                    log_warn(f"预览文件时间早于触发时间，忽略: {preview}")
                    return None
            if len(previews) > 1:
                log_warn("出现多个预览文件，无法确定正确缩略图")
                return None
            time.sleep(1)
        return None

    preview = try_generate()
    if not preview and retry:
        log_info("⏳ 尝试再次生成")
        preview = try_generate()

    return preview


def has_existing_preview(file_path: Path) -> bool:
    """检查目标文件是否已有缩略图。"""
    return any(file_path.with_suffix(ext).exists() for ext in IMAGE_EXTS)


# ================== 插件逻辑 ==================


def start_plugin() -> None:
    """插件启动"""
    folder = QtWidgets.QFileDialog.getExistingDirectory(
        None,
        "选择包含 .spsm/.sbsar/.sppr/ .spmsk 的文件夹",
        str(Path.home()),
    )
    if not folder:
        return

    folder_path = Path(folder)
    all_files = [
        *folder_path.glob("**/*.spsm"),
        *folder_path.glob("**/*.sbsar"),
        *folder_path.glob("**/*.sppr"),
        *folder_path.glob("**/*.spmsk"),
    ]

    if not all_files:
        QtWidgets.QMessageBox.information(None, "提示", "未找到可处理的文件")
        return

    processed, skipped = [], []

    for file_path in all_files:
        if has_existing_preview(file_path):
            log_warn(f"已存在缩略图，跳过: {file_path.name}")
            skipped.append(file_path.name)
            continue

        try:
            log_info(f"📦 正在处理: {file_path.name}")

            if file_path.suffix.lower() == ".sbsar" and extract_single_image(file_path):
                processed.append(file_path.name)
                continue

            usage = SUFFIX_USAGE_MAP.get(file_path.suffix.lower())
            if not usage:
                log_warn(f"未知文件类型: {file_path}")
                skipped.append(file_path.name)
                continue

            resource = spr.import_session_resource(str(file_path), usage)
            preview_file = get_new_preview(resource)
            if not preview_file:
                log_error(f"未生成预览，跳过: {file_path}")
                skipped.append(file_path.name)
                continue

            output_file = file_path.with_suffix(".webp")
            if repair_webp(preview_file, output_file):
                processed.append(file_path.name)
            else:
                skipped.append(file_path.name)

        except Exception as e:
            log_error(f"处理 {file_path} 出错: {e}")
            skipped.append(file_path.name)

    QtWidgets.QMessageBox.information(
        None,
        "处理完成",
        f"✅ 成功生成: {len(processed)} 文件\n⚠️ 跳过/失败: {len(skipped)} 文件",
    )


def close_plugin():
    """插件关闭时清理 UI"""
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)
    plugin_widgets.clear()


if __name__ == "__main__":
    start_plugin()
