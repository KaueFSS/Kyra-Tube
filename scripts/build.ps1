# Gera o executável (pasta dist\KyraTube) e, se o Inno Setup estiver instalado, o instalador.
#   powershell -ExecutionPolicy Bypass -File scripts\build.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

python -m pip install -r requirements-dev.txt
python -m PyInstaller --noconfirm --clean --windowed --onedir --name KyraTube `
  --icon assets\kyra-tube.ico --add-data "assets;assets" `
  --collect-all customtkinter --collect-all imageio_ffmpeg --collect-all yt_dlp main.py

$version = (python -c "from core.config import APP_VERSION; print(APP_VERSION)").Trim()
$iscc = @("$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe", "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") |
  Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
  & $iscc "/DAppVersion=$version" installer\kyra-tube.iss
  Write-Host "Instalador: dist\Kyra-Tube-Setup.exe"
} else {
  Write-Host "Inno Setup não encontrado: gerei só o executável em dist\KyraTube. Instale em https://jrsoftware.org/isdl.php para gerar o instalador."
}
