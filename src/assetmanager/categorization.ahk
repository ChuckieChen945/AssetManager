#Requires AutoHotkey v2.0
#SingleInstance Force

global g_explorer := 0  ; 缓存当前 Explorer 窗口对象

; ---- 快捷键 ----
z::
{
    selItems := Explorer_GetSelection()
    if selItems.Length = 0 {
        curDir := Explorer_GetPath()
        if !curDir
            return
        EnsureDir(curDir "\main_assets")
        EnsureDir(curDir "\thumbnail")
    }
    else if selItems.Length = 1 {
        file := selItems[1]
        dir := RegExReplace(file, "\\[^\\]+$")
        name := RegExReplace(file, ".*\\")
        name_no_ext := RegExReplace(name, "(?i)\.[^.]+$")
        newDir := dir

        EnsureDir(newDir "\main_assets")
        EnsureDir(newDir "\thumbnail")

        ; 移动文件 → main_assets
        FastMove(file, newDir "\main_assets\" name)
    }
    else {
        ; 多文件 → 按文件名无扩展名分组
        groups := Map()
        for file in selItems {
            dir := RegExReplace(file, "\\[^\\]+$")
            name := RegExReplace(file, ".*\\")
            name_no_ext := RegExReplace(name, "(?i)\.[^.]+$")
            if !groups.Has(name_no_ext)
                groups[name_no_ext] := []
            groups[name_no_ext].Push(file)
        }

        ; 遍历分组
        for name_no_ext, files in groups {
            dir := RegExReplace(files[1], "\\[^\\]+$")  ; 取第一个文件的目录
            newDir := dir "\" name_no_ext
            EnsureDir(newDir "\main_assets")
            EnsureDir(newDir "\thumbnail")

            for file in files {
                name := RegExReplace(file, ".*\\")
                ext := RegExReplace(name, ".*\.")
                if (ext ~= "i)(png|jpg|jpeg|gif|bmp|tif|tiff|webp)") {
                    FastMove(file, newDir "\thumbnail\" name)
                } else {
                    FastMove(file, newDir "\main_assets\" name)
                }
            }
        }
    }
}

; ---- 快速移动文件 (用 robocopy) ----
FastMove(src, dst) {
    dstDir := RegExReplace(dst, "\\[^\\]+$")
    EnsureDir(dstDir)
    ; /MOV = 移动文件 (保留目录结构)
    RunWait 'robocopy "' RegExReplace(src, "\\[^\\]+$") '" "' dstDir '" "' RegExReplace(src, ".*\\") '" /MOV /NFL /NDL /NJH /NJS /NC /NS', ,
    "Hide"
}

; ---- 确保目录存在 ----
EnsureDir(path) {
    if !DirExist(path)
        DirCreate(path)
}

; ---- 获取当前 Explorer 路径 ----
Explorer_GetPath() {
    global g_explorer
    try {
        if !g_explorer || g_explorer.hwnd != WinActive("A")
            g_explorer := Explorer_GetActive()
        return g_explorer.Document.Folder.Self.Path
    }
    return ""
}

; ---- 获取当前 Explorer 选中文件 ----
Explorer_GetSelection() {
    global g_explorer
    sel := []
    try {
        if !g_explorer || g_explorer.hwnd != WinActive("A")
            g_explorer := Explorer_GetActive()
        for item in g_explorer.Document.SelectedItems
            sel.Push(item.Path)
    }
    return sel
}

; ---- 获取当前激活的 Explorer 窗口对象 ----
Explorer_GetActive() {
    windows := ComObject("Shell.Application").Windows
    hwnd := WinActive("A")
    for win in windows {
        try {
            if win.hwnd = hwnd
                return win
        }
    }
    return 0
}
