# One-time setup: downloads a private copy of Python with pygame and pyserial.
# Needs internet once. After that the arcade runs fully offline. Nothing is installed system-wide.
# It lives in %LOCALAPPDATA%\IEEEArcade (a short path, so Windows' 260-character path limit
# never bites, and it survives downloading a newer copy of the repo).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$rt = Join-Path $env:LOCALAPPDATA 'IEEEArcade\python'
$py = Join-Path $rt 'python.exe'
$pyVersion = '3.12.10'

function Test-Runtime {
    if (-not (Test-Path $py)) { return $false }
    # Start-Process keeps a failed import from stopping this script
    $p = Start-Process -FilePath $py -ArgumentList '-c', '"import pygame, serial"' -Wait -PassThru -WindowStyle Hidden
    return $p.ExitCode -eq 0
}

if (Test-Runtime) { Write-Host 'Python runtime already set up.'; exit 0 }

Write-Host 'Setting up the arcade (one time only, needs internet)...'
if (Test-Path $rt) { Remove-Item $rt -Recurse -Force }
New-Item -ItemType Directory -Path $rt -Force | Out-Null
$tmp = Join-Path $env:TEMP 'ieee-arcade-setup'
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

Write-Host '  1/3 Downloading Python...'
$zip = Join-Path $tmp 'python-embed.zip'
Invoke-WebRequest "https://www.python.org/ftp/python/$pyVersion/python-$pyVersion-embed-amd64.zip" -OutFile $zip -UseBasicParsing
Expand-Archive $zip -DestinationPath $rt -Force

# Let the private Python find installed packages
$pth = Get-ChildItem $rt -Filter 'python*._pth' | Select-Object -First 1
$zipName = (Get-ChildItem $rt -Filter 'python3*.zip' | Select-Object -First 1).Name
Set-Content -Path $pth.FullName -Encoding ASCII -Value @($zipName, '.', 'Lib\site-packages', 'import site')

Write-Host '  2/3 Installing pip...'
$getPip = Join-Path $tmp 'get-pip.py'
Invoke-WebRequest 'https://bootstrap.pypa.io/get-pip.py' -OutFile $getPip -UseBasicParsing
& $py $getPip --no-warn-script-location --quiet
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

Write-Host '  3/3 Installing pygame and pyserial...'
& $py -m pip install --no-warn-script-location --quiet 'pygame==2.6.1' 'pyserial==3.5'
if ($LASTEXITCODE -ne 0) { throw 'package install failed' }

if (-not (Test-Runtime)) { throw 'Python runtime check failed after setup' }
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'Setup complete.'
