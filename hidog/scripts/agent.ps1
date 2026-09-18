# Windows entry point. Linux execution always stays inside the selected WSL distro.
[CmdletBinding()]
param(
    [ValidateSet('check', 'install', 'run', 'example')][string]$Action = 'check',
    [string]$Distro,
    [string]$Prefix,
    [string[]]$HidogArgs = @()
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'WSL is required. Install WSL with Ubuntu, complete its first launch, then retry. This script does not change Windows features.'
}
$wslSelection = @()
if ($Distro) { $wslSelection = @('--distribution', $Distro) }
# A package stored in WSL must be run in that same distro.
$bridgePath = Join-Path $PSScriptRoot 'agent.sh'
if ($bridgePath -match '^\\\\(?:wsl\.localhost|wsl\$)\\([^\\]+)\\') {
    $packageDistro = $Matches[1]
    if ($Distro -and $Distro -ne $packageDistro) { throw 'The package is in a different WSL distribution.' }
    $Distro = $packageDistro
    $wslSelection = @('--distribution', $Distro)
}
& wsl.exe @wslSelection --exec /bin/true
if ($LASTEXITCODE -ne 0) { throw 'WSL is not ready. Start an installed Ubuntu distribution and finish first-time setup.' }
function Convert-HiDOGPath([string]$Value) {
    if ($Value -match '^\\\\(?:wsl\.localhost|wsl\$)\\([^\\]+)\\(.*)$') {
        if (-not $Distro -or $Matches[1] -ne $Distro) {
            throw 'For WSL network paths select the matching distribution with -Distro.'
        }
        return '/' + $Matches[2].Replace('\', '/')
    }
    if ($Value -match '^[A-Za-z]:[\\/]') {
        $converted = & wsl.exe @wslSelection --exec wslpath -a -u $Value
        if ($LASTEXITCODE -ne 0) { throw "Cannot translate Windows path: $Value" }
        return ($converted -join "`n").Trim()
    }
    if ($Value.StartsWith('\\')) { throw 'Copy network-share inputs to a local drive or WSL before analysis.' }
    return $Value
}
$linuxBridge = Convert-HiDOGPath $bridgePath
$bridgeArgs = @()
if ($Prefix) { $bridgeArgs += @('--prefix', (Convert-HiDOGPath $Prefix)) }
$bridgeArgs += $Action
foreach ($item in $HidogArgs) { $bridgeArgs += (Convert-HiDOGPath $item) }
& wsl.exe @wslSelection --exec bash $linuxBridge @bridgeArgs
exit $LASTEXITCODE
