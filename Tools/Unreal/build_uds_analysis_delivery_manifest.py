#!/usr/bin/env python3
"""Build a delivery manifest for the UDS analysis branch.

The manifest is intentionally read-only. It classifies Git status entries into
stage candidates, explicit manual decisions, and excluded/unrelated paths so
UDS analysis delivery does not accidentally mix unrelated Unreal assets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from run_pcg_bookmark_visual_qa import PROJECT_ROOT


SIBLING_MCP_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless"
REPORT_DIR = PROJECT_ROOT / "Saved" / "UDS_Analysis"
DEFAULT_REPORT_PATH = REPORT_DIR / "uds_analysis_delivery_manifest.json"
EXPECTED_BRANCH = "codex/uds-analysis"
EXCLUDED_PATH_SAMPLE_LIMIT = 25

STAGE_EXACT = {
    "Content/Cubeless/Sky/BP_SkySystem.uasset",
    "Content/Cubeless/Sky/Data/DA_Weather_Clear.uasset",
    "Content/Cubeless/Sky/Data/DA_Weather_Cloudy.uasset",
    "Content/Cubeless/Sky/Data/DA_Weather_Overcast.uasset",
    "Content/Cubeless/Sky/Materials/M_Sky_Dome.uasset",
    "docs/work-log.md",
    "Tools/Unreal/audit_cubeless_sky_dependencies.py",
    "Tools/Unreal/build_uds_analysis_delivery_manifest.py",
    "Tools/Unreal/check_uds_analysis_staging_scope.py",
    "Tools/Unreal/capture_uds_sky_snapshot.py",
    "Tools/Unreal/check_cubeless_sky_promotion_preflight.py",
    "Tools/Unreal/run_uds_analysis_closeout.py",
    "Tools/Unreal/scan_unreal_editor_log.py",
}

STAGE_PREFIXES = (
    "Content/Cubeless/Sky/Meshes/",
    "docs/uds-analysis/",
)

MANUAL_EXACT = {
    "Content/UltraDynamicSky/Maps/DemoMap.umap": (
        "UDS reference map was touched by runtime cloud repair. Review this binary "
        "map diff separately before staging."
    ),
}

EXCLUDED_PREFIXES = {
    "Content/ANGRY_MESH/": "Unrelated untracked content present before delivery classification.",
    "Saved/": "Generated reports/screenshots are not delivery source files.",
    "Intermediate/": "Generated Unreal intermediate output.",
    "DerivedDataCache/": "Generated Unreal cache output.",
    "Binaries/": "Generated build output unless explicitly requested.",
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


def _parse_status(stdout: str) -> list[dict[str, Any]]:
    entries = []
    for line in stdout.splitlines():
        if not line:
            continue
        if len(line) < 4:
            entries.append({"raw": line, "status": "", "path": line, "parse_error": "short status line"})
            continue
        status = line[:2]
        path = line[3:]
        entries.append({"raw": line, "status": status, "path": path.replace("\\", "/")})
    return entries


def _branch_name(branch_stdout: str) -> str:
    first_line = branch_stdout.splitlines()[0] if branch_stdout.splitlines() else ""
    if first_line.startswith("## "):
        return first_line[3:].split("...", 1)[0].strip()
    return ""


def _latest_report(pattern: str) -> dict[str, Any]:
    reports = sorted(REPORT_DIR.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not reports:
        return {"found": False, "pattern": pattern}

    latest = reports[0]
    payload: dict[str, Any] = {}
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as exc:
        payload = {"read_error": str(exc)}
    return {
        "found": True,
        "path": str(latest),
        "pass": bool(payload.get("pass")),
        "schema": payload.get("schema"),
        "timestamp": payload.get("timestamp"),
    }


def _classify_entry(entry: dict[str, Any]) -> dict[str, Any]:
    path = str(entry.get("path", ""))
    classified = dict(entry)

    if path in STAGE_EXACT or any(path.startswith(prefix) for prefix in STAGE_PREFIXES):
        classified["classification"] = "stage_candidate"
        classified["reason"] = "Part of the UDS analysis, Cubeless sky cleanup, docs, or delivery tooling."
        return classified

    if path in MANUAL_EXACT:
        classified["classification"] = "manual_decision"
        classified["reason"] = MANUAL_EXACT[path]
        return classified

    for prefix, reason in EXCLUDED_PREFIXES.items():
        if path.startswith(prefix):
            classified["classification"] = "excluded"
            classified["reason"] = reason
            return classified

    classified["classification"] = "unknown_review"
    classified["reason"] = "Path is not in the known UDS analysis delivery scope."
    return classified


def _dedupe_paths(paths: list[str]) -> list[str]:
    return sorted(set(paths))


def _build_summary(classified_entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, list[dict[str, Any]]] = {}
    for entry in classified_entries:
        by_class.setdefault(str(entry.get("classification")), []).append(entry)

    excluded_prefix_counts: dict[str, int] = {}
    for entry in by_class.get("excluded", []):
        path = str(entry.get("path", ""))
        for prefix in EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                excluded_prefix_counts[prefix] = excluded_prefix_counts.get(prefix, 0) + 1
                break

    excluded_paths = _dedupe_paths([entry["path"] for entry in by_class.get("excluded", [])])
    return {
        "stage_candidate_count": len(by_class.get("stage_candidate", [])),
        "manual_decision_count": len(by_class.get("manual_decision", [])),
        "excluded_count": len(by_class.get("excluded", [])),
        "unknown_review_count": len(by_class.get("unknown_review", [])),
        "stage_candidate_paths": _dedupe_paths(
            [entry["path"] for entry in by_class.get("stage_candidate", [])]
        ),
        "manual_decision_paths": _dedupe_paths(
            [entry["path"] for entry in by_class.get("manual_decision", [])]
        ),
        "excluded_paths_sample": excluded_paths[:EXCLUDED_PATH_SAMPLE_LIMIT],
        "excluded_paths_sample_limit": EXCLUDED_PATH_SAMPLE_LIMIT,
        "excluded_paths_omitted_count": max(0, len(excluded_paths) - EXCLUDED_PATH_SAMPLE_LIMIT),
        "excluded_prefix_counts": dict(sorted(excluded_prefix_counts.items())),
        "unknown_review_paths": _dedupe_paths(
            [entry["path"] for entry in by_class.get("unknown_review", [])]
        ),
    }


def _validation(
    branch: str,
    project_status: dict[str, Any],
    sibling_status: dict[str, Any],
    diff_check: dict[str, Any],
    summary: dict[str, Any],
    closeout_report: dict[str, Any],
    promotion_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "on_expected_branch": branch == EXPECTED_BRANCH,
        "project_status_read": bool(project_status.get("success")),
        "sibling_mcp_status_read": bool(sibling_status.get("success")),
        "project_diff_check_pass": bool(diff_check.get("success")),
        "no_unknown_review_paths": int(summary.get("unknown_review_count", -1)) == 0,
        "has_stage_candidates": int(summary.get("stage_candidate_count", 0)) > 0,
        "latest_closeout_pass": bool(closeout_report.get("pass")),
        "latest_promotion_preflight_pass": bool(promotion_report.get("pass")),
    }


def _warnings(summary: dict[str, Any]) -> list[str]:
    warnings = []
    manual_paths = summary.get("manual_decision_paths", []) or []
    excluded_prefix_counts = summary.get("excluded_prefix_counts", {}) or {}
    if manual_paths:
        warnings.append("Manual staging decision required for: " + ", ".join(manual_paths))
    angry_mesh_count = int(excluded_prefix_counts.get("Content/ANGRY_MESH/", 0) or 0)
    if angry_mesh_count:
        warnings.append(f"Excluded {angry_mesh_count} unrelated untracked Content/ANGRY_MESH/ file(s).")
    return warnings


def run(args: argparse.Namespace) -> dict[str, Any]:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else DEFAULT_REPORT_PATH
    if args.timestamped_output:
        output_path = REPORT_DIR / f"uds_analysis_delivery_manifest_{timestamp}.json"

    project_status = _run_command(["git", "status", "--porcelain=v1", "-uall"], PROJECT_ROOT)
    project_branch_status = _run_command(["git", "status", "--short", "--branch"], PROJECT_ROOT)
    sibling_status = _run_command(["git", "status", "--short", "--branch"], SIBLING_MCP_ROOT)
    diff_check = _run_command(["git", "diff", "--check"], PROJECT_ROOT)

    branch = _branch_name(str(project_branch_status.get("stdout", "")))
    raw_entries = _parse_status(str(project_status.get("stdout", "")))
    classified_entries = [_classify_entry(entry) for entry in raw_entries]
    summary = _build_summary(classified_entries)
    closeout_report = _latest_report("uds_analysis_closeout_*.json")
    promotion_report = _latest_report("cubeless_sky_promotion_preflight_*.json")
    validation = _validation(
        branch,
        project_status,
        sibling_status,
        diff_check,
        summary,
        closeout_report,
        promotion_report,
    )

    report = {
        "schema": "uds_analysis_delivery_manifest_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only delivery classifier. Does not stage, commit, save, or modify Unreal assets.",
        "project_root": str(PROJECT_ROOT),
        "sibling_mcp_root": str(SIBLING_MCP_ROOT),
        "status_mode": "git status --porcelain=v1 -uall",
        "expected_branch": EXPECTED_BRANCH,
        "current_branch": branch,
        "status_entries": classified_entries,
        "summary": summary,
        "latest_closeout_report": closeout_report,
        "latest_promotion_preflight_report": promotion_report,
        "git_checks": {
            "project_status": project_status,
            "project_branch_status": project_branch_status,
            "sibling_mcp_status": sibling_status,
            "project_diff_check": diff_check,
        },
        "validation": validation,
        "warnings": _warnings(summary),
        "pass": all(bool(value) for value in validation.values()),
        "report_path": str(output_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _console_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {}) or {}
    validation = report.get("validation", {}) or {}
    return {
        "pass": bool(report.get("pass")),
        "report_path": report.get("report_path"),
        "current_branch": report.get("current_branch"),
        "summary": {
            "stage_candidate_count": summary.get("stage_candidate_count"),
            "manual_decision_count": summary.get("manual_decision_count"),
            "excluded_count": summary.get("excluded_count"),
            "unknown_review_count": summary.get("unknown_review_count"),
        },
        "validation": validation,
        "warnings": report.get("warnings", []),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the UDS analysis delivery manifest.")
    parser.add_argument("--output", default="")
    parser.add_argument("--timestamped-output", action="store_true")
    parser.add_argument(
        "--full-json",
        action="store_true",
        help="Print the full manifest JSON to stdout. The report file is always full JSON.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_args()
    manifest = run(parsed_args)
    stdout_payload = manifest if parsed_args.full_json else _console_summary(manifest)
    print(json.dumps(stdout_payload, indent=2, ensure_ascii=False))
