# Windows owns the worker. Its wsl.exe call stays attached until the confirmed plan exits.
[CmdletBinding(DefaultParameterSetName='Start')]
param(
    [Parameter(Mandatory,ParameterSetName='Start')][string]$Distro,
    [Parameter(Mandatory,ParameterSetName='Start')][string]$Plan,
    [Parameter(Mandatory,ParameterSetName='Start')][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ConfirmedPlan,
    [Parameter(Mandatory,ParameterSetName='Worker')][string]$JobDir
)
$ErrorActionPreference = 'Stop'
if ($PSCmdlet.ParameterSetName -eq 'Worker') {
    $code = 1
    try {
        $request = Get-Content -LiteralPath (Join-Path $JobDir 'request.json') -Encoding utf8 -Raw | ConvertFrom-Json
        & (Join-Path $PSScriptRoot 'agent.ps1') -Distro $request.distro -Action run-plan -HidogArgs @(
            '--plan', $request.plan, '--confirmed-plan', $request.digest
        )
        $code = $LASTEXITCODE
    } catch {
        [Console]::Error.WriteLine($_.Exception.Message)
    } finally {
        $tmp = Join-Path $JobDir 'exit-code.tmp'
        [IO.File]::WriteAllText($tmp, [string]$code)
        [IO.File]::Move($tmp, (Join-Path $JobDir 'exit-code.txt'))
    }
    exit $code
}
if ($Plan -notmatch '^(/|[a-zA-Z]:[\\/]|\\\\)') {
    throw 'Use the absolute path of the confirmed plan.'
}
# Keep status on Windows, including the exit code of a failed WSL invocation.
$job = Join-Path $env:LOCALAPPDATA ('HiDOG/jobs/' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($job) | Out-Null
$request = @{ distro=$Distro; plan=$Plan; digest=$ConfirmedPlan }
[IO.File]::WriteAllText((Join-Path $job 'request.json'), ($request | ConvertTo-Json))
$exe = if ($PSVersionTable.PSEdition -eq 'Core') { Join-Path $PSHOME 'pwsh.exe' } else { Join-Path $PSHOME 'powershell.exe' }
# Only Windows filesystem paths are interpolated here; user input travels in JSON.
$arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -JobDir "' + $job + '"'
$worker = Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -WorkingDirectory $job -RedirectStandardOutput (Join-Path $job 'stdout.log') -RedirectStandardError (Join-Path $job 'stderr.log') -PassThru
[pscustomobject]@{ pid=$worker.Id; startedUtc=$worker.StartTime.ToUniversalTime().ToString('o'); jobDir=$job }
