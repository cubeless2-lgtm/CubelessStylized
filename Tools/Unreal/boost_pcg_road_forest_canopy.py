"""Boost road-safe forest canopy density on existing PCG tree ISM components.

This is a visual QA pass for the field level. It appends deterministic tree
instances to existing PCG-generated tree components, so the result is still
carried by PCG instance components instead of loose StaticMeshActors.
"""

import json
import math
import os
import random
import time

import unreal


REPORT_NAME = "CubelessRoadForestCanopyBoost_Report.json"
ORIGINAL_COUNT_TAG_PREFIX = "CubelessRoadForestCanopyBoostOriginalCount="
MAX_ADDITIONS = 5200
BLOCK_TAG_TOKEN = "block"

ROAD_POINTS = [
    (4740.5, 10249.0, -54.2),
    (11204.9, 12049.1, -19.4),
    (17281.7, 16363.3, 1.1),
    (23407.1, 20512.5, 1.1),
    (29277.9, 25104.5, 1.1),
    (35071.3, 29853.7, 1.1),
    (40847.3, 34671.2, 1.1),
    (46419.2, 39919.5, 1.1),
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
        ax, ay, az = ROAD_POINTS[index]
        bx, by, bz = ROAD_POINTS[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length <= 0.0:
            continue
        segments.append(
            {
                "ax": ax,
                "ay": ay,
                "az": az,
                "bx": bx,
                "by": by,
                "bz": bz,
                "dx": dx,
                "dy": dy,
                "length": length,
            }
        )
    return segments


ROAD_SEGMENTS = _road_segments()


def _road_distance(x, y):
    best = 10**12
    for segment in ROAD_SEGMENTS:
        dx = segment["dx"]
        dy = segment["dy"]
        length = segment["length"]
        t = max(
            0.0,
            min(
                1.0,
                ((x - segment["ax"]) * dx + (y - segment["ay"]) * dy)
                / (length * length),
            ),
        )
        px = segment["ax"] + dx * t
        py = segment["ay"] + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best


def _total_road_length():
    return sum(segment["length"] for segment in ROAD_SEGMENTS)


def _sample_road(distance):
    remaining = distance
    for segment in ROAD_SEGMENTS:
        if remaining > segment["length"]:
            remaining -= segment["length"]
            continue
        t = max(0.0, min(1.0, remaining / segment["length"]))
        x = segment["ax"] + segment["dx"] * t
        y = segment["ay"] + segment["dy"] * t
        z = segment["az"] + (segment["bz"] - segment["az"]) * t
        nx = -segment["dy"] / segment["length"]
        ny = segment["dx"] / segment["length"]
        tx = segment["dx"] / segment["length"]
        ty = segment["dy"] / segment["length"]
        return x, y, z, nx, ny, tx, ty
    last = ROAD_SEGMENTS[-1]
    return (
        last["bx"],
        last["by"],
        last["bz"],
        -last["dy"] / last["length"],
        last["dx"] / last["length"],
        last["dx"] / last["length"],
        last["dy"] / last["length"],
    )


def _in_bounds(x, y):
    return (
        LEVEL_BOUNDS["min_x"] <= x <= LEVEL_BOUNDS["max_x"]
        and LEVEL_BOUNDS["min_y"] <= y <= LEVEL_BOUNDS["max_y"]
    )


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return ""


def _is_target_tree_component(component):
    mesh_path = _mesh_path(component).lower()
    name = component.get_name().lower()
    text = mesh_path + " " + name
    return "conifer" in text or "pine" in text or "tree" in text


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


def _actor_tags(actor):
    try:
        return [str(tag) for tag in actor.tags]
    except Exception:
        return []


def _tagged_as_block(actor, component=None):
    tags = _actor_tags(actor)
    if component is not None:
        tags.extend(_component_tags(component))
    return any(BLOCK_TAG_TOKEN in tag.lower() for tag in tags)


def _collect_block_bounds():
    bounds = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not _tagged_as_block(actor):
            actor_has_block_tag = False
        else:
            actor_has_block_tag = True

        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not actor_has_block_tag and not _tagged_as_block(actor, component):
                continue
            try:
                origin = component.bounds.origin
                extent = component.bounds.box_extent
            except Exception:
                try:
                    origin = component.get_component_location()
                    extent = unreal.Vector(0.0, 0.0, 0.0)
                except Exception:
                    continue
            mesh = None
            try:
                mesh = component.get_editor_property("static_mesh")
            except Exception:
                pass
            bounds.append(
                {
                    "actor": actor.get_actor_label(),
                    "component": component.get_name(),
                    "tags": _actor_tags(actor) + _component_tags(component),
                    "mesh": mesh.get_path_name() if mesh else None,
                    "origin": [float(origin.x), float(origin.y), float(origin.z)],
                    "extent": [float(extent.x), float(extent.y), float(extent.z)],
                }
            )
    return bounds


def _inside_block_bounds(x, y, block_bounds, margin=360.0):
    for entry in block_bounds or []:
        origin = entry.get("origin") or [0.0, 0.0, 0.0]
        extent = entry.get("extent") or [0.0, 0.0, 0.0]
        if abs(x - origin[0]) <= extent[0] + margin and abs(y - origin[1]) <= extent[1] + margin:
            return True
    return False


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


def _reset_component(component, original_count):
    removed = 0
    while _instance_count(component) > original_count:
        if component.remove_instance(_instance_count(component) - 1):
            removed += 1
        else:
            break
    return removed


def _stable_rng(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return random.Random(seed)


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


def _grid_key(x, y, cell_size):
    return int(math.floor(x / cell_size)), int(math.floor(y / cell_size))


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


def _add_spatial(x, y, spatial, cell_size):
    spatial.setdefault(_grid_key(x, y, cell_size), []).append((x, y))


def _existing_tree_positions():
    positions = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not actor.get_actor_label().startswith("MCP_PCG_"):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not _is_target_tree_component(component):
                continue
            count = _instance_count(component)
            for index in range(count):
                try:
                    location = component.get_instance_transform(index, True).translation
                    positions.append((float(location.x), float(location.y)))
                except Exception:
                    pass
    return positions


def _target_components():
    components = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not actor.get_actor_label().startswith("MCP_PCG_"):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not _is_target_tree_component(component):
                continue
            count = _instance_count(component)
            if count <= 0:
                continue
            components.append(
                {
                    "actor": actor.get_actor_label(),
                    "component": component,
                    "name": component.get_name(),
                    "count": count,
                    "mesh": _mesh_path(component),
                }
            )
    components.sort(key=lambda entry: entry["count"], reverse=True)
    return components[:8]


def _candidate_points(block_bounds=None):
    rng = random.Random(61120261)
    candidates = []
    spatial = {}
    cell_size = 860.0

    for x, y in _existing_tree_positions():
        _add_spatial(x, y, spatial, cell_size)

    def add_candidate(x, y, z, kind, min_road, min_spacing):
        if len(candidates) >= MAX_ADDITIONS:
            return
        if not _in_bounds(x, y):
            return
        if _inside_block_bounds(x, y, block_bounds):
            return
        road_distance = _road_distance(x, y)
        if road_distance < min_road:
            return
        if _too_close(x, y, spatial, cell_size, min_spacing):
            return
        candidates.append((x, y, z, kind, road_distance))
        _add_spatial(x, y, spatial, cell_size)

    road_length = _total_road_length()
    distance = 900.0
    while distance < road_length - 900.0:
        cx, cy, cz, nx, ny, tx, ty = _sample_road(distance)
        for side in (-1.0, 1.0):
            for offset in (3800.0, 5400.0, 7600.0, 10300.0):
                along = rng.uniform(-520.0, 520.0)
                jitter = rng.uniform(-620.0, 620.0)
                x = cx + nx * side * (offset + jitter) + tx * along
                y = cy + ny * side * (offset + jitter) + ty * along
                add_candidate(x, y, cz, "roadside_canopy", 3150.0, 820.0)
        distance += 1150.0

    for gx in range(4200, 48001, 2600):
        for gy in range(0, 52001, 2600):
            x = gx + rng.uniform(-950.0, 950.0)
            y = gy + rng.uniform(-950.0, 950.0)
            add_candidate(x, y, 0.0, "field_mass", 4700.0, 980.0)

    rng.shuffle(candidates)
    return candidates[:MAX_ADDITIONS]


def _scale_for(distance, kind, rng):
    if kind == "roadside_canopy":
        if distance < 5200.0:
            s = rng.uniform(2.35, 3.65)
        elif distance < 8000.0:
            s = rng.uniform(2.75, 4.65)
        else:
            s = rng.uniform(3.15, 5.40)
    else:
        s = rng.uniform(3.05, 5.95)
    return unreal.Vector(s, s, s * rng.uniform(1.02, 1.22))


def boost_road_forest_canopy():
    world = unreal.EditorLevelLibrary.get_editor_world()
    components = _target_components()
    block_bounds = _collect_block_bounds()
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target_component_count": len(components),
        "target_components": [
            {
                "actor": entry["actor"],
                "component": entry["name"],
                "count_before": entry["count"],
                "mesh": entry["mesh"],
            }
            for entry in components
        ],
        "removed_previous_boost": 0,
        "block_tagged_component_count": len(block_bounds),
        "block_tagged_components": block_bounds[:40],
        "candidate_count": 0,
        "added_instances": 0,
        "tree_near_road_after": {"within_1800": 0, "within_2400": 0, "within_3000": 0},
        "pitch_roll_violations_after": 0,
        "samples": [],
        "failures": [],
    }

    if not components:
        raise RuntimeError("No existing PCG tree ISM components found.")

    for entry in components:
        component = entry["component"]
        original_count = _get_or_set_original_count(component)
        report["removed_previous_boost"] += _reset_component(component, original_count)

    candidates = _candidate_points(block_bounds)
    report["candidate_count"] = len(candidates)

    for index, (x, y, fallback_z, kind, road_distance) in enumerate(candidates):
        entry = components[index % len(components)]
        component = entry["component"]
        rng = _stable_rng("road_forest_canopy", index, kind, round(x), round(y))
        z = _sample_ground_z(world, x, y, fallback_z)
        transform = unreal.Transform()
        transform.translation = unreal.Vector(x, y, z)
        transform.rotation = _make_rotator(
            rng.uniform(-2.2, 2.2),
            rng.uniform(0.0, 360.0),
            rng.uniform(-2.2, 2.2),
        ).quaternion()
        transform.scale3d = _scale_for(road_distance, kind, rng)

        try:
            component.add_instance_world_space(transform)
            report["added_instances"] += 1
            if len(report["samples"]) < 32:
                report["samples"].append(
                    {
                        "component": entry["name"],
                        "kind": kind,
                        "road_distance": round(road_distance, 1),
                        "location": [round(x, 1), round(y, 1), round(z, 1)],
                        "scale": [
                            round(transform.scale3d.x, 2),
                            round(transform.scale3d.y, 2),
                            round(transform.scale3d.z, 2),
                        ],
                    }
                )
        except Exception as exc:
            if len(report["failures"]) < 40:
                report["failures"].append(
                    {
                        "component": entry["name"],
                        "index": index,
                        "error": str(exc),
                    }
                )

    checked = 0
    for entry in components:
        component = entry["component"]
        count = _instance_count(component)
        for index in range(count):
            try:
                world_transform = component.get_instance_transform(index, True)
                local_transform = component.get_instance_transform(index, False)
                rotator = local_transform.rotation.rotator()
                if abs(_clamp_angle(rotator.pitch) - rotator.pitch) > 0.01:
                    report["pitch_roll_violations_after"] += 1
                if abs(_clamp_angle(rotator.roll) - rotator.roll) > 0.01:
                    report["pitch_roll_violations_after"] += 1
                distance = _road_distance(
                    world_transform.translation.x, world_transform.translation.y
                )
                if distance < 1800.0:
                    report["tree_near_road_after"]["within_1800"] += 1
                if distance < 2400.0:
                    report["tree_near_road_after"]["within_2400"] += 1
                if distance < 3000.0:
                    report["tree_near_road_after"]["within_3000"] += 1
                checked += 1
            except Exception:
                pass
        try:
            component.mark_render_state_dirty()
        except Exception:
            pass

    report["checked_tree_instances"] = checked
    report["failure_count"] = len(report["failures"])

    try:
        unreal.EditorLevelLibrary.save_current_level()
        report["save_attempted"] = True
    except Exception as exc:
        report["save_attempted"] = "failed: " + str(exc)

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    boost_road_forest_canopy()
