param(
    [string]$WorkspaceRoot = "",
    [string]$InputPath = "input_templates\resume_input_template.md",
    [string]$OutputTex = ""
)

$ErrorActionPreference = "Stop"

function Resolve-InputPath {
    param(
        [string]$PathValue,
        [string]$PreferredRoot
    )

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }

    $candidates = @(
        [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PathValue))
    )
    if ($PreferredRoot) {
        $candidates += [System.IO.Path]::GetFullPath((Join-Path $PreferredRoot $PathValue))
    }
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "Input file not found: $PathValue"
}

function Get-WorkspaceRoot {
    param(
        [string]$PreferredRoot,
        [string]$InputFile
    )

    if ($PreferredRoot) {
        return [System.IO.Path]::GetFullPath($PreferredRoot)
    }

    return [System.IO.Path]::GetFullPath((Split-Path -Parent $InputFile))
}

function Resolve-InWorkspace {
    param(
        [string]$BaseDir,
        [string]$PathValue
    )

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $PathValue))
}

function Get-OutputRoot {
    param(
        [string]$WorkspaceDir
    )

    if (Test-Path (Join-Path $WorkspaceDir "template\resume.cls")) {
        return [System.IO.Path]::GetFullPath((Join-Path $WorkspaceDir "template"))
    }
    if (Test-Path (Join-Path $WorkspaceDir "resume.cls")) {
        return [System.IO.Path]::GetFullPath($WorkspaceDir)
    }
    return [System.IO.Path]::GetFullPath($WorkspaceDir)
}

function Ensure-TemplateAssets {
    param(
        [string]$WorkspaceDir,
        [string]$ScriptDirectory
    )

    $targetTemplate = Get-OutputRoot -WorkspaceDir $WorkspaceDir
    if (Test-Path (Join-Path $targetTemplate "resume.cls")) {
        return
    }

    $assetTemplate = [System.IO.Path]::GetFullPath((Join-Path $ScriptDirectory "..\assets\template"))
    if (-not (Test-Path $assetTemplate)) {
        throw "Template assets not found: $assetTemplate"
    }

    New-Item -ItemType Directory -Force -Path $targetTemplate | Out-Null
    Copy-Item (Join-Path $assetTemplate '*') $targetTemplate -Recurse -Force
}

function Get-LayoutAnalyzerPath {
    param(
        [string]$WorkspaceDir,
        [string]$ScriptDirectory
    )

    $workspaceAnalyzer = Join-Path $WorkspaceDir "resume_layout_optimizer_skill\scripts\analyze_layout.py"
    if (Test-Path $workspaceAnalyzer) {
        return $workspaceAnalyzer
    }

    $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    $installedAnalyzer = Join-Path $codexHome "skills\resume-layout-optimizer\scripts\analyze_layout.py"
    if (Test-Path $installedAnalyzer) {
        return $installedAnalyzer
    }

    $adjacentAnalyzer = [System.IO.Path]::GetFullPath((Join-Path $ScriptDirectory "..\..\resume_layout_optimizer_skill\scripts\analyze_layout.py"))
    if (Test-Path $adjacentAnalyzer) {
        return $adjacentAnalyzer
    }

    throw "analyze_layout.py not found in workspace or installed skills."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$inputFull = Resolve-InputPath -PathValue $InputPath -PreferredRoot $WorkspaceRoot
$rootDir = Get-WorkspaceRoot -PreferredRoot $WorkspaceRoot -InputFile $inputFull
Ensure-TemplateAssets -WorkspaceDir $rootDir -ScriptDirectory $scriptDir
$outputRoot = Get-OutputRoot -WorkspaceDir $rootDir
$outputPathValue = if ($OutputTex) { $OutputTex } else { "main.tex" }
$outputFull = Resolve-InWorkspace -BaseDir $outputRoot -PathValue $outputPathValue
$layoutAnalyzer = Get-LayoutAnalyzerPath -WorkspaceDir $rootDir -ScriptDirectory $scriptDir
$layoutReport = Join-Path $outputRoot "layout_diagnosis.json"
$layoutTasks = Join-Path $outputRoot "layout_tasks.json"

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputFull) | Out-Null

Write-Host "[1/5] Checking environment..."
powershell -ExecutionPolicy Bypass -File (Join-Path $scriptDir "check_env.ps1")

Write-Host "[2/5] Normalizing encoding..."
python (Join-Path $scriptDir "normalize_encoding.py") $inputFull

Write-Host "[3/5] Rendering markdown to TeX..."
python (Join-Path $scriptDir "render_resume.py") --input $inputFull --output $outputFull
python (Join-Path $scriptDir "normalize_encoding.py") $outputFull

Write-Host "[4/5] Compiling resume..."
powershell -ExecutionPolicy Bypass -File (Join-Path $scriptDir "compile_resume.ps1") -WorkspaceRoot $rootDir -OutputRoot $outputRoot

Write-Host "[5/5] Diagnosing layout and generating tasks..."
python $layoutAnalyzer --pdf (Join-Path $outputRoot 'main.pdf') --tex $outputFull --json-output $layoutReport --tasks-output $layoutTasks

Write-Host "Done. Output: $(Join-Path $outputRoot 'main.pdf')"
Write-Host "Layout diagnosis: $layoutReport"
Write-Host "Layout tasks: $layoutTasks"
