# PCG Dungeon V2 Prototype

V2 is a separate PCG dungeon-generation prototype. It must not overwrite the
current V1 delivery under `/Game/Cubeless/PCG/Dungeon`.

## Scope

- Asset root: `/Game/Cubeless/PCG/DungeonV2`
- Report root: `Saved/MCP_DungeonV2/`
- Default V2 scale: `DungeonGridCellSize=800`, `DungeonCorridorWidth=800`
- Gameplay implementation remains out of scope.
- Project C++ is not required for this first V2 pass.

## Intended Difference From V1

V1 is the delivered baseline: Geometry Script modules, Python/export-backed
layout, native PCG mesh spawning, and V1 closeout gates.

V2 starts from the same module and spawner pattern, but uses a separate root and
2x spatial scale so layout and room-rule changes can be tested without touching
V1. Room markers and room-variant floor details are still inherited from V1 for
the first prototype; later V2 passes should move those into a debug/review-only
mode or replace them with clearer room design language.

## V2 Core Output Policy

The V2 default Native PCG output is now a core structure view. The generation
reports still keep room-rule, marker, and detail data, but the NativeOutput
spawner contract excludes these semantic/detail modules by default:

- `marker`
- `room_variant_detail`
- `detail_mesh`

This keeps the default visual review focused on generated rooms, corridors,
walls, doors, ceiling, and connector structure. The excluded data remains in
`Saved/MCP_DungeonV2/CubelessDungeonV2_GameplayData.json` and the V2 spawner
contract for audit/debug use.

For a human-readable explanation of the current room rules, marker meanings,
room-variant details, excluded modules, and adjustable config values, check:

- `Saved/MCP_DungeonV2/CubelessDungeonV2_RoomRuleSummary.md`
- `Saved/MCP_DungeonV2/CubelessDungeonV2_RoomRuleSummary.json`

For preset-by-preset room-rule comparison, check:

- `Saved/MCP_DungeonV2/CubelessDungeonV2_RoomRuleMatrix.md`
- `Saved/MCP_DungeonV2/CubelessDungeonV2_RoomRuleMatrix.json`

The matrix compares V2 authoring presets without issuing another PCG refresh,
so it is safe to use as a quick rule-tuning reference.

For quick preset selection and direct tuning knobs, check:

- `Saved/MCP_DungeonV2/CubelessDungeonV2_TuningGuide.md`
- `Saved/MCP_DungeonV2/CubelessDungeonV2_TuningGuide.json`

The tuning guide maps common goals such as compact review, loop-heavy route
testing, open cutaway inspection, boss/combat focus, and balanced default output
to the current V2 authoring presets.

## Runner

From the repository root, with Unreal Editor and UnrealMCP running:

```powershell
python Tools\Unreal\run_pcg_dungeon_v2_prototype.py --preset default
```

The runner builds the V2 assets, refreshes the V2 NativeOutput graph, captures
top and oblique screenshots, and records the V2 final gate under
`Saved/MCP_DungeonV2/`.

To validate an already generated V2 output without issuing another PCG refresh:

```powershell
python Tools\Unreal\run_pcg_dungeon_v2_prototype.py --verify-existing-output
```

`--skip-refresh` is an alias for the same path. This mode still checks the live
editor worktree, verifies NativeOutput, writes the room-rule summary, preset
matrix, and tuning guide, captures top/oblique screenshots, and records the
final gate. It skips `build_all()` and skips the async PCG refresh request.

The runner also checks the live Unreal Editor project directory before it
generates assets. If the editor is attached to another Git worktree, the run
fails early instead of writing `/Game/Cubeless/PCG/DungeonV2` assets into the
wrong checkout.

## How To Tune V2

The safest user-facing workflow is preset-based:

```powershell
python Tools\Unreal\run_pcg_dungeon_v2_prototype.py --preset default --no-build
python Tools\Unreal\run_pcg_dungeon_v2_prototype.py --preset loop_dense --no-build
python Tools\Unreal\run_pcg_dungeon_v2_prototype.py --preset open_cutaway --no-build
```

Available V2 presets:

- `default`: balanced closed-ceiling baseline.
- `small_route`: smallest quick-iteration route.
- `compact_branching`: compact branch readability test.
- `loop_dense`: dense loop/alternate-route stress test.
- `wide_looped`: wider loop-heavy footprint.
- `open_cutaway`: ceiling-off structural inspection.
- `boss_focus`: compact boss/combat focus.
- `long_route`: longer route with fewer loops.

For manual editor tuning, open
`/Game/Cubeless/PCG/DungeonV2/Maps/LVL_Cubeless_PCG_Dungeon_V2`, select the
actor labeled `MCP_Cubeless_Dungeon_V2_PCGBridge`, and edit its actor Tags. The
current V2 prototype treats these `Dungeon...` tags as the supported authoring
surface:

| Tag | Range | Purpose |
| --- | ---: | --- |
| `DungeonSeed` | `1..2147483647` | Deterministic layout seed. |
| `DungeonRoomCount` | `2..32` | Requested room count. |
| `DungeonBranchChancePercent` | `0..100` | Chance to accept valid branch/loop candidates. |
| `DungeonMaxLoopEdges` | `0..16` | Maximum added loop/branch edges. |
| `DungeonGridCellSize` | `200..1200` | World spacing and base XY module scale. |
| `DungeonCorridorWidth` | `200..1200` | Corridor, door, connector, and seal width scale. |
| `DungeonChestCount` | `0..16` | Treasure room budget. |
| `DungeonEnemyCount` | `0..32` | Combat room budget. |
| `DungeonKeyCount` | `0..8` | Progression key room count. |
| `DungeonShopCount` | `0..6` | Shop room count. |
| `DungeonLockedDoorCount` | `0..8` | Locked gate count. |
| `DungeonBossEnabled` | `0..1` | Boss/exit encounter toggle. |
| `DungeonUseCeiling` | `0..1` | Ceiling module toggle. |
| `DungeonCeilingStride` | `0..64` | Ceiling sampling cadence; `0` disables ceiling samples. |
| `DungeonUseThemeMaterials` | `0..1` | Room-theme material override toggle. |
| `DungeonPreviewMode` | `0..1` | Review metadata flag. |

After manual tag edits, run `--verify-existing-output` only if the PCG output is
already generated. If the tags should drive a fresh output, run a preset refresh
or add a matching custom preset in `CubelessDungeonPCGV2.py` and run the runner.

## Preset Refresh Notes

Actual preset refreshes can complete even when the immediate verify command
times out while Unreal is still finishing PCG work. The runner now treats that
as a recoverable post-refresh condition: each immediate verify attempt uses a
shorter socket timeout, and if it times out the runner opens a fresh UnrealMCP
connection and validates the currently generated NativeOutput before continuing
to Summary/Matrix/TuningGuide, screenshots, and the final gate.

Typical preset refresh:

```powershell
python Tools\Unreal\run_pcg_dungeon_v2_prototype.py --preset loop_dense --no-build
```

Useful recovery-related options:

```powershell
--refresh-verify-response-timeout-seconds 90
--verify-recovery-timeout-seconds 300
--verify-recovery-response-timeout-seconds 180
--no-refresh-verify-timeout-recovery
```

Manual `--verify-existing-output` is still useful if the editor was interrupted
after a refresh, but it is no longer required for the normal post-refresh
timeout pattern.

## Current Smoke Result

- Preset: `default`
- Level: `/Game/Cubeless/PCG/DungeonV2/Maps/LVL_Cubeless_PCG_Dungeon_V2`
- Native output: 37 components, 725 instances
- Core output exclusions: 47 static mesh validation actors excluded from NativeOutput (`24` detail meshes, `12` markers, `11` room-variant details)
- Room rules: `11` rooms, main path `[0, 1, 5, 8]`, roles `start=1`, `exit=1`, `boss=1`, `key=1`, `shop=1`, `treasure=3`, `combat=4`, `locked_after=1`
- Final gate: passed
- Screenshot reports: `Saved/MCP_DungeonV2/CubelessDungeonV2_PCGGeneration_*`
- Room-rule summary: `Saved/MCP_DungeonV2/CubelessDungeonV2_RoomRuleSummary.md`
- Room-rule preset matrix: `Saved/MCP_DungeonV2/CubelessDungeonV2_RoomRuleMatrix.md`
- Tuning guide: `Saved/MCP_DungeonV2/CubelessDungeonV2_TuningGuide.md`

Latest `--verify-existing-output` validation passed in 6.984 seconds with the
same `37` native components, `725` instances, screenshot QA pass, final gate
pass, room-rule summary pass, room-rule matrix pass across 8 presets, tuning
guide pass across 6 quick-choice goals, and zero dirty packages.

Additional preset smoke:

- All 8 V2 presets now have actual refresh smoke coverage: `boss_focus`,
  `compact_branching`, `default`, `long_route`, `loop_dense`, `open_cutaway`,
  `small_route`, and `wide_looped`.
- `loop_dense` refresh was re-run after adding automatic recovery. The first
  immediate verify socket timed out after 60.047 seconds, then the runner opened
  a fresh connection and recovered in 4.469 seconds. The full command completed
  successfully in 85.640 seconds with `37` native components, `722` instances,
  Summary/Matrix/TuningGuide pass, screenshot QA pass, final gate pass, and zero
  dirty packages.
- `default` restoration was re-run after adding automatic recovery. The
  immediate verify passed without recovery in 1.469 seconds, and the full
  command completed successfully in 21.141 seconds with `37` native components,
  `725` instances, Summary/Matrix/TuningGuide pass, screenshot QA pass, final
  gate pass, and zero dirty packages.
- `small_route` refresh passed after automatic recovery. The first immediate
  verify socket timed out after 60.016 seconds, recovery succeeded in 4.672
  seconds, and the full command completed successfully in 83.922 seconds with
  `38` native components, `520` instances, 7 rooms, Summary/Matrix/TuningGuide
  pass, screenshot QA pass, final gate pass, and zero dirty packages.
- `open_cutaway` refresh passed without recovery. The full command completed
  successfully in 19.282 seconds with `33` native components, `492` instances,
  ceiling disabled by preset intent, Summary/Matrix/TuningGuide pass, screenshot
  QA pass, final gate pass, and zero dirty packages.
- `boss_focus` refresh passed after automatic recovery. The first immediate
  verify socket timed out after 60.032 seconds, recovery succeeded in 4.687
  seconds, and the full command completed successfully in 83.344 seconds with
  `38` native components, `683` instances, 10 rooms, Summary/Matrix/TuningGuide
  pass, screenshot QA pass, final gate pass, and zero dirty packages.
- Final `default` restoration was run again after those preset smokes. The
  first immediate verify socket timed out after 60.032 seconds, recovery
  succeeded in 4.703 seconds, and the full command completed successfully in
  84.313 seconds with `37` native components, `725` instances,
  Summary/Matrix/TuningGuide pass, screenshot QA pass, final gate pass, and zero
  dirty packages.
- `compact_branching` refresh passed without recovery. The full command
  completed successfully in 20.657 seconds with `38` native components, `562`
  instances, 8 rooms, Summary/Matrix/TuningGuide pass, screenshot QA pass, final
  gate pass, and zero dirty packages.
- `wide_looped` refresh passed after automatic recovery. The first immediate
  verify socket timed out after 60.031 seconds, recovery succeeded in 4.781
  seconds, and the full command completed successfully in 84.563 seconds with
  `38` native components, `778` instances, Summary/Matrix/TuningGuide pass,
  screenshot QA pass, final gate pass, and zero dirty packages.
- `long_route` refresh passed after automatic recovery. The first immediate
  verify socket timed out after 60.032 seconds, recovery succeeded in 4.500
  seconds, and the full command completed successfully in 85.172 seconds with
  `38` native components, `720` instances, Summary/Matrix/TuningGuide pass,
  screenshot QA pass, final gate pass, and zero dirty packages.
- Final `default` restoration after all 8 preset smokes passed after automatic
  recovery. The first immediate verify socket timed out after 60.031 seconds,
  recovery succeeded in 4.781 seconds, and the full command completed
  successfully in 83.969 seconds with `37` native components, `725` instances,
  Summary/Matrix/TuningGuide pass, screenshot QA pass, final gate pass, and zero
  dirty packages.
- `loop_dense` refresh was requested with `--no-build`; the immediate verify
  call timed out, but follow-up `--verify-existing-output` passed in 7.718
  seconds with `37` native components, `722` instances, screenshot QA pass,
  final gate pass, and zero dirty packages.
- `default` refresh was requested again for final restoration; the immediate
  verify call timed out, but follow-up `--verify-existing-output` passed in
  7.797 seconds with `37` native components, `725` instances, screenshot QA
  pass, final gate pass, and zero dirty packages. Final `GameplayData` is back
  on default config (`seed=242857`, `grid_cell_size=800`,
  `corridor_width=800`).
