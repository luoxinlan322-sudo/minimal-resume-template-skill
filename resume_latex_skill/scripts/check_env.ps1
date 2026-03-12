Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
if ($xelatex) {
  Write-Host "xelatex OK: $($xelatex.Source)"
} else {
  Write-Host "xelatex not found, trying winget install..."
  winget install --id MiKTeX.MiKTeX --silent --accept-package-agreements --accept-source-agreements
}

Add-Type -AssemblyName System.Drawing
$installedFonts = New-Object System.Drawing.Text.InstalledFontCollection
if ($installedFonts.Families.Name -contains "Arial") {
  Write-Host "Arial OK"
} else {
  Write-Warning "Arial not found. Latin text may render differently."
}

