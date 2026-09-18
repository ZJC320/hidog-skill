$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'hidog'
$target = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.claude\skills\hidog'
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) { throw 'Extract the complete package first.' }
if (Test-Path -LiteralPath $target) { throw "Skill already exists; preserved unchanged: $target" }
New-Item -ItemType Directory -Path $target | Out-Null
Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $target -Recurse
Write-Output "Skill installed: $target"
Write-Output 'Open Windows Claude Code and use /hidog. If Claude runs inside WSL, use install-claude.sh inside WSL instead.'
