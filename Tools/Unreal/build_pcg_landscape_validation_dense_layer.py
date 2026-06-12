"""Build a dense whole-landscape PCG validation layer.

This script is intentionally scoped to the MCP temporary landscape validation
map. It uses the existing Cubeless PCG candidate actor and graphs, then adds
deterministic density supplements only to PCG-generated ISM components.
"""

import json
import math
import os
import random
import time

import unreal


PREFIX = "MCP_PCG_LandscapeDenseValidation"
REPORT_NAME = "pcg_landscape_dense_validation_report.json"
WAIT_SECONDS = 35.0
STATE_ATTR = "_cubeless_landscape_dense_validation_state"

BP_CLASS_PATH = (
    "/Game/Cubeless/PCG/ProductionCandidates/Blueprints/"
    "BP_Cubeless_PCG_EcosystemCandidate.BP_Cubeless_PCG_EcosystemCandidate_C"
)

STYLE_GRAPHS = {
    "MixedGrassDense": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_MixedGrass_Both_GroundDense_DitchDense"
    ),
    "TallGrassDense": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_TallGrass_Both_GroundDense_DitchDense"
    ),
    "GroundFoliageDense": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_GroundFoliage_Both_GroundDense_DitchDense"
    ),
    "WarmGroundFoliageDense": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/TrueMaterialApplied/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_TrueMaterial_WarmLeaf_StyleProfileMatrix_"
        "GroundFoliage_GroundOnly_GroundDense"
    ),
}

TREE_GRAPHS = {
    "SoftMixedLightGrove": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/TrueMaterialApplied/"
        "TreeProfilePresets/"
        "PCG_Cubeless_ED_TrueMaterial_SoftPine_TreeProfile_MixedConifer_LightGrove"
    ),
    "SoftCompactSparse": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/TrueMaterialApplied/"
        "TreeProfilePresets/"
        "PCG_Cubeless_ED_TrueMaterial_SoftPine_TreeProfile_CompactConifer_Sparse"
    ),
    "DarkColumnSparse": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/TrueMaterialApplied/"
        "TreeProfilePresets/"
        "PCG_Cubeless_ED_TrueMaterial_DarkPine_TreeProfile_ColumnConifer_Sparse"
    ),
}

ROAD_CORE_WIDTH = 3600.0
ROAD_FEATHER_WIDTH = 5200.0
TILE_STEP = 15000.0
TILE_RADIUS = 6900.0
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


def _load_required(path):
    obj = unreal.load_object(None, path)
    if not obj:
        obj = unreal.EditorAssetLibrary.load_asset(path)
    if not obj:
        raise RuntimeError("Failed to load asset: " + path)
    return obj


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
        raise RuntimeError("No Landscape actors found in current level.")

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
    # Keep the path centered enough to be useful from broad review views.
    points[4] = (cx, cy)
    return points


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
    text = component.get_name().lower()
    try:
        mesh = component.get_editor_property("static_mesh")
        if mesh:
            text += " " + mesh.get_path_name().lower()
    except Exception:
        pass

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


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _delete_existing_layer():
    deleted = 0
    for actor in _all_level_actors():
        if not _actor_label(actor).startswith(PREFIX):
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


def _style_for(index, road_distance):
    if road_distance < ROAD_CORE_WIDTH + ROAD_FEATHER_WIDTH:
        pattern = ["WarmGroundFoliageDense", "MixedGrassDense", "GroundFoliageDense"]
    elif road_distance < 16000.0:
        pattern = ["MixedGrassDense", "TallGrassDense", "GroundFoliageDense"]
    else:
        pattern = ["GroundFoliageDense", "TallGrassDense", "MixedGrassDense"]
    return pattern[index % len(pattern)]


def _tree_for(index, road_distance):
    if road_distance < 10500.0:
        return None
    pattern = ["SoftMixedLightGrove", "SoftCompactSparse", "DarkColumnSparse"]
    return pattern[index % len(pattern)]


def _target_counts(road_distance):
    if road_distance < ROAD_CORE_WIDTH:
        return {"grass": 0, "tree": 0, "rock": 0}
    if road_distance < ROAD_CORE_WIDTH + ROAD_FEATHER_WIDTH:
        fade = (road_distance - ROAD_CORE_WIDTH) / ROAD_FEATHER_WIDTH
        return {"grass": int(45 + fade * 80), "tree": 0, "rock": 1}
    if road_distance < 16000.0:
        return {"grass": 155, "tree": 4, "rock": 2}
    return {"grass": 220, "tree": 13, "rock": 3}


def _make_specs(bounds, road_segments):
    rng = random.Random(6112031)
    specs = []
    min_x = bounds["min_x"] + TILE_STEP * 0.65
    max_x = bounds["max_x"] - TILE_STEP * 0.65
    min_y = bounds["min_y"] + TILE_STEP * 0.65
    max_y = bounds["max_y"] - TILE_STEP * 0.65

    ix = 0
    x = min_x
    while x <= max_x:
        iy = 0
        y = min_y
        while y <= max_y:
            jitter_x = rng.uniform(-TILE_STEP * 0.18, TILE_STEP * 0.18)
            jitter_y = rng.uniform(-TILE_STEP * 0.18, TILE_STEP * 0.18)
            sx = x + jitter_x
            sy = y + jitter_y
            distance = _road_distance(sx, sy, road_segments)
            if distance >= ROAD_CORE_WIDTH:
                index = len(specs)
                counts = _target_counts(distance)
                specs.append(
                    {
                        "x": sx,
                        "y": sy,
                        "grid": [ix, iy],
                        "road_distance": distance,
                        "style": _style_for(index, distance),
                        "tree": _tree_for(index, distance),
                        "counts": counts,
                    }
                )
            y += TILE_STEP
            iy += 1
        x += TILE_STEP
        ix += 1

    return specs


def _configure_spline(actor):
    for spline in actor.get_components_by_class(unreal.SplineComponent):
        try:
            spline.clear_spline_points(False)
            points = [
                unreal.Vector(-TILE_RADIUS, -TILE_RADIUS, 0.0),
                unreal.Vector(TILE_RADIUS, -TILE_RADIUS, 0.0),
                unreal.Vector(TILE_RADIUS, TILE_RADIUS, 0.0),
                unreal.Vector(-TILE_RADIUS, TILE_RADIUS, 0.0),
            ]
            for point in points:
                spline.add_spline_point(point, unreal.SplineCoordinateSpace.LOCAL, False)
            spline.set_closed_loop(True, False)
            spline.update_spline()
        except Exception:
            pass


def _configure_pcg_components(actor, style_graph, tree_graph, seed):
    rows = []
    for component in actor.get_components_by_class(unreal.PCGComponent):
        name = component.get_name()
        graph = None
        enabled = False
        if name == "PCG_Style":
            graph = style_graph
            enabled = True
        elif name == "PCG_Tree" and tree_graph:
            graph = tree_graph
            enabled = True
        elif name == "PCG_MaterialPreview":
            enabled = False
        row = {"component": name, "enabled": enabled}
        try:
            component.cleanup(True)
        except Exception as exc:
            row["cleanup_error"] = str(exc)
        try:
            if not enabled:
                component.deactivate()
                row["configured"] = True
            else:
                component.activate(True)
                component.set_graph(graph)
                try:
                    component.set_editor_property("seed", seed)
                except Exception:
                    pass
                component.generate(True)
                try:
                    component.generate_local(True)
                except Exception as local_exc:
                    row["generate_local_error"] = str(local_exc)
                row["configured"] = True
        except Exception as exc:
            row["configured"] = False
            row["error"] = str(exc)
        rows.append(row)
    return rows


def _spawn_layer(world, specs, actor_class, style_graphs, tree_graphs):
    rows = []
    for index, spec in enumerate(specs):
        fallback_z = 0.0
        z, _hit_landscape, _normal = _sample_ground_z(world, spec["x"], spec["y"], fallback_z)
        yaw = _stable_rng("actor", index, round(spec["x"]), round(spec["y"])).uniform(0.0, 360.0)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            actor_class,
            unreal.Vector(spec["x"], spec["y"], z + 8.0),
            _make_rotator(0.0, yaw, 0.0),
        )
        if not actor:
            rows.append({"index": index, "spawned": False, "spec": spec})
            continue
        label = (
            f"{PREFIX}_{index:03d}_{spec['style']}_"
            f"{spec['tree'] or 'NoTree'}"
        )
        actor.set_actor_label(label)
        _configure_spline(actor)
        style_graph = style_graphs[spec["style"]]
        tree_graph = tree_graphs.get(spec["tree"]) if spec.get("tree") else None
        rows.append(
            {
                "index": index,
                "spawned": True,
                "label": label,
                "x": round(spec["x"], 1),
                "y": round(spec["y"], 1),
                "z": round(z, 1),
                "road_distance": round(spec["road_distance"], 1),
                "style": spec["style"],
                "tree": spec["tree"],
                "targets": spec["counts"],
                "components": _configure_pcg_components(
                    actor, style_graph, tree_graph, 6112031 + index
                ),
            }
        )
    return rows


def _target_actors():
    return [actor for actor in _all_level_actors() if _actor_label(actor).startswith(PREFIX)]


def _components_by_category(actor):
    result = {"grass": [], "tree": [], "rock": [], "other": []}
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        category = _classify_component(component)
        result.setdefault(category, []).append(component)
    return result


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


def _collect_existing_tree_rock_positions(actors):
    spatial = {}
    cell_size = 1250.0
    for actor in actors:
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if _classify_component(component) not in {"tree", "rock"}:
                continue
            count = _instance_count(component)
            for index in range(count):
                try:
                    location = component.get_instance_transform(index, True).translation
                    _add_spatial(location.x, location.y, spatial, cell_size)
                except Exception:
                    pass
    return spatial, cell_size


def _candidate_location(spec, rng):
    angle = rng.uniform(0.0, math.tau)
    distance = math.sqrt(rng.random()) * TILE_RADIUS
    return spec["x"] + math.cos(angle) * distance, spec["y"] + math.sin(angle) * distance


def _grass_acceptance(distance):
    if distance < ROAD_CORE_WIDTH:
        return 0.0
    if distance < ROAD_CORE_WIDTH + ROAD_FEATHER_WIDTH:
        return 0.15 + 0.70 * ((distance - ROAD_CORE_WIDTH) / ROAD_FEATHER_WIDTH)
    return 1.0


def _make_transform(x, y, z, category, rng, normal=None):
    transform = unreal.Transform()
    transform.translation = unreal.Vector(x, y, z)
    yaw = rng.uniform(0.0, 360.0)
    if category == "tree":
        pitch = rng.uniform(-3.0, 3.0)
        roll = rng.uniform(-3.0, 3.0)
        scale = rng.uniform(1.55, 3.35)
        transform.scale3d = unreal.Vector(scale, scale, scale * rng.uniform(1.02, 1.18))
    elif category == "rock":
        pitch = rng.uniform(-4.0, 4.0)
        roll = rng.uniform(-4.0, 4.0)
        scale = rng.uniform(0.50, 4.00)
        transform.scale3d = unreal.Vector(scale, scale, scale * rng.uniform(0.65, 1.10))
    else:
        pitch = rng.uniform(-3.5, 3.5)
        roll = rng.uniform(-3.5, 3.5)
        scale = rng.uniform(0.76, 1.44)
        transform.scale3d = unreal.Vector(scale, scale, rng.uniform(0.82, 1.28))
    if category == "grass" and normal is not None:
        transform.rotation = _normal_aligned_quat(normal, yaw)
    else:
        transform.rotation = _make_rotator(pitch, yaw, roll).quaternion()
    return transform


def _add_instances(component, transforms):
    added = 0
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


def _supplement_density(world, specs, road_segments):
    actors = _target_actors()
    actor_by_grid = {}
    for actor in actors:
        label = _actor_label(actor)
        parts = label.split("_")
        try:
            index = int(parts[4])
            actor_by_grid[index] = actor
        except Exception:
            pass

    spatial, spatial_cell = _collect_existing_tree_rock_positions(actors)
    report = {
        "actor_count": len(actors),
        "added": {"grass": 0, "tree": 0, "rock": 0},
        "missing_components": {"grass": 0, "tree": 0, "rock": 0},
        "landscape_trace_misses": {"grass": 0, "tree": 0, "rock": 0},
        "samples": [],
    }

    for index, spec in enumerate(specs):
        actor = actor_by_grid.get(index)
        if not actor:
            continue
        components = _components_by_category(actor)
        rng = _stable_rng("dense_supplement", index, round(spec["x"]), round(spec["y"]))
        counts = spec["counts"]

        for category in ["grass", "tree", "rock"]:
            target = counts.get(category, 0)
            if target <= 0:
                continue
            candidates = components.get(category) or []
            if not candidates:
                report["missing_components"][category] += 1
                continue

            transforms_by_component = {component: [] for component in candidates}
            attempts = 0
            made = 0
            max_attempts = max(80, target * 10)
            while made < target and attempts < max_attempts:
                attempts += 1
                x, y = _candidate_location(spec, rng)
                distance = _road_distance(x, y, road_segments)

                if category == "grass":
                    if rng.random() > _grass_acceptance(distance):
                        continue
                elif category == "tree":
                    if distance < 9000.0:
                        continue
                    if _too_close(x, y, spatial, spatial_cell, 1250.0):
                        continue
                    _add_spatial(x, y, spatial, spatial_cell)
                elif category == "rock":
                    if distance < 5600.0:
                        continue
                    if _too_close(x, y, spatial, spatial_cell, 850.0):
                        continue
                    _add_spatial(x, y, spatial, spatial_cell)

                z, hit_landscape, normal = _sample_ground_z(world, x, y, actor.get_actor_location().z)
                if not hit_landscape:
                    report["landscape_trace_misses"][category] += 1
                    continue
                component = candidates[made % len(candidates)]
                transforms_by_component[component].append(
                    _make_transform(x, y, z, category, rng, normal)
                )
                made += 1

            for component, transforms in transforms_by_component.items():
                if not transforms:
                    continue
                added = _add_instances(component, transforms)
                report["added"][category] += added
                if len(report["samples"]) < 40:
                    report["samples"].append(
                        {
                            "actor": _actor_label(actor),
                            "component": component.get_name(),
                            "category": category,
                            "added": added,
                        }
                    )

    return report


def _summarize_layer(world, road_segments):
    summary = {
        "actor_count": 0,
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "road_violations": {
            "grass_in_core": 0,
            "tree_within_9000": 0,
            "rock_within_5600": 0,
        },
        "tilt_violations": 0,
        "zero_actor_count": 0,
    }
    for actor in _target_actors():
        summary["actor_count"] += 1
        actor_total = 0
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _classify_component(component)
            count = _instance_count(component)
            summary["instances"]["all"] += count
            summary["instances"].setdefault(category, 0)
            summary["instances"][category] += count
            actor_total += count
            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, True)
                    location = transform.translation
                    rot = transform.rotation.rotator()
                except Exception:
                    continue
                distance = _road_distance(location.x, location.y, road_segments)
                if category == "grass" and distance < ROAD_CORE_WIDTH:
                    summary["road_violations"]["grass_in_core"] += 1
                if category == "tree" and distance < 9000.0:
                    summary["road_violations"]["tree_within_9000"] += 1
                if category == "rock" and distance < 5600.0:
                    summary["road_violations"]["rock_within_5600"] += 1
                if category == "grass":
                    normal = _sample_ground_normal(world, location)
                    if normal is None or _angle_degrees(_quat_up(transform.rotation), normal) > 5.01:
                        summary["tilt_violations"] += 1
                elif abs(rot.pitch) > 5.01 or abs(rot.roll) > 5.01:
                    summary["tilt_violations"] += 1
        if actor_total == 0:
            summary["zero_actor_count"] += 1
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


def _finish(state):
    world = unreal.EditorLevelLibrary.get_editor_world()
    supplement = _supplement_density(world, state["specs"], state["road_segments"])
    summary = _summarize_layer(world, state["road_segments"])
    save_result = _save_map_only()
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "complete",
        "prefix": PREFIX,
        "level": state["level"],
        "landscape_bounds": state["bounds"],
        "road_points": state["road_points"],
        "deleted_existing": state["deleted_existing"],
        "candidate_count": len(state["specs"]),
        "spawned_count": len([row for row in state["spawn_rows"] if row.get("spawned")]),
        "spawn_sample": state["spawn_rows"][:24],
        "supplement": supplement,
        "summary": summary,
        "save_map_only": save_result,
        "notes": [
            "Generated actors use the existing PCG candidate Blueprint and PCG graphs.",
            "Density supplements are appended only to ISM components produced under those PCG actors.",
            "Grass is allowed to overlap grass more than trees/rocks; tree and rock spacing is protected.",
            "Pitch/Roll are limited to +/-5 degrees while yaw remains random.",
        ],
    }
    report_path = _write_report(report)
    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


def build_pcg_landscape_validation_dense_layer():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle") is not None:
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world is available.")

    actor_class = _load_required(BP_CLASS_PATH)
    style_graphs = {name: _load_required(path) for name, path in STYLE_GRAPHS.items()}
    tree_graphs = {name: _load_required(path) for name, path in TREE_GRAPHS.items()}

    actors = _all_level_actors()
    bounds = _landscape_bounds(actors)
    road_points = _make_road_points(bounds)
    road_segments = _road_segments(road_points)
    specs = _make_specs(bounds, road_segments)
    deleted_existing = _delete_existing_layer()
    spawn_rows = _spawn_layer(world, specs, actor_class, style_graphs, tree_graphs)

    state = {
        "started_at": time.time(),
        "handle": None,
        "completed": False,
        "level": world.get_outer().get_path_name(),
        "bounds": bounds,
        "road_points": road_points,
        "road_segments": road_segments,
        "specs": specs,
        "deleted_existing": deleted_existing,
        "spawn_rows": spawn_rows,
    }

    def _tick(_delta_seconds):
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
            state["final_report"] = _finish(state)
        except Exception as exc:
            state["error"] = str(exc)
            report_path = _write_report(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "failed",
                    "prefix": PREFIX,
                    "error": str(exc),
                }
            )
            print(json.dumps({"status": "failed", "report": report_path, "error": str(exc)}, ensure_ascii=False))
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)

    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "scheduled",
        "prefix": PREFIX,
        "level": state["level"],
        "landscape_actor_count": bounds["count"],
        "candidate_count": len(specs),
        "spawned_count": len([row for row in spawn_rows if row.get("spawned")]),
        "deleted_existing": deleted_existing,
        "wait_seconds": WAIT_SECONDS,
    }
    report_path = _write_report(scheduled)
    print(json.dumps({"report": report_path, **scheduled}, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    build_pcg_landscape_validation_dense_layer()
