import subprocess
from pathlib import Path


def convert_and_cleanup(root: Path) -> None:
    # 递归查找所有 .sppr 文件
    for sppr_file in root.rglob("*.sppr"):
        webp_file = Path(str(sppr_file.with_suffix(".webp")).replace("main_assets", "thumbnail"))
        png_file = Path(str(sppr_file.with_suffix(".png")).replace("main_assets", "thumbnail"))

        if webp_file.exists():
            try:
                # 调用 dwebp 进行转换
                subprocess.run(
                    ["dwebp", str(webp_file), "-o", str(png_file)],
                    check=True,
                )
                print(f"转换成功: {webp_file} -> {png_file}")

                # 删除原来的 .webp 文件
                webp_file.unlink()
                print(f"已删除: {webp_file}")
            except subprocess.CalledProcessError as e:
                print(f"转换失败: {webp_file}, 错误: {e}")
        else:
            print(f"未找到同名 .webp 文件: {sppr_file}")


if __name__ == "__main__":
    # 这里替换为你的目标目录，例如 Path("/path/to/dir")
    target_dir = Path(
        "F:\\eagle_librarys\\Illusion.library\\images\\MDR4DVA51K586.info\\SP材质大合集"
    )  # 当前目录
    convert_and_cleanup(target_dir)
