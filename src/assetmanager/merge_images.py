from pathlib import Path
from math import floor, sqrt
from subprocess import run
from datetime import datetime
from typing import List
import tempfile
import shutil

def create_thumbnail_montage(image_paths: List[Path], output_dir: str = ".", tmp_dir: str | None = None):
    """
    使用 ImageMagick 将一组图片拼成缩略图蒙太奇。

    image_paths: 图片文件路径列表
    output_dir: 输出目录
    tmp_dir: 临时文件目录，默认自动创建
    """

    if not image_paths:
        raise ValueError("请提供至少一张图片路径。")

    # 临时目录
    if tmp_dir is None:
        tmp_dir_obj = Path(tempfile.mkdtemp())
    else:
        tmp_dir_obj = Path(tmp_dir)
        tmp_dir_obj.mkdir(parents=True, exist_ok=True)

    filelist = []
    count = 0

    try:
        for img_path in image_paths:
            count += 1
            # 获取图片尺寸
            result = run(
                ["magick", "identify", "-format", "%w %h", str(img_path)],
                capture_output=True, text=True
            )
            width, height = map(int, result.stdout.split())

            if width == 4096 and height == 4096:
                print(f"检测到大图：{img_path}，裁剪左上角 512x512")
                tmpfile = tmp_dir_obj / f"crop_{count}.png"
                run(["magick", "convert", str(img_path), "-crop", "512x512+0+0", "+repage", str(tmpfile)])
                filelist.append(tmpfile)
            else:
                filelist.append(img_path)

        # 计算列数
        cols = max(1, floor(sqrt(count)))

        # 输出文件名
        now = datetime.now()
        output_file = Path(output_dir) / f"montage_{now:%Y%m%d_%H%M%S}.jpg"

        # 调用 ImageMagick montage
        montage_cmd = ["montage", *map(str, filelist), "-geometry", "+0+0", "-tile", f"{cols}x", "-background", "none", str(output_file)]
        run(montage_cmd)

        print(f"拼图完成！输出文件：{output_file}")

    finally:
        # 清理临时目录（如果是自动创建的）
        if tmp_dir is None:
            shutil.rmtree(tmp_dir_obj)
