import json
import logging
from collections import deque
from pathlib import Path

from jsonschema import validate
from jsonschema.exceptions import ValidationError

# 配置日志，调试时可将 level 设置为 logging.DEBUG
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def directory_to_json(path: Path) -> dict:
    """
    递归地将文件夹结构转换为包含文件系统路径的 JSON 对象。

    Args:
        path: 要转换的目录或文件的 Path 对象。

    Returns
    -------
        一个表示文件或目录结构的字典。

    Raises
    ------
        FileNotFoundError: 如果提供的路径不存在。
    """
    logging.debug(f"正在处理路径: {path}")
    if not path.exists():
        logging.error(f"路径不存在: {path}")
        raise FileNotFoundError(f"路径 '{path}' 不存在。")

    # 在节点中包含绝对路径，以便于后续错误追溯
    node = {
        "name": path.name,
        "path": str(path.resolve()),  # 新增：记录节点的绝对路径
        "type": "directory" if path.is_dir() else "file",
    }

    if path.is_dir():
        node["children"] = []
        try:
            for child in sorted(path.iterdir(), key=lambda p: p.name):  # 排序以保证结果一致性
                node["children"].append(directory_to_json(child))
        except PermissionError as e:
            logging.warning(f"无权限访问路径，已跳过: {path}。错误信息: {e}")

    return node


def get_file_tree_schema() -> dict:
    """
    返回用于验证文件树结构的 JSON Schema。
    Schema 已更新，要求每个节点都包含 'path' 字段。
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "文件树结构 Schema",
        "description": "用于验证文件和目录层级结构的 JSON Schema，要求包含文件路径",
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "文件或目录名"},
            "path": {"type": "string", "description": "文件或目录的绝对路径"},
            "type": {"type": "string", "enum": ["directory", "file"]},
            "children": {
                "type": "array",
                "items": {"$ref": "#"},
                "description": "目录下的子节点列表",
            },
        },
        "required": ["name", "type", "path"],
        "if": {
            "properties": {"type": {"const": "directory"}},
        },
        "then": {
            "required": ["children"],
            "allOf": [
                {
                    "if": {
                        "properties": {
                            "children": {
                                "type": "array",
                                "minItems": 1,
                                "items": {"properties": {"type": {"const": "file"}}},
                            },
                        },
                    },
                    "then": {
                        "properties": {
                            "children": {
                                "minItems": 2,
                                "allOf": [
                                    {
                                        "contains": {
                                            "properties": {
                                                "name": {"pattern": r"^[^.\\/:*?\"<>|]+\.json$"},
                                                "type": {"const": "file"},
                                            },
                                            "required": ["name", "type", "path"],
                                        },
                                    },
                                    {
                                        "contains": {
                                            "properties": {
                                                "name": {
                                                    "pattern": r".*_[pP]review\.(png|jpeg|jpg)$"
                                                },
                                                "type": {"const": "file"},
                                            },
                                            "required": ["name", "type", "path"],
                                        },
                                    },
                                ],
                            },
                        },
                    },
                },
            ],
        },
    }
    return schema


def format_json_path(path_deque: deque) -> str:
    """将 jsonschema 的路径 deque 格式化为更易读的字符串。"""
    if not path_deque:
        return "(root)"
    return "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in path_deque).lstrip(".")


def find_error_node_path(json_data: dict, error_path: deque) -> str:
    """
    根据验证错误的路径，在 JSON 数据中找到对应节点并返回其文件系统路径。

    Args:
        json_data: 完整的文件树 JSON 数据。
        error_path: 来自 ValidationError 对象的路径队列 (e.g., deque(['children', 0, 'name'])).

    Returns
    -------
        出错节点对应的文件系统路径字符串，如果找不到则返回 '未知路径'。
    """
    current_node = json_data
    try:
        for key in error_path:
            current_node = current_node[key]
        # 如果路径指向一个属性而不是一个节点对象，回退到其父节点
        if not isinstance(current_node, dict):
            return find_error_node_path(json_data, deque(list(error_path)[:-1]))
        return current_node.get("path", "路径属性缺失")
    except (KeyError, IndexError, TypeError):
        # 如果路径中间断掉，尝试返回能找到的最后一个节点的路径
        if isinstance(current_node, dict) and "path" in current_node:
            return current_node["path"]
        return "未知路径（追溯中断）"


# 完成 TODO: 显示出错的文件夹路径
def print_validation_error(error: ValidationError, json_data: dict, indent: int = 0):
    """
    以更友好的格式打印验证错误，包含出错的文件/文件夹的实际路径。

    Args:
        error: ValidationError 对象。
        json_data: 被验证的完整 JSON 数据。
        indent: 打印缩进。
    """
    prefix = " " * indent
    json_path_str = format_json_path(error.path)

    # 查找并报告出错的实际文件/文件夹路径
    file_system_path = find_error_node_path(json_data, error.path)

    logging.error(f"{prefix}❌ 验证错误!")
    logging.error(f"{prefix}   - 错误信息: {error.message}")
    logging.error(f"{prefix}   - 关联路径: {file_system_path}")
    logging.error(f"{prefix}   - JSON 路径: {json_path_str}")
    logging.error(f"{prefix}   - 验证规则 (Schema Path): {list(error.schema_path)}")

    # 递归打印上下文中的子错误，以分析 'allOf' 或 'anyOf' 等复杂失败
    if error.context:
        logging.error(f"{prefix}   - 上下文子错误:")
        for suberror in sorted(error.context, key=lambda e: e.path):
            print_validation_error(suberror, json_data, indent + 4)


def validate_json_with_schema(json_data: dict, schema: dict) -> bool:
    """
    验证 JSON 数据是否符合给定 Schema，并在失败时打印详细错误信息。
    """
    try:
        validate(instance=json_data, schema=schema)
        logging.info("✅ 验证成功: JSON 数据符合 Schema 结构。")
        return True
    except ValidationError as e:
        logging.exception("❌ 验证失败: JSON 数据不符合 Schema 结构。")
        print_validation_error(e, json_data)  # 传入 json_data 以便追溯路径
        return False
    except Exception as e:
        logging.exception(f"发生未知错误: {e}")
        return False


def main():
    # --- 请将此路径修改为您要扫描的目标文件夹 ---
    # 使用 Path 对象并进行路径转换，提高跨平台兼容性
    target_directory = Path("F:/QUIXEL/Quixel持续更新部分等多个文件/QUIXEL-第一部分/资源库-/3D")

    if not target_directory.exists() or not target_directory.is_dir():
        logging.error(f"目标路径不是一个有效的目录或不存在: {target_directory}")
        return

    logging.info(f"--- (1/3) 开始扫描文件夹: {target_directory} ---")
    file_tree_json = directory_to_json(target_directory)

    # 可以在调试时取消注释，以查看生成的完整 JSON
    # logging.debug(json.dumps(file_tree_json, indent=2, ensure_ascii=False))

    logging.info("--- (2/3) 获取 JSON Schema ---")
    file_schema = get_file_tree_schema()

    logging.info("--- (3/3) 开始验证数据结构 ---")
    validate_json_with_schema(file_tree_json, file_schema)


if __name__ == "__main__":
    main()
