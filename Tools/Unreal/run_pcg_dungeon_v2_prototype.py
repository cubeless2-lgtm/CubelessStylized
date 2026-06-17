"""Build and validate the first Cubeless PCG Dungeon V2 prototype."""

from __future__ import annotations

import argparse
import json
import os
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
REPORT_DIR = PROJECT_ROOT / "Saved" / "MCP_DungeonV2"
RUNNER_REPORT_PATH = REPORT_DIR / "CubelessDungeonV2_PrototypeRunner_Report.json"
TOP_REPORT_PATH = REPORT_DIR / "CubelessDungeonV2_PCGGeneration_NativeOutputOnly_ScreenshotQA.json"
OBLIQUE_REPORT_PATH = REPORT_DIR / "CubelessDungeonV2_PCGGeneration_NativeOutputOnly_Oblique_ScreenshotQA.json"


def _create_unreal_connection(timeout_seconds: int) -> UnrealConnection:
    timeout = max(1, int(timeout_seconds))
    os.environ["UNREAL_MCP_RESPONSE_TIMEOUT_SECONDS"] = str(timeout)
    try:
        import unreal_mcp_server  # type: ignore

        unreal_mcp_server.UNREAL_RESPONSE_TIMEOUT_SECONDS = timeout
    except Exception:
        pass
    unreal = UnrealConnection()
    if hasattr(unreal, "timeout"):
        unreal.timeout = timeout
    return unreal


def _execute_v2_python(unreal: UnrealConnection, body: str) -> dict[str, Any]:
    code = f"""
import json
import sys
import importlib

script_dir = r"{DUNGEON_SCRIPT_DIR}"
if script_dir not in sys.path:
    sys.path.append(script_dir)
import CubelessDungeonPCGV2 as dungeon_v2
dungeon_v2 = importlib.reload(dungeon_v2)

{body}
"""
    response = send(unreal, "execute_python", {"code": code, "mode": "ExecuteFile"})
    return parse_execute_python_log_json(response)


def _normalize_path_for_compare(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").rstrip("/").casefold()


def _get_editor_paths(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
print(json.dumps({
    "success": True,
    "project_dir": unreal.Paths.project_dir(),
    "project_saved_dir": unreal.Paths.project_saved_dir(),
    "project_content_dir": unreal.Paths.project_content_dir(),
}, ensure_ascii=False))
""",
    )


def _ensure_editor_project_matches(editor_paths: dict[str, Any]) -> None:
    expected = _normalize_path_for_compare(PROJECT_ROOT)
    actual = _normalize_path_for_compare(str(editor_paths.get("project_dir") or ""))
    if actual != expected:
        raise RuntimeError(
            "Unreal Editor is attached to a different worktree: "
            + json.dumps(
                {
                    "expected_project_root": str(PROJECT_ROOT),
                    "editor_project_dir": editor_paths.get("project_dir"),
                },
                ensure_ascii=False,
            )
        )


def _build_all(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
result = dungeon_v2.build_all()
payload = result.get("payload", {})
print(json.dumps({
    "success": bool(result.get("pass")),
    "wrapper_report_path": result.get("report_path"),
    "root": result.get("root"),
    "level_path": result.get("level_path"),
    "default_config": result.get("default_config"),
    "output_policy": result.get("output_policy"),
    "module_asset_count": payload.get("module_asset_count"),
    "pcg_spawn_point_count": payload.get("dungeon", {}).get("pcg_spawn_point_count"),
    "pcg_spawner_group_count": payload.get("dungeon", {}).get("pcg_spawner_group_count"),
    "dungeon_pass": bool(payload.get("dungeon", {}).get("pass")),
    "bp_controller_pass": bool(payload.get("v2_bp_controller", {}).get("pass")),
    "bp_controller_blueprint_path": payload.get("v2_bp_controller", {}).get("blueprint_path"),
    "bp_controller_label": payload.get("v2_bp_controller", {}).get("controller_label"),
    "bp_controller_created_blueprint": bool(payload.get("v2_bp_controller", {}).get("created_blueprint")),
    "bp_controller_created_actor": bool(payload.get("v2_bp_controller", {}).get("created_actor")),
    "pcg_parameter_binding_pass": bool(payload.get("v2_pcg_parameter_binding", {}).get("pass")),
    "pcg_parameter_binding_report_path": payload.get("v2_pcg_parameter_binding", {}).get("report_path"),
    "native_integration_graph_pass": bool(payload.get("native_integration_graph", {}).get("pass")),
    "native_integration_audit_pass": bool(payload.get("native_integration_audit", {}).get("pass")),
    "seed_suite_pass": bool(payload.get("seed_suite", {}).get("pass")),
}, ensure_ascii=False))
""",
    )


def _parse_config_overrides(values: list[str] | None) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for raw in values or []:
        if "=" not in raw:
            raise ValueError("--set values must use KEY=VALUE syntax: {}".format(raw))
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError("--set key cannot be empty: {}".format(raw))
        if not value:
            raise ValueError("--set value cannot be empty: {}".format(raw))
        overrides[key] = value
    return overrides


def _begin_refresh_from_bp_controller(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
result = dungeon_v2.begin_generation_refresh_with_bp_controller(
    keep_existing_output=False,
    save_dirty_packages=True,
)
sync = result.get("bp_controller_sync", {})
controller_config = sync.get("controller_config", {})
print(json.dumps({
    "success": bool(
        result.get("status") == "generation_requested"
        and sync.get("pass")
        and result.get("native_output_begin", {}).get("generate_request", {}).get("ok")
    ),
    "status": result.get("status"),
    "source": result.get("source"),
    "bp_controller_sync_pass": bool(sync.get("pass")),
    "pcg_parameter_binding_pass": bool(sync.get("pcg_parameter_binding", {}).get("pass")),
    "pcg_parameter_binding_report_path": sync.get("pcg_parameter_binding", {}).get("report_path"),
    "bp_controller_label": sync.get("controller_label"),
    "bridge_label": sync.get("bridge_label"),
    "controller_config": controller_config.get("config"),
    "dungeon_pass": bool(result.get("dungeon", {}).get("pass")),
    "authoring_surface_pass": bool(result.get("authoring_surface", {}).get("pass")),
    "native_integration_graph_pass": bool(result.get("native_integration_graph", {}).get("pass")),
    "native_integration_audit_pass": bool(result.get("native_integration_audit", {}).get("pass")),
    "output_requested": result.get("native_output_begin", {}).get("generate_request", {}).get("ok"),
}, ensure_ascii=False))
""",
    )


def _begin_refresh(unreal: UnrealConnection, preset_name: str, config_overrides: dict[str, str]) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        f"""
result = dungeon_v2.begin_generation_refresh_with_authoring_preset(
    preset_name={json.dumps(preset_name)},
    config_overrides={json.dumps(config_overrides, ensure_ascii=False)},
    keep_existing_output=False,
    save_dirty_packages=True,
)
print(json.dumps({{
    "success": bool(
        result.get("status") == "generation_requested"
        and result.get("preset_apply", {{}}).get("pass")
        and result.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok")
    ),
    "status": result.get("status"),
    "preset_name": result.get("preset_name"),
    "config_overrides": result.get("config_overrides"),
    "preset_apply_pass": bool(result.get("preset_apply", {{}}).get("pass")),
    "config_overrides_pass": bool(result.get("config_overrides", {{}}).get("pass", True)),
    "applied_config": result.get("preset_apply", {{}}).get("config"),
    "dungeon_pass": bool(result.get("dungeon", {{}}).get("pass")),
    "authoring_surface_pass": bool(result.get("authoring_surface", {{}}).get("pass")),
    "native_integration_graph_pass": bool(result.get("native_integration_graph", {{}}).get("pass")),
    "native_integration_audit_pass": bool(result.get("native_integration_audit", {{}}).get("pass")),
    "output_requested": result.get("native_output_begin", {{}}).get("generate_request", {{}}).get("ok"),
}}, ensure_ascii=False))
""",
    )


def _verify_refresh(unreal: UnrealConnection, allow_seed_suite_warning: bool = False) -> dict[str, Any]:
    allow_seed_suite_warning_literal = "True" if allow_seed_suite_warning else "False"
    return _execute_v2_python(
        unreal,
        """
result = dungeon_v2.verify_generation_refresh(
    enable_output_only_review=True,
    save_dirty_packages=True,
    allow_seed_suite_warning=ALLOW_SEED_SUITE_WARNING,
)
print(json.dumps({
    "success": bool(result.get("pass")),
    "status": result.get("status"),
    "failed_checks": [key for key, value in result.get("checks", {}).items() if not value],
    "seed_suite_warning": result.get("seed_suite_warning"),
    "native_components": result.get("native_output_verify", {}).get("generation_verification", {}).get("component_summary", {}).get("component_count"),
    "native_instances": result.get("native_output_verify", {}).get("generation_verification", {}).get("component_summary", {}).get("instance_count_total"),
    "structure_audit_pass": bool(result.get("structure_audit", {}).get("pass")),
    "review_pass": bool(result.get("native_output_only_review", {}).get("pass")),
    "camera_success": bool(result.get("native_output_only_camera", {}).get("success")),
    "dirty_after": result.get("dirty_after_count"),
}, ensure_ascii=False))
""".replace("ALLOW_SEED_SUITE_WARNING", allow_seed_suite_warning_literal),
    )


def _wait_for_verify(
    unreal: UnrealConnection,
    timeout_seconds: float,
    poll_seconds: float,
    allow_seed_suite_warning: bool = False,
) -> dict[str, Any]:
    started_at = time.monotonic()
    attempts = []
    while True:
        try:
            result = _verify_refresh(unreal, allow_seed_suite_warning=allow_seed_suite_warning)
        except TimeoutError as exc:
            return {
                "success": False,
                "status": "verify_response_timeout",
                "error": str(exc) or exc.__class__.__name__,
                "attempts": attempts,
                "elapsed_seconds": round(time.monotonic() - started_at, 4),
            }
        except OSError as exc:
            return {
                "success": False,
                "status": "verify_connection_error",
                "error": str(exc) or exc.__class__.__name__,
                "attempts": attempts,
                "elapsed_seconds": round(time.monotonic() - started_at, 4),
            }
        attempts.append(
            {
                "success": bool(result.get("success")),
                "failed_checks": result.get("failed_checks", []),
                "native_components": result.get("native_components"),
                "native_instances": result.get("native_instances"),
                "elapsed_seconds": round(time.monotonic() - started_at, 4),
            }
        )
        if result.get("success") or time.monotonic() - started_at >= timeout_seconds:
            result["attempts"] = attempts
            return result
        time.sleep(max(0.1, poll_seconds))


def _recover_verify_after_timeout(
    args: argparse.Namespace,
    initial_verify: dict[str, Any],
    allow_seed_suite_warning: bool = False,
) -> tuple[dict[str, Any], UnrealConnection | None]:
    if not args.recover_refresh_verify_timeout:
        return initial_verify, None
    if initial_verify.get("status") not in {"verify_response_timeout", "verify_connection_error"}:
        return initial_verify, None

    started_at = time.monotonic()
    attempts = []
    time.sleep(max(0.0, float(args.verify_recovery_initial_wait_seconds)))
    while time.monotonic() - started_at <= float(args.verify_recovery_timeout_seconds):
        recovery_unreal = _create_unreal_connection(args.verify_recovery_response_timeout_seconds)
        try:
            result = _verify_refresh(recovery_unreal, allow_seed_suite_warning=allow_seed_suite_warning)
        except (TimeoutError, OSError) as exc:
            attempts.append(
                {
                    "success": False,
                    "error": str(exc) or exc.__class__.__name__,
                    "elapsed_seconds": round(time.monotonic() - started_at, 4),
                }
            )
        else:
            attempts.append(
                {
                    "success": bool(result.get("success")),
                    "failed_checks": result.get("failed_checks", []),
                    "native_components": result.get("native_components"),
                    "native_instances": result.get("native_instances"),
                    "elapsed_seconds": round(time.monotonic() - started_at, 4),
                }
            )
            if result.get("success"):
                result["status"] = "passed_after_refresh_verify_timeout_recovery"
                result["recovered_after_timeout"] = True
                result["initial_verify_failure"] = initial_verify
                result["recovery_attempts"] = attempts
                return result, recovery_unreal
        time.sleep(max(0.1, float(args.verify_recovery_poll_seconds)))

    recovered = dict(initial_verify)
    recovered["recovered_after_timeout"] = False
    recovered["recovery_attempts"] = attempts
    recovered["recovery_elapsed_seconds"] = round(time.monotonic() - started_at, 4)
    return recovered, None


def _setup_top_camera(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
review = dungeon_v2.set_native_output_only_review_mode(True)
camera = dungeon_v2.setup_native_output_only_review_camera()
print(json.dumps({
    "success": bool(review.get("pass") and camera.get("success")),
    "review_pass": bool(review.get("pass")),
    "camera_success": bool(camera.get("success")),
    "camera": camera,
}, ensure_ascii=False))
""",
    )


def _setup_oblique_camera(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
review = dungeon_v2.set_native_output_only_review_mode(True)
camera = dungeon_v2.setup_pcg_generation_oblique_review_camera()
print(json.dumps({
    "success": bool(review.get("pass") and camera.get("success")),
    "review_pass": bool(review.get("pass")),
    "camera_success": bool(camera.get("success")),
    "camera": camera,
}, ensure_ascii=False))
""",
    )


def _clear_editor_selection(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
result = {"success": False}
try:
    subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    subsystem = unreal.get_editor_subsystem(subsystem_cls) if subsystem_cls else None
    if subsystem:
        before = len(list(subsystem.get_selected_level_actors()))
        subsystem.clear_actor_selection_set()
        after = len(list(subsystem.get_selected_level_actors()))
    else:
        before = len(list(unreal.EditorLevelLibrary.get_selected_level_actors()))
        unreal.EditorLevelLibrary.clear_actor_selection_set()
        after = len(list(unreal.EditorLevelLibrary.get_selected_level_actors()))
    result.update({"success": after == 0, "selected_before": before, "selected_after": after})
except Exception as exc:
    result["error"] = str(exc)
print(json.dumps(result, ensure_ascii=False))
""",
    )


def _capture_args(output_prefix: str, report_path: Path, redraw_count: int) -> argparse.Namespace:
    return argparse.Namespace(
        bookmarks=[],
        no_active_viewport=False,
        output_dir=REPORT_DIR,
        output_prefix=output_prefix,
        report_path=report_path,
        redraw_count=redraw_count,
        min_grass_instances=1000,
        min_tree_instances=100,
        min_rock_instances=0,
        capture_only=True,
        clean_game_view=True,
        allow_duplicate_capture_hashes=False,
    )


def _record_final_gate(unreal: UnrealConnection, allow_seed_suite_warning: bool = False) -> dict[str, Any]:
    allow_seed_suite_warning_literal = "True" if allow_seed_suite_warning else "False"
    return _execute_v2_python(
        unreal,
        """
result = dungeon_v2.record_generation_final_gate(
    allow_seed_suite_warning=ALLOW_SEED_SUITE_WARNING,
)
print(json.dumps({
    "success": bool(result.get("pass")),
    "gate_pass": bool(result.get("pass")),
    "failed_checks": [key for key, value in result.get("checks", {}).items() if not value],
    "seed_suite_warning": result.get("seed_suite_warning"),
    "native_components": result.get("live_native_output", {}).get("component_summary", {}).get("component_count"),
    "native_instances": result.get("live_native_output", {}).get("component_summary", {}).get("instance_count_total"),
    "dirty_count": result.get("live_dirty_packages", {}).get("count"),
}, ensure_ascii=False))
""".replace("ALLOW_SEED_SUITE_WARNING", allow_seed_suite_warning_literal),
    )


def _write_room_rule_summary(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
result = dungeon_v2.write_room_rule_summary()
print(json.dumps({
    "success": bool(result.get("pass")),
    "report_path": result.get("report_path"),
    "markdown_path": result.get("markdown_path"),
    "room_count": result.get("counts", {}).get("room_count"),
    "role_counts": result.get("progression", {}).get("role_counts"),
    "excluded_module_counts": result.get("output_policy", {}).get("excluded_module_counts"),
    "failed_checks": [key for key, value in result.get("checks", {}).items() if not value],
}, ensure_ascii=False))
""",
    )


def _write_room_rule_matrix(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
result = dungeon_v2.write_room_rule_matrix()
print(json.dumps({
    "success": bool(result.get("pass")),
    "report_path": result.get("report_path"),
    "markdown_path": result.get("markdown_path"),
    "preset_count": result.get("preset_count"),
    "missing_presets": result.get("missing_presets"),
    "failed_checks": [key for key, value in result.get("checks", {}).items() if not value],
}, ensure_ascii=False))
""",
    )


def _write_tuning_guide(unreal: UnrealConnection) -> dict[str, Any]:
    return _execute_v2_python(
        unreal,
        """
result = dungeon_v2.write_tuning_guide()
print(json.dumps({
    "success": bool(result.get("pass")),
    "report_path": result.get("report_path"),
    "markdown_path": result.get("markdown_path"),
    "quick_choice_count": len(result.get("quick_choices", [])),
    "recommended_preset_names": result.get("recommended_preset_names"),
    "missing_recommended_presets": result.get("missing_recommended_presets"),
    "failed_checks": [key for key, value in result.get("checks", {}).items() if not value],
}, ensure_ascii=False))
""",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    config_overrides = _parse_config_overrides(args.config_override)
    if args.verify_existing_output and config_overrides:
        raise ValueError("--set/--config-override requires a refresh run; remove --verify-existing-output.")
    if args.verify_existing_output and args.use_bp_controller:
        raise ValueError("--use-bp-controller requires a refresh run; remove --verify-existing-output.")
    if args.use_bp_controller and config_overrides:
        raise ValueError("--use-bp-controller cannot be combined with --set/--config-override.")
    allow_seed_suite_warning = bool(args.allow_seed_suite_warning or args.use_bp_controller or config_overrides)
    unreal = _create_unreal_connection(args.mcp_response_timeout_seconds)

    editor_paths = _get_editor_paths(unreal)
    _ensure_editor_project_matches(editor_paths)

    if args.verify_existing_output:
        mode = "verify_existing_output"
    elif args.use_bp_controller:
        mode = "bp_controller_refresh_verify"
    else:
        mode = "build_refresh_verify"
    if args.verify_existing_output:
        build = {"success": True, "skipped": True, "reason": "--verify-existing-output"}
        begin = {"success": True, "skipped": True, "reason": "--verify-existing-output"}
        verify = _verify_refresh(unreal, allow_seed_suite_warning=allow_seed_suite_warning)
    else:
        build = _build_all(unreal) if args.build else {"success": True, "skipped": True}
        if not build.get("success"):
            raise RuntimeError("V2 build failed: " + json.dumps(build, ensure_ascii=False))

        begin = _begin_refresh_from_bp_controller(unreal) if args.use_bp_controller else _begin_refresh(
            unreal,
            args.preset,
            config_overrides,
        )
        if not begin.get("success"):
            raise RuntimeError("V2 refresh begin failed: " + json.dumps(begin, ensure_ascii=False))
        time.sleep(max(0.0, float(args.refresh_wait_seconds)))
        verify_unreal = _create_unreal_connection(args.refresh_verify_response_timeout_seconds)
        verify = _wait_for_verify(
            verify_unreal,
            args.refresh_timeout_seconds,
            args.refresh_poll_seconds,
            allow_seed_suite_warning=allow_seed_suite_warning,
        )
        if not verify.get("success"):
            recovered_verify, recovered_unreal = _recover_verify_after_timeout(
                args,
                verify,
                allow_seed_suite_warning=allow_seed_suite_warning,
            )
            verify = recovered_verify
            if recovered_unreal is not None:
                unreal = recovered_unreal
    if not verify.get("success"):
        raise RuntimeError("V2 refresh verify failed: " + json.dumps(verify, ensure_ascii=False))

    room_rule_summary = _write_room_rule_summary(unreal)
    if not room_rule_summary.get("success"):
        raise RuntimeError("V2 room rule summary failed: " + json.dumps(room_rule_summary, ensure_ascii=False))
    room_rule_matrix = _write_room_rule_matrix(unreal)
    if not room_rule_matrix.get("success"):
        raise RuntimeError("V2 room rule matrix failed: " + json.dumps(room_rule_matrix, ensure_ascii=False))
    tuning_guide = _write_tuning_guide(unreal)
    if not tuning_guide.get("success"):
        raise RuntimeError("V2 tuning guide failed: " + json.dumps(tuning_guide, ensure_ascii=False))

    top_camera = _setup_top_camera(unreal)
    if not top_camera.get("success"):
        raise RuntimeError("V2 top camera setup failed: " + json.dumps(top_camera, ensure_ascii=False))
    top_selection = _clear_editor_selection(unreal)
    if not top_selection.get("success"):
        raise RuntimeError("V2 top selection clear failed: " + json.dumps(top_selection, ensure_ascii=False))
    top_capture = run_screenshot_qa(
        _capture_args("CubelessDungeonV2_PCGGenerationNativeOutputOnly", TOP_REPORT_PATH, args.redraw_count)
    )

    oblique_camera = _setup_oblique_camera(unreal)
    if not oblique_camera.get("success"):
        raise RuntimeError("V2 oblique camera setup failed: " + json.dumps(oblique_camera, ensure_ascii=False))
    oblique_selection = _clear_editor_selection(unreal)
    if not oblique_selection.get("success"):
        raise RuntimeError("V2 oblique selection clear failed: " + json.dumps(oblique_selection, ensure_ascii=False))
    oblique_capture = run_screenshot_qa(
        _capture_args("CubelessDungeonV2_PCGGenerationNativeOutputOnly_Oblique", OBLIQUE_REPORT_PATH, args.redraw_count)
    )

    final_gate = _record_final_gate(unreal, allow_seed_suite_warning=allow_seed_suite_warning)
    report = {
        "success": bool(
            build.get("success")
            and begin.get("success")
            and verify.get("success")
            and room_rule_summary.get("success")
            and room_rule_matrix.get("success")
            and tuning_guide.get("success")
            and top_camera.get("success")
            and top_capture.get("qa_pass")
            and top_capture.get("capture_qa_pass")
            and oblique_camera.get("success")
            and oblique_capture.get("qa_pass")
            and oblique_capture.get("capture_qa_pass")
            and final_gate.get("success")
        ),
        "schema": "cubeless_pcg_dungeon_v2_prototype_runner_v1",
        "mode": mode,
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "preset": args.preset,
        "use_bp_controller": bool(args.use_bp_controller),
        "config_overrides": config_overrides,
        "editor_paths": editor_paths,
        "build": build,
        "refresh_begin": begin,
        "refresh_verify": verify,
        "room_rule_summary": room_rule_summary,
        "room_rule_matrix": room_rule_matrix,
        "tuning_guide": tuning_guide,
        "top_camera": top_camera,
        "top_selection": top_selection,
        "top_capture": {
            "qa_pass": bool(top_capture.get("qa_pass")),
            "capture_qa_pass": bool(top_capture.get("capture_qa_pass")),
            "report_path": str(TOP_REPORT_PATH),
            "screenshot_path": (top_capture.get("captures") or [{}])[0].get("filepath"),
        },
        "oblique_camera": oblique_camera,
        "oblique_selection": oblique_selection,
        "oblique_capture": {
            "qa_pass": bool(oblique_capture.get("qa_pass")),
            "capture_qa_pass": bool(oblique_capture.get("capture_qa_pass")),
            "report_path": str(OBLIQUE_REPORT_PATH),
            "screenshot_path": (oblique_capture.get("captures") or [{}])[0].get("filepath"),
        },
        "final_gate": final_gate,
        "report_path": str(RUNNER_REPORT_PATH),
    }
    RUNNER_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if not report["success"]:
        raise RuntimeError("V2 prototype runner failed: " + json.dumps(report, ensure_ascii=False))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and validate PCG Dungeon V2 prototype.")
    parser.add_argument("--preset", default="default")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        dest="config_override",
        metavar="KEY=VALUE",
        help=(
            "Override one V2 authoring config value on top of --preset before refresh. "
            "Keys may be config keys such as room_count or tags such as DungeonRoomCount. "
            "Repeat for multiple overrides."
        ),
    )
    parser.add_argument(
        "--config-override",
        action="append",
        dest="config_override",
        metavar="KEY=VALUE",
        help="Alias for --set.",
    )
    parser.set_defaults(config_override=[])
    parser.add_argument(
        "--use-bp-controller",
        action="store_true",
        help=(
            "Read the placed BP_Cubeless_DungeonV2_Controller actor variables, sync them to bridge tags, "
            "and refresh NativeOutput. Cannot be combined with --set or --verify-existing-output."
        ),
    )
    parser.add_argument("--no-build", action="store_false", dest="build")
    parser.set_defaults(build=True)
    parser.add_argument(
        "--verify-existing-output",
        action="store_true",
        help="Skip build/refresh and validate the currently generated V2 NativeOutput.",
    )
    parser.add_argument(
        "--skip-refresh",
        action="store_true",
        dest="verify_existing_output",
        help="Alias for --verify-existing-output.",
    )
    parser.add_argument(
        "--allow-seed-suite-warning",
        action="store_true",
        help=(
            "Treat seed-suite failures as warnings during verification. This is enabled automatically for "
            "--use-bp-controller and --set refreshes, and is useful when validating an already generated "
            "single-seed custom/BP output."
        ),
    )
    parser.add_argument("--refresh-wait-seconds", type=float, default=1.0)
    parser.add_argument("--refresh-timeout-seconds", type=float, default=600.0)
    parser.add_argument("--refresh-poll-seconds", type=float, default=1.5)
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=900)
    parser.add_argument(
        "--refresh-verify-response-timeout-seconds",
        type=int,
        default=90,
        help="Socket response timeout for each immediate post-refresh verify attempt.",
    )
    parser.add_argument(
        "--no-refresh-verify-timeout-recovery",
        action="store_false",
        dest="recover_refresh_verify_timeout",
        help="Disable automatic existing-output verify recovery after a post-refresh timeout.",
    )
    parser.set_defaults(recover_refresh_verify_timeout=True)
    parser.add_argument("--verify-recovery-initial-wait-seconds", type=float, default=3.0)
    parser.add_argument("--verify-recovery-timeout-seconds", type=float, default=300.0)
    parser.add_argument("--verify-recovery-poll-seconds", type=float, default=5.0)
    parser.add_argument("--verify-recovery-response-timeout-seconds", type=int, default=180)
    parser.add_argument("--redraw-count", type=int, default=2)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        result = run(parse_args())
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        raise
    print(json.dumps(result, ensure_ascii=False))
