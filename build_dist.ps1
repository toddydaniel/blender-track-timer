# Build the ready-to-post distribution zip for Track Timer.
# Run from Blender-less terminal:  powershell -File build_dist.ps1
# Output: dist\add-on-track-timer-vX.Y.Z.zip (extension package, Blender 4.2+)
# The bare track_timer_addon.py next to this script is the legacy file
# for Blender 3.6-4.1 (Install from Disk > select the .py).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $root "track_timer_addon.py"
$manifest = Join-Path $root "blender_manifest.toml"

foreach ($f in @($py, $manifest, (Join-Path $root "LICENSE"), (Join-Path $root "README.txt"))) {
    if (-not (Test-Path -LiteralPath $f)) { throw ("missing file: " + $f) }
}

# versions must match: bl_info (x, y, z) vs manifest version = "x.y.z"
$pyText = Get-Content -LiteralPath $py -Raw
$mm = [regex]::Match($pyText, '"version": \((\d+), (\d+), (\d+)\)')
if (-not $mm.Success) { throw "bl_info version not found" }
$ver = "$($mm.Groups[1].Value).$($mm.Groups[2].Value).$($mm.Groups[3].Value)"
$manText = Get-Content -LiteralPath $manifest -Raw
if ($manText -notmatch [regex]::Escape("version = `"$ver`"")) { throw "manifest version mismatch (expected $ver)" }

$stage = Join-Path $root "dist\stage"
$zip = Join-Path $root ("dist\add-on-track-timer-v{0}.zip" -f $ver)
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null
Copy-Item -LiteralPath $py -Destination (Join-Path $stage "__init__.py")
Copy-Item -LiteralPath $manifest -Destination (Join-Path $stage "blender_manifest.toml")
Copy-Item -LiteralPath (Join-Path $root "LICENSE") -Destination (Join-Path $stage "LICENSE")
Copy-Item -LiteralPath (Join-Path $root "README.txt") -Destination (Join-Path $stage "README.txt")
python -m py_compile (Join-Path $stage "__init__.py")
$pcache = Join-Path $stage "__pycache__"
if (Test-Path -LiteralPath $pcache) { Remove-Item -LiteralPath $pcache -Recurse -Force }
$rootcache = Join-Path $root "__pycache__"
if (Test-Path -LiteralPath $rootcache) { Remove-Item -LiteralPath $rootcache -Recurse -Force }
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip
Remove-Item -LiteralPath $stage -Recurse -Force
Write-Output ("READY TO POST: " + $zip)
