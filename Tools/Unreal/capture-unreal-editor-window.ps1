param(
    [string]$OutputPath = "",
    [string]$TitlePattern = "Unreal Editor|CubelessStylized|StylizedCubeless",
    [switch]$NoForeground
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputPath = Join-Path (Get-Location) "Saved\MCP_Screenshots\unreal_editor_window_$stamp.png"
}

$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public class CubelessWin32Capture {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr GetDC(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);

    [DllImport("gdi32.dll")]
    public static extern IntPtr CreateCompatibleDC(IntPtr hDC);

    [DllImport("gdi32.dll")]
    public static extern IntPtr CreateCompatibleBitmap(IntPtr hDC, int nWidth, int nHeight);

    [DllImport("gdi32.dll")]
    public static extern IntPtr SelectObject(IntPtr hDC, IntPtr hObject);

    [DllImport("gdi32.dll")]
    public static extern bool BitBlt(IntPtr hdcDest, int nXDest, int nYDest, int nWidth, int nHeight, IntPtr hdcSrc, int nXSrc, int nYSrc, int dwRop);

    [DllImport("gdi32.dll")]
    public static extern bool DeleteObject(IntPtr hObject);

    [DllImport("gdi32.dll")]
    public static extern bool DeleteDC(IntPtr hDC);

    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
}
'@

$Srccopy = 0x00CC0020

function Get-WindowCaptureStats {
    param([System.Drawing.Bitmap]$Bitmap)

    $sampleCount = 0
    $nonBlackCount = 0
    $stepX = [Math]::Max(1, [Math]::Floor($Bitmap.Width / 32))
    $stepY = [Math]::Max(1, [Math]::Floor($Bitmap.Height / 18))

    for ($y = 0; $y -lt $Bitmap.Height; $y += $stepY) {
        for ($x = 0; $x -lt $Bitmap.Width; $x += $stepX) {
            $pixel = $Bitmap.GetPixel($x, $y)
            $sampleCount++
            if (($pixel.R + $pixel.G + $pixel.B) -gt 18) {
                $nonBlackCount++
            }
        }
    }

    [pscustomobject]@{
        SampleCount = $sampleCount
        NonBlackCount = $nonBlackCount
        NonBlackRatio = if ($sampleCount -gt 0) { [Math]::Round($nonBlackCount / $sampleCount, 4) } else { 0.0 }
    }
}

function New-BitmapFromScreenBitBlt {
    param(
        [int]$Left,
        [int]$Top,
        [int]$Width,
        [int]$Height
    )

    $screenDc = [CubelessWin32Capture]::GetDC([IntPtr]::Zero)
    if ($screenDc -eq [IntPtr]::Zero) {
        throw "GetDC(NULL) failed"
    }

    $memoryDc = [IntPtr]::Zero
    $bitmapHandle = [IntPtr]::Zero
    $oldObject = [IntPtr]::Zero

    try {
        $memoryDc = [CubelessWin32Capture]::CreateCompatibleDC($screenDc)
        if ($memoryDc -eq [IntPtr]::Zero) {
            throw "CreateCompatibleDC failed"
        }

        $bitmapHandle = [CubelessWin32Capture]::CreateCompatibleBitmap($screenDc, $Width, $Height)
        if ($bitmapHandle -eq [IntPtr]::Zero) {
            throw "CreateCompatibleBitmap failed"
        }

        $oldObject = [CubelessWin32Capture]::SelectObject($memoryDc, $bitmapHandle)
        $ok = [CubelessWin32Capture]::BitBlt($memoryDc, 0, 0, $Width, $Height, $screenDc, $Left, $Top, $Srccopy)
        if (-not $ok) {
            throw "BitBlt failed"
        }

        $image = [System.Drawing.Image]::FromHbitmap($bitmapHandle)
        try {
            return New-Object System.Drawing.Bitmap $image
        } finally {
            $image.Dispose()
        }
    } finally {
        if ($oldObject -ne [IntPtr]::Zero -and $memoryDc -ne [IntPtr]::Zero) {
            [void][CubelessWin32Capture]::SelectObject($memoryDc, $oldObject)
        }
        if ($bitmapHandle -ne [IntPtr]::Zero) {
            [void][CubelessWin32Capture]::DeleteObject($bitmapHandle)
        }
        if ($memoryDc -ne [IntPtr]::Zero) {
            [void][CubelessWin32Capture]::DeleteDC($memoryDc)
        }
        [void][CubelessWin32Capture]::ReleaseDC([IntPtr]::Zero, $screenDc)
    }
}

$windows = New-Object System.Collections.Generic.List[object]
$callback = [CubelessWin32Capture+EnumWindowsProc]{
    param([IntPtr]$hWnd, [IntPtr]$lParam)

    if (-not [CubelessWin32Capture]::IsWindowVisible($hWnd)) {
        return $true
    }

    $length = [CubelessWin32Capture]::GetWindowTextLength($hWnd)
    if ($length -le 0) {
        return $true
    }

    $builder = New-Object System.Text.StringBuilder ($length + 1)
    [void][CubelessWin32Capture]::GetWindowText($hWnd, $builder, $builder.Capacity)
    $title = $builder.ToString()
    if ($title -notmatch $TitlePattern) {
        return $true
    }

    $rect = New-Object CubelessWin32Capture+RECT
    [void][CubelessWin32Capture]::GetWindowRect($hWnd, [ref]$rect)
    $width = [Math]::Max(0, $rect.Right - $rect.Left)
    $height = [Math]::Max(0, $rect.Bottom - $rect.Top)
    $area = $width * $height

    if ($area -gt 100000) {
        $windows.Add([pscustomobject]@{
            Area = $area
            Handle = $hWnd
            Title = $title
            Left = $rect.Left
            Top = $rect.Top
            Right = $rect.Right
            Bottom = $rect.Bottom
            Width = $width
            Height = $height
        }) | Out-Null
    }

    return $true
}

[void][CubelessWin32Capture]::EnumWindows($callback, [IntPtr]::Zero)
$target = $windows | Sort-Object Area -Descending | Select-Object -First 1
if ($null -eq $target) {
    throw "No Unreal Editor window matched title pattern: $TitlePattern"
}

if (-not $NoForeground) {
    [void][CubelessWin32Capture]::SetForegroundWindow($target.Handle)
    Start-Sleep -Milliseconds 800
}

$virtualScreen = [System.Windows.Forms.SystemInformation]::VirtualScreen
$left = [Math]::Max($virtualScreen.Left, $target.Left)
$top = [Math]::Max($virtualScreen.Top, $target.Top)
$right = [Math]::Min($virtualScreen.Right, $target.Right)
$bottom = [Math]::Min($virtualScreen.Bottom, $target.Bottom)
$width = $right - $left
$height = $bottom - $top

if ($width -le 0 -or $height -le 0) {
    throw "Invalid Unreal window capture rect: target=$($target | ConvertTo-Json -Compress), virtual=$virtualScreen"
}

try {
    $bitmap = New-BitmapFromScreenBitBlt -Left $left -Top $top -Width $width -Height $height
    $stats = Get-WindowCaptureStats -Bitmap $bitmap
    if ($stats.NonBlackRatio -lt 0.02) {
        throw "Capture produced mostly black image: non_black_ratio=$($stats.NonBlackRatio)"
    }
    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
} finally {
    if ($bitmap) {
        $bitmap.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $OutputPath)) {
    Remove-Item -LiteralPath $OutputPath -Force -ErrorAction SilentlyContinue
    throw "Unreal Editor window capture failed before producing a valid PNG"
}

$file = Get-Item -LiteralPath $OutputPath
[pscustomobject]@{
    path = $file.FullName
    bytes = $file.Length
    title = $target.Title
    rect = "$left,$top,$right,$bottom"
    non_black_ratio = $stats.NonBlackRatio
} | ConvertTo-Json -Compress
