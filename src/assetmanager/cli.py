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
from pathlib import Path
from PIL import Image
import subprocess
from long_sword.eagle import Eagle

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

        return [
            f for f in path.rglob("*")
            if (
                f.is_file()
                and f.suffix.lower() in COMPRESS_EXTENSIONS
                and "__MACOSX" not in f.parts
            )
        ]

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
    r"""用于快速将素材分类到 main_assets 和 thumbnail 目录中.

    被 categorization.bat 调用 接收单个文件/多个文件/单个文件夹

    当接收单个文件时:
    1.在当前文件夹下创建 main_assets 、 thumbnail 和 main_assets_others 三个目录
    2.视文扩展名将文件移动到 main_assets 或 thumbnail 下

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

    当接收单个文件夹时：
    将文件夹中的所有文件视为多文件处理，主要是为了绕开windows向.cmd文件传递参数长度有限制的问题
    """
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
    """
    验证目录结构并按问题类型分类返回.

    规则概述：
    - 非特殊目录（非 main_assets/thumbnail/main_assets_others）：
      - 不允许直接包含文件（文件应放入 main_assets 或 thumbnail 或 main_assets_others）
      - 若包含了 main_assets 或 thumbnail，必须严格且仅包含这两个子目录，（可选包含main_assets_others）
      - 若无任何子目录（叶子目录），则应包含上述两个子目录（可选包含main_assets_others）（否则判为缺失）
    - 特殊目录：
      - main_assets/thumbnail 不允许包含子目录
      - main_assets 必须且仅能包含 1 个文件
      - thumbnail 仅允许 1 个文件
      - main_assets_others 可选且可包含多个文件
    返回：问题分类到目录列表的映射
    """

    root = Path(path)
    VIDEO_EXTENSIONS = {".mp4", ".srt", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
    videos = [f for f in root.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS]
    for video in videos:
        console.print(f"❌ 目录中存在视频文件: {video}")
    report = validate_structure(root)
    console.print(report)

@app.command()
def compress(root: Path) -> None:
    """压缩 main_assets 文件夹中的内容（不包含文件夹本身）."""
    # TODO：历史遗留代码。现添加了 main_assets_others 目录，考虑还要不要压缩
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

@app.command()
def merge_images(paths: list[Path] = typer.Argument(None)) -> None:
    """合并 main_assets 文件夹中的图片文件为一个图片文件."""
    from .merge_images import create_thumbnail_montage
    create_thumbnail_montage(paths)

@app.command()
def set_private_images(path: Path) -> None:
    """
    遍历文件夹中的所有图片
    对每张图片，生成缩略图
    将原图用7zip压缩为7z格式，放到 原图片名/main_assets中
    将缩略图放到 原图片名/thumbnail 中
    将原图片删除
    """
    # 支持的图片格式
    from .file_organizer import is_image_file

    image_files = [
        p for p in path.rglob("*")
        if is_image_file(str(p)) and "thumbnail" not in p.parts and "main_assets" not in p.parts
    ]

    for img_path in image_files:
        if not is_image_file(str(img_path)):
            continue

        print(f"Processing: {img_path.name}")

        # 创建相关文件夹
        base_name = img_path.stem
        main_assets_dir = img_path.parent / base_name / "main_assets"
        thumbnail_dir = img_path.parent / base_name / "thumbnail"
        main_assets_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)

        # 生成缩略图
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                aspect_ratio = width / height

                # 根据图片方向设置缩放尺寸
                if aspect_ratio > 1:  # 横图
                    new_width = 512
                    new_height = int(512 / aspect_ratio)
                else:  # 竖图或方图
                    new_height = 512
                    new_width = int(512 * aspect_ratio)

                img.thumbnail((new_width, new_height))
                thumbnail_path = thumbnail_dir / img_path.name
                img.save(thumbnail_path)
                print(f"Thumbnail saved to: {thumbnail_path}")
        except Exception as e:
            print(f"❌ Error creating thumbnail for {img_path}: {e}")
            continue

        # 压缩原图为 7z
        try:
            output_7z = main_assets_dir / f"{img_path.stem}.priv"
            subprocess.run(
                ["7z", "a", str(output_7z), str(img_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"Compressed to: {output_7z}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 7z compression failed for {img_path}: {e}")
            continue

        # 删除原图
        try:
            img_path.unlink()
            print(f"Deleted original: {img_path}")
        except Exception as e:
            print(f"❌ Error deleting {img_path}: {e}")

@app.command()
def git_init(folder: str) -> None:
    """在指定目录初始化 git 仓库"""
    eagle = Eagle()
    for path in eagle.list_items_path(folder):
        if not (path / ".git").exists():  # 检查是否是 git 仓库
            print(f"初始化 Git 仓库: {path}")
            try:
                subprocess.run(["git", "init"], cwd=path, check=True)
                subprocess.run(["git", "add", "-A"], cwd=path, check=True)
                subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True)
            except subprocess.CalledProcessError as e:
                print(f"⚠️ 初始化失败：{path}\n{e}")
        else:
            print(f"已是 Git 仓库: {path}")

# TODO: 在eagle以外为".zprj", ".zpac" 生成缩略图，不通过eagle生成
# GET_THUMBNAIL_SCRIPT_PATH = str(
#     Path(__file__) / "../../../src_eagle_plugin/thumbnail/get_thumbnail.ps1",
# )
# if folder.name == "main_assets":
#     thumbnail_folder = folder.parent / "thumbnail"
#     thumbnail = [f for f in thumbnail_folder.iterdir() if f.is_file()]
#     if len(thumbnail) <= 0:
#         main_file = next(
#             (f for f in folder.iterdir() if f.is_file() and f.suffix in {".zprj", ".zpac"}),
#             None,
#         )
#         if main_file:
#             console.print(f"为 {main_file} 生成thumbnail...")
#             result = subprocess.run([
#                 "pwsh.exe", "-File", GET_THUMBNAIL_SCRIPT_PATH,
#                 "-InputFile", str(main_file),
#                 "-OutputFile", str(thumbnail_folder / "thumbnail.png"),
#                 "-NoProfile", "-NoLogo",
#             ], check=False, capture_output=True, text=True)
#             if result.returncode == 0:
#                 print("✅ 生成成功:", result.stdout.strip())
#             else:
#                 print("❌ 生成失败:", result.stderr.strip())