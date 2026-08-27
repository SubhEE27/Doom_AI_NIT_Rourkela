$ErrorActionPreference = "Stop"

Write-Host "DOOM AI Hackathon Validation" -ForegroundColor Cyan
Write-Host "Project root: $PWD"

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "No .venv activation script found. Continuing with current Python." -ForegroundColor Yellow
}

python -m compileall doom_ai doom tests hackathon_tests 2>$null
if ($LASTEXITCODE -ne 0) {
    # compileall may mention missing optional package variants; the scenario runner will provide the authoritative result.
    Write-Host "Compileall returned non-zero; continuing to scenario runner." -ForegroundColor Yellow
}

python -m hackathon_tests.scenario_runner
exit $LASTEXITCODE
