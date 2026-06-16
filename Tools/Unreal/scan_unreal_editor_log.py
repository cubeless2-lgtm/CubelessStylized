#!/usr/bin/env python3
"""Scan the latest Unreal editor log for errors and fatal entries.

The scanner is read-only and intentionally conservative: normal historical
`Error:` lines are reported as warnings for human review, while fatal/crash
signals fail the scan.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

from run_pcg_bookmark_visual_qa import PROJECT_ROOT


REPORT_DIR = PROJECT_ROOT / "Saved" / "UDS_Analysis"
DEFAULT_REPORT_PATH = REPORT_DIR / "unreal_editor_log_scan.json"
DEFAULT_LOG_DIR = PROJECT_ROOT / "Saved" / "Logs"
DEFAULT_LOG_PATTERN = "StylizedCubeless*.log"

TIMESTAMP_RE = re.compile(r"^\[(?P<timestamp>\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\]")

FATAL_PATTERNS = (
    "Fatal:",
    "LogOutputDevice: Error:",
    "Critical error:",
    "Unhandled Exception:",
    "Assertion failed:",
)
ENSURE_PATTERNS = (
    "Ensure condition failed",
    "ensure condition failed",
)


def _latest_log(log_dir: Path, pattern: str) -> Path | None:
    candidates = [path for path in log_dir.glob(pattern) if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _trimmed_entry(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return entries[-limit:]


def _line_timestamp(line: str) -> str:
    match = TIMESTAMP_RE.match(line)
    return match.group("timestamp") if match else ""


def _classify_line(line: str) -> str | None:
    if any(pattern in line for pattern in FATAL_PATTERNS):
        return "fatal"
    if any(pattern in line for pattern in ENSURE_PATTERNS):
        return "ensure"
    if ": Warning:" in line:
        return "warning"
    if ": Error:" in line:
        return "error"
    return None


def _scan_log(log_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    counts = {
        "fatal": 0,
        "ensure": 0,
        "error": 0,
        "warning": 0,
    }
    entries = {
        "fatal": [],
        "ensure": [],
        "error": [],
        "warning": [],
    }
    line_count = 0

    with log_path.open("r", encoding=args.encoding, errors="replace") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line_count = line_number
            line = raw_line.rstrip("\r\n")
            severity = _classify_line(line)
            if not severity:
                continue
            counts[severity] += 1
            entries[severity].append(
                {
                    "line_number": line_number,
                    "timestamp": _line_timestamp(line),
                    "line": line[: args.max_line_chars],
                }
            )

    latest_entries = {
        "fatal": _trimmed_entry(entries["fatal"], args.max_fatal_entries),
        "ensure": _trimmed_entry(entries["ensure"], args.max_ensure_entries),
        "error": _trimmed_entry(entries["error"], args.max_error_entries),
        "warning": _trimmed_entry(entries["warning"], args.max_warning_entries),
    }
    fatal_like_count = counts["fatal"]
    return {
        "success": True,
        "log_path": str(log_path),
        "log_size_bytes": log_path.stat().st_size,
        "log_last_write_time": time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(log_path.stat().st_mtime),
        ),
        "line_count": line_count,
        "counts": counts,
        "latest_entries": latest_entries,
        "fatal_like_count": fatal_like_count,
        "pass": fatal_like_count == 0,
    }


def _warnings(scan: dict[str, Any]) -> list[str]:
    warnings = []
    counts = scan.get("counts", {})
    if int(counts.get("error", 0) or 0) > 0:
        warnings.append(
            f"Latest Unreal log contains {counts.get('error')} Error line(s); review latest_entries.error."
        )
    if int(counts.get("ensure", 0) or 0) > 0:
        warnings.append(
            f"Latest Unreal log contains {counts.get('ensure')} ensure line(s); review latest_entries.ensure."
        )
    if int(counts.get("warning", 0) or 0) > 0:
        warnings.append(
            f"Latest Unreal log contains {counts.get('warning')} Warning line(s); review latest_entries.warning."
        )
    return warnings


def run(args: argparse.Namespace) -> dict[str, Any]:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else DEFAULT_REPORT_PATH
    if args.timestamped_output:
        output_path = REPORT_DIR / f"unreal_editor_log_scan_{timestamp}.json"

    log_dir = Path(args.log_dir)
    log_path = Path(args.log_path) if args.log_path else _latest_log(log_dir, args.log_pattern)
    if not log_path:
        scan = {
            "success": False,
            "pass": False,
            "log_dir": str(log_dir),
            "log_pattern": args.log_pattern,
            "error": "No Unreal editor log found.",
        }
    else:
        scan = _scan_log(log_path, args)

    report = {
        "schema": "unreal_editor_log_scan_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only Unreal editor log scan. Does not save or modify Unreal assets.",
        "scan": scan,
        "warnings": _warnings(scan) if scan.get("success") else [],
        "pass": bool(scan.get("pass")),
        "report_path": str(output_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan the latest Unreal editor log.")
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--log-pattern", default=DEFAULT_LOG_PATTERN)
    parser.add_argument("--log-path", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--timestamped-output", action="store_true")
    parser.add_argument("--encoding", default="utf-8")
    parser.add_argument("--max-line-chars", type=int, default=800)
    parser.add_argument("--max-fatal-entries", type=int, default=25)
    parser.add_argument("--max-ensure-entries", type=int, default=25)
    parser.add_argument("--max-error-entries", type=int, default=50)
    parser.add_argument("--max-warning-entries", type=int, default=25)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
