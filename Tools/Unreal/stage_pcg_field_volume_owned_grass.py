"""Stage a non-destructive volume-owned grass review layer in the field level.

This replaces the visual role of dense short open-spline grass handles with a
single PCGVolume-owned review layer. The old spline actors are temporarily
hidden in the editor for review, not deleted or archived.
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


FIELD_LEVEL_PATH = "/Game/Cubeless/Map/LVL_Cubeless_PCG_Ecosystem_Field"
REPORT_NAME = "pcg_field_volume_owned_grass_stage_report.json"

GRAPH_FOLDER = "/Game/_MCP_Temp/PCG/Graphs"
GRAPH_NAME = "PCG_Cubeless_FieldVolumeOwnedGrass_MCP"
GRAPH_OBJECT = GRAPH_FOLDER + "/" + GRAPH_NAME + "." + GRAPH_NAME

BP_FOLDER = "/Game/_MCP_Temp/PCG/Blueprints"
BP_NAME = "BP_Cubeless_FieldVolumeOwnedGrassSource_MCP"
BP_OBJECT_PATH = BP_FOLDER + "/" + BP_NAME
BP_CLASS_PATH = BP_OBJECT_PATH + "." + BP_NAME + "_C"

SOURCE_LABEL = "MCP_PCG_FieldVolumeOwnedGrass_Source"
VOLUME_LABEL = "MCP_PCG_FieldVolumeOwnedGrass_Review"
SOURCE_ACTOR_TAG = "MCPFieldVolumeOwnedGrass"
RUNTIME_ROAD_ACTOR_TAG = "CubelessRuntimeRoad"
RUNTIME_ROAD_SPLINE_NAME = "Road_SourceSpline"
BLOCK_TAG = "block"

DYNAMIC_MESH_ATTR = "DynamicMeshPath"
DYNAMIC_MATERIAL_SLOT0_ATTR = "DynamicMaterialSlot0"
BLOCK_DISTANCE_ATTR = "BlockClearanceDistance"

GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)
GRASS_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_GrassMedium_ForestBalanced.MI_Cubeless_PCG_GrassMedium_ForestBalanced"
)

POINTS_PER_SQM = __POINTS_PER_SQM__
ROAD_CLEARANCE_CM = __ROAD_CLEARANCE_CM__
ROAD_FILTER_EXTRA_CLEARANCE_CM = 220.0
ROAD_REFERENCE_DISTANCE_INCREMENT_CM = 120.0
HIDE_OLD_SPLINE_GRASS = __HIDE_OLD_SPLINE_GRASS__
SAVE_DIRTY_PACKAGES = __SAVE_DIRTY_PACKAGES__

# Bounds are the 2D audit envelope for the grass-candidate spline layer, padded
# enough that the review volume covers the visible field without relying on the
# old actor cloud as an authoring surface.
VOLUME_CENTER = unreal.Vector(24342.97, 26073.656, 0.0)
VOLUME_SCALE = unreal.Vector(620.0, 700.0, 120.0)
VOLUME_GRID_EXTENTS = unreal.Vector(27000.0, 31000.0, 12000.0)


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


def _load_level():
    world = _get_editor_world()
    if not world or not world.get_path_name().startswith(FIELD_LEVEL_PATH + "."):
        unreal.EditorLevelLibrary.load_level(FIELD_LEVEL_PATH)
    return _get_editor_world()


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
    token = token.lower()
    return any(token in tag.lower() for tag in _tags(obj, prop))


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


def _classify_spline_actor(actor):
    label = _actor_label(actor)
    text = (label + " " + " ".join(_tags(actor, "tags"))).lower()
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        return None
    component_instances = {"grass": 0, "tree": 0, "rock": 0, "other": 0}
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        component_instances[_component_category(component)] += _instance_count(component)
    if "road" in text:
        return "keep_linear_road_or_road_feather"
    if "camera" in text or "bookmark" in text:
        return "ignore_camera_or_bookmark"
    if "landmark" in text:
        return "review_landmark_layer"
    if "qualitylayer" in text or "fulllandscapefill" in text or "groundcarpet" in text:
        return "replace_with_volume_owned_grass"
    if component_instances.get("grass", 0) > 0 and component_instances.get("tree", 0) == 0:
        return "replace_with_volume_owned_grass"
    if component_instances.get("grass", 0) > 0:
        return "review_mixed_grass_layer"
    return "keep_or_review_non_grass"


def _temporarily_hide_old_spline_grass():
    report = {
        "requested": bool(HIDE_OLD_SPLINE_GRASS),
        "hidden_actor_count": 0,
        "hidden_grass_instances": 0,
        "failed": [],
        "kept_counts": {},
    }
    if not HIDE_OLD_SPLINE_GRASS:
        return report
    for actor in _all_level_actors():
        if _actor_label(actor) == VOLUME_LABEL:
            continue
        classification = _classify_spline_actor(actor)
        if not classification:
            continue
        if classification != "replace_with_volume_owned_grass":
            report["kept_counts"][classification] = report["kept_counts"].get(classification, 0) + 1
            continue
        grass_count = 0
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if _component_category(component) == "grass":
                grass_count += _instance_count(component)
        try:
            if hasattr(actor, "set_is_temporarily_hidden_in_editor"):
                actor.set_is_temporarily_hidden_in_editor(True)
            else:
                actor.set_actor_hidden_in_game(True)
            report["hidden_actor_count"] += 1
            report["hidden_grass_instances"] += grass_count
        except Exception as exc:
            if len(report["failed"]) < 20:
                report["failed"].append({"actor": _actor_label(actor), "error": str(exc)})
    return report


def _make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _blueprint_variable_exists(blueprint_object_path, variable_name):
    try:
        cls = unreal.EditorAssetLibrary.load_blueprint_class(blueprint_object_path)
        if cls:
            unreal.get_default_object(cls).get_editor_property(variable_name)
            return True
    except Exception:
        pass
    return False


def _set_variable_editable(blueprint, variable_name, value=True):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(
            blueprint, variable_name, bool(value)
        )
    except Exception:
        pass
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_expose_on_spawn(
            blueprint, variable_name, bool(value)
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
        raise RuntimeError("Failed to create/load volume grass source Blueprint: " + BP_OBJECT_PATH)

    bool_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    mesh_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.StaticMesh.static_class())
    material_type = unreal.BlueprintEditorLibrary.get_object_reference_type(
        unreal.MaterialInterface.static_class()
    )
    specs = [
        ("UseGrassMeshOverride", bool_type, True),
        ("GrassMesh", mesh_type, GRASS_MESH),
        ("UseGrassMaterialOverride", bool_type, True),
        ("GrassMaterial", material_type, GRASS_MATERIAL),
    ]
    added = []
    for variable_name, pin_type, _default in specs:
        if _blueprint_variable_exists(BP_OBJECT_PATH, variable_name):
            continue
        if not unreal.BlueprintEditorLibrary.add_member_variable(blueprint, variable_name, pin_type):
            raise RuntimeError("Failed to add Blueprint variable: " + variable_name)
        added.append(variable_name)
    for variable_name, _pin_type, _default in specs:
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
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False))
    return {
        "blueprint": BP_OBJECT_PATH,
        "class": BP_CLASS_PATH,
        "created": created,
        "added_variables": added,
        "saved": saved,
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


def _selector_import(settings, prop, text):
    selector = settings.get_editor_property(prop)
    selector.import_text("PCGBegin({})PCGEnd".format(text))
    settings.set_editor_property(prop, selector)


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


def _configure_surface_sampler(node):
    settings = node.get_settings()
    settings.set_editor_property("points_per_squared_meter", float(POINTS_PER_SQM))
    settings.set_editor_property("point_extents", unreal.Vector(45.0, 45.0, 90.0))
    settings.set_editor_property("point_steepness", 0.5)
    settings.set_editor_property("keep_zero_density_points", False)
    settings.set_editor_property("seed", 6122026)
    try:
        settings.set_editor_property("apply_density_to_points", True)
    except Exception:
        pass


def _grid_cell_size_cm():
    density = max(float(POINTS_PER_SQM), 0.0001)
    return max(90.0, min(1600.0, 100.0 / math.sqrt(density)))


def _configure_grid(node):
    settings = node.get_settings()
    cell = _grid_cell_size_cm()
    settings.set_editor_property("grid_extents", VOLUME_GRID_EXTENTS)
    settings.set_editor_property("cell_size", unreal.Vector(cell, cell, 100000.0))
    settings.set_editor_property("set_points_bounds", True)
    settings.set_editor_property("cull_points_outside_volume", False)
    settings.set_editor_property("point_steepness", 0.5)
    settings.set_editor_property("seed", 6122026)
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


def _configure_get_road_spline(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", RUNTIME_ROAD_ACTOR_TAG)
    actor_selector.set_editor_property("select_multiple", False)
    actor_selector.set_editor_property("ignore_self_and_children", False)
    settings.set_editor_property("actor_selector", actor_selector)

    component_selector = settings.get_editor_property("component_selector")
    component_selector.set_editor_property("component_selection", unreal.PCGComponentSelection.BY_CLASS)
    component_selector.set_editor_property("component_selection_class", unreal.SplineComponent.static_class())
    settings.set_editor_property("component_selector", component_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("components_must_overlap_self", False)
    settings.set_editor_property("track_actors_only_within_bounds", False)


def _configure_spline_sampler(node):
    settings = node.get_settings()
    params = settings.get_editor_property("sampler_params")
    params.set_editor_property("dimension", unreal.PCGSplineSamplingDimension.ON_SPLINE)
    params.set_editor_property("mode", unreal.PCGSplineSamplingMode.DISTANCE)
    params.set_editor_property("distance_increment", float(ROAD_REFERENCE_DISTANCE_INCREMENT_CM))
    params.set_editor_property("subdivisions_per_segment", 8)
    params.set_editor_property("compute_distance", True)
    params.set_editor_property("compute_segment_index", True)
    settings.set_editor_property("sampler_params", params)


def _configure_distance(node):
    settings = node.get_settings()
    settings.set_editor_property("output_to_attribute", True)
    settings.set_editor_property(
        "output_attribute",
        _selector("RoadClearanceDistance", unreal.PCGAttributePropertySelector),
    )
    settings.set_editor_property("maximum_distance", float(ROAD_CLEARANCE_CM) * 3.0)
    settings.set_editor_property("set_density", False)
    settings.set_editor_property("source_shape", unreal.PCGDistanceShape.CENTER)
    settings.set_editor_property("target_shape", unreal.PCGDistanceShape.CENTER)


def _selector(attribute_name, selector_cls):
    selector = selector_cls()
    selector.import_text('(AttributeName="{}")'.format(attribute_name))
    return selector


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


def _configure_clearance_filter(node):
    settings = node.get_settings()
    settings.set_editor_property(
        "target_attribute",
        _selector("RoadClearanceDistance", unreal.PCGAttributePropertyInputSelector),
    )
    settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.GREATER_OR_EQUAL)
    settings.set_editor_property("use_constant_threshold", True)
    settings.set_editor_property(
        "attribute_types",
        _constant(unreal.PCGMetadataTypes.DOUBLE, ROAD_CLEARANCE_CM + ROAD_FILTER_EXTRA_CLEARANCE_CM),
    )
    settings.set_editor_property("generate_output_data_even_if_empty", True)
    try:
        settings.set_editor_property("warn_on_data_missing_attribute", False)
    except Exception:
        pass


def _configure_block_mask_points(node, block_bounds):
    settings = node.get_settings()
    points = settings.get_editor_property("points_to_create")
    points.clear()
    for index, entry in enumerate(block_bounds):
        mn = entry["min"]
        mx = entry["max"]
        center = unreal.Vector(
            (mn[0] + mx[0]) * 0.5,
            (mn[1] + mx[1]) * 0.5,
            (mn[2] + mx[2]) * 0.5,
        )
        extent = unreal.Vector(
            max(1.0, (mx[0] - mn[0]) * 0.5),
            max(1.0, (mx[1] - mn[1]) * 0.5),
            max(1.0, (mx[2] - mn[2]) * 0.5),
        )
        point = unreal.PCGPoint()
        transform = point.get_editor_property("transform")
        transform.set_editor_property("translation", center)
        point.set_editor_property("transform", transform)
        point.set_editor_property("bounds_min", unreal.Vector(-extent.x, -extent.y, -extent.z))
        point.set_editor_property("bounds_max", unreal.Vector(extent.x, extent.y, extent.z))
        point.set_editor_property("density", 1.0)
        point.set_editor_property("steepness", 1.0)
        point.set_editor_property("seed", 6134000 + index)
        points.append(point)
    settings.set_editor_property("points_to_create", points)
    settings.set_editor_property("cull_points_outside_volume", False)


def _configure_block_distance(node):
    settings = node.get_settings()
    settings.set_editor_property("output_to_attribute", True)
    settings.set_editor_property("output_attribute", _selector(BLOCK_DISTANCE_ATTR, unreal.PCGAttributePropertySelector))
    settings.set_editor_property("maximum_distance", 1000000.0)
    settings.set_editor_property("set_density", False)
    settings.set_editor_property("source_shape", unreal.PCGDistanceShape.CENTER)
    settings.set_editor_property("target_shape", unreal.PCGDistanceShape.BOX_BOUNDS)


def _configure_block_filter(node):
    settings = node.get_settings()
    settings.set_editor_property(
        "target_attribute",
        _selector(BLOCK_DISTANCE_ATTR, unreal.PCGAttributePropertyInputSelector),
    )
    settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.GREATER_OR_EQUAL)
    settings.set_editor_property("use_constant_threshold", True)
    settings.set_editor_property("attribute_types", _constant(unreal.PCGMetadataTypes.DOUBLE, 120.0))
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
    settings.set_editor_property("scale_min", unreal.Vector(0.74, 0.74, 0.86))
    settings.set_editor_property("scale_max", unreal.Vector(1.38, 1.38, 1.18))
    settings.set_editor_property("recompute_seed", True)
    settings.set_editor_property("seed", 6122027)


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
        "input_pins": [{"label": _pin_label(pin), "connected": bool(pin.is_connected())} for pin in getattr(node, "input_pins", [])],
        "output_pins": [{"label": _pin_label(pin), "connected": bool(pin.is_connected())} for pin in getattr(node, "output_pins", [])],
    }


def _create_or_update_graph():
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

    block_bounds = _collect_block_bounds()
    # Difference over-subtracted this review volume in UE 5.7. Use a distance
    # filter against the tagged StaticMesh bounds instead; this keeps block
    # exclusion graph-native without the destructive Difference path.
    has_block_bounds = len(block_bounds) > 0

    nodes = {
        "landscape": _add_node(graph, unreal.PCGGetLandscapeSettings, "Get Field Landscape", -1500, 0),
        "grid": _add_node(graph, unreal.PCGCreatePointsGridSettings, "Create Volume-Owned Grass Grid", -1160, 0),
        "project": _add_node(graph, unreal.PCGProjectionSettings, "Project Grass Grid To Landscape", -820, 0),
        "road": _add_node(graph, unreal.PCGGetSplineSettings, "Get Runtime Road_SourceSpline", -1160, -360),
        "road_reference_points": _add_node(graph, unreal.PCGSplineSamplerSettings, "Sample Road Clearance Reference Points", -820, -360),
        "distance": _add_node(graph, unreal.PCGDistanceSettings, "Compute RoadClearanceDistance", -480, 0),
        "road_filter": _add_node(graph, unreal.PCGAttributeFilteringSettings, "Keep Grass Outside Road Core", -120, 0),
        "get_mesh": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor GrassMesh", 220, -360),
        "copy_mesh": _add_node(graph, unreal.PCGCopyAttributesSettings, "Copy GrassMesh To DynamicMeshPath", 560, -80),
        "get_material": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor GrassMaterial", 560, -360),
        "copy_material": _add_node(graph, unreal.PCGCopyAttributesSettings, "Copy GrassMaterial To DynamicMaterialSlot0", 900, -80),
        "transform": _add_node(graph, unreal.PCGTransformPointsSettings, "Randomize Grass Yaw And Scale", 1240, 0),
        "spawn": _add_node(graph, unreal.PCGStaticMeshSpawnerSettings, "Spawn Actor-Property Grass", 1580, 0),
    }
    if has_block_bounds:
        nodes["block_data"] = _add_node(
            graph,
            unreal.PCGCreatePointsSettings,
            "Create block-tag bounds mask points",
            -120,
            -360,
        )
        nodes["block_distance"] = _add_node(
            graph,
            unreal.PCGDistanceSettings,
            "Compute BlockClearanceDistance",
            220,
            0,
        )
        nodes["block_filter"] = _add_node(
            graph,
            unreal.PCGAttributeFilteringSettings,
            "Keep Grass Outside Block Bounds",
            560,
            0,
        )

    _configure_get_landscape(nodes["landscape"])
    _configure_grid(nodes["grid"])
    _configure_projection(nodes["project"])
    _configure_get_road_spline(nodes["road"])
    _configure_spline_sampler(nodes["road_reference_points"])
    _configure_distance(nodes["distance"])
    _configure_clearance_filter(nodes["road_filter"])
    if has_block_bounds:
        _configure_block_mask_points(nodes["block_data"], block_bounds)
        _configure_block_distance(nodes["block_distance"])
        _configure_block_filter(nodes["block_filter"])
    _configure_get_actor_property(nodes["get_mesh"], "GrassMesh", "GrassMesh")
    _configure_copy_attr(nodes["copy_mesh"], "GrassMesh", DYNAMIC_MESH_ATTR)
    _configure_get_actor_property(nodes["get_material"], "GrassMaterial", "GrassMaterial")
    _configure_copy_attr(nodes["copy_material"], "GrassMaterial", DYNAMIC_MATERIAL_SLOT0_ATTR)
    _configure_transform(nodes["transform"])
    _configure_by_attribute_spawner(nodes["spawn"])

    edges = [
        _add_edge(graph, nodes["grid"], nodes["project"], "Out", "In"),
        _add_edge(graph, nodes["landscape"], nodes["project"], "Out", "Projection Target"),
        _add_edge(graph, nodes["project"], nodes["copy_mesh"], "Out", "Target"),
        _add_edge(graph, nodes["get_mesh"], nodes["copy_mesh"], "Out", "Source"),
        _add_edge(graph, nodes["copy_mesh"], nodes["copy_material"], "Out", "Target"),
        _add_edge(graph, nodes["get_material"], nodes["copy_material"], "Out", "Source"),
        _add_edge(graph, nodes["copy_material"], nodes["distance"], "Out", "Source"),
        _add_edge(graph, nodes["road"], nodes["road_reference_points"], "Out", "Spline"),
        _add_edge(graph, nodes["road_reference_points"], nodes["distance"], "Out", "Target"),
        _add_edge(graph, nodes["distance"], nodes["road_filter"], "Out", "In"),
    ]
    post_filter_node = nodes["road_filter"]
    post_filter_pin = "InsideFilter"
    if has_block_bounds:
        edges.extend(
            [
                _add_edge(graph, nodes["road_filter"], nodes["block_distance"], "InsideFilter", "Source"),
                _add_edge(graph, nodes["block_data"], nodes["block_distance"], "Out", "Target"),
                _add_edge(graph, nodes["block_distance"], nodes["block_filter"], "Out", "In"),
            ]
        )
        post_filter_node = nodes["block_filter"]
        post_filter_pin = "InsideFilter"
    edges.extend(
        [
            _add_edge(graph, post_filter_node, nodes["transform"], post_filter_pin, "In"),
            _add_edge(graph, nodes["transform"], nodes["spawn"], "Out", "In"),
            _add_edge(graph, nodes["spawn"], graph.get_output_node(), "Out", "Out"),
        ]
    )

    try:
        graph.description = (
            "Temporary field review graph for volume-owned grass. "
            "A volume-owned grid is projected to the Landscape, filtered by "
            "reference points sampled from the runtime road spline and block-tag "
            "StaticMesh bounds, then StaticMeshSpawner reads GrassMesh and "
            "GrassMaterial from the owner actor properties."
        )
        graph.get_input_node().set_node_position(-1780, 0)
        graph.get_output_node().set_node_position(1580, 0)
    except Exception:
        pass
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(graph, False))
    return {
        "graph": GRAPH_OBJECT,
        "created": created,
        "saved": saved,
        "points_per_squared_meter": POINTS_PER_SQM,
        "grid_cell_size_cm": round(_grid_cell_size_cm(), 3),
        "road_clearance_cm": ROAD_CLEARANCE_CM,
        "road_filter_extra_clearance_cm": ROAD_FILTER_EXTRA_CLEARANCE_CM,
        "road_reference_point_distance_increment_cm": ROAD_REFERENCE_DISTANCE_INCREMENT_CM,
        "road_filter_mode": "PCGGetSplineSettings runtime road + PCGSplineSamplerSettings reference points + PCGDistanceSettings CENTER + AttributeFilter",
        "block_bounds_detected": len(block_bounds),
        "block_graph_enabled": has_block_bounds,
        "block_filter_mode": "block-tag StaticMesh bounds -> PCGCreatePointsSettings mask + PCGDistanceSettings BOX_BOUNDS + AttributeFilter",
        "block_filter_clearance_cm": 120.0 if has_block_bounds else None,
        "block_graph_disabled_reason": None if has_block_bounds else "No block-tagged StaticMesh bounds detected.",
        "edges": edges,
        "edge_errors": [edge for edge in edges if not edge.get("ok")],
        "nodes": [_node_summary(node) for node in nodes.values()],
    }


def _find_actor(label):
    for actor in _all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _ensure_source_actor():
    existing = _find_actor(SOURCE_LABEL)
    if existing:
        actor = existing
        reused = True
    else:
        actor_class = unreal.EditorAssetLibrary.load_blueprint_class(BP_OBJECT_PATH)
        if not actor_class:
            raise RuntimeError("Failed to load volume grass source Blueprint class: " + BP_CLASS_PATH)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            actor_class,
            VOLUME_CENTER,
            _make_rotator(),
        )
        if not actor:
            raise RuntimeError("Failed to spawn volume grass source actor.")
        actor.set_actor_label(SOURCE_LABEL)
        reused = False

    actor.set_actor_location(VOLUME_CENTER, False, False)
    actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    actor.set_editor_property(
        "tags",
        [
            unreal.Name(SOURCE_ACTOR_TAG),
            unreal.Name("MCPVolumeOwnedGrass"),
            unreal.Name("MCPValidation"),
        ],
    )
    actor.set_editor_property("UseGrassMeshOverride", True)
    actor.set_editor_property("GrassMesh", _load_asset(GRASS_MESH))
    actor.set_editor_property("UseGrassMaterialOverride", True)
    actor.set_editor_property("GrassMaterial", _load_asset(GRASS_MATERIAL))
    try:
        if hasattr(actor, "set_is_temporarily_hidden_in_editor"):
            actor.set_is_temporarily_hidden_in_editor(False)
        actor.set_actor_hidden_in_game(False)
    except Exception:
        pass
    return {"actor": actor, "reused": reused}


def _ensure_volume_actor(graph):
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
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PCGVolume,
            VOLUME_CENTER,
            _make_rotator(),
        )
        if not actor:
            raise RuntimeError("Failed to spawn volume grass review actor.")
        actor.set_actor_label(VOLUME_LABEL)
        reused = False

    actor.set_actor_location(VOLUME_CENTER, False, False)
    actor.set_actor_scale3d(VOLUME_SCALE)
    actor.set_editor_property(
        "tags",
        [
            unreal.Name("MCPVolumeOwnedGrass"),
            unreal.Name("MCPValidation"),
        ],
    )
    try:
        if hasattr(actor, "set_is_temporarily_hidden_in_editor"):
            actor.set_is_temporarily_hidden_in_editor(False)
        actor.set_actor_hidden_in_game(False)
    except Exception:
        pass

    components = list(actor.get_components_by_class(unreal.PCGComponent))
    if not components:
        raise RuntimeError("Volume grass actor has no PCGComponent.")
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


def _road_spline_points():
    for actor in _all_level_actors():
        if not _has_tag_token(actor, "tags", RUNTIME_ROAD_ACTOR_TAG):
            continue
        for spline in actor.get_components_by_class(unreal.SplineComponent):
            if spline.get_name() != RUNTIME_ROAD_SPLINE_NAME:
                continue
            points = []
            for index in range(spline.get_number_of_spline_points()):
                point = spline.get_location_at_spline_point(index, unreal.SplineCoordinateSpace.WORLD)
                points.append((float(point.x), float(point.y), float(point.z)))
            if len(points) >= 2:
                return points
    return []


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


def _collect_block_bounds():
    rows = []
    for actor in _all_level_actors():
        actor_is_block = _has_tag_token(actor, "tags", BLOCK_TAG)
        component_blocks = [
            component
            for component in actor.get_components_by_class(unreal.StaticMeshComponent)
            if _has_tag_token(component, "component_tags", BLOCK_TAG)
        ]
        if actor_is_block or component_blocks:
            try:
                origin, extent = actor.get_actor_bounds(False)
                rows.append(
                    {
                        "actor": _actor_label(actor),
                        "component": "ActorBounds",
                        "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
                        "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
                    }
                )
            except Exception:
                pass
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not actor_is_block and not _has_tag_token(component, "component_tags", BLOCK_TAG):
                continue
            try:
                bounds = component.bounds
                origin = bounds.origin
                extent = bounds.box_extent
            except Exception:
                try:
                    local_min, local_max = component.get_local_bounds()
                    transform = component.get_component_transform()
                    center = (local_min + local_max) * 0.5
                    extent = (local_max - local_min) * 0.5
                    origin = transform.transform_position(center)
                except Exception:
                    continue
            rows.append(
                {
                    "actor": _actor_label(actor),
                    "component": component.get_name(),
                    "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
                    "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
                }
            )
    return rows


def _inside_block(location, block_bounds, margin=120.0):
    for entry in block_bounds:
        mn = entry["min"]
        mx = entry["max"]
        if (
            mn[0] - margin <= location.x <= mx[0] + margin
            and mn[1] - margin <= location.y <= mx[1] + margin
            and mn[2] - margin <= location.z <= mx[2] + margin
        ):
            return True
    return False


def _collect_instances(actor, prune_block_overlaps=False):
    road_points = _road_spline_points()
    block_bounds = _collect_block_bounds()
    summary = {
        "actor": _actor_label(actor),
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "components": [],
        "road_points": len(road_points),
        "road_clearance_violations": 0,
        "block_tagged_component_count": len(block_bounds),
        "block_overlap_violations": 0,
        "block_overlap_samples": [],
        "road_violation_samples": [],
        "post_prune_removed": 0,
    }
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        category = _component_category(component)
        count = _instance_count(component)
        component_summary = {
            "component": component.get_name(),
            "category": category,
            "mesh": _mesh_path(component),
            "before": count,
            "after": count,
            "removed_block_overlaps": 0,
        }
        remove_indexes = []
        for index in range(count):
            try:
                transform = component.get_instance_transform(index, True)
            except Exception:
                continue
            location = transform.translation
            if category == "grass":
                distance = _road_distance_xy(location.x, location.y, road_points)
                if distance is not None and distance < ROAD_CLEARANCE_CM:
                    summary["road_clearance_violations"] += 1
                    if len(summary["road_violation_samples"]) < 20:
                        summary["road_violation_samples"].append(
                            {
                                "component": component.get_name(),
                                "index": index,
                                "distance": round(distance, 2),
                            }
                        )
                if _inside_block(location, block_bounds):
                    summary["block_overlap_violations"] += 1
                    remove_indexes.append(index)
                    if len(summary["block_overlap_samples"]) < 20:
                        summary["block_overlap_samples"].append(
                            {"component": component.get_name(), "index": index}
                        )
        if prune_block_overlaps and remove_indexes:
            for index in sorted(remove_indexes, reverse=True):
                try:
                    component.remove_instance(index)
                    component_summary["removed_block_overlaps"] += 1
                except Exception:
                    pass
            try:
                component.mark_render_state_dirty()
            except Exception:
                pass
            component_summary["after"] = _instance_count(component)
            summary["post_prune_removed"] += component_summary["removed_block_overlaps"]
        final_count = component_summary["after"]
        summary["instances"]["all"] += final_count
        summary["instances"][category] += final_count
        summary["components"].append(component_summary)
    return summary


def _report_path():
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, REPORT_NAME)


def _write_report(report):
    path = _report_path()
    report["report_path"] = path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("Cubeless field volume-owned grass stage report: {}".format(path))
    print(json.dumps(report, ensure_ascii=False))
    return path


def stage_volume_owned_grass():
    world = _load_level()
    report = {
        "success": False,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": world.get_path_name() if world else None,
        "policy": {
            "grass_groundcover": "broad grass should be volume-owned PCG, not dense overlapping short open-spline handles",
            "old_spline_cleanup": "temporarily hidden for review only; no delete/archive",
            "mesh_material_rule": "StaticMeshSpawner reads GrassMesh and GrassMaterial from actor properties",
            "screenshot_route": "active viewport only; no user bookmark overwrite",
        },
    }
    try:
        report["old_spline_visibility"] = _temporarily_hide_old_spline_grass()
        report["blueprint"] = _ensure_source_blueprint()
        graph_update = _create_or_update_graph()
        report["graph"] = graph_update
        graph = _load_asset(GRAPH_OBJECT)
        if not graph:
            raise RuntimeError("Graph missing after update: " + GRAPH_OBJECT)
        source_info = _ensure_source_actor()
        volume_info = _ensure_volume_actor(graph)
        actor = volume_info["actor"]
        source_actor = source_info["actor"]
        report["source_actor"] = {
            "label": _actor_label(source_actor),
            "reused": source_info["reused"],
            "tags": _tags(source_actor, "tags"),
            "location": [round(source_actor.get_actor_location().x, 3), round(source_actor.get_actor_location().y, 3), round(source_actor.get_actor_location().z, 3)],
            "grass_mesh": _object_path(source_actor.get_editor_property("GrassMesh")),
            "grass_material": _object_path(source_actor.get_editor_property("GrassMaterial")),
        }
        report["volume_actor"] = {
            "label": _actor_label(actor),
            "reused": volume_info["reused"],
            "pcg_components": volume_info["pcg_components"],
            "tags": _tags(actor, "tags"),
            "location": [round(actor.get_actor_location().x, 3), round(actor.get_actor_location().y, 3), round(actor.get_actor_location().z, 3)],
            "scale": [round(actor.get_actor_scale3d().x, 3), round(actor.get_actor_scale3d().y, 3), round(actor.get_actor_scale3d().z, 3)],
        }
        report["generation"] = _generate(actor)
        raw_summary = _collect_instances(actor, prune_block_overlaps=False)
        report["raw_validation"] = raw_summary
        final_summary = raw_summary
        if raw_summary.get("block_overlap_violations", 0) > 0:
            final_summary = _collect_instances(actor, prune_block_overlaps=True)
            final_summary = _collect_instances(actor, prune_block_overlaps=False)
            report["python_block_overlap_prune_applied"] = True
        else:
            report["python_block_overlap_prune_applied"] = False
        report["final_validation"] = final_summary
        report["pass"] = (
            final_summary["instances"].get("grass", 0) > 0
            and final_summary.get("road_clearance_violations", 0) == 0
            and final_summary.get("block_overlap_violations", 0) == 0
            and not graph_update.get("edge_errors")
        )
        report["success"] = True
        if SAVE_DIRTY_PACKAGES:
            try:
                report["save_dirty_packages"] = bool(
                    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
                )
            except Exception as exc:
                report["save_dirty_packages"] = "failed: " + str(exc)
    except Exception as exc:
        report["error"] = str(exc)
        report["success"] = False
        report["pass"] = False
    _write_report(report)
    return report


stage_volume_owned_grass()
"""


VALIDATE_UNREAL_CODE_TEMPLATE = r"""
import json
import math
import os
import time

import unreal


REPORT_NAME = "pcg_field_volume_owned_grass_stage_report.json"
VOLUME_LABEL = "MCP_PCG_FieldVolumeOwnedGrass_Review"
SOURCE_LABEL = "MCP_PCG_FieldVolumeOwnedGrass_Source"
RUNTIME_ROAD_ACTOR_TAG = "CubelessRuntimeRoad"
RUNTIME_ROAD_SPLINE_NAME = "Road_SourceSpline"
BLOCK_TAG = "block"
ROAD_CLEARANCE_CM = __ROAD_CLEARANCE_CM__
SETTLE_SECONDS = __SETTLE_SECONDS__


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


def _tags(obj, prop):
    try:
        return [str(tag) for tag in obj.get_editor_property(prop)]
    except Exception:
        return []


def _has_tag_token(obj, prop, token):
    token = token.lower()
    return any(token in tag.lower() for tag in _tags(obj, prop))


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


def _object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _road_spline_points():
    for actor in _all_level_actors():
        if not _has_tag_token(actor, "tags", RUNTIME_ROAD_ACTOR_TAG):
            continue
        for spline in actor.get_components_by_class(unreal.SplineComponent):
            if spline.get_name() != RUNTIME_ROAD_SPLINE_NAME:
                continue
            points = []
            for index in range(spline.get_number_of_spline_points()):
                point = spline.get_location_at_spline_point(index, unreal.SplineCoordinateSpace.WORLD)
                points.append((float(point.x), float(point.y), float(point.z)))
            if len(points) >= 2:
                return points
    return []


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


def _collect_block_bounds():
    rows = []
    for actor in _all_level_actors():
        actor_is_block = _has_tag_token(actor, "tags", BLOCK_TAG)
        component_blocks = [
            component
            for component in actor.get_components_by_class(unreal.StaticMeshComponent)
            if _has_tag_token(component, "component_tags", BLOCK_TAG)
        ]
        if actor_is_block or component_blocks:
            try:
                origin, extent = actor.get_actor_bounds(False)
                rows.append(
                    {
                        "actor": _actor_label(actor),
                        "component": "ActorBounds",
                        "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
                        "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
                    }
                )
            except Exception:
                pass
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not actor_is_block and not _has_tag_token(component, "component_tags", BLOCK_TAG):
                continue
            try:
                bounds = component.bounds
                origin = bounds.origin
                extent = bounds.box_extent
            except Exception:
                try:
                    local_min, local_max = component.get_local_bounds()
                    transform = component.get_component_transform()
                    center = (local_min + local_max) * 0.5
                    extent = (local_max - local_min) * 0.5
                    origin = transform.transform_position(center)
                except Exception:
                    continue
            rows.append(
                {
                    "actor": _actor_label(actor),
                    "component": component.get_name(),
                    "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
                    "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
                }
            )
    return rows


def _inside_block(location, block_bounds, margin=120.0):
    for entry in block_bounds:
        mn = entry["min"]
        mx = entry["max"]
        if (
            mn[0] - margin <= location.x <= mx[0] + margin
            and mn[1] - margin <= location.y <= mx[1] + margin
            and mn[2] - margin <= location.z <= mx[2] + margin
        ):
            return True
    return False


def _collect_instances(actor, prune_block_overlaps=False):
    road_points = _road_spline_points()
    block_bounds = _collect_block_bounds()
    summary = {
        "actor": _actor_label(actor) if actor else None,
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "components": [],
        "road_points": len(road_points),
        "road_clearance_violations": 0,
        "block_tagged_component_count": len(block_bounds),
        "block_overlap_violations": 0,
        "block_overlap_samples": [],
        "road_violation_samples": [],
    }
    if not actor:
        return summary
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        category = _component_category(component)
        count = _instance_count(component)
        component_summary = {
            "component": component.get_name(),
            "category": category,
            "mesh": _mesh_path(component),
            "before": count,
            "after": count,
            "removed_block_overlaps": 0,
        }
        remove_indexes = []
        for index in range(count):
            try:
                transform = component.get_instance_transform(index, True)
            except Exception:
                continue
            location = transform.translation
            if category == "grass":
                distance = _road_distance_xy(location.x, location.y, road_points)
                if distance is not None and distance < ROAD_CLEARANCE_CM:
                    summary["road_clearance_violations"] += 1
                    if len(summary["road_violation_samples"]) < 20:
                        summary["road_violation_samples"].append(
                            {
                                "component": component.get_name(),
                                "index": index,
                                "distance": round(distance, 2),
                            }
                        )
                if _inside_block(location, block_bounds):
                    summary["block_overlap_violations"] += 1
                    remove_indexes.append(index)
                    if len(summary["block_overlap_samples"]) < 20:
                        summary["block_overlap_samples"].append(
                            {"component": component.get_name(), "index": index}
                        )
        if prune_block_overlaps and remove_indexes:
            for index in sorted(remove_indexes, reverse=True):
                try:
                    component.remove_instance(index)
                    component_summary["removed_block_overlaps"] += 1
                except Exception:
                    pass
            try:
                component.mark_render_state_dirty()
            except Exception:
                pass
            component_summary["after"] = _instance_count(component)
        final_count = component_summary["after"]
        summary["instances"]["all"] += final_count
        summary["instances"][category] += final_count
        summary["components"].append(component_summary)
    return summary


def _report_path():
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, REPORT_NAME)


def _load_report(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def validate_settled_stage():
    path = _report_path()
    report = _load_report(path)
    actor = _find_actor(VOLUME_LABEL)
    source = _find_actor(SOURCE_LABEL)
    final_summary = _collect_instances(actor, prune_block_overlaps=False)
    if final_summary.get("block_overlap_violations", 0) > 0:
        _collect_instances(actor, prune_block_overlaps=True)
        final_summary = _collect_instances(actor, prune_block_overlaps=False)
        report["settled_python_block_overlap_prune_applied"] = True
    else:
        report["settled_python_block_overlap_prune_applied"] = False
    report["settled_validation"] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "settle_seconds": SETTLE_SECONDS,
    }
    report["final_validation"] = final_summary
    report["source_actor"] = {
        "label": _actor_label(source) if source else None,
        "tags": _tags(source, "tags") if source else [],
        "grass_mesh": _object_path(source.get_editor_property("GrassMesh")) if source else None,
        "grass_material": _object_path(source.get_editor_property("GrassMaterial")) if source else None,
    }
    graph_info = report.get("graph", {}) if isinstance(report.get("graph", {}), dict) else {}
    report["pass"] = (
        final_summary["instances"].get("grass", 0) > 0
        and final_summary.get("road_clearance_violations", 0) == 0
        and final_summary.get("block_overlap_violations", 0) == 0
        and not graph_info.get("edge_errors")
    )
    report["success"] = True
    report["report_path"] = path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps(report, ensure_ascii=False))
    return report


validate_settled_stage()
"""


def parse_response(response: dict[str, Any] | None) -> dict[str, Any]:
    if not response:
        raise RuntimeError("No response from UnrealMCP bridge")
    if response.get("status") == "error":
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    result = response.get("result", response)
    logs = result.get("logs", []) if isinstance(result, dict) else []
    for line in reversed(logs):
        text = line.get("output", "") if isinstance(line, dict) else str(line)
        start = text.find("{")
        if start >= 0:
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                pass
    raise RuntimeError("Could not parse stage result")


def build_unreal_code(args: argparse.Namespace) -> str:
    return (
        UNREAL_CODE_TEMPLATE
        .replace("__POINTS_PER_SQM__", repr(float(args.points_per_sqm)))
        .replace("__ROAD_CLEARANCE_CM__", repr(float(args.road_clearance_cm)))
        .replace("__HIDE_OLD_SPLINE_GRASS__", "True" if args.hide_old_spline_grass else "False")
        .replace("__SAVE_DIRTY_PACKAGES__", "True" if args.save else "False")
    )


def build_validate_unreal_code(args: argparse.Namespace) -> str:
    return (
        VALIDATE_UNREAL_CODE_TEMPLATE
        .replace("__ROAD_CLEARANCE_CM__", repr(float(args.road_clearance_cm)))
        .replace("__SETTLE_SECONDS__", repr(float(args.settle_seconds)))
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    response = UnrealConnection().send_command(
        "execute_python",
        {
            "code": build_unreal_code(args),
            "mode": "ExecuteFile",
            "description": "Stage field volume-owned grass review layer",
        },
    )
    stage_report = parse_response(response)
    if args.settle_seconds > 0 and stage_report.get("success"):
        time.sleep(float(args.settle_seconds))
        validate_response = UnrealConnection().send_command(
            "execute_python",
            {
                "code": build_validate_unreal_code(args),
                "mode": "ExecuteFile",
                "description": "Validate settled field volume-owned grass review layer",
            },
        )
        return parse_response(validate_response)
    return stage_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage field volume-owned grass review layer.")
    parser.add_argument(
        "--points-per-sqm",
        type=float,
        default=1.15,
        help="Target point density used to derive the volume grid cell size.",
    )
    parser.add_argument(
        "--road-clearance-cm",
        type=float,
        default=950.0,
        help="Minimum road-spline clearance for generated grass points.",
    )
    parser.add_argument(
        "--hide-old-spline-grass",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Temporarily hide old broad spline grass actors for review.",
    )
    parser.add_argument(
        "--save",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save dirty map/content packages after staging.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=8.0,
        help="Seconds to wait outside Unreal before the settled validation pass.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
