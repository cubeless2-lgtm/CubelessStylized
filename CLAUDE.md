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
