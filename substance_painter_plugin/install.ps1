# 用于安装该插件
# TODO: substance panter 插件 好像不支持 软链接
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\thumbnail.py" -Target ".\thumbnail.py"