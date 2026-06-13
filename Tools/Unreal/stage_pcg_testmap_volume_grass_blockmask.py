"""Stage a TestMap PCG volume-owned grass fixture with native block masking.

This is an isolated productionization test for broad grass ownership:
PCGVolume owns the grass, road and block masks are read as PCG inputs, and
StaticMeshSpawner mesh/material come from actor properties.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIBLING_PYTHON_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless" / "Python"

if str(SIBLING_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(SIBLING_PYTHON_ROOT))

try:
    from unreal_mcp_server import UnrealConnection  # type: ignore  # noqa: E402
except ModuleNotFoundError:

    class UnrealConnection:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.host = os.environ.get("UNREAL_MCP_HOST", "127.0.0.1")
            self.port = int(os.environ.get("UNREAL_MCP_PORT", "55557"))
            self.timeout = int(os.environ.get("UNREAL_MCP_RESPONSE_TIMEOUT_SECONDS", "240"))

        def send_command(
            self,
            command: str,
            params: dict[str, Any] | None = None,
        ) -> dict[str, Any] | None:
            payload = {"type": command, "params": params or {}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.connect((self.host, self.port))
                sock.sendall(json.dumps(payload).encode("utf-8"))
                chunks: list[bytes] = []
                while True:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    try:
                        return json.loads(b"".join(chunks).decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
            return json.loads(b"".join(chunks).decode("utf-8")) if chunks else None


UNREAL_CODE_TEMPLATE = r"""
import json
import math
import os
import time

import unreal


TEST_LEVEL_PATH = "/Game/Cubeless/TestMap"
REPORT_NAME = "pcg_testmap_volume_grass_blockmask_report.json"

GRAPH_FOLDER = "/Game/_MCP_Temp/PCG/Graphs"
GRAPH_NAME = "PCG_Cubeless_TestMap_VolumeGrassBlockMask_MCP"
GRAPH_OBJECT = GRAPH_FOLDER + "/" + GRAPH_NAME + "." + GRAPH_NAME

BP_FOLDER = "/Game/_MCP_Temp/PCG/Blueprints"
BP_NAME = "BP_Cubeless_TestMap_VolumeGrassSource_MCP"
BP_OBJECT_PATH = BP_FOLDER + "/" + BP_NAME
BP_CLASS_PATH = BP_OBJECT_PATH + "." + BP_NAME + "_C"

SOURCE_LABEL = "MCP_TestMap_VolumeGrass_Source"
VOLUME_LABEL = "MCP_TestMap_VolumeGrass_Review"
ROAD_LABEL = "MCP_TestMap_VolumeGrass_RoadSource"
ROAD_MASK_LABEL = "MCP_TestMap_RoadClearance_Mask"
BLOCK_LABEL = "MCP_TestMap_Block_StaticMesh"

SOURCE_ACTOR_TAG = "MCPTestMapVolumeGrassSource"
ROAD_ACTOR_TAG = "MCPTestMapVolumeGrassRoad"
ROAD_SPLINE_TAG = "MCPTestMapVolumeGrassSpline"
ROAD_MASK_TAG = "MCPTestMapRoadClearanceMask"
BLOCK_TAG = "block"

DYNAMIC_MESH_ATTR = "DynamicMeshPath"
DYNAMIC_MATERIAL_SLOT0_ATTR = "DynamicMaterialSlot0"
ROAD_DISTANCE_ATTR = "RoadClearanceDistance"
BLOCK_DISTANCE_ATTR = "BlockClearanceDistance"
ROAD_MASK_SAFETY_CM = 420.0
GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)
GRASS_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_GrassMedium_ForestBalanced.MI_Cubeless_PCG_GrassMedium_ForestBalanced"
)
ROAD_BP_CLASS_PATH = (
    "/Game/Cubeless/PCG/Runtime/Blueprints/"
    "BP_Cubeless_PCG_ForestRoadRuntime.BP_Cubeless_PCG_ForestRoadRuntime_C"
)
CUBE_MESH = "/Engine/BasicShapes/Cube.Cube"
BASIC_SHAPE_MATERIAL = "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"
HELPER_MATERIAL_FOLDER = "/Game/_MCP_Temp/PCG/Materials"
HELPER_INVISIBLE_MATERIAL = HELPER_MATERIAL_FOLDER + "/M_MCP_TestMap_HelperInvisible"

POINTS_PER_SQM = __POINTS_PER_SQM__
ROAD_CLEARANCE_CM = __ROAD_CLEARANCE_CM__
ROAD_FILTER_EXTRA_CLEARANCE_CM = 140.0
BLOCK_CLEARANCE_CM = __BLOCK_CLEARANCE_CM__
SETTLE_SECONDS = __SETTLE_SECONDS__
SAVE_ASSETS = __SAVE_ASSETS__
SAVE_MAP = __SAVE_MAP__
ENABLE_ROAD_FILTER = __ENABLE_ROAD_FILTER__
ENABLE_BLOCK_FILTER = __ENABLE_BLOCK_FILTER__


def _get_editor_world():
    subsystem_cls = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_cls:
        try:
            subsystem = unreal.get_editor_subsystem(subsystem_cls)
            world = subsystem.get_editor_world() if subsystem else None
            if world:
                return world
        except Exception:
            pass
    return unreal.EditorLevelLibrary.get_editor_world()


def _load_test_map():
    world = _get_editor_world()
    if not world or not world.get_path_name().startswith(TEST_LEVEL_PATH + "."):
        unreal.EditorLevelLibrary.load_level(TEST_LEVEL_PATH)
    return _get_editor_world()


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


def _find_actor(label):
    for actor in _all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _load_asset(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        asset = unreal.load_object(None, path)
    return asset


def _object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _tags(obj, prop):
    try:
        return [str(tag) for tag in obj.get_editor_property(prop)]
    except Exception:
        return []


def _has_tag_token(obj, prop, token):
    needle = token.lower()
    return any(needle in tag.lower() for tag in _tags(obj, prop))


def _ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _ensure_invisible_helper_material():
    material = _load_asset(HELPER_INVISIBLE_MATERIAL)
    if not material:
        _ensure_directory(HELPER_MATERIAL_FOLDER)
        factory_cls = getattr(unreal, "MaterialFactoryNew", None)
        if not factory_cls:
            return None
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_MCP_TestMap_HelperInvisible",
            HELPER_MATERIAL_FOLDER,
            unreal.Material,
            factory_cls(),
        )
    if not material:
        return None
    try:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property("two_sided", True)
        lib = unreal.MaterialEditingLibrary
        lib.delete_all_material_expressions(material)
        opacity = lib.create_material_expression(material, unreal.MaterialExpressionConstant, -360, 0)
        opacity.set_editor_property("r", 0.0)
        lib.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
        base = lib.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -360, -140)
        base.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
        lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
        lib.recompile_material(material)
        if SAVE_ASSETS:
            unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    except Exception:
        pass
    return material


def _blueprint_variable_exists(blueprint_path, variable_name):
    try:
        data = unreal.BlueprintEditorLibrary.get_blueprint_variable_list(blueprint_path)
        for item in data:
            if str(item.var_name) == variable_name:
                return True
    except Exception:
        pass
    return False


def _set_variable_editable(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_expose_on_spawn(
            blueprint,
            variable_name,
            bool(value),
        )
    except Exception:
        pass
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(
            blueprint,
            variable_name,
            bool(value),
        )
    except Exception:
        pass


def _ensure_source_blueprint():
    _ensure_directory(BP_FOLDER)
    blueprint = unreal.load_object(None, BP_OBJECT_PATH + "." + BP_NAME)
    created = False
    if not blueprint:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("ParentClass", unreal.Actor)
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            BP_NAME,
            BP_FOLDER,
            unreal.Blueprint,
            factory,
        )
        created = bool(blueprint)
    if not blueprint:
        raise RuntimeError("Failed to create/load source Blueprint: " + BP_OBJECT_PATH)

    bool_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    mesh_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.StaticMesh.static_class())
    material_type = unreal.BlueprintEditorLibrary.get_object_reference_type(
        unreal.MaterialInterface.static_class()
    )
    specs = [
        ("UseGrassMeshOverride", bool_type),
        ("GrassMesh", mesh_type),
        ("UseGrassMaterialOverride", bool_type),
        ("GrassMaterial", material_type),
    ]
    added = []
    for variable_name, pin_type in specs:
        if _blueprint_variable_exists(BP_OBJECT_PATH, variable_name):
            continue
        if not unreal.BlueprintEditorLibrary.add_member_variable(blueprint, variable_name, pin_type):
            raise RuntimeError("Failed to add Blueprint variable: " + variable_name)
        added.append(variable_name)
    for variable_name, _pin_type in specs:
        _set_variable_editable(blueprint, variable_name, True)

    blueprint.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    cls = unreal.EditorAssetLibrary.load_blueprint_class(BP_OBJECT_PATH)
    if not cls:
        raise RuntimeError("Failed to load source Blueprint class: " + BP_CLASS_PATH)
    cdo = unreal.get_default_object(cls)
    cdo.modify()
    cdo.set_editor_property("UseGrassMeshOverride", True)
    cdo.set_editor_property("GrassMesh", _load_asset(GRASS_MESH))
    cdo.set_editor_property("UseGrassMaterialOverride", True)
    cdo.set_editor_property("GrassMaterial", _load_asset(GRASS_MATERIAL))
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False)) if SAVE_ASSETS else False
    return {
        "blueprint": BP_OBJECT_PATH,
        "class": BP_CLASS_PATH,
        "created": created,
        "added_variables": added,
        "saved": saved,
    }


def _landscape_bounds():
    landscapes = []
    for actor in _all_level_actors():
        if actor.get_class().get_name() in ("Landscape", "LandscapeProxy"):
            landscapes.append(actor)
    if not landscapes:
        return {
            "origin": unreal.Vector(0.0, 0.0, 0.0),
            "extent": unreal.Vector(5000.0, 5000.0, 1000.0),
            "source": "fallback",
        }
    origin, extent = landscapes[0].get_actor_bounds(False)
    return {"origin": origin, "extent": extent, "source": _actor_label(landscapes[0])}


def _fixture_layout():
    bounds = _landscape_bounds()
    origin = bounds["origin"]
    extent = bounds["extent"]
    size_x = max(2500.0, min(float(extent.x) * 0.8, 7000.0))
    size_y = max(2500.0, min(float(extent.y) * 0.8, 7000.0))
    center = unreal.Vector(float(origin.x), float(origin.y), float(origin.z) + 150.0)
    ground_z = float(origin.z + extent.z - 100.0)
    road_y = center.y - size_y * 0.30
    return {
        "landscape": {
            "source": bounds["source"],
            "origin": [round(origin.x, 3), round(origin.y, 3), round(origin.z, 3)],
            "extent": [round(extent.x, 3), round(extent.y, 3), round(extent.z, 3)],
        },
        "center": center,
        "ground_z": ground_z,
        "grid_extents": unreal.Vector(size_x, size_y, 12000.0),
        "volume_scale": unreal.Vector(max(size_x / 100.0, 40.0), max(size_y / 100.0, 40.0), 120.0),
        "road_a": unreal.Vector(center.x - size_x * 0.42, road_y, ground_z + 10.0),
        "road_b": unreal.Vector(center.x + size_x * 0.42, road_y, ground_z + 10.0),
        "block": unreal.Vector(center.x + size_x * 0.30, center.y + size_y * 0.32, ground_z),
        "camera": unreal.Vector(center.x - size_x * 0.52, center.y - size_y * 0.72, center.z + 2200.0),
    }


def _pin_label(pin):
    try:
        return str(pin.get_editor_property("properties").get_editor_property("label"))
    except Exception:
        try:
            return pin.get_name()
        except Exception:
            return str(pin)


def _add_node(graph, settings_cls, title, x, y):
    created = graph.add_node_of_type(settings_cls.static_class())
    node = created[0] if isinstance(created, tuple) else created
    try:
        node.set_editor_property("node_title", title)
    except Exception:
        try:
            node.node_title = title
        except Exception:
            pass
    try:
        node.set_node_position(int(x), int(y))
    except Exception:
        pass
    return node


def _add_edge(graph, from_node, to_node, from_pin="Out", to_pin="In"):
    try:
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


def _selector(attribute_name, selector_cls):
    selector = selector_cls()
    selector.import_text('(AttributeName="{}")'.format(attribute_name))
    return selector


def _selector_import(settings, prop, text):
    selector = settings.get_editor_property(prop)
    selector.import_text("PCGBegin({})PCGEnd".format(text))
    settings.set_editor_property(prop, selector)


def _constant(metadata_type, value):
    constant = unreal.PCGMetadataTypesConstantStruct()
    constant.set_editor_property("type", metadata_type)
    if metadata_type == unreal.PCGMetadataTypes.DOUBLE:
        constant.set_editor_property("double_value", float(value))
    elif metadata_type == unreal.PCGMetadataTypes.FLOAT:
        constant.set_editor_property("float_value", float(value))
    elif metadata_type == unreal.PCGMetadataTypes.BOOLEAN:
        constant.set_editor_property("bool_value", bool(value))
    else:
        constant.set_editor_property("double_value", float(value))
    return constant


def _grid_cell_size_cm():
    density = max(float(POINTS_PER_SQM), 0.0001)
    return max(150.0, min(1400.0, 100.0 / math.sqrt(density)))


def _configure_get_landscape(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_CLASS)
    landscape_cls = getattr(unreal, "LandscapeProxy", None) or getattr(unreal, "Landscape", None)
    if landscape_cls:
        actor_selector.set_editor_property("actor_selection_class", landscape_cls.static_class())
    actor_selector.set_editor_property("select_multiple", True)
    actor_selector.set_editor_property("must_overlap_self", True)
    settings.set_editor_property("actor_selector", actor_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("track_actors_only_within_bounds", True)
    try:
        settings.set_editor_property("ignore_pcg_generated_components", True)
    except Exception:
        pass


def _configure_grid(node, layout):
    settings = node.get_settings()
    cell = _grid_cell_size_cm()
    settings.set_editor_property("grid_extents", layout["grid_extents"])
    settings.set_editor_property("cell_size", unreal.Vector(cell, cell, 100000.0))
    settings.set_editor_property("coordinate_space", unreal.PCGCoordinateSpace.LOCAL_COMPONENT)
    settings.set_editor_property("set_points_bounds", True)
    settings.set_editor_property("cull_points_outside_volume", False)
    settings.set_editor_property("point_steepness", 0.5)
    settings.set_editor_property("seed", 6132026)
    try:
        settings.set_editor_property("point_position", unreal.PCGPointPosition.CELL_CENTER)
    except Exception:
        pass


def _configure_projection(node):
    settings = node.get_settings()
    params = settings.get_editor_property("projection_params")
    params.set_editor_property("project_positions", True)
    params.set_editor_property("project_rotations", True)
    params.set_editor_property("project_scales", False)
    settings.set_editor_property("projection_params", params)
    settings.set_editor_property("force_collapse_to_point", False)
    settings.set_editor_property("keep_zero_density_points", False)


def _configure_surface_sampler(node):
    settings = node.get_settings()
    settings.set_editor_property("points_per_squared_meter", float(POINTS_PER_SQM))
    settings.set_editor_property("point_extents", unreal.Vector(45.0, 45.0, 90.0))
    settings.set_editor_property("point_steepness", 0.5)
    settings.set_editor_property("keep_zero_density_points", False)
    settings.set_editor_property("seed", 6132028)
    try:
        settings.set_editor_property("apply_density_to_points", True)
    except Exception:
        pass


def _configure_point_extents(node):
    settings = node.get_settings()
    try:
        settings.set_editor_property("mode", unreal.PCGPointExtentsModifierMode.SET)
    except Exception:
        pass
    settings.set_editor_property("extents", unreal.Vector(45.0, 45.0, 90.0))


def _configure_get_road_spline(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", ROAD_ACTOR_TAG)
    actor_selector.set_editor_property("select_multiple", False)
    actor_selector.set_editor_property("ignore_self_and_children", False)
    settings.set_editor_property("actor_selector", actor_selector)
    component_selector = settings.get_editor_property("component_selector")
    component_selector.set_editor_property("component_selection", unreal.PCGComponentSelection.BY_TAG)
    component_selector.set_editor_property("component_selection_tag", ROAD_SPLINE_TAG)
    settings.set_editor_property("component_selector", component_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("components_must_overlap_self", False)
    settings.set_editor_property("track_actors_only_within_bounds", False)


def _configure_spline_sampler(node):
    settings = node.get_settings()
    params = settings.get_editor_property("sampler_params")
    params.set_editor_property("dimension", unreal.PCGSplineSamplingDimension.ON_SPLINE)
    params.set_editor_property("mode", unreal.PCGSplineSamplingMode.DISTANCE)
    params.set_editor_property("distance_increment", 120.0)
    params.set_editor_property("subdivisions_per_segment", 8)
    params.set_editor_property("compute_distance", True)
    params.set_editor_property("compute_segment_index", True)
    settings.set_editor_property("sampler_params", params)


def _configure_get_road_mask_data(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", ROAD_MASK_TAG)
    actor_selector.set_editor_property("select_multiple", True)
    actor_selector.set_editor_property("ignore_self_and_children", False)
    settings.set_editor_property("actor_selector", actor_selector)
    component_selector = settings.get_editor_property("component_selector")
    component_selector.set_editor_property("component_selection", unreal.PCGComponentSelection.BY_TAG)
    component_selector.set_editor_property("component_selection_tag", ROAD_MASK_TAG)
    settings.set_editor_property("component_selector", component_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("track_actors_only_within_bounds", False)
    try:
        settings.set_editor_property("also_output_single_point_data", True)
        settings.set_editor_property("merge_single_point_data", True)
    except Exception:
        pass


def _configure_get_block_data(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", BLOCK_TAG)
    actor_selector.set_editor_property("select_multiple", True)
    actor_selector.set_editor_property("ignore_self_and_children", False)
    settings.set_editor_property("actor_selector", actor_selector)
    component_selector = settings.get_editor_property("component_selector")
    component_selector.set_editor_property("component_selection", unreal.PCGComponentSelection.BY_TAG)
    component_selector.set_editor_property("component_selection_tag", BLOCK_TAG)
    settings.set_editor_property("component_selector", component_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("track_actors_only_within_bounds", False)
    try:
        settings.set_editor_property("also_output_single_point_data", True)
        settings.set_editor_property("merge_single_point_data", True)
    except Exception:
        pass


def _configure_difference(node):
    settings = node.get_settings()
    try:
        settings.set_editor_property("mode", unreal.PCGDifferenceMode.INFERRED)
    except Exception:
        pass
    try:
        settings.set_editor_property("keep_zero_density_points", False)
    except Exception:
        pass


def _configure_distance(node, attr, maximum, target_shape):
    settings = node.get_settings()
    settings.set_editor_property("output_to_attribute", True)
    settings.set_editor_property("output_attribute", _selector(attr, unreal.PCGAttributePropertySelector))
    settings.set_editor_property("maximum_distance", float(maximum))
    settings.set_editor_property("set_density", False)
    settings.set_editor_property("source_shape", unreal.PCGDistanceShape.CENTER)
    settings.set_editor_property("target_shape", target_shape)


def _configure_filter(node, attr, threshold):
    settings = node.get_settings()
    settings.set_editor_property(
        "target_attribute",
        _selector(attr, unreal.PCGAttributePropertyInputSelector),
    )
    settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.GREATER_OR_EQUAL)
    settings.set_editor_property("use_constant_threshold", True)
    settings.set_editor_property("attribute_types", _constant(unreal.PCGMetadataTypes.DOUBLE, threshold))
    settings.set_editor_property("generate_output_data_even_if_empty", True)
    try:
        settings.set_editor_property("warn_on_data_missing_attribute", False)
    except Exception:
        pass


def _configure_get_actor_property(node, property_name, output_attr):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", SOURCE_ACTOR_TAG)
    actor_selector.set_editor_property("select_multiple", False)
    actor_selector.set_editor_property("ignore_self_and_children", False)
    settings.set_editor_property("actor_selector", actor_selector)
    settings.set_editor_property("property_name", property_name)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("force_object_and_struct_extraction", False)
    settings.set_editor_property("sanitize_output_attribute_name", True)
    _selector_import(settings, "output_attribute_name", output_attr)


def _configure_copy_attr(node, source_attr, target_attr):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    _selector_import(settings, "input_source", source_attr)
    _selector_import(settings, "output_target", target_attr)


def _configure_transform(node):
    settings = node.get_settings()
    settings.set_editor_property("absolute_rotation", False)
    settings.set_editor_property("absolute_scale", False)
    settings.set_editor_property("uniform_scale", True)
    settings.set_editor_property("rotation_min", _make_rotator(0.0, 0.0, 0.0))
    settings.set_editor_property("rotation_max", _make_rotator(0.0, 359.0, 0.0))
    settings.set_editor_property("scale_min", unreal.Vector(0.72, 0.72, 0.84))
    settings.set_editor_property("scale_max", unreal.Vector(1.28, 1.28, 1.12))
    settings.set_editor_property("recompute_seed", True)
    settings.set_editor_property("seed", 6132027)


def _configure_by_attribute_spawner(node):
    settings = node.get_settings()
    settings.set_editor_property("allow_descriptor_changes", True)
    settings.set_mesh_selector_type(unreal.PCGMeshSelectorByAttribute.static_class())
    params = settings.get_editor_property("mesh_selector_parameters")
    params.set_editor_property("attribute_name", DYNAMIC_MESH_ATTR)
    params.set_editor_property("use_attribute_material_overrides", True)
    params.set_editor_property("material_override_attributes", [DYNAMIC_MATERIAL_SLOT0_ATTR])
    try:
        settings.set_editor_property("synchronous_load", True)
        settings.set_editor_property("apply_mesh_bounds_to_points", True)
    except Exception:
        pass


def _node_summary(node):
    try:
        settings_class = node.get_settings().get_class().get_name()
    except Exception:
        settings_class = ""
    try:
        title = str(node.get_editor_property("node_title"))
    except Exception:
        title = str(getattr(node, "node_title", ""))
    return {
        "node": node.get_name(),
        "title": title,
        "settings_class": settings_class,
        "input_pins": [
            {"label": _pin_label(pin), "connected": bool(pin.is_connected())}
            for pin in getattr(node, "input_pins", [])
        ],
        "output_pins": [
            {"label": _pin_label(pin), "connected": bool(pin.is_connected())}
            for pin in getattr(node, "output_pins", [])
        ],
    }


def _create_or_update_graph(layout):
    _ensure_directory(GRAPH_FOLDER)
    graph = unreal.load_object(None, GRAPH_OBJECT)
    created = False
    if not graph:
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            GRAPH_NAME,
            GRAPH_FOLDER,
            unreal.PCGGraph,
            unreal.PCGGraphFactory(),
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load graph: " + GRAPH_OBJECT)
    for node in list(graph.nodes):
        try:
            graph.remove_node(node)
        except Exception:
            pass

    nodes = {
        "landscape": _add_node(graph, unreal.PCGGetLandscapeSettings, "Get TestMap Landscape", -1500, 0),
        "surface": _add_node(graph, unreal.PCGSurfaceSamplerSettings, "Sample Volume-Owned Grass On Landscape", -1160, 0),
        "get_mesh": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor GrassMesh", 340, -360),
        "copy_mesh": _add_node(graph, unreal.PCGCopyAttributesSettings, "Copy GrassMesh To DynamicMeshPath", 680, -80),
        "get_material": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor GrassMaterial", 680, -360),
        "copy_material": _add_node(graph, unreal.PCGCopyAttributesSettings, "Copy GrassMaterial To DynamicMaterialSlot0", 1020, -80),
        "transform": _add_node(graph, unreal.PCGTransformPointsSettings, "Randomize Grass Yaw And Scale", 1360, 0),
        "spawn": _add_node(graph, unreal.PCGStaticMeshSpawnerSettings, "Spawn Actor-Property Grass", 1700, 0),
    }
    if ENABLE_ROAD_FILTER:
        nodes["road_spline"] = _add_node(graph, unreal.PCGGetSplineSettings, "Get Road Source Spline", -680, -360)
        nodes["road_reference_points"] = _add_node(graph, unreal.PCGSplineSamplerSettings, "Sample Road Clearance Reference Points", -340, -360)
        nodes["road_distance"] = _add_node(graph, unreal.PCGDistanceSettings, "Compute RoadClearanceDistance", -340, 0)
        nodes["road_filter"] = _add_node(graph, unreal.PCGAttributeFilteringSettings, "Keep Outside Road Clearance", 0, 0)
    if ENABLE_BLOCK_FILTER:
        nodes["block"] = _add_node(graph, unreal.PCGDataFromActorSettings, "Get block-tagged StaticMesh", -340, -360)
        nodes["block_distance"] = _add_node(graph, unreal.PCGDistanceSettings, "Compute BlockClearanceDistance", 0, 0)
        nodes["block_filter"] = _add_node(graph, unreal.PCGAttributeFilteringSettings, "Keep Outside Block Bounds", 340, 0)
    _configure_get_landscape(nodes["landscape"])
    _configure_surface_sampler(nodes["surface"])
    if ENABLE_ROAD_FILTER:
        _configure_get_road_spline(nodes["road_spline"])
        _configure_spline_sampler(nodes["road_reference_points"])
        _configure_distance(nodes["road_distance"], ROAD_DISTANCE_ATTR, 20000.0, unreal.PCGDistanceShape.CENTER)
        _configure_filter(nodes["road_filter"], ROAD_DISTANCE_ATTR, ROAD_CLEARANCE_CM + ROAD_FILTER_EXTRA_CLEARANCE_CM)
    if ENABLE_BLOCK_FILTER:
        _configure_get_block_data(nodes["block"])
        _configure_distance(nodes["block_distance"], BLOCK_DISTANCE_ATTR, 20000.0, unreal.PCGDistanceShape.BOX_BOUNDS)
        _configure_filter(nodes["block_filter"], BLOCK_DISTANCE_ATTR, BLOCK_CLEARANCE_CM)
    _configure_get_actor_property(nodes["get_mesh"], "GrassMesh", "GrassMesh")
    _configure_copy_attr(nodes["copy_mesh"], "GrassMesh", DYNAMIC_MESH_ATTR)
    _configure_get_actor_property(nodes["get_material"], "GrassMaterial", "GrassMaterial")
    _configure_copy_attr(nodes["copy_material"], "GrassMaterial", DYNAMIC_MATERIAL_SLOT0_ATTR)
    _configure_transform(nodes["transform"])
    _configure_by_attribute_spawner(nodes["spawn"])

    edges = [
        _add_edge(graph, graph.get_input_node(), nodes["surface"], "Out", "Bounding Shape"),
        _add_edge(graph, nodes["landscape"], nodes["surface"], "Out", "Surface"),
        _add_edge(graph, nodes["surface"], nodes["copy_mesh"], "Out", "Target"),
        _add_edge(graph, nodes["get_mesh"], nodes["copy_mesh"], "Out", "Source"),
        _add_edge(graph, nodes["copy_mesh"], nodes["copy_material"], "Out", "Target"),
        _add_edge(graph, nodes["get_material"], nodes["copy_material"], "Out", "Source"),
    ]
    current_node = nodes["copy_material"]
    current_pin = "Out"
    if ENABLE_ROAD_FILTER:
        edges.extend(
            [
                _add_edge(graph, current_node, nodes["road_distance"], current_pin, "Source"),
                _add_edge(graph, nodes["road_spline"], nodes["road_reference_points"], "Out", "Spline"),
                _add_edge(graph, nodes["road_reference_points"], nodes["road_distance"], "Out", "Target"),
                _add_edge(graph, nodes["road_distance"], nodes["road_filter"], "Out", "In"),
            ]
        )
        current_node = nodes["road_filter"]
        current_pin = "InsideFilter"
    if ENABLE_BLOCK_FILTER:
        edges.extend(
            [
                _add_edge(graph, current_node, nodes["block_distance"], current_pin, "Source"),
                _add_edge(graph, nodes["block"], nodes["block_distance"], "Out", "Target"),
                _add_edge(graph, nodes["block_distance"], nodes["block_filter"], "Out", "In"),
            ]
        )
        current_node = nodes["block_filter"]
        current_pin = "InsideFilter"
    edges.extend(
        [
            _add_edge(graph, current_node, nodes["transform"], current_pin, "In"),
            _add_edge(graph, nodes["transform"], nodes["spawn"], "Out", "In"),
            _add_edge(graph, nodes["spawn"], graph.get_output_node(), "Out", "Out"),
        ]
    )
    try:
        graph.description = (
            "Temporary TestMap graph for volume-owned grass productionization. "
            "SurfaceSampler points are filtered by road-clearance and block StaticMesh "
            "distance attributes, then spawn grass from "
            "actor-property mesh/material attributes."
        )
        graph.get_input_node().set_node_position(-1980, 0)
        graph.get_output_node().set_node_position(2040, 0)
    except Exception:
        pass
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(graph, False)) if SAVE_ASSETS else False
    return {
        "graph": graph,
        "graph_path": GRAPH_OBJECT,
        "created": created,
        "saved": saved,
        "points_per_squared_meter": POINTS_PER_SQM,
        "grid_cell_size_cm": round(_grid_cell_size_cm(), 3),
        "road_clearance_cm": ROAD_CLEARANCE_CM,
        "road_filter_extra_clearance_cm": ROAD_FILTER_EXTRA_CLEARANCE_CM,
        "road_mask_safety_cm": ROAD_MASK_SAFETY_CM,
        "block_clearance_cm": BLOCK_CLEARANCE_CM,
        "road_filter_enabled": ENABLE_ROAD_FILTER,
        "block_filter_enabled": ENABLE_BLOCK_FILTER,
        "road_filter_mode": "PCGGetSplineSettings road source + PCGSplineSamplerSettings reference points + PCGDistanceSettings CENTER + AttributeFilter",
        "block_filter_mode": "PCGDistanceSettings block StaticMesh BOX_BOUNDS + AttributeFilter",
        "edges": edges,
        "edge_errors": [edge for edge in edges if not edge.get("ok")],
        "nodes": [_node_summary(node) for node in nodes.values()],
    }


def _ensure_source_actor(layout):
    existing = _find_actor(SOURCE_LABEL)
    if existing:
        actor = existing
        reused = True
    else:
        actor_class = unreal.EditorAssetLibrary.load_blueprint_class(BP_OBJECT_PATH)
        if not actor_class:
            raise RuntimeError("Failed to load source Blueprint class: " + BP_CLASS_PATH)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, layout["center"], _make_rotator())
        if not actor:
            raise RuntimeError("Failed to spawn source actor")
        actor.set_actor_label(SOURCE_LABEL)
        reused = False
    actor.set_actor_location(layout["center"] + unreal.Vector(0.0, -600.0, 120.0), False, False)
    actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    actor.set_editor_property("tags", [unreal.Name(SOURCE_ACTOR_TAG), unreal.Name("MCPValidation")])
    actor.set_editor_property("UseGrassMeshOverride", True)
    actor.set_editor_property("GrassMesh", _load_asset(GRASS_MESH))
    actor.set_editor_property("UseGrassMaterialOverride", True)
    actor.set_editor_property("GrassMaterial", _load_asset(GRASS_MATERIAL))
    return {"actor": actor, "reused": reused}


def _road_spline(actor):
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        raise RuntimeError("Road actor has no SplineComponent")
    for spline in splines:
        if spline.get_name() == "Road_SourceSpline":
            return spline
    return splines[0]


def _set_spline_two_points(spline, a, b):
    try:
        spline.clear_spline_points(False)
    except Exception:
        while spline.get_number_of_spline_points() > 0:
            spline.remove_spline_point(0, False)
    spline.add_spline_point(a, unreal.SplineCoordinateSpace.WORLD, False)
    spline.add_spline_point(b, unreal.SplineCoordinateSpace.WORLD, False)
    if spline.get_number_of_spline_points() < 2:
        raise RuntimeError(
            "Road spline setup failed: expected 2 points, got {}".format(
                spline.get_number_of_spline_points()
            )
        )
    for index in range(spline.get_number_of_spline_points()):
        try:
            spline.set_spline_point_type(index, unreal.SplinePointType.LINEAR, False)
        except Exception:
            pass
    spline.set_closed_loop(False, False)
    try:
        tags = list(spline.get_editor_property("component_tags"))
    except Exception:
        tags = []
    if ROAD_SPLINE_TAG not in {str(tag) for tag in tags}:
        tags.append(unreal.Name(ROAD_SPLINE_TAG))
        spline.set_editor_property("component_tags", tags)
    spline.update_spline()


def _ensure_road_actor(layout):
    existing = _find_actor(ROAD_LABEL)
    if existing:
        actor = existing
        reused = True
    else:
        actor_class = unreal.load_object(None, ROAD_BP_CLASS_PATH)
        if not actor_class:
            raise RuntimeError("Missing road runtime Blueprint class: " + ROAD_BP_CLASS_PATH)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, layout["center"], _make_rotator())
        if not actor:
            raise RuntimeError("Failed to spawn road actor")
        actor.set_actor_label(ROAD_LABEL)
        reused = False
    actor.set_actor_location(layout["center"], False, False)
    actor.set_editor_property("tags", [unreal.Name(ROAD_ACTOR_TAG), unreal.Name("MCPValidation")])
    spline = _road_spline(actor)
    _set_spline_two_points(spline, layout["road_a"], layout["road_b"])
    return {"actor": actor, "spline": spline, "reused": reused}


def _ensure_road_mask_actor(layout):
    existing = _find_actor(ROAD_MASK_LABEL)
    if existing:
        actor = existing
        reused = True
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            layout["center"],
            _make_rotator(),
        )
        if not actor:
            raise RuntimeError("Failed to spawn road clearance mask actor")
        actor.set_actor_label(ROAD_MASK_LABEL)
        reused = False

    a = layout["road_a"]
    b = layout["road_b"]
    center = unreal.Vector((a.x + b.x) * 0.5, (a.y + b.y) * 0.5, layout["ground_z"])
    dx = float(b.x - a.x)
    dy = float(b.y - a.y)
    length = math.sqrt(dx * dx + dy * dy)
    yaw = math.degrees(math.atan2(dy, dx))
    actor.set_actor_location(center, False, False)
    actor.set_actor_rotation(_make_rotator(0.0, yaw, 0.0), False)
    actor.set_actor_scale3d(
        unreal.Vector(
            max((length + (ROAD_CLEARANCE_CM + ROAD_MASK_SAFETY_CM) * 2.0) / 100.0, 10.0),
            max(((ROAD_CLEARANCE_CM + ROAD_MASK_SAFETY_CM) * 2.0) / 100.0, 2.0),
            10.0,
        )
    )
    try:
        actor.set_is_temporarily_hidden_in_editor(False)
    except Exception:
        pass
    actor.set_editor_property("tags", [unreal.Name(ROAD_MASK_TAG), unreal.Name("MCPValidation")])
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        raise RuntimeError("Road clearance mask actor has no StaticMeshComponent")
    component.set_static_mesh(_load_asset(CUBE_MESH))
    basic_material = _load_asset(BASIC_SHAPE_MATERIAL)
    if basic_material:
        component.set_material(0, basic_material)
    component.set_editor_property("component_tags", [unreal.Name(ROAD_MASK_TAG)])
    try:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    try:
        component.set_visibility(True, True)
        component.set_hidden_in_game(False)
        component.set_editor_property("render_in_main_pass", True)
    except Exception:
        pass
    return {"actor": actor, "reused": reused, "visible_for_pcg": True}


def _ensure_block_actor(layout):
    existing = _find_actor(BLOCK_LABEL)
    if existing:
        actor = existing
        reused = True
    else:
        mesh = _load_asset(CUBE_MESH)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, layout["block"], _make_rotator())
        if not actor:
            raise RuntimeError("Failed to spawn block actor")
        actor.set_actor_label(BLOCK_LABEL)
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_static_mesh(mesh)
        reused = False
    actor.set_actor_location(layout["block"], False, False)
    actor.set_actor_scale3d(unreal.Vector(20.0, 20.0, 20.0))
    try:
        actor.set_is_temporarily_hidden_in_editor(False)
    except Exception:
        pass
    actor.set_editor_property("tags", [unreal.Name(BLOCK_TAG), unreal.Name("MCPValidation")])
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(_load_asset(CUBE_MESH))
    basic_material = _load_asset(BASIC_SHAPE_MATERIAL)
    if basic_material:
        component.set_material(0, basic_material)
    try:
        component.set_editor_property("component_tags", [unreal.Name(BLOCK_TAG)])
    except Exception:
        pass
    try:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    try:
        component.set_visibility(True, True)
        component.set_hidden_in_game(False)
        component.set_editor_property("render_in_main_pass", True)
    except Exception:
        pass
    return {"actor": actor, "reused": reused}


def _ensure_volume_actor(graph, layout):
    existing = _find_actor(VOLUME_LABEL)
    if existing:
        for component in existing.get_components_by_class(unreal.PCGComponent):
            try:
                component.cleanup(True)
            except Exception:
                pass
        actor = existing
        reused = True
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PCGVolume, layout["center"], _make_rotator())
        if not actor:
            raise RuntimeError("Failed to spawn PCGVolume")
        actor.set_actor_label(VOLUME_LABEL)
        reused = False
    actor.set_actor_location(layout["center"], False, False)
    actor.set_actor_scale3d(layout["volume_scale"])
    actor.set_editor_property("tags", [unreal.Name("MCPValidation"), unreal.Name("MCPVolumeOwnedGrass")])
    components = list(actor.get_components_by_class(unreal.PCGComponent))
    if not components:
        raise RuntimeError("PCGVolume has no PCGComponent")
    pcg = components[0]
    pcg.set_graph(graph)
    return {"actor": actor, "reused": reused, "pcg_components": [component.get_name() for component in components]}


def _generate(actor):
    results = []
    for component in actor.get_components_by_class(unreal.PCGComponent):
        entry = {"component": component.get_name()}
        try:
            component.activate(True)
            component.cleanup(True)
            component.generate(True)
            entry["generated"] = True
        except Exception as exc:
            entry["generated"] = False
            entry["error"] = str(exc)
        results.append(entry)
    return results


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
        if mesh and hasattr(mesh, "get_path_name"):
            return mesh.get_path_name()
    except Exception:
        pass
    return ""


def _component_category(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(token in text for token in ("grass", "fern", "groundleaf", "flower", "leaf", "foliage", "plant")):
        return "grass"
    if any(token in text for token in ("tree", "pine", "spruce", "conifer", "trunk")):
        return "tree"
    if any(token in text for token in ("rock", "stone", "boulder")):
        return "rock"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _road_points(spline):
    points = []
    for index in range(spline.get_number_of_spline_points()):
        point = spline.get_location_at_spline_point(index, unreal.SplineCoordinateSpace.WORLD)
        points.append((float(point.x), float(point.y), float(point.z)))
    return points


def _road_distance_xy(x, y, points):
    if len(points) < 2:
        return None
    best = 10**18
    for index in range(len(points) - 1):
        ax, ay, _az = points[index]
        bx, by, _bz = points[index + 1]
        dx = bx - ax
        dy = by - ay
        length_sq = dx * dx + dy * dy
        if length_sq <= 0.001:
            continue
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / length_sq))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best if best < 10**18 else None


def _block_bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return {"origin": origin, "extent": extent}


def _inside_block_clearance(location, bounds):
    origin = bounds["origin"]
    extent = bounds["extent"]
    return (
        abs(float(location.x) - float(origin.x)) <= float(extent.x) + BLOCK_CLEARANCE_CM
        and abs(float(location.y) - float(origin.y)) <= float(extent.y) + BLOCK_CLEARANCE_CM
        and abs(float(location.z) - float(origin.z)) <= float(extent.z) + BLOCK_CLEARANCE_CM
    )


def _validate(volume_actor, road_spline, block_actor):
    points = _road_points(road_spline)
    bounds = _block_bounds(block_actor)
    summary = {
        "actor": _actor_label(volume_actor),
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "components": [],
        "road_points": len(points),
        "road_clearance_violations": 0,
        "block_overlap_violations": 0,
        "road_violation_samples": [],
        "block_violation_samples": [],
        "python_prune_applied": False,
    }
    for component in volume_actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        category = _component_category(component)
        count = _instance_count(component)
        component_summary = {
            "component": component.get_name(),
            "category": category,
            "mesh": _mesh_path(component),
            "count": count,
        }
        for index in range(count):
            try:
                transform = component.get_instance_transform(index, True)
            except Exception:
                continue
            location = transform.translation
            if category == "grass":
                distance = _road_distance_xy(location.x, location.y, points)
                if distance is not None and distance < ROAD_CLEARANCE_CM:
                    summary["road_clearance_violations"] += 1
                    if len(summary["road_violation_samples"]) < 20:
                        summary["road_violation_samples"].append(
                            {"component": component.get_name(), "index": index, "distance": round(distance, 2)}
                        )
                if _inside_block_clearance(location, bounds):
                    summary["block_overlap_violations"] += 1
                    if len(summary["block_violation_samples"]) < 20:
                        summary["block_violation_samples"].append(
                            {"component": component.get_name(), "index": index}
                        )
        summary["instances"]["all"] += count
        summary["instances"][category] += count
        summary["components"].append(component_summary)
    return summary


def _stabilize_validation(volume_actor, road_spline, block_actor):
    deadline = time.time() + max(float(SETTLE_SECONDS), 1.0)
    last_grass = None
    stable_ticks = 0
    snapshots = []
    latest = None
    while time.time() <= deadline:
        time.sleep(1.0)
        latest = _validate(volume_actor, road_spline, block_actor)
        grass_count = latest["instances"].get("grass", 0)
        snapshots.append({"time": round(time.time(), 3), "grass": grass_count})
        if grass_count <= 0:
            stable_ticks = 0
            last_grass = grass_count
            continue
        if grass_count == last_grass:
            stable_ticks += 1
            if stable_ticks >= 2:
                break
        else:
            stable_ticks = 0
            last_grass = grass_count
    if latest is None:
        latest = _validate(volume_actor, road_spline, block_actor)
    latest["stabilization"] = {
        "stable_ticks": stable_ticks,
        "snapshots": snapshots[-10:],
    }
    return latest


def _set_viewport_camera(layout):
    try:
        target = layout["center"]
        location = layout["camera"]
        direction = target - location
        yaw = math.degrees(math.atan2(direction.y, direction.x))
        dist_xy = math.sqrt(direction.x * direction.x + direction.y * direction.y)
        pitch = math.degrees(math.atan2(direction.z, dist_xy))
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(
            location,
            _make_rotator(pitch, yaw, 0.0),
        )
        return {"success": True, "location": [round(location.x, 3), round(location.y, 3), round(location.z, 3)], "rotation": [round(pitch, 3), round(yaw, 3), 0.0]}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _dirty_packages():
    rows = []
    try:
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():
            rows.append(package.get_name())
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
            rows.append(package.get_name())
    except Exception:
        pass
    return sorted(set(rows))


def _report_path():
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, REPORT_NAME)


def _write_report(report):
    path = _report_path()
    report["report_path"] = path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("Cubeless TestMap volume grass block mask report: {}".format(path))
    print(json.dumps(report, ensure_ascii=False))
    return path


def run():
    world = _load_test_map()
    layout = _fixture_layout()
    report = {
        "success": False,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": world.get_path_name() if world else None,
        "policy": {
            "grass_groundcover": "volume-owned PCG fixture, not broad grass spline handles",
            "mesh_material_rule": "StaticMeshSpawner reads GrassMesh and GrassMaterial from actor properties",
            "block_rule": "block tag StaticMesh exclusion must be PCG-native; no Python prune",
            "map": "TestMap fixture; production field map is not opened or modified by this script",
        },
        "layout": {
            "landscape": layout["landscape"],
            "center": [round(layout["center"].x, 3), round(layout["center"].y, 3), round(layout["center"].z, 3)],
            "ground_z": round(layout["ground_z"], 3),
            "grid_extents": [round(layout["grid_extents"].x, 3), round(layout["grid_extents"].y, 3), round(layout["grid_extents"].z, 3)],
        },
        "dirty_before": _dirty_packages(),
    }
    bp_info = _ensure_source_blueprint()
    graph_info = _create_or_update_graph(layout)
    source_info = _ensure_source_actor(layout)
    road_info = _ensure_road_actor(layout)
    road_mask_info = _ensure_road_mask_actor(layout)
    block_info = _ensure_block_actor(layout)
    volume_info = _ensure_volume_actor(graph_info["graph"], layout)
    generation = _generate(volume_info["actor"])
    validation = _stabilize_validation(volume_info["actor"], road_info["spline"], block_info["actor"])
    camera = _set_viewport_camera(layout)
    if SAVE_MAP:
        try:
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        except Exception:
            pass
    report.update(
        {
            "blueprint": bp_info,
            "graph": {key: value for key, value in graph_info.items() if key != "graph"},
            "source_actor": {
                "label": _actor_label(source_info["actor"]),
                "reused": source_info["reused"],
                "tags": _tags(source_info["actor"], "tags"),
                "grass_mesh": _object_path(source_info["actor"].get_editor_property("GrassMesh")),
                "grass_material": _object_path(source_info["actor"].get_editor_property("GrassMaterial")),
            },
            "road_actor": {
                "label": _actor_label(road_info["actor"]),
                "reused": road_info["reused"],
                "tags": _tags(road_info["actor"], "tags"),
                "spline_tags": _tags(road_info["spline"], "component_tags"),
                "spline_points": [[round(x, 3), round(y, 3), round(z, 3)] for x, y, z in _road_points(road_info["spline"])],
            },
            "road_mask_actor": {
                "label": _actor_label(road_mask_info["actor"]),
                "reused": road_mask_info["reused"],
                "tags": _tags(road_mask_info["actor"], "tags"),
                "component_tags": _tags(road_mask_info["actor"].get_component_by_class(unreal.StaticMeshComponent), "component_tags"),
                "visible_for_pcg": road_mask_info.get("visible_for_pcg", True),
            },
            "block_actor": {
                "label": _actor_label(block_info["actor"]),
                "reused": block_info["reused"],
                "tags": _tags(block_info["actor"], "tags"),
                "component_tags": _tags(block_info["actor"].get_component_by_class(unreal.StaticMeshComponent), "component_tags"),
            },
            "volume_actor": {
                "label": _actor_label(volume_info["actor"]),
                "reused": volume_info["reused"],
                "pcg_components": volume_info["pcg_components"],
                "tags": _tags(volume_info["actor"], "tags"),
            },
            "generation": generation,
            "validation": validation,
            "viewport_camera": camera,
            "dirty_after": _dirty_packages(),
        }
    )
    report["pass"] = (
        validation["instances"].get("grass", 0) > 0
        and (not ENABLE_ROAD_FILTER or validation.get("road_points", 0) >= 2)
        and (not ENABLE_ROAD_FILTER or validation.get("road_clearance_violations", 0) == 0)
        and (not ENABLE_BLOCK_FILTER or validation.get("block_overlap_violations", 0) == 0)
        and validation.get("python_prune_applied") is False
        and not graph_info.get("edge_errors")
    )
    report["success"] = True
    _write_report(report)


run()
"""


def command_succeeded(response: dict[str, Any] | None) -> bool:
    if not response:
        return False
    return response.get("status") == "success" or response.get("success") is True


def response_result(response: dict[str, Any] | None) -> dict[str, Any]:
    if not response:
        return {}
    result = response.get("result", response)
    return result if isinstance(result, dict) else {"result": result}


def parse_response(response: dict[str, Any] | None) -> dict[str, Any]:
    result = response_result(response)
    parsed_logs: list[dict[str, Any]] = []
    for log_item in result.get("logs", []):
        if not isinstance(log_item, dict):
            continue
        output = str(log_item.get("output", "")).strip()
        if not output.startswith("{"):
            continue
        try:
            parsed_logs.append(json.loads(output))
        except json.JSONDecodeError:
            continue
    if parsed_logs:
        parsed = parsed_logs[-1]
        parsed["unreal_execute_summary"] = {
            "success": result.get("success"),
            "command_result": result.get("command_result"),
            "log_count": len(result.get("logs", [])),
        }
        return parsed
    return result


def build_unreal_code(args: argparse.Namespace) -> str:
    return (
        UNREAL_CODE_TEMPLATE.replace("__POINTS_PER_SQM__", repr(float(args.points_per_sqm)))
        .replace("__ROAD_CLEARANCE_CM__", repr(float(args.road_clearance_cm)))
        .replace("__BLOCK_CLEARANCE_CM__", repr(float(args.block_clearance_cm)))
        .replace("__SETTLE_SECONDS__", repr(float(args.settle_seconds)))
        .replace("__SAVE_ASSETS__", "True" if args.save_assets else "False")
        .replace("__SAVE_MAP__", "True" if args.save_map else "False")
        .replace("__ENABLE_ROAD_FILTER__", "True" if args.enable_road_filter else "False")
        .replace("__ENABLE_BLOCK_FILTER__", "True" if args.enable_block_filter else "False")
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    response = UnrealConnection().send_command(
        "execute_python",
        {
            "code": build_unreal_code(args),
            "mode": "ExecuteFile",
            "description": "Stage TestMap volume-owned grass block mask fixture",
        },
    )
    if not command_succeeded(response):
        raise RuntimeError(f"execute_python failed: {json.dumps(response, ensure_ascii=False)}")
    return parse_response(response)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage TestMap volume-owned grass block mask fixture.")
    parser.add_argument("--points-per-sqm", type=float, default=0.22)
    parser.add_argument("--road-clearance-cm", type=float, default=650.0)
    parser.add_argument("--block-clearance-cm", type=float, default=1.0)
    parser.add_argument("--settle-seconds", type=float, default=6.0)
    parser.add_argument(
        "--enable-road-filter",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable tagged road spline distance filtering in the graph.",
    )
    parser.add_argument(
        "--enable-block-filter",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable block tagged StaticMesh BOX_BOUNDS distance filtering in the graph.",
    )
    parser.add_argument(
        "--save-assets",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save generated _MCP_Temp graph/source Blueprint assets.",
    )
    parser.add_argument(
        "--save-map",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Save TestMap after placing fixture actors. Default leaves map dirty for review.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        print(json.dumps(run(parse_args()), ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        raise
