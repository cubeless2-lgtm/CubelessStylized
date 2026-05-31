# Cubeless Light-Packed Cloud Plane Workflow

This workflow keeps Ultra Dynamic Sky assets untouched. All editable assets live under `/Game/Cubeless/Env/Sky`.

## Asset Layout

- Source RGBA atlas: `SourceArt/Sky/CloudPlaneAtlas_RGBA_2048.png`
- Source light-packed atlas: `SourceArt/Sky/CloudPlaneAtlas_LightPacked_UDSLike_RGBA_2048.png`
- Unreal packed texture: `/Game/Cubeless/Env/Sky/Textures/T_CloudPlaneAtlas_LightPacked_UDSLike`
- Master material: `/Game/Cubeless/Env/Sky/Materials/M_CloudPlane_LightPacked_Master`
- Tile material instances: `/Game/Cubeless/Env/Sky/Materials/MI_CloudPlane_LightPacked_Tile_00` through `_07`
- Single-plane prefab: `/Game/Cubeless/Env/Sky/Blueprints/BP_CloudPlane_LightPacked`
- Multi-plane field preset: `/Game/Cubeless/Env/Sky/Blueprints/BP_CloudField_LightPacked_Preset`
- UDS static-sky material generator: `SourceArt/Sky/create_uds_static_cloud_placard_material.py`

## Keilan Image Generation Brief

Keilan owns future image-generation work for this cloud source art. Ieta records Keilan's output and keeps the project documents, Notion summaries, source-art paths, and texture-packing notes aligned. Tivret handles Unreal import, material hookup, and asset verification when implementation is requested.

The target use case is Ultra Dynamic Sky static-cloud texture work, so generated cloud art must be designed for Polar/Radial UV sampling rather than a normal flat viewport composition.

Current Polar/Radial UV reference:

- `/Script/Engine.Texture2D'/Game/UltraDynamicSky/Textures/StaticClouds/Custom/cloub02.cloub02'`
- Local file: `Content/UltraDynamicSky/Textures/StaticClouds/Custom/cloub02.uasset`
- Use this as the latest visual standard for cloud shape, radial readability, and projection behavior.
- Treat it as a reference only. Do not overwrite or modify UDS reference assets while generating Cubeless source art.

Generation requirements:

- Draw clouds so they remain readable after polar/radial projection.
- Avoid hard seams across radial wrap boundaries.
- Keep alpha edges soft enough for sky blending.
- Preserve useful internal density and underside variation so the packing pass can derive lighting response.
- Do not bake final day/sunset/night color into the source. The material applies lighting color later.
- Prefer broad, sky-scale cloud masses and wispy breakup over near-camera card silhouettes.

Keilan deliverables:

- Source image intent and prompt notes.
- Expected radial/polar UV behavior.
- RGBA channel-packing notes.
- Preview expectation for day/sunset/night readability.
- Any risks, such as seam visibility, overly dense alpha, or detail that will collapse after radial sampling.

Keilan handoff template:

```text
Target: UDS static cloud texture, Polar/Radial UV.
Source intent: [cloud type, density, mood, scale]
Projection notes: [center/edge behavior, radial wrap seam handling]
Packing contract: R=upper-right key, G=upper-left key, B=overhead/front fill, A=opacity/density
Alpha notes: [soft edge, density range, transparent areas]
Preview checks: [day readability, sunset readability, night readability]
Risks: [seams, overpainted final color, crushed alpha, noisy detail]
```

## Packed Texture Contract

- `R`: upper-right key light response
- `G`: upper-left key light response
- `B`: overhead/front fill response
- `A`: original opacity/density

The material blends the packed lighting channels with `LightWeights_RGB`, then colors that response through `CloudShadowTint`, `CloudLightTint`, `TimeOfDayTint`, and a small `AmbientColor` lift.

It also reads UDS Material Parameter Collections directly where UDS exposes runtime cloud state:

- `/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters`: `Sun Vector`, `Cloud Coverage`
- `/Game/UltraDynamicSky/Materials/Material_Functions/UDS_VolumetricClouds_MPC`: `Cloud Density`, `Cloud Coverage Target Opacity`, `Cloud Shadows Light Vector`, `Cloud Shadows Cancel`

The MPC inputs are blended through `MPCSunVectorInfluence`, `MPCCloudDensityInfluence`, `MPCCloudCoverageInfluence`, and `MPCShadowCancelInfluence`. Static-sky sampled values remain as fallback so cards do not disappear when an MPC value is zero.

The current `uds_static_sky` preset was sampled from the placed `Ultra_Dynamic_Sky` actor's sky MID while UDS static sky/static clouds were active:

- `LightWeights_RGB`: `(0.586461, 0.340078, 0.073461)`
- `CloudShadowTint`: UDS `Static Clouds Color Tint` `(0.701009, 0.702989, 0.760417)`
- `CloudLightTint`: UDS `Static Clouds Shadow Tint` `(0.869251, 0.840228, 0.815230)`
- `CloudDensity`: `1.596`
- `SunLightingIntensity`: `3.0`

## Placement

Use `BP_CloudPlane_LightPacked` for one cloud plane at a time, or drag `BP_CloudField_LightPacked_Preset` into the level for a ready-made 8-plane arc.

For hand placement:

1. Place a plane-facing actor in the sky composition.
2. Assign one of `MI_CloudPlane_LightPacked_Tile_00` through `_07`.
3. Rotate and scale the plane to match the desired sky direction.
4. Keep shadow casting disabled for these stylized translucent planes.
5. Increase translucency sort priority if the planes need deterministic overlap.

## Art Direction Presets

Preset data lives in:

- `SourceArt/Sky/cloud_plane_art_direction_presets.json`

The Unreal Python batch applier lives in:

- `SourceArt/Sky/apply_cloud_plane_art_direction.py`

Run it inside Unreal Python with one preset name:

```python
import sys

script_path = r"D:\Git\CubelessStylized\SourceArt\Sky\apply_cloud_plane_art_direction.py"
sys.argv = [script_path, "sunset_warm"]
namespace = {"__file__": script_path, "__name__": "__main__"}
with open(script_path, "r", encoding="utf-8") as handle:
    exec(compile(handle.read(), script_path, "exec"), namespace)
```

Available initial presets:

- `uds_static_sky`
- `day_soft`
- `sunset_warm`
- `moon_cool`

## Guardrails

- Do not save or modify assets under `/Game/UltraDynamicSky`.
- Do not use the UnrealMCP `add_blueprint_variable` helper on path-qualified Blueprint names; it previously produced an invalid `/Game/Blueprints//Game/...` path.
- Use material instances or Unreal Python for batch edits until a dedicated Cubeless Blueprint automation path is added.
