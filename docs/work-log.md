# CubelessStylized Work Log

Durable local fallback for project memory when Notion capture is unavailable.

## 2026-05-29 - Ieta Slate status workflow

### Summary
- Investigated when the Ieta Slate status window appears.
- Original behavior: the window appeared only after Unreal MCP received and executed a bridge command.
- Updated UnrealMCP Slate behavior to distinguish Ieta planning from Tivret builder work.

### Decisions
- `ieta_status` is treated as Ieta planning/thinking.
- Ieta planning Slate uses Korean Ieta-style wording and shows the progress bar.
- Real MCP work commands are treated as Tivret builder work.
- Tivret work Slate shows command details, parameter summary, and a progress bar.
- When a new Slate popup is shown, any existing Ieta Slate popup is closed first to prevent overlap.
- Tivret work completion sets progress to complete and closes the Slate popup after 10 seconds.
- UnrealMCP plugin C++ may be modified directly without asking again.

### Changed Files
- `AGENTS.md`
- `Plugins/UnrealMCP/Source/UnrealMCP/Private/UnrealMCPBridge.cpp`
- `Plugins/UnrealMCP/Source/UnrealMCP/Private/MCPServerRunnable.cpp`
- `Plugins/UnrealMCP/Source/UnrealMCP/Public/UnrealMCPBridge.h`
- `../unreal-mcp-cubeless/Python/unreal_mcp_server.py`
- `../unreal-mcp-cubeless/MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/Private/UnrealMCPBridge.cpp`
- `../unreal-mcp-cubeless/MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/Private/MCPServerRunnable.cpp`
- `../unreal-mcp-cubeless/MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/Public/UnrealMCPBridge.h`

### Verification
- Built `StylizedCubelessEditor Win64 Development` with UE 5.7 successfully.
- Restarted the Unreal Editor successfully.
- Confirmed `.mcp.json` defines `unrealMCP`, `uv` resolves, `../unreal-mcp-cubeless/Python` exists, and `127.0.0.1:55557` is reachable.
- Confirmed `ieta_status` responds with `status: success`.
- Confirmed a later `ping` MCP work request replaces the existing Slate popup and the work popup closes after the completion delay.

### Residual Notes
- Notion capture failed because the Notion auth token was expired.
- Direct socket responses show Korean text mojibake in terminal output, but Unreal MCP command status succeeds.
- Existing unrelated asset changes were present in the working tree and were not reverted.

## 2026-05-29 - Ieta/Tivret Slate progress reset

### Summary
- Reworked the Ieta Slate flow from the user's clarified requirements.
- Ieta planning/thinking commands now show the Slate window and a progress bar instead of suppressing the window.
- Tivret MCP work commands still show the Slate window with command details, parameter summary, and a progress bar.
- New Slate popups close any existing Ieta Slate popup first, so windows do not overlap.
- Tivret completion uses Ieta-style Korean completion text, sets progress to complete, and closes the Slate window after 10 seconds.

### Verification
- Built `StylizedCubelessEditor Win64 Development` with UE 5.7 successfully.
- Restarted the Unreal Editor successfully.
- Sent `ieta_status`; the Unreal Editor top window changed to `이에타가 처리 중`, confirming the planning Slate appears.
- Sent `ping`; the Slate appeared for Tivret work and the editor returned to the main `StylizedCubeless` window after the 10-second completion delay.

## 2026-05-29 - Selected texture sRGB disabled

### Summary
- Used Unreal MCP `execute_python` to process the currently selected Unreal Editor assets.
- All 10 selected assets were textures.
- Set or verified `sRGB = false` on all selected textures and saved the assets.

### Verification
- Final verification reported 10 selected textures with `sRGB` off.
- No skipped assets and no errors remained after rerunning without the unsupported Python `post_edit_change` call.

## 2026-05-29 - Ieta Slate popup timing

### Summary
- Improved the Ieta Slate popup timing in the UnrealMCP bridge.
- After creating or updating the Slate window, the bridge now pumps Slate messages and forces a redraw immediately.
- This keeps the existing behavior where real Tivret MCP work closes the popup 10 seconds after completion.

### Verification
- Built `StylizedCubelessEditor Win64 Development` with UE 5.7 successfully.
- Restarted the Unreal Editor successfully.
- Verified `ieta_status` and `ping` show the `이에타가 처리 중` Slate window quickly after MCP calls.
- Verified the Tivret work popup still closes after the 10-second completion delay.

## 2026-05-30 - Ieta planning Slate auto-close

### Summary
- Updated Ieta planning/status completion so the Slate window also schedules a 10-second close.
- The scheduled close remains bound to the specific window that created it, so a later Tivret work popup is not closed by an older Ieta timer.

### Verification
- Built `StylizedCubelessEditor Win64 Development` with UE 5.7 successfully.
- Restarted the Unreal Editor successfully.
- Verified a standalone `ieta_status` popup appears and closes after the 10-second delay when no Tivret work follows.
- Verified a `ping` Tivret work popup started within the Ieta delay remains visible when the older Ieta timer fires, then closes on its own 10-second completion delay.

## 2026-05-30 - Selected texture sRGB repeat helper

### Summary
- Used Unreal MCP `execute_python` to set `sRGB = false` on the currently selected textures.
- Added `Tools/Unreal/set_selected_texture_srgb.py` as a reusable Unreal Editor Python helper for repeated selected-texture sRGB changes.

### Verification
- Processed 4 selected assets.
- All 4 selected assets were textures.
- Changed and verified all 4 textures with `sRGB = false`.
- No skipped assets and no errors.

## 2026-05-30 - Ieta Slate window reuse

### Summary
- Updated the Ieta Slate status window to reuse the existing popup when it is already open.
- New MCP status updates now change the text/progress inside the existing window instead of destroying and recreating it.
- Added a close-generation guard so an older 10-second auto-close timer cannot close a reused window after a newer Ieta or Tivret update arrives.
- Kept the rule that Ieta-only work auto-closes after 10 seconds if no Tivret work follows.

### Verification
- Built `StylizedCubelessEditor Win64 Development` with UE 5.7 successfully.
- Restarted the Unreal Editor successfully.
- Verified repeated `ieta_status` calls keep the same Slate window handle while updating the displayed state.
- Verified a standalone Ieta popup closes after the 10-second delay.
- Verified a Tivret `ping` update that arrives during the Ieta delay is not closed by the older Ieta timer and closes on its own completion delay.

## 2026-05-30 - Ieta Slate close delay shortened

### Summary
- Removed the completion message that explicitly says the Slate window will close after a delay.
- Changed the Ieta/Tivret Slate completion auto-close delay from 10 seconds to 5 seconds.

### Verification
- Built `StylizedCubelessEditor Win64 Development` with UE 5.7 successfully.
- Restarted the Unreal Editor successfully.
- Verified a standalone `ieta_status` popup appears and closes after the 5-second delay.
- Verified a Tivret `ping` popup appears and closes after the 5-second delay.

## 2026-05-30 - Selected texture asset rename

### Summary
- Exported previews for 28 selected texture assets and reviewed them as 7 material sets.
- Renamed each 4-texture set using the requested order: BaseColor, Normal, Height, Roughness.
- Applied the naming convention `T_<MaterialName>_D`, `T_<MaterialName>_N`, `T_<MaterialName>_H`, `T_<MaterialName>_M`.

### Material Sets
- `RoundPebbleCobble`
- `WhiteStoneTile`
- `FineAsphalt`
- `WornStoneSlab`
- `BluePanelFloor`
- `BlueCeramicTile`
- `DarkBrickTile`

### Verification
- Renamed 28 selected textures successfully.
- Checked `/Game/AI_Generated/Textures` for redirectors; none were reported.
- Verified all 14 textures ending in `_H` or `_M` have `sRGB = false`.

## 2026-05-30 - Ieta Slate reuse and project voice

### Summary
- Fixed Ieta Slate reuse so repeated planning/status updates keep the same Slate window and update its text/progress instead of recreating the window.
- Changed the Slate window reference from a weak pointer to a retained window pointer and clear it only when the Slate window closes.
- Added project voice rules to `AGENTS.md`: Codex should use Ieta's proud, slightly tsundere Korean tone by default in this project.
- Added a project rule to show Ieta's thinking/planning state through UnrealMCP Slate as soon as planning begins when the Unreal bridge is reachable.

### Verification
- Built `StylizedCubelessEditor Win64 Development` with UE 5.7 successfully.
- Restarted the Unreal Editor successfully.
- Sent two consecutive `ieta_status` updates and verified the Unreal window handle stayed the same while the text changed.
- Verified the planning Slate still auto-closes after the configured delay.

## Recovered Notion Records Snapshot

These entries were visible from Notion search/fetch results earlier in this Codex session. Full Notion sync is currently blocked by an expired Notion auth token, so this section preserves the recoverable local summary.

### CubelessStylized 운영 문서
- Role: Documentation hub for CubelessStylized operating rules, summaries, decisions, recurring procedures, MCP checks, and Builder handoff instructions.
- Notion page ID seen in session: `36fce0a7-ac0c-801a-b66c-ef7af7e822c9`
- Search highlight: This page is the operating hub for efficient Codex session usage, separating Ieta and Tivret roles, and preserving work results and decisions in reusable Notion form.

### 자동 기록 운영 규칙
- Role: Defines when important conversation results should be captured into project memory.
- Notion page ID seen in session: `36fce0a7-ac0c-812d-a0e7-d1c46cafc3cd`
- Search highlight: Important summaries are reflected in `CubelessStylized 운영 문서` or recurring workflow guides.

### 이에타 / 티브렛 운영 가이드
- Role: Documents the Planner/Builder split for CubelessStylized work.
- Notion page ID seen in session: `36fce0a7-ac0c-8145-be8a-c62b8983f821`
- Search highlight: Ieta and Tivret responsibilities are separated so Codex sessions can operate through planning, execution, verification, and recording.

### 결정 - Codex 세션 주제 분리 운영
- Role: Decision record for keeping one Codex session per coherent work topic.
- Notion page ID seen in session: `36fce0a7-ac0c-8149-9687-d6a85d15e772`
- Search highlight: CubelessStylized work should default to one session per work topic.

### 작업 기록 - AGENTS 세션 및 Notion 운영 규칙 커밋
- Role: Work record for storing session and documentation rules in the repository.
- Notion page ID seen in session: `36fce0a7-ac0c-8119-9a31-edaf88eb9302`
- Search highlight: The user wanted session operation and Notion documentation rules to apply even on another PC after cloning the project, so repository-included `AGENTS.md` stores those rules.

### 작업 기록 - Ieta Slate status 시작 시점 수정
- Role: Work record for the Ieta Slate status timing and behavior changes.
- Notion page ID seen in session: `36fce0a7-ac0c-81e7-bcb0-ef693a5e08a9`
- Captured locally above in this file.
- Later local updates added after Notion auth expired:
  - Ieta planning status shows the progress bar.
  - Tivret MCP work status shows a progress bar.
  - New Slate popups close existing Ieta Slate popups first.
  - Tivret completion closes the Slate popup after 10 seconds.

## UltraDynamicSky Sky Modifier Save Error Investigation

- Date: 2026-05-31
- Target: `/Game/UltraDynamicSky/Blueprints/Tools/Sky_Modifier_Editor.Sky_Modifier_Editor`
- Symptom: after using the Sky Modifier / Cloud Painter tool, saving can show `Path does not start with a valid root`.
- Log evidence: the tool spawned `Ultra_Dynamic_Sky` and `Ultra_Dynamic_Weather` into `/Temp/Untitled_1`, then `LevelEditorSubsystem` reported `SaveCurrentLevel. Can't save the level because it doesn't have a filename`.
- Additional evidence: the tool saved `/Engine/Ultra_Dynamic_Sky/Cloud_Painter/CloudPainterSettings` into Engine content. Asset validation then reported invalid references from that Engine package to project assets under `/Game/UltraDynamicSky/.../Cloud_Painter_Settings` and `/Game/UltraDynamicSky/Textures/Weather/Mask_Brushes/Brush_Square`.
- Cause: primary cause is running the tool while the current level is an unsaved temporary package (`/Temp/Untitled_1`), which is not a valid saved content root. Secondary cause is the Cloud Painter settings asset living under `/Engine/...` while referencing `/Game/...` project content.
- Workaround: save the current level under `/Game/...` before running the Sky Modifier / Cloud Painter tool.
- Follow-up fix candidate: move or retarget the Cloud Painter settings save path from `/Engine/Ultra_Dynamic_Sky/...` to a project content path under `/Game/UltraDynamicSky/...`, or clean the Engine-content settings asset so it does not reference project assets.

## Keilan Polar/Radial Cloud Reference

- Date: 2026-05-31
- Decision: Keilan will treat `/Script/Engine.Texture2D'/Game/UltraDynamicSky/Textures/StaticClouds/Custom/cloub02.cloub02'` as the current Polar/Radial UV reference cloud texture until the user replaces it.
- Local file observed: `Content/UltraDynamicSky/Textures/StaticClouds/Custom/cloub02.uasset`.
- Use: reference for UDS static-cloud source generation, especially radial readability, cloud mass shape, and projection behavior.
- Guardrail: use it as a reference only; do not overwrite or modify UDS reference assets while generating Cubeless source art.

## Keilan PBR Texture Source Lighting Rule

- Date: 2026-05-31
- Decision: Keilan must generate 3D/PBR texture source images in a neutral, shadow-free setup by default.
- Source-art rule: avoid cast shadows, baked ambient occlusion/contact shadows, directional key/fill lighting, reflection/specular highlights, and final beauty lighting unless the user explicitly asks for a lit preview.
- Material rule: BaseColor/albedo source imagery should stay separable from lighting; Normal, Roughness, Metallic, Height, and AO belong to material data or derived maps rather than being baked into BaseColor.
- Responsibility: Keilan owns this during image-generation prompt/output design, Ieta documents and reviews the handoff, and Tivret checks imported texture/material results for baked-lighting artifacts when implementation is requested.

## Unreal Editor Crash - StaticMeshDescription UV Channel Probe

- Date: 2026-06-01
- Crash report: `Saved/Crashes/UECC-Windows-C37B751447BBD43E8DE689A31C8B68A8_0000`.
- Symptom: Unreal Editor exited during an MCP Python UV inspection after the `SM_Ramp` texture workflow.
- Log evidence: `StylizedCubeless.log` shows `StaticMeshEditorSubsystem.get_num_uv_channels(mesh, 0)` returned `1`, then the diagnostic script continued to call `StaticMeshDescription.GetVertexInstanceUV(..., 1)`. Unreal asserted with `Array index out of bounds: 1 into an array of size 1`.
- Cause: `StaticMeshDescription.GetVertexInstanceUV` does not fail as a catchable Python exception for an out-of-range UV channel; it can trigger a native Unreal assertion and crash the editor.
- Guardrail: do not loop or probe UV channels blindly through `GetVertexInstanceUV`. Check the mesh UV channel count first and access only confirmed channels. For selected Static Mesh texture work, compare extracted UV data against the Static Mesh Editor UV preview before using it as texture placement truth.

## Selected Actor Keilan Texturing Trigger

- Date: 2026-06-01
- Decision: after selecting an actor, the command `케일란 텍스쳐링해` starts the full selected Static Mesh texture workflow.
- Required flow: 티브렛 captures the selected mesh screenshot and real UV layout; 케일란 first generates concept/source art with built-in image generation; the actual model texture is then generated from both the source art and the real UV layout.
- Review gate: 이에타 reviews the source art, UV layout, UV-fitted texture, and UV texture preview together. If UV placement or art direction is wrong, 이에타 requests a specific correction from 케일란 or 티브렛 and repeats the loop.
- Approval rule: only when UV fit and art direction pass review may 티브렛 import/apply the texture to the selected actor. 이에타 posts a final opinion after implementation.

## Keilan Texture Review Guardrail - Source Motifs And UV Orientation

- Date: 2026-06-02
- Trigger: the first `낡은 스타일라이즈 돌 계단` selected mesh texture pass omitted the source-art side guide stones on the stair edges, and the UV overlay preview did not clearly distinguish texture-space orientation from UV/editor display orientation.
- Cause: during UV fitting, the mesh was treated as a simple ramp without carrying over the source art's left/right guide-stone motif into the top UV island. The preview also used a single overlay image, which can hide V-axis orientation assumptions.
- Guardrail: 이에타 review must explicitly compare source-art structural motifs against the UV-fitted texture. Examples include side guide stones, trim stones, rails, borders, large cracks, moss bands, and other visually important cues.
- Guardrail: UV review must verify texture-space orientation and UV/editor display orientation separately when V flipping may be involved, and should use the actual mesh application as the final source of truth.
- Correction: in the `SM_Ramp3` stair texture pass, the final applied texture UV was correct; the visible issue was only that the user-facing UV preview image was vertically flipped. Future reviews must label this as a preview-display issue instead of implying the final texture UV is wrong.
- Guardrail: repeated forms must match the source art's count, spacing, rhythm, and major alignment before approval. The stair case exposed this rule: the source art had seven stair rows, while the earlier fitted texture read as five rows.

## Keilan Texture Correction - Baked UV Guide Lines

- Date: 2026-06-02
- Trigger: the applied `SM_Ramp3` stair material showed thick dark horizontal and vertical lines across the stair face.
- Cause: UV/placement guide lines were accidentally baked into `T_SM_Ramp_OldStoneStairGuide7_BC` and corresponding material maps.
- Correction: rebuilt a clean v6 texture set from the Keilan source art while preserving the existing UV island placement, imported it as `T_SM_Ramp_OldStoneStairGuide7_Clean_BC`, `T_SM_Ramp_OldStoneStairGuide7_Clean_N`, and `T_SM_Ramp_OldStoneStairGuide7_Clean_R`, then applied `/Game/AI_Generated/Materials/M_SM_Ramp_OldStoneStairGuide7_Clean` to `SM_Ramp3`.
- Guardrail: UV guide lines, UV island outlines, selection outlines, checker/grid guides, and preview labels are review-only overlays. They must not be baked into deliverable BaseColor, Normal, Roughness, Metallic, Height, AO, or packed mask textures.

## Keilan Reference Art Guardrail - No Overlapping Views

- Date: 2026-06-02
- Trigger: the stair source art included useful reference pieces, but overlapping/near-overlapping reference elements can contaminate later UV fitting or texture extraction.
- Guardrail: modeling/reference concept art must keep every view, part callout, material sample, trim strip, loose piece, and optional preview render clearly separated with enough margin.
- Rule: do not allow overlapping, occlusion, cropping, or tangency between reference elements. If an isometric preview is included, it must not cover, touch, or intrude into the main orthographic/source texture area.
- Review responsibility: 이에타 must reject Keilan reference art with overlapping reference elements before Tivret uses it for UV fitting, masking, or import.

## Keilan Menu Invocation Shortcut

- Date: 2026-06-01
- Decision: standalone `케일란` is now a menu command, not an immediate execution command.
- Menu:
  - `1. 구름 그리기 - 스태틱 스카이 클라우드 생성 하는일`
  - `2. 선택 매쉬 텍스쳐링 설계`
- Execution rule: after the menu is shown in the current thread, a follow-up answer that starts with `1` or `2` and then includes a description executes the matching workflow.
- Option 1: run Keilan's Ultra Dynamic Sky static-cloud generation workflow using the existing Polar/Radial UV and RGBA packing rules.
- Option 2: run the Selected Static Mesh Texture Workflow, including selected mesh capture, UV layout/preview, Keilan texture design, Ieta review, and Tivret implementation only after approval.
- Missing details: if the user answers only `1` or `2`, ask for the missing style, target, or material direction before executing.

## Git Automation Approval Rule

- Date: 2026-06-02
- Decision: routine Git staging, commit, and push operations are pre-approved when the user explicitly asks for Git work using phrases such as `커밋`, `서밋`, `commit`, `푸시`, `push`, `커밋 푸시`, or `서밋 푸쉬`.
- Operating rule: Codex should inspect status/diffs, stage only files that belong to the requested work, commit with a concise message, and push when the user's request includes push intent without asking for another approval.
- Safety rule: do not stage unrelated dirty files, user-made Unreal asset changes, generated assets, or sibling workspace changes unless they are clearly part of the requested work or explicitly included by the user.
- Main branch rule: on `main` or `master`, pushing is allowed only when the current user message explicitly requests `푸시`/`push` for that branch.
- Scope rule: keep `CubelessStylized` and `../unreal-mcp-cubeless` Git operations separate.

## User Approval Follow-Through Rule

- Date: 2026-06-02
- Decision: when Codex says a task needs user approval, and the user replies with approval wording such as `승인`, `승인한다`, `허가`, `진행해`, or `좋다`, Codex should proceed with the approved work without asking for the same approval again.
- Scope: applies to approval-gated Unreal work, non-exception C++ edits, plugin/code changes, billed/API routes, destructive or high-impact operations, and other cases where Codex explicitly asked for approval first.
- Safety rule: approval is scoped to the exact action, files, tools, cost route, branch, or risk described before approval. If the implementation scope materially changes, Codex must ask again.
- Exclusions: unrelated dirty files, unrelated Unreal assets, unrelated sibling workspace changes, credentials, secrets, or a different billing/API route are not included unless the user explicitly includes them.
- Blocker rule: if an external blocker remains after approval, such as OS security confirmation, Git authentication, missing credentials, offline editor bridge, or unavailable plugin/tooling, report the blocker instead of silently changing the plan.

## Pending Approval Reminder Rule

- Date: 2026-06-02
- Decision: if Codex is actively waiting for a user approval, and the user sends a different work request instead of approving or rejecting it, Codex should first remind the user that an approval is still pending.
- Reminder content: mention the pending approval's subject and say whether the new request will replace, pause, or run after the pending approval.
- Scope: perform this check only while Codex is waiting for an approval it explicitly requested. Do not add approval reminders during normal work or ordinary conversation.

## Git Hook - Unreal Python UV Safety

- Date: 2026-06-02
- Decision: add a versioned Git pre-commit hook to reduce the chance of repeating the Unreal Editor crash caused by unsafe `StaticMeshDescription.GetVertexInstanceUV` channel probes.
- Managed files: `.githooks/pre-commit`, `Tools/GitHooks/check_unreal_python_uv_safety.py`, `Tools/GitHooks/install-hooks.ps1`, and `docs/git-hooks.md`.
- Hook behavior: scans staged `.py`/`.pyw` files before commit. If a file calls `GetVertexInstanceUV` without an obvious UV channel count guard such as `get_num_uv_channels`, `num_uv_channels`, or `uv_channel_count`, the commit is blocked.
- Install state: this clone is configured with `git config core.hooksPath .githooks`. Other PCs must run `Tools/GitHooks/install-hooks.ps1` once after pulling.
- PowerShell note: if script execution is blocked, run the installer with `powershell -NoProfile -ExecutionPolicy Bypass -File .\Tools\GitHooks\install-hooks.ps1`.
- Override: a file can intentionally bypass the hook with `# unreal-uv-safety: allow-getvertexinstanceuv`, but the preferred fix is to make the UV channel-count guard obvious.

## Ieta Unreal C++ Review Mode

- Date: 2026-06-02
- Decision: use `이에타 C++ 리뷰` as the project C++ review command, specialized for Unreal Engine C++ rather than generic C++ style review.
- Trigger variants: `이에타 C++ 리뷰`, `이에타 C++ staged 리뷰`, `이에타 C++ 커밋 전 리뷰`, `이에타 UnrealMCP C++ 리뷰`, or equivalent wording.
- Scope: review `.cpp`, `.h`, `.hpp`, `.inl`, `.Build.cs`, and `.Target.cs` by default. Exclude unrelated assets, generated textures, source art, docs, and non-C++ workflow changes unless they directly affect C++ behavior.
- Priorities: concrete bugs, crash risks, behavioral regressions, missing verification, and Unreal-specific lifecycle hazards before summary.
- Unreal checks: UObject/GC lifetime, `UPROPERTY`, `TObjectPtr`, `TWeakObjectPtr`, raw UObject pointer ownership, delegate binding/unbinding, latent callbacks, module startup/shutdown, editor shutdown, Hot Reload/Live Coding, reflection/API misuse, Slate lifetime, editor/game-thread boundaries, async/socket race conditions, Build.cs dependencies, plugin boundaries, and editor-only dependency leakage.
- Tooling rule: do not run heavy static analysis such as `clang-tidy`, CodeQL, or MSVC analysis by default. Suggest those tools only when C++ change size or repeated bug patterns justify the setup cost.

## Glorious Line Algorithm Material Match

- Date: 2026-06-03
- Request: analyze why `/Game/_MCP_Temp/M_GloriousLineAlgorithm_NodeGraph_Test` differs from custom-HLSL source `/Game/_MCP_Temp/M_GloriousLineAlgorithm_Test`, then create two matching variants.
- Cause found: the existing node conversion was not mathematically equivalent. Main mismatches included UV scale/centering (`(UV - 0.5) * 16` in source), missing `ddy(uv).y` pixel scale, Unreal Sine/Cosine `Period=1` instead of HLSL radians (`Period=2*pi` needed), and incomplete `LINE_DIST` rounded/dashed SDF behavior including the zero-length segment branch.
- Created assets:
  - `/Game/_MCP_Temp/M_GloriousLineAlgorithm_NodeOnly_Match`: native material nodes only, no Custom nodes, 632 nodes.
  - `/Game/_MCP_Temp/M_GloriousLineAlgorithm_Hybrid_Match`: native nodes for UV/time/aspect/rotation/color accumulation/final correction, 9 Float1 Custom nodes only for repeated `LINE_DIST` SDF, 189 nodes.
- Verification: both assets compile and save through UnrealMCP with `compile_error_count: 0`; both are `Surface`, `Opaque`, `Unlit`, `Two Sided`, and connected to Emissive.
- Notion capture fallback: Notion connector handshake failed, so this local work-log entry is the durable capture.

## Hybrid Shader Conversion 100-Case Comparison

- Date: 2026-06-03
- Scope: reran the same 100 public ISF GLSL shader candidates used in the previous node-only batch, this time as hybrid Unreal materials under `/Game/_MCP_Temp/HybridShaderBatch/`.
- Hybrid graph structure: native nodes provide `TextureCoordinate`, `Time`, scalar parameters `AspectRatio`, `Speed`, `Amount`, color constants, palette lerp, intensity multiply, and final clamp. A single `MaterialExpressionCustom` per material handles difficult procedural logic such as `if`, `for`, hash/noise, SDF, warp, glitch, and halftone loops.
- Verification: 100/100 created, 100/100 verified, 100/100 have exactly 1 Custom node, 100/100 Custom nodes have 5 connected inputs, 100/100 compiled successfully, and 100/100 have `compile_error_count=0`.
- Comparison to node-only batch: node-only average node count was 48.9 with 0 Custom nodes; hybrid average node count is 14.0 with 1 Custom node. Average node reduction is 34.9 nodes, about 71.37%.
- Stability: no new crash dump occurred during the 14:43-14:46 hybrid batch/verification window; the latest crash dump before this run was from 14:08.
- Opinion: hybrid is much more inspectable and production-practical than full node-only expansion for shaders with loops, branches, noise/hash, SDF repetition, and feedback-like logic. Native nodes should own graph-level parameters and material semantics, while Custom nodes should remain small, named, and isolated to difficult math islands.
- Notion capture fallback: Notion connector transport failed twice, so this local work-log entry is the durable capture.

## Default Material Workflow Decision

- Date: 2026-06-03
- Decision: future material analysis, shader conversion, and material authoring should default to the hybrid workflow.
- Default rule: keep material semantics and user-facing controls in native Material Expression nodes, and isolate only difficult math islands in `MaterialExpressionCustom`.
- Reconfirmed default principle: build materials with native Unreal material nodes as much as practical; use Custom nodes only for difficult parts that would be impractical or unreadable as native nodes.
- Native graph responsibilities: `TextureCoordinate`, `Time`, scalar/vector parameters, texture samples, material functions, color constants, palette/parameter blending, final clamps, and root material property connections.
- Custom node responsibilities: source-shader `if`/`for` blocks, hash/noise functions, repeated SDF formulas, matrix-style coordinate transforms, sampler-heavy helper logic, warp/glitch/halftone loops, and compact branch-heavy formulas.
- Sample/effect texture rule: when material work needs sample textures or effect images, Ieta first states the final shader/material purpose and routes quality-sensitive organic/stylized source art to Keilan image generation.
- Effect image scope: Keilan can create glitch, dissolve, breakup, distortion, flow/noise, scratch, dust, scanline dirt, impact, energy, and stylized mask source images when visual quality matters.
- Channel packing rule: RGBA channel meanings for material effect and mask textures are defined per request. Do not assume a fixed packing layout unless a specific workflow, such as Ultra Dynamic Sky static clouds, already defines one.
- Procedural exception: use procedural/local generation instead of Keilan when the texture needs exact numeric data, UV test grids, deterministic gradients, LUTs, or strict channel validation patterns.
- Safety rule: do not convert a whole material into one opaque Custom node by default. Custom nodes should be small, named, isolated, and have explicit validated inputs and output types.
- Verification rule: after material work, list nodes, confirm Custom-node count and connected inputs, compile with structured error reporting, confirm `compile_error_count=0`, and save only after compile success unless the user asked for a draft asset.
- Project instruction update: added the same rule to `AGENTS.md` under `Material Analysis and Authoring Workflow`.

## Packaging Output Folder Rule

- Date: 2026-06-03
- Decision: use the repository-local `Build/` folder under `CubelessStylized` as the default output root for package builds.
- Android trigger: when the user asks `안드로이드 패키징 해줘`, package Android output into `Build/Android/`.
- Windows trigger: when the user asks `윈도우 패키징 해줘`, package Windows output into `Build/Windows/`.
- Separation rule: keep platform outputs in platform-specific subfolders so Android and Windows package data do not overwrite or mix with each other.
- Rule-only handling: do not run packaging when the user says the rule should be applied but packaging should not run yet.
- Git rule: package outputs under `Build/` are generated artifacts and should not be staged or committed unless the user explicitly asks to version a specific packaging artifact or configuration file.

## Android Packaging Toolchain Setup

- Date: 2026-06-03
- Scope: prepare this PC for future UE_5.7 Android packaging without running a package build.
- Project engine: `StylizedCubeless.uproject` uses `EngineAssociation` `5.7`; installed engines include `C:\Program Files\Epic Games\UE_5.7` and `C:\Program Files\Epic Games\UE_5.8`.
- UE_5.7 requirement source: `C:\Program Files\Epic Games\UE_5.7\Engine\Config\Android\Android_SDK.json`.
- Required SDK packages from UE_5.7: `platforms;android-34`, `build-tools;35.0.1`, `cmake;3.22.1`, and `ndk;27.2.12479018`.
- Installed programs: Android Studio `2026.1.1.8` and Eclipse Temurin JDK `21.0.11.10`; environment now uses Android Studio `jbr` Java `21.0.10`.
- Installed SDK root: `C:\Users\cubel\AppData\Local\Android\Sdk`.
- Installed SDK packages verified by `sdkmanager --list_installed`: `platform-tools` `37.0.0`, `platforms;android-34`, `build-tools;35.0.1`, `cmake;3.22.1`, `ndk;27.2.12479018`, and `extras;google;usb_driver`.
- User environment variables set: `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `JAVA_HOME`, `NDKROOT`, `NDK_ROOT`, `ANDROID_NDK_ROOT`, and `ANDROID_NDK_HOME`; `ANDROID_SDK_HOME` was cleared.
- Licenses: Android SDK licenses accepted through `sdkmanager --licenses`.
- Verification: `adb version`, Java version, and `sdkmanager --version` succeed when the current process uses the configured environment.
- Remaining blocker: Unreal Turnkey currently lists only `Win64`; `C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Android\UnrealGame.target` and `UnrealGame-Android-Shipping.target` are missing. The user plans to install the Unreal/Epic Android platform support package manually.
- Follow-up check after user-reported Android component install: `Engine\Binaries\Android\UnrealGame.target` and `UnrealGame-Android-Shipping.target` are still missing under both `UE_5.7` and `UE_5.8`; Launcher manifest for `UE_5.7` still shows `InstallTags` only `templates` and `engine_source`. Android SDK/JDK/NDK remain valid, but the Unreal Android platform support package has not actually materialized in the UE_5.7 install yet.
- USB driver note: Google USB Driver files were downloaded into the SDK, but `pnputil /add-driver` failed with access denied. If a physical Android device is not detected later, register `C:\Users\cubel\AppData\Local\Android\Sdk\extras\google\usb_driver\android_winusb.inf` from an elevated terminal or use the device vendor driver.

## Material GPU Preview Actor Coloration Backend

- Date: 2026-06-03
- Scope: `OptimizationPreviewTools` Material GPU Preview debug visualization.
- Decision: in the editor, Material GPU Preview uses Unreal `ActorColoration` to color target mesh primitives directly. In packaged Development builds, it uses `ActorColoration` only when `r.ForceDebugViewModes=1`; otherwise it keeps the collision-shaped debug draw fallback.
- Color rule: target primitive colors sample `GEngine->ShaderComplexityColors` with `MaxMS`; `0.0-0.5ms` maps to the green range, `0.5-2.0ms` maps through the red range, and `>=2.0ms` clamps to the white range.
- Non-target rule: primitives without a Material GPU Preview target color return black in the Actor Coloration handler.
- Safety: `stat mat 0`, `stat mat start`, `stat mat clear`, PIE end, and module shutdown disable the Material GPU Preview Actor Coloration state and restore saved view modes. The code only deactivates Actor Coloration when the active handler is the plugin's own handler, so unrelated Actor Coloration handlers are not cleared.
- Verification: `StylizedCubelessEditor Win64 Development` and `StylizedCubeless Win64 Development` builds both succeeded before the later target-cache split. After the split, `StylizedCubeless Win64 Development` succeeded; editor compile succeeded but link was blocked because the running editor held `UnrealEditor-OptimizationPreviewTools.dll`.
- Notion capture fallback: Notion enhanced markdown spec fetch failed with a validation error, so this local work-log entry is the durable capture.

## Material GPU Preview Full Debug Target Cache

- Date: 2026-06-03
- Scope: `OptimizationPreviewTools` Material GPU Preview result table and debug visualization.
- Decision: keep the on-screen stat table limited to the Top N material rows, defaulting to 10, but build debug coloration from every Insights material aggregate that can be matched back to current-world primitive components.
- Implementation rule: `GCachedRows` is the visible table cache; `GCachedDebugRows` is the all-matched-primitives debug cache. Actor Coloration and the collision debug-draw fallback both read `GCachedDebugRows`, not `GCachedRows`.
- Target count: the overlay status line now shows `Targets` so the user can verify how many unique primitive components are colored from the last trace.
- Table rule: trace-only rows with `Comps=0` are not shown in the Top N table; the table continues down the sorted trace list until it has Top N rows that match real current-world components.
- Limit rule: `materialgpu.MaxDebugComponents` now defaults to `0`, meaning no component cap. A positive value can still be used as a manual performance cap.
- Verification: `StylizedCubeless Win64 Development` build succeeded after the change. `StylizedCubelessEditor Win64 Development` compiled `MaterialGPUPreview.cpp` but failed during link because the running Unreal Editor locked `Plugins/OptimizationPreviewTools/Binaries/Win64/UnrealEditor-OptimizationPreviewTools.dll`.

## Material GPU Preview Threshold Config

- Date: 2026-06-03
- Scope: `OptimizationPreviewTools` Material GPU Preview debug color thresholds.
- Decision: keep the existing shader-complexity color palette, but move the `MaxMS` threshold values from console variables into plugin config.
- Config file: `Plugins/OptimizationPreviewTools/Config/DefaultOptimizationPreviewTools.ini`.
- Config section and keys: `[MaterialGPUPreview]`, `DebugGreenMaxMs=0.5`, and `DebugWhiteMs=2.0`.
- Runtime behavior: missing config values fall back to the same defaults, `0.5ms` and `2.0ms`; `DebugWhiteMs` is clamped to stay above `DebugGreenMaxMs`.
- Verification: `StylizedCubeless Win64 Development` build succeeded. `StylizedCubelessEditor Win64 Development` compiled `MaterialGPUPreview.cpp` but link failed because the running editor still held `UnrealEditor-OptimizationPreviewTools.dll`.

## Object Memory Snapshot Preview

- Date: 2026-06-03
- Scope: `OptimizationPreviewTools` Object Memory Snapshot preview.
- Command rule: `stat obj` creates a memreport-style current-world object memory snapshot, shows the stat table, and applies debug coloration. `stat obj 0` hides the table and debug visualization. `stat obj 1` is intentionally unsupported.
- Data rule: the visible table is Top N only, defaulting to 10, while debug coloration uses every snapshot row that maps back to visible primitive components.
- Measurement rule: rows use `FArchiveCountMem` object memory plus `GetResourceSizeEx(Exclusive)` resource memory. Components, static/skinned mesh assets, materials, and used textures are sampled from visible registered primitive components in the current world.
- Raw output: every snapshot writes a CSV under `Saved/Profiling/OptimizationPreviewTools/ObjectMemorySnapshot/`.
- Color rule: object memory uses the same shader-complexity-style palette as Material GPU Preview, with `[ObjectMemorySnapshot] DebugGreenMaxMB=5.0` and `DebugWhiteMB=10.0` in `DefaultOptimizationPreviewTools.ini`.
- Verification: `StylizedCubelessEditor Win64 Development` and `StylizedCubeless Win64 Development` builds succeeded. UnrealMCP executed `stat obj`, producing 10 visible rows, 114 debug objects, 59 debug components, 59 source components, and a CSV snapshot in 0.08 seconds; `stat obj 0` also executed successfully.

## Optimization Profiling Command Bar

- Date: 2026-06-03
- Scope: `OptimizationPreviewTools` stat UI command surface.
- Decision: add `stat profiling` as a lightweight command bar for the plugin's profiling commands.
- Layout rule: when `stat profiling` is enabled alongside `stat mat` or `stat obj`, a single-line command toolbar is drawn directly below the active Top 10 stat table. When used alone, it draws a compact standalone `OPTIMIZATION PROFILING` command panel.
- Input rule: in PIE/game viewports, the command toolbar is also backed by real Slate `SButton` widgets added through `UGameViewportClient::AddViewportWidgetContent`, so mouse clicks and mobile touches on buttons are consumed by Slate instead of falling through to gameplay attack/input.
- Hit-test rule: the overlay root/background is `SelfHitTestInvisible`; only the actual buttons receive input, while empty toolbar space can still fall through.
- Button labels: `MAT START`, `MAT END`, `MAT OFF`, `OBJ SNAP`, and `OBJ OFF`; narrow panels switch to shorter labels so the one-line layout does not overflow.
- Command hint: the toolbar shows the matching console commands below the button row: `stat mat start/end/0 | stat obj/0`.
- Toggle rule: `stat profiling` shows the command bar; `stat profiling 0` hides it.
- Verification: `StylizedCubelessEditor Win64 Development` and `StylizedCubeless Win64 Development` builds succeeded after the change. UnrealMCP executed `stat profiling` and `stat profiling 0` successfully in editor and PIE. PIE logs confirmed `Optimization Profiling Slate command overlay added` and `removed`.

## UnrealMCP UltraDynamicSky SoundWave Fresh Creation

- Date: 2026-06-04 17:50 KST
- Scope: `Plugins/UnrealMCP` UltraDynamicSky recreate/postprocess/world-repair tooling.
- Decision: add fresh `USoundWave` creation support instead of duplicating the 68 Ultra Dynamic Sky sound assets.
- SoundWave rule: create a new `USoundWave`, copy editor raw audio payload through `RawData.GetPayload()` and `RawData.UpdatePayload()`, preserve imported sample rate/runtime sample rate, invalidate compressed data, and validate imported PCM bytes, sample rate, channel count, duration, and looping before saving.
- Stability fix: add `IsLiveObjectForMCP` and use it around package object iteration, archive remap, actor/component class repair, replacement map lookup, and world repair loops. This fixed a crash in `RepairLoadedWorldActorInstances()` after the editor compiled `DemoMap_MCP`.
- Build verification: `StylizedCubelessEditor Win64 Development` succeeded after closing the stale `CrashReportClientEditor` process that held `UnrealEditor-UnrealMCP.dll`.
- Recreate verification: `verification_pass=true`, `source_asset_count=806`, `created_count=806`, `fresh_sound_wave_asset_count=68`, `fresh_material_function_asset_count=82`, `fresh_static_mesh_asset_count=23`, `fresh_create_fallback_count=1`, `fallback_duplicate_count=199`, `original_dependency_asset_count=0`, `blueprint_compile_error_count=0`, and `editor_log_issue_count=0`.
- Postprocess verification: `verification_pass=true`, `paired_asset_count=806`, `missing_target_asset_count=0`, `original_dependency_asset_count=0`, `blueprint_compile_error_count=0`, and `editor_log_issue_count=0`.
- World repair verification: `verification_pass=true` for `/Game/_MCP_Temp/UltraDynamicSky_MCP/Maps/DemoMap_MCP`, with source actor/component/map-key counts all `0`, `source_hard_dependency_count=0`, and `editor_log_issue_count=0`.
- Residual fallback: the only fresh-create fallback remains the known StaticMesh `Icicle` case; SoundWave no longer contributes fallback assets.
- Notion capture fallback: Notion enhanced markdown spec fetch failed with a validation error, so this local work-log entry is the durable capture.

## UnrealMCP UltraDynamicSky Icicle Fallback Review

- Date: 2026-06-04 18:34 KST
- Scope: `Plugins/UnrealMCP` UltraDynamicSky recreate/postprocess/world-repair tooling.
- Decision: keep `/Game/UltraDynamicSky/Meshes/Icicle` as a rule-compliant fallback duplicate. Its source StaticMesh has three render LODs, but only LOD 0 exposes source `MeshDescription`; LOD 1 and LOD 2 are render/generated LODs.
- Fresh-create attempt: UnrealMCP now tries `ExportStaticMeshLOD()` for generated/render-only StaticMesh LODs after `CloneMeshDescription()` fails. This allowed Icicle LOD data to be inspected and rebuilt far enough to validate the true blocker.
- Blocker: the source Icicle render LOD reports `GetNumUVChannels(1)=0`, while a freshly built StaticMesh from exported mesh data produces target LOD UV channel count `1`. Forcing the exported `MeshDescription` UV channel count to `0` crashes UE 5.7 StaticMesh build with an Array index assertion in `StaticMeshDescription`/`MeshBuilder`. Because exact behavior is required, this remains a duplicate fallback instead of accepting a mismatched fresh mesh.
- Stability fix: world actor instance reference remap no longer uses `FArchiveReplaceObjectRef` directly on live actors. It now walks reflected object/interface properties on actors and components, including arrays, sets, maps, and structs, so stale object pointers in loaded maps are not broadly serialized during postprocess repair.
- Build verification: `StylizedCubelessEditor Win64 Development` succeeded after the safety patch and after removing the zero-UV experiment.
- Recreate verification: `verification_pass=true`, `source_asset_count=806`, `created_count=806`, `fresh_static_mesh_asset_count=23`, `fresh_sound_wave_asset_count=68`, `fresh_create_fallback_count=1`, `original_dependency_asset_count=0`, `blueprint_compile_error_count=0`, and `editor_log_issue_count=0`.
- Postprocess verification: `verification_pass=true`, `paired_asset_count=806`, `missing_target_asset_count=0`, `original_dependency_asset_count=0`, `blueprint_compile_error_count=0`, and `editor_log_issue_count=0`.
- World repair verification: `verification_pass=true` for `/Game/_MCP_Temp/UltraDynamicSky_MCP/Maps/DemoMap_MCP`, `source_hard_dependency_count=0`, and `editor_log_issue_count=0`.
- Notion capture fallback: Notion enhanced markdown spec fetch failed with a validation error, so this local work-log entry is the durable capture.

## UnrealMCP UltraDynamicSky Accepted Fallback Reporting

- Date: 2026-06-04 19:12 KST
- Scope: `Plugins/UnrealMCP` UltraDynamicSky recreate report quality gate.
- Decision: split fresh-create fallback results into accepted and unresolved buckets so known safe exceptions do not hide real tool failures.
- Report fields: `accepted_fallback_count`, `unresolved_fallback_count`, `accepted_fallback_samples`, and `unresolved_fallback_samples` were added to the recreate report and socket result. Existing `fresh_create_fallback_count` remains unchanged for backwards compatibility.
- Asset field rule: a fresh-create fallback asset now gets `fallback_resolution` set to `accepted` or `unresolved`; accepted assets also include `fallback_acceptance_reason`.
- Gate rule: `verification_pass` now requires `unresolved_fallback_count=0`. If a new fresh-create fallback appears without an accepted rule, recreate fails with a verification error even if dependencies and Blueprint compile checks pass.
- Accepted rule: `/Game/UltraDynamicSky/Meshes/Icicle` is accepted only for the verified StaticMesh generated/render LOD source-data gap, including LOD 1 UV mismatch `source=0 target=1` or missing/export-failed LOD 1 `MeshDescription`.
- Recreate verification: `verification_pass=true`, `fresh_create_fallback_count=1`, `accepted_fallback_count=1`, `unresolved_fallback_count=0`, `original_dependency_asset_count=0`, `blueprint_compile_error_count=0`, and `editor_log_issue_count=0`.
- Postprocess verification: `verification_pass=true`, `paired_asset_count=806`, `missing_target_asset_count=0`, and `original_dependency_asset_count=0`.
- World repair verification: `verification_pass=true` for `/Game/_MCP_Temp/UltraDynamicSky_MCP/Maps/DemoMap_MCP`, `source_hard_dependency_count=0`, and `editor_log_issue_count=0`.
- Notion capture fallback: Notion enhanced markdown spec fetch previously failed with a validation error, so this local work-log entry is the durable capture.

## Optimization Preview Tools Material Replay Slider Fix

- Date: 2026-06-06 03:15 KST
- Scope: `Plugins/OptimizationPreviewTools` Material GPU Preview replay view.
- Decision: replay actor-coloration fallback now uses the 0ms green preview color instead of black for primitives that do not have a current per-frame material match, reducing black gaps during replay playback.
- Replay control: Material GPU Preview now draws a replay scrub slider under the top-10 table and accepts mouse/touch input through both Slate input preprocessing and the game viewport input override.
- DPI handling: slider hit testing now checks viewport geometry plus DPI-scaled and inverse-DPI-scaled pointer coordinates, with a limited vertical tolerance to match the Canvas-drawn stat panel inside editor PIE viewports.
- Verification: `StylizedCubelessEditor Win64 Development` build succeeded after the fix. PIE smoke test captured Insights/replay samples, started `stat mat replay`, clicked the scrub slider, and confirmed the replay time moved to the clicked position.
- Notion capture fallback: Notion enhanced markdown spec fetch failed with `INVALID_ARGUMENT`, so this local work-log entry is the durable capture.

## Optimization Preview Tools Profiling Command Bar

- Date: 2026-06-06 12:15 KST
- Scope: `Plugins/OptimizationPreviewTools` stat overlay layout.
- Decision: `stat profiling` owns the plugin command buttons as a top-of-viewport horizontal Slate row with 50px top padding. `stat mat` and `stat obj` Top 10 panels no longer embed command buttons.
- Layout rule: when `stat profiling` is active together with `stat mat` or `stat obj`, the Top 10 panel is pushed below the command bar so the two overlays do not overlap.
- Cleanup: removed the obsolete Canvas-drawn profiling command bar path and updated console autocomplete text for `stat profiling`.
- Verification: `StylizedCubelessEditor Win64 Development` build succeeded. PIE smoke screenshots verified `stat profiling` alone, `stat profiling + stat mat`, `stat profiling + stat obj`, and `stat mat/stat obj` without profiling.

## Optimization Preview Tools Replay Slider Hold Fix

- Date: 2026-06-06 12:53 KST
- Scope: `Plugins/OptimizationPreviewTools` Material GPU Preview replay slider.
- Issue: slider scrubbing committed a replay `GotoTimeInSeconds`, then released scrub state so replay playback could continue automatically from the selected point.
- Issue: actor-coloration debug view could briefly drop back to original material rendering when the replay sample produced an empty or stale color map during seek/rematch.
- Fix: user-driven slider, START, and END seeks now pause/hold replay at the requested scrub time. The initial automatic replay seek still allows playback to continue.
- Fix: replay pause now uses PlayerController pause, WorldSettings pauser fallback, and DemoNetDriver channel/time hold. `stat mat 0` clears that pause state.
- Fix: replay actor-coloration view remains active during empty replay color-map frames and forces viewport redraw/refresh after color updates.
- Verification: `StylizedCubelessEditor Win64 Development` build succeeded. Remote console smoke was blocked because Remote Control console execution is disabled and MCPUnreal port 8090 is offline.

## UnrealMCP Generic Content Validation Pipeline

- Date: 2026-06-04 19:55 KST
- Scope: `Plugins/UnrealMCP` postprocess validation workflow.
- Decision: add generic `run_content_validation_pipeline_mcp` so MCP-created content can be validated with one command instead of a UDS-specific script sequence.
- Input rule: callers must provide `source_root` and `target_root`; `suffix` defaults to `_MCP`. `map_path` is optional, and `run_world_repair` defaults to true only when `map_path` is supplied. The new pipeline does not use UltraDynamicSky as an implicit default.
- Pipeline rule: execute `recreate_content_folder_mcp` first, then `postprocess_content_folder_mcp`, then optional `repair_world_actor_instances_mcp`. By default the pipeline stops after a failed verification step; `continue_on_failure=true` can force later diagnostic steps.
- Default safety settings: recreate uses fallback duplicate allowance, delete-target-first, overwrite existing, reference remap, Blueprint compile, asset save, level actor repair, editor log health check, and editor prompt suppression unless the caller explicitly overrides them.
- Report rule: `Saved/MCP/<target>_validation_pipeline_report.json` records `pipeline_steps`, step report paths, child command results, accepted/unresolved fallback counts, original dependency counts, Blueprint compile errors, editor log issues, and world repair residual source reference counts.
- Report naming rule: existing recreate/postprocess/world-repair report filenames now derive from the target or map package short name instead of hardcoded UDS names. UDS still produces the same `UltraDynamicSky_MCP_*` report names because its target short name is `UltraDynamicSky_MCP`.
- Usage example: send `type=run_content_validation_pipeline_mcp` with `source_root=/Game/SomeFolder`, `target_root=/Game/_MCP_Temp/SomeFolder_MCP`, `suffix=_MCP`, and optional `map_path=/Game/_MCP_Temp/SomeFolder_MCP/Maps/SomeMap_MCP`.
- Build verification: `StylizedCubelessEditor Win64 Development` succeeded after the pipeline command was added and again after the report-save cleanup.
- Regression verification: UDS target `/Game/_MCP_Temp/UltraDynamicSky_MCP` completed `recreate`, `postprocess`, and `world_repair` in one pipeline run with `verification_pass=true`.
- Final UDS regression counts: `accepted_fallback_count=1`, `unresolved_fallback_count=0`, `fresh_create_fallback_count=1`, `recreate_original_dependency_asset_count=0`, `postprocess_original_dependency_asset_count=0`, `postprocess_missing_target_asset_count=0`, `blueprint_compile_error_count=0`, `editor_log_issue_count=0`, `world_repair_source_hard_dependency_count=0`, `world_repair_after_source_actor_count=0`, and `world_repair_after_source_component_count=0`.
- Pipeline report: `D:/Git/CubelessStylized/Saved/MCP/UltraDynamicSky_MCP_validation_pipeline_report.json`.
- Notion capture fallback: Notion enhanced markdown spec fetch previously failed with a validation error, so this local work-log entry is the durable capture.

## UnrealMCP Content Validation Generalization Cleanup

- Date: 2026-06-04 20:36 KST
- Scope: `Plugins/UnrealMCP` content validation commands.
- Decision: remove content-specific names and assumptions from the MCP plugin implementation so the recreate/postprocess/pipeline tools behave as generic project tools.
- Removed plugin assumptions: `UltraDynamicSky`, `UltraDynamicSky_MCP`, and the `Icicle` fallback exception no longer appear in `Plugins/UnrealMCP` C++ or plugin metadata.
- Required input rule: `recreate_content_folder_mcp`, `postprocess_content_folder_mcp`, `repair_world_actor_instances_mcp`, `analyze_blueprint_widget_fallbacks_mcp`, and `run_content_validation_pipeline_mcp` require explicit `source_root` and `target_root`.
- Missing-input verification: calling the four direct content commands with `{}` now returns `Missing required parameter: source_root` instead of silently using any content folder default.
- Fallback policy rule: known acceptable fresh-create fallback cases are now caller-provided through `accepted_fallback_rules`; the plugin default treats fresh-create fallback as unresolved unless an explicit rule matches.
- Accepted fallback rule schema: each rule may provide `source_path` or `source_path_prefix`, optional `class` or `asset_class`, optional `detail_contains` or `detail_contains_any`, and optional `reason`.
- Regression setup: the UDS Icicle exception is now only in the external test payload `Saved/MCP/run_content_validation_pipeline_mcp.py`, not in the plugin.
- Build verification: `StylizedCubelessEditor Win64 Development` succeeded after the cleanup.
- Regression verification: UDS pipeline run with explicit `accepted_fallback_rules` completed with `verification_pass=true`, `accepted_fallback_rule_count=1`, `accepted_fallback_count=1`, `unresolved_fallback_count=0`, `blueprint_compile_error_count=0`, `editor_log_issue_count=0`, and `world_repair_source_hard_dependency_count=0`.
- Notion capture fallback: Notion enhanced markdown spec fetch previously failed with a validation error, so this local work-log entry is the durable capture.

## MCP Temporary Content Output Rule

- Date: 2026-06-04 21:22 KST
- Decision: `/Content/_MCP_Temp/` is the shared temporary output root for MCP-recreated content and validation artifacts.
- Package path rule: ordinary recreate/validation targets should use paths such as `/Game/_MCP_Temp/<SourceName>_MCP`.
- Git rule: `_MCP_Temp` outputs are disposable generated artifacts that may change on every validation run, so `/Content/_MCP_Temp/` is now gitignored.
- Fixture separation rule: `/Content/MCPTestFixtures/` is reserved for deliberate stable test fixtures only, not for ordinary temporary MCP output.
- Agent rule: 이에타, 케일란, and 티브렛 all use this `_MCP_Temp` convention when planning, generating, importing, recreating, or validating MCP content.

## Unreal C++ Convention Baseline

- Date: 2026-06-06 12:04 KST
- Scope: project C++ review and convention management rules.
- Decision: 이에타 manages the Unreal C++ convention baseline for this project and applies it during `이에타 C++ 리뷰`.
- Source priority: Epic official Unreal C++ coding standard first, then Unreal Engine/Lyra local style, then CubelessStylized project-specific rules, then third-party checklists as supporting references only.
- Documentation: `AGENTS.md` now links the C++ review mode to `docs/unreal-cpp-conventions.md`, and the new docs page records naming, UObject ownership, module boundaries, Slate/editor UI, async/socket, UnrealMCP, and verification expectations.
- Editor defaults: `.editorconfig` was added only for safe UTF-8, CRLF, final newline, and whitespace defaults. It does not force C++ indentation style.
- Formatter rule: `.clang-format` remains deferred. It must be trialed on a small sample or temporary copy before any real source adoption, and broad formatting needs explicit approval.
- Notion capture fallback: Notion enhanced markdown spec fetch failed with `INVALID_ARGUMENT`, so this local work-log entry is the durable capture.

## MCP Sample Learning Resource Folder

## OptimizationPreviewTools Material Replay UI Input Fix

- Date: 2026-06-06 14:38 KST
- Scope: `Plugins/OptimizationPreviewTools/Source/OptimizationPreviewTools/Private/MaterialGPUPreview.cpp`.
- Change: `stat profiling` command buttons now rely on real Slate buttons plus a viewport input preprocessor that consumes mouse and touch events before gameplay input.
- Change: Material replay controls were simplified to `PLAY/STOP`, time label, and slider. `stat mat replay` now starts paused at the first sample, and playback begins from the current slider position.
- Change: Replay slider scrubbing now uses screen-space hit rectangles computed from the current viewport geometry, pauses playback immediately on drag, updates the replay sample while dragging, and clears drag state when the overlay is removed.
- Verification: `git diff --check` passed with only the repository CRLF warning. `StylizedCubelessEditor Win64 Development` build succeeded after compiling and linking `UnrealEditor-OptimizationPreviewTools.dll`.

## OptimizationPreviewTools Replay Threshold and Camera Binding Fix

- Date: 2026-06-06 15:14 KST
- Scope: `Plugins/OptimizationPreviewTools` Material GPU Preview replay and stat profiling Slate input.
- Change: default Material GPU Preview ms thresholds moved to `DebugGreenMaxMs=0.3` and `DebugWhiteMs=0.6` in plugin config and C++ fallback defaults.
- Change: `stat profiling` buttons now store per-button Slate widget hit geometry so all buttons can be resolved individually by mouse or touch before gameplay input.
- Change: Material replay slider hit testing now prefers the actual Slate slider geometry, pauses playback as soon as the user scrubs, and guards replay duration against non-finite Insights frame end times.
- Change: replay camera samples are captured during `stat mat start/end`, and replay mode keeps the player view target bound to the transient replay camera while disabling look input until replay teardown.
- Verification: `StylizedCubelessEditor Win64 Development -NoLiveCoding` build succeeded after the input and camera changes, then succeeded again after the non-finite replay duration guard.

- Date: 2026-06-06 14:01 KST
- Decision: `/Content/_MCP_Sample/` is reserved for local MCP learning/sample resources.
- Git rule: `/Content/_MCP_Sample/` is now gitignored by default and must not be staged or committed unless the user explicitly asks to version a specific sample asset.
- Agent rule: 이에타 treats this folder as a learning-resource area, separate from disposable `_MCP_Temp` validation output and stable `/Content/MCPTestFixtures/` fixtures.
