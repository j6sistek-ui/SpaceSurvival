<#
Render the actual replacement squirrel through two ordinary station jumps in a fresh isolated profile.
Uses the existing guarded offscreen harness; no asset writes, live owner editor or packaged launch.
Native metadata measures the actual skin-weighted tail surface against the real collision floor.
#>
param(
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')][string]$Label = 'SquirrelJump',
    [string]$EngineRoot = 'C:/Program Files/EpicGames2/UE_5.8',
    [ValidateRange(640,3840)][int]$Width = 1280,
    [ValidateRange(480,2160)][int]$Height = 720
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'CaptureSpaceLook.ps1') -TailReview -Label $Label -EngineRoot $EngineRoot -Width $Width -Height $Height
