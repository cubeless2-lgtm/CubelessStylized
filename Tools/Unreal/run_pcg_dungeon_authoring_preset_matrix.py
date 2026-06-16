"""Run layout-only QA for all documented PCG dungeon authoring presets.

This runner is intentionally cheaper than the visual gate. It asks the running
Unreal Editor to evaluate every preset across a small seed window and writes a
matrix report under Saved/MCP_Dungeon. It does not regenerate assets, capture
screenshots, or modify project C++.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from run_pcg_dungeon_generation_visual_gate_qa import (
    DUNGEON_REPORT_DIR,
    UnrealConnection,
    _execute_dungeon_python,
)


RUNNER_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_AuthoringPresetMatrixRunner_Report.json"


def _execute_preset_matrix(unreal: UnrealConnection, seed_count: int, write_report: bool) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        f"""
catalog = dungeon.get_authoring_preset_catalog(seed_count=0)
matrix = dungeon.run_authoring_preset_seed_matrix(
    seed_count={int(seed_count)},
    write_report={bool(write_report)},
)
compact_presets = {{}}
for name, preset in sorted(matrix.get("presets", {{}}).items()):
    compact_presets[name] = {{
        "label": preset.get("label"),
        "intent": preset.get("intent"),
        "pass": bool(preset.get("pass")),
        "seed_count": preset.get("seed_count"),
        "pass_count": preset.get("pass_count"),
        "fail_count": preset.get("fail_count"),
        "failed_seeds": preset.get("failed_seeds", []),
        "seeds": preset.get("seeds", []),
        "config": preset.get("config", {{}}),
    }}
print(json.dumps({{
    "success": bool(matrix.get("pass")),
    "catalog_schema": catalog.get("schema"),
    "catalog_pass": bool(catalog.get("pass")),
    "available_presets": catalog.get("available_presets", []),
    "matrix_schema": matrix.get("schema"),
    "matrix_pass": bool(matrix.get("pass")),
    "preset_count": matrix.get("preset_count"),
    "seed_count": matrix.get("seed_count"),
    "failures": matrix.get("failures", []),
    "missing_presets": matrix.get("missing_presets", []),
    "matrix_report_path": matrix.get("report_path"),
    "presets": compact_presets,
}}, ensure_ascii=False))
""",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    DUNGEON_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    unreal = UnrealConnection()
    if hasattr(unreal, "timeout"):
        unreal.timeout = max(int(getattr(unreal, "timeout", 0)), int(args.mcp_response_timeout_seconds))

    matrix = _execute_preset_matrix(unreal, args.seed_count, not args.no_write_report)
    report = {
        "schema": "cubeless_pcg_dungeon_authoring_preset_matrix_runner_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "policy": (
            "Runs layout-only preset QA through UnrealMCP. It does not regenerate NativeOutput, "
            "capture screenshots, implement gameplay, stage files, commit, or push."
        ),
        "seed_count": int(args.seed_count),
        "write_unreal_report": not args.no_write_report,
        "matrix": matrix,
        "pass": bool(matrix.get("success") and matrix.get("matrix_pass")),
        "report_path": str(RUNNER_REPORT_PATH),
    }
    RUNNER_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PCG dungeon authoring preset layout matrix QA.")
    parser.add_argument("--seed-count", type=int, default=5)
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=240)
    parser.add_argument("--no-write-report", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
