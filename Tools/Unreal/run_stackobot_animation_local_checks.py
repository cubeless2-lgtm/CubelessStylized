"""Run the local StackOBot animation documentation/tooling checks.

This is a read-only convenience runner. It compiles the StackOBot animation
checker scripts, validates the documentation audit, runs the static preflight
gate, checks staged Git scope, and reports sibling workspace Git status. It does
not call Unreal commands or mutate assets. Use --require-bridge immediately
before live editor work.
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
SIBLING_MCP_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless"
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_DocAudit" / "StackOBotAnimationLocalChecks.json"
EXPECTED_DOCS_AUDIT_SCHEMA = "stackobot_animation_docs_link_audit_v95"
EXPECTED_PREFLIGHT_SCHEMA = "stackobot_animation_preflight_v1"
EXPECTED_STAGING_SCOPE_SCHEMA = "stackobot_animation_staging_scope_v1"

CHECKER_FILES = [
    "Tools/Unreal/check_stackobot_animation_docs.py",
    "Tools/Unreal/check_stackobot_animation_preflight.py",
    "Tools/Unreal/check_stackobot_animation_staging_scope.py",
    "Tools/Unreal/run_stackobot_animation_local_checks.py",
]


def _configure_output_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _run_command(label: str, command: list[str], cwd: Path = PROJECT_ROOT) -> dict[str, Any]:
    started_at = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "label": label,
            "command": command,
            "cwd": cwd.as_posix(),
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
            "cwd": cwd.as_posix(),
            "elapsed_seconds": round(time.monotonic() - started_at, 4),
            "success": False,
            "error": str(exc),
        }


def _require_stdout_token(check: dict[str, Any], token: str, description: str) -> None:
    stdout = str(check.get("stdout", ""))
    matched = token in stdout
    check["expected_token"] = token
    check["expected_token_description"] = description
    check["expected_token_matched"] = matched
    if not matched:
        check["success"] = False
        check["error"] = f"Missing expected {description}: {token}"


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
    docs_audit_check = next(check for check in checks if check["label"] == "docs_audit")
    _require_stdout_token(
        docs_audit_check,
        f"schema={EXPECTED_DOCS_AUDIT_SCHEMA}",
        "docs audit schema",
    )
    preflight_check = next(check for check in checks if check["label"] == "preflight")
    _require_stdout_token(
        preflight_check,
        f"schema={EXPECTED_PREFLIGHT_SCHEMA}",
        "preflight schema",
    )
    staging_scope_check = next(check for check in checks if check["label"] == "staging_scope")
    _require_stdout_token(
        staging_scope_check,
        f"schema={EXPECTED_STAGING_SCOPE_SCHEMA}",
        "staging scope schema",
    )
    workspace_status = {
        "cubeless_status": _run_command("cubeless_git_status", ["git", "status", "--short"], PROJECT_ROOT),
        "sibling_mcp_status": _run_command("sibling_mcp_git_status", ["git", "status", "--short"], SIBLING_MCP_ROOT),
    }
    sibling_status = str(workspace_status["sibling_mcp_status"].get("stdout", "")).strip()
    sibling_clean = bool(workspace_status["sibling_mcp_status"].get("success")) and not sibling_status

    pass_value = all(check["success"] for check in checks) and (sibling_clean or not args.require_sibling_clean)
    report = {
        "schema": "stackobot_animation_local_checks_v16",
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": PROJECT_ROOT.as_posix(),
        "sibling_mcp_root": SIBLING_MCP_ROOT.as_posix(),
        "expected_docs_audit_schema": EXPECTED_DOCS_AUDIT_SCHEMA,
        "expected_preflight_schema": EXPECTED_PREFLIGHT_SCHEMA,
        "expected_staging_scope_schema": EXPECTED_STAGING_SCOPE_SCHEMA,
        "require_bridge": args.require_bridge,
        "require_sibling_clean": args.require_sibling_clean,
        "sibling_clean": sibling_clean,
        "pass": pass_value,
        "checks": checks,
        "workspace_status": workspace_status,
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
            f"require_sibling_clean={str(report['require_sibling_clean']).lower()} "
            f"sibling_clean={str(report['sibling_clean']).lower()} "
            f"expected_docs_audit_schema={report['expected_docs_audit_schema']} "
            f"expected_preflight_schema={report['expected_preflight_schema']} "
            f"expected_staging_scope_schema={report['expected_staging_scope_schema']} "
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
    workspace_status = report.get("workspace_status", {})
    for label in ["cubeless_status", "sibling_mcp_status"]:
        entry = workspace_status.get(label) or {}
        stdout = str(entry.get("stdout", "")).strip()
        count = len(stdout.splitlines()) if stdout else 0
        status = "PASS" if entry.get("success") else "FAIL"
        lines.append(f"{label}: {status} dirty_lines={count}")
        if stdout:
            lines.extend(f"  {line}" for line in stdout.splitlines()[:20])
            if count > 20:
                lines.append(f"  ... {count - 20} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    _configure_output_encoding()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-bridge",
        action="store_true",
        help="Require the StackOBot UnrealMCP bridge to be reachable.",
    )
    parser.add_argument(
        "--require-sibling-clean",
        action="store_true",
        help="Fail if the sibling unreal-mcp-cubeless workspace has dirty files.",
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
