param(
    [string]$WorkspaceRoot = "",
    [string]$PdfPath = "",
    [string]$DiagnosisPath = "",
    [string]$TasksPath = ""
)

$ErrorActionPreference = "Stop"

function Get-WorkspaceRoot {
    param(
        [string]$PreferredRoot,
        [string]$ScriptDirectory
    )

    if ($PreferredRoot) {
        return [System.IO.Path]::GetFullPath($PreferredRoot)
    }

    $candidates = @()
    $cursor = (Get-Location).Path
    while ($true) {
        $candidates += $cursor
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) {
            break
        }
        $cursor = $parent
    }
    $cursor = [System.IO.Path]::GetFullPath((Join-Path $ScriptDirectory "..\.."))
    while ($true) {
        $candidates += $cursor
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) {
            break
        }
        $cursor = $parent
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (
            ((Test-Path (Join-Path $candidate "template\main.tex")) -and (Test-Path (Join-Path $candidate "template\resume.cls"))) -or
            ((Test-Path (Join-Path $candidate "main.tex")) -and (Test-Path (Join-Path $candidate "resume.cls")))
        ) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    throw "Workspace root not found. Provide -WorkspaceRoot pointing to the folder that contains main.tex and resume.cls."
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

    throw "Output root not found. Expected resume.cls in workspace root or workspace\\template."
}

function Get-CompileScriptPath {
    param(
        [string]$WorkspaceDir,
        [string]$ScriptDirectory
    )

    $workspaceScript = Join-Path $WorkspaceDir "resume_latex_skill\scripts\compile_resume.ps1"
    if (Test-Path $workspaceScript) {
        return $workspaceScript
    }

    $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    $installedScript = Join-Path $codexHome "skills\resume-latex-builder\scripts\compile_resume.ps1"
    if (Test-Path $installedScript) {
        return $installedScript
    }

    $adjacentScript = [System.IO.Path]::GetFullPath((Join-Path $ScriptDirectory "..\..\resume_latex_skill\scripts\compile_resume.ps1"))
    if (Test-Path $adjacentScript) {
        return $adjacentScript
    }

    throw "compile_resume.ps1 not found in workspace or installed skills."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Get-WorkspaceRoot -PreferredRoot $WorkspaceRoot -ScriptDirectory $scriptDir
$outputRoot = Get-OutputRoot -WorkspaceDir $rootDir
$pdfPathValue = if ($PdfPath) { $PdfPath } else { "main.pdf" }
$diagnosisPathValue = if ($DiagnosisPath) { $DiagnosisPath } else { "layout_diagnosis.json" }
$tasksPathValue = if ($TasksPath) { $TasksPath } else { "layout_tasks.json" }
$pdfFull = Resolve-InWorkspace -BaseDir $outputRoot -PathValue $pdfPathValue
$diagnosisFull = Resolve-InWorkspace -BaseDir $outputRoot -PathValue $diagnosisPathValue
$tasksFull = Resolve-InWorkspace -BaseDir $outputRoot -PathValue $tasksPathValue
$compileScript = Get-CompileScriptPath -WorkspaceDir $rootDir -ScriptDirectory $scriptDir

Write-Host "[1/2] Compiling resume..."
powershell -ExecutionPolicy Bypass -File $compileScript -WorkspaceRoot $rootDir -OutputRoot $outputRoot

Write-Host "[2/2] Rechecking layout..."
python (Join-Path $scriptDir "analyze_layout.py") --pdf $pdfFull --tex (Join-Path $outputRoot "main.tex") --json-output $diagnosisFull --tasks-output $tasksFull

Write-Host "Done. PDF: $pdfFull"
Write-Host "Diagnosis: $diagnosisFull"
Write-Host "Tasks: $tasksFull"
