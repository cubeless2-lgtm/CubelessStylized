"""Validate current Landscape PCG placement quality rules without editing assets."""

import json
import math
import os
import time

import unreal


REPORT_NAME = "pcg_landscape_quality_rules_report.json"
WORLD_UP = unreal.Vector(0.0, 0.0, 1.0)
ROAD_ACTOR_LABEL = "MCP_PCG_RoadMaskSpline_ClearForest_Test"
ROAD_SPLINE_NAME = "Road_SourceSpline"

TREE_TILT_LIMIT_DEG = 5.0
ROCK_TILT_LIMIT_DEG = 5.0
GRASS_NORMAL_P95_LIMIT_DEG = 8.0
GRASS_CORE_CLEARANCE = 2600.0
TREE_CLEARANCE = 7800.0
ROCK_CLEARANCE = 4800.0


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


def _percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * fraction))
    return ordered[max(0, min(len(ordered) - 1, index))]


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


def _hit_landscape_normal(world, location):
    start = unreal.Vector(location.x, location.y, location.z + 80000.0)
    end = unreal.Vector(location.x, location.y, location.z - 80000.0)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        values = hit.to_tuple()
    except Exception:
        return None, "trace_exception"
    if not values or not bool(values[0]):
        return None, "trace_miss"

    actor = values[9]
    component = values[10]
    actor_text = ""
    if actor:
        actor_text = " ".join([actor.get_name(), _actor_label(actor), actor.get_class().get_name()])
    component_text = ""
    if component:
        component_text = " ".join([component.get_name(), component.get_class().get_name()])
    if "Landscape" not in actor_text and "Landscape" not in component_text and "HLOD" not in actor_text:
        return None, ("non_landscape_hit:" + actor_text + "/" + component_text)[:180]
    return _normalized(values[7]), "ok"


def _new_category_summary():
    return {
        "instances": 0,
        "components": 0,
        "tilt_violations": 0,
        "max_world_up_angle_deg": 0.0,
        "road_clearance_violations": 0,
        "nearest_road_distance_cm": None,
    }


def validate_pcg_landscape_quality_rules():
    world = unreal.EditorLevelLibrary.get_editor_world()
    route_points = _route_points_from_spline(_find_road_spline())
    route_segments = _segments(route_points)

    report = {
        "success": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": world.get_path_name() if world else None,
        "road": {
            "actor": ROAD_ACTOR_LABEL,
            "spline": ROAD_SPLINE_NAME,
            "point_count": len(route_points),
            "segment_count": len(route_segments),
            "available": bool(route_segments),
        },
        "limits": {
            "tree_tilt_limit_deg": TREE_TILT_LIMIT_DEG,
            "rock_tilt_limit_deg": ROCK_TILT_LIMIT_DEG,
            "grass_normal_p95_limit_deg": GRASS_NORMAL_P95_LIMIT_DEG,
            "grass_core_clearance_cm": GRASS_CORE_CLEARANCE,
            "tree_clearance_cm": TREE_CLEARANCE,
            "rock_clearance_cm": ROCK_CLEARANCE,
        },
        "categories": {
            "grass": _new_category_summary(),
            "tree": _new_category_summary(),
            "rock": _new_category_summary(),
        },
        "grass_normal_alignment": {
            "sample_count": 0,
            "trace_miss_count": 0,
            "avg_align_deg": None,
            "p95_align_deg": None,
            "max_align_deg": None,
            "pass": False,
        },
        "samples": [],
        "failures": [],
    }

    grass_angles = []
    counted_components = {"grass": set(), "tree": set(), "rock": set()}

    for actor in _all_level_actors():
        label = _actor_label(actor)
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _category(component)
            if category not in report["categories"]:
                continue
            count = _instance_count(component)
            if count <= 0:
                continue
            report["categories"][category]["instances"] += count
            component_key = component.get_path_name()
            if component_key not in counted_components[category]:
                counted_components[category].add(component_key)
                report["categories"][category]["components"] += 1

            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, True)
                    location = transform.translation
                    up_angle = _angle_degrees(_quat_up(transform.rotation), WORLD_UP)
                    category_report = report["categories"][category]
                    category_report["max_world_up_angle_deg"] = max(
                        category_report["max_world_up_angle_deg"],
                        up_angle,
                    )

                    if category == "tree" and up_angle > TREE_TILT_LIMIT_DEG:
                        category_report["tilt_violations"] += 1
                    elif category == "rock" and up_angle > ROCK_TILT_LIMIT_DEG:
                        category_report["tilt_violations"] += 1
                    elif category == "grass":
                        normal, reason = _hit_landscape_normal(world, location)
                        if normal is None:
                            report["grass_normal_alignment"]["trace_miss_count"] += 1
                            if len(report["failures"]) < 40:
                                report["failures"].append(
                                    {
                                        "actor": label,
                                        "component": component.get_name(),
                                        "index": index,
                                        "reason": reason,
                                    }
                                )
                        else:
                            normal_angle = _angle_degrees(_quat_up(transform.rotation), normal)
                            grass_angles.append(normal_angle)

                    distance = _route_distance(location.x, location.y, route_segments)
                    if distance is not None:
                        previous = category_report["nearest_road_distance_cm"]
                        category_report["nearest_road_distance_cm"] = (
                            distance if previous is None else min(previous, distance)
                        )
                        if category == "grass" and distance < GRASS_CORE_CLEARANCE:
                            category_report["road_clearance_violations"] += 1
                        elif category == "tree" and distance < TREE_CLEARANCE:
                            category_report["road_clearance_violations"] += 1
                        elif category == "rock" and distance < ROCK_CLEARANCE:
                            category_report["road_clearance_violations"] += 1

                    if len(report["samples"]) < 30:
                        report["samples"].append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "category": category,
                                "index": index,
                                "mesh": _mesh_path(component),
                                "world_up_angle_deg": round(up_angle, 4),
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

    if grass_angles:
        report["grass_normal_alignment"] = {
            "sample_count": len(grass_angles),
            "trace_miss_count": report["grass_normal_alignment"]["trace_miss_count"],
            "avg_align_deg": round(sum(grass_angles) / len(grass_angles), 4),
            "p95_align_deg": round(_percentile(grass_angles, 0.95), 4),
            "max_align_deg": round(max(grass_angles), 4),
            "pass": _percentile(grass_angles, 0.95) <= GRASS_NORMAL_P95_LIMIT_DEG,
        }

    for category_report in report["categories"].values():
        if category_report["nearest_road_distance_cm"] is not None:
            category_report["nearest_road_distance_cm"] = round(
                category_report["nearest_road_distance_cm"],
                4,
            )
        category_report["max_world_up_angle_deg"] = round(
            category_report["max_world_up_angle_deg"],
            4,
        )

    report["quality_pass"] = (
        report["grass_normal_alignment"]["pass"]
        and report["categories"]["tree"]["tilt_violations"] == 0
        and report["categories"]["rock"]["tilt_violations"] == 0
        and report["categories"]["grass"]["road_clearance_violations"] == 0
        and report["categories"]["tree"]["road_clearance_violations"] == 0
        and report["categories"]["rock"]["road_clearance_violations"] == 0
    )

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = report_path
    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    validate_pcg_landscape_quality_rules()
