"""Build a safer spline-mesh road visual for the Landscape PCG validation map.

This avoids rebuilding StaticMesh assets from Python. It uses engine cube mesh
as the deformable SplineMesh source and only replaces the cube-segment fallback
after the spline-mesh pass is successfully spawned.
"""

import json
import math
import os
import time

import unreal


PREFIX = "MCP_RoadSplineSurfaceVisual"
FALLBACK_PREFIX = "MCP_RoadSurfaceVisual"
REPORT_NAME = "CubelessRoadSplineMeshVisual_Report.json"

ROAD_MASK_ACTOR_LABEL = "MCP_PCG_RoadMaskSpline_ClearForest_Test"
ROAD_MASK_SPLINE_NAME = "Road_SourceSpline"

ROAD_SOURCE_MESH = "/Engine/BasicShapes/Plane.Plane"
CORE_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "M_Cubeless_PCG_RoadSurface_CoreVisual.M_Cubeless_PCG_RoadSurface_CoreVisual"
)
SHOULDER_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "M_Cubeless_PCG_RoadSurface_ShoulderVisual.M_Cubeless_PCG_RoadSurface_ShoulderVisual"
)

SAMPLE_STEP = 12000.0
MIN_SEGMENT_LENGTH = 350.0

LAYERS = [
    {
        "name": "Shoulder",
        "label_prefix": f"{PREFIX}_Shoulder",
        "material": SHOULDER_MATERIAL,
        "base_color": (0.075, 0.058, 0.032),
        "roughness": 0.98,
        "specular": 0.015,
        "width": 5200.0,
        "z_offset": 205.0,
        "cross_scale": 1.0,
    },
    {
        "name": "Core",
        "label_prefix": f"{PREFIX}_Core",
        "material": CORE_MATERIAL,
        "base_color": (0.16, 0.078, 0.032),
        "roughness": 0.98,
        "specular": 0.02,
        "width": 2700.0,
        "z_offset": 235.0,
        "cross_scale": 1.0,
    },
]


def _all_actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def _find_actor(label):
    for actor in _all_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def _find_road_spline():
    actor = _find_actor(ROAD_MASK_ACTOR_LABEL)
    if not actor:
        raise RuntimeError("Missing road mask actor: " + ROAD_MASK_ACTOR_LABEL)

    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    for spline in splines:
        if spline.get_name() == ROAD_MASK_SPLINE_NAME:
            return actor, spline
    if splines:
        return actor, splines[0]
    raise RuntimeError("Road mask actor has no SplineComponent.")


def _road_points_from_spline(spline, step=SAMPLE_STEP):
    length = float(spline.get_spline_length())
    if length < MIN_SEGMENT_LENGTH:
        raise RuntimeError("Road spline is too short: %.2f" % length)

    sample_count = max(2, int(math.ceil(length / float(step))) + 1)
    points = []
    for index in range(sample_count):
        distance = min(length, (length * index) / float(sample_count - 1))
        location = spline.get_location_at_distance_along_spline(
            distance, unreal.SplineCoordinateSpace.WORLD
        )
        points.append(unreal.Vector(location.x, location.y, location.z))
    return points, length


def _ignore_actors_for_trace():
    ignored = []
    for actor in _all_actors():
        label = actor.get_actor_label()
        if (
            label.startswith(PREFIX)
            or label.startswith(FALLBACK_PREFIX)
            or label.startswith("MCP_Cubeless_PCG_LandscapeVisualBaseline_")
            or label == ROAD_MASK_ACTOR_LABEL
        ):
            ignored.append(actor)
    return ignored


def _sample_landscape_z(world, x, y, fallback_z, ignored):
    start = unreal.Vector(float(x), float(y), 80000.0)
    end = unreal.Vector(float(x), float(y), -20000.0)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            ignored,
            unreal.DrawDebugTrace.NONE,
            True,
        )
        values = hit.to_tuple()
    except Exception:
        return float(fallback_z), False

    if not values or not bool(values[0]):
        return float(fallback_z), False

    actor = values[9] if len(values) > 9 else None
    component = values[10] if len(values) > 10 else None
    actor_text = ""
    component_text = ""
    try:
        actor_text = actor.get_actor_label() + " " + actor.get_class().get_name()
    except Exception:
        pass
    try:
        component_text = component.get_name() + " " + component.get_class().get_name()
    except Exception:
        pass
    if "Landscape" not in actor_text and "Landscape" not in component_text:
        return float(fallback_z), False

    location = values[4]
    return float(location.z), True


def _grounded_points(points):
    world = unreal.EditorLevelLibrary.get_editor_world()
    ignored = _ignore_actors_for_trace()
    grounded = []
    misses = 0
    for point in points:
        z, hit = _sample_landscape_z(world, point.x, point.y, point.z, ignored)
        if not hit:
            misses += 1
        grounded.append(unreal.Vector(point.x, point.y, z))
    return grounded, misses


def _delete_prefixed(prefix):
    deleted = 0
    for actor in _all_actors():
        if not actor.get_actor_label().startswith(prefix):
            continue
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted += 1
        except Exception:
            pass
    return deleted


def _set_with_optional_update(method, *args):
    try:
        return method(*args, True)
    except TypeError:
        return method(*args)


def _make_zero_rotator():
    rotator = unreal.Rotator()
    rotator.pitch = 0.0
    rotator.yaw = 0.0
    rotator.roll = 0.0
    return rotator


def _spawn_spline_mesh(layer, mesh, material, start, end, index):
    delta = unreal.Vector(end.x - start.x, end.y - start.y, end.z - start.z)
    length = math.sqrt(delta.x * delta.x + delta.y * delta.y + delta.z * delta.z)
    if length < MIN_SEGMENT_LENGTH:
        return None

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SplineMeshActor, start, _make_zero_rotator()
    )
    if not actor:
        raise RuntimeError("Failed to spawn SplineMeshActor.")

    label = f"{layer['label_prefix']}_{index:03d}"
    actor.set_actor_label(label)
    component = actor.get_component_by_class(unreal.SplineMeshComponent)
    if not component:
        raise RuntimeError("SplineMeshActor missing SplineMeshComponent: " + label)

    component.set_static_mesh(mesh)
    component.set_material(0, material)
    try:
        component.set_forward_axis(unreal.SplineMeshAxis.X)
    except Exception:
        try:
            component.set_editor_property("forward_axis", unreal.SplineMeshAxis.X)
        except Exception:
            pass

    local_start = unreal.Vector(0.0, 0.0, float(layer["z_offset"]))
    local_end = unreal.Vector(delta.x, delta.y, delta.z + float(layer["z_offset"]))
    tangent = unreal.Vector(delta.x, delta.y, delta.z)
    _set_with_optional_update(component.set_start_and_end, local_start, tangent, local_end, tangent)

    scale = unreal.Vector2D(float(layer["width"]) / 100.0, float(layer["cross_scale"]))
    _set_with_optional_update(component.set_start_scale, scale)
    _set_with_optional_update(component.set_end_scale, scale)
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
    try:
        component.update_mesh()
    except Exception:
        pass

    return actor


def _spawn_layer(layer, mesh, points):
    material = _prepare_material(layer)

    actors = []
    failures = []
    for index in range(len(points) - 1):
        try:
            actor = _spawn_spline_mesh(layer, mesh, material, points[index], points[index + 1], index)
            if actor:
                actors.append(actor)
        except Exception as exc:
            failures.append({"index": index, "error": str(exc)})
            if len(failures) > 20:
                break

    return {
        "name": layer["name"],
        "label_prefix": layer["label_prefix"],
        "actor_count": len(actors),
        "failed_count": len(failures),
        "failures": failures,
        "width": layer["width"],
        "z_offset": layer["z_offset"],
        "material": layer["material"],
        "base_color": layer["base_color"],
    }


def _prepare_material(layer):
    material = unreal.load_object(None, layer["material"])
    if not material:
        raise RuntimeError("Missing road material: " + layer["material"])

    try:
        material.set_editor_property("two_sided", True)
    except Exception:
        pass

    try:
        mel = unreal.MaterialEditingLibrary
        mel.delete_all_material_expressions(material)
        base = mel.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -360, -120
        )
        r, g, b = layer["base_color"]
        base.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
        mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

        rough = mel.create_material_expression(
            material, unreal.MaterialExpressionConstant, -360, 40
        )
        rough.set_editor_property("r", float(layer["roughness"]))
        mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

        spec = mel.create_material_expression(
            material, unreal.MaterialExpressionConstant, -360, 180
        )
        spec.set_editor_property("r", float(layer["specular"]))
        mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

        try:
            mel.layout_material_expressions(material)
        except Exception:
            pass
        mel.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
    except Exception:
        pass

    return material


def _summarize_prefixed(prefix):
    actor_count = 0
    spline_mesh_components = 0
    static_mesh_components = 0
    samples = []
    for actor in _all_actors():
        label = actor.get_actor_label()
        if not label.startswith(prefix):
            continue
        actor_count += 1
        spline_count = len(actor.get_components_by_class(unreal.SplineMeshComponent))
        static_count = len(actor.get_components_by_class(unreal.StaticMeshComponent))
        spline_mesh_components += spline_count
        static_mesh_components += static_count
        if len(samples) < 12:
            samples.append(
                {
                    "label": label,
                    "class": actor.get_class().get_name(),
                    "spline_mesh_components": spline_count,
                    "static_mesh_components": static_count,
                }
            )
    return {
        "actor_count": actor_count,
        "spline_mesh_components": spline_mesh_components,
        "static_mesh_components": static_mesh_components,
        "samples": samples,
    }


def build_road_spline_mesh_visual():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    road_actor, spline = _find_road_spline()
    raw_points, spline_length = _road_points_from_spline(spline)
    points, trace_misses = _grounded_points(raw_points)

    mesh = unreal.load_object(None, ROAD_SOURCE_MESH)
    if not mesh:
        raise RuntimeError("Missing spline road source mesh: " + ROAD_SOURCE_MESH)

    deleted_previous_spline = _delete_prefixed(PREFIX)
    layer_reports = []
    spawn_ok = False
    try:
        for layer in LAYERS:
            layer_reports.append(_spawn_layer(layer, mesh, points))
        spawn_ok = all(row["actor_count"] > 0 and row["failed_count"] == 0 for row in layer_reports)
    except Exception:
        _delete_prefixed(PREFIX)
        raise

    deleted_fallback_cube = 0
    if spawn_ok:
        deleted_fallback_cube = _delete_prefixed(FALLBACK_PREFIX)

    try:
        save_result = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        save_result = False

    dirty = [
        package.get_name()
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
        + unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    ]

    report = {
        "timestamp": started,
        "status": "complete" if spawn_ok else "partial",
        "road_actor": road_actor.get_actor_label(),
        "spline_component": spline.get_name(),
        "spline_point_count": int(spline.get_number_of_spline_points()),
        "spline_length": round(float(spline_length), 2),
        "sample_step": SAMPLE_STEP,
        "sample_count": len(points),
        "landscape_trace_misses": trace_misses,
        "deleted_previous_spline": deleted_previous_spline,
        "deleted_fallback_cube": deleted_fallback_cube,
        "layers": layer_reports,
        "summary": _summarize_prefixed(PREFIX),
        "save_result": bool(save_result),
        "dirty_after": dirty,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = report_path
    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    build_road_spline_mesh_visual()
