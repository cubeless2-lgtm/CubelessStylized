"""Run the Cubeless PCG dungeon V1 delivery closeout checks.

This runner is intentionally a local orchestration wrapper. It refreshes the
read-only dirty-state and asset-manifest reports, rebuilds summary/readiness
reports from existing evidence, runs the delivery preflight, and finishes with
`git diff --check`. It does not generate dungeon output, modify Unreal assets,
stage files, commit, push, or implement gameplay.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "MCP_Dungeon"
REPORT_PATH = REPORT_DIR / "CubelessDungeonMVP_DeliveryCloseout.json"


def _run_command(args: list[str], *, timeout_seconds: float) -> dict[str, Any]:
    started_at = time.monotonic()
    completed = subprocess.run(
        args,
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        check=False,
        timeout=max(1.0, timeout_seconds),
    )
    return {
        "args": args,
        "cwd": str(PROJECT_ROOT),
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _step(
    name: str,
    args: list[str],
    *,
    timeout_seconds: float,
    report_path: Path | None = None,
) -> dict[str, Any]:
    result = _run_command(args, timeout_seconds=timeout_seconds)
    result["name"] = name
    if report_path:
        report = _read_json(report_path)
        result["report_path"] = str(report_path)
        result["report_exists"] = report_path.exists()
        result["report_pass"] = report.get("pass")
        result["report_success"] = report.get("success")
        result["report_timestamp"] = report.get("timestamp")
    result["pass"] = bool(
        result["success"]
        and (
            not report_path
            or result.get("report_pass") is True
            or result.get("report_success") is True
        )
    )
    return result


def _failed_steps(steps: list[dict[str, Any]]) -> list[str]:
    return [step["name"] for step in steps if not step.get("pass")]


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    python = sys.executable
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    steps = [
        _step(
            "live_dirty_state",
            [
                python,
                "Tools/Unreal/check_pcg_dungeon_live_dirty_state.py",
                "--mcp-response-timeout-seconds",
                str(args.mcp_response_timeout_seconds),
            ],
            timeout_seconds=args.unreal_step_timeout_seconds,
            report_path=REPORT_DIR / "CubelessDungeonMVP_LiveDirtyState.json",
        ),
        _step(
            "asset_manifest_audit",
            [
                python,
                "Tools/Unreal/audit_pcg_dungeon_asset_manifest.py",
                "--mcp-response-timeout-seconds",
                str(args.mcp_response_timeout_seconds),
            ],
            timeout_seconds=args.unreal_step_timeout_seconds,
            report_path=REPORT_DIR / "CubelessDungeonMVP_AssetManifestAudit.json",
        ),
        _step(
            "native_evidence_summary",
            [python, "Tools/Unreal/run_pcg_dungeon_native_evidence_refresh.py", "--summarize-existing"],
            timeout_seconds=args.local_step_timeout_seconds,
            report_path=REPORT_DIR / "CubelessDungeonMVP_NativeEvidenceRefresh_Report.json",
        ),
        _step(
            "authoring_preset_matrix",
            [python, "Tools/Unreal/run_pcg_dungeon_authoring_preset_matrix.py", "--seed-count", "5"],
            timeout_seconds=args.unreal_step_timeout_seconds,
            report_path=REPORT_DIR / "CubelessDungeonMVP_AuthoringPresetMatrixRunner_Report.json",
        ),
        _step(
            "handoff_readiness",
            [python, "Tools/Unreal/check_pcg_dungeon_handoff_readiness.py"],
            timeout_seconds=args.local_step_timeout_seconds,
            report_path=REPORT_DIR / "CubelessDungeonMVP_HandoffReadiness.json",
        ),
        _step(
            "delivery_preflight",
            [python, "Tools/Unreal/check_pcg_dungeon_delivery_preflight.py"],
            timeout_seconds=args.local_step_timeout_seconds,
            report_path=REPORT_DIR / "CubelessDungeonMVP_DeliveryPreflight.json",
        ),
        _step(
            "git_diff_check",
            ["git", "diff", "--check"],
            timeout_seconds=args.local_step_timeout_seconds,
        ),
    ]

    failed = _failed_steps(steps)
    report = {
        "schema": "cubeless_pcg_dungeon_delivery_closeout_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "policy": (
            "Local closeout runner for the PCG dungeon V1 delivery. It refreshes read-only evidence reports "
            "and validates handoff/preflight state; it does not generate output, modify Unreal assets, stage, commit, or push."
        ),
        "steps": steps,
        "failed_steps": failed,
        "pass": not failed,
        "report_path": str(REPORT_PATH),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PCG dungeon V1 delivery closeout checks.")
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=120)
    parser.add_argument("--unreal-step-timeout-seconds", type=float, default=180.0)
    parser.add_argument("--local-step-timeout-seconds", type=float, default=120.0)
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result.get("pass") else 1)
