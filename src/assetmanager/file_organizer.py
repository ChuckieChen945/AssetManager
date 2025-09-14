import shutil
from collections import defaultdict
from pathlib import Path

from rich.console import Console

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
console = Console()


def ensure_dir(path: Path | str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def get_name_without_ext(filename: str) -> str:
    return Path(filename).stem


def is_image_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def organize_files(selected_items: list[str]) -> None:
    selected_items_list = list(selected_items) if selected_items is not None else []
    if not selected_items_list:
        return
    if len(selected_items_list) == 1:
        _handle_single_path(Path(selected_items_list[0]))
        return
    _handle_multiple(selected_items_list)


def _handle_single_path(file_path: Path) -> None:
    if not file_path.exists():
        console.print(f"错误: 文件不存在 {file_path}")
        return
    if file_path.suffix.lower() in IMAGE_EXTENSIONS:
        raise ValueError("单个文件时，不能是图片文件")

    if file_path.is_file():
        parent_dir = file_path.parent
        _ensure_asset_dirs(parent_dir)
        dst_path = parent_dir / "main_assets" / file_path.name
        fast_move(str(file_path), str(dst_path))
        # 如果parent_dir直接子文件下只有一张图片，把它移动到thumbnail
        image_files = [p for p in parent_dir.iterdir() if p.is_file() and is_image_file(p.name)]
        if len(image_files) == 1:  # 只有一张图片
            img_file = image_files[0]
            dst_img_path = parent_dir / "thumbnail" / img_file.name
            fast_move(str(img_file), str(dst_img_path))
        # 把除了 main_assets 和 thumbnail 以外的文件及文件夹都移动到 main_assets
        for p in parent_dir.iterdir():
            if p.name not in {"main_assets", "thumbnail", "main_assets_others"}:
                dst_other_path = parent_dir / "main_assets_others" / p.name
                fast_move(str(p), str(dst_other_path))

    else:
        console.print(f"跳过目录: {file_path}")


def _ensure_asset_dirs(base_dir: Path) -> None:
    ensure_dir(base_dir / "main_assets")
    ensure_dir(base_dir / "thumbnail")
    ensure_dir(base_dir / "main_assets_others")


def fast_move(src: str, dst: str) -> None:
    dst_path = Path(dst)
    ensure_dir(dst_path.parent)
    try:
        shutil.move(src, dst)
        console.print(f"移动: {src} -> {dst}")
    except Exception as e:
        console.print(f"移动失败: {src} -> {dst}, 错误: {e}")


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
