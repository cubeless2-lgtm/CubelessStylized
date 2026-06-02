Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel
Push-Location $repoRoot
try {
    git config core.hooksPath .githooks
    $configured = git config --get core.hooksPath
    Write-Host "Configured core.hooksPath=$configured"
    Write-Host "Git hooks are managed from $repoRoot\.githooks"
}
finally {
    Pop-Location
}
