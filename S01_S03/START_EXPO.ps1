Set-Location (Join-Path $PSScriptRoot "mobile")
if (!(Test-Path .env)) {
  Write-Host "Set your laptop Wi-Fi IPv4 in mobile/.env before launching!" -ForegroundColor Yellow
  Copy-Item .env.example .env
  notepad .env
}
npm install
npx expo start --go --lan -c
