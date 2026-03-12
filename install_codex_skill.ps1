param(
    [string]$CodexHome = "",
    [string]$SkillName = "all"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillMap = @{
    "resume-latex-builder" = "resume_latex_skill"
    "resume-layout-optimizer" = "resume_layout_optimizer_skill"
}

if (-not $CodexHome) {
    if ($env:CODEX_HOME) {
        $CodexHome = $env:CODEX_HOME
    } else {
        $CodexHome = Join-Path $HOME ".codex"
    }
}

$skillsDir = Join-Path $CodexHome "skills"

New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null

if ($SkillName -eq "all") {
    $skillNames = @("resume-latex-builder", "resume-layout-optimizer")
} else {
    $skillNames = @($SkillName)
}

foreach ($name in $skillNames) {
    if (-not $skillMap.ContainsKey($name)) {
        throw "Unknown skill: $name"
    }

    $sourceDir = Join-Path $repoRoot $skillMap[$name]
    if (-not (Test-Path $sourceDir)) {
        throw "Skill source not found: $sourceDir"
    }

    $targetDir = Join-Path $skillsDir $name
    if (Test-Path $targetDir) {
        Remove-Item -Recurse -Force $targetDir
    }

    Copy-Item -Recurse -Force $sourceDir $targetDir
    Write-Host "Installed skill to: $targetDir"
}

Write-Host "Next step:"
Write-Host "1. Ensure this repository remains accessible to the agent."
Write-Host "2. In chat, mention: use resume-latex-builder."
Write-Host "3. For layout-only tuning, mention: use resume-layout-optimizer."
