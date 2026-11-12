#Requires -Version 5.1
[CmdletBinding()]
param([switch]$JsonProgress)

$ErrorActionPreference = 'Stop'
if ($JsonProgress) {
    $ProgressPreference = 'SilentlyContinue'
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
}
$component = 'detector'

function Write-SetupProgress($State, $Message) {
    if ($JsonProgress) {
        [Console]::WriteLine((@{component = $component; state = $State; message = $Message} | ConvertTo-Json -Compress))
    } else {
        Write-Host $Message
    }
}
$modelRoot = Join-Path $PSScriptRoot 'model'
$detectorPath = Join-Path $modelRoot 'b-tok2'
$runtimeRoot = Join-Path $PSScriptRoot 'runtime'
$portableOllama = Join-Path $runtimeRoot 'ollama'
$portableExe = Join-Path $portableOllama 'ollama.exe'
$qwen = 'qwen2.5:3b'
$ollamaAddress = '127.0.0.1:11434'
$tagsUrl = "http://$ollamaAddress/api/tags"

# Keep these release details in sync with get_model.py.
$detectorUrl = 'https://github.com/aadyash24/promptshield/releases/download/model-b-tok2/b-tok2.zip'
$detectorHash = '31385e2a42d590160732a3e4c7ae6cd08056be26a490f66cc73b52053b30b026'
$detectorFiles = @('model.safetensors', 'config.json', 'tokenizer.json', 'tokenizer_config.json')

function Test-DetectorFiles($Path) {
    foreach ($name in $detectorFiles) {
        $file = Get-Item -LiteralPath (Join-Path $Path $name) -ErrorAction SilentlyContinue
        if (-not $file -or $file.PSIsContainer -or $file.Length -eq 0) { return $false }
    }
    return $true
}

function Expand-Release($Url, $Destination, $Sha256, [switch]$Detector) {
    $parent = Split-Path -Parent $Destination
    $null = New-Item -ItemType Directory -Path $parent -Force
    $stage = New-Item -ItemType Directory -Path (Join-Path $parent ([guid]::NewGuid().ToString()))
    $archive = Join-Path $stage.FullName 'release.zip'
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $archive
        Write-SetupProgress 'verifying' 'Verifying the download and extracting files...'
        if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $Sha256) {
            throw "The archive checksum does not match the published release at $Url"
        }
        $expanded = Join-Path $stage.FullName 'expanded'
        Expand-Archive -LiteralPath $archive -DestinationPath $expanded
        if ($Detector) {
            $checkpoint = Join-Path $expanded 'b-tok2'
            if (-not (Test-DetectorFiles $checkpoint)) { throw 'The b-tok2 archive is incomplete.' }
            $null = New-Item -ItemType Directory -Path $Destination -Force
            Get-ChildItem -LiteralPath $checkpoint -File | Copy-Item -Destination $Destination -Force
        } else {
            if (-not (Test-Path -LiteralPath (Join-Path $expanded 'ollama.exe') -PathType Leaf)) {
                throw 'The Ollama archive does not contain ollama.exe.'
            }
            Move-Item -LiteralPath $expanded -Destination $Destination
        }
    } finally {
        $resolved = (Resolve-Path -LiteralPath $stage.FullName).Path
        if ($resolved -eq $stage.FullName -and (Split-Path -Parent $resolved) -eq $parent) {
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
    }
}

try {
    if (Test-DetectorFiles $detectorPath) {
        Write-SetupProgress 'installed' 'b-tok2 is already installed.'
    } else {
        Write-SetupProgress 'downloading' 'Downloading b-tok2...'
        Expand-Release $detectorUrl $detectorPath $detectorHash -Detector
        Write-SetupProgress 'installed' 'b-tok2 installed.'
    }

    $component = 'ollama'
    $usePortable = Test-Path -LiteralPath $portableExe -PathType Leaf
    if ($usePortable) {
        $ollama = $portableExe
    } else {
        $ollama = (Get-Command ollama.exe -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1).Source
        if (-not $ollama -and $env:LOCALAPPDATA) {
            $installedExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
            if (Test-Path -LiteralPath $installedExe -PathType Leaf) { $ollama = $installedExe }
        }
    }

    if ($ollama) {
        Write-SetupProgress 'installed' "Using existing Ollama at $ollama"
    } else {
        if (Test-Path -LiteralPath $portableOllama) {
            throw "The Ollama folder exists without ollama.exe. Move it aside and rerun setup. Path $portableOllama"
        }
        $architecture = $env:PROCESSOR_ARCHITECTURE
        if ($env:PROCESSOR_ARCHITEW6432) { $architecture = $env:PROCESSOR_ARCHITEW6432 }
        $releaseHashes = @{
            amd64 = '50fcf5ad54277f2fa5d173ebfc93bcb017adbc0c9ef2314daabc96ca9e6aa64e'
            arm64 = '86d2b329cae3125684ff29b506623710b68e1393f679594f1c6aa267beac31c2'
        }
        if (-not $releaseHashes.ContainsKey($architecture)) {
            throw 'Install Ollama for your Windows architecture and rerun setup.'
        }
        $asset = "ollama-windows-$($architecture.ToLowerInvariant()).zip"
        Write-SetupProgress 'downloading' 'Downloading standalone Ollama...'
        Expand-Release "https://github.com/ollama/ollama/releases/download/v0.40.16/$asset" $portableOllama $releaseHashes[$architecture]
        $ollama = $portableExe
        $usePortable = $true
        Write-SetupProgress 'installed' 'Standalone Ollama installed.'
    }

    function Get-OllamaTags {
        try {
            Invoke-RestMethod -Uri $tagsUrl -TimeoutSec 2
        } catch {
            return $null
        }
    }

    $component = 'qwen'
    Write-SetupProgress 'checking' "Checking for $qwen..."
    $previousHost = $env:OLLAMA_HOST
    $previousModels = $env:OLLAMA_MODELS
    $server = $null
    try {
        $env:OLLAMA_HOST = $ollamaAddress
        $tags = Get-OllamaTags
        if ($null -eq $tags) {
            if ($usePortable) { $env:OLLAMA_MODELS = Join-Path $modelRoot 'ollama' }
            $server = Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden -PassThru
            $deadline = (Get-Date).AddSeconds(30)
            do {
                Start-Sleep -Milliseconds 500
                $tags = Get-OllamaTags
            } until ($null -ne $tags -or $server.HasExited -or (Get-Date) -ge $deadline)
            if ($null -eq $tags) { throw "Ollama did not start at $ollamaAddress." }
        }

        if ($qwen -in $tags.models.name) {
            Write-SetupProgress 'installed' "$qwen is already installed."
        } else {
            Write-SetupProgress 'downloading' "Downloading $qwen..."
            & $ollama pull $qwen
            if ($LASTEXITCODE -ne 0) { throw "Ollama failed to download $qwen." }
            $tags = Get-OllamaTags
            if ($qwen -notin $tags.models.name) { throw "Ollama did not list $qwen after the download." }
            Write-SetupProgress 'installed' "$qwen installed."
        }
    } finally {
        if ($server -and -not $server.HasExited) { Stop-Process -InputObject $server }
        $env:OLLAMA_HOST = $previousHost
        $env:OLLAMA_MODELS = $previousModels
    }

    $component = 'setup'
    Write-SetupProgress 'installed' 'PromptShield model setup complete.'
} catch {
    Write-SetupProgress 'failed' $_.Exception.Message
    throw
}
