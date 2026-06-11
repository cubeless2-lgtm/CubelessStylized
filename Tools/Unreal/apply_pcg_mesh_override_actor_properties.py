import json
import pathlib

import unreal


BLUEPRINT_PATH = (
    "/Game/Cubeless/PCG/ProductionCandidates/Blueprints/"
    "BP_Cubeless_PCG_EcosystemCandidate.BP_Cubeless_PCG_EcosystemCandidate"
)
VALIDATION_LEVEL = "/Game/_MCP_Temp/PCG/LVL_ElectricDreams_SplineAssembly_MCP"
REPORT_PATH = "Saved/MCP_PCG/pcg_mesh_override_actor_properties_report.json"
VALIDATION_ACTOR_PREFIX = "MCP_Cubeless_PCG_MeshOverrideActorProperty"
DEFERRED_VALIDATION_MIN_TICKS = 3
DEFERRED_VALIDATION_MAX_TICKS = 60

TREE_DEFAULT_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_05.SM_Conifer_05"
)
TREE_OVERRIDE_TEST_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_08.SM_Conifer_08"
)
GRASS_DEFAULT_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)
GRASS_OVERRIDE_TEST_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Plants/"
    "SM_Fern_01.SM_Fern_01"
)
ROCK_DEFAULT_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Stones/Rocks/"
    "SM_SmallRock_01.SM_SmallRock_01"
)
ROCK_OVERRIDE_TEST_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Stones/Rocks/"
    "SM_SmallRock_02.SM_SmallRock_02"
)
ROCK_VALIDATION_GRAPH = (
    "/Game/Cubeless/PCG/ElectricDreamsLearning/DesignerStyleProfileMatrixCombos/"
    "PCG_Cubeless_ED_StyleProfileMatrix_SmallRocks_Both_GroundNormal_DitchSparse."
    "PCG_Cubeless_ED_StyleProfileMatrix_SmallRocks_Both_GroundNormal_DitchSparse"
)
VALIDATION_CASE_COMPONENTS = {
    "tree_baseline": "PCG_Tree",
    "tree_override": "PCG_Tree",
    "grass_override": "PCG_Style",
    "rock_override": "PCG_Style",
}

DYNAMIC_MESH_ATTR = "DynamicMeshPath"
OVERRIDE_TRUE_ATTR = "MeshOverrideTrue"


def analysis_dir():
    project_dir = pathlib.Path(unreal.Paths.project_dir()).resolve()
    return project_dir.parent / "unreal-mcp-cubeless" / "Docs" / "Analysis" / "ElectricDreams"


def load_config(script_name, namespace_name):
    script = analysis_dir() / script_name
    namespace = {"__name__": namespace_name, "__file__": str(script)}
    with open(script, "r", encoding="utf-8") as handle:
        code = compile(handle.read(), str(script), "exec")
    exec(code, namespace)
    return namespace


TREE_CONFIG = load_config("build_cubeless_ed_tree_profile_presets.py", "_tree_profile_config")
STYLE_CONFIG = load_config(
    "build_cubeless_ed_style_profile_matrix_presets.py",
    "_style_profile_matrix_config",
)


def add_node(graph, settings_cls, title, x, y):
    created = graph.add_node_of_type(settings_cls.static_class())
    node = created[0] if isinstance(created, tuple) else created
    node.set_editor_property("node_title", title)
    try:
        node.set_node_position(unreal.Vector2D(float(x), float(y)))
    except Exception:
        pass
    return node


def selector_import(settings, prop, text):
    selector = settings.get_editor_property(prop)
    selector.import_text(f"PCGBegin({text})PCGEnd")
    settings.set_editor_property(prop, selector)


def set_const_value_struct(value_struct, value_type, value):
    value_struct.set_editor_property("type", value_type)
    if value_type == unreal.PCGMetadataTypes.BOOLEAN:
        value_struct.set_editor_property("bool_value", bool(value))
    elif value_type == unreal.PCGMetadataTypes.INTEGER32:
        value_struct.set_editor_property("int32_value", int(value))
        value_struct.set_editor_property("int_value", int(value))
    elif value_type == unreal.PCGMetadataTypes.INTEGER64:
        value_struct.set_editor_property("int_value", int(value))
        value_struct.set_editor_property("int32_value", int(value))
    elif value_type == unreal.PCGMetadataTypes.SOFT_OBJECT_PATH:
        value_struct.set_editor_property("soft_object_path_value", unreal.SoftObjectPath(str(value)))
    elif value_type == unreal.PCGMetadataTypes.STRING:
        value_struct.set_editor_property("string_value", str(value))
    elif value_type == unreal.PCGMetadataTypes.NAME:
        value_struct.set_editor_property("name_value", str(value))
    else:
        value_struct.set_editor_property("double_value", float(value))
        value_struct.set_editor_property("float_value", float(value))
    return value_struct


def configure_add(node, output_attr, input_attr="@Last", value_type=None, value=None):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    selector_import(settings, "input_source", input_attr)
    selector_import(settings, "output_target", output_attr)
    if value_type is not None:
        value_struct = settings.get_editor_property("attribute_types")
        set_const_value_struct(value_struct, value_type, value)
        settings.set_editor_property("attribute_types", value_struct)


def configure_get_actor_property(node, property_name, output_attr):
    settings = node.get_settings()
    settings.set_editor_property("property_name", property_name)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("sanitize_output_attribute_name", True)
    selector_import(settings, "output_attribute_name", output_attr)


def configure_actor_bool_filter(node, use_property_name):
    settings = node.get_settings()
    settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.EQUAL)
    settings.set_editor_property("use_constant_threshold", False)
    settings.set_editor_property("use_spatial_query", False)
    selector_import(settings, "target_attribute", OVERRIDE_TRUE_ATTR)
    selector_import(settings, "threshold_attribute", use_property_name)
    settings.set_editor_property("warn_on_data_missing_attribute", False)
    settings.set_editor_property("generate_output_data_even_if_empty", True)


def configure_copy_actor_mesh(node, source_attr, target_attr=DYNAMIC_MESH_ATTR):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    selector_import(settings, "input_source", source_attr)
    selector_import(settings, "output_target", target_attr)


def configure_weighted_spawner(node, mesh_paths):
    settings = node.get_settings()
    entries = []
    for mesh_path in mesh_paths:
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        if not mesh:
            raise RuntimeError(f"Missing static mesh: {mesh_path}")
        descriptor = unreal.PCGSoftISMComponentDescriptor()
        descriptor.set_editor_property("static_mesh", mesh)
        entry = unreal.PCGMeshSelectorWeightedEntry()
        entry.set_editor_property("descriptor", descriptor)
        entry.set_editor_property("weight", 1)
        entries.append(entry)
    params = settings.get_editor_property("mesh_selector_parameters")
    params.set_editor_property("mesh_entries", entries)


def configure_by_attribute_spawner(node):
    settings = node.get_settings()
    settings.set_editor_property("allow_descriptor_changes", True)
    settings.set_mesh_selector_type(unreal.PCGMeshSelectorByAttribute.static_class())
    params = settings.get_editor_property("mesh_selector_parameters")
    params.set_editor_property("attribute_name", DYNAMIC_MESH_ATTR)
    params.set_editor_property("use_attribute_material_overrides", False)
    params.set_editor_property("material_override_attributes", [])


def configure_subgraph(node, subgraph_path):
    subgraph = unreal.EditorAssetLibrary.load_asset(subgraph_path)
    if not subgraph:
        raise RuntimeError(f"Missing subgraph asset: {subgraph_path}")
    settings = node.get_settings()
    instance = settings.get_editor_property("subgraph_instance")
    instance.set_editor_property("graph", subgraph)


def configure_density_filter(node, lower, upper):
    settings = node.get_settings()
    settings.set_editor_property("lower_bound", float(lower))
    settings.set_editor_property("upper_bound", float(upper))
    settings.set_editor_property("invert_filter", False)
    settings.set_editor_property("keep_zero_density_points", False)


def configure_duplicate(node, iterations, offset):
    settings = node.get_settings()
    settings.set_editor_property("iterations", int(iterations))
    settings.set_editor_property("output_source_point", True)
    transform = settings.get_editor_property("point_transform")
    transform.set_editor_property("translation", offset)
    settings.set_editor_property("point_transform", transform)


def add_mesh_override_switch(graph, upstream, domain_name, use_property, mesh_property, mesh_paths, x, y):
    flag = add_node(graph, unreal.PCGAddAttributeSettings, f"{domain_name} Override Flag True", x, y)
    configure_add(flag, OVERRIDE_TRUE_ATTR, "@Last", unreal.PCGMetadataTypes.BOOLEAN, True)

    get_use = add_node(graph, unreal.PCGGetActorPropertySettings, f"Get Actor {use_property}", x, y - 280)
    configure_get_actor_property(get_use, use_property, use_property)

    split = add_node(graph, unreal.PCGAttributeFilteringSettings, f"Split {domain_name} Mesh Override", x + 340, y)
    configure_actor_bool_filter(split, use_property)

    original_spawner = add_node(
        graph,
        unreal.PCGStaticMeshSpawnerSettings,
        f"Spawn {domain_name} Weighted Default",
        x + 700,
        y + 120,
    )
    configure_weighted_spawner(original_spawner, mesh_paths)

    get_mesh = add_node(graph, unreal.PCGGetActorPropertySettings, f"Get Actor {mesh_property}", x + 700, y - 280)
    configure_get_actor_property(get_mesh, mesh_property, mesh_property)

    copy_mesh = add_node(
        graph,
        unreal.PCGCopyAttributesSettings,
        f"Copy {mesh_property} To {DYNAMIC_MESH_ATTR}",
        x + 1040,
        y - 120,
    )
    configure_copy_actor_mesh(copy_mesh, mesh_property, DYNAMIC_MESH_ATTR)

    override_spawner = add_node(
        graph,
        unreal.PCGStaticMeshSpawnerSettings,
        f"Spawn {domain_name} ByActorMeshOverride",
        x + 1380,
        y - 120,
    )
    configure_by_attribute_spawner(override_spawner)

    merge = add_node(graph, unreal.PCGMergeSettings, f"Merge {domain_name} Mesh Override Result", x + 1760, y)

    graph.add_edge(upstream, "Out", flag, "In")
    graph.add_edge(flag, "Out", split, "In")
    graph.add_edge(get_use, "Out", split, "Filter")
    graph.add_edge(split, "OutsideFilter", original_spawner, "In")
    graph.add_edge(split, "InsideFilter", copy_mesh, "Target")
    graph.add_edge(get_mesh, "Out", copy_mesh, "Source")
    graph.add_edge(copy_mesh, "Out", override_spawner, "In")
    graph.add_edge(original_spawner, "Out", merge, "In")
    graph.add_edge(override_spawner, "Out", merge, "In")
    return merge


def ensure_blueprint_mesh_override_variables():
    blueprint = unreal.EditorAssetLibrary.load_asset(BLUEPRINT_PATH)
    if not blueprint:
        raise RuntimeError(f"Missing production candidate Blueprint: {BLUEPRINT_PATH}")

    bool_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    mesh_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.StaticMesh.static_class())
    variable_specs = [
        ("UseTreeMeshOverride", bool_type, False),
        ("UseGrassMeshOverride", bool_type, False),
        ("UseRockMeshOverride", bool_type, False),
        ("TreeMeshOverride", mesh_type, TREE_DEFAULT_MESH),
        ("GrassMeshOverride", mesh_type, GRASS_DEFAULT_MESH),
        ("RockMeshOverride", mesh_type, ROCK_DEFAULT_MESH),
    ]

    added = []
    for variable_name, pin_type, _ in variable_specs:
        if blueprint_variable_exists(blueprint, variable_name):
            continue
        ok = unreal.BlueprintEditorLibrary.add_member_variable(blueprint, variable_name, pin_type)
        if not ok:
            raise RuntimeError(f"Failed to add Blueprint variable: {variable_name}")
        added.append(variable_name)

    for variable_name, _, _ in variable_specs:
        set_variable_editable(blueprint, variable_name, True)
        set_variable_expose_on_spawn(blueprint, variable_name, True)

    blueprint.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    cls = unreal.EditorAssetLibrary.load_blueprint_class(BLUEPRINT_PATH)
    if not cls:
        raise RuntimeError(f"Failed to load Blueprint class after compile: {BLUEPRINT_PATH}")
    cdo = unreal.get_default_object(cls)
    cdo.modify()
    for variable_name, _, default_value in variable_specs:
        if isinstance(default_value, bool):
            cdo.set_editor_property(variable_name, default_value)
        else:
            mesh = unreal.EditorAssetLibrary.load_asset(default_value)
            if not mesh:
                raise RuntimeError(f"Missing default mesh for {variable_name}: {default_value}")
            cdo.set_editor_property(variable_name, mesh)

    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    return added


def blueprint_variable_exists(blueprint, variable_name):
    try:
        cls = unreal.EditorAssetLibrary.load_blueprint_class(BLUEPRINT_PATH)
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


def set_variable_editable(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(blueprint, variable_name, value)
    except Exception:
        blueprint.set_blueprint_variable_instance_editable(variable_name, value)


def set_variable_expose_on_spawn(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_expose_on_spawn(blueprint, variable_name, value)
    except Exception:
        blueprint.set_blueprint_variable_expose_on_spawn(variable_name, value)


def build_tree_profile_graph(spec):
    graph = TREE_CONFIG["ensure_graph"](spec["asset_name"])
    source = add_node(graph, unreal.PCGCreatePointsSettings, f"{spec['name']} Tree Points", -1200, 0)
    TREE_CONFIG["configure_points"](source, spec)
    markers = TREE_CONFIG["add_tree_markers"](graph, source, spec, -820, 0)
    merged = add_mesh_override_switch(
        graph,
        markers,
        "Tree",
        "UseTreeMeshOverride",
        "TreeMeshOverride",
        spec["mesh_paths"],
        2600,
        0,
    )
    graph.add_edge(merged, "Out", graph.get_output_node(), "Out")
    unreal.EditorAssetLibrary.save_loaded_asset(graph)
    return graph


def build_style_amount_graph(profile_key, amount, style):
    asset_name = STYLE_CONFIG["style_amount_asset_name"](profile_key, amount, style)
    graph = STYLE_CONFIG["ensure_graph"](STYLE_CONFIG["STYLE_AMOUNT_PACKAGE"], asset_name)

    source = add_node(graph, unreal.PCGSubgraphSettings, f"{amount['name']} Core", -1700, 0)
    configure_subgraph(source, amount["core_graph_path"])
    graph.add_edge(graph.get_input_node(), "In", source, "In")
    upstream = source
    x = -1320

    if amount["density_filter"]:
        lower, upper = amount["density_filter"]
        density_filter = add_node(graph, unreal.PCGDensityFilterSettings, f"Density {lower}-{upper}", x, 0)
        configure_density_filter(density_filter, lower, upper)
        graph.add_edge(upstream, "Out", density_filter, "In")
        upstream = density_filter
        x += 320

    if amount["duplicate_iterations"] > 0:
        duplicate = add_node(
            graph,
            unreal.PCGDuplicatePointSettings,
            f"Duplicate x{amount['duplicate_iterations']}",
            x,
            0,
        )
        configure_duplicate(duplicate, amount["duplicate_iterations"], amount["duplicate_offset"])
        graph.add_edge(upstream, "Out", duplicate, "In")
        upstream = duplicate
        x += 320

    markers = STYLE_CONFIG["add_profile_amount_style_markers"](graph, upstream, amount, style, x, 0)
    is_rock_style = int(style["style_type"]) == 5
    domain_name = "Rock" if is_rock_style else "Grass"
    use_property = "UseRockMeshOverride" if is_rock_style else "UseGrassMeshOverride"
    mesh_property = "RockMeshOverride" if is_rock_style else "GrassMeshOverride"
    merged = add_mesh_override_switch(
        graph,
        markers,
        domain_name,
        use_property,
        mesh_property,
        style["mesh_paths"],
        x + 2520,
        0,
    )
    graph.add_edge(merged, "Out", graph.get_output_node(), "Out")
    unreal.EditorAssetLibrary.save_loaded_asset(graph)
    return graph


def rebuild_target_graphs():
    tree_paths = []
    for spec in TREE_CONFIG["TREE_PROFILE_SPECS"]:
        tree_paths.append(build_tree_profile_graph(spec).get_path_name())

    style_amount_paths = []
    for style in STYLE_CONFIG["STYLE_SPECS"]:
        for amount in STYLE_CONFIG["GROUND_AMOUNT_SPECS"]:
            style_amount_paths.append(build_style_amount_graph("Ground", amount, style).get_path_name())
        for amount in STYLE_CONFIG["DITCH_AMOUNT_SPECS"]:
            style_amount_paths.append(build_style_amount_graph("Ditch", amount, style).get_path_name())
    return tree_paths, style_amount_paths


def get_all_level_actors():
    actor_subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if actor_subsystem_cls:
        actor_subsystem = unreal.get_editor_subsystem(actor_subsystem_cls)
        if actor_subsystem:
            return actor_subsystem.get_all_level_actors()
    return unreal.EditorLevelLibrary.get_all_level_actors()


def destroy_actor_by_label(label):
    for actor in list(get_all_level_actors()):
        if actor.get_actor_label() == label:
            unreal.EditorLevelLibrary.destroy_actor(actor)


def get_pcg_component(actor, name_prefix):
    for component in actor.get_components_by_class(unreal.PCGComponent):
        if component.get_name().startswith(name_prefix):
            return component
    raise RuntimeError(f"Missing PCG component prefix {name_prefix} on {actor.get_actor_label()}")


def generate_component(component):
    component.cleanup(True)
    component.generate(True)
    try:
        component.generate_local(True)
    except Exception:
        pass
    component.generate(True)


def ism_rows(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        rows.append({
            "component": component.get_name(),
            "mesh": mesh.get_path_name() if mesh else "None",
            "count": int(component.get_instance_count()),
        })
    rows.sort(key=lambda row: (row["mesh"], row["component"]))
    return rows


def actor_properties_summary(actor):
    props_summary = {}
    for prop in [
        "UseTreeMeshOverride",
        "TreeMeshOverride",
        "UseGrassMeshOverride",
        "GrassMeshOverride",
        "UseRockMeshOverride",
        "RockMeshOverride",
    ]:
        value = actor.get_editor_property(prop)
        props_summary[prop] = value.get_path_name() if hasattr(value, "get_path_name") else value
    return props_summary


def spawn_validation_actor(label, location):
    actor_class = unreal.EditorAssetLibrary.load_blueprint_class(BLUEPRINT_PATH)
    if not actor_class:
        raise RuntimeError(f"Missing Blueprint class: {BLUEPRINT_PATH}")
    destroy_actor_by_label(label)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    return actor


def set_validation_defaults(actor):
    defaults = {
        "UseTreeMeshOverride": False,
        "TreeMeshOverride": TREE_DEFAULT_MESH,
        "UseGrassMeshOverride": False,
        "GrassMeshOverride": GRASS_DEFAULT_MESH,
        "UseRockMeshOverride": False,
        "RockMeshOverride": ROCK_DEFAULT_MESH,
    }
    for prop, value in defaults.items():
        if isinstance(value, str):
            mesh = unreal.EditorAssetLibrary.load_asset(value)
            if not mesh:
                raise RuntimeError(f"Missing default validation mesh: {value}")
            actor.set_editor_property(prop, mesh)
        else:
            actor.set_editor_property(prop, value)


def validation_case(case_name, component_prefix, props, graph_path=None, location=None):
    if location is None:
        location = unreal.Vector(142000, 0, 0)
    actor = spawn_validation_actor(f"{VALIDATION_ACTOR_PREFIX}_{case_name}", location)
    set_validation_defaults(actor)
    for prop, value in props.items():
        if isinstance(value, str):
            mesh = unreal.EditorAssetLibrary.load_asset(value)
            if not mesh:
                raise RuntimeError(f"Missing validation mesh: {value}")
            actor.set_editor_property(prop, mesh)
        else:
            actor.set_editor_property(prop, value)
    component = get_pcg_component(actor, component_prefix)
    if graph_path:
        graph = unreal.EditorAssetLibrary.load_asset(graph_path)
        if not graph:
            raise RuntimeError(f"Missing validation graph: {graph_path}")
        component.set_graph(graph)
    generate_component(component)
    return {
        "actor": actor.get_actor_label(),
        "component": component.get_name(),
        "graph": get_component_graph_path(component),
        "properties": actor_properties_summary(actor),
        "rows": ism_rows(actor),
    }


def find_actor_by_label(label):
    for actor in get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def read_existing_validation():
    cases = {}
    for case_name, component_prefix in VALIDATION_CASE_COMPONENTS.items():
        label = f"{VALIDATION_ACTOR_PREFIX}_{case_name}"
        actor = find_actor_by_label(label)
        if not actor:
            cases[case_name] = {
                "actor": label,
                "component": component_prefix,
                "graph": None,
                "properties": {},
                "rows": [],
                "error": "actor not found",
            }
            continue
        component = get_pcg_component(actor, component_prefix)
        cases[case_name] = {
            "actor": actor.get_actor_label(),
            "component": component.get_name(),
            "graph": get_component_graph_path(component),
            "properties": actor_properties_summary(actor),
            "rows": ism_rows(actor),
        }
    return {
        "actor_prefix": VALIDATION_ACTOR_PREFIX,
        "cases": cases,
    }


def get_component_graph_path(component):
    try:
        graph = component.get_editor_property("graph")
        if graph:
            return graph.get_path_name()
    except Exception:
        pass
    try:
        graph_instance = component.get_editor_property("graph_instance")
        if graph_instance:
            graph = graph_instance.get_editor_property("graph")
            if graph:
                return graph.get_path_name()
    except Exception:
        pass
    return None


def run_validation():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(VALIDATION_LEVEL)

    tree_baseline = validation_case(
        "tree_baseline",
        "PCG_Tree",
        {
            "UseTreeMeshOverride": False,
            "TreeMeshOverride": TREE_OVERRIDE_TEST_MESH,
        },
        location=unreal.Vector(144000, 0, 0),
    )
    tree_override = validation_case(
        "tree_override",
        "PCG_Tree",
        {
            "UseTreeMeshOverride": True,
            "TreeMeshOverride": TREE_OVERRIDE_TEST_MESH,
        },
        location=unreal.Vector(146000, 0, 0),
    )
    grass_override = validation_case(
        "grass_override",
        "PCG_Style",
        {
            "UseGrassMeshOverride": True,
            "GrassMeshOverride": GRASS_OVERRIDE_TEST_MESH,
            "UseRockMeshOverride": False,
        },
        location=unreal.Vector(148000, 0, 0),
    )

    rock_override = validation_case(
        "rock_override",
        "PCG_Style",
        {
            "UseGrassMeshOverride": False,
            "UseRockMeshOverride": True,
            "RockMeshOverride": ROCK_OVERRIDE_TEST_MESH,
        },
        graph_path=ROCK_VALIDATION_GRAPH,
        location=unreal.Vector(150000, 0, 0),
    )

    return {
        "actor_prefix": VALIDATION_ACTOR_PREFIX,
        "cases": {
            "tree_baseline": tree_baseline,
            "tree_override": tree_override,
            "grass_override": grass_override,
            "rock_override": rock_override,
        },
    }


def summarize_validation(validation):
    def total(rows):
        return sum(max(0, int(row["count"])) for row in rows)

    def positive_meshes(rows):
        return {row["mesh"] for row in rows if int(row["count"]) > 0}

    cases = validation["cases"]
    tree_base_meshes = positive_meshes(cases["tree_baseline"]["rows"])
    tree_override_meshes = positive_meshes(cases["tree_override"]["rows"])
    grass_override_meshes = positive_meshes(cases["grass_override"]["rows"])
    rock_override_meshes = positive_meshes(cases["rock_override"]["rows"])

    checks = {
        "tree_baseline_preserves_default": (
            total(cases["tree_baseline"]["rows"]) > 0
            and TREE_DEFAULT_MESH in tree_base_meshes
            and TREE_OVERRIDE_TEST_MESH not in tree_base_meshes
        ),
        "tree_override_uses_bp_mesh": (
            total(cases["tree_override"]["rows"]) > 0
            and tree_override_meshes == {TREE_OVERRIDE_TEST_MESH}
        ),
        "grass_override_uses_bp_mesh": (
            total(cases["grass_override"]["rows"]) > 0
            and grass_override_meshes == {GRASS_OVERRIDE_TEST_MESH}
        ),
        "rock_override_uses_bp_mesh": (
            total(cases["rock_override"]["rows"]) > 0
            and rock_override_meshes == {ROCK_OVERRIDE_TEST_MESH}
        ),
    }
    checks["validation_pass"] = all(checks.values())
    return checks


def write_report(report):
    project_dir = pathlib.Path(unreal.Paths.project_dir()).resolve()
    report_path = project_dir / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(report_path)


def finalize_deferred_validation(report, tick_state):
    tick_state["ticks"] += 1
    if tick_state["ticks"] < DEFERRED_VALIDATION_MIN_TICKS:
        return

    validation = read_existing_validation()
    checks = summarize_validation(validation)
    if not checks["validation_pass"] and tick_state["ticks"] < DEFERRED_VALIDATION_MAX_TICKS:
        return

    try:
        unreal.unregister_slate_post_tick_callback(tick_state["handle"])
    except Exception:
        pass

    report["validation_mode"] = "separate_actors_deferred_read"
    report["validation"] = validation
    report["checks"] = checks
    report["deferred_validation_ticks"] = tick_state["ticks"]
    report_path = write_report(report)
    print(json.dumps({"report_path": report_path, "checks": checks}, indent=2, ensure_ascii=False))
    if not checks["validation_pass"]:
        print(f"PCG mesh override deferred validation failed: {json.dumps(checks, ensure_ascii=False)}")


def schedule_deferred_validation(report):
    tick_state = {"ticks": 0, "handle": None}

    def on_tick(_delta_seconds):
        finalize_deferred_validation(report, tick_state)

    tick_state["handle"] = unreal.register_slate_post_tick_callback(on_tick)
    return tick_state["handle"]


def main():
    print("MCP_CUBELESS_PCG_MESH_OVERRIDE_ACTOR_PROPERTIES_BEGIN")
    added_variables = ensure_blueprint_mesh_override_variables()
    tree_paths, style_amount_paths = rebuild_target_graphs()
    validation = run_validation()
    checks = summarize_validation(validation)
    report = {
        "blueprint": BLUEPRINT_PATH,
        "validation_mode": "separate_actors_immediate_read",
        "added_variables": added_variables,
        "variables": [
            "UseTreeMeshOverride",
            "TreeMeshOverride",
            "UseGrassMeshOverride",
            "GrassMeshOverride",
            "UseRockMeshOverride",
            "RockMeshOverride",
        ],
        "graph_route": (
            "Use*MeshOverride actor property splits points; false/missing property keeps weighted default, "
            "*MeshOverride actor property is copied to DynamicMeshPath and consumed by PCGMeshSelectorByAttribute."
        ),
        "tree_graph_count": len(tree_paths),
        "style_amount_graph_count": len(style_amount_paths),
        "tree_graphs": tree_paths,
        "style_amount_graphs": style_amount_paths,
        "validation": validation,
        "checks": checks,
    }
    report_path = write_report(report)
    print(json.dumps({"report_path": report_path, "checks": checks}, indent=2, ensure_ascii=False))
    if not checks["validation_pass"]:
        handle = schedule_deferred_validation(report)
        print(
            "Immediate PCG mesh override validation is pending deferred read; "
            f"scheduled slate tick callback {handle}."
        )
        print("MCP_CUBELESS_PCG_MESH_OVERRIDE_ACTOR_PROPERTIES_DEFERRED_PENDING")
        return
    print("MCP_CUBELESS_PCG_MESH_OVERRIDE_ACTOR_PROPERTIES_END")


if __name__ == "__main__":
    main()
