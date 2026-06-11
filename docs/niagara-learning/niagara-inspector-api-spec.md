# Niagara Inspector API Spec

This document defines the future C++ or editor-backed UnrealMCP API needed before the generative Niagara pipeline should perform deep edits.

The current branch does not implement these APIs. It defines the contract so the implementation can be added later without guessing.

## Goals

- Read Niagara assets structurally instead of guessing from names.
- Keep original assets read-only during inspection.
- Return JSON that can feed the structural signature index and generation recipe builder.
- Expose enough data to reason about Scratch Pads, Blueprint/User parameter linkage, renderers, materials, and validation.

## Non-Goals For The First API

- No source asset modification.
- No emitter add/remove.
- No Scratch Pad creation.
- No material replacement.
- No production asset saving.

Those belong to later Safe Edit APIs.

## API 1: `analyze_niagara_system`

### Request

```json
{
  "system_path": "/Game/Path/NS_System.NS_System",
  "include_emitters": true,
  "include_renderers": true,
  "include_user_parameters": true,
  "include_scratch_pads": true,
  "include_module_stack": true,
  "include_dependencies": true,
  "compile_check": false
}
```

### Response

```json
{
  "ok": true,
  "system_path": "/Game/Path/NS_System.NS_System",
  "asset_class": "NiagaraSystem",
  "source_policy": "read_only",
  "emitters": [
    {
      "name": "Emitter",
      "enabled": true,
      "source_emitter_path": "/Game/Path/NE_Source.NE_Source",
      "simulation_target": "CPUSim",
      "renderer_properties": [
        {
          "renderer_type": "Sprite",
          "material": "/Game/Path/MI_FX.MI_FX",
          "sort_mode": "ViewDepth",
          "bindings": []
        }
      ],
      "user_parameters_read": [
        "User.Gen_Color"
      ],
      "data_interfaces": [
        {
          "name": "User.RenderTarget",
          "type": "RenderTarget2D"
        }
      ],
      "scratch_pads": [
        {
          "name": "SP_RadialBurstVelocity",
          "stage": "Particle Spawn",
          "inputs": [
            {
              "name": "Speed",
              "type": "float"
            }
          ],
          "outputs": [
            {
              "name": "Particles.Velocity",
              "type": "float3"
            }
          ],
          "is_local_to_asset": true
        }
      ],
      "module_stack": {
        "system_spawn": [],
        "system_update": [],
        "emitter_spawn": [],
        "emitter_update": [],
        "particle_spawn": [
          "InitializeParticle",
          "AddVelocity"
        ],
        "particle_update": [
          "ScaleColor",
          "ScaleSpriteSize"
        ],
        "render": [
          "SpriteRenderer"
        ]
      },
      "coverage_notes": []
    }
  ],
  "system_user_parameters": [
    {
      "name": "User.Gen_Color",
      "type": "LinearColor",
      "default_value": null,
      "is_bp_safe_to_set": true
    }
  ],
  "dependencies": {
    "materials": [],
    "textures": [],
    "meshes": [],
    "parameter_collections": [],
    "blueprints": []
  },
  "compile": {
    "checked": false,
    "error_count": null,
    "warning_count": null,
    "messages": []
  },
  "dirty_source_assets_after_inspection": []
}
```

## Required Field Semantics

### `source_policy`

Must be `read_only` for inspection. The implementation must not call save on the inspected source.

### `dirty_source_assets_after_inspection`

Must be reported even if empty. If inspection dirties a source asset, that is a bug and generation must stop.

### `coverage_notes`

Use this when the API can only partially inspect a system.

Examples:

- `renderer material unavailable through current API`
- `scratch pad inputs not exposed`
- `module stack names only; no parameter values`

Partial data is better than a failed call as long as the limitation is explicit.

## API 2: `analyze_niagara_references`

Batch wrapper for multiple systems.

### Request

```json
{
  "system_paths": [
    "/Game/A.A",
    "/Game/B.B"
  ],
  "options": {
    "include_scratch_pads": true,
    "compile_check": false
  }
}
```

### Response

```json
{
  "ok": true,
  "results": [],
  "failed": []
}
```

## API 3: `compile_niagara_system`

This can be implemented after read-only inspection.

### Request

```json
{
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "save_on_success": false
}
```

### Rules

- Only compile generated or duplicate assets by default.
- Refuse source paths outside `/Game/_MCP_Temp/` unless a later production workflow explicitly allows it.
- Return structured errors.

## API 4: `preview_niagara_system_in_review_map`

Future validation API.

### Request

```json
{
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "review_map": "/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'",
  "bookmarks": [1, 2, 3],
  "capture_times_seconds": [0.5, 1.0, 2.0],
  "output_dir": "Saved/MCP_NiagaraPreview/Test"
}
```

### Required Behavior

- Load the Niagara review map.
- Spawn the system in the predefined review location.
- Capture screenshots from bookmarks 1, 2, and 3.
- Report missing bookmark or screenshot failure explicitly.
- Do not save the review map unless a separate workflow explicitly asks for it.

## API 5: Safe Edit APIs

These are not first-step APIs, but the Inspector should be designed so these can be added later.

Needed later:

- `duplicate_niagara_system`
- `set_niagara_user_parameter_default`
- `set_niagara_renderer_material`
- `add_niagara_emitter`
- `remove_niagara_emitter`
- `duplicate_material_instance_for_fx`
- `list_niagara_scratch_pads`
- `create_niagara_scratch_pad_module`
- `add_scratch_pad_to_emitter`

## Scratch Pad Rules

First pass:

- Read Scratch Pad names, stage, inputs, outputs, and whether they are local.
- Treat Scratch Pads as owning-emitter/system behavior.
- Reuse by duplicating the owning asset first.

Do not:

- Extract local Scratch Pads into shared modules automatically.
- Rename Scratch Pad inputs.
- Generate Scratch Pad graph nodes until the Inspector can validate existing Scratch Pads reliably.

## Blueprint/User Parameter Linkage Rules

Inspector should preserve enough names for BP safety:

- All `User.*` parameters found on the system.
- Data interface parameters such as RenderTargets, StaticMesh, SkeletalMesh, Actor, Component, or Position arrays.
- Any parameter likely set from BP or AnimNotify should be tagged as `runtime_input_candidate`.

Generation rule:

- Existing `User.*` names must be preserved.
- New generator-owned values use `User.Gen_*`.

## Material Rules

Inspector should return renderer material references.

Material graph analysis can be a separate API, but the Niagara response should at least expose:

- renderer material path
- renderer type
- whether the renderer appears to use dynamic material parameters
- material slot/index if available

## Review Map Rule

All preview APIs use:

```text
/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'
```

Bookmark meanings:

- 1: near
- 2: mid
- 3: far

Any generated Niagara validation must include all three bookmark views or report why a capture is missing.

## Implementation Notes For Tivret

- Start read-only.
- Return partial data with `coverage_notes` instead of crashing.
- Avoid direct source asset saves.
- Check dirty packages before and after inspection.
- Keep command output stable and schema-friendly.
- Prefer adding Niagara-specific command files over modifying shared PCG command code while PCG C++ work is active elsewhere.
