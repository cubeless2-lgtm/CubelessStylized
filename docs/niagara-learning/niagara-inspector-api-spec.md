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

## Preview Player Editor Commands

These commands support the level-independent Niagara Preview Player UI. They are
not deep Niagara inspection APIs; they provide the interaction surface that lets
the user or Codex choose a source by drag-and-drop before later analysis or
generation starts.

### `open_niagara_preview_player`

Opens the Slate Preview Player window. The current implementation is a drop
surface MVP and must not save or mutate source assets.

### `get_niagara_preview_player_state`

Returns window/drop state:

```json
{
  "success": true,
  "window_open": true,
  "player_mode": "drop_surface_mvp",
  "drop_count": 1,
  "last_drop_kind": "asset",
  "last_display_name": "NS_Slash",
  "last_object_path": "/Game/FX/NS_Slash.NS_Slash",
  "last_class_name": "/Script/Niagara.NiagaraSystem"
}
```

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

## Implemented Read API: `inspect_niagara_module_inputs`

This is the first implemented module-input candidate API. It is intentionally
read-only and intended to feed generation planning and the Niagara Preview
Player analysis panel.

### Request

```json
{
  "system_path": "/Game/Path/NS_System.NS_System",
  "include_linked_sources": true,
  "include_resolved_stack_inputs": true,
  "max_modules": 120,
  "max_candidates_per_module": 16,
  "max_resolved_inputs_per_module": 8,
  "max_top_candidates": 20
}
```

### Response Shape

```json
{
  "success": true,
  "system_path": "/Game/Path/NS_System.NS_System",
  "emitter_count": 5,
  "module_count": 70,
  "candidate_count": 283,
  "top_candidate_count": 20,
  "include_resolved_stack_inputs": true,
  "can_author_module_inputs": false,
  "authoring_status": "read_only; use this result as generation planning input before enabling temp-asset module writes",
  "emitters": [
    {
      "name": "Emitter",
      "emitter_index": 0,
      "enabled": true,
      "module_count": 15,
      "modules_truncated": false,
      "modules": [
        {
          "function_name": "ScaleColor",
          "node_guid": "...",
          "input_candidate_count": 5,
          "resolved_stack_inputs_enabled": true,
          "resolved_stack_input_count": 2,
          "input_candidates": [
            {
              "emitter_name": "Emitter",
              "module_name": "ScaleColor",
              "pin_name": "ScaleRGB",
              "control_kind": "color",
              "priority": 100,
              "default_value": "true",
              "linked_to_count": 0,
              "can_author_now": false
            }
          ],
          "resolved_stack_inputs": [
            {
              "variable": {
                "name": "Module.Spawn Count",
                "type": "Int 32"
              },
              "is_hidden": false,
              "value_source": "rapid_iteration",
              "rapid_iteration_parameter": {
                "name": "Constants.Emitter.SpawnBurst_Instantaneous.Spawn Count",
                "type": "Int 32",
                "has_value": true,
                "value": 1
              },
              "can_author_now": false
            }
          ]
        }
      ]
    }
  ],
  "top_candidates": []
}
```

### Current Semantics

- The command reads function-call input pins from emitter graph sources.
- When `include_resolved_stack_inputs=true`, it also uses Niagara Stack graph
  utilities to read module input variables and RapidIteration values where
  available.
- Low-signal graph plumbing pins such as `InputMap`, `OutputMap`, parameter-map
  pins, and `Write Parameter Index` toggles are filtered out.
- Candidate priority favors generation-relevant modules such as `ScaleColor`,
  `DynamicMaterialParameters`, `ScaleMeshSize`, `AddVelocity`, and
  `SpawnBurst_Instantaneous`.
- `can_author_module_inputs` is currently `false`. This API is not yet allowed
  to write rapid-iteration values or module override pins.
- Resolved stack input readback is intentionally capped. Use
  `max_resolved_inputs_per_module` and avoid uncapped UI calls.

### Known Gap

The command now resolves many RapidIteration values, but does not yet resolve
every default source exactly as the Niagara Stack UI displays it. Unresolved
defaults, dynamic inputs, and complex data interfaces still need more mapping
before safe temp-asset module writing is enabled.

## Implemented Safe Edit API: `set_niagara_module_input_value`

This is the first module-input write API. It only edits existing RapidIteration
parameters and refuses source Niagara systems by default.

### Request

```json
{
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "emitter_name": "FX_E_SwordTrail04_L",
  "module_name": "SpawnBurst_Instantaneous",
  "input_name": "Spawn Count",
  "value": 2,
  "save": true
}
```

Supported selectors:

- `emitter_name` or `emitter_index`
- `module_name`, `module_index`, or `module_node_guid`
- `input_name`, with either `Spawn Count` or `Module.Spawn Count`

### Response Shape

```json
{
  "success": true,
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "emitter_name": "FX_E_SwordTrail04_L",
  "emitter_index": 0,
  "module_name": "SpawnBurst_Instantaneous",
  "module_node_guid": "...",
  "module_index": 1,
  "input_name": "Module.Spawn Count",
  "input_type": "Int 32",
  "rapid_iteration_parameter": {
    "name": "Constants.FX_E_SwordTrail04_L.SpawnBurst_Instantaneous.Spawn Count",
    "type": "Int 32",
    "has_data": true,
    "value": 2
  },
  "previous_value": 1,
  "new_value": 2,
  "saved": true,
  "write_scope": "existing_rapid_iteration_parameter_only"
}
```

### Safety Rules

- Default write scope is `/Game/_MCP_Temp/NiagaraGenerated/` only.
- Source Niagara systems are rejected unless `allow_source_edit=true` is
  explicitly passed.
- The command refuses to create a new override. It only edits an existing
  RapidIteration value found by resolved stack input readback.
- Supported first-pass types are float, int, bool, color, vec2, vec3, vec4, and
  position.
- Complex data interfaces, dynamic inputs, unresolved defaults, and new
  override-pin creation are intentionally deferred.

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

## API 4: `preview_niagara_system_in_preview_lab`

Future validation API.

### Request

```json
{
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "preview_system": "Niagara Preview Lab",
  "review_map": "/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'",
  "views": [1, 2, 3],
  "camera_mode": "auto_preview_actor_frame",
  "quick_preview_fallback": [1, 2, 3],
  "capture_mode": "still",
  "capture_times_seconds": [0.5, 1.0, 2.0],
  "output_dir": "Saved/MCP_NiagaraPreview/Test"
}
```

### Required Behavior

- Use the Niagara Preview Lab map.
- Spawn the system in the predefined review location.
- Default quick review captures one screenshot only: capture from auto-framed view 1 first, then use view 2 if the effect is too large, clipped, invisible, or not reviewable, then view 3 if view 2 is still not reviewable.
- Capture views 1, 2, and 3 only when the request explicitly needs near/mid/far comparison or formal scale evidence.
- For timing-sensitive Niagara systems, capture a PNG frame sequence first. MP4/video export is a second step after frame output is verified.
- Report camera framing fallback or screenshot failure explicitly.
- Do not save the Niagara Preview Lab map unless a separate workflow explicitly asks for it.
- Do not reload the same Niagara Preview Lab map from the same Unreal Python session after preview actors, world objects, callbacks, or capture tasks have existed. This can trigger Unreal `World Memory Leaks` fatal shutdown. If a reset is required, restart the editor and open the map fresh.

## API 5: Safe Edit APIs

These are not first-step APIs, but the Inspector should be designed so these can be added later.

Needed later:

- `duplicate_niagara_system`
- `set_niagara_renderer_material`
- `inspect_niagara_user_parameters`
- `set_niagara_user_parameter`
- `inspect_niagara_stack`
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

Current read-only stack inspector:

- `inspect_niagara_stack(system_path, include_pins=false, max_function_calls=200)`
- Returns system spawn/update graphs, emitter graph function calls, input/output node summaries, script usage summaries, and Scratch Pad script containers.
- The recipe builder stores a compact summary instead of the full graph dump.
- This is intended for classification and planning, not authoring.

## Blueprint/User Parameter Linkage Rules

Inspector should preserve enough names for BP safety:

- All `User.*` parameters found on the system.
- Data interface parameters such as RenderTargets, StaticMesh, SkeletalMesh, Actor, Component, or Position arrays.
- Any parameter likely set from BP or AnimNotify should be tagged as `runtime_input_candidate`.

Generation rule:

- Existing `User.*` names must be preserved.
- New generator-owned values use `User.Gen_*`, but adding them is useful only after a generated module or Scratch Pad actually reads them.
- First-pass generation should set only existing exposed `User.*` parameters on temp systems when type/name hints match safely.

## Material Rules

Inspector should return renderer material references.

Material graph analysis can be a separate API, but the Niagara response should at least expose:

- renderer material path
- renderer type
- whether the renderer appears to use dynamic material parameters
- material slot/index if available

## Niagara Preview Lab Map Rule

All preview APIs use:

```text
/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'
```

Bookmark meanings:

- 1: near, first quick-preview camera
- 2: mid, fallback when view 1 does not show the effect
- 3: far, fallback when view 2 still does not show the effect

Any generated Niagara validation should record the first reviewable auto-framed view selected from the 1 -> 2 -> 3 fallback sequence. Three-view capture is opt-in for distance comparison. Timing-sensitive validation should include a frame sequence or video artifact in addition to the selected still.

## Niagara Preview Lab MCP Commands

First-pass C++ MCP commands:

- `get_niagara_preview_lab_state`: report current map, dirty state, preview actor count, and whether editor restart is recommended.
- `cleanup_niagara_preview_lab`: delete `MCP_NiagaraPreviewLab_` preview actors and legacy `MCP_NiagaraReview_` actors without saving or reloading the map.
- `capture_niagara_preview_lab_view`: capture a clean PNG from view 1, 2, or 3. When preview actors exist, the command auto-frames them and treats the view number as a distance hint. Relative paths resolve under `Saved/MCP/NiagaraReviews`.
- `preview_niagara_system_in_preview_lab`: optimized default route for repeated reviews. It loads a read-only Niagara system, optionally cleans prior preview actors, spawns a transient preview actor, advances simulation for warmup, captures with auto framing, and optionally cleans up afterward.
- `sample_niagara_system_in_preview_lab`: optimized quality route for timing-sensitive or initially invisible effects. It captures multiple warmup/view candidates in one MCP round trip and returns per-sample PNG metadata.

These commands must never call `load_map` for the Preview Lab map. They either reuse the loaded map or return a structured error telling the caller to open/restart the editor.

## Implementation Notes For Tivret

- Start read-only.
- Return partial data with `coverage_notes` instead of crashing.
- Avoid direct source asset saves.
- Check dirty packages before and after inspection.
- Keep command output stable and schema-friendly.
- Prefer adding Niagara-specific command files over modifying shared PCG command code while PCG C++ work is active elsewhere.
