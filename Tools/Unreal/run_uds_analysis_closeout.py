#!/usr/bin/env python3
"""Run the UDS analysis closeout checks.

This runner is a read-only orchestration layer. It compiles the local helper
scripts, captures the current UDS/UDW runtime state, runs the Cubeless sky
promotion preflight, records Git status for both managed workspaces, and writes
a single generated closeout report.
"""

from __future__ import annotations

import argparse
import json
import py_compile
import subprocess
import time
from pathlib import Path
from typing import Any

import capture_uds_sky_snapshot
import check_cubeless_sky_promotion_preflight
import scan_unreal_editor_log
from run_pcg_bookmark_visual_qa import PROJECT_ROOT


SIBLING_MCP_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless"
REPORT_DIR = PROJECT_ROOT / "Saved" / "UDS_Analysis"
DEFAULT_REPORT_PATH = REPORT_DIR / "uds_analysis_closeout.json"

HELPER_SCRIPTS = [
    PROJECT_ROOT / "Tools" / "Unreal" / "audit_cubeless_sky_dependencies.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "build_uds_analysis_delivery_manifest.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "check_uds_analysis_staging_scope.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "capture_uds_sky_snapshot.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "check_cubeless_sky_promotion_preflight.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "run_uds_analysis_closeout.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "scan_unreal_editor_log.py",
]


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


def _compile_helpers() -> dict[str, Any]:
    records = []
    for script_path in HELPER_SCRIPTS:
        record: dict[str, Any] = {
            "path": str(script_path),
            "exists": script_path.exists(),
            "compiled": False,
        }
        if not script_path.exists():
            record["error"] = "missing script"
            records.append(record)
            continue
        try:
            py_compile.compile(str(script_path), doraise=True)
            record["compiled"] = True
        except py_compile.PyCompileError as exc:
            record["error"] = str(exc)
        records.append(record)

    return {
        "success": all(bool(record.get("compiled")) for record in records),
        "scripts": records,
    }


def _snapshot_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        uds_actor_hint=args.uds_actor_hint,
        udw_actor_hint=args.udw_actor_hint,
        output="",
        timestamped_output=True,
        capture_screenshot=args.capture_screenshot,
        redraw_count=args.redraw_count,
        mcp_response_timeout_seconds=args.mcp_response_timeout_seconds,
    )


def _promotion_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        package_root=args.package_root,
        forbidden_root=list(args.forbidden_root),
        bp_sky_system=args.bp_sky_system,
        sky_dome_component_name=args.sky_dome_component_name,
        sky_dome_material=args.sky_dome_material,
        expected_sky_mesh=args.expected_sky_mesh,
        expected_cloud_texture=args.expected_cloud_texture,
        weather_data_asset=list(args.weather_data_asset),
        output="",
        timestamped_output=True,
        max_recursion_nodes=args.max_recursion_nodes,
        mcp_response_timeout_seconds=args.mcp_response_timeout_seconds,
    )


def _safe_run_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    if args.skip_snapshot:
        return {"skipped": True, "pass": True}
    try:
        return capture_uds_sky_snapshot.run(_snapshot_args(args))
    except Exception as exc:
        return {
            "schema": "cubeless_uds_sky_snapshot_runner_v1",
            "pass": False,
            "error": str(exc),
        }


def _safe_run_promotion_preflight(args: argparse.Namespace) -> dict[str, Any]:
    if args.skip_promotion_preflight:
        return {"skipped": True, "pass": True}
    try:
        return check_cubeless_sky_promotion_preflight.run(_promotion_args(args))
    except Exception as exc:
        return {
            "schema": "cubeless_sky_promotion_preflight_runner_v1",
            "pass": False,
            "error": str(exc),
        }


def _log_scan_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        log_dir=args.log_dir,
        log_pattern=args.log_pattern,
        log_path=args.log_path,
        output="",
        timestamped_output=True,
        encoding=args.log_encoding,
        max_line_chars=args.log_max_line_chars,
        max_fatal_entries=args.log_max_fatal_entries,
        max_ensure_entries=args.log_max_ensure_entries,
        max_error_entries=args.log_max_error_entries,
        max_warning_entries=args.log_max_warning_entries,
    )


def _safe_run_log_scan(args: argparse.Namespace) -> dict[str, Any]:
    if args.skip_log_scan:
        return {"skipped": True, "pass": True}
    try:
        return scan_unreal_editor_log.run(_log_scan_args(args))
    except Exception as exc:
        return {
            "schema": "unreal_editor_log_scan_v1",
            "pass": False,
            "error": str(exc),
        }


def _git_checks() -> dict[str, Any]:
    return {
        "project_status": _run_command(["git", "status", "--short", "--branch"], PROJECT_ROOT),
        "project_diff_check": _run_command(["git", "diff", "--check"], PROJECT_ROOT),
        "sibling_mcp_status": _run_command(["git", "status", "--short", "--branch"], SIBLING_MCP_ROOT),
    }


def _validation(
    compile_result: dict[str, Any],
    snapshot: dict[str, Any],
    promotion_preflight: dict[str, Any],
    editor_log_scan: dict[str, Any],
    git_checks: dict[str, Any],
) -> dict[str, Any]:
    return {
        "helper_scripts_compile": bool(compile_result.get("success")),
        "uds_snapshot_pass": bool(snapshot.get("pass")),
        "promotion_preflight_pass": bool(promotion_preflight.get("pass")),
        "editor_log_scan_pass": bool(editor_log_scan.get("pass")),
        "project_diff_check_pass": bool(git_checks.get("project_diff_check", {}).get("success")),
        "sibling_mcp_status_read": bool(git_checks.get("sibling_mcp_status", {}).get("success")),
    }


def _warnings(
    snapshot: dict[str, Any],
    promotion_preflight: dict[str, Any],
    editor_log_scan: dict[str, Any],
    git_checks: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []

    snapshot_dirty = (
        snapshot.get("unreal_snapshot", {})
        .get("dirty_packages", {})
        .get("dirty_map_packages", [])
    )
    if snapshot_dirty:
        warnings.append(
            "UDS snapshot reports dirty map packages: "
            + ", ".join(str(item) for item in snapshot_dirty)
        )

    warnings.extend(str(item) for item in promotion_preflight.get("warnings", []) or [])
    warnings.extend(str(item) for item in editor_log_scan.get("warnings", []) or [])

    project_status = git_checks.get("project_status", {}).get("stdout", "")
    if "Content/ANGRY_MESH/" in project_status:
        warnings.append("Project status includes unrelated untracked Content/ANGRY_MESH/; it was not touched.")
    if "Content/UltraDynamicSky/Maps/DemoMap.umap" in project_status:
        warnings.append("Project status still includes the UDS DemoMap binary map touched by runtime repair.")

    return warnings


def run(args: argparse.Namespace) -> dict[str, Any]:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else DEFAULT_REPORT_PATH
    if args.timestamped_output:
        output_path = REPORT_DIR / f"uds_analysis_closeout_{timestamp}.json"

    compile_result = _compile_helpers()
    snapshot = _safe_run_snapshot(args)
    promotion_preflight = _safe_run_promotion_preflight(args)
    editor_log_scan = _safe_run_log_scan(args)
    git_checks = _git_checks()
    validation = _validation(compile_result, snapshot, promotion_preflight, editor_log_scan, git_checks)

    report = {
        "schema": "uds_analysis_closeout_runner_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only UDS analysis closeout. Does not save or modify Unreal assets.",
        "project_root": str(PROJECT_ROOT),
        "sibling_mcp_root": str(SIBLING_MCP_ROOT),
        "helper_compile": compile_result,
        "uds_snapshot": snapshot,
        "promotion_preflight": promotion_preflight,
        "editor_log_scan": editor_log_scan,
        "git_checks": git_checks,
        "validation": validation,
        "warnings": _warnings(snapshot, promotion_preflight, editor_log_scan, git_checks),
        "pass": all(bool(value) for value in validation.values()),
        "report_path": str(output_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _console_summary(report: dict[str, Any]) -> dict[str, Any]:
    snapshot = report.get("uds_snapshot", {}) or {}
    promotion_preflight = report.get("promotion_preflight", {}) or {}
    editor_log_scan = report.get("editor_log_scan", {}) or {}
    return {
        "pass": bool(report.get("pass")),
        "report_path": report.get("report_path"),
        "validation": report.get("validation", {}),
        "generated_reports": {
            "uds_snapshot": snapshot.get("report_path"),
            "promotion_preflight": promotion_preflight.get("report_path"),
            "editor_log_scan": editor_log_scan.get("report_path"),
        },
        "warnings": report.get("warnings", []),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run UDS analysis closeout checks.")
    parser.add_argument("--output", default="")
    parser.add_argument("--timestamped-output", action="store_true")
    parser.add_argument(
        "--full-json",
        action="store_true",
        help="Print the full closeout JSON to stdout. The report file is always full JSON.",
    )
    parser.add_argument("--capture-screenshot", action="store_true")
    parser.add_argument("--redraw-count", type=int, default=2)
    parser.add_argument("--skip-snapshot", action="store_true")
    parser.add_argument("--skip-promotion-preflight", action="store_true")
    parser.add_argument("--skip-log-scan", action="store_true")
    parser.add_argument("--uds-actor-hint", default="")
    parser.add_argument("--udw-actor-hint", default="")
    parser.add_argument("--package-root", default=check_cubeless_sky_promotion_preflight.DEFAULT_PACKAGE_ROOT)
    parser.add_argument(
        "--forbidden-root",
        action="append",
        default=list(check_cubeless_sky_promotion_preflight.DEFAULT_FORBIDDEN_ROOTS),
    )
    parser.add_argument("--bp-sky-system", default=check_cubeless_sky_promotion_preflight.DEFAULT_BP_SKY_SYSTEM)
    parser.add_argument(
        "--sky-dome-component-name",
        default=check_cubeless_sky_promotion_preflight.DEFAULT_SKY_DOME_COMPONENT,
    )
    parser.add_argument(
        "--sky-dome-material",
        default=check_cubeless_sky_promotion_preflight.DEFAULT_SKY_DOME_MATERIAL,
    )
    parser.add_argument(
        "--expected-sky-mesh",
        default=check_cubeless_sky_promotion_preflight.DEFAULT_SKY_MESH,
    )
    parser.add_argument(
        "--expected-cloud-texture",
        default=check_cubeless_sky_promotion_preflight.DEFAULT_CLOUD_TEXTURE,
    )
    parser.add_argument(
        "--weather-data-asset",
        action="append",
        default=list(check_cubeless_sky_promotion_preflight.DEFAULT_WEATHER_DATA_ASSETS),
    )
    parser.add_argument("--max-recursion-nodes", type=int, default=5000)
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=240)
    parser.add_argument("--log-dir", default=str(scan_unreal_editor_log.DEFAULT_LOG_DIR))
    parser.add_argument("--log-pattern", default=scan_unreal_editor_log.DEFAULT_LOG_PATTERN)
    parser.add_argument("--log-path", default="")
    parser.add_argument("--log-encoding", default="utf-8")
    parser.add_argument("--log-max-line-chars", type=int, default=800)
    parser.add_argument("--log-max-fatal-entries", type=int, default=25)
    parser.add_argument("--log-max-ensure-entries", type=int, default=25)
    parser.add_argument("--log-max-error-entries", type=int, default=50)
    parser.add_argument("--log-max-warning-entries", type=int, default=25)
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_args()
    closeout = run(parsed_args)
    stdout_payload = closeout if parsed_args.full_json else _console_summary(closeout)
    print(json.dumps(stdout_payload, indent=2, ensure_ascii=False))
