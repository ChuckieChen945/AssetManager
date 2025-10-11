"""
将houdini2chat的py脚本喂给AI，生成markdown解释文本
"""

import logging
import os
from pathlib import Path
from time import sleep

from long_sword.openai_customized import ask_openai
from long_sword.eagle import Eagle

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def process_file(filepath: Path) -> None:
    """
    处理单个 Python 文件
    """

    md_filepath = filepath.with_suffix(".md")
    if md_filepath.exists():
        return
    # 读取文件内容
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return

    prompt = f"""
解释houdini节点网格：
{data}
"""
    result = ""
    for i in range(3):
        result = ask_openai(prompt)
        if result:
            break
        sleep(0.5)

    if not result:
        logger.error(f"OpenAI API 调用失败，跳过: {filepath}")
        return

    # 将数据写回同名 的 .md 文件
    try:
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(result)
            logger.info(f"写入文件成功: {md_filepath}")
    except Exception as e:
        logger.error(f"写入文件失败: {e}")


def main() -> None:
    folder_id = "METEXKIEN5Q7P" # houdini folder
    # folder_id = "ME2U2JT8S0WU8" # temp folder
    eagle = Eagle()
    paths = eagle.list_items_path(folder_id)
    for path in paths:
        for py_file in path.rglob("*.py"):
            logger.info(f"=Processing file: {py_file}")
            process_file(py_file)
            sleep(0.1)


if __name__ == "__main__":
    main()
