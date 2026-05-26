# Codex Project Instructions

## Unreal MCP Asset Editing

- When debugging, modifying, or creating Blueprints, PCG graphs, Animation Blueprints, Control Rigs, or related Unreal assets through Unreal MCP, do not add or generate C++ code by default.
- Prefer fixing the issue inside the existing Unreal asset/class: Blueprint graph, AnimBP graph, Control Rig graph, PCG graph, asset defaults, component settings, level instance settings, or editor-exposed properties.
- If an Unreal asset cannot be safely modified through MCP or editor scripting, provide a concrete manual edit guide instead of adding C++.
- Add or modify C++ only when the user explicitly asks for a code/C++ implementation.
- Before considering C++ for an Unreal MCP task, state the non-C++ approach being attempted or why MCP/editor-asset editing is blocked.
