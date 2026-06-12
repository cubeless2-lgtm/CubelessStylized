"""Fill the landscape validation map from working runtime PCG components.

The current candidate-actor whole-map layer can spawn actors but may produce no
ISM output on the validation landscape. This pass deletes that failed layer and
uses the already validated runtime PCG actors as the source of PCG-owned ISM
components, then fills the full Landscape with deterministic transforms.
"""

import json
import math
import os
import random
import time

import unreal


BASELINE_PREFIX = "MCP_Cubeless_PCG_LandscapeVisualBaseline_"
FAILED_LAYER_PREFIX = "MCP_PCG_LandscapeDenseValidation"
REPORT_NAME = "pcg_landscape_runtime_full_coverage_report.json"
ORIGINAL_COUNT_TAG_PREFIX = "CubelessLandscapeRuntimeFullCoverageOriginalCount="
CARPET_GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)
ROAD_MASK_ACTOR_LABEL = "MCP_PCG_RoadMaskSpline_ClearForest_Test"
ROAD_MASK_SPLINE_NAME = "Road_SourceSpline"
MIN_EXISTING_SPLINE_LENGTH = 5000.0

TARGET_GRASS = 180000
TARGET_TREES = 5200
TARGET_ROCKS = 1000
ROAD_CORE_WIDTH = 2200.0
ROAD_FEATHER_WIDTH = 4200.0
TREE_ROAD_CLEARANCE = 6500.0
ROCK_ROAD_CLEARANCE = 4200.0
WORLD_UP = unreal.Vector(0.0, 0.0, 1.0)


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


def _landscape_bounds(actors):
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    count = 0
    for actor in actors:
        class_name = actor.get_class().get_name()
        label = _actor_label(actor)
        if "Landscape" not in class_name and "Landscape" not in label:
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


def _make_road_points(bounds):
    min_x = bounds["min_x"]
    max_x = bounds["max_x"]
    min_y = bounds["min_y"]
    max_y = bounds["max_y"]
    width = max_x - min_x
    height = max_y - min_y
    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5
    points = []
    for index in range(9):
        t = index / 8.0
        x = min_x + width * (0.11 + 0.78 * t)
        y = cy + math.sin((t * math.pi * 1.35) - 0.55) * height * 0.20
        y += math.sin(t * math.pi * 4.0) * height * 0.035
        points.append((x, y))
    points[4] = (cx, cy)
    return points


def _find_actor(label):
    for actor in _all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _spline_road_points(actor):
    if not actor:
        return None
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        return None
    named = [spline for spline in splines if spline.get_name() == ROAD_MASK_SPLINE_NAME]
    spline = named[0] if named else splines[0]
    if int(spline.get_number_of_spline_points()) < 2:
        return None
    if float(spline.get_spline_length()) < MIN_EXISTING_SPLINE_LENGTH:
        return None
    points = []
    for index in range(int(spline.get_number_of_spline_points())):
        location = spline.get_location_at_spline_point(
            index,
            unreal.SplineCoordinateSpace.WORLD,
        )
        points.append((float(location.x), float(location.y)))
    return {
        "source": ROAD_MASK_ACTOR_LABEL + "." + spline.get_name(),
        "point_count": int(spline.get_number_of_spline_points()),
        "length_cm": round(float(spline.get_spline_length()), 2),
        "points": points,
    }


def _resolve_road_points(bounds):
    spline_points = _spline_road_points(_find_actor(ROAD_MASK_ACTOR_LABEL))
    if spline_points:
        return spline_points
    points = _make_road_points(bounds)
    segments = _road_segments(points)
    return {
        "source": "generated_fallback",
        "point_count": len(points),
        "length_cm": round(sum(segment[4] for segment in segments), 2),
        "points": points,
    }


def _road_segments(road_points):
    segments = []
    for index in range(len(road_points) - 1):
        ax, ay = road_points[index]
        bx, by = road_points[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0.0:
            segments.append((ax, ay, dx, dy, length))
    return segments


def _road_distance(x, y, segments):
    best = 10.0**12
    for ax, ay, dx, dy, length in segments:
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (length * length)))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best


def _sample_ground_z(world, x, y, fallback_z):
    start = unreal.Vector(x, y, 80000.0)
    end = unreal.Vector(x, y, -30000.0)
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
        return fallback_z, False, WORLD_UP
    if not values or not bool(values[0]):
        return fallback_z, False, WORLD_UP
    try:
        actor = values[9]
        actor_name = actor.get_name() if actor else ""
        actor_label = _actor_label(actor) if actor else ""
        actor_class = actor.get_class().get_name() if actor else ""
        component = values[10]
        component_name = component.get_name() if component else ""
        component_class = component.get_class().get_name() if component else ""
    except Exception:
        actor_name = ""
        actor_label = ""
        actor_class = ""
        component_name = ""
        component_class = ""
    hit_text = " ".join([actor_name, actor_label, actor_class, component_name, component_class])
    if "Landscape" not in hit_text and "HLOD" not in hit_text:
        return fallback_z, False, WORLD_UP
    try:
        return float(values[4].z), True, _normalized(values[7])
    except Exception:
        return fallback_z, False, WORLD_UP


def _sample_ground_normal(world, location):
    _z, hit_landscape, normal = _sample_ground_z(world, location.x, location.y, location.z)
    if not hit_landscape:
        return None
    return normal


def _stable_rng(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return random.Random(seed)


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


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


def _normal_aligned_quat(normal, yaw_degrees):
    normal = _normalized(normal)
    align_quat = unreal.MathLibrary.quat_find_between_normals(WORLD_UP, normal)
    yaw_quat = unreal.MathLibrary.rotator_from_axis_and_angle(
        normal, float(yaw_degrees)
    ).quaternion()
    return unreal.MathLibrary.multiply_quat_quat(yaw_quat, align_quat)


def _classify_component(component):
    text = _component_text(component)
    if any(token in text for token in ["tree", "pine", "spruce", "conifer", "trunk"]):
        return "tree"
    if any(token in text for token in ["rock", "stone", "boulder"]):
        return "rock"
    if any(
        token in text
        for token in ["grass", "flower", "fern", "leaf", "leaves", "foliage", "plant"]
    ):
        return "grass"
    return "other"


def _component_text(component):
    text = component.get_name().lower()
    try:
        mesh = component.get_editor_property("static_mesh")
        if mesh:
            text += " " + mesh.get_path_name().lower()
    except Exception:
        pass
    return text


def _is_flower_component(component):
    return "flower" in _component_text(component)


def _is_carpet_candidate(component):
    text = _component_text(component)
    return any(token in text for token in ["grass", "fern", "leaf", "leaves", "foliage", "plant"])


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return None


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _component_tags(component):
    try:
        return [str(tag) for tag in component.get_editor_property("component_tags")]
    except Exception:
        return []


def _set_component_tags(component, tags):
    try:
        component.set_editor_property("component_tags", tags)
    except Exception:
        pass


def _get_or_set_original_count(component):
    tags = _component_tags(component)
    for tag in tags:
        if not tag.startswith(ORIGINAL_COUNT_TAG_PREFIX):
            continue
        try:
            return int(tag[len(ORIGINAL_COUNT_TAG_PREFIX) :])
        except ValueError:
            pass
    count = _instance_count(component)
    tags.append(ORIGINAL_COUNT_TAG_PREFIX + str(count))
    _set_component_tags(component, tags)
    return count


def _reset_to_original_count(component, original_count):
    removed = 0
    while _instance_count(component) > original_count:
        try:
            if component.remove_instance(_instance_count(component) - 1):
                removed += 1
            else:
                break
        except Exception:
            break
    return removed


def _delete_failed_candidate_layer():
    deleted = 0
    for actor in _all_level_actors():
        if not _actor_label(actor).startswith(FAILED_LAYER_PREFIX):
            continue
        for component in actor.get_components_by_class(unreal.PCGComponent):
            try:
                component.cleanup(True)
            except Exception:
                pass
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted += 1
        except Exception:
            pass
    return deleted


def _baseline_components():
    actors = [
        actor
        for actor in _all_level_actors()
        if _actor_label(actor).startswith(BASELINE_PREFIX)
    ]
    scatter_components = {"grass": [], "tree": [], "rock": []}
    all_components = {"grass": [], "tree": [], "rock": []}
    rows = []
    carpet_mesh = unreal.EditorAssetLibrary.load_asset(CARPET_GRASS_MESH)
    if not carpet_mesh:
        raise RuntimeError("Missing carpet grass mesh: " + CARPET_GRASS_MESH)
    for actor in actors:
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _classify_component(component)
            if category not in all_components:
                continue
            all_components[category].append(component)
            original_mesh = _mesh_path(component)
            used_for_scatter = True
            mesh_changed = False
            if category == "grass" and _is_flower_component(component):
                used_for_scatter = False
            elif category == "grass" and _is_carpet_candidate(component):
                try:
                    if original_mesh != CARPET_GRASS_MESH:
                        component.set_static_mesh(carpet_mesh)
                        mesh_changed = True
                    try:
                        component.mark_render_state_dirty()
                    except Exception:
                        pass
                except Exception as exc:
                    rows.append(
                        {
                            "actor": _actor_label(actor),
                            "component": component.get_name(),
                            "category": category,
                            "mesh_override_error": str(exc),
                        }
                    )
            if not used_for_scatter:
                # Keep existing flower output as a light accent; do not let it
                # dominate the high-density carpet pass.
                pass
            else:
                scatter_components[category].append(component)
            count = _instance_count(component)
            rows.append(
                {
                    "actor": _actor_label(actor),
                    "component": component.get_name(),
                    "category": category,
                    "used_for_scatter": used_for_scatter,
                    "original_mesh": original_mesh,
                    "current_mesh": _mesh_path(component),
                    "mesh_changed": mesh_changed,
                    "count_before_reset": count,
                }
            )
    return actors, scatter_components, all_components, rows


def _grid_key(x, y, cell_size):
    return int(math.floor(x / cell_size)), int(math.floor(y / cell_size))


def _add_spatial(x, y, spatial, cell_size):
    spatial.setdefault(_grid_key(x, y, cell_size), []).append((x, y))


def _too_close(x, y, spatial, cell_size, min_distance):
    key_x, key_y = _grid_key(x, y, cell_size)
    min_sq = min_distance * min_distance
    for gx in range(key_x - 1, key_x + 2):
        for gy in range(key_y - 1, key_y + 2):
            for px, py in spatial.get((gx, gy), []):
                dx = x - px
                dy = y - py
                if dx * dx + dy * dy < min_sq:
                    return True
    return False


def _sample_xy(bounds, rng):
    margin = 3600.0
    x = rng.uniform(bounds["min_x"] + margin, bounds["max_x"] - margin)
    y = rng.uniform(bounds["min_y"] + margin, bounds["max_y"] - margin)
    return x, y


def _grass_acceptance(distance):
    if distance < ROAD_CORE_WIDTH:
        return 0.0
    if distance < ROAD_CORE_WIDTH + ROAD_FEATHER_WIDTH:
        return 0.16 + 0.70 * ((distance - ROAD_CORE_WIDTH) / ROAD_FEATHER_WIDTH)
    return 1.0


def _make_transform(x, y, z, category, rng, normal=None):
    transform = unreal.Transform()
    transform.translation = unreal.Vector(x, y, z)
    yaw = rng.uniform(0.0, 360.0)
    if category == "tree":
        pitch = rng.uniform(-3.0, 3.0)
        roll = rng.uniform(-3.0, 3.0)
        scale = rng.uniform(1.45, 3.45)
        transform.scale3d = unreal.Vector(scale, scale, scale * rng.uniform(1.03, 1.18))
    elif category == "rock":
        pitch = rng.uniform(-4.0, 4.0)
        roll = rng.uniform(-4.0, 4.0)
        scale = rng.uniform(0.50, 4.00)
        transform.scale3d = unreal.Vector(scale, scale, scale * rng.uniform(0.62, 1.08))
    else:
        pitch = rng.uniform(-3.5, 3.5)
        roll = rng.uniform(-3.5, 3.5)
        scale = rng.uniform(1.05, 2.40)
        transform.scale3d = unreal.Vector(scale, scale, rng.uniform(0.92, 1.55))
    if category == "grass" and normal is not None:
        transform.rotation = _normal_aligned_quat(normal, yaw)
    else:
        transform.rotation = _make_rotator(pitch, yaw, roll).quaternion()
    return transform


def _batch_add(category, components, transforms_by_component):
    added = 0
    for component in components:
        transforms = transforms_by_component.get(component) or []
        if not transforms:
            continue
        try:
            component.add_instances(transforms, False, True)
            added += len(transforms)
        except Exception:
            for transform in transforms:
                try:
                    component.add_instance_world_space(transform)
                    added += 1
                except Exception:
                    pass
        try:
            component.mark_render_state_dirty()
        except Exception:
            pass
    return added


def _reset_components(components):
    report = {"removed_previous_supplements": 0, "original_counts": []}
    for category, category_components in components.items():
        for component in category_components:
            original_count = _get_or_set_original_count(component)
            removed = _reset_to_original_count(component, original_count)
            report["removed_previous_supplements"] += removed
            report["original_counts"].append(
                {
                    "component": component.get_name(),
                    "category": category,
                    "original_count": original_count,
                    "removed": removed,
                }
            )
    return report


def _collect_object_spatial(components):
    spatial = {}
    cell_size = 1250.0
    for category in ["tree", "rock"]:
        for component in components.get(category, []):
            count = _instance_count(component)
            for index in range(count):
                try:
                    location = component.get_instance_transform(index, True).translation
                    _add_spatial(location.x, location.y, spatial, cell_size)
                except Exception:
                    pass
    return spatial, cell_size


def _scatter_category(world, bounds, road_segments, components, category, target, object_spatial, object_cell):
    category_components = components.get(category, [])
    report = {
        "category": category,
        "target": target,
        "component_count": len(category_components),
        "added": 0,
        "attempts": 0,
        "landscape_trace_misses": 0,
        "samples": [],
    }
    if not category_components:
        return report

    rng = _stable_rng("landscape_full_coverage", category, target)
    transforms_by_component = {component: [] for component in category_components}
    made = 0
    max_attempts = target * 16

    while made < target and report["attempts"] < max_attempts:
        report["attempts"] += 1
        x, y = _sample_xy(bounds, rng)
        distance = _road_distance(x, y, road_segments)

        if category == "grass":
            if rng.random() > _grass_acceptance(distance):
                continue
            if _too_close(x, y, object_spatial, object_cell, 260.0):
                continue
        elif category == "tree":
            if distance < TREE_ROAD_CLEARANCE:
                continue
            if _too_close(x, y, object_spatial, object_cell, 1350.0):
                continue
            _add_spatial(x, y, object_spatial, object_cell)
        elif category == "rock":
            if distance < ROCK_ROAD_CLEARANCE:
                continue
            if _too_close(x, y, object_spatial, object_cell, 900.0):
                continue
            _add_spatial(x, y, object_spatial, object_cell)

        z, hit_landscape, normal = _sample_ground_z(world, x, y, 0.0)
        if not hit_landscape:
            report["landscape_trace_misses"] += 1
            continue

        component = category_components[made % len(category_components)]
        transform = _make_transform(x, y, z, category, rng, normal)
        transforms_by_component[component].append(transform)
        if len(report["samples"]) < 20:
            report["samples"].append(
                {
                    "component": component.get_name(),
                    "location": [round(x, 1), round(y, 1), round(z, 1)],
                    "road_distance": round(distance, 1),
                    "scale": [
                        round(transform.scale3d.x, 2),
                        round(transform.scale3d.y, 2),
                        round(transform.scale3d.z, 2),
                    ],
                }
            )
        made += 1

    report["added"] = _batch_add(category, category_components, transforms_by_component)
    return report


def _norm_angle(value):
    while value > 180.0:
        value -= 360.0
    while value < -180.0:
        value += 360.0
    return value


def _clamp_existing_rotation(components, world):
    report = {
        "scanned": 0,
        "updated": 0,
        "violations_after": 0,
        "grass_normal_aligned": 0,
        "grass_normal_trace_misses": 0,
    }
    for category, category_components in components.items():
        for component in category_components:
            count = _instance_count(component)
            for index in range(count):
                report["scanned"] += 1
                try:
                    transform = component.get_instance_transform(index, True)
                    rotator = transform.rotation.rotator()
                    if category == "grass":
                        normal = _sample_ground_normal(world, transform.translation)
                        if normal is None:
                            report["grass_normal_trace_misses"] += 1
                            continue
                        transform.rotation = _normal_aligned_quat(normal, rotator.yaw)
                        if component.update_instance_transform(index, transform, True, True, True):
                            report["updated"] += 1
                            report["grass_normal_aligned"] += 1
                        if _angle_degrees(_quat_up(transform.rotation), normal) > 5.01:
                            report["violations_after"] += 1
                        continue
                    pitch = max(-4.9, min(4.9, _norm_angle(rotator.pitch)))
                    roll = max(-4.9, min(4.9, _norm_angle(rotator.roll)))
                    yaw = _norm_angle(rotator.yaw)
                    if abs(yaw) < 0.01:
                        yaw = _stable_rng(component.get_name(), index, "yaw").uniform(0.0, 360.0)
                    if (
                        abs(pitch - _norm_angle(rotator.pitch)) > 0.01
                        or abs(roll - _norm_angle(rotator.roll)) > 0.01
                        or abs(yaw - _norm_angle(rotator.yaw)) > 0.01
                    ):
                        transform.rotation = _make_rotator(pitch, yaw, roll).quaternion()
                        if component.update_instance_transform(index, transform, True, True, True):
                            report["updated"] += 1
                    if abs(pitch) > 5.01 or abs(roll) > 5.01:
                        report["violations_after"] += 1
                except Exception:
                    pass
            try:
                component.mark_render_state_dirty()
            except Exception:
                pass
    return report


def _road_threshold_for(category):
    if category == "grass":
        return ROAD_CORE_WIDTH
    if category == "tree":
        return TREE_ROAD_CLEARANCE
    if category == "rock":
        return ROCK_ROAD_CLEARANCE
    return 0.0


def _prune_road_violations(components, road_segments):
    report = {
        "removed": {"grass": 0, "tree": 0, "rock": 0},
        "failed_removals": [],
    }
    for category, category_components in components.items():
        threshold = _road_threshold_for(category)
        if threshold <= 0.0:
            continue
        for component in category_components:
            remove_indexes = []
            count = _instance_count(component)
            for index in range(count):
                try:
                    location = component.get_instance_transform(index, True).translation
                except Exception:
                    continue
                if _road_distance(location.x, location.y, road_segments) < threshold:
                    remove_indexes.append(index)
            for index in sorted(remove_indexes, reverse=True):
                try:
                    if component.remove_instance(index):
                        report["removed"][category] += 1
                    elif len(report["failed_removals"]) < 30:
                        report["failed_removals"].append(
                            {
                                "component": component.get_name(),
                                "category": category,
                                "index": index,
                                "error": "remove_instance returned false",
                            }
                        )
                except Exception as exc:
                    if len(report["failed_removals"]) < 30:
                        report["failed_removals"].append(
                            {
                                "component": component.get_name(),
                                "category": category,
                                "index": index,
                                "error": str(exc),
                            }
                        )
            try:
                component.mark_render_state_dirty()
            except Exception:
                pass
    report["failed_removal_count"] = len(report["failed_removals"])
    return report


def _summarize(world, actors, components, road_segments):
    summary = {
        "baseline_actor_count": len(actors),
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0},
        "road_violations": {
            "grass_in_core": 0,
            "tree_within_clearance": 0,
            "rock_within_clearance": 0,
        },
        "tilt_violations": 0,
    }
    for category, category_components in components.items():
        for component in category_components:
            count = _instance_count(component)
            summary["instances"][category] += count
            summary["instances"]["all"] += count
            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, True)
                    location = transform.translation
                    rotator = transform.rotation.rotator()
                except Exception:
                    continue
                distance = _road_distance(location.x, location.y, road_segments)
                if category == "grass" and distance < ROAD_CORE_WIDTH:
                    summary["road_violations"]["grass_in_core"] += 1
                if category == "tree" and distance < TREE_ROAD_CLEARANCE:
                    summary["road_violations"]["tree_within_clearance"] += 1
                if category == "rock" and distance < ROCK_ROAD_CLEARANCE:
                    summary["road_violations"]["rock_within_clearance"] += 1
                if category == "grass":
                    normal = _sample_ground_normal(world, location)
                    if normal is None or _angle_degrees(_quat_up(transform.rotation), normal) > 5.01:
                        summary["tilt_violations"] += 1
                elif abs(_norm_angle(rotator.pitch)) > 5.01 or abs(_norm_angle(rotator.roll)) > 5.01:
                    summary["tilt_violations"] += 1
    return summary


def _save_map_only():
    try:
        return bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False))
    except Exception as exc:
        return "failed: " + str(exc)


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report_path


def fill_pcg_landscape_validation_from_runtime_baseline():
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world is available.")

    actors = _all_level_actors()
    bounds = _landscape_bounds(actors)
    road_source = _resolve_road_points(bounds)
    road_points = road_source["points"]
    road_segments = _road_segments(road_points)
    deleted_failed_layer = _delete_failed_candidate_layer()

    baseline_actors, scatter_components, all_components, component_rows = _baseline_components()
    if not baseline_actors:
        raise RuntimeError("No runtime baseline PCG actors found: " + BASELINE_PREFIX)
    if not scatter_components["grass"]:
        raise RuntimeError("No baseline PCG grass ISM components found.")

    reset_report = _reset_components(all_components)
    object_spatial, object_cell = _collect_object_spatial(all_components)

    rock_report = _scatter_category(
        world, bounds, road_segments, scatter_components, "rock", TARGET_ROCKS, object_spatial, object_cell
    )
    tree_report = _scatter_category(
        world, bounds, road_segments, scatter_components, "tree", TARGET_TREES, object_spatial, object_cell
    )
    grass_report = _scatter_category(
        world, bounds, road_segments, scatter_components, "grass", TARGET_GRASS, object_spatial, object_cell
    )

    prune_report = _prune_road_violations(all_components, road_segments)
    rotation_report = _clamp_existing_rotation(all_components, world)
    summary = _summarize(world, baseline_actors, all_components, road_segments)
    save_result = _save_map_only()

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "complete",
        "level": world.get_outer().get_path_name(),
        "baseline_prefix": BASELINE_PREFIX,
        "deleted_failed_candidate_layer": deleted_failed_layer,
        "landscape_bounds": bounds,
        "road_source": {
            key: value
            for key, value in road_source.items()
            if key != "points"
        },
        "road_points": road_points,
        "component_rows": component_rows,
        "scatter_component_counts": {
            "grass": len(scatter_components["grass"]),
            "tree": len(scatter_components["tree"]),
            "rock": len(scatter_components["rock"]),
        },
        "reset": reset_report,
        "scatter": {
            "rock": rock_report,
            "tree": tree_report,
            "grass": grass_report,
        },
        "prune_road_violations": prune_report,
        "rotation": rotation_report,
        "summary": summary,
        "save_map_only": save_result,
        "notes": [
            "Candidate whole-map PCG actor layer is removed because it produced zero ISM output.",
            "Full coverage uses existing runtime PCG-generated ISM components as the instance owners.",
            "Grass overlap is relaxed only against other grass; tree/rock/object spacing still blocks grass placement.",
            "Rock scale random range is 0.5 to 4.0.",
            "Pitch/Roll are clamped within 5 degrees while yaw remains random.",
        ],
    }
    report_path = _write_report(report)
    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    fill_pcg_landscape_validation_from_runtime_baseline()
