import requests
from pathlib import Path

BASE_URL = "http://localhost:41595/api"
TRASH_FOLDER_ID = "MFDVSSH14GC83"
LIBRARY_PATH = Path(r"F:\eagle_librarys\Illusion.library\images")

def list_items_in_folder(folder_id):
    url = f"{BASE_URL}/item/list"
    params = {"folders": folder_id, "limit": 10000, "offset": 0}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if data.get("status") == "success":
        return data.get("data", [])
    else:
        raise RuntimeError(f"API 返回错误: {data}")

def check_item_files(items):
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
            files = list(info_dir.iterdir())
            file_count = len(files)
            if file_count != 3:
                problems.append((item_id, f"{file_count} 个文件"))
        except Exception as e:
            problems.append((item_id, f"读取失败: {e}"))
    return problems
