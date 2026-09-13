param(
    [string]$Sc2Path = 'D:\MARL\StarCraftII',
    [switch]$InstallMaps
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MapsSource = Join-Path $ProjectRoot 'third_party\smacv2\smacv2\env\starcraft2\maps\SMAC_Maps'
$MapsTarget = Join-Path $Sc2Path 'Maps\SMAC_Maps'

function Require-Path([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
}

Require-Path $Sc2Path 'StarCraft II root'
Require-Path (Join-Path $Sc2Path 'Versions') 'StarCraft II Versions directory'
Require-Path $MapsSource 'Official SMACv2 map source'

$Executable = Get-ChildItem -LiteralPath (Join-Path $Sc2Path 'Versions') -Recurse -Filter 'SC2_x64.exe' -File |
    Select-Object -First 1
if ($null -eq $Executable) {
    throw "SC2_x64.exe not found below $(Join-Path $Sc2Path 'Versions')"
}

if ($InstallMaps) {
    New-Item -ItemType Directory -Force -Path $MapsTarget | Out-Null
    Copy-Item -LiteralPath (Join-Path $MapsSource '*') -Destination $MapsTarget -Recurse -Force
}

$RequiredMap = Join-Path $MapsTarget '32x32_flat.SC2Map'
$Report = [ordered]@{
    protocol = 'SMACV2-D-DRIVE-RUNTIME-CHECK-V1'
    sc2_path = (Resolve-Path -LiteralPath $Sc2Path).Path
    sc2_executable = $Executable.FullName
    maps_source = (Resolve-Path -LiteralPath $MapsSource).Path
    maps_target = $MapsTarget
    required_map_present = Test-Path -LiteralPath $RequiredMap
    sc2path_for_current_shell = "`$env:SC2PATH='$Sc2Path'"
    status = if (Test-Path -LiteralPath $RequiredMap) { 'SMACV2_RUNTIME_PREREQUISITES_PASS' } else { 'SMACV2_MAPS_MISSING' }
}

$Report | ConvertTo-Json -Depth 3
if ($Report.status -ne 'SMACV2_RUNTIME_PREREQUISITES_PASS') {
    throw "SMACv2 maps are missing. Re-run with -InstallMaps after reviewing the target path."
}
