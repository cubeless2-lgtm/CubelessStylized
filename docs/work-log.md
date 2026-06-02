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
