"""AssetManager CLI."""

import typer
from rich.console import Console
from pathlib import Path
from .file_organizer import organize_files
from .structure_validator import (
    validate_structure, fix_duplicate_named_dirs, delete_useless_files_and_dirs, delete_empty_dirs
)
from .compressor import process as compress_main_assets
from .eagle_api import list_items_in_folder, check_item_files, TRASH_FOLDER_ID

console = Console()
app = typer.Typer()

@app.command()
def extract(path: str) -> None:
    """多轮解压目录中的所有压缩文件，并在最后整理."""
    from .structure_validator import delete_useless_files_and_dirs, fix_duplicate_named_dirs, delete_empty_dirs
    import os, concurrent.futures, subprocess
    from pathlib import Path
    COMPRESS_EXTENSIONS = {".zip", ".7z", ".rar"}
    def _find_archive_files(path: Path):
        return [f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in COMPRESS_EXTENSIONS]
    def extract_file(file: Path):
        out_dir = file.with_name(file.stem)
        if not out_dir.exists():
            out_dir.mkdir(parents=True)
        try:
            result = subprocess.run([
                "7z", "x", "-y", str(file), f"-o{out_dir!s}"],
                check=False, capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"✅ 解压完成: {file.name}")
                file.unlink()
                console.print(f"🗑️ 已删除压缩包: {file}")
            else:
                console.print(f"❌ 解压失败: {file}")
                console.print(result.stderr)
        except Exception as e:
            console.print(f"❌ 异常解压: {file} - {e}")
    def _extract_round(path: Path) -> int:
        archive_files = _find_archive_files(path)
        if not archive_files:
            return 0
        console.print(f"共找到 {len(archive_files)} 个压缩包，开始多线程解压...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            list(executor.map(extract_file, archive_files))
        return len(archive_files)
    target = Path(path)
    console.print("📦 开始批量解压...")
    total_round = 0
    total_archives = 0
    while True:
        extracted = _extract_round(target)
        if extracted == 0:
            break
        total_round += 1
        total_archives += extracted
    console.print(f"📦 解压完成，共 {total_round} 轮，处理压缩包 {total_archives} 个")
    arrange(path)

@app.command()
def arrange(path: str) -> None:
    """整理目录."""
    path_ = Path(path)
    console.print("🧹 开始清理无用文件...")
    delete_useless_files_and_dirs(path_)
    console.print("📁 合并重复目录...")
    fix_duplicate_named_dirs(path_)
    delete_empty_dirs(path_)
    console.print("✅ 所有操作已完成")

@app.command()
def categorize(paths: list[Path] = typer.Argument(None)) -> None:
    """用于快速将素材分类到 main_assets 和 thumbnail 目录中."""
    selected = paths if paths is not None else []
    dirs = [p for p in selected if p.is_dir()]
    files = [p for p in selected if p.is_file()]
    if dirs and not files:
        dir_path = Path(dirs[0])
        files_in_dir = [str(p) for p in dir_path.iterdir() if p.is_file()]
        organize_files(selected_items=files_in_dir)
    else:
        organize_files(selected_items=[str(p) for p in files])

@app.command()
def validate(path: str) -> None:
    """验证目录结构是否符合要求（分类输出，带可点击路径）。"""
    from rich.table import Table
    root = Path(path)
    VIDEO_EXTENSIONS = {".mp4", ".srt", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
    videos = [f for f in root.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS]
    for video in videos:
        console.print(f"❌ 目录中存在视频文件: {video}")
    report = validate_structure(root)
    warning_keys = {"main_assets_has_subdirs"}
    error_keys = {
        "main_assets_multiple_files", "main_assets_empty", "thumbnail_has_subdirs", "thumbnail_multiple_files",
        "container_has_extra_files", "incorrect_special_structure", "leaf_missing_special"
    }
    num_errors = sum(len(report.get(k, [])) for k in error_keys)
    num_warnings = sum(len(report.get(k, [])) for k in warning_keys)
    if num_errors == 0 and num_warnings == 0:
        console.print("✅ 所有终端目录均符合要求")
        return
    if num_errors > 0:
        console.print("❌ 验证未通过（存在错误）")
    else:
        console.print("⚠️ 验证通过但存在警告")
    labels = [
        ("main_assets_has_subdirs", "main_assets 中存在子目录（警告）"),
        ("main_assets_multiple_files", "main_assets 中有多个文件"),
        ("main_assets_empty", "main_assets 中没有文件"),
        ("thumbnail_has_subdirs", "thumbnail 中存在子目录"),
        ("thumbnail_multiple_files", "thumbnail 中有多个文件"),
        ("container_has_extra_files", "非特殊目录中包含多余文件"),
        ("incorrect_special_structure", "目录包含 main_assets/thumbnail 但结构不正确"),
        ("leaf_missing_special", "叶子目录缺少 main_assets/thumbnail 子目录"),
    ]
    summary_table = Table(show_header=True, header_style="bold")
    summary_table.add_column("级别", style="bold")
    summary_table.add_column("数量", justify="right")
    summary_table.add_row("错误", str(num_errors))
    summary_table.add_row("警告", str(num_warnings))
    console.print(summary_table)
    def _to_file_uri(p: Path) -> str:
        return p.resolve().as_uri()
    for key, title in labels:
        paths = sorted(report.get(key, []))
        if not paths:
            continue
        level = "警告" if key in warning_keys else "错误"
        table = Table(show_header=True, header_style="bold")
        table.title = f"{title}（{level}）: {len(paths)}"
        table.add_column("原始路径")
        table.add_column("可点击链接（file:///）")
        for p in paths:
            raw_path = str(p.resolve())
            uri = _to_file_uri(p)
            table.add_row(raw_path, f"[link={uri}]{uri}[/link]")
        console.print(table)

@app.command()
def compress(root: Path) -> None:
    """压缩 main_assets 文件夹中的内容（不包含文件夹本身）."""
    compress_main_assets(root)

@app.command()
def validate_trash_items():
    """验证回收站目录下的项目文件夹中除了eagle本身的文件外，是否还有其它文件"""
    items = list_items_in_folder(TRASH_FOLDER_ID)
    problems = check_item_files(items)
    if problems:
        print("以下项目不符合要求：")
        for item_id, issue in problems:
            print(f"- {item_id}: {issue}")
    else:
        print("✅ 验证通过，所有目录都有 3 个文件")

@app.callback()
def _root_callback(name: str = typer.Option(None, "--name", help="Echo helper")) -> None:
    if name:
        console.print(name)
