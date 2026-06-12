"""Build a readable static-mesh road surface from the Cubeless road spline."""

import json
import math
import os
import time

import unreal


PREFIX = "MCP_RoadSurfaceVisual"
REPORT_NAME = "CubelessRoadSurfaceVisual_Report.json"
MESH_FOLDER = "/Game/Cubeless/PCG/Runtime/Meshes"
MATERIAL_FOLDER = "/Game/Cubeless/PCG/Runtime/Materials"
CUBE_MESH = "/Engine/BasicShapes/Cube.Cube"
SEGMENT_STEP = 700.0

ROAD_SOURCE_LABELS = [
    "MCP_PCG_RoadMaskSpline_ClearForest_Test",
    "MCP_Cubeless_PCG_ForestRoadRuntime_Validation",
    "MCP_RoadAuthoringHandle_Prototype",
]

FALLBACK_ROAD_POINTS = [
    (4740.5, 10249.0, -54.2),
    (11204.9, 12049.1, -19.4),
    (17281.7, 16363.3, 1.1),
    (23407.1, 20512.5, 1.1),
    (29277.9, 25104.5, 1.1),
    (35071.3, 29853.7, 1.1),
    (40847.3, 34671.2, 1.1),
    (46419.2, 39919.5, 1.1),
]

LAYERS = [
    {
        "name": "Shoulder",
        "label": f"{PREFIX}_Shoulder",
        "mesh_name": "SM_Cubeless_PCG_RoadSurface_ShoulderVisualQA",
        "material_name": "M_Cubeless_PCG_RoadSurface_ShoulderVisual",
        "base_color": (0.18, 0.125, 0.055),
        "roughness": 0.96,
        "specular": 0.08,
        "width": 6400.0,
        "z_offset": 125.0,
        "uv_scale": 2600.0,
    },
    {
        "name": "Core",
        "label": f"{PREFIX}_Core",
        "mesh_name": "SM_Cubeless_PCG_RoadSurface_CoreVisualQA",
        "material_name": "M_Cubeless_PCG_RoadSurface_CoreVisual",
        "base_color": (0.23, 0.115, 0.035),
        "roughness": 0.98,
        "specular": 0.04,
        "width": 3300.0,
        "z_offset": 150.0,
        "uv_scale": 1800.0,
    },
]


def _as_tuple(vector):
    return (float(vector.x), float(vector.y), float(vector.z))


def _find_actor(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def _read_road_spline_points():
    for label in ROAD_SOURCE_LABELS:
        actor = _find_actor(label)
        if not actor:
            continue
        splines = actor.get_components_by_class(unreal.SplineComponent)
        for spline in splines:
            if spline.get_name() != "Road_SourceSpline":
                continue
            count = int(spline.get_number_of_spline_points())
            if count < 2:
                continue
            points = []
            for index in range(count):
                location = spline.get_location_at_spline_point(
                    index, unreal.SplineCoordinateSpace.WORLD
                )
                points.append(_as_tuple(location))
            total_length = sum(
                _segment_length(points[i], points[i + 1])
                for i in range(len(points) - 1)
            )
            if count < 4 or total_length < 20000.0:
                continue
            return points, {"source": "spline", "actor": label, "point_count": count}
    return list(FALLBACK_ROAD_POINTS), {
        "source": "fallback",
        "actor": None,
        "point_count": len(FALLBACK_ROAD_POINTS),
    }


def _segment_length(a, b):
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)


def _densify(points, step=650.0):
    dense = [points[0]]
    for index in range(len(points) - 1):
        a = points[index]
        b = points[index + 1]
        length = _segment_length(a, b)
        samples = max(1, int(math.ceil(length / step)))
        for sample in range(1, samples + 1):
            t = sample / float(samples)
            dense.append(
                (
                    a[0] + (b[0] - a[0]) * t,
                    a[1] + (b[1] - a[1]) * t,
                    a[2] + (b[2] - a[2]) * t,
                )
            )
    return dense


def _safe_normalize(x, y):
    length = math.sqrt(x * x + y * y)
    if length <= 1.0e-6:
        return 1.0, 0.0
    return x / length, y / length


def _tangent(points, index):
    if index <= 0:
        a = points[0]
        b = points[1]
    elif index >= len(points) - 1:
        a = points[-2]
        b = points[-1]
    else:
        a = points[index - 1]
        b = points[index + 1]
    return _safe_normalize(b[0] - a[0], b[1] - a[1])


def _road_distance_segments(points):
    segments = []
    for index in range(len(points) - 1):
        a = points[index]
        b = points[index + 1]
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            segments.append((a[0], a[1], dx, dy, length))
    return segments


def _road_distance(x, y, segments):
    best = 10**12
    for ax, ay, dx, dy, length in segments:
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (length * length)))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best


def _cumulative_lengths(points):
    lengths = [0.0]
    for index in range(len(points) - 1):
        lengths.append(lengths[-1] + _segment_length(points[index], points[index + 1]))
    return lengths


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


def _delete_existing_actors():
    deleted = 0
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if not actor.get_actor_label().startswith(PREFIX):
            continue
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted += 1
        except Exception:
            pass
    return deleted


def _mesh_object_path(mesh_name):
    return f"{MESH_FOLDER}/{mesh_name}.{mesh_name}"


def _material_object_path(material_name):
    return f"{MATERIAL_FOLDER}/{material_name}.{material_name}"


def _load_or_create_static_mesh(mesh_name):
    unreal.EditorAssetLibrary.make_directory(MESH_FOLDER)
    mesh = unreal.load_object(None, _mesh_object_path(mesh_name))
    if mesh:
        return mesh, False

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mesh = asset_tools.create_asset(mesh_name, MESH_FOLDER, unreal.StaticMesh, None)
    if not mesh:
        raise RuntimeError("Failed to create static mesh: " + _mesh_object_path(mesh_name))
    return mesh, True


def _load_or_create_visual_material(layer):
    unreal.EditorAssetLibrary.make_directory(MATERIAL_FOLDER)
    material_path = _material_object_path(layer["material_name"])
    material = unreal.load_object(None, material_path)
    created = False
    if material:
        created = False
    else:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = asset_tools.create_asset(
            layer["material_name"],
            MATERIAL_FOLDER,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
        created = True
        if not material:
            raise RuntimeError("Failed to create material: " + material_path)

    lib = unreal.MaterialEditingLibrary
    try:
        material.set_editor_property("two_sided", True)
    except Exception:
        pass
    try:
        lib.delete_all_material_expressions(material)
    except Exception:
        pass

    color = layer["base_color"]
    color_node = lib.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -420, -140
    )
    color_node.set_editor_property(
        "constant", unreal.LinearColor(color[0], color[1], color[2], 1.0)
    )
    lib.connect_material_property(color_node, "", unreal.MaterialProperty.MP_BASE_COLOR)

    roughness_node = lib.create_material_expression(
        material, unreal.MaterialExpressionConstant, -420, 20
    )
    roughness_node.set_editor_property("r", float(layer["roughness"]))
    lib.connect_material_property(roughness_node, "", unreal.MaterialProperty.MP_ROUGHNESS)

    specular_node = lib.create_material_expression(
        material, unreal.MaterialExpressionConstant, -420, 160
    )
    specular_node.set_editor_property("r", float(layer["specular"]))
    lib.connect_material_property(specular_node, "", unreal.MaterialProperty.MP_SPECULAR)

    try:
        lib.layout_material_expressions(material)
    except Exception:
        pass
    try:
        lib.recompile_material(material)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material, created


def _build_ribbon_mesh(mesh, material, points, width, z_offset, uv_scale):
    dense = _densify(points)
    cumulative = _cumulative_lengths(dense)
    world = unreal.EditorLevelLibrary.get_editor_world()
    desc = mesh.create_static_mesh_description()
    polygon_group = desc.create_polygon_group()
    desc.set_polygon_group_material_slot_name(polygon_group, "Road")

    left_instances = []
    right_instances = []
    half_width = width * 0.5
    min_x = min(point[0] for point in dense)
    max_x = max(point[0] for point in dense)
    min_y = min(point[1] for point in dense)
    max_y = max(point[1] for point in dense)
    origin = (
        (min_x + max_x) * 0.5,
        (min_y + max_y) * 0.5,
        0.0,
    )

    for index, point in enumerate(dense):
        surface_z = _sample_ground_z(world, point[0], point[1], point[2])
        tx, ty = _tangent(dense, index)
        nx, ny = -ty, tx
        z = surface_z + z_offset
        left = (point[0] + nx * half_width, point[1] + ny * half_width, z)
        right = (point[0] - nx * half_width, point[1] - ny * half_width, z)
        u_length = cumulative[index] / max(1.0, uv_scale)

        left_vertex = desc.create_vertex()
        desc.set_vertex_position(
            left_vertex,
            unreal.Vector(left[0] - origin[0], left[1] - origin[1], left[2] - origin[2]),
        )
        left_instance = desc.create_vertex_instance(left_vertex)
        desc.set_vertex_instance_uv(left_instance, unreal.Vector2D(0.0, u_length), 0)

        right_vertex = desc.create_vertex()
        desc.set_vertex_position(
            right_vertex,
            unreal.Vector(
                right[0] - origin[0],
                right[1] - origin[1],
                right[2] - origin[2],
            ),
        )
        right_instance = desc.create_vertex_instance(right_vertex)
        desc.set_vertex_instance_uv(right_instance, unreal.Vector2D(1.0, u_length), 0)

        left_instances.append(left_instance)
        right_instances.append(right_instance)

    for index in range(len(dense) - 1):
        desc.create_triangle(
            polygon_group,
            [left_instances[index], right_instances[index + 1], right_instances[index]],
        )
        desc.create_triangle(
            polygon_group,
            [left_instances[index], left_instances[index + 1], right_instances[index + 1]],
        )

    mesh.build_from_static_mesh_descriptions([desc])
    mesh.set_material(0, material)
    try:
        mesh.modify()
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)

    return {
        "vertex_count": len(dense) * 2,
        "triangle_count": (len(dense) - 1) * 2,
        "point_count": len(dense),
        "width": width,
        "z_offset": z_offset,
        "actor_origin": origin,
    }


def _spawn_mesh_actor(label, mesh, material, actor_origin):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(float(actor_origin[0]), float(actor_origin[1]), float(actor_origin[2])),
    )
    if not actor:
        raise RuntimeError("Failed to spawn actor: " + label)
    actor.set_actor_label(label)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        raise RuntimeError("StaticMeshActor missing StaticMeshComponent: " + label)
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    try:
        component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    except Exception:
        pass
    try:
        component.set_editor_property("bounds_scale", 2.0)
    except Exception:
        pass
    return actor


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _spawn_segment_visual_layer(layer, material, points):
    cube = unreal.load_object(None, CUBE_MESH)
    if not cube:
        raise RuntimeError("Failed to load cube mesh: " + CUBE_MESH)

    dense = _densify(points, SEGMENT_STEP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = []
    width = float(layer["width"])
    z_offset = float(layer["z_offset"])
    half_step_overlap = 420.0

    for index in range(len(dense) - 1):
        a = dense[index]
        b = dense[index + 1]
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1.0:
            continue

        mx = (a[0] + b[0]) * 0.5
        my = (a[1] + b[1]) * 0.5
        mz = (
            _sample_ground_z(world, a[0], a[1], a[2])
            + _sample_ground_z(world, b[0], b[1], b[2])
        ) * 0.5 + z_offset
        yaw = math.degrees(math.atan2(dy, dx))
        label = f"{layer['label']}_{index:03d}"
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(mx, my, mz),
            _make_rotator(0.0, yaw, 0.0),
        )
        if not actor:
            continue
        actor.set_actor_label(label)
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if not component:
            continue
        component.set_static_mesh(cube)
        component.set_material(0, material)
        actor.set_actor_scale3d(
            unreal.Vector((length + half_step_overlap) / 100.0, width / 100.0, 0.16)
        )
        try:
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        except Exception:
            pass
        try:
            component.set_editor_property("collision_profile_name", "NoCollision")
        except Exception:
            pass
        try:
            component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        except Exception:
            pass
        actors.append(actor)

    return {
        "actor_count": len(actors),
        "segment_count": max(0, len(dense) - 1),
        "point_count": len(dense),
        "width": width,
        "z_offset": z_offset,
        "mesh": CUBE_MESH,
    }


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
    if any(token in text for token in ["tree", "pine", "spruce", "conifer", "trunk"]):
        return "tree"
    if any(token in text for token in ["rock", "stone", "boulder"]):
        return "rock"
    if any(token in text for token in ["grass", "foliage", "leaf", "leaves", "fern", "plant"]):
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


def _summarize_safety(points):
    segments = _road_distance_segments(points)
    summary = {
        "tree_within_1800": 0,
        "tree_within_2400": 0,
        "rock_within_1800": 0,
        "rock_within_2400": 0,
        "samples": [],
    }
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
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
                distance = _road_distance(location.x, location.y, segments)
                if category == "tree":
                    if distance < 1800.0:
                        summary["tree_within_1800"] += 1
                    if distance < 2400.0:
                        summary["tree_within_2400"] += 1
                else:
                    if distance < 1800.0:
                        summary["rock_within_1800"] += 1
                    if distance < 2400.0:
                        summary["rock_within_2400"] += 1
                if distance < 2400.0 and len(summary["samples"]) < 20:
                    summary["samples"].append(
                        {
                            "actor": label,
                            "component": component.get_name(),
                            "class": category,
                            "distance": round(distance, 1),
                        }
                    )
    return summary


def _summarize_existing_visual_actors():
    entries = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not actor.get_actor_label().startswith(PREFIX):
            continue
        spline_mesh_count = len(actor.get_components_by_class(unreal.SplineMeshComponent))
        static_mesh_count = len(actor.get_components_by_class(unreal.StaticMeshComponent))
        entries.append(
            {
                "label": actor.get_actor_label(),
                "class": actor.get_class().get_name(),
                "static_mesh_components": static_mesh_count,
                "spline_mesh_components": spline_mesh_count,
            }
        )
    return entries


def build_road_surface_visual():
    road_points, road_source = _read_road_spline_points()
    deleted_existing = _delete_existing_actors()
    layer_reports = []

    for layer in LAYERS:
        material, material_created = _load_or_create_visual_material(layer)
        mesh_report = _spawn_segment_visual_layer(layer, material, road_points)
        layer_reports.append(
            {
                "name": layer["name"],
                "label_prefix": layer["label"],
                "material": _material_object_path(layer["material_name"]),
                "material_created": material_created,
                "base_color": layer["base_color"],
                **mesh_report,
            }
        )

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "deleted_existing": deleted_existing,
        "road_source": road_source,
        "road_point_count": len(road_points),
        "layers": layer_reports,
        "visual_actors": _summarize_existing_visual_actors(),
        "road_safety": _summarize_safety(road_points),
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
    build_road_surface_visual()
