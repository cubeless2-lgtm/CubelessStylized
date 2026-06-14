"""Check current Unreal Editor dirty package state for PCG dungeon delivery.

This check is read-only. It does not save packages; it only reports whether the
currently running editor has dirty content or map packages.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from run_pcg_bookmark_visual_qa import (
    PROJECT_ROOT,
    UnrealConnection,
    parse_execute_python_log_json,
    send,
)


REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_LiveDirtyState.json"


def _execute_dirty_state_check(unreal: UnrealConnection) -> dict[str, Any]:
    code = """
import json
import unreal


def _package_names(packages):
    names = []
    for package in packages:
        try:
            names.append(package.get_name())
        except Exception:
            names.append(str(package))
    return sorted(set(names))


error = None
try:
    dirty_content = _package_names(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    dirty_maps = _package_names(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
except Exception as exc:
    dirty_content = []
    dirty_maps = []
    error = str(exc)

result = {
    "success": error is None,
    "schema": "cubeless_pcg_dungeon_live_dirty_state_v1",
    "policy": "Read-only dirty package check. Does not save content or maps.",
    "dirty_content_packages": dirty_content,
    "dirty_map_packages": dirty_maps,
    "dirty_content_count": len(dirty_content),
    "dirty_map_count": len(dirty_maps),
    "dirty_total_count": len(set(dirty_content + dirty_maps)),
    "error": error,
}
result["pass"] = bool(result["success"] and result["dirty_total_count"] == 0)
print(json.dumps(result, ensure_ascii=False))
"""
    response = send(unreal, "execute_python", {"code": code, "mode": "ExecuteFile"})
    return parse_execute_python_log_json(response)


def run(args: argparse.Namespace) -> dict[str, Any]:
    unreal = UnrealConnection()
    if hasattr(unreal, "timeout"):
        unreal.timeout = max(int(getattr(unreal, "timeout", 0)), int(args.mcp_response_timeout_seconds))

    dirty_state = _execute_dirty_state_check(unreal)
    report = {
        "schema": "cubeless_pcg_dungeon_live_dirty_state_runner_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only live editor dirty package check. Does not save packages.",
        "dirty_state": dirty_state,
        "pass": bool(dirty_state.get("pass")),
        "report_path": str(REPORT_PATH),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check current Unreal Editor dirty package state.")
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=120)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
