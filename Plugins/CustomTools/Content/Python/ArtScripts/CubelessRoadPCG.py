import json
import math
import os
import random
import traceback

import unreal


LEVEL_PATH = "/Game/_MCP_Temp/PCG/LVL_Cubeless_PCG_IntentGallery_MCP"
SPEC_VERSION = 1

ROAD_CONTROL_POINTS = [
    [4740.5, 10249.0, -54.2],
    [11204.9, 12049.1, -19.4],
    [17281.7, 16363.3, 1.1],
    [23407.1, 20512.5, 1.1],
    [29277.9, 25104.5, 1.1],
    [35071.3, 29853.7, 1.1],
    [40847.3, 34671.2, 1.1],
    [46419.2, 39919.5, 1.1],
]

ASSET_PATHS = {
    "road_core_mesh": "/Engine/BasicShapes/Cube.Cube",
    "road_edge_mesh": "/Engine/BasicShapes/Cylinder.Cylinder",
    "road_core_material": "/Game/_MCP_Temp/Materials/M_MCP_RoadRibbon_DarkSoil.M_MCP_RoadRibbon_DarkSoil",
    "road_edge_material": "/Game/_MCP_Temp/Materials/M_MCP_RoadRibbon_EdgeSoil.M_MCP_RoadRibbon_EdgeSoil",
    "road_dust_material": "/Game/_MCP_Temp/Materials/M_MCP_RoadRibbon_MutedDust.M_MCP_RoadRibbon_MutedDust",
    "tuned_road_core_material": "/Game/_MCP_Temp/Materials/M_MCP_RoadRibbon_Tuned04_CoolDarkForestSoil.M_MCP_RoadRibbon_Tuned04_CoolDarkForestSoil",
    "tuned_road_edge_material": "/Game/_MCP_Temp/Materials/M_MCP_RoadRibbon_Tuned04_CompactShoulder.M_MCP_RoadRibbon_Tuned04_CompactShoulder",
    "tuned_road_soften_material": "/Game/_MCP_Temp/Materials/M_MCP_RoadRibbon_Tuned04_ShadowedGrassDuff.M_MCP_RoadRibbon_Tuned04_ShadowedGrassDuff",
    "tuned_road_dust_material": "/Game/_MCP_Temp/Materials/M_MCP_RoadRibbon_Tuned04_DryNeedleDust.M_MCP_RoadRibbon_Tuned04_DryNeedleDust",
    "runtime_road_core_material": "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Core.M_Cubeless_PCG_ForestRoad_Core",
    "runtime_road_edge_material": "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Shoulder.M_Cubeless_PCG_ForestRoad_Shoulder",
    "runtime_road_soften_material": "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Duff.M_Cubeless_PCG_ForestRoad_Duff",
    "runtime_road_strip_mesh": "/Engine/BasicShapes/Plane.Plane",
    "learned_rock_mesh": "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Stones/Rocks/SM_SmallRock_01.SM_SmallRock_01",
    "learned_rock_material": "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Stones/MI_Tiling_Rock_02.MI_Tiling_Rock_02",
    "electric_dreams_source_data": "/Game/EL/ART/BG/PCG/Road/BG_Smallroad01_PL_PCG.BG_Smallroad01_PL_PCG",
}

RUNTIME_ROAD_MATERIAL_SPECS = {
    "core": {
        "path_key": "runtime_road_core_material",
        "base_color": [0.018, 0.013, 0.007],
        "roughness": 0.98,
        "specular": 0.08,
    },
    "edge": {
        "path_key": "runtime_road_edge_material",
        "base_color": [0.014, 0.010, 0.005],
        "roughness": 0.98,
        "specular": 0.08,
    },
    "soften": {
        "path_key": "runtime_road_soften_material",
        "base_color": [0.020, 0.018, 0.007],
        "roughness": 0.98,
        "specular": 0.07,
    },
}

FOLDERS = {
    "MCP_ForestRoad_Instancer_": "MCP/PCG_ForestRoad/ForestInstancers",
    "MCP_OrganicRoadRibbon_Core_": "MCP/PCG_ForestRoad/RoadRibbon/Core",
    "MCP_OrganicRoadRibbon_Edge_": "MCP/PCG_ForestRoad/RoadRibbon/Edge",
    "MCP_OrganicRoadRibbon_Soften_": "MCP/PCG_ForestRoad/RoadRibbon/Soften",
    "MCP_OrganicRoadRibbon_Dust_": "MCP/PCG_ForestRoad/RoadRibbon/Dust",
    "MCP_SplineRoadMesh_Core_": "MCP/PCG_ForestRoad/SplineRoad/Core",
    "MCP_SplineRoadMesh_Edge_": "MCP/PCG_ForestRoad/SplineRoad/Edge",
    "MCP_SplineRoadMesh_Soften_": "MCP/PCG_ForestRoad/SplineRoad/Soften",
    "MCP_CubelessRuntimeRoad_Core_": "MCP/PCG_ForestRoad/RuntimeRoad/Core",
    "MCP_CubelessRuntimeRoad_Edge_": "MCP/PCG_ForestRoad/RuntimeRoad/Edge",
    "MCP_CubelessRuntimeRoad_Soften_": "MCP/PCG_ForestRoad/RuntimeRoad/Soften",
    "MCP_LearnedRoadData_gravel_": "MCP/PCG_ForestRoad/LearnedRoadData/Gravel",
    "MCP_LearnedRoadData_stone_": "MCP/PCG_ForestRoad/LearnedRoadData/Stone",
    "MCP_LearnedRoadData_embankment_": "MCP/PCG_ForestRoad/LearnedRoadData/Embankment",
    "MCP_CubelessRuntimeRoadData_gravel_": "MCP/PCG_ForestRoad/RuntimeRoadData/Gravel",
    "MCP_CubelessRuntimeRoadData_stone_": "MCP/PCG_ForestRoad/RuntimeRoadData/Stone",
    "MCP_CubelessRuntimeRoadData_embankment_": "MCP/PCG_ForestRoad/RuntimeRoadData/Embankment",
}

VISIBLE_ROAD_PREFIXES = (
    "MCP_OrganicRoadRibbon_Core_",
    "MCP_OrganicRoadRibbon_Edge_",
    "MCP_OrganicRoadRibbon_Soften_",
    "MCP_OrganicRoadRibbon_Dust_",
    "MCP_SplineRoadMesh_Core_",
    "MCP_SplineRoadMesh_Edge_",
    "MCP_SplineRoadMesh_Soften_",
    "MCP_CubelessRuntimeRoad_Core_",
    "MCP_CubelessRuntimeRoad_Edge_",
    "MCP_CubelessRuntimeRoad_Soften_",
)

EXPECTED_COUNTS = {
    "forest_instancers": 9,
    "road_core": 96,
    "road_edge": 96,
    "road_soften": 96,
    "road_dust": 0,
    "learned_gravel": 235,
    "learned_stone": 46,
    "learned_embankment": 7,
}

REGEN_PREFIX = "MCP_RoadWrapperRegen_"
REGEN_FOLDER = "MCP/PCG_ForestRoad/RegenValidation"
REGEN_REPORT_NAME = "CubelessForestRoadRegenSmokeTest.json"
AUTHORING_SPLINE_REGEN_REPORT_NAME = "CubelessForestRoadAuthoringSplineRegenSmokeTest.json"
PCG_GRAPH_FOLDER = "/Game/_MCP_Temp/PCG/Graphs"
PCG_GRAPH_NAME = "PCG_Cubeless_ForestRoadWrapper_Skeleton"
AUTHORING_BP_FOLDER = "/Game/_MCP_Temp/PCG/Blueprints"
AUTHORING_BP_NAME = "BP_Cubeless_ForestRoadAuthoringHandle"
AUTHORING_SPLINE_NAME = "Road_SourceSpline"
AUTHORING_ACTOR_LABEL = "MCP_RoadAuthoringHandle_Prototype"
AUTHORING_ACTOR_FOLDER = "MCP/PCG_ForestRoad/Authoring"
AUTHORING_REPORT_NAME = "CubelessForestRoadAuthoringHandle.json"
VISUAL_TUNE_REPORT_NAME = "CubelessForestRoadVisualTune.json"
SPLINE_MESH_PROTOTYPE_REPORT_NAME = "CubelessForestRoadSplineMeshPrototype.json"
RUNTIME_ROAD_REPORT_NAME = "CubelessForestRoadRuntimePromotion.json"
RUNTIME_ROAD_REGENERATE_REPORT_NAME = "CubelessForestRoadRuntimeRegenerate.json"
RUNTIME_ROAD_CONTROL_SMOKE_TEST_REPORT_NAME = "CubelessForestRoadRuntimeControlSmokeTest.json"
RUNTIME_ROAD_CONTROL_PROFILE_NAME = "CubelessForestRoadRuntimeControlProfile.json"
RUNTIME_ROAD_NATIVE_GRAPH_REPORT_NAME = "CubelessForestRoadNativeGraphSkeleton.json"
RUNTIME_ROAD_NATIVE_GRAPH_SMOKE_REPORT_NAME = "CubelessForestRoadNativeGraphLiveSmoke.json"
RUNTIME_ROAD_NATIVE_GRAPH_SHAPE_SUITE_REPORT_NAME = "CubelessForestRoadNativeGraphShapeSuite.json"
RUNTIME_ROAD_BP_FOLDER = "/Game/Cubeless/PCG/Runtime/Blueprints"
RUNTIME_ROAD_BP_NAME = "BP_Cubeless_PCG_ForestRoadRuntime"
RUNTIME_ROAD_ACTOR_LABEL = "MCP_Cubeless_PCG_ForestRoadRuntime_Validation"
RUNTIME_ROAD_ACTOR_FOLDER = "MCP/PCG_ForestRoad/RuntimeAuthoring"
RUNTIME_ROAD_ACTOR_TAG = "CubelessRuntimeRoad"
RUNTIME_ROAD_SPLINE_TAG = "CubelessRuntimeRoadSpline"
RUNTIME_ROAD_PCG_GRAPH_FOLDER = "/Game/Cubeless/PCG/Runtime/Graphs"
RUNTIME_ROAD_PCG_GRAPH_NAME = "PCG_Cubeless_ForestRoadRuntime_Bridge"
RUNTIME_ROAD_NATIVE_GRAPH_NAME = "PCG_Cubeless_ForestRoadRuntime_NativeSkeleton"
RUNTIME_ROAD_PCG_ENTRYPOINT_RELATIVE_PATH = (
    "Plugins/CustomTools/Content/Python/ArtScripts/CubelessRoadPCGRuntimeEntrypoint.py"
)

RUNTIME_ROAD_PREFIXES_BY_KIND = {
    "Core": "MCP_CubelessRuntimeRoad_Core_",
    "Edge": "MCP_CubelessRuntimeRoad_Edge_",
    "Soften": "MCP_CubelessRuntimeRoad_Soften_",
}

VISIBLE_ROAD_GENERATION_COUNTS = {
    "Core": 193,
    "Edge": 168,
    "Soften": 216,
    "Dust": 0,
}

SPLINE_MESH_ROAD_COUNTS = {
    "Core": 96,
    "Edge": 96,
    "Soften": 96,
}

ROAD_GENERATION_COUNTS = {
    "Core": 193,
    "Edge": 168,
    "Soften": 216,
    "Dust": 17,
    "gravel": 235,
    "stone": 46,
    "embankment": 7,
}

FOOTPRINT_RADIUS = {
    "smalltree": 420.0,
    "embankment": 210.0,
    "stone": 180.0,
    "bush": 110.0,
    "gravel": 70.0,
}

LEARNED_ROUTE_CLEARANCE_CM = {
    "gravel": 620.0,
    "stone": 1700.0,
    "embankment": 2250.0,
}

NATIVE_ROADSIDE_FILTER_CLEARANCE_CM = {
    "gravel": 620.0,
    "stone": 1700.0,
    "embankment": 2250.0,
}

NATIVE_ROADSIDE_CATEGORY_ORDER = ("gravel", "stone", "embankment")
NATIVE_ROADSIDE_SEED_DISTANCE_INCREMENT_CM = 120.0
NATIVE_ROADCLEARANCE_REFERENCE_DISTANCE_INCREMENT_CM = 80.0
NATIVE_ROADSIDE_SELECT_RATIOS = {
    "gravel": 0.5297,
    "stone": 0.0958,
    "embankment": 0.0163,
}
NATIVE_ROADSIDE_SELECT_SEEDS = {
    "gravel": 7101,
    "stone": 7201,
    "embankment": 7301,
}


def _actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def _label(actor):
    return actor.get_actor_label()


def _ensure_actor_tag(actor, tag):
    tags = list(actor.get_editor_property("tags"))
    tag_name = unreal.Name(tag)
    if tag_name not in tags:
        tags.append(tag_name)
        actor.modify()
        actor.set_editor_property("tags", tags)
        return True
    return False


def _ensure_component_tag(component, tag):
    tags = list(component.get_editor_property("component_tags"))
    tag_name = unreal.Name(tag)
    if tag_name not in tags:
        tags.append(tag_name)
        component.modify()
        component.set_editor_property("component_tags", tags)
        return True
    return False


def _world_path():
    world = unreal.EditorLevelLibrary.get_editor_world()
    return world.get_path_name() if world else None


def _level_object_path(level_path):
    asset_name = level_path.rsplit("/", 1)[-1]
    return "{}.{}".format(level_path, asset_name)


def ensure_pcg_validation_level_loaded():
    target_world = _level_object_path(LEVEL_PATH)
    before = _world_path()
    if before == target_world:
        return {
            "target": target_world,
            "before": before,
            "after": before,
            "loaded": False,
            "pass": True,
        }

    load_result = unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    after = _world_path()
    return {
        "target": target_world,
        "before": before,
        "after": after,
        "load_result": str(load_result),
        "loaded": before != after,
        "pass": after == target_world,
    }


def _saved_spec_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        "CubelessForestRoadWrapperSpec.json",
    )


def _category_for_label(label):
    if label.startswith("MCP_LearnedRoadData_"):
        return label[len("MCP_LearnedRoadData_") :].split("_")[0]
    if label.startswith("MCP_CubelessRuntimeRoadData_"):
        return label[len("MCP_CubelessRuntimeRoadData_") :].split("_")[0]
    return None


def _regen_category_for_label(label):
    if label.startswith(REGEN_PREFIX):
        remainder = label[len(REGEN_PREFIX) :]
        return remainder.split("_")[0]
    return None


def _saved_regen_report_path(report_name=REGEN_REPORT_NAME):
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        report_name,
    )


def _saved_authoring_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        AUTHORING_REPORT_NAME,
    )


def _saved_visual_tune_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        VISUAL_TUNE_REPORT_NAME,
    )


def _saved_spline_mesh_prototype_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        SPLINE_MESH_PROTOTYPE_REPORT_NAME,
    )


def _saved_runtime_road_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        RUNTIME_ROAD_REPORT_NAME,
    )


def _saved_runtime_road_regenerate_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        RUNTIME_ROAD_REGENERATE_REPORT_NAME,
    )


def _saved_runtime_road_control_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        RUNTIME_ROAD_CONTROL_SMOKE_TEST_REPORT_NAME,
    )


def _saved_runtime_road_control_profile_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        RUNTIME_ROAD_CONTROL_PROFILE_NAME,
    )


def _saved_runtime_road_native_graph_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        RUNTIME_ROAD_NATIVE_GRAPH_REPORT_NAME,
    )


def _saved_runtime_road_native_graph_smoke_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        RUNTIME_ROAD_NATIVE_GRAPH_SMOKE_REPORT_NAME,
    )


def _saved_runtime_road_native_graph_shape_suite_report_path():
    return os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        RUNTIME_ROAD_NATIVE_GRAPH_SHAPE_SUITE_REPORT_NAME,
    )


def _runtime_road_pcg_graph_path():
    return RUNTIME_ROAD_PCG_GRAPH_FOLDER + "/" + RUNTIME_ROAD_PCG_GRAPH_NAME


def _runtime_road_pcg_graph_object_path():
    return _runtime_road_pcg_graph_path() + "." + RUNTIME_ROAD_PCG_GRAPH_NAME


def _runtime_road_native_graph_path():
    return RUNTIME_ROAD_PCG_GRAPH_FOLDER + "/" + RUNTIME_ROAD_NATIVE_GRAPH_NAME


def _runtime_road_native_graph_object_path():
    return _runtime_road_native_graph_path() + "." + RUNTIME_ROAD_NATIVE_GRAPH_NAME


def _runtime_road_pcg_entrypoint_abs_path():
    return os.path.join(
        unreal.Paths.project_dir(),
        *RUNTIME_ROAD_PCG_ENTRYPOINT_RELATIVE_PATH.split("/"),
    )


def _load_object(path):
    obj = unreal.load_object(None, path)
    if not obj:
        raise RuntimeError("Failed to load asset: {}".format(path))
    return obj


def _make_rotator(pitch, yaw, roll):
    rot = unreal.Rotator()
    rot.pitch = float(pitch)
    rot.yaw = float(yaw)
    rot.roll = float(roll)
    return rot


def _visible_road_key_for_label(label):
    if (
        label.startswith("MCP_OrganicRoadRibbon_Core_")
        or label.startswith("MCP_SplineRoadMesh_Core_")
        or label.startswith("MCP_CubelessRuntimeRoad_Core_")
    ):
        return "road_core"
    if (
        label.startswith("MCP_OrganicRoadRibbon_Edge_")
        or label.startswith("MCP_SplineRoadMesh_Edge_")
        or label.startswith("MCP_CubelessRuntimeRoad_Edge_")
    ):
        return "road_edge"
    if (
        label.startswith("MCP_OrganicRoadRibbon_Soften_")
        or label.startswith("MCP_SplineRoadMesh_Soften_")
        or label.startswith("MCP_CubelessRuntimeRoad_Soften_")
    ):
        return "road_soften"
    if label.startswith("MCP_OrganicRoadRibbon_Dust_"):
        return "road_dust"
    return None


def _visible_road_expected_counts(mode="auto", counts=None):
    if mode == "spline_mesh":
        return {
            "road_core": SPLINE_MESH_ROAD_COUNTS["Core"],
            "road_edge": SPLINE_MESH_ROAD_COUNTS["Edge"],
            "road_soften": SPLINE_MESH_ROAD_COUNTS["Soften"],
            "road_dust": 0,
        }
    if mode == "organic":
        return {
            "road_core": VISIBLE_ROAD_GENERATION_COUNTS["Core"],
            "road_edge": VISIBLE_ROAD_GENERATION_COUNTS["Edge"],
            "road_soften": VISIBLE_ROAD_GENERATION_COUNTS["Soften"],
            "road_dust": VISIBLE_ROAD_GENERATION_COUNTS["Dust"],
        }
    counts = counts or {}
    if (
        counts.get("road_core") == SPLINE_MESH_ROAD_COUNTS["Core"]
        and counts.get("road_edge") == SPLINE_MESH_ROAD_COUNTS["Edge"]
        and counts.get("road_soften") == SPLINE_MESH_ROAD_COUNTS["Soften"]
    ):
        return _visible_road_expected_counts("spline_mesh")
    return _visible_road_expected_counts("organic")


def _route_segments(points=None):
    points = points or ROAD_CONTROL_POINTS
    segments = []
    total = 0.0
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length <= 0.001:
            continue
        yaw = math.degrees(math.atan2(dy, dx))
        segments.append(
            {
                "start": start,
                "end": end,
                "length": length,
                "accum_start": total,
                "accum_end": total + length,
                "yaw": yaw,
                "dir": [dx / length, dy / length, dz / length],
                "normal": [-dy / max(math.sqrt(dx * dx + dy * dy), 0.001), dx / max(math.sqrt(dx * dx + dy * dy), 0.001)],
            }
        )
        total += length
    return segments, total


def _sample_route(distance, lateral_offset=0.0, z_offset=0.0, points=None):
    segments, total = _route_segments(points)
    if total <= 0.001:
        raise RuntimeError("Road route has no length")
    distance = max(0.0, min(float(distance), total))
    segment = segments[-1]
    for item in segments:
        if item["accum_start"] <= distance <= item["accum_end"]:
            segment = item
            break
    alpha = (distance - segment["accum_start"]) / max(segment["length"], 0.001)
    start = segment["start"]
    end = segment["end"]
    x = start[0] + (end[0] - start[0]) * alpha + segment["normal"][0] * lateral_offset
    y = start[1] + (end[1] - start[1]) * alpha + segment["normal"][1] * lateral_offset
    z = start[2] + (end[2] - start[2]) * alpha + z_offset
    return [x, y, z], segment["yaw"]


def _nearest_route_clearance(x, y, points=None):
    segments, _total = _route_segments(points)
    best = None
    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length_sq = dx * dx + dy * dy
        if length_sq <= 0.001:
            continue
        alpha = max(0.0, min(1.0, ((x - start[0]) * dx + (y - start[1]) * dy) / length_sq))
        px = start[0] + dx * alpha
        py = start[1] + dy * alpha
        clearance = math.sqrt((x - px) * (x - px) + (y - py) * (y - py))
        if best is None or clearance < best:
            best = clearance
    return best if best is not None else 0.0


def _spawn_static_mesh_actor(label, mesh, material, location, rotation, scale, folder):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, unreal.Vector(*location), rotation)
    actor.set_actor_label(label, mark_dirty=True)
    actor.set_folder_path(folder)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    if material:
        try:
            actor.static_mesh_component.set_material(0, material)
        except Exception:
            pass
    return actor


def _make_vector2d(x, y):
    vector = unreal.Vector2D()
    vector.x = float(x)
    vector.y = float(y)
    return vector


def _spawn_spline_mesh_actor(label, mesh, material, start, end, start_tangent, end_tangent, width_scale, z_scale, folder):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SplineMeshActor,
        unreal.Vector(*start),
        _make_rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(label, mark_dirty=True)
    actor.set_folder_path(folder)

    component = actor.spline_mesh_component
    component.set_static_mesh(mesh)
    if material:
        component.set_material(0, material)
    component.set_forward_axis(unreal.SplineMeshAxis.X)

    local_end = [
        float(end[0]) - float(start[0]),
        float(end[1]) - float(start[1]),
        float(end[2]) - float(start[2]),
    ]
    component.set_start_and_end(
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Vector(*start_tangent),
        unreal.Vector(*local_end),
        unreal.Vector(*end_tangent),
        True,
    )
    component.set_start_scale(_make_vector2d(width_scale, z_scale), True)
    component.set_end_scale(_make_vector2d(width_scale, z_scale), True)
    component.update_mesh()
    return actor


def _asset_folder_and_name(object_path):
    package_path = object_path.split(".")[0]
    folder, name = package_path.rsplit("/", 1)
    return folder, name


def _build_constant_material_graph(material, color, roughness, specular):
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    base_color = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant3Vector,
        -360,
        -120,
    )
    base_color.set_editor_property("constant", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        base_color,
        "",
        unreal.MaterialProperty.MP_BASE_COLOR,
    )

    roughness_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant,
        -360,
        80,
    )
    roughness_node.set_editor_property("r", float(roughness))
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness_node,
        "",
        unreal.MaterialProperty.MP_ROUGHNESS,
    )

    specular_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant,
        -360,
        220,
    )
    specular_node.set_editor_property("r", float(specular))
    unreal.MaterialEditingLibrary.connect_material_property(
        specular_node,
        "",
        unreal.MaterialProperty.MP_SPECULAR,
    )

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, False)


def _update_constant_material_graph(material, color, roughness, specular):
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    base_color = unreal.MaterialEditingLibrary.get_material_property_input_node(
        material,
        unreal.MaterialProperty.MP_BASE_COLOR,
    )
    roughness_node = unreal.MaterialEditingLibrary.get_material_property_input_node(
        material,
        unreal.MaterialProperty.MP_ROUGHNESS,
    )
    specular_node = unreal.MaterialEditingLibrary.get_material_property_input_node(
        material,
        unreal.MaterialProperty.MP_SPECULAR,
    )
    if not base_color or not roughness_node or not specular_node:
        _build_constant_material_graph(material, color, roughness, specular)
        return "rebuilt"

    base_color.set_editor_property("constant", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    roughness_node.set_editor_property("r", float(roughness))
    specular_node.set_editor_property("r", float(specular))
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    return "updated"


def _ensure_constant_material(object_path, color, roughness=0.94, specular=0.18):
    material = unreal.load_object(None, object_path)
    created = False
    if material:
        _update_constant_material_graph(material, color, roughness, specular)
        return material, created

    folder, name = _asset_folder_and_name(object_path)
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)

    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name,
        folder,
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if not material:
        raise RuntimeError("Failed to create tuned road material: {}".format(object_path))
    created = True
    _build_constant_material_graph(material, color, roughness, specular)
    return material, created


def ensure_tuned_road_materials():
    material_specs = {
        "core": (
            ASSET_PATHS["tuned_road_core_material"],
            [0.008, 0.006, 0.004],
            0.98,
            0.12,
        ),
        "edge": (
            ASSET_PATHS["tuned_road_edge_material"],
            [0.010, 0.008, 0.005],
            0.96,
            0.12,
        ),
        "soften": (
            ASSET_PATHS["tuned_road_soften_material"],
            [0.006, 0.010, 0.004],
            0.98,
            0.10,
        ),
        "dust": (
            ASSET_PATHS["tuned_road_dust_material"],
            [0.014, 0.011, 0.006],
            0.97,
            0.11,
        ),
    }
    materials = {}
    created = []
    for key, (path, color, roughness, specular) in material_specs.items():
        material, was_created = _ensure_constant_material(path, color, roughness, specular)
        materials[key] = material
        if was_created:
            created.append(path)
    return {"materials": materials, "created": created}


def ensure_runtime_road_materials():
    materials = {}
    created = []
    for key, spec in RUNTIME_ROAD_MATERIAL_SPECS.items():
        path = ASSET_PATHS[spec["path_key"]]
        color = spec["base_color"]
        roughness = spec["roughness"]
        specular = spec["specular"]
        material, was_created = _ensure_constant_material(path, color, roughness, specular)
        materials[key] = material
        if was_created:
            created.append(path)
    return {"materials": materials, "created": created}


def save_runtime_road_assets():
    paths = [
        _runtime_road_blueprint_object_path(),
        ASSET_PATHS["runtime_road_core_material"],
        ASSET_PATHS["runtime_road_edge_material"],
        ASSET_PATHS["runtime_road_soften_material"],
    ]
    results = {}
    for path in paths:
        asset = unreal.load_object(None, path)
        if not asset:
            results[path] = "missing"
            continue
        results[path] = bool(unreal.EditorAssetLibrary.save_loaded_asset(asset, False))
    return results


def runtime_road_control_profile():
    return {
        "profile_version": 1,
        "runtime_blueprint": _runtime_road_blueprint_object_path(),
        "runtime_blueprint_class": _runtime_road_blueprint_class_path(),
        "runtime_pcg_graph": _runtime_road_pcg_graph_object_path(),
        "runtime_native_graph_skeleton": _runtime_road_native_graph_object_path(),
        "runtime_pcg_entrypoint": _runtime_road_pcg_entrypoint_abs_path(),
        "runtime_actor_label": RUNTIME_ROAD_ACTOR_LABEL,
        "spline_component": AUTHORING_SPLINE_NAME,
        "control_input": "Read Road_SourceSpline from the runtime road actor; do not regenerate from ROAD_CONTROL_POINTS unless the actor is missing.",
        "generation": {
            "road_counts": {
                "core": SPLINE_MESH_ROAD_COUNTS["Core"],
                "edge": SPLINE_MESH_ROAD_COUNTS["Edge"],
                "soften": SPLINE_MESH_ROAD_COUNTS["Soften"],
                "dust": 0,
            },
            "learned_data_counts": {
                "gravel": ROAD_GENERATION_COUNTS["gravel"],
                "stone": ROAD_GENERATION_COUNTS["stone"],
                "embankment": ROAD_GENERATION_COUNTS["embankment"],
            },
            "output_prefixes": dict(RUNTIME_ROAD_PREFIXES_BY_KIND),
            "learned_output_prefix": "MCP_CubelessRuntimeRoadData_",
        },
        "materials": {
            "core": ASSET_PATHS["runtime_road_core_material"],
            "edge": ASSET_PATHS["runtime_road_edge_material"],
            "soften": ASSET_PATHS["runtime_road_soften_material"],
        },
        "rules": {
            "pitch_roll_max_degrees": 5.0,
            "yaw_randomization": "allowed",
            "stone_scale_range": [0.5, 4.0],
            "large_rock_road_clearance_cm": {
                "stone": LEARNED_ROUTE_CLEARANCE_CM["stone"],
                "embankment": LEARNED_ROUTE_CLEARANCE_CM["embankment"],
            },
            "gravel_road_clearance_cm": LEARNED_ROUTE_CLEARANCE_CM["gravel"],
            "hard_overlap": "validated with category footprint radii and samples must be empty",
        },
    }


def write_runtime_road_control_profile(output_path=None):
    output_path = output_path or _saved_runtime_road_control_profile_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    profile = runtime_road_control_profile()
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(profile, handle, ensure_ascii=False, indent=2)
    return {"profile_path": output_path, "profile": profile}


def clear_visible_road_ribbon(save=False):
    removed = []
    for actor in _actors():
        label = _label(actor)
        if label.startswith(VISIBLE_ROAD_PREFIXES):
            removed.append(label)
            unreal.EditorLevelLibrary.destroy_actor(actor)
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return {"removed_count": len(removed)}


def clear_learned_road_data(save=False):
    removed = []
    for actor in _actors():
        label = _label(actor)
        if label.startswith("MCP_LearnedRoadData_"):
            removed.append(label)
            unreal.EditorLevelLibrary.destroy_actor(actor)
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return {"removed_count": len(removed)}


def clear_runtime_road_validation_output(save=False):
    prefixes = tuple(RUNTIME_ROAD_PREFIXES_BY_KIND.values()) + ("MCP_CubelessRuntimeRoadData_",)
    removed = []
    for actor in _actors():
        label = _label(actor)
        if label.startswith(prefixes):
            removed.append(label)
            unreal.EditorLevelLibrary.destroy_actor(actor)
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return {"removed_count": len(removed)}


def clear_superseded_road_validation_output(save=False):
    prefixes = (
        "MCP_OrganicRoadRibbon_",
        "MCP_SplineRoadMesh_",
        "MCP_LearnedRoadData_",
    )
    removed = []
    for actor in _actors():
        label = _label(actor)
        if label.startswith(prefixes):
            removed.append(label)
            unreal.EditorLevelLibrary.destroy_actor(actor)
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return {"removed_count": len(removed)}


def organize_outliner(save=True):
    changed = []
    for actor in _actors():
        label = _label(actor)
        for prefix, folder in FOLDERS.items():
            if label.startswith(prefix):
                actor.set_folder_path(folder)
                changed.append({"label": label, "folder": folder})
                break
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return {
        "changed_count": len(changed),
        "folder_counts": _count_by([item["folder"] for item in changed]),
    }


def collect_scene_state():
    counts = {
        "forest_instancers": 0,
        "road_core": 0,
        "road_edge": 0,
        "road_soften": 0,
        "road_dust": 0,
        "learned_gravel": 0,
        "learned_stone": 0,
        "learned_embankment": 0,
        "tmp_actors": 0,
    }
    pcg_actors = []
    folders = {}
    for actor in _actors():
        label = _label(actor)
        if label.startswith("MCP_ForestRoad_Instancer_"):
            counts["forest_instancers"] += 1
        elif _visible_road_key_for_label(label):
            counts[_visible_road_key_for_label(label)] += 1
        elif label.startswith("MCP_LearnedRoadData_gravel_"):
            counts["learned_gravel"] += 1
        elif label.startswith("MCP_LearnedRoadData_stone_"):
            counts["learned_stone"] += 1
        elif label.startswith("MCP_LearnedRoadData_embankment_"):
            counts["learned_embankment"] += 1
        elif label.startswith("MCP_CubelessRuntimeRoadData_gravel_"):
            counts["learned_gravel"] += 1
        elif label.startswith("MCP_CubelessRuntimeRoadData_stone_"):
            counts["learned_stone"] += 1
        elif label.startswith("MCP_CubelessRuntimeRoadData_embankment_"):
            counts["learned_embankment"] += 1
        elif label.startswith("MCP_TMP_"):
            counts["tmp_actors"] += 1

        try:
            folder = str(actor.get_folder_path())
            if folder and folder != "None":
                folders[folder] = folders.get(folder, 0) + 1
        except Exception:
            pass

        try:
            if actor.get_components_by_class(unreal.PCGComponent):
                pcg_actors.append(label)
        except Exception:
            pass

    dirty = [pkg.get_name() for pkg in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    return {
        "level": _world_path(),
        "counts": counts,
        "expected_counts": dict(EXPECTED_COUNTS),
        "counts_match_expected": all(counts.get(k) == v for k, v in EXPECTED_COUNTS.items()),
        "folder_counts": dict(sorted(folders.items())),
        "pcg_actor_labels": sorted(pcg_actors),
        "dirty_packages": dirty,
    }


def validate_scene():
    learned = []
    for actor in _actors():
        label = _label(actor)
        category = _category_for_label(label)
        if not category:
            continue
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        scale = actor.get_actor_scale3d()
        learned.append(
            {
                "label": label,
                "category": category,
                "x": float(loc.x),
                "y": float(loc.y),
                "pitch": float(rot.pitch),
                "roll": float(rot.roll),
                "scale": float(scale.x),
            }
        )

    pitch_roll_violations = [
        item
        for item in learned
        if abs(item["pitch"]) > 5.1 or abs(item["roll"]) > 5.1
    ]
    scale_violations = [
        item
        for item in learned
        if item["category"] in ("stone", "embankment") and not (0.45 <= item["scale"] <= 4.5)
    ]
    clearance_violations = []
    for item in learned:
        if item["category"] not in LEARNED_ROUTE_CLEARANCE_CM:
            continue
        min_clearance = LEARNED_ROUTE_CLEARANCE_CM[item["category"]]
        clearance = _nearest_route_clearance(item["x"], item["y"])
        if clearance < min_clearance:
            clearance_violations.append(
                {
                    "label": item["label"],
                    "category": item["category"],
                    "clearance": round(clearance, 1),
                    "required": min_clearance,
                }
            )

    overlaps = []
    for index, a in enumerate(learned):
        for b in learned[index + 1 :]:
            if a["category"] == "bush" and b["category"] == "bush":
                continue
            radius = max(
                FOOTPRINT_RADIUS.get(a["category"], 120.0),
                FOOTPRINT_RADIUS.get(b["category"], 120.0),
            ) * 0.58
            dx = a["x"] - b["x"]
            dy = a["y"] - b["y"]
            distance_sq = dx * dx + dy * dy
            if distance_sq < radius * radius:
                overlaps.append(
                    {
                        "a": a["label"],
                        "b": b["label"],
                        "categories": a["category"] + "," + b["category"],
                        "distance": round(math.sqrt(distance_sq), 1),
                    }
                )
                if len(overlaps) >= 20:
                    break
        if len(overlaps) >= 20:
            break

    return {
        "learned_actor_count": len(learned),
        "learned_counts": _count_by([item["category"] for item in learned]),
        "pitch_roll_limit_violations": len(pitch_roll_violations),
        "scale_violations": len(scale_violations),
        "large_rock_clearance_violations": clearance_violations,
        "hard_overlap_samples": overlaps,
        "pass": not pitch_roll_violations and not scale_violations and not clearance_violations and not overlaps,
    }


def clear_regen_preview(save=False):
    removed = []
    for actor in _actors():
        label = _label(actor)
        if label.startswith(REGEN_PREFIX):
            removed.append(label)
            unreal.EditorLevelLibrary.destroy_actor(actor)
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return {"removed_count": len(removed)}


def generate_regen_preview(points=None):
    core_mesh = _load_object(ASSET_PATHS["road_core_mesh"])
    edge_mesh = _load_object(ASSET_PATHS["road_edge_mesh"])
    core_mat = _load_object(ASSET_PATHS["road_core_material"])
    edge_mat = _load_object(ASSET_PATHS["road_edge_material"])
    dust_mat = _load_object(ASSET_PATHS["road_dust_material"])
    rock_mesh = _load_object(ASSET_PATHS["learned_rock_mesh"])
    rock_mat = _load_object(ASSET_PATHS["learned_rock_material"])

    segments, total_length = _route_segments(points)
    if not segments:
        raise RuntimeError("Cannot generate road wrapper preview without route segments")

    counts = {}
    counts.update(_generate_regen_road_layer(core_mesh, edge_mesh, core_mat, edge_mat, dust_mat, total_length, points))
    counts.update(_generate_regen_learned_data(rock_mesh, rock_mat, total_length, points))
    return {"generated_counts": counts, "total_generated": sum(counts.values())}


def _generate_regen_road_layer(core_mesh, edge_mesh, core_mat, edge_mat, dust_mat, total_length, points=None):
    counts = {}
    core_count = ROAD_GENERATION_COUNTS["Core"]
    core_step = total_length / core_count
    for index in range(core_count):
        loc, yaw = _sample_route((index + 0.5) * core_step, 0.0, 6.0, points)
        label = "{}Core_{:03d}".format(REGEN_PREFIX, index)
        _spawn_static_mesh_actor(
            label,
            core_mesh,
            core_mat,
            loc,
            _make_rotator(0.0, yaw, 0.0),
            [max(core_step / 100.0 * 1.08, 0.1), 6.8, 0.035],
            REGEN_FOLDER + "/Road/Core",
        )
    counts["Core"] = core_count

    edge_count = ROAD_GENERATION_COUNTS["Edge"]
    half_edge = edge_count // 2
    edge_step = total_length / half_edge
    for index in range(edge_count):
        side = -1.0 if index < half_edge else 1.0
        side_index = index % half_edge
        wave = math.sin(side_index * 0.61) * 45.0
        loc, yaw = _sample_route((side_index + 0.5) * edge_step, side * (430.0 + wave), 9.0, points)
        label = "{}Edge_{:03d}".format(REGEN_PREFIX, index)
        _spawn_static_mesh_actor(
            label,
            edge_mesh,
            edge_mat,
            loc,
            _make_rotator(0.0, yaw + 8.0 * side, 0.0),
            [2.7, 0.8, 0.02],
            REGEN_FOLDER + "/Road/Edge",
        )
    counts["Edge"] = edge_count

    soften_count = ROAD_GENERATION_COUNTS["Soften"]
    half_soften = soften_count // 2
    soften_step = total_length / half_soften
    for index in range(soften_count):
        side = -1.0 if index < half_soften else 1.0
        side_index = index % half_soften
        wave = math.sin(side_index * 0.43 + 1.7) * 80.0
        loc, yaw = _sample_route((side_index + 0.5) * soften_step, side * (660.0 + wave), 7.0, points)
        label = "{}Soften_{:03d}".format(REGEN_PREFIX, index)
        _spawn_static_mesh_actor(
            label,
            edge_mesh,
            edge_mat,
            loc,
            _make_rotator(0.0, yaw - 12.0 * side, 0.0),
            [3.2, 1.15, 0.014],
            REGEN_FOLDER + "/Road/Soften",
        )
    counts["Soften"] = soften_count

    dust_count = ROAD_GENERATION_COUNTS["Dust"]
    rng = random.Random(918273)
    for index in range(dust_count):
        distance = (index + 0.5) * total_length / dust_count
        lateral = rng.uniform(-240.0, 240.0)
        loc, yaw = _sample_route(distance, lateral, 10.0, points)
        label = "{}Dust_{:03d}".format(REGEN_PREFIX, index)
        _spawn_static_mesh_actor(
            label,
            edge_mesh,
            dust_mat,
            loc,
            _make_rotator(0.0, yaw + rng.uniform(-25.0, 25.0), 0.0),
            [rng.uniform(1.4, 2.7), rng.uniform(0.7, 1.4), 0.01],
            REGEN_FOLDER + "/Road/Dust",
        )
    counts["Dust"] = dust_count
    return counts


def _generate_visible_tuned_road_layer(core_mesh, edge_mesh, materials, total_length, points):
    rng = random.Random(20260610)
    counts = {}

    core_count = VISIBLE_ROAD_GENERATION_COUNTS["Core"]
    core_step = total_length / core_count
    for index in range(core_count):
        distance = (index + 0.5) * core_step
        lateral = math.sin(index * 0.73) * 28.0 + math.sin(index * 0.19 + 1.3) * 18.0
        loc, yaw = _sample_route(distance, lateral, 5.5, points)
        width = 3.95 + math.sin(index * 0.31) * 0.31 + math.sin(index * 0.071 + 2.0) * 0.22
        length_scale = max(core_step / 100.0 * rng.uniform(1.02, 1.16), 0.1)
        label = "MCP_OrganicRoadRibbon_Core_{:03d}".format(index)
        _spawn_static_mesh_actor(
            label,
            core_mesh,
            materials["core"],
            loc,
            _make_rotator(0.0, yaw + rng.uniform(-2.2, 2.2), 0.0),
            [length_scale, max(width, 3.35), 0.018],
            FOLDERS["MCP_OrganicRoadRibbon_Core_"],
        )
    counts["road_core"] = core_count

    edge_count = VISIBLE_ROAD_GENERATION_COUNTS["Edge"]
    half_edge = edge_count // 2
    edge_step = total_length / half_edge
    for index in range(edge_count):
        side = -1.0 if index < half_edge else 1.0
        side_index = index % half_edge
        wave = math.sin(side_index * 0.48) * 58.0 + math.sin(side_index * 0.13 + 0.8) * 36.0
        loc, yaw = _sample_route((side_index + 0.5) * edge_step, side * (265.0 + wave), 7.5, points)
        label = "MCP_OrganicRoadRibbon_Edge_{:03d}".format(index)
        _spawn_static_mesh_actor(
            label,
            edge_mesh,
            materials["edge"],
            loc,
            _make_rotator(0.0, yaw + side * rng.uniform(6.0, 18.0), 0.0),
            [rng.uniform(1.12, 2.15), rng.uniform(0.22, 0.44), 0.008],
            FOLDERS["MCP_OrganicRoadRibbon_Edge_"],
        )
    counts["road_edge"] = edge_count

    soften_count = VISIBLE_ROAD_GENERATION_COUNTS["Soften"]
    half_soften = soften_count // 2
    soften_step = total_length / half_soften
    for index in range(soften_count):
        side = -1.0 if index < half_soften else 1.0
        side_index = index % half_soften
        wave = math.sin(side_index * 0.37 + 1.7) * 96.0 + math.sin(side_index * 0.09) * 54.0
        loc, yaw = _sample_route((side_index + 0.5) * soften_step, side * (420.0 + wave), 6.5, points)
        label = "MCP_OrganicRoadRibbon_Soften_{:03d}".format(index)
        _spawn_static_mesh_actor(
            label,
            edge_mesh,
            materials["soften"],
            loc,
            _make_rotator(0.0, yaw - side * rng.uniform(9.0, 22.0), 0.0),
            [rng.uniform(1.05, 2.25), rng.uniform(0.30, 0.62), 0.006],
            FOLDERS["MCP_OrganicRoadRibbon_Soften_"],
        )
    counts["road_soften"] = soften_count

    dust_count = VISIBLE_ROAD_GENERATION_COUNTS["Dust"]
    for index in range(dust_count):
        distance = (index + 0.5) * total_length / dust_count + rng.uniform(-120.0, 120.0)
        lateral = rng.uniform(-135.0, 135.0)
        loc, yaw = _sample_route(distance, lateral, 8.0, points)
        label = "MCP_OrganicRoadRibbon_Dust_{:03d}".format(index)
        _spawn_static_mesh_actor(
            label,
            edge_mesh,
            materials["dust"],
            loc,
            _make_rotator(0.0, yaw + rng.uniform(-36.0, 36.0), 0.0),
            [rng.uniform(0.48, 1.15), rng.uniform(0.20, 0.55), 0.006],
            FOLDERS["MCP_OrganicRoadRibbon_Dust_"],
        )
    counts["road_dust"] = dust_count
    return counts


def _generate_spline_mesh_road_layer(core_mesh, materials, total_length, points, label_prefixes=None):
    label_prefixes = label_prefixes or {
        "Core": "MCP_SplineRoadMesh_Core_",
        "Edge": "MCP_SplineRoadMesh_Edge_",
        "Soften": "MCP_SplineRoadMesh_Soften_",
    }
    counts = {}

    core_count = SPLINE_MESH_ROAD_COUNTS["Core"]
    core_step = total_length / core_count
    for index in range(core_count):
        start_distance = index * core_step
        end_distance = (index + 1) * core_step
        start_lateral = math.sin(index * 0.31) * 20.0 + math.sin(index * 0.09 + 0.8) * 13.0
        end_lateral = math.sin((index + 1) * 0.31) * 20.0 + math.sin((index + 1) * 0.09 + 0.8) * 13.0
        start, _start_yaw = _sample_route(start_distance, start_lateral, 5.5, points)
        end, _end_yaw = _sample_route(end_distance, end_lateral, 5.5, points)
        tangent = [end[0] - start[0], end[1] - start[1], end[2] - start[2]]
        width = 3.85 + math.sin(index * 0.17) * 0.18 + math.sin(index * 0.047 + 1.2) * 0.14
        core_prefix = label_prefixes["Core"]
        label = "{}{:03d}".format(core_prefix, index)
        _spawn_spline_mesh_actor(
            label,
            core_mesh,
            materials["core"],
            start,
            end,
            tangent,
            tangent,
            max(width, 3.45),
            0.018,
            FOLDERS[core_prefix],
        )
    counts["road_core"] = core_count

    edge_count = SPLINE_MESH_ROAD_COUNTS["Edge"]
    half_edge = edge_count // 2
    edge_step = total_length / half_edge
    for index in range(edge_count):
        side = -1.0 if index < half_edge else 1.0
        side_index = index % half_edge
        start_distance = side_index * edge_step
        end_distance = (side_index + 1) * edge_step
        start_wave = math.sin(side_index * 0.42) * 34.0 + math.sin(side_index * 0.11 + 0.8) * 22.0
        end_wave = math.sin((side_index + 1) * 0.42) * 34.0 + math.sin((side_index + 1) * 0.11 + 0.8) * 22.0
        start, _start_yaw = _sample_route(start_distance, side * (230.0 + start_wave), 7.0, points)
        end, _end_yaw = _sample_route(end_distance, side * (230.0 + end_wave), 7.0, points)
        tangent = [end[0] - start[0], end[1] - start[1], end[2] - start[2]]
        edge_prefix = label_prefixes["Edge"]
        label = "{}{:03d}".format(edge_prefix, index)
        _spawn_spline_mesh_actor(
            label,
            core_mesh,
            materials["edge"],
            start,
            end,
            tangent,
            tangent,
            0.18 + math.sin(side_index * 0.23) * 0.035,
            0.010,
            FOLDERS[edge_prefix],
        )
    counts["road_edge"] = edge_count

    soften_count = SPLINE_MESH_ROAD_COUNTS["Soften"]
    half_soften = soften_count // 2
    soften_step = total_length / half_soften
    for index in range(soften_count):
        side = -1.0 if index < half_soften else 1.0
        side_index = index % half_soften
        start_distance = side_index * soften_step
        end_distance = (side_index + 1) * soften_step
        start_wave = math.sin(side_index * 0.29 + 1.5) * 54.0 + math.sin(side_index * 0.07) * 34.0
        end_wave = math.sin((side_index + 1) * 0.29 + 1.5) * 54.0 + math.sin((side_index + 1) * 0.07) * 34.0
        start, _start_yaw = _sample_route(start_distance, side * (330.0 + start_wave), 6.0, points)
        end, _end_yaw = _sample_route(end_distance, side * (330.0 + end_wave), 6.0, points)
        tangent = [end[0] - start[0], end[1] - start[1], end[2] - start[2]]
        soften_prefix = label_prefixes["Soften"]
        label = "{}{:03d}".format(soften_prefix, index)
        _spawn_spline_mesh_actor(
            label,
            core_mesh,
            materials["edge"],
            start,
            end,
            tangent,
            tangent,
            0.16 + math.sin(side_index * 0.19 + 0.4) * 0.035,
            0.007,
            FOLDERS[soften_prefix],
        )
    counts["road_soften"] = soften_count
    counts["road_dust"] = 0
    return counts


def _generate_learned_data(label_prefix, folder_for_category, rock_mesh, rock_mat, total_length, points=None):
    rng = random.Random(314159)
    occupied = []
    counts = {}
    for category in ("gravel", "stone", "embankment"):
        target_count = ROAD_GENERATION_COUNTS[category]
        generated = 0
        attempts = 0
        while generated < target_count and attempts < target_count * 80:
            attempts += 1
            side = -1.0 if rng.random() < 0.5 else 1.0
            distance = rng.uniform(0.02 * total_length, 0.98 * total_length)
            if category == "gravel":
                lateral = side * rng.uniform(680.0, 1450.0)
                scale_value = rng.uniform(0.18, 0.58)
                z_offset = 34.0
                min_route_clearance = LEARNED_ROUTE_CLEARANCE_CM["gravel"]
            elif category == "stone":
                lateral = side * rng.uniform(1950.0, 4100.0)
                scale_value = rng.uniform(0.5, 2.0)
                z_offset = 38.0
                min_route_clearance = LEARNED_ROUTE_CLEARANCE_CM["stone"]
            else:
                lateral = side * rng.uniform(2400.0, 4700.0)
                scale_value = rng.uniform(0.7, 2.0)
                z_offset = 42.0
                min_route_clearance = LEARNED_ROUTE_CLEARANCE_CM["embankment"]

            loc, yaw = _sample_route(distance, lateral, z_offset, points)
            if min_route_clearance > 0.0 and _nearest_route_clearance(loc[0], loc[1], points) < min_route_clearance:
                continue
            radius = FOOTPRINT_RADIUS.get(category, 120.0) * 0.58
            if _has_hard_overlap(loc, radius, occupied):
                continue

            pitch = rng.uniform(-4.5, 4.5)
            roll = rng.uniform(-4.5, 4.5)
            label = "{}{}_{:03d}".format(label_prefix, category, generated)
            _spawn_static_mesh_actor(
                label,
                rock_mesh,
                rock_mat,
                loc,
                _make_rotator(pitch, yaw + rng.uniform(-180.0, 180.0), roll),
                [scale_value, scale_value, scale_value],
                folder_for_category(category),
            )
            occupied.append({"category": category, "location": loc, "radius": radius})
            generated += 1

        if generated != target_count:
            raise RuntimeError(
                "Failed to generate {} {} actors without hard overlap".format(target_count, category)
            )
        counts[category] = generated
    return counts


def _generate_regen_learned_data(rock_mesh, rock_mat, total_length, points=None):
    return _generate_learned_data(
        REGEN_PREFIX,
        lambda category: REGEN_FOLDER + "/Learned/" + category,
        rock_mesh,
        rock_mat,
        total_length,
        points,
    )


def _generate_visible_learned_data(rock_mesh, rock_mat, total_length, points=None):
    return _generate_learned_data(
        "MCP_LearnedRoadData_",
        lambda category: FOLDERS["MCP_LearnedRoadData_{}_".format(category)],
        rock_mesh,
        rock_mat,
        total_length,
        points,
    )


def _generate_runtime_learned_data(rock_mesh, rock_mat, total_length, points=None):
    return _generate_learned_data(
        "MCP_CubelessRuntimeRoadData_",
        lambda category: FOLDERS["MCP_CubelessRuntimeRoadData_{}_".format(category)],
        rock_mesh,
        rock_mat,
        total_length,
        points,
    )


def _has_hard_overlap(location, radius, occupied):
    for item in occupied:
        other = item["location"]
        min_distance = max(radius, item["radius"])
        dx = location[0] - other[0]
        dy = location[1] - other[1]
        if dx * dx + dy * dy < min_distance * min_distance:
            return True
    return False


def validate_regen_preview(points=None):
    actors = []
    for actor in _actors():
        label = _label(actor)
        category = _regen_category_for_label(label)
        if not category:
            continue
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        scale = actor.get_actor_scale3d()
        actors.append(
            {
                "label": label,
                "category": category,
                "x": float(loc.x),
                "y": float(loc.y),
                "pitch": float(rot.pitch),
                "roll": float(rot.roll),
                "scale": float(scale.x),
            }
        )

    counts = _count_by([item["category"] for item in actors])
    expected = dict(ROAD_GENERATION_COUNTS)
    count_mismatches = {
        key: {"expected": value, "actual": counts.get(key, 0)}
        for key, value in expected.items()
        if counts.get(key, 0) != value
    }

    learned = [item for item in actors if item["category"] in ("gravel", "stone", "embankment")]
    pitch_roll_violations = [
        item for item in learned if abs(item["pitch"]) > 5.1 or abs(item["roll"]) > 5.1
    ]
    scale_violations = [
        item
        for item in learned
        if item["category"] in ("stone", "embankment") and not (0.45 <= item["scale"] <= 4.5)
    ]
    clearance_violations = []
    for item in learned:
        if item["category"] not in LEARNED_ROUTE_CLEARANCE_CM:
            continue
        min_clearance = LEARNED_ROUTE_CLEARANCE_CM[item["category"]]
        clearance = _nearest_route_clearance(item["x"], item["y"], points)
        if clearance < min_clearance:
            clearance_violations.append(
                {
                    "label": item["label"],
                    "category": item["category"],
                    "clearance": round(clearance, 1),
                    "required": min_clearance,
                }
            )
    overlaps = []
    for index, a in enumerate(learned):
        for b in learned[index + 1 :]:
            radius = max(
                FOOTPRINT_RADIUS.get(a["category"], 120.0),
                FOOTPRINT_RADIUS.get(b["category"], 120.0),
            ) * 0.58
            dx = a["x"] - b["x"]
            dy = a["y"] - b["y"]
            if dx * dx + dy * dy < radius * radius:
                overlaps.append(
                    {
                        "a": a["label"],
                        "b": b["label"],
                        "categories": a["category"] + "," + b["category"],
                        "distance": round(math.sqrt(dx * dx + dy * dy), 1),
                    }
                )
                if len(overlaps) >= 20:
                    break
        if len(overlaps) >= 20:
            break

    return {
        "actor_count": len(actors),
        "counts": counts,
        "expected_counts": expected,
        "count_mismatches": count_mismatches,
        "pitch_roll_limit_violations": len(pitch_roll_violations),
        "scale_violations": len(scale_violations),
        "large_rock_clearance_violations": clearance_violations,
        "hard_overlap_samples": overlaps,
        "pass": not count_mismatches and not pitch_roll_violations and not scale_violations and not clearance_violations and not overlaps,
    }


def run_regeneration_smoke_test(keep_preview=False, points=None, route_source="ROAD_CONTROL_POINTS", report_name=REGEN_REPORT_NAME):
    cleared_before = clear_regen_preview(save=False)
    try:
        generated = generate_regen_preview(points=points)
        validation = validate_regen_preview(points=points)
        report = {
            "level": _world_path(),
            "prefix": REGEN_PREFIX,
            "route_source": route_source,
            "route_point_count": len(points) if points else len(ROAD_CONTROL_POINTS),
            "keep_preview": bool(keep_preview),
            "cleared_before": cleared_before,
            "generated": generated,
            "validation": validation,
            "bookmark_policy": "bookmark 1/2 are user-owned and are not modified by this smoke test",
        }
        report_path = _saved_regen_report_path(report_name)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        report["report_path"] = report_path
        if not keep_preview:
            report["cleared_after"] = clear_regen_preview(save=False)
        save_ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        report["save_ok"] = bool(save_ok)
        unreal.log("CubelessRoadPCG regen smoke test: {}".format(json.dumps(report, ensure_ascii=False)))
        return report
    except Exception:
        clear_regen_preview(save=False)
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        raise


def create_or_update_pcg_graph_skeleton():
    if not unreal.EditorAssetLibrary.does_directory_exist(PCG_GRAPH_FOLDER):
        unreal.EditorAssetLibrary.make_directory(PCG_GRAPH_FOLDER)

    graph_path = PCG_GRAPH_FOLDER + "/" + PCG_GRAPH_NAME
    graph = unreal.load_object(None, graph_path + "." + PCG_GRAPH_NAME)
    created = False
    if not graph:
        factory = unreal.PCGGraphFactory()
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            PCG_GRAPH_NAME,
            PCG_GRAPH_FOLDER,
            unreal.PCGGraph,
            factory,
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load PCG graph skeleton: {}".format(graph_path))

    nodes = list(graph.nodes)
    if not nodes:
        node, settings = graph.add_node_of_type(unreal.PCGExecutePythonScriptSettings)
    else:
        node = nodes[0]
        settings = node.get_settings()
        for extra_node in nodes[1:]:
            graph.remove_node(extra_node)

    node_update = {}
    try:
        graph.description = (
            "Cubeless forest road wrapper skeleton. The validated backend is "
            "Plugins/CustomTools/Content/Python/ArtScripts/CubelessRoadPCG.py. "
            "The editable route handle is "
            "/Game/_MCP_Temp/PCG/Blueprints/BP_Cubeless_ForestRoadAuthoringHandle "
            "with SplineComponent Road_SourceSpline. "
            "Bookmark 1/2 are user-owned and must not be overwritten."
        )
        node_update["graph_description"] = "set"
    except Exception as exc:
        node_update["graph_description_error"] = str(exc)

    try:
        node.node_title = "RoadWrapper Backend Smoke Test"
        node.set_node_position(120, 0)
        node_update["node_title"] = str(node.node_title)
    except Exception as exc:
        node_update["node_title_error"] = str(exc)

    try:
        settings.description = (
            "Backend: CubelessRoadPCG.py. "
            "Safe test entries: run_regeneration_smoke_test(keep_preview=False), "
            "run_authoring_spline_regeneration_smoke_test(keep_preview=False)."
        )
        node_update["settings_description"] = str(settings.description)
    except Exception as exc:
        node_update["settings_description_error"] = str(exc)

    try:
        graph.get_input_node().set_node_position(-220, 0)
        graph.get_output_node().set_node_position(460, 0)
        node_update["io_positions"] = "set"
    except Exception as exc:
        node_update["io_position_error"] = str(exc)

    unreal.EditorAssetLibrary.save_loaded_asset(graph, False)
    return {
        "created": created,
        "graph_path": graph.get_path_name(),
        "node_count": len(graph.nodes),
        "node_names": [item.get_name() for item in graph.nodes],
        "update": node_update,
    }


def _make_file_path(file_path):
    value = unreal.FilePath()
    value.file_path = file_path
    return value


def create_or_update_runtime_road_pcg_graph_bridge():
    if not unreal.EditorAssetLibrary.does_directory_exist(RUNTIME_ROAD_PCG_GRAPH_FOLDER):
        unreal.EditorAssetLibrary.make_directory(RUNTIME_ROAD_PCG_GRAPH_FOLDER)

    graph_path = _runtime_road_pcg_graph_path()
    graph = unreal.load_object(None, graph_path + "." + RUNTIME_ROAD_PCG_GRAPH_NAME)
    created = False
    if not graph:
        factory = unreal.PCGGraphFactory()
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            RUNTIME_ROAD_PCG_GRAPH_NAME,
            RUNTIME_ROAD_PCG_GRAPH_FOLDER,
            unreal.PCGGraph,
            factory,
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load runtime road PCG graph bridge: {}".format(graph_path))

    nodes = list(graph.nodes)
    if not nodes:
        node, settings = graph.add_node_of_type(unreal.PCGExecutePythonScriptSettings)
    else:
        python_nodes = [
            item
            for item in nodes
            if item.get_settings().get_class().get_name() == "PCGExecutePythonScriptSettings"
        ]
        node = python_nodes[0] if python_nodes else nodes[0]
        settings = node.get_settings()
        if settings.get_class().get_name() != "PCGExecutePythonScriptSettings":
            graph.remove_node(node)
            node, settings = graph.add_node_of_type(unreal.PCGExecutePythonScriptSettings)
        for extra_node in nodes:
            if extra_node != node:
                graph.remove_node(extra_node)

    entrypoint_path = _runtime_road_pcg_entrypoint_abs_path()
    node_update = {}
    try:
        graph.description = (
            "Cubeless forest road runtime bridge guard. Reads the level actor "
            "{}.{} only for status, then skips legacy Python SplineMeshActor strip generation. "
            "Use {} as the native PCG replacement target."
        ).format(RUNTIME_ROAD_ACTOR_LABEL, AUTHORING_SPLINE_NAME, _runtime_road_native_graph_object_path())
        node_update["graph_description"] = "set"
    except Exception as exc:
        node_update["graph_description_error"] = str(exc)

    try:
        node.node_title = "Forest Road Runtime Guard"
        node.set_node_position(120, 0)
        node_update["node_title"] = str(node.node_title)
    except Exception as exc:
        node_update["node_title_error"] = str(exc)

    try:
        settings.description = (
            "Entry: CubelessRoadPCGRuntimeEntrypoint.py. "
            "Calls write_runtime_road_bridge_guard_report() so the bridge no longer "
            "auto-spawns separate SplineMeshActor validation strips. "
            "Call regenerate_runtime_road_from_actor() manually only for legacy validation."
        )
        settings.set_editor_property("script_input_method", unreal.PCGPythonScriptInputMethod.FILE)
        settings.set_editor_property("script_path", _make_file_path(entrypoint_path))
        node_update["settings_description"] = str(settings.description)
        node_update["script_input_method"] = str(settings.get_editor_property("script_input_method"))
        node_update["script_path"] = str(settings.get_editor_property("script_path"))
    except Exception as exc:
        node_update["settings_error"] = str(exc)

    try:
        graph.get_input_node().set_node_position(-220, 0)
        graph.get_output_node().set_node_position(460, 0)
        node_update["io_positions"] = "set"
    except Exception as exc:
        node_update["io_position_error"] = str(exc)

    unreal.EditorAssetLibrary.save_loaded_asset(graph, False)
    return {
        "created": created,
        "graph_path": graph.get_path_name(),
        "entrypoint_path": entrypoint_path,
        "entrypoint_exists": os.path.exists(entrypoint_path),
        "node_count": len(graph.nodes),
        "node_names": [item.get_name() for item in graph.nodes],
        "update": node_update,
    }


def _pcg_pin_label(pin):
    try:
        return str(pin.get_editor_property("properties").get_editor_property("label"))
    except Exception:
        return pin.get_name()


def _pcg_node_pin_summary(node):
    return {
        "node": node.get_name(),
        "title": str(node.node_title),
        "settings_class": node.get_settings().get_class().get_name(),
        "input_pins": [
            {
                "label": _pcg_pin_label(pin),
                "connected": bool(pin.is_connected()),
            }
            for pin in node.input_pins
        ],
        "output_pins": [
            {
                "label": _pcg_pin_label(pin),
                "connected": bool(pin.is_connected()),
            }
            for pin in node.output_pins
        ],
    }


def _pcg_set_description(settings, text):
    try:
        settings.description = text
        return True
    except Exception:
        try:
            settings.set_editor_property("description", text)
            return True
        except Exception:
            return False


def _pcg_add_edge_report(graph, from_node, to_node, from_pin="Out", to_pin="In"):
    try:
        from_labels = [_pcg_pin_label(pin) for pin in from_node.output_pins]
        to_labels = [_pcg_pin_label(pin) for pin in to_node.input_pins]
        if from_pin not in from_labels:
            raise RuntimeError("From node {} does not have output pin {}; available={}".format(
                from_node.get_name(),
                from_pin,
                from_labels,
            ))
        if to_pin not in to_labels:
            raise RuntimeError("To node {} does not have input pin {}; available={}".format(
                to_node.get_name(),
                to_pin,
                to_labels,
            ))
        graph.add_edge(from_node, unreal.Name(from_pin), to_node, unreal.Name(to_pin))
        return {
            "from": from_node.get_name(),
            "from_pin": from_pin,
            "to": to_node.get_name(),
            "to_pin": to_pin,
            "ok": True,
        }
    except Exception as exc:
        return {
            "from": from_node.get_name(),
            "from_pin": from_pin,
            "to": to_node.get_name(),
            "to_pin": to_pin,
            "ok": False,
            "error": str(exc),
        }


def _pcg_weighted_mesh_entry(mesh_path, material_path=None, weight=1):
    entry = unreal.PCGMeshSelectorWeightedEntry()
    text = entry.export_text()
    text = text.replace("StaticMesh=None", 'StaticMesh="{}"'.format(mesh_path))
    if material_path:
        text = text.replace("OverrideMaterials=", 'OverrideMaterials=("{}")'.format(material_path))
    entry.import_text(text)
    try:
        entry.set_editor_property("weight", int(weight))
    except Exception:
        pass
    return entry


def _pcg_object_property_override(input_attribute, property_target):
    override = unreal.PCGObjectPropertyOverrideDescription()
    override.import_text(
        '(InputSource=PCGBegin(${})PCGEnd,PropertyTarget="{}")'.format(
            input_attribute,
            property_target,
        )
    )
    return override


def _pcg_output_attribute_selector(attribute_name):
    selector = unreal.PCGAttributePropertyOutputSelector()
    selector.import_text('(AttributeName="{}")'.format(attribute_name))
    return selector


def _pcg_input_attribute_selector(attribute_name):
    selector = unreal.PCGAttributePropertyInputSelector()
    selector.import_text('(AttributeName="{}")'.format(attribute_name))
    return selector


def _pcg_property_attribute_selector(attribute_name):
    selector = unreal.PCGAttributePropertySelector()
    selector.import_text('(AttributeName="{}")'.format(attribute_name))
    return selector


def _pcg_constant_value(metadata_type, value):
    constant = unreal.PCGMetadataTypesConstantStruct()
    constant.set_editor_property("type", metadata_type)
    if metadata_type == unreal.PCGMetadataTypes.SOFT_OBJECT_PATH:
        constant.set_editor_property("soft_object_path_value", unreal.SoftObjectPath(value))
    elif metadata_type == unreal.PCGMetadataTypes.INTEGER32:
        constant.set_editor_property("int32_value", int(value))
    elif metadata_type == unreal.PCGMetadataTypes.NAME:
        constant.set_editor_property("name_value", unreal.Name(value))
    elif metadata_type == unreal.PCGMetadataTypes.VECTOR2:
        constant.set_editor_property("vector2_value", unreal.Vector2D(float(value[0]), float(value[1])))
    elif metadata_type == unreal.PCGMetadataTypes.VECTOR:
        constant.set_editor_property("vector_value", unreal.Vector(float(value[0]), float(value[1]), float(value[2])))
    elif metadata_type == unreal.PCGMetadataTypes.FLOAT:
        constant.set_editor_property("float_value", float(value))
    elif metadata_type == unreal.PCGMetadataTypes.DOUBLE:
        constant.set_editor_property("double_value", float(value))
    elif metadata_type == unreal.PCGMetadataTypes.STRING:
        constant.set_editor_property("string_value", str(value))
    else:
        raise ValueError("Unsupported PCG constant metadata type: {}".format(metadata_type))
    return constant


def _pcg_configure_add_attribute_node(settings, attribute_name, metadata_type, value):
    result = {}
    try:
        settings.set_editor_property("output_target", _pcg_output_attribute_selector(attribute_name))
        result["output_target"] = attribute_name
    except Exception as exc:
        result["output_target_error"] = str(exc)
    try:
        settings.set_editor_property("attribute_types", _pcg_constant_value(metadata_type, value))
        result["attribute_type"] = metadata_type.name
        result["attribute_value"] = str(value)
    except Exception as exc:
        result["attribute_value_error"] = str(exc)
    try:
        settings.set_editor_property("copy_all_attributes", True)
        settings.set_editor_property("copy_all_domains", True)
        result["copy_mode"] = "copy_all_attributes, copy_all_domains"
    except Exception as exc:
        result["copy_mode_error"] = str(exc)
    return result


def _pcg_configure_attribute_noise_node(settings, input_attribute, output_attribute, noise_min, noise_max, seed):
    result = {}
    try:
        settings.set_editor_property("input_source", _pcg_input_attribute_selector(input_attribute))
        settings.set_editor_property("output_target", _pcg_output_attribute_selector(output_attribute))
        result["attributes"] = "{} -> {}".format(input_attribute, output_attribute)
    except Exception as exc:
        result["attribute_selector_error"] = str(exc)
    try:
        settings.set_editor_property("mode", unreal.PCGAttributeNoiseMode.ADD)
        settings.set_editor_property("noise_min", float(noise_min))
        settings.set_editor_property("noise_max", float(noise_max))
        settings.set_editor_property("seed", int(seed))
        result["noise"] = "ADD {:.4f}..{:.4f}, seed {}".format(float(noise_min), float(noise_max), int(seed))
    except Exception as exc:
        result["noise_error"] = str(exc)
    return result


def _pcg_configure_make_vector2_node(settings, x_attribute, y_attribute, output_attribute):
    result = {}
    try:
        settings.set_editor_property("input_source1", _pcg_input_attribute_selector(x_attribute))
        settings.set_editor_property("input_source2", _pcg_input_attribute_selector(y_attribute))
        settings.set_editor_property("output_target", _pcg_output_attribute_selector(output_attribute))
        settings.set_editor_property("output_type", unreal.PCGMetadataTypes.VECTOR2)
        settings.set_editor_property("output_data_from_pin", unreal.Name("X"))
        result["make_vector2"] = "({}, {}) -> {}".format(x_attribute, y_attribute, output_attribute)
        result["output_data_from_pin"] = "X"
    except Exception as exc:
        result["make_vector2_error"] = str(exc)
    return result


def _pcg_configure_spline_mesh_node(settings, mesh_path, material_path, lateral_offset_cm=0.0, attribute_overrides=None):
    result = {}
    try:
        descriptor = settings.get_editor_property("spline_mesh_descriptor")
        descriptor.set_editor_property("static_mesh", _load_object(mesh_path))
        materials = descriptor.get_editor_property("override_materials")
        materials.clear()
        materials.append(_load_object(material_path))
        descriptor.set_editor_property("override_materials", materials)
        settings.set_editor_property("spline_mesh_descriptor", descriptor)
        result["descriptor"] = "{} + {}".format(mesh_path, material_path)
    except Exception as exc:
        result["descriptor_error"] = str(exc)

    try:
        params = settings.get_editor_property("spline_mesh_params")
        params.set_editor_property("forward_axis", unreal.PCGSplineMeshForwardAxis.X)
        params.set_editor_property("start_offset", _make_vector2d(lateral_offset_cm, 0.0))
        params.set_editor_property("end_offset", _make_vector2d(lateral_offset_cm, 0.0))
        settings.set_editor_property("spline_mesh_params", params)
        result["params"] = "ForwardAxis=X, lateral offset {:.1f} cm".format(lateral_offset_cm)
    except Exception as exc:
        result["params_error"] = str(exc)

    try:
        overrides = settings.get_editor_property("spline_mesh_override_descriptions")
        overrides.clear()
        for attribute_name, property_target in attribute_overrides or []:
            overrides.append(_pcg_object_property_override(attribute_name, property_target))
        settings.set_editor_property("spline_mesh_override_descriptions", overrides)
        result["spline_mesh_override_descriptions"] = [
            "{} -> {}".format(attribute_name, property_target)
            for attribute_name, property_target in attribute_overrides or []
        ] or "cleared"
    except Exception as exc:
        result["spline_mesh_override_descriptions_error"] = str(exc)

    for property_name in (
        "spline_mesh_params_override",
        "spline_mesh_component_override",
    ):
        try:
            overrides = settings.get_editor_property(property_name)
            overrides.clear()
            settings.set_editor_property(property_name, overrides)
            result[property_name] = "cleared"
        except Exception as exc:
            result[property_name + "_error"] = str(exc)

    try:
        settings.set_editor_property("synchronous_load", True)
        result["synchronous_load"] = "True"
    except Exception as exc:
        result["synchronous_load_error"] = str(exc)

    return result


def _pcg_configure_spline_to_segment(settings):
    result = {}
    try:
        settings.set_editor_property("extract_tangents", True)
        settings.set_editor_property("extract_angles", True)
        settings.set_editor_property("extract_clockwise_info", True)
        settings.set_editor_property("extract_connectivity_info", True)
        result["segment_extract"] = "tangents, angles, clockwise, connectivity"
    except Exception as exc:
        result["segment_extract_error"] = str(exc)
    return result


def _pcg_configure_subdivide_segment(settings, symbol, module_size_cm):
    result = {}
    try:
        module = unreal.PCGSubdivisionSubmodule()
        module.set_editor_property("symbol", unreal.Name(symbol))
        module.set_editor_property("size", float(module_size_cm))
        module.set_editor_property("scalable", True)
        modules = settings.get_editor_property("modules_info")
        modules.clear()
        modules.append(module)
        settings.set_editor_property("modules_info", modules)

        grammar = settings.get_editor_property("grammar_selection")
        grammar.set_editor_property("grammar_string", "{}*".format(symbol))
        settings.set_editor_property("grammar_selection", grammar)

        settings.set_editor_property("accept_incomplete_subdivision", True)
        settings.set_editor_property("output_module_index_attribute", True)
        settings.set_editor_property("module_index_attribute_name", "RoadStripIndex")
        settings.set_editor_property("output_size_attribute", True)
        settings.set_editor_property("size_attribute_name", "RoadStripSizeCm")
        settings.set_editor_property("output_extremity_attributes", True)
        settings.set_editor_property("is_first_attribute_name", "RoadStripIsFirst")
        settings.set_editor_property("is_final_attribute_name", "RoadStripIsFinal")
        result["subdivide_segment"] = "{}* module_size={:.2f}cm".format(symbol, module_size_cm)
        result["output_attributes"] = "RoadStripIndex, RoadStripSizeCm, RoadStripIsFirst, RoadStripIsFinal"
    except Exception as exc:
        result["subdivide_segment_error"] = str(exc)
    return result


def _pcg_configure_subdivide_spline(settings, symbol, module_size_cm, module_height_cm=2.0):
    result = _pcg_configure_subdivide_segment(settings, symbol, module_size_cm)
    try:
        settings.set_editor_property("module_height", float(module_height_cm))
        result["module_height_cm"] = float(module_height_cm)
    except Exception as exc:
        result["module_height_error"] = str(exc)
    result["subdivide_spline"] = "{}* module_size={:.2f}cm".format(symbol, module_size_cm)
    return result


def _pcg_configure_create_spline_node(settings):
    result = {}
    try:
        settings.set_editor_property("mode", unreal.PCGCreateSplineMode.CREATE_DATA_ONLY)
        settings.set_editor_property("closed_loop", False)
        settings.set_editor_property("linear", True)
        settings.set_editor_property("apply_custom_tangents", False)
        result["create_spline"] = "CreateDataOnly, open, linear"
    except Exception as exc:
        result["create_spline_error"] = str(exc)
    return result


def _tag_existing_runtime_road_actors():
    tagged = []
    for actor in _actors():
        if _label(actor) != RUNTIME_ROAD_ACTOR_LABEL:
            continue
        tag_added = _ensure_actor_tag(actor, RUNTIME_ROAD_ACTOR_TAG)
        spline_tag_added = False
        spline_tag_error = None
        try:
            spline, _splines = _authoring_spline_component(actor)
            spline_tag_added = _ensure_component_tag(spline, RUNTIME_ROAD_SPLINE_TAG)
        except Exception as exc:
            spline_tag_error = str(exc)
        tagged.append({
            "label": _label(actor),
            "path": actor.get_path_name(),
            "tag_added": tag_added,
            "spline_tag": RUNTIME_ROAD_SPLINE_TAG,
            "spline_tag_added": spline_tag_added,
            "spline_tag_error": spline_tag_error,
        })
    return tagged


def _pcg_configure_get_runtime_road_spline_node(settings, runtime_sync=None):
    result = {}
    if runtime_sync is not None:
        result["runtime_sync"] = runtime_sync
    try:
        actor_selector = settings.get_editor_property("actor_selector")
        actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
        actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
        actor_selector.set_editor_property("actor_selection_tag", RUNTIME_ROAD_ACTOR_TAG)
        actor_selector.set_editor_property("select_multiple", False)
        actor_selector.set_editor_property("ignore_self_and_children", False)
        settings.set_editor_property("actor_selector", actor_selector)

        component_selector = settings.get_editor_property("component_selector")
        component_selector.set_editor_property("component_selection", unreal.PCGComponentSelection.BY_TAG)
        component_selector.set_editor_property("component_selection_tag", RUNTIME_ROAD_SPLINE_TAG)
        settings.set_editor_property("component_selector", component_selector)
        settings.set_editor_property("always_requery_actors", True)
        settings.set_editor_property("components_must_overlap_self", False)
        settings.set_editor_property("track_actors_only_within_bounds", False)

        result["selector"] = "actor tag {} + component tag {}".format(
            RUNTIME_ROAD_ACTOR_TAG,
            RUNTIME_ROAD_SPLINE_TAG,
        )
        result["actor_selector"] = str(actor_selector)
        result["component_selector"] = str(component_selector)
    except Exception as exc:
        result["selector_error"] = str(exc)
    return result


def _pcg_configure_static_mesh_spawner(settings, mesh_path, material_path):
    result = {}
    try:
        settings.set_mesh_selector_type(unreal.PCGMeshSelectorWeighted)
        result["selector_type"] = "PCGMeshSelectorWeighted"
    except Exception as exc:
        result["selector_type_error"] = str(exc)
    try:
        selector = settings.get_editor_property("mesh_selector_parameters")
        entries = selector.get_editor_property("mesh_entries")
        entries.clear()
        entries.append(_pcg_weighted_mesh_entry(mesh_path, material_path, weight=1))
        result["mesh_entries"] = str(selector.get_editor_property("mesh_entries"))
    except Exception as exc:
        result["mesh_entries_error"] = str(exc)
    try:
        settings.set_editor_property("synchronous_load", True)
        settings.set_editor_property("apply_mesh_bounds_to_points", True)
        result["spawner_flags"] = "synchronous_load, apply_mesh_bounds_to_points"
    except Exception as exc:
        result["spawner_flags_error"] = str(exc)
    return result


def _pcg_configure_spline_sampler(settings, distance_increment_cm=250.0):
    result = {}
    try:
        params = settings.get_editor_property("sampler_params")
        params.set_editor_property("dimension", unreal.PCGSplineSamplingDimension.ON_SPLINE)
        params.set_editor_property("mode", unreal.PCGSplineSamplingMode.DISTANCE)
        params.set_editor_property("distance_increment", float(distance_increment_cm))
        params.set_editor_property("subdivisions_per_segment", 8)
        params.set_editor_property("compute_distance", True)
        params.set_editor_property("compute_segment_index", True)
        settings.set_editor_property("sampler_params", params)
        result["sampler_params"] = (
            "OnSpline Distance mode, distance_increment={:.1f}cm, subdivisions_per_segment=8".format(
                float(distance_increment_cm),
            )
        )
    except Exception as exc:
        result["sampler_params_error"] = str(exc)
    return result


def _pcg_configure_distance_node(settings, output_attribute, maximum_distance):
    result = {}
    try:
        settings.set_editor_property("output_to_attribute", True)
        settings.set_editor_property("output_attribute", _pcg_property_attribute_selector(output_attribute))
        settings.set_editor_property("maximum_distance", float(maximum_distance))
        settings.set_editor_property("set_density", False)
        settings.set_editor_property("source_shape", unreal.PCGDistanceShape.CENTER)
        settings.set_editor_property("target_shape", unreal.PCGDistanceShape.CENTER)
        result["distance"] = "{} <= {:.1f} cm center-to-center attribute".format(output_attribute, maximum_distance)
        result["distance_shape"] = "source=CENTER, target=CENTER"
    except Exception as exc:
        result["distance_error"] = str(exc)
    return result


def _pcg_configure_attribute_threshold_filter(settings, attribute_name, threshold):
    result = {}
    try:
        settings.set_editor_property("target_attribute", _pcg_input_attribute_selector(attribute_name))
        settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.GREATER_OR_EQUAL)
        settings.set_editor_property("use_constant_threshold", True)
        settings.set_editor_property("attribute_types", _pcg_constant_value(unreal.PCGMetadataTypes.DOUBLE, threshold))
        settings.set_editor_property("generate_output_data_even_if_empty", True)
        result["threshold"] = "{} >= {:.1f}".format(attribute_name, threshold)
    except Exception as exc:
        result["threshold_error"] = str(exc)
    return result


def _pcg_configure_self_pruning(settings):
    result = {}
    try:
        parameters = settings.get_editor_property("parameters")
        parameters.set_editor_property("pruning_type", unreal.PCGSelfPruningType.LARGE_TO_SMALL)
        parameters.set_editor_property("radius_similarity_factor", 0.25)
        parameters.set_editor_property("randomized_pruning", False)
        parameters.set_editor_property("use_collision_attribute", False)
        settings.set_editor_property("parameters", parameters)
        result["parameters"] = "LargeToSmall, radius_similarity_factor=0.25, randomized=False"
    except Exception as exc:
        result["parameters_error"] = str(exc)
    return result


def create_or_update_runtime_road_native_skeleton_graph(source_points_override=None, source_label_override=None):
    level_load = ensure_pcg_validation_level_loaded()
    if not level_load["pass"]:
        raise RuntimeError("Failed to load PCG validation level: {}".format(level_load))

    if not unreal.EditorAssetLibrary.does_directory_exist(RUNTIME_ROAD_PCG_GRAPH_FOLDER):
        unreal.EditorAssetLibrary.make_directory(RUNTIME_ROAD_PCG_GRAPH_FOLDER)

    graph_path = _runtime_road_native_graph_path()
    graph = unreal.load_object(None, graph_path + "." + RUNTIME_ROAD_NATIVE_GRAPH_NAME)
    created = False
    if not graph:
        factory = unreal.PCGGraphFactory()
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            RUNTIME_ROAD_NATIVE_GRAPH_NAME,
            RUNTIME_ROAD_PCG_GRAPH_FOLDER,
            unreal.PCGGraph,
            factory,
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load runtime road native skeleton graph: {}".format(graph_path))

    for node in list(graph.nodes):
        graph.remove_node(node)

    if source_points_override:
        actor_result = _find_or_spawn_runtime_road_actor()
        actor = actor_result["actor"]
        before = read_runtime_road_spline_points(create_if_missing=False, source_points=source_points_override)
        before_delta = _spline_points_delta_summary(source_points_override, before["points"])
        set_result = _set_actor_spline_points(actor, source_points_override)
        spline, splines = _authoring_spline_component(actor)
        spline_tag_added = _ensure_component_tag(spline, RUNTIME_ROAD_SPLINE_TAG)
        after = read_runtime_road_spline_points(create_if_missing=False, source_points=source_points_override)
        after_delta = _spline_points_delta_summary(source_points_override, after["points"])
        runtime_sync = {
            "source_label": source_label_override or "source_points_override",
            "source_error": None,
            "source_point_count": len(source_points_override),
            "source_repair": None,
            "actor": {
                key: value
                for key, value in actor_result.items()
                if key != "actor"
            },
            "blueprint_refreshed": False,
            "before": {
                "point_count": before["point_count"],
                "route_length_cm": before["route_length_cm"],
                "delta_from_source": before_delta,
            },
            "sync_applied": True,
            "set_result": set_result,
            "spline_component": {
                "name": spline.get_name(),
                "path": spline.get_path_name(),
                "component_count_on_actor": len(splines),
                "tag": RUNTIME_ROAD_SPLINE_TAG,
                "tag_added": spline_tag_added,
            },
            "after": {
                "point_count": after["point_count"],
                "route_length_cm": after["route_length_cm"],
                "delta_from_source": after_delta,
                "points": after["points"],
            },
            "pass": (
                after["point_count"] == len(source_points_override)
                and after_delta["max_delta_cm"] <= 1.0
            ),
        }
    else:
        runtime_sync = ensure_runtime_road_spline_synced_to_authoring(save=False)
    runtime_route_points = runtime_sync["after"]["points"]
    _segments, baseline_route_length_cm = _route_segments(runtime_route_points)
    road_branch_specs = [
        {
            "key": "core",
            "display": "Core",
            "target_count": SPLINE_MESH_ROAD_COUNTS["Core"],
            "mesh": ASSET_PATHS["runtime_road_strip_mesh"],
            "material": ASSET_PATHS["runtime_road_core_material"],
            "lateral_offset_cm": 0.0,
            "lateral_variation_cm": 36.0,
            "width_scale": 4.60,
            "z_scale": 0.004,
            "subdivision_symbol": "C",
            "y": -760,
        },
        {
            "key": "edge_left",
            "display": "Edge Left",
            "target_count": SPLINE_MESH_ROAD_COUNTS["Edge"] // 2,
            "mesh": ASSET_PATHS["runtime_road_strip_mesh"],
            "material": ASSET_PATHS["runtime_road_edge_material"],
            "lateral_offset_cm": -230.0,
            "lateral_variation_cm": 56.0,
            "width_scale": 0.35,
            "z_scale": 0.002,
            "subdivision_symbol": "L",
            "y": -460,
        },
        {
            "key": "edge_right",
            "display": "Edge Right",
            "target_count": SPLINE_MESH_ROAD_COUNTS["Edge"] // 2,
            "mesh": ASSET_PATHS["runtime_road_strip_mesh"],
            "material": ASSET_PATHS["runtime_road_edge_material"],
            "lateral_offset_cm": 230.0,
            "lateral_variation_cm": 56.0,
            "width_scale": 0.35,
            "z_scale": 0.002,
            "subdivision_symbol": "R",
            "y": -180,
        },
        {
            "key": "soften_left",
            "display": "Soften Left",
            "target_count": SPLINE_MESH_ROAD_COUNTS["Soften"] // 2,
            "mesh": ASSET_PATHS["runtime_road_strip_mesh"],
            "material": ASSET_PATHS["runtime_road_soften_material"],
            "lateral_offset_cm": -310.0,
            "lateral_variation_cm": 88.0,
            "width_scale": 0.55,
            "z_scale": 0.0015,
            "subdivision_symbol": "A",
            "y": 100,
        },
        {
            "key": "soften_right",
            "display": "Soften Right",
            "target_count": SPLINE_MESH_ROAD_COUNTS["Soften"] // 2,
            "mesh": ASSET_PATHS["runtime_road_strip_mesh"],
            "material": ASSET_PATHS["runtime_road_soften_material"],
            "lateral_offset_cm": 310.0,
            "lateral_variation_cm": 88.0,
            "width_scale": 0.55,
            "z_scale": 0.0015,
            "subdivision_symbol": "B",
            "y": 380,
        },
    ]
    roadside_category_specs = [
        {
            "key": "gravel",
            "display": "Gravel",
            "target_count": ROAD_GENERATION_COUNTS["gravel"],
            "clearance_cm": LEARNED_ROUTE_CLEARANCE_CM["gravel"],
            "filter_clearance_cm": NATIVE_ROADSIDE_FILTER_CLEARANCE_CM["gravel"],
            "distance_max_cm": max(LEARNED_ROUTE_CLEARANCE_CM["gravel"] * 2.0, 5000.0),
            "select_ratio": NATIVE_ROADSIDE_SELECT_RATIOS["gravel"],
            "select_seed": NATIVE_ROADSIDE_SELECT_SEEDS["gravel"],
            "scale_min": 0.18,
            "scale_max": 0.58,
            "offset_min": [-120.0, 840.0, 0.0],
            "offset_max": [120.0, 1800.0, 0.0],
            "y": 700,
        },
        {
            "key": "stone",
            "display": "Stone",
            "target_count": ROAD_GENERATION_COUNTS["stone"],
            "clearance_cm": LEARNED_ROUTE_CLEARANCE_CM["stone"],
            "filter_clearance_cm": NATIVE_ROADSIDE_FILTER_CLEARANCE_CM["stone"],
            "distance_max_cm": max(LEARNED_ROUTE_CLEARANCE_CM["stone"] * 2.0, 5000.0),
            "select_ratio": NATIVE_ROADSIDE_SELECT_RATIOS["stone"],
            "select_seed": NATIVE_ROADSIDE_SELECT_SEEDS["stone"],
            "scale_min": 0.5,
            "scale_max": 4.0,
            "offset_min": [-260.0, 2100.0, 0.0],
            "offset_max": [260.0, 4500.0, 0.0],
            "y": 980,
        },
        {
            "key": "embankment",
            "display": "Embankment",
            "target_count": ROAD_GENERATION_COUNTS["embankment"],
            "clearance_cm": LEARNED_ROUTE_CLEARANCE_CM["embankment"],
            "filter_clearance_cm": NATIVE_ROADSIDE_FILTER_CLEARANCE_CM["embankment"],
            "distance_max_cm": max(LEARNED_ROUTE_CLEARANCE_CM["embankment"] * 2.0, 5000.0),
            "select_ratio": NATIVE_ROADSIDE_SELECT_RATIOS["embankment"],
            "select_seed": NATIVE_ROADSIDE_SELECT_SEEDS["embankment"],
            "scale_min": 0.7,
            "scale_max": 4.0,
            "offset_min": [-380.0, 2700.0, 0.0],
            "offset_max": [380.0, 6000.0, 0.0],
            "y": 1260,
        },
    ]

    node_specs = [
        ("get_spline", unreal.PCGGetSplineSettings, 0, 0, "Get runtime Road_SourceSpline"),
    ]
    for branch in road_branch_specs:
        prefix = "road_{}".format(branch["key"])
        display = branch["display"]
        y = branch["y"]
        node_specs.extend(
            [
                (prefix + "_subdivide_spline", unreal.PCGSubdivideSplineSettings, 300, y, "{} active spline subdivision".format(display)),
                (prefix + "_create_spline", unreal.PCGCreateSplineSettings, 600, y, "{} recreate spline data".format(display)),
                (prefix + "_spline_mesh", unreal.PCGSpawnSplineMeshSettings, 900, y, "{} native spline-mesh branch".format(display)),
                (prefix + "_to_segment", unreal.PCGSplineToSegmentSettings, 300, y + 120, "{} spline to segment diagnostic".format(display)),
                (prefix + "_subdivide_segment", unreal.PCGSubdivideSegmentSettings, 600, y + 120, "{} point subdivision diagnostic".format(display)),
                (prefix + "_attr_mesh", unreal.PCGAddAttributeSettings, 900, y + 120, "Set {} RoadMesh attribute".format(display)),
                (prefix + "_attr_material", unreal.PCGAddAttributeSettings, 1200, y + 120, "Set {} RoadMaterial attribute".format(display)),
                (prefix + "_attr_forward_axis", unreal.PCGAddAttributeSettings, 1500, y + 120, "Set {} RoadForwardAxis attribute".format(display)),
                (prefix + "_attr_start_offset_x", unreal.PCGAddAttributeSettings, 1800, y + 120, "Set {} RoadStartOffsetX base".format(display)),
                (prefix + "_noise_start_offset_x", unreal.PCGAttributeNoiseSettings, 2100, y + 120, "Noise {} RoadStartOffsetX".format(display)),
                (prefix + "_attr_end_offset_x", unreal.PCGAddAttributeSettings, 2400, y + 120, "Set {} RoadEndOffsetX base".format(display)),
                (prefix + "_noise_end_offset_x", unreal.PCGAttributeNoiseSettings, 2700, y + 120, "Noise {} RoadEndOffsetX".format(display)),
                (prefix + "_attr_offset_y", unreal.PCGAddAttributeSettings, 3000, y + 120, "Set {} RoadOffsetY base".format(display)),
                (prefix + "_make_start_offset", unreal.PCGMetadataMakeVectorSettings, 3300, y + 120, "Make {} RoadStartOffset".format(display)),
                (prefix + "_make_end_offset", unreal.PCGMetadataMakeVectorSettings, 3600, y + 120, "Make {} RoadEndOffset".format(display)),
                (prefix + "_attr_start_scale_x", unreal.PCGAddAttributeSettings, 3900, y + 120, "Set {} RoadStartScaleX base".format(display)),
                (prefix + "_noise_start_scale_x", unreal.PCGAttributeNoiseSettings, 4200, y + 120, "Noise {} RoadStartScaleX".format(display)),
                (prefix + "_attr_end_scale_x", unreal.PCGAddAttributeSettings, 4500, y + 120, "Set {} RoadEndScaleX base".format(display)),
                (prefix + "_noise_end_scale_x", unreal.PCGAttributeNoiseSettings, 4800, y + 120, "Noise {} RoadEndScaleX".format(display)),
                (prefix + "_attr_scale_y", unreal.PCGAddAttributeSettings, 5100, y + 120, "Set {} RoadScaleY base".format(display)),
                (prefix + "_make_start_scale", unreal.PCGMetadataMakeVectorSettings, 5400, y + 120, "Make {} RoadStartScale".format(display)),
                (prefix + "_make_end_scale", unreal.PCGMetadataMakeVectorSettings, 5700, y + 120, "Make {} RoadEndScale".format(display)),
            ]
        )
    node_specs.extend(
        [
            ("roadside_seed_points", unreal.PCGSplineSamplerSettings, 340, 700, "Open-road seed points for roadside candidates"),
            ("road_clearance_reference_points", unreal.PCGSplineSamplerSettings, 340, 1540, "Road clearance reference points"),
        ]
    )
    for category in roadside_category_specs:
        prefix = "roadside_{}".format(category["key"])
        display = category["display"]
        y = category["y"]
        node_specs.extend(
            [
                (prefix + "_points", unreal.PCGPointSamplerSettings, 660, y, "{} roadside candidate points".format(display)),
                (prefix + "_density_filter", unreal.PCGDensityFilterSettings, 980, y, "{} clearance/density filter candidate".format(display)),
                (prefix + "_transform_limits", unreal.PCGTransformPointsSettings, 1300, y, "{} pitch/roll/scale limits".format(display)),
                (prefix + "_distance_to_road", unreal.PCGDistanceSettings, 1600, y, "{} road-clearance distance".format(display)),
                (prefix + "_road_clearance_filter", unreal.PCGAttributeFilteringSettings, 1900, y, "{} road-clearance threshold filter".format(display)),
                (prefix + "_self_pruning", unreal.PCGSelfPruningSettings, 2200, y, "{} self-pruning overlap candidate".format(display)),
                (prefix + "_static_mesh_spawn", unreal.PCGStaticMeshSpawnerSettings, 2500, y, "{} native static-mesh spawn candidate".format(display)),
            ]
        )
    nodes = {}
    setup = {}
    for key, settings_class, x, y, title in node_specs:
        node, settings = graph.add_node_of_type(settings_class)
        node.set_node_position(x, y)
        try:
            node.node_title = title
        except Exception:
            pass
        nodes[key] = node
        setup[key] = {"settings_class": settings.get_class().get_name(), "description_set": False, "property_updates": {}}

    tagged_runtime_actors = _tag_existing_runtime_road_actors()
    setup["get_spline"]["description_set"] = _pcg_set_description(
        nodes["get_spline"].get_settings(),
        "Native input: select actors tagged {} and read spline components tagged {}. Current verified backend reads label {} in CubelessRoadPCG.py.".format(
            RUNTIME_ROAD_ACTOR_TAG,
            RUNTIME_ROAD_SPLINE_TAG,
            RUNTIME_ROAD_ACTOR_LABEL,
        ),
    )
    setup["get_spline"]["property_updates"] = _pcg_configure_get_runtime_road_spline_node(
        nodes["get_spline"].get_settings(),
        runtime_sync,
    )
    setup["get_spline"]["property_updates"]["tagged_runtime_actors"] = tagged_runtime_actors
    for branch in road_branch_specs:
        prefix = "road_{}".format(branch["key"])
        active_point_target = int(branch["target_count"]) + 2
        active_module_size_cm = baseline_route_length_cm / max(float(active_point_target), 1.0)
        diagnostic_module_size_cm = baseline_route_length_cm / max(float(branch["target_count"]), 1.0)
        setup[prefix + "_subdivide_spline"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_subdivide_spline"].get_settings(),
            "{} active spline subdivision. Target {} spline-mesh components by creating {} module points, module size {:.2f} cm from {:.2f} cm route. SubdivideSpline/CreateSpline consumes both end points before SpawnSplineMesh emission.".format(
                branch["display"],
                branch["target_count"],
                active_point_target,
                active_module_size_cm,
                baseline_route_length_cm,
            ),
        )
        setup[prefix + "_subdivide_spline"]["property_updates"].update(
            _pcg_configure_subdivide_spline(
                nodes[prefix + "_subdivide_spline"].get_settings(),
                branch["subdivision_symbol"],
                active_module_size_cm,
                module_height_cm=2.0,
            )
        )
        setup[prefix + "_subdivide_spline"]["property_updates"]["expected_spline_mesh_components"] = branch["target_count"]
        setup[prefix + "_subdivide_spline"]["property_updates"]["target_module_points"] = active_point_target
        setup[prefix + "_create_spline"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_create_spline"].get_settings(),
            "Recreate spline data from {} module points so SpawnSplineMesh receives polyline data instead of point data.".format(
                branch["display"],
            ),
        )
        setup[prefix + "_create_spline"]["property_updates"].update(
            _pcg_configure_create_spline_node(nodes[prefix + "_create_spline"].get_settings())
        )
        setup[prefix + "_to_segment"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_to_segment"].get_settings(),
            "Diagnostic only: convert runtime spline to segment data for {}. SpawnSplineMesh cannot consume this point-data route directly.".format(
                branch["display"],
            ),
        )
        setup[prefix + "_to_segment"]["property_updates"].update(
            _pcg_configure_spline_to_segment(nodes[prefix + "_to_segment"].get_settings())
        )
        setup[prefix + "_subdivide_segment"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_subdivide_segment"].get_settings(),
            "Diagnostic only: {} point subdivision candidate. Baseline target: {} strips, module size {:.2f} cm from {:.2f} cm route.".format(
                branch["display"],
                branch["target_count"],
                diagnostic_module_size_cm,
                baseline_route_length_cm,
            ),
        )
        setup[prefix + "_subdivide_segment"]["property_updates"].update(
            _pcg_configure_subdivide_segment(
                nodes[prefix + "_subdivide_segment"].get_settings(),
                branch["subdivision_symbol"],
                diagnostic_module_size_cm,
            )
        )
        branch_seed_base = 9100 + (road_branch_specs.index(branch) * 100)
        offset_variation_cm = float(branch["lateral_variation_cm"])
        width_variation_scale = min(float(branch["width_scale"]) * 0.06, 0.18)
        branch_attribute_specs = [
            (prefix + "_attr_mesh", "RoadMesh", unreal.PCGMetadataTypes.SOFT_OBJECT_PATH, branch["mesh"]),
            (prefix + "_attr_material", "RoadMaterial", unreal.PCGMetadataTypes.SOFT_OBJECT_PATH, branch["material"]),
            (prefix + "_attr_forward_axis", "RoadForwardAxis", unreal.PCGMetadataTypes.INTEGER32, 0),
            (prefix + "_attr_start_offset_x", "RoadStartOffsetX", unreal.PCGMetadataTypes.FLOAT, branch["lateral_offset_cm"]),
            (prefix + "_attr_end_offset_x", "RoadEndOffsetX", unreal.PCGMetadataTypes.FLOAT, branch["lateral_offset_cm"]),
            (prefix + "_attr_offset_y", "RoadOffsetY", unreal.PCGMetadataTypes.FLOAT, 0.0),
            (prefix + "_attr_start_scale_x", "RoadStartScaleX", unreal.PCGMetadataTypes.FLOAT, branch["width_scale"]),
            (prefix + "_attr_end_scale_x", "RoadEndScaleX", unreal.PCGMetadataTypes.FLOAT, branch["width_scale"]),
            (prefix + "_attr_scale_y", "RoadScaleY", unreal.PCGMetadataTypes.FLOAT, branch["z_scale"]),
        ]
        for key, attribute_name, metadata_type, value in branch_attribute_specs:
            setup[key]["description_set"] = _pcg_set_description(
                nodes[key].get_settings(),
                "Native {} road spline-mesh override attribute candidate: {}.".format(
                    branch["display"],
                    attribute_name,
                ),
            )
            setup[key]["property_updates"].update(
                _pcg_configure_add_attribute_node(
                    nodes[key].get_settings(),
                    attribute_name,
                    metadata_type,
                    value,
                )
            )
        branch_noise_specs = [
            (prefix + "_noise_start_offset_x", "RoadStartOffsetX", "RoadStartOffsetX", -offset_variation_cm, offset_variation_cm, branch_seed_base + 1),
            (prefix + "_noise_end_offset_x", "RoadEndOffsetX", "RoadEndOffsetX", -offset_variation_cm, offset_variation_cm, branch_seed_base + 2),
            (prefix + "_noise_start_scale_x", "RoadStartScaleX", "RoadStartScaleX", -width_variation_scale, width_variation_scale, branch_seed_base + 3),
            (prefix + "_noise_end_scale_x", "RoadEndScaleX", "RoadEndScaleX", -width_variation_scale, width_variation_scale, branch_seed_base + 4),
        ]
        for key, input_attribute, output_attribute, noise_min, noise_max, seed in branch_noise_specs:
            setup[key]["description_set"] = _pcg_set_description(
                nodes[key].get_settings(),
                "Native {} organic road variation: add deterministic noise to {} only.".format(
                    branch["display"],
                    output_attribute,
                ),
            )
            setup[key]["property_updates"].update(
                _pcg_configure_attribute_noise_node(
                    nodes[key].get_settings(),
                    input_attribute,
                    output_attribute,
                    noise_min,
                    noise_max,
                    seed,
                )
            )
        branch_vector_specs = [
            (prefix + "_make_start_offset", "RoadStartOffsetX", "RoadOffsetY", "RoadStartOffset"),
            (prefix + "_make_end_offset", "RoadEndOffsetX", "RoadOffsetY", "RoadEndOffset"),
            (prefix + "_make_start_scale", "RoadStartScaleX", "RoadScaleY", "RoadStartScale"),
            (prefix + "_make_end_scale", "RoadEndScaleX", "RoadScaleY", "RoadEndScale"),
        ]
        for key, x_attribute, y_attribute, output_attribute in branch_vector_specs:
            setup[key]["description_set"] = _pcg_set_description(
                nodes[key].get_settings(),
                "Native {} road override vector: combine {} and {} into {}.".format(
                    branch["display"],
                    x_attribute,
                    y_attribute,
                    output_attribute,
                ),
            )
            setup[key]["property_updates"].update(
                _pcg_configure_make_vector2_node(
                    nodes[key].get_settings(),
                    x_attribute,
                    y_attribute,
                    output_attribute,
                )
            )

        branch_spline_key = prefix + "_spline_mesh"
        setup[branch_spline_key]["description_set"] = _pcg_set_description(
            nodes[branch_spline_key].get_settings(),
            "{} native road branch. Target count: {} spline-mesh strips. Organic offset noise +/-{:.1f} cm and width noise +/-{:.3f}; z scale remains {:.4f}.".format(
                branch["display"],
                branch["target_count"],
                offset_variation_cm,
                width_variation_scale,
                branch["z_scale"],
            ),
        )
        setup[branch_spline_key]["property_updates"].update(
            _pcg_configure_spline_mesh_node(
                nodes[branch_spline_key].get_settings(),
                branch["mesh"],
                branch["material"],
                branch["lateral_offset_cm"],
                attribute_overrides=[
                    ("RoadStartOffset", "SplineMeshParams.StartOffset"),
                    ("RoadEndOffset", "SplineMeshParams.EndOffset"),
                    ("RoadStartScale", "SplineMeshParams.StartScale"),
                    ("RoadEndScale", "SplineMeshParams.EndScale"),
                ],
            )
        )
    setup["roadside_seed_points"]["description_set"] = _pcg_set_description(
        nodes["roadside_seed_points"].get_settings(),
        "Sample the open runtime road spline into seed points for roadside candidate branches. Avoid CreateSurfaceFromSpline because the road spline is open.",
    )
    setup["roadside_seed_points"]["property_updates"].update(
        _pcg_configure_spline_sampler(
            nodes["roadside_seed_points"].get_settings(),
            distance_increment_cm=NATIVE_ROADSIDE_SEED_DISTANCE_INCREMENT_CM,
        )
    )
    setup["road_clearance_reference_points"]["description_set"] = _pcg_set_description(
        nodes["road_clearance_reference_points"].get_settings(),
        "Sample the runtime road spline into reference points for native road-clearance distance checks.",
    )
    setup["road_clearance_reference_points"]["property_updates"].update(
        _pcg_configure_spline_sampler(
            nodes["road_clearance_reference_points"].get_settings(),
            distance_increment_cm=NATIVE_ROADCLEARANCE_REFERENCE_DISTANCE_INCREMENT_CM,
        )
    )
    for category in roadside_category_specs:
        prefix = "roadside_{}".format(category["key"])
        setup[prefix + "_points"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_points"].get_settings(),
            "Sample deterministic {} roadside candidates. Target count: {}, select ratio {:.4f}, seed {}.".format(
                category["display"].lower(),
                category["target_count"],
                category["select_ratio"],
                category["select_seed"],
            ),
        )
        setup[prefix + "_density_filter"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_density_filter"].get_settings(),
            "{} pass-through density filter. Clearance is currently guaranteed by lateral offset ranges and verified by Python nearest-route smoke checks.".format(
                category["display"],
            ),
        )
        setup[prefix + "_transform_limits"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_transform_limits"].get_settings(),
            "{} transform limits: yaw varied, pitch/roll +/-5 degrees, scale {:.2f}..{:.2f}.".format(
                category["display"],
                category["scale_min"],
                category["scale_max"],
            ),
        )
        setup[prefix + "_self_pruning"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_self_pruning"].get_settings(),
            "{} self-pruning candidate for same-category hard-overlap suppression. Python footprint radius after factor: {:.2f} cm.".format(
                category["display"],
                FOOTPRINT_RADIUS[category["key"]] * 0.58,
            ),
        )
        setup[prefix + "_self_pruning"]["property_updates"].update(
            _pcg_configure_self_pruning(nodes[prefix + "_self_pruning"].get_settings())
        )
        setup[prefix + "_static_mesh_spawn"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_static_mesh_spawn"].get_settings(),
            "{} native mesh selector/spawn candidate. Preserve validated Python route-clearance and hard-overlap behavior.".format(
                category["display"],
            ),
        )
        setup[prefix + "_static_mesh_spawn"]["property_updates"].update(
            _pcg_configure_static_mesh_spawner(
                nodes[prefix + "_static_mesh_spawn"].get_settings(),
                ASSET_PATHS["learned_rock_mesh"],
                ASSET_PATHS["learned_rock_material"],
            )
        )

        try:
            settings = nodes[prefix + "_points"].get_settings()
            settings.set_editor_property("ratio", float(category["select_ratio"]))
            setup[prefix + "_points"]["property_updates"]["ratio"] = "{:.4f}".format(float(category["select_ratio"]))
        except Exception as exc:
            setup[prefix + "_points"]["property_updates"]["ratio_error"] = str(exc)
        try:
            settings = nodes[prefix + "_points"].get_settings()
            settings.set_editor_property("seed", int(category["select_seed"]))
            setup[prefix + "_points"]["property_updates"]["seed"] = int(category["select_seed"])
        except Exception as exc:
            setup[prefix + "_points"]["property_updates"]["seed_error"] = str(exc)
        try:
            settings = nodes[prefix + "_points"].get_settings()
            settings.set_editor_property("keep_zero_density_points", False)
            setup[prefix + "_points"]["property_updates"]["keep_zero_density_points"] = False
        except Exception as exc:
            setup[prefix + "_points"]["property_updates"]["keep_zero_density_points_error"] = str(exc)

        try:
            settings = nodes[prefix + "_density_filter"].get_settings()
            settings.set_editor_property("lower_bound", 0.0)
            settings.set_editor_property("upper_bound", 1.0)
            setup[prefix + "_density_filter"]["property_updates"]["bounds"] = "0.0000..1.0000"
            setup[prefix + "_density_filter"]["property_updates"]["target_clearance_cm"] = str(category["clearance_cm"])
            setup[prefix + "_density_filter"]["property_updates"]["distance_max_cm"] = str(category["distance_max_cm"])
            setup[prefix + "_density_filter"]["property_updates"]["clearance_mode"] = "pass-through; TransformPoints lateral offsets enforce clearance before Python smoke validation"
        except Exception as exc:
            setup[prefix + "_density_filter"]["property_updates"]["bounds_error"] = str(exc)

        try:
            settings = nodes[prefix + "_transform_limits"].get_settings()
            settings.set_editor_property("rotation_min", _make_rotator(-5.0, 0.0, -5.0))
            settings.set_editor_property("rotation_max", _make_rotator(5.0, 360.0, 5.0))
            settings.set_editor_property("offset_min", unreal.Vector(*category["offset_min"]))
            settings.set_editor_property("offset_max", unreal.Vector(*category["offset_max"]))
            settings.set_editor_property("scale_min", unreal.Vector(category["scale_min"], category["scale_min"], category["scale_min"]))
            settings.set_editor_property("scale_max", unreal.Vector(category["scale_max"], category["scale_max"], category["scale_max"]))
            settings.set_editor_property("absolute_offset", False)
            settings.set_editor_property("absolute_rotation", False)
            settings.set_editor_property("uniform_scale", True)
            setup[prefix + "_transform_limits"]["property_updates"]["rotation_scale"] = (
                "pitch/roll +/-5, yaw 0..360, offset {}..{}, scale {:.2f}..{:.2f}".format(
                    category["offset_min"],
                    category["offset_max"],
                    category["scale_min"],
                    category["scale_max"],
                )
            )
        except Exception as exc:
            setup[prefix + "_transform_limits"]["property_updates"]["rotation_scale_error"] = str(exc)

        setup[prefix + "_distance_to_road"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_distance_to_road"].get_settings(),
            "{} distance-to-road diagnostic. Writes RoadClearanceDistance for inspection; active clearance is enforced by lateral offsets and smoke validation.".format(
                category["display"],
            ),
        )
        setup[prefix + "_distance_to_road"]["property_updates"].update(
            _pcg_configure_distance_node(
                nodes[prefix + "_distance_to_road"].get_settings(),
                "RoadClearanceDistance",
                category["distance_max_cm"],
            )
        )
        setup[prefix + "_road_clearance_filter"]["description_set"] = _pcg_set_description(
            nodes[prefix + "_road_clearance_filter"].get_settings(),
            "{} active road-clearance threshold filter. Keeps points whose native RoadClearanceDistance is at least {:.1f} cm before density/self-pruning; Python validation still checks {:.1f} cm nearest-route clearance.".format(
                category["display"],
                category["filter_clearance_cm"],
                category["clearance_cm"],
            ),
        )
        setup[prefix + "_road_clearance_filter"]["property_updates"].update(
            _pcg_configure_attribute_threshold_filter(
                nodes[prefix + "_road_clearance_filter"].get_settings(),
                "RoadClearanceDistance",
                category["filter_clearance_cm"],
            )
        )

    edges = []
    for branch in road_branch_specs:
        prefix = "road_{}".format(branch["key"])
        edges.extend(
            [
                _pcg_add_edge_report(graph, nodes["get_spline"], nodes[prefix + "_subdivide_spline"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_subdivide_spline"], nodes[prefix + "_attr_start_offset_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_start_offset_x"], nodes[prefix + "_noise_start_offset_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_noise_start_offset_x"], nodes[prefix + "_attr_end_offset_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_end_offset_x"], nodes[prefix + "_noise_end_offset_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_noise_end_offset_x"], nodes[prefix + "_attr_offset_y"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_offset_y"], nodes[prefix + "_make_start_offset"], "Out", "X"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_offset_y"], nodes[prefix + "_make_start_offset"], "Out", "Y"),
                _pcg_add_edge_report(graph, nodes[prefix + "_make_start_offset"], nodes[prefix + "_make_end_offset"], "Out", "X"),
                _pcg_add_edge_report(graph, nodes[prefix + "_make_start_offset"], nodes[prefix + "_make_end_offset"], "Out", "Y"),
                _pcg_add_edge_report(graph, nodes[prefix + "_make_end_offset"], nodes[prefix + "_attr_start_scale_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_start_scale_x"], nodes[prefix + "_noise_start_scale_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_noise_start_scale_x"], nodes[prefix + "_attr_end_scale_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_end_scale_x"], nodes[prefix + "_noise_end_scale_x"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_noise_end_scale_x"], nodes[prefix + "_attr_scale_y"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_scale_y"], nodes[prefix + "_make_start_scale"], "Out", "X"),
                _pcg_add_edge_report(graph, nodes[prefix + "_attr_scale_y"], nodes[prefix + "_make_start_scale"], "Out", "Y"),
                _pcg_add_edge_report(graph, nodes[prefix + "_make_start_scale"], nodes[prefix + "_make_end_scale"], "Out", "X"),
                _pcg_add_edge_report(graph, nodes[prefix + "_make_start_scale"], nodes[prefix + "_make_end_scale"], "Out", "Y"),
                _pcg_add_edge_report(graph, nodes[prefix + "_make_end_scale"], nodes[prefix + "_create_spline"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_create_spline"], nodes[prefix + "_spline_mesh"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_spline_mesh"], graph.get_output_node(), "Out", "Out"),
            ]
        )
    edges.extend(
        [
            _pcg_add_edge_report(graph, nodes["get_spline"], nodes["roadside_seed_points"], "Out", "Spline"),
            _pcg_add_edge_report(graph, nodes["get_spline"], nodes["road_clearance_reference_points"], "Out", "Spline"),
        ]
    )
    for category in roadside_category_specs:
        prefix = "roadside_{}".format(category["key"])
        edges.extend(
            [
                _pcg_add_edge_report(graph, nodes["roadside_seed_points"], nodes[prefix + "_points"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_points"], nodes[prefix + "_transform_limits"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_transform_limits"], nodes[prefix + "_distance_to_road"], "Out", "Source"),
                _pcg_add_edge_report(graph, nodes["road_clearance_reference_points"], nodes[prefix + "_distance_to_road"], "Out", "Target"),
                _pcg_add_edge_report(graph, nodes[prefix + "_distance_to_road"], nodes[prefix + "_road_clearance_filter"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_road_clearance_filter"], nodes[prefix + "_density_filter"], "InsideFilter", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_density_filter"], nodes[prefix + "_self_pruning"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_self_pruning"], nodes[prefix + "_static_mesh_spawn"], "Out", "In"),
                _pcg_add_edge_report(graph, nodes[prefix + "_static_mesh_spawn"], graph.get_output_node(), "Out", "Out"),
            ]
        )

    try:
        graph.description = (
            "Cubeless forest road native skeleton. This graph captures the planned native PCG replacement for "
            "CubelessRoadPCG.py: runtime spline input, segment subdivision, spline mesh road branches, roadside point branch, density/clearance "
            "filtering, pitch/roll-limited transforms, and static mesh spawning. It is not yet the final production graph."
        )
        graph.get_input_node().set_node_position(-260, 0)
        graph.get_output_node().set_node_position(3300, -160)
        graph_update = "description/io positions set"
    except Exception as exc:
        graph_update = "graph update error: {}".format(exc)

    unreal.EditorAssetLibrary.save_loaded_asset(graph, False)

    report = {
        "created": created,
        "graph_path": graph.get_path_name(),
        "level_load": level_load,
        "graph_update": graph_update,
        "node_count": len(graph.nodes),
        "edge_count": len([item for item in edges if item["ok"]]),
        "edge_errors": [item for item in edges if not item["ok"]],
        "edges": edges,
        "runtime_spline_sync": runtime_sync,
        "setup": setup,
        "node_pin_summary": [_pcg_node_pin_summary(node) for node in list(graph.nodes) + [graph.get_output_node()]],
        "native_conversion_status": {
            "spline_input": "node created, connected, and bound to actor tag {} + component tag {}".format(
                RUNTIME_ROAD_ACTOR_TAG,
                RUNTIME_ROAD_SPLINE_TAG,
            ),
            "road_segment_subdivision": "active path uses GetSpline -> SubdivideSpline -> CreateSpline -> SpawnSplineMesh; SubdivideSegment nodes remain only as point-data diagnostics",
            "road_spline_mesh_output": "core, edge-left, edge-right, soften-left, and soften-right branches recreate spline data before SpawnSplineMesh so target component counts are preserved",
            "road_attribute_sources": "Start/end offset and scale attributes are built from base float attributes, deterministic native noise, and MakeVector2 nodes, then bound through SpawnSplineMesh override descriptions; mesh/material/forward-axis attributes remain diagnostic candidates.",
            "expected_spline_mesh_component_total": (
                SPLINE_MESH_ROAD_COUNTS["Core"]
                + SPLINE_MESH_ROAD_COUNTS["Edge"]
                + SPLINE_MESH_ROAD_COUNTS["Soften"]
            ),
            "road_branch_targets": {
                branch["key"]: {
                    "target_count": branch["target_count"],
                    "subdivide_spline_point_target": branch["target_count"] + 2,
                    "mesh": branch["mesh"],
                    "material": branch["material"],
                    "module_size_cm": round(baseline_route_length_cm / max(float(branch["target_count"] + 2), 1.0), 2),
                    "diagnostic_segment_module_size_cm": round(baseline_route_length_cm / max(float(branch["target_count"]), 1.0), 2),
                    "lateral_offset_cm": branch["lateral_offset_cm"],
                    "lateral_variation_cm": branch["lateral_variation_cm"],
                    "width_scale": branch["width_scale"],
                    "width_variation_scale": round(min(float(branch["width_scale"]) * 0.06, 0.18), 4),
                    "z_scale": branch["z_scale"],
                }
                for branch in road_branch_specs
            },
            "road_clearance_reference_points": "PCGSplineSamplerSettings samples the runtime road spline for native distance checks",
            "roadside_point_pipeline": "gravel, stone, and embankment open-spline seed/sample/transform/distance/density-filter/self-pruning/spawner branches created and connected",
            "roadside_self_pruning": "PCGSelfPruningSettings nodes added per category as native hard-overlap suppression candidates",
            "roadside_road_clearance": "PCGDistanceSettings writes RoadClearanceDistance, then PCGAttributeFilteringSettings actively keeps only points beyond the category clearance threshold before density/self-pruning.",
            "roadside_category_targets": {
                category["key"]: {
                    "target_count": category["target_count"],
                    "select_ratio": category["select_ratio"],
                    "select_seed": category["select_seed"],
                    "clearance_cm": category["clearance_cm"],
                    "filter_clearance_cm": category["filter_clearance_cm"],
                    "distance_max_cm": category["distance_max_cm"],
                    "density_filter_mode": "pass-through",
                    "footprint_radius_cm": FOOTPRINT_RADIUS[category["key"]] * 0.58,
                    "scale_min": category["scale_min"],
                    "scale_max": category["scale_max"],
                    "mesh": ASSET_PATHS["learned_rock_mesh"],
                    "material": ASSET_PATHS["learned_rock_material"],
                }
                for category in roadside_category_specs
            },
            "missing_before_production": [
                "validate native self-pruning, road-clearance filtering, and density expectations across additional road shapes before production placement",
            ],
        },
    }
    report_path = _saved_runtime_road_native_graph_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    unreal.log("CubelessRoadPCG native skeleton graph: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def _native_smoke_write_report(report_path, payload):
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)


def _native_smoke_tagged_data_data(item):
    try:
        item_tuple = item.to_tuple()
        if item_tuple:
            return item_tuple[0]
    except Exception:
        pass
    try:
        data = item.get_editor_property("data")
        try:
            nested_data = data.get_editor_property("data")
            return nested_data or data
        except Exception:
            return data
    except Exception:
        return None


def _native_smoke_class_name(obj):
    try:
        return obj.get_class().get_name()
    except Exception:
        return type(obj).__name__


def _native_smoke_component_generated(component):
    try:
        return bool(component.generated) and not bool(component.dirty_generated)
    except Exception:
        try:
            return bool(component.get_editor_property("generated")) and not bool(
                component.get_editor_property("dirty_generated")
            )
        except Exception:
            return False


def _native_smoke_instance_count(component):
    for method_name in ("get_instance_count", "get_num_instances"):
        try:
            return int(getattr(component, method_name)())
        except Exception:
            pass
    return None


def _runtime_material_value_node(material, material_property):
    try:
        return unreal.MaterialEditingLibrary.get_material_property_input_node(
            material,
            material_property,
        )
    except Exception:
        return None


def collect_runtime_road_material_values():
    values = {}
    for key, spec in RUNTIME_ROAD_MATERIAL_SPECS.items():
        path = ASSET_PATHS[spec["path_key"]]
        material = unreal.load_object(None, path)
        item = {"path": path, "exists": bool(material)}
        if material:
            base_color = _runtime_material_value_node(material, unreal.MaterialProperty.MP_BASE_COLOR)
            roughness = _runtime_material_value_node(material, unreal.MaterialProperty.MP_ROUGHNESS)
            specular = _runtime_material_value_node(material, unreal.MaterialProperty.MP_SPECULAR)
            if base_color:
                try:
                    color = base_color.get_editor_property("constant")
                    item["base_color"] = [
                        round(float(color.r), 4),
                        round(float(color.g), 4),
                        round(float(color.b), 4),
                    ]
                except Exception as exc:
                    item["base_color_error"] = str(exc)
            if roughness:
                try:
                    item["roughness"] = round(float(roughness.get_editor_property("r")), 4)
                except Exception as exc:
                    item["roughness_error"] = str(exc)
            if specular:
                try:
                    item["specular"] = round(float(specular.get_editor_property("r")), 4)
                except Exception as exc:
                    item["specular_error"] = str(exc)
        values[key] = item
    return values


def runtime_road_material_value_mismatches(values=None):
    values = values or collect_runtime_road_material_values()
    mismatches = {}
    for key, spec in RUNTIME_ROAD_MATERIAL_SPECS.items():
        item = values.get(key, {})
        expected = {
            "base_color": [round(float(value), 4) for value in spec["base_color"]],
            "roughness": round(float(spec["roughness"]), 4),
            "specular": round(float(spec["specular"]), 4),
        }
        actual = {
            "base_color": item.get("base_color"),
            "roughness": item.get("roughness"),
            "specular": item.get("specular"),
        }
        if not item.get("exists") or actual != expected:
            mismatches[key] = {
                "expected": expected,
                "actual": actual,
                "exists": bool(item.get("exists")),
            }
    return mismatches


def _native_smoke_summarize_actor(actor, component, elapsed_seconds, route_points=None):
    expected_spline_mesh_components = (
        SPLINE_MESH_ROAD_COUNTS["Core"]
        + SPLINE_MESH_ROAD_COUNTS["Edge"]
        + SPLINE_MESH_ROAD_COUNTS["Soften"]
    )
    route_points = route_points or ROAD_CONTROL_POINTS
    tagged_data = []
    point_total = 0
    point_array_counts = []
    point_array_data = []
    try:
        collection = component.get_generated_graph_output()
        for item in collection.get_editor_property("tagged_data"):
            data = _native_smoke_tagged_data_data(item)
            data_class = _native_smoke_class_name(data) if data else None
            num_points = None
            if data and hasattr(data, "get_num_points"):
                try:
                    num_points = int(data.get_num_points())
                    point_total += num_points
                    if data_class and "Point" in data_class:
                        point_array_counts.append(num_points)
                        point_array_data.append(data)
                except Exception:
                    pass
            tags = []
            try:
                tags = [str(tag) for tag in item.get_editor_property("tags")]
            except Exception:
                pass
            tagged_data.append(
                {
                    "data_class": data_class,
                    "num_points": num_points,
                    "tags": tags,
                }
            )
    except Exception as exc:
        tagged_data.append({"error": str(exc)})

    instanced_components = []
    for generated_component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        mesh_path = None
        try:
            mesh = generated_component.get_editor_property("static_mesh")
            mesh_path = mesh.get_path_name() if mesh else None
        except Exception:
            pass
        instanced_components.append(
            {
                "name": generated_component.get_name(),
                "class": _native_smoke_class_name(generated_component),
                "instances": _native_smoke_instance_count(generated_component),
                "mesh": mesh_path,
            }
        )

    spline_mesh_components = []
    for generated_component in actor.get_components_by_class(unreal.SplineMeshComponent):
        mesh_path = None
        materials = []
        try:
            mesh = generated_component.get_editor_property("static_mesh")
            mesh_path = mesh.get_path_name() if mesh else None
        except Exception:
            pass
        try:
            for index in range(generated_component.get_num_materials()):
                material = generated_component.get_material(index)
                materials.append(material.get_path_name() if material else None)
        except Exception:
            pass
        spline_mesh_components.append(
            {
                "name": generated_component.get_name(),
                "class": _native_smoke_class_name(generated_component),
                "mesh": mesh_path,
                "materials": materials,
            }
        )

    roadside_point_counts = {
        category: int(point_array_counts[index]) if index < len(point_array_counts) else 0
        for index, category in enumerate(NATIVE_ROADSIDE_CATEGORY_ORDER)
    }
    roadside_expected_counts = {
        category: int(ROAD_GENERATION_COUNTS[category])
        for category in NATIVE_ROADSIDE_CATEGORY_ORDER
    }
    roadside_count_mismatches = {
        category: {
            "expected": roadside_expected_counts[category],
            "actual": roadside_point_counts.get(category, 0),
        }
        for category in NATIVE_ROADSIDE_CATEGORY_ORDER
        if roadside_point_counts.get(category, 0) != roadside_expected_counts[category]
    }
    roadside_clearance_summary = {}
    roadside_clearance_violations = []
    for index, category in enumerate(NATIVE_ROADSIDE_CATEGORY_ORDER):
        required_clearance = float(LEARNED_ROUTE_CLEARANCE_CM[category])
        data = point_array_data[index] if index < len(point_array_data) else None
        distances = []
        samples = []
        if data:
            for point_index in range(int(data.get_num_points())):
                try:
                    transform = data.get_transform(point_index)
                    location = transform.translation
                    clearance = float(_nearest_route_clearance(float(location.x), float(location.y), route_points))
                    distances.append(clearance)
                    if clearance + 0.01 < required_clearance:
                        violation = {
                            "category": category,
                            "point_index": point_index,
                            "clearance_cm": round(clearance, 2),
                            "required_cm": required_clearance,
                            "x": round(float(location.x), 1),
                            "y": round(float(location.y), 1),
                        }
                        roadside_clearance_violations.append(violation)
                        if len(samples) < 5:
                            samples.append(violation)
                except Exception as exc:
                    roadside_clearance_violations.append(
                        {
                            "category": category,
                            "point_index": point_index,
                            "error": str(exc),
                        }
                    )
                    if len(samples) < 5:
                        samples.append(roadside_clearance_violations[-1])
        roadside_clearance_summary[category] = {
            "required_cm": required_clearance,
            "count": len(distances),
            "min_cm": round(min(distances), 2) if distances else None,
            "avg_cm": round(sum(distances) / len(distances), 2) if distances else None,
            "max_cm": round(max(distances), 2) if distances else None,
            "violation_count": len(
                [
                    item
                    for item in roadside_clearance_violations
                    if item.get("category") == category
                ]
            ),
            "violation_samples": samples,
        }
    instanced_instance_total = sum(
        int(item["instances"])
        for item in instanced_components
        if item.get("instances") is not None
    )
    runtime_material_values = collect_runtime_road_material_values()
    runtime_material_value_mismatches = runtime_road_material_value_mismatches(runtime_material_values)

    return {
        "pass": (
            len(spline_mesh_components) >= expected_spline_mesh_components
            and len(instanced_components) == 3
            and not roadside_count_mismatches
            and not roadside_clearance_violations
            and not runtime_material_value_mismatches
        ),
        "elapsed_sec": round(float(elapsed_seconds), 3),
        "world": _world_path(),
        "graph_path": _runtime_road_native_graph_object_path(),
        "actor_label": actor.get_actor_label(),
        "pcg_generated": _native_smoke_component_generated(component),
        "tagged_data_count": len(tagged_data),
        "tagged_data": tagged_data,
        "point_total": point_total,
        "point_array_counts": point_array_counts,
        "roadside_point_counts": roadside_point_counts,
        "roadside_expected_counts": roadside_expected_counts,
        "roadside_count_mismatches": roadside_count_mismatches,
        "roadside_clearance_summary": roadside_clearance_summary,
        "roadside_clearance_violation_count": len(roadside_clearance_violations),
        "roadside_clearance_violations": roadside_clearance_violations[:20],
        "instanced_component_count": len(instanced_components),
        "instanced_instance_total": instanced_instance_total,
        "instanced_components": instanced_components,
        "spline_mesh_component_count": len(spline_mesh_components),
        "spline_mesh_components": spline_mesh_components,
        "runtime_material_values": runtime_material_values,
        "runtime_material_value_mismatches": runtime_material_value_mismatches,
        "expected_min_spline_mesh_components": expected_spline_mesh_components,
        "expected_instanced_component_count": 3,
    }


def start_runtime_road_native_graph_live_smoke_test(keep_preview=False, timeout_seconds=6.0, source_points_override=None, source_label_override=None, preview_label_suffix=""):
    label = "MCP_TMP_NativeRoadPCGValidation_LiveCollect{}".format(preview_label_suffix or "")
    report_path = _saved_runtime_road_native_graph_smoke_report_path()
    graph_report = create_or_update_runtime_road_native_skeleton_graph(
        source_points_override=source_points_override,
        source_label_override=source_label_override,
    )
    graph = _load_object(_runtime_road_native_graph_object_path())
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_actor_label() == label:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PCGVolume,
        unreal.Vector(25500.0, 25000.0, 500.0),
    )
    actor.set_actor_label(label)
    try:
        actor.set_actor_scale3d(unreal.Vector(600.0, 600.0, 30.0))
    except Exception:
        pass

    components = actor.get_components_by_class(unreal.PCGComponent)
    if not components:
        raise RuntimeError("Spawned PCGVolume has no PCGComponent")
    component = components[0]
    component.set_graph(graph)
    component.cleanup(True)
    component.activate(True)
    component.generate(True)
    component.generate(True)

    scheduled_report = {
        "pass": None,
        "status": "scheduled",
        "world": _world_path(),
        "graph_path": _runtime_road_native_graph_object_path(),
        "actor_label": label,
        "source_label": graph_report.get("runtime_spline_sync", {}).get("source_label"),
        "keep_preview": bool(keep_preview),
        "timeout_seconds": float(timeout_seconds),
        "graph_report_path": graph_report.get("report_path"),
    }
    _native_smoke_write_report(report_path, scheduled_report)

    state = {"elapsed": 0.0, "handle": None, "done": False}

    def _on_tick(delta_seconds):
        if state["done"]:
            return
        state["elapsed"] += float(delta_seconds)
        if state["elapsed"] < 0.25:
            return
        ready = _native_smoke_component_generated(component)
        if not ready and state["elapsed"] < float(timeout_seconds):
            return
        state["done"] = True
        try:
            route_points = (
                graph_report.get("runtime_spline_sync", {})
                .get("after", {})
                .get("points")
            )
            result = _native_smoke_summarize_actor(actor, component, state["elapsed"], route_points=route_points)
            result["status"] = "ready" if ready else "timeout_collect"
            result["source_label"] = graph_report.get("runtime_spline_sync", {}).get("source_label")
            result["keep_preview"] = bool(keep_preview)
            result["graph_report_path"] = graph_report.get("report_path")
            _native_smoke_write_report(report_path, result)
        except Exception:
            _native_smoke_write_report(
                report_path,
                {
                    "pass": False,
                    "status": "error",
                    "world": _world_path(),
                    "graph_path": _runtime_road_native_graph_object_path(),
                    "error": traceback.format_exc(),
                },
            )
        if not keep_preview:
            try:
                unreal.EditorLevelLibrary.destroy_actor(actor)
            except Exception:
                pass
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass

    state["handle"] = unreal.register_slate_post_tick_callback(_on_tick)
    scheduled_report["report_path"] = report_path
    return scheduled_report


def read_runtime_road_native_graph_live_smoke_report():
    report_path = _saved_runtime_road_native_graph_smoke_report_path()
    if not os.path.exists(report_path):
        return {"exists": False, "report_path": report_path}
    with open(report_path, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    report["exists"] = True
    report["report_path"] = report_path
    return report


def read_runtime_road_native_graph_shape_suite_report():
    report_path = _saved_runtime_road_native_graph_shape_suite_report_path()
    if not os.path.exists(report_path):
        return {"exists": False, "report_path": report_path}
    with open(report_path, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    report["exists"] = True
    report["report_path"] = report_path
    return report


def _shape_suite_point(origin, offset_x, offset_y, offset_z=0.0):
    return [
        float(origin[0]) + float(offset_x),
        float(origin[1]) + float(offset_y),
        float(origin[2]) + float(offset_z),
    ]


def _shape_suite_points_from_offsets(origin, offsets):
    return [_shape_suite_point(origin, item[0], item[1], item[2] if len(item) > 2 else 0.0) for item in offsets]


def _runtime_road_native_graph_shape_specs(source_points):
    origin = source_points[0] if source_points else ROAD_CONTROL_POINTS[0]
    return [
        {
            "key": "authoring_baseline",
            "description": "Current authoring/runtime route restored from the user's Road_SourceSpline.",
            "points": source_points,
        },
        {
            "key": "compact_curve",
            "description": "Shorter route with a compact S curve; validates module-size recalculation on small roads.",
            "points": _shape_suite_points_from_offsets(
                origin,
                [
                    (0.0, 0.0, 0.0),
                    (3500.0, 1800.0, 20.0),
                    (7600.0, -1600.0, 35.0),
                    (11600.0, 2300.0, 40.0),
                    (15800.0, 700.0, 30.0),
                ],
            ),
        },
        {
            "key": "tight_switchback",
            "description": "Alternating tight turns; validates edge/soften offset noise on high-curvature routes.",
            "points": _shape_suite_points_from_offsets(
                origin,
                [
                    (0.0, 0.0, 0.0),
                    (4200.0, 300.0, 20.0),
                    (7000.0, 5200.0, 40.0),
                    (10800.0, -4200.0, 45.0),
                    (14600.0, 5600.0, 35.0),
                    (19000.0, -2700.0, 20.0),
                    (23800.0, 2600.0, 10.0),
                ],
            ),
        },
        {
            "key": "long_sweep",
            "description": "Long sweeping route; validates target component counts and clearance over a longer road.",
            "points": _shape_suite_points_from_offsets(
                origin,
                [
                    (0.0, 0.0, 0.0),
                    (7200.0, 1300.0, 20.0),
                    (14600.0, -2600.0, 45.0),
                    (23000.0, 2100.0, 55.0),
                    (31400.0, -1900.0, 45.0),
                    (40000.0, 3300.0, 35.0),
                    (48600.0, -600.0, 20.0),
                    (57400.0, 4500.0, 10.0),
                ],
            ),
        },
    ]


def _runtime_road_native_graph_shape_suite_source():
    try:
        source = read_authoring_spline_points(create_if_missing=False)
        return {
            "label": source["actor_label"] + "." + source["component_name"],
            "points": source["points"],
            "source": source,
            "fallback": False,
        }
    except Exception as authoring_exc:
        try:
            source = read_runtime_road_spline_points(create_if_missing=False)
            return {
                "label": source["actor_label"] + "." + source["component_name"],
                "points": source["points"],
                "source": source,
                "fallback": True,
                "authoring_error": str(authoring_exc),
            }
        except Exception as runtime_exc:
            return {
                "label": "ROAD_CONTROL_POINTS fallback",
                "points": ROAD_CONTROL_POINTS,
                "source": {"point_count": len(ROAD_CONTROL_POINTS)},
                "fallback": True,
                "authoring_error": str(authoring_exc),
                "runtime_error": str(runtime_exc),
            }


def _runtime_road_native_shape_suite_quality(result, baseline_route_length_cm):
    expected_spline_mesh_components = (
        SPLINE_MESH_ROAD_COUNTS["Core"]
        + SPLINE_MESH_ROAD_COUNTS["Edge"]
        + SPLINE_MESH_ROAD_COUNTS["Soften"]
    )
    expected_instances_at_baseline = sum(ROAD_GENERATION_COUNTS[category] for category in NATIVE_ROADSIDE_CATEGORY_ORDER)
    route_length = max(float(result.get("shape_route_length_cm") or baseline_route_length_cm), 1.0)
    baseline_length = max(float(baseline_route_length_cm), 1.0)
    expected_instances_for_route = expected_instances_at_baseline * (route_length / baseline_length)
    spline_mesh_count = int(result.get("spline_mesh_component_count") or 0)
    instanced_total = int(result.get("instanced_instance_total") or 0)
    spline_mesh_min = expected_spline_mesh_components - max(12, int(round(expected_spline_mesh_components * 0.055)))
    spline_mesh_max = expected_spline_mesh_components + max(12, int(round(expected_spline_mesh_components * 0.055)))
    instance_min = max(12, int(round(expected_instances_for_route * 0.45)))
    instance_max = max(instance_min, int(round(expected_instances_for_route * 1.70)) + 8)
    checks = {
        "graph_edges": not result.get("graph_edge_errors"),
        "runtime_materials": not result.get("runtime_material_value_mismatches"),
        "clearance": int(result.get("roadside_clearance_violation_count") or 0) == 0,
        "spline_mesh_count": spline_mesh_min <= spline_mesh_count <= spline_mesh_max,
        "route_density": instance_min <= instanced_total <= instance_max,
    }
    if result.get("shape_key") == "authoring_baseline":
        checks["baseline_exact_smoke"] = bool(result.get("pass"))
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "expected_spline_mesh_count": expected_spline_mesh_components,
        "spline_mesh_allowed_range": [spline_mesh_min, spline_mesh_max],
        "expected_instances_for_route": round(float(expected_instances_for_route), 2),
        "instance_allowed_range": [instance_min, instance_max],
    }


def start_runtime_road_native_graph_shape_suite_smoke_test(timeout_seconds=6.0, keep_last_preview=False):
    report_path = _saved_runtime_road_native_graph_shape_suite_report_path()
    source = _runtime_road_native_graph_shape_suite_source()
    shape_specs = _runtime_road_native_graph_shape_specs(source["points"])
    baseline_route_length_cm = float(_route_segments(source["points"])[1])
    actor_label_prefix = "MCP_TMP_NativeRoadPCGShapeSuite_"

    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_actor_label().startswith(actor_label_prefix):
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass

    scheduled_report = {
        "pass": None,
        "status": "scheduled",
        "world": _world_path(),
        "graph_path": _runtime_road_native_graph_object_path(),
        "shape_count": len(shape_specs),
        "source_label": source["label"],
        "baseline_route_length_cm": round(baseline_route_length_cm, 2),
        "keep_last_preview": bool(keep_last_preview),
        "timeout_seconds": float(timeout_seconds),
        "results": [],
    }
    _native_smoke_write_report(report_path, scheduled_report)

    state = {
        "index": -1,
        "elapsed": 0.0,
        "handle": None,
        "actor": None,
        "component": None,
        "graph_report": None,
        "shape": None,
        "results": [],
        "done": False,
    }

    def _write_suite(status, extra=None):
        completed_pass = all(item.get("shape_suite_quality", {}).get("pass") for item in state["results"])
        payload = {
            "pass": None if status == "scheduled" else completed_pass,
            "status": status,
            "world": _world_path(),
            "graph_path": _runtime_road_native_graph_object_path(),
            "shape_count": len(shape_specs),
            "completed_shape_count": len(state["results"]),
            "source_label": source["label"],
            "baseline_route_length_cm": round(baseline_route_length_cm, 2),
            "keep_last_preview": bool(keep_last_preview),
            "timeout_seconds": float(timeout_seconds),
            "results": state["results"],
        }
        if extra:
            payload.update(extra)
        _native_smoke_write_report(report_path, payload)

    def _finish_suite(status="ready", error=None):
        state["done"] = True
        restore_report = None
        try:
            restore_report = create_or_update_runtime_road_native_skeleton_graph(
                source_points_override=source["points"],
                source_label_override="shape_suite:restore:" + source["label"],
            )
        except Exception:
            if error:
                error = error + "\n" + traceback.format_exc()
            else:
                error = traceback.format_exc()
        extra = {
            "restore_graph_report_path": restore_report.get("report_path") if restore_report else None,
            "restore_pass": bool(restore_report and restore_report.get("runtime_spline_sync", {}).get("pass")),
            "report_path": report_path,
        }
        extra["pass"] = all(item.get("shape_suite_quality", {}).get("pass") for item in state["results"]) and bool(extra["restore_pass"])
        if error:
            extra["error"] = error
            extra["pass"] = False
        _write_suite(status, extra)
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass

    def _start_shape():
        state["index"] += 1
        if state["index"] >= len(shape_specs):
            _finish_suite("ready")
            return

        shape = shape_specs[state["index"]]
        state["shape"] = shape
        state["elapsed"] = 0.0
        graph_report = create_or_update_runtime_road_native_skeleton_graph(
            source_points_override=shape["points"],
            source_label_override="shape_suite:" + shape["key"],
        )
        graph = _load_object(_runtime_road_native_graph_object_path())
        label = actor_label_prefix + shape["key"]
        for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
            try:
                if actor.get_actor_label() == label:
                    unreal.EditorLevelLibrary.destroy_actor(actor)
            except Exception:
                pass
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PCGVolume,
            unreal.Vector(25500.0, 25000.0, 500.0),
        )
        actor.set_actor_label(label)
        try:
            actor.set_actor_scale3d(unreal.Vector(800.0, 800.0, 30.0))
        except Exception:
            pass
        components = actor.get_components_by_class(unreal.PCGComponent)
        if not components:
            raise RuntimeError("Spawned shape suite PCGVolume has no PCGComponent: {}".format(label))
        component = components[0]
        component.set_graph(graph)
        component.cleanup(True)
        component.activate(True)
        component.generate(True)
        component.generate(True)
        state["actor"] = actor
        state["component"] = component
        state["graph_report"] = graph_report
        _write_suite("scheduled", {"active_shape": shape["key"], "report_path": report_path})

    def _on_tick(delta_seconds):
        if state["done"]:
            return
        try:
            if state["shape"] is None:
                _start_shape()
                return
            state["elapsed"] += float(delta_seconds)
            if state["elapsed"] < 0.25:
                return
            ready = _native_smoke_component_generated(state["component"])
            if not ready and state["elapsed"] < float(timeout_seconds):
                return

            shape = state["shape"]
            result = _native_smoke_summarize_actor(
                state["actor"],
                state["component"],
                state["elapsed"],
                route_points=shape["points"],
            )
            result["shape_key"] = shape["key"]
            result["shape_description"] = shape["description"]
            result["shape_route_length_cm"] = round(float(_route_segments(shape["points"])[1]), 2)
            result["status"] = "ready" if ready else "timeout_collect"
            result["graph_report_path"] = state["graph_report"].get("report_path")
            result["graph_edge_count"] = state["graph_report"].get("edge_count")
            result["graph_edge_errors"] = state["graph_report"].get("edge_errors")
            result["source_label"] = state["graph_report"].get("runtime_spline_sync", {}).get("source_label")
            result["shape_suite_quality"] = _runtime_road_native_shape_suite_quality(result, baseline_route_length_cm)
            state["results"].append(result)

            keep_actor = bool(keep_last_preview and state["index"] == len(shape_specs) - 1)
            if not keep_actor:
                try:
                    unreal.EditorLevelLibrary.destroy_actor(state["actor"])
                except Exception:
                    pass
            state["actor"] = None
            state["component"] = None
            state["graph_report"] = None
            state["shape"] = None
            _start_shape()
        except Exception:
            _finish_suite("error", traceback.format_exc())

    state["handle"] = unreal.register_slate_post_tick_callback(_on_tick)
    scheduled_report["report_path"] = report_path
    return scheduled_report


def _authoring_blueprint_path():
    return AUTHORING_BP_FOLDER + "/" + AUTHORING_BP_NAME


def _runtime_road_blueprint_path():
    return RUNTIME_ROAD_BP_FOLDER + "/" + RUNTIME_ROAD_BP_NAME


def _runtime_road_blueprint_object_path():
    return _runtime_road_blueprint_path() + "." + RUNTIME_ROAD_BP_NAME


def _runtime_road_blueprint_class_path():
    return _runtime_road_blueprint_object_path() + "_C"


def _get_blueprint_subobject_rows(blueprint):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    rows = []
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        obj = None
        try:
            obj = library.get_associated_object(data)
        except Exception:
            obj = None
        rows.append(
            {
                "handle": handle,
                "display": str(library.get_display_name(data)),
                "variable": str(library.get_variable_name(data)),
                "class": obj.get_class().get_name() if obj else None,
                "path": obj.get_path_name() if obj else None,
                "is_root_component": bool(library.is_root_component(data)),
                "is_default_scene_root": bool(library.is_default_scene_root(data)),
            }
        )
    return rows


def _ensure_spline_blueprint(folder, name, component_name):
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)

    blueprint_path = folder + "/" + name
    blueprint = unreal.load_object(None, blueprint_path + "." + name)
    created = False
    if not blueprint:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("ParentClass", unreal.Actor)
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name,
            folder,
            unreal.Blueprint,
            factory,
        )
        created = bool(blueprint)
    if not blueprint:
        raise RuntimeError("Failed to create/load spline blueprint: {}".format(blueprint_path))

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    rows = _get_blueprint_subobject_rows(blueprint)
    root_handle = None
    spline_rows = []
    for row in rows:
        if row["is_default_scene_root"] or row["is_root_component"]:
            root_handle = row["handle"]
        if row["class"] == "SplineComponent":
            spline_rows.append(row)

    unique_spline_paths = sorted({row["path"] for row in spline_rows if row["path"]})
    added_spline = False
    add_fail_reason = ""
    named_spline_rows = [row for row in spline_rows if row["variable"] == component_name or row["display"] == component_name]
    if not named_spline_rows:
        if root_handle is None:
            raise RuntimeError("Spline blueprint has no root handle for SplineComponent attach")
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("blueprint_context", blueprint)
        params.set_editor_property("new_class", unreal.SplineComponent)
        params.set_editor_property("parent_handle", root_handle)
        params.set_editor_property("skip_mark_blueprint_modified", False)
        params.set_editor_property("conform_transform_to_parent", True)
        new_handle, fail_reason = subsystem.add_new_subobject(params)
        add_fail_reason = str(fail_reason)
        if add_fail_reason:
            raise RuntimeError("Failed to add spline component: {}".format(add_fail_reason))
        subsystem.rename_subobject(new_handle, unreal.Text(component_name))
        try:
            subsystem.rename_subobject_member_variable(blueprint, new_handle, unreal.Name(component_name))
        except Exception:
            pass
        added_spline = True
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False)
        rows = _get_blueprint_subobject_rows(blueprint)
        spline_rows = [row for row in rows if row["class"] == "SplineComponent"]
        unique_spline_paths = sorted({row["path"] for row in spline_rows if row["path"]})

    named_spline_paths = sorted(
        {
            row["path"]
            for row in spline_rows
            if row["path"] and (row["variable"] == component_name or row["display"] == component_name)
        }
    )
    if len(named_spline_paths) != 1:
        raise RuntimeError("Expected one named spline template {}, found {}".format(component_name, named_spline_paths))

    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False)
    return {
        "created": created,
        "added_spline": added_spline,
        "blueprint_path": blueprint.get_path_name(),
        "spline_unique_paths": named_spline_paths,
        "spline_handle_count": len(spline_rows),
        "subobject_count": len(rows),
        "add_fail_reason": add_fail_reason,
    }


def _ensure_authoring_blueprint():
    return _ensure_spline_blueprint(AUTHORING_BP_FOLDER, AUTHORING_BP_NAME, AUTHORING_SPLINE_NAME)


def create_or_update_runtime_road_blueprint():
    blueprint_result = _ensure_spline_blueprint(
        RUNTIME_ROAD_BP_FOLDER,
        RUNTIME_ROAD_BP_NAME,
        AUTHORING_SPLINE_NAME,
    )
    blueprint = _load_object(_runtime_road_blueprint_object_path())
    runtime_class = unreal.load_class(None, _runtime_road_blueprint_class_path())
    if not runtime_class:
        unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
        unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False)
        runtime_class = unreal.load_class(None, _runtime_road_blueprint_class_path())
    if not runtime_class:
        raise RuntimeError("Runtime road Blueprint class did not load: {}".format(_runtime_road_blueprint_class_path()))
    return {
        "blueprint": blueprint_result,
        "runtime_blueprint_object": _runtime_road_blueprint_object_path(),
        "runtime_blueprint_class": _runtime_road_blueprint_class_path(),
        "class_loaded": True,
    }


def _get_authoring_blueprint():
    return _load_object(_authoring_blueprint_path() + "." + AUTHORING_BP_NAME)


def _find_or_spawn_authoring_actor(blueprint):
    matches = [actor for actor in _actors() if _label(actor) == AUTHORING_ACTOR_LABEL]
    removed_duplicates = 0

    valid_matches = []
    for actor in matches:
        splines = list(actor.get_components_by_class(unreal.SplineComponent))
        valid_splines = [
            component
            for component in splines
            if component.get_name() == AUTHORING_SPLINE_NAME and not component.get_name().startswith("TRASH_")
        ]
        if valid_splines:
            valid_matches.append(actor)
        else:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed_duplicates += 1

    for extra_actor in valid_matches[1:]:
        unreal.EditorLevelLibrary.destroy_actor(extra_actor)
        removed_duplicates += 1

    if valid_matches:
        actor = valid_matches[0]
        spawned = False
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            blueprint.generated_class(),
            unreal.Vector(*ROAD_CONTROL_POINTS[0]),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        spawned = True

    actor.modify()
    actor.set_actor_label(AUTHORING_ACTOR_LABEL, mark_dirty=True)
    actor.set_folder_path(AUTHORING_ACTOR_FOLDER)
    actor.set_actor_location(unreal.Vector(*ROAD_CONTROL_POINTS[0]), False, True)
    return {
        "actor": actor,
        "spawned": spawned,
        "removed_duplicates": removed_duplicates,
        "actor_path": actor.get_path_name(),
    }


def _find_or_spawn_runtime_road_actor():
    runtime_class = unreal.load_class(None, _runtime_road_blueprint_class_path())
    if not runtime_class:
        raise RuntimeError("Missing runtime road Blueprint class: {}".format(_runtime_road_blueprint_class_path()))

    matches = [actor for actor in _actors() if _label(actor) == RUNTIME_ROAD_ACTOR_LABEL]
    removed_duplicates = 0
    valid_matches = []
    for actor in matches:
        splines = list(actor.get_components_by_class(unreal.SplineComponent))
        valid_splines = [
            component
            for component in splines
            if component.get_name() == AUTHORING_SPLINE_NAME and not component.get_name().startswith("TRASH_")
        ]
        if valid_splines:
            valid_matches.append(actor)
        else:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed_duplicates += 1

    for extra_actor in valid_matches[1:]:
        unreal.EditorLevelLibrary.destroy_actor(extra_actor)
        removed_duplicates += 1

    if valid_matches:
        actor = valid_matches[0]
        spawned = False
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            runtime_class,
            unreal.Vector(*ROAD_CONTROL_POINTS[0]),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        spawned = True

    actor.modify()
    actor.set_actor_label(RUNTIME_ROAD_ACTOR_LABEL, mark_dirty=True)
    actor.set_folder_path(RUNTIME_ROAD_ACTOR_FOLDER)
    tag_added = _ensure_actor_tag(actor, RUNTIME_ROAD_ACTOR_TAG)
    spline, splines = _authoring_spline_component(actor)
    spline_tag_added = _ensure_component_tag(spline, RUNTIME_ROAD_SPLINE_TAG)
    target_location = unreal.Vector(*ROAD_CONTROL_POINTS[0])
    current_location = actor.get_actor_location()
    location_delta = math.sqrt(
        (float(current_location.x) - float(target_location.x)) ** 2
        + (float(current_location.y) - float(target_location.y)) ** 2
        + (float(current_location.z) - float(target_location.z)) ** 2
    )
    location_set = False
    if spawned or location_delta > 1.0:
        actor.set_actor_location(target_location, False, True)
        location_set = True
    return {
        "actor": actor,
        "spawned": spawned,
        "removed_duplicates": removed_duplicates,
        "actor_path": actor.get_path_name(),
        "tag": RUNTIME_ROAD_ACTOR_TAG,
        "tag_added": tag_added,
        "spline_component": spline.get_name(),
        "spline_component_count": len(splines),
        "spline_tag": RUNTIME_ROAD_SPLINE_TAG,
        "spline_tag_added": spline_tag_added,
        "location_delta_before_set_cm": round(location_delta, 3),
        "location_set": location_set,
    }


def _authoring_spline_component(actor):
    splines = [
        component
        for component in actor.get_components_by_class(unreal.SplineComponent)
        if not component.get_name().startswith("TRASH_")
    ]
    named = [component for component in splines if component.get_name() == AUTHORING_SPLINE_NAME]
    if named:
        return named[0], splines
    if splines:
        return splines[0], splines
    raise RuntimeError("Authoring actor has no SplineComponent: {}".format(actor.get_actor_label()))


def _set_actor_spline_points(actor, points):
    spline, splines = _authoring_spline_component(actor)
    actor.modify()
    spline.modify()
    spline.clear_spline_points(False)
    for point in points:
        spline.add_spline_point(unreal.Vector(*point), unreal.SplineCoordinateSpace.WORLD, False)
    for index in range(len(points)):
        spline.set_spline_point_type(index, unreal.SplinePointType.LINEAR, False)
    try:
        spline.set_editor_property("input_spline_points_to_construction_script", True)
    except Exception:
        pass
    spline.update_spline()

    segments, route_length = _route_segments(points)
    point_deltas = []
    for index, expected in enumerate(points):
        location = spline.get_world_location_at_spline_point(index)
        delta = math.sqrt(
            (float(location.x) - expected[0]) ** 2
            + (float(location.y) - expected[1]) ** 2
            + (float(location.z) - expected[2]) ** 2
        )
        point_deltas.append(round(delta, 3))

    return {
        "component_name": spline.get_name(),
        "component_path": spline.get_path_name(),
        "component_count_on_actor": len(splines),
        "point_count": spline.get_number_of_spline_points(),
        "expected_point_count": len(points),
        "max_point_delta_cm": max(point_deltas) if point_deltas else 0.0,
        "spline_length_cm": round(float(spline.get_spline_length()), 2),
        "wrapper_route_length_cm": round(float(route_length), 2),
        "length_delta_cm": round(abs(float(spline.get_spline_length()) - float(route_length)), 2),
    }


def _set_authoring_spline_points(actor):
    return _set_actor_spline_points(actor, ROAD_CONTROL_POINTS)


def create_or_update_authoring_handle():
    blueprint_result = _ensure_authoring_blueprint()
    blueprint = _get_authoring_blueprint()
    actor_result = _find_or_spawn_authoring_actor(blueprint)
    actor = actor_result.pop("actor")
    spline_result = _set_authoring_spline_points(actor)
    validation = validate_scene()
    report = {
        "level": _world_path(),
        "bookmark_policy": "bookmark 1/2 are user-owned and are not modified by this authoring handle step",
        "blueprint": blueprint_result,
        "actor": actor_result,
        "spline": spline_result,
        "scene_validation": validation,
    }
    report_path = _saved_authoring_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    save_ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    report["save_ok"] = bool(save_ok)
    unreal.log("CubelessRoadPCG authoring handle: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def read_authoring_spline_points(create_if_missing=False):
    matches = [actor for actor in _actors() if _label(actor) == AUTHORING_ACTOR_LABEL]
    if not matches and create_if_missing:
        create_or_update_authoring_handle()
        matches = [actor for actor in _actors() if _label(actor) == AUTHORING_ACTOR_LABEL]
    if not matches:
        raise RuntimeError("Authoring actor not found: {}".format(AUTHORING_ACTOR_LABEL))
    actor = matches[0]
    spline, splines = _authoring_spline_component(actor)
    point_count = spline.get_number_of_spline_points()
    if point_count < 2:
        raise RuntimeError("Authoring spline has too few points: {}".format(point_count))

    points = []
    for index in range(point_count):
        location = spline.get_world_location_at_spline_point(index)
        points.append([float(location.x), float(location.y), float(location.z)])

    segments, route_length = _route_segments(points)
    return {
        "actor_label": actor.get_actor_label(),
        "actor_path": actor.get_path_name(),
        "component_name": spline.get_name(),
        "component_path": spline.get_path_name(),
        "component_count_on_actor": len(splines),
        "point_count": point_count,
        "segment_count": len(segments),
        "route_length_cm": round(float(route_length), 2),
        "points": points,
    }


def read_runtime_road_spline_points(create_if_missing=False, source_points=None):
    matches = [actor for actor in _actors() if _label(actor) == RUNTIME_ROAD_ACTOR_LABEL]
    if not matches and create_if_missing:
        create_or_update_runtime_road_blueprint()
        actor_result = _find_or_spawn_runtime_road_actor()
        actor = actor_result["actor"]
        _set_actor_spline_points(actor, source_points or ROAD_CONTROL_POINTS)
        matches = [actor]
    if not matches:
        raise RuntimeError("Runtime road actor not found: {}".format(RUNTIME_ROAD_ACTOR_LABEL))
    actor = matches[0]
    spline, splines = _authoring_spline_component(actor)
    point_count = spline.get_number_of_spline_points()
    if point_count < 2:
        raise RuntimeError("Runtime road spline has too few points: {}".format(point_count))

    points = []
    for index in range(point_count):
        location = spline.get_world_location_at_spline_point(index)
        points.append([float(location.x), float(location.y), float(location.z)])

    segments, route_length = _route_segments(points)
    return {
        "actor_label": actor.get_actor_label(),
        "actor_path": actor.get_path_name(),
        "component_name": spline.get_name(),
        "component_path": spline.get_path_name(),
        "component_count_on_actor": len(splines),
        "point_count": point_count,
        "segment_count": len(segments),
        "route_length_cm": round(float(route_length), 2),
        "points": points,
    }


def _spline_points_delta_summary(before_points, after_points):
    deltas = []
    compared_count = min(len(before_points), len(after_points))
    for index in range(compared_count):
        before = before_points[index]
        after = after_points[index]
        deltas.append(
            math.sqrt(
                (float(before[0]) - float(after[0])) ** 2
                + (float(before[1]) - float(after[1])) ** 2
                + (float(before[2]) - float(after[2])) ** 2
            )
        )
    return {
        "compared_count": compared_count,
        "point_count_before": len(before_points),
        "point_count_after": len(after_points),
        "max_delta_cm": round(max(deltas) if deltas else 0.0, 2),
        "avg_delta_cm": round(sum(deltas) / len(deltas), 2) if deltas else 0.0,
    }


def ensure_runtime_road_spline_synced_to_authoring(save=False):
    source_repair = None
    try:
        source_spline = read_authoring_spline_points(create_if_missing=True)
        if (
            source_spline["point_count"] < len(ROAD_CONTROL_POINTS)
            or source_spline["route_length_cm"] < 10000.0
        ):
            source_repair = create_or_update_authoring_handle()
            source_spline = read_authoring_spline_points(create_if_missing=False)
        source_points = source_spline["points"]
        source_label = source_spline["actor_label"] + "." + source_spline["component_name"]
        source_error = None
    except Exception as exc:
        source_points = ROAD_CONTROL_POINTS
        source_label = "ROAD_CONTROL_POINTS fallback"
        source_error = str(exc)

    blueprint_refreshed = False
    if not unreal.load_class(None, _runtime_road_blueprint_class_path()):
        create_or_update_runtime_road_blueprint()
        blueprint_refreshed = True
    actor_result = _find_or_spawn_runtime_road_actor()
    actor = actor_result["actor"]
    before = read_runtime_road_spline_points(create_if_missing=False, source_points=source_points)
    before_delta = _spline_points_delta_summary(source_points, before["points"])
    needs_sync = (
        before["point_count"] != len(source_points)
        or before_delta["max_delta_cm"] > 1.0
    )
    if needs_sync:
        set_result = _set_actor_spline_points(actor, source_points)
    else:
        set_result = {"skipped": True, "reason": "runtime spline already matches source"}

    spline, splines = _authoring_spline_component(actor)
    spline_tag_added = _ensure_component_tag(spline, RUNTIME_ROAD_SPLINE_TAG)
    after = read_runtime_road_spline_points(create_if_missing=False, source_points=source_points)
    after_delta = _spline_points_delta_summary(source_points, after["points"])
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return {
        "source_label": source_label,
        "source_error": source_error,
        "source_point_count": len(source_points),
        "source_repair": source_repair,
        "actor": {
            key: value
            for key, value in actor_result.items()
            if key != "actor"
        },
        "blueprint_refreshed": blueprint_refreshed,
        "before": {
            "point_count": before["point_count"],
            "route_length_cm": before["route_length_cm"],
            "delta_from_source": before_delta,
        },
        "sync_applied": bool(needs_sync),
        "set_result": set_result,
        "spline_component": {
            "name": spline.get_name(),
            "path": spline.get_path_name(),
            "component_count_on_actor": len(splines),
            "tag": RUNTIME_ROAD_SPLINE_TAG,
            "tag_added": spline_tag_added,
        },
        "after": {
            "point_count": after["point_count"],
            "route_length_cm": after["route_length_cm"],
            "delta_from_source": after_delta,
            "points": after["points"],
        },
        "pass": after["point_count"] == len(source_points) and after_delta["max_delta_cm"] <= 1.0,
    }


def run_authoring_spline_regeneration_smoke_test(keep_preview=False):
    spline_read = read_authoring_spline_points(create_if_missing=True)
    report = run_regeneration_smoke_test(
        keep_preview=keep_preview,
        points=spline_read["points"],
        route_source=AUTHORING_ACTOR_LABEL + "." + AUTHORING_SPLINE_NAME,
        report_name=AUTHORING_SPLINE_REGEN_REPORT_NAME,
    )
    report["authoring_spline"] = {
        "actor_label": spline_read["actor_label"],
        "actor_path": spline_read["actor_path"],
        "component_name": spline_read["component_name"],
        "component_path": spline_read["component_path"],
        "point_count": spline_read["point_count"],
        "segment_count": spline_read["segment_count"],
        "route_length_cm": spline_read["route_length_cm"],
    }
    report_path = _saved_regen_report_path(AUTHORING_SPLINE_REGEN_REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    unreal.log("CubelessRoadPCG authoring spline regen smoke test: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def validate_visible_road_tune(mode="auto"):
    counts = {
        "road_core": 0,
        "road_edge": 0,
        "road_soften": 0,
        "road_dust": 0,
    }
    scale_samples = {
        "road_core_width_y": [],
        "road_edge_width_y": [],
        "road_soften_width_y": [],
        "road_dust_width_y": [],
    }
    material_paths = {}
    regen_count = 0
    tmp_count = 0
    for actor in _actors():
        label = _label(actor)
        if label.startswith(REGEN_PREFIX):
            regen_count += 1
        if label.startswith("MCP_TMP_"):
            tmp_count += 1

        matched_key = _visible_road_key_for_label(label)
        if not matched_key:
            continue

        counts[matched_key] += 1
        sample_key = matched_key + "_width_y"
        if len(scale_samples[sample_key]) < 24:
            try:
                if label.startswith("MCP_SplineRoadMesh_"):
                    component = actor.spline_mesh_component
                    start_scale = component.get_start_scale()
                    end_scale = component.get_end_scale()
                    scale_samples[sample_key].append(
                        {
                            "start": [round(float(start_scale.x), 3), round(float(start_scale.y), 3)],
                            "end": [round(float(end_scale.x), 3), round(float(end_scale.y), 3)],
                        }
                    )
                else:
                    scale = actor.get_actor_scale3d()
                    scale_samples[sample_key].append(round(float(scale.y), 3))
            except Exception:
                scale = actor.get_actor_scale3d()
                scale_samples[sample_key].append(round(float(scale.y), 3))
        try:
            component = actor.spline_mesh_component if label.startswith("MCP_SplineRoadMesh_") else actor.static_mesh_component
            material = component.get_material(0)
            if material:
                material_paths[matched_key] = material.get_path_name()
        except Exception:
            pass

    expected = _visible_road_expected_counts(mode, counts)
    count_mismatches = {
        key: {"expected": value, "actual": counts.get(key, 0)}
        for key, value in expected.items()
        if counts.get(key, 0) != value
    }
    return {
        "counts": counts,
        "expected": expected,
        "count_mismatches": count_mismatches,
        "scale_samples": scale_samples,
        "material_paths": dict(sorted(material_paths.items())),
        "regen_actor_count": regen_count,
        "tmp_actor_count": tmp_count,
        "pass": not count_mismatches and regen_count == 0 and tmp_count == 0,
    }


def _runtime_data_category_for_label(label):
    if label.startswith("MCP_CubelessRuntimeRoadData_"):
        return label[len("MCP_CubelessRuntimeRoadData_") :].split("_")[0]
    return None


def validate_runtime_road_validation_output(points=None):
    road_counts = {
        "road_core": 0,
        "road_edge": 0,
        "road_soften": 0,
        "road_dust": 0,
    }
    learned = []
    material_paths = {}
    runtime_actor_count = 0
    for actor in _actors():
        label = _label(actor)
        if label == RUNTIME_ROAD_ACTOR_LABEL:
            runtime_actor_count += 1

        matched_key = None
        if label.startswith(RUNTIME_ROAD_PREFIXES_BY_KIND["Core"]):
            matched_key = "road_core"
        elif label.startswith(RUNTIME_ROAD_PREFIXES_BY_KIND["Edge"]):
            matched_key = "road_edge"
        elif label.startswith(RUNTIME_ROAD_PREFIXES_BY_KIND["Soften"]):
            matched_key = "road_soften"
        if matched_key:
            road_counts[matched_key] += 1
            try:
                material = actor.spline_mesh_component.get_material(0)
                if material:
                    material_paths[matched_key] = material.get_path_name()
            except Exception:
                pass
            continue

        category = _runtime_data_category_for_label(label)
        if category:
            loc = actor.get_actor_location()
            rot = actor.get_actor_rotation()
            scale = actor.get_actor_scale3d()
            learned.append(
                {
                    "label": label,
                    "category": category,
                    "x": float(loc.x),
                    "y": float(loc.y),
                    "pitch": float(rot.pitch),
                    "roll": float(rot.roll),
                    "scale": float(scale.x),
                }
            )

    road_expected = _visible_road_expected_counts("spline_mesh")
    road_mismatches = {
        key: {"expected": value, "actual": road_counts.get(key, 0)}
        for key, value in road_expected.items()
        if road_counts.get(key, 0) != value
    }

    learned_counts = _count_by([item["category"] for item in learned])
    learned_expected = {
        "gravel": ROAD_GENERATION_COUNTS["gravel"],
        "stone": ROAD_GENERATION_COUNTS["stone"],
        "embankment": ROAD_GENERATION_COUNTS["embankment"],
    }
    learned_mismatches = {
        key: {"expected": value, "actual": learned_counts.get(key, 0)}
        for key, value in learned_expected.items()
        if learned_counts.get(key, 0) != value
    }
    pitch_roll_violations = [
        item for item in learned if abs(item["pitch"]) > 5.1 or abs(item["roll"]) > 5.1
    ]
    scale_violations = [
        item
        for item in learned
        if item["category"] in ("stone", "embankment") and not (0.45 <= item["scale"] <= 4.5)
    ]
    clearance_violations = []
    for item in learned:
        if item["category"] not in LEARNED_ROUTE_CLEARANCE_CM:
            continue
        min_clearance = LEARNED_ROUTE_CLEARANCE_CM[item["category"]]
        clearance = _nearest_route_clearance(item["x"], item["y"], points=points)
        if clearance < min_clearance:
            clearance_violations.append(
                {
                    "label": item["label"],
                    "category": item["category"],
                    "clearance": round(clearance, 1),
                    "required": min_clearance,
                }
            )

    overlaps = []
    for index, a in enumerate(learned):
        for b in learned[index + 1 :]:
            radius = max(
                FOOTPRINT_RADIUS.get(a["category"], 120.0),
                FOOTPRINT_RADIUS.get(b["category"], 120.0),
            ) * 0.58
            dx = a["x"] - b["x"]
            dy = a["y"] - b["y"]
            if dx * dx + dy * dy < radius * radius:
                overlaps.append(
                    {
                        "a": a["label"],
                        "b": b["label"],
                        "categories": a["category"] + "," + b["category"],
                        "distance": round(math.sqrt(dx * dx + dy * dy), 1),
                    }
                )
                if len(overlaps) >= 20:
                    break
        if len(overlaps) >= 20:
            break

    return {
        "runtime_actor_count": runtime_actor_count,
        "road_counts": road_counts,
        "road_expected": road_expected,
        "road_mismatches": road_mismatches,
        "learned_counts": learned_counts,
        "learned_expected": learned_expected,
        "learned_mismatches": learned_mismatches,
        "pitch_roll_limit_violations": len(pitch_roll_violations),
        "scale_violations": len(scale_violations),
        "large_rock_clearance_violations": clearance_violations,
        "hard_overlap_samples": overlaps,
        "material_paths": dict(sorted(material_paths.items())),
        "pass": (
            runtime_actor_count == 1
            and not road_mismatches
            and not learned_mismatches
            and not pitch_roll_violations
            and not scale_violations
            and not clearance_violations
            and not overlaps
        ),
    }


def _runtime_output_spatial_summary(max_samples=8):
    rows = []
    for actor in _actors():
        label = _label(actor)
        is_runtime_road = any(label.startswith(prefix) for prefix in RUNTIME_ROAD_PREFIXES_BY_KIND.values())
        is_runtime_data = label.startswith("MCP_CubelessRuntimeRoadData_")
        if not is_runtime_road and not is_runtime_data:
            continue
        loc = actor.get_actor_location()
        rows.append(
            {
                "label": label,
                "x": float(loc.x),
                "y": float(loc.y),
                "z": float(loc.z),
            }
        )

    rows = sorted(rows, key=lambda item: item["label"])
    if not rows:
        return {
            "count": 0,
            "bounds": None,
            "centroid": None,
            "location_checksum": 0.0,
            "samples": [],
        }

    xs = [item["x"] for item in rows]
    ys = [item["y"] for item in rows]
    zs = [item["z"] for item in rows]
    checksum = 0.0
    for index, item in enumerate(rows):
        checksum += (index + 1) * (item["x"] * 0.0017 + item["y"] * 0.0023 + item["z"] * 0.00019)

    return {
        "count": len(rows),
        "bounds": {
            "min": [round(min(xs), 2), round(min(ys), 2), round(min(zs), 2)],
            "max": [round(max(xs), 2), round(max(ys), 2), round(max(zs), 2)],
        },
        "centroid": [
            round(sum(xs) / len(xs), 2),
            round(sum(ys) / len(ys), 2),
            round(sum(zs) / len(zs), 2),
        ],
        "location_checksum": round(checksum, 3),
        "samples": [
            {
                "label": item["label"],
                "location": [round(item["x"], 2), round(item["y"], 2), round(item["z"], 2)],
            }
            for item in rows[:max_samples]
        ],
    }


def _generate_runtime_road_validation_from_points(points, clear_superseded=False, save_assets=False):
    segments, total_length = _route_segments(points)
    if not segments:
        raise RuntimeError("Cannot generate runtime road validation without runtime spline segments")

    runtime_material_result = ensure_runtime_road_materials()
    core_mesh = _load_object(ASSET_PATHS["road_core_mesh"])
    rock_mesh = _load_object(ASSET_PATHS["learned_rock_mesh"])
    rock_mat = _load_object(ASSET_PATHS["learned_rock_material"])

    cleared_superseded = {"removed_count": 0}
    if clear_superseded:
        cleared_superseded = clear_superseded_road_validation_output(save=False)
    cleared = clear_runtime_road_validation_output(save=False)
    generated_counts = _generate_spline_mesh_road_layer(
        core_mesh,
        runtime_material_result["materials"],
        total_length,
        points,
        label_prefixes=RUNTIME_ROAD_PREFIXES_BY_KIND,
    )
    generated_learned_counts = _generate_runtime_learned_data(rock_mesh, rock_mat, total_length, points)
    organize_result = organize_outliner(save=False)
    validation = validate_runtime_road_validation_output(points=points)
    scene_state = collect_scene_state()
    runtime_asset_save = save_runtime_road_assets() if save_assets else None
    return {
        "route_length_cm": round(float(total_length), 2),
        "cleared_superseded": cleared_superseded,
        "cleared": cleared,
        "generated_counts": generated_counts,
        "generated_learned_counts": generated_learned_counts,
        "organize": organize_result,
        "validation": validation,
        "scene_state": scene_state,
        "spatial_summary": _runtime_output_spatial_summary(),
        "runtime_materials_created": runtime_material_result["created"],
        "runtime_asset_save": runtime_asset_save,
    }


def _offset_runtime_control_test_points(points):
    if len(points) < 4:
        raise RuntimeError("Runtime road control test needs at least 4 spline points")
    adjusted = [[float(value) for value in point] for point in points]
    center = max(1, min(len(adjusted) - 2, len(adjusted) // 2))
    before = adjusted[center - 1]
    after = adjusted[center + 1]
    dx = after[0] - before[0]
    dy = after[1] - before[1]
    length = max(math.sqrt(dx * dx + dy * dy), 0.001)
    normal = [-dy / length, dx / length]
    offsets = {
        center - 1: 420.0,
        center: 950.0,
        center + 1: 420.0,
    }
    for index, offset in offsets.items():
        adjusted[index][0] += normal[0] * offset
        adjusted[index][1] += normal[1] * offset
    return adjusted


def _point_delta_summary(before_points, after_points):
    deltas = []
    for before, after in zip(before_points, after_points):
        deltas.append(
            math.sqrt(
                (float(before[0]) - float(after[0])) ** 2
                + (float(before[1]) - float(after[1])) ** 2
                + (float(before[2]) - float(after[2])) ** 2
            )
        )
    return {
        "compared_count": min(len(before_points), len(after_points)),
        "point_count_before": len(before_points),
        "point_count_after": len(after_points),
        "max_delta_cm": round(max(deltas) if deltas else 0.0, 2),
        "avg_delta_cm": round(sum(deltas) / len(deltas), 2) if deltas else 0.0,
    }


def regenerate_runtime_road_from_actor(clear_superseded=False):
    blueprint_result = create_or_update_runtime_road_blueprint()
    runtime_material_result = ensure_runtime_road_materials()
    graph_result = create_or_update_runtime_road_pcg_graph_bridge()
    profile_result = write_runtime_road_control_profile()
    runtime_asset_save = save_runtime_road_assets()

    actor_result = _find_or_spawn_runtime_road_actor()
    actor = actor_result["actor"]
    runtime_spline = read_runtime_road_spline_points(create_if_missing=False)
    if runtime_spline["point_count"] < len(ROAD_CONTROL_POINTS):
        _set_actor_spline_points(actor, ROAD_CONTROL_POINTS)
        runtime_spline = read_runtime_road_spline_points(create_if_missing=False)

    regenerated = _generate_runtime_road_validation_from_points(
        runtime_spline["points"],
        clear_superseded=clear_superseded,
        save_assets=False,
    )
    report = {
        "level": _world_path(),
        "runtime_scope": "/Game/Cubeless/PCG/Runtime road Blueprint/materials/PCG bridge plus _MCP_Temp validation actors",
        "bookmark_policy": "bookmark 1/2 are user-owned and are not modified by runtime road regeneration",
        "blueprint": blueprint_result,
        "graph": graph_result,
        "runtime_materials_created": runtime_material_result["created"],
        "runtime_asset_save": runtime_asset_save,
        "profile": {
            "profile_path": profile_result["profile_path"],
            "profile": profile_result["profile"],
        },
        "runtime_actor": {
            "label": RUNTIME_ROAD_ACTOR_LABEL,
            "spawned": actor_result["spawned"],
            "removed_duplicates": actor_result["removed_duplicates"],
            "path": actor_result["actor_path"],
        },
        "runtime_spline": {
            "actor_label": runtime_spline["actor_label"],
            "component_name": runtime_spline["component_name"],
            "point_count": runtime_spline["point_count"],
            "segment_count": runtime_spline["segment_count"],
            "route_length_cm": runtime_spline["route_length_cm"],
        },
        "regenerated": regenerated,
        "pass": regenerated["validation"]["pass"],
        "next_gate": "replace the Python bridge with native PCG nodes or place this runtime road actor in a production level",
    }
    report_path = _saved_runtime_road_regenerate_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    unreal.log("CubelessRoadPCG runtime road regenerate: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def write_runtime_road_bridge_guard_report():
    """Record that the PCG bridge intentionally skipped legacy actor spawning."""
    try:
        runtime_spline = read_runtime_road_spline_points(create_if_missing=False)
        runtime_spline_summary = {
            "actor_label": runtime_spline["actor_label"],
            "actor_path": runtime_spline["actor_path"],
            "component_name": runtime_spline["component_name"],
            "component_path": runtime_spline["component_path"],
            "point_count": runtime_spline["point_count"],
            "segment_count": runtime_spline["segment_count"],
            "route_length_cm": runtime_spline["route_length_cm"],
        }
    except Exception as exc:
        runtime_spline_summary = {
            "error": str(exc),
            "actor_label": RUNTIME_ROAD_ACTOR_LABEL,
            "component_name": AUTHORING_SPLINE_NAME,
        }

    report = {
        "level": _world_path(),
        "mode": "native_pcg_guard",
        "runtime_scope": "/Game/Cubeless/PCG/Runtime bridge guard; no _MCP_Temp road strip actors spawned",
        "legacy_actor_generation_skipped": True,
        "blocked_legacy_prefixes": list(RUNTIME_ROAD_PREFIXES_BY_KIND.values()),
        "reason": (
            "The bridge previously spawned one independent SplineMeshActor per road strip. "
            "Those actors are useful for legacy validation, but they are not the final PCG road structure."
        ),
        "runtime_actor": {
            "label": RUNTIME_ROAD_ACTOR_LABEL,
            "spline_component": AUTHORING_SPLINE_NAME,
        },
        "runtime_spline": runtime_spline_summary,
        "native_graph_target": _runtime_road_native_graph_object_path(),
        "manual_legacy_validation": (
            "Call regenerate_runtime_road_from_actor(clear_superseded=False) directly from "
            "CubelessRoadPCG.py only when the legacy validation actors are intentionally needed."
        ),
        "pass": True,
        "next_gate": "Continue converting road strip generation and roadside placement into native PCG graph nodes.",
    }
    report_path = _saved_runtime_road_regenerate_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    unreal.log("CubelessRoadPCG runtime bridge guard: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def run_runtime_road_control_smoke_test():
    blueprint_result = create_or_update_runtime_road_blueprint()
    runtime_material_result = ensure_runtime_road_materials()
    profile_result = write_runtime_road_control_profile()
    runtime_asset_save = save_runtime_road_assets()
    actor_result = _find_or_spawn_runtime_road_actor()
    actor = actor_result["actor"]

    runtime_spline = read_runtime_road_spline_points(create_if_missing=False)
    if runtime_spline["point_count"] < len(ROAD_CONTROL_POINTS):
        _set_actor_spline_points(actor, ROAD_CONTROL_POINTS)
        runtime_spline = read_runtime_road_spline_points(create_if_missing=False)

    baseline_points = runtime_spline["points"]
    baseline = _generate_runtime_road_validation_from_points(
        baseline_points,
        clear_superseded=True,
        save_assets=False,
    )

    variant_points = _offset_runtime_control_test_points(baseline_points)
    variant_spline_set = _set_actor_spline_points(actor, variant_points)
    variant_spline = read_runtime_road_spline_points(create_if_missing=False)
    variant = _generate_runtime_road_validation_from_points(
        variant_spline["points"],
        clear_superseded=False,
        save_assets=False,
    )

    restore_spline_set = _set_actor_spline_points(actor, baseline_points)
    restored_spline = read_runtime_road_spline_points(create_if_missing=False)
    restored = _generate_runtime_road_validation_from_points(
        restored_spline["points"],
        clear_superseded=False,
        save_assets=False,
    )

    baseline_checksum = baseline["spatial_summary"]["location_checksum"]
    variant_checksum = variant["spatial_summary"]["location_checksum"]
    restored_checksum = restored["spatial_summary"]["location_checksum"]
    output_changed_delta = abs(variant_checksum - baseline_checksum)
    output_restored_delta = abs(restored_checksum - baseline_checksum)
    route_length_delta = abs(variant_spline["route_length_cm"] - runtime_spline["route_length_cm"])

    control_response = {
        "route_length_delta_cm": round(route_length_delta, 2),
        "variant_point_delta": _point_delta_summary(baseline_points, variant_spline["points"]),
        "restore_point_delta": _point_delta_summary(baseline_points, restored_spline["points"]),
        "output_checksum_delta_variant": round(output_changed_delta, 3),
        "output_checksum_delta_restored": round(output_restored_delta, 3),
        "route_changed": route_length_delta > 1.0,
        "output_changed": output_changed_delta > 1.0,
        "output_restored": output_restored_delta <= 1.0,
    }

    report = {
        "level": _world_path(),
        "runtime_scope": "/Game/Cubeless/PCG/Runtime road Blueprint/materials plus _MCP_Temp validation actors",
        "bookmark_policy": "bookmark 1/2 are user-owned and are not modified by this runtime control smoke test",
        "blueprint": blueprint_result,
        "runtime_asset_save": runtime_asset_save,
        "runtime_materials_created": runtime_material_result["created"],
        "profile": {
            "profile_path": profile_result["profile_path"],
            "profile": profile_result["profile"],
        },
        "runtime_actor": {
            "label": RUNTIME_ROAD_ACTOR_LABEL,
            "spawned": actor_result["spawned"],
            "removed_duplicates": actor_result["removed_duplicates"],
            "path": actor_result["actor_path"],
        },
        "baseline_spline": {
            "point_count": runtime_spline["point_count"],
            "segment_count": runtime_spline["segment_count"],
            "route_length_cm": runtime_spline["route_length_cm"],
        },
        "variant_spline_set": variant_spline_set,
        "variant_spline": {
            "point_count": variant_spline["point_count"],
            "segment_count": variant_spline["segment_count"],
            "route_length_cm": variant_spline["route_length_cm"],
        },
        "restore_spline_set": restore_spline_set,
        "restored_spline": {
            "point_count": restored_spline["point_count"],
            "segment_count": restored_spline["segment_count"],
            "route_length_cm": restored_spline["route_length_cm"],
        },
        "baseline": baseline,
        "variant": variant,
        "restored": restored,
        "control_response": control_response,
        "pass": (
            baseline["validation"]["pass"]
            and variant["validation"]["pass"]
            and restored["validation"]["pass"]
            and control_response["route_changed"]
            and control_response["output_changed"]
            and control_response["output_restored"]
        ),
        "next_gate": "wire this runtime control into a real production level or replace the Python generator with native PCG graph controls",
    }
    report_path = _saved_runtime_road_control_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    unreal.log("CubelessRoadPCG runtime road control smoke test: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def apply_spline_visual_road_tuning():
    spline_read = read_authoring_spline_points(create_if_missing=True)
    points = spline_read["points"]
    segments, total_length = _route_segments(points)
    if not segments:
        raise RuntimeError("Cannot tune visible road without authoring spline segments")

    material_result = ensure_tuned_road_materials()
    core_mesh = _load_object(ASSET_PATHS["road_core_mesh"])
    edge_mesh = _load_object(ASSET_PATHS["road_edge_mesh"])

    cleared = clear_visible_road_ribbon(save=False)
    generated_counts = _generate_visible_tuned_road_layer(
        core_mesh,
        edge_mesh,
        material_result["materials"],
        total_length,
        points,
    )
    organize_result = organize_outliner(save=False)
    visible_validation = validate_visible_road_tune(mode="organic")
    learned_validation = validate_scene()
    scene_state = collect_scene_state()

    report = {
        "level": _world_path(),
        "route_source": AUTHORING_ACTOR_LABEL + "." + AUTHORING_SPLINE_NAME,
        "bookmark_policy": "bookmark 1/2 are user-owned and are not modified by this visual tune step",
        "visual_goal": "dark forest soil road, softer irregular edge, less flat orange strip, more small dust/duff patches",
        "authoring_spline": {
            "actor_label": spline_read["actor_label"],
            "component_name": spline_read["component_name"],
            "point_count": spline_read["point_count"],
            "segment_count": spline_read["segment_count"],
            "route_length_cm": spline_read["route_length_cm"],
        },
        "materials_created": material_result["created"],
        "cleared": cleared,
        "generated_counts": generated_counts,
        "organize": organize_result,
        "visible_validation": visible_validation,
        "learned_validation": learned_validation,
        "scene_state": scene_state,
    }
    report_path = _saved_visual_tune_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    save_ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    report["save_ok"] = bool(save_ok)
    unreal.log("CubelessRoadPCG visual road tune: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def apply_spline_mesh_road_prototype():
    spline_read = read_authoring_spline_points(create_if_missing=True)
    points = spline_read["points"]
    segments, total_length = _route_segments(points)
    if not segments:
        raise RuntimeError("Cannot generate spline mesh road without authoring spline segments")

    material_result = ensure_tuned_road_materials()
    core_mesh = _load_object(ASSET_PATHS["road_core_mesh"])
    rock_mesh = _load_object(ASSET_PATHS["learned_rock_mesh"])
    rock_mat = _load_object(ASSET_PATHS["learned_rock_material"])

    cleared = clear_visible_road_ribbon(save=False)
    cleared_learned = clear_learned_road_data(save=False)
    generated_counts = _generate_spline_mesh_road_layer(
        core_mesh,
        material_result["materials"],
        total_length,
        points,
    )
    generated_learned_counts = _generate_visible_learned_data(rock_mesh, rock_mat, total_length, points)
    organize_result = organize_outliner(save=False)
    visible_validation = validate_visible_road_tune(mode="spline_mesh")
    learned_validation = validate_scene()
    scene_state = collect_scene_state()

    report = {
        "level": _world_path(),
        "route_source": AUTHORING_ACTOR_LABEL + "." + AUTHORING_SPLINE_NAME,
        "bookmark_policy": "bookmark 1/2 are user-owned and are not modified by this spline mesh prototype step",
        "visual_goal": "continuous dark forest-soil road generated from editable Road_SourceSpline using SplineMeshActor strips",
        "prototype_scope": "_MCP_Temp validation prototype; production /Game/Cubeless/PCG/Runtime promotion still requires user approval",
        "authoring_spline": {
            "actor_label": spline_read["actor_label"],
            "component_name": spline_read["component_name"],
            "point_count": spline_read["point_count"],
            "segment_count": spline_read["segment_count"],
            "route_length_cm": spline_read["route_length_cm"],
        },
        "materials_created": material_result["created"],
        "cleared": cleared,
        "cleared_learned": cleared_learned,
        "generated_counts": generated_counts,
        "generated_learned_counts": generated_learned_counts,
        "organize": organize_result,
        "visible_validation": visible_validation,
        "learned_validation": learned_validation,
        "scene_state": scene_state,
    }
    report_path = _saved_spline_mesh_prototype_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    save_ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    report["save_ok"] = bool(save_ok)
    unreal.log("CubelessRoadPCG spline mesh road prototype: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def apply_runtime_road_promotion_validation():
    blueprint_result = create_or_update_runtime_road_blueprint()
    runtime_material_result = ensure_runtime_road_materials()

    try:
        source_spline = read_authoring_spline_points(create_if_missing=False)
        source_points = source_spline["points"]
        source_label = source_spline["actor_label"] + "." + source_spline["component_name"]
    except Exception:
        source_points = ROAD_CONTROL_POINTS
        source_label = "ROAD_CONTROL_POINTS fallback"

    actor_result = _find_or_spawn_runtime_road_actor()
    actor = actor_result["actor"]
    runtime_spline_set = _set_actor_spline_points(actor, source_points)
    runtime_spline = read_runtime_road_spline_points(create_if_missing=False)
    if (
        runtime_spline["point_count"] != len(source_points)
        or abs(runtime_spline["route_length_cm"] - runtime_spline_set["wrapper_route_length_cm"]) > 1.0
    ):
        runtime_spline_set = _set_actor_spline_points(actor, source_points)
        runtime_spline = read_runtime_road_spline_points(create_if_missing=False)
    if runtime_spline["point_count"] != len(source_points):
        raise RuntimeError(
            "Runtime road spline point count mismatch after set: expected {} actual {}".format(
                len(source_points),
                runtime_spline["point_count"],
            )
        )
    points = runtime_spline["points"]
    segments, total_length = _route_segments(points)
    if not segments:
        raise RuntimeError("Cannot generate runtime road validation without runtime spline segments")

    core_mesh = _load_object(ASSET_PATHS["road_core_mesh"])
    rock_mesh = _load_object(ASSET_PATHS["learned_rock_mesh"])
    rock_mat = _load_object(ASSET_PATHS["learned_rock_material"])

    cleared_superseded = clear_superseded_road_validation_output(save=False)
    cleared = clear_runtime_road_validation_output(save=False)
    generated_counts = _generate_spline_mesh_road_layer(
        core_mesh,
        runtime_material_result["materials"],
        total_length,
        points,
        label_prefixes=RUNTIME_ROAD_PREFIXES_BY_KIND,
    )
    generated_learned_counts = _generate_runtime_learned_data(rock_mesh, rock_mat, total_length, points)
    organize_result = organize_outliner(save=False)
    validation = validate_runtime_road_validation_output(points=points)
    runtime_asset_save = save_runtime_road_assets()
    scene_state = collect_scene_state()

    report = {
        "level": _world_path(),
        "route_source": source_label,
        "runtime_scope": "/Game/Cubeless/PCG/Runtime road Blueprint/materials plus _MCP_Temp validation actors",
        "bookmark_policy": "bookmark 1/2 are user-owned and are not modified by this runtime promotion validation step",
        "blueprint": blueprint_result,
        "runtime_materials_created": runtime_material_result["created"],
        "runtime_actor": {
            "label": RUNTIME_ROAD_ACTOR_LABEL,
            "spawned": actor_result["spawned"],
            "removed_duplicates": actor_result["removed_duplicates"],
            "path": actor_result["actor_path"],
        },
        "runtime_spline_set": runtime_spline_set,
        "runtime_spline": {
            "actor_label": runtime_spline["actor_label"],
            "component_name": runtime_spline["component_name"],
            "point_count": runtime_spline["point_count"],
            "segment_count": runtime_spline["segment_count"],
            "route_length_cm": runtime_spline["route_length_cm"],
        },
        "cleared_superseded": cleared_superseded,
        "cleared": cleared,
        "generated_counts": generated_counts,
        "generated_learned_counts": generated_learned_counts,
        "organize": organize_result,
        "validation": validation,
        "runtime_asset_save": runtime_asset_save,
        "scene_state": scene_state,
        "next_gate": "saving or placing this road runtime into the real field level is a separate production placement step",
    }
    report_path = _saved_runtime_road_report_path()
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    report["report_path"] = report_path
    unreal.log("CubelessRoadPCG runtime road promotion validation: {}".format(json.dumps(report, ensure_ascii=False)))
    return report


def write_wrapper_spec_json(output_path=None):
    output_path = output_path or _saved_spec_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    spec = {
        "spec_version": SPEC_VERSION,
        "source_level": LEVEL_PATH,
        "current_level": _world_path(),
        "bookmark_policy": {
            "bookmark_1": "user-owned overview camera; do not overwrite",
            "bookmark_2": "user-owned ground-quality camera; do not overwrite",
            "automation": "use explicit viewport/camera capture paths without saving bookmark slots",
        },
        "source": {
            "electric_dreams_learned_data": ASSET_PATHS["electric_dreams_source_data"],
            "note": "This is a Cubeless wrapper spec transferred from ED learned data, not native ED road graph output.",
        },
        "route": {
            "control_points": ROAD_CONTROL_POINTS,
            "dominant_axis_degrees": 36.31,
        },
        "authoring_handle": {
            "blueprint": _authoring_blueprint_path(),
            "level_actor_label": AUTHORING_ACTOR_LABEL,
            "level_folder": AUTHORING_ACTOR_FOLDER,
            "spline_component": AUTHORING_SPLINE_NAME,
            "report_path": _saved_authoring_report_path(),
            "spline_regen_report_path": _saved_regen_report_path(AUTHORING_SPLINE_REGEN_REPORT_NAME),
            "visual_tune_report_path": _saved_visual_tune_report_path(),
            "spline_mesh_prototype_report_path": _saved_spline_mesh_prototype_report_path(),
            "runtime_road_report_path": _saved_runtime_road_report_path(),
            "runtime_road_regenerate_report_path": _saved_runtime_road_regenerate_report_path(),
            "runtime_road_control_report_path": _saved_runtime_road_control_report_path(),
            "runtime_road_control_profile_path": _saved_runtime_road_control_profile_path(),
            "runtime_road_pcg_graph": _runtime_road_pcg_graph_object_path(),
            "runtime_road_native_graph": _runtime_road_native_graph_object_path(),
            "runtime_road_native_graph_report_path": _saved_runtime_road_native_graph_report_path(),
            "note": "This temporary handle stores the same route as ROAD_CONTROL_POINTS for future spline-driven PCG promotion.",
        },
        "assets": dict(ASSET_PATHS),
        "expected_counts": dict(EXPECTED_COUNTS),
        "rules": {
            "pitch_roll_max_degrees": 5.0,
            "yaw_randomization": "allowed",
            "stone_scale_range": [0.5, 4.0],
            "large_rock_road_clearance_cm": {
                "stone": 1700.0,
                "embankment": 2250.0,
            },
            "large_rock_generation_lateral_cm": {
                "stone": [1850.0, 3900.0],
                "embankment": [2400.0, 4700.0],
            },
            "grass_overlap_relaxation": "grass-only; do not relax tree/rock overlap",
            "road_gradient": "grass density decreases as distance to road approaches zero",
        },
        "scene_state": collect_scene_state(),
        "validation": validate_scene(),
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(spec, handle, ensure_ascii=False, indent=2)
    return {"spec_path": output_path, "spec": spec}


def run_bookmark_safe_wrapper_step():
    organize_result = organize_outliner(save=False)
    scene_state = collect_scene_state()
    validation = validate_scene()
    spec_result = write_wrapper_spec_json()
    save_ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    result = {
        "organize": organize_result,
        "scene_state": scene_state,
        "validation": validation,
        "spec_path": spec_result["spec_path"],
        "save_ok": bool(save_ok),
    }
    unreal.log("CubelessRoadPCG wrapper step: {}".format(json.dumps(result, ensure_ascii=False)))
    return result


def _count_by(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))
