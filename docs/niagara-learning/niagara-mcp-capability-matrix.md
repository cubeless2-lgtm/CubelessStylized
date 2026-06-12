# Niagara MCP Capability Matrix

Last updated: 2026-06-12 KST

This matrix separates what is already safe to run, what is implemented through
UnrealMCP C++, what still needs C++ authoring work, and what should stay
deferred until the API surface is safer.

## Workspace Scope

| Area | Location | Current role |
| --- | --- | --- |
| Project | `C:\Git\CubelessStylized` | Game project, executor scripts, docs, project plugin copy |
| Sibling | `C:\Git\unreal-mcp-cubeless` | Primary UnrealMCP authoring branch for reusable MCP work |
| Project plugin copy | `C:\Git\CubelessStylized\Plugins\UnrealMCP` | Build/runtime validation copy used by this project |

Keep Git status, diffs, commits, and pushes separate between the project repo,
the project plugin submodule, and the sibling repo.

## Capability Summary

| Capability | Current status | Implementation surface | Safe write scope | Notes |
| --- | --- | --- | --- | --- |
| Natural-language recipe build | implemented | `Tools/Unreal/niagara_generation_recipe_builder.py` | no asset writes | Parses style, color, duration, motion, layer, and phrase hints into a recipe. |
| Temp Niagara duplication | implemented | executor in Unreal Python | `/Game/_MCP_Temp/NiagaraGenerated/` | Source systems remain read-only. |
| Temp Material Instance duplication/tint | implemented | executor in Unreal Python | `/Game/_MCP_Temp/NiagaraGenerated/<slug>/Materials/` | Only duplicated temp material instances are edited. |
| System analysis aggregation | implemented | C++ MCP: `analyze_niagara_system` | read-only | Aggregates renderer, User parameter, stack, graph, module-input, and compile-health inspection. |
| Renderer/material inspection | implemented | C++ MCP: `inspect_niagara_renderers` | read-only | Reads renderer classes, material slots, primary material, and used materials. |
| Renderer material binding | implemented | C++ MCP: `set_niagara_renderer_material` | temp systems by default | Source edit requires explicit `allow_source_edit=true`. |
| Emitter attach/duplicate from source | implemented | C++ MCP: `duplicate_or_attach_emitter_from_source` | temp systems by default | Adds a source emitter asset or source system emitter handle into a generated temp system. |
| User parameter inspection | implemented | C++ MCP: `inspect_niagara_user_parameters` | read-only | Reads exposed `User.*` values and supported types. |
| User parameter writes | implemented | C++ MCP: `set_niagara_user_parameter` | temp systems by default | Supports bool, int, float, vector, color, and object-like values. |
| Stack function-call inspection | implemented | C++ MCP: `inspect_niagara_stack` | read-only | Reads system, emitter, and Scratch Pad stack calls. |
| Graph topology inspection | implemented | C++ MCP: `inspect_niagara_graph` | read-only | Reads system scripts, emitter graphs, Scratch Pad graphs, nodes, pins, and links. |
| Scratch Pad interface inspection | implemented | C++ MCP: `inspect_niagara_scratch_pad_interface` | read-only | Reads Scratch Pad ownership, usage, supported usage contexts, inputs, outputs, and compact graph summaries. |
| Scratch Pad script duplication | implemented | C++ MCP: `create_or_duplicate_scratch_pad_module` | temp systems by default | Duplicates an existing Scratch Pad script into a generated temp system or emitter without stack insertion or node wiring. |
| Scratch Pad stack insertion | implemented | C++ MCP: `add_scratch_pad_module_to_stack` | temp systems by default | Inserts a target-local Module Scratch Pad into a system/emitter stack through Niagara stack utilities after usage compatibility validation; skips duplicate insertion by default. |
| Scratch Pad recipe/executor insertion | implemented | builder/executor + C++ MCP | temp systems by default | Recipes can plan target-local Scratch Pad stack insertion when prompt intent requests Scratch Pad/reactive behavior; executor applies it through `add_scratch_pad_module_to_stack` and reports inserted/skipped/failed counts plus compile validation. |
| Module input candidate inspection | implemented | C++ MCP: `inspect_niagara_module_inputs` | read-only | Reads existing module input candidates and optional resolved stack inputs. |
| New RapidIteration override creation | implemented | C++ MCP: `create_niagara_module_input_override` | temp systems by default | Creates missing module input overrides; existing overrides require `overwrite_existing=true`. |
| Existing RapidIteration writes | implemented | C++ MCP: `set_niagara_module_input_value` | temp systems by default | Writes existing RapidIteration overrides only. It does not create missing overrides. |
| Batch RapidIteration module input writes | implemented | C++ MCP: `set_niagara_module_inputs_batch` | temp systems by default | Applies multiple set/create/upsert RapidIteration edits and saves once. |
| Compile health inspection | implemented | C++ MCP: `inspect_niagara_compile_status` | read-only by default | Can request/wait compile for generated temp systems. Source compile is guarded. |
| Compile validation gate | implemented | executor socket postprocess | temp systems | Fails on wait timeout, outstanding compile, compile errors, dirty scripts, missing scripts. |
| Preview Player open/state | implemented | C++ MCP editor commands | no asset writes | `open_niagara_preview_player` returns loaded state; state refresh is optional. |
| Preview Player screenshot gate | implemented | executor + OS-window capture script | generated files only | Captures multiple candidates and selects the best visual-read frame. |
| Visual-read classification | implemented | executor screenshot analysis | generated files only | Advisory by default; fatal when `--preview-require-visual-pass` is passed. |
| Dirty package gate | implemented | executor via `execute_python` | read-only check | Any recorded dirty content/map package marks the review failed. |
| Compact review summary | implemented | executor | generated JSON only | Writes `<report_stem>_review_summary.json` unless `--no-review-summary` is passed. |

## Python-Only Or Mostly Python Work

These tasks can continue without new C++ as long as they only affect generated
temp assets, reports, or docs.

| Task | Status | Next use |
| --- | --- | --- |
| Prompt parsing and phrase binding | implemented, iterative | Improve Korean connective/particle parsing and conflict resolution. |
| Layer-aware emitter targeting | implemented, heuristic | Replace name heuristics with graph/renderer/material-derived roles. |
| Recipe/report/schema refinement | safe | Keep generated report shapes stable before deeper graph authoring; Scratch Pad write counts are now included in review summaries. |
| Review summary aggregation | implemented | Add richer human-readable summaries or CI-friendly pass/fail exports. |
| Preview screenshot scoring | implemented, heuristic | Tune thresholds per effect family after more samples. |
| Temporary generated asset orchestration | implemented subset | Continue only under `/Game/_MCP_Temp/NiagaraGenerated/`. |

## C++ MCP Work Needed Next

These are the next reasonable C++ extension targets. Keep them temp-only first,
batch-oriented, and validation-gated.

| Priority | API | Status | Purpose |
| --- | --- | --- | --- |
| 1 | `analyze_niagara_system` aggregation | implemented | One call that combines renderer, user parameter, stack, graph, module input, compile summary, and key limitations. |
| 2 | `create_niagara_module_input_override` | implemented | Add a missing RapidIteration override when the module input exists but has no writable override yet. |
| 3 | `set_niagara_module_inputs_batch` | implemented | Apply multiple existing or newly created module input writes with one aggregated result. |
| 4 | `inspect_niagara_scratch_pad_interface` | implemented | Read Scratch Pad input/output signatures, owning scripts, and editable boundaries. |
| 5 | `duplicate_or_attach_emitter_from_source` | implemented | Add an existing source emitter into a generated temp system. |
| 6 | `create_or_duplicate_scratch_pad_module` | implemented | Duplicate an existing Scratch Pad into a temp system/emitter without arbitrary node edits. |
| 7 | `add_scratch_pad_module_to_stack` | implemented | Insert a duplicated target-local Scratch Pad module into a compatible stack. |
| 8 | `connect_niagara_graph_nodes_batch` | deferred | Low-level node/link mutation for Scratch Pad or script graphs. |

## Deferred Or High-Risk

| Capability | Why deferred |
| --- | --- |
| Arbitrary Scratch Pad node creation/wiring | High crash/regression risk without a transaction, graph diff, and compile rollback story. |
| Source asset Niagara writes | Source edit must remain opt-in and reviewed; temp generated systems are the default write target. |
| Production promotion to `/Game/Cubeless/FX/Generated/` | Needs manual review gate, screenshot evidence, compile pass, dirty pass, and explicit promotion workflow. |
| Whole-material opaque Custom-node conversion | Project material rule prefers hybrid native nodes with small Custom islands. |
| Preview Lab map reload during Python sessions | Project rule forbids reloading the same dirty/referenced preview map; use Preview Player first. |
| Saving `_MCP_Temp` outputs to Git | `_MCP_Temp` is disposable and gitignored unless explicitly versioned. |

## Recommended Next Order

1. Add more source samples for Scratch Pad stack insertion across different effect families and target usages.
2. Add insertion rollback or disable-on-failed-compile handling before allowing larger automatic batches.
3. Extend planning beyond primary-source-local Scratch Pads only after duplicate/insert has enough successful samples.
4. Keep lower-level Scratch Pad graph creation/wiring deferred until stack insertion has more runtime samples.

## Required Review Gates For Generated Niagara

Before any generated temp Niagara system is considered promotable:

| Gate | Required status |
| --- | --- |
| Compile | `gates.compile.status=pass`, errors/warnings/dirty/missing reviewed |
| Preview Player | `gates.preview.status=pass`, `last_preview_renderable=true` |
| Visual read | `gates.visual.status=pass` or explicit manual acceptance |
| Dirty packages | `gates.dirty_packages.status=pass` |
| Source policy | Original source assets remain read-only |
| Screenshot | Selected Preview Player screenshot path is present |
| Review summary | `overall_status=pass` or a documented manual override |
