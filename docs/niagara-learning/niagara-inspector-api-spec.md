# Niagara Inspector API Spec

This document tracks the C++ or editor-backed UnrealMCP API needed before the generative Niagara pipeline should perform deep edits.

For the current implemented/planned/deferred capability boundary, start with
`docs/niagara-learning/niagara-mcp-capability-matrix.md`. This API spec keeps
the detailed command contracts and older design context.

## 2026-06-12 Current Implementation

Implemented in the sibling repository `C:\Git\unreal-mcp-cubeless` on branch
`codex/niagara-mcp-authoring`:

| Tool | Status | Scope |
| --- | --- | --- |
| `analyze_niagara_system` | implemented | read-only aggregation of renderer, User parameter, stack, graph, module input, and compile-health inspection |
| `inspect_niagara_renderers` | implemented | reads enabled renderer classes, material fields, material slots, and used materials |
| `set_niagara_renderer_material` | implemented | writes renderer material references, temp/generated assets only unless `allow_source_edit=true` |
| `duplicate_or_attach_emitter_from_source` | implemented | adds a source Niagara Emitter asset or source system emitter handle into a generated temp system |
| `inspect_niagara_user_parameters` | implemented | reads exposed `User.*` parameters and current values |
| `set_niagara_user_parameter` | implemented | writes supported bool, int, float, vector, color, and object-like user values |
| `inspect_niagara_stack` | implemented | reads system, emitter, and Scratch Pad function-call stack data |
| `inspect_niagara_graph` | implemented | reads full graph node, pin, and link topology for system scripts, emitter graphs, and Scratch Pad scripts |
| `inspect_niagara_compile_status` | implemented | reads per-script compile status, optionally requests temp-system compile, waits/polls outstanding requests, and reports error/warning/dirty state |
| `inspect_niagara_scratch_pad_interface` | implemented | reads Scratch Pad ownership, usage, supported usage contexts, inputs, outputs, and compact graph summaries |
| `create_or_duplicate_scratch_pad_module` | implemented | duplicates an existing Scratch Pad script into a generated temp system or emitter without stack insertion |
| `add_scratch_pad_module_to_stack` | implemented | inserts a target-local Module Scratch Pad into a compatible system/emitter stack in generated temp systems by default |
| `inspect_niagara_module_inputs` | implemented | reads module input candidates and optional resolved stack inputs |
| `create_niagara_module_input_override` | implemented | creates missing RapidIteration module input overrides on temp systems by default |
| `set_niagara_module_inputs_batch` | implemented | applies multiple RapidIteration module input edits with aggregated per-edit results |
| `set_niagara_module_input_value` | implemented | writes existing RapidIteration module input overrides only |

Still future work:

- New Scratch Pad graph/node creation and arbitrary Scratch Pad node wiring.
- Arbitrary graph node wiring.
- Emitter remove workflows and complex emitter merge conflict resolution.
- Graph-pin or dynamic-input authoring beyond RapidIteration parameter data.

Older sections below still describe the original target contract and are retained for design context.

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
surface plus renderable preview player and must not save or mutate source
assets. Passing `system_path` loads that Niagara System directly into the
Preview Player and returns the current Preview Player state.

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

## Implemented Read API: `analyze_niagara_system`

This is the read-only aggregation API for generation planning. It calls the
existing renderer, User parameter, stack, graph, module input, and compile
status inspectors and folds them into one response.

### Request

```json
{
  "system_path": "/Game/Path/NS_System.NS_System",
  "include_renderers": true,
  "include_user_parameters": true,
  "include_stack": true,
  "include_graph": true,
  "include_module_inputs": true,
  "include_compile_status": true,
  "include_pins": false,
  "include_links": false,
  "include_scratch_pads": true,
  "include_resolved_stack_inputs": false,
  "max_function_calls": 200,
  "max_nodes_per_graph": 300,
  "max_links_per_graph": 0,
  "max_modules": 200,
  "max_candidates_per_module": 24,
  "max_resolved_inputs_per_module": 8,
  "max_top_candidates": 80
}
```

### Response Shape

- `success`: true when the aggregation command itself completes.
- `read_only`: always true.
- `source_policy`: `read_only_analysis_no_save_no_compile_request`.
- `summary`: compact counts for renderers, User parameters, stack calls,
  Scratch Pads, graph topology, module input candidates, and compile health.
- `section_status`: boolean success for each included section.
- `limitations`: section-level errors, if an included inspector could not
  complete.
- Included payloads: `renderers`, `user_parameters`, `stack`, `graph`,
  `module_inputs`, and `compile_status` when requested.

### Safety

- Does not save, mutate assets, or request compile.
- Compile status is inspected with `request_compile=false` and
  `wait_for_completion=false`.
- Graph defaults are summary-oriented: `include_pins=false`,
  `include_links=false`, and `max_links_per_graph=0` unless the caller asks for
  more detail.

### Verification

- Sibling `MCPGameProjectEditor Win64 Development -NoHotReloadFromIDE` build
  succeeded after adding the command and bridge route.
- Cubeless `StylizedCubelessEditor Win64 Development -NoHotReloadFromIDE` build
  linked successfully after closing the running editor that held
  `UnrealEditor-UnrealMCP.dll`.
- Runtime smoke on `FX_S_Parry03` returned all six sections successful and wrote
  `Saved/MCP_NiagaraGeneration/analyze_niagara_system_smoke.json`.
- The smoke summary reported `2` renderers, `40` stack calls, `4` graphs,
  `104` graph nodes, `219` module input candidates, `10` compile scripts, and
  compile errors/warnings/dirty all `0`.

## Implemented Read API: `inspect_niagara_graph`

This is the first graph-topology API for Niagara MCP. It is read-only and
exists to make future safe graph authoring possible without guessing from stack
summaries alone.

### Request

```json
{
  "system_path": "/Game/Path/NS_System.NS_System",
  "include_pins": true,
  "include_links": true,
  "include_scratch_pads": true,
  "max_nodes_per_graph": 600,
  "max_links_per_graph": 2000
}
```

### Executor Preview Gate

`Tools/Unreal/niagara_generation_recipe_executor.py` now uses the Preview Player
commands as a generated-temp validation gate:

- `--socket-validate-preview-only`
- automatic final Preview Player validation during `--socket-postprocess-only`

The gate opens the generated temp system in the Preview Player, records the
renderability/playback/analysis state returned by `open_niagara_preview_player`,
captures multiple actual `Niagara Preview Player` OS-window candidates through
`Tools/Unreal/capture-unreal-editor-window.ps1`, selects the best frame by a
viewport brightness/readability score, and writes candidate paths/scores plus
the selected screenshot into the execution report.

`get_niagara_preview_player_state` remains available as an optional refresh via
`--preview-refresh-state`, but the default gate avoids the extra socket round
trip because `open_niagara_preview_player` already returns the loaded state. A
mostly dark viewport is reported as a warning rather than an automatic failure
in this first gate.

If the `open_niagara_preview_player` socket response times out but the Preview
Player state already matches the requested target system, the executor recovers
from `get_niagara_preview_player_state` and records `open_error` plus
`open_recovered_from_state` in the report.

The selected screenshot also receives a non-fatal visual-read classification:
`screenshot_visual_pass`, `screenshot_visual_read_status`,
`screenshot_visual_confidence`, `screenshot_visual_warnings`, and
`screenshot_visual_failure_reasons`. These fields help review automation
separate a strong visual-read frame from a weak or dark frame without rejecting
intentionally subtle effects too early.

For stricter generated-temp validation, pass `--preview-require-visual-pass`.
That option promotes a failed visual-read classification to the fatal reason
`preview_visual_read_failed`; the default remains advisory.

Every executor run writes a compact review summary next to the execution report
unless `--no-review-summary` is passed. The summary folds compile, preview,
visual-read, write-count, artifact, issue, and recommended-next-action fields
into `<report_stem>_review_summary.json`.

Socket executor modes also run a post-run dirty package check by default unless
`--no-dirty-package-check` is passed. The execution report records
`dirty_package_check`, and the review summary exposes it as
`gates.dirty_packages`. Any recorded dirty content or map package marks the
review as failed.

### Response Shape

- `system_scripts`: system spawn/update script graphs.
- `emitters[].graph`: each emitter graph.
- `system_scratch_pad_scripts`: system-owned Scratch Pad scripts.
- `emitters[].scratch_pad_scripts`: emitter-owned Scratch Pad scripts.
- `emitters[].parent_scratch_pad_scripts`: parent emitter Scratch Pad scripts when exposed by Niagara editor data.
- Each graph reports `nodes`, optional per-node `pins`, graph-level `links`, node class counts, truncation flags, and node/link totals.

### Safety

- The command does not save, compile, mutate nodes, or modify links.
- It is intentionally separate from `inspect_niagara_stack`: stack inspection is a semantic/module summary, while graph inspection is the lower-level topology needed before any future node wiring API.

### Verification

- `MCPGameProjectEditor Win64 Development -NoHotReloadFromIDE` built successfully in the sibling repo after adding the command and bridge route.
- Cubeless `StylizedCubelessEditor Win64 Development -NoHotReloadFromIDE` linked successfully after normally closing the running editor.
- Runtime smoke on the Sword Trail source reported `5` emitters, `7` graphs, `188` nodes, `190` links, `0` Scratch Pads, and `read_only=true`.
- A pins/links sample returned node pin metadata and `35` first-emitter graph links before the requested truncation limit.
- Post-inspection dirty check reported `dirty_content_count=0` and `dirty_map_count=0`.

### Current Consumers

- `niagara_generation_recipe_builder.py` stores a compact `graph_analysis`
  summary and mirrors key topology into `reference_analysis`.
- The Niagara Preview Player analysis panel displays graph count, node count,
  link count, and a compact node-class summary next to renderer, stack, and
  module-input analysis.

## Implemented Read API: `inspect_niagara_compile_status`

This is the first compile-health API. It is read-only by default and exists so
generation recipes, Preview Player review, and future mutation validation can
detect compile errors before saving or promoting generated systems.

### Request

```json
{
  "system_path": "/Game/Path/NS_System.NS_System",
  "request_compile": false,
  "force": false,
  "allow_source_compile": false,
  "wait_for_completion": false,
  "timeout_seconds": 10.0,
  "poll_interval_seconds": 0.1
}
```

### Response Shape

```json
{
  "success": true,
  "system_path": "/Game/Path/NS_System.NS_System",
  "read_only": true,
  "request_compile": false,
  "compile_requested": false,
  "wait_for_completion": false,
  "wait_timed_out": false,
  "wait_elapsed_seconds": 0.0,
  "wait_iterations": 0,
  "outstanding_compilation_requests_before": false,
  "outstanding_compilation_requests_after_request": false,
  "outstanding_compilation_requests_after": false,
  "script_count": 10,
  "error_count": 0,
  "warning_count": 0,
  "dirty_count": 0,
  "unknown_count": 0,
  "missing_count": 0,
  "scripts": [
    {
      "script_index": 0,
      "owner_kind": "system",
      "owner_name": "system_spawn",
      "script_name": "SystemSpawnScript",
      "usage": "SystemSpawnScript",
      "compile_status": "NCS_UpToDate",
      "has_error": false,
      "has_warning": false,
      "is_ready_cpu": true,
      "is_ready_gpu": false
    }
  ]
}
```

### Safety Rules

- Default mode does not compile, save, mark dirty, or mutate Niagara assets.
- `request_compile=true` is blocked outside
  `/Game/_MCP_Temp/NiagaraGenerated/` unless `allow_source_compile=true` is
  explicitly passed.
- `wait_for_completion=true` polls `UNiagaraSystem::PollForCompilationComplete()`
  and pumps `FAssetCompilingManager::ProcessAsyncTasks(true)` until outstanding
  compile requests clear or `timeout_seconds` expires.
- Source systems should use read-only status inspection during reference
  analysis; generated temp systems may request compile as part of validation.

### Current Consumers

- `niagara_generation_recipe_builder.py` stores compact
  `compile_status_analysis`, status counts, notable scripts, and risk notes.
- `niagara_generation_recipe_builder.py` writes a `validation.compile_gate`
  contract describing default timeout, poll interval, and fatal conditions.
- `niagara_generation_recipe_executor.py --socket-validate-compile-only`
  requests and waits for generated-temp Niagara compile validation.
- `niagara_generation_recipe_executor.py --socket-postprocess-only` now runs the
  compile gate as its final step.
- The Niagara Preview Player analysis panel displays compile error, warning,
  dirty, and outstanding request counts next to graph/module analysis.

### Verification

- Sibling and Cubeless UE 5.7 editor builds passed after adding the command.
- Runtime read-only smoke on `FX_S_Parry03` returned `10` scripts, `0` errors,
  `0` warnings, `0` dirty scripts, and no package dirtiness.
- Source safety guard smoke rejected `request_compile=true` on the same source
  system without `allow_source_compile=true`.
- Preview Player smoke showed
  `Compile status errors 0 | warnings 0 | dirty 0 | outstanding true` in
  `analysis_summary`.
- Generated-temp compile gate smoke on `codex_socket_postprocess_smoke`
  succeeded with `23` scripts, `0` errors, `0` warnings, `0` dirty scripts,
  `wait_timed_out=false`, and
  `outstanding_compilation_requests_after=false`.
- Full socket postprocess smoke finished with four successful steps:
  renderer binding, User parameter application, module input application, and
  compile validation.

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

## Implemented Safe Edit API: `create_niagara_module_input_override`

This API creates a missing RapidIteration parameter for an input that already
exists on a matched Niagara module. It is intentionally separate from
`set_niagara_module_input_value` so normal set calls cannot accidentally create
new overrides.

### Request

```json
{
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "emitter_name": "FX_E_SwordTrail04_L",
  "module_name": "SpawnBurst_Instantaneous",
  "input_name": "Spawn Count",
  "value": 2,
  "overwrite_existing": false,
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
  "created": true,
  "overwrote_existing": false,
  "previous_value": null,
  "new_value": 2,
  "saved": true,
  "write_scope": "new_or_explicitly_overwritten_rapid_iteration_parameter"
}
```

### Safety Rules

- Default write scope is `/Game/_MCP_Temp/NiagaraGenerated/` only.
- Source Niagara systems are rejected unless `allow_source_edit=true` is
  explicitly passed.
- Existing overrides are rejected unless `overwrite_existing=true` is
  explicitly passed. Use `set_niagara_module_input_value` for routine edits to
  existing RapidIteration values.
- Supported first-pass types are float, int, bool, color, vec2, vec3, vec4, and
  position.
- This does not create graph pins, dynamic inputs, Scratch Pad nodes, or data
  interface values. It only adds RapidIteration parameter data for an existing
  stack input.

### Verification

- Build verification passed for both `MCPGameProjectEditor Win64 Development`
  in the sibling workspace and `StylizedCubelessEditor Win64 Development` in
  the Cubeless project.
- Runtime smoke used the temp system
  `/Game/_MCP_Temp/NiagaraGenerated/codex_socket_postprocess_smoke/NS_codex_socket_postprocess_smoke.NS_codex_socket_postprocess_smoke`.
- The command created `Module.Scale Alpha` on emitter `FX_E_Line01_L`, module
  `ScaleColor`, GUID `49302E58-47DF-ABAE-60E1-62A13DC8D4CC`, with value
  `0.77`.
- Post-inspection read the input back as `value_source=rapid_iteration` with
  value `0.7699999809265137`.
- Compile status after the smoke reported `error_count=0`, `warning_count=0`,
  `dirty_count=0`, and `wait_timed_out=false`. Dirty package check reported
  `dirty_content_count=0` and `dirty_map_count=0`.

## Implemented Safe Edit API: `set_niagara_module_inputs_batch`

This API batches existing RapidIteration edits, missing override creation, or
upserts into one command. It is an orchestration wrapper over the single-edit
handlers, so the same temp-only and type support rules apply.

### Request

```json
{
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "operation": "set_existing",
  "continue_on_error": false,
  "save": true,
  "edits": [
    {
      "emitter_name": "FX_E_Line01_L",
      "module_name": "EmitterState",
      "input_name": "Loop Duration",
      "value": 2.0
    },
    {
      "operation": "upsert",
      "emitter_name": "FX_E_Line01_L",
      "module_name": "ScaleColor",
      "module_node_guid": "49302E58-47DF-ABAE-60E1-62A13DC8D4CC",
      "input_name": "Scale Alpha",
      "value": 0.66
    }
  ]
}
```

Supported operations:

- `set_existing`: only edit existing RapidIteration parameter data.
- `create_override`: create missing RapidIteration parameter data and reject
  existing overrides unless `overwrite_existing=true`.
- `upsert`: create missing data or overwrite existing data. If no explicit
  `overwrite_existing` is passed, upsert defaults to overwrite existing values.

### Response Shape

```json
{
  "success": true,
  "system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "requested_count": 2,
  "processed_count": 2,
  "applied_count": 2,
  "failed_count": 0,
  "continue_on_error": false,
  "saved": true,
  "write_scope": "batch_rapid_iteration_module_inputs",
  "results": []
}
```

### Safety Rules

- Default write scope is `/Game/_MCP_Temp/NiagaraGenerated/` only.
- Source Niagara systems are rejected unless `allow_source_edit=true` is
  explicitly passed.
- The command saves once after successful edits when `save=true`.
- `continue_on_error=false` stops on the first failed edit; `true` records
  failures and continues through the remaining edit entries.

### Verification

- Build verification passed for both `MCPGameProjectEditor Win64 Development`
  in the sibling workspace and `StylizedCubelessEditor Win64 Development` in
  the Cubeless project.
- Runtime smoke used the temp system
  `/Game/_MCP_Temp/NiagaraGenerated/codex_socket_postprocess_smoke/NS_codex_socket_postprocess_smoke.NS_codex_socket_postprocess_smoke`.
- Batch smoke applied three edits with `applied_count=3`, `failed_count=0`,
  and `saved=true`: `Module.Loop Duration=1.75`, `Module.Scale Alpha=0.66`,
  and `Module.Lifetime=1.25` on `FX_E_Line01_L`.
- Post-inspection read all three back as `value_source=rapid_iteration`.
- Compile status after the smoke reported `error_count=0`, `warning_count=0`,
  `dirty_count=0`, and `wait_timed_out=false`. Dirty package check reported
  `dirty_content_count=0` and `dirty_map_count=0`.

## Implemented Safe Edit API: `add_scratch_pad_module_to_stack`

This API inserts an existing target-local Scratch Pad module into a Niagara
stack through `FNiagaraStackGraphUtilities::AddScriptModuleToStack`.

### Request

```json
{
  "target_system_path": "/Game/_MCP_Temp/NiagaraGenerated/Test/NS_Test.NS_Test",
  "scratch_pad_owner_kind": "system",
  "scratch_pad_script_index": 0,
  "target_usage": "ParticleUpdateScript",
  "target_emitter_index": 0,
  "target_index": -1,
  "suggested_name": "MCP_RenderCircleToGrid",
  "skip_if_duplicate": true,
  "save": true
}
```

Supported selectors:

- `scratch_pad_script_path`, or local owner selection through
  `scratch_pad_owner_kind`, `scratch_pad_script_index`, and
  `scratch_pad_name`.
- Emitter-owned Scratch Pads through `scratch_pad_emitter_index` or
  `scratch_pad_emitter_name`.
- Emitter/particle target stacks through `target_emitter_index` or
  `target_emitter_name`.
- `target_usage` accepts common Niagara script usage names such as
  `SystemUpdateScript`, `EmitterSpawnScript`, and `ParticleUpdateScript`.

### Safety Rules

- Default write scope is `/Game/_MCP_Temp/NiagaraGenerated/` only.
- The Scratch Pad must already belong to the target temp system. Duplicate it
  first with `create_or_duplicate_scratch_pad_module`.
- Only `Module` Scratch Pads are inserted.
- The command validates the Scratch Pad's advertised supported usage contexts
  against the requested target stack usage before mutation.
- `skip_if_duplicate` defaults to `true`; if the same Scratch Pad script is
  already present in the requested output stack, including `target_usage_id`
  when provided, the command returns success with `skipped_duplicate=true`,
  reports the existing module node, and does not save or request compile.
- Save failure after a real insertion is reported as command failure instead
  of a successful write with `saved=false`.
- It does not create internal Scratch Pad graph nodes or arbitrary pin links.

### Recipe/Executor Integration

- `niagara_generation_recipe_builder.py` now writes
  `scratch_pad_analysis` and `generation_plan.scratch_pad_stack_insertions`
  when the primary source has compatible target-local Scratch Pads and the
  prompt intent requests Scratch Pad/reactive behavior.
- `niagara_generation_recipe_executor.py --socket-insert-scratch-pads-only`
  applies those planned insertions through `add_scratch_pad_module_to_stack`.
- Full `--socket-postprocess-only` runs planned Scratch Pad insertion before
  compile validation.
- Executor reports now distinguish `inserted`, `skipped_duplicate`, and
  `failed` Scratch Pad applications, and include post-insertion compile
  validation fatal reasons when present.

### Verification

- UTF-8 receive handling was hardened in the Python MCP socket client and the
  builder/executor socket helpers so large Scratch Pad responses with localized
  type names no longer fail when a multibyte sequence crosses a socket chunk
  boundary.
- Runtime decode smoke on
  `/Game/Cubeless/Reactive/NS_Reactive_RTTexturePainter.NS_Reactive_RTTexturePainter`
  returned `5` available system Scratch Pads and first script
  `RenderCircleToGrid`.
- Recipe/executor integration smoke planned and inserted `ParticleOnerScale`
  into the temp duplicate
  `/Game/_MCP_Temp/NiagaraGenerated/scratch_pad_recipe_integration_smoke/NS_scratch_pad_recipe_integration_smoke`.
  The inserted node GUID was `0B5586CB-4BF8-A1C0-D0B1-96A313CBE8EB`, and
  compile validation reported `error_count=0`, `warning_count=0`,
  `dirty_count=0`.
- Usage matrix smoke inserted compatible Scratch Pads into
  `ParticleSpawnScript`, `ParticleUpdateScript`, and `EmitterSpawnScript`;
  an incompatible `SystemUpdateScript` request was rejected with a usage
  compatibility error. Compile validation after the successful insertions
  reported `error_count=0`, `warning_count=0`, `dirty_count=0`, and
  `wait_timed_out=false`.
- Duplicate-skip smoke inserted `RenderCircleToGrid` into a temp duplicate of
  `/Game/Cubeless/Reactive/NS_Reactive_RTTexturePainter.NS_Reactive_RTTexturePainter`,
  then repeated the same insertion. The first call reported graph nodes
  `55 -> 56`; the second returned `skipped_duplicate=true`, reused the
  existing node GUID, kept graph nodes `56 -> 56`, and compile validation
  reported `error_count=0`, `warning_count=0`, `dirty_count=0`.
- C++ review follow-up tightened duplicate detection to the exact downstream
  output stack rather than usage-only comparison, so repeated usages with
  distinct `target_usage_id` values are not skipped incorrectly.

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

Future write/validation API. The read-only
`inspect_niagara_compile_status` API above now covers compile-health
diagnostics; this future API should handle blocking compile requests, waiting,
and structured compile event collection for generated temp systems.

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
