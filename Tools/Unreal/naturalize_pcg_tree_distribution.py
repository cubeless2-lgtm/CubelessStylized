"""Recenter and naturalize PCG tree instance placement across the Cubeless field.

Some Electric Dreams-derived tree graphs create origin-centered template
points. This pass converts those template points into actor-centered world
positions, then applies deterministic road-safe jitter. The result is
idempotent: rerunning the script recomputes the same target positions from
actor location plus known template offsets instead of drifting trees.
"""

import json
import math
import os
import random
import time

import unreal


REPORT_NAME = "CubelessTreeDistributionNaturalize_Report.json"

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

TREE_TEMPLATES = [
    (-1300.0, -700.0),
    (1300.0, -700.0),
    (0.0, 1300.0),
    (0.0, 0.0),
]


def _road_segments():
    segments = []
    for index in range(len(ROAD_POINTS) - 1):
        ax, ay, _az = ROAD_POINTS[index]
        bx, by, _bz = ROAD_POINTS[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
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
    return any(
        token in text
        for token in ["tree", "pine", "spruce", "conifer", "trunk", "branch"]
    )


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _stable_rng(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return random.Random(seed)


def _dist_sq(x1, y1, x2, y2):
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy


def _nearest_template(local_x, local_y):
    best = TREE_TEMPLATES[0]
    best_dist = 10**18
    for tx, ty in TREE_TEMPLATES:
        dist = _dist_sq(local_x, local_y, tx, ty)
        if dist < best_dist:
            best = (tx, ty)
            best_dist = dist
    return best, math.sqrt(best_dist)


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
    key = _grid_key(x, y, cell_size)
    spatial.setdefault(key, []).append((x, y))


def _collect_tree_instances():
    items = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not _is_tree_component(component):
                continue
            count = _instance_count(component)
            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, True)
                    location = transform.translation
                except Exception:
                    continue
                items.append(
                    {
                        "actor": actor,
                        "actor_label": label,
                        "actor_location": actor.get_actor_location(),
                        "component": component,
                        "component_name": component.get_name(),
                        "index": index,
                        "x": float(location.x),
                        "y": float(location.y),
                        "z": float(location.z),
                    }
                )
    return items


def _template_base(entry):
    actor_location = entry["actor_location"]
    current_x = entry["x"]
    current_y = entry["y"]

    # If the point is still an origin template, use that local template.
    if abs(current_x) <= 1800.0 and abs(current_y) <= 1800.0:
        template, distance = _nearest_template(current_x, current_y)
        return (
            actor_location.x + template[0],
            actor_location.y + template[1],
            actor_location.z,
            "origin_template",
            round(distance, 2),
        )

    local_x = current_x - actor_location.x
    local_y = current_y - actor_location.y
    template, distance = _nearest_template(local_x, local_y)
    if distance <= 1800.0:
        return (
            actor_location.x + template[0],
            actor_location.y + template[1],
            actor_location.z,
            "actor_template",
            round(distance, 2),
        )

    # Fallback for hand-placed or already non-template trees.
    return current_x, current_y, entry["z"], "current_world", round(distance, 2)


def naturalize_tree_distribution():
    world = unreal.EditorLevelLibrary.get_editor_world()
    items = _collect_tree_instances()
    cell_size = 520.0
    min_distance = 0.0
    min_road_distance = 3000.0
    spatial = {}
    updated = 0
    removed_near_road = 0
    recentered_origin_templates = 0
    skipped_near_road = 0
    kept_original = 0
    failures = []
    samples = []

    # Stable order prevents a late row from always overriding an early row.
    items.sort(key=lambda entry: (entry["x"], entry["y"], entry["actor_label"]))

    for entry in items:
        current_x = entry["x"]
        current_y = entry["y"]
        current_z = entry["z"]
        base_x, base_y, base_z, base_source, template_distance = _template_base(entry)
        if base_source == "origin_template":
            recentered_origin_templates += 1

        road_distance = _road_distance(base_x, base_y)

        if road_distance < min_road_distance:
            component = entry["component"]
            try:
                component.remove_instance(entry["index"])
                removed_near_road += 1
            except Exception:
                skipped_near_road += 1
                _add_spatial(current_x, current_y, spatial, cell_size)
            continue

        rng = _stable_rng(entry["actor_label"], entry["component_name"], entry["index"])
        chosen = None

        for attempt in range(8):
            radius = rng.uniform(80.0, 360.0)
            if attempt >= 4:
                radius *= 0.55
            angle = rng.uniform(0.0, math.tau)
            x = base_x + math.cos(angle) * radius
            y = base_y + math.sin(angle) * radius
            if not _in_bounds(x, y):
                continue
            if _road_distance(x, y) < min_road_distance:
                continue
            if min_distance > 0.0 and _too_close(x, y, spatial, cell_size, min_distance):
                continue
            chosen = (x, y)
            break

        if not chosen:
            if min_distance <= 0.0 or not _too_close(
                base_x, base_y, spatial, cell_size, min_distance
            ):
                _add_spatial(base_x, base_y, spatial, cell_size)
            kept_original += 1
            continue

        x, y = chosen
        z = _sample_ground_z(world, x, y, base_z if base_z is not None else current_z)
        component = entry["component"]
        index = entry["index"]

        try:
            transform = component.get_instance_transform(index, True)
            transform.translation = unreal.Vector(x, y, z)
            rotator = transform.rotation.rotator()
            pitch = _clamp_angle(rotator.pitch)
            roll = _clamp_angle(rotator.roll)
            yaw = rotator.yaw
            if abs(yaw) < 0.01:
                yaw = rng.uniform(0.0, 360.0)
            transform.rotation = _make_rotator(pitch, yaw, roll).quaternion()

            if component.update_instance_transform(index, transform, True, True, True):
                updated += 1
                _add_spatial(x, y, spatial, cell_size)
                if len(samples) < 30:
                    samples.append(
                        {
                            "actor": entry["actor_label"],
                            "component": entry["component_name"],
                            "index": index,
                            "from": [
                                round(current_x, 1),
                                round(current_y, 1),
                                round(current_z, 1),
                            ],
                            "to": [round(x, 1), round(y, 1), round(z, 1)],
                            "base_source": base_source,
                            "template_distance": template_distance,
                            "road_distance": round(_road_distance(x, y), 1),
                        }
                    )
            else:
                local_transform = component.get_instance_transform(index, False)
                local_transform.translation = unreal.Vector(
                    local_transform.translation.x + (x - current_x),
                    local_transform.translation.y + (y - current_y),
                    local_transform.translation.z + (z - current_z),
                )
                local_rotator = local_transform.rotation.rotator()
                local_pitch = _clamp_angle(local_rotator.pitch)
                local_roll = _clamp_angle(local_rotator.roll)
                local_yaw = local_rotator.yaw
                if abs(local_yaw) < 0.01:
                    local_yaw = yaw
                local_transform.rotation = _make_rotator(
                    local_pitch, local_yaw, local_roll
                ).quaternion()
                if component.update_instance_transform(
                    index, local_transform, False, True, True
                ):
                    updated += 1
                    _add_spatial(x, y, spatial, cell_size)
                    if len(samples) < 30:
                        samples.append(
                            {
                                "actor": entry["actor_label"],
                                "component": entry["component_name"],
                                "index": index,
                                "from": [
                                    round(current_x, 1),
                                    round(current_y, 1),
                                    round(current_z, 1),
                                ],
                                "to": [round(x, 1), round(y, 1), round(z, 1)],
                                "space": "local_fallback",
                                "base_source": base_source,
                                "template_distance": template_distance,
                                "road_distance": round(_road_distance(x, y), 1),
                            }
                        )
                else:
                    kept_original += 1
                    _add_spatial(current_x, current_y, spatial, cell_size)
        except Exception as exc:
            kept_original += 1
            _add_spatial(current_x, current_y, spatial, cell_size)
            if len(failures) < 40:
                failures.append(
                    {
                        "actor": entry["actor_label"],
                        "component": entry["component_name"],
                        "index": index,
                        "error": str(exc),
                    }
                )

    touched_components = set()
    for entry in items:
        component = entry["component"]
        if component in touched_components:
            continue
        touched_components.add(component)
        try:
            component.mark_render_state_dirty()
        except Exception:
            pass

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tree_instances": len(items),
        "updated_instances": updated,
        "recentered_origin_templates": recentered_origin_templates,
        "removed_near_road": removed_near_road,
        "kept_original": kept_original,
        "skipped_near_road": skipped_near_road,
        "min_road_distance": min_road_distance,
        "min_tree_spacing": min_distance,
        "failure_count": len(failures),
        "failures": failures,
        "samples": samples,
        "save_attempted": save_attempted,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    naturalize_tree_distribution()
