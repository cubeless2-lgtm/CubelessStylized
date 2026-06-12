"""Regenerate and stabilize the Cubeless visual tree-frame PCG layer.

This is the supported editor-python path for regenerating
MCP_PCG_VisualTreeFrameLayer actors. The shared tree profile PCG graphs use
origin-centered CreatePoints templates, so a raw PCG regenerate is not enough:
Conifer instances must be re-centered around their owning actor afterwards.
"""

import importlib.util
import json
import math
import os
import time

import unreal


PREFIX = "MCP_PCG_VisualTreeFrameLayer"
REPORT_NAME = "CubelessVisualTreeFrameLayer_RegenerateAndStabilize.json"
STABILIZE_SCRIPT = os.path.join(
    os.path.dirname(__file__), "stabilize_pcg_tree_frame.py"
)
WAIT_SECONDS = 25.0
STATE_ATTR = "_cubeless_visual_tree_frame_regen_state"
ROAD_POINTS = [
    (4740.5, 10249.0),
    (11204.9, 12049.1),
    (17281.7, 16363.3),
    (23407.1, 20512.5),
    (29277.9, 25104.5),
    (35071.3, 29853.7),
    (40847.3, 34671.2),
    (46419.2, 39919.5),
]


def _load_stabilizer():
    spec = importlib.util.spec_from_file_location(
        "stabilize_pcg_tree_frame", STABILIZE_SCRIPT
    )
    if not spec or not spec.loader:
        raise RuntimeError("Failed to load stabilizer: " + STABILIZE_SCRIPT)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _road_segments():
    segments = []
    for index in range(len(ROAD_POINTS) - 1):
        ax, ay = ROAD_POINTS[index]
        bx, by = ROAD_POINTS[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        segments.append((ax, ay, dx, dy, length))
    return segments


ROAD_SEGMENTS = _road_segments()


def _road_distance(x, y):
    best = 10**12
    for ax, ay, dx, dy, length in ROAD_SEGMENTS:
        if length <= 0:
            continue
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (length * length)))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return str(mesh)


def _classify(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(
        token in text
        for token in ["tree", "pine", "spruce", "conifer", "trunk", "branch"]
    ):
        return "tree"
    if any(token in text for token in ["rock", "stone", "boulder"]):
        return "rock"
    if any(
        token in text
        for token in ["grass", "foliage", "leaf", "leaves", "fern", "plant", "flower"]
    ):
        return "grass"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _instance_location(component, index):
    try:
        return component.get_instance_transform(index, True).translation
    except Exception:
        return None


def _get_visual_tree_actors():
    return [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]


def _regenerate_pcg_components(actors):
    results = []
    for actor in actors:
        for component in actor.get_components_by_class(unreal.PCGComponent):
            name = component.get_name()
            if name == "PCG_MaterialPreview":
                continue
            entry = {"actor": actor.get_actor_label(), "component": name}
            try:
                component.cleanup(True)
                component.generate(True)
                try:
                    component.generate_local(True)
                except Exception as local_exc:
                    entry["generate_local_error"] = str(local_exc)
                entry["generated"] = True
            except Exception as exc:
                entry["generated"] = False
                entry["error"] = str(exc)
            results.append(entry)
    return results


def _summarize_regenerate_results(results):
    failed = [entry for entry in results if not entry.get("generated")]
    local_warnings = [
        entry for entry in results if entry.get("generate_local_error")
    ]
    return {
        "component_count": len(results),
        "failed_count": len(failed),
        "local_warning_count": len(local_warnings),
        "failed_sample": failed[:5],
        "local_warning_sample": local_warnings[:5],
    }


def _summarize_layer(actors):
    summary = {
        "actor_count": len(actors),
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "zero_actor_count": 0,
        "zero_actor_sample": [],
    }
    road_safety = {
        "tree_within_1800": 0,
        "tree_within_2400": 0,
        "rock_within_1800": 0,
        "rock_within_2400": 0,
        "samples": [],
    }

    for actor in actors:
        actor_total = 0
        components = []
        try:
            components.extend(
                actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)
            )
        except Exception:
            pass
        try:
            for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if component not in components:
                    components.append(component)
        except Exception:
            pass

        for component in components:
            count = _instance_count(component)
            category = _classify(component)
            actor_total += count
            summary["instances"]["all"] += count
            summary["instances"][category] += count

            if category not in ["tree", "rock"]:
                continue
            for index in range(count):
                location = _instance_location(component, index)
                if not location:
                    continue
                distance = _road_distance(location.x, location.y)
                if category == "tree":
                    if distance < 1800.0:
                        road_safety["tree_within_1800"] += 1
                    if distance < 2400.0:
                        road_safety["tree_within_2400"] += 1
                else:
                    if distance < 1800.0:
                        road_safety["rock_within_1800"] += 1
                    if distance < 2400.0:
                        road_safety["rock_within_2400"] += 1
                if distance < 2400.0 and len(road_safety["samples"]) < 20:
                    road_safety["samples"].append(
                        {
                            "actor": actor.get_actor_label(),
                            "component": component.get_name(),
                            "class": category,
                            "distance": round(distance, 2),
                            "x": round(location.x, 1),
                            "y": round(location.y, 1),
                            "z": round(location.z, 1),
                        }
                    )

        if actor_total == 0:
            summary["zero_actor_count"] += 1
            if len(summary["zero_actor_sample"]) < 20:
                summary["zero_actor_sample"].append(actor.get_actor_label())

    return summary, road_safety


def _finish_regenerate_and_stabilize(state):
    stabilizer = _load_stabilizer()
    stabilization_report = stabilizer.stabilize_tree_frame()

    actors = _get_visual_tree_actors()
    layer_summary, road_safety = _summarize_layer(actors)

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "wait_seconds": WAIT_SECONDS,
        "regenerate_results": state.get("regenerate_results", []),
        "stabilization": stabilization_report,
        "layer_summary": layer_summary,
        "road_safety": road_safety,
        "save_attempted": save_attempted,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    regen_summary = _summarize_regenerate_results(
        state.get("regenerate_results", [])
    )
    print(
        json.dumps(
            {
                "report": report_path,
                "timestamp": report["timestamp"],
                "prefix": PREFIX,
                "status": "completed",
                "regenerate_summary": regen_summary,
                "stabilization": {
                    "updated_instances": stabilization_report.get(
                        "updated_instances"
                    ),
                    "normalized_components": stabilization_report.get(
                        "normalized_components"
                    ),
                    "normalized_instances": stabilization_report.get(
                        "normalized_instances"
                    ),
                    "failure_count": stabilization_report.get("failure_count"),
                },
                "layer_summary": layer_summary,
                "road_safety": road_safety,
                "save_attempted": save_attempted,
            },
            ensure_ascii=False,
        )
    )
    return report


def regenerate_and_stabilize():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle") is not None:
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    actors = _get_visual_tree_actors()
    regenerate_results = _regenerate_pcg_components(actors)

    state = {
        "started_at": time.time(),
        "regenerate_results": regenerate_results,
        "handle": None,
        "completed": False,
    }

    def _tick(delta_seconds):
        if state["completed"]:
            return False
        if time.time() - state["started_at"] < WAIT_SECONDS:
            return True

        state["completed"] = True
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        try:
            state["final_report"] = _finish_regenerate_and_stabilize(state)
        except Exception as exc:
            state["error"] = str(exc)
            print(
                json.dumps(
                    {
                        "prefix": PREFIX,
                        "status": "failed",
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)

    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "status": "scheduled",
        "actor_count": len(actors),
        "wait_seconds": WAIT_SECONDS,
        "regenerate_summary": _summarize_regenerate_results(regenerate_results),
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    regenerate_and_stabilize()
