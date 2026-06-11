# PCG C++ Improvement Backlog

This backlog collects places where current PCG, screenshot, or UnrealMCP
workflows rely on fragile Python/editor scripting workarounds. Do not implement
these as C++ changes one by one during PCG tuning. Batch them later after the
workarounds prove which API surface is worth making durable.

## Rules

- Keep using Blueprint, PCG graph, editor scripting, and MCP Python first.
- Add an item here when the workaround becomes slow, error-prone, or hard to
  validate.
- Do not modify non-exception project C++ from this backlog without explicit
  user approval.
- UnrealMCP plugin C++ remains an allowed exception, but still prefer batching
  related bridge/API changes.
- Each C++ item should include the current workaround, the desired durable API,
  and the verification gate that would prove it works.

## Current Candidates

### 1. Bookmark and Screenshot Capture API

- Current workaround: Python sets viewport camera locations, uses temporary
  validation cameras or OS/window capture, and then waits for screenshot files.
- Pain: bookmark recall can read the wrong/stale viewport buffer, keyboard
  shortcut recall can be blocked by the Windows session, and multi-bookmark
  validation costs too much operator time.
- Latest evidence: `AutomationLibrary.take_high_res_screenshot` produced the
  first validation PNG but later capture requests reported scheduled tasks
  without writing files. The fallback `PrintWindow` OS capture succeeded, but
  it captures the whole editor window and can show a stale viewport if the
  camera update path fails.
- Desired API: UnrealMCP command that reads user-owned bookmark camera data
  without overwriting it, applies the view to a known editor viewport, captures
  a screenshot, waits until the final image is written, and reports resolution,
  path, and capture camera transform.
- Verification gate: capture bookmark slots 1 and 2 in sequence, prove image
  files differ when camera transforms differ, and report no dirty packages.

### 1a. Safe Editor Map Transition API

- Current workaround: Python scripts call `load_level` or `load_map` after trying
  to clear Python references and run GC.
- Pain: loading another map from inside `execute_python` can still leave the old
  world package referenced by `FPyReferenceCollector`, causing Unreal's `World
  Memory Leaks` fatal during editor map transition.
- Desired API: UnrealMCP command that performs map transition outside the active
  Python execution frame, clears Python exception/reference state, runs Unreal
  GC at the right boundary, and returns a structured success/failure result.
- Verification gate: switch from `/Game/_MCP_Temp/PCG/LVL_ElectricDreams_SplineAssembly_MCP`
  to `/Game/_MCP_Temp/PCG/LVL_PCG_LandscapeValidation_MCP` without a crash,
  with no stale old-world reference in the log.

### 2. PCG Regeneration Completion and Readback

- Current workaround: Python calls `cleanup`, `generate`, `generate_local`,
  schedules ticker retries, and polls ISM components until output appears.
- Pain: delayed PCG output causes immediate validation false negatives and
  forces scripts to carry retry loops.
- Latest evidence: a whole-Landscape candidate actor layer spawned `161` PCG
  actors but produced `0` ISM instances on
  `/Game/_MCP_Temp/PCG/LVL_PCG_LandscapeValidation_MCP`. The validation pass
  had to fall back to appending transforms to existing runtime PCG-generated
  ISM components.
- Desired API: UnrealMCP command that refreshes selected PCG components and
  waits for generation completion or timeout, then returns generated component
  counts and package dirty state.
- Verification gate: run on a selected PCG actor with known tree, grass, and
  rock outputs; validate count changes after changing an exposed actor
  property.

### 3. Safe PCG Data Introspection

- Current workaround: Python avoids broad reflection after an unsafe
  `PCGBasePointData.GetDensityBounds` probe crashed the editor.
- Pain: readback is limited to manually known methods, so diagnostics are slow
  and easy to under-report.
- Desired API: read-only C++ wrapper for PCG point data that validates ranges
  before reading counts, density bounds, transforms, metadata attribute names,
  and selected numeric/string/object attributes.
- Verification gate: malformed or empty point data returns structured errors
  instead of asserting or crashing.

### 4. Native Road Clearance and Overlap Filtering

- Current workaround: Python validates nearest-route clearance and overlap
  after generation while native `PCGDistanceSettings` and attribute/density
  filter semantics remain diagnostic.
- Pain: the active quality guarantee lives partly outside the graph, so visual
  tuning and native graph promotion can drift apart.
- Desired API or graph support: durable native PCG rule path for category
  clearance and footprint overlap, or a focused C++ PCG element if built-in
  nodes cannot express the exact road/tree/grass/rock rules reliably.
- Verification gate: native output matches Python validator targets for gravel,
  stone, embankment, tree, grass, and rock clearance with zero hard-overlap
  violations.

### 4a. High-Density PCG Validation Scatter

- Current workaround: Python resets previous supplements by removing thousands
  of ISM instances one by one, line-traces Landscape height for every candidate,
  filters road clearance and object spacing in Python, then appends `180k+`
  validation instances to PCG-owned ISM components.
- Pain: this pass works for validation, but it is slow enough to interrupt
  iteration, depends on editor-exposed component mutation, and does not prove
  the native PCG graph can reproduce the same full-Landscape density.
- Latest evidence: the full-coverage validation pass scanned `186,275`
  instances, reset `186,200` previous supplements, and added `180,000` grass
  instances plus tree/rock supplements through Python.
- Desired API or graph support: native PCG element or UnrealMCP helper that can
  apply deterministic density, Landscape projection, category spacing, and road
  clearance in one native generation path rather than as a post-process.
- Verification gate: regenerate the validation Landscape to the same target
  counts with `0` road violations and `0` tilt violations without Python
  per-instance reset/scatter loops.

### 5. PCG Graph Authoring Helpers

- Current workaround: Python creates PCG nodes, sets editor properties by name,
  and relies on several engine-exposed classes whose property behavior varies
  by UE version.
- Pain: graph authoring scripts are verbose, and failures often appear only
  after live graph generation.
- Latest evidence: true-material grass, rock, and tree graphs had to be
  regenerated across `102` PCGGraph assets to add the same actor-property mesh
  override branch that base graphs already had. The first runtime validation
  failed only for rocks because `MaterialMood=2` routed to a true-material rock
  graph that still spawned the default mesh.
- Desired API: typed UnrealMCP helpers for common PCG graph operations: create
  node, set settings with validation, wire pins, configure actor property
  getters, configure static mesh spawners with attribute selectors, and save
  with compile/validation reporting.
- Verification gate: rebuild a small fixture graph with actor-property mesh
  overrides and verify BP variable changes alter spawned meshes.

### 5a. Actor-Property Mesh Override Promotion

- Current workaround: validation can directly replace PCG-generated ISM
  component meshes with `SM_Grass_Medium01` after generation to make the ground
  read more like a grass carpet.
- Pain: direct component mesh replacement is useful for visual validation but
  bypasses the intended PCG rule that Static Mesh Spawner mesh choices should
  be driven through Blueprint actor properties.
- Latest evidence: the Landscape validation pass changed leaf/fern grass
  components to `SM_Grass_Medium01` and excluded flower components from the
  high-density scatter. It improved the output but remains a Python
  post-process.
- Latest validation: runtime Blueprint variables were added to
  `/Game/Cubeless/PCG/Runtime/Blueprints/BP_Cubeless_PCG_EcosystemRuntime`, and
  the two-phase validation report
  `Saved/MCP_PCG/pcg_runtime_actor_property_override_validation_report.json`
  passed for grass, tree, and rock. Generated ISM rows used `SM_Fern_01`,
  `SM_Conifer_08`, and `SM_SmallRock_02` from actor properties with no direct
  component mesh replacement.
- Desired API or graph support: make the production/runtime PCG graphs expose
  grass/tree/rock mesh selector inputs through actor properties by default, and
  provide a validation command that proves the generated ISM mesh paths match
  those Blueprint values after regeneration.
- Verification gate: keep the current grass/tree/rock runtime override report
  passing after future graph rebuilds, including true-material graph routes.

### 5b. Viewport Camera Control Reliability

- Current workaround: Python calls `set_level_viewport_camera_info`, invalidates
  viewports, then uses HighResShot, Automation screenshot tasks, or OS
  `PrintWindow` fallback.
- Pain: camera changes and screenshot output can lag or capture a stale
  viewport. This makes close/far visual QA less trustworthy than the numeric
  reports.
- Latest evidence: after setting a close validation camera, OS capture still
  showed the editor viewport from a higher/wider view, while console
  `HighResShot` did not always write a file immediately.
- Desired API: a native editor viewport command that applies a camera transform,
  waits for the target viewport to render that exact transform, captures either
  viewport-only or whole-editor output, and returns the actual camera transform
  used for the image.
- Verification gate: capture three different camera transforms in sequence and
  confirm image hashes and reported transforms differ as expected.

### 6. Long Command Transport and Response Framing

- Current workaround: large Python payloads previously stressed the bridge;
  `MCPServerRunnable` has already been hardened to buffer JSON chunks and send
  complete responses.
- Pain: any future large binary/report payload could regress this class of
  error.
- Desired API: keep transport chunking covered by an explicit bridge regression
  test and avoid sending huge source strings when file execution is available.
- Verification gate: execute a large but harmless file-based command and a large
  response command without `BufferReader` or partial JSON failures.

## Keep In Python For Now

- One-off temp validation level setup.
- Disposable `_MCP_Temp` actor cleanup.
- Report JSON writing under `Saved/MCP_*`.
- Local visual tuning experiments that are not yet stable production behavior.
- Small asset inspections where Unreal Python exposes a safe, documented API.
