"""Repair current Landscape PCG placement rule violations.

This is scoped to the validation Landscape map: it removes tree/rock instances
inside the road clearance corridor and clamps rock tilt to the project limit.
Grass is not modified here because it is validated against Landscape normals.
"""

import json
import math
import os
import time

import unreal


REPORT_NAME = "pcg_landscape_quality_rules_repair_report.json"
WORLD_UP = unreal.Vector(0.0, 0.0, 1.0)
ROAD_ACTOR_LABEL = "MCP_PCG_RoadMaskSpline_ClearForest_Test"
ROAD_SPLINE_NAME = "Road_SourceSpline"
TREE_CLEARANCE = 7800.0
ROCK_CLEARANCE = 4800.0
ROCK_TILT_LIMIT_DEG = 5.0
ROCK_TILT_TARGET_DEG = 0.0


def _all_level_actors():
    subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if subsystem_cls:
        subsystem = unreal.get_editor_subsystem(subsystem_cls)
        if subsystem:
            return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def _actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return ""


def _category(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(token in text for token in ("tree", "pine", "spruce", "conifer", "trunk")):
        return "tree"
    if any(token in text for token in ("rock", "stone", "boulder")):
        return "rock"
    if any(
        token in text
        for token in ("grass", "fern", "groundleaf", "flower", "leaf", "foliage", "plant")
    ):
        return "grass"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _vector_size(vector):
    return math.sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z)


def _normalized(vector, fallback=None):
    size = _vector_size(vector)
    if size <= 1.0e-6:
        return fallback or WORLD_UP
    return unreal.Vector(vector.x / size, vector.y / size, vector.z / size)


def _angle_degrees(a, b):
    aa = _normalized(a)
    bb = _normalized(b)
    dot = max(-1.0, min(1.0, aa.x * bb.x + aa.y * bb.y + aa.z * bb.z))
    return math.degrees(math.acos(dot))


def _quat_up(quat):
    try:
        return _normalized(unreal.MathLibrary.quat_rotate_vector(quat, WORLD_UP))
    except Exception:
        x, y, z, w = quat.x, quat.y, quat.z, quat.w
        return _normalized(
            unreal.Vector(
                2.0 * (x * z + w * y),
                2.0 * (y * z - w * x),
                1.0 - 2.0 * (x * x + y * y),
            )
        )


def _norm_angle(value):
    while value > 180.0:
        value -= 360.0
    while value < -180.0:
        value += 360.0
    return value


def _clamp(value, limit):
    return max(-limit, min(limit, value))


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _find_actor(label):
    for actor in _all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _find_road_spline():
    actor = _find_actor(ROAD_ACTOR_LABEL)
    if not actor:
        return None
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        return None
    for spline in splines:
        if spline.get_name() == ROAD_SPLINE_NAME:
            return spline
    return splines[0]


def _route_points_from_spline(spline):
    if not spline:
        return []
    point_count = int(spline.get_number_of_spline_points())
    if point_count < 2:
        return []
    points = []
    for index in range(point_count):
        location = spline.get_location_at_spline_point(index, unreal.SplineCoordinateSpace.WORLD)
        points.append((float(location.x), float(location.y)))
    return points


def _segments(points):
    out = []
    for index in range(len(points) - 1):
        ax, ay = points[index]
        bx, by = points[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0.0:
            out.append((ax, ay, dx, dy, length))
    return out


def _route_distance(x, y, route_segments):
    if not route_segments:
        return None
    best = 10.0**12
    for ax, ay, dx, dy, length in route_segments:
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (length * length)))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best


def _dirty_names():
    packages = []
    try:
        utils = unreal.EditorLoadingAndSavingUtils
        packages = list(utils.get_dirty_content_packages() or []) + list(utils.get_dirty_map_packages() or [])
    except Exception:
        pass
    names = []
    for package in packages:
        try:
            names.append(package.get_name())
        except Exception:
            names.append(str(package))
    return sorted(set(names))


def repair_pcg_landscape_quality_rules():
    world = unreal.EditorLevelLibrary.get_editor_world()
    route_points = _route_points_from_spline(_find_road_spline())
    route_segments = _segments(route_points)
    if not route_segments:
        raise RuntimeError("Road spline is missing or invalid; repair cannot evaluate clearance.")

    report = {
        "success": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": world.get_path_name() if world else None,
        "road": {
            "actor": ROAD_ACTOR_LABEL,
            "spline": ROAD_SPLINE_NAME,
            "point_count": len(route_points),
            "segment_count": len(route_segments),
        },
        "limits": {
            "tree_clearance_cm": TREE_CLEARANCE,
            "rock_clearance_cm": ROCK_CLEARANCE,
            "rock_tilt_limit_deg": ROCK_TILT_LIMIT_DEG,
            "rock_tilt_target_deg": ROCK_TILT_TARGET_DEG,
        },
        "removed": {"tree": 0, "rock": 0},
        "rock_tilt_updates": 0,
        "scanned": {"tree": 0, "rock": 0},
        "samples": [],
        "failures": [],
        "dirty_before": _dirty_names(),
    }

    touched_components = set()
    removals_by_component = {}

    for actor in _all_level_actors():
        label = _actor_label(actor)
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _category(component)
            if category not in ("tree", "rock"):
                continue

            count = _instance_count(component)
            report["scanned"][category] += count
            remove_indices = removals_by_component.setdefault(component, [])

            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, True)
                    location = transform.translation
                    distance = _route_distance(location.x, location.y, route_segments)
                    if category == "tree" and distance is not None and distance < TREE_CLEARANCE:
                        remove_indices.append(index)
                        report["removed"]["tree"] += 1
                        if len(report["samples"]) < 40:
                            report["samples"].append(
                                {
                                    "action": "remove_tree_clearance",
                                    "actor": label,
                                    "component": component.get_name(),
                                    "index": index,
                                    "distance_cm": round(distance, 4),
                                }
                            )
                        continue
                    if category == "rock" and distance is not None and distance < ROCK_CLEARANCE:
                        remove_indices.append(index)
                        report["removed"]["rock"] += 1
                        if len(report["samples"]) < 40:
                            report["samples"].append(
                                {
                                    "action": "remove_rock_clearance",
                                    "actor": label,
                                    "component": component.get_name(),
                                    "index": index,
                                    "distance_cm": round(distance, 4),
                                }
                            )
                        continue

                    if category != "rock":
                        continue

                    up_angle = _angle_degrees(_quat_up(transform.rotation), WORLD_UP)
                    if up_angle <= ROCK_TILT_LIMIT_DEG:
                        continue

                    rotator = transform.rotation.rotator()
                    pitch = _clamp(_norm_angle(rotator.pitch), ROCK_TILT_TARGET_DEG)
                    yaw = _norm_angle(rotator.yaw)
                    roll = _clamp(_norm_angle(rotator.roll), ROCK_TILT_TARGET_DEG)
                    transform.rotation = _make_rotator(pitch, yaw, roll).quaternion()

                    if component.update_instance_transform(index, transform, True, False, True):
                        report["rock_tilt_updates"] += 1
                        touched_components.add(component)
                        if len(report["samples"]) < 40:
                            report["samples"].append(
                                {
                                    "action": "clamp_rock_tilt",
                                    "actor": label,
                                    "component": component.get_name(),
                                    "index": index,
                                    "before_world_up_angle_deg": round(up_angle, 4),
                                    "after_rotator": [round(pitch, 4), round(yaw, 4), round(roll, 4)],
                                }
                            )
                    else:
                        if len(report["failures"]) < 40:
                            report["failures"].append(
                                {
                                    "actor": label,
                                    "component": component.get_name(),
                                    "index": index,
                                    "reason": "update_instance_transform returned false",
                                }
                            )
                except Exception as exc:
                    if len(report["failures"]) < 40:
                        report["failures"].append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "reason": str(exc),
                            }
                        )

    for component, indices in removals_by_component.items():
        if not indices:
            continue
        touched_components.add(component)
        for index in sorted(set(indices), reverse=True):
            try:
                component.remove_instance(index)
            except Exception as exc:
                if len(report["failures"]) < 40:
                    report["failures"].append(
                        {
                            "component": component.get_name(),
                            "index": index,
                            "reason": "remove_instance failed: " + str(exc),
                        }
                    )

    for component in touched_components:
        try:
            component.mark_render_state_dirty()
        except Exception:
            pass

    report["dirty_after_repair"] = _dirty_names()
    try:
        report["save_dirty_packages_result"] = bool(
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        )
    except Exception as exc:
        report["save_dirty_packages_result"] = "failed: " + str(exc)
    report["dirty_after_save"] = _dirty_names()
    report["failure_count"] = len(report["failures"])

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = report_path
    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    repair_pcg_landscape_quality_rules()
