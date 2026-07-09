# Claude AI Scraper - Secure API Key Setup
Write-Host ""
Write-Host "  Claude AI Web Scraper - Secure Key Setup" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Paste your Anthropic API key - input will be hidden" -ForegroundColor White
Write-Host "  Get it from: console.anthropic.com/settings/keys" -ForegroundColor DarkGray
Write-Host ""
$secureKey = Read-Host "  API Key" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
$key  = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
if (-not $key.StartsWith("sk-ant-")) {
    Write-Host "  ERROR: Key must start with sk-ant-" -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    exit 1
}
$envPath = Join-Path $PSScriptRoot ".env"
$env = Get-Content $envPath -Raw
$env = $env -replace "ANTHROPIC_API_KEY=.*", ("ANTHROPIC_API_KEY=" + $key)
Set-Content $envPath $env -NoNewline -Encoding UTF8
Write-Host ""
Write-Host "  OK  Key saved to .env" -ForegroundColor Green
Write-Host "  OK  .env is gitignored - never pushed to GitHub" -ForegroundColor Green
Write-Host ""
Write-Host "  Next: python main.py scrape https://example.com --schema lead" -ForegroundColor DarkCyan
Write-Host ""
Read-Host "  Press Enter to close"
