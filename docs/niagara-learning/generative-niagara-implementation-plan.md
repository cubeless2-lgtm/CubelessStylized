# Generative Niagara Implementation Plan

## 2026-06-12 Implementation Status

The active UnrealMCP implementation work is now in the sibling repository
`C:\Git\unreal-mcp-cubeless` on branch `codex/niagara-mcp-authoring`.

Current implementation and next-work boundaries are summarized in
`docs/niagara-learning/niagara-mcp-capability-matrix.md`. Treat that matrix as
the shortest source of truth before choosing the next C++ extension.

Current MCP Niagara coverage:

- Read: aggregated system analysis with `analyze_niagara_system`.
- Read: renderer/material inspection with `inspect_niagara_renderers`.
- Read: exposed `User.*` parameter inspection with `inspect_niagara_user_parameters`.
- Read: system, emitter, and Scratch Pad stack function-call inspection with `inspect_niagara_stack`.
- Read: Scratch Pad ownership, usage, input, and output inspection with `inspect_niagara_scratch_pad_interface`.
- Read: module input candidate inspection with `inspect_niagara_module_inputs`.
- Write: renderer material replacement with `set_niagara_renderer_material`.
- Write: source emitter asset/system-handle attachment into generated temp systems with `duplicate_or_attach_emitter_from_source`.
- Write: existing Scratch Pad script duplication into generated temp systems/emitters with `create_or_duplicate_scratch_pad_module`.
- Write: target-local Scratch Pad module stack insertion with `add_scratch_pad_module_to_stack`.
- Pipeline: recipe/executor Scratch Pad insertion for target-local primary-source Scratch Pads when prompt intent requests Scratch Pad/reactive behavior.
- Write: supported exposed User parameter values with `set_niagara_user_parameter`.
- Write: missing RapidIteration module input overrides with `create_niagara_module_input_override`.
- Write: existing RapidIteration module input overrides with `set_niagara_module_input_value`.
- Write: batch RapidIteration module input edits with `set_niagara_module_inputs_batch`.
- Pipeline: `Tools/Unreal/niagara_generation_recipe_builder.py` promotes renderer binding, matching User parameter overrides, and batch module input overrides into `can_execute_now` when the MCP inspection data is available.
- Pipeline: `Tools/Unreal/niagara_generation_recipe_executor.py --socket-apply-module-inputs-only` now calls `set_niagara_module_inputs_batch` and can create supported missing RapidIteration overrides for generated temp systems.
- Pipeline: `Tools/Unreal/niagara_generation_recipe_executor.py --socket-insert-scratch-pads-only` now inserts planned target-local Scratch Pad modules through `add_scratch_pad_module_to_stack`.
- Pipeline: `Tools/Unreal/niagara_generation_recipe_executor.py --socket-postprocess-only` runs all safe socket post-processing steps on an already duplicated temp Niagara System.
- Preview: Niagara Preview Player screenshot capture targets the `UnrealEditor`
  process and uses HWND `PrintWindow` capture so occluded windows do not
  accidentally capture Codex or another foreground app.

Safety defaults:

- Write tools refuse source assets unless `allow_source_edit=true`.
- The default editable output scope remains `/Game/_MCP_Temp/NiagaraGenerated/` and related `_MCP_Temp` generated assets.
- Full Scratch Pad graph creation, arbitrary node wiring, emitter merge, and graph-pin/dynamic-input authoring are still future work. Scratch Pad stack insertion is available only for target-local Module Scratch Pads in generated temp systems by default.

The phase notes below are retained as project history. Some early sections still describe the pre-C++ state and should be read as historical context, not the current branch state.

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

## Phase 0.5: Natural-Language Recipe Compiler

Purpose:

- Turn a Korean or English effect request into a structured generation recipe before any Unreal asset write.
- Always analyze current Niagara reference sources first, then separate immediately executable temp-asset steps from steps blocked by missing Niagara edit APIs.
- Keep the output safe for 티브렛: original Niagara, Material, Blueprint, Texture, and Mesh assets remain read-only.

Current implementation:

- `Tools/Unreal/niagara_generation_recipe_builder.py` parses Korean/English role, material, color, motion, and duration hints.
- The recipe now includes `generation_plan`:
  - `can_execute_now`: safe temp duplication/material-instance preparation steps.
  - `can_execute_now`: now also includes `bind_duplicated_materials_to_matching_renderers` when duplicated material candidates exist.
  - `blocked_by_api`: emitter merge, user parameter override, Scratch Pad reuse, and other steps that still need Inspector/Edit API coverage.
  - `preview_after_generation`: Preview Player first, Preview Lab for review-gated screenshots.
- `docs/niagara-learning/schemas/niagara_generation_recipe.schema.json` documents the new `generation_plan` shape.

Smoke prompts:

- `붉은색 검 궤적` -> `ribbon_trail`, `ribbon_slash`, `red`.
- `푸른 번개 장판` -> `ground_area`, `lightning_arc`, `radial_shockwave`, `stylized_lightning`, `blue`.
- `연기 폭발` -> `smoke_volume`, `impact_burst`.
- `스타일라이즈 화염` -> `fire_flame`, `fire_flipbook`.
- `초록 독 안개` -> `smoke_volume`, `soft_smoke`, `green`.

## Phase 0.6: Safe Temp Recipe Executor

Purpose:

- Execute only the safe subset of a recipe before the full Niagara edit API exists.
- Convert `can_execute_now` into temp asset writes under `/Game/_MCP_Temp/NiagaraGenerated/`.
- Keep all source Niagara and Material assets read-only.

Current implementation:

- `Tools/Unreal/niagara_generation_recipe_executor.py`
- Outside Unreal, use `--dry-run` to verify the recipe and execution report shape.
- Inside Unreal Editor Python, the executor can:
  - duplicate the primary Niagara System to the recipe target path.
  - duplicate candidate Material Instances to the recipe temp material folder.
  - save only duplicated temp assets unless `--no-save` is passed.
  - write a report under `Saved/MCP_NiagaraGeneration`.

Explicitly deferred:

- emitter stack merge
- Scratch Pad extraction or mutation
- user parameter override writing
- source asset saves
- production promotion

## Phase 0.7: Temp Material Stack

Purpose:

- Prepare stylized material variants next to the generated temp Niagara System.
- Apply natural-language color intent to duplicated temp Material Instances when safe vector color parameters are visible.
- Keep the operation reviewable before source promotion; renderer material rebinding is now available for temp systems.

Current implementation:

- `niagara_generation_recipe_builder.py` now promotes likely Material Instance candidates to `duplicate_material_instance` instead of leaving them as plain `reuse`.
- `niagara_generation_recipe_executor.py` duplicates those candidates under `/Game/_MCP_Temp/NiagaraGenerated/<request>/Materials/`.
- The executor reads the first parsed color and applies it only to duplicated temp `MaterialInstanceConstant` vector parameters with safe color-like names, such as:
  - `LineColor`
  - `EmissionColor`
  - `DarkColor`
  - `BrightColor`
  - `BaseTint_*`
- The execution report records every material parameter application and every skipped/no-parameter result.

Still deferred:

- Mapping material parameter names per project style family.
- Setting Niagara `User.*` parameters inside the duplicated system.
- Deep material graph inspection beyond exposed MI parameters.

## Phase 0.8: Renderer Material Binding API

Purpose:

- Inspect Niagara renderer material slots through UnrealMCP.
- Bind duplicated temp Material Instances back onto matching renderers on the duplicated temp Niagara System only.
- Keep source Niagara systems protected by default.

Current implementation:

- UnrealMCP plugin adds:
  - `inspect_niagara_renderers`
  - `set_niagara_renderer_material`
- `inspect_niagara_renderers` reads enabled renderers per emitter and reports renderer class, emitter index/name, renderer index, `used_materials`, and primary material/mesh overrides when available.
- `set_niagara_renderer_material` supports Sprite, Ribbon, Mesh, Decal, and Volume renderers:
  - Sprite/Ribbon/Decal/Volume: sets `Material`.
  - Mesh: enables `OverrideMaterials` and sets `OverrideMaterials[material_slot].ExplicitMat`.
- The set command refuses writes outside `/Game/_MCP_Temp/NiagaraGenerated/` unless `allow_source_edit=true` is explicitly passed.
- `niagara_generation_recipe_executor.py --socket-bind-only` inspects a generated temp system, maps source renderer materials to duplicated temp material instances from `material_plan`, and applies matching renderer bindings through the UnrealMCP socket after the Unreal Python duplication step.

Smoke verification:

- Built `StylizedCubelessEditor Win64 Development` successfully after adding the UnrealMCP Niagara commands.
- Inspected `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail/NS_red_sword_trail` and read `21` emitters / `22` enabled renderers.
- Set emitter index `4`, renderer index `0` from original `FX_MI_Glow_Y003` to duplicated temp `MI_red_sword_trail_FX_MI_Glow_Y003`; readback confirmed both `used_materials` and `primary_material` use the temp MI.
- Ran `--socket-bind-only` on the red sword trail recipe; it bound one additional matching renderer (`FX_M_RadialBlur01_Y001`) and reported skipped renderers whose actual renderer material was not present in `material_plan`.

Gap found in Phase 0.8:

- The existing `material_plan` is selected from the material index by style/role, not from the actual renderer material list of the chosen primary Niagara System.
- Next material-planning iteration should promote `inspect_niagara_renderers` output into the recipe so the executor duplicates and binds actual renderer materials first, then adds optional style/material variants second.

## Phase 0.9: Renderer-First Material Plan

Purpose:

- Make every generated recipe analyze the chosen primary Niagara System's actual renderer materials first.
- Duplicate and bind renderer-owned materials before adding optional style/material variants.
- Reduce false material matches caused by name/style search only.

Current implementation:

- `niagara_generation_recipe_builder.py` now attempts `inspect_niagara_renderers` by default through the UnrealMCP bridge.
- CLI control:
  - `--renderer-inspect-mode auto`: default; use renderer inspect when the bridge is reachable and fall back to index-only planning if not.
  - `--renderer-inspect-mode required`: fail recipe generation if renderer inspect is unavailable.
  - `--renderer-inspect-mode off`: keep the old index-only behavior.
- Recipes now include:
  - `renderer_analysis`: raw renderer inspect status, renderers, and unique renderer materials.
  - `reference_analysis.renderer_material_sources`: actual materials used by the chosen primary system.
  - `material_plan[].source_kind`: `renderer_bound`, `style_variant`, or `missing`.
  - `material_plan[].renderer_bindings`: emitter/renderer locations where a renderer-bound material is used.
- `material_plan` ordering:
  - actual renderer materials first.
  - style/role material variants second.
  - case-insensitive duplicate paths are collapsed.

Smoke verification:

- Red sword trail recipe with `--renderer-inspect-mode required` inspected `22` enabled renderers and found `13` unique renderer materials.
- The regenerated recipe has `19` material plan entries: `13` renderer-bound materials and `6` style variants.
- Temp execution duplicated the primary system and renderer/style material candidates under `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail/`.
- `--socket-bind-only` bound `21` material renderers successfully, skipped only the `NiagaraLightRendererProperties` renderer, and had `0` failed bindings.
- Final inspect readback confirmed `21/21` material renderers use temp materials and `0` material renderers still point to source materials.

Remaining deferred:

- Deeper Scratch Pad/module stack extraction.
- Renderer-aware style selection so optional variants target only visually relevant layers.

## Phase 0.10: User Parameter API And Source Matching

Status:

- UnrealMCP now has first-pass `inspect_niagara_user_parameters` and `set_niagara_user_parameter` commands.
- The setter is temp-safe by default and refuses writes outside `/Game/_MCP_Temp/NiagaraGenerated/` unless explicitly overridden.
- Supported first-pass value types are simple scalar/vector controls: float, int, bool, color, vec2, vec3, vec4, and position.
- `niagara_generation_recipe_executor.py --socket-apply-user-parameters-only` inspects the generated temp system and applies prompt intent only to existing exposed `User.*` parameters when name and type hints match safely.
- If a sample has no exposed `User.*` parameters, the report records the unapplied intent instead of creating unused parameters.

Source matching update:

- `niagara_generation_recipe_builder.py` now derives source-match keywords from the natural-language request, such as `sword`, `trail`, `slash`, and `ribbon`.
- Direct matches in Niagara object path, package, display name, and tags score higher than incidental matches in referenced material or mesh paths.
- This prevents a system from winning only because it uses a matching material, for example preferring an actual Sword Trail system over a Shockwave system that happens to reference a SwordTrail material.

Verification:

- `inspect_niagara_user_parameters` succeeded on `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail/NS_red_sword_trail` and reported `0` exposed user parameters.
- The user-parameter executor pass wrote `Saved/MCP_NiagaraGeneration/red_sword_trail_user_parameter_report.json` with `application_count=0` and a safe no-match reason.
- Regenerating the red sword trail recipe through a UTF-8 prompt file now selects `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Sword_C_Skill01_Trail01.FX_S_Sword_C_Skill01_Trail01` as the primary source.
- That Sword Trail source also has `0` exposed `User.*` parameters, so it is currently controlled through renderer/material/Scratch Pad analysis rather than BP user parameters.

Coverage note:

This is a common foundation for all Niagara samples, not full sample coverage yet. Every sample can be inspected through the same path, but each sample may fall into a different controllability bucket:

- renderer/material controllable
- exposed `User.*` controllable
- Blueprint/AnimNotify runtime-input dependent
- Scratch Pad/module-stack dependent
- not safely editable until a deeper Niagara graph API exists

## Phase 0.11: Stack And Scratch Pad Inspector

Status:

- UnrealMCP now has a read-only `inspect_niagara_stack` command.
- The command reads system spawn/update script graphs, emitter graph sources, function-call/module nodes, input/output nodes, script usage summaries, and emitter/system Scratch Pad script containers where exposed by the engine API.
- It does not modify, compile, save, or regenerate Niagara assets.
- Output can include pins with `include_pins=true`, but recipe generation uses the compact default without pin dumps to keep recipe JSON readable.

Recipe integration:

- `niagara_generation_recipe_builder.py` now supports `--stack-inspect-mode auto|required|off`, defaulting to `auto`.
- Recipe output includes compact `stack_analysis`:
  - emitter count
  - total emitter function call count
  - Scratch Pad count
  - emitter-level control hints
  - top function/module names per emitter
- `reference_analysis.stack_control_hints` records controllability buckets such as:
  - `spawn_control`
  - `lifetime_control`
  - `dynamic_material_parameter_control`
  - `scale_control`
  - `size_control`
  - `color_or_tint_control`
  - `velocity_control`

Verification:

- `inspect_niagara_stack` succeeded on `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Sword_C_Skill01_Trail01.FX_S_Sword_C_Skill01_Trail01`.
- It reported `5` emitters, `70` emitter function calls, and `0` Scratch Pads.
- Important module/function candidates include:
  - `SpawnBurst_Instantaneous`
  - `InitializeParticle`
  - `DynamicMaterialParameters`
  - `ScaleMeshSize`
  - `ScaleColor`
  - `AddVelocity`
- The regenerated red sword trail recipe now has both `renderer_analysis.status=success` and `stack_analysis.status=success`.

Why this matters:

This turns generation from asset-name matching into behavior-aware analysis. For samples with no exposed `User.*` parameters, the generator can now see whether the effect is likely controlled by material parameters, color scaling modules, mesh/ribbon size modules, velocity modules, spawn modules, or Scratch Pad scripts.

Remaining deferred:

- Exact editable stack operation API, such as add/remove/reorder module.
- Reading resolved rapid-iteration/default override values for each module input.
- Mapping `DynamicMaterialParameters` outputs to specific material parameter slots.
- Scratch Pad creation and insertion into temp systems.

## Phase 0.11b: Graph Topology Inspector

Purpose:

- Move from function-call summaries toward full graph topology awareness.
- Read the actual Niagara graph nodes, pins, and links before attempting any
  future Scratch Pad or arbitrary graph authoring.
- Keep this phase read-only so source systems, generated temp systems, maps,
  materials, and textures are not dirtied by inspection.

Current implementation:

- UnrealMCP now has a read-only `inspect_niagara_graph` command.
- It reports system spawn/update graphs, emitter graphs, system Scratch Pads,
  emitter Scratch Pads, and parent emitter Scratch Pads where exposed by
  Niagara editor data.
- Each graph includes node class counts, node positions, node titles, Niagara
  node kind, optional pins, explicit output-to-input links, truncation flags,
  and node/link totals.
- The command is separate from `inspect_niagara_stack`: stack inspection is a
  semantic/module summary, while graph inspection is the lower-level topology
  needed before safe node wiring can be designed.

Verification:

- `uv run --python 3.11 python -m py_compile Python/unreal_mcp_server.py Python/tools/niagara_tools.py` passed in the sibling repo.
- `MCPGameProjectEditor Win64 Development -NoHotReloadFromIDE` built
  successfully in `C:\Git\unreal-mcp-cubeless`.
- Cubeless `StylizedCubelessEditor Win64 Development -NoHotReloadFromIDE`
  initially compiled the UnrealMCP plugin sources but could not link while the
  editor held `UnrealEditor-UnrealMCP.dll`; after a normal editor close, the
  same build linked successfully.
- Runtime smoke on
  `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Sword_C_Skill01_Trail01.FX_S_Sword_C_Skill01_Trail01`
  succeeded:
  - minimal graph read: `5` emitters, `7` graphs, `188` nodes, `190` links,
    `0` Scratch Pads, `read_only=true`.
  - pins/links sample: first emitter graph returned `20` nodes and `35` links
    with pin metadata before the requested truncation limit.
  - post-inspection dirty check: `dirty_content_count=0`,
    `dirty_map_count=0`.

Remaining deferred:

- Safe graph mutation APIs. This phase only observes topology.

## Phase 0.11c: Graph Topology Integration

Purpose:

- Make `inspect_niagara_graph` useful in the generation loop instead of leaving
  it as a standalone smoke command.
- Surface graph topology in both generated recipes and the Niagara Preview
  Player analysis panel.

Current implementation:

- `niagara_generation_recipe_builder.py` now supports
  `--graph-inspect-mode auto|off|required`, defaulting to `auto`.
- Recipes now include:
  - `graph_analysis`
  - `reference_analysis.graph_top_node_classes`
  - `reference_analysis.graph_scratch_pad_sources`
  - graph-aware risk notes such as graph count, node count, link count, and
    Scratch Pad count.
- The Niagara Preview Player analysis panel now shows:
  - `Graph topology <graphs> graphs | <nodes> nodes | <links> links`
  - a compact `Graph node classes` summary.

Verification:

- `py_compile` passed for `Tools/Unreal/niagara_generation_recipe_builder.py`.
- `StylizedCubelessEditor Win64 Development -NoHotReloadFromIDE` built
  successfully after the Preview Player update.
- Required-mode recipe smoke
  `red sword trail graph topology smoke` produced
  `Saved/MCP_NiagaraGeneration/graph_topology_recipe_smoke_generation_recipe.json`
  with `Graph inspect: success`.
- The recipe graph summary for selected source `FX_S_Parry03` reported `4`
  graphs, `104` nodes, `106` links, `0` Scratch Pads, and top node classes
  including `NiagaraNodeFunctionCall`, `NiagaraNodeInput`,
  `NiagaraNodeParameterMapSet`, `NiagaraNodeOutput`, and `NiagaraNodeEmitter`.
- Opening `FX_S_Parry03` in the Niagara Preview Player returned an
  `analysis_summary` containing `Graph topology 4 graphs | 104 nodes | 106 links`.
- Post-inspection dirty check: `dirty_content_count=0`, `dirty_map_count=0`.

Remaining deferred:

- Use graph topology to design a safe temp-only graph mutation API.
- Add wait/retry handling for outstanding Niagara compile requests after mutation
  batches.

## Phase 0.11d: Compile Status Diagnostics

Purpose:

- Add a safe compile-health read API before the generator performs deeper
  Niagara graph or module-input mutation batches.
- Surface compile errors, warnings, dirty script states, and outstanding
  compilation requests in both recipes and the Niagara Preview Player.

Current implementation:

- UnrealMCP now has `inspect_niagara_compile_status`.
- The command is read-only by default and returns per-script compile status,
  readiness, error/warning flags, dirty/unknown/missing counts, and
  `HasOutstandingCompilationRequests(true)` before/after the call.
- `wait_for_completion=true` now polls Niagara through
  `UNiagaraSystem::PollForCompilationComplete()` and pumps
  `FAssetCompilingManager::ProcessAsyncTasks(true)` until outstanding
  compilation requests clear or the timeout expires.
- Optional `request_compile=true` exists, but is blocked for source assets
  outside `/Game/_MCP_Temp/NiagaraGenerated/` unless
  `allow_source_compile=true` is explicitly passed.
- The sibling Python MCP layer exposes
  `inspect_niagara_compile_status(system_path, request_compile=False,
  force=False, allow_source_compile=False)`.
- `niagara_generation_recipe_builder.py` now supports
  `--compile-status-inspect-mode auto|off|required`, stores
  `compile_status_analysis`, mirrors status counts/notable scripts into
  `reference_analysis`, and adds compile-health risk notes.
- `niagara_generation_recipe_builder.py` also writes a `validation.compile_gate`
  contract with the default compile wait timeout, poll interval, and fatal
  conditions.
- `niagara_generation_recipe_executor.py` now has
  `--socket-validate-compile-only` and runs compile validation automatically at
  the end of `--socket-postprocess-only`.
- `niagara_generation_recipe_executor.py` now also has
  `--socket-validate-preview-only` and runs Preview Player validation after the
  compile gate at the end of `--socket-postprocess-only`.
- Preview Player validation opens the generated temp system with
  `open_niagara_preview_player`, captures the actual `Niagara Preview Player`
  window through `Tools/Unreal/capture-unreal-editor-window.ps1`, stores the
  PNG under `Saved/MCP/NiagaraReviews/<slug>/`, and records screenshot brightness
  statistics in the report.
- Preview Player validation now captures multiple screenshot candidates and
  selects the best frame by a viewport brightness/readability score. The
  selected candidate is copied to the canonical
  `<slug>_niagara_previewer.png` path, while candidate paths and scores remain
  in the report.
- The gate now uses the state returned by `open_niagara_preview_player` as the
  default state source. `get_niagara_preview_player_state` remains available
  through `--preview-refresh-state` for explicit refresh checks, which avoids
  routine timeout noise during screenshot validation.
- The selected Preview Player screenshot now receives non-fatal visual-read
  fields: `screenshot_visual_pass`, `screenshot_visual_read_status`,
  `screenshot_visual_confidence`, `screenshot_visual_warnings`, and
  `screenshot_visual_failure_reasons`.
- `--preview-require-visual-pass` promotes a failed visual-read classification
  to the fatal reason `preview_visual_read_failed`; the default remains
  advisory for subtle or intentionally dark effects.
- The Niagara Preview Player analysis panel now shows:
  - `Compile status errors <n> | warnings <n> | dirty <n> | outstanding <true|false>`.

Verification:

- Sibling `MCPGameProjectEditor Win64 Development -NoHotReloadFromIDE` built
  successfully after adding the command, bridge route, Python tool, and docs.
- Cubeless `StylizedCubelessEditor Win64 Development -NoHotReloadFromIDE`
  built successfully after mirroring the C++ command and adding Preview Player
  integration.
- Runtime read-only smoke on `FX_S_Parry03` returned `10` scripts, `0` errors,
  `0` warnings, `0` dirty scripts, `4` unknown emitter scripts, and
  `read_only=true`.
- Source safety guard smoke rejected `request_compile=true` on
  `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Parry03.FX_S_Parry03`
  without `allow_source_compile=true`.
- Post-inspection dirty check reported `dirty_content_count=0`,
  `dirty_map_count=0`.
- Required-mode recipe smoke
  `red sword trail compile status smoke` wrote
  `Saved/MCP_NiagaraGeneration/compile_status_recipe_smoke_generation_recipe.json`
  with all Niagara inspection modes successful.
- Preview Player smoke loaded `FX_S_Parry03` and returned an
  `analysis_summary` containing
  `Compile status errors 0 | warnings 0 | dirty 0 | outstanding true`.
- First generated-temp wait smoke with Sleep-only polling timed out with
  outstanding compilation still true; after switching to
  `PollForCompilationComplete()` plus asset-compiling task pumping, the same
  temp system validated successfully.
- Compile gate smoke on
  `/Game/_MCP_Temp/NiagaraGenerated/codex_socket_postprocess_smoke/NS_codex_socket_postprocess_smoke`
  returned `success=true`, `23` scripts, `0` errors, `0` warnings, `0` dirty
  scripts, `wait_timed_out=false`, and
  `outstanding_compilation_requests_after=false`.
- `--socket-postprocess-only` now produced a report with four successful steps:
  renderer binding, User parameter application, module input application, and
  `socket_validate_compile_status`.
- Preview Player gate smoke wrote
  `Saved/MCP_NiagaraGeneration/preview_player_gate_smoke_report.json` and
  captured the actual Preview Player window at
  `Saved/MCP/NiagaraReviews/codex_socket_postprocess_smoke/codex_socket_postprocess_smoke_niagara_previewer.png`.
- Full postprocess smoke now produced five successful steps: renderer binding,
  User parameter application, module input application, compile validation, and
  Preview Player validation. The report is
  `Saved/MCP_NiagaraGeneration/preview_player_postprocess_gate_smoke_report.json`.
- The Preview Player screenshot gate reported `last_preview_renderable=true`,
  `playback_state=playing`, and `looping=true`. The viewport brightness analysis
  warned that the captured frame was mostly dark, so the screenshot is useful as
  Preview Player UI evidence but should not be treated as a strong visual-read
  pass.
- Multi-capture Preview Player smoke with `4` candidates selected a visible
  sword-trail frame and wrote
  `Saved/MCP_NiagaraGeneration/preview_player_multicapture_smoke_report.json`.
- Full postprocess multi-capture smoke succeeded with five steps and selected a
  visible Preview Player screenshot candidate. Report:
  `Saved/MCP_NiagaraGeneration/preview_player_multicapture_postprocess_report.json`.
- Visual-read classification smoke wrote
  `Saved/MCP_NiagaraGeneration/preview_player_visual_read_smoke_report.json`
  with `screenshot_visual_pass=true` and
  `screenshot_visual_read_status=pass`.
- Full postprocess visual-read smoke wrote
  `Saved/MCP_NiagaraGeneration/preview_player_visual_read_postprocess_report.json`
  with five successful steps, compile errors/warnings/dirty all `0`,
  `screenshot_visual_pass=true`, and no visual failure reasons.
- Required visual-read smoke wrote
  `Saved/MCP_NiagaraGeneration/preview_player_visual_required_smoke_report.json`
  with `require_visual_pass=true`, `success=true`, and no fatal reasons.
- Full postprocess required visual-read smoke wrote
  `Saved/MCP_NiagaraGeneration/preview_player_visual_required_postprocess_report.json`
  with five successful steps, compile errors/warnings/dirty all `0`, and
  `require_visual_pass=true`.
- Executor runs now write a compact `<report_stem>_review_summary.json` unless
  `--no-review-summary` is passed. The summary folds compile, preview,
  visual-read, write-count, artifact, issue, and recommended-next-action fields
  into one small review object.
- Review summary smoke wrote
  `Saved/MCP_NiagaraGeneration/review_summary_required_postprocess_report_review_summary.json`
  with `overall_status=pass`, compile/preview/visual all `pass`, and no
  warnings or fatal reasons.
- Socket executor modes now run a post-run dirty package check by default and
  store it as `dirty_package_check` in the execution report plus
  `gates.dirty_packages` in the review summary. `--no-dirty-package-check`
  disables this check when needed.
- Dirty summary smoke wrote
  `Saved/MCP_NiagaraGeneration/dirty_summary_required_postprocess_report.json`
  and
  `Saved/MCP_NiagaraGeneration/dirty_summary_required_postprocess_report_review_summary.json`
  with `dirty_content_count=0`, `dirty_map_count=0`, and overall
  `pass`.
- `analyze_niagara_system` aggregation API smoke wrote
  `Saved/MCP_NiagaraGeneration/analyze_niagara_system_smoke.json` with
  renderer, User parameter, stack, graph, module input, and compile status
  sections all successful. Sibling and Cubeless editor builds both passed after
  releasing the project plugin DLL lock.
- Post-postprocess dirty check reported `dirty_content_count=0`,
  `dirty_map_count=0`.

Remaining deferred:

- Add richer compile event/message extraction if a stable public UE API path is
  identified.

## Phase 0.12: Preview Player Analysis Panel

Rule:

- Niagara analysis should not stay only in JSON or Codex-side summaries.
- When a Niagara System is opened or dropped into the Niagara Preview Player, the viewer should display a compact analysis panel next to the live preview.
- This panel is the shared review surface for Ieta, Tivret, and the user before generation or promotion decisions.

Current panel contents:

- system name
- emitter count
- renderer count and renderer classes
- exposed `User.*` count and settable count
- emitter stack function-call count
- Scratch Pad count
- compile status error/warning/dirty counts and outstanding compilation state
- control hints such as `spawn_control`, `lifetime_control`, `dynamic_material_parameter_control`, `scale_control`, `size_control`, `color_or_tint_control`, and `velocity_control`
- top module/function names per emitter

## Phase 0.13: Module Input Candidate Inspector

Purpose:

- Move from module-name awareness toward controllable module-input awareness.
- Surface candidate controls in the Niagara Preview Player so analysis is shared
  visually instead of staying only in Codex-side JSON.
- Keep the operation read-only until the exact rapid-iteration/default override
  authoring path is verified.

Current implementation:

- UnrealMCP now has a read-only `inspect_niagara_module_inputs` command.
- The command loads a Niagara System and walks emitter graph function-call
  nodes, returning per-module input candidates.
- It filters low-signal graph plumbing pins such as `InputMap`, `OutputMap`,
  parameter-map pins, and `Write Parameter Index` toggles.
- It classifies candidates into control kinds such as:
  - `color`
  - `scale_or_size`
  - `width`
  - `velocity`
  - `spawn`
  - `lifetime`
  - `dynamic_material_parameter`
  - `user_parameter_reference`
- Candidate priority favors modules that matter for generation, including
  `ScaleColor`, `DynamicMaterialParameters`, `ScaleMeshSize`, `AddVelocity`,
  and `SpawnBurst_Instantaneous`.
- The Niagara Preview Player analysis panel now calls
  `inspect_niagara_module_inputs` and shows a `Control candidates` section.
- `get_niagara_preview_player_state.analysis_summary` includes that same
  candidate summary for automation checks.
- `niagara_generation_recipe_builder.py` now supports
  `--module-input-inspect-mode auto|required|off`, defaulting to `auto`.
- Recipes now include:
  - `module_input_analysis`
  - `reference_analysis.module_input_control_candidates`
  - `reference_analysis.module_input_control_kinds`

Verification:

- Built `StylizedCubelessEditor Win64 Development` successfully after adding
  the command and Preview Player integration.
- Runtime inspect succeeded on:
  `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_stack_smoke/NS_red_sword_trail_stack_smoke.NS_red_sword_trail_stack_smoke`
- The command reported `5` emitters, `70` modules, and `283` input candidates.
- The top candidates were `ScaleColor` controls such as `ScaleRGBA`,
  `ScaleRGB`, `ScaleA`, and `ColorCurve`.
- Opening the same temp system in the Niagara Preview Player returned
  `last_preview_renderable=true`, and `analysis_summary` contained both
  `Module input candidates` and `Control candidates`.
- Regenerating a `red sword trail` smoke recipe with
  `--module-input-inspect-mode required` selected the Sword Trail source and
  wrote `module_input_analysis.status=success`, `candidate_count=283`, and
  control kinds including `color`, `velocity`, `spawn`, `scale_or_size`, and
  `width`.

Remaining deferred:

- Resolve exact Niagara Stack UI values and rapid-iteration/default override
  values for each module input.
- Map `DynamicMaterialParameters` to concrete material parameter slots.
- Enable safe writes only for duplicated temp systems under
  `/Game/_MCP_Temp/NiagaraGenerated/`.
- Add generation recipe integration so natural-language requests can select
  module-input edit intents, not just display candidates.

## Phase 0.14: Resolved Stack Input Readback

Purpose:

- Move beyond candidate pin names into actual Niagara Stack input variables.
- Read RapidIteration/default override values where the engine exposes them.
- Keep this as a read-only analysis layer before enabling any temp-system write.

Current implementation:

- `inspect_niagara_module_inputs` now accepts:
  - `include_resolved_stack_inputs`
  - `max_resolved_inputs_per_module`
- When enabled, the command uses Niagara Stack graph utilities to collect
  module input variables and attempts to read matching RapidIteration values
  from the owning Niagara script.
- Returned module objects now include:
  - `resolved_stack_inputs_enabled`
  - `resolved_stack_input_count`
  - `resolved_stack_inputs`
- Each resolved input records:
  - variable name and type
  - hidden status
  - value source, such as `rapid_iteration`, `unresolved_default`, or
    `no_owning_script`
  - RapidIteration parameter name
  - JSON value for supported scalar/vector/color types
- The Preview Player analysis panel now shows a `Resolved stack inputs`
  section with a small sample of RapidIteration values.
- `niagara_generation_recipe_builder.py` records limited examples under
  `module_input_analysis.resolved_input_examples`.

Verification:

- Direct inspect on the Sword Trail source succeeded with
  `include_resolved_stack_inputs=true`, `max_modules=40`, and
  `max_resolved_inputs_per_module=6`.
- The result reported `candidate_count=283` and `resolved_total=284`.
- RapidIteration values were read for controls such as:
  - `EmitterState.Module.Loop Duration = 1`
  - `EmitterState.Module.Loop Delay = 0`
  - `SpawnBurst_Instantaneous.Module.Spawn Count = 1`
  - `SpawnBurst_Instantaneous.Module.Spawn Time = 0`
  - `SpawnBurst_Instantaneous.Module.Spawn Probability = 1`
- The Preview Player `analysis_summary` included the new
  `Resolved stack inputs` section with those values.
- The recipe builder wrote
  `Saved/MCP_NiagaraGeneration/Smoke/red_sword_trail_resolved_input_smoke_generation_recipe.json`
  with `module_input_analysis.include_resolved_stack_inputs=true` and
  `resolved_input_examples`.

Performance rule:

- Resolved stack input readback can produce large JSON and should stay capped
  in UI/recipe paths.
- Default command behavior remains lightweight unless
  `include_resolved_stack_inputs=true` is requested.

Remaining deferred:

- Resolve every default source exactly as the Niagara Stack UI displays it.
- Map unresolved defaults and dynamic inputs into editable authoring operations.
- Add safe temp-only module-input write commands after readback behavior is
  stable across more samples.

## Phase 0.15: Temp-Only Module Input Write API

Purpose:

- Convert resolved stack input readback into the first safe Niagara behavior
  edit path.
- Edit only duplicated temp systems, never source Niagara references.
- Start with existing RapidIteration values only so the command does not create
  new graph structure.

Current implementation:

- UnrealMCP now has `set_niagara_module_input_value`.
- The command supports selectors:
  - `emitter_name` or `emitter_index`
  - `module_name`, `module_index`, or `module_node_guid`
  - `input_name`, with or without the `Module.` prefix
- It writes only existing RapidIteration parameters.
- It refuses source systems outside `/Game/_MCP_Temp/NiagaraGenerated/` unless
  `allow_source_edit=true` is explicitly supplied.
- Supported first-pass value types:
  - float
  - int
  - bool
  - color
  - vec2, vec3, vec4
  - position

Verification:

- Built `StylizedCubelessEditor Win64 Development` successfully.
- On temp system
  `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_stack_smoke/NS_red_sword_trail_stack_smoke.NS_red_sword_trail_stack_smoke`,
  changed:
  `FX_E_SwordTrail04_L / SpawnBurst_Instantaneous / Spawn Count`
  from `1` to `2`.
- Immediate readback reported value `2`.
- Restored the same temp value from `2` back to `1`.
- Final readback reported value `1`.
- Attempting the same write on the source Sword Trail system was rejected with
  the temp-root safety error.
- Opened the temp system in Niagara Preview Player and confirmed the
  `Resolved stack inputs` panel still reported `Spawn Count = 1`.

Remaining deferred:

- Natural-language module-input edit planning in the recipe builder/executor.
- Creating missing override pins when a value is currently an unresolved default.
- Dynamic input, curve, data interface, and complex object input authoring.
- Compile diagnostics specific to Niagara systems after module-input writes.

## Phase 0.16: Natural-Language Module Input Application

Purpose:

- Connect the temp-only module input write API to the recipe executor.
- Let natural-language duration and color intent drive existing module inputs
  when the target temp system exposes safe RapidIteration values.
- Keep the first pass deliberately conservative: no source edits, no missing
  override creation, no dynamic-input rewriting.

Current implementation:

- The recipe builder adds `apply_matching_module_input_overrides` when module
  input readback includes resolved stack inputs and the prompt contains a
  supported duration or color intent.
- The recipe executor now supports:
  `--socket-apply-module-inputs-only`.
- The executor re-inspects the generated temp system, selects only resolved
  stack inputs with existing RapidIteration values, then calls
  `set_niagara_module_input_value`.
- First-pass matching:
  - duration prompts can set numeric inputs such as `Module.Loop Duration`,
    `Module.Lifetime`, `Module.Lifetime Min`, and `Module.Lifetime Max`.
  - color prompts can set color/tint/emissive-like inputs only when those
    inputs already have editable RapidIteration values.

Verification:

- Built a smoke recipe for `red sword trail 2 seconds` with output name
  `red_sword_trail_module_input_smoke`.
- The generated plan included `apply_matching_module_input_overrides`.
- Created the duplicated temp Niagara system under:
  `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_module_input_smoke/`.
- Ran `--socket-apply-module-inputs-only`.
- The executor inspected `5` emitters and `70` modules, then applied `5`
  module input edits:
  - `FX_E_SwordTrail04_L / EmitterState / Module.Loop Duration`: `1 -> 2`
  - `FX_E_SwordTrail05_L / EmitterState / Module.Loop Duration`: `1 -> 2`
  - `FX_E_SwordTrail_Ref01_L / EmitterState / Module.Loop Duration`: `1 -> 2`
  - `FX_E_Line01_L / EmitterState / Module.Loop Duration`: `1 -> 2`
  - `FX_E_SwordTrail_Ref01_L001 / EmitterState / Module.Loop Duration`:
    `1 -> 2`
- The report stayed inside the temp-system policy and did not edit source
  Niagara assets.

Remaining deferred:

- Better semantic ranking so duration does not over-apply to every matching
  emitter when the request implies only one layer.
- Color support for systems where color is driven by material parameters,
  curves, dynamic material parameters, or renderer material instances rather
  than direct RapidIteration color values.
- Size, spawn density, velocity, opacity, and timing-shape intent matching.
- Niagara compile diagnostics after each module-input application batch.

## Phase 0.17: Conservative Module Intent Routing

Purpose:

- Expand natural-language module input application beyond duration.
- Route common visual intent into safe existing RapidIteration values:
  color, size, spawn density, velocity, and opacity.
- Keep routing conservative enough for generated temp systems: avoid curves,
  dynamic inputs, data interfaces, and unresolved defaults.

Current implementation:

- `niagara_generation_recipe_executor.py` now derives a module intent bundle
  from the request text.
- Supported first-pass route families:
  - color terms -> existing `Color`, `Tint`, `Emissive`, `Scale RGB`, or
    `Scale RGBA` inputs.
  - duration terms -> existing `Loop Duration`, `Lifetime`, and similar
    numeric duration inputs.
  - large/small terms -> existing explicit size inputs such as `Scale Factor`,
    mesh scale, sprite size, radius, or width.
  - dense/sparse terms -> existing `Spawn Count` or `Spawn Rate` inputs.
  - fast/slow terms -> existing velocity/speed inputs.
  - fade/strong terms -> existing alpha/opacity inputs.
- The executor now skips no-op writes when the requested value already matches
  the current RapidIteration value.
- Spawn probability is clamped to `0..1`; it is not allowed to become `2` or
  another invalid probability.
- Size routing was tightened after smoke review. It no longer treats broad
  curve values such as `Scale Curve` as safe size controls.

Preview Player update:

- The `Resolved stack inputs` panel now prioritizes review-relevant values
  before generic RapidIteration values.
- Priority examples include color, `Scale RGB`, `Scale Alpha`, `Spawn Count`,
  velocity, `Loop Duration`, lifetime, size, and `Scale Factor`.

Verification:

- Built `StylizedCubelessEditor Win64 Development` successfully after the
  Preview Player C++ change.
- Generated a smoke recipe for:
  `large dense fast red sword trail 2 seconds`
  with output name `red_sword_trail_intent_route_smoke`.
- Duplicated the selected source into:
  `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_intent_route_smoke/`.
- Ran `--socket-apply-module-inputs-only` after resetting the temp system from
  source.
- First broad route attempt applied too much (`44` writes), including curve
  values. The route was tightened and the smoke was rerun.
- Final conservative route applied `18` writes:
  - duration: `Loop Duration` from `1` to `2`.
  - spawn density: `Spawn Count` from `1` to `2`.
  - size: `Scale Factor` vectors multiplied by `1.5`.
  - color: `Scale RGB` to red `[1.0, 0.08, 0.035]` where editable.
  - velocity: `Speed Limit` from `1000` to `1500` where editable.
- Module-input reports now include `application_summary`, grouped by intent and
  by input name. The smoke summary was:
  - `parsed_duration`: `5`
  - `parsed_spawn_multiplier`: `5`
  - `parsed_size_multiplier`: `4`
  - `parsed_color`: `3`
  - `parsed_velocity_multiplier`: `1`
- Preview Player opened the generated temp system with
  `last_preview_renderable=true` and showed priority lines including:
  `Loop Duration = 2`, `Spawn Count = 2`, `Scale Factor = [...]`, and
  `Scale RGB = [1.0, 0.08, 0.035]`.
- Unreal dirty check reported `dirty_content_count=0` and
  `dirty_map_count=0`.

Remaining deferred:

- Layer-aware routing, so a request can target only the main trail, line
  highlight, sparks, smoke, or support emitters.
- Better Korean synonym coverage and numeric parsing for strength words such
  as "아주", "조금", "두 배", "절반".
- Dynamic material parameter slot semantics.
- Curve/data-interface authoring and unresolved default override creation.
- Niagara compile diagnostics after each module-input batch.

## Phase 0.18: Amount Word Multipliers

Purpose:

- Make module intent routing respond to common strength words instead of fixed
  multipliers only.
- Improve Korean prompt handling for early natural-language generation.

Current implementation:

- The executor recognizes amount words while deriving module intent:
  - `두 배`, `두배`, `2배`, `double`, `2x` -> `2.0`
  - `절반`, `반으로`, `half`, `0.5x` -> `0.5`
  - `아주`, `매우`, `very`, `super` -> stronger up/down multiplier
  - `조금`, `약간`, `살짝`, `slightly` -> gentler up/down multiplier
- Verified examples:
  - `아주 크게 빨간 검궤적` -> `size_multiplier=1.8`
  - `조금 작게 빨간 검궤적` -> `size_multiplier=0.85`
  - `두 배 크게 dense fast red trail` -> `2.0` for matching up-route
    families.
  - `절반 작게 sparse slow faint trail` -> `0.5` for matching down-route
    families.

Remaining deferred:

- Phrase-level binding, so `두 배 크게` affects size only instead of every
  positive route family also present in the same prompt.
- Numeric parsing such as `1.25배`, `30%`, and "세 배".

## Phase 0.19: Layer-Aware Module Targeting

Purpose:

- Stop natural-language module input application from always affecting every
  matching emitter.
- Add a conservative first pass for explicit layer targeting such as main,
  line, support/ref, and afterimage.

Current implementation:

- `module_intent_from_recipe` now records `target_layers`.
- Explicit prompt terms activate the filter:
  - line targets: `line only`, `line layer`, `라인`, `선만`, `선형`
  - main targets: `main`, `primary`, `core`, `메인`, `주`, `중심`
  - support targets: `support`, `sub`, `ref`, `afterimage`, `보조`, `서브`,
    `잔상`
- Generic role words such as `sword trail` do not activate filtering, so the
  existing full-system behavior remains the fallback.
- Emitter tags are inferred from emitter names:
  - `FX_E_Line01_L` -> `line`
  - names containing `Ref`, `Sub`, `Support`, or `AfterImage` -> `support`
  - remaining sword/trail emitters -> `main` plus `trail`
- Rows outside the requested target layer are skipped with
  `outside_requested_layer_target` and report their inferred emitter tags.
- Module-input reports now include a `module_intent` block with target layers
  and parsed multipliers.

Verification:

- Parser examples:
  - `line only red sword trail 2 seconds` -> `target_layers=["line"]`
  - `라인만 빨간 검궤적` -> `target_layers=["line"]`
  - `main red sword trail large` -> `target_layers=["main"]`
  - `메인만 크게 빨간 검궤적` -> `target_layers=["main"]`
  - `잔상만 빨간 검궤적` -> `target_layers=["support"]`
- Line-only smoke:
  - prompt: `line only red sword trail 2 seconds`
  - output: `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_line_only_smoke/`
  - final writes: `2`
  - edited emitter: `FX_E_Line01_L` only
  - edited inputs: `Loop Duration`, `Scale RGB`
- Main-only smoke:
  - prompt: `main red sword trail large 2 seconds`
  - output: `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_main_only_smoke/`
  - final writes: `4`
  - edited emitters: `FX_E_SwordTrail04_L`, `FX_E_SwordTrail05_L`
  - edited inputs: `Loop Duration`, `Scale Factor`
- Preview Player opened the main-only smoke with `last_preview_renderable=true`
  and showed main emitters changed while ref/support lines stayed at original
  values.

Remaining deferred:

- Better layer labels from actual renderer/material/module analysis instead of
  name heuristics only.
- Prompt binding for phrases such as "라인은 빨갛게, 메인은 크게".
- Spark/smoke/impact role targeting across broader Niagara samples.

## Phase 0.20: Phrase-Level Layer Intent Binding

Purpose:

- Support prompts that assign different intents to different layers in one
  request.
- Example target: `라인은 빨갛게 2초, 메인은 크게`.

Current implementation:

- The executor splits prompts into simple clauses using separators such as
  comma, semicolon, slash, newline, `and`, `then`, `그리고`, and `그다음`.
- Each clause can become a module binding when it contains:
  - at least one explicit layer target, and
  - at least one actionable module intent.
- Binding currently supports:
  - color from text inside the clause.
  - duration from text inside the clause.
  - size, spawn, velocity, and opacity multipliers from text inside the clause.
- During module input application:
  - if bindings exist, a row is evaluated only against the binding whose
    target layer matches the emitter tag.
  - rows outside all bindings are skipped.
  - each application records `intent_source_text` and
    `intent_target_layers`.
- Reports include `module_intent.bindings` so the generated behavior can be
  reviewed without reading the full prompt parser state.

Verification:

- Parser examples:
  - `line red, main large` -> two bindings:
    line/color and main/size.
  - `line red 2 seconds, main large` -> two bindings:
    line/color+duration and main/size.
  - `라인은 빨갛게, 메인은 크게` -> two bindings:
    line/color and main/size.
  - `라인은 빨갛게 2초, 메인은 아주 크게` -> two bindings:
    line/color+duration and main/size `1.8`.
- Smoke prompt:
  `sword trail, line red 2 seconds, main large`
- Source selection:
  `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Sword_C_Skill01_Trail01.FX_S_Sword_C_Skill01_Trail01`
- Generated temp:
  `/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_phrase_binding_smoke/NS_red_sword_trail_phrase_binding_smoke.NS_red_sword_trail_phrase_binding_smoke`
- Module input application report:
  - total writes: `4`
  - main binding `main large`:
    `FX_E_SwordTrail04_L / ScaleMeshSize / Scale Factor`
    and `FX_E_SwordTrail05_L / ScaleMeshSize / Scale Factor`
  - line binding `line red 2 seconds`:
    `FX_E_Line01_L / EmitterState / Loop Duration`
    and `FX_E_Line01_L / ScaleColor / Scale RGB`
- Preview Player:
  - rebuilt after increasing resolved stack preview lines to `18`.
  - opened the temp system with `last_preview_renderable=true`.
  - analysis showed main `Scale Factor` changed, line `Loop Duration=2`,
    line `Scale RGB=[1.0, 0.08, 0.035]`, and support/ref emitters at source
    defaults.

Remaining deferred:

- Korean connective/particle parsing beyond simple separators.
- Clause-specific source selection hints.
- Multiple bindings for the same layer with conflict resolution.
- More robust phrase-level numeric parsing such as `라인은 1.2배, 메인은 2배`.

Verification:

- Opened `/Game/EL/ART/FX/Niagara/System/PC/Sword/FX_S_Sword_C_Skill01_Trail01.FX_S_Sword_C_Skill01_Trail01` in the Niagara Preview Player.
- `get_niagara_preview_player_state` returned `last_preview_renderable=true`.
- The viewer state included the same analysis summary shown in the panel:
  - `5` emitters
  - `5` renderers
  - `0` exposed `User.*`
  - `70` stack calls
  - `0` Scratch Pads
  - key modules including `DynamicMaterialParameters`, `ScaleMeshSize`, `ScaleColor`, and `AddVelocity`

## Phase 0.13: First Generated Temp Variant Preview

Status:

- The first Preview Player review of a generated temp Niagara variant is working.
- This is not yet full module re-authoring. It is the safe first generation path:
  - choose a source from natural language
  - duplicate the Niagara System to `/Game/_MCP_Temp/NiagaraGenerated/`
  - duplicate renderer/style material candidates
  - apply natural-language color intent to safe material instance vector parameters
  - verify renderer references point to temp materials
  - open the generated temp system in the Preview Player with analysis visible

Verification:

- Recipe: `Saved/MCP_NiagaraGeneration/Smoke/red_sword_trail_stack_smoke_generation_recipe.json`
- Generated system:

```text
/Game/_MCP_Temp/NiagaraGenerated/red_sword_trail_stack_smoke/NS_red_sword_trail_stack_smoke.NS_red_sword_trail_stack_smoke
```

- Duplicated source system and `13` material candidates into the temp root.
- Applied red intent to safe vector parameters on matching temp material instances, including `DarkColor`, `BrightColor`, `LineColor`, and `EmissionColor` where present.
- Renderer readback reported:
  - `5` renderers
  - `5` temp material references
  - `0` source material references
- User parameter pass reported `0` exposed `User.*`, so no parameter values were applied.
- Preview Player opened the generated temp system with `last_preview_renderable=true`, `playback_state=playing`, and the analysis panel populated.

Important distinction:

This is a generated temp variant, not a fully new module-composed Niagara yet. The next generation step is to map `DynamicMaterialParameters` and rapid-iteration/default module inputs so the generator can modify stack behavior, not only duplicated materials.

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
