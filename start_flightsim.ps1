$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Test-PortFree([int]$Port) {
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'), $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) { $listener.Stop() }
    }
}

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
$pythonArgs = @('-3', '-m', 'http.server')
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $pythonArgs = @('-m', 'http.server')
}
if (-not $pythonCommand) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show('找不到 Python。請安裝 Python 3，並勾選 Add Python to PATH。', '台灣飛行模擬器') | Out-Null
    exit 1
}

$port = 8000
while ($port -le 8010 -and -not (Test-PortFree $port)) { $port++ }
if ($port -gt 8010) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show('連接埠 8000–8010 都在使用中，請關閉其他本機伺服器後再試。', '台灣飛行模擬器') | Out-Null
    exit 1
}

$pythonArgs += @('--bind', '127.0.0.1', "$port")
$server = Start-Process -FilePath $pythonCommand.Source -ArgumentList $pythonArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
Set-Content -LiteralPath (Join-Path $PSScriptRoot '.flightsim_server.pid') -Value $server.Id -Encoding ASCII
$url = "http://127.0.0.1:$port/"

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 300
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $client.Connect('127.0.0.1', $port)
        $client.Close()
        $ready = $true
        break
    } catch {
        if ($server.HasExited) { break }
    }
}
if (-not $ready) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show('背景伺服器啟動失敗。請確認 Python 安裝正常。', '台灣飛行模擬器') | Out-Null
    exit 1
}
Start-Process $url
