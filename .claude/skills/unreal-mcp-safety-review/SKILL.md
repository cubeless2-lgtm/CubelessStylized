---
name: unreal-mcp-safety-review
description: Audit Unreal MCP or UnrealMCP-assisted changes for unsafe project dependencies and editor crash hazards. Use when modifying MCP C++ or Python tools, authoring Unreal assets through MCP, promoting MCP-authored content, opening or creating maps, reviewing for /Script/UnrealMCP hard references, checking generic Python map switching, dirty package blockers, packaging safety, or editor-only tooling boundaries.
---

# unreal-mcp-safety-review (CubelessOps Claude wrapper)

> Thin Claude Code discovery wrapper. The real skill lives in CubelessOps and must not be copied or edited here.

When this skill runs:

1. From the consuming project root, resolve CubelessOps as sibling `../CubelessOps`, or use `CUBELESS_OPS_ROOT`.
2. Read the original skill body at `../CubelessOps/skills/unreal-mcp-safety-review/SKILL.md`.
3. Read `../CubelessOps/skills/unreal-mcp-safety-review/references/ops-references.md` and load the linked workflow, policy, project, or role docs as instructed.
4. Follow the original instructions with these reader substitutions:
   - The Codex `$skill-name` invocation syntax -> invoke the matching Claude Code skill, or read that skill's `SKILL.md` and follow it.
   - "Codex" in source text -> the current Claude Code agent.
5. Do not modify files under `CubelessOps` while acting through Claude. Apply edits only in the consuming repository unless the user explicitly switches to a Codex/Ops maintenance task.

Re-run the CubelessOps Claude sync tool only when original skill frontmatter changes or the project allowlist changes. Body and reference edits are read live from CubelessOps.
