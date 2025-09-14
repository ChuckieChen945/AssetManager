# -*- coding: utf-8 -*-
"""为指定目录下的所有 .sbs 文件生成缩略图."""

import os
import subprocess
import shutil
import tempfile
import logging
from pathlib import Path

import sd
from sd.api.sbs.sdsbsarexporter import SDSBSARExporter

# ================= 配置区域 =================
INPUT_DIR = Path("D:\\temp\\01格子衫")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

# ================= 初始化 =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

app = sd.getContext().getSDApplication()

exporter = SDSBSARExporter.sNew()
exporter.setIconEnabled(True)


# ================= 工具函数 =================
def run_7z_extract(sbsar_path: Path, output_dir: Path) -> bool:
    """调用 7z 解压文件，成功返回 True"""
    try:
        subprocess.run(
            ["7z", "x", str(sbsar_path), f"-o{output_dir}", "-y"],
            check=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error("解压失败: %s (%s)", sbsar_path, e)
        return False


def extract_images_from_sbsar(sbsar_path: Path, output_dir: Path, base_name: str) -> int:
    """解压 sbsar 文件中的图片并重命名，返回提取的数量"""
    # ✅ 使用系统临时目录，避免和原文件同目录权限冲突
    with tempfile.TemporaryDirectory(prefix="sbsar_extract_") as temp_dir:
        temp_path = Path(temp_dir)

        if not run_7z_extract(sbsar_path, temp_path):
            return 0

        extracted_images = []
        for ext in IMAGE_EXTS:
            extracted_images.extend(temp_path.rglob(f"*{ext}"))

        if not extracted_images:
            return 0

        # 排序 & 重命名
        for idx, img_file in enumerate(sorted(extracted_images), start=1):
            new_name = (
                f"{base_name}{img_file.suffix.lower()}"
                if len(extracted_images) == 1
                else f"{base_name}_{idx}{img_file.suffix.lower()}"
            )
            new_path = output_dir / new_name
            if new_path.exists():
                new_path.unlink()
            shutil.move(str(img_file), new_path)

        return len(extracted_images)


def export_sbs_to_sbsar(sbs_file: Path, target: Path) -> None:
    """导出 .sbs 为 .sbsar"""
    exporter.exportSBSFileToSBSAR(str(sbs_file), str(target))
    logging.info("已导出 %s", target.name)


# ================= 主逻辑 =================
def process_sbs_file(sbs_file: Path) -> None:
    """处理单个 .sbs 文件"""
    base_name = sbs_file.stem
    sbsar_file = sbs_file.parent / f"{base_name}.sbsar"
    existing_images = [sbs_file.parent / f"{base_name}{ext}" for ext in IMAGE_EXTS]

    # 1. 已有缩略图
    if any(img.exists() for img in existing_images):
        logging.info("跳过 %s: 已存在缩略图", sbs_file.name)
        return

    # 2. 已有 sbsar，尝试解压
    if sbsar_file.exists():
        count = extract_images_from_sbsar(sbsar_file, sbs_file.parent, base_name)
        if count:
            logging.info("从 %s 提取到 %d 张图片", sbsar_file.name, count)
            return

        # 解压失败，导出临时 sbsar
        temp_sbsar = INPUT_DIR / f"{base_name}.sbsar.temp"
        try:
            export_sbs_to_sbsar(sbs_file, temp_sbsar)
            count = extract_images_from_sbsar(temp_sbsar, sbs_file.parent, base_name)
            if count:
                logging.info("从 %s 提取到 %d 张图片", temp_sbsar.name, count)
        finally:
            if temp_sbsar.exists():
                temp_sbsar.unlink()

    # 3. 如果没有 sbsar，生成一个正式的
    if not sbsar_file.exists():
        export_sbs_to_sbsar(sbs_file, sbsar_file)

    # 4. 再尝试一次解压
    count = extract_images_from_sbsar(sbsar_file, sbs_file.parent, base_name)
    if count:
        logging.info("从 %s 提取到 %d 张图片", sbsar_file.name, count)
    else:
        logging.warning("即使导出 %s 也未提取到图片", sbsar_file.name)


def main() -> None:
    """批量处理目录下的所有 .sbs 文件"""
    for sbs_file in INPUT_DIR.rglob("*.sbs"):
        process_sbs_file(sbs_file)


if __name__ == "__main__":
    main()
