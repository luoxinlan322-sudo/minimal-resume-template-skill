param(
    [string]$WorkspaceRoot = "",
    [string]$InputPath = "input_templates\resume_input_template_word.docx",
    [string]$OutputMarkdown = "",
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
$mdPathValue = if ($OutputMarkdown) { $OutputMarkdown } else { "resume_input_from_word.md" }
if (($mdPathValue -eq "resume_input_from_word.md") -and (-not (Test-Path (Join-Path $rootDir "input_templates")))) {
    $defaultMdName = ([System.IO.Path]::GetFileNameWithoutExtension($inputFull) + "_from_word.md")
    $mdPathValue = Join-Path (Split-Path -Parent $inputFull) $defaultMdName
}
$mdFull = Resolve-InWorkspace -BaseDir (Split-Path -Parent $inputFull) -PathValue $mdPathValue
$outputTexValue = if ($OutputTex) { $OutputTex } else { "main.tex" }
$texFull = Resolve-InWorkspace -BaseDir $outputRoot -PathValue $outputTexValue
$layoutAnalyzer = Get-LayoutAnalyzerPath -WorkspaceDir $rootDir -ScriptDirectory $scriptDir
$layoutReport = Join-Path $outputRoot "layout_diagnosis.json"
$layoutTasks = Join-Path $outputRoot "layout_tasks.json"

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $mdFull) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $texFull) | Out-Null

Write-Host "[1/6] Checking environment..."
powershell -ExecutionPolicy Bypass -File (Join-Path $scriptDir "check_env.ps1")

Write-Host "[2/6] Converting Word to markdown..."
python (Join-Path $scriptDir "word_to_markdown.py") --input $inputFull --output $mdFull

Write-Host "[3/6] Normalizing encoding..."
python (Join-Path $scriptDir "normalize_encoding.py") $mdFull

Write-Host "[4/6] Rendering markdown to TeX..."
python (Join-Path $scriptDir "render_resume.py") --input $mdFull --output $texFull
python (Join-Path $scriptDir "normalize_encoding.py") $texFull

Write-Host "[5/6] Compiling resume..."
powershell -ExecutionPolicy Bypass -File (Join-Path $scriptDir "compile_resume.ps1") -WorkspaceRoot $rootDir -OutputRoot $outputRoot

Write-Host "[6/6] Diagnosing layout and generating tasks..."
python $layoutAnalyzer --pdf (Join-Path $outputRoot 'main.pdf') --tex $texFull --json-output $layoutReport --tasks-output $layoutTasks

Write-Host "Done. Output: $(Join-Path $outputRoot 'main.pdf')"
Write-Host "Layout diagnosis: $layoutReport"
Write-Host "Layout tasks: $layoutTasks"
