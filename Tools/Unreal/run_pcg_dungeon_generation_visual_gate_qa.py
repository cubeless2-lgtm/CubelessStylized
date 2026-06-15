"""Run the Cubeless PCG dungeon visual QA and final gate.

This is a convenience runner for the current dungeon-generation goal. It uses
UnrealMCP to set the NativeOutput-only review cameras, reuses the active
viewport screenshot QA route, then asks the dungeon script to record the final
PCG generation gate.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from run_pcg_bookmark_visual_qa import (
    PROJECT_ROOT,
    UnrealConnection,
    parse_execute_python_log_json,
    run as run_screenshot_qa,
    send,
)


DUNGEON_SCRIPT_DIR = PROJECT_ROOT / "Plugins" / "CustomTools" / "Content" / "Python" / "ArtScripts"
DUNGEON_REPORT_DIR = PROJECT_ROOT / "Saved" / "MCP_Dungeon"
ARCHIVE_DIR = DUNGEON_REPORT_DIR / "PresetQA"
SUMMARY_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_PCGGeneration_VisualGateQA_Report.json"
REFRESH_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_PCGGeneration_Refresh_Report.json"
FINAL_GATE_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_PCGGeneration_FinalGate.json"
TOP_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_PCGGeneration_NativeOutputOnly_ScreenshotQA.json"
OBLIQUE_REPORT_PATH = DUNGEON_REPORT_DIR / "CubelessDungeonMVP_PCGGeneration_NativeOutputOnly_Oblique_ScreenshotQA.json"

EXPOSURE_BRIGHT_LUMA_THRESHOLD = 220.0
EXPOSURE_NEAR_WHITE_RGB_THRESHOLD = 245
EXPOSURE_NEAR_BLACK_LUMA_THRESHOLD = 18.0
EXPOSURE_MAX_BRIGHT_PERCENT = 8.0
EXPOSURE_MAX_NEAR_WHITE_PERCENT = 1.0
EXPOSURE_MIN_NON_BLACK_PERCENT = 3.0
EXPOSURE_MIN_VISIBLE_AVERAGE_LUMA = 9.0
EXPOSURE_MAX_VISIBLE_NEAR_BLACK_PERCENT = 92.0


def _execute_dungeon_python(unreal: UnrealConnection, body: str, retry_count: int = 1) -> dict[str, Any]:
    code = f"""
import json
import sys
import importlib

script_dir = r"{DUNGEON_SCRIPT_DIR}"
if script_dir not in sys.path:
    sys.path.append(script_dir)
import CubelessDungeonPCG as dungeon
dungeon = importlib.reload(dungeon)

{body}
"""
    last_error: Exception | None = None
    for attempt_index in range(max(1, retry_count + 1)):
        try:
            response = send(unreal, "execute_python", {"code": code, "mode": "ExecuteFile"})
            return parse_execute_python_log_json(response)
        except OSError as exc:
            last_error = exc
            if attempt_index >= retry_count:
                raise
            time.sleep(0.75)
    raise RuntimeError(f"execute_python failed after retry: {last_error}")


def _clear_editor_selection(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
result = {
    "success": False,
    "selected_before": None,
    "selected_after": None,
    "route": None,
}
try:
    actor_subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    actor_subsystem = unreal.get_editor_subsystem(actor_subsystem_cls) if actor_subsystem_cls else None
    if actor_subsystem:
        selected_before = list(actor_subsystem.get_selected_level_actors())
        actor_subsystem.clear_actor_selection_set()
        selected_after = list(actor_subsystem.get_selected_level_actors())
        result.update({
            "success": len(selected_after) == 0,
            "selected_before": len(selected_before),
            "selected_after": len(selected_after),
            "route": "EditorActorSubsystem",
        })
    else:
        selected_before = list(unreal.EditorLevelLibrary.get_selected_level_actors())
        unreal.EditorLevelLibrary.clear_actor_selection_set()
        selected_after = list(unreal.EditorLevelLibrary.get_selected_level_actors())
        result.update({
            "success": len(selected_after) == 0,
            "selected_before": len(selected_before),
            "selected_after": len(selected_after),
            "route": "EditorLevelLibrary",
        })
except Exception as exc:
    result["error"] = str(exc)
print(json.dumps(result, ensure_ascii=False))
""",
    )


def _setup_top_camera(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
review = dungeon.set_native_output_only_review_mode(True)
camera = dungeon.setup_native_output_only_review_camera()
print(json.dumps({
    "success": bool(review.get("pass") and camera.get("success")),
    "review_pass": bool(review.get("pass")),
    "camera_success": bool(camera.get("success")),
    "bridge_visible": review.get("bridge_static_mesh_after", {}).get("visible_static_mesh_component_count"),
    "preview_visible": review.get("preview_after", {}).get("visible_static_mesh_component_count"),
    "lights_visible": review.get("bridge_review_lights_after", {}).get("visible_light_component_count"),
    "camera": camera,
}, ensure_ascii=False))
""",
    )


def _setup_oblique_camera(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
review = dungeon.set_native_output_only_review_mode(True)
camera = dungeon.setup_pcg_generation_oblique_review_camera()
print(json.dumps({
    "success": bool(review.get("pass") and camera.get("success")),
    "review_pass": bool(review.get("pass")),
    "camera_success": bool(camera.get("success")),
    "bridge_visible": review.get("bridge_static_mesh_after", {}).get("visible_static_mesh_component_count"),
    "preview_visible": review.get("preview_after", {}).get("visible_static_mesh_component_count"),
    "lights_visible": review.get("bridge_review_lights_after", {}).get("visible_light_component_count"),
    "camera": camera,
}, ensure_ascii=False))
""",
    )


def _record_final_gate(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
gate = dungeon.record_pcg_generation_final_gate()
print(json.dumps({
    "success": bool(gate.get("pass")),
    "gate_pass": bool(gate.get("pass")),
    "failed_checks": [key for key, value in gate.get("checks", {}).items() if not value],
    "native_components": gate.get("live_native_output", {}).get("component_summary", {}).get("component_count"),
    "native_instances": gate.get("live_native_output", {}).get("component_summary", {}).get("instance_count_total"),
    "dirty_count": gate.get("live_dirty_packages", {}).get("count"),
    "top_screenshot_after_generation_refresh": gate.get("checks", {}).get("top_screenshot_after_generation_refresh"),
    "oblique_screenshot_after_generation_refresh": gate.get("checks", {}).get("oblique_screenshot_after_generation_refresh"),
}, ensure_ascii=False))
""",
    )


def _begin_refresh_with_preset(
    unreal: UnrealConnection,
    preset_name: str,
    keep_existing_output: bool,
) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        f"""
begin = dungeon.begin_pcg_generation_refresh_with_authoring_preset(
    preset_name={json.dumps(preset_name)},
    keep_existing_output={bool(keep_existing_output)},
    save_dirty_packages=True,
)
print(json.dumps({{
    "success": bool(
        begin.get("status") == "generation_requested"
        and begin.get("preset_apply", {{}}).get("pass")
        and begin.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok")
    ),
    "status": begin.get("status"),
    "preset_name": begin.get("preset_name"),
    "preset_apply_pass": bool(begin.get("preset_apply", {{}}).get("pass")),
    "dungeon_pass": bool(begin.get("dungeon", {{}}).get("pass")),
    "seed_suite_pass": bool(begin.get("seed_suite", {{}}).get("pass")),
    "authoring_surface_pass": bool(begin.get("authoring_surface", {{}}).get("pass")),
    "preset_smoke_pass": bool(begin.get("authoring_preset_smoke", {{}}).get("pass")),
    "scale_pass": bool(begin.get("generation_parameter_scale", {{}}).get("pass")),
    "integration_graph_pass": bool(begin.get("native_integration_graph", {{}}).get("pass")),
    "integration_audit_pass": bool(begin.get("native_integration_audit", {{}}).get("pass")),
    "output_requested": begin.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok"),
}}, ensure_ascii=False))
""",
    )


def _begin_refresh_from_bridge(unreal: UnrealConnection, keep_existing_output: bool) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        f"""
begin = dungeon.begin_pcg_generation_refresh_from_bridge(keep_existing_output={bool(keep_existing_output)})
print(json.dumps({{
    "success": bool(
        begin.get("status") == "generation_requested"
        and begin.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok")
    ),
    "status": begin.get("status"),
    "preset_name": begin.get("preset_name"),
    "dungeon_pass": bool(begin.get("dungeon", {{}}).get("pass")),
    "seed_suite_pass": bool(begin.get("seed_suite", {{}}).get("pass")),
    "authoring_surface_pass": bool(begin.get("authoring_surface", {{}}).get("pass")),
    "preset_smoke_pass": bool(begin.get("authoring_preset_smoke", {{}}).get("pass")),
    "scale_pass": bool(begin.get("generation_parameter_scale", {{}}).get("pass")),
    "integration_graph_pass": bool(begin.get("native_integration_graph", {{}}).get("pass")),
    "integration_audit_pass": bool(begin.get("native_integration_audit", {{}}).get("pass")),
    "output_requested": begin.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok"),
}}, ensure_ascii=False))
""",
    )


def _verify_refresh(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_dungeon_python(
        unreal,
        """
verify = dungeon.verify_pcg_generation_refresh(enable_output_only_review=True, save_dirty_packages=True)
print(json.dumps({
    "success": bool(verify.get("pass")),
    "refresh_pass": bool(verify.get("pass")),
    "preset_name": verify.get("preset_name"),
    "preset_apply_pass": bool(verify.get("preset_apply", {}).get("pass")) if verify.get("preset_apply") else None,
    "failed_checks": [key for key, value in verify.get("checks", {}).items() if not value],
    "native_components": verify.get("native_output_verify", {}).get("generation_verification", {}).get("component_summary", {}).get("component_count"),
    "native_instances": verify.get("native_output_verify", {}).get("generation_verification", {}).get("component_summary", {}).get("instance_count_total"),
    "structure_audit_pass": bool(verify.get("structure_audit", {}).get("pass")),
    "review_pass": bool(verify.get("native_output_only_review", {}).get("pass")),
    "camera_success": bool(verify.get("native_output_only_camera", {}).get("success")),
    "dirty_after": verify.get("dirty_after_count"),
}, ensure_ascii=False))
""",
    )


def _wait_for_refresh_verify(
    unreal: UnrealConnection,
    *,
    timeout_seconds: float,
    poll_seconds: float,
) -> dict[str, Any]:
    started_at = time.monotonic()
    attempts: list[dict[str, Any]] = []
    while True:
        verify = _verify_refresh(unreal)
        attempts.append(
            {
                "success": bool(verify.get("success")),
                "failed_checks": verify.get("failed_checks", []),
                "native_components": verify.get("native_components"),
                "native_instances": verify.get("native_instances"),
                "elapsed_seconds": round(time.monotonic() - started_at, 4),
            }
        )
        if verify.get("success"):
            verify["attempts"] = attempts
            return verify
        if time.monotonic() - started_at >= max(0.0, timeout_seconds):
            verify["attempts"] = attempts
            return verify
        time.sleep(max(0.1, poll_seconds))


def _screenshot_namespace(
    *,
    output_prefix: str,
    report_path: Path,
    redraw_count: int,
    clean_game_view: bool,
) -> argparse.Namespace:
    return argparse.Namespace(
        bookmarks=[],
        no_active_viewport=False,
        output_dir=DUNGEON_REPORT_DIR,
        output_prefix=output_prefix,
        report_path=report_path,
        redraw_count=redraw_count,
        min_grass_instances=1000,
        min_tree_instances=100,
        min_rock_instances=0,
        capture_only=True,
        clean_game_view=clean_game_view,
        allow_duplicate_capture_hashes=False,
    )


def _capture_top(redraw_count: int, clean_game_view: bool) -> dict[str, Any]:
    return run_screenshot_qa(
        _screenshot_namespace(
            output_prefix="CubelessDungeonMVP_PCGGenerationNativeOutputOnly",
            report_path=TOP_REPORT_PATH,
            redraw_count=redraw_count,
            clean_game_view=clean_game_view,
        )
    )


def _capture_oblique(redraw_count: int, clean_game_view: bool) -> dict[str, Any]:
    return run_screenshot_qa(
        _screenshot_namespace(
            output_prefix="CubelessDungeonMVP_PCGGenerationNativeOutputOnly_Oblique",
            report_path=OBLIQUE_REPORT_PATH,
            redraw_count=redraw_count,
            clean_game_view=clean_game_view,
        )
    )


def _safe_archive_label(label: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in str(label).strip())
    return safe.strip("._") or "unnamed"


def _resolve_artifact_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _load_pil_image_class() -> Any:
    script_dir = str(DUNGEON_SCRIPT_DIR)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    try:
        from PIL import Image
    except Exception:
        return None
    return Image


def _screenshot_exposure_stats(path_value: str | None) -> dict[str, Any]:
    image_path = _resolve_artifact_path(path_value)
    thresholds = {
        "bright_luma": EXPOSURE_BRIGHT_LUMA_THRESHOLD,
        "near_white_rgb": EXPOSURE_NEAR_WHITE_RGB_THRESHOLD,
        "max_bright_percent": EXPOSURE_MAX_BRIGHT_PERCENT,
        "max_near_white_percent": EXPOSURE_MAX_NEAR_WHITE_PERCENT,
        "min_non_black_percent": EXPOSURE_MIN_NON_BLACK_PERCENT,
        "min_visible_average_luma": EXPOSURE_MIN_VISIBLE_AVERAGE_LUMA,
        "near_black_luma": EXPOSURE_NEAR_BLACK_LUMA_THRESHOLD,
        "max_visible_near_black_percent": EXPOSURE_MAX_VISIBLE_NEAR_BLACK_PERCENT,
    }
    if not image_path:
        return {
            "pass": False,
            "available": False,
            "reason": "missing_screenshot_path",
            "thresholds": thresholds,
        }
    if not image_path.exists():
        return {
            "pass": False,
            "available": False,
            "reason": "screenshot_missing",
            "path": str(image_path),
            "thresholds": thresholds,
        }
    Image = _load_pil_image_class()
    if Image is None:
        return {
            "pass": False,
            "available": False,
            "reason": "pillow_unavailable",
            "path": str(image_path),
            "thresholds": thresholds,
        }

    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        pixels = rgb_image.getdata()
        pixel_count = max(1, width * height)
        luma_total = 0.0
        bright_count = 0
        near_white_count = 0
        non_black_count = 0
        near_black_visible_count = 0
        visible_luma_total = 0.0
        max_luma = 0.0
        for red, green, blue in pixels:
            luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue
            luma_total += luma
            if luma >= EXPOSURE_BRIGHT_LUMA_THRESHOLD:
                bright_count += 1
            if (
                red >= EXPOSURE_NEAR_WHITE_RGB_THRESHOLD
                and green >= EXPOSURE_NEAR_WHITE_RGB_THRESHOLD
                and blue >= EXPOSURE_NEAR_WHITE_RGB_THRESHOLD
            ):
                near_white_count += 1
            if red > 8 or green > 8 or blue > 8:
                non_black_count += 1
                visible_luma_total += luma
                if luma <= EXPOSURE_NEAR_BLACK_LUMA_THRESHOLD:
                    near_black_visible_count += 1
            max_luma = max(max_luma, luma)

    bright_percent = 100.0 * bright_count / pixel_count
    near_white_percent = 100.0 * near_white_count / pixel_count
    non_black_percent = 100.0 * non_black_count / pixel_count
    visible_average_luma = visible_luma_total / max(1, non_black_count)
    visible_near_black_percent = 100.0 * near_black_visible_count / max(1, non_black_count)
    average_luma = luma_total / pixel_count
    pass_result = (
        bright_percent <= EXPOSURE_MAX_BRIGHT_PERCENT
        and near_white_percent <= EXPOSURE_MAX_NEAR_WHITE_PERCENT
        and non_black_percent >= EXPOSURE_MIN_NON_BLACK_PERCENT
        and visible_average_luma >= EXPOSURE_MIN_VISIBLE_AVERAGE_LUMA
        and visible_near_black_percent <= EXPOSURE_MAX_VISIBLE_NEAR_BLACK_PERCENT
    )
    return {
        "pass": bool(pass_result),
        "available": True,
        "path": str(image_path),
        "width": width,
        "height": height,
        "average_luma": round(average_luma, 4),
        "visible_average_luma": round(visible_average_luma, 4),
        "max_luma": round(max_luma, 4),
        "bright_percent": round(bright_percent, 4),
        "near_white_percent": round(near_white_percent, 4),
        "non_black_percent": round(non_black_percent, 4),
        "visible_near_black_percent": round(visible_near_black_percent, 4),
        "thresholds": thresholds,
    }


def _archive_file(source: Path | None, destination_dir: Path, prefix: str) -> dict[str, Any]:
    if not source:
        return {"source": None, "copied": False, "reason": "missing_source"}
    record: dict[str, Any] = {
        "source": str(source),
        "exists": source.exists(),
        "copied": False,
    }
    if not source.exists():
        record["reason"] = "source_missing"
        return record
    destination = destination_dir / f"{prefix}_{source.name}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    record.update(
        {
            "copied": True,
            "destination": str(destination),
            "file_size": destination.stat().st_size,
        }
    )
    return record


def _write_summary_report(report: dict[str, Any]) -> None:
    SUMMARY_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def _archive_current_artifacts(label: str, report: dict[str, Any]) -> dict[str, Any]:
    safe_label = _safe_archive_label(label)
    destination_dir = ARCHIVE_DIR / safe_label
    top_screenshot = _resolve_artifact_path(report.get("top_capture", {}).get("screenshot_path"))
    oblique_screenshot = _resolve_artifact_path(report.get("oblique_capture", {}).get("screenshot_path"))
    artifacts = {
        "refresh_report": _archive_file(REFRESH_REPORT_PATH, destination_dir, safe_label),
        "final_gate_report": _archive_file(FINAL_GATE_REPORT_PATH, destination_dir, safe_label),
        "top_screenshot_report": _archive_file(TOP_REPORT_PATH, destination_dir, safe_label),
        "oblique_screenshot_report": _archive_file(OBLIQUE_REPORT_PATH, destination_dir, safe_label),
        "top_screenshot_png": _archive_file(top_screenshot, destination_dir, safe_label),
        "oblique_screenshot_png": _archive_file(oblique_screenshot, destination_dir, safe_label),
    }
    return {
        "requested": True,
        "label": str(label),
        "safe_label": safe_label,
        "directory": str(destination_dir),
        "artifacts": artifacts,
        "pass": all(item.get("copied") for item in artifacts.values()),
    }


def _archive_summary_report(archive: dict[str, Any]) -> None:
    destination_dir = Path(archive["directory"])
    safe_label = str(archive["safe_label"])
    archive["artifacts"]["summary_report"] = _archive_file(SUMMARY_REPORT_PATH, destination_dir, safe_label)
    archive["pass"] = all(item.get("copied") for item in archive["artifacts"].values())


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    DUNGEON_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    unreal = UnrealConnection()
    if hasattr(unreal, "timeout"):
        unreal.timeout = max(int(getattr(unreal, "timeout", 0)), int(args.mcp_response_timeout_seconds))

    refresh_begin = {}
    refresh_verify = {}
    if args.preset:
        refresh_begin = _begin_refresh_with_preset(unreal, args.preset, args.keep_existing_output)
    elif args.refresh_current:
        refresh_begin = _begin_refresh_from_bridge(unreal, args.keep_existing_output)
    if refresh_begin:
        if not refresh_begin.get("success"):
            raise RuntimeError(f"PCG generation refresh begin failed: {json.dumps(refresh_begin, ensure_ascii=False)}")
        time.sleep(max(0.0, float(args.refresh_wait_seconds)))
        refresh_verify = _wait_for_refresh_verify(
            unreal,
            timeout_seconds=float(args.refresh_timeout_seconds),
            poll_seconds=float(args.refresh_poll_seconds),
        )
        if not refresh_verify.get("success"):
            raise RuntimeError(f"PCG generation refresh verify failed: {json.dumps(refresh_verify, ensure_ascii=False)}")

    top_camera = _setup_top_camera(unreal)
    if not top_camera.get("success"):
        raise RuntimeError(f"top camera setup failed: {json.dumps(top_camera, ensure_ascii=False)}")
    top_selection_clear = _clear_editor_selection(unreal)
    if not top_selection_clear.get("success"):
        raise RuntimeError(f"top selection clear failed: {json.dumps(top_selection_clear, ensure_ascii=False)}")
    top_capture = _capture_top(args.redraw_count, not args.no_clean_game_view)
    top_screenshot_path = (top_capture.get("captures") or [{}])[0].get("filepath")
    top_exposure = _screenshot_exposure_stats(top_screenshot_path)

    oblique_camera = _setup_oblique_camera(unreal)
    if not oblique_camera.get("success"):
        raise RuntimeError(f"oblique camera setup failed: {json.dumps(oblique_camera, ensure_ascii=False)}")
    oblique_selection_clear = _clear_editor_selection(unreal)
    if not oblique_selection_clear.get("success"):
        raise RuntimeError(f"oblique selection clear failed: {json.dumps(oblique_selection_clear, ensure_ascii=False)}")
    oblique_capture = _capture_oblique(args.redraw_count, not args.no_clean_game_view)
    oblique_screenshot_path = (oblique_capture.get("captures") or [{}])[0].get("filepath")
    oblique_exposure = _screenshot_exposure_stats(oblique_screenshot_path)
    exposure_review_pass = bool(top_exposure.get("pass") and oblique_exposure.get("pass"))

    final_gate = {} if args.skip_final_gate else _record_final_gate(unreal)
    report = {
        "success": bool(
            top_camera.get("success")
            and oblique_camera.get("success")
            and top_capture.get("qa_pass")
            and top_capture.get("capture_qa_pass")
            and oblique_capture.get("qa_pass")
            and oblique_capture.get("capture_qa_pass")
            and exposure_review_pass
            and (args.skip_final_gate or final_gate.get("gate_pass"))
            and (not refresh_begin or refresh_begin.get("success"))
            and (not refresh_verify or refresh_verify.get("success"))
        ),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "policy": (
            "PCG dungeon generation visual gate QA. Uses active viewport screenshot capture only, does not create "
            "or overwrite viewport bookmarks, and leaves gameplay implementation outside this gate."
        ),
        "refresh": {
            "requested": bool(refresh_begin),
            "mode": "preset" if args.preset else "current_bridge" if args.refresh_current else "none",
            "preset_name": args.preset,
            "keep_existing_output": bool(args.keep_existing_output),
            "wait_seconds": float(args.refresh_wait_seconds) if refresh_begin else 0.0,
            "begin": refresh_begin,
            "verify": refresh_verify,
        },
        "top_camera": top_camera,
        "top_selection_clear": top_selection_clear,
        "top_capture": {
            "qa_pass": bool(top_capture.get("qa_pass")),
            "capture_qa_pass": bool(top_capture.get("capture_qa_pass")),
            "report_path": str(TOP_REPORT_PATH),
            "screenshot_path": top_screenshot_path,
            "dirty_package_added_count": (top_capture.get("captures") or [{}])[0].get("dirty_package_added_count"),
            "exposure": top_exposure,
        },
        "oblique_camera": oblique_camera,
        "oblique_selection_clear": oblique_selection_clear,
        "oblique_capture": {
            "qa_pass": bool(oblique_capture.get("qa_pass")),
            "capture_qa_pass": bool(oblique_capture.get("capture_qa_pass")),
            "report_path": str(OBLIQUE_REPORT_PATH),
            "screenshot_path": oblique_screenshot_path,
            "dirty_package_added_count": (oblique_capture.get("captures") or [{}])[0].get("dirty_package_added_count"),
            "exposure": oblique_exposure,
        },
        "exposure_review_pass": exposure_review_pass,
        "final_gate": final_gate,
        "report_path": str(SUMMARY_REPORT_PATH),
    }
    _write_summary_report(report)
    if args.archive_label:
        report["archive"] = _archive_current_artifacts(args.archive_label, report)
        _write_summary_report(report)
        _archive_summary_report(report["archive"])
        _write_summary_report(report)
        _archive_summary_report(report["archive"])
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PCG dungeon NativeOutput visual QA and final gate.")
    parser.add_argument(
        "--preset",
        default=None,
        help="Apply a documented dungeon authoring preset, refresh PCG generation, then run visual QA and final gate.",
    )
    parser.add_argument(
        "--refresh-current",
        action="store_true",
        help="Refresh PCG generation from the current bridge tags before visual QA.",
    )
    parser.add_argument("--keep-existing-output", action="store_true")
    parser.add_argument("--refresh-wait-seconds", type=float, default=1.0)
    parser.add_argument("--refresh-timeout-seconds", type=float, default=600.0)
    parser.add_argument("--refresh-poll-seconds", type=float, default=1.5)
    parser.add_argument(
        "--mcp-response-timeout-seconds",
        type=int,
        default=600,
        help="Minimum socket response timeout for long UnrealMCP execute_python verification calls.",
    )
    parser.add_argument("--redraw-count", type=int, default=2)
    parser.add_argument("--no-clean-game-view", action="store_true")
    parser.add_argument("--skip-final-gate", action="store_true")
    parser.add_argument(
        "--archive-label",
        default=None,
        help="Copy the generated refresh/final gate/screenshot reports and PNGs under Saved/MCP_Dungeon/PresetQA/<label>.",
    )
    args = parser.parse_args()
    if args.preset and args.refresh_current:
        parser.error("--preset and --refresh-current are mutually exclusive")
    return args


if __name__ == "__main__":
    try:
        result = run(parse_args())
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        raise
    print(json.dumps(result, ensure_ascii=False))
