# Claude Project Instructions

@AGENTS.md

## Claude Code Handoff

- Treat `AGENTS.md` as the project source of truth. If these Claude-specific notes conflict with `AGENTS.md`, follow `AGENTS.md`.
- Start from the cloned `CubelessStylized` repository root unless the user says otherwise.
- The sibling managed workspace is `../unreal-mcp-cubeless` relative to the `CubelessStylized` parent folder. If Claude Code cannot access it, restart from the project root with `claude --add-dir ../unreal-mcp-cubeless`.
- At the start of work, check `CubelessStylized` and `unreal-mcp-cubeless` separately:
  - `git fetch --prune`
  - `git status --short --branch --untracked-files=all`
  - `git rev-list --left-right --count 'HEAD...@{u}'`
- Keep Git operations separate between the two repositories. Do not mix status, diffs, staging, commits, pushes, or summaries.
- Do not stage ignored or generated outputs unless the user explicitly asks for a specific artifact. This includes `_MCP_Temp`, `_MCP_Sample`, packaging outputs under `Build/`, and ordinary Unreal/editor temporary assets.
- If Unreal MCP, editor bridge, Ieta Slate, Notion, or other Codex-specific tooling is unavailable in Claude Code, report the blocker. Do not pretend that Unreal assets or external records were modified.

### CubelessOps Claude Adapter

- `../CubelessOps` is the shared operating-memory source. Claude-specific adapter files are isolated under `../CubelessOps/integrations/claude-code/`; do not put Claude wrappers or templates into the Codex `../CubelessOps/skills/` tree.
- Treat `../CubelessOps` as read-only while acting through Claude Code. Reference it with pointers / Read unless the user explicitly switches to a Codex/Ops maintenance task.
- CubelessOps skills are exposed to Claude only through thin discovery wrappers under `.claude/skills/` (`unreal-material-decomposition`, `unreal-mcp-safety-review`, `unreal-pcg-authoring`). Each wrapper reads its CubelessOps original at runtime.
- When the allowed CubelessOps skill frontmatter changes, refresh wrappers from the project root with `pwsh ../CubelessOps/integrations/claude-code/sync-cubelessops-skills.ps1 -ProjectRoot .`. Body/doc/memory changes need no sync because wrappers read upstream live.
- Full mapping, sync flow, and reader substitutions live in `../CubelessOps/integrations/claude-code/claude-code-bridge.md`.
