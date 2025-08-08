"""AssetManager CLI."""

import concurrent.futures
import os
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer()

COMPRESS_EXTENSIONS = {".zip", ".7z", ".rar"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def ensure_dir(path: Path | str) -> None:
    """确保目录存在.

    Args:
        path: 目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def fast_move(src: str, dst: str) -> None:
    """快速移动文件."""
    dst_path = Path(dst)
    ensure_dir(dst_path.parent)

    try:
        shutil.move(src, dst)
        Console.print(f"移动: {src} -> {dst}")
    except Exception as e:  # noqa: BLE001
        Console.print(f"移动失败: {src} -> {dst}, 错误: {e}")


def get_name_without_ext(filename: str) -> str:
    """获取文件名（不含扩展名）."""
    return Path(filename).stem


def is_image_file(filename: str) -> bool:
    """判断是否为图片文件."""
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


# TODO: RuffC901: `organize_files` is too complex (13 > 10)
def organize_files(selected_items: Iterable[str], current_dir: str | None = None) -> None:
    """
    组织文件的主要逻辑.

    Args:
        selected_items: 选中的文件/目录列表
        current_dir: 当前目录（当没有选中项时使用）
    """
    selected_items_list = list(selected_items)
    if not selected_items_list:
        # 没有选中文件，在当前目录创建文件夹
        if not current_dir:
            Console.print("错误: 没有选中文件且未提供当前目录")
            return

        current_path = Path(current_dir)
        ensure_dir(current_path / "main_assets")
        ensure_dir(current_path / "thumbnail")
        Console.print(f"在 {current_dir} 创建了 main_assets 和 thumbnail 目录")

    elif len(selected_items_list) == 1:
        # 单个文件
        file_path = Path(selected_items_list[0])
        if not file_path.exists():
            Console.print(f"错误: 文件不存在 {file_path}")
            return

        if file_path.is_file():
            parent_dir = file_path.parent
            filename = file_path.name

            # 创建目录
            ensure_dir(parent_dir / "main_assets")
            ensure_dir(parent_dir / "thumbnail")

            # 移动文件到 main_assets
            dst_path = parent_dir / "main_assets" / filename
            fast_move(str(file_path), str(dst_path))
        else:
            Console.print(f"跳过目录: {file_path}")

    else:
        # 多个文件 - 按文件名（无扩展名）分组
        groups: dict[str, list[Path]] = defaultdict(list)

        for item in selected_items_list:
            item_path = Path(item)
            if not item_path.exists():
                Console.print(f"警告: 文件不存在 {item_path}")
                continue

            if item_path.is_file():
                name_no_ext = get_name_without_ext(item_path.name)
                groups[name_no_ext].append(item_path)
            else:
                Console.print(f"跳过目录: {item_path}")

        # 处理每个分组
        for name_no_ext, files in groups.items():
            if not files:
                continue

            # 使用第一个文件的目录作为基础目录
            base_dir = files[0].parent
            new_dir = base_dir / name_no_ext

            # 创建目录结构
            ensure_dir(new_dir / "main_assets")
            ensure_dir(new_dir / "thumbnail")

            Console.print(f"处理分组: {name_no_ext}")

            # 移动文件
            for file_path in files:
                filename = file_path.name

                if is_image_file(filename):
                    # 图片文件移动到 thumbnail
                    dst_path = new_dir / "thumbnail" / filename
                else:
                    # 其他文件移动到 main_assets
                    dst_path = new_dir / "main_assets" / filename

                fast_move(str(file_path), str(dst_path))


def move_file_with_check(src_file: Path, dst_dir: Path) -> None:
    """move_file_with_check."""
    dst_file = dst_dir / src_file.name

    if dst_file.exists():
        if src_file.stat().st_size == dst_file.stat().st_size:
            Console.print(f"⚠️ 同名文件大小相同，删除源文件: {src_file}")
            src_file.unlink()
        else:
            base = src_file.stem
            ext = src_file.suffix
            i = 1
            while True:
                new_name = f"{base}_{i}{ext}"
                new_dst = dst_dir / new_name
                if not new_dst.exists():
                    Console.print(f"⚠️ 同名文件大小不同，重命名为: {new_dst}")
                    shutil.move(str(src_file), str(new_dst))
                    break
                i += 1
    else:
        shutil.move(str(src_file), str(dst_file))
        Console.print(f"移动文件: {src_file.name}")


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
                Console.print(f"⚠️ 已存在同名目录: {target_sub} -> 合并中")
                merge_directories(sub_dir, target_sub)
            else:
                shutil.move(str(sub_dir), str(target_sub))
                Console.print(f"移动目录: {sub_dir.name}")

    # 清理空目录
    if not any(src_dir.iterdir()):
        src_dir.rmdir()
        Console.print(f"🗑️ 删除空目录: {src_dir}")


def fix_duplicate_named_dirs(path: Path) -> None:
    """fix_duplicate_named_dirs."""
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and dir.parent.name == dir.name:
            Console.print(f"发现重复目录: {dir}")
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
            Console.print(f"✅ 解压完成: {file.name}")
            file.unlink()
            Console.print(f"🗑️ 已删除压缩包: {file}")
        else:
            Console.print(f"❌ 解压失败: {file}")
            Console.print(result.stderr)
    except Exception as e:  # noqa: BLE001
        Console.print(f"❌ 异常解压: {file} - {e}")


def _find_archive_files(path: Path) -> list[Path]:
    return [f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in COMPRESS_EXTENSIONS]


def _extract_round(path: Path) -> int:
    """执行一轮解压，返回本轮解压的压缩包数量."""
    archive_files = _find_archive_files(path)
    if not archive_files:
        return 0

    Console.print(f"共找到 {len(archive_files)} 个压缩包，开始多线程解压...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        list(executor.map(extract_file, archive_files))
    return len(archive_files)


def delete_useless_files_and_dirs(path: Path) -> None:
    """删除无用文件."""
    # 删除所有 __MACOSX 文件夹
    for dir in path.rglob("*"):
        if dir.is_dir() and dir.name == "__MACOSX":
            Console.print(f"🗑️ 删除无用目录: {dir}")
            shutil.rmtree(dir, ignore_errors=True)

    # 删除所有 ._Thumbs.db 文件
    for file in path.rglob("._Thumbs.db"):
        Console.print(f"🗑️ 删除无用文件: {file}")
        file.unlink(missing_ok=True)


def delete_empty_dirs(path: Path) -> None:
    """删除空目录."""
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and not any(dir.iterdir()):
            Console.print(f"🗑️ 删除空目录: {dir}")
            dir.rmdir()


@app.command()
def extract(path: str) -> None:
    """多轮解压目录中的所有压缩文件，并在最后整理."""
    target = Path(path)
    Console.print("📦 开始批量解压...")

    total_round = 0
    total_archives = 0
    while True:
        extracted = _extract_round(target)
        if extracted == 0:
            break
        total_round += 1
        total_archives += extracted
        # 解压一轮后，可能产生新的压缩包，继续下一轮

    Console.print(f"📦 解压完成，共 {total_round} 轮，处理压缩包 {total_archives} 个")
    # 解压出来的文件可能会嵌套相同的文件夹名称、空文件夹等，所以要整理
    arrange(path)


@app.command()
def arrange(path: str) -> None:
    """整理目录."""
    path_ = Path(path)
    Console.print("🧹 开始清理无用文件...")
    delete_useless_files_and_dirs(path_)
    Console.print("📁 合并重复目录...")
    fix_duplicate_named_dirs(path_)
    delete_empty_dirs(path_)
    Console.print("✅ 所有操作已完成")


@app.command()
def categorize(paths: list[Path] = typer.Argument(None)) -> None:
    r"""用于快速将素材分类到 main_assets 和 thumbnail 目录中.

    被 categorization.bat 调用 接收单个文件或多个文件。

    当接收单个文件时:
    1.在当前文件夹下创建 main_assets 和 thumbnail 两个目录
    2.将文件移动到 main_assets 下

    当接收多个文件时：
    1.将所有选中的文件以文件名相同但扩展名不同两两分组，假设选中的文件为：
    D:\\foo\\bar.png
    D:\\foo\\bar.zprj
    D:\\foo\\aaa.zprj
    应分组为：
    组一：
    D:\\foo\\bar.png
    D:\\foo\\bar.zprj
    组二：
    D:\\foo\\aaa.zprj
    2.为每个分组创建一个目录，如上述分组应创建 D:\\foo\\bar 和 D:\\foo\\aaa 两个目录
    3.在每个新目录中创建main_assets和thumbnails两个目录
    4.将每个分组中的图片文件移动到thumbnails目录中，将其他文件移动到main_assets目录中
    """
    # Typer 会在没有传参时传入 None
    selected = [str(p) for p in paths] if paths is not None else []
    organize_files(selected, current_dir=None)
