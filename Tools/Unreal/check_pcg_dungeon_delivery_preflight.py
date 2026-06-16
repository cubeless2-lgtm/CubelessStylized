"""Run a local delivery preflight for the Cubeless PCG dungeon work.

This tool is intentionally local/read-only for Unreal assets. It validates the
Python files, current Git scope, delivery manifest coverage, latest gate
reports, asset manifest audit, and preset archive summaries, then writes one
summary report under Saved/MCP_Dungeon.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import py_compile
import re
import subprocess
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIBLING_MCP_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless"
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_DeliveryPreflight.json"
CONTENT_ROOT = PROJECT_ROOT / "Content" / "Cubeless" / "PCG" / "Dungeon"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "pcg-dungeon-delivery-manifest.md"
LOG_DIR = PROJECT_ROOT / "Saved" / "Logs"

PYTHON_FILES = [
    PROJECT_ROOT / "Plugins" / "CustomTools" / "Content" / "Python" / "ArtScripts" / "CubelessDungeonPCG.py",
    PROJECT_ROOT / "Plugins" / "CustomTools" / "Content" / "Python" / "ArtScripts" / "CubelessDungeonPCGEntrypoint.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "audit_pcg_dungeon_asset_manifest.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "check_pcg_dungeon_delivery_preflight.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "check_pcg_dungeon_handoff_readiness.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "check_pcg_dungeon_live_dirty_state.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "run_pcg_dungeon_delivery_closeout.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "run_pcg_dungeon_authoring_preset_matrix.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "run_pcg_dungeon_generation_visual_gate_qa.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "run_pcg_dungeon_native_evidence_refresh.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "run_pcg_screenshot_visual_qa.py",
    PROJECT_ROOT / "Tools" / "Unreal" / "run_pcg_bookmark_visual_qa.py",
]

EXPECTED_GIT_PATH_PREFIXES = [
    "Content/Cubeless/PCG/Dungeon/",
    "Plugins/CustomTools/Content/Python/ArtScripts/CubelessDungeonPCG.py",
    "Plugins/CustomTools/Content/Python/ArtScripts/CubelessDungeonPCGEntrypoint.py",
    "Tools/Unreal/audit_pcg_dungeon_asset_manifest.py",
    "Tools/Unreal/check_pcg_dungeon_delivery_preflight.py",
    "Tools/Unreal/check_pcg_dungeon_handoff_readiness.py",
    "Tools/Unreal/check_pcg_dungeon_live_dirty_state.py",
    "Tools/Unreal/run_pcg_dungeon_delivery_closeout.py",
    "Tools/Unreal/run_pcg_dungeon_authoring_preset_matrix.py",
    "Tools/Unreal/run_pcg_dungeon_generation_visual_gate_qa.py",
    "Tools/Unreal/run_pcg_dungeon_native_evidence_refresh.py",
    "docs/pcg-dungeon-delivery-manifest.md",
    "docs/pcg-dungeon-mvp.md",
    "docs/pcg-dungeon-operator-guide.md",
    "docs/pcg-dungeon-v2-roadmap.md",
    "docs/pcg-dungeon-review-checklist.md",
    "docs/work-log.md",
]

ARCHIVE_LABELS = [
    "wide_looped_postprocess",
    "compact_branching_postprocess",
    "open_cutaway_postprocess",
    "default_restored_after_postprocess_preset_suite",
    "small_route_v1qa",
    "long_route_v1qa",
    "loop_dense_v1qa",
    "boss_focus_v1qa",
    "default_restored_after_v1qa_preset_expansion",
]

LOG_ERROR_PATTERNS = [
    "Fatal error",
    "Assertion failed",
    "Unhandled Exception",
    "Ensure condition failed",
    "LogPython: Error",
    "LogPCG: Error",
    "LogLinker: Error",
    " Error:",
]
LOG_TIMESTAMP_RE = re.compile(
    r"^\[(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})-"
    r"(?P<hour>\d{2})\.(?P<minute>\d{2})\.(?P<second>\d{2}):(?P<millis>\d{3})\]"
)


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_from_mtime(path: Path) -> dt.datetime:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)


def _parse_unreal_log_timestamp(line: str) -> dt.datetime | None:
    match = LOG_TIMESTAMP_RE.match(line)
    if not match:
        return None
    parts = {key: int(value) for key, value in match.groupdict().items()}
    return dt.datetime(
        parts["year"],
        parts["month"],
        parts["day"],
        parts["hour"],
        parts["minute"],
        parts["second"],
        parts["millis"] * 1000,
        tzinfo=dt.timezone.utc,
    )


def _run_command(args: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": args,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "success": completed.returncode == 0,
    }


def _compile_python() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in PYTHON_FILES:
        entry: dict[str, Any] = {
            "path": _relative(path),
            "exists": path.exists(),
            "compiled": False,
            "error": None,
        }
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
                entry["compiled"] = True
            except py_compile.PyCompileError as exc:
                entry["error"] = str(exc)
        entries.append(entry)
    return {
        "pass": all(item["exists"] and item["compiled"] for item in entries),
        "entries": entries,
    }


def _parse_git_status(stdout: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        entries.append({"status": status, "path": path.replace("\\", "/")})
    return entries


def _is_expected_path(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in EXPECTED_GIT_PATH_PREFIXES)


def _git_scope() -> dict[str, Any]:
    project = _run_command(["git", "status", "--porcelain=v1"], PROJECT_ROOT)
    project_entries = _parse_git_status(project["stdout"])
    unexpected = [entry for entry in project_entries if not _is_expected_path(entry["path"])]

    sibling = _run_command(["git", "status", "--porcelain=v1"], SIBLING_MCP_ROOT)
    sibling_entries = _parse_git_status(sibling["stdout"]) if sibling["success"] else []

    return {
        "project_status_command": project,
        "project_entries": project_entries,
        "expected_path_prefixes": EXPECTED_GIT_PATH_PREFIXES,
        "unexpected_entries": unexpected,
        "project_scope_pass": project["success"] and not unexpected,
        "sibling_status_command": sibling,
        "sibling_entries": sibling_entries,
        "sibling_clean": sibling["success"] and not sibling_entries,
        "pass": project["success"] and not unexpected and sibling["success"] and not sibling_entries,
    }


def _git_binary_asset_attributes() -> dict[str, Any]:
    asset_paths = [
        _relative(path)
        for path in sorted(CONTENT_ROOT.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".uasset", ".umap"}
    ]
    if not asset_paths:
        return {
            "pass": False,
            "asset_count": 0,
            "entries": [],
            "failures": [{"reason": "no_unreal_binary_assets_found"}],
        }

    command = ["git", "check-attr", "filter", "merge", "diff", "text", "--", *asset_paths]
    result = _run_command(command, PROJECT_ROOT)
    attributes_by_path: dict[str, dict[str, str]] = {path: {} for path in asset_paths}
    for line in result["stdout"].splitlines():
        parts = line.split(": ", 2)
        if len(parts) != 3:
            continue
        path, attribute, value = parts
        attributes_by_path.setdefault(path.replace("\\", "/"), {})[attribute] = value

    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for path in asset_paths:
        attrs = attributes_by_path.get(path, {})
        expected = {
            "filter": "lfs",
            "merge": "lfs",
            "diff": "lfs",
            "text": "unset",
        }
        pass_value = all(attrs.get(key) == value for key, value in expected.items())
        entry = {
            "path": path,
            "attributes": attrs,
            "pass": pass_value,
        }
        entries.append(entry)
        if not pass_value:
            failures.append(entry)

    return {
        "pass": result["success"] and not failures,
        "command": result,
        "asset_count": len(asset_paths),
        "entries": entries,
        "failure_count": len(failures),
        "failures": failures,
    }


def _manifest_coverage() -> dict[str, Any]:
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8") if MANIFEST_PATH.exists() else ""
    asset_paths = [
        _relative(path)
        for path in sorted(CONTENT_ROOT.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".uasset", ".umap"}
    ]
    missing_assets = [path for path in asset_paths if path not in manifest_text]
    expected_scope_missing = [path for path in EXPECTED_GIT_PATH_PREFIXES if path not in manifest_text and path != "docs/work-log.md"]
    return {
        "manifest_path": _relative(MANIFEST_PATH),
        "manifest_exists": MANIFEST_PATH.exists(),
        "asset_count": len(asset_paths),
        "missing_assets": missing_assets,
        "expected_scope_missing": expected_scope_missing,
        "pass": MANIFEST_PATH.exists() and not missing_assets and not expected_scope_missing,
    }


def _latest_gate_reports() -> dict[str, Any]:
    summary_path = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_PCGGeneration_VisualGateQA_Report.json"
    final_path = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_PCGGeneration_FinalGate.json"
    summary = _read_json(summary_path)
    final = _read_json(final_path)
    final_checks = final.get("checks", {})
    failed_checks = [key for key, value in final_checks.items() if value is False]
    return {
        "summary_path": str(summary_path),
        "final_gate_path": str(final_path),
        "summary_success": bool(summary.get("success")),
        "summary_preset": summary.get("refresh", {}).get("preset_name"),
        "summary_archive_pass": bool(summary.get("archive", {}).get("pass")),
        "summary_components": summary.get("final_gate", {}).get("native_components"),
        "summary_instances": summary.get("final_gate", {}).get("native_instances"),
        "summary_dirty": summary.get("final_gate", {}).get("dirty_count"),
        "final_pass": bool(final.get("pass")),
        "final_status": final.get("status"),
        "failed_checks": failed_checks,
        "final_components": final.get("live_native_output", {}).get("component_summary", {}).get("component_count"),
        "final_instances": final.get("live_native_output", {}).get("component_summary", {}).get("instance_count_total"),
        "final_dirty": final.get("live_dirty_packages", {}).get("count"),
        "seed_suite_pass": bool(final.get("seed_suite", {}).get("pass")),
        "top_screenshot_fresh": bool(final_checks.get("top_screenshot_after_generation_refresh")),
        "oblique_screenshot_fresh": bool(final_checks.get("oblique_screenshot_after_generation_refresh")),
        "pass": bool(summary.get("success"))
        and bool(final.get("pass"))
        and not failed_checks
        and final.get("live_dirty_packages", {}).get("count") == 0,
    }


def _asset_manifest_audit() -> dict[str, Any]:
    path = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_AssetManifestAudit.json"
    report = _read_json(path)
    unreal_audit = report.get("unreal_audit", {})
    return {
        "path": str(path),
        "pass": bool(report.get("pass")),
        "expected_asset_count": report.get("expected_asset_count"),
        "registry_count": unreal_audit.get("registry_count"),
        "loaded_count": unreal_audit.get("loaded_count"),
        "redirector_count": unreal_audit.get("redirector_count"),
        "load_failure_count": unreal_audit.get("load_failure_count"),
        "missing_from_registry_count": len(unreal_audit.get("missing_from_registry", [])),
        "class_counts": unreal_audit.get("class_counts", {}),
    }


def _live_dirty_state() -> dict[str, Any]:
    path = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_LiveDirtyState.json"
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "pass": False,
            "reason": "Run Tools/Unreal/check_pcg_dungeon_live_dirty_state.py before delivery preflight.",
        }
    report = _read_json(path)
    dirty_state = report.get("dirty_state", {})
    return {
        "path": str(path),
        "exists": True,
        "pass": bool(report.get("pass") and dirty_state.get("pass")),
        "timestamp": report.get("timestamp"),
        "dirty_content_count": dirty_state.get("dirty_content_count"),
        "dirty_map_count": dirty_state.get("dirty_map_count"),
        "dirty_total_count": dirty_state.get("dirty_total_count"),
        "dirty_content_packages": dirty_state.get("dirty_content_packages", []),
        "dirty_map_packages": dirty_state.get("dirty_map_packages", []),
    }


def _preset_archives() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for label in ARCHIVE_LABELS:
        path = (
            PROJECT_ROOT
            / "Saved"
            / "MCP_Dungeon"
            / "PresetQA"
            / label
            / f"{label}_CubelessDungeonMVP_PCGGeneration_VisualGateQA_Report.json"
        )
        entry: dict[str, Any] = {"label": label, "path": str(path), "exists": path.exists()}
        if path.exists():
            report = _read_json(path)
            entry.update(
                {
                    "success": bool(report.get("success")),
                    "preset": report.get("refresh", {}).get("preset_name"),
                    "archive_pass": bool(report.get("archive", {}).get("pass")),
                    "exposure_review_pass": bool(report.get("exposure_review_pass")),
                    "native_components": report.get("final_gate", {}).get("native_components"),
                    "native_instances": report.get("final_gate", {}).get("native_instances"),
                    "failed_check_count": len(report.get("final_gate", {}).get("failed_checks", [])),
                    "dirty_count": report.get("final_gate", {}).get("dirty_count"),
                }
            )
            entry["pass"] = bool(
                entry["success"]
                and entry["archive_pass"]
                and entry["exposure_review_pass"]
                and entry["failed_check_count"] == 0
                and entry["dirty_count"] == 0
            )
        else:
            entry["pass"] = False
        entries.append(entry)
    return {"pass": all(entry.get("pass") for entry in entries), "entries": entries}


def _authoring_preset_matrix() -> dict[str, Any]:
    base = PROJECT_ROOT / "Saved" / "MCP_Dungeon"
    runner_path = base / "CubelessDungeonMVP_AuthoringPresetMatrixRunner_Report.json"
    matrix_path = base / "CubelessDungeonMVP_AuthoringPresetMatrix_Report.json"
    runner = _read_json(runner_path)
    matrix = _read_json(matrix_path)
    return {
        "runner_path": str(runner_path),
        "matrix_path": str(matrix_path),
        "runner_exists": runner_path.exists(),
        "matrix_exists": matrix_path.exists(),
        "runner_pass": bool(runner.get("pass")),
        "matrix_pass": bool(matrix.get("pass")),
        "preset_count": matrix.get("preset_count"),
        "seed_count": matrix.get("seed_count"),
        "failures": matrix.get("failures", []),
        "missing_presets": matrix.get("missing_presets", []),
        "pass": bool(
            runner_path.exists()
            and matrix_path.exists()
            and runner.get("pass")
            and matrix.get("pass")
            and not matrix.get("failures")
            and not matrix.get("missing_presets")
        ),
    }


def _nested_dict(source: dict[str, Any], *keys: str) -> dict[str, Any]:
    value: Any = source
    for key in keys:
        if not isinstance(value, dict):
            return {}
        value = value.get(key)
    return value if isinstance(value, dict) else {}


def _native_evidence_refresh() -> dict[str, Any]:
    base = PROJECT_ROOT / "Saved" / "MCP_Dungeon"
    final_gate_path = base / "CubelessDungeonMVP_PCGGeneration_FinalGate.json"
    summary_path = base / "CubelessDungeonMVP_NativeEvidenceRefresh_Report.json"
    primary_path = base / "CubelessDungeonMVP_NativePrimaryRefresh_Report.json"
    smoke_path = base / "CubelessDungeonMVP_NativeIntegrationTest_Report.json"
    preview_path = base / "CubelessDungeonMVP_NativeIntegrationPreview_Report.json"
    primary_gate_path = base / "CubelessDungeonMVP_NativePrimaryRefresh_FinalGate.json"

    final_gate = _read_json(final_gate_path)
    expected_summary = _nested_dict(final_gate, "live_native_output", "component_summary")
    expected_components = expected_summary.get("component_count")
    expected_instances = expected_summary.get("instance_count_total")

    def read_optional(path: Path) -> dict[str, Any]:
        return _read_json(path) if path.exists() else {}

    summary = read_optional(summary_path)
    primary = read_optional(primary_path)
    smoke = read_optional(smoke_path)
    preview = read_optional(preview_path)
    primary_gate = read_optional(primary_gate_path)

    primary_counts = _nested_dict(primary, "native_output_verify", "generation_verification", "component_summary")
    smoke_counts = _nested_dict(smoke, "generation_verification", "component_summary")
    preview_counts = _nested_dict(preview, "generation_verification", "component_summary")
    smoke_cleanup = _nested_dict(smoke, "cleanup_verification")
    preview_screenshot = _nested_dict(preview, "screenshot", "side_by_side")
    primary_gate_counts = _nested_dict(primary_gate, "live_native_output", "component_summary")

    entries = {
        "summary": {
            "path": str(summary_path),
            "exists": summary_path.exists(),
            "success": bool(summary.get("success")) if summary else None,
            "timestamp": summary.get("timestamp"),
            "mode": summary.get("mode"),
            "active_gate_components": summary.get("active_gate", {}).get("native_components") if summary else None,
            "active_gate_instances": summary.get("active_gate", {}).get("native_instances") if summary else None,
            "failed_checks": [
                key for key, value in summary.get("checks", {}).items() if value is False
            ]
            if summary
            else [],
        },
        "primary_refresh": {
            "path": str(primary_path),
            "exists": primary_path.exists(),
            "pass": bool(primary.get("pass")),
            "status": primary.get("status"),
            "native_components": primary_counts.get("component_count"),
            "native_instances": primary_counts.get("instance_count_total"),
            "screenshot_qa_pass": bool(primary.get("checks", {}).get("screenshot_qa_pass")),
            "smoke_test_pass": bool(primary.get("checks", {}).get("smoke_test_pass")),
            "dirty_after_count": primary.get("dirty_after_count"),
        },
        "smoke_test": {
            "path": str(smoke_path),
            "exists": smoke_path.exists(),
            "pass": bool(smoke.get("pass")),
            "status": smoke.get("status"),
            "native_components": smoke_counts.get("component_count"),
            "native_instances": smoke_counts.get("instance_count_total"),
            "cleanup_residual_components": smoke_cleanup.get("residual_static_mesh_component_count"),
            "cleanup_residual_instances": smoke_cleanup.get("residual_static_mesh_instance_count"),
        },
        "preview": {
            "path": str(preview_path),
            "exists": preview_path.exists(),
            "pass": bool(preview.get("pass")),
            "status": preview.get("status"),
            "native_components": preview_counts.get("component_count"),
            "native_instances": preview_counts.get("instance_count_total"),
            "side_by_side_screenshot_qa_pass": bool(preview.get("checks", {}).get("side_by_side_screenshot_qa_pass")),
            "side_by_side_screenshot_path": preview_screenshot.get("screenshot_path"),
        },
        "primary_final_gate_context": {
            "path": str(primary_gate_path),
            "exists": primary_gate_path.exists(),
            "pass": bool(primary_gate.get("pass")) if primary_gate else None,
            "status": primary_gate.get("status"),
            "native_components": primary_gate_counts.get("component_count"),
            "native_instances": primary_gate_counts.get("instance_count_total"),
            "dirty_count": primary_gate.get("live_dirty_packages", {}).get("count") if primary_gate else None,
        },
    }
    checks = {
        "expected_counts_available": expected_components is not None and expected_instances is not None,
        "summary_exists": summary_path.exists(),
        "summary_success": bool(summary.get("success")),
        "summary_count_match": summary.get("active_gate", {}).get("native_components") == expected_components
        and summary.get("active_gate", {}).get("native_instances") == expected_instances,
        "summary_checks_pass": bool(summary.get("checks"))
        and all(bool(value) for value in summary.get("checks", {}).values()),
        "primary_refresh_exists": primary_path.exists(),
        "primary_refresh_pass": bool(primary.get("pass")),
        "primary_count_match": primary_counts.get("component_count") == expected_components
        and primary_counts.get("instance_count_total") == expected_instances,
        "primary_screenshot_qa_pass": bool(primary.get("checks", {}).get("screenshot_qa_pass")),
        "primary_smoke_embedded_pass": bool(primary.get("checks", {}).get("smoke_test_pass")),
        "smoke_exists": smoke_path.exists(),
        "smoke_pass": bool(smoke.get("pass")),
        "smoke_count_match": smoke_counts.get("component_count") == expected_components
        and smoke_counts.get("instance_count_total") == expected_instances,
        "smoke_cleanup_zero": smoke_cleanup.get("residual_static_mesh_component_count") == 0
        and smoke_cleanup.get("residual_static_mesh_instance_count") == 0,
        "preview_exists": preview_path.exists(),
        "preview_pass": bool(preview.get("pass")),
        "preview_count_match": preview_counts.get("component_count") == expected_components
        and preview_counts.get("instance_count_total") == expected_instances,
        "preview_side_by_side_screenshot_pass": bool(preview.get("checks", {}).get("side_by_side_screenshot_qa_pass")),
    }
    return {
        "pass": all(checks.values()),
        "policy": (
            "PCG-only native evidence freshness check. Primary final gate is recorded as context only because that older gate "
            "also reads gameplay placeholder reports outside the current PCG-generation delivery scope."
        ),
        "expected_native_components": expected_components,
        "expected_native_instances": expected_instances,
        "checks": checks,
        "entries": entries,
    }


def _handoff_readiness() -> dict[str, Any]:
    path = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_HandoffReadiness.json"
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "pass": False,
            "reason": "Run Tools/Unreal/check_pcg_dungeon_handoff_readiness.py before delivery preflight.",
        }
    report = _read_json(path)
    checks = report.get("checks", {}) if isinstance(report.get("checks"), dict) else {}
    return {
        "path": str(path),
        "exists": True,
        "pass": bool(report.get("pass") and checks and all(bool(value) for value in checks.values())),
        "timestamp": report.get("timestamp"),
        "expected": report.get("expected", {}),
        "summary": report.get("summary", {}),
        "failed_checks": report.get("failed_checks", []),
    }


def _latest_editor_log_health() -> dict[str, Any]:
    evidence_paths = [
        PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_PCGGeneration_FinalGate.json",
        PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_PCGGeneration_VisualGateQA_Report.json",
        PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_AssetManifestAudit.json",
    ]
    existing_evidence = [path for path in evidence_paths if path.exists()]
    checkpoint_utc = max((_utc_from_mtime(path) for path in existing_evidence), default=None)
    latest_logs = sorted(LOG_DIR.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    latest_log = latest_logs[0] if latest_logs else None
    if not latest_log:
        return {
            "pass": False,
            "reason": "no_log_file_found",
            "log_dir": str(LOG_DIR),
            "checkpoint_utc": checkpoint_utc.isoformat() if checkpoint_utc else None,
        }

    matches: list[dict[str, Any]] = []
    current_timestamp: dt.datetime | None = None
    with latest_log.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            parsed_timestamp = _parse_unreal_log_timestamp(line)
            if parsed_timestamp:
                current_timestamp = parsed_timestamp
            if not any(pattern in line for pattern in LOG_ERROR_PATTERNS):
                continue
            matches.append(
                {
                    "line": line_number,
                    "timestamp_utc": current_timestamp.isoformat() if current_timestamp else None,
                    "text": line.strip()[:1000],
                }
            )

    blocking_matches = []
    if checkpoint_utc:
        blocking_matches = [
            item
            for item in matches
            if item.get("timestamp_utc") and dt.datetime.fromisoformat(str(item["timestamp_utc"])) > checkpoint_utc
        ]
    latest_prior_match = None
    prior_matches = matches
    if checkpoint_utc:
        prior_matches = [
            item
            for item in matches
            if not item.get("timestamp_utc") or dt.datetime.fromisoformat(str(item["timestamp_utc"])) <= checkpoint_utc
        ]
    if prior_matches:
        latest_prior_match = prior_matches[-1]

    return {
        "pass": bool(checkpoint_utc and not blocking_matches),
        "policy": "Only errors after the latest delivery evidence checkpoint block the preflight; older matches are recorded for context.",
        "log_path": str(latest_log),
        "log_modified_utc": _utc_from_mtime(latest_log).isoformat(),
        "checkpoint_utc": checkpoint_utc.isoformat() if checkpoint_utc else None,
        "checked_patterns": LOG_ERROR_PATTERNS,
        "total_match_count": len(matches),
        "blocking_match_count": len(blocking_matches),
        "blocking_matches": blocking_matches[-20:],
        "latest_prior_match": latest_prior_match,
    }


def run(_args: argparse.Namespace) -> dict[str, Any]:
    sections = {
        "python_compile": _compile_python(),
        "git_scope": _git_scope(),
        "git_binary_asset_attributes": _git_binary_asset_attributes(),
        "manifest_coverage": _manifest_coverage(),
        "latest_gate_reports": _latest_gate_reports(),
        "asset_manifest_audit": _asset_manifest_audit(),
        "live_dirty_state": _live_dirty_state(),
        "preset_archives": _preset_archives(),
        "authoring_preset_matrix": _authoring_preset_matrix(),
        "native_evidence_refresh": _native_evidence_refresh(),
        "handoff_readiness": _handoff_readiness(),
        "latest_editor_log_health": _latest_editor_log_health(),
    }
    report = {
        "schema": "cubeless_pcg_dungeon_delivery_preflight_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Local delivery preflight only. Does not stage, commit, push, modify Unreal assets, or run generation.",
        "sections": sections,
        "pass": all(section.get("pass") for section in sections.values()),
        "report_path": str(REPORT_PATH),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local PCG dungeon delivery preflight checks.")
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
