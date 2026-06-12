"""Audit grass-related spline control handles in the Cubeless field level.

This is a read-only classification pass. It identifies short open 2-point
splines that are likely implementation anchors for grass/groundcover layers,
so they can be replaced later by volume-owned PCG without destructive cleanup.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIBLING_PYTHON_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless" / "Python"

if str(SIBLING_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(SIBLING_PYTHON_ROOT))

try:
    from unreal_mcp_server import UnrealConnection  # type: ignore  # noqa: E402
except ModuleNotFoundError:

    class UnrealConnection:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.host = os.environ.get("UNREAL_MCP_HOST", "127.0.0.1")
            self.port = int(os.environ.get("UNREAL_MCP_PORT", "55557"))
            self.timeout = int(os.environ.get("UNREAL_MCP_RESPONSE_TIMEOUT_SECONDS", "120"))

        def send_command(
            self,
            command: str,
            params: dict[str, Any] | None = None,
        ) -> dict[str, Any] | None:
            payload = {"type": command, "params": params or {}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.connect((self.host, self.port))
                sock.sendall(json.dumps(payload).encode("utf-8"))
                chunks: list[bytes] = []
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    try:
                        return json.loads(b"".join(chunks).decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
            return json.loads(b"".join(chunks).decode("utf-8")) if chunks else None


UNREAL_CODE = r"""
import json
import os
import time

import unreal


FIELD_LEVEL_PATH = "/Game/Cubeless/Map/LVL_Cubeless_PCG_Ecosystem_Field"
REPORT_NAME = "pcg_grass_spline_control_handles_audit.json"


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
    return unreal.EditorLevelLibrary.get_editor_world()


def all_level_actors():
    subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if subsystem_cls:
        subsystem = unreal.get_editor_subsystem(subsystem_cls)
        if subsystem:
            return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def tags(obj, prop):
    try:
        return [str(tag) for tag in obj.get_editor_property(prop)]
    except Exception:
        return []


def mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
        if mesh and hasattr(mesh, "get_path_name"):
            return mesh.get_path_name()
    except Exception:
        pass
    return ""


def category_for_component(component):
    text = (component.get_name() + " " + mesh_path(component)).lower()
    if any(token in text for token in ("grass", "fern", "groundleaf", "flower", "leaf", "foliage", "plant")):
        return "grass"
    if any(token in text for token in ("tree", "pine", "spruce", "conifer", "trunk")):
        return "tree"
    if any(token in text for token in ("rock", "stone", "boulder")):
        return "rock"
    return "other"


def instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def actor_bounds(actor):
    try:
        origin, extent = actor.get_actor_bounds(False)
        return {
            "origin": [round(float(origin.x), 3), round(float(origin.y), 3), round(float(origin.z), 3)],
            "extent": [round(float(extent.x), 3), round(float(extent.y), 3), round(float(extent.z), 3)],
        }
    except Exception:
        return None


def classify_actor(label, actor_tag_text, component_counts):
    text = (label + " " + actor_tag_text).lower()
    if "road" in text:
        return "keep_linear_road_or_road_feather"
    if "camera" in text or "bookmark" in text:
        return "ignore_camera_or_bookmark"
    if "landmark" in text:
        return "review_landmark_layer"
    if "qualitylayer" in text or "fulllandscapefill" in text or "groundcarpet" in text:
        return "replace_with_volume_owned_grass"
    if component_counts.get("grass", 0) > 0 and component_counts.get("tree", 0) == 0:
        return "replace_with_volume_owned_grass"
    if component_counts.get("grass", 0) > 0:
        return "review_mixed_grass_layer"
    return "keep_or_review_non_grass"


def audit():
    world = get_editor_world()
    if not world or not world.get_path_name().startswith(FIELD_LEVEL_PATH + "."):
        unreal.EditorLevelLibrary.load_level(FIELD_LEVEL_PATH)
        world = get_editor_world()

    report = {
        "success": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": world.get_path_name() if world else None,
        "policy": {
            "grass_groundcover": "prefer volume-owned PCG; do not keep dense short open-spline handles as final authoring controls",
            "open_two_point_splines": "keep for road/fence/guide/border/mask linear intent",
            "closed_splines": "keep for explicit 3+ point area patches",
            "cleanup": "classification only; no actor deletion or archive in this pass",
        },
        "summary": {
            "total_spline_actors": 0,
            "open_2_point_spline_actors": 0,
            "closed_spline_actors": 0,
            "grass_candidate_actor_count": 0,
            "grass_candidate_instance_count": 0,
        },
        "classification_counts": {},
        "classification_instances": {},
        "samples": [],
        "volume_candidate_bounds": None,
    }

    min_x = min_y = min_z = None
    max_x = max_y = max_z = None

    for actor in all_level_actors():
        label = actor_label(actor)
        splines = list(actor.get_components_by_class(unreal.SplineComponent))
        if not splines:
            continue

        actor_tags = tags(actor, "tags")
        actor_tag_text = " ".join(actor_tags)
        component_counts = {"grass": 0, "tree": 0, "rock": 0, "other": 0}
        component_instances = {"grass": 0, "tree": 0, "rock": 0, "other": 0}
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = category_for_component(component)
            count = instance_count(component)
            component_counts[category] += 1
            component_instances[category] += count

        has_open_2_point = False
        has_closed = False
        spline_rows = []
        for spline in splines:
            try:
                point_count = int(spline.get_number_of_spline_points())
                closed = bool(spline.is_closed_loop())
                length = float(spline.get_spline_length())
            except Exception:
                continue
            if point_count == 2 and not closed:
                has_open_2_point = True
            if closed:
                has_closed = True
            spline_rows.append(
                {
                    "component": spline.get_name(),
                    "point_count": point_count,
                    "closed_loop": closed,
                    "length_cm": round(length, 2),
                    "tags": tags(spline, "component_tags"),
                }
            )

        report["summary"]["total_spline_actors"] += 1
        if has_open_2_point:
            report["summary"]["open_2_point_spline_actors"] += 1
        if has_closed:
            report["summary"]["closed_spline_actors"] += 1

        classification = classify_actor(label, actor_tag_text, component_instances)
        report["classification_counts"][classification] = report["classification_counts"].get(classification, 0) + 1
        report["classification_instances"][classification] = report["classification_instances"].get(classification, 0) + component_instances.get("grass", 0)

        if classification in ("replace_with_volume_owned_grass", "review_mixed_grass_layer"):
            report["summary"]["grass_candidate_actor_count"] += 1
            report["summary"]["grass_candidate_instance_count"] += component_instances.get("grass", 0)
            bounds = actor_bounds(actor)
            if bounds:
                origin = bounds["origin"]
                extent = bounds["extent"]
                bx_min = origin[0] - extent[0]
                bx_max = origin[0] + extent[0]
                by_min = origin[1] - extent[1]
                by_max = origin[1] + extent[1]
                bz_min = origin[2] - extent[2]
                bz_max = origin[2] + extent[2]
                min_x = bx_min if min_x is None else min(min_x, bx_min)
                max_x = bx_max if max_x is None else max(max_x, bx_max)
                min_y = by_min if min_y is None else min(min_y, by_min)
                max_y = by_max if max_y is None else max(max_y, by_max)
                min_z = bz_min if min_z is None else min(min_z, bz_min)
                max_z = bz_max if max_z is None else max(max_z, bz_max)

        if len(report["samples"]) < 80:
            report["samples"].append(
                {
                    "actor": label,
                    "classification": classification,
                    "actor_tags": actor_tags,
                    "component_instances": component_instances,
                    "spline_rows": spline_rows[:4],
                }
            )

    if min_x is not None:
        report["volume_candidate_bounds"] = {
            "min": [round(min_x, 3), round(min_y, 3), round(min_z, 3)],
            "max": [round(max_x, 3), round(max_y, 3), round(max_z, 3)],
            "center": [
                round((min_x + max_x) * 0.5, 3),
                round((min_y + max_y) * 0.5, 3),
                round((min_z + max_z) * 0.5, 3),
            ],
            "extent": [
                round((max_x - min_x) * 0.5, 3),
                round((max_y - min_y) * 0.5, 3),
                round((max_z - min_z) * 0.5, 3),
            ],
        }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    report["report_path"] = report_path
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps(report, ensure_ascii=False))
    return report


audit()
"""


def parse_response(response: dict[str, Any] | None) -> dict[str, Any]:
    if not response:
        raise RuntimeError("No response from UnrealMCP bridge")
    if response.get("status") == "error":
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    result = response.get("result", response)
    logs = result.get("logs", []) if isinstance(result, dict) else []
    for line in reversed(logs):
        text = line.get("output", "") if isinstance(line, dict) else str(line)
        start = text.find("{")
        if start >= 0:
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                pass
    raise RuntimeError("Could not parse audit result")


def run(_args: argparse.Namespace) -> dict[str, Any]:
    response = UnrealConnection().send_command(
        "execute_python",
        {
            "code": UNREAL_CODE,
            "mode": "ExecuteFile",
            "description": "Audit grass spline control handles",
        },
    )
    return parse_response(response)


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Audit grass spline control handles.").parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
