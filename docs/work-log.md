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
