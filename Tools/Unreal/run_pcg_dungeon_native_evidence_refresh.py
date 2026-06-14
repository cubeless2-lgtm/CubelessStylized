"""Refresh Cubeless PCG dungeon native-primary and preview evidence.

This runner closes stale native evidence after the dungeon point contract
changes. It refreshes the native primary route, native smoke route, and preview
route, then captures the review screenshots used by the handoff docs.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable

from run_pcg_dungeon_generation_visual_gate_qa import (
    DUNGEON_REPORT_DIR,
    UnrealConnection,
    _clear_editor_selection,
    _execute_dungeon_python,
    _screenshot_namespace,
    run_screenshot_qa,
)


PRIMARY_SCREENSHOT_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_NativePrimaryRefresh_ScreenshotQA.json"
PRIMARY_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_NativePrimaryRefresh_Report.json"
PRIMARY_FINAL_GATE_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_NativePrimaryRefresh_FinalGate.json"
PCG_FINAL_GATE_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_PCGGeneration_FinalGate.json"
SMOKE_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_NativeIntegrationTest_Report.json"
PREVIEW_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_NativeIntegrationPreview_Report.json"
PREVIEW_SIDE_BY_SIDE_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_NativePreview_SideBySide_ScreenshotQA.json"
SUMMARY_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_NativeEvidenceRefresh_Report.json"


def _component_summary(report: dict[str, Any], *keys: str) -> dict[str, Any]:
    value: Any = report
    for key in keys:
        if not isinstance(value, dict):
            return {}
        value = value.get(key)
    return value if isinstance(value, dict) else {}


def _compact_primary_begin(unreal: UnrealConnection, keep_existing_output: bool) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        f"""
begin = dungeon.begin_native_primary_output_refresh(keep_existing_output={bool(keep_existing_output)})
print(json.dumps({{
    "success": bool(
        begin.get("status") == "generation_requested"
        and begin.get("dungeon", {{}}).get("pass")
        and begin.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok")
    ),
    "status": begin.get("status"),
    "dungeon_pass": bool(begin.get("dungeon", {{}}).get("pass")),
    "point_source_graph_pass": bool(begin.get("native_point_source_graph", {{}}).get("pass")),
    "integration_graph_pass": bool(begin.get("native_integration_graph", {{}}).get("pass")),
    "integration_audit_pass": bool(begin.get("native_integration_audit", {{}}).get("pass")),
    "output_requested": begin.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok"),
}}, ensure_ascii=False))
""",
    )


def _compact_primary_verify(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
verify = dungeon.verify_native_primary_output_refresh(enable_output_only_review=True, save_dirty_packages=True)
summary = verify.get("native_output_verify", {}).get("generation_verification", {}).get("component_summary", {})
print(json.dumps({
    "success": bool(verify.get("pass")),
    "status": verify.get("status"),
    "failed_checks": [key for key, value in verify.get("checks", {}).items() if not value],
    "native_components": summary.get("component_count"),
    "native_instances": summary.get("instance_count_total"),
    "dirty_after": verify.get("dirty_after_count"),
}, ensure_ascii=False))
""",
    )


def _compact_smoke_begin(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
begin = dungeon.begin_native_integration_smoke_test()
print(json.dumps({
    "success": bool(begin.get("generate_request", {}).get("ok")),
    "status": begin.get("status"),
    "actor_setup_pass": bool(begin.get("actor_setup", {}).get("pass")),
    "generate_request_ok": bool(begin.get("generate_request", {}).get("ok")),
}, ensure_ascii=False))
""",
    )


def _compact_smoke_generation(unreal: UnrealConnection, request_cleanup: bool) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        f"""
verify = dungeon.verify_native_integration_smoke_generation(request_cleanup={bool(request_cleanup)})
summary = verify.get("generation_verification", {{}}).get("component_summary", {{}})
print(json.dumps({{
    "success": bool(verify.get("generation_verification", {{}}).get("pass")),
    "status": verify.get("status"),
    "cleanup_requested": {bool(request_cleanup)},
    "native_components": summary.get("component_count"),
    "native_instances": summary.get("instance_count_total"),
    "cleanup_request_ok": bool(verify.get("cleanup_request", {{}}).get("ok")) if {bool(request_cleanup)} else None,
}}, ensure_ascii=False))
""",
    )


def _compact_smoke_cleanup(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
verify = dungeon.verify_native_integration_smoke_cleanup()
cleanup = verify.get("cleanup_verification", {})
print(json.dumps({
    "success": bool(verify.get("pass")),
    "status": verify.get("status"),
    "cleanup_pass": bool(cleanup.get("pass")),
    "residual_components": cleanup.get("residual_static_mesh_component_count"),
    "residual_instances": cleanup.get("residual_static_mesh_instance_count"),
}, ensure_ascii=False))
""",
    )


def _compact_record_primary_artifacts(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
artifacts = dungeon.record_native_primary_refresh_artifacts()
gate = dungeon.record_native_primary_refresh_final_gate()
summary = gate.get("live_native_output", {}).get("component_summary", {})
print(json.dumps({
    "success": bool(artifacts.get("pass")),
    "artifacts_pass": bool(artifacts.get("pass")),
    "final_gate_pass": bool(gate.get("pass")),
    "final_gate_status": gate.get("status"),
    "failed_checks": [key for key, value in gate.get("checks", {}).items() if not value],
    "native_components": summary.get("component_count"),
    "native_instances": summary.get("instance_count_total"),
    "dirty_count": gate.get("live_dirty_packages", {}).get("count"),
}, ensure_ascii=False))
""",
    )


def _compact_restore_review_mode(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
restore = dungeon.restore_native_output_only_review_mode()
print(json.dumps({
    "success": bool(restore.get("pass")),
    "pass": bool(restore.get("pass")),
    "bridge_visible": restore.get("bridge_after", {}).get("visible_static_mesh_component_count"),
    "preview_visible": restore.get("preview_after", {}).get("visible_static_mesh_component_count"),
}, ensure_ascii=False))
""",
    )


def _compact_preview_begin(unreal: UnrealConnection, keep_existing: bool) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        f"""
begin = dungeon.begin_native_integration_preview(keep_existing={bool(keep_existing)})
print(json.dumps({{
    "success": bool(begin.get("generate_request", {{}}).get("ok")),
    "status": begin.get("status"),
    "point_source_preview_pass": bool(begin.get("preview_graph_setup", {{}}).get("point_source_graph", {{}}).get("pass")),
    "integration_preview_pass": bool(begin.get("preview_graph_setup", {{}}).get("integration_graph", {{}}).get("pass")),
    "generate_request_ok": bool(begin.get("generate_request", {{}}).get("ok")),
}}, ensure_ascii=False))
""",
    )


def _compact_preview_verify(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
verify = dungeon.verify_native_integration_preview_generation()
summary = verify.get("generation_verification", {}).get("component_summary", {})
print(json.dumps({
    "success": bool(verify.get("pass")),
    "status": verify.get("status"),
    "native_components": summary.get("component_count"),
    "native_instances": summary.get("instance_count_total"),
}, ensure_ascii=False))
""",
    )


def _compact_preview_camera(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
camera = dungeon.setup_native_preview_side_by_side_review_camera()
print(json.dumps({
    "success": bool(camera.get("success")),
    "camera": camera,
}, ensure_ascii=False))
""",
    )


def _poll(
    action: Callable[[], dict[str, Any]],
    *,
    timeout_seconds: float,
    poll_seconds: float,
) -> dict[str, Any]:
    started_at = time.monotonic()
    attempts: list[dict[str, Any]] = []
    while True:
        result = action()
        attempts.append(
            {
                "success": bool(result.get("success")),
                "status": result.get("status"),
                "native_components": result.get("native_components"),
                "native_instances": result.get("native_instances"),
                "elapsed_seconds": round(time.monotonic() - started_at, 4),
            }
        )
        if result.get("success") or time.monotonic() - started_at >= timeout_seconds:
            result["attempts"] = attempts
            return result
        time.sleep(max(0.1, poll_seconds))


def _capture_active_viewport(
    *,
    output_prefix: str,
    report_path: Path,
    redraw_count: int,
    clean_game_view: bool,
) -> dict[str, Any]:
    report = run_screenshot_qa(
        _screenshot_namespace(
            output_prefix=output_prefix,
            report_path=report_path,
            redraw_count=redraw_count,
            clean_game_view=clean_game_view,
        )
    )
    capture = (report.get("captures") or [{}])[0]
    return {
        "qa_pass": bool(report.get("qa_pass")),
        "capture_qa_pass": bool(report.get("capture_qa_pass")),
        "report_path": str(report_path),
        "screenshot_path": capture.get("filepath"),
        "file_size": capture.get("file_size"),
        "sha256": capture.get("sha256"),
        "dirty_package_added_count": capture.get("dirty_package_added_count"),
    }


def _embed_preview_screenshot(capture: dict[str, Any]) -> dict[str, Any]:
    preview = json.loads(PREVIEW_REPORT_PATH.read_text(encoding="utf-8"))
    preview.setdefault("screenshot", {})["side_by_side"] = capture
    preview.setdefault("checks", {})["side_by_side_screenshot_qa_pass"] = bool(
        capture.get("qa_pass") and capture.get("capture_qa_pass")
    )
    preview["pass"] = bool(preview.get("pass") and preview["checks"]["side_by_side_screenshot_qa_pass"])
    PREVIEW_REPORT_PATH.write_text(json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "success": bool(preview.get("pass")),
        "preview_pass": bool(preview.get("pass")),
        "side_by_side_screenshot_qa_pass": bool(preview["checks"]["side_by_side_screenshot_qa_pass"]),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    return _read_json(path) if path.exists() else {}


def _screenshot_report_summary(path: Path) -> dict[str, Any]:
    report = _read_json_if_exists(path)
    capture = (report.get("captures") or [{}])[0] if report else {}
    return {
        "exists": path.exists(),
        "qa_pass": bool(report.get("qa_pass")),
        "capture_qa_pass": bool(report.get("capture_qa_pass")),
        "report_path": str(path),
        "screenshot_path": capture.get("filepath"),
        "file_size": capture.get("file_size"),
        "sha256": capture.get("sha256"),
        "dirty_package_added_count": capture.get("dirty_package_added_count"),
    }


def _active_gate_summary() -> dict[str, Any]:
    gate = _read_json_if_exists(PCG_FINAL_GATE_PATH)
    component_summary = _component_summary(gate, "live_native_output", "component_summary")
    return {
        "exists": PCG_FINAL_GATE_PATH.exists(),
        "path": str(PCG_FINAL_GATE_PATH),
        "pass": bool(gate.get("pass")),
        "status": gate.get("status"),
        "native_components": component_summary.get("component_count"),
        "native_instances": component_summary.get("instance_count_total"),
        "dirty_count": gate.get("live_dirty_packages", {}).get("count"),
    }


def _summarize_final_reports() -> dict[str, Any]:
    primary = _read_json(PRIMARY_REPORT_PATH)
    primary_gate = _read_json(PRIMARY_FINAL_GATE_PATH)
    smoke = _read_json(SMOKE_REPORT_PATH)
    preview = _read_json(PREVIEW_REPORT_PATH)
    primary_summary = _component_summary(
        primary,
        "native_output_verify",
        "generation_verification",
        "component_summary",
    )
    primary_gate_summary = _component_summary(primary_gate, "live_native_output", "component_summary")
    smoke_summary = _component_summary(smoke, "generation_verification", "component_summary")
    preview_summary = _component_summary(preview, "generation_verification", "component_summary")
    return {
        "primary_refresh": {
            "pass": bool(primary.get("pass")),
            "status": primary.get("status"),
            "native_components": primary_summary.get("component_count"),
            "native_instances": primary_summary.get("instance_count_total"),
            "screenshot_qa_pass": bool(primary.get("checks", {}).get("screenshot_qa_pass")),
            "smoke_test_pass": bool(primary.get("checks", {}).get("smoke_test_pass")),
        },
        "primary_final_gate": {
            "pass": bool(primary_gate.get("pass")),
            "status": primary_gate.get("status"),
            "native_components": primary_gate_summary.get("component_count"),
            "native_instances": primary_gate_summary.get("instance_count_total"),
            "dirty_count": primary_gate.get("live_dirty_packages", {}).get("count"),
        },
        "smoke_test": {
            "pass": bool(smoke.get("pass")),
            "status": smoke.get("status"),
            "native_components": smoke_summary.get("component_count"),
            "native_instances": smoke_summary.get("instance_count_total"),
            "cleanup_residual_components": smoke.get("cleanup_verification", {}).get("residual_static_mesh_component_count"),
            "cleanup_residual_instances": smoke.get("cleanup_verification", {}).get("residual_static_mesh_instance_count"),
        },
        "preview": {
            "pass": bool(preview.get("pass")),
            "status": preview.get("status"),
            "native_components": preview_summary.get("component_count"),
            "native_instances": preview_summary.get("instance_count_total"),
            "side_by_side_screenshot_qa_pass": bool(preview.get("checks", {}).get("side_by_side_screenshot_qa_pass")),
        },
    }


def _build_summary_report(
    *,
    started_at: float,
    mode: str,
    primary_capture: dict[str, Any],
    preview_capture: dict[str, Any],
    operation_steps: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_gate = _active_gate_summary()
    final_reports = _summarize_final_reports()
    expected_components = active_gate.get("native_components")
    expected_instances = active_gate.get("native_instances")

    def count_match(section_name: str) -> bool:
        section = final_reports.get(section_name, {})
        return (
            expected_components is not None
            and expected_instances is not None
            and section.get("native_components") == expected_components
            and section.get("native_instances") == expected_instances
        )

    checks = {
        "active_gate_pass": bool(active_gate.get("pass")),
        "active_gate_dirty_zero": active_gate.get("dirty_count") == 0,
        "expected_counts_available": expected_components is not None and expected_instances is not None,
        "primary_refresh_pass": bool(final_reports.get("primary_refresh", {}).get("pass")),
        "primary_count_match": count_match("primary_refresh"),
        "primary_screenshot_qa_pass": bool(final_reports.get("primary_refresh", {}).get("screenshot_qa_pass")),
        "primary_smoke_embedded_pass": bool(final_reports.get("primary_refresh", {}).get("smoke_test_pass")),
        "primary_capture_report_pass": bool(primary_capture.get("qa_pass") and primary_capture.get("capture_qa_pass")),
        "primary_final_gate_pass": bool(final_reports.get("primary_final_gate", {}).get("pass")),
        "primary_final_gate_count_match": count_match("primary_final_gate"),
        "primary_final_gate_dirty_zero": final_reports.get("primary_final_gate", {}).get("dirty_count") == 0,
        "smoke_test_pass": bool(final_reports.get("smoke_test", {}).get("pass")),
        "smoke_count_match": count_match("smoke_test"),
        "smoke_cleanup_zero": final_reports.get("smoke_test", {}).get("cleanup_residual_components") == 0
        and final_reports.get("smoke_test", {}).get("cleanup_residual_instances") == 0,
        "preview_pass": bool(final_reports.get("preview", {}).get("pass")),
        "preview_count_match": count_match("preview"),
        "preview_side_by_side_screenshot_qa_pass": bool(
            final_reports.get("preview", {}).get("side_by_side_screenshot_qa_pass")
        ),
        "preview_capture_report_pass": bool(preview_capture.get("qa_pass") and preview_capture.get("capture_qa_pass")),
    }
    success = all(bool(value) for value in checks.values())
    report = {
        "schema": "cubeless_pcg_dungeon_native_evidence_refresh_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "mode": mode,
        "policy": (
            "Refreshes or summarizes native primary, native smoke, and native preview evidence for PCG dungeon generation. "
            "Does not implement gameplay or touch project C++."
        ),
        "active_gate": active_gate,
        "primary_capture": primary_capture,
        "preview_capture": preview_capture,
        "final_reports": final_reports,
        "checks": checks,
        "success": success,
        "report_path": str(SUMMARY_REPORT_PATH),
    }
    if operation_steps:
        report["operation_steps"] = operation_steps
    SUMMARY_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if not success:
        raise RuntimeError(f"native evidence refresh failed: {json.dumps(report, ensure_ascii=False)}")
    return report


def summarize_existing_reports() -> dict[str, Any]:
    started_at = time.monotonic()
    DUNGEON_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return _build_summary_report(
        started_at=started_at,
        mode="summarize_existing_reports",
        primary_capture=_screenshot_report_summary(PRIMARY_SCREENSHOT_REPORT_PATH),
        preview_capture=_screenshot_report_summary(PREVIEW_SIDE_BY_SIDE_REPORT_PATH),
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    if args.summarize_existing:
        return summarize_existing_reports()

    DUNGEON_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    unreal = UnrealConnection()
    if hasattr(unreal, "timeout"):
        unreal.timeout = max(int(getattr(unreal, "timeout", 0)), int(args.mcp_response_timeout_seconds))

    primary_begin = _compact_primary_begin(unreal, args.keep_existing_output)
    if not primary_begin.get("success"):
        raise RuntimeError(f"native primary begin failed: {json.dumps(primary_begin, ensure_ascii=False)}")
    time.sleep(max(0.0, float(args.refresh_wait_seconds)))
    primary_verify = _poll(
        lambda: _compact_primary_verify(unreal),
        timeout_seconds=float(args.refresh_timeout_seconds),
        poll_seconds=float(args.refresh_poll_seconds),
    )
    if not primary_verify.get("success"):
        raise RuntimeError(f"native primary verify failed: {json.dumps(primary_verify, ensure_ascii=False)}")

    primary_selection_clear = _clear_editor_selection(unreal)
    if not primary_selection_clear.get("success"):
        raise RuntimeError(f"primary selection clear failed: {json.dumps(primary_selection_clear, ensure_ascii=False)}")
    primary_capture = _capture_active_viewport(
        output_prefix="CubelessDungeonMVP_NativePrimaryRefresh",
        report_path=PRIMARY_SCREENSHOT_REPORT_PATH,
        redraw_count=args.redraw_count,
        clean_game_view=not args.no_clean_game_view,
    )

    smoke_begin = _compact_smoke_begin(unreal)
    if not smoke_begin.get("success"):
        raise RuntimeError(f"native smoke begin failed: {json.dumps(smoke_begin, ensure_ascii=False)}")
    time.sleep(max(0.0, float(args.refresh_wait_seconds)))
    smoke_generation = _poll(
        lambda: _compact_smoke_generation(unreal, request_cleanup=False),
        timeout_seconds=float(args.refresh_timeout_seconds),
        poll_seconds=float(args.refresh_poll_seconds),
    )
    if not smoke_generation.get("success"):
        raise RuntimeError(f"native smoke generation failed: {json.dumps(smoke_generation, ensure_ascii=False)}")
    smoke_cleanup_request = _compact_smoke_generation(unreal, request_cleanup=True)
    if not smoke_cleanup_request.get("success") or not smoke_cleanup_request.get("cleanup_request_ok"):
        raise RuntimeError(f"native smoke cleanup request failed: {json.dumps(smoke_cleanup_request, ensure_ascii=False)}")
    smoke_cleanup = _poll(
        lambda: _compact_smoke_cleanup(unreal),
        timeout_seconds=float(args.refresh_timeout_seconds),
        poll_seconds=float(args.refresh_poll_seconds),
    )
    if not smoke_cleanup.get("success"):
        raise RuntimeError(f"native smoke cleanup failed: {json.dumps(smoke_cleanup, ensure_ascii=False)}")

    primary_artifacts = _compact_record_primary_artifacts(unreal)
    if not primary_artifacts.get("success"):
        raise RuntimeError(f"native primary artifact/final gate failed: {json.dumps(primary_artifacts, ensure_ascii=False)}")

    restore_review = _compact_restore_review_mode(unreal)
    if not restore_review.get("success"):
        raise RuntimeError(f"review restore failed: {json.dumps(restore_review, ensure_ascii=False)}")
    preview_begin = _compact_preview_begin(unreal, args.keep_existing_preview)
    if not preview_begin.get("success"):
        raise RuntimeError(f"native preview begin failed: {json.dumps(preview_begin, ensure_ascii=False)}")
    time.sleep(max(0.0, float(args.refresh_wait_seconds)))
    preview_verify = _poll(
        lambda: _compact_preview_verify(unreal),
        timeout_seconds=float(args.refresh_timeout_seconds),
        poll_seconds=float(args.refresh_poll_seconds),
    )
    if not preview_verify.get("success"):
        raise RuntimeError(f"native preview verify failed: {json.dumps(preview_verify, ensure_ascii=False)}")
    preview_camera = _compact_preview_camera(unreal)
    if not preview_camera.get("success"):
        raise RuntimeError(f"native preview camera failed: {json.dumps(preview_camera, ensure_ascii=False)}")
    preview_selection_clear = _clear_editor_selection(unreal)
    if not preview_selection_clear.get("success"):
        raise RuntimeError(f"preview selection clear failed: {json.dumps(preview_selection_clear, ensure_ascii=False)}")
    preview_capture = _capture_active_viewport(
        output_prefix="CubelessDungeonMVP_NativePreview_SideBySide",
        report_path=PREVIEW_SIDE_BY_SIDE_REPORT_PATH,
        redraw_count=args.redraw_count,
        clean_game_view=not args.no_clean_game_view,
    )
    preview_embed = _embed_preview_screenshot(preview_capture)
    if not preview_embed.get("success"):
        raise RuntimeError(f"native preview screenshot embed failed: {json.dumps(preview_embed, ensure_ascii=False)}")

    return _build_summary_report(
        started_at=started_at,
        mode="full_refresh",
        primary_capture=primary_capture,
        preview_capture=preview_capture,
        operation_steps={
            "primary_begin": primary_begin,
            "primary_verify": primary_verify,
            "primary_selection_clear": primary_selection_clear,
            "smoke_begin": smoke_begin,
            "smoke_generation": smoke_generation,
            "smoke_cleanup_request": smoke_cleanup_request,
            "smoke_cleanup": smoke_cleanup,
            "primary_artifacts": primary_artifacts,
            "restore_review": restore_review,
            "preview_begin": preview_begin,
            "preview_verify": preview_verify,
            "preview_camera": preview_camera,
            "preview_selection_clear": preview_selection_clear,
            "preview_embed": preview_embed,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh PCG dungeon native primary/smoke/preview evidence.")
    parser.add_argument(
        "--summarize-existing",
        action="store_true",
        help="Write the native evidence summary from existing primary/smoke/preview reports without touching Unreal.",
    )
    parser.add_argument("--keep-existing-output", action="store_true")
    parser.add_argument("--keep-existing-preview", action="store_true")
    parser.add_argument("--refresh-wait-seconds", type=float, default=1.0)
    parser.add_argument("--refresh-timeout-seconds", type=float, default=600.0)
    parser.add_argument("--refresh-poll-seconds", type=float, default=1.5)
    parser.add_argument("--redraw-count", type=int, default=2)
    parser.add_argument("--no-clean-game-view", action="store_true")
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=600)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        result = run(parse_args())
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        raise
    print(json.dumps(result, ensure_ascii=False))
