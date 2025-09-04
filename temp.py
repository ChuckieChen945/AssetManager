# import re

# # 示例文件名列表
# filenames = [
#     "Assembly_Rock_td0fefoda_8K_3d_ms.zip",
#     "Brick_Debris_Rubble_Detritus_tfcnfgfpa_4K_3d_ms.zip",
#     "Brick_Rough_tkclabvla_8K_3d_ms.zip",
# ]

# pattern = re.compile(
#     r"^(?P<category>[^_]+)"  # 第一个字段 Category
#     r"(?:_(?P<descriptors>(?:[^_]+_)*[^_]+))?"  # 中间多个描述词（可选）
#     r"_(?P<id>[a-z0-9A-Z]+)"  # 随机 ID
#     r"_(?P<resolution>\d+[Kk])"  # 分辨率（4K/8K等）
#     r"_(?P<type>\d?[a-zA-Z]+)"  # 类型（3d/2d等）
#     r"_(?P<source>[a-zA-Z]+)"  # 来源（ms）
#     r"\.zip$",
# )

# parsed_data = []
# for fname in filenames:
#     match = pattern.match(fname)
#     if match:
#         data = match.groupdict()
#         # 分割 descriptors
#         if data["descriptors"]:
#             desc_list = data["descriptors"].split("_")
#         else:
#             desc_list = []
#         data["descriptors"] = desc_list
#         parsed_data.append(data)

# # 输出
# for item in parsed_data:
#     print(item)

