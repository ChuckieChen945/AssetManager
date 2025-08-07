param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,

    [Parameter(Mandatory = $true)]
    [string]$OutputFile,

    [Parameter(Mandatory = $false)]
    [int]$Size = 512
)

function Initialize-ThumbnailExtractor {
    try {
        Add-Type -AssemblyName System.Drawing.Common -ErrorAction SilentlyContinue
        Add-Type -AssemblyName System.Drawing.Primitives -ErrorAction SilentlyContinue

        if (-not ([System.Management.Automation.PSTypeName]'ThumbnailExtractor').Type) {
            $csFile = Join-Path -Path $PSScriptRoot -ChildPath "windows_shell_api.cs"
            Add-Type -Path $csFile -ReferencedAssemblies @("System.Drawing.Common", "System.Drawing.Primitives", "System.Windows.Forms")
        }
        return $true
    }
    catch {
        Write-Warning "can't initialize thumbnail extractor: $($_.Exception.Message)"
        return $false
    }
}

function Get-FileThumbnail {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $false)]
        [string]$OutputPath = "thumbnail_advanced.png",

        [Parameter(Mandatory = $false)]
        [int]$Size = 256
    )

    if (-not (Initialize-ThumbnailExtractor)) {
        Write-Error "can't initialize thumbnail extractor"
        return
    }

    try {
        if (-not (Test-Path $FilePath)) {
            Write-Error "file not found: $FilePath"
            return
        }

        $absolutePath = Resolve-Path $FilePath
        $thumbnail = [ThumbnailExtractor]::GetThumbnail($absolutePath.Path, $Size)

        if ($thumbnail) {
            $thumbnail.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Host "thumbnail saved to: $OutputPath" -ForegroundColor Green
            Write-Host "thumbnail size: $($thumbnail.Width)x$($thumbnail.Height)" -ForegroundColor Gray
            $thumbnail.Dispose()
            return $true
        }
        else {
            Write-Warning "can't get thumbnail"
            return $false
        }
    }
    catch {
        Write-Error "can't get thumbnail: $($_.Exception.Message)"
        return $false
    }
}

Get-FileThumbnail -FilePath $InputFile -OutputPath $OutputFile -Size $Size
