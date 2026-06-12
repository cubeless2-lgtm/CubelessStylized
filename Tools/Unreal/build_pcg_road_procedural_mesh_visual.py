"""Build a single procedural-mesh road surface for PCG validation.

This avoids Python StaticMesh asset rebuilds and avoids many individual
SplineMesh/segment actors. The road source remains the editor-owned spline used
by the road-mask clear validation.
"""

import json
import math
import os
import time

import unreal


PREFIX = "MCP_RoadProceduralSurfaceVisual"
SPLINE_PREFIX = "MCP_RoadSplineSurfaceVisual"
FALLBACK_PREFIX = "MCP_RoadSurfaceVisual"
REPORT_NAME = "CubelessRoadProceduralMeshVisual_Report.json"

ROAD_MASK_ACTOR_LABEL = "MCP_PCG_RoadMaskSpline_ClearForest_Test"
ROAD_MASK_SPLINE_NAME = "Road_SourceSpline"

CORE_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "M_Cubeless_PCG_RoadSurface_CoreVisual.M_Cubeless_PCG_RoadSurface_CoreVisual"
)
SHOULDER_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "M_Cubeless_PCG_RoadSurface_ShoulderVisual.M_Cubeless_PCG_RoadSurface_ShoulderVisual"
)

SAMPLE_STEP = 950.0
MIN_SEGMENT_LENGTH = 150.0

LAYERS = [
    {
        "name": "Road",
        "section": 0,
        "material": CORE_MATERIAL,
        "base_color": (0.105, 0.073, 0.042),
        "emissive": (0.018, 0.012, 0.007),
        "roughness": 0.98,
        "specular": 0.018,
        "width": 4300.0,
        "z_offset": 82.0,
        "uv_scale": 2400.0,
    },
]
CROSS_VALUES = [-0.5, -0.25, 0.0, 0.25, 0.5]


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


def _road_points_from_spline(spline):
    length = float(spline.get_spline_length())
    if length < MIN_SEGMENT_LENGTH:
        raise RuntimeError("Road spline is too short: %.2f" % length)

    sample_count = max(2, int(math.ceil(length / SAMPLE_STEP)) + 1)
    points = []
    for index in range(sample_count):
        distance = min(length, (length * index) / float(sample_count - 1))
        location = spline.get_location_at_distance_along_spline(
            distance, unreal.SplineCoordinateSpace.WORLD
        )
        points.append((float(location.x), float(location.y), float(location.z), distance))
    return points, length


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


def _ignore_actors_for_trace():
    ignored = []
    for actor in _all_actors():
        label = actor.get_actor_label()
        if (
            label.startswith(PREFIX)
            or label.startswith(SPLINE_PREFIX)
            or label.startswith(FALLBACK_PREFIX)
            or label.startswith("MCP_Cubeless_PCG_LandscapeVisualBaseline_")
            or label == ROAD_MASK_ACTOR_LABEL
        ):
            ignored.append(actor)
    return ignored


def _sample_landscape(world, x, y, fallback_z, ignored):
    start = unreal.Vector(float(x), float(y), 80000.0)
    end = unreal.Vector(float(x), float(y), -20000.0)
    try:
        hits = unreal.SystemLibrary.line_trace_multi(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            ignored,
            unreal.DrawDebugTrace.NONE,
            True,
        )
    except Exception:
        hits = []

    for hit in hits:
        values = hit.to_tuple()
        if not values or not bool(values[0]):
            continue

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
            continue

        location = values[4]
        normal = values[7] if len(values) > 7 else unreal.Vector(0.0, 0.0, 1.0)
        return float(location.z), normal, True

    return float(fallback_z), unreal.Vector(0.0, 0.0, 1.0), False


def _safe_normalize_xy(x, y):
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
    return _safe_normalize_xy(b[0] - a[0], b[1] - a[1])


def _center_origin(points):
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    return unreal.Vector((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, 0.0)


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

        emissive_color = layer.get("emissive", (0.0, 0.0, 0.0))
        if any(float(value) > 0.0 for value in emissive_color):
            emissive = mel.create_material_expression(
                material, unreal.MaterialExpressionConstant3Vector, -360, 320
            )
            er, eg, eb = emissive_color
            emissive.set_editor_property("constant", unreal.LinearColor(er, eg, eb, 1.0))
            mel.connect_material_property(
                emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
            )

        try:
            mel.layout_material_expressions(material)
        except Exception:
            pass
        mel.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
    except Exception:
        pass

    return material


def _make_tangent(x, y, z=0.0):
    tangent = unreal.ProcMeshTangent()
    tangent.set_editor_property("tangent_x", unreal.Vector(float(x), float(y), float(z)))
    return tangent


def _build_layer_section(component, layer, points, origin, world, ignored):
    width = float(layer["width"])
    z_offset = float(layer["z_offset"])
    uv_scale = max(1.0, float(layer["uv_scale"]))

    vertices = []
    triangles = []
    normals = []
    uv0 = []
    colors = []
    tangents = []
    trace_misses = 0

    for index, point in enumerate(points):
        tx, ty = _tangent(points, index)
        nx, ny = -ty, tx
        v = point[3] / uv_scale
        for cross in CROSS_VALUES:
            x = point[0] + nx * width * float(cross)
            y = point[1] + ny * width * float(cross)
            z, normal, hit = _sample_landscape(world, x, y, point[2], ignored)
            if not hit:
                trace_misses += 1
            vertex = unreal.Vector(x - origin.x, y - origin.y, z + z_offset)
            vertices.append(vertex)

            try:
                normal.normalize()
            except Exception:
                normal = unreal.Vector(0.0, 0.0, 1.0)
            normals.append(normal)

            uv0.append(unreal.Vector2D(float(cross) + 0.5, v))
            colors.append(unreal.LinearColor(1, 1, 1, 1))
            tangents.append(_make_tangent(tx, ty, 0.0))

    column_count = len(CROSS_VALUES)
    for index in range(len(points) - 1):
        row0 = index * column_count
        row1 = row0 + column_count
        for column in range(column_count - 1):
            a = row0 + column
            b = row0 + column + 1
            c = row1 + column
            d = row1 + column + 1
            triangles.extend([a, c, b, b, c, d])

    component.create_mesh_section_linear_color(
        int(layer["section"]),
        vertices,
        triangles,
        normals,
        uv0,
        [],
        [],
        [],
        colors,
        tangents,
        False,
        False,
    )
    return {
        "name": layer["name"],
        "section": layer["section"],
        "vertex_count": len(vertices),
        "triangle_count": int(len(triangles) / 3),
        "trace_misses": trace_misses,
        "width": layer["width"],
        "z_offset": layer["z_offset"],
        "material": layer["material"],
        "base_color": layer["base_color"],
    }


def _spawn_procedural_actor(origin):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.ProceduralMeshActor, origin, unreal.Rotator(0.0, 0.0, 0.0)
    )
    if not actor:
        raise RuntimeError("Failed to spawn ProceduralMeshActor.")
    actor.set_actor_label(PREFIX)

    component = actor.get_component_by_class(unreal.ProceduralMeshComponent)
    if not component:
        raise RuntimeError("ProceduralMeshActor missing ProceduralMeshComponent.")
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
        component.set_editor_property("bounds_scale", 2.0)
    except Exception:
        pass
    return actor, component


def _summarize_current():
    procedural = 0
    spline_mesh = 0
    fallback = 0
    proc_sections = 0
    for actor in _all_actors():
        label = actor.get_actor_label()
        if label.startswith(PREFIX):
            procedural += 1
            component = actor.get_component_by_class(unreal.ProceduralMeshComponent)
            if component:
                proc_sections += int(component.get_num_sections())
        elif label.startswith(SPLINE_PREFIX):
            spline_mesh += 1
        elif label.startswith(FALLBACK_PREFIX):
            fallback += 1
    return {
        "procedural_actor_count": procedural,
        "procedural_section_count": proc_sections,
        "spline_mesh_actor_count": spline_mesh,
        "fallback_actor_count": fallback,
    }


def build_road_procedural_mesh_visual():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    world = unreal.EditorLevelLibrary.get_editor_world()
    road_actor, spline = _find_road_spline()
    points, spline_length = _road_points_from_spline(spline)
    origin = _center_origin(points)

    deleted_previous_procedural = _delete_prefixed(PREFIX)
    ignored = _ignore_actors_for_trace()
    actor = None
    layer_reports = []
    spawn_ok = False
    try:
        actor, component = _spawn_procedural_actor(origin)
        ignored.append(actor)
        for index, layer in enumerate(LAYERS):
            material = _prepare_material(layer)
            component.set_material(index, material)
            layer_reports.append(
                _build_layer_section(component, layer, points, origin, world, ignored)
            )
        spawn_ok = all(row["vertex_count"] > 0 and row["trace_misses"] == 0 for row in layer_reports)
    except Exception:
        if actor:
            try:
                unreal.EditorLevelLibrary.destroy_actor(actor)
            except Exception:
                pass
        raise

    deleted_spline_mesh = 0
    deleted_fallback = 0
    if spawn_ok:
        deleted_spline_mesh = _delete_prefixed(SPLINE_PREFIX)
        deleted_fallback = _delete_prefixed(FALLBACK_PREFIX)

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
        "origin": [round(origin.x, 2), round(origin.y, 2), round(origin.z, 2)],
        "deleted_previous_procedural": deleted_previous_procedural,
        "deleted_spline_mesh": deleted_spline_mesh,
        "deleted_fallback": deleted_fallback,
        "layers": layer_reports,
        "summary": _summarize_current(),
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
    build_road_procedural_mesh_visual()
