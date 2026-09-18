[CmdletBinding()]
param(
    [ValidateSet('codex', 'claude')][string]$Client,
    [string]$SkillsDir,
    [string]$Distro,
    [string]$Prefix
)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'hidog'
if (-not $SkillsDir) {
    $userDir = [Environment]::GetFolderPath('UserProfile')
    switch ($Client) {
        'codex' { $SkillsDir = Join-Path $userDir '.agents\skills' }
        'claude' { $SkillsDir = Join-Path $userDir '.claude\skills' }
        default { throw 'The agent must select -Client codex/claude or -SkillsDir.' }
    }
}
if (-not [IO.Path]::IsPathRooted($SkillsDir)) { throw 'SkillsDir must be an absolute user directory.' }
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) { throw 'Download and extract the complete package.' }
$target = Join-Path $SkillsDir 'hidog'
function Get-SkillManifest([string]$Folder) {
    $items = @(Get-ChildItem -LiteralPath $Folder -Recurse -Force)
    if ($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) {
        throw 'Linked skill contents are preserved; automatic replacement is not supported.'
    }
    $entries = foreach ($item in $items) {
        if (-not $item.PSIsContainer) {
            $relative = $item.FullName.Substring($Folder.TrimEnd('\').Length).TrimStart('\')
            $relative + ':' + (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
        }
    }
    return (($entries | Sort-Object) -join "`n")
}
if (Test-Path -LiteralPath $target) {
    if ((Get-Item -LiteralPath $target -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Existing skill is linked; preserved: $target"
    }
    if ((Get-SkillManifest $source) -ne (Get-SkillManifest $target)) {
        throw "Existing skill differs; preserved: $target"
    }
} else {
    New-Item -ItemType Directory -Path $target | Out-Null
    Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $target -Recurse
}
Write-Output "Skill registered: $target"
$options = @{ Action = 'setup' }
if ($Distro) { $options.Distro = $Distro }
if ($Prefix) { $options.Prefix = $Prefix }
& (Join-Path $target 'scripts\agent.ps1') @options
exit $LASTEXITCODE
