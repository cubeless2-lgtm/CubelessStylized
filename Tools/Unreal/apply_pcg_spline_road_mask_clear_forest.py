"""Apply a temporary spline road mask to PCG-generated forest instances.

This validates the behavior the production PCG graph must eventually own:
an editable spline clears a corridor through already generated forest output,
with a hard road core and softer grass-only shoulder thinning.
"""

import json
import math
import os
import time

import unreal


REPORT_NAME = "pcg_spline_road_mask_clear_forest_report.json"
BASELINE_PREFIX = "MCP_Cubeless_PCG_LandscapeVisualBaseline_"
MASK_ACTOR_LABEL = "MCP_PCG_RoadMaskSpline_ClearForest_Test"
ROAD_BP_CLASS_PATH = (
    "/Game/Cubeless/PCG/Runtime/Blueprints/"
    "BP_Cubeless_PCG_ForestRoadRuntime.BP_Cubeless_PCG_ForestRoadRuntime_C"
)

GRASS_CORE_CLEARANCE = 2600.0
GRASS_FEATHER_END = 6800.0
TREE_CLEARANCE = 7800.0
ROCK_CLEARANCE = 4800.0
ROUTE_SAMPLE_STEP = 1600.0
WORLD_UP = unreal.Vector(0.0, 0.0, 1.0)
MIN_EXISTING_SPLINE_LENGTH = 5000.0


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


def _landscape_bounds(actors):
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    count = 0
    for actor in actors:
        label = _actor_label(actor)
        class_name = actor.get_class().get_name()
        if "Landscape" not in label and "Landscape" not in class_name:
            continue
        try:
            origin, extent = actor.get_actor_bounds(False)
        except Exception:
            continue
        mins[0] = min(mins[0], origin.x - extent.x)
        mins[1] = min(mins[1], origin.y - extent.y)
        mins[2] = min(mins[2], origin.z - extent.z)
        maxs[0] = max(maxs[0], origin.x + extent.x)
        maxs[1] = max(maxs[1], origin.y + extent.y)
        maxs[2] = max(maxs[2], origin.z + extent.z)
        count += 1
    if count <= 0:
        raise RuntimeError("No Landscape actors found.")
    return {
        "count": count,
        "min_x": mins[0],
        "max_x": maxs[0],
        "min_y": mins[1],
        "max_y": maxs[1],
        "min_z": mins[2],
        "max_z": maxs[2],
    }


def _sample_landscape_z(world, x, y, fallback_z=0.0):
    start = unreal.Vector(x, y, 90000.0)
    end = unreal.Vector(x, y, -40000.0)
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
        return fallback_z, False
    if not values or not bool(values[0]):
        return fallback_z, False
    actor = values[9]
    component = values[10]
    actor_text = ""
    if actor:
        actor_text = " ".join([actor.get_name(), _actor_label(actor), actor.get_class().get_name()])
    component_text = ""
    if component:
        component_text = " ".join([component.get_name(), component.get_class().get_name()])
    if "Landscape" not in actor_text and "Landscape" not in component_text and "HLOD" not in actor_text:
        return fallback_z, False
    try:
        return float(values[4].z), True
    except Exception:
        return fallback_z, False


def _find_actor(label):
    for actor in _all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _find_spline(actor):
    if not actor:
        return None
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        return None
    for spline in splines:
        if spline.get_name() == "Road_SourceSpline":
            return spline
    return splines[0]


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _route_points(bounds, world):
    min_x = bounds["min_x"] + 15000.0
    max_x = bounds["max_x"] - 15000.0
    center_y = (bounds["min_y"] + bounds["max_y"]) * 0.5
    amplitude = min((bounds["max_y"] - bounds["min_y"]) * 0.18, 36000.0)
    points = []
    for index in range(8):
        t = index / 7.0
        x = min_x + (max_x - min_x) * t
        y = center_y + math.sin(t * math.pi * 2.0 - 0.55) * amplitude
        z, _hit = _sample_landscape_z(world, x, y, 0.0)
        points.append(unreal.Vector(x, y, z + 35.0))
    return points


def _ensure_mask_spline(world, bounds):
    actor = _find_actor(MASK_ACTOR_LABEL)
    created_actor = False
    if not actor:
        actor_class = unreal.load_object(None, ROAD_BP_CLASS_PATH)
        if not actor_class:
            raise RuntimeError("Missing road runtime Blueprint class: " + ROAD_BP_CLASS_PATH)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            actor_class, unreal.Vector(0.0, 0.0, 0.0), _make_rotator(0.0, 0.0, 0.0)
        )
        if not actor:
            raise RuntimeError("Failed to spawn road mask actor.")
        actor.set_actor_label(MASK_ACTOR_LABEL)
        created_actor = True

    spline = _find_spline(actor)
    if not spline:
        raise RuntimeError("Road mask actor has no SplineComponent.")

    if created_actor or spline.get_number_of_spline_points() < 2 or spline.get_spline_length() < MIN_EXISTING_SPLINE_LENGTH:
        points = _route_points(bounds, world)
        spline.clear_spline_points(False)
        for point in points:
            spline.add_spline_point(point, unreal.SplineCoordinateSpace.WORLD, False)
        for index in range(spline.get_number_of_spline_points()):
            try:
                spline.set_spline_point_type(index, unreal.SplinePointType.LINEAR, False)
            except Exception:
                pass
        spline.update_spline()
        try:
            actor.modify()
            spline.modify()
        except Exception:
            pass
        route_source = "generated_default"
    else:
        route_source = "existing_editor_spline"

    return actor, spline, _spline_control_points(spline), route_source


def _spline_control_points(spline):
    points = []
    for index in range(spline.get_number_of_spline_points()):
        try:
            points.append(
                spline.get_location_at_spline_point(
                    index, unreal.SplineCoordinateSpace.WORLD
                )
            )
        except Exception:
            pass
    return points


def _spline_polyline(spline):
    length = max(0.0, float(spline.get_spline_length()))
    if length <= 0.0:
        return []
    samples = max(2, int(math.ceil(length / ROUTE_SAMPLE_STEP)) + 1)
    points = []
    for index in range(samples):
        distance = min(length, (length * index) / (samples - 1))
        try:
            point = spline.get_location_at_distance_along_spline(
                distance, unreal.SplineCoordinateSpace.WORLD
            )
        except Exception:
            point = None
        if point:
            points.append((float(point.x), float(point.y)))
    segments = []
    for index in range(len(points) - 1):
        ax, ay = points[index]
        bx, by = points[index + 1]
        dx = bx - ax
        dy = by - ay
        length_sq = dx * dx + dy * dy
        if length_sq > 1.0:
            segments.append((ax, ay, dx, dy, length_sq))
    return segments


def _distance_to_route(x, y, segments):
    best = float("inf")
    for ax, ay, dx, dy, length_sq in segments:
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / length_sq))
        px = ax + dx * t
        py = ay + dy * t
        dist_sq = (x - px) * (x - px) + (y - py) * (y - py)
        if dist_sq < best:
            best = dist_sq
    return math.sqrt(best) if best < float("inf") else float("inf")


def _stable_unit(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return (seed & 0xFFFFFF) / float(0xFFFFFF)


def _grass_remove_probability(distance):
    if distance < GRASS_CORE_CLEARANCE:
        return 1.0
    if distance >= GRASS_FEATHER_END:
        return 0.0
    alpha = (distance - GRASS_CORE_CLEARANCE) / (GRASS_FEATHER_END - GRASS_CORE_CLEARANCE)
    return max(0.0, min(1.0, 0.82 * (1.0 - alpha)))


def _should_remove(category, distance, actor_label, component_name, index):
    if category == "tree":
        return distance < TREE_CLEARANCE
    if category == "rock":
        return distance < ROCK_CLEARANCE
    if category == "grass":
        probability = _grass_remove_probability(distance)
        return probability >= 1.0 or _stable_unit(actor_label, component_name, index, "road_mask") < probability
    return False


def _band_key(distance):
    if distance < GRASS_CORE_CLEARANCE:
        return "core"
    if distance < GRASS_FEATHER_END:
        return "feather"
    if distance < TREE_CLEARANCE:
        return "outer_tree_clearance"
    return "outside"


def _target_components():
    rows = []
    for actor in _all_level_actors():
        label = _actor_label(actor)
        if not label.startswith(BASELINE_PREFIX):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _category(component)
            if category == "other":
                continue
            count = _instance_count(component)
            if count <= 0:
                continue
            rows.append((actor, label, component, component.get_name(), category, count))
    return rows


def _collect_before(rows, segments):
    summary = {
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0},
        "near_route": {"grass_core": 0, "grass_feather": 0, "tree_clearance": 0, "rock_clearance": 0},
        "grass_bands": {"core": 0, "feather": 0, "outer_tree_clearance": 0, "outside": 0},
    }
    for _actor, _label, component, _component_name, category, count in rows:
        summary["instances"]["all"] += count
        summary["instances"][category] += count
        for index in range(count):
            try:
                location = component.get_instance_transform(index, True).translation
            except Exception:
                continue
            distance = _distance_to_route(location.x, location.y, segments)
            if category == "grass":
                summary["grass_bands"][_band_key(distance)] += 1
                if distance < GRASS_CORE_CLEARANCE:
                    summary["near_route"]["grass_core"] += 1
                elif distance < GRASS_FEATHER_END:
                    summary["near_route"]["grass_feather"] += 1
            elif category == "tree" and distance < TREE_CLEARANCE:
                summary["near_route"]["tree_clearance"] += 1
            elif category == "rock" and distance < ROCK_CLEARANCE:
                summary["near_route"]["rock_clearance"] += 1
    return summary


def _apply_mask(rows, segments):
    report = {
        "removed": {"all": 0, "grass": 0, "tree": 0, "rock": 0},
        "components": [],
        "failures": [],
    }
    for _actor, label, component, component_name, category, count in rows:
        to_remove = []
        nearest = {"min": None, "max_removed_distance": 0.0}
        for index in range(count):
            try:
                location = component.get_instance_transform(index, True).translation
                distance = _distance_to_route(location.x, location.y, segments)
            except Exception as exc:
                if len(report["failures"]) < 40:
                    report["failures"].append(
                        {
                            "actor": label,
                            "component": component_name,
                            "index": index,
                            "stage": "distance",
                            "error": str(exc),
                        }
                    )
                continue
            nearest["min"] = distance if nearest["min"] is None else min(nearest["min"], distance)
            if _should_remove(category, distance, label, component_name, index):
                to_remove.append(index)
                nearest["max_removed_distance"] = max(nearest["max_removed_distance"], distance)

        removed = 0
        for index in reversed(to_remove):
            try:
                if component.remove_instance(index):
                    removed += 1
                elif len(report["failures"]) < 40:
                    report["failures"].append(
                        {
                            "actor": label,
                            "component": component_name,
                            "index": index,
                            "stage": "remove",
                            "error": "remove_instance returned false",
                        }
                    )
            except Exception as exc:
                if len(report["failures"]) < 40:
                    report["failures"].append(
                        {
                            "actor": label,
                            "component": component_name,
                            "index": index,
                            "stage": "remove",
                            "error": str(exc),
                        }
                    )

        if removed:
            try:
                component.mark_render_state_dirty()
            except Exception:
                pass
        report["removed"]["all"] += removed
        report["removed"][category] += removed
        report["components"].append(
            {
                "actor": label,
                "component": component_name,
                "category": category,
                "before_count": count,
                "removed": removed,
                "after_count": _instance_count(component),
                "nearest_distance": round(nearest["min"], 2) if nearest["min"] is not None else None,
                "max_removed_distance": round(nearest["max_removed_distance"], 2),
            }
        )
    return report


def _validate_after(rows, segments):
    validation = {
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0},
        "violations": {"grass_core": 0, "tree_clearance": 0, "rock_clearance": 0},
        "grass_bands": {"core": 0, "feather": 0, "outer_tree_clearance": 0, "outside": 0},
        "samples": [],
    }
    for _actor, label, component, component_name, category, _count in rows:
        count = _instance_count(component)
        validation["instances"]["all"] += count
        validation["instances"][category] += count
        for index in range(count):
            try:
                location = component.get_instance_transform(index, True).translation
            except Exception:
                continue
            distance = _distance_to_route(location.x, location.y, segments)
            if category == "grass":
                band = _band_key(distance)
                validation["grass_bands"][band] += 1
                if distance < GRASS_CORE_CLEARANCE:
                    validation["violations"]["grass_core"] += 1
                    if len(validation["samples"]) < 30:
                        validation["samples"].append(
                            {
                                "actor": label,
                                "component": component_name,
                                "category": category,
                                "index": index,
                                "distance": round(distance, 2),
                            }
                        )
            elif category == "tree" and distance < TREE_CLEARANCE:
                validation["violations"]["tree_clearance"] += 1
            elif category == "rock" and distance < ROCK_CLEARANCE:
                validation["violations"]["rock_clearance"] += 1

    validation["pass"] = all(value == 0 for value in validation["violations"].values())
    return validation


def _dirty_packages():
    rows = []
    try:
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():
            rows.append({"type": "content", "name": package.get_name()})
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
            rows.append({"type": "map", "name": package.get_name()})
    except Exception:
        pass
    return rows


def _save_map_only():
    try:
        return bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False))
    except Exception as exc:
        return "failed: " + str(exc)


def apply_pcg_spline_road_mask_clear_forest():
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world is available.")

    actors = _all_level_actors()
    bounds = _landscape_bounds(actors)
    mask_actor, spline, route_points, route_source = _ensure_mask_spline(world, bounds)
    segments = _spline_polyline(spline)
    if not segments:
        raise RuntimeError("Road mask spline produced no route segments.")

    rows = _target_components()
    before = _collect_before(rows, segments)
    removal = _apply_mask(rows, segments)
    after_rows = _target_components()
    validation = _validate_after(after_rows, segments)

    dirty_before_save = _dirty_packages()
    save_result = _save_map_only()
    dirty_after_save = _dirty_packages()

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": world.get_outer().get_path_name(),
        "mask_actor": _actor_label(mask_actor),
        "spline_component": spline.get_name(),
        "route_source": route_source,
        "spline_point_count": spline.get_number_of_spline_points(),
        "spline_length": round(float(spline.get_spline_length()), 2),
        "route_point_sample": [
            [round(point.x, 1), round(point.y, 1), round(point.z, 1)]
            for point in route_points
        ],
        "clearance": {
            "grass_core": GRASS_CORE_CLEARANCE,
            "grass_feather_end": GRASS_FEATHER_END,
            "tree": TREE_CLEARANCE,
            "rock": ROCK_CLEARANCE,
        },
        "before": before,
        "removal": removal,
        "after": validation,
        "road_mask_clear_forest_pass": validation["pass"],
        "dirty_before_save": dirty_before_save,
        "save_result": save_result,
        "dirty_after_save": dirty_after_save,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = report_path
    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    apply_pcg_spline_road_mask_clear_forest()
