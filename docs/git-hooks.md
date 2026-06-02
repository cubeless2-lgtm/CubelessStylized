# Git Hooks

This project keeps versioned Git hooks in `.githooks`.

Git does not clone or share `.git/hooks` contents, so hooks that should travel with the project must live in a tracked folder. Each local clone then points Git at that folder with:

```powershell
.\Tools\GitHooks\install-hooks.ps1
```

If PowerShell blocks script execution on this PC, run the installer with a one-time bypass:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Tools\GitHooks\install-hooks.ps1
```

The installer runs:

```powershell
git config core.hooksPath .githooks
```

This setting is local to the clone. Other PCs must run the installer once after pulling the repository.

## Active Hooks

### pre-commit

Managed file: `.githooks/pre-commit`

Runs: `Tools/GitHooks/check_unreal_python_uv_safety.py`

Purpose: block staged Unreal Python scripts that call `StaticMeshDescription.GetVertexInstanceUV` without an obvious UV channel count guard.

Why: Unreal can crash with a native assertion if `GetVertexInstanceUV` is called for a UV channel that does not exist. The known crash happened after `get_num_uv_channels(mesh, 0)` returned `1`, but the diagnostic script continued to call `GetVertexInstanceUV(..., 1)`.

Expected safe pattern:

```python
num_uv_channels = unreal.StaticMeshEditorSubsystem().get_num_uv_channels(mesh, 0)
for uv_channel in range(num_uv_channels):
    uv = mesh_description.get_vertex_instance_uv(vertex_instance_id, uv_channel)
```

If a script is intentionally safe but the hook cannot recognize it, add this comment in the file:

```python
# unreal-uv-safety: allow-getvertexinstanceuv
```

Use that override sparingly. Prefer making the channel-count guard obvious instead.
