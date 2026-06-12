"""Add deterministic tree-cluster supplements around existing PCG tree output.

The source PCG tree graphs currently emit sparse, fixed-scale conifer points.
This pass keeps the original generated instances and adds road-safe companion
instances to the same PCG tree ISM components, so the validation view reads as
a forest canopy instead of isolated dots.
"""

import json
import math
import os
import random
import time

import unreal


REPORT_NAME = "CubelessPCGTreeClusterSupplement_Report.json"
ORIGINAL_COUNT_TAG_PREFIX = "CubelessTreeClusterOriginalCount="

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

LEVEL_BOUNDS = {
    "min_x": 2300.0,
    "max_x": 48800.0,
    "min_y": -1200.0,
    "max_y": 52800.0,
}


def _road_segments():
    segments = []
    for index in range(len(ROAD_POINTS) - 1):
        ax, ay = ROAD_POINTS[index]
        bx, by = ROAD_POINTS[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0.0:
            segments.append((ax, ay, dx, dy, length))
    return segments


ROAD_SEGMENTS = _road_segments()


def _road_distance(x, y):
    best = 10**12
    for ax, ay, dx, dy, length in ROAD_SEGMENTS:
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (length * length)))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best


def _in_bounds(x, y):
    return (
        LEVEL_BOUNDS["min_x"] <= x <= LEVEL_BOUNDS["max_x"]
        and LEVEL_BOUNDS["min_y"] <= y <= LEVEL_BOUNDS["max_y"]
    )


def _stable_rng(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return random.Random(seed)


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return ""


def _is_tree_component(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    return any(token in text for token in ["tree", "pine", "spruce", "conifer", "trunk"])


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _clamp_angle(value, limit=5.0):
    while value > 180.0:
        value -= 360.0
    while value < -180.0:
        value += 360.0
    return max(-limit, min(limit, value))


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _get_original_count(component):
    tags = [str(tag) for tag in component.get_editor_property("component_tags")]
    for tag in tags:
        if tag.startswith(ORIGINAL_COUNT_TAG_PREFIX):
            try:
                return int(tag[len(ORIGINAL_COUNT_TAG_PREFIX) :])
            except ValueError:
                pass
    count = _instance_count(component)
    tags.append(ORIGINAL_COUNT_TAG_PREFIX + str(count))
    component.set_editor_property("component_tags", tags)
    return count


def _reset_to_original_count(component, original_count):
    removed = 0
    while _instance_count(component) > original_count:
        index = _instance_count(component) - 1
        if component.remove_instance(index):
            removed += 1
        else:
            break
    return removed


def _sample_ground_z(world, x, y, fallback_z):
    start = unreal.Vector(x, y, 50000.0)
    end = unreal.Vector(x, y, -10000.0)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        values = hit.to_tuple()
    except Exception:
        return fallback_z

    if not values or not bool(values[0]):
        return fallback_z

    try:
        actor = values[9]
        actor_name = actor.get_name() if actor else ""
        actor_class = actor.get_class().get_name() if actor else ""
    except Exception:
        actor_name = ""
        actor_class = ""

    if "Landscape" not in actor_name and "Landscape" not in actor_class:
        return fallback_z

    try:
        return float(values[4].z)
    except Exception:
        return fallback_z


def _supplement_count(road_distance):
    if road_distance < 2800.0:
        return 0
    if road_distance < 4200.0:
        return 1
    if road_distance < 7000.0:
        return 2
    return 4


def supplement_tree_clusters():
    world = unreal.EditorLevelLibrary.get_editor_world()
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tree_components": 0,
        "original_tree_instances": 0,
        "removed_previous_supplements": 0,
        "added_supplements": 0,
        "skipped_candidates": 0,
        "tree_near_road_after": {"within_1800": 0, "within_2400": 0},
        "pitch_roll_violations_after": 0,
        "samples": [],
        "failures": [],
    }

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not _is_tree_component(component):
                continue

            original_count = _get_original_count(component)
            if original_count <= 0:
                continue

            report["tree_components"] += 1
            report["original_tree_instances"] += original_count
            report["removed_previous_supplements"] += _reset_to_original_count(
                component, original_count
            )

            for index in range(original_count):
                try:
                    base_transform = component.get_instance_transform(index, True)
                    base_location = base_transform.translation
                    base_distance = _road_distance(base_location.x, base_location.y)
                    clone_count = _supplement_count(base_distance)
                    if clone_count <= 0:
                        continue

                    base_rotator = base_transform.rotation.rotator()
                    rng = _stable_rng(label, component.get_name(), index, "tree_cluster")

                    for clone_index in range(clone_count):
                        candidate = None
                        for _attempt in range(8):
                            radius = rng.uniform(520.0, 1850.0)
                            angle = rng.uniform(0.0, math.tau)
                            x = base_location.x + math.cos(angle) * radius
                            y = base_location.y + math.sin(angle) * radius
                            if not _in_bounds(x, y):
                                continue
                            if _road_distance(x, y) < 2600.0:
                                continue
                            z = _sample_ground_z(world, x, y, base_location.z)
                            candidate = (x, y, z)
                            break

                        if not candidate:
                            report["skipped_candidates"] += 1
                            continue

                        x, y, z = candidate
                        s = rng.uniform(1.65, 3.10)
                        yaw = base_rotator.yaw + rng.uniform(-42.0, 42.0)
                        clone_transform = unreal.Transform()
                        clone_transform.translation = unreal.Vector(x, y, z)
                        clone_transform.rotation = _make_rotator(
                            _clamp_angle(base_rotator.pitch),
                            yaw,
                            _clamp_angle(base_rotator.roll),
                        ).quaternion()
                        clone_transform.scale3d = unreal.Vector(
                            s,
                            s,
                            s * rng.uniform(1.0, 1.18),
                        )
                        component.add_instance_world_space(clone_transform)
                        report["added_supplements"] += 1
                        if len(report["samples"]) < 24:
                            report["samples"].append(
                                {
                                    "actor": label,
                                    "component": component.get_name(),
                                    "base_index": index,
                                    "road_distance": round(_road_distance(x, y), 1),
                                    "scale": [
                                        round(clone_transform.scale3d.x, 2),
                                        round(clone_transform.scale3d.y, 2),
                                        round(clone_transform.scale3d.z, 2),
                                    ],
                                }
                            )
                except Exception as exc:
                    if len(report["failures"]) < 40:
                        report["failures"].append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "error": str(exc),
                            }
                        )

            try:
                component.mark_render_state_dirty()
            except Exception:
                pass

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not actor.get_actor_label().startswith("MCP_PCG_"):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not _is_tree_component(component):
                continue
            for index in range(_instance_count(component)):
                try:
                    transform = component.get_instance_transform(index, False)
                    rotator = transform.rotation.rotator()
                    if abs(_clamp_angle(rotator.pitch) - rotator.pitch) > 0.01:
                        report["pitch_roll_violations_after"] += 1
                    if abs(_clamp_angle(rotator.roll) - rotator.roll) > 0.01:
                        report["pitch_roll_violations_after"] += 1
                    location = component.get_instance_transform(index, True).translation
                    distance = _road_distance(location.x, location.y)
                    if distance < 1800.0:
                        report["tree_near_road_after"]["within_1800"] += 1
                    if distance < 2400.0:
                        report["tree_near_road_after"]["within_2400"] += 1
                except Exception:
                    pass

    report["failure_count"] = len(report["failures"])
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    supplement_tree_clusters()
