param(
    [string]$WorkspaceRoot = "",
    [string]$OutputRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-WorkspaceRoot {
    param(
        [string]$PreferredRoot,
        [string]$ScriptDirectory
    )

    $candidates = @()
    if ($PreferredRoot) {
        $candidates += $PreferredRoot
    }
    $cwd = (Get-Location).Path
    $cursor = $cwd
    while ($true) {
        $candidates += $cursor
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) {
            break
        }
        $cursor = $parent
    }
    $cursor = [System.IO.Path]::GetFullPath((Join-Path $ScriptDirectory "..\\.."))
    while ($true) {
        $candidates += $cursor
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) {
            break
        }
        $cursor = $parent
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if ((Test-Path (Join-Path $candidate "template\\main.tex")) -and (Test-Path (Join-Path $candidate "template\\resume.cls"))) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    throw "Workspace root not found. Provide -WorkspaceRoot pointing to the folder that contains template\\main.tex."
}

function Get-OutputRoot {
    param(
        [string]$WorkspaceDir,
        [string]$PreferredOutputRoot
    )

    if ($PreferredOutputRoot) {
        return [System.IO.Path]::GetFullPath($PreferredOutputRoot)
    }
    if (Test-Path (Join-Path $WorkspaceDir "template\\resume.cls")) {
        return [System.IO.Path]::GetFullPath((Join-Path $WorkspaceDir "template"))
    }
    if (Test-Path (Join-Path $WorkspaceDir "resume.cls")) {
        return [System.IO.Path]::GetFullPath($WorkspaceDir)
    }

    throw "Output root not found. Expected resume.cls in workspace root or workspace\\template."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceDir = Get-WorkspaceRoot -PreferredRoot $WorkspaceRoot -ScriptDirectory $scriptDir
$templateDir = Get-OutputRoot -WorkspaceDir $workspaceDir -PreferredOutputRoot $OutputRoot

Push-Location $templateDir
try {
  & xelatex -interaction=nonstopmode -halt-on-error main.tex
  if ($LASTEXITCODE -ne 0) {
    throw "xelatex failed on pass 1 with exit code $LASTEXITCODE"
  }
  & xelatex -interaction=nonstopmode -halt-on-error main.tex
  if ($LASTEXITCODE -ne 0) {
    throw "xelatex failed on pass 2 with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}
