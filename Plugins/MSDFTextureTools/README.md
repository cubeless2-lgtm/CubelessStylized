# MSDF Texture Tools

Editor-only Unreal Engine 5 plugin for generating MSDF Texture2D assets from clean alpha-mask textures such as logos, icons, UI masks, and single-color silhouettes.

## Installation

This plugin is installed at:

`Plugins/MSDFTextureTools`

It is enabled in `Cubeless_AI.uproject` for Editor targets only. Regenerate project files after adding the plugin, then build the Editor target.

## msdfgen executable

Version 0.1 uses an external `msdfgen` executable.

Expected Windows path:

`Plugins/MSDFTextureTools/ThirdParty/msdfgen/Win64/msdfgen.exe`

Build msdfgen from its upstream source or download a compatible binary, then place the executable at that path. The plugin keeps conversion behind `IMSDFTextureBackend`, so the external process backend can later be replaced with an embedded C++ library backend.

## Usage

1. Select a `Texture2D` asset in Content Browser.
2. Right-click the asset.
3. Choose `Generate MSDF Texture...`.
4. Adjust output resolution, threshold, invert alpha, padding, pxRange, edge coloring mode, preview/debug options, and output folder.
5. Press `Generate`.

If the source asset is `T_Icon`, the new asset name starts as `T_Icon_MSDF`. If that name already exists, Unreal creates a unique suffix.

Generated texture settings:

- `sRGB = false`
- `Compression Settings = VectorDisplacementmap`
- `Mip Gen Settings = NoMipmaps`
- `Texture Group = UI`
- `Never Stream = true`

## Source Image Limits

Best input:

- Alpha-channel logos
- Icons
- UI masks
- Single-color silhouettes
- Clean high-contrast shapes

Poor input:

- Photos
- Complex color art
- Noisy images
- Soft transparent gradients
- Tiny masks with many disconnected pixels

The tool warns when the foreground contains many distinct colors, because that usually means the input is not an MSDF-friendly silhouette.

## Pipeline

1. Reads `UTexture2D::Source` pixels.
2. Extracts alpha or grayscale data.
3. Applies threshold and optional alpha inversion.
4. Builds a binary mask.
5. Extracts contour edges from the mask.
6. Writes an SVG path into `Saved/MSDFTextureTools/...`.
7. Calls external `msdfgen`.
8. Decodes the generated PNG.
9. Creates and saves a new `UTexture2D` asset.
10. Selects the generated asset in Content Browser.

When `Save Debug Files` is enabled, temporary SVG and PNG files are kept under `Saved/MSDFTextureTools`.

## Material Formula

Use the RGB median value to restore signed distance:

```hlsl
float Median(float r, float g, float b)
{
    return max(min(r, g), min(max(r, g), b));
}

float sd = Median(MSDF.r, MSDF.g, MSDF.b) - 0.5;
float alpha = smoothstep(-Softness, Softness, sd);
float outline = smoothstep(-OutlineWidth - Softness, -OutlineWidth + Softness, sd);
float glow = 1.0 - smoothstep(0.0, GlowSize, abs(sd));
```

Recommended material setup:

- Domain: Surface or User Interface depending on use case
- Shading Model: Unlit
- Blend Mode: Translucent or Masked
- Texture sample: `Sampler Type = Linear Color`
- Parameters: `Softness`, `OutlineWidth`, `GlowSize`, `FillColor`, `OutlineColor`, `GlowColor`

## Current Limitations

- The preview panes are placeholders in this first version. Debug SVG/PNG output is available for inspection.
- The raster-to-SVG contour extraction is intentionally simple and optimized for clean masks, not photographic or noisy textures.
- `msdfgen.exe` is not bundled.
- Source texture data must be available in the asset.
- Supported source formats are `BGRA8`, `G8`, `G16`, and `RGBA16`.
