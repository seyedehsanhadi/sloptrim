# Combined statusline: shows active ponytail/caveman/sloptrim levels.
$ErrorActionPreference = 'SilentlyContinue'
try { $null = [Console]::In.ReadToEnd() } catch {}

$claude = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME '.claude' }

function Seg($file, $label, $default) {
    $p = Join-Path $claude $file
    $v = $default
    if (Test-Path $p) {
        try { $v = (Get-Content -Raw -LiteralPath $p).Trim() } catch { $v = $default }
    }
    if (-not $v -or $v -eq 'off') { return '' }
    return "[$label`:$($v.ToUpper())]"
}

$parts = @(
    (Seg '.ponytail-mode'  'PONY' ''),
    (Seg '.caveman-active' 'CAVE' ''),
    (Seg '.sloptrim-active' 'SLOP' 'full')
) | Where-Object { $_ }

$esc = [char]27
$dim = "$esc[38;5;245m"
$reset = "$esc[0m"
Write-Host "$dim$($parts -join ' ')$reset" -NoNewline
