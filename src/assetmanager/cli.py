"""AssetManager CLI."""

import requests
import concurrent.futures
import os
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Iterable
from multiprocessing import Pool, cpu_count
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer()

COMPRESS_EXTENSIONS = {".zip", ".7z", ".rar"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
GET_THUMBNAIL_SCRIPT_PATH = str(
    Path(__file__) / "../../../src_eagle_plugin/thumbnail/get_thumbnail.ps1",
)
VIDEO_EXTENSIONS = {".mp4", ".srt", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}


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
        console.print(f"移动: {src} -> {dst}")
    except Exception as e:  # noqa: BLE001
        console.print(f"移动失败: {src} -> {dst}, 错误: {e}")


def get_name_without_ext(filename: str) -> str:
    """获取文件名（不含扩展名）."""
    return Path(filename).stem


def is_image_file(filename: str) -> bool:
    """判断是否为图片文件."""
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def _ensure_asset_dirs(base_dir: Path) -> None:
    ensure_dir(base_dir / "main_assets")
    ensure_dir(base_dir / "thumbnail")


def _handle_no_selection(current_dir: str) -> None:
    current_path = Path(current_dir)
    _ensure_asset_dirs(current_path)
    console.print(f"在 {current_dir} 创建了 main_assets 和 thumbnail 目录")


def _handle_single_path(file_path: Path) -> None:
    if not file_path.exists():
        console.print(f"错误: 文件不存在 {file_path}")
        return

    if file_path.is_file():
        parent_dir = file_path.parent
        _ensure_asset_dirs(parent_dir)

        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            dst_path = parent_dir / "thumbnail" / file_path.name
        else:
            dst_path = parent_dir / "main_assets" / file_path.name
        fast_move(str(file_path), str(dst_path))

        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            # 将 parent_dir 下除 thumbnail 和 main_assets 以外的所有其它内容（包括文件和文件夹） 移到 main_assets 中
            for path in parent_dir.iterdir():
                if path.name not in {"thumbnail", "main_assets"}:
                    shutil.move(str(path), str(parent_dir / "main_assets" / path.name))

    else:
        console.print(f"跳过目录: {file_path}")


def _group_selected_files(selected_items_list: list[str]) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for item in selected_items_list:
        item_path = Path(item)
        if not item_path.exists():
            console.print(f"警告: 文件不存在 {item_path}")
            continue
        if item_path.is_file():
            name_no_ext = get_name_without_ext(item_path.name)
            groups[name_no_ext].append(item_path)
        else:
            console.print(f"跳过目录: {item_path}")
    return groups


def _handle_multiple(selected_items_list: list[str]) -> None:
    groups = _group_selected_files(selected_items_list)

    for name_no_ext, files in groups.items():
        if not files:
            continue

        base_dir = files[0].parent
        new_dir = base_dir / name_no_ext.strip()

        _ensure_asset_dirs(new_dir)
        console.print(f"处理分组: {name_no_ext}")

        for file_path in files:
            filename = file_path.name
            if is_image_file(filename):
                dst_path = new_dir / "thumbnail" / filename
            else:
                dst_path = new_dir / "main_assets" / filename
            fast_move(str(file_path), str(dst_path))


def organize_files(selected_items: Iterable[str]) -> None:
    """
    组织文件的主要逻辑.

    Args:
        selected_items: 选中的文件/目录列表
        current_dir: 当前目录（当没有选中项时使用）
    """
    selected_items_list = list(selected_items) if selected_items is not None else []

    if not selected_items_list:
        return
    if len(selected_items_list) == 1:
        _handle_single_path(Path(selected_items_list[0]))
        return

    _handle_multiple(selected_items_list)


def move_file_with_check(src_file: Path, dst_dir: Path) -> None:
    """move_file_with_check."""
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
                console.print(f"⚠️ 已存在同名目录: {target_sub} -> 合并中")
                merge_directories(sub_dir, target_sub)
            else:
                shutil.move(str(sub_dir), str(target_sub))
                console.print(f"移动目录: {sub_dir.name}")

    # 清理空目录
    if not any(src_dir.iterdir()):
        src_dir.rmdir()
        console.print(f"🗑️ 删除空目录: {src_dir}")


def fix_duplicate_named_dirs(path: Path) -> None:
    """fix_duplicate_named_dirs."""
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and dir.parent.name == dir.name:
            console.print(f"发现重复目录: {dir}")
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
            console.print(f"✅ 解压完成: {file.name}")
            file.unlink()
            console.print(f"🗑️ 已删除压缩包: {file}")
        else:
            console.print(f"❌ 解压失败: {file}")
            console.print(result.stderr)
    except Exception as e:  # noqa: BLE001
        console.print(f"❌ 异常解压: {file} - {e}")


def _find_archive_files(path: Path) -> list[Path]:
    return [f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in COMPRESS_EXTENSIONS]


def _extract_round(path: Path) -> int:
    """执行一轮解压，返回本轮解压的压缩包数量."""
    archive_files = _find_archive_files(path)
    if not archive_files:
        return 0

    console.print(f"共找到 {len(archive_files)} 个压缩包，开始多线程解压...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        list(executor.map(extract_file, archive_files))
    return len(archive_files)


def delete_useless_files_and_dirs(path: Path) -> None:
    """删除无用文件."""
    # 删除所有 __MACOSX 文件夹
    for dir in path.rglob("*"):
        if dir.is_dir() and (dir.name == "__MACOSX" or dir.name == ".alg_meta"):
            console.print(f"🗑️ 删除无用目录: {dir}")
            shutil.rmtree(dir, ignore_errors=True)

    # 删除所有 ._Thumbs.db 文件
    for file in path.rglob("._Thumbs.db"):
        console.print(f"🗑️ 删除无用文件: {file}")
        file.unlink(missing_ok=True)

    # 删除所有 .DS_Store 文件
    for file in path.rglob(".DS_Store"):
        console.print(f"🗑️ 删除无用文件: {file}")
        file.unlink(missing_ok=True)


def delete_empty_dirs(path: Path) -> None:
    """删除空目录."""
    for dir in sorted(path.rglob("*"), reverse=True):
        if dir.is_dir() and not any(dir.iterdir()):
            console.print(f"🗑️ 删除空目录: {dir}")
            dir.rmdir()


@app.command()
def extract(path: str) -> None:
    """多轮解压目录中的所有压缩文件，并在最后整理."""
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
        # 解压一轮后，可能产生新的压缩包，继续下一轮

    console.print(f"📦 解压完成，共 {total_round} 轮，处理压缩包 {total_archives} 个")
    # 解压出来的文件可能会嵌套相同的文件夹名称、空文件夹等，所以要整理
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
    selected = paths if paths is not None else []

    # 判断传入的路径是目录还是文件
    dirs = [p for p in selected if p.is_dir()]
    files = [p for p in selected if p.is_file()]

    if dirs and not files:
        # 一次只能有一个path
        dir_path = Path(dirs[0])  # 假设 dirs[0] 是你目标目录路径
        # 列出目录中所有文件（不包括子目录）
        files_in_dir = [p for p in dir_path.iterdir() if p.is_file()]
        organize_files(selected_items=files_in_dir)
    else:
        # 只有文件
        organize_files(selected_items=files)


@app.callback()
def _root_callback(name: str = typer.Option(None, "--name", help="Echo helper")) -> None:
    """Root callback to keep backward-compat tests happy."""
    if name:
        console.print(name)


def validate_structure(root: Path) -> dict[str, list[Path]]:
    """
    验证目录结构并按问题类型分类返回.

    规则概述：
    - 非特殊目录（非 main_assets/thumbnail）：
      - 不允许直接包含文件（文件应放入 main_assets 或 thumbnail）
      - 若包含了 main_assets 或 thumbnail，必须严格且仅包含这两个子目录
      - 若无任何子目录（叶子目录），则应包含上述两个子目录（否则判为缺失）
    - 特殊目录：
      - main_assets/thumbnail 不允许包含子目录
      - main_assets 必须且仅能包含 1 个文件
      - thumbnail 仅允许 1 个文件
    返回：问题分类到目录列表的映射
    """
    categories: dict[str, list[Path]] = {
        # 特殊目录问题
        "main_assets_has_subdirs": [],
        "main_assets_multiple_files": [],
        "main_assets_empty": [],
        "thumbnail_has_subdirs": [],
        "thumbnail_multiple_files": [],
        # 非特殊目录问题
        "container_has_extra_files": [],
        "incorrect_special_structure": [],
        "leaf_missing_special": [],
    }

    def _is_under_directory(path: Path, ancestor_dir_name: str) -> bool:
        """判断 path 是否位于名为 ancestor_dir_name 的祖先目录之下（不含自身）。"""
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
                    None,  # 如果没有匹配到，返回 None
                )
                if main_file:
                    console.print(f"为 {main_file} 生成thumbnail...")
                    result = subprocess.run(
                        [
                            "pwsh.exe",
                            "-File",
                            GET_THUMBNAIL_SCRIPT_PATH,
                            "-InputFile",
                            str(main_file),
                            "-OutputFile",
                            str(thumbnail_folder / "thumbnail.png"),
                            "-NoProfile",
                            "-NoLogo",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        print("✅ 生成成功:", result.stdout.strip())
                    else:
                        print("❌ 生成失败:", result.stderr.strip())

        if folder.name in {"main_assets", "thumbnail"}:
            # 特殊目录校验
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

        # 非特殊目录校验
        # 若该目录在 main_assets 中，则 忽略
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


def _to_file_uri(p: Path) -> str:
    # 使用 Path.as_uri 生成带百分号编码的 file:/// 链接，保证可点击
    return p.resolve().as_uri()


@app.command()
def validate(path: str) -> None:
    """验证目录结构是否符合要求（分类输出，带可点击路径）。"""
    root = Path(path)
    # 查找root下是否有 .mp4 文件或 .srt 字幕文件
    videos = [f for f in root.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS]
    for video in videos:
        console.print(f"❌ 目录中存在视频文件: {video}")
    report = validate_structure(root)

    # 严重级别分类
    warning_keys: set[str] = {"main_assets_has_subdirs"}
    error_keys: set[str] = {
        "main_assets_multiple_files",
        "main_assets_empty",
        "thumbnail_has_subdirs",
        "thumbnail_multiple_files",
        "container_has_extra_files",
        "incorrect_special_structure",
        "leaf_missing_special",
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

    # 友好标签
    labels: list[tuple[str, str]] = [
        ("main_assets_has_subdirs", "main_assets 中存在子目录（警告）"),
        ("main_assets_multiple_files", "main_assets 中有多个文件"),
        ("main_assets_empty", "main_assets 中没有文件"),
        ("thumbnail_has_subdirs", "thumbnail 中存在子目录"),
        ("thumbnail_multiple_files", "thumbnail 中有多个文件"),
        ("container_has_extra_files", "非特殊目录中包含多余文件"),
        ("incorrect_special_structure", "目录包含 main_assets/thumbnail 但结构不正确"),
        ("leaf_missing_special", "叶子目录缺少 main_assets/thumbnail 子目录"),
    ]

    # 概览表（错误/警告计数）
    summary_table = Table(show_header=True, header_style="bold")
    summary_table.add_column("级别", style="bold")
    summary_table.add_column("数量", justify="right")
    summary_table.add_row("错误", str(num_errors))
    summary_table.add_row("警告", str(num_warnings))
    console.print(summary_table)

    # 逐类详情（仅展示有数据的类别）
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


# ===== 常量配置 =====
ARCHIVE_SUFFIX = ".7z"
ARCHIVE_LEVEL = "-mx=9"
TARGET_FOLDER_NAME = "main_assets"


def log(message: str) -> None:
    """统一日志输出"""
    print(message)


def should_compress(folder: Path) -> bool:
    """判断是否需要压缩该目录"""
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
    """压缩 main_assets 文件夹中的内容（不包含文件夹本身）"""
    if not should_compress(folder):
        return

    zip_name = folder / f"{folder.parent.name}{ARCHIVE_SUFFIX}"
    content_to_compress = [str(item) for item in folder.iterdir()]

    log(f"[压缩中] {folder}")

    try:
        result = subprocess.run(
            [
                "7z",
                "a",
                str(zip_name),
                *content_to_compress,
                "-r",
                ARCHIVE_LEVEL,
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            log(f"[失败] 压缩失败：{folder}\n错误信息：{result.stderr}")
            return

        log(f"[成功] 压缩完成：{zip_name}")
        _cleanup_original_files(folder, zip_name)

    except Exception as e:
        log(f"[异常] 压缩异常：{folder}，原因：{e}")


def _cleanup_original_files(folder: Path, zip_file: Path) -> None:
    """清空压缩前的原始内容（保留压缩包和空文件夹）"""
    try:
        for item in folder.iterdir():
            if item.resolve() == zip_file.resolve():
                continue  # 跳过压缩包自身
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        log(f"[清理完成] 已清空原始内容：{folder}")
    except Exception as e:
        log(f"[清理失败] {folder}，原因：{e}")


def process(root: Path) -> None:
    """扫描根目录，查找并处理所有 main_assets 文件夹"""
    folders = [f for f in root.rglob(TARGET_FOLDER_NAME) if f.is_dir()]

    if not folders:
        log("[信息] 未找到任何 main_assets 文件夹。")
        return

    log(f"[发现] 共找到 {len(folders)} 个 main_assets 文件夹，开始处理...")
    # with Pool(processes=int(cpu_count() / 2)) as pool:
    with Pool(processes=3) as pool:
        pool.map(compress_folder, folders)


@app.command()
def compress(root: Path) -> None:
    """压缩 main_assets 文件夹中的内容（不包含文件夹本身）."""
    process(root)

# Eagle API 本地默认地址
BASE_URL = "http://localhost:41595/api"

# 目标文件夹 ID
TRASH_FOLDER_ID = "MFDVSSH14GC83"

# 本地 Eagle library 路径
LIBRARY_PATH = Path(r"F:\eagle_librarys\Illusion.library\images")

def list_items_in_folder(folder_id):
    """从 Eagle API 获取指定文件夹的所有项目"""
    url = f"{BASE_URL}/item/list"
    params = {
        "folders": folder_id,
        "limit": 10000,   # 如果项目超过 1000，需要做分页
        "offset": 0
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if data.get("status") == "success":
        return data.get("data", [])
    else:
        raise RuntimeError(f"API 返回错误: {data}")

def check_item_files(items):
    """检查每个 item 的 .info 文件夹下的文件数"""
    problems = []
    for item in items:
        item_id = item.get("id")
        info_dir = LIBRARY_PATH / f"{item_id}.info"

        if not info_dir.exists():
            problems.append((item_id, "目录不存在"))
            continue

        if not info_dir.is_dir():
            problems.append((item_id, "不是目录"))
            continue

        try:
            # TODO: 更严格的验证
            files = list(info_dir.iterdir())
            file_count = len(files)
            if file_count != 3:
                problems.append((item_id, f"{file_count} 个文件"))
        except Exception as e:
            problems.append((item_id, f"读取失败: {e}"))

    return problems

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
