"""Build an intentional forest-road composition accent PCG layer.

The level already has broad density. This layer adds readable composition:
roadside understory rhythm, deeper grove anchors, and far-view pine accents.
It is isolated behind a new prefix so it can be regenerated without touching
the user's bookmarks or the existing base PCG layers.
"""

import json
import math
import os
import random
import time

import unreal


PREFIX = "MCP_PCG_CompositionAccentLayer"
REPORT_NAME = "CubelessCompositionAccentLayer_Report.json"
WAIT_SECONDS = 35.0
STATE_ATTR = "_cubeless_composition_accent_layer_state"

BP_CLASS_PATH = (
    "/Game/Cubeless/PCG/ProductionCandidates/Blueprints/"
    "BP_Cubeless_PCG_EcosystemCandidate.BP_Cubeless_PCG_EcosystemCandidate_C"
)

STYLE_GRAPHS = {
    "ClassicGrassNormal": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_ClassicGrass_GroundOnly_GroundNormal"
    ),
    "MixedGrassDense": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_MixedGrass_GroundOnly_GroundDense"
    ),
    "TallGrassDense": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_TallGrass_GroundOnly_GroundDense"
    ),
    "GroundFoliageDense": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_GroundFoliage_GroundOnly_GroundDense"
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

TARGET_CONIFER = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_05.SM_Conifer_05"
)

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
    "min_x": 2500.0,
    "max_x": 48500.0,
    "min_y": -1000.0,
    "max_y": 52500.0,
}


def _road_segments():
    segments = []
    for index in range(len(ROAD_POINTS) - 1):
        ax, ay, az = ROAD_POINTS[index]
        bx, by, bz = ROAD_POINTS[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
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
        yaw = math.degrees(math.atan2(segment["dy"], segment["dx"]))
        return x, y, z, nx, ny, yaw

    segment = ROAD_SEGMENTS[-1]
    yaw = math.degrees(math.atan2(segment["dy"], segment["dx"]))
    return (
        segment["bx"],
        segment["by"],
        segment["bz"],
        -segment["dy"] / segment["length"],
        segment["dx"] / segment["length"],
        yaw,
    )


def _in_bounds(x, y):
    return (
        LEVEL_BOUNDS["min_x"] <= x <= LEVEL_BOUNDS["max_x"]
        and LEVEL_BOUNDS["min_y"] <= y <= LEVEL_BOUNDS["max_y"]
    )


def _jittered(value, amount, rng):
    return value + rng.uniform(-amount, amount)


def _style_for(index, kind):
    patterns = {
        "RoadsideUnderstory": [
            "WarmGroundFoliageDense",
            "MixedGrassDense",
            "GroundFoliageDense",
            "ClassicGrassNormal",
        ],
        "RoadsideFlowerBeat": [
            "WarmGroundFoliageDense",
            "GroundFoliageDense",
            "MixedGrassDense",
        ],
        "DepthGrove": [
            "MixedGrassDense",
            "TallGrassDense",
            "GroundFoliageDense",
        ],
        "VistaPine": [
            "ClassicGrassNormal",
            "MixedGrassDense",
        ],
        "OuterFill": [
            "MixedGrassDense",
            "ClassicGrassNormal",
            "TallGrassDense",
        ],
    }
    pattern = patterns.get(kind, ["MixedGrassDense"])
    return pattern[index % len(pattern)]


def _tree_for(index, kind):
    if kind == "VistaPine":
        pattern = ["DarkColumnSparse", "SoftMixedLightGrove", "SoftCompactSparse"]
    elif kind == "DepthGrove":
        pattern = ["SoftMixedLightGrove", "SoftCompactSparse", "SoftMixedLightGrove"]
    else:
        return None
    return pattern[index % len(pattern)]


def _candidate_specs():
    rng = random.Random(6112026)
    specs = []
    occupied = set()
    road_length = _total_road_length()

    def add_spec(x, y, kind, style_name, tree_name, yaw, min_road, spacing):
        if not _in_bounds(x, y):
            return
        if _road_distance(x, y) < min_road:
            return
        key = (int(round(x / spacing)), int(round(y / spacing)))
        if key in occupied:
            return
        occupied.add(key)
        specs.append(
            {
                "x": x,
                "y": y,
                "kind": kind,
                "style": style_name,
                "tree": tree_name,
                "yaw": yaw,
                "min_road": min_road,
            }
        )

    # Low road-edge rhythm: visible, but placed outside the road surface.
    distances = []
    d = 1200.0
    while d < road_length - 1400.0:
        distances.append(d)
        d += 2300.0

    for i, distance in enumerate(distances):
        cx, cy, _cz, nx, ny, yaw = _sample_road(distance)
        for side in (-1.0, 1.0):
            base_offset = 4150.0 if i % 2 == 0 else 5050.0
            offset = _jittered(base_offset, 360.0, rng)
            along = rng.uniform(-320.0, 320.0)
            tx = math.cos(math.radians(yaw))
            ty = math.sin(math.radians(yaw))
            x = cx + nx * side * offset + tx * along
            y = cy + ny * side * offset + ty * along
            kind = "RoadsideFlowerBeat" if i % 5 == 0 else "RoadsideUnderstory"
            add_spec(
                x,
                y,
                kind,
                _style_for(i + (0 if side < 0 else 1), kind),
                None,
                yaw + side * 10.0,
                2850.0,
                950.0,
            )

    # Mid-depth groves: tree mass is readable from bookmark 5/7, away from road.
    grove_distances = []
    d = 2500.0
    while d < road_length - 2500.0:
        grove_distances.append(d)
        d += 4300.0

    for i, distance in enumerate(grove_distances):
        cx, cy, _cz, nx, ny, yaw = _sample_road(distance)
        for side in (-1.0, 1.0):
            if (i + int(side > 0)) % 3 == 1:
                offset = _jittered(8200.0, 620.0, rng)
            else:
                offset = _jittered(10100.0, 720.0, rng)
            x = cx + nx * side * offset + rng.uniform(-420.0, 420.0)
            y = cy + ny * side * offset + rng.uniform(-420.0, 420.0)
            add_spec(
                x,
                y,
                "DepthGrove",
                _style_for(i, "DepthGrove"),
                _tree_for(i + (0 if side < 0 else 1), "DepthGrove"),
                yaw + side * rng.uniform(25.0, 55.0),
                6100.0,
                1500.0,
            )

    # Far visual anchors: sparse but tall enough to make the forest intentional.
    vista_fractions = [0.10, 0.19, 0.31, 0.44, 0.58, 0.70, 0.83, 0.93]
    for i, fraction in enumerate(vista_fractions):
        cx, cy, _cz, nx, ny, yaw = _sample_road(road_length * fraction)
        for side in (-1.0, 1.0):
            if i % 4 == 2 and side > 0:
                continue
            offset = _jittered(13700.0 + 1200.0 * (i % 2), 900.0, rng)
            x = cx + nx * side * offset + rng.uniform(-600.0, 600.0)
            y = cy + ny * side * offset + rng.uniform(-600.0, 600.0)
            add_spec(
                x,
                y,
                "VistaPine",
                _style_for(i, "VistaPine"),
                _tree_for(i + (0 if side < 0 else 1), "VistaPine"),
                yaw + side * 80.0,
                9300.0,
                1900.0,
            )

    # Fill obvious empty outer cells without creating another uniform grid.
    outer_cells = [
        (5200.0, 4700.0),
        (9200.0, 26600.0),
        (12800.0, 45600.0),
        (17700.0, 5200.0),
        (22500.0, 36500.0),
        (26600.0, 11800.0),
        (31500.0, 42000.0),
        (37200.0, 15800.0),
        (42100.0, 47200.0),
        (46200.0, 23100.0),
        (7200.0, 50500.0),
        (47000.0, 51500.0),
    ]
    for i, (x, y) in enumerate(outer_cells):
        add_spec(
            _jittered(x, 520.0, rng),
            _jittered(y, 520.0, rng),
            "OuterFill",
            _style_for(i, "OuterFill"),
            None,
            rng.uniform(0.0, 360.0),
            3900.0,
            1450.0,
        )

    return specs


def _delete_existing_layer(actors):
    deleted = 0
    for actor in actors:
        if not actor.get_actor_label().startswith(PREFIX):
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


def _z_references(actors):
    refs = []
    for actor in actors:
        label = actor.get_actor_label()
        if label.startswith(PREFIX):
            continue
        if not label.startswith("MCP_PCG_"):
            continue
        location = actor.get_actor_location()
        refs.append((location.x, location.y, location.z))
    return refs


def _nearest_z(x, y, refs):
    if not refs:
        return 0.0
    best_z = 0.0
    best_dist = 10**18
    for rx, ry, rz in refs:
        distance = (x - rx) * (x - rx) + (y - ry) * (y - ry)
        if distance < best_dist:
            best_z = rz
            best_dist = distance
    return best_z


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


def _dist_2d(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)


def _is_unshifted_template(world_location, actor_location):
    if _dist_2d(world_location, actor_location) <= 2600.0:
        return False
    return abs(world_location.x) <= 2600.0 and abs(world_location.y) <= 2600.0


def _normalize_conifer_mesh(component, target_mesh):
    mesh_path = _mesh_path(component)
    if "Conifer" not in mesh_path:
        return False
    if target_mesh and "SM_Conifer_05" not in mesh_path:
        component.set_static_mesh(target_mesh)
        try:
            component.mark_render_state_dirty()
        except Exception:
            pass
        return True
    return False


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


def _stable_rng(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return random.Random(seed)


def _stabilize_and_normalize_instances():
    target_mesh = unreal.load_object(None, TARGET_CONIFER)
    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]

    report = {
        "actor_count": len(actors),
        "tree_template_recentered": 0,
        "conifer_components_normalized": 0,
        "tilt_limited_instances": 0,
        "yaw_randomized_instances": 0,
        "failures": [],
    }

    for actor in actors:
        actor_label = actor.get_actor_label()
        actor_location = actor.get_actor_location()
        components = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
        for component in components:
            category = _classify(component)
            if category == "tree":
                try:
                    if _normalize_conifer_mesh(component, target_mesh):
                        report["conifer_components_normalized"] += 1
                except Exception as exc:
                    report["failures"].append(
                        {
                            "actor": actor_label,
                            "component": component.get_name(),
                            "stage": "normalize_mesh",
                            "error": str(exc),
                        }
                    )

            count = _instance_count(component)
            for index in range(count):
                try:
                    world_transform = component.get_instance_transform(index, True)
                    local_transform = component.get_instance_transform(index, False)

                    if category == "tree" and _is_unshifted_template(
                        world_transform.translation, actor_location
                    ):
                        local_transform.translation = unreal.Vector(
                            world_transform.translation.x,
                            world_transform.translation.y,
                            world_transform.translation.z,
                        )
                        report["tree_template_recentered"] += 1

                    rotator = local_transform.rotation.rotator()
                    pitch = _clamp_angle(rotator.pitch)
                    roll = _clamp_angle(rotator.roll)
                    yaw = rotator.yaw

                    if abs(yaw) < 0.01:
                        yaw = _stable_rng(actor_label, component.get_name(), index).uniform(
                            0.0, 360.0
                        )
                        report["yaw_randomized_instances"] += 1

                    if (
                        abs(pitch - rotator.pitch) > 0.01
                        or abs(roll - rotator.roll) > 0.01
                        or abs(yaw - rotator.yaw) > 0.01
                    ):
                        local_transform.rotation = _make_rotator(
                            pitch, yaw, roll
                        ).quaternion()
                        if component.update_instance_transform(
                            index, local_transform, False, True, True
                        ):
                            report["tilt_limited_instances"] += 1
                except Exception as exc:
                    if len(report["failures"]) < 40:
                        report["failures"].append(
                            {
                                "actor": actor_label,
                                "component": component.get_name(),
                                "index": index,
                                "stage": "normalize_instance",
                                "error": str(exc),
                            }
                        )

            try:
                component.mark_render_state_dirty()
            except Exception:
                pass

    report["failure_count"] = len(report["failures"])
    return report


def _collect_protected_positions():
    protected = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label().startswith(PREFIX):
            continue
        if not actor.get_actor_label().startswith("MCP_PCG_"):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _classify(component)
            if category not in ["tree", "rock"]:
                continue
            count = _instance_count(component)
            for index in range(count):
                location = _instance_location(component, index)
                if not location:
                    continue
                protected.append((location.x, location.y, category))
    return protected


def _too_close_to_positions(location, positions, min_distance):
    min_sq = min_distance * min_distance
    for px, py, _category in positions:
        dx = location.x - px
        dy = location.y - py
        if dx * dx + dy * dy < min_sq:
            return True
    return False


def _prune_tree_and_rock_overlaps():
    protected = _collect_protected_positions()
    accepted = list(protected)
    report = {
        "protected_existing_positions": len(protected),
        "removed_tree_near_road": 0,
        "removed_tree_overlap": 0,
        "removed_rock_near_road": 0,
        "removed_rock_overlap": 0,
        "failed_removals": [],
    }

    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]

    for actor in actors:
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _classify(component)
            if category not in ["tree", "rock"]:
                continue
            min_overlap = 900.0 if category == "tree" else 720.0
            min_road = 3000.0 if category == "tree" else 2300.0
            remove_indexes = []
            keep_locations = []
            count = _instance_count(component)
            for index in range(count):
                location = _instance_location(component, index)
                if not location:
                    continue
                road_distance = _road_distance(location.x, location.y)
                if road_distance < min_road:
                    remove_indexes.append(index)
                    key = f"removed_{category}_near_road"
                    report[key] += 1
                    continue
                if _too_close_to_positions(location, accepted, min_overlap):
                    remove_indexes.append(index)
                    key = f"removed_{category}_overlap"
                    report[key] += 1
                    continue
                keep_locations.append((location.x, location.y, category))
                accepted.append((location.x, location.y, category))

            for index in sorted(remove_indexes, reverse=True):
                try:
                    component.remove_instance(index)
                except Exception as exc:
                    if len(report["failed_removals"]) < 20:
                        report["failed_removals"].append(
                            {
                                "actor": actor.get_actor_label(),
                                "component": component.get_name(),
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


def _configure_component(component, graph, seed, enabled):
    entry = {
        "component": component.get_name(),
        "enabled": enabled,
        "configured": False,
    }
    try:
        component.cleanup(True)
    except Exception as exc:
        entry["cleanup_error"] = str(exc)

    if not enabled:
        try:
            component.deactivate()
        except Exception:
            pass
        return entry

    try:
        component.activate(True)
        component.set_graph(graph)
        try:
            component.set_editor_property("seed", seed)
        except Exception:
            pass
        entry["configured"] = True
    except Exception as exc:
        entry["error"] = str(exc)
    return entry


def _spawn_layer(specs, refs, actor_class, style_graphs, tree_graphs):
    world = unreal.EditorLevelLibrary.get_editor_world()
    results = []

    for index, spec in enumerate(specs):
        style_graph = style_graphs[spec["style"]]
        tree_graph = tree_graphs.get(spec["tree"]) if spec.get("tree") else None
        fallback_z = _nearest_z(spec["x"], spec["y"], refs)
        z = _sample_ground_z(world, spec["x"], spec["y"], fallback_z)
        label = (
            f"{PREFIX}_{index:03d}_{spec['kind']}_"
            f"{spec['style']}_{spec.get('tree') or 'NoTree'}"
        )

        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            actor_class,
            unreal.Vector(spec["x"], spec["y"], z),
            _make_rotator(0.0, spec["yaw"], 0.0),
        )
        if not actor:
            results.append({"label": label, "spawned": False})
            continue

        actor.set_actor_label(label)
        component_results = []
        for component in actor.get_components_by_class(unreal.PCGComponent):
            name = component.get_name()
            if name == "PCG_Style":
                component_results.append(
                    _configure_component(
                        component,
                        style_graph,
                        6112026 + index * 13,
                        True,
                    )
                )
            elif name == "PCG_Tree" and tree_graph:
                component_results.append(
                    _configure_component(
                        component,
                        tree_graph,
                        6113026 + index * 17,
                        True,
                    )
                )
            else:
                component_results.append(
                    _configure_component(component, None, 0, False)
                )

        results.append(
            {
                "label": label,
                "spawned": True,
                "kind": spec["kind"],
                "style": spec["style"],
                "tree": spec.get("tree"),
                "x": round(spec["x"], 1),
                "y": round(spec["y"], 1),
                "z": round(z, 1),
                "road_distance": round(_road_distance(spec["x"], spec["y"]), 1),
                "component_results": component_results,
            }
        )

    return results


def _generate_enabled_components():
    results = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not actor.get_actor_label().startswith(PREFIX):
            continue
        for component in actor.get_components_by_class(unreal.PCGComponent):
            if component.get_name() not in ["PCG_Style", "PCG_Tree"]:
                continue
            entry = {"actor": actor.get_actor_label(), "component": component.get_name()}
            try:
                component.activate(True)
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


def _summarize_layer():
    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]
    summary = {
        "actor_count": len(actors),
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "road_safety": {
            "tree_within_2400": 0,
            "tree_within_3000": 0,
            "rock_within_2400": 0,
            "rock_within_3000": 0,
            "samples": [],
        },
        "zero_actor_count": 0,
        "zero_actor_sample": [],
    }
    by_kind = {}

    for actor in actors:
        actor_total = 0
        label = actor.get_actor_label()
        parts = label.split("_")
        kind = "Unknown"
        if len(parts) > 4:
            kind = parts[4]
        by_kind.setdefault(kind, {"actors": 0, "instances": 0})
        by_kind[kind]["actors"] += 1

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            count = _instance_count(component)
            category = _classify(component)
            actor_total += count
            summary["instances"]["all"] += count
            summary["instances"][category] += count
            by_kind[kind]["instances"] += count

            if category not in ["tree", "rock"]:
                continue
            for index in range(count):
                location = _instance_location(component, index)
                if not location:
                    continue
                distance = _road_distance(location.x, location.y)
                if category == "tree":
                    if distance < 2400.0:
                        summary["road_safety"]["tree_within_2400"] += 1
                    if distance < 3000.0:
                        summary["road_safety"]["tree_within_3000"] += 1
                else:
                    if distance < 2400.0:
                        summary["road_safety"]["rock_within_2400"] += 1
                    if distance < 3000.0:
                        summary["road_safety"]["rock_within_3000"] += 1

                if distance < 3000.0 and len(summary["road_safety"]["samples"]) < 20:
                    summary["road_safety"]["samples"].append(
                        {
                            "actor": label,
                            "component": component.get_name(),
                            "class": category,
                            "distance": round(distance, 1),
                            "x": round(location.x, 1),
                            "y": round(location.y, 1),
                            "z": round(location.z, 1),
                        }
                    )

        if actor_total == 0:
            summary["zero_actor_count"] += 1
            if len(summary["zero_actor_sample"]) < 20:
                summary["zero_actor_sample"].append(label)

    summary["by_kind"] = by_kind
    return summary


def _finish(state):
    stabilization = _stabilize_and_normalize_instances()
    pruning = _prune_tree_and_rock_overlaps()
    summary = _summarize_layer()

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    spawn_results = state.get("spawn_results", [])
    generation_results = state.get("generation_results", [])
    failed_spawns = [entry for entry in spawn_results if not entry.get("spawned")]
    failed_generations = [
        entry for entry in generation_results if not entry.get("generated")
    ]
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "wait_seconds": WAIT_SECONDS,
        "deleted_existing": state.get("deleted_existing", 0),
        "candidate_count": state.get("candidate_count", 0),
        "spawn_count": len(spawn_results) - len(failed_spawns),
        "failed_spawn_count": len(failed_spawns),
        "generation_count": len(generation_results),
        "generation_failed_count": len(failed_generations),
        "stabilization": stabilization,
        "overlap_pruning": pruning,
        "summary": summary,
        "spawn_sample": spawn_results[:40],
        "failed_generations": failed_generations[:20],
        "save_attempted": save_attempted,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


def build_composition_accent_layer():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle") is not None:
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    actor_class = unreal.load_object(None, BP_CLASS_PATH)
    if not actor_class:
        raise RuntimeError("Failed to load actor class: " + BP_CLASS_PATH)

    style_graphs = {}
    for name, path in STYLE_GRAPHS.items():
        graph = unreal.load_object(None, path)
        if not graph:
            raise RuntimeError("Failed to load style graph: " + path)
        style_graphs[name] = graph

    tree_graphs = {}
    for name, path in TREE_GRAPHS.items():
        graph = unreal.load_object(None, path)
        if not graph:
            raise RuntimeError("Failed to load tree graph: " + path)
        tree_graphs[name] = graph

    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    refs = _z_references(actors)
    deleted_existing = _delete_existing_layer(actors)
    specs = _candidate_specs()
    spawn_results = _spawn_layer(specs, refs, actor_class, style_graphs, tree_graphs)
    generation_results = _generate_enabled_components()

    state = {
        "started_at": time.time(),
        "handle": None,
        "completed": False,
        "deleted_existing": deleted_existing,
        "candidate_count": len(specs),
        "spawn_results": spawn_results,
        "generation_results": generation_results,
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
            state["final_report"] = _finish(state)
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
        "deleted_existing": deleted_existing,
        "candidate_count": len(specs),
        "spawn_count": len(spawn_results),
        "generation_count": len(generation_results),
        "generation_failed_count": len(
            [entry for entry in generation_results if not entry.get("generated")]
        ),
        "wait_seconds": WAIT_SECONDS,
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    build_composition_accent_layer()
