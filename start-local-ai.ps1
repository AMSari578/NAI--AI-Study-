$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Ollama = Join-Path $ProjectRoot "tools\ollama\ollama.exe"
$ModelDirectory = Join-Path $ProjectRoot "tools\ollama-models"

if (-not (Test-Path $Ollama)) {
    throw "Ollama is not installed in tools\ollama."
}

$env:OLLAMA_MODELS = $ModelDirectory
$env:OLLAMA_CONTEXT_LENGTH = "16384"

$listening = netstat -ano | Select-String "127.0.0.1:11434\s+.*LISTENING"
if (-not $listening) {
    Start-Process -FilePath $Ollama -ArgumentList "serve" -WorkingDirectory (Split-Path $Ollama) -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

& $Ollama list
