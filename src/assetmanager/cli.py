"""AssetManager CLI."""

import concurrent.futures
import os
import shutil
import subprocess
from pathlib import Path

import typer
from rich import print as rprint

app = typer.Typer()

exts = {".zip", ".7z", ".rar"}


def move_file_with_check(src_file: Path, dst_dir: Path) -> None:
    """move_file_with_check."""
    dst_file = dst_dir / src_file.name

    if dst_file.exists():
        if src_file.stat().st_size == dst_file.stat().st_size:
            print(f"⚠️ 同名文件大小相同，删除源文件: {src_file}")
            src_file.unlink()
        else:
            base = src_file.stem
            ext = src_file.suffix
            i = 1
            while True:
                new_name = f"{base}_{i}{ext}"
                new_dst = dst_dir / new_name
                if not new_dst.exists():
                    print(f"⚠️ 同名文件大小不同，重命名为: {new_dst}")
                    shutil.move(str(src_file), str(new_dst))
                    break
                i += 1
    else:
        shutil.move(str(src_file), str(dst_file))
        print(f"移动文件: {src_file.name}")


def merge_directories(src_dir: Path, dst_dir: Path) -> None:
    """merge_directories."""
    dst_dir.mkdir(parents=True, exist_ok=True)

    # 文件合并
    for file in src_dir.glob("*"):
        if file.is_file():
            move_file_with_check(file, dst_dir)

    # 递归合并子目录
    for sub_dir in src_dir.glob("*"):
        if sub_dir.is_dir():
            target_sub = dst_dir / sub_dir.name
            if target_sub.exists():
                print(f"⚠️ 已存在同名目录: {target_sub} -> 合并中")
                merge_directories(sub_dir, target_sub)
            else:
                shutil.move(str(sub_dir), str(target_sub))
                print(f"移动目录: {sub_dir.name}")

    # 清理空目录
    if not any(src_dir.iterdir()):
        src_dir.rmdir()
        print(f"🗑️ 删除空目录: {src_dir}")


def fix_duplicate_named_dirs(path: Path) -> None:
    """fix_duplicate_named_dirs."""
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and dir.parent.name == dir.name:
            print(f"发现重复目录: {dir}")
            merge_directories(dir, dir.parent)


def extract_file(file: Path) -> None:
    """解压单个."""
    out_dir = file.with_name(file.stem)
    if not out_dir.exists():
        out_dir.mkdir(parents=True)

    try:
        result = subprocess.run(
            ["7z", "x", "-y", str(file), f"-o{out_dir!s}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"✅ 解压完成: {file.name}")
            file.unlink()
            print(f"🗑️ 已删除压缩包: {file}")
        else:
            print(f"❌ 解压失败: {file}")
            print(result.stderr)
    except Exception as e:
        print(f"❌ 异常解压: {file} - {e}")


def extract_archives_multithreaded(path: Path) -> None:
    """批量解压."""
    archive_files = [f for f in path.rglob("*") if f.suffix.lower() in exts and f.is_file()]
    print(f"共找到 {len(archive_files)} 个压缩包，开始多线程解压...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(extract_file, archive_files)


def delete_useless_files_and_dirs(path: Path) -> None:
    """删除无用文件."""
    # 删除所有 __MACOSX 文件夹
    for dir in path.rglob("*"):
        if dir.is_dir() and dir.name == "__MACOSX":
            print(f"🗑️ 删除无用目录: {dir}")
            shutil.rmtree(dir, ignore_errors=True)

    # 删除所有 ._Thumbs.db 文件
    for file in path.rglob("._Thumbs.db"):
        print(f"🗑️ 删除无用文件: {file}")
        file.unlink(missing_ok=True)


def delete_empty_dirs(path: Path) -> None:
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and not any(dir.iterdir()):
            print(f"🗑️ 删除空目录: {dir}")
            dir.rmdir()


@app.command()
def extract(path: str) -> None:
    """多线程解压目录中的所有压缩文件."""
    print("📦 开始批量解压...")
    extract_archives_multithreaded(Path(path))


@app.command()
def arrange(path: str) -> None:
    """整理目录."""
    path_ = Path(path)
    print("🧹 开始清理无用文件...")
    delete_useless_files_and_dirs(path_)
    print("📁 合并重复目录...")
    fix_duplicate_named_dirs(path_)
    delete_empty_dirs(path_)
    print("✅ 所有操作已完成")


@app.command()
def all_in_one(path: str) -> None:
    """一次性整理、解压、验证文件夹."""
