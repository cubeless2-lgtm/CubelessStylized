"""Commandlet wrapper for the dedicated fence runtime promotion."""

from __future__ import annotations

import json
import os
import runpy


SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "promote_pcg_fence_runtime.py")


namespace = runpy.run_path(SCRIPT_PATH, run_name="cubeless_fence_runtime_direct")
result = namespace["promote_pcg_fence_runtime_direct"]()
print(
    json.dumps(
        {
            "pass": bool(result.get("pass")),
            "report": result.get("report_path"),
            "graph": result.get("graph_update", {}).get("graph_path"),
            "blueprint": result.get("blueprint_update", {}).get("blueprint_path"),
            "spline_mesh_component_count": result.get("validation", {}).get("spline_mesh_component_count"),
        },
        ensure_ascii=False,
    )
)
