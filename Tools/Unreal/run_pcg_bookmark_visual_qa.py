"""Run a fast PCG screenshot/visual QA pass through the UnrealMCP bridge.

The pass is intentionally read-only for Unreal assets: it gathers current level
PCG/ISM summary data, captures the active viewport by default, optionally
captures existing viewport bookmarks without creating or overwriting slots, and
writes a generated JSON report under Saved/MCP_PCG.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
import textwrap
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIBLING_MCP_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless"
SIBLING_PYTHON_ROOT = SIBLING_MCP_ROOT / "Python"
IMAGE_TOOL_ROOT = PROJECT_ROOT / "Tools" / "Image"

if str(SIBLING_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(SIBLING_PYTHON_ROOT))
if str(IMAGE_TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(IMAGE_TOOL_ROOT))

try:
    from ensure_review_image_opaque_alpha import ensure_review_image_opaque_alpha  # type: ignore  # noqa: E402
except Exception as exc:  # pragma: no cover - reported in QA output.
    ensure_review_image_opaque_alpha = None  # type: ignore[assignment]
    REVIEW_IMAGE_ALPHA_HOOK_IMPORT_ERROR = str(exc)
else:
    REVIEW_IMAGE_ALPHA_HOOK_IMPORT_ERROR = ""

try:
    from unreal_mcp_server import UnrealConnection  # type: ignore  # noqa: E402
except ModuleNotFoundError:
    class UnrealConnection:  # type: ignore[no-redef]
        """Minimal UnrealMCP socket client for running outside the MCP venv."""

        def __init__(self) -> None:
            self.host = os.environ.get("UNREAL_MCP_HOST", "127.0.0.1")
            self.port = int(os.environ.get("UNREAL_MCP_PORT", "55557"))
            self.timeout = int(os.environ.get("UNREAL_MCP_RESPONSE_TIMEOUT_SECONDS", "120"))

        def send_command(
            self,
            command: str,
            params: dict[str, Any] | None = None,
        ) -> dict[str, Any] | None:
            command_obj = {"type": command, "params": params or {}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.connect((self.host, self.port))
                sock.sendall(json.dumps(command_obj).encode("utf-8"))

                chunks: list[bytes] = []
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        if not chunks:
                            return None
                        break
                    chunks.append(chunk)
                    data = b"".join(chunks)
                    try:
                        return json.loads(data.decode("utf-8"))
                    except json.JSONDecodeError:
                        continue

            return json.loads(b"".join(chunks).decode("utf-8"))


UNREAL_STATS_CODE = r"""
import json
import os
import time

import unreal


def get_editor_world():
    subsystem_cls = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_cls:
        try:
            subsystem = unreal.get_editor_subsystem(subsystem_cls)
            world = subsystem.get_editor_world() if subsystem else None
            if world:
                return world
        except Exception:
            pass
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def get_all_level_actors():
    actor_subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if actor_subsystem_cls:
        actor_subsystem = unreal.get_editor_subsystem(actor_subsystem_cls)
        if actor_subsystem:
            return list(actor_subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return ""


def instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def classify_component(actor, component):
    path_text = mesh_path(component).lower()
    component_text = component.get_name().lower()
    actor_text = " ".join([actor_label(actor), actor.get_name()]).lower()
    mesh_component_text = " ".join([path_text, component_text])

    if any(token in mesh_component_text for token in ("grass", "fern", "groundleaf", "flower", "leaf", "plant")):
        return "grass"
    if any(token in mesh_component_text for token in ("tree", "pine", "conifer")):
        return "tree"
    if any(token in mesh_component_text for token in ("rock", "stone", "boulder")):
        return "rock"
    if "fence" in mesh_component_text or "fence" in actor_text:
        return "fence"
    if any(token in " ".join([mesh_component_text, actor_text]) for token in ("road", "spline", "asphalt", "gravel", "duff")):
        return "road"
    return "other"


def add_category(summary, category, component, count, path):
    item = summary.setdefault(
        category,
        {
            "component_count": 0,
            "instance_count": 0,
            "top_meshes": {},
            "sample_components": [],
        },
    )
    item["component_count"] += 1
    item["instance_count"] += count
    if path:
        item["top_meshes"][path] = item["top_meshes"].get(path, 0) + count
    if len(item["sample_components"]) < 10:
        item["sample_components"].append(
            {
                "component": component.get_name(),
                "instance_count": count,
                "mesh": path,
            }
        )


def compact_category(summary):
    for item in summary.values():
        item["top_meshes"] = [
            {"mesh": mesh, "instance_count": count}
            for mesh, count in sorted(
                item["top_meshes"].items(),
                key=lambda entry: entry[1],
                reverse=True,
            )[:12]
        ]


def dirty_packages():
    try:
        packages = list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() or [])
        packages += list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or [])
    except Exception:
        packages = []
    names = []
    for package in packages:
        try:
            names.append(package.get_name())
        except Exception:
            names.append(str(package))
    return sorted(set(names))


world = get_editor_world()
actors = get_all_level_actors()
pcg_components = []
component_summary = {}
pcg_actor_labels = []
landscape_labels = []
camera_like_labels = []
spline_actor_labels = []

for actor in actors:
    label = actor_label(actor)
    class_name = actor.get_class().get_name()
    if "Landscape" in class_name or "Landscape" in label:
        landscape_labels.append(label)
    if "Camera" in class_name or "Camera" in label or "Bookmark" in label:
        camera_like_labels.append(label)
    if "Spline" in class_name or "Spline" in label or "Road" in label:
        spline_actor_labels.append(label)

    actor_has_pcg = False
    for component in actor.get_components_by_class(unreal.ActorComponent):
        component_class = component.get_class().get_name()
        if "PCG" in component_class:
            actor_has_pcg = True
            pcg_components.append(
                {
                    "actor": label,
                    "component": component.get_name(),
                    "component_class": component_class,
                }
            )
    if actor_has_pcg:
        pcg_actor_labels.append(label)

    ism_components = []
    try:
        ism_components.extend(actor.get_components_by_class(unreal.InstancedStaticMeshComponent))
    except Exception:
        pass
    hism_cls = getattr(unreal, "HierarchicalInstancedStaticMeshComponent", None)
    if hism_cls:
        try:
            ism_components.extend(actor.get_components_by_class(hism_cls))
        except Exception:
            pass

    seen = set()
    for component in ism_components:
        key = component.get_path_name()
        if key in seen:
            continue
        seen.add(key)
        count = instance_count(component)
        if count <= 0:
            continue
        path = mesh_path(component)
        add_category(component_summary, classify_component(actor, component), component, count, path)

compact_category(component_summary)

report_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
os.makedirs(report_dir, exist_ok=True)
report_path = os.path.join(report_dir, "pcg_bookmark_visual_qa_level_stats.json")
RESULT = {
    "success": True,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "world": world.get_path_name() if world else None,
    "actor_count": len(actors),
    "landscape_count": len(landscape_labels),
    "landscape_labels_sample": landscape_labels[:20],
    "pcg_component_count": len(pcg_components),
    "pcg_components_sample": pcg_components[:30],
    "pcg_actor_labels_sample": pcg_actor_labels[:30],
    "component_summary": component_summary,
    "camera_like_labels_sample": camera_like_labels[:30],
    "spline_actor_labels_sample": spline_actor_labels[:30],
    "dirty_packages": dirty_packages(),
    "report_path": report_path,
}
with open(report_path, "w", encoding="utf-8") as handle:
    json.dump(RESULT, handle, indent=2, ensure_ascii=False)
print(json.dumps(RESULT, ensure_ascii=False))
"""


UNREAL_SET_GAME_VIEW_CODE = r"""
import json

import unreal


TARGET_GAME_VIEW = __TARGET_GAME_VIEW__

result = {
    "success": False,
    "target_game_view": TARGET_GAME_VIEW,
    "previous_game_view": None,
    "current_game_view": None,
}

try:
    subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not subsystem:
        raise RuntimeError("LevelEditorSubsystem is unavailable")
    result["previous_game_view"] = bool(subsystem.editor_get_game_view())
    subsystem.editor_set_game_view(bool(TARGET_GAME_VIEW))
    subsystem.editor_invalidate_viewports()
    result["current_game_view"] = bool(subsystem.editor_get_game_view())
    result["success"] = result["current_game_view"] == bool(TARGET_GAME_VIEW)
except Exception as exc:
    result["error"] = str(exc)

print(json.dumps(result, ensure_ascii=False))
"""


def command_succeeded(response: dict[str, Any] | None) -> bool:
    if not response:
        return False
    return response.get("status") == "success" or response.get("success") is True


def response_result(response: dict[str, Any] | None) -> dict[str, Any]:
    if not response:
        return {}
    result = response.get("result", response)
    return result if isinstance(result, dict) else {"result": result}


def parse_execute_python_log_json(response: dict[str, Any] | None) -> dict[str, Any]:
    result = response_result(response)
    parsed_logs: list[dict[str, Any]] = []
    for log_item in result.get("logs", []):
        if not isinstance(log_item, dict):
            continue
        output = str(log_item.get("output", "")).strip()
        if not output.startswith("{"):
            continue
        try:
            parsed_logs.append(json.loads(output))
        except json.JSONDecodeError:
            continue
    if not parsed_logs:
        return result

    parsed = parsed_logs[-1]
    parsed["unreal_execute_summary"] = {
        "success": result.get("success"),
        "command_result": result.get("command_result"),
        "log_count": len(result.get("logs", [])),
    }
    return parsed


def send(unreal: UnrealConnection, command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = unreal.send_command(command, params or {})
    if not command_succeeded(response):
        raise RuntimeError(f"{command} failed: {json.dumps(response, ensure_ascii=False)}")
    return response


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def apply_review_image_alpha_hook(path: Path) -> dict[str, Any]:
    if ensure_review_image_opaque_alpha is None:
        return {
            "success": False,
            "input_path": str(path),
            "opaque_for_review": False,
            "error": REVIEW_IMAGE_ALPHA_HOOK_IMPORT_ERROR or "review image alpha hook import failed",
        }
    try:
        return ensure_review_image_opaque_alpha(path, in_place=True)
    except Exception as exc:
        return {
            "success": False,
            "input_path": str(path),
            "opaque_for_review": False,
            "error": str(exc),
        }


def set_editor_game_view(unreal: UnrealConnection, enabled: bool) -> dict[str, Any]:
    code = UNREAL_SET_GAME_VIEW_CODE.replace(
        "__TARGET_GAME_VIEW__",
        "True" if enabled else "False",
    )
    response = send(
        unreal,
        "execute_python",
        {"code": code, "mode": "ExecuteFile"},
    )
    result = parse_execute_python_log_json(response)
    if not result.get("success"):
        raise RuntimeError(f"editor_set_game_view failed: {json.dumps(result, ensure_ascii=False)}")
    return result


def capture_bookmark(
    unreal: UnrealConnection,
    output_dir: Path,
    bookmark_index: int,
    redraw_count: int,
    output_prefix: str,
) -> dict[str, Any]:
    return capture_viewport(
        unreal,
        output_dir,
        "bookmark",
        redraw_count,
        output_prefix,
        bookmark_index=bookmark_index,
    )


def capture_viewport(
    unreal: UnrealConnection,
    output_dir: Path,
    capture_source: str,
    redraw_count: int,
    output_prefix: str,
    bookmark_index: int | None = None,
) -> dict[str, Any]:
    safe_prefix = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in output_prefix
    ).strip("_")
    if not safe_prefix:
        safe_prefix = "pcg"
    suffix = "active_viewport" if bookmark_index is None else f"bookmark{bookmark_index}"
    filepath = output_dir / f"{safe_prefix}_{suffix}_visual_qa.png"
    params: dict[str, Any] = {
        "filepath": str(filepath),
        "redraw_count": redraw_count,
    }
    if bookmark_index is not None:
        params["bookmark_index"] = bookmark_index
    response = send(
        unreal,
        "capture_viewport_bookmark_screenshot",
        params,
    )
    result = response_result(response)
    result["capture_source"] = capture_source
    result["requested_bookmark_index"] = bookmark_index
    file_path = Path(result.get("filepath") or filepath)
    result["exists_on_disk"] = file_path.exists()
    if file_path.exists():
        result["review_image_alpha"] = apply_review_image_alpha_hook(file_path)
        result["sha256"] = sha256_file(file_path)
        result["file_size"] = file_path.stat().st_size
    return result


def category_instance_count(level_stats: dict[str, Any], category: str) -> int:
    try:
        return int(
            level_stats.get("component_summary", {})
            .get(category, {})
            .get("instance_count", 0)
        )
    except (TypeError, ValueError):
        return 0


def build_content_review(
    level_stats: dict[str, Any],
    captures: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    grass_count = category_instance_count(level_stats, "grass")
    tree_count = category_instance_count(level_stats, "tree")
    rock_count = category_instance_count(level_stats, "rock")
    world = str(level_stats.get("world") or "")
    warnings: list[str] = []

    if int(level_stats.get("landscape_count", 0) or 0) <= 0:
        warnings.append("No Landscape actor was detected in the current level.")
    if int(level_stats.get("pcg_component_count", 0) or 0) <= 0:
        warnings.append("No PCG components were detected in the current level.")
    if grass_count < args.min_grass_instances:
        warnings.append(
            f"Grass density is below the visual QA target "
            f"({grass_count} < {args.min_grass_instances})."
        )
    if tree_count < args.min_tree_instances:
        warnings.append(
            f"Tree density is below the visual QA target "
            f"({tree_count} < {args.min_tree_instances})."
        )
    if rock_count < args.min_rock_instances:
        warnings.append(
            f"Rock density is below the visual QA target "
            f"({rock_count} < {args.min_rock_instances})."
        )
    if "_MCP_Temp" in world:
        warnings.append(
            "Current world is under /Game/_MCP_Temp; treat captures as validation output, not production art approval."
        )

    capture_hashes = [capture.get("sha256") for capture in captures if capture.get("sha256")]
    if len(capture_hashes) != len(set(capture_hashes)):
        warnings.append("At least two screenshot captures have identical hashes; check for stale viewport reuse.")

    visual_density_pass = (
        grass_count >= args.min_grass_instances
        and tree_count >= args.min_tree_instances
        and rock_count >= args.min_rock_instances
        and int(level_stats.get("landscape_count", 0) or 0) > 0
        and int(level_stats.get("pcg_component_count", 0) or 0) > 0
    )

    return {
        "visual_density_pass": visual_density_pass,
        "grass_instance_count": grass_count,
        "tree_instance_count": tree_count,
        "rock_instance_count": rock_count,
        "min_grass_instances": args.min_grass_instances,
        "min_tree_instances": args.min_tree_instances,
        "min_rock_instances": args.min_rock_instances,
        "warnings": warnings,
    }


def build_capture_route_health(captures: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    capture_hashes = [capture.get("sha256") for capture in captures if capture.get("sha256")]
    duplicate_hash_count = len(capture_hashes) - len(set(capture_hashes))
    checks = {
        "requires_at_least_one_capture": bool(captures),
        "captures_exist_on_disk": all(capture.get("exists_on_disk") for capture in captures),
        "captures_have_nonzero_size": all(int(capture.get("file_size", 0) or 0) > 0 for capture in captures),
        "review_images_have_alpha_255": all(
            bool(capture.get("review_image_alpha", {}).get("opaque_for_review"))
            for capture in captures
        ),
        "capture_must_not_add_dirty_packages": all(
            int(capture.get("dirty_package_added_count", 0) or 0) == 0
            for capture in captures
        ),
        "capture_hashes_unique_when_multiple": (
            True
            if args.allow_duplicate_capture_hashes or len(capture_hashes) <= 1
            else duplicate_hash_count == 0
        ),
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "duplicate_hash_count": duplicate_hash_count,
        "capture_count": len(captures),
        "capture_sources": [capture.get("capture_source") for capture in captures],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    unreal = UnrealConnection()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    started_at = time.monotonic()
    level_stats_response = send(
        unreal,
        "execute_python",
        {"code": UNREAL_STATS_CODE, "mode": "ExecuteFile"},
    )
    level_stats = parse_execute_python_log_json(level_stats_response)

    bookmarks = response_result(send(unreal, "list_viewport_bookmarks", {}))
    existing = set(int(value) for value in bookmarks.get("existing_indices", []))

    captures = []
    skipped = []
    clean_game_view_state: dict[str, Any] = {
        "requested": bool(args.clean_game_view),
        "set_before_capture": None,
        "restore_after_capture": None,
    }
    previous_game_view: bool | None = None
    if args.clean_game_view:
        clean_game_view_state["set_before_capture"] = set_editor_game_view(unreal, True)
        previous_game_view = bool(
            clean_game_view_state["set_before_capture"].get("previous_game_view", False)
        )
    try:
        if not args.no_active_viewport:
            captures.append(
                capture_viewport(
                    unreal,
                    output_dir,
                    "active_viewport",
                    args.redraw_count,
                    args.output_prefix,
                )
            )
        for bookmark_index in args.bookmarks:
            if bookmark_index not in existing:
                skipped.append({"bookmark_index": bookmark_index, "reason": "missing"})
                continue
            captures.append(
                capture_bookmark(
                    unreal,
                    output_dir,
                    bookmark_index,
                    args.redraw_count,
                    args.output_prefix,
                )
            )
    finally:
        if args.clean_game_view and previous_game_view is not None:
            clean_game_view_state["restore_after_capture"] = set_editor_game_view(
                unreal,
                previous_game_view,
            )

    capture_route_health = build_capture_route_health(captures, args)
    capture_qa_pass = bool(capture_route_health.get("pass"))
    content_review = build_content_review(level_stats, captures, args)

    report = {
        "success": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": str(PROJECT_ROOT),
        "sibling_python_root": str(SIBLING_PYTHON_ROOT),
        "level_stats": level_stats,
        "bookmarks": bookmarks,
        "captures": captures,
        "skipped_bookmarks": skipped,
        "capture_qa_pass": capture_qa_pass,
        "screenshot_validation_route": {
            "default_capture": "active_viewport",
            "native_command": "capture_viewport_bookmark_screenshot",
            "review_image_alpha_hook": "Tools/Image/ensure_review_image_opaque_alpha.py",
            "display_alpha_policy": "user-facing review screenshots are rewritten so every alpha value is 255 before hashing/reporting",
            "active_viewport_enabled": not args.no_active_viewport,
            "clean_game_view": clean_game_view_state,
            "requested_bookmarks": args.bookmarks,
            "existing_bookmarks": sorted(existing),
            "bookmark_behavior": "optional existing-slot capture only; missing slots are skipped and no slots are created or overwritten",
        },
        "capture_route_health": capture_route_health,
        "content_review": content_review,
        "qa_pass": capture_qa_pass
        if args.capture_only
        else capture_qa_pass and bool(content_review.get("visual_density_pass")),
        "qa_rules": {
            "requires_at_least_one_capture": True,
            "capture_must_exist_on_disk": True,
            "capture_must_have_nonzero_size": True,
            "review_image_alpha_must_be_255": True,
            "screenshot_capture_must_not_add_dirty_packages": True,
            "capture_hashes_unique_when_multiple": not args.allow_duplicate_capture_hashes,
            "visual_density_required": not args.capture_only,
        },
    }

    report_path = args.report_path
    report["report_path"] = str(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    default_saved = PROJECT_ROOT / "Saved"
    parser = argparse.ArgumentParser(
        description="Capture active-viewport/bookmark screenshots and current PCG level stats through UnrealMCP."
    )
    parser.add_argument(
        "--bookmarks",
        nargs="+",
        type=int,
        default=[],
        help="Optional existing viewport bookmark indices to capture after the active viewport.",
    )
    parser.add_argument(
        "--no-active-viewport",
        action="store_true",
        help="Skip the default active viewport capture and capture only explicitly requested bookmarks.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_saved / "MCP_Screenshots",
        help="Directory for generated screenshot PNGs.",
    )
    parser.add_argument(
        "--output-prefix",
        default="pcg",
        help="Filename prefix for generated screenshot PNGs.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=default_saved / "MCP_PCG" / "pcg_bookmark_visual_qa_report.json",
        help="Generated JSON report path.",
    )
    parser.add_argument(
        "--redraw-count",
        type=int,
        default=2,
        help="Number of forced viewport redraws before native pixel readback.",
    )
    parser.add_argument(
        "--min-grass-instances",
        type=int,
        default=1000,
        help="Minimum grass/groundcover instances required for visual-density pass.",
    )
    parser.add_argument(
        "--min-tree-instances",
        type=int,
        default=100,
        help="Minimum tree instances required for visual-density pass.",
    )
    parser.add_argument(
        "--min-rock-instances",
        type=int,
        default=0,
        help="Minimum rock instances required for visual-density pass.",
    )
    parser.add_argument(
        "--capture-only",
        action="store_true",
        help="Do not fail qa_pass on visual-density warnings.",
    )
    parser.add_argument(
        "--clean-game-view",
        action="store_true",
        help="Temporarily enable editor game view during capture and restore the previous state afterwards.",
    )
    parser.add_argument(
        "--allow-duplicate-capture-hashes",
        action="store_true",
        help="Do not fail capture_qa_pass when multiple requested captures produce identical image hashes.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        result = run(parse_args())
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        raise
    print(json.dumps(result, ensure_ascii=False))
