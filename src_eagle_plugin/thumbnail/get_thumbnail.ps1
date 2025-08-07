param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,

    [Parameter(Mandatory = $true)]
    [string]$OutputFile,

    [Parameter(Mandatory = $false)]
    [int]$Size = 400
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


if (-not (Initialize-ThumbnailExtractor)) {
    Write-Error "can't initialize thumbnail extractor"
    return
}

try {
    if (-not (Test-Path $InputFile)) {
        Write-Error "file not found: $InputFile"
        return
    }

    $absolutePath = Resolve-Path $InputFile
    $thumbnail = [ThumbnailExtractor]::GetThumbnail($absolutePath.Path, $Size)

    if ($thumbnail) {
        $thumbnail.Save($OutputFile, [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Host "thumbnail saved to: $OutputFile" -ForegroundColor Green
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
