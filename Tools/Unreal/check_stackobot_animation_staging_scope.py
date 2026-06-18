"""Check staged Git paths for StackOBot animation study commits.

This helper is intentionally local/read-only. It inspects the Cubeless Git
index and fails if paths outside the StackOBot animation documentation/tooling
scope are staged. It is meant to keep unrelated Unreal assets and PCG work out
of StackOBot animation study commits.
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
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_DocAudit" / "StackOBotAnimationStagingScope.json"

ALLOWED_EXACT = {
    "docs/work-log.md",
    "Tools/Unreal/check_stackobot_animation_docs.py",
    "Tools/Unreal/check_stackobot_animation_preflight.py",
    "Tools/Unreal/check_stackobot_animation_staging_scope.py",
}

ALLOWED_PREFIXES = (
    "docs/stackobot",
)

BLOCKED_PREFIX_REASONS = {
    "Content/": "Unreal assets/content are not part of StackOBot animation docs/tooling commits.",
    "Plugins/CustomTools/Content/Python/ArtScripts/CubelessDungeonPCGV2.py": (
        "PCG Dungeon V2 Python work is unrelated to StackOBot animation study commits."
    ),
    "docs/pcg-": "PCG documentation is unrelated to StackOBot animation study commits.",
    "Build/": "Build outputs are generated artifacts.",
    "Saved/": "Saved outputs are generated artifacts unless explicitly versioned.",
    "Intermediate/": "Intermediate outputs are generated artifacts.",
}


def _run_command(command: list[str], cwd: Path) -> dict[str, Any]:
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
            "command": command,
            "cwd": str(cwd),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "success": completed.returncode == 0,
        }
    except Exception as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "success": False,
            "error": str(exc),
        }


def _parse_name_status(stdout: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0] if parts else ""
        path = parts[-1] if parts else line
        entries.append(
            {
                "raw": line,
                "status": status,
                "path": path.replace("\\", "/"),
            }
        )
    return entries


def _classify_path(path: str) -> tuple[str, str]:
    if path in ALLOWED_EXACT:
        return "allowed_stackobot_animation_scope", "Exact StackOBot animation tooling or work-log path."
    if any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return "allowed_stackobot_animation_scope", "StackOBot animation documentation path."

    for prefix, reason in BLOCKED_PREFIX_REASONS.items():
        if path.startswith(prefix):
            return "blocked_staged", reason

    return "unknown_staged", "Path is not in the StackOBot animation documentation/tooling scope."


def _classify_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified: list[dict[str, Any]] = []
    for entry in entries:
        path = str(entry.get("path", ""))
        classification, reason = _classify_path(path)
        record = dict(entry)
        record["classification"] = classification
        record["reason"] = reason
        classified.append(record)
    return classified


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    staged_result = _run_command(["git", "diff", "--cached", "--name-status"], PROJECT_ROOT)
    diff_check = _run_command(["git", "diff", "--cached", "--check"], PROJECT_ROOT)

    entries = _parse_name_status(staged_result.get("stdout", "")) if staged_result.get("success") else []
    classified = _classify_entries(entries)
    blocked = [entry for entry in classified if entry["classification"] == "blocked_staged"]
    unknown = [entry for entry in classified if entry["classification"] == "unknown_staged"]
    allowed = [entry for entry in classified if entry["classification"] == "allowed_stackobot_animation_scope"]

    pass_value = bool(staged_result.get("success")) and bool(diff_check.get("success")) and not blocked and not unknown

    report = {
        "schema": "stackobot_animation_staging_scope_v1",
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": PROJECT_ROOT.as_posix(),
        "pass": pass_value,
        "staged_count": len(classified),
        "allowed_count": len(allowed),
        "blocked_count": len(blocked),
        "unknown_count": len(unknown),
        "diff_check_success": bool(diff_check.get("success")),
        "staged_command": staged_result,
        "diff_check": diff_check,
        "entries": classified,
        "blocked_entries": blocked,
        "unknown_entries": unknown,
        "allowed_exact": sorted(ALLOWED_EXACT),
        "allowed_prefixes": list(ALLOWED_PREFIXES),
    }

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = REPORT_PATH.relative_to(PROJECT_ROOT).as_posix()

    return report


def _format_summary(report: dict[str, Any]) -> str:
    status = "PASS" if report["pass"] else "FAIL"
    lines = [
        f"StackOBot animation staging scope: {status}",
        (
            f"schema={report['schema']} staged={report['staged_count']} "
            f"allowed={report['allowed_count']} blocked={report['blocked_count']} "
            f"unknown={report['unknown_count']} diff_check={str(report['diff_check_success']).lower()}"
        ),
    ]
    if report.get("report_path"):
        lines.append(f"report={report['report_path']}")
    if report["blocked_entries"]:
        lines.append("blocked_entries:")
        for entry in report["blocked_entries"]:
            lines.append(f"  - {entry['status']} {entry['path']}: {entry['reason']}")
    if report["unknown_entries"]:
        lines.append("unknown_entries:")
        for entry in report["unknown_entries"]:
            lines.append(f"  - {entry['status']} {entry['path']}: {entry['reason']}")
    if not report["diff_check_success"]:
        lines.append("diff_check_failed:")
        lines.append(str(report["diff_check"].get("stdout", "")).rstrip())
        lines.append(str(report["diff_check"].get("stderr", "")).rstrip())
    return "\n".join(line for line in lines if line != "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
