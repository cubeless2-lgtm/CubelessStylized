# Niagara Preview Lab Rules

Niagara Preview Lab is the project's visual safety and capture system for generated or modified Niagara work.

Niagara Preview Player is the level-independent editor widget layer for fast
asset/actor drag-and-drop, source selection, and future isolated preview-scene
playback. It complements the Preview Lab map; it does not replace the map's
formal capture rule until the viewport player has equivalent still/video
capture and cleanup guarantees.

All Niagara generation, duplication, material replacement, Scratch Pad behavior testing, and final visual preview must use the dedicated Niagara Preview Lab map:

```text
/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'
```

## Camera Bookmarks

Use Preview Lab auto framing first. When temporary Preview Lab actors exist, the capture command should frame those actors with an auto camera so the effect is visible without requiring a hand-authored bookmark.

The map's existing editor camera bookmarks remain a human reference and fallback:

| Bookmark | Review distance |
| --- | --- |
| 1 | Near |
| 2 | Mid |
| 3 | Far |

## Screenshot Rule

Use auto-framed view distance as a visibility fallback sequence:

1. Start from view 1, the near auto-framed view.
2. If the effect is not visible or cannot be judged from view 1, use view 2, the mid auto-framed view.
3. If view 2 still does not show the effect clearly, use view 3, the far auto-framed view.

The selected screenshot should be the first view in this sequence where the effect is visible and reviewable.

Do not capture all three views by default. Capture all three only when the user asks for a distance comparison, when the effect's scale is uncertain, or when a formal review needs near/mid/far evidence.

## Motion And Video Rule

Timing-sensitive Niagara effects should include a short motion review:

- sword trails
- slash ribbons
- projectile trails
- hit bursts with important timing
- dissolve, spawn, and vanish effects

Capture a PNG frame sequence first. Convert to video only after the frame sequence is verified. The frame sequence is the source-of-truth review artifact because individual frames can be inspected when timing or visibility fails.

Use `preview_niagara_system_in_preview_lab` as the default optimized still-review route when C++ MCP is available. It avoids separate spawn, state, capture, and cleanup round trips. If the first still is invisible or timing-sensitive, use `sample_niagara_system_in_preview_lab` to capture multiple warmup/view candidates in one MCP round trip. Use `Tools/Unreal/niagara_review_capture.py` as the no-C++ fallback runner. For motion-driven trails, run a frame sequence with `--motion slash` or another motion preset.

The report must call out failures such as:

- effect is not visible from one or more bookmarks
- effect is too small or too large for the review frame
- effect is off-center
- effect reads well near but not mid/far
- timing makes the effect miss the capture frame
- material is too dim, too bright, or visually inconsistent with the stylized reference

## Scope

This rule applies to:

- `_MCP_Temp` duplicate tests
- generated primitive tests
- generated material instance tests
- BP/User parameter integration tests
- Scratch Pad reuse or generation tests
- production promotion reviews

Original reference assets remain read-only during Niagara Preview Lab work.

## Niagara Preview Player Rule

Use `open_niagara_preview_player` to open the editor widget when the task starts
from a dragged asset or actor rather than a known path. Use
`get_niagara_preview_player_state` to confirm what was dropped before generating,
duplicating, or sampling anything.

The current MVP is a Slate drop surface. It records dropped Content Browser
assets and World Outliner actors only. Future versions may embed `FPreviewScene`,
Niagara playback controls, material/context presets, still capture, and motion
capture, but the same rule applies: do not save or modify source assets merely
because they were dropped into the player.

## Map Reload Safety Rule

Do not reload `/Game/SampleTestMap/Niagara_TestMap` from the same Unreal Python session after preview actors, world objects, callbacks, or captured references have existed.

This is a crash-safety rule. On 2026-06-11, reloading the same review map through `EditorLoadingAndSavingUtils.load_map` after Niagara preview work caused Unreal to exit with:

```text
World Memory Leaks: Old Package /Game/SampleTestMap/Niagara_TestMap not cleaned up by GC
```

Safe behavior:

- Use the already loaded review map when possible.
- Load the review map only at the beginning of a fresh operation, before creating preview actors or holding world references.
- Delete preview actors by the `MCP_NiagaraPreviewLab_` label prefix. Also clean the legacy `MCP_NiagaraReview_` prefix when present.
- Drop Python references to actors, components, world objects, tasks, and callbacks after cleanup.
- Do not save the review map during preview work.
- If the map must be reset, restart Unreal Editor and open the map fresh instead of reloading it from the same Python session.
