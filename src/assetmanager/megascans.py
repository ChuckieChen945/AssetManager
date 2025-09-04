from pathlib import Path


def validate_asset_path(path: Path):
    """
    验证资源目录结构是否符合规则：
    1. 如果当前目录只有文件：必须包含一个 `.json` 文件，和一个 `_preview.png` 结尾的文件
    2. 如果当前目录有子文件夹：不能有文件，且对子文件夹递归验证

    Args:
        path (Path): 要验证的目录路径

    Returns
    -------
        bool: 是否符合规则
    """
    if not path.is_dir():
        print(f"[ERROR] {path} 不是目录")
        return False

    files = [f for f in path.iterdir() if f.is_file()]
    dirs = [d for d in path.iterdir() if d.is_dir()]
    # TODO:改为只有一个 .json 和 只有一个_preview.png/jpeg/jpg 文件
    has_json = any(f.suffix == ".json" for f in files)
    has_preview_png = any(f.name.endswith("_preview.png") for f in files)

    # 情况1：模型、贴图、等都放一起
    if has_json and has_preview_png:
        if dirs == []:
            if not has_json:
                print(f"[ERROR] {path} 缺少 .json 文件")
                return False
            if not has_preview_png:
                print(f"[ERROR] {path} 缺少 '_preview.png' 文件")
                return False
            return True

    # 情况2：有子目录
    if files:
        print(f"[ERROR] {path} 存在文件（目录下有子文件夹时不允许有文件）")
        return False

    # 递归检查子目录
    for sub_dir in dirs:
        if not validate_asset_path(sub_dir):
            return False
    return True


if __name__ == "__main__":
    pathes = [
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\QUIXEL-第一部分\\资源库-\\3D",
        ######
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2020.3-2020.5更新\\3D",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2020.3-2020.5更新\\3dplant",
        ####
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2020.6-2020.12更新",
        #### 2021
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\1月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\2月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\3月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\4月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\5月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\6月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\7月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\8月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\9月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\10月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\11月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\12月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2021年更新\\植物部分",
        #### 2022
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\1月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\2月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\3月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\4月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\5月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\6月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\7月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\8月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\9月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\10月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\11月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\12月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2022年更新\\植物",
        #### 2023
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\1月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\2月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\3月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\4月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\5月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\6月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\7月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\8月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\9月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\10月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\11月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\12月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2023年更新\\植物",
        #### 2024
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\1月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\2月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\3月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\4月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\5月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\6月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\7月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\8月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\9月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\10月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\11月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\12月",
        "F:\\QUIXEL\\Quixel持续更新部分等多个文件\\Quixel持续更新部分\\Quixel Megascan素材库持续更新3D\\2024年更新\\植物",
    ]
    root_path = Path("path/to/your/assets")
    is_valid = validate_asset_path(root_path)
    print(f"目录验证结果: {is_valid}")
