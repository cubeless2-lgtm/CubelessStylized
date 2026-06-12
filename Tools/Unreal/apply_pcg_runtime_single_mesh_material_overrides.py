import json
import pathlib

import unreal


REPORT_PATH = "Saved/MCP_PCG/pcg_runtime_weighted_material_overrides_report.json"

DYNAMIC_MESH_ATTR = "DynamicMeshPath"
DYNAMIC_MATERIAL_SLOT0_ATTR = "DynamicMaterialSlot0"
DYNAMIC_MATERIAL_SLOT1_ATTR = "DynamicMaterialSlot1"
MESH_OVERRIDE_TRUE_ATTR = "MeshOverrideTrue"
MATERIAL_OVERRIDE_TRUE_ATTR = "MaterialOverrideTrue"

RUNTIME_BLUEPRINT_OBJECT = (
    "/Game/Cubeless/PCG/Runtime/Blueprints/"
    "BP_Cubeless_PCG_EcosystemRuntime.BP_Cubeless_PCG_EcosystemRuntime"
)
VALIDATION_ACTOR_PREFIX = "MCP_Cubeless_PCG_SingleMeshMaterialOverride"

TEST_GRASS_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Plants/"
    "MI_Fern.MI_Fern"
)
TEST_TREE_SLOT0_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Plants/"
    "MI_Fern.MI_Fern"
)
TEST_TREE_SLOT1_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Stones/"
    "MI_Rock_01.MI_Rock_01"
)
VALIDATION_GRASS_GRAPH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos/"
    "PCG_Cubeless_ED_StyleProfileMatrix_ClassicGrass_GroundOnly_GroundDense."
    "PCG_Cubeless_ED_StyleProfileMatrix_ClassicGrass_GroundOnly_GroundDense"
)
VALIDATION_TREE_GRAPH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/TreeProfilePresets/"
    "PCG_Cubeless_ED_TreeProfile_CompactConifer_Solo."
    "PCG_Cubeless_ED_TreeProfile_CompactConifer_Solo"
)
VALIDATION_MIXED_GRASS_GRAPH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos/"
    "PCG_Cubeless_ED_StyleProfileMatrix_MixedGrass_Both_GroundDense_DitchDense."
    "PCG_Cubeless_ED_StyleProfileMatrix_MixedGrass_Both_GroundDense_DitchDense"
)
VALIDATION_SMALL_ROCK_GRAPH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos/"
    "PCG_Cubeless_ED_StyleProfileMatrix_SmallRocks_Both_GroundNormal_DitchSparse."
    "PCG_Cubeless_ED_StyleProfileMatrix_SmallRocks_Both_GroundNormal_DitchSparse"
)
VALIDATION_MIXED_TREE_GRAPH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/TreeProfilePresets/"
    "PCG_Cubeless_ED_TreeProfile_MixedConifer_LightGrove."
    "PCG_Cubeless_ED_TreeProfile_MixedConifer_LightGrove"
)
VALIDATION_TREE_OVERRIDE_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_05.SM_Conifer_05"
)


def _analysis_dir():
    return pathlib.Path(unreal.Paths.project_dir()).resolve().parent / "unreal-mcp-cubeless" / "Docs" / "Analysis" / "ElectricDreams"


def _load_config(script_name, namespace_name):
    script = _analysis_dir() / script_name
    if not script.exists():
        script = pathlib.Path(unreal.Paths.project_dir()).resolve() / "Tools" / "Unreal" / script_name
    namespace = {"__name__": namespace_name, "__file__": str(script)}
    with open(script, "r", encoding="utf-8") as handle:
        exec(compile(handle.read(), str(script), "exec"), namespace)
    return namespace


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


def _configure_get_actor_property(node, property_name, output_attr):
    settings = node.get_settings()
    settings.set_editor_property("property_name", property_name)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("sanitize_output_attribute_name", True)
    _selector_import(settings, "output_attribute_name", output_attr)


def _configure_bool_filter(node, target_attr, threshold_attr):
    settings = node.get_settings()
    settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.EQUAL)
    settings.set_editor_property("use_constant_threshold", False)
    settings.set_editor_property("use_spatial_query", False)
    _selector_import(settings, "target_attribute", target_attr)
    _selector_import(settings, "threshold_attribute", threshold_attr)
    settings.set_editor_property("warn_on_data_missing_attribute", False)
    settings.set_editor_property("generate_output_data_even_if_empty", True)


def _configure_copy(node, source_attr, target_attr):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    _selector_import(settings, "input_source", source_attr)
    _selector_import(settings, "output_target", target_attr)


def _configure_by_attribute_spawner(node, material_slots=None):
    settings = node.get_settings()
    settings.set_editor_property("allow_descriptor_changes", True)
    settings.set_mesh_selector_type(unreal.PCGMeshSelectorByAttribute.static_class())
    params = settings.get_editor_property("mesh_selector_parameters")
    params.set_editor_property("attribute_name", DYNAMIC_MESH_ATTR)
    params.set_editor_property("use_attribute_material_overrides", bool(material_slots))
    params.set_editor_property("material_override_attributes", list(material_slots or []))
    try:
        settings.set_editor_property("synchronous_load", True)
        settings.set_editor_property("apply_mesh_bounds_to_points", True)
    except Exception:
        pass


def _domain_material_config(domain_name):
    if domain_name == "Tree":
        return {
            "use_property": "UseTreeMaterialOverride",
            "slots": [
                ("TreeMaterialOverride", DYNAMIC_MATERIAL_SLOT0_ATTR),
                ("TreeMaterialOverrideSlot1", DYNAMIC_MATERIAL_SLOT1_ATTR),
            ],
        }
    if domain_name == "Rock":
        return {
            "use_property": "UseRockMaterialOverride",
            "slots": [("RockMaterialOverride", DYNAMIC_MATERIAL_SLOT0_ATTR)],
        }
    return {
        "use_property": "UseGrassMaterialOverride",
        "slots": [("GrassMaterialOverride", DYNAMIC_MATERIAL_SLOT0_ATTR)],
    }


def _add_node(add_node_fn, graph, settings_cls, title, x, y):
    return add_node_fn(graph, settings_cls, title, x, y)


def _add_default_mesh_attr(add_node_fn, graph, upstream, source_pin, default_mesh_path, x, y):
    node = _add_node(add_node_fn, graph, unreal.PCGAddAttributeSettings, "Set Default DynamicMeshPath", x, y)
    _configure_add(node, DYNAMIC_MESH_ATTR, "@Last", unreal.PCGMetadataTypes.SOFT_OBJECT_PATH, default_mesh_path)
    graph.add_edge(upstream, source_pin, node, "In")
    return node


def _add_mesh_property_attr(add_node_fn, graph, upstream, source_pin, use_mesh_property, mesh_property, x, y):
    flag = _add_node(add_node_fn, graph, unreal.PCGAddAttributeSettings, "Mesh Override Flag True", x, y)
    _configure_add(flag, MESH_OVERRIDE_TRUE_ATTR, "@Last", unreal.PCGMetadataTypes.BOOLEAN, True)
    get_use = _add_node(add_node_fn, graph, unreal.PCGGetActorPropertySettings, "Get Actor {}".format(use_mesh_property), x, y - 280)
    _configure_get_actor_property(get_use, use_mesh_property, use_mesh_property)
    split = _add_node(add_node_fn, graph, unreal.PCGAttributeFilteringSettings, "Split Mesh Override", x + 340, y)
    _configure_bool_filter(split, MESH_OVERRIDE_TRUE_ATTR, use_mesh_property)
    graph.add_edge(upstream, source_pin, flag, "In")
    graph.add_edge(flag, "Out", split, "In")
    graph.add_edge(get_use, "Out", split, "Filter")

    get_mesh = _add_node(add_node_fn, graph, unreal.PCGGetActorPropertySettings, "Get Actor {}".format(mesh_property), x + 700, y - 280)
    _configure_get_actor_property(get_mesh, mesh_property, mesh_property)
    copy_mesh = _add_node(add_node_fn, graph, unreal.PCGCopyAttributesSettings, "Copy {} To {}".format(mesh_property, DYNAMIC_MESH_ATTR), x + 1040, y - 120)
    _configure_copy(copy_mesh, mesh_property, DYNAMIC_MESH_ATTR)
    graph.add_edge(split, "InsideFilter", copy_mesh, "Target")
    graph.add_edge(get_mesh, "Out", copy_mesh, "Source")
    return split, copy_mesh


def _add_material_attr_chain(add_node_fn, graph, upstream, x, y, material_slots, source_pin="Out"):
    current = upstream
    current_pin = source_pin
    for index, (property_name, slot_attr) in enumerate(material_slots):
        get_material = _add_node(
            add_node_fn,
            graph,
            unreal.PCGGetActorPropertySettings,
            "Get Actor {}".format(property_name),
            x,
            y - 280 - index * 160,
        )
        _configure_get_actor_property(get_material, property_name, property_name)
        copy_material = _add_node(
            add_node_fn,
            graph,
            unreal.PCGCopyAttributesSettings,
            "Copy {} To {}".format(property_name, slot_attr),
            x + 340 + index * 320,
            y,
        )
        _configure_copy(copy_material, property_name, slot_attr)
        graph.add_edge(current, current_pin, copy_material, "Target")
        graph.add_edge(get_material, "Out", copy_material, "Source")
        current = copy_material
        current_pin = "Out"
    return current


def _add_mesh_switch_from_pin(
    add_node_fn,
    graph,
    upstream,
    source_pin,
    domain_name,
    use_mesh_property,
    mesh_property,
    mesh_paths,
    x,
    y,
    configure_default_spawner,
    default_title,
):
    flag = _add_node(add_node_fn, graph, unreal.PCGAddAttributeSettings, "{} Mesh Override Flag True".format(domain_name), x, y)
    _configure_add(flag, MESH_OVERRIDE_TRUE_ATTR, "@Last", unreal.PCGMetadataTypes.BOOLEAN, True)
    get_use = _add_node(add_node_fn, graph, unreal.PCGGetActorPropertySettings, "Get Actor {}".format(use_mesh_property), x, y - 280)
    _configure_get_actor_property(get_use, use_mesh_property, use_mesh_property)
    split = _add_node(add_node_fn, graph, unreal.PCGAttributeFilteringSettings, "Split {} Mesh Override".format(domain_name), x + 340, y)
    _configure_bool_filter(split, MESH_OVERRIDE_TRUE_ATTR, use_mesh_property)

    default_spawner = _add_node(add_node_fn, graph, unreal.PCGStaticMeshSpawnerSettings, default_title, x + 700, y + 120)
    configure_default_spawner(default_spawner, mesh_paths)

    get_mesh = _add_node(add_node_fn, graph, unreal.PCGGetActorPropertySettings, "Get Actor {}".format(mesh_property), x + 700, y - 280)
    _configure_get_actor_property(get_mesh, mesh_property, mesh_property)
    copy_mesh = _add_node(add_node_fn, graph, unreal.PCGCopyAttributesSettings, "Copy {} To {}".format(mesh_property, DYNAMIC_MESH_ATTR), x + 1040, y - 120)
    _configure_copy(copy_mesh, mesh_property, DYNAMIC_MESH_ATTR)
    override_spawner = _add_node(add_node_fn, graph, unreal.PCGStaticMeshSpawnerSettings, "Spawn {} ByActorMeshOverride".format(domain_name), x + 1380, y - 120)
    _configure_by_attribute_spawner(override_spawner)
    merge = _add_node(add_node_fn, graph, unreal.PCGMergeSettings, "Merge {} Mesh Override Result".format(domain_name), x + 1760, y)

    graph.add_edge(upstream, source_pin, flag, "In")
    graph.add_edge(flag, "Out", split, "In")
    graph.add_edge(get_use, "Out", split, "Filter")
    graph.add_edge(split, "OutsideFilter", default_spawner, "In")
    graph.add_edge(split, "InsideFilter", copy_mesh, "Target")
    graph.add_edge(get_mesh, "Out", copy_mesh, "Source")
    graph.add_edge(copy_mesh, "Out", override_spawner, "In")
    graph.add_edge(default_spawner, "Out", merge, "In")
    graph.add_edge(override_spawner, "Out", merge, "In")
    return merge


def _configure_weighted_material_spawner(node, mesh_paths, configure_default_spawner, material_slots):
    configure_default_spawner(node, mesh_paths)
    settings = node.get_settings()
    try:
        settings.set_editor_property("allow_descriptor_changes", True)
    except Exception:
        pass
    params = settings.get_editor_property("mesh_selector_parameters")
    params.set_editor_property("use_attribute_material_overrides", bool(material_slots))
    params.set_editor_property("material_override_attributes", list(material_slots or []))


def _add_material_override_switch(
    add_node_fn,
    graph,
    upstream,
    domain_name,
    use_mesh_property,
    mesh_property,
    mesh_paths,
    x,
    y,
    configure_default_spawner,
    original_mesh_switch,
    default_title,
):
    material_config = _domain_material_config(domain_name)
    use_material_property = material_config["use_property"]
    material_slots = material_config["slots"]
    material_slot_attrs = [slot_attr for _property_name, slot_attr in material_slots]

    flag = _add_node(add_node_fn, graph, unreal.PCGAddAttributeSettings, "{} Material Override Flag True".format(domain_name), x, y)
    _configure_add(flag, MATERIAL_OVERRIDE_TRUE_ATTR, "@Last", unreal.PCGMetadataTypes.BOOLEAN, True)
    get_use_material = _add_node(add_node_fn, graph, unreal.PCGGetActorPropertySettings, "Get Actor {}".format(use_material_property), x, y - 320)
    _configure_get_actor_property(get_use_material, use_material_property, use_material_property)
    split_material = _add_node(add_node_fn, graph, unreal.PCGAttributeFilteringSettings, "Split {} Material Override".format(domain_name), x + 340, y)
    _configure_bool_filter(split_material, MATERIAL_OVERRIDE_TRUE_ATTR, use_material_property)

    graph.add_edge(upstream, "Out", flag, "In")
    graph.add_edge(flag, "Out", split_material, "In")
    graph.add_edge(get_use_material, "Out", split_material, "Filter")

    no_material_merge = _add_mesh_switch_from_pin(
        add_node_fn,
        graph,
        split_material,
        "OutsideFilter",
        domain_name,
        use_mesh_property,
        mesh_property,
        mesh_paths,
        x + 720,
        y + 260,
        configure_default_spawner,
        default_title,
    )

    mesh_split, copy_actor_mesh = _add_mesh_property_attr(
        add_node_fn,
        graph,
        split_material,
        "InsideFilter",
        use_mesh_property,
        mesh_property,
        x + 720,
        y - 360,
    )

    default_material_chain = _add_material_attr_chain(
        add_node_fn,
        graph,
        mesh_split,
        x + 1420,
        y - 520,
        material_slots,
        "OutsideFilter",
    )
    default_material_spawner = _add_node(
        add_node_fn,
        graph,
        unreal.PCGStaticMeshSpawnerSettings,
        "Spawn {} WeightedMaterialOverride".format(domain_name),
        x + 2460,
        y - 520,
    )
    _configure_weighted_material_spawner(
        default_material_spawner,
        mesh_paths,
        configure_default_spawner,
        material_slot_attrs,
    )
    graph.add_edge(default_material_chain, "Out", default_material_spawner, "In")

    actor_material_chain = _add_material_attr_chain(
        add_node_fn,
        graph,
        copy_actor_mesh,
        x + 1420,
        y - 180,
        material_slots,
    )
    material_spawner = _add_node(
        add_node_fn,
        graph,
        unreal.PCGStaticMeshSpawnerSettings,
        "Spawn {} ByActorMeshMaterialOverride".format(domain_name),
        x + 2460,
        y - 180,
    )
    _configure_by_attribute_spawner(material_spawner, material_slot_attrs)
    graph.add_edge(actor_material_chain, "Out", material_spawner, "In")

    merge = _add_node(add_node_fn, graph, unreal.PCGMergeSettings, "Merge {} Material Override Result".format(domain_name), x + 3400, y)
    graph.add_edge(no_material_merge, "Out", merge, "In")
    graph.add_edge(default_material_spawner, "Out", merge, "In")
    graph.add_edge(material_spawner, "Out", merge, "In")
    return merge


def _install_base_patch(base_ns):
    original = base_ns["add_mesh_override_switch"]
    add_node_fn = base_ns["add_node"]

    def patched(graph, upstream, domain_name, use_property, mesh_property, mesh_paths, x, y):
        return _add_material_override_switch(
            add_node_fn,
            graph,
            upstream,
            domain_name,
            use_property,
            mesh_property,
            mesh_paths,
            x,
            y,
            lambda node, paths: base_ns["configure_weighted_spawner"](node, paths),
            lambda: original(graph, upstream, domain_name, use_property, mesh_property, mesh_paths, x, y),
            "Spawn {} Weighted Default".format(domain_name),
        )

    base_ns["add_mesh_override_switch"] = patched


def _install_true_patch(true_ns):
    original = true_ns["add_true_material_mesh_override_switch"]
    add_node_fn = true_ns["add_node"]

    def patched(graph, upstream, domain_name, use_property, mesh_property, mesh_paths, override_map, x, y):
        return _add_material_override_switch(
            add_node_fn,
            graph,
            upstream,
            domain_name,
            use_property,
            mesh_property,
            mesh_paths,
            x,
            y,
            lambda node, paths: true_ns["configure_spawner_with_overrides"](node, paths, override_map),
            lambda: original(graph, upstream, domain_name, use_property, mesh_property, mesh_paths, override_map, x, y),
            "Spawn {} TrueMaterial Default".format(domain_name),
        )

    true_ns["add_true_material_mesh_override_switch"] = patched


def _build_graphs():
    base_ns = _load_config("apply_pcg_mesh_override_actor_properties.py", "_cubeless_base_mesh_override")
    _install_base_patch(base_ns)

    built = {
        "base_tree": [],
        "base_style_amount": [],
        "true_style_amount": [],
        "true_style_matrix": [],
        "true_tree": [],
    }

    for spec in base_ns["TREE_CONFIG"]["TREE_PROFILE_SPECS"]:
        built["base_tree"].append(base_ns["build_tree_profile_graph"](spec).get_path_name())

    for style in base_ns["STYLE_CONFIG"]["STYLE_SPECS"]:
        for amount in base_ns["STYLE_CONFIG"]["GROUND_AMOUNT_SPECS"]:
            built["base_style_amount"].append(
                base_ns["build_style_amount_graph"]("Ground", amount, style).get_path_name()
            )
        for amount in base_ns["STYLE_CONFIG"]["DITCH_AMOUNT_SPECS"]:
            built["base_style_amount"].append(
                base_ns["build_style_amount_graph"]("Ditch", amount, style).get_path_name()
            )

    true_ns = _load_config("build_cubeless_ed_true_material_applied_presets.py", "_cubeless_true_material_override")
    _install_true_patch(true_ns)
    material_config = true_ns["MATERIAL_CONFIG"]
    try:
        material_config["ensure_material_variants"]()
    except Exception as exc:
        built["true_material_variant_warning"] = str(exc)
    for style in true_ns["STYLE_CONFIG"]["STYLE_SPECS"]:
        if style["style_type"] not in true_ns["STYLE_DOMAIN_BY_STYLE_TYPE"]:
            continue
        for variant_type in (2, 3):
            for amount in true_ns["STYLE_CONFIG"]["GROUND_AMOUNT_SPECS"]:
                built["true_style_amount"].append(
                    true_ns["build_true_style_amount_graph"]("Ground", amount, style, variant_type).get_path_name()
                )
            for amount in true_ns["STYLE_CONFIG"]["DITCH_AMOUNT_SPECS"]:
                built["true_style_amount"].append(
                    true_ns["build_true_style_amount_graph"]("Ditch", amount, style, variant_type).get_path_name()
                )
    for spec in true_ns["TRUE_STYLE_MATRIX_SPECS"]:
        built["true_style_matrix"].append(
            true_ns["build_true_style_matrix_graph"](spec["style_matrix_spec"], spec["variant_type"]).get_path_name()
        )
    for spec in true_ns["TREE_CONFIG"]["TREE_PROFILE_SPECS"]:
        for variant_type in (2, 3):
            built["true_tree"].append(true_ns["build_true_tree_graph"](spec, variant_type).get_path_name())

    return built


def _ensure_actor_property_variables():
    base_ns = _load_config("apply_pcg_mesh_override_actor_properties.py", "_cubeless_base_mesh_override_vars")
    material_ns = _load_config("apply_pcg_material_override_actor_properties.py", "_cubeless_material_override_vars")
    return {
        "mesh_override_added": base_ns["ensure_blueprint_mesh_override_variables"](),
        "material_override": material_ns["_ensure_blueprint_material_override_variables"](),
    }


def _destroy_validation_actors():
    destroyed = []
    for actor in list(_get_all_level_actors()):
        label = _actor_label(actor)
        if not label.startswith(VALIDATION_ACTOR_PREFIX):
            continue
        for component in actor.get_components_by_class(unreal.PCGComponent):
            try:
                component.cleanup(True)
            except Exception:
                pass
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            destroyed.append(label)
        except Exception:
            pass
    return destroyed


def _spawn_runtime_actor(label, location):
    actor_class = unreal.EditorAssetLibrary.load_blueprint_class(RUNTIME_BLUEPRINT_OBJECT)
    if not actor_class:
        raise RuntimeError("Missing runtime Blueprint class: {}".format(RUNTIME_BLUEPRINT_OBJECT))
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(label)
    return actor


def _set_material(actor, prop_name, material_path):
    actor.set_editor_property(prop_name, _load_asset(material_path))


def _set_mesh(actor, prop_name, mesh_path):
    actor.set_editor_property(prop_name, _load_asset(mesh_path))


def _validate_components(actor, category):
    rows = []
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        try:
            mesh = component.get_editor_property("static_mesh")
            mesh_path = mesh.get_path_name() if mesh else None
        except Exception:
            mesh_path = None
        materials = []
        for index in range(4):
            try:
                material = component.get_material(index)
                materials.append(material.get_path_name() if material else None)
            except Exception:
                materials.append(None)
        try:
            count = int(component.get_instance_count())
        except Exception:
            count = -1
        text = "{} {}".format(component.get_name(), mesh_path).lower()
        if category == "tree" and not any(token in text for token in ("tree", "conifer", "pine")):
            continue
        if category == "grass" and not any(token in text for token in ("grass", "fern", "leaf", "flower")):
            continue
        if category == "rock" and not any(token in text for token in ("rock", "stone")):
            continue
        rows.append(
            {
                "component": component.get_name(),
                "mesh": mesh_path,
                "materials_0_3": materials,
                "count": count,
            }
        )
    rows.sort(key=lambda row: (row["mesh"] or "", row["component"]))
    return rows


def _configure_runtime_component(actor, enabled_component_name, graph_path):
    graph = _load_asset(graph_path)
    rows = []
    for component in actor.get_components_by_class(unreal.PCGComponent):
        row = {"component": component.get_name(), "enabled": component.get_name() == enabled_component_name}
        try:
            component.cleanup(True)
        except Exception as exc:
            row["cleanup_error"] = str(exc)
        if row["enabled"]:
            component.activate(True)
            component.set_graph(graph)
            try:
                component.generate(True)
                try:
                    component.generate_local(True)
                except Exception as local_exc:
                    row["generate_local_error"] = str(local_exc)
                row["generated"] = True
            except Exception as exc:
                row["generated"] = False
                row["generate_error"] = str(exc)
        else:
            component.deactivate()
        rows.append(row)
    return {"graph": graph_path, "components": rows}


def _run_validation():
    _destroy_validation_actors()

    grass_actor = _spawn_runtime_actor(
        "{}_Grass".format(VALIDATION_ACTOR_PREFIX),
        unreal.Vector(-900.0, -13200.0, 650.0),
    )
    grass_actor.set_editor_property("PresetType", 5)
    grass_actor.set_editor_property("DensityOverride", 0)
    grass_actor.set_editor_property("TreeOverride", 1)
    grass_actor.set_editor_property("MaterialMood", 0)
    grass_actor.set_editor_property("UseGrassMaterialOverride", True)
    _set_material(grass_actor, "GrassMaterialOverride", TEST_GRASS_MATERIAL)

    tree_actor = _spawn_runtime_actor(
        "{}_Tree".format(VALIDATION_ACTOR_PREFIX),
        unreal.Vector(900.0, -13200.0, 650.0),
    )
    tree_actor.set_editor_property("PresetType", 1)
    tree_actor.set_editor_property("DensityOverride", 1)
    tree_actor.set_editor_property("TreeOverride", 2)
    tree_actor.set_editor_property("MaterialMood", 0)
    tree_actor.set_editor_property("UseTreeMaterialOverride", True)
    _set_material(tree_actor, "TreeMaterialOverride", TEST_TREE_SLOT0_MATERIAL)
    _set_material(tree_actor, "TreeMaterialOverrideSlot1", TEST_TREE_SLOT1_MATERIAL)

    mixed_grass_actor = _spawn_runtime_actor(
        "{}_MixedGrass".format(VALIDATION_ACTOR_PREFIX),
        unreal.Vector(-2700.0, -13200.0, 650.0),
    )
    mixed_grass_actor.set_editor_property("PresetType", 5)
    mixed_grass_actor.set_editor_property("DensityOverride", 2)
    mixed_grass_actor.set_editor_property("TreeOverride", 1)
    mixed_grass_actor.set_editor_property("MaterialMood", 0)
    mixed_grass_actor.set_editor_property("UseGrassMeshOverride", False)
    mixed_grass_actor.set_editor_property("UseGrassMaterialOverride", True)
    _set_material(mixed_grass_actor, "GrassMaterialOverride", TEST_GRASS_MATERIAL)

    rock_actor = _spawn_runtime_actor(
        "{}_SmallRocks".format(VALIDATION_ACTOR_PREFIX),
        unreal.Vector(2700.0, -13200.0, 650.0),
    )
    rock_actor.set_editor_property("PresetType", 5)
    rock_actor.set_editor_property("DensityOverride", 1)
    rock_actor.set_editor_property("TreeOverride", 1)
    rock_actor.set_editor_property("MaterialMood", 0)
    rock_actor.set_editor_property("UseRockMeshOverride", False)
    rock_actor.set_editor_property("UseRockMaterialOverride", True)
    _set_material(rock_actor, "RockMaterialOverride", TEST_GRASS_MATERIAL)

    mixed_tree_actor = _spawn_runtime_actor(
        "{}_MixedTree".format(VALIDATION_ACTOR_PREFIX),
        unreal.Vector(4500.0, -13200.0, 650.0),
    )
    mixed_tree_actor.set_editor_property("PresetType", 1)
    mixed_tree_actor.set_editor_property("DensityOverride", 1)
    mixed_tree_actor.set_editor_property("TreeOverride", 3)
    mixed_tree_actor.set_editor_property("MaterialMood", 0)
    mixed_tree_actor.set_editor_property("UseTreeMeshOverride", False)
    mixed_tree_actor.set_editor_property("UseTreeMaterialOverride", True)
    _set_material(mixed_tree_actor, "TreeMaterialOverride", TEST_TREE_SLOT0_MATERIAL)
    _set_material(mixed_tree_actor, "TreeMaterialOverrideSlot1", TEST_TREE_SLOT1_MATERIAL)

    actor_mesh_tree = _spawn_runtime_actor(
        "{}_MixedTreeActorMesh".format(VALIDATION_ACTOR_PREFIX),
        unreal.Vector(6300.0, -13200.0, 650.0),
    )
    actor_mesh_tree.set_editor_property("PresetType", 1)
    actor_mesh_tree.set_editor_property("DensityOverride", 1)
    actor_mesh_tree.set_editor_property("TreeOverride", 3)
    actor_mesh_tree.set_editor_property("MaterialMood", 0)
    actor_mesh_tree.set_editor_property("UseTreeMeshOverride", True)
    actor_mesh_tree.set_editor_property("UseTreeMaterialOverride", True)
    _set_mesh(actor_mesh_tree, "TreeMeshOverride", VALIDATION_TREE_OVERRIDE_MESH)
    _set_material(actor_mesh_tree, "TreeMaterialOverride", TEST_TREE_SLOT0_MATERIAL)
    _set_material(actor_mesh_tree, "TreeMaterialOverrideSlot1", TEST_TREE_SLOT1_MATERIAL)

    return {
        "grass": {
            "actor": _actor_label(grass_actor),
            "apply": _configure_runtime_component(grass_actor, "PCG_Style", VALIDATION_GRASS_GRAPH),
        },
        "tree": {
            "actor": _actor_label(tree_actor),
            "apply": _configure_runtime_component(tree_actor, "PCG_Tree", VALIDATION_TREE_GRAPH),
        },
        "mixed_grass": {
            "actor": _actor_label(mixed_grass_actor),
            "apply": _configure_runtime_component(mixed_grass_actor, "PCG_Style", VALIDATION_MIXED_GRASS_GRAPH),
        },
        "small_rocks": {
            "actor": _actor_label(rock_actor),
            "apply": _configure_runtime_component(rock_actor, "PCG_Style", VALIDATION_SMALL_ROCK_GRAPH),
        },
        "mixed_tree": {
            "actor": _actor_label(mixed_tree_actor),
            "apply": _configure_runtime_component(mixed_tree_actor, "PCG_Tree", VALIDATION_MIXED_TREE_GRAPH),
        },
        "mixed_tree_actor_mesh": {
            "actor": _actor_label(actor_mesh_tree),
            "apply": _configure_runtime_component(actor_mesh_tree, "PCG_Tree", VALIDATION_MIXED_TREE_GRAPH),
        },
    }


def _collect_validation_results():
    results = {}
    expected = {
        "{}_Grass".format(VALIDATION_ACTOR_PREFIX): {
            "category": "grass",
            "slot_expectations": {0: TEST_GRASS_MATERIAL},
        },
        "{}_Tree".format(VALIDATION_ACTOR_PREFIX): {
            "category": "tree",
            "slot_expectations": {0: TEST_TREE_SLOT0_MATERIAL, 1: TEST_TREE_SLOT1_MATERIAL},
        },
        "{}_MixedGrass".format(VALIDATION_ACTOR_PREFIX): {
            "category": "grass",
            "slot_expectations": {0: TEST_GRASS_MATERIAL},
            "min_unique_meshes": 2,
            "require_all_slots": True,
        },
        "{}_SmallRocks".format(VALIDATION_ACTOR_PREFIX): {
            "category": "rock",
            "slot_expectations": {0: TEST_GRASS_MATERIAL},
            "min_unique_meshes": 2,
            "require_all_slots": True,
        },
        "{}_MixedTree".format(VALIDATION_ACTOR_PREFIX): {
            "category": "tree",
            "slot_expectations": {0: TEST_TREE_SLOT0_MATERIAL},
            "require_all_slots": True,
        },
        "{}_MixedTreeActorMesh".format(VALIDATION_ACTOR_PREFIX): {
            "category": "tree",
            "slot_expectations": {0: TEST_TREE_SLOT0_MATERIAL, 1: TEST_TREE_SLOT1_MATERIAL},
            "expected_mesh": VALIDATION_TREE_OVERRIDE_MESH,
            "require_all_slots": True,
        },
    }
    for actor in _get_all_level_actors():
        label = _actor_label(actor)
        if label not in expected:
            continue
        spec = expected[label]
        rows = _validate_components(actor, spec["category"])
        generated = sum(max(0, int(row["count"])) for row in rows)
        active_rows = [row for row in rows if int(row["count"]) > 0]
        unique_meshes = sorted({row["mesh"] for row in active_rows if row["mesh"]})
        slot_checks = {}
        for slot, material_path in spec["slot_expectations"].items():
            slot_checks["slot{}_matches".format(slot)] = any(
                int(row["count"]) > 0 and len(row["materials_0_3"]) > slot and row["materials_0_3"][slot] == material_path
                for row in rows
            )
            if spec.get("require_all_slots"):
                slot_checks["slot{}_all_rows_match".format(slot)] = bool(active_rows) and all(
                    len(row["materials_0_3"]) > slot and row["materials_0_3"][slot] == material_path
                    for row in active_rows
                )
        mesh_checks = {
            "unique_mesh_count": len(unique_meshes),
            "min_unique_meshes": int(spec.get("min_unique_meshes", 1)),
            "unique_mesh_requirement_pass": len(unique_meshes) >= int(spec.get("min_unique_meshes", 1)),
        }
        if spec.get("expected_mesh"):
            mesh_checks["expected_mesh"] = spec["expected_mesh"]
            mesh_checks["expected_mesh_all_rows_match"] = bool(active_rows) and all(
                row["mesh"] == spec["expected_mesh"] for row in active_rows
            )
        results[label] = {
            "category": spec["category"],
            "generated_instances": generated,
            "unique_meshes": unique_meshes,
            "rows": rows,
            "slot_checks": slot_checks,
            "mesh_checks": mesh_checks,
            "pass": generated > 0 and all(slot_checks.values()) and all(
                value for key, value in mesh_checks.items() if key.endswith("_pass") or key.endswith("_match")
            ),
        }
    return results


def _write_report(report):
    path = pathlib.Path(unreal.Paths.project_dir()) / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _schedule_final_report(report, min_ticks=10, max_ticks=90):
    if not hasattr(unreal, "register_slate_post_tick_callback"):
        report["deferred_report_scheduled"] = False
        report["validation_results"] = _collect_validation_results()
        report["validation_pass"] = bool(report["validation_results"]) and all(
            item["pass"] for item in report["validation_results"].values()
        )
        report["report_path"] = _write_report(report)
        return False

    state = {"ticks": 0, "handle": None}

    def _on_tick(_delta_seconds):
        state["ticks"] += 1
        if state["ticks"] < min_ticks:
            return
        deferred = dict(report)
        deferred["deferred_ticks"] = state["ticks"]
        deferred["validation_results"] = _collect_validation_results()
        deferred["validation_pass"] = bool(deferred["validation_results"]) and all(
            item["pass"] for item in deferred["validation_results"].values()
        )
        if deferred["validation_pass"] or state["ticks"] >= max_ticks:
            deferred["destroyed_validation_actors"] = _destroy_validation_actors()
            deferred["report_path"] = _write_report(deferred)
            try:
                unreal.unregister_slate_post_tick_callback(state["handle"])
            except Exception:
                pass
            unreal.log(
                "MCP runtime single-mesh material override validation: {}".format(
                    json.dumps(deferred, ensure_ascii=False)
                )
            )
        else:
            deferred["report_path"] = _write_report(deferred)

    state["handle"] = unreal.register_slate_post_tick_callback(_on_tick)
    report["deferred_report_scheduled"] = True
    report["report_path"] = _write_report(report)
    return True


def main():
    report = {
        "blueprint_actor_properties": _ensure_actor_property_variables(),
        "built_graphs": _build_graphs(),
        "validation_setup": _run_validation(),
    }
    _schedule_final_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main()
