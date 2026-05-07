import shutil
import subprocess
from pathlib import Path
from tkinter.tix import IMAGE

from rich.console import Console

from assetmanager.file_organizer import IMAGE_EXTENSIONS

VIDEO_EXTENSIONS = {".mp4", ".srt", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
console = Console()


def validate_structure(root: Path) -> dict[str, list[Path]]:
    categories: dict[str, list[Path]] = {
        "main_assets_has_subdirs": [],
        "main_assets_multiple_files": [],
        "main_assets_empty": [],
        "thumbnail_has_subdirs": [],
        "thumbnail_multiple_files": [],
        "thumbnail_empty": [],
        "container_has_extra_files": [],
        "incorrect_special_structure": [],
        "leaf_missing_special": [],
    }

    def _is_under_directory(path: Path, ancestor_dir_name: str) -> bool:
        return any(parent.name == ancestor_dir_name for parent in path.parents)

    for folder in root.rglob("*"):
        if folder.is_file():
            continue
        subdirs = [d for d in folder.iterdir() if d.is_dir()]
        files = [f for f in folder.iterdir() if f.is_file()]
        subdir_names = {d.name for d in subdirs}
        # 1. 检查特殊目录
        if folder.name in {"main_assets", "thumbnail"}:
            if subdirs:
                if folder.name == "main_assets":
                    categories["main_assets_has_subdirs"].append(folder)
                else:
                    categories["thumbnail_has_subdirs"].append(folder)
            if len(files) > 1:
                if folder.name == "main_assets":
                    categories["main_assets_multiple_files"].append(folder)
                else:
                    categories["thumbnail_multiple_files"].append(folder)
            if len(files) + len(subdirs) == 0:
                if folder.name == "main_assets":
                    categories["main_assets_empty"].append(folder)
                else:
                    main_images = [
                        f for f in (folder.parent / "main_assets").iterdir() if f.is_file()
                    ]
                    if main_images[0].suffix.lower() not in IMAGE_EXTENSIONS:
                        categories["thumbnail_empty"].append(folder)
            continue
        # main_assets_others 中允许任意文件和子目录，这里跳过main_assets_others中的目录的检查
        if _is_under_directory(folder, "main_assets_others"):
            continue
        # 2. 如果不是特殊目录，检查是否包含多余文件
        if files and folder.name != "main_assets_others":
            categories["container_has_extra_files"].append(folder)
        # 3. 如果不是特殊目录，且包含 main_assets 或 thumbnail，检查其结构是否正确
        expected1 = {"main_assets", "thumbnail"}
        expected2 = {"main_assets", "thumbnail", "main_assets_others"}
        if ("main_assets" in subdir_names) or ("thumbnail" in subdir_names):
            if subdir_names not in (expected1, expected2):
                categories["incorrect_special_structure"].append(folder)
        if not subdirs and folder.name != "main_assets_others":
            categories["leaf_missing_special"].append(folder)
    return categories


def fix_duplicate_named_dirs(path: Path) -> None:
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and dir.parent.name == dir.name:
            console.print(f"发现重复目录: {dir}")
            merge_directories(dir, dir.parent)


def merge_directories(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for file in src_dir.glob("*"):
        if file.is_file():
            move_file_with_check(file, dst_dir)
    for sub_dir in src_dir.glob("*"):
        if sub_dir.is_dir():
            target_sub = dst_dir / sub_dir.name
            if target_sub.exists():
                console.print(f"⚠️ 已存在同名目录: {target_sub} -> 合并中")
                merge_directories(sub_dir, target_sub)
            else:
                shutil.move(str(sub_dir), str(target_sub))
                console.print(f"移动目录: {sub_dir.name}")
    if not any(src_dir.iterdir()):
        src_dir.rmdir()
        console.print(f"🗑️ 删除空目录: {src_dir}")


def move_file_with_check(src_file: Path, dst_dir: Path) -> None:
    dst_file = dst_dir / src_file.name
    if dst_file.exists():
        if src_file.stat().st_size == dst_file.stat().st_size:
            console.print(f"⚠️ 同名文件大小相同，删除源文件: {src_file}")
            src_file.unlink()
        else:
            base = src_file.stem
            ext = src_file.suffix
            i = 1
            while True:
                new_name = f"{base}_{i}{ext}"
                new_dst = dst_dir / new_name
                if not new_dst.exists():
                    console.print(f"⚠️ 同名文件大小不同，重命名为: {new_dst}")
                    shutil.move(str(src_file), str(new_dst))
                    break
                i += 1
    else:
        shutil.move(str(src_file), str(dst_file))
        console.print(f"移动文件: {src_file.name}")


def delete_useless_files_and_dirs(path: Path) -> None:
    for dir in path.rglob("*"):
        if dir.is_dir() and (dir.name == "__MACOSX" or dir.name == ".alg_meta"):
            console.print(f"🗑️ 删除无用目录: {dir}")
            shutil.rmtree(dir, ignore_errors=True)
    for file in path.rglob("._Thumbs.db"):
        console.print(f"🗑️ 删除无用文件: {file}")
        file.unlink(missing_ok=True)
    for file in path.rglob(".DS_Store"):
        console.print(f"🗑️ 删除无用文件: {file}")
        file.unlink(missing_ok=True)


def delete_empty_dirs(path: Path) -> None:
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and not any(dir.iterdir()):
            console.print(f"🗑️ 删除空目录: {dir}")
            dir.rmdir()
