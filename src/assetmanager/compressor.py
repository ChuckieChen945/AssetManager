from pathlib import Path
import shutil
import subprocess
from multiprocessing import Pool

ARCHIVE_SUFFIX = ".7z"
ARCHIVE_LEVEL = "-mx=9"
TARGET_FOLDER_NAME = "main_assets"

def log(message: str) -> None:
    print(message)

def should_compress(folder: Path) -> bool:
    if not folder.is_dir():
        return False
    files = list(folder.iterdir())
    if len(files) <= 1:
        log(f"[跳过] {folder} 不需要压缩（文件数 <= 1）")
        return False
    zip_name = folder / f"{folder.parent.name}{ARCHIVE_SUFFIX}"
    if zip_name.exists():
        log(f"[跳过] {zip_name} 已存在")
        return False
    return True

def compress_folder(folder: Path) -> None:
    if not should_compress(folder):
        return
    zip_name = folder / f"{folder.parent.name}{ARCHIVE_SUFFIX}"
    content_to_compress = [str(item) for item in folder.iterdir()]
    log(f"[压缩中] {folder}")
    try:
        result = subprocess.run([
            "7z", "a", str(zip_name), *content_to_compress, "-r", ARCHIVE_LEVEL
        ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            log(f"[失败] 压缩失败：{folder}\n错误信息：{result.stderr}")
            return
        log(f"[成功] 压缩完成：{zip_name}")
        _cleanup_original_files(folder, zip_name)
    except Exception as e:
        log(f"[异常] 压缩异常：{folder}，原因：{e}")

def _cleanup_original_files(folder: Path, zip_file: Path) -> None:
    try:
        for item in folder.iterdir():
            if item.resolve() == zip_file.resolve():
                continue
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        log(f"[清理完成] 已清空原始内容：{folder}")
    except Exception as e:
        log(f"[清理失败] {folder}，原因：{e}")

def process(root: Path) -> None:
    folders = [f for f in root.rglob(TARGET_FOLDER_NAME) if f.is_dir()]
    if not folders:
        log("[信息] 未找到任何 main_assets 文件夹。")
        return
    log(f"[发现] 共找到 {len(folders)} 个 main_assets 文件夹，开始处理...")
    with Pool(processes=3) as pool:
        pool.map(compress_folder, folders)
