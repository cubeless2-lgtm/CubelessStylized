import json
import pathlib

import unreal


RUNTIME_BLUEPRINT_OBJECT = (
    "/Game/Cubeless/PCG/Runtime/Blueprints/"
    "BP_Cubeless_PCG_EcosystemRuntime.BP_Cubeless_PCG_EcosystemRuntime"
)
RUNTIME_BLUEPRINT_CLASS = RUNTIME_BLUEPRINT_OBJECT + "_C"

VALIDATION_GRAPH_PACKAGE = "/Game/_MCP_Temp/PCG"
VALIDATION_GRAPH_ASSET = "PCG_MCP_MaterialOverrideActorPropertyValidation"
VALIDATION_GRAPH_OBJECT = (
    f"{VALIDATION_GRAPH_PACKAGE}/{VALIDATION_GRAPH_ASSET}.{VALIDATION_GRAPH_ASSET}"
)
VALIDATION_ACTOR_LABEL = "MCP_Cubeless_PCG_MaterialOverrideActorProperty_Validation"

REPORT_PATH = "Saved/MCP_PCG/pcg_material_override_actor_properties_report.json"

DEFAULT_TREE_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Trees/"
    "M_PineLeaves_01.M_PineLeaves_01"
)
DEFAULT_TREE_MATERIAL_SLOT1 = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Trees/"
    "M_PineBark_01.M_PineBark_01"
)
DEFAULT_GRASS_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Grass/"
    "MI_GrassMedium.MI_GrassMedium"
)
DEFAULT_ROCK_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Stones/"
    "MI_Rock_01.MI_Rock_01"
)

TEST_GRASS_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Plants/"
    "MI_Fern.MI_Fern"
)
VALIDATION_GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)

DYNAMIC_MESH_ATTR = "DynamicMeshPath"
DYNAMIC_MATERIAL_SLOT0_ATTR = "DynamicMaterialSlot0"
OVERRIDE_TRUE_ATTR = "MaterialOverrideTrue"


def _load_asset(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError("Missing asset: {}".format(path))
    return asset


def _actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def _get_all_level_actors():
    actor_subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if actor_subsystem_cls:
        actor_subsystem = unreal.get_editor_subsystem(actor_subsystem_cls)
        if actor_subsystem:
            return actor_subsystem.get_all_level_actors()
    return unreal.EditorLevelLibrary.get_all_level_actors()


def _blueprint_variable_exists(blueprint_object_path, variable_name):
    try:
        cls = unreal.EditorAssetLibrary.load_blueprint_class(blueprint_object_path)
        if cls:
            unreal.get_default_object(cls).get_editor_property(variable_name)
            return True
    except Exception:
        pass
    return False


def _set_blueprint_variable_editable(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(
            blueprint,
            variable_name,
            value,
        )
    except Exception:
        try:
            blueprint.set_blueprint_variable_instance_editable(variable_name, value)
        except Exception:
            pass


def _set_blueprint_variable_expose_on_spawn(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_expose_on_spawn(
            blueprint,
            variable_name,
            value,
        )
    except Exception:
        try:
            blueprint.set_blueprint_variable_expose_on_spawn(variable_name, value)
        except Exception:
            pass


def _ensure_blueprint_material_override_variables():
    blueprint = _load_asset(RUNTIME_BLUEPRINT_OBJECT)
    bool_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    material_type = unreal.BlueprintEditorLibrary.get_object_reference_type(
        unreal.MaterialInterface.static_class()
    )
    variable_specs = [
        ("UseTreeMaterialOverride", bool_type, False),
        ("TreeMaterialOverride", material_type, DEFAULT_TREE_MATERIAL),
        ("TreeMaterialOverrideSlot1", material_type, DEFAULT_TREE_MATERIAL_SLOT1),
        ("UseGrassMaterialOverride", bool_type, False),
        ("GrassMaterialOverride", material_type, DEFAULT_GRASS_MATERIAL),
        ("UseRockMaterialOverride", bool_type, False),
        ("RockMaterialOverride", material_type, DEFAULT_ROCK_MATERIAL),
    ]

    added = []
    for variable_name, pin_type, _default_value in variable_specs:
        if _blueprint_variable_exists(RUNTIME_BLUEPRINT_OBJECT, variable_name):
            continue
        if not unreal.BlueprintEditorLibrary.add_member_variable(blueprint, variable_name, pin_type):
            raise RuntimeError("Failed to add Blueprint variable: {}".format(variable_name))
        added.append(variable_name)

    for variable_name, _pin_type, _default_value in variable_specs:
        _set_blueprint_variable_editable(blueprint, variable_name, True)
        _set_blueprint_variable_expose_on_spawn(blueprint, variable_name, True)

    blueprint.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    runtime_class = unreal.EditorAssetLibrary.load_blueprint_class(RUNTIME_BLUEPRINT_OBJECT)
    if not runtime_class:
        raise RuntimeError("Failed to load runtime Blueprint class: {}".format(RUNTIME_BLUEPRINT_CLASS))
    cdo = unreal.get_default_object(runtime_class)
    cdo.modify()
    for variable_name, _pin_type, default_value in variable_specs:
        if isinstance(default_value, bool):
            cdo.set_editor_property(variable_name, default_value)
        else:
            cdo.set_editor_property(variable_name, _load_asset(default_value))

    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False))
    return {
        "blueprint": RUNTIME_BLUEPRINT_OBJECT,
        "variables": [item[0] for item in variable_specs],
        "added": added,
        "saved": saved,
    }


def _add_node(graph, settings_cls, title, x, y):
    created = graph.add_node_of_type(settings_cls.static_class())
    node = created[0] if isinstance(created, tuple) else created
    node.set_editor_property("node_title", title)
    try:
        node.set_node_position(unreal.Vector2D(float(x), float(y)))
    except Exception:
        pass
    return node


def _selector_import(settings, prop, text):
    selector = settings.get_editor_property(prop)
    selector.import_text("PCGBegin({})PCGEnd".format(text))
    settings.set_editor_property(prop, selector)


def _set_const_value_struct(value_struct, value_type, value):
    value_struct.set_editor_property("type", value_type)
    if value_type == unreal.PCGMetadataTypes.BOOLEAN:
        value_struct.set_editor_property("bool_value", bool(value))
    elif value_type == unreal.PCGMetadataTypes.SOFT_OBJECT_PATH:
        value_struct.set_editor_property("soft_object_path_value", unreal.SoftObjectPath(str(value)))
    elif value_type == unreal.PCGMetadataTypes.INTEGER32:
        value_struct.set_editor_property("int32_value", int(value))
        value_struct.set_editor_property("int_value", int(value))
    else:
        value_struct.set_editor_property("double_value", float(value))
        value_struct.set_editor_property("float_value", float(value))
    return value_struct


def _configure_add(node, output_attr, input_attr="@Last", value_type=None, value=None):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    _selector_import(settings, "input_source", input_attr)
    _selector_import(settings, "output_target", output_attr)
    if value_type is not None:
        value_struct = settings.get_editor_property("attribute_types")
        _set_const_value_struct(value_struct, value_type, value)
        settings.set_editor_property("attribute_types", value_struct)


def _configure_points(node):
    settings = node.get_settings()
    points = settings.get_editor_property("points_to_create")
    points.clear()
    for index, coord in enumerate([(-220.0, 0.0, 0.0), (220.0, 0.0, 0.0)]):
        point = unreal.PCGPoint()
        transform = point.get_editor_property("transform")
        transform.set_editor_property("translation", unreal.Vector(*coord))
        point.set_editor_property("transform", transform)
        point.set_editor_property("bounds_min", unreal.Vector(-80.0, -80.0, 0.0))
        point.set_editor_property("bounds_max", unreal.Vector(80.0, 80.0, 80.0))
        point.set_editor_property("density", 1.0)
        point.set_editor_property("steepness", 1.0)
        point.set_editor_property("seed", 611200 + index)
        points.append(point)
    settings.set_editor_property("points_to_create", points)
    settings.set_editor_property("cull_points_outside_volume", False)


def _configure_get_actor_property(node, property_name, output_attr):
    settings = node.get_settings()
    settings.set_editor_property("property_name", property_name)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("sanitize_output_attribute_name", True)
    _selector_import(settings, "output_attribute_name", output_attr)


def _configure_actor_bool_filter(node, use_property_name):
    settings = node.get_settings()
    settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.EQUAL)
    settings.set_editor_property("use_constant_threshold", False)
    settings.set_editor_property("use_spatial_query", False)
    _selector_import(settings, "target_attribute", OVERRIDE_TRUE_ATTR)
    _selector_import(settings, "threshold_attribute", use_property_name)
    settings.set_editor_property("warn_on_data_missing_attribute", False)
    settings.set_editor_property("generate_output_data_even_if_empty", True)


def _configure_copy_attr(node, source_attr, target_attr):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    _selector_import(settings, "input_source", source_attr)
    _selector_import(settings, "output_target", target_attr)


def _configure_by_attribute_spawner(node, material_override=False):
    settings = node.get_settings()
    settings.set_editor_property("allow_descriptor_changes", True)
    settings.set_mesh_selector_type(unreal.PCGMeshSelectorByAttribute.static_class())
    params = settings.get_editor_property("mesh_selector_parameters")
    params.set_editor_property("attribute_name", DYNAMIC_MESH_ATTR)
    params.set_editor_property("use_attribute_material_overrides", bool(material_override))
    params.set_editor_property(
        "material_override_attributes",
        [DYNAMIC_MATERIAL_SLOT0_ATTR] if material_override else [],
    )
    try:
        settings.set_editor_property("synchronous_load", True)
        settings.set_editor_property("apply_mesh_bounds_to_points", True)
    except Exception:
        pass


def _ensure_validation_graph():
    unreal.EditorAssetLibrary.make_directory(VALIDATION_GRAPH_PACKAGE)
    graph = None
    if unreal.EditorAssetLibrary.does_asset_exist(VALIDATION_GRAPH_OBJECT):
        graph = unreal.EditorAssetLibrary.load_asset(VALIDATION_GRAPH_OBJECT)
    if not graph:
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            VALIDATION_GRAPH_ASSET,
            VALIDATION_GRAPH_PACKAGE,
            unreal.PCGGraph.static_class(),
            unreal.PCGGraphFactory(),
        )
    if not graph:
        raise RuntimeError("Failed to create validation graph: {}".format(VALIDATION_GRAPH_OBJECT))

    for node in list(graph.get_editor_property("nodes")):
        graph.remove_node(node)

    source = _add_node(graph, unreal.PCGCreatePointsSettings, "Validation Grass Points", -1300, 0)
    _configure_points(source)

    mesh_attr = _add_node(graph, unreal.PCGAddAttributeSettings, "Set DynamicMeshPath Grass", -980, 0)
    _configure_add(
        mesh_attr,
        DYNAMIC_MESH_ATTR,
        "@Last",
        unreal.PCGMetadataTypes.SOFT_OBJECT_PATH,
        VALIDATION_GRASS_MESH,
    )

    flag = _add_node(graph, unreal.PCGAddAttributeSettings, "Material Override Flag True", -660, 0)
    _configure_add(flag, OVERRIDE_TRUE_ATTR, "@Last", unreal.PCGMetadataTypes.BOOLEAN, True)

    get_use = _add_node(
        graph,
        unreal.PCGGetActorPropertySettings,
        "Get Actor UseGrassMaterialOverride",
        -660,
        -260,
    )
    _configure_get_actor_property(get_use, "UseGrassMaterialOverride", "UseGrassMaterialOverride")

    split = _add_node(graph, unreal.PCGAttributeFilteringSettings, "Split Grass Material Override", -320, 0)
    _configure_actor_bool_filter(split, "UseGrassMaterialOverride")

    default_spawn = _add_node(graph, unreal.PCGStaticMeshSpawnerSettings, "Spawn Grass Default Material", 40, 160)
    _configure_by_attribute_spawner(default_spawn, material_override=False)

    get_material = _add_node(
        graph,
        unreal.PCGGetActorPropertySettings,
        "Get Actor GrassMaterialOverride",
        40,
        -260,
    )
    _configure_get_actor_property(get_material, "GrassMaterialOverride", "GrassMaterialOverride")

    copy_material = _add_node(
        graph,
        unreal.PCGCopyAttributesSettings,
        "Copy GrassMaterialOverride To DynamicMaterialSlot0",
        380,
        -60,
    )
    _configure_copy_attr(copy_material, "GrassMaterialOverride", DYNAMIC_MATERIAL_SLOT0_ATTR)

    override_spawn = _add_node(
        graph,
        unreal.PCGStaticMeshSpawnerSettings,
        "Spawn Grass Actor Material Override",
        740,
        -60,
    )
    _configure_by_attribute_spawner(override_spawn, material_override=True)

    merge = _add_node(graph, unreal.PCGMergeSettings, "Merge Material Override Result", 1100, 40)

    graph.add_edge(source, "Out", mesh_attr, "In")
    graph.add_edge(mesh_attr, "Out", flag, "In")
    graph.add_edge(flag, "Out", split, "In")
    graph.add_edge(get_use, "Out", split, "Filter")
    graph.add_edge(split, "OutsideFilter", default_spawn, "In")
    graph.add_edge(split, "InsideFilter", copy_material, "Target")
    graph.add_edge(get_material, "Out", copy_material, "Source")
    graph.add_edge(copy_material, "Out", override_spawn, "In")
    graph.add_edge(default_spawn, "Out", merge, "In")
    graph.add_edge(override_spawn, "Out", merge, "In")
    graph.add_edge(merge, "Out", graph.get_output_node(), "Out")

    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(graph, False))
    return {"graph": graph.get_path_name(), "saved": saved}


def _destroy_existing_validation_actor():
    destroyed = []
    for actor in list(_get_all_level_actors()):
        if _actor_label(actor) != VALIDATION_ACTOR_LABEL:
            continue
        for component in actor.get_components_by_class(unreal.PCGComponent):
            try:
                component.cleanup(True)
            except Exception:
                pass
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            destroyed.append(VALIDATION_ACTOR_LABEL)
        except Exception:
            pass
    return destroyed


def _spawn_validation_actor():
    runtime_class = unreal.EditorAssetLibrary.load_blueprint_class(RUNTIME_BLUEPRINT_OBJECT)
    if not runtime_class:
        raise RuntimeError("Missing runtime Blueprint class: {}".format(RUNTIME_BLUEPRINT_CLASS))
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        runtime_class,
        unreal.Vector(0.0, -12000.0, 600.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(VALIDATION_ACTOR_LABEL)
    actor.set_editor_property("UseGrassMaterialOverride", True)
    actor.set_editor_property("GrassMaterialOverride", _load_asset(TEST_GRASS_MATERIAL))
    return actor


def _configure_validation_component(actor):
    graph = _load_asset(VALIDATION_GRAPH_OBJECT)
    rows = []
    components = list(actor.get_components_by_class(unreal.PCGComponent))
    enabled_name = "PCG_Style" if any(c.get_name() == "PCG_Style" for c in components) else None
    if not enabled_name and components:
        enabled_name = components[0].get_name()
    if not enabled_name:
        raise RuntimeError("Validation actor has no PCGComponent: {}".format(_actor_label(actor)))

    for component in components:
        row = {"component": component.get_name(), "enabled": component.get_name() == enabled_name}
        try:
            component.cleanup(True)
        except Exception as exc:
            row["cleanup_error"] = str(exc)
        if row["enabled"]:
            component.activate(True)
            component.set_graph(graph)
            try:
                component.set_editor_property("seed", 6112031)
            except Exception:
                pass
        else:
            component.deactivate()
        rows.append(row)
    return rows


def _generate_validation_actor(actor):
    validation_graph = _load_asset(VALIDATION_GRAPH_OBJECT)
    rows = []
    for component in actor.get_components_by_class(unreal.PCGComponent):
        graph = None
        try:
            graph_instance = component.get_editor_property("graph_instance")
            graph = graph_instance.get_editor_property("graph") if graph_instance else None
        except Exception:
            pass
        if not graph:
            try:
                graph = component.get_editor_property("graph")
            except Exception:
                graph = None
        should_generate = graph == validation_graph
        row = {
            "component": component.get_name(),
            "active": bool(component.is_active()),
            "graph": _object_path(graph),
            "should_generate": should_generate,
        }
        if not should_generate:
            rows.append(row)
            continue
        try:
            component.activate(True)
            component.cleanup(True)
            component.generate(True)
            try:
                component.generate_local(True)
            except Exception as exc:
                row["generate_local_error"] = str(exc)
            row["generated"] = True
        except Exception as exc:
            row["generated"] = False
            row["error"] = str(exc)
        rows.append(row)
    return rows


def _object_path(value):
    if not value:
        return None
    try:
        return value.get_path_name()
    except Exception:
        return str(value)


def _collect_ism_rows(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        mesh = None
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            pass
        try:
            material0 = component.get_material(0)
        except Exception:
            material0 = None
        try:
            count = int(component.get_instance_count())
        except Exception:
            count = -1
        rows.append(
            {
                "component": component.get_name(),
                "mesh": _object_path(mesh),
                "material0": _object_path(material0),
                "count": count,
            }
        )
    rows.sort(key=lambda item: (str(item["mesh"]), str(item["material0"]), item["component"]))
    return rows


def _write_report(report):
    path = pathlib.Path(unreal.Paths.project_dir()) / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _refresh_validation_checks(result, actor):
    result["ism_rows"] = _collect_ism_rows(actor)
    expected_material = TEST_GRASS_MATERIAL
    positive_rows = [row for row in result["ism_rows"] if int(row["count"]) > 0]
    result["checks"] = {
        "blueprint_variables_present": all(
            _blueprint_variable_exists(RUNTIME_BLUEPRINT_OBJECT, name)
            for name in result["blueprint"]["variables"]
        ),
        "validation_graph_saved": bool(result["graph"]["saved"]),
        "generated_instances": sum(max(0, int(row["count"])) for row in positive_rows),
        "expected_material": expected_material,
        "material_override_applied": any(
            row["material0"] == expected_material and int(row["count"]) > 0
            for row in positive_rows
        ),
    }
    result["validation_pass"] = (
        result["checks"]["blueprint_variables_present"]
        and result["checks"]["validation_graph_saved"]
        and result["checks"]["generated_instances"] > 0
        and result["checks"]["material_override_applied"]
    )
    result["report_path"] = _write_report(result)
    return result


def _schedule_deferred_validation_report(result, actor, min_ticks=6, max_ticks=60):
    if not hasattr(unreal, "register_slate_post_tick_callback"):
        result["deferred_validation_scheduled"] = False
        result["deferred_validation_reason"] = "register_slate_post_tick_callback unavailable"
        return False

    state = {
        "ticks": 0,
        "handle": None,
    }

    def _on_tick(_delta_seconds):
        state["ticks"] += 1
        if state["ticks"] < min_ticks:
            return
        deferred = dict(result)
        deferred["deferred_validation"] = True
        deferred["deferred_ticks"] = state["ticks"]
        _refresh_validation_checks(deferred, actor)
        if deferred.get("validation_pass") or state["ticks"] >= max_ticks:
            try:
                unreal.unregister_slate_post_tick_callback(state["handle"])
            except Exception:
                pass
            unreal.log(
                "MCP material override actor-property deferred validation: {}".format(
                    json.dumps(deferred, ensure_ascii=False)
                )
            )

    state["handle"] = unreal.register_slate_post_tick_callback(_on_tick)
    return True


def main():
    result = {
        "validation_level": _object_path(unreal.EditorLevelLibrary.get_editor_world()),
        "blueprint": _ensure_blueprint_material_override_variables(),
        "graph": _ensure_validation_graph(),
        "destroyed_validation_actors": _destroy_existing_validation_actor(),
    }
    actor = _spawn_validation_actor()
    result["actor"] = {
        "label": _actor_label(actor),
        "class": actor.get_class().get_path_name(),
        "UseGrassMaterialOverride": bool(actor.get_editor_property("UseGrassMaterialOverride")),
        "GrassMaterialOverride": _object_path(actor.get_editor_property("GrassMaterialOverride")),
    }
    result["component_config"] = _configure_validation_component(actor)
    result["generation"] = _generate_validation_actor(actor)
    _refresh_validation_checks(result, actor)
    if not result["validation_pass"]:
        result["deferred_validation_scheduled"] = _schedule_deferred_validation_report(result, actor)
        result["report_path"] = _write_report(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
