"""Run the local StackOBot animation documentation/tooling checks.

This is a read-only convenience runner. It compiles the StackOBot animation
checker scripts, validates the documentation audit, runs the static preflight
gate, and checks staged Git scope. It does not call Unreal commands or mutate
assets. Use --require-bridge immediately before live editor work.
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
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_DocAudit" / "StackOBotAnimationLocalChecks.json"

CHECKER_FILES = [
    "Tools/Unreal/check_stackobot_animation_docs.py",
    "Tools/Unreal/check_stackobot_animation_preflight.py",
    "Tools/Unreal/check_stackobot_animation_staging_scope.py",
    "Tools/Unreal/run_stackobot_animation_local_checks.py",
]


def _run_command(label: str, command: list[str]) -> dict[str, Any]:
    started_at = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "label": label,
            "command": command,
            "cwd": PROJECT_ROOT.as_posix(),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "elapsed_seconds": round(time.monotonic() - started_at, 4),
            "success": completed.returncode == 0,
        }
    except Exception as exc:
        return {
            "label": label,
            "command": command,
            "cwd": PROJECT_ROOT.as_posix(),
            "elapsed_seconds": round(time.monotonic() - started_at, 4),
            "success": False,
            "error": str(exc),
        }


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    preflight_command = [
        sys.executable,
        "Tools/Unreal/check_stackobot_animation_preflight.py",
        "--summary",
    ]
    if args.require_bridge:
        preflight_command.append("--require-bridge")

    checks = [
        _run_command("py_compile", [sys.executable, "-m", "py_compile", *CHECKER_FILES]),
        _run_command("docs_audit", [sys.executable, "Tools/Unreal/check_stackobot_animation_docs.py", "--summary"]),
        _run_command("preflight", preflight_command),
        _run_command(
            "staging_scope",
            [sys.executable, "Tools/Unreal/check_stackobot_animation_staging_scope.py", "--summary"],
        ),
    ]

    pass_value = all(check["success"] for check in checks)
    report = {
        "schema": "stackobot_animation_local_checks_v1",
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": PROJECT_ROOT.as_posix(),
        "require_bridge": args.require_bridge,
        "pass": pass_value,
        "checks": checks,
    }

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = REPORT_PATH.relative_to(PROJECT_ROOT).as_posix()

    return report


def _format_summary(report: dict[str, Any]) -> str:
    status = "PASS" if report["pass"] else "FAIL"
    lines = [
        f"StackOBot animation local checks: {status}",
        (
            f"schema={report['schema']} require_bridge={str(report['require_bridge']).lower()} "
            f"checks={len(report['checks'])}"
        ),
    ]
    if report.get("report_path"):
        lines.append(f"report={report['report_path']}")
    for check in report["checks"]:
        check_status = "PASS" if check["success"] else "FAIL"
        lines.append(f"{check['label']}: {check_status} rc={check.get('returncode', 'error')}")
        stdout = str(check.get("stdout", "")).strip()
        stderr = str(check.get("stderr", "")).strip()
        if stdout:
            lines.extend(f"  {line}" for line in stdout.splitlines())
        if stderr:
            lines.extend(f"  stderr: {line}" for line in stderr.splitlines())
        if check.get("error"):
            lines.append(f"  error: {check['error']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-bridge",
        action="store_true",
        help="Require the StackOBot UnrealMCP bridge to be reachable.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write JSON report under Saved/MCP_DocAudit.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a concise pass/fail summary instead of the full JSON report.",
    )
    args = parser.parse_args(argv)

    report = run(args)
    if args.summary:
        print(_format_summary(report))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
