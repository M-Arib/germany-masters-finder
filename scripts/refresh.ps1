# Re-scrapes DAAD, rebuilds the dashboard, runs the tests and publishes the result.
#
# DAAD blocks requests from cloud servers (GitHub Actions gets HTTP 403), so the
# refresh has to run from a normal internet connection like this computer.
#
# Usage (from the repository folder):   .\scripts\refresh.ps1
# Add -NoPush to only update the files locally.

param([switch]$NoPush)

# Failures are detected through exit codes below. "Stop" would also abort on harmless
# warnings that git prints to stderr, which Windows PowerShell 5.1 treats as errors.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

git pull --rebase --quiet
if ($LASTEXITCODE -ne 0) { throw "git pull failed. Commit or stash your local changes first." }

python -m germany_masters all
if ($LASTEXITCODE -ne 0) { throw "Scrape or build failed. See the output above." }

python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed on the new data. Nothing was committed." }

git add data docs
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes since the last refresh."
    exit 0
}

$today = Get-Date -Format "yyyy-MM-dd"
git commit --quiet -m "Refresh DAAD data ($today)"
if ($NoPush) {
    Write-Host "Committed locally. Run 'git push' to publish."
} else {
    git push --quiet
    Write-Host "Published. The website updates in about a minute."
}
