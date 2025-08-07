const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

module.exports = async ({ src, dest, item }) => {
    return new Promise(async (resolve, reject) => {
        try {
            debugger;
            // 1. 获取 PowerShell 脚本的绝对路径
            const scriptPath = path.resolve(__dirname, "get_thumbnail.ps1");

            // 2. 检查源文件是否存在
            if (!fs.existsSync(src)) {
                return reject(new Error(`Source file does not exist: ${src}`));
            }

            // 3. 调用 PowerShell 脚本生成缩略图
            const result = await executePowerShellScript(
                scriptPath,
                src,
                dest,
                400
            );

            if (!result.success) {
                return reject(
                    new Error(`Failed to generate thumbnail: ${result.error}`)
                );
            }

            // 3. 检查生成的缩略图文件
            if (!fs.existsSync(dest)) {
                return reject(new Error(`file thumbnail generate fail.`));
            }

            // 4. 返回结果
            return resolve(item);
        } catch (err) {
            return reject(err);
        }
    });
};

// 执行 PowerShell 脚本的辅助函数
function executePowerShellScript(scriptPath, inputFile, outputFile, size) {
    return new Promise((resolve) => {
        // 构建 PowerShell 命令
        const args = [
            "-ExecutionPolicy",
            "Bypass",
            "-NoProfile",
            "-NoLogo",
            "-File",
            `"${scriptPath}"`,
            "-InputFile",
            `"${inputFile}"`,
            "-OutputFile",
            `"${outputFile}"`,
            "-Size",
            size.toString(),
        ];

        const powershell = spawn("pwsh.exe", args, {
            stdio: ["pipe", "pipe", "pipe"],
            shell: true,
        });

        let stdout = "";
        let stderr = "";

        powershell.stdout.on("data", (data) => {
            stdout += data.toString();
        });

        powershell.stderr.on("data", (data) => {
            stderr += data.toString();
        });

        powershell.on("close", (code) => {
            if (code === 0) {
                resolve({ success: true, output: stdout });
            } else {
                resolve({
                    success: false,
                    error:
                        stderr || `PowerShell script exited with code ${code}`,
                    output: stdout,
                });
            }
        });

        powershell.on("error", (error) => {
            resolve({
                success: false,
                error: `Failed to execute PowerShell script: ${error.message}`,
            });
        });
    });
}
