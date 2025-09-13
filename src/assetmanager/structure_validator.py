from pathlib import Path
import shutil
import subprocess
from rich.console import Console

VIDEO_EXTENSIONS = {".mp4", ".srt", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
GET_THUMBNAIL_SCRIPT_PATH = str(
    Path(__file__) / "../../../src_eagle_plugin/thumbnail/get_thumbnail.ps1",
)
console = Console()

def validate_structure(root: Path) -> dict[str, list[Path]]:
    categories: dict[str, list[Path]] = {
        "main_assets_has_subdirs": [],
        "main_assets_multiple_files": [],
        "main_assets_empty": [],
        "thumbnail_has_subdirs": [],
        "thumbnail_multiple_files": [],
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
        if folder.name == "main_assets":
            thumbnail_folder = folder.parent / "thumbnail"
            thumbnail = [f for f in thumbnail_folder.iterdir() if f.is_file()]
            if len(thumbnail) <= 0:
                main_file = next(
                    (f for f in folder.iterdir() if f.is_file() and f.suffix in {".zprj", ".zpac"}),
                    None,
                )
                if main_file:
                    console.print(f"为 {main_file} 生成thumbnail...")
                    result = subprocess.run([
                        "pwsh.exe", "-File", GET_THUMBNAIL_SCRIPT_PATH,
                        "-InputFile", str(main_file),
                        "-OutputFile", str(thumbnail_folder / "thumbnail.png"),
                        "-NoProfile", "-NoLogo",
                    ], check=False, capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ 生成成功:", result.stdout.strip())
                    else:
                        print("❌ 生成失败:", result.stderr.strip())
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
            if folder.name == "main_assets" and len(files) + len(subdirs) == 0:
                categories["main_assets_empty"].append(folder)
            continue
        if _is_under_directory(folder, "main_assets"):
            continue
        if files:
            categories["container_has_extra_files"].append(folder)
        expected = {"main_assets", "thumbnail"}
        if ("main_assets" in subdir_names) or ("thumbnail" in subdir_names):
            if subdir_names != expected:
                categories["incorrect_special_structure"].append(folder)
        if not subdirs:
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
