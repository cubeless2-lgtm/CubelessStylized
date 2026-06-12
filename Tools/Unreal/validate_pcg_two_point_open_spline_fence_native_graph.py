"""Validate native PCG linear mesh output for a 2-point open fence spline.

This promotes the simpler SplineMeshActor fixture into a PCG graph fixture:
- source spline must stay open with exactly 2 points
- PCG graph must consume that spline as a linear source
- SpawnSplineMesh should output fence components
- mesh selection should be driven by an actor property when the engine exposes
  enough override support for the SplineMesh descriptor

All assets are disposable validation assets under _MCP_Temp.
"""

import json
import math
import os
import time

import unreal


LEVEL_PATH = "/Game/_MCP_Temp/PCG/LVL_Cubeless_PCG_IntentGallery_MCP"
SOURCE_LABEL = "MCP_PCG_TwoPointOpenFenceNative_Source"
PCG_VOLUME_LABEL = "MCP_PCG_TwoPointOpenFenceNative_PCGVolume"
GRAPH_FOLDER = "/Game/_MCP_Temp/PCG/Graphs"
GRAPH_NAME = "PCG_Cubeless_TwoPointOpenFenceNative_MCP"
GRAPH_OBJECT = GRAPH_FOLDER + "/" + GRAPH_NAME + "." + GRAPH_NAME
REPORT_NAME = "CubelessTwoPointOpenSplineFenceNativeGraph_Report.json"
SETTLE_SECONDS = 8.0
SPAWN_SETTLE_SECONDS = 0.75
STATE_ATTR = "_cubeless_two_point_open_spline_fence_native_state"

BP_OBJECT_PATH = (
    "/Game/_MCP_Temp/PCG/Blueprints/"
    "BP_Cubeless_ClosedSplineAreaAuthoring.BP_Cubeless_ClosedSplineAreaAuthoring"
)
BP_CLASS_PATH = BP_OBJECT_PATH + "_C"

FENCE_MESH_OVERRIDE = "/Game/AI_Generated/Meshes/SM_Ieta_RoadFence_A.SM_Ieta_RoadFence_A"
FENCE_MESH_FALLBACK = (
    "/Game/AI_Generated/AIModeling/Additional_512/12_stair_retaining_wall_rail_module/"
    "Models/SM_12_stair_retaining_wall_rail_module.SM_12_stair_retaining_wall_rail_module"
)
FENCE_MATERIAL = "/Game/AI_Generated/Materials/M_Ieta_RoadFence_Metal.M_Ieta_RoadFence_Metal"

LOCAL_POINTS = [
    unreal.Vector(-4200.0, -750.0, 0.0),
    unreal.Vector(4200.0, 750.0, 0.0),
]


def _make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _load_level():
    world = unreal.EditorLevelLibrary.get_editor_world()
    current_path = world.get_path_name() if world else ""
    if current_path.startswith(LEVEL_PATH + "."):
        return {"loaded": False, "world_before": current_path}
    unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    return {"loaded": True, "world_before": current_path, "world_after": world.get_path_name()}


def _actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return ""


def _find_actor(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _delete_existing():
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


def _sample_ground_z(world, x, y, fallback_z=0.0):
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
        return fallback_z, False
    if not values or not bool(values[0]):
        return fallback_z, False
    try:
        actor = values[9]
        actor_name = actor.get_name() if actor else ""
        actor_class = actor.get_class().get_name() if actor else ""
    except Exception:
        actor_name = ""
        actor_class = ""
    if "Landscape" not in actor_name and "Landscape" not in actor_class:
        return fallback_z, False
    try:
        return float(values[4].z), True
    except Exception:
        return fallback_z, False


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


def _set_actor_tags(actor, tags):
    try:
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])
    except Exception:
        pass


def _blueprint_variable_exists(blueprint, variable_name):
    try:
        cls = unreal.EditorAssetLibrary.load_blueprint_class(BP_OBJECT_PATH)
        if cls:
            cdo = unreal.get_default_object(cls)
            cdo.get_editor_property(variable_name)
            return True
    except Exception:
        pass
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


def _ensure_blueprint_fence_variables():
    blueprint = _load_asset(BP_OBJECT_PATH)
    if not blueprint:
        raise RuntimeError("Missing validation Blueprint: " + BP_OBJECT_PATH)
    bool_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    mesh_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.StaticMesh.static_class())
    specs = [
        ("UseFenceMeshOverride", bool_type, True),
        ("FenceMeshOverride", mesh_type, FENCE_MESH_OVERRIDE),
    ]
    added = []
    for name, pin_type, _default_value in specs:
        if _blueprint_variable_exists(blueprint, name):
            continue
        if not unreal.BlueprintEditorLibrary.add_member_variable(blueprint, name, pin_type):
            raise RuntimeError("Failed to add Blueprint variable: " + name)
        added.append(name)
    for name, _pin_type, _default_value in specs:
        _set_variable_editable(blueprint, name, True)
    blueprint.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    cls = unreal.EditorAssetLibrary.load_blueprint_class(BP_OBJECT_PATH)
    if not cls:
        raise RuntimeError("Failed to load validation Blueprint class: " + BP_OBJECT_PATH)
    cdo = unreal.get_default_object(cls)
    cdo.modify()
    cdo.set_editor_property("UseFenceMeshOverride", True)
    cdo.set_editor_property("FenceMeshOverride", _load_asset(FENCE_MESH_OVERRIDE))
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(blueprint))
    return {"added": added, "saved": saved}


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
        try:
            node.node_title = title
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
        if from_pin not in from_labels:
            raise RuntimeError("missing output pin {} on {}; available={}".format(
                from_pin, from_node.get_name(), from_labels
            ))
        if to_pin not in to_labels:
            raise RuntimeError("missing input pin {} on {}; available={}".format(
                to_pin, to_node.get_name(), to_labels
            ))
        graph.add_edge(from_node, unreal.Name(from_pin), to_node, unreal.Name(to_pin))
        return {"from": from_node.get_name(), "from_pin": from_pin, "to": to_node.get_name(), "to_pin": to_pin, "ok": True}
    except Exception as exc:
        return {"from": from_node.get_name(), "from_pin": from_pin, "to": to_node.get_name(), "to_pin": to_pin, "ok": False, "error": str(exc)}


def _selector_import(settings, prop, text):
    selector = settings.get_editor_property(prop)
    selector.import_text("PCGBegin({})PCGEnd".format(text))
    settings.set_editor_property(prop, selector)


def _configure_get_actor_property(node, property_name, output_attr):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", "PCGNativeFenceSource")
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


def _configure_get_tagged_spline(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", "PCGNativeFenceSource")
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
    target_segments = max(1, int(math.ceil(route_length_cm / 500.0)))
    active_point_target = target_segments + 2
    module_size = route_length_cm / float(active_point_target)
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
        "route_length_cm": round(route_length_cm, 2),
        "target_segments": target_segments,
        "active_point_target": active_point_target,
        "module_size_cm": round(module_size, 2),
    }


def _configure_create_spline(node):
    settings = node.get_settings()
    settings.set_editor_property("mode", unreal.PCGCreateSplineMode.CREATE_DATA_ONLY)
    settings.set_editor_property("closed_loop", False)
    settings.set_editor_property("linear", True)
    settings.set_editor_property("apply_custom_tangents", False)


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
    override_attribute_candidates = ["FenceMeshPath"]
    descriptor_target_candidates = [
        "StaticMesh",
    ]
    component_target_candidates = [
        "StaticMesh",
    ]
    overrides = settings.get_editor_property("spline_mesh_override_descriptions")
    overrides.clear()
    for attribute_name in override_attribute_candidates:
        for target_name in descriptor_target_candidates:
            overrides.append(_object_property_override(attribute_name, target_name))
    settings.set_editor_property("spline_mesh_override_descriptions", overrides)
    component_overrides = settings.get_editor_property("spline_mesh_component_override")
    component_overrides.clear()
    for attribute_name in override_attribute_candidates:
        for target_name in component_target_candidates:
            component_overrides.append(_object_property_override(attribute_name, target_name))
    settings.set_editor_property("spline_mesh_component_override", component_overrides)
    settings.set_editor_property("synchronous_load", True)
    return {
        "descriptor_fallback_mesh": FENCE_MESH_FALLBACK,
        "expected_actor_property_mesh": FENCE_MESH_OVERRIDE,
        "override_attribute_candidates": override_attribute_candidates,
        "descriptor_target_candidates": descriptor_target_candidates,
        "component_target_candidates": component_target_candidates,
    }


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
    graph = unreal.load_object(None, GRAPH_OBJECT)
    created = False
    if not graph:
        factory = unreal.PCGGraphFactory()
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            GRAPH_NAME,
            GRAPH_FOLDER,
            unreal.PCGGraph,
            factory,
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load graph: " + GRAPH_OBJECT)
    for node in list(graph.nodes):
        graph.remove_node(node)
    nodes = {
        "get_spline": _add_node(graph, unreal.PCGGetSplineSettings, "Get Tagged 2-Point Fence Spline", 0, 0),
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
    spawn = _configure_spawn_spline_mesh(nodes["spawn"])
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
            "Validation graph for open 2-point fence splines. Keeps 2-point open spline intent separate from closed area generation."
        )
        graph.get_input_node().set_node_position(-260, 0)
        graph.get_output_node().set_node_position(1780, 0)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(graph, False)
    return {
        "created": created,
        "graph": graph,
        "graph_path": graph.get_path_name(),
        "subdivide": subdivide,
        "spawn": spawn,
        "edge_count": len([edge for edge in edges if edge.get("ok")]),
        "edge_errors": [edge for edge in edges if not edge.get("ok")],
        "nodes": [_node_summary(node) for node in list(graph.nodes) + [graph.get_output_node()]],
    }


def _configure_open_spline(actor):
    splines = actor.get_components_by_class(unreal.SplineComponent)
    if not splines:
        raise RuntimeError("Source actor has no SplineComponent.")
    spline = splines[0]
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
                unreal.Name("PCGNativeFenceSource"),
            ],
        )
    except Exception:
        pass
    return spline


def _spawn_source_actor(world):
    actor_class = unreal.load_object(None, BP_CLASS_PATH)
    if not actor_class:
        raise RuntimeError("Missing source Blueprint class: " + BP_CLASS_PATH)
    origin_x = 23800.0
    origin_y = 13300.0
    origin_z, hit_landscape = _sample_ground_z(world, origin_x, origin_y, 0.0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        unreal.Vector(origin_x, origin_y, origin_z),
        _make_rotator(0.0, 10.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn native fence source actor.")
    actor.set_actor_label(SOURCE_LABEL)
    _set_actor_tags(
        actor,
        [
            "MCPValidation",
            "PCGOpenLinearSpline",
            "PCGFenceGuide",
            "PCGTwoPointOpenSpline",
            "PCGNativeFenceSource",
        ],
    )
    actor.set_editor_property("UseFenceMeshOverride", True)
    actor.set_editor_property("FenceMeshOverride", _load_asset(FENCE_MESH_OVERRIDE))
    spline = _configure_open_spline(actor)
    return actor, spline, hit_landscape


def _spawn_pcg_volume(world):
    origin_x = 23800.0
    origin_y = 13300.0
    origin_z, _hit_landscape = _sample_ground_z(world, origin_x, origin_y, 0.0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PCGVolume,
        unreal.Vector(origin_x, origin_y, origin_z + 500.0),
        _make_rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn native fence PCGVolume.")
    actor.set_actor_label(PCG_VOLUME_LABEL)
    try:
        actor.set_actor_scale3d(unreal.Vector(140.0, 80.0, 20.0))
    except Exception:
        pass
    _set_actor_tags(actor, ["MCPValidation", "PCGNativeFenceVolume"])
    return actor


def _route_length_from_spline(spline):
    try:
        return float(spline.get_spline_length())
    except Exception:
        start = LOCAL_POINTS[0]
        end = LOCAL_POINTS[1]
        return math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)


def _configure_component(actor, graph):
    components = [
        component
        for component in actor.get_components_by_class(unreal.PCGComponent)
        if not component.get_name().startswith("TRASH_")
    ]
    if not components:
        components = list(actor.get_components_by_class(unreal.PCGComponent))
    if not components:
        raise RuntimeError("Source actor has no PCGComponent.")
    component = components[0]
    try:
        component.cleanup(True)
    except Exception:
        pass
    component.activate(True)
    component.set_graph(graph)
    try:
        component.set_editor_property("seed", 6122031)
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
                material = component.get_material(index)
                materials.append(_object_path(material))
        except Exception:
            pass
        rows.append(
            {
                "component": component.get_name(),
                "mesh": mesh_path,
                "materials": materials,
            }
        )
    return rows


def _validate(source_actor, spline, generated_actor):
    rows = _spline_mesh_rows(generated_actor)
    meshes = sorted({row.get("mesh") for row in rows if row.get("mesh")})
    actor_mesh = _object_path(source_actor.get_editor_property("FenceMeshOverride"))
    fallback_mesh = FENCE_MESH_FALLBACK
    validation = {
        "source_actor": _actor_label(source_actor),
        "generated_actor": _actor_label(generated_actor),
        "spline_closed_loop": bool(spline.is_closed_loop()),
        "spline_point_count": int(spline.get_number_of_spline_points()),
        "spline_length": round(float(spline.get_spline_length()), 2),
        "actor_property_mesh": actor_mesh,
        "descriptor_fallback_mesh": fallback_mesh,
        "spline_mesh_component_count": len(rows),
        "output_meshes": meshes,
        "rows": rows[:40],
    }
    validation["native_spawn_pass"] = len(rows) > 0
    validation["actor_property_mesh_override_pass"] = bool(rows) and meshes == [actor_mesh]
    validation["descriptor_fallback_used"] = fallback_mesh in meshes
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
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report_path


def validate_two_point_open_spline_fence_native_graph():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle"):
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    level_load = _load_level()
    world = unreal.EditorLevelLibrary.get_editor_world()
    deleted_existing = _delete_existing()
    blueprint_update = _ensure_blueprint_fence_variables()
    actor, spline, hit_landscape = _spawn_source_actor(world)
    pcg_actor = _spawn_pcg_volume(world)
    state = {
        "started_at": time.time(),
        "generation_started_at": None,
        "handle": None,
        "completed": False,
        "setup_done": False,
        "level_load": level_load,
        "deleted_existing": deleted_existing,
        "blueprint_update": blueprint_update,
        "hit_landscape": hit_landscape,
        "pcg_volume_actor": PCG_VOLUME_LABEL,
        "graph_update": None,
        "component_update": None,
    }

    def _tick(_delta_seconds):
        if state["completed"]:
            return False

        if not state["setup_done"]:
            if time.time() - state["started_at"] < SPAWN_SETTLE_SECONDS:
                return True
            try:
                settled_actor = _find_actor(SOURCE_LABEL)
                if not settled_actor:
                    raise RuntimeError("Source actor disappeared before setup: " + SOURCE_LABEL)
                settled_pcg_actor = _find_actor(PCG_VOLUME_LABEL)
                if not settled_pcg_actor:
                    raise RuntimeError("PCGVolume disappeared before setup: " + PCG_VOLUME_LABEL)
                settled_actor.set_editor_property("UseFenceMeshOverride", True)
                settled_actor.set_editor_property("FenceMeshOverride", _load_asset(FENCE_MESH_OVERRIDE))
                settled_spline = _configure_open_spline(settled_actor)
                route_length = _route_length_from_spline(settled_spline)
                graph_update = _create_or_update_graph(route_length)
                component_update = _configure_component(settled_pcg_actor, graph_update["graph"])
                state["graph_update"] = {key: value for key, value in graph_update.items() if key != "graph"}
                state["component_update"] = component_update
                state["generation_started_at"] = time.time()
                state["setup_done"] = True
                return True
            except Exception as exc:
                state["completed"] = True
                _write_report(
                    {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "failed",
                        "pass": False,
                        "error": str(exc),
                        "stage": "settled_setup",
                        "level_load": state.get("level_load", {}),
                    }
                )
                return False

        if time.time() - float(state["generation_started_at"] or state["started_at"]) < SETTLE_SECONDS:
            return True
        state["completed"] = True
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        try:
            settled_actor = _find_actor(SOURCE_LABEL)
            if not settled_actor:
                raise RuntimeError("Source actor disappeared: " + SOURCE_LABEL)
            settled_pcg_actor = _find_actor(PCG_VOLUME_LABEL)
            if not settled_pcg_actor:
                raise RuntimeError("PCGVolume disappeared: " + PCG_VOLUME_LABEL)
            settled_spline = _configure_open_spline(settled_actor)
            validation = _validate(settled_actor, settled_spline, settled_pcg_actor)
            try:
                unreal.EditorLevelLibrary.save_current_level()
                save_current_level = True
            except Exception as exc:
                save_current_level = "failed: " + str(exc)
            world_now = unreal.EditorLevelLibrary.get_editor_world()
            report = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "world": world_now.get_path_name() if world_now else None,
                "policy": {
                    "open_2_point_spline": "native PCG linear mesh path must remain valid",
                    "closed_area_spline": "separate 3+ point area-mask case; not used by this fixture",
                    "mesh_override_rule": "Spline mesh output should use the source actor FenceMeshOverride property when possible",
                },
                "level_load": state["level_load"],
                "deleted_existing": state["deleted_existing"],
                "blueprint_update": state["blueprint_update"],
                "hit_landscape": state["hit_landscape"],
                "pcg_volume_actor": state["pcg_volume_actor"],
                "graph_update": state.get("graph_update"),
                "component_update": state.get("component_update"),
                "validation": validation,
                "save_current_level": save_current_level,
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
                    "level_load": state.get("level_load", {}),
                }
            )
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)
    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "scheduled",
        "wait_seconds": SPAWN_SETTLE_SECONDS + SETTLE_SECONDS,
        "source_actor": SOURCE_LABEL,
        "pcg_volume_actor": PCG_VOLUME_LABEL,
        "graph": GRAPH_OBJECT,
        "component": "deferred until spawned actor settles",
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    validate_two_point_open_spline_fence_native_graph()
