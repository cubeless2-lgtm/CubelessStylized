# Generative Niagara Implementation Plan

## Goal

Build a safe generative Niagara workflow for CubelessStylized:

`natural language request -> reference analysis -> style and structure recipe -> temporary Niagara generation -> validation -> review -> optional production promotion`

The generator must not rely only on asset names. It must learn from project sources:

- Niagara Systems and Emitters
- Scratch Pad modules
- Blueprint and AnimNotify user parameter usage
- FX Materials, Material Instances, Textures, and Meshes
- Existing stylized visual language

## Non-Negotiable Rules

- Original Niagara, Material, Blueprint, and source-art assets are read-only references.
- Temporary generated assets go under `/Game/_MCP_Temp/NiagaraGenerated/`.
- Production assets require a review gate before moving to `/Game/Cubeless/FX/Generated/`.
- Every generation request must produce a reference analysis before asset generation.
- If a Blueprint or AnimNotify expects an existing `User.*` parameter, preserve that parameter name.
- New generator-owned parameters use `User.Gen_*`.
- Scratch Pad logic is reused by duplicating its owning System or Emitter first. Standalone Scratch Pad extraction is a later step.
- All new or modified Niagara assets must be tested through Niagara Preview Lab in the dedicated map:
  `/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'`.
- Do not reload the Niagara Preview Lab map from the same Unreal Python session after preview actors or world references have existed. Reuse the loaded map, clean preview actors by prefix, and restart the editor if a full map reset is required.
- Niagara visual review screenshots must use editor camera bookmarks in that map:
  bookmark 1 = near view, bookmark 2 = mid view, bookmark 3 = far view.
  Default review captures one screenshot only: start from bookmark 1, fall back to bookmark 2 if the effect is too large, clipped, or not reviewable, and fall back to bookmark 3 only if bookmark 2 still fails.

## Current State

Already available:

- `docs/niagara-learning/niagara_asset_index.json`
- `docs/niagara-learning/niagara_generation_index.json`
- Natural-language duplicate planner on the `migration` branch

Current limitation:

- The first index is mostly name/path/dependency based.
- It does not deeply inspect emitter stacks, renderer properties, Scratch Pad inputs/outputs, or Blueprint call sites.
- The next C++ work should add Inspector APIs, but this branch intentionally starts with no C++ changes.

## Phase 0: No-C++ Planning And Prototype

Purpose:

- Prepare the data shape before touching UnrealMCP C++.
- Define what the future Inspector API must return.
- Produce a first structural signature index from existing dependency data.

Deliverables:

- `generative-niagara-implementation-plan.md`
- `schemas/niagara_structural_signature.schema.json`
- `schemas/niagara_generation_recipe.schema.json`
- `Tools/Unreal/niagara_structural_signature_builder.py`
- `docs/niagara-learning/niagara_structural_signature_index.json`

This phase is safe to run while another PC edits MCP C++ for PCG because it does not touch plugin code.

## Phase 1: Niagara Inspector API

First C++ or editor API target:

`analyze_niagara_system(system_path)`

Minimum response:

```json
{
  "system_path": "/Game/...",
  "emitters": [
    {
      "name": "EmitterName",
      "enabled": true,
      "renderer_types": ["Sprite", "Ribbon", "Mesh"],
      "renderer_materials": ["/Game/..."],
      "user_parameters_read": ["User.Color"],
      "user_parameters_written": [],
      "scratch_pads": [
        {
          "name": "SP_RadialBurst",
          "stage": "Particle Spawn",
          "inputs": ["Speed"],
          "outputs": ["Particles.Velocity"]
        }
      ],
      "module_stack": {
        "system_spawn": [],
        "system_update": [],
        "emitter_spawn": [],
        "emitter_update": [],
        "particle_spawn": ["InitializeParticle"],
        "particle_update": ["ScaleColor"]
      }
    }
  ],
  "compile": {
    "error_count": 0,
    "warning_count": 0
  }
}
```

티브렛 검토:

- Start read-only.
- Prefer stable public Niagara editor APIs.
- If the full stack is not accessible, return partial results with `coverage_notes`.
- Never save source assets during inspection.
- Keep the API output JSON-forward so the planner can consume it directly.

## Phase 2: Structural Signature Index

Goal:

Replace name-only matching with structure-aware matching.

Signature fields:

- `visual_roles`: ground area, lightning arc, spark spray, smoke volume, ribbon trail, burst impact
- `renderer_types`: sprite, ribbon, mesh, decal, unknown
- `motion`: radial expand, upward spark, falling, follow, swirl, static glow
- `timing`: instant burst, short burst, loop, lingering, weather loop
- `style_profiles`: EL stylized combat, UltraDynamicSky weather, UltraVolumetrics soft volume, Cubeless reactive
- `material_roles`: additive glow, stylized lightning, soft smoke, radial shockwave, ribbon slash
- `usable_as`: primary template, support layer, material source, primitive candidate, BP-driven source

No-C++ first pass:

- Derive coarse signatures from path/name/dependency/material/mesh hints.
- Mark confidence as `low` or `medium`.

Inspector-backed pass:

- Use actual emitter/render/module/Scratch Pad data.
- Raise confidence to `high` when verified.

## Phase 3: Blueprint/User Parameter Linkage

Why it matters:

Many production effects are controlled by Blueprint, AnimNotify, Components, or Material Parameter Collections. A generated effect can look right but break gameplay if these links are ignored.

Track:

- `User.*` parameter names
- Blueprint nodes that call `Set Niagara Variable`
- AnimNotify and AnimNotifyState payloads
- component-attached systems
- static mesh, skeletal mesh, actor, transform, socket, render target inputs
- Material Parameter Collections used by FX materials

Rules:

- Preserve existing `User.*` names on duplicated systems.
- Add generator parameters only with `User.Gen_*`.
- If a source is BP-driven, tag it as `bp_driven_source`.
- If a source requires a runtime RenderTarget, tag it as `runtime_input_required`.

티브렛 검토:

- The first pass can search Blueprint dependencies and strings without editing BP assets.
- Deep Blueprint graph analysis can be added later through UnrealMCP Blueprint APIs.
- Do not rename user parameters on source or duplicate assets unless a recipe explicitly asks for it.

## Phase 4: Material Style Index

Stylized Niagara depends heavily on materials.

Analyze:

- Blend Mode: Additive, Translucent, Masked, Opaque
- Shading model and material domain
- Emissive/Opacity wiring
- Dynamic Material Parameter usage
- texture roles: noise, gradient, mask, flipbook, lightning, smoke, spark
- panner/rotator/fresnel/depth fade usage
- mesh/ribbon/sprite compatibility

Material tags:

- `additive_glow`
- `soft_translucent_smoke`
- `stylized_lightning`
- `radial_shockwave`
- `ribbon_slash`
- `spark_sprite`
- `fire_flipbook`
- `decal_crack`
- `dissolve_noise`
- `mesh_ring`

Strategy:

- Prefer existing Material Instances first.
- Duplicate an MI and tune parameters before creating a new master.
- Create common stylized master materials only for missing primitives.

## Phase 5: Primitive Kit

Needed for "make something that does not already exist".

Initial primitives:

- `NS_Primitive_SpriteBurst`
- `NS_Primitive_RingShockwave`
- `NS_Primitive_RibbonTrail`
- `NS_Primitive_BeamLightning`
- `NS_Primitive_SparkSpray`
- `NS_Primitive_SmokePuff`
- `NS_Primitive_GroundGlow`
- `NS_Primitive_MeshRing`

Each primitive needs:

- preview-safe scale
- one clear renderer role
- one default material
- `User.Gen_*` exposed controls
- compile validation
- metadata entry in the structural signature index

## Phase 6: Recipe Generator

The generator does not create immediately. It first writes a recipe:

```json
{
  "request": "black lightning field with purple sparks",
  "layers": [
    {
      "role": "primary_area",
      "source": "/Game/...",
      "operation": "duplicate_system"
    },
    {
      "role": "spark_support",
      "source": "/Game/...",
      "operation": "copy_or_add_emitter"
    }
  ],
  "material_plan": [
    {
      "role": "lightning_arc",
      "source_material": "/Game/...",
      "operation": "duplicate_mi_and_tint"
    }
  ],
  "parameters": {
    "User.Gen_Color": [0.45, 0.05, 1.0, 1.0],
    "User.Gen_Duration": 2.0
  }
}
```

Review before execution:

- Does each layer have a clear visual purpose?
- Are all sources read-only?
- Does any source require BP/runtime input?
- Are missing primitives explicit?

## Phase 7: Safe Generator

Execution ladder:

1. Duplicate source system only.
2. Duplicate/tune Material Instance only.
3. Set exposed `User.Gen_*` parameters.
4. Replace renderer material on duplicate only.
5. Add/remove emitters on duplicate only.
6. Reuse Scratch Pad by duplicating owning emitter/system.
7. Generate new Scratch Pad only after Inspector APIs are stable.

Validation:

- load duplicate
- compile or gather compile status
- check dependency missing state
- spawn preview actor
- open `/Game/SampleTestMap/Niagara_TestMap`
- never reload the same Niagara Preview Lab map after preview actors or Python world references exist
- capture a quick preview from the first reviewable bookmark in the 1 -> 2 -> 3 fallback sequence
- capture all three bookmarks only for explicit distance-comparison or formal scale-review requests
- capture a frame sequence for timing-sensitive effects such as sword trails, slash ribbons, projectile trails, dissolve timing, and hit bursts
- report dirty source assets

## Niagara Preview Lab Map

All generated Niagara validation uses this fixed Niagara Preview Lab map:

```text
/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'
```

Camera bookmark policy:

- Bookmark 1: near view
- Bookmark 2: mid view
- Bookmark 3: far view

Default review output should include one selected screenshot from the first reviewable bookmark. If a Niagara effect is too small, too large, off-center, too dim, or only readable from one distance, the report must call that out instead of treating the preview as passed.

Use bookmark 1 first. If the effect is too large, clipped, not visible, or cannot be judged, use bookmark 2. If bookmark 2 is still not visible or reviewable, use bookmark 3. Record which bookmark was used for the selected preview image. Do not capture all three bookmarks unless the review specifically needs near/mid/far comparison.

For timing-sensitive effects, also capture a short frame sequence. Convert the sequence to video only after the PNG frames are verified.

This applies to:

- duplicated template tests
- generated primitive tests
- material replacement tests
- Scratch Pad behavior tests
- final production promotion reviews

## Phase 8: Scratch Pad Generation

Scratch Pad generation is a late-stage feature.

Prepare first:

- catalog existing Scratch Pads
- identify repeated useful behaviors
- map Scratch Pad inputs/outputs
- test module creation in `_MCP_Temp`

Candidate generated Scratch Pads:

- `NMS_Gen_RadialBurstVelocity`
- `NMS_Gen_UpwardSparkVelocity`
- `NMS_Gen_RingExpandScale`
- `NMS_Gen_StylizedColorOverLife`
- `NMS_Gen_AlphaFadeSoft`
- `NMS_Gen_MaterialParamPulse`
- `NMS_Gen_OrbitSwirlVelocity`
- `NMS_Gen_GroundPlaneConstrain`

Do not make Scratch Pad generation the first implementation target. It is powerful, but it is also the easiest place to create brittle Niagara graphs.

## Human Review Workflow

The user does not need to classify modules.

User input can be:

```text
12 = 푸른 번개 장판
18 = 검기 잔상 / 플레이어 베기
31 = 불씨 튐 / 횃불 보조
```

The system converts that into:

- display name
- aliases
- visual roles
- style profile
- source usability
- recipe hints

## Recommended Next Work

1. Generate first structural signature index from the current asset index.
2. Review the signature fields and schema.
3. Add no-C++ material style inference from current dependencies.
4. Wait for the other PC's PCG MCP C++ work to settle.
5. Add Niagara Inspector API in a separate C++ branch.
