const { exec } = require("child_process");

// 全局变量
let selectedPath = "";
let isImporting = false;

// 工具函数
function showStatus(message, type = "info") {
    const statusEl = document.getElementById("status");
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.style.display = "block";
}

function hideStatus() {
    document.getElementById("status").style.display = "none";
}

function showProgress() {
    document.getElementById("progress").style.display = "block";
}

function hideProgress() {
    document.getElementById("progress").style.display = "none";
}

function updateProgress(current, total) {
    const percentage = Math.round((current / total) * 100);
    document.getElementById("progressFill").style.width = `${percentage}%`;
    document.getElementById(
        "progressText"
    ).textContent = `${current}/${total} (${percentage}%)`;
}

// 突出显示所有 error log 和 warning log
function addLog(message, type = "info") {
    const logEl = document.getElementById("log");
    logEl.style.display = "block";
    const timestamp = new Date().toLocaleTimeString();

    let logMessage = `[${timestamp}] ${message}\n`;

    // 为错误日志添加红色高亮
    if (
        type === "error" ||
        message.toLowerCase().includes("失败") ||
        message.toLowerCase().includes("错误")
    ) {
        logMessage = `<span style="color: #dc3545; font-weight: bold;">[${timestamp}] ${message}</span>\n`;
    }
    // 为警告日志添加橙色高亮
    else if (type === "warning" || message.toLowerCase().includes("警告")) {
        logMessage = `<span style="color: #fd7e14; font-weight: bold;">[${timestamp}] ${message}</span>\n`;
    }

    logEl.innerHTML += logMessage;
    logEl.scrollTop = logEl.scrollHeight;
}

function clearLog() {
    const logEl = document.getElementById("log");
    logEl.innerHTML = "";
    logEl.style.display = "none";
}

// 获取用户输入的文件夹列表
function getUserFolders() {
    const foldersInput = document.getElementById("folders");
    const foldersText = foldersInput.value.trim();

    if (!foldersText) {
        return [];
    }

    // 按逗号分割并去除空白
    return foldersText
        .split(",")
        .map((folder) => folder.trim())
        .filter((folder) => folder.length > 0);
}

// 使用Node.js的fs模块进行文件系统操作
const fs = require("fs");
const path = require("path");

// 检查路径是否存在
function checkPathExists(path) {
    try {
        return fs.existsSync(path);
    } catch (error) {
        console.error("检查路径失败:", error);
        return false;
    }
}

// 获取目录下的所有子目录
function getDirectories(dirPath) {
    try {
        const items = fs.readdirSync(dirPath);
        const directories = [];

        for (const item of items) {
            const fullPath = path.join(dirPath, item);
            const stats = fs.statSync(fullPath);
            if (stats.isDirectory()) {
                directories.push(item);
            }
        }

        return directories;
    } catch (error) {
        console.error("读取目录失败:", error);
        return [];
    }
}

// 获取目录下的所有文件
function getFiles(dirPath) {
    try {
        const items = fs.readdirSync(dirPath);
        const files = [];

        for (const item of items) {
            const fullPath = path.join(dirPath, item);
            const stats = fs.statSync(fullPath);
            if (!stats.isDirectory()) {
                files.push(item);
            }
        }

        return files;
    } catch (error) {
        console.error("读取文件失败:", error);
        return [];
    }
}

// 递归查找所有main_assets文件夹
function findMainAssetsFolders(rootPath) {
    const mainAssetsFolders = [];

    function searchRecursively(currentPath) {
        try {
            const items = fs.readdirSync(currentPath);

            for (const item of items) {
                const fullPath = path.join(currentPath, item);
                const stats = fs.statSync(fullPath);

                if (stats.isDirectory()) {
                    if (item === "main_assets") {
                        mainAssetsFolders.push(fullPath);
                    } else {
                        // 递归搜索子目录
                        searchRecursively(fullPath);
                    }
                }
            }
        } catch (error) {
            console.error(`搜索目录失败: ${currentPath}`, error);
        }
    }

    searchRecursively(rootPath);
    return mainAssetsFolders;
}

// 从路径生成标签
function generateTagsFromPath(filePath) {
    // 移除根路径部分，只保留相对路径
    const relativePath = path.relative(selectedPath, filePath);

    // 按路径分隔符分割
    const pathParts = relativePath.split(path.sep);

    // 过滤掉空字符串和main_assets
    const tags = pathParts.filter((part) => part && part !== "main_assets");

    return tags;
}

// 检查thumbnail目录
function checkThumbnailDirectory(mainAssetsPath) {
    const parentDir = path.dirname(mainAssetsPath);
    const thumbnailPath = path.join(parentDir, "thumbnail");

    try {
        if (!fs.existsSync(thumbnailPath)) {
            return { exists: false, path: null, files: [] };
        }

        const files = getFiles(thumbnailPath);
        const imageFiles = files.filter((file) => {
            const ext = path.extname(file).toLowerCase().substring(1);
            return ["jpg", "jpeg", "png", "gif", "bmp", "webp"].includes(ext);
        });

        return {
            exists: true,
            path: thumbnailPath,
            files: imageFiles,
        };
    } catch (error) {
        console.error("检查thumbnail目录失败:", error);
        return { exists: false, path: null, files: [] };
    }
}

// 导入单个main_assets文件夹
async function importMainAssetsFolder(mainAssetsPath, index, total) {
    try {
        addLog(`处理: ${mainAssetsPath}`);

        // 获取main_assets目录下的文件
        const files = getFiles(mainAssetsPath);

        if (files.length === 0) {
            addLog(`警告: ${mainAssetsPath} 目录为空`, "warning");
            return;
        }

        if (files.length > 1) {
            addLog(`警告: ${mainAssetsPath} 目录包含多个文件!`, "warning");
            return;
        }

        const assetFile = files[0];
        const assetFilePath = path.join(mainAssetsPath, assetFile);

        // 生成标签
        const tags = generateTagsFromPath(mainAssetsPath);

        // 检查thumbnail目录
        const thumbnailInfo = checkThumbnailDirectory(mainAssetsPath);

        // 如果没有thumbnail，添加no_thumbnail标签
        if (!thumbnailInfo.exists || thumbnailInfo.files.length === 0) {
            tags.push("no_thumbnail");
        }

        addLog(`导入文件: ${assetFile}`);
        addLog(`标签: ${tags.join(", ")}`);

        // 获取用户输入的文件夹
        const userFolders = getUserFolders();

        // 导入文件到Eagle
        const itemId = await eagle.item.addFromPath(assetFilePath, {
            name: assetFile,
            tags: tags,
            folders: userFolders,
        });

        // 等100ms，不要太快
        await new Promise((r) => setTimeout(r, 100));

        let importedItem = await eagle.item.getById(itemId);
        addLog(`成功导入: ${importedItem.name} (ID: ${importedItem.id})`);

        // 如果有thumbnail，设置自定义缩略图
        let thumbnailSetSuccess = true;
        if (thumbnailInfo.exists && thumbnailInfo.files.length > 0) {
            const thumbnailFile = thumbnailInfo.files[0];
            const thumbnailFilePath = path.join(
                thumbnailInfo.path,
                thumbnailFile
            );

            try {
                await importedItem.setCustomThumbnail(thumbnailFilePath);
                addLog(`设置缩略图: ${thumbnailFile}`);
                thumbnailSetSuccess = true;
            } catch (error) {
                addLog(`设置缩略图失败: ${error.message}`, "error");
                thumbnailSetSuccess = false;
            }
        }

        // 如果有 mainAssetsPath 同级目录中有 main_assets_others 文件夹，将文件夹中的内容复制到 item 目录中
        // TODO： checkmainAssetsOthersDirectory 函数还没写，补充这个函数
        const mainAssetsOthersInfo =
            checkmainAssetsOthersDirectory(mainAssetsPath);
        let mainAssetsOthersCopySuccess = true;
        if (
            mainAssetsOthersInfo.exists &&
            mainAssetsOthersInfo.files.length > 0
        ) {
            // TODO：改为 将 main_assets_others 目录中的所有内容按照原本的结构原封不动地复制到 destPath 目录中
            const destPath = path.join(
                eagle.library.path,
                "images",
                `${importedItem.id}.info`
            );
            try {
                // 确保目标目录存在
                if (!fs.existsSync(destPath)) {
                    fs.mkdirSync(destPath, { recursive: true });
                }
                for (const file of mainAssetsOthersInfo.files) {
                    const srcFile = path.join(mainAssetsOthersInfo.path, file);
                    const destFile = path.join(destPath, file);
                    fs.copyFileSync(srcFile, destFile);
                    addLog(`复制 main_assets_others 文件: ${file}`);
                }
                mainAssetsOthersCopySuccess = true;
            } catch (error) {
                addLog(
                    `复制 main_assets_others 文件失败: ${error.message}`,
                    "error"
                );
                mainAssetsOthersCopySuccess = false;
            }
        }

        // 确认导入成功且缩略图设置成功，main_assets_others复制成功 后，删除 mainAssetsPath 的 parent 文件夹（已导入成功，源文件没用了）
        // 必需同时满足：1. 素材导入成功 2. 缩略图（如有）设置成功，3. main_assets_others（如有）复制成功 , 缺一不可
        if (thumbnailSetSuccess && mainAssetsOthersCopySuccess) {
            try {
                const parentFolder = path.dirname(mainAssetsPath);
                const psCommand = `
Add-Type -AssemblyName Microsoft.VisualBasic;
[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
    '${parentFolder.replace(/'/g, "''")}',
    [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
    [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
)
`;
                exec(
                    `pwsh -NoProfile -Command "${psCommand
                        .replace(/\n/g, " ")
                        .replace(/"/g, '\\"')}"`,
                    (error, stdout, stderr) => {
                        if (error) {
                            console.error(`出错: ${error.message}`);
                            return;
                        }
                        if (stderr) {
                            console.error(`标准错误: ${stderr}`);
                            return;
                        }
                        console.log(`完成: ${stdout}`);
                    }
                );
                console.log(`已删除源文件夹: ${parentFolder}`);
            } catch (error) {
                addLog(
                    `删除源文件夹失败: ${parentFolder} - ${error.message}`,
                    "error"
                );
            }
        } else {
            addLog(
                `跳过删除源文件夹：缩略图或main_assets_others复制失败`,
                "warning"
            );
        }

        // 更新进度
        updateProgress(index + 1, total);
    } catch (error) {
        addLog(`导入失败: ${mainAssetsPath} - ${error.message}`, "error");
        console.error("导入失败:", error);
    }
}

// 开始批量导入
async function startBatchImport() {
    if (isImporting) {
        return;
    }

    if (!selectedPath) {
        showStatus("请先选择根目录路径", "error");
        return;
    }

    // 检查路径是否存在
    if (!checkPathExists(selectedPath)) {
        showStatus("选择的路径不存在", "error");
        return;
    }

    isImporting = true;
    document.getElementById("startImportBtn").disabled = true;
    document.getElementById("selectPathBtn").disabled = true;

    try {
        showStatus("正在搜索main_assets文件夹...", "info");
        clearLog();
        showProgress();

        // 查找所有main_assets文件夹
        const mainAssetsFolders = findMainAssetsFolders(selectedPath);

        if (mainAssetsFolders.length === 0) {
            showStatus("未找到任何main_assets文件夹", "error");
            return;
        }

        showStatus(
            `找到 ${mainAssetsFolders.length} 个main_assets文件夹，开始导入...`,
            "info"
        );
        addLog(`开始批量导入，共 ${mainAssetsFolders.length} 个文件夹`);

        // 逐个导入
        for (let i = 0; i < mainAssetsFolders.length; i++) {
            await importMainAssetsFolder(
                mainAssetsFolders[i],
                i,
                mainAssetsFolders.length
            );
        }

        showStatus(
            `批量导入完成！共处理 ${mainAssetsFolders.length} 个文件夹`,
            "success"
        );
        addLog("批量导入完成！");
    } catch (error) {
        showStatus(`导入过程中发生错误: ${error.message}`, "error");
        addLog(`错误: ${error.message}`);
        console.error("批量导入失败:", error);
    } finally {
        isImporting = false;
        document.getElementById("startImportBtn").disabled = false;
        document.getElementById("selectPathBtn").disabled = false;
        hideProgress();
    }
}

// 选择路径
async function selectPath() {
    try {
        const result = await eagle.dialog.showOpenDialog({
            title: "选择包含main_assets文件夹的根目录",
            properties: ["openDirectory"],
        });

        if (result && result.filePaths && result.filePaths.length > 0) {
            selectedPath = result.filePaths[0];
            document.getElementById("rootPath").value = selectedPath;
            document.getElementById("startImportBtn").disabled = false;
            showStatus("路径已选择，可以开始导入", "success");
        }
    } catch (error) {
        showStatus(`选择路径失败: ${error.message}`, "error");
        console.error("选择路径失败:", error);
    }
}

// Eagle插件生命周期事件
eagle.onPluginCreate((plugin) => {
    console.log("eagle.onPluginCreate");
    console.log(plugin);

    // 绑定事件监听器
    document
        .getElementById("selectPathBtn")
        .addEventListener("click", selectPath);
    document
        .getElementById("startImportBtn")
        .addEventListener("click", startBatchImport);

    // 显示插件信息
    showStatus(
        `插件已加载: ${plugin.manifest.name} v${plugin.manifest.version}`,
        "info"
    );
});

eagle.onPluginRun(() => {
    console.log("eagle.onPluginRun");
});

eagle.onPluginShow(() => {
    console.log("eagle.onPluginShow");
});

eagle.onPluginHide(() => {
    console.log("eagle.onPluginHide");
});

eagle.onPluginBeforeExit((event) => {
    console.log("eagle.onPluginBeforeExit");
});
