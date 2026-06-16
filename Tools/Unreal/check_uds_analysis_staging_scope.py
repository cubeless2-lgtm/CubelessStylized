#!/usr/bin/env python3
"""Check staged Git paths for the UDS analysis branch.

This helper is intentionally read-only. It inspects the Git index and fails if
manual-decision, excluded, or unknown paths are staged for the UDS analysis
delivery.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import build_uds_analysis_delivery_manifest as manifest
from run_pcg_bookmark_visual_qa import PROJECT_ROOT


REPORT_DIR = PROJECT_ROOT / "Saved" / "UDS_Analysis"
DEFAULT_REPORT_PATH = REPORT_DIR / "uds_analysis_staging_scope.json"


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
    if path in manifest.STAGE_EXACT or any(path.startswith(prefix) for prefix in manifest.STAGE_PREFIXES):
        return "allowed_stage_candidate", "Path is part of the intended UDS analysis delivery scope."

    if path in manifest.MANUAL_EXACT:
        return "manual_decision_staged", manifest.MANUAL_EXACT[path]

    for prefix, reason in manifest.EXCLUDED_PREFIXES.items():
        if path.startswith(prefix):
            return "excluded_staged", reason

    return "unknown_staged", "Path is not in the known UDS analysis delivery scope."


def _branch_name(branch_stdout: str) -> str:
    first_line = branch_stdout.splitlines()[0] if branch_stdout.splitlines() else ""
    if first_line.startswith("## "):
        return first_line[3:].split("...", 1)[0].strip()
    return ""


def _dedupe(paths: list[str]) -> list[str]:
    return sorted(set(paths))


def _classify_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = []
    for entry in entries:
        path = str(entry.get("path", ""))
        classification, reason = _classify_path(path)
        record = dict(entry)
        record["classification"] = classification
        record["reason"] = reason
        classified.append(record)
    return classified


def _summary(classified_entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, list[dict[str, Any]]] = {}
    for entry in classified_entries:
        by_class.setdefault(str(entry.get("classification")), []).append(entry)

    return {
        "staged_count": len(classified_entries),
        "allowed_stage_candidate_count": len(by_class.get("allowed_stage_candidate", [])),
        "manual_decision_staged_count": len(by_class.get("manual_decision_staged", [])),
        "excluded_staged_count": len(by_class.get("excluded_staged", [])),
        "unknown_staged_count": len(by_class.get("unknown_staged", [])),
        "allowed_stage_candidate_paths": _dedupe(
            [str(entry.get("path")) for entry in by_class.get("allowed_stage_candidate", [])]
        ),
        "manual_decision_staged_paths": _dedupe(
            [str(entry.get("path")) for entry in by_class.get("manual_decision_staged", [])]
        ),
        "excluded_staged_paths": _dedupe(
            [str(entry.get("path")) for entry in by_class.get("excluded_staged", [])]
        ),
        "unknown_staged_paths": _dedupe(
            [str(entry.get("path")) for entry in by_class.get("unknown_staged", [])]
        ),
    }


def _expected_candidate_paths_from_worktree() -> list[str]:
    project_status = _run_command(["git", "status", "--porcelain=v1", "-uall"], PROJECT_ROOT)
    if not project_status.get("success"):
        return []

    raw_entries = manifest._parse_status(str(project_status.get("stdout", "")))
    classified_entries = [manifest._classify_entry(entry) for entry in raw_entries]
    summary = manifest._build_summary(classified_entries)
    return list(summary.get("stage_candidate_paths", []) or [])


def _validation(
    branch: str,
    staged_status: dict[str, Any],
    cached_diff_check: dict[str, Any],
    summary: dict[str, Any],
    expected_candidate_paths: list[str],
    args: argparse.Namespace,
) -> dict[str, Any]:
    staged_paths = set(summary.get("allowed_stage_candidate_paths", []) or [])
    missing_candidates = sorted(set(expected_candidate_paths) - staged_paths)
    return {
        "on_expected_branch": branch == manifest.EXPECTED_BRANCH,
        "staged_status_read": bool(staged_status.get("success")),
        "cached_diff_check_pass": bool(cached_diff_check.get("success")),
        "no_manual_decision_staged": args.allow_manual_decisions
        or int(summary.get("manual_decision_staged_count", -1)) == 0,
        "no_excluded_staged": int(summary.get("excluded_staged_count", -1)) == 0,
        "no_unknown_staged": int(summary.get("unknown_staged_count", -1)) == 0,
        "has_staged_paths_if_required": (not args.require_staged) or int(summary.get("staged_count", 0)) > 0,
        "all_candidates_staged_if_required": (not args.require_all_candidates) or not missing_candidates,
    }


def _warnings(summary: dict[str, Any], expected_candidate_paths: list[str], args: argparse.Namespace) -> list[str]:
    warnings = []
    if int(summary.get("staged_count", 0)) == 0:
        warnings.append("No staged paths were found. This is fine before staging; use --require-staged after staging.")

    staged_paths = set(summary.get("allowed_stage_candidate_paths", []) or [])
    missing_candidates = sorted(set(expected_candidate_paths) - staged_paths)
    if missing_candidates and not args.require_all_candidates:
        warnings.append(
            f"{len(missing_candidates)} current stage candidate path(s) are not staged. "
            "Use --require-all-candidates for a strict post-staging check."
        )
    return warnings


def run(args: argparse.Namespace) -> dict[str, Any]:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else DEFAULT_REPORT_PATH
    if args.timestamped_output:
        output_path = REPORT_DIR / f"uds_analysis_staging_scope_{timestamp}.json"

    branch_status = _run_command(["git", "status", "--short", "--branch"], PROJECT_ROOT)
    staged_status = _run_command(["git", "diff", "--cached", "--name-status"], PROJECT_ROOT)
    cached_diff_check = _run_command(["git", "diff", "--cached", "--check"], PROJECT_ROOT)
    branch = _branch_name(str(branch_status.get("stdout", "")))

    raw_entries = _parse_name_status(str(staged_status.get("stdout", "")))
    classified_entries = _classify_entries(raw_entries)
    summary = _summary(classified_entries)
    expected_candidate_paths = _expected_candidate_paths_from_worktree()
    staged_paths = set(summary.get("allowed_stage_candidate_paths", []) or [])
    missing_candidates = sorted(set(expected_candidate_paths) - staged_paths)
    validation = _validation(
        branch,
        staged_status,
        cached_diff_check,
        summary,
        expected_candidate_paths,
        args,
    )

    report = {
        "schema": "uds_analysis_staging_scope_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only staged Git scope check. Does not stage, unstage, commit, or modify Unreal assets.",
        "project_root": str(PROJECT_ROOT),
        "expected_branch": manifest.EXPECTED_BRANCH,
        "current_branch": branch,
        "staged_entries": classified_entries,
        "summary": summary,
        "expected_stage_candidate_count": len(expected_candidate_paths),
        "missing_stage_candidate_count": len(missing_candidates),
        "missing_stage_candidate_paths": missing_candidates,
        "git_checks": {
            "branch_status": branch_status,
            "staged_status": staged_status,
            "cached_diff_check": cached_diff_check,
        },
        "validation": validation,
        "warnings": _warnings(summary, expected_candidate_paths, args),
        "pass": all(bool(value) for value in validation.values()),
        "report_path": str(output_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _console_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {}) or {}
    return {
        "pass": bool(report.get("pass")),
        "report_path": report.get("report_path"),
        "current_branch": report.get("current_branch"),
        "summary": {
            "staged_count": summary.get("staged_count"),
            "allowed_stage_candidate_count": summary.get("allowed_stage_candidate_count"),
            "manual_decision_staged_count": summary.get("manual_decision_staged_count"),
            "excluded_staged_count": summary.get("excluded_staged_count"),
            "unknown_staged_count": summary.get("unknown_staged_count"),
            "missing_stage_candidate_count": report.get("missing_stage_candidate_count"),
        },
        "validation": report.get("validation", {}),
        "warnings": report.get("warnings", []),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check staged paths for the UDS analysis delivery.")
    parser.add_argument("--output", default="")
    parser.add_argument("--timestamped-output", action="store_true")
    parser.add_argument("--require-staged", action="store_true")
    parser.add_argument("--require-all-candidates", action="store_true")
    parser.add_argument(
        "--allow-manual-decisions",
        action="store_true",
        help="Allow staged paths that are classified as explicit manual decisions.",
    )
    parser.add_argument(
        "--full-json",
        action="store_true",
        help="Print the full staging-scope JSON to stdout. The report file is always full JSON.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_args()
    staging_scope = run(parsed_args)
    stdout_payload = staging_scope if parsed_args.full_json else _console_summary(staging_scope)
    print(json.dumps(stdout_payload, indent=2, ensure_ascii=False))
    if not staging_scope.get("pass"):
        sys.exit(1)
