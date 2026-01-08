# Set EMPIRICA_SESSION_ID to latest active claude-code session (PowerShell version)
# Dot-source this in your PowerShell: . ~/.claude/plugins/local/empirica-integration/hooks/set-session-env.ps1

try {
    $output = empirica sessions-list --output json 2>$null | ConvertFrom-Json
    $sessions = $output.sessions

    # Filter for active claude-code* sessions
    $activeClaude = $sessions | Where-Object {
        $_.ai_id -like "claude-code*" -and $null -eq $_.end_time
    }

    if ($activeClaude) {
        # Sort by start_time descending, get most recent
        $latest = $activeClaude | Sort-Object -Property start_time -Descending | Select-Object -First 1
        $sessionId = $latest.session_id

        $env:EMPIRICA_SESSION_ID = $sessionId
        Write-Host "✓ EMPIRICA_SESSION_ID set to: $($sessionId.Substring(0,8))..." -ForegroundColor Green
        Write-Host "  Hooks will now use this session automatically" -ForegroundColor Gray
    } else {
        Write-Host "⚠ No active claude-code session found" -ForegroundColor Yellow
        Write-Host "  Create one with: empirica session-create --ai-id claude-code" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠ Failed to get session list: $_" -ForegroundColor Yellow
    Write-Host "  Ensure empirica is installed and working" -ForegroundColor Gray
}
