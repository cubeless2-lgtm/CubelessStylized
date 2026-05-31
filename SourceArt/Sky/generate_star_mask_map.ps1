param(
    [string]$OutputPath = "Content/Cubeless/Env/Sky/Textures/StarsMaskTile_RGBA_2048.png",
    [string]$PreviewPath = "SourceArt/Sky/StarsMaskTile_RGBA_2048_Preview.png",
    [int]$Size = 2048,
    [int]$Seed = 250530
)

Add-Type -AssemblyName System.Drawing

$rand = [System.Random]::new($Seed)
$count = $Size * $Size
$r = [float[]]::new($count)
$g = [float[]]::new($count)
$b = [float[]]::new($count)
$a = [float[]]::new($count)

function Add-WrappedGaussian {
    param(
        [float[]]$Channel,
        [int]$N,
        [double]$Cx,
        [double]$Cy,
        [double]$Radius,
        [double]$Strength
    )

    $limit = [int][Math]::Ceiling($Radius * 3.0)
    $twoSigma2 = 2.0 * $Radius * $Radius
    for ($oy = -$limit; $oy -le $limit; ++$oy) {
        $yy = ([int][Math]::Floor($Cy) + $oy) % $N
        if ($yy -lt 0) { $yy += $N }
        $dy = $oy + ([Math]::Floor($Cy) - $Cy)
        for ($ox = -$limit; $ox -le $limit; ++$ox) {
            $xx = ([int][Math]::Floor($Cx) + $ox) % $N
            if ($xx -lt 0) { $xx += $N }
            $dx = $ox + ([Math]::Floor($Cx) - $Cx)
            $falloff = [Math]::Exp(-(($dx * $dx + $dy * $dy) / $twoSigma2))
            $idx = $yy * $N + $xx
            $value = [float]($Strength * $falloff)
            if ($value -gt $Channel[$idx]) {
                $Channel[$idx] = [Math]::Min(1.0, $value)
            }
        }
    }
}

function Frac([double]$Value) {
    return $Value - [Math]::Floor($Value)
}

$pi2 = [Math]::PI * 2.0

for ($y = 0; $y -lt $Size; ++$y) {
    $v = $y / [double]$Size
    for ($x = 0; $x -lt $Size; ++$x) {
        $u = $x / [double]$Size

        $center = 0.52 + 0.17 * [Math]::Sin($pi2 * ($u + 0.14)) + 0.045 * [Math]::Sin($pi2 * ($u * 2.0 + 0.72))
        $delta = Frac($v - $center + 0.5) - 0.5
        $distance = [Math]::Abs($delta)
        $width = 0.070 + 0.025 * ([Math]::Sin($pi2 * ($u * 3.0 + 0.20)) * 0.5 + 0.5)

        $n1 = [Math]::Sin($pi2 * ($u * 3.0 + $v * 2.0 + 0.17))
        $n2 = [Math]::Sin($pi2 * ($u * -5.0 + $v * 4.0 + 0.61))
        $n3 = [Math]::Sin($pi2 * ($u * 9.0 + $v * -7.0 + 0.31))
        $noise = [Math]::Max(0.0, [Math]::Min(1.0, 0.52 + 0.25 * $n1 + 0.16 * $n2 + 0.08 * $n3))

        $softBand = [Math]::Exp(-(($distance * $distance) / (2.0 * $width * $width)))
        $coreBand = [Math]::Exp(-(($distance * $distance) / (2.0 * ($width * 0.36) * ($width * 0.36))))
        $idx = $y * $Size + $x

        $g[$idx] = [float][Math]::Min(1.0, ($softBand * (0.35 + 0.45 * $noise)) + ($coreBand * 0.35 * $noise))
        $a[$idx] = [float][Math]::Min(1.0, $g[$idx] * 0.36)
    }
}

# Fine field stars.
for ($i = 0; $i -lt 5400; ++$i) {
    $cx = $rand.NextDouble() * $Size
    $cy = $rand.NextDouble() * $Size
    $radius = 0.45 + $rand.NextDouble() * 0.95
    $strength = 0.25 + $rand.NextDouble() * 0.75
    Add-WrappedGaussian $r $Size $cx $cy $radius $strength
    Add-WrappedGaussian $a $Size $cx $cy ($radius * 1.7) ($strength * 0.30)
}

# Denser fine stars along the Milky Way band.
for ($i = 0; $i -lt 3800; ++$i) {
    $u = $rand.NextDouble()
    $center = 0.52 + 0.17 * [Math]::Sin($pi2 * ($u + 0.14)) + 0.045 * [Math]::Sin($pi2 * ($u * 2.0 + 0.72))
    $cyNorm = Frac($center + ($rand.NextDouble() - 0.5) * 0.22)
    $cx = $u * $Size
    $cy = $cyNorm * $Size
    $radius = 0.35 + $rand.NextDouble() * 0.85
    $strength = 0.28 + $rand.NextDouble() * 0.72
    Add-WrappedGaussian $r $Size $cx $cy $radius $strength
    Add-WrappedGaussian $a $Size $cx $cy ($radius * 1.8) ($strength * 0.25)
}

# Larger hero stars and glows.
for ($i = 0; $i -lt 90; ++$i) {
    $cx = $rand.NextDouble() * $Size
    $cy = $rand.NextDouble() * $Size
    $core = 1.1 + $rand.NextDouble() * 2.4
    $glow = 4.0 + $rand.NextDouble() * 10.0
    $strength = 0.45 + $rand.NextDouble() * 0.55
    Add-WrappedGaussian $r $Size $cx $cy $core $strength
    Add-WrappedGaussian $b $Size $cx $cy $glow ($strength * 0.90)
    Add-WrappedGaussian $a $Size $cx $cy ($glow * 1.1) ($strength * 0.38)
}

New-Item -ItemType Directory -Force -Path (Split-Path $OutputPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $PreviewPath) | Out-Null

$bitmap = [System.Drawing.Bitmap]::new($Size, $Size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$preview = [System.Drawing.Bitmap]::new($Size, $Size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)

for ($y = 0; $y -lt $Size; ++$y) {
    for ($x = 0; $x -lt $Size; ++$x) {
        $idx = $y * $Size + $x
        $rr = [int][Math]::Round([Math]::Min(1.0, $r[$idx]) * 255.0)
        $gg = [int][Math]::Round([Math]::Min(1.0, $g[$idx]) * 255.0)
        $bb = [int][Math]::Round([Math]::Min(1.0, $b[$idx]) * 255.0)
        $aa = [int][Math]::Round([Math]::Min(1.0, $a[$idx]) * 255.0)
        $bitmap.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($aa, $rr, $gg, $bb))

        $pr = [Math]::Min(255, [int]($rr + $bb * 0.8))
        $pg = [Math]::Min(255, [int]($gg * 1.15 + $rr * 0.18))
        $pb = [Math]::Min(255, [int]($bb + $gg * 0.85 + $rr * 0.35))
        $preview.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(255, $pr, $pg, $pb))
    }
}

$bitmap.Save((Resolve-Path -LiteralPath (Split-Path $OutputPath)).Path + "\" + (Split-Path $OutputPath -Leaf), [System.Drawing.Imaging.ImageFormat]::Png)
$preview.Save((Resolve-Path -LiteralPath (Split-Path $PreviewPath)).Path + "\" + (Split-Path $PreviewPath -Leaf), [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
$preview.Dispose()

Write-Output "Generated $OutputPath"
Write-Output "Generated $PreviewPath"
