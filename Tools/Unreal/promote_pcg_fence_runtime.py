"""Promote the validated open-spline fence PCG fixture into runtime assets.

This creates a dedicated fence runtime Blueprint/PCG graph instead of reusing
the broad ecosystem candidate Blueprint. The graph keeps the project rule that
open 2-point splines are valid for linear fence placement.
"""

from __future__ import annotations

import json
import math
import os
import time

import unreal


BP_FOLDER = "/Game/Cubeless/PCG/Runtime/Blueprints"
BP_NAME = "BP_Cubeless_PCG_FenceSourceRuntime"
BP_OBJECT = f"{BP_FOLDER}/{BP_NAME}.{BP_NAME}"
BP_CLASS = BP_OBJECT + "_C"

GRAPH_FOLDER = "/Game/Cubeless/PCG/Runtime/Graphs"
GRAPH_NAME = "PCG_Cubeless_FenceRuntime_Native"
GRAPH_OBJECT = f"{GRAPH_FOLDER}/{GRAPH_NAME}.{GRAPH_NAME}"

VALIDATION_LEVEL_PATH = "/Game/Cubeless/Map/LVL_Cubeless_PCG_Ecosystem_Field"
REPORT_NAME = "CubelessFenceRuntimePromotion_Report.json"
STATE_ATTR = "_cubeless_fence_runtime_promotion_state"

SOURCE_RUNTIME_TAG = "CubelessFenceRuntimeSource"
SOURCE_SELECTION_TAG = "PCGNativeFenceSource"
SOURCE_TAG = SOURCE_SELECTION_TAG
SOURCE_LABEL = "MCP_Cubeless_PCG_FenceRuntime_Source_Validation"
PCG_VOLUME_LABEL = "MCP_Cubeless_PCG_FenceRuntime_PCGVolume_Validation"
SPLINE_COMPONENT_NAME = "Fence_SourceSpline"

FENCE_MESH_OVERRIDE = "/Game/AI_Generated/Meshes/SM_Ieta_RoadFence_A.SM_Ieta_RoadFence_A"
FENCE_MESH_FALLBACK = (
    "/Game/AI_Generated/AIModeling/Additional_512/12_stair_retaining_wall_rail_module/"
    "Models/SM_12_stair_retaining_wall_rail_module.SM_12_stair_retaining_wall_rail_module"
)
FENCE_MATERIAL = "/Game/AI_Generated/Materials/M_Ieta_RoadFence_Metal.M_Ieta_RoadFence_Metal"
SEGMENT_SIZE_CM = 500.0
SPAWN_SETTLE_SECONDS = 0.75
GENERATION_SETTLE_SECONDS = 8.0

LOCAL_POINTS = [
    unreal.Vector(-4200.0, -750.0, 0.0),
    unreal.Vector(4200.0, 750.0, 0.0),
]


def _load_asset(path):
    return unreal.EditorAssetLibrary.load_asset(path) or unreal.load_object(None, path)


def _ensure_validation_level():
    world = unreal.EditorLevelLibrary.get_editor_world()
    world_before = world.get_path_name() if world else None
    if world_before and world_before.startswith(VALIDATION_LEVEL_PATH + "."):
        return {"loaded": False, "world_before": world_before, "world_after": world_before}
    unreal.EditorLevelLibrary.load_level(VALIDATION_LEVEL_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    world_after = world.get_path_name() if world else None
    return {"loaded": True, "world_before": world_before, "world_after": world_after}


def _object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name() if actor else ""


def _make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _set_actor_tags(actor, tags):
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])


def _configure_spline_component(spline):
    spline.modify()
    spline.clear_spline_points(True)
    for point in LOCAL_POINTS:
        spline.add_spline_point(point, unreal.SplineCoordinateSpace.LOCAL, True)
    for index in range(spline.get_number_of_spline_points()):
        try:
            spline.set_spline_point_type(index, unreal.SplinePointType.LINEAR, True)
        except Exception:
            pass
    spline.set_closed_loop(False, True)
    spline.update_spline()
    try:
        spline.set_editor_property(
            "component_tags",
            [
                unreal.Name("PCGOpenLinearSpline"),
                unreal.Name("PCGFenceGuide"),
                unreal.Name("PCGTwoPointOpenSpline"),
                unreal.Name(SOURCE_SELECTION_TAG),
                unreal.Name(SOURCE_RUNTIME_TAG),
            ],
        )
    except Exception:
        pass
    return spline


def _sample_ground_z(world, x, y, fallback_z=0.0):
    start = unreal.Vector(float(x), float(y), 50000.0)
    end = unreal.Vector(float(x), float(y), -10000.0)
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
        return float(fallback_z), False
    if not values or not bool(values[0]):
        return float(fallback_z), False
    try:
        actor = values[9]
        actor_name = actor.get_name() if actor else ""
        actor_class = actor.get_class().get_name() if actor else ""
    except Exception:
        actor_name = ""
        actor_class = ""
    if "Landscape" not in actor_name and "Landscape" not in actor_class:
        return float(fallback_z), False
    try:
        return float(values[4].z), True
    except Exception:
        return float(fallback_z), False


def _get_blueprint_subobject_rows(blueprint):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    rows = []
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        try:
            obj = library.get_associated_object(data)
        except Exception:
            obj = None
        rows.append(
            {
                "handle": handle,
                "object": obj,
                "display": str(library.get_display_name(data)),
                "variable": str(library.get_variable_name(data)),
                "class": obj.get_class().get_name() if obj else None,
                "path": obj.get_path_name() if obj else None,
                "is_root_component": bool(library.is_root_component(data)),
                "is_default_scene_root": bool(library.is_default_scene_root(data)),
            }
        )
    return rows


def _ensure_component_template(blueprint, component_class, component_name):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    rows = _get_blueprint_subobject_rows(blueprint)
    root_handle = None
    for row in rows:
        if row["is_default_scene_root"] or row["is_root_component"]:
            root_handle = row["handle"]
            break
    if root_handle is None:
        raise RuntimeError(f"{BP_NAME} has no root component handle.")

    matching = [
        row
        for row in rows
        if row["class"] == component_class.static_class().get_name()
        and (row["variable"] == component_name or row["display"] == component_name)
    ]
    if matching:
        return {"added": False, "row": matching[0], "rows": rows}

    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("blueprint_context", blueprint)
    params.set_editor_property("new_class", component_class)
    params.set_editor_property("parent_handle", root_handle)
    params.set_editor_property("skip_mark_blueprint_modified", False)
    params.set_editor_property("conform_transform_to_parent", True)
    new_handle, fail_reason = subsystem.add_new_subobject(params)
    if str(fail_reason):
        raise RuntimeError(f"Failed to add {component_name}: {fail_reason}")
    subsystem.rename_subobject(new_handle, unreal.Text(component_name))
    try:
        subsystem.rename_subobject_member_variable(blueprint, new_handle, unreal.Name(component_name))
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False)

    rows = _get_blueprint_subobject_rows(blueprint)
    matching = [
        row
        for row in rows
        if row["class"] == component_class.static_class().get_name()
        and (row["variable"] == component_name or row["display"] == component_name)
    ]
    if not matching:
        raise RuntimeError(f"Failed to find added component template: {component_name}")
    return {"added": True, "row": matching[0], "rows": rows}


def _blueprint_variable_exists(variable_name):
    try:
        cls = unreal.load_class(None, BP_CLASS)
        if cls:
            unreal.get_default_object(cls).get_editor_property(variable_name)
            return True
    except Exception:
        pass
    blueprint = _load_asset(BP_OBJECT)
    try:
        for desc in blueprint.get_editor_property("new_variables"):
            if str(desc.get_editor_property("var_name")) == variable_name:
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


def _ensure_fence_blueprint():
    if not unreal.EditorAssetLibrary.does_directory_exist(BP_FOLDER):
        unreal.EditorAssetLibrary.make_directory(BP_FOLDER)
    blueprint = _load_asset(BP_OBJECT)
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
        raise RuntimeError("Failed to create/load fence Blueprint: " + BP_OBJECT)

    spline_result = _ensure_component_template(blueprint, unreal.SplineComponent, SPLINE_COMPONENT_NAME)
    spline_template = spline_result["row"].get("object")
    if spline_template and spline_template.get_class().get_name() == "SplineComponent":
        _configure_spline_component(spline_template)

    mesh_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.StaticMesh.static_class())
    added_variables = []
    if not _blueprint_variable_exists("FenceMeshOverride"):
        if not unreal.BlueprintEditorLibrary.add_member_variable(blueprint, "FenceMeshOverride", mesh_type):
            raise RuntimeError("Failed to add FenceMeshOverride variable.")
        added_variables.append("FenceMeshOverride")
    _set_variable_editable(blueprint, "FenceMeshOverride", True)

    blueprint.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    cls = unreal.load_class(None, BP_CLASS)
    if not cls:
        raise RuntimeError("Failed to load fence Blueprint class after compile: " + BP_CLASS)

    cdo = unreal.get_default_object(cls)
    cdo.modify()
    cdo.set_editor_property("FenceMeshOverride", _load_asset(FENCE_MESH_OVERRIDE))
    try:
        cdo.set_editor_property(
            "tags",
            [
                unreal.Name(SOURCE_SELECTION_TAG),
                unreal.Name(SOURCE_RUNTIME_TAG),
                unreal.Name("PCGFenceGuide"),
            ],
        )
    except Exception:
        pass

    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False))
    return {
        "created": created,
        "saved": saved,
        "blueprint_path": BP_OBJECT,
        "class_path": BP_CLASS,
        "spline_component_added": spline_result["added"],
        "added_variables": added_variables,
        "default_mesh": FENCE_MESH_OVERRIDE,
    }


def _pin_label(pin):
    try:
        return str(pin.get_editor_property("properties").get_editor_property("label"))
    except Exception:
        return pin.get_name()


def _add_node(graph, settings_cls, title, x, y):
    created = graph.add_node_of_type(settings_cls.static_class())
    node = created[0] if isinstance(created, tuple) else created
    try:
        node.set_editor_property("node_title", title)
    except Exception:
        pass
    try:
        node.set_node_position(int(x), int(y))
    except Exception:
        try:
            node.set_node_position(unreal.Vector2D(float(x), float(y)))
        except Exception:
            pass
    return node


def _add_edge(graph, from_node, to_node, from_pin="Out", to_pin="In"):
    try:
        from_labels = [_pin_label(pin) for pin in from_node.output_pins]
        to_labels = [_pin_label(pin) for pin in to_node.input_pins]
        if from_pin not in from_labels or to_pin not in to_labels:
            raise RuntimeError(
                f"Missing pin {from_pin}->{to_pin}; from={from_labels}; to={to_labels}"
            )
        graph.add_edge(from_node, unreal.Name(from_pin), to_node, unreal.Name(to_pin))
        return {"ok": True, "from": from_node.get_name(), "to": to_node.get_name()}
    except Exception as exc:
        return {"ok": False, "from": from_node.get_name(), "to": to_node.get_name(), "error": str(exc)}


def _selector_import(settings, prop, text):
    selector = settings.get_editor_property(prop)
    selector.import_text(f"PCGBegin({text})PCGEnd")
    settings.set_editor_property(prop, selector)


def _configure_get_tagged_spline(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", SOURCE_TAG)
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


def _configure_subdivide_spline(node, route_length_cm):
    target_segments = max(1, int(math.ceil(float(route_length_cm) / SEGMENT_SIZE_CM)))
    active_point_target = target_segments + 2
    module_size = float(route_length_cm) / float(active_point_target)
    settings = node.get_settings()
    module = unreal.PCGSubdivisionSubmodule()
    module.set_editor_property("symbol", unreal.Name("F"))
    module.set_editor_property("size", float(module_size))
    module.set_editor_property("scalable", True)
    modules = settings.get_editor_property("modules_info")
    modules.clear()
    modules.append(module)
    settings.set_editor_property("modules_info", modules)
    grammar = settings.get_editor_property("grammar_selection")
    grammar.set_editor_property("grammar_string", "F*")
    settings.set_editor_property("grammar_selection", grammar)
    settings.set_editor_property("accept_incomplete_subdivision", True)
    settings.set_editor_property("module_height", 2.0)
    settings.set_editor_property("output_module_index_attribute", True)
    settings.set_editor_property("module_index_attribute_name", "FenceSegmentIndex")
    settings.set_editor_property("output_size_attribute", True)
    settings.set_editor_property("size_attribute_name", "FenceSegmentSizeCm")
    return {
        "route_length_cm": round(float(route_length_cm), 2),
        "target_segments": target_segments,
        "active_point_target": active_point_target,
        "module_size_cm": round(float(module_size), 2),
    }


def _configure_create_spline(node):
    settings = node.get_settings()
    settings.set_editor_property("mode", unreal.PCGCreateSplineMode.CREATE_DATA_ONLY)
    settings.set_editor_property("closed_loop", False)
    settings.set_editor_property("linear", True)
    settings.set_editor_property("apply_custom_tangents", False)


def _configure_get_actor_property(node, property_name, output_attr):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", SOURCE_TAG)
    actor_selector.set_editor_property("select_multiple", False)
    actor_selector.set_editor_property("ignore_self_and_children", False)
    settings.set_editor_property("actor_selector", actor_selector)
    settings.set_editor_property("property_name", property_name)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("force_object_and_struct_extraction", False)
    settings.set_editor_property("sanitize_output_attribute_name", True)
    _selector_import(settings, "output_attribute_name", output_attr)


def _configure_copy_actor_mesh(node, source_attr, target_attr):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    _selector_import(settings, "input_source", source_attr)
    _selector_import(settings, "output_target", target_attr)


def _object_property_override(input_attribute, property_target):
    override = unreal.PCGObjectPropertyOverrideDescription()
    override.import_text(
        '(InputSource=PCGBegin({})PCGEnd,PropertyTarget="{}")'.format(
            input_attribute,
            property_target,
        )
    )
    return override


def _configure_spawn_spline_mesh(node):
    settings = node.get_settings()
    descriptor = settings.get_editor_property("spline_mesh_descriptor")
    descriptor.set_editor_property("static_mesh", _load_asset(FENCE_MESH_FALLBACK))
    materials = descriptor.get_editor_property("override_materials")
    materials.clear()
    material = _load_asset(FENCE_MATERIAL)
    if material:
        materials.append(material)
    descriptor.set_editor_property("override_materials", materials)
    settings.set_editor_property("spline_mesh_descriptor", descriptor)

    params = settings.get_editor_property("spline_mesh_params")
    params.set_editor_property("forward_axis", unreal.PCGSplineMeshForwardAxis.X)
    settings.set_editor_property("spline_mesh_params", params)

    overrides = settings.get_editor_property("spline_mesh_override_descriptions")
    overrides.clear()
    overrides.append(_object_property_override("FenceMeshPath", "StaticMesh"))
    settings.set_editor_property("spline_mesh_override_descriptions", overrides)

    component_overrides = settings.get_editor_property("spline_mesh_component_override")
    component_overrides.clear()
    component_overrides.append(_object_property_override("FenceMeshPath", "StaticMesh"))
    settings.set_editor_property("spline_mesh_component_override", component_overrides)
    settings.set_editor_property("synchronous_load", True)


def _node_summary(node):
    return {
        "node": node.get_name(),
        "title": str(getattr(node, "node_title", "")),
        "settings_class": node.get_settings().get_class().get_name(),
        "input_pins": [{"label": _pin_label(pin), "connected": bool(pin.is_connected())} for pin in node.input_pins],
        "output_pins": [{"label": _pin_label(pin), "connected": bool(pin.is_connected())} for pin in node.output_pins],
    }


def _create_or_update_graph(route_length_cm):
    if not unreal.EditorAssetLibrary.does_directory_exist(GRAPH_FOLDER):
        unreal.EditorAssetLibrary.make_directory(GRAPH_FOLDER)
    graph = _load_asset(GRAPH_OBJECT)
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
        raise RuntimeError("Failed to create/load fence graph: " + GRAPH_OBJECT)

    for node in list(graph.nodes):
        graph.remove_node(node)

    nodes = {
        "get_spline": _add_node(graph, unreal.PCGGetSplineSettings, "Get Fence Source Spline", 0, 0),
        "subdivide": _add_node(graph, unreal.PCGSubdivideSplineSettings, "Subdivide Fence Spline", 360, 0),
        "create_spline": _add_node(graph, unreal.PCGCreateSplineSettings, "Recreate Open Fence Spline", 720, 0),
        "get_mesh": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor FenceMeshOverride", 720, -280),
        "copy_mesh": _add_node(graph, unreal.PCGCopyAttributesSettings, "Copy Fence Mesh To Spawn Attribute", 1080, -120),
        "spawn": _add_node(graph, unreal.PCGSpawnSplineMeshSettings, "Spawn Fence SplineMesh By Actor Property", 1440, 0),
    }
    _configure_get_tagged_spline(nodes["get_spline"])
    subdivide = _configure_subdivide_spline(nodes["subdivide"], route_length_cm)
    _configure_create_spline(nodes["create_spline"])
    _configure_get_actor_property(nodes["get_mesh"], "FenceMeshOverride", "FenceMeshOverride")
    _configure_copy_actor_mesh(nodes["copy_mesh"], "FenceMeshOverride", "FenceMeshPath")
    _configure_spawn_spline_mesh(nodes["spawn"])

    edges = [
        _add_edge(graph, nodes["get_spline"], nodes["subdivide"], "Out", "In"),
        _add_edge(graph, nodes["subdivide"], nodes["create_spline"], "Out", "In"),
        _add_edge(graph, nodes["create_spline"], nodes["copy_mesh"], "Out", "Target"),
        _add_edge(graph, nodes["get_mesh"], nodes["copy_mesh"], "Out", "Source"),
        _add_edge(graph, nodes["copy_mesh"], nodes["spawn"], "Out", "In"),
        _add_edge(graph, nodes["spawn"], graph.get_output_node(), "Out", "Out"),
    ]
    try:
        graph.description = (
            "Runtime fence graph for open 2-point or longer linear splines. "
            "Consumes a tagged BP_Cubeless_PCG_FenceSourceRuntime source and spawns spline mesh fence segments."
        )
        graph.get_input_node().set_node_position(-260, 0)
        graph.get_output_node().set_node_position(1780, 0)
    except Exception:
        pass
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(graph, False))
    return {
        "created": created,
        "saved": saved,
        "graph_path": GRAPH_OBJECT,
        "edge_count": len([edge for edge in edges if edge.get("ok")]),
        "edge_errors": [edge for edge in edges if not edge.get("ok")],
        "segment_size_cm": SEGMENT_SIZE_CM,
        "subdivide": subdivide,
        "nodes": [_node_summary(node) for node in list(graph.nodes) + [graph.get_output_node()]],
    }


def _find_actor(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _delete_validation_actor():
    deleted = []
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        label = _actor_label(actor)
        if label not in {SOURCE_LABEL, PCG_VOLUME_LABEL}:
            continue
        for component in actor.get_components_by_class(unreal.PCGComponent):
            try:
                component.cleanup(True)
            except Exception:
                pass
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted.append(label)
        except Exception:
            pass
    return deleted


def _configure_open_spline(actor):
    splines = actor.get_components_by_class(unreal.SplineComponent)
    if not splines:
        raise RuntimeError("Fence runtime actor has no SplineComponent.")
    return _configure_spline_component(splines[0])


def _route_length_from_spline(spline):
    try:
        return float(spline.get_spline_length())
    except Exception:
        start, end = LOCAL_POINTS
        return math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)


def _spawn_validation_actor():
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world is loaded.")
    actor_class = unreal.load_class(None, BP_CLASS)
    if not actor_class:
        raise RuntimeError("Missing fence runtime class: " + BP_CLASS)
    _delete_validation_actor()
    origin_x = 23800.0
    origin_y = 13300.0
    origin_z, _hit_landscape = _sample_ground_z(world, origin_x, origin_y, 0.0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        unreal.Vector(origin_x, origin_y, origin_z),
        _make_rotator(0.0, 10.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn fence runtime validation actor.")
    actor.set_actor_label(SOURCE_LABEL)
    _set_actor_tags(
        actor,
        [
            SOURCE_SELECTION_TAG,
            SOURCE_RUNTIME_TAG,
            "PCGFenceGuide",
            "PCGTwoPointOpenSpline",
            "MCPValidation",
        ],
    )
    actor.set_editor_property("FenceMeshOverride", _load_asset(FENCE_MESH_OVERRIDE))
    spline = _configure_open_spline(actor)
    return actor, spline


def _spawn_validation_pcg_volume():
    world = unreal.EditorLevelLibrary.get_editor_world()
    origin_x = 23800.0
    origin_y = 13300.0
    origin_z, _hit_landscape = _sample_ground_z(world, origin_x, origin_y, 0.0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PCGVolume,
        unreal.Vector(origin_x, origin_y, origin_z + 500.0),
        _make_rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn fence runtime validation PCGVolume.")
    actor.set_actor_label(PCG_VOLUME_LABEL)
    try:
        actor.set_actor_scale3d(unreal.Vector(140.0, 80.0, 20.0))
    except Exception:
        pass
    _set_actor_tags(actor, ["MCPValidation", "CubelessFenceRuntimeVolume"])
    return actor


def _configure_actor_pcg(actor, graph):
    components = actor.get_components_by_class(unreal.PCGComponent)
    if not components:
        raise RuntimeError("Fence runtime validation PCGVolume has no PCGComponent.")
    component = components[0]
    try:
        component.cleanup(True)
    except Exception:
        pass
    try:
        component.set_editor_property("activated", True)
    except Exception:
        pass
    component.activate(True)
    component.set_graph(graph)
    try:
        component.notify_properties_changed_from_blueprint()
    except Exception:
        pass
    try:
        component.set_editor_property("seed", 6122032)
    except Exception:
        pass
    component.generate(True)
    try:
        component.generate_local(True)
    except Exception:
        pass
    return {"component": component.get_name(), "graph": _object_path(graph)}


def _spline_mesh_rows(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.SplineMeshComponent):
        mesh_path = None
        materials = []
        try:
            mesh_path = _object_path(component.get_editor_property("static_mesh"))
        except Exception:
            pass
        try:
            for index in range(component.get_num_materials()):
                materials.append(_object_path(component.get_material(index)))
        except Exception:
            pass
        rows.append({"component": component.get_name(), "mesh": mesh_path, "materials": materials})
    return rows


def _validate(source_actor, spline, generated_actor):
    rows = _spline_mesh_rows(generated_actor)
    meshes = sorted({row.get("mesh") for row in rows if row.get("mesh")})
    actor_mesh = _object_path(source_actor.get_editor_property("FenceMeshOverride"))
    route_length = _route_length_from_spline(spline)
    validation = {
        "source_actor": _actor_label(source_actor),
        "generated_actor": _actor_label(generated_actor),
        "spline_closed_loop": bool(spline.is_closed_loop()),
        "spline_point_count": int(spline.get_number_of_spline_points()),
        "spline_length": round(route_length, 2),
        "expected_min_segments": max(1, int(math.floor(route_length / SEGMENT_SIZE_CM))),
        "actor_property_mesh": actor_mesh,
        "descriptor_fallback_mesh": FENCE_MESH_FALLBACK,
        "spline_mesh_component_count": len(rows),
        "output_meshes": meshes,
        "rows": rows[:40],
    }
    validation["native_spawn_pass"] = len(rows) > 0
    validation["actor_property_mesh_override_pass"] = bool(rows) and meshes == [actor_mesh]
    validation["descriptor_fallback_used"] = FENCE_MESH_FALLBACK in meshes
    validation["pass"] = (
        not validation["spline_closed_loop"]
        and validation["spline_point_count"] == 2
        and validation["native_spawn_pass"]
        and validation["actor_property_mesh_override_pass"]
    )
    return validation


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, REPORT_NAME)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"report": path, **report}, ensure_ascii=False))
    return path


def promote_pcg_fence_runtime():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle"):
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    state = {
        "started_at": time.time(),
        "generation_started_at": None,
        "handle": None,
        "completed": False,
        "source_spawned": False,
        "generation_started": False,
        "level_load": None,
        "graph_update": None,
        "blueprint_update": None,
        "component_update": None,
    }

    def _tick(_delta_seconds):
        if state["completed"]:
            return False

        if not state["source_spawned"]:
            try:
                state["level_load"] = _ensure_validation_level()
                state["blueprint_update"] = _ensure_fence_blueprint()
                _spawn_validation_actor()
                _spawn_validation_pcg_volume()
                state["source_spawned"] = True
                return True
            except Exception as exc:
                state["completed"] = True
                _write_report(
                    {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "failed",
                        "pass": False,
                        "stage": "source_setup",
                        "error": str(exc),
                        "blueprint_update": state.get("blueprint_update"),
                    }
                )
                return False

        if not state["generation_started"]:
            if time.time() - state["started_at"] < SPAWN_SETTLE_SECONDS:
                return True
            try:
                settled_actor = _find_actor(SOURCE_LABEL)
                if not settled_actor:
                    raise RuntimeError("Validation source actor disappeared: " + SOURCE_LABEL)
                settled_pcg_actor = _find_actor(PCG_VOLUME_LABEL)
                if not settled_pcg_actor:
                    raise RuntimeError("Validation PCGVolume disappeared: " + PCG_VOLUME_LABEL)
                settled_spline = _configure_open_spline(settled_actor)
                route_length = _route_length_from_spline(settled_spline)
                state["graph_update"] = _create_or_update_graph(route_length)
                graph = _load_asset(GRAPH_OBJECT)
                state["component_update"] = _configure_actor_pcg(settled_pcg_actor, graph)
                state["generation_started"] = True
                state["generation_started_at"] = time.time()
                return True
            except Exception as exc:
                state["completed"] = True
                _write_report(
                    {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "failed",
                        "pass": False,
                        "stage": "pcg_setup",
                        "error": str(exc),
                        "blueprint_update": state.get("blueprint_update"),
                        "graph_update": state.get("graph_update"),
                    }
                )
                return False

        if time.time() - float(state["generation_started_at"] or state["started_at"]) < GENERATION_SETTLE_SECONDS:
            return True
        state["completed"] = True
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        try:
            settled_actor = _find_actor(SOURCE_LABEL)
            if not settled_actor:
                raise RuntimeError("Validation actor disappeared: " + SOURCE_LABEL)
            settled_pcg_actor = _find_actor(PCG_VOLUME_LABEL)
            if not settled_pcg_actor:
                raise RuntimeError("Validation PCGVolume disappeared: " + PCG_VOLUME_LABEL)
            settled_spline = _configure_open_spline(settled_actor)
            validation = _validate(settled_actor, settled_spline, settled_pcg_actor)
            dirty_content = []
            dirty_maps = []
            try:
                dirty_content = [
                    package.get_name()
                    for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
                ]
                dirty_maps = [
                    package.get_name()
                    for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
                ]
            except Exception:
                pass
            report = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
                "level_load": state.get("level_load"),
                "policy": {
                    "separate_from_ecosystem_candidate": True,
                    "open_2_point_spline": "valid for fence/guide/linear placement",
                    "level_save_attempted": False,
                    "mesh_override_rule": "Fence mesh is read from BP actor property FenceMeshOverride",
                },
                "graph_update": state["graph_update"],
                "blueprint_update": state["blueprint_update"],
                "component_update": state["component_update"],
                "validation": validation,
                "dirty_content_packages": dirty_content,
                "dirty_map_packages": dirty_maps,
            }
            report["pass"] = bool(validation.get("pass"))
            _write_report(report)
        except Exception as exc:
            _write_report(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "failed",
                    "pass": False,
                    "error": str(exc),
                    "graph_update": state.get("graph_update"),
                    "blueprint_update": state.get("blueprint_update"),
                    "component_update": state.get("component_update"),
                }
            )
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)
    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "scheduled",
        "wait_seconds": 8.0,
        "blueprint": BP_OBJECT,
        "graph": GRAPH_OBJECT,
        "validation_actor": SOURCE_LABEL,
        "validation_pcg_volume": PCG_VOLUME_LABEL,
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


def promote_pcg_fence_runtime_direct():
    """Run the promotion synchronously for commandlet/fallback execution."""
    level_load = _ensure_validation_level()
    deleted_existing = _delete_validation_actor()
    blueprint_update = _ensure_fence_blueprint()
    source_actor, spline = _spawn_validation_actor()
    pcg_actor = _spawn_validation_pcg_volume()
    time.sleep(SPAWN_SETTLE_SECONDS)
    route_length = _route_length_from_spline(spline)
    graph_update = _create_or_update_graph(route_length)
    graph = _load_asset(GRAPH_OBJECT)
    component_update = _configure_actor_pcg(pcg_actor, graph)
    time.sleep(GENERATION_SETTLE_SECONDS)
    settled_source = _find_actor(SOURCE_LABEL) or source_actor
    settled_pcg_actor = _find_actor(PCG_VOLUME_LABEL) or pcg_actor
    settled_spline = _configure_open_spline(settled_source)
    validation = _validate(settled_source, settled_spline, settled_pcg_actor)
    dirty_content = []
    dirty_maps = []
    try:
        dirty_content = [
            package.get_name()
            for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
        ]
        dirty_maps = [
            package.get_name()
            for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
        ]
    except Exception:
        pass
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "direct_commandlet_safe",
        "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
        "level_load": level_load,
        "deleted_existing_validation_actors": deleted_existing,
        "policy": {
            "separate_from_ecosystem_candidate": True,
            "open_2_point_spline": "valid for fence/guide/linear placement",
            "level_save_attempted": False,
            "mesh_override_rule": "Fence mesh is read from BP actor property FenceMeshOverride",
        },
        "graph_update": graph_update,
        "blueprint_update": blueprint_update,
        "component_update": component_update,
        "validation": validation,
        "dirty_content_packages": dirty_content,
        "dirty_map_packages": dirty_maps,
    }
    report["pass"] = bool(validation.get("pass"))
    _write_report(report)
    try:
        _delete_validation_actor()
    except Exception:
        pass
    return report


if __name__ == "__main__":
    if "--direct" in os.sys.argv:
        promote_pcg_fence_runtime_direct()
    else:
        promote_pcg_fence_runtime()
