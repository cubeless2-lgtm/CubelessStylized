from __future__ import annotations

import contextlib
import copy
import json
import os

import unreal

import CubelessDungeonPCG as v1


V2_ROOT = "/Game/Cubeless/PCG/DungeonV2"
V2_MATERIAL_DIR = V2_ROOT + "/Materials"
V2_MESH_DIR = V2_ROOT + "/Meshes"
V2_GRAPH_DIR = V2_ROOT + "/Graphs"
V2_MAP_DIR = V2_ROOT + "/Maps"
V2_BLUEPRINT_DIR = V2_ROOT + "/Blueprints"

V2_LEVEL_PATH = V2_MAP_DIR + "/LVL_Cubeless_PCG_Dungeon_V2"
V2_GRAPH_NAME = "PCG_Cubeless_Dungeon_V2_Bridge"
V2_NATIVE_GRAPH_NAME = "PCG_Cubeless_Dungeon_V2_NativeSkeleton"
V2_NATIVE_POINT_SOURCE_GRAPH_NAME = "PCG_Cubeless_Dungeon_V2_NativePointSource"
V2_NATIVE_INTEGRATION_GRAPH_NAME = "PCG_Cubeless_Dungeon_V2_NativeIntegration"
V2_NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME = "PCG_Cubeless_Dungeon_V2_NativePointSource_PreviewOffset"
V2_NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME = "PCG_Cubeless_Dungeon_V2_NativeIntegration_PreviewOffset"

V2_ACTOR_PREFIX = "MCP_Dungeon_V2_"
V2_GAMEPLAY_PLACEHOLDER_PREFIX = "MCP_DungeonV2_Gameplay_"
V2_BRIDGE_LABEL = "MCP_Cubeless_Dungeon_V2_PCGBridge"
V2_NATIVE_INTEGRATION_TEST_LABEL = "MCP_Cubeless_Dungeon_V2_NativeIntegrationTest"
V2_NATIVE_INTEGRATION_OUTPUT_LABEL = "MCP_Cubeless_Dungeon_V2_NativeOutput"
V2_NATIVE_INTEGRATION_PREVIEW_LABEL = "MCP_Cubeless_Dungeon_V2_NativeIntegrationPreview"
V2_CONTROLLER_BLUEPRINT_NAME = "BP_Cubeless_DungeonV2_Controller"
V2_CONTROLLER_BLUEPRINT_PATH = V2_BLUEPRINT_DIR + "/" + V2_CONTROLLER_BLUEPRINT_NAME
V2_CONTROLLER_LABEL = "MCP_Cubeless_Dungeon_V2_Controller"
V2_CONTROLLER_PCG_COMPONENT_NAME = "PCG_DungeonV2_Bridge"
V2_PARAMETER_NODE_TITLE_PREFIX = "Get BP Parameter "
V2_BASE_WALL_HEIGHT = float(v1.WALL_HEIGHT)
V2_STORY_HEIGHT_SCALE = 2.0
V2_WALL_HEIGHT = V2_BASE_WALL_HEIGHT * V2_STORY_HEIGHT_SCALE
V2_STORY_HEIGHT_MODULE_KEYS = ("wall", "door", "column")

V2_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
V2_ENTRYPOINT_PATH = os.path.join(V2_SCRIPT_DIR, "CubelessDungeonPCGV2Entrypoint.py")
V2_REPORT_DIR_NAME = "MCP_DungeonV2"
V2_REPORT_PREFIX = "CubelessDungeonV2"
V2_CORE_OUTPUT_EXCLUDED_MODULES = {
    "connector_detail",
    "corridor_detail",
    "marker",
    "room_variant_detail",
    "detail_mesh",
}
V2_OUTPUT_POLICY = {
    "mode": "core_structure_output",
    "excluded_modules": sorted(V2_CORE_OUTPUT_EXCLUDED_MODULES),
    "reason": (
        "V2 keeps room-rule, connector/corridor detail, and gameplay marker data in reports, but excludes "
        "overlapping detail/review meshes from the default Native PCG structure output."
    ),
}
V2_ROOM_RULE_MEANINGS = {
    "start": "Player entry room marker and spawn anchor.",
    "exit": "Dungeon exit route marker.",
    "boss": "Final encounter room marker.",
    "key": "Progression key room marker linked to locked gates.",
    "shop": "Utility/shop room marker.",
    "treasure": "Reward room marker.",
    "combat": "Enemy/combat room marker.",
    "locked_after": "Room reached after a locked gate.",
}
V2_CONFIG_MEANINGS = {
    "seed": "Deterministic layout seed.",
    "room_count": "Requested room count.",
    "branch_chance_percent": "Chance to add valid branch or loop edges.",
    "max_loop_edges": "Maximum extra loop or branch edges.",
    "grid_cell_size": "World grid spacing and base module XY scale.",
    "corridor_width": "Corridor, door, connector, and seal width scale.",
    "use_ceiling": "Ceiling module toggle.",
    "ceiling_stride": "Ceiling sampling cadence.",
    "key_count": "Progression key room count.",
    "locked_door_count": "Locked progression gate count.",
    "shop_count": "Shop room count.",
    "chest_count": "Reward room count.",
    "enemy_count": "Combat room budget.",
    "boss_enabled": "Boss/exit encounter toggle.",
    "use_theme_materials": "Room-theme material override toggle.",
    "preview_mode": "Review metadata flag.",
}
V2_MATRIX_CONFIG_KEYS = [
    "seed",
    "room_count",
    "grid_cell_size",
    "corridor_width",
    "branch_chance_percent",
    "max_loop_edges",
    "key_count",
    "shop_count",
    "chest_count",
    "enemy_count",
    "locked_door_count",
    "boss_enabled",
    "use_ceiling",
    "ceiling_stride",
]
V2_TUNING_GUIDE_GOALS = [
    {
        "goal": "balanced_default",
        "title": "Balanced V2 baseline",
        "recommended_presets": ["default"],
        "use_when": "Use this when you want the current stable V2 dungeon shape with balanced route, reward, combat, and ceiling coverage.",
        "tradeoff": "It is the safest baseline, but it is not the fastest iteration map and not the most loop-heavy route.",
    },
    {
        "goal": "fast_small_iteration",
        "title": "Fast small iteration",
        "recommended_presets": ["small_route", "compact_branching"],
        "use_when": "Use this when layout readability, quick refresh review, and compact test screenshots matter more than dungeon size.",
        "tradeoff": "Smaller layouts expose fewer long-route and large-room problems.",
    },
    {
        "goal": "loop_route_variety",
        "title": "More loops and route variety",
        "recommended_presets": ["loop_dense", "wide_looped"],
        "use_when": "Use this when testing alternate paths, branch readability, and connector/wall behavior around loops.",
        "tradeoff": "Loop-heavy layouts can be visually busier and should be checked with the top screenshot.",
    },
    {
        "goal": "ceiling_off_structure_review",
        "title": "Ceiling-off structural review",
        "recommended_presets": ["open_cutaway"],
        "use_when": "Use this when you need to inspect wall direction, door gaps, room boundaries, and corridor joins from above.",
        "tradeoff": "It is a review preset, not the target closed dungeon mood.",
    },
    {
        "goal": "boss_combat_focus",
        "title": "Boss and combat focus",
        "recommended_presets": ["boss_focus"],
        "use_when": "Use this when the boss room, combat room allocation, and progression gate placement are the current concern.",
        "tradeoff": "It favors encounter checks over balanced reward-room distribution.",
    },
    {
        "goal": "longer_route_less_dense",
        "title": "Longer route with fewer loops",
        "recommended_presets": ["long_route"],
        "use_when": "Use this when checking longer main-route pacing without making the graph too branch-dense.",
        "tradeoff": "It is useful for path pacing, but less useful for loop stress testing.",
    },
]
V2_TUNING_PARAMETER_KNOBS = [
    {
        "key": "room_count",
        "meaning": "Changes the requested number of rooms.",
        "increase": "Larger dungeon and more chances for side rooms.",
        "decrease": "Faster iteration and simpler readability.",
    },
    {
        "key": "branch_chance_percent",
        "meaning": "Controls how aggressively valid branch or loop candidates are accepted.",
        "increase": "More route variety when `max_loop_edges` also allows it.",
        "decrease": "Straighter route and fewer confusing joins.",
    },
    {
        "key": "max_loop_edges",
        "meaning": "Caps extra loop or branch edges.",
        "increase": "More alternate connections and PCG join stress testing.",
        "decrease": "Cleaner main-route validation.",
    },
    {
        "key": "grid_cell_size",
        "meaning": "Controls world spacing and the visual footprint of the whole dungeon.",
        "increase": "More generous spacing and easier camera review.",
        "decrease": "Compact footprint, but tighter visual overlap risk.",
    },
    {
        "key": "corridor_width",
        "meaning": "Controls corridor, door, connector, and seal width scale.",
        "increase": "Wider movement/readability space.",
        "decrease": "Narrower dungeon feel and stronger corridor compression.",
    },
    {
        "key": "enemy_count",
        "meaning": "Controls combat room budget.",
        "increase": "More combat-role rooms and encounter slots.",
        "decrease": "Less combat noise while reviewing structure.",
    },
    {
        "key": "chest_count",
        "meaning": "Controls reward room budget.",
        "increase": "More treasure/reward room pressure.",
        "decrease": "Cleaner route and structure-only review.",
    },
    {
        "key": "key_count",
        "meaning": "Controls progression key room count.",
        "increase": "More progression item pressure when lock rules support it.",
        "decrease": "Simpler progression validation.",
    },
    {
        "key": "shop_count",
        "meaning": "Controls utility/shop room count.",
        "increase": "More utility-room allocation pressure.",
        "decrease": "Less non-combat side-room noise.",
    },
    {
        "key": "locked_door_count",
        "meaning": "Controls locked progression gate count.",
        "increase": "More gate/key validation pressure.",
        "decrease": "Simpler route reachability checks.",
    },
    {
        "key": "boss_enabled",
        "meaning": "Controls whether the boss/exit encounter role is used.",
        "increase": "Enable final encounter review.",
        "decrease": "Disable boss-specific route pressure for structure-only tests.",
    },
    {
        "key": "use_ceiling",
        "meaning": "Controls ceiling module generation.",
        "increase": "Closed dungeon mood and delivery-like visual review.",
        "decrease": "Open top-down structural inspection.",
    },
    {
        "key": "ceiling_stride",
        "meaning": "Controls ceiling sampling cadence.",
        "increase": "Sparser ceiling coverage for review when supported by the graph.",
        "decrease": "Denser ceiling coverage.",
    },
]


def _saved_report_path(filename):
    return os.path.join(unreal.Paths.project_saved_dir(), V2_REPORT_DIR_NAME, filename)


def _scale_2x_config(config, *, seed_offset=100000):
    result = dict(config)
    result["seed"] = int(result.get("seed", 1)) + int(seed_offset)
    result["grid_cell_size"] = min(1200, max(200, int(round(float(result.get("grid_cell_size", 400)) * 2.0))))
    result["corridor_width"] = min(1200, max(200, int(round(float(result.get("corridor_width", 400)) * 2.0))))
    return result


V2_DEFAULT_DUNGEON_CONFIG = _scale_2x_config(v1.DEFAULT_DUNGEON_CONFIG)

V2_AUTHORING_PRESETS = {
    name: _scale_2x_config(config, seed_offset=100000 + index * 17)
    for index, (name, config) in enumerate(sorted(v1.DUNGEON_AUTHORING_PRESETS.items()))
}
V2_AUTHORING_PRESETS["default"] = dict(V2_DEFAULT_DUNGEON_CONFIG)

V2_AUTHORING_PRESET_NOTES = {
    name: dict(
        v1.DUNGEON_AUTHORING_PRESET_NOTES.get(name, {}),
        label="V2 2x " + v1.DUNGEON_AUTHORING_PRESET_NOTES.get(name, {}).get("label", name.replace("_", " ").title()),
        intent=(
            "V2 2x spatial-scale prototype. "
            + v1.DUNGEON_AUTHORING_PRESET_NOTES.get(name, {}).get("intent", "")
        ).strip(),
    )
    for name in V2_AUTHORING_PRESETS
}


def _v2_build_door_mesh():
    mesh = unreal.DynamicMesh()
    side_width = 70.0
    lintel_height = max(64.0, V2_WALL_HEIGHT * 0.2)
    opening_width = 220.0
    opening_height = max(250.0, V2_WALL_HEIGHT - lintel_height)
    total_width = opening_width + side_width * 2.0
    v1.box(
        mesh,
        "M_Dungeon_Door_WornBronze",
        (-opening_width * 0.5 - side_width * 0.5, 0, opening_height * 0.5),
        (side_width, v1.WALL_THICKNESS * 1.35, opening_height),
    )
    v1.box(
        mesh,
        "M_Dungeon_Door_WornBronze",
        (opening_width * 0.5 + side_width * 0.5, 0, opening_height * 0.5),
        (side_width, v1.WALL_THICKNESS * 1.35, opening_height),
    )
    v1.box(
        mesh,
        "M_Dungeon_Door_WornBronze",
        (0, 0, opening_height + lintel_height * 0.5),
        (total_width, v1.WALL_THICKNESS * 1.45, lintel_height),
    )
    v1.box(
        mesh,
        "M_Dungeon_Trim_DarkIron",
        (0, -v1.WALL_THICKNESS, opening_height + 8),
        (total_width + 28, 12, 16),
    )
    return mesh


def _v2_mesh_builders():
    builders = dict(v1.MESH_BUILDERS)
    builders["door"] = _v2_build_door_mesh
    return builders


def _v2_load_existing_materials():
    materials = []
    missing = []
    for name, *_rest in v1.MATERIALS:
        material = unreal.EditorAssetLibrary.load_asset(V2_MATERIAL_DIR + "/" + name)
        if not material:
            missing.append(V2_MATERIAL_DIR + "/" + name)
        materials.append(material)
    if missing:
        raise RuntimeError("Missing V2 dungeon materials for targeted mesh rebuild: " + ", ".join(missing))
    return materials


def _v2_controller_var_name(spec):
    return v1.CONFIG_TAG_PREFIX + str(spec["tag"])


def _v2_controller_specs():
    specs = []
    for spec in v1.CONFIG_AUTHORING_SPECS:
        default_value = V2_DEFAULT_DUNGEON_CONFIG.get(spec["config_key"])
        is_bool = spec.get("type") == "bool_int"
        specs.append(
            {
                "config_key": spec["config_key"],
                "variable_name": _v2_controller_var_name(spec),
                "tag": v1.CONFIG_TAG_PREFIX + str(spec["tag"]),
                "pin_type": "bool" if is_bool else "int",
                "default_value": bool(int(default_value or 0)) if is_bool else int(default_value),
                "min": spec.get("min"),
                "max": spec.get("max"),
                "purpose": spec.get("purpose"),
            }
        )
    return specs


def _v2_find_actor_by_label(label):
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_actor_label() == label:
                return actor
        except Exception:
            pass
    return None


def _v2_find_controller_actor():
    return _v2_find_actor_by_label(V2_CONTROLLER_LABEL)


def _v2_load_or_create_controller_blueprint():
    unreal.EditorAssetLibrary.make_directory(V2_BLUEPRINT_DIR)
    blueprint = unreal.EditorAssetLibrary.load_asset(V2_CONTROLLER_BLUEPRINT_PATH)
    created = False
    if not blueprint:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor)
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            V2_CONTROLLER_BLUEPRINT_NAME,
            V2_BLUEPRINT_DIR,
            unreal.Blueprint,
            factory,
        )
        created = True
    return blueprint, created


def _v2_ensure_controller_variables(blueprint):
    added = []
    existing_or_failed = []
    for spec in _v2_controller_specs():
        pin_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name(spec["pin_type"])
        variable_name = spec["variable_name"]
        try:
            was_added = bool(unreal.BlueprintEditorLibrary.add_member_variable(blueprint, variable_name, pin_type))
        except Exception as exc:
            was_added = False
            existing_or_failed.append({"variable": variable_name, "error": str(exc)})
        else:
            if was_added:
                added.append(variable_name)
            else:
                existing_or_failed.append({"variable": variable_name, "already_existed_or_not_added": True})
        try:
            unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(blueprint, variable_name, True)
            unreal.BlueprintEditorLibrary.set_blueprint_variable_expose_on_spawn(blueprint, variable_name, True)
        except Exception as exc:
            existing_or_failed.append({"variable": variable_name, "metadata_error": str(exc)})
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_asset(V2_CONTROLLER_BLUEPRINT_PATH, only_if_is_dirty=False)
    return {"added_variables": added, "existing_or_failed": existing_or_failed}


def _v2_get_blueprint_subobject_rows(blueprint):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    rows = []
    if not subsystem or not library or not blueprint:
        return rows
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


def _v2_configure_pcg_component(component, graph):
    report = {"component": component.get_name() if component else None, "graph": None, "errors": []}
    if not component:
        report["errors"].append("missing component")
        return report
    if graph:
        try:
            component.set_graph(graph)
            report["graph"] = graph.get_path_name()
        except Exception as exc:
            report["errors"].append("set_graph: " + str(exc))
    try:
        component.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
        report["generation_trigger"] = str(component.get_editor_property("generation_trigger"))
    except Exception as exc:
        report["errors"].append("generation_trigger: " + str(exc))
    try:
        component.set_editor_property("input_type", unreal.PCGComponentInput.ACTOR)
        report["input_type"] = str(component.get_editor_property("input_type"))
    except Exception as exc:
        report["errors"].append("input_type: " + str(exc))
    report["pass"] = not report["errors"]
    return report


def _v2_component_graph_path(component):
    if not component:
        return None
    try:
        graph = component.get_graph()
        return graph.get_path_name() if graph else None
    except Exception:
        pass
    try:
        graph = component.get_editor_property("graph")
        return graph.get_path_name() if graph else None
    except Exception:
        return None


def _v2_graph_paths_match(actual_path, expected_package_path):
    if not actual_path or not expected_package_path:
        return False
    actual = str(actual_path)
    expected = str(expected_package_path)
    asset_name = expected.rsplit("/", 1)[-1]
    return actual == expected or actual == expected + "." + asset_name


def _v2_ensure_controller_pcg_component(blueprint):
    graph = unreal.EditorAssetLibrary.load_asset(V2_GRAPH_DIR + "/" + V2_GRAPH_NAME)
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    rows_before = _v2_get_blueprint_subobject_rows(blueprint)
    root_handle = None
    for row in rows_before:
        if row["is_default_scene_root"] or row["is_root_component"]:
            root_handle = row["handle"]
            break
    matching = [
        row
        for row in rows_before
        if row["class"] == unreal.PCGComponent.static_class().get_name()
        and (row["variable"] == V2_CONTROLLER_PCG_COMPONENT_NAME or row["display"] == V2_CONTROLLER_PCG_COMPONENT_NAME)
    ]
    added = False
    add_error = None
    if not matching and subsystem and root_handle is not None:
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("blueprint_context", blueprint)
        params.set_editor_property("new_class", unreal.PCGComponent)
        params.set_editor_property("parent_handle", root_handle)
        params.set_editor_property("skip_mark_blueprint_modified", False)
        params.set_editor_property("conform_transform_to_parent", True)
        try:
            new_handle, fail_reason = subsystem.add_new_subobject(params)
            if str(fail_reason):
                add_error = str(fail_reason)
            else:
                subsystem.rename_subobject(new_handle, unreal.Text(V2_CONTROLLER_PCG_COMPONENT_NAME))
                try:
                    subsystem.rename_subobject_member_variable(
                        blueprint,
                        new_handle,
                        unreal.Name(V2_CONTROLLER_PCG_COMPONENT_NAME),
                    )
                except Exception:
                    pass
                added = True
        except Exception as exc:
            add_error = str(exc)

    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    rows_after = _v2_get_blueprint_subobject_rows(blueprint)
    matching_after = [
        row
        for row in rows_after
        if row["class"] == unreal.PCGComponent.static_class().get_name()
        and (row["variable"] == V2_CONTROLLER_PCG_COMPONENT_NAME or row["display"] == V2_CONTROLLER_PCG_COMPONENT_NAME)
    ]
    template_report = {"pass": False, "skipped": True}
    if matching_after:
        template_report = _v2_configure_pcg_component(matching_after[0].get("object"), graph)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False)
    return {
        "schema": "cubeless_pcg_dungeon_v2_controller_pcg_component_template_v1",
        "component_name": V2_CONTROLLER_PCG_COMPONENT_NAME,
        "graph_path": V2_GRAPH_DIR + "/" + V2_GRAPH_NAME,
        "graph_exists": bool(graph),
        "added_component": added,
        "add_error": add_error,
        "component_rows_before": [
            {key: value for key, value in row.items() if key not in {"handle", "object"}}
            for row in rows_before
            if row.get("class") == "PCGComponent"
        ],
        "component_rows_after": [
            {key: value for key, value in row.items() if key not in {"handle", "object"}}
            for row in rows_after
            if row.get("class") == "PCGComponent"
        ],
        "template_configure": template_report,
        "pass": bool(graph and matching_after and template_report.get("pass") and not add_error),
    }


def _v2_controller_actor_pcg_components(actor):
    if not actor:
        return []
    try:
        return list(actor.get_components_by_class(unreal.PCGComponent))
    except Exception:
        return []


def _v2_controller_actor_pcg_component(actor):
    components = _v2_controller_actor_pcg_components(actor)
    for component in components:
        try:
            if component.get_name().startswith(V2_CONTROLLER_PCG_COMPONENT_NAME):
                return component
        except Exception:
            pass
    return components[0] if components else None


def _v2_ensure_controller_actor_pcg_component(actor):
    graph = unreal.EditorAssetLibrary.load_asset(V2_GRAPH_DIR + "/" + V2_GRAPH_NAME)
    rerun_error = None
    if actor:
        try:
            actor.rerun_construction_scripts()
        except Exception as exc:
            rerun_error = str(exc)
    component = _v2_controller_actor_pcg_component(actor)
    configure_report = _v2_configure_pcg_component(component, graph) if component else {
        "pass": False,
        "errors": ["missing placed actor PCGComponent"],
    }
    components = _v2_controller_actor_pcg_components(actor)
    component_rows = []
    for item in components:
        component_rows.append(
            {
                "name": item.get_name(),
                "class": item.get_class().get_name(),
                "graph_path": _v2_component_graph_path(item),
            }
        )
    graph_path = _v2_component_graph_path(component)
    configured_graph_path = configure_report.get("graph") if isinstance(configure_report, dict) else None
    return {
        "schema": "cubeless_pcg_dungeon_v2_controller_pcg_component_actor_v1",
        "actor_label": actor.get_actor_label() if actor else V2_CONTROLLER_LABEL,
        "component_name": component.get_name() if component else None,
        "component_count": len(components),
        "component_rows": component_rows,
        "graph_path": graph_path,
        "expected_graph_path": V2_GRAPH_DIR + "/" + V2_GRAPH_NAME,
        "rerun_construction_error": rerun_error,
        "configure": configure_report,
        "pass": bool(
            component
            and configure_report.get("pass")
            and (
                _v2_graph_paths_match(graph_path, V2_GRAPH_DIR + "/" + V2_GRAPH_NAME)
                or _v2_graph_paths_match(configured_graph_path, V2_GRAPH_DIR + "/" + V2_GRAPH_NAME)
            )
        ),
    }


def _v2_set_controller_actor_values(actor, config):
    values = {}
    errors = []
    for spec in _v2_controller_specs():
        variable_name = spec["variable_name"]
        raw_value = config.get(spec["config_key"], V2_DEFAULT_DUNGEON_CONFIG.get(spec["config_key"]))
        value = bool(int(raw_value or 0)) if spec["pin_type"] == "bool" else int(raw_value)
        try:
            actor.set_editor_property(variable_name, value)
            values[variable_name] = actor.get_editor_property(variable_name)
        except Exception as exc:
            errors.append({"variable": variable_name, "value": value, "error": str(exc)})
    return {"values": values, "errors": errors}


def _v2_controller_actor_to_config(actor, clamp_to_ranges=False):
    raw_values = {}
    values = {}
    errors = []
    clamped_values = []
    for spec in _v2_controller_specs():
        variable_name = spec["variable_name"]
        try:
            value = actor.get_editor_property(variable_name)
        except Exception as exc:
            errors.append({"variable": variable_name, "error": str(exc)})
            continue
        raw_values[variable_name] = value
        normalized_value = 1 if isinstance(value, bool) and value else (0 if isinstance(value, bool) else int(value))
        if clamp_to_ranges:
            clamped_value = normalized_value
            min_value = spec.get("min")
            max_value = spec.get("max")
            if min_value is not None:
                clamped_value = max(int(min_value), int(clamped_value))
            if max_value is not None:
                clamped_value = min(int(max_value), int(clamped_value))
            if clamped_value != normalized_value:
                corrected_value = bool(clamped_value) if spec["pin_type"] == "bool" else int(clamped_value)
                try:
                    actor.set_editor_property(variable_name, corrected_value)
                    raw_values[variable_name] = actor.get_editor_property(variable_name)
                    clamped_values.append(
                        {
                            "variable": variable_name,
                            "config_key": spec["config_key"],
                            "from": normalized_value,
                            "to": clamped_value,
                            "min": min_value,
                            "max": max_value,
                        }
                    )
                    normalized_value = clamped_value
                except Exception as exc:
                    errors.append(
                        {
                            "variable": variable_name,
                            "value": corrected_value,
                            "clamp_error": str(exc),
                        }
                    )
        values[spec["config_key"]] = normalized_value
    override_report = normalize_authoring_config_overrides(values)
    checks = {
        "actor_found": bool(actor),
        "read_error_count_zero": not errors,
        "all_controller_fields_present": len(values) == len(_v2_controller_specs()),
        "config_values_valid": bool(override_report.get("pass")),
    }
    return {
        "schema": "cubeless_pcg_dungeon_v2_bp_controller_config_v1",
        "actor_label": actor.get_actor_label() if actor else V2_CONTROLLER_LABEL,
        "raw_values": raw_values,
        "config": override_report.get("config", {}),
        "config_overrides": override_report,
        "clamp_to_ranges": bool(clamp_to_ranges),
        "clamped_values": clamped_values,
        "read_errors": errors,
        "checks": checks,
        "pass": all(bool(value) for value in checks.values()),
    }


def _v2_room_count_controller_spec():
    for spec in _v2_controller_specs():
        if spec["config_key"] == "room_count":
            return spec
    return None


def _v2_resolve_controller_layout_config(dungeon, actor, config):
    requested_config = dict(config)
    requested_room_count = int(requested_config.get("room_count", V2_DEFAULT_DUNGEON_CONFIG["room_count"]))
    seed = int(requested_config.get("seed", V2_DEFAULT_DUNGEON_CONFIG["seed"]))
    first_summary = dungeon.validate_layout_summary(seed, requested_room_count, requested_config)
    attempts = [
        {
            "room_count": requested_room_count,
            "pass": bool(first_summary.get("pass")),
            "generated_room_count": first_summary.get("room_count"),
        }
    ]
    if first_summary.get("pass"):
        return {
            "schema": "cubeless_pcg_dungeon_v2_bp_controller_layout_resolution_v1",
            "pass": True,
            "adjusted": False,
            "config": requested_config,
            "layout_summary": first_summary,
            "attempts": attempts,
            "adjustments": [],
        }

    room_spec = _v2_room_count_controller_spec()
    min_room_count = int((room_spec or {}).get("min") or 2)
    max_room_count = int((room_spec or {}).get("max") or 32)
    generated_room_count = int(first_summary.get("room_count") or 0)
    adjustments = []
    candidate_room_counts = []
    default_room_count = int(V2_DEFAULT_DUNGEON_CONFIG.get("room_count", requested_room_count))
    if requested_room_count < default_room_count:
        candidate_room_counts.extend(range(default_room_count, max_room_count + 1))
    downward_start = min(requested_room_count - 1, generated_room_count)
    candidate_room_counts.extend(range(downward_start, min_room_count - 1, -1))
    seen_room_counts = set()
    for candidate_room_count in candidate_room_counts:
        candidate_room_count = int(candidate_room_count)
        if candidate_room_count in seen_room_counts or candidate_room_count < min_room_count or candidate_room_count > max_room_count:
            continue
        seen_room_counts.add(candidate_room_count)
        candidate_config = dict(requested_config)
        candidate_config["room_count"] = int(candidate_room_count)
        summary = dungeon.validate_layout_summary(seed, int(candidate_room_count), candidate_config)
        attempts.append(
            {
                "room_count": int(candidate_room_count),
                "pass": bool(summary.get("pass")),
                "generated_room_count": summary.get("room_count"),
            }
        )
        if summary.get("pass"):
            if actor and room_spec:
                try:
                    actor.set_editor_property(room_spec["variable_name"], int(candidate_room_count))
                except Exception as exc:
                    adjustments.append(
                        {
                            "variable": room_spec["variable_name"],
                            "from": requested_room_count,
                            "to": int(candidate_room_count),
                            "error": str(exc),
                        }
                    )
                else:
                    adjustments.append(
                        {
                            "variable": room_spec["variable_name"],
                            "from": requested_room_count,
                            "to": int(candidate_room_count),
                            "reason": "requested room count did not produce a passing layout for this seed",
                        }
                    )
            return {
                "schema": "cubeless_pcg_dungeon_v2_bp_controller_layout_resolution_v1",
                "pass": True,
                "adjusted": int(candidate_room_count) != requested_room_count,
                "config": candidate_config,
                "layout_summary": summary,
                "attempts": attempts,
                "adjustments": adjustments,
            }

    return {
        "schema": "cubeless_pcg_dungeon_v2_bp_controller_layout_resolution_v1",
        "pass": False,
        "adjusted": False,
        "config": requested_config,
        "layout_summary": first_summary,
        "attempts": attempts,
        "adjustments": adjustments,
    }


def ensure_bp_controller(save_dirty_packages=True):
    with v2_context() as dungeon:
        return _ensure_bp_controller_in_context(dungeon, save_dirty_packages=save_dirty_packages)


def _ensure_bp_controller_in_context(dungeon, save_dirty_packages=True):
    bridge_graph_report = dungeon.create_or_update_pcg_bridge_graph()
    blueprint, created_blueprint = _v2_load_or_create_controller_blueprint()
    variable_report = _v2_ensure_controller_variables(blueprint) if blueprint else {"added_variables": [], "existing_or_failed": []}
    pcg_component_template_report = (
        _v2_ensure_controller_pcg_component(blueprint)
        if blueprint
        else {"pass": False, "skipped": True, "reason": "missing blueprint"}
    )
    controller_class = blueprint.generated_class() if blueprint else None
    actor = _v2_find_controller_actor()
    created_actor = False
    replaced_actor = False
    if actor and controller_class and actor.get_class().get_path_name() != controller_class.get_path_name():
        try:
            actor.destroy_actor()
            replaced_actor = True
        except Exception:
            pass
        actor = None
    if not actor and controller_class:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            controller_class,
            unreal.Vector(-1200.0, -1200.0, 160.0),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        if actor:
            actor.set_actor_label(V2_CONTROLLER_LABEL)
            created_actor = True
    default_value_report = _v2_set_controller_actor_values(actor, V2_DEFAULT_DUNGEON_CONFIG) if actor and created_actor else {
        "values": {},
        "errors": [],
        "skipped": not created_actor,
    }
    actor_component_report = (
        _v2_ensure_controller_actor_pcg_component(actor)
        if actor
        else {"pass": False, "skipped": True, "reason": "missing controller actor"}
    )
    if (
        actor
        and controller_class
        and pcg_component_template_report.get("pass")
        and not actor_component_report.get("pass")
        and int(actor_component_report.get("component_count") or 0) == 0
    ):
        preserved_config = _v2_controller_actor_to_config(actor, clamp_to_ranges=False)
        try:
            location = actor.get_actor_location()
            rotation = actor.get_actor_rotation()
        except Exception:
            location = unreal.Vector(-1200.0, -1200.0, 160.0)
            rotation = unreal.Rotator(0.0, 0.0, 0.0)
        try:
            actor.destroy_actor()
            replaced_actor = True
        except Exception:
            pass
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(controller_class, location, rotation)
        if actor:
            actor.set_actor_label(V2_CONTROLLER_LABEL)
            restore_config = preserved_config.get("config") if preserved_config.get("pass") else V2_DEFAULT_DUNGEON_CONFIG
            default_value_report = _v2_set_controller_actor_values(actor, restore_config)
            actor_component_report = _v2_ensure_controller_actor_pcg_component(actor)
    if actor:
        try:
            actor.tags = [
                unreal.Name("DungeonV2BPController"),
                unreal.Name("DungeonAuthoringSource=BlueprintController"),
            ]
        except Exception:
            pass
    current_config = (
        _v2_controller_actor_to_config(actor, clamp_to_ranges=True)
        if actor
        else {"pass": False, "config": {}, "read_errors": []}
    )
    save_summary = dungeon._save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    checks = {
        "blueprint_exists": bool(blueprint),
        "controller_class_exists": bool(controller_class),
        "actor_exists": bool(actor),
        "bridge_graph_pass": bool(bridge_graph_report.get("pass")),
        "pcg_component_template_pass": bool(pcg_component_template_report.get("pass")),
        "pcg_component_actor_pass": bool(actor_component_report.get("pass")),
        "default_value_error_count_zero": not default_value_report.get("errors"),
        "current_config_pass": bool(current_config.get("pass")),
        "save_dirty_packages_pass": (
            True if not save_dirty_packages else bool(save_summary.get("save_dirty_packages_result"))
            and int(save_summary.get("dirty_after_count", -1)) == 0
        ),
    }
    report = {
        "schema": "cubeless_pcg_dungeon_v2_bp_controller_ensure_v1",
        "blueprint_path": V2_CONTROLLER_BLUEPRINT_PATH,
        "controller_label": V2_CONTROLLER_LABEL,
        "created_blueprint": created_blueprint,
        "created_actor": created_actor,
        "replaced_actor": replaced_actor,
        "variable_count": len(_v2_controller_specs()),
        "variables": _v2_controller_specs(),
        "variable_report": variable_report,
        "bridge_graph": bridge_graph_report,
        "pcg_component_template": pcg_component_template_report,
        "pcg_component_actor": actor_component_report,
        "default_value_report": default_value_report,
        "current_config": current_config,
        "save_dirty_packages": save_summary,
        "checks": checks,
        "pass": all(bool(value) for value in checks.values()),
    }
    path = _saved_report_path(V2_REPORT_PREFIX + "_BPControllerEnsure_Report.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = path
    unreal.log(
        "CubelessDungeonPCGV2 BP controller ensure: "
        + json.dumps(
            {
                "pass": report["pass"],
                "created_blueprint": created_blueprint,
                "created_actor": created_actor,
                "variable_count": report["variable_count"],
            },
            ensure_ascii=False,
        )
    )
    return report


def _sync_bp_controller_to_bridge_in_context(dungeon, save_dirty_packages=True):
    ensure_report = _ensure_bp_controller_in_context(dungeon, save_dirty_packages=save_dirty_packages)
    binding_audit = _audit_pcg_parameter_binding_in_context(dungeon, save_report=True)
    actor = _v2_find_controller_actor()
    controller_config = (
        _v2_controller_actor_to_config(actor, clamp_to_ranges=True)
        if actor
        else {"pass": False, "config": {}}
    )
    bridge_actor = dungeon._find_pcg_bridge_actor()
    layout_resolution = {}
    if bridge_actor and controller_config.get("pass"):
        layout_resolution = _v2_resolve_controller_layout_config(dungeon, actor, controller_config["config"])
        if layout_resolution.get("adjusted"):
            controller_config = _v2_controller_actor_to_config(actor, clamp_to_ranges=True)
        config_to_apply = layout_resolution.get("config", controller_config["config"])
        tag_update = dungeon._set_bridge_config_tags(bridge_actor, config_to_apply) if layout_resolution.get("pass") else {}
        parsed_config = dungeon._normalize_authoring_config(dungeon._parse_dungeon_config_from_actor(bridge_actor))
        layout_summary = layout_resolution.get("layout_summary", {})
    else:
        tag_update = {}
        parsed_config = {}
        layout_summary = {}
    save_summary = dungeon._save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    checks = {
        "controller_ensure_pass": bool(ensure_report.get("pass")),
        "pcg_parameter_binding_pass": bool(binding_audit.get("pass")),
        "controller_config_pass": bool(controller_config.get("pass")),
        "bridge_actor_found": bool(bridge_actor),
        "bridge_tags_updated": bool(tag_update),
        "parsed_config_matches_controller": bool(tag_update)
        and all(
            parsed_config.get(spec["config_key"]) == tag_update["config"].get(spec["config_key"])
            for spec in dungeon.CONFIG_AUTHORING_SPECS
        ),
        "layout_pass": bool(layout_summary.get("pass")),
        "save_dirty_packages_pass": (
            True if not save_dirty_packages else bool(save_summary.get("save_dirty_packages_result"))
            and int(save_summary.get("dirty_after_count", -1)) == 0
        ),
    }
    report = {
        "schema": "cubeless_pcg_dungeon_v2_bp_controller_sync_v1",
        "controller_label": V2_CONTROLLER_LABEL,
        "bridge_label": V2_BRIDGE_LABEL,
        "controller_ensure": ensure_report,
        "pcg_parameter_binding": binding_audit,
        "controller_config": controller_config,
        "tag_update": tag_update,
        "parsed_bridge_config": parsed_config,
        "layout_summary": layout_summary,
        "layout_resolution": layout_resolution,
        "save_dirty_packages": save_summary,
        "checks": checks,
        "pass": all(bool(value) for value in checks.values()),
    }
    path = _saved_report_path(V2_REPORT_PREFIX + "_BPControllerSync_Report.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = path
    unreal.log(
        "CubelessDungeonPCGV2 BP controller sync: "
        + json.dumps(
            {
                "pass": report["pass"],
                "room_count": controller_config.get("config", {}).get("room_count"),
                "grid_cell_size": controller_config.get("config", {}).get("grid_cell_size"),
            },
            ensure_ascii=False,
        )
    )
    return report


def sync_bp_controller_to_bridge(save_dirty_packages=True):
    with v2_context() as dungeon:
        return _sync_bp_controller_to_bridge_in_context(dungeon, save_dirty_packages=save_dirty_packages)


def _v2_override_lookup():
    lookup = {}
    for spec in v1.CONFIG_AUTHORING_SPECS:
        names = {
            spec["config_key"],
            spec["tag"],
            v1.CONFIG_TAG_PREFIX + str(spec["tag"]),
        }
        for alias in spec.get("aliases", []):
            names.add(alias)
            names.add(v1.CONFIG_TAG_PREFIX + str(alias))
        for name in names:
            lookup[str(name).strip().casefold()] = spec
    return lookup


def _v2_coerce_override_value(spec, raw_value):
    text = str(raw_value).strip()
    if spec.get("type") == "bool_int":
        lowered = text.casefold()
        if lowered in {"true", "yes", "on"}:
            value = 1
        elif lowered in {"false", "no", "off"}:
            value = 0
        else:
            value = int(text)
    else:
        value = int(text)
    min_value = spec.get("min")
    max_value = spec.get("max")
    if min_value is not None and value < int(min_value):
        raise ValueError("below minimum {}".format(min_value))
    if max_value is not None and value > int(max_value):
        raise ValueError("above maximum {}".format(max_value))
    return value


def normalize_authoring_config_overrides(config_overrides=None):
    raw = dict(config_overrides or {})
    lookup = _v2_override_lookup()
    normalized = {}
    entries = []
    invalid_entries = []
    unknown_keys = []
    duplicate_config_keys = []
    seen_config_keys = set()
    for raw_key, raw_value in raw.items():
        key_text = str(raw_key).strip()
        spec = lookup.get(key_text.casefold())
        if spec is None:
            unknown_keys.append(key_text)
            invalid_entries.append({"key": key_text, "value": raw_value, "error": "unknown override key"})
            continue
        config_key = spec["config_key"]
        if config_key in seen_config_keys:
            duplicate_config_keys.append(config_key)
            invalid_entries.append({"key": key_text, "value": raw_value, "config_key": config_key, "error": "duplicate config key"})
            continue
        seen_config_keys.add(config_key)
        try:
            coerced = _v2_coerce_override_value(spec, raw_value)
        except Exception as exc:
            invalid_entries.append({"key": key_text, "value": raw_value, "config_key": config_key, "error": str(exc)})
            continue
        normalized[config_key] = coerced
        entries.append(
            {
                "key": key_text,
                "config_key": config_key,
                "tag": v1.CONFIG_TAG_PREFIX + str(spec["tag"]),
                "value": coerced,
                "min": spec.get("min"),
                "max": spec.get("max"),
            }
        )
    checks = {
        "unknown_key_count_zero": not unknown_keys,
        "invalid_entry_count_zero": not invalid_entries,
        "duplicate_config_key_count_zero": not duplicate_config_keys,
    }
    pass_value = all(bool(value) for value in checks.values())
    return {
        "schema": "cubeless_pcg_dungeon_v2_authoring_config_overrides_v1",
        "raw": raw,
        "config": normalized,
        "entries": entries,
        "unknown_keys": unknown_keys,
        "duplicate_config_keys": duplicate_config_keys,
        "invalid_entries": invalid_entries,
        "checks": checks,
        "pass": pass_value,
    }


def _apply_authoring_preset_overrides_to_bridge_in_context(
    dungeon,
    preset_name="default",
    config_overrides=None,
    save_dirty_packages=True,
):
    actor = dungeon._find_pcg_bridge_actor()
    preset = dungeon.DUNGEON_AUTHORING_PRESETS.get(str(preset_name))
    override_report = normalize_authoring_config_overrides(config_overrides)
    if not actor or preset is None or not override_report.get("pass"):
        result = {
            "schema": "cubeless_pcg_dungeon_v2_authoring_preset_override_apply_v1",
            "status": "failed",
            "preset_name": str(preset_name),
            "actor_found": bool(actor),
            "preset_found": preset is not None,
            "available_presets": sorted(dungeon.DUNGEON_AUTHORING_PRESETS.keys()),
            "config_overrides": override_report,
            "checks": {
                "actor_found": bool(actor),
                "preset_found": preset is not None,
                "config_overrides_pass": bool(override_report.get("pass")),
            },
            "pass": False,
        }
        unreal.log("CubelessDungeonPCGV2 apply preset overrides: " + json.dumps(result, ensure_ascii=False))
        return result

    merged_config = dict(preset)
    merged_config.update(override_report["config"])
    tag_update = dungeon._set_bridge_config_tags(actor, merged_config)
    parsed_config = dungeon._normalize_authoring_config(dungeon._parse_dungeon_config_from_actor(actor))
    layout_summary = dungeon.validate_layout_summary(
        tag_update["config"]["seed"],
        tag_update["config"]["room_count"],
        tag_update["config"],
    )
    save_summary = dungeon._save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    checks = {
        "actor_found": True,
        "preset_found": True,
        "config_overrides_pass": bool(override_report.get("pass")),
        "parsed_config_matches_merged_config": all(
            parsed_config.get(spec["config_key"]) == tag_update["config"].get(spec["config_key"])
            for spec in dungeon.CONFIG_AUTHORING_SPECS
        ),
        "override_values_applied": all(
            tag_update["config"].get(key) == value for key, value in override_report["config"].items()
        ),
        "preset_layout_pass": bool(layout_summary.get("pass")),
        "save_dirty_packages_pass": (
            True if not save_dirty_packages else bool(save_summary.get("save_dirty_packages_result"))
            and int(save_summary.get("dirty_after_count", -1)) == 0
        ),
    }
    pass_value = all(bool(value) for value in checks.values())
    result = {
        "schema": "cubeless_pcg_dungeon_v2_authoring_preset_override_apply_v1",
        "status": "passed" if pass_value else "failed",
        "preset_name": str(preset_name),
        "actor_found": True,
        "preset_found": True,
        "actor_label": actor.get_actor_label(),
        "base_config": dict(preset),
        "config_overrides": override_report,
        "config": tag_update["config"],
        "tags": dungeon._config_tags_from_config(tag_update["config"]),
        "preserved_tag_count": len(tag_update["preserved_tags"]),
        "removed_config_tag_count": len(tag_update["removed_config_tags"]),
        "parsed_config": parsed_config,
        "layout_summary": layout_summary,
        "save_dirty_packages": save_summary,
        "checks": checks,
        "pass": pass_value,
    }
    unreal.log(
        "CubelessDungeonPCGV2 apply preset overrides: "
        + json.dumps(
            {
                "pass": pass_value,
                "preset_name": str(preset_name),
                "override_count": len(override_report.get("entries", [])),
                "seed": tag_update["config"].get("seed"),
                "room_count": tag_update["config"].get("room_count"),
                "added_loop_edges": layout_summary.get("added_loop_edges"),
            },
            ensure_ascii=False,
        )
    )
    return result


def _v2_report_overrides():
    overrides = {}
    for name, value in vars(v1).items():
        if not name.endswith("_PATH") or not isinstance(value, str):
            continue
        base_name = os.path.basename(value)
        if "CubelessDungeonMVP" not in base_name:
            continue
        overrides[name] = _saved_report_path(base_name.replace("CubelessDungeonMVP", V2_REPORT_PREFIX))
    overrides["ENTRYPOINT_PATH"] = V2_ENTRYPOINT_PATH
    return overrides


def _v2_overrides():
    overrides = {
        "ROOT": V2_ROOT,
        "MATERIAL_DIR": V2_MATERIAL_DIR,
        "MESH_DIR": V2_MESH_DIR,
        "GRAPH_DIR": V2_GRAPH_DIR,
        "MAP_DIR": V2_MAP_DIR,
        "BLUEPRINT_DIR": V2_BLUEPRINT_DIR,
        "LEVEL_PATH": V2_LEVEL_PATH,
        "GRAPH_NAME": V2_GRAPH_NAME,
        "GRAPH_PATH": V2_GRAPH_DIR + "/" + V2_GRAPH_NAME,
        "NATIVE_GRAPH_NAME": V2_NATIVE_GRAPH_NAME,
        "NATIVE_GRAPH_PATH": V2_GRAPH_DIR + "/" + V2_NATIVE_GRAPH_NAME,
        "NATIVE_POINT_SOURCE_GRAPH_NAME": V2_NATIVE_POINT_SOURCE_GRAPH_NAME,
        "NATIVE_POINT_SOURCE_GRAPH_PATH": V2_GRAPH_DIR + "/" + V2_NATIVE_POINT_SOURCE_GRAPH_NAME,
        "NATIVE_INTEGRATION_GRAPH_NAME": V2_NATIVE_INTEGRATION_GRAPH_NAME,
        "NATIVE_INTEGRATION_GRAPH_PATH": V2_GRAPH_DIR + "/" + V2_NATIVE_INTEGRATION_GRAPH_NAME,
        "NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME": V2_NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME,
        "NATIVE_POINT_SOURCE_PREVIEW_GRAPH_PATH": V2_GRAPH_DIR + "/" + V2_NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME,
        "NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME": V2_NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME,
        "NATIVE_INTEGRATION_PREVIEW_GRAPH_PATH": V2_GRAPH_DIR + "/" + V2_NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME,
        "ACTOR_PREFIX": V2_ACTOR_PREFIX,
        "GAMEPLAY_PLACEHOLDER_PREFIX": V2_GAMEPLAY_PLACEHOLDER_PREFIX,
        "PCG_BRIDGE_LABEL": V2_BRIDGE_LABEL,
        "PCG_NATIVE_INTEGRATION_TEST_LABEL": V2_NATIVE_INTEGRATION_TEST_LABEL,
        "PCG_NATIVE_INTEGRATION_OUTPUT_LABEL": V2_NATIVE_INTEGRATION_OUTPUT_LABEL,
        "PCG_NATIVE_INTEGRATION_PREVIEW_LABEL": V2_NATIVE_INTEGRATION_PREVIEW_LABEL,
        "WALL_HEIGHT": V2_WALL_HEIGHT,
        "MESH_BUILDERS": _v2_mesh_builders(),
        "DEFAULT_DUNGEON_CONFIG": copy.deepcopy(V2_DEFAULT_DUNGEON_CONFIG),
        "DUNGEON_AUTHORING_PRESETS": copy.deepcopy(V2_AUTHORING_PRESETS),
        "DUNGEON_AUTHORING_PRESET_NOTES": copy.deepcopy(V2_AUTHORING_PRESET_NOTES),
        "GENERATION_METRICS": {
            "grid_cell_size": float(V2_DEFAULT_DUNGEON_CONFIG["grid_cell_size"]),
            "corridor_width": float(V2_DEFAULT_DUNGEON_CONFIG["corridor_width"]),
        },
    }
    overrides.update(_v2_report_overrides())
    overrides["MINIMAP_PATH"] = _saved_report_path(V2_REPORT_PREFIX + "_Minimap.txt")
    return overrides


def _v2_actor_module(actor):
    try:
        values = v1._tag_values(getattr(actor, "tags", []))
    except Exception:
        values = {}
    return str(values.get("DungeonModule", ""))


def _v2_core_output_contract_builder(original_builder):
    def build_pcg_spawner_contract_v2(actors):
        kept_actors = []
        excluded_records = []
        excluded_module_counts = {}
        for actor in actors:
            module = _v2_actor_module(actor)
            if module in V2_CORE_OUTPUT_EXCLUDED_MODULES:
                excluded_module_counts[module] = excluded_module_counts.get(module, 0) + 1
                try:
                    label = actor.get_actor_label()
                except Exception:
                    label = str(actor)
                excluded_records.append({"label": label, "module": module})
                continue
            kept_actors.append(actor)
        contract = original_builder(kept_actors)
        contract["v2_output_policy"] = dict(V2_OUTPUT_POLICY)
        contract["v2_excluded_static_mesh_actor_count"] = len(excluded_records)
        contract["v2_excluded_module_counts"] = dict(sorted(excluded_module_counts.items()))
        contract["v2_excluded_sample_labels"] = excluded_records[:16]
        return contract

    return build_pcg_spawner_contract_v2


def _v2_core_expected_spawn_point_counter(original_counter):
    def expected_static_mesh_spawn_point_count_v2(counts):
        base_count = int(original_counter(counts))
        excluded_count = sum(int(counts.get(module, 0)) for module in V2_CORE_OUTPUT_EXCLUDED_MODULES)
        return max(0, base_count - excluded_count)

    return expected_static_mesh_spawn_point_count_v2


def _v2_int(value, default=-1):
    try:
        return int(value)
    except Exception:
        return int(default)


def _v2_core_output_review_mode(original_review_mode):
    def set_native_output_only_review_mode_v2(enabled=True):
        report = original_review_mode(enabled)
        if bool(report.get("pass")):
            report["v2_output_policy"] = dict(V2_OUTPUT_POLICY)
            return report

        contract_source = v1._read_json_report(v1.PCG_SPAWNER_CONTRACT_PATH)
        contract = contract_source.get("data", {}) if contract_source.get("load_ok") else {}
        excluded_count = int(contract.get("v2_excluded_static_mesh_actor_count", 0) or 0)
        expected_native_count = int(report.get("expected_bridge_static_mesh_actor_count", 0) or 0)
        expected_bridge_count = expected_native_count + excluded_count
        after = report.get("bridge_static_mesh_after", {})
        preview_after = report.get("preview_after", {})
        light_after = report.get("bridge_review_lights_after", {})
        errors = (
            report.get("visibility_operations", {}).get("errors", [])
            + report.get("preview_visibility_operations", {}).get("errors", [])
            + report.get("bridge_review_light_visibility_operations", {}).get("errors", [])
        )
        bridge_count_ok = _v2_int(after.get("actor_count")) == expected_bridge_count
        hidden_ok = bool(enabled) and _v2_int(after.get("visible_static_mesh_component_count")) == 0
        restored_ok = (not bool(enabled)) and _v2_int(after.get("visible_static_mesh_component_count")) == _v2_int(
            after.get("static_mesh_component_count"), -2
        )
        preview_hidden_ok = bool(enabled) and _v2_int(preview_after.get("visible_static_mesh_component_count")) == 0
        preview_restored_ok = (not bool(enabled)) and (
            _v2_int(preview_after.get("static_mesh_component_count"), 0) == 0
            or _v2_int(preview_after.get("visible_static_mesh_component_count"))
            == _v2_int(preview_after.get("static_mesh_component_count"), -2)
        )
        light_hidden_ok = bool(enabled) and _v2_int(light_after.get("visible_light_component_count")) == 0
        light_restored_ok = (not bool(enabled)) and (
            _v2_int(light_after.get("light_component_count"), 0) == 0
            or _v2_int(light_after.get("visible_light_component_count"))
            == _v2_int(light_after.get("light_component_count"), -2)
        )
        adjustment = {
            "mode": "v2_core_output_review_count_adjustment",
            "expected_native_output_count": expected_native_count,
            "excluded_static_mesh_actor_count": excluded_count,
            "expected_bridge_validation_actor_count": expected_bridge_count,
            "actual_bridge_validation_actor_count": _v2_int(after.get("actor_count")),
            "bridge_count_ok": bridge_count_ok,
            "reason": (
                "V2 core output filters semantic/detail StaticMeshActors from NativeOutput, while the "
                "bridge validation actors remain present so room-rule data can still be audited."
            ),
        }
        report["v2_output_policy"] = dict(V2_OUTPUT_POLICY)
        report["v2_review_mode_adjustment"] = adjustment
        report["pass"] = bool(
            report.get("native_output_generation", {}).get("pass")
            and not errors
            and bridge_count_ok
            and (hidden_ok or restored_ok)
            and (preview_hidden_ok or preview_restored_ok)
            and (light_hidden_ok or light_restored_ok)
        )
        v1._write_native_output_only_review_report(report)
        return report

    return set_native_output_only_review_mode_v2


def _v2_selector_import(settings, prop, text):
    selector = settings.get_editor_property(prop)
    selector.import_text("PCGBegin({})PCGEnd".format(text))
    settings.set_editor_property(prop, selector)


def _v2_configure_get_actor_property_node(node, spec):
    settings = node.get_settings()
    variable_name = spec["variable_name"]
    report = {"variable_name": variable_name, "errors": []}
    try:
        node.set_editor_property("node_title", V2_PARAMETER_NODE_TITLE_PREFIX + variable_name)
    except Exception:
        try:
            node.node_title = V2_PARAMETER_NODE_TITLE_PREFIX + variable_name
        except Exception as exc:
            report["errors"].append("node_title: " + str(exc))
    try:
        settings.set_editor_property("property_name", variable_name)
        report["property_name"] = variable_name
    except Exception as exc:
        report["errors"].append("property_name: " + str(exc))
    try:
        settings.set_editor_property("always_requery_actors", True)
        settings.set_editor_property("sanitize_output_attribute_name", True)
    except Exception as exc:
        report["errors"].append("actor_property_flags: " + str(exc))
    try:
        _v2_selector_import(settings, "output_attribute_name", variable_name)
        report["output_attribute_name"] = variable_name
    except Exception as exc:
        report["errors"].append("output_attribute_name: " + str(exc))
    try:
        settings.description = (
            "Reads BP_Cubeless_DungeonV2_Controller actor property {}. "
            "This PCG actor-property parameter name must match the Blueprint variable name."
        ).format(variable_name)
    except Exception:
        pass
    report["pass"] = not report["errors"]
    return report


def _v2_bridge_graph_actor_property_builder(original_builder):
    def create_or_update_pcg_bridge_graph_v2():
        report = original_builder()
        graph = unreal.load_object(None, V2_GRAPH_DIR + "/" + V2_GRAPH_NAME + "." + V2_GRAPH_NAME)
        if not graph:
            report["v2_actor_property_parameters"] = {
                "pass": False,
                "graph_loaded": False,
                "error": "failed to load V2 bridge graph after base builder",
            }
            return report

        removed = []
        for node in list(graph.nodes):
            title = v1._pcg_node_title(node)
            if title.startswith(V2_PARAMETER_NODE_TITLE_PREFIX):
                graph.remove_node(node)
                removed.append(title)

        python_nodes = [
            node
            for node in list(graph.nodes)
            if v1._pcg_settings_class(node) == "PCGExecutePythonScriptSettings"
        ]
        python_node = python_nodes[0] if python_nodes else None
        node_reports = []
        edge_reports = []
        y = -780
        for index, spec in enumerate(_v2_controller_specs()):
            created = graph.add_node_of_type(unreal.PCGGetActorPropertySettings.static_class())
            node = created[0] if isinstance(created, tuple) else created
            try:
                node.set_node_position(unreal.Vector2D(-620.0, float(y + index * 150)))
            except Exception:
                pass
            node_report = _v2_configure_get_actor_property_node(node, spec)
            node_reports.append(node_report)
            try:
                edge_reports.append(v1._try_add_edge(graph, graph.get_input_node(), node, "In", "In"))
                if python_node:
                    edge_reports.append(v1._try_add_edge(graph, node, python_node, "Out", "In"))
            except Exception as exc:
                edge_reports.append(
                    {
                        "ok": False,
                        "variable_name": spec["variable_name"],
                        "error": str(exc),
                    }
                )

        try:
            graph.description = (
                "V2 bridge graph. The PCG Get Actor Property nodes read "
                "BP_Cubeless_DungeonV2_Controller variables whose names match the Dungeon... authoring schema, "
                "then the Python bridge uses the same BP actor properties as the authoritative editor source."
            )
        except Exception:
            pass
        try:
            graph.notify_graph_changed()
        except Exception:
            pass
        unreal.EditorAssetLibrary.save_loaded_asset(graph, only_if_is_dirty=False)
        property_report = {
            "schema": "cubeless_pcg_dungeon_v2_bridge_actor_property_nodes_v1",
            "graph_path": graph.get_path_name(),
            "removed_previous_nodes": removed,
            "expected_parameter_count": len(_v2_controller_specs()),
            "created_parameter_count": len(node_reports),
            "node_reports": node_reports,
            "edge_reports": edge_reports,
            "edge_failure_count": len([edge for edge in edge_reports if not edge.get("ok")]),
            "python_node_found": bool(python_node),
            "pass": bool(
                len(node_reports) == len(_v2_controller_specs())
                and all(item.get("pass") for item in node_reports)
                and python_node
            ),
        }
        report["v2_actor_property_parameters"] = property_report
        report["node_count"] = len(graph.nodes)
        report["pass"] = bool(report.get("pass", True) and property_report.get("pass"))
        return report

    return create_or_update_pcg_bridge_graph_v2


def _v2_expected_parameter_names():
    return [spec["variable_name"] for spec in _v2_controller_specs()]


def _v2_safe_prop(obj, prop, default=None):
    if obj is None:
        return default
    try:
        return obj.get_editor_property(prop)
    except Exception:
        return default


def _v2_selector_value_text(value):
    if value is None:
        return ""
    try:
        return str(value.export_text())
    except Exception:
        pass
    return str(value)


def _v2_output_selector_matches(selector_text, expected_name):
    text = str(selector_text or "")
    return (
        text == expected_name
        or "PCGBegin({})PCGEnd".format(expected_name) in text
        or 'AttributeName="{}"'.format(expected_name) in text
        or "AttributeName='{}'".format(expected_name) in text
        or "AttributeName={}".format(expected_name) in text
    )


def _v2_blueprint_variable_audit(blueprint):
    expected = _v2_expected_parameter_names()
    rows = []
    errors = []
    cls = None
    cdo = None
    if blueprint:
        try:
            unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
        except Exception as exc:
            errors.append("compile_blueprint: " + str(exc))
        try:
            cls = blueprint.generated_class()
            cdo = unreal.get_default_object(cls)
        except Exception as exc:
            errors.append("generated_class_or_cdo: " + str(exc))
    for name in expected:
        exists = False
        value = None
        error = None
        if cdo:
            try:
                value = cdo.get_editor_property(name)
                exists = True
            except Exception as exc:
                error = str(exc)
        rows.append({"variable_name": name, "exists": exists, "default_value": value, "error": error})
    existing = [row["variable_name"] for row in rows if row.get("exists")]
    return {
        "blueprint_path": V2_CONTROLLER_BLUEPRINT_PATH,
        "blueprint_exists": bool(blueprint),
        "generated_class": cls.get_path_name() if cls else None,
        "expected_variable_names": expected,
        "existing_variable_names": existing,
        "missing_variable_names": [name for name in expected if name not in existing],
        "rows": rows,
        "errors": errors,
        "pass": bool(blueprint and len(existing) == len(expected) and not errors),
    }


def _v2_graph_actor_property_node_audit(graph):
    expected = _v2_expected_parameter_names()
    rows = []
    for node in list(getattr(graph, "nodes", []) or []):
        if v1._pcg_settings_class(node) != "PCGGetActorPropertySettings":
            continue
        title = v1._pcg_node_title(node)
        if not title.startswith(V2_PARAMETER_NODE_TITLE_PREFIX):
            continue
        settings = node.get_settings()
        property_name = str(_v2_safe_prop(settings, "property_name", "") or "")
        output_selector = _v2_safe_prop(settings, "output_attribute_name", None)
        output_selector_text = _v2_selector_value_text(output_selector)
        output_selector_readable = (
            "PCGBegin(" in output_selector_text
            or "AttributeName" in output_selector_text
            or property_name in output_selector_text
            or output_selector_text == property_name
        )
        expected_from_title = title[len(V2_PARAMETER_NODE_TITLE_PREFIX):]
        rows.append(
            {
                "node": node.get_name(),
                "title": title,
                "expected_from_title": expected_from_title,
                "property_name": property_name,
                "output_attribute_name_text": output_selector_text,
                "output_attribute_name_readable": output_selector_readable,
                "title_matches_property": expected_from_title == property_name,
                "output_attribute_name_matches_property": (
                    not output_selector_readable or _v2_output_selector_matches(output_selector_text, property_name)
                ),
            }
        )
    property_names = sorted({row["property_name"] for row in rows if row.get("property_name")})
    title_names = sorted({row["expected_from_title"] for row in rows if row.get("expected_from_title")})
    output_mismatch = [
        row
        for row in rows
        if row.get("property_name") in expected and not row.get("output_attribute_name_matches_property")
    ]
    return {
        "graph_path": graph.get_path_name() if graph else V2_GRAPH_DIR + "/" + V2_GRAPH_NAME,
        "graph_exists": bool(graph),
        "expected_parameter_names": expected,
        "property_node_count": len(rows),
        "property_names": property_names,
        "title_names": title_names,
        "missing_property_names": [name for name in expected if name not in property_names],
        "extra_property_names": [name for name in property_names if name not in expected],
        "title_property_mismatch": [row for row in rows if not row.get("title_matches_property")],
        "output_attribute_mismatch": output_mismatch,
        "rows": rows,
        "pass": bool(
            graph
            and property_names == sorted(expected)
            and title_names == sorted(expected)
            and not output_mismatch
            and all(row.get("title_matches_property") for row in rows)
        ),
    }


def _audit_pcg_parameter_binding_in_context(dungeon, save_report=True):
    bridge_graph_report = dungeon.create_or_update_pcg_bridge_graph()
    blueprint, _created = _v2_load_or_create_controller_blueprint()
    variable_report = _v2_ensure_controller_variables(blueprint) if blueprint else {"pass": False}
    component_template_report = (
        _v2_ensure_controller_pcg_component(blueprint)
        if blueprint
        else {"pass": False, "skipped": True, "reason": "missing blueprint"}
    )
    actor = _v2_find_controller_actor()
    component_actor_report = (
        _v2_ensure_controller_actor_pcg_component(actor)
        if actor
        else {"pass": False, "skipped": True, "reason": "missing controller actor"}
    )
    graph = unreal.EditorAssetLibrary.load_asset(V2_GRAPH_DIR + "/" + V2_GRAPH_NAME)
    blueprint_audit = _v2_blueprint_variable_audit(blueprint)
    graph_audit = _v2_graph_actor_property_node_audit(graph)
    actor_config = (
        _v2_controller_actor_to_config(actor, clamp_to_ranges=True)
        if actor
        else {"pass": False, "config": {}, "read_errors": ["missing controller actor"]}
    )
    expected = sorted(_v2_expected_parameter_names())
    actor_names = sorted(actor_config.get("raw_values", {}).keys())
    checks = {
        "bridge_graph_pass": bool(bridge_graph_report.get("pass")),
        "blueprint_variables_pass": bool(blueprint_audit.get("pass")),
        "graph_actor_property_nodes_pass": bool(graph_audit.get("pass")),
        "pcg_component_template_pass": bool(component_template_report.get("pass")),
        "pcg_component_actor_pass": bool(component_actor_report.get("pass")),
        "actor_values_read_pass": bool(actor_config.get("pass")),
        "actor_parameter_names_match_expected": actor_names == expected,
    }
    report = {
        "schema": "cubeless_pcg_dungeon_v2_pcg_parameter_binding_audit_v1",
        "policy": (
            "V2 PCG parameters are bound by exact-name actor-property nodes. "
            "Each BP_Cubeless_DungeonV2_Controller variable must have a matching PCG Get Actor Property "
            "property_name and output attribute name."
        ),
        "expected_parameter_names": expected,
        "bridge_graph": bridge_graph_report,
        "variable_ensure": variable_report,
        "blueprint_variables": blueprint_audit,
        "graph_actor_property_nodes": graph_audit,
        "pcg_component_template": component_template_report,
        "pcg_component_actor": component_actor_report,
        "actor_config": actor_config,
        "checks": checks,
        "pass": all(bool(value) for value in checks.values()),
    }
    if save_report:
        path = _saved_report_path(V2_REPORT_PREFIX + "_PCGParameterBindingAudit.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        report["report_path"] = path
    unreal.log(
        "CubelessDungeonPCGV2 PCG parameter binding audit: "
        + json.dumps(
            {
                "pass": report["pass"],
                "failed_checks": [key for key, value in checks.items() if not value],
                "parameter_count": len(expected),
            },
            ensure_ascii=False,
        )
    )
    return report


@contextlib.contextmanager
def v2_context(core_output_only=True):
    overrides = _v2_overrides()
    overrides["create_or_update_pcg_bridge_graph"] = _v2_bridge_graph_actor_property_builder(
        v1.create_or_update_pcg_bridge_graph
    )
    if core_output_only:
        overrides["build_pcg_spawner_contract"] = _v2_core_output_contract_builder(v1.build_pcg_spawner_contract)
        overrides["_expected_static_mesh_spawn_point_count"] = _v2_core_expected_spawn_point_counter(
            v1._expected_static_mesh_spawn_point_count
        )
        overrides["set_native_output_only_review_mode"] = _v2_core_output_review_mode(
            v1.set_native_output_only_review_mode
        )
    previous = {}
    for name, value in overrides.items():
        previous[name] = getattr(v1, name, None)
        setattr(v1, name, value)
    try:
        yield v1
    finally:
        for name, value in previous.items():
            setattr(v1, name, value)


def _write_v2_wrapper_report(name, payload):
    report = {
        "schema": "cubeless_pcg_dungeon_v2_wrapper_v1",
        "name": str(name),
        "root": V2_ROOT,
        "level_path": V2_LEVEL_PATH,
        "default_config": dict(V2_DEFAULT_DUNGEON_CONFIG),
        "output_policy": dict(V2_OUTPUT_POLICY),
        "payload": payload,
        "pass": bool(payload.get("pass")) if isinstance(payload, dict) else False,
    }
    path = _saved_report_path(V2_REPORT_PREFIX + "_" + str(name) + "_Wrapper.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = path
    return report


def audit_pcg_parameter_binding(save_report=True):
    with v2_context() as dungeon:
        return _audit_pcg_parameter_binding_in_context(dungeon, save_report=save_report)


def _v2_static_mesh_bounds_record(static_mesh):
    if not static_mesh:
        return {}
    try:
        bounds = static_mesh.get_bounds()
        origin = bounds.origin
        extent = bounds.box_extent
        return {
            "origin": [float(origin.x), float(origin.y), float(origin.z)],
            "extent": [float(extent.x), float(extent.y), float(extent.z)],
            "min": [float(origin.x - extent.x), float(origin.y - extent.y), float(origin.z - extent.z)],
            "max": [float(origin.x + extent.x), float(origin.y + extent.y), float(origin.z + extent.z)],
        }
    except Exception as exc:
        return {"error": str(exc)}


def rebuild_story_height_modules(save_dirty_packages=True):
    with v2_context() as dungeon:
        dungeon.ensure_dirs()
        materials = _v2_load_existing_materials()
        rebuilt = {}
        for module_key in V2_STORY_HEIGHT_MODULE_KEYS:
            static_mesh = dungeon.bake_static_mesh(
                module_key,
                dungeon.MESH_BUILDERS[module_key](),
                materials,
            )
            rebuilt[module_key] = {
                "asset_path": static_mesh.get_path_name() if static_mesh else None,
                "bounds": _v2_static_mesh_bounds_record(static_mesh),
            }
        save_summary = dungeon._save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
        report = {
            "schema": "cubeless_pcg_dungeon_v2_story_height_modules_rebuild_v1",
            "story_height_scale": V2_STORY_HEIGHT_SCALE,
            "wall_height": V2_WALL_HEIGHT,
            "rebuilt_module_keys": list(V2_STORY_HEIGHT_MODULE_KEYS),
            "rebuilt": rebuilt,
            "save_dirty_packages": save_summary,
            "checks": {
                "rebuilt_all_story_height_modules": len(rebuilt) == len(V2_STORY_HEIGHT_MODULE_KEYS),
                "wall_height_is_2x_v1": abs(float(V2_WALL_HEIGHT) - float(V2_BASE_WALL_HEIGHT) * 2.0) < 0.001,
                "save_dirty_packages_pass": (
                    True if not save_dirty_packages else bool(save_summary.get("save_dirty_packages_result"))
                    and int(save_summary.get("dirty_after_count", -1)) == 0
                ),
            },
        }
        report["pass"] = all(bool(value) for value in report["checks"].values())
        path = _saved_report_path(V2_REPORT_PREFIX + "_StoryHeightModulesRebuild.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        report["report_path"] = path
        unreal.log(
            "CubelessDungeonPCGV2 story-height modules rebuild: "
            + json.dumps(
                {
                    "pass": report["pass"],
                    "wall_height": report["wall_height"],
                    "rebuilt_module_keys": report["rebuilt_module_keys"],
                },
                ensure_ascii=False,
            )
        )
        return report


def _read_saved_json(filename):
    path = _saved_report_path(filename)
    if not os.path.exists(path):
        return {"exists": False, "path": path, "data": {}}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return {"exists": True, "path": path, "data": data}
    except Exception as exc:
        return {"exists": True, "path": path, "data": {}, "error": str(exc)}


def _count_by(records, key):
    counts = {}
    for record in records or []:
        value = str(record.get(key, "<missing>"))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _room_rule_room_sample(room_archetypes, room_shapes, room_themes, max_count=16):
    shape_by_room = {int(item.get("room_id", -1)): item for item in room_shapes or []}
    theme_by_room = {int(item.get("room_id", -1)): item for item in room_themes or []}
    rows = []
    for archetype in sorted(room_archetypes or [], key=lambda item: int(item.get("room_id", -1))):
        room_id = int(archetype.get("room_id", -1))
        shape = shape_by_room.get(room_id, {})
        theme = theme_by_room.get(room_id, {})
        rows.append(
            {
                "room_id": room_id,
                "archetype": archetype.get("archetype"),
                "roles": list(archetype.get("roles", [])),
                "route_kind": archetype.get("route_kind"),
                "main_path_index": archetype.get("main_path_index"),
                "theme": theme.get("theme_name"),
                "shape": shape.get("shape_name"),
                "variant_kind": shape.get("variant_kind"),
                "variant_mesh_key": shape.get("variant_mesh_key"),
            }
        )
        if len(rows) >= int(max_count):
            break
    return rows


def _marker_summary(markers):
    rows = []
    for marker in markers or []:
        role = str(marker.get("role", ""))
        rows.append(
            {
                "label": marker.get("label"),
                "role": role,
                "meaning": V2_ROOM_RULE_MEANINGS.get(role, "Semantic review marker."),
                "room_id": marker.get("room_id"),
                "native_output": "excluded_from_default_core_output",
            }
        )
    return rows


def _config_summary(config):
    result = {}
    for key in sorted(V2_CONFIG_MEANINGS.keys()):
        if key in config:
            result[key] = {
                "value": config.get(key),
                "meaning": V2_CONFIG_MEANINGS[key],
            }
    return result


def _write_room_rule_markdown(summary):
    markdown_path = _saved_report_path(V2_REPORT_PREFIX + "_RoomRuleSummary.md")
    lines = [
        "# Cubeless PCG Dungeon V2 Room Rule Summary",
        "",
        "## Output Policy",
        "",
        "- Mode: `{}`".format(summary["output_policy"].get("mode")),
        "- Excluded modules: `{}`".format(", ".join(summary["output_policy"].get("excluded_modules", []))),
        "- Reason: {}".format(summary["output_policy"].get("reason")),
        "",
        "## Current Result",
        "",
        "- Rooms: `{}`".format(summary["counts"].get("room_count")),
        "- Main path rooms: `{}`".format(summary["progression"].get("main_path_room_ids")),
        "- Side rooms: `{}`".format(summary["progression"].get("side_room_ids")),
        "- NativeOutput: `{}` components, `{}` instances".format(
            summary["native_output"].get("component_count"),
            summary["native_output"].get("instance_count"),
        ),
        "- Excluded validation actors: `{}`".format(summary["output_policy"].get("excluded_static_mesh_actor_count")),
        "",
        "## Role Counts",
        "",
    ]
    for role, count in sorted(summary["progression"].get("role_counts", {}).items()):
        lines.append("- `{}`: `{}` - {}".format(role, count, V2_ROOM_RULE_MEANINGS.get(role, "Room role.")))
    lines.extend(["", "## Room Archetypes", ""])
    for archetype, count in sorted(summary["counts"].get("archetype_counts", {}).items()):
        lines.append("- `{}`: `{}`".format(archetype, count))
    lines.extend(["", "## Marker Meaning", ""])
    for marker in summary.get("markers", []):
        lines.append(
            "- `{}` room `{}` role `{}`: {} ({})".format(
                marker.get("label"),
                marker.get("room_id"),
                marker.get("role"),
                marker.get("meaning"),
                marker.get("native_output"),
            )
        )
    lines.extend(["", "## Room Variant Details", ""])
    for kind, count in sorted(summary["counts"].get("room_variant_kind_counts", {}).items()):
        lines.append("- `{}`: `{}`".format(kind, count))
    lines.extend(["", "## Detail Meshes", ""])
    for kind, count in sorted(summary["counts"].get("detail_kind_counts", {}).items()):
        lines.append("- `{}`: `{}`".format(kind, count))
    lines.extend(["", "## Adjustable Config", ""])
    for key, item in summary.get("config", {}).items():
        lines.append("- `{}` = `{}` - {}".format(key, item.get("value"), item.get("meaning")))
    os.makedirs(os.path.dirname(markdown_path), exist_ok=True)
    with open(markdown_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return markdown_path


def write_room_rule_summary():
    gameplay_source = _read_saved_json(V2_REPORT_PREFIX + "_GameplayData.json")
    spawner_source = _read_saved_json(V2_REPORT_PREFIX + "_PCGSpawnerContract.json")
    runner_source = _read_saved_json(V2_REPORT_PREFIX + "_PrototypeRunner_Report.json")
    gameplay = gameplay_source.get("data", {})
    spawner = spawner_source.get("data", {})
    runner = runner_source.get("data", {})
    room_archetypes = gameplay.get("room_archetypes", [])
    room_shapes = gameplay.get("room_shapes", [])
    room_themes = gameplay.get("room_themes", [])
    markers = gameplay.get("markers", [])
    room_variant_details = gameplay.get("room_variant_details", [])
    detail_meshes = gameplay.get("detail_meshes", [])
    config = dict(gameplay.get("config", {}))
    if "seed" not in config and gameplay.get("seed") is not None:
        config["seed"] = gameplay.get("seed")
    progression = gameplay.get("progression", {})
    native_output = runner.get("final_gate", {})
    excluded_counts = spawner.get("v2_excluded_module_counts", {})
    expected_excluded = {
        "marker": len(markers),
        "room_variant_detail": len(room_variant_details),
        "detail_mesh": len(detail_meshes),
    }
    checks = {
        "gameplay_data_loaded": bool(gameplay_source.get("exists")) and not gameplay_source.get("error"),
        "spawner_contract_loaded": bool(spawner_source.get("exists")) and not spawner_source.get("error"),
        "room_count_matches_records": int(config.get("room_count", len(room_archetypes)) or 0) == len(room_archetypes),
        "excluded_marker_count_matches": int(excluded_counts.get("marker", -1) or -1) == len(markers),
        "excluded_room_variant_count_matches": int(excluded_counts.get("room_variant_detail", -1) or -1)
        == len(room_variant_details),
        "excluded_detail_mesh_count_matches": int(excluded_counts.get("detail_mesh", -1) or -1) == len(detail_meshes),
        "core_output_policy_present": spawner.get("v2_output_policy", {}).get("mode") == V2_OUTPUT_POLICY["mode"],
    }
    summary = {
        "schema": "cubeless_pcg_dungeon_v2_room_rule_summary_v1",
        "root": V2_ROOT,
        "level_path": V2_LEVEL_PATH,
        "source_paths": {
            "gameplay_data": gameplay_source.get("path"),
            "spawner_contract": spawner_source.get("path"),
            "runner_report": runner_source.get("path"),
        },
        "output_policy": dict(
            V2_OUTPUT_POLICY,
            excluded_module_counts=dict(sorted(excluded_counts.items())),
            excluded_static_mesh_actor_count=int(spawner.get("v2_excluded_static_mesh_actor_count", 0) or 0),
            expected_excluded_module_counts=expected_excluded,
        ),
        "native_output": {
            "component_count": native_output.get("native_components"),
            "instance_count": native_output.get("native_instances"),
            "final_gate_pass": bool(native_output.get("success")),
        },
        "config": _config_summary(config),
        "progression": {
            "main_path_room_ids": progression.get("main_path_room_ids", []),
            "side_room_ids": progression.get("side_room_ids", []),
            "locked_door_specs": progression.get("locked_door_specs", []),
            "key_room_ids": progression.get("key_room_ids", []),
            "shop_room_ids": progression.get("shop_room_ids", []),
            "treasure_room_ids": progression.get("treasure_room_ids", []),
            "enemy_room_ids": progression.get("enemy_room_ids", []),
            "boss_room_id": progression.get("boss_room_id"),
            "role_counts": progression.get("role_counts", {}),
        },
        "counts": {
            "room_count": len(room_archetypes),
            "archetype_counts": _count_by(room_archetypes, "archetype"),
            "theme_counts": _count_by(room_themes, "theme_name"),
            "shape_family_counts": _count_by(room_shapes, "shape_family"),
            "room_variant_kind_counts": _count_by(room_variant_details, "kind"),
            "room_variant_mesh_counts": _count_by(room_variant_details, "mesh_key"),
            "detail_kind_counts": _count_by(detail_meshes, "kind"),
            "detail_mesh_key_counts": _count_by(detail_meshes, "mesh_key"),
        },
        "room_sample": _room_rule_room_sample(room_archetypes, room_shapes, room_themes),
        "markers": _marker_summary(markers),
        "pass": all(bool(value) for value in checks.values()),
        "checks": checks,
    }
    json_path = _saved_report_path(V2_REPORT_PREFIX + "_RoomRuleSummary.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    summary["report_path"] = json_path
    summary["markdown_path"] = _write_room_rule_markdown(summary)
    unreal.log(
        "CubelessDungeonPCGV2 room rule summary: "
        + json.dumps(
            {
                "pass": summary["pass"],
                "room_count": summary["counts"]["room_count"],
                "excluded": summary["output_policy"]["excluded_module_counts"],
            },
            ensure_ascii=False,
        )
    )
    return summary


def _matrix_config(config):
    return {key: config.get(key) for key in V2_MATRIX_CONFIG_KEYS if key in config}


def _matrix_layout_summary(dungeon, preset_name, config):
    merged = dict(dungeon.DEFAULT_DUNGEON_CONFIG)
    merged.update(config)
    seed = int(merged.get("seed", dungeon.DEFAULT_DUNGEON_CONFIG["seed"]))
    room_count = int(merged.get("room_count", dungeon.DEFAULT_DUNGEON_CONFIG["room_count"]))
    layout = dungeon.validate_layout_summary(seed, room_count, merged)
    notes = dungeon.DUNGEON_AUTHORING_PRESET_NOTES.get(str(preset_name), {})
    return {
        "preset": str(preset_name),
        "label": notes.get("label", str(preset_name)),
        "intent": notes.get("intent", ""),
        "config": _matrix_config(merged),
        "layout": {
            "pass": bool(layout.get("pass")),
            "room_count": layout.get("room_count"),
            "main_path_room_count": layout.get("main_path_room_count"),
            "side_room_count": layout.get("side_room_count"),
            "added_loop_edges": layout.get("added_loop_edges"),
            "start_room_id": layout.get("start_room_id"),
            "exit_room_id": layout.get("exit_room_id"),
            "start_exit_grid_distance": layout.get("start_exit_grid_distance"),
            "cell_count": layout.get("cell_count"),
            "room_cell_count": layout.get("room_cell_count"),
            "corridor_cell_count": layout.get("corridor_cell_count"),
            "boundary_wall_edge_count": layout.get("boundary_wall_edge_count"),
            "room_corridor_edge_count": layout.get("room_corridor_edge_count"),
            "locked_door_count": layout.get("locked_door_count"),
            "key_room_count": layout.get("key_room_count"),
            "shop_room_count": layout.get("shop_room_count"),
            "treasure_room_count": layout.get("treasure_room_count"),
            "enemy_room_count": layout.get("enemy_room_count"),
            "encounter_spawn_slot_count": layout.get("encounter_spawn_slot_count"),
            "reward_anchor_count": layout.get("reward_anchor_count"),
            "room_variant_detail_count": layout.get("room_variant_detail_count"),
            "detail_mesh_count": layout.get("detail_mesh_count"),
            "role_counts": layout.get("role_counts", {}),
            "archetype_counts": layout.get("room_archetype_counts", {}),
            "shape_counts": layout.get("room_shape_counts", {}),
            "theme_counts": layout.get("room_theme_counts", {}),
        },
        "failed_reason": None if layout.get("pass") else "validate_layout_summary failed",
    }


def _write_room_rule_matrix_markdown(matrix):
    markdown_path = _saved_report_path(V2_REPORT_PREFIX + "_RoomRuleMatrix.md")
    lines = [
        "# Cubeless PCG Dungeon V2 Room Rule Matrix",
        "",
        "This report compares V2 authoring presets without issuing a PCG refresh.",
        "",
        "## Output Policy",
        "",
        "- Mode: `{}`".format(matrix["output_policy"].get("mode")),
        "- Default excluded modules: `{}`".format(", ".join(matrix["output_policy"].get("excluded_modules", []))),
        "",
        "## Preset Comparison",
        "",
        "| Preset | Rooms | Main | Side | Loops | Grid | Corridor | Key | Shop | Treasure | Combat | Locked | Ceiling | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in matrix.get("presets", []):
        config = row.get("config", {})
        layout = row.get("layout", {})
        lines.append(
            "| `{preset}` | {rooms} | {main} | {side} | {loops} | {grid} | {corridor} | {key} | {shop} | {treasure} | {combat} | {locked} | {ceiling} | {passed} |".format(
                preset=row.get("preset"),
                rooms=layout.get("room_count"),
                main=layout.get("main_path_room_count"),
                side=layout.get("side_room_count"),
                loops=layout.get("added_loop_edges"),
                grid=config.get("grid_cell_size"),
                corridor=config.get("corridor_width"),
                key=layout.get("key_room_count"),
                shop=layout.get("shop_room_count"),
                treasure=layout.get("treasure_room_count"),
                combat=layout.get("enemy_room_count"),
                locked=layout.get("locked_door_count"),
                ceiling=config.get("use_ceiling"),
                passed="yes" if layout.get("pass") else "no",
            )
        )
    lines.extend(["", "## Preset Intent", ""])
    for row in matrix.get("presets", []):
        lines.append("- `{}`: {}".format(row.get("preset"), row.get("intent") or row.get("label")))
    lines.extend(["", "## Role Counts By Preset", ""])
    for row in matrix.get("presets", []):
        role_counts = row.get("layout", {}).get("role_counts", {})
        role_text = ", ".join("{}={}".format(key, value) for key, value in sorted(role_counts.items()))
        lines.append("- `{}`: {}".format(row.get("preset"), role_text))
    os.makedirs(os.path.dirname(markdown_path), exist_ok=True)
    with open(markdown_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return markdown_path


def write_room_rule_matrix(preset_names=None):
    with v2_context() as dungeon:
        if preset_names is None:
            names = sorted(dungeon.DUNGEON_AUTHORING_PRESETS.keys())
        else:
            names = [str(name) for name in preset_names]
        missing = [name for name in names if name not in dungeon.DUNGEON_AUTHORING_PRESETS]
        presets = [
            _matrix_layout_summary(dungeon, name, dungeon.DUNGEON_AUTHORING_PRESETS[name])
            for name in names
            if name in dungeon.DUNGEON_AUTHORING_PRESETS
        ]
    checks = {
        "preset_names_valid": not missing,
        "preset_count_positive": len(presets) > 0,
        "all_presets_pass": all(bool(row.get("layout", {}).get("pass")) for row in presets),
    }
    matrix = {
        "schema": "cubeless_pcg_dungeon_v2_room_rule_matrix_v1",
        "root": V2_ROOT,
        "level_path": V2_LEVEL_PATH,
        "output_policy": dict(V2_OUTPUT_POLICY),
        "preset_count": len(presets),
        "missing_presets": missing,
        "presets": presets,
        "checks": checks,
        "pass": all(bool(value) for value in checks.values()),
    }
    json_path = _saved_report_path(V2_REPORT_PREFIX + "_RoomRuleMatrix.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(matrix, handle, indent=2, ensure_ascii=False)
    matrix["report_path"] = json_path
    matrix["markdown_path"] = _write_room_rule_matrix_markdown(matrix)
    unreal.log(
        "CubelessDungeonPCGV2 room rule matrix: "
        + json.dumps(
            {
                "pass": matrix["pass"],
                "preset_count": matrix["preset_count"],
                "missing_presets": missing,
            },
            ensure_ascii=False,
        )
    )
    return matrix


def _md_cell(value):
    return str(value).replace("|", "/").replace("\r", " ").replace("\n", " ")


def _tuning_recommended_preset_names():
    names = []
    for goal in V2_TUNING_GUIDE_GOALS:
        for preset_name in goal.get("recommended_presets", []):
            if preset_name not in names:
                names.append(preset_name)
    return names


def _tuning_layout_snapshot(row):
    layout = row.get("layout", {})
    return {
        "room_count": layout.get("room_count"),
        "main_path_room_count": layout.get("main_path_room_count"),
        "side_room_count": layout.get("side_room_count"),
        "added_loop_edges": layout.get("added_loop_edges"),
        "locked_door_count": layout.get("locked_door_count"),
        "key_room_count": layout.get("key_room_count"),
        "shop_room_count": layout.get("shop_room_count"),
        "treasure_room_count": layout.get("treasure_room_count"),
        "enemy_room_count": layout.get("enemy_room_count"),
        "boss_room_count": layout.get("role_counts", {}).get("boss", 0),
        "pass": bool(layout.get("pass")),
    }


def _tuning_preset_snapshot(row):
    return {
        "preset": row.get("preset"),
        "label": row.get("label"),
        "intent": row.get("intent"),
        "config": _matrix_config(row.get("config", {})),
        "layout": _tuning_layout_snapshot(row),
    }


def _build_tuning_quick_choices(matrix):
    rows_by_name = {str(row.get("preset")): row for row in matrix.get("presets", [])}
    choices = []
    for goal in V2_TUNING_GUIDE_GOALS:
        presets = [
            _tuning_preset_snapshot(rows_by_name[preset_name])
            for preset_name in goal.get("recommended_presets", [])
            if preset_name in rows_by_name
        ]
        choices.append(
            {
                "goal": goal.get("goal"),
                "title": goal.get("title"),
                "use_when": goal.get("use_when"),
                "tradeoff": goal.get("tradeoff"),
                "recommended_presets": list(goal.get("recommended_presets", [])),
                "available_presets": presets,
            }
        )
    return choices


def _write_tuning_guide_markdown(guide):
    markdown_path = _saved_report_path(V2_REPORT_PREFIX + "_TuningGuide.md")
    lines = [
        "# Cubeless PCG Dungeon V2 Tuning Guide",
        "",
        "This guide translates the current RoomRuleMatrix into quick authoring choices.",
        "",
        "## Quick Choice",
        "",
        "| Goal | Recommended Preset | Use When | Tradeoff |",
        "| --- | --- | --- | --- |",
    ]
    for choice in guide.get("quick_choices", []):
        preset_names = ", ".join("`{}`".format(item.get("preset")) for item in choice.get("available_presets", []))
        if not preset_names:
            preset_names = "(missing)"
        lines.append(
            "| {goal} | {presets} | {use_when} | {tradeoff} |".format(
                goal=_md_cell(choice.get("title")),
                presets=preset_names,
                use_when=_md_cell(choice.get("use_when")),
                tradeoff=_md_cell(choice.get("tradeoff")),
            )
        )
    lines.extend(
        [
            "",
            "## Preset Matrix Inputs",
            "",
            "| Preset | Rooms | Main | Side | Loops | Grid | Corridor | Combat | Treasure | Key | Shop | Locked | Boss | Ceiling |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in guide.get("preset_matrix_inputs", []):
        config = row.get("config", {})
        layout = row.get("layout", {})
        lines.append(
            "| `{preset}` | {rooms} | {main} | {side} | {loops} | {grid} | {corridor} | {combat} | {treasure} | {key} | {shop} | {locked} | {boss} | {ceiling} |".format(
                preset=row.get("preset"),
                rooms=layout.get("room_count"),
                main=layout.get("main_path_room_count"),
                side=layout.get("side_room_count"),
                loops=layout.get("added_loop_edges"),
                grid=config.get("grid_cell_size"),
                corridor=config.get("corridor_width"),
                combat=layout.get("enemy_room_count"),
                treasure=layout.get("treasure_room_count"),
                key=layout.get("key_room_count"),
                shop=layout.get("shop_room_count"),
                locked=layout.get("locked_door_count"),
                boss=layout.get("boss_room_count"),
                ceiling=config.get("use_ceiling"),
            )
        )
    lines.extend(["", "## Parameter Knobs", ""])
    for knob in guide.get("parameter_knobs", []):
        lines.append(
            "- `{}`: {} Increase: {} Decrease: {}".format(
                knob.get("key"),
                knob.get("meaning"),
                knob.get("increase"),
                knob.get("decrease"),
            )
        )
    lines.extend(
        [
            "",
            "## Source Reports",
            "",
            "- Matrix JSON: `{}`".format(guide.get("source_paths", {}).get("room_rule_matrix")),
            "- Tuning JSON: `{}`".format(guide.get("report_path")),
        ]
    )
    os.makedirs(os.path.dirname(markdown_path), exist_ok=True)
    with open(markdown_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return markdown_path


def write_tuning_guide():
    matrix_source = _read_saved_json(V2_REPORT_PREFIX + "_RoomRuleMatrix.json")
    matrix = matrix_source.get("data", {})
    matrix_presets = [_tuning_preset_snapshot(row) for row in matrix.get("presets", [])]
    matrix_preset_names = {str(row.get("preset")) for row in matrix.get("presets", [])}
    recommended_names = _tuning_recommended_preset_names()
    missing_recommended = sorted(name for name in recommended_names if name not in matrix_preset_names)
    quick_choices = _build_tuning_quick_choices(matrix)
    checks = {
        "room_rule_matrix_loaded": bool(matrix_source.get("exists")) and not matrix_source.get("error"),
        "room_rule_matrix_pass": bool(matrix.get("pass")),
        "recommended_presets_exist": not missing_recommended,
        "quick_choices_present": len(quick_choices) == len(V2_TUNING_GUIDE_GOALS),
        "parameter_knobs_present": len(V2_TUNING_PARAMETER_KNOBS) > 0,
    }
    guide = {
        "schema": "cubeless_pcg_dungeon_v2_tuning_guide_v1",
        "root": V2_ROOT,
        "level_path": V2_LEVEL_PATH,
        "source_paths": {
            "room_rule_matrix": matrix_source.get("path"),
        },
        "output_policy": dict(V2_OUTPUT_POLICY),
        "recommended_preset_names": recommended_names,
        "missing_recommended_presets": missing_recommended,
        "quick_choices": quick_choices,
        "parameter_knobs": copy.deepcopy(V2_TUNING_PARAMETER_KNOBS),
        "preset_matrix_inputs": matrix_presets,
        "checks": checks,
        "pass": all(bool(value) for value in checks.values()),
    }
    json_path = _saved_report_path(V2_REPORT_PREFIX + "_TuningGuide.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(guide, handle, indent=2, ensure_ascii=False)
    guide["report_path"] = json_path
    guide["markdown_path"] = _write_tuning_guide_markdown(guide)
    unreal.log(
        "CubelessDungeonPCGV2 tuning guide: "
        + json.dumps(
            {
                "pass": guide["pass"],
                "quick_choice_count": len(guide["quick_choices"]),
                "missing_recommended_presets": missing_recommended,
            },
            ensure_ascii=False,
        )
    )
    return guide


def run_pcg_bridge_entrypoint():
    with v2_context() as dungeon:
        controller_actor = _v2_find_controller_actor()
        controller_config = (
            _v2_controller_actor_to_config(controller_actor, clamp_to_ranges=True)
            if controller_actor
            else {"pass": False, "config": {}, "read_errors": ["missing controller actor"]}
        )
        layout_resolution = {}
        bridge_actor = dungeon._find_pcg_bridge_actor()
        bridge_tag_update = {}
        source = "pcg_bridge_v2_bp_actor_property"
        if controller_config.get("pass"):
            layout_resolution = _v2_resolve_controller_layout_config(dungeon, controller_actor, controller_config["config"])
            if layout_resolution.get("adjusted"):
                controller_config = _v2_controller_actor_to_config(controller_actor, clamp_to_ranges=True)
            config = layout_resolution.get("config", controller_config["config"])
            if bridge_actor:
                bridge_tag_update = dungeon._set_bridge_config_tags(bridge_actor, config)
        else:
            source = "pcg_bridge_v2_bridge_tag_fallback"
            config = dungeon._parse_dungeon_config_from_actor(bridge_actor)
        report = dungeon.spawn_validation_dungeon(source=source, config=config)
        report["v2_entrypoint_source"] = source
        report["v2_bp_controller_config"] = controller_config
        report["v2_bp_controller_layout_resolution"] = layout_resolution
        report["v2_bridge_tag_fallback_sync"] = bridge_tag_update
        unreal.log("CubelessDungeonPCGV2Entrypoint report: {}".format(report.get("pass")))
        return report


def build_all():
    with v2_context() as dungeon:
        report = dungeon.build_all()
        controller_report = _ensure_bp_controller_in_context(dungeon, save_dirty_packages=True)
        binding_audit = _audit_pcg_parameter_binding_in_context(dungeon, save_report=True)
        report["v2_bp_controller"] = controller_report
        report["v2_pcg_parameter_binding"] = binding_audit
        report["pass"] = bool(
            report.get("pass")
            and controller_report.get("pass")
            and binding_audit.get("pass")
        )
    return _write_v2_wrapper_report("BuildAll", report)


def begin_generation_refresh_from_bridge(keep_existing_output=False):
    with v2_context() as dungeon:
        return dungeon.begin_pcg_generation_refresh_from_bridge(keep_existing_output=keep_existing_output)


def begin_generation_refresh_with_bp_controller(
    keep_existing_output=False,
    save_dirty_packages=True,
):
    with v2_context() as dungeon:
        controller_sync = _sync_bp_controller_to_bridge_in_context(
            dungeon,
            save_dirty_packages=save_dirty_packages,
        )
        if not controller_sync.get("pass"):
            report = {
                "schema": "cubeless_pcg_dungeon_generation_refresh_v1",
                "status": "failed",
                "refresh_policy": (
                    "V2 BP-controller-backed PCG generation refresh. BP controller sync failed before "
                    "the bridge validation dungeon or native output generation was requested."
                ),
                "source": "bp_controller",
                "bp_controller_sync": controller_sync,
                "checks": {
                    "bp_controller_sync_pass": False,
                },
                "pass": False,
            }
            dungeon._write_pcg_generation_refresh_report(report)
            unreal.log(
                "CubelessDungeonPCGV2 BP-controller refresh begin failed: "
                + json.dumps(
                    {
                        "controller_label": V2_CONTROLLER_LABEL,
                        "failed_checks": [
                            key for key, value in controller_sync.get("checks", {}).items() if not value
                        ],
                    },
                    ensure_ascii=False,
                )
            )
            return report

        report = dungeon.begin_pcg_generation_refresh_from_bridge(keep_existing_output=keep_existing_output)
        report["source"] = "bp_controller"
        report["bp_controller_sync"] = controller_sync
        report["refresh_policy"] = (
            "V2 BP-controller-backed PCG-generation-only refresh. It reads the placed BP controller "
            "actor's Details-panel variables, validates them, writes the bridge tag authoring surface, "
            "then regenerates the validation dungeon and NativeOutput. Gameplay implementation validation "
            "is intentionally excluded."
        )
        report["checks"] = dict(report.get("checks", {}), bp_controller_sync_pass=True)
        dungeon._write_pcg_generation_refresh_report(report)
        unreal.log(
            "CubelessDungeonPCGV2 BP-controller PCG generation refresh begin: "
            + json.dumps(
                {
                    "controller_label": V2_CONTROLLER_LABEL,
                    "status": report.get("status"),
                    "output_generate_requested": report.get("native_output_begin", {}).get("generate_request", {}).get("ok"),
                },
                ensure_ascii=False,
            )
        )
        return report


def begin_generation_refresh_with_authoring_preset(
    preset_name="default",
    config_overrides=None,
    keep_existing_output=False,
    save_dirty_packages=True,
):
    with v2_context() as dungeon:
        if config_overrides:
            preset_apply_report = _apply_authoring_preset_overrides_to_bridge_in_context(
                dungeon,
                preset_name=preset_name,
                config_overrides=config_overrides,
                save_dirty_packages=save_dirty_packages,
            )
            if not preset_apply_report.get("pass"):
                report = {
                    "schema": "cubeless_pcg_dungeon_generation_refresh_v1",
                    "status": "failed",
                    "refresh_policy": (
                        "V2 preset-plus-override PCG generation refresh. Override validation or application "
                        "failed before the bridge validation dungeon or native output generation was requested."
                    ),
                    "preset_name": str(preset_name),
                    "config_overrides": preset_apply_report.get("config_overrides", {}),
                    "preset_apply": preset_apply_report,
                    "checks": {
                        "preset_apply_pass": False,
                        "config_overrides_pass": bool(
                            preset_apply_report.get("config_overrides", {}).get("pass")
                        ),
                    },
                    "pass": False,
                }
                dungeon._write_pcg_generation_refresh_report(report)
                unreal.log(
                    "CubelessDungeonPCGV2 preset-plus-override refresh begin failed: "
                    + json.dumps(
                        {
                            "preset_name": str(preset_name),
                            "available_presets": preset_apply_report.get("available_presets", []),
                            "invalid_overrides": preset_apply_report.get("config_overrides", {}).get("invalid_entries", []),
                        },
                        ensure_ascii=False,
                    )
                )
                return report

            report = dungeon.begin_pcg_generation_refresh_from_bridge(keep_existing_output=keep_existing_output)
            report["preset_name"] = str(preset_name)
            report["config_overrides"] = preset_apply_report.get("config_overrides", {})
            report["preset_apply"] = preset_apply_report
            report["refresh_policy"] = (
                "V2 preset-plus-override PCG-generation-only refresh. It applies the requested base preset, "
                "validates the provided config overrides, writes the merged bridge tag authoring surface, "
                "then regenerates the validation dungeon and NativeOutput. Gameplay implementation validation "
                "is intentionally excluded."
            )
            report["checks"] = dict(
                report.get("checks", {}),
                preset_apply_pass=True,
                config_overrides_pass=True,
            )
            dungeon._write_pcg_generation_refresh_report(report)
            unreal.log(
                "CubelessDungeonPCGV2 preset-plus-override PCG generation refresh begin: "
                + json.dumps(
                    {
                        "preset_name": str(preset_name),
                        "override_count": len(report.get("config_overrides", {}).get("entries", [])),
                        "status": report.get("status"),
                        "output_generate_requested": report.get("native_output_begin", {}).get("generate_request", {}).get("ok"),
                    },
                    ensure_ascii=False,
                )
            )
            return report

        return dungeon.begin_pcg_generation_refresh_with_authoring_preset(
            preset_name=preset_name,
            keep_existing_output=keep_existing_output,
            save_dirty_packages=save_dirty_packages,
        )


def _v2_allow_seed_suite_warning(report, reason):
    checks = dict(report.get("checks", {}))
    if checks.get("seed_suite_pass", True):
        report["seed_suite_warning"] = {"applied": False}
        return report

    seed_suite = report.get("seed_suite", {})
    checks["seed_suite_pass"] = True
    pass_value = bool(all(checks.values()))
    report["checks"] = checks
    report["seed_suite_warning"] = {
        "applied": True,
        "reason": str(reason),
        "original_seed_suite_pass": bool(seed_suite.get("pass")),
        "fail_count": seed_suite.get("fail_count"),
        "pass_count": seed_suite.get("pass_count"),
        "seed_count": seed_suite.get("seed_count"),
    }
    report["status"] = "passed" if pass_value else "failed"
    report["pass"] = pass_value
    v1._write_pcg_generation_refresh_report(report)
    return report


def _v2_allow_final_gate_seed_suite_warning(gate, reason):
    checks = dict(gate.get("checks", {}))
    seed_suite_failed = not bool(checks.get("seed_suite_pass", True)) or not bool(
        checks.get("seed_suite_fail_count_zero", True)
    )
    if not seed_suite_failed:
        gate["seed_suite_warning"] = {"applied": False}
        return gate

    checks["seed_suite_pass"] = True
    checks["seed_suite_fail_count_zero"] = True
    pass_value = bool(all(checks.values()))
    gate["checks"] = checks
    gate["seed_suite_warning"] = {
        "applied": True,
        "reason": str(reason),
        "ignored_checks": ["seed_suite_pass", "seed_suite_fail_count_zero"],
    }
    gate["status"] = "passed" if pass_value else "failed"
    gate["pass"] = pass_value
    v1._write_pcg_generation_gate_report(gate)
    return gate


def verify_generation_refresh(
    enable_output_only_review=True,
    save_dirty_packages=True,
    allow_seed_suite_warning=False,
):
    with v2_context() as dungeon:
        report = dungeon.verify_pcg_generation_refresh(
            enable_output_only_review=enable_output_only_review,
            save_dirty_packages=save_dirty_packages,
        )
        if allow_seed_suite_warning:
            report = _v2_allow_seed_suite_warning(
                report,
                "BP/custom single-seed authoring validates the generated output and records seed-suite failures as warnings.",
            )
        return report


def set_native_output_only_review_mode(enabled=True):
    with v2_context() as dungeon:
        return dungeon.set_native_output_only_review_mode(enabled)


def setup_native_output_only_review_camera(camera_height=14500.0, y_backoff=2600.0):
    with v2_context() as dungeon:
        return dungeon.setup_native_output_only_review_camera(
            camera_height=camera_height * 1.65,
            y_backoff=y_backoff * 1.65,
        )


def setup_pcg_generation_oblique_review_camera(
    camera_height=4200.0,
    x_backoff=5200.0,
    y_backoff=6900.0,
    pitch=-32.0,
    yaw=48.0,
):
    with v2_context() as dungeon:
        return dungeon.setup_pcg_generation_oblique_review_camera(
            camera_height=camera_height * 1.65,
            x_backoff=x_backoff * 1.75,
            y_backoff=y_backoff * 1.75,
            pitch=pitch,
            yaw=yaw,
        )


def record_generation_final_gate(allow_seed_suite_warning=False):
    with v2_context() as dungeon:
        gate = dungeon.record_pcg_generation_final_gate()
        if allow_seed_suite_warning:
            gate = _v2_allow_final_gate_seed_suite_warning(
                gate,
                "BP/custom single-seed authoring validates the generated output and records seed-suite failures as warnings.",
            )
        return gate


def get_authoring_preset_catalog(seed_count=0):
    with v2_context() as dungeon:
        return dungeon.get_authoring_preset_catalog(seed_count=seed_count)


def run_authoring_preset_seed_matrix(preset_names=None, seed_count=5, write_report=True):
    with v2_context() as dungeon:
        return dungeon.run_authoring_preset_seed_matrix(
            preset_names=preset_names,
            seed_count=seed_count,
            write_report=write_report,
        )


def get_output_policy():
    return dict(V2_OUTPUT_POLICY)
