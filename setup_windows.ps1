Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$templateDir = Join-Path $root "template"
$miktexExe = $null

Write-Host "[1/4] Checking template files..."
if (!(Test-Path (Join-Path $templateDir "main.tex"))) {
  throw "template/main.tex not found."
}

Write-Host "[2/4] Checking xelatex..."
$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
if ($xelatex) {
  $miktexExe = $xelatex.Source
} else {
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if (!$winget) {
    throw "winget is not available. Please install MiKTeX manually."
  }

  Write-Host "Installing MiKTeX via winget..."
  winget install --id MiKTeX.MiKTeX --silent --accept-package-agreements --accept-source-agreements

  $candidate = Join-Path $env:LOCALAPPDATA "Programs\\MiKTeX\\miktex\\bin\\x64\\xelatex.exe"
  if (Test-Path $candidate) {
    $miktexExe = $candidate
  } else {
    $xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
    if ($xelatex) {
      $miktexExe = $xelatex.Source
    }
  }
}

if (!$miktexExe) {
  throw "xelatex not found after installation."
}

Write-Host "[3/4] Checking fonts..."
Add-Type -AssemblyName System.Drawing
$installedFonts = New-Object System.Drawing.Text.InstalledFontCollection
$hasArial = $installedFonts.Families.Name -contains "Arial"
if ($hasArial) {
  Write-Host "Arial detected."
} else {
  Write-Warning "Arial was not detected. The template expects Arial as the Latin font."
}

Write-Host "[4/4] Compiling template..."
Push-Location $templateDir
try {
  & $miktexExe -interaction=nonstopmode -halt-on-error main.tex | Out-Host
} finally {
  Pop-Location
}

Write-Host "Done. Output: $templateDir\\main.pdf"
