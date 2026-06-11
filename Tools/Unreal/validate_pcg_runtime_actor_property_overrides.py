"""Validate runtime PCG static-mesh overrides through actor properties.

This is a disposable validation pass for the Landscape MCP temp map. It does
not rewrite PCG graphs or production assets; it spawns short-lived runtime
actors, reads their generated ISM components, writes a report, then removes the
validation actors again.
"""

import gc
import importlib
import json
import os
import pathlib
import sys
import traceback

import unreal


TARGET_LEVEL = "/Game/_MCP_Temp/PCG/LVL_PCG_LandscapeValidation_MCP"
REPORT_NAME = "pcg_runtime_actor_property_override_validation_report.json"
ACTOR_PREFIX = "MCP_Cubeless_PCG_RuntimeOverrideValidation"
PROJECT_PLUGIN_PYTHON = r"D:\Git\CubelessStylized\Plugins\CustomTools\Content\Python"
VALIDATION_MODE = globals().get("VALIDATION_MODE", "run")

RUNTIME_BLUEPRINT_OBJECT = (
    "/Game/Cubeless/PCG/Runtime/Blueprints/"
    "BP_Cubeless_PCG_EcosystemRuntime.BP_Cubeless_PCG_EcosystemRuntime"
)
RUNTIME_BLUEPRINT_CLASS = (
    "/Game/Cubeless/PCG/Runtime/Blueprints/"
    "BP_Cubeless_PCG_EcosystemRuntime.BP_Cubeless_PCG_EcosystemRuntime_C"
)

DEFAULT_TREE_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_05.SM_Conifer_05"
)
OVERRIDE_TREE_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_08.SM_Conifer_08"
)
DEFAULT_GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)
OVERRIDE_GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Plants/"
    "SM_Fern_01.SM_Fern_01"
)
DEFAULT_ROCK_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Stones/Rocks/"
    "SM_SmallRock_01.SM_SmallRock_01"
)
OVERRIDE_ROCK_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Stones/Rocks/"
    "SM_SmallRock_02.SM_SmallRock_02"
)

CASE_SPECS = [
    {
        "name": "GrassAndTreeOverride",
        "center_xy": (-12600.0, 12600.0),
        "preset_type": 1,
        "density_override": 3,
        "tree_override": 4,
        "material_mood": 3,
        "debug_material_preview": False,
        "overrides": {
            "UseGrassMeshOverride": True,
            "GrassMeshOverride": OVERRIDE_GRASS_MESH,
            "UseTreeMeshOverride": True,
            "TreeMeshOverride": OVERRIDE_TREE_MESH,
            "UseRockMeshOverride": False,
        },
        "expected": {
            "grass": OVERRIDE_GRASS_MESH,
            "tree": OVERRIDE_TREE_MESH,
        },
    },
    {
        "name": "RockOverride",
        "center_xy": (12600.0, -12600.0),
        "preset_type": 3,
        "density_override": 0,
        "tree_override": 1,
        "material_mood": 2,
        "debug_material_preview": False,
        "overrides": {
            "UseGrassMeshOverride": False,
            "UseTreeMeshOverride": False,
            "UseRockMeshOverride": True,
            "RockMeshOverride": OVERRIDE_ROCK_MESH,
        },
        "expected": {
            "rock": OVERRIDE_ROCK_MESH,
        },
    },
]


def release_python_uobject_refs():
    for attr_name in ("last_type", "last_value", "last_traceback"):
        try:
            if hasattr(sys, attr_name):
                setattr(sys, attr_name, None)
        except Exception:
            pass
    gc.collect()
    collect_garbage = getattr(getattr(unreal, "SystemLibrary", None), "collect_garbage", None)
    if collect_garbage:
        try:
            collect_garbage()
        except Exception:
            pass


def load_menu_module():
    if PROJECT_PLUGIN_PYTHON not in sys.path:
        sys.path.append(PROJECT_PLUGIN_PYTHON)
    from ArtScripts import CubelessEDPCG

    return importlib.reload(CubelessEDPCG)


def get_editor_world():
    subsystem_cls = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_cls:
        try:
            subsystem = unreal.get_editor_subsystem(subsystem_cls)
            world = subsystem.get_editor_world() if subsystem else None
            if world:
                return world
        except Exception:
            pass
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def get_current_level_path():
    world = get_editor_world()
    if not world:
        return None
    return world.get_path_name().split(".", 1)[0]


def get_all_level_actors():
    actor_subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if actor_subsystem_cls:
        actor_subsystem = unreal.get_editor_subsystem(actor_subsystem_cls)
        if actor_subsystem:
            return list(actor_subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def is_landscape_actor(actor):
    class_name = actor.get_class().get_name()
    label = actor_label(actor)
    return class_name == "Landscape" or "LandscapeStreamingProxy" in class_name or "Landscape" in label


def trace_landscape(x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        get_editor_world(),
        unreal.Vector(float(x), float(y), 200000.0),
        unreal.Vector(float(x), float(y), -200000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
    )
    data = hit.to_tuple()
    blocking = bool(data[0]) if data else False
    actor = data[9] if blocking and len(data) > 9 else None
    if not blocking or not actor or not is_landscape_actor(actor):
        return {"hit": False, "actor": actor_label(actor) if actor else "None", "location": None}
    return {"hit": True, "actor": actor_label(actor), "location": data[4]}


def load_static_mesh(mesh_path):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        raise RuntimeError("Missing static mesh: " + mesh_path)
    return mesh


def load_runtime_blueprint_class():
    actor_class = unreal.load_class(None, RUNTIME_BLUEPRINT_CLASS)
    if not actor_class:
        actor_class = unreal.EditorAssetLibrary.load_blueprint_class(RUNTIME_BLUEPRINT_OBJECT)
    return actor_class


def blueprint_variable_exists(blueprint, variable_name):
    actor_class = load_runtime_blueprint_class()
    if actor_class:
        try:
            cdo = unreal.get_default_object(actor_class)
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
        try:
            blueprint.set_blueprint_variable_instance_editable(variable_name, value)
        except Exception:
            pass


def set_variable_expose_on_spawn(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_expose_on_spawn(blueprint, variable_name, value)
    except Exception:
        try:
            blueprint.set_blueprint_variable_expose_on_spawn(variable_name, value)
        except Exception:
            pass


def ensure_runtime_blueprint_override_variables():
    blueprint = unreal.EditorAssetLibrary.load_asset(RUNTIME_BLUEPRINT_OBJECT)
    if not blueprint:
        raise RuntimeError("Missing runtime Blueprint: " + RUNTIME_BLUEPRINT_OBJECT)

    bool_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    mesh_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.StaticMesh.static_class())
    variable_specs = [
        ("UseTreeMeshOverride", bool_type, False),
        ("TreeMeshOverride", mesh_type, DEFAULT_TREE_MESH),
        ("UseGrassMeshOverride", bool_type, False),
        ("GrassMeshOverride", mesh_type, DEFAULT_GRASS_MESH),
        ("UseRockMeshOverride", bool_type, False),
        ("RockMeshOverride", mesh_type, DEFAULT_ROCK_MESH),
    ]

    added = []
    for variable_name, pin_type, _default_value in variable_specs:
        if blueprint_variable_exists(blueprint, variable_name):
            continue
        ok = unreal.BlueprintEditorLibrary.add_member_variable(blueprint, variable_name, pin_type)
        if not ok:
            raise RuntimeError("Failed to add runtime Blueprint variable: " + variable_name)
        added.append(variable_name)

    for variable_name, _pin_type, _default_value in variable_specs:
        set_variable_editable(blueprint, variable_name, True)
        set_variable_expose_on_spawn(blueprint, variable_name, True)

    blueprint.modify()
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    actor_class = load_runtime_blueprint_class()
    if not actor_class:
        raise RuntimeError("Failed to load runtime Blueprint class after compile: " + RUNTIME_BLUEPRINT_CLASS)
    cdo = unreal.get_default_object(actor_class)
    cdo.modify()
    for variable_name, _pin_type, default_value in variable_specs:
        if isinstance(default_value, bool):
            cdo.set_editor_property(variable_name, default_value)
        else:
            cdo.set_editor_property(variable_name, load_static_mesh(default_value))

    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(blueprint))
    return {"added": added, "saved": saved}


def set_mesh_property(actor, prop_name, mesh_path):
    actor.set_editor_property(prop_name, load_static_mesh(mesh_path))


def set_default_override_properties(actor):
    defaults = {
        "UseTreeMeshOverride": False,
        "TreeMeshOverride": DEFAULT_TREE_MESH,
        "UseGrassMeshOverride": False,
        "GrassMeshOverride": DEFAULT_GRASS_MESH,
        "UseRockMeshOverride": False,
        "RockMeshOverride": DEFAULT_ROCK_MESH,
    }
    for prop_name, value in defaults.items():
        if isinstance(value, bool):
            actor.set_editor_property(prop_name, value)
        else:
            set_mesh_property(actor, prop_name, value)


def apply_spec_properties(actor, spec):
    actor.set_editor_property("PresetType", int(spec["preset_type"]))
    actor.set_editor_property("DensityOverride", int(spec["density_override"]))
    actor.set_editor_property("TreeOverride", int(spec["tree_override"]))
    actor.set_editor_property("MaterialMood", int(spec["material_mood"]))
    actor.set_editor_property("DebugMaterialPreview", bool(spec["debug_material_preview"]))
    set_default_override_properties(actor)
    for prop_name, value in spec["overrides"].items():
        if isinstance(value, bool):
            actor.set_editor_property(prop_name, value)
        else:
            set_mesh_property(actor, prop_name, value)


def configure_validation_spline(actor):
    splines = actor.get_components_by_class(unreal.SplineComponent)
    if not splines:
        raise RuntimeError("Runtime PCG actor has no SplineComponent: " + actor_label(actor))
    points = [
        unreal.Vector(0.0, -6000.0, 0.0),
        unreal.Vector(-900.0, -3000.0, 0.0),
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Vector(900.0, 3000.0, 0.0),
        unreal.Vector(0.0, 6000.0, 0.0),
    ]
    for spline in splines:
        spline.clear_spline_points(False)
        for point in points:
            spline.add_spline_point(point, unreal.SplineCoordinateSpace.LOCAL, False)
        spline.set_closed_loop(False, False)
        spline.update_spline()


def destroy_validation_actors():
    destroyed = []
    for actor in list(get_all_level_actors()):
        label = actor_label(actor)
        if not label.startswith(ACTOR_PREFIX):
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


def find_actor_by_label(label):
    for actor in get_all_level_actors():
        if actor_label(actor) == label:
            return actor
    return None


def case_actor_label(spec):
    return "{}_{}_Validation".format(ACTOR_PREFIX, spec["name"])


def object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def component_graph_path(component):
    try:
        graph_instance = component.get_editor_property("graph_instance")
        graph = graph_instance.get_editor_property("graph") if graph_instance else None
        if graph:
            return graph.get_path_name()
    except Exception:
        pass
    try:
        graph = component.get_editor_property("graph")
        if graph:
            return graph.get_path_name()
    except Exception:
        pass
    return None


def classify_mesh(component_name, mesh_path):
    text = (component_name + " " + str(mesh_path)).lower()
    if any(token in text for token in ("tree", "pine", "spruce", "conifer", "trunk")):
        return "tree"
    if any(token in text for token in ("rock", "stone", "boulder")):
        return "rock"
    if any(token in text for token in ("grass", "fern", "foliage", "leaf", "leaves", "plant", "flower")):
        return "grass"
    return "other"


def ism_rows(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        try:
            mesh = component.get_editor_property("static_mesh")
            mesh_path = object_path(mesh)
        except Exception:
            mesh_path = None
        try:
            count = int(component.get_instance_count())
        except Exception:
            count = -1
        rows.append(
            {
                "component": component.get_name(),
                "mesh": mesh_path,
                "category": classify_mesh(component.get_name(), mesh_path),
                "count": count,
            }
        )
    rows.sort(key=lambda row: (str(row["category"]), str(row["mesh"]), row["component"]))
    return rows


def pcg_component_rows(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.PCGComponent):
        rows.append({"component": component.get_name(), "graph": component_graph_path(component)})
    rows.sort(key=lambda row: row["component"])
    return rows


def summarize_properties(actor):
    prop_names = [
        "PresetType",
        "DensityOverride",
        "TreeOverride",
        "MaterialMood",
        "DebugMaterialPreview",
        "UseTreeMeshOverride",
        "TreeMeshOverride",
        "UseGrassMeshOverride",
        "GrassMeshOverride",
        "UseRockMeshOverride",
        "RockMeshOverride",
    ]
    summary = {}
    for prop_name in prop_names:
        try:
            value = actor.get_editor_property(prop_name)
            summary[prop_name] = object_path(value) if hasattr(value, "get_path_name") else value
        except Exception as exc:
            summary[prop_name] = "ERR: " + str(exc)
    return summary


def validate_case_rows(spec, rows):
    positive_rows = [row for row in rows if int(row["count"]) > 0]
    meshes = {row["mesh"] for row in positive_rows}
    category_meshes = {}
    for row in positive_rows:
        category_meshes.setdefault(row["category"], set()).add(row["mesh"])
    checks = {}
    for category, expected_mesh in spec["expected"].items():
        checks[category + "_override_has_output"] = expected_mesh in meshes
        checks[category + "_override_exclusive_for_category"] = category_meshes.get(category, set()) == {
            expected_mesh
        }
    checks["case_pass"] = bool(positive_rows) and all(checks.values())
    return checks


def spawn_case_actor(spec, index, menu_module):
    trace = trace_landscape(*spec["center_xy"])
    if not trace["hit"]:
        raise RuntimeError("Landscape trace failed for {} at {}".format(spec["name"], spec["center_xy"]))

    actor_class = load_runtime_blueprint_class()
    if not actor_class:
        raise RuntimeError("Missing runtime Blueprint class: " + RUNTIME_BLUEPRINT_CLASS)

    location = trace["location"]
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        unreal.Vector(location.x, location.y, location.z),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn runtime validation actor: " + spec["name"])

    label = case_actor_label(spec)
    actor.set_actor_label(label)
    apply_spec_properties(actor, spec)
    configure_validation_spline(actor)
    apply_result = menu_module.apply_production_candidate_selector(actor, force=True)
    rows = ism_rows(actor)
    return {
        "index": index,
        "name": spec["name"],
        "actor": actor_label(actor),
        "class": object_path(actor.get_class()),
        "trace_actor": trace["actor"],
        "location": [float(location.x), float(location.y), float(location.z)],
        "properties": summarize_properties(actor),
        "apply_result": apply_result,
        "pcg_components": pcg_component_rows(actor),
        "ism_rows": rows,
        "checks": validate_case_rows(spec, rows),
    }


def read_existing_case(spec, index):
    label = case_actor_label(spec)
    actor = find_actor_by_label(label)
    if not actor:
        return {
            "index": index,
            "name": spec["name"],
            "actor": label,
            "error": "validation actor not found",
            "checks": {"case_pass": False},
        }
    rows = ism_rows(actor)
    return {
        "index": index,
        "name": spec["name"],
        "actor": actor_label(actor),
        "class": object_path(actor.get_class()),
        "properties": summarize_properties(actor),
        "pcg_components": pcg_component_rows(actor),
        "ism_rows": rows,
        "checks": validate_case_rows(spec, rows),
    }


def get_dirty_map_package_names():
    utils = getattr(unreal, "EditorLoadingAndSavingUtils", None)
    if not utils or not hasattr(utils, "get_dirty_map_packages"):
        return []
    result = []
    for package in utils.get_dirty_map_packages():
        try:
            result.append(package.get_name())
        except Exception:
            result.append(str(package))
    return sorted(result)


def is_target_level_dirty_package(package_name):
    external_prefix = "/Game/__ExternalActors__" + TARGET_LEVEL[len("/Game") :] + "/"
    return package_name.startswith(TARGET_LEVEL) or package_name.startswith(external_prefix)


def get_dirty_content_package_names():
    utils = getattr(unreal, "EditorLoadingAndSavingUtils", None)
    if not utils or not hasattr(utils, "get_dirty_content_packages"):
        return []
    result = []
    for package in utils.get_dirty_content_packages():
        try:
            result.append(package.get_name())
        except Exception:
            result.append(str(package))
    return sorted(result)


def save_target_level_if_safe(dirty_before):
    dirty_maps = get_dirty_map_package_names()
    unexpected_before = [name for name in dirty_before if not is_target_level_dirty_package(name)]
    if unexpected_before:
        return {
            "attempted": False,
            "reason": "non-target dirty maps existed before validation",
            "dirty_maps_before": dirty_before,
            "dirty_maps": dirty_maps,
        }
    unexpected = [name for name in dirty_maps if not is_target_level_dirty_package(name)]
    if unexpected:
        return {"attempted": False, "reason": "unexpected dirty maps", "dirty_maps": dirty_maps}
    try:
        saved = bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False))
    except Exception:
        saved = bool(unreal.EditorAssetLibrary.save_asset(TARGET_LEVEL, only_if_is_dirty=True))
    release_python_uobject_refs()
    return {"attempted": True, "saved": saved, "dirty_maps_after": get_dirty_map_package_names()}


def write_report(report):
    out_dir = pathlib.Path(unreal.Paths.project_saved_dir()) / "MCP_PCG"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / REPORT_NAME
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(out_path)


def main():
    print("MCP_CUBELESS_PCG_RUNTIME_ACTOR_PROPERTY_OVERRIDE_VALIDATE_BEGIN")
    current_level = get_current_level_path()
    dirty_before = get_dirty_map_package_names()
    dirty_content_before = get_dirty_content_package_names()
    report = {
        "target_level": TARGET_LEVEL,
        "current_level": current_level,
        "validation_mode": VALIDATION_MODE,
        "runtime_blueprint": RUNTIME_BLUEPRINT_OBJECT,
        "runtime_blueprint_class": RUNTIME_BLUEPRINT_CLASS,
        "actor_prefix": ACTOR_PREFIX,
        "dirty_maps_before": dirty_before,
        "dirty_content_before": dirty_content_before,
        "cases": [],
    }

    if current_level != TARGET_LEVEL:
        report["validation_pass"] = False
        report["error"] = "Current level is not the Landscape validation level; refusing Python map transition."
        report_path = write_report(report)
        print(json.dumps({"report_path": report_path, "validation_pass": False}, ensure_ascii=False))
        return

    try:
        report["runtime_blueprint_variables"] = ensure_runtime_blueprint_override_variables()
        menu_module = load_menu_module()
        if VALIDATION_MODE in ("run", "prepare"):
            report["destroyed_before"] = destroy_validation_actors()
            for index, spec in enumerate(CASE_SPECS):
                try:
                    report["cases"].append(spawn_case_actor(spec, index, menu_module))
                except Exception as exc:
                    report["cases"].append(
                        {
                            "index": index,
                            "name": spec["name"],
                            "error": str(exc),
                            "traceback": traceback.format_exc(),
                            "checks": {"case_pass": False},
                        }
                    )
            report["prepared"] = True
            if VALIDATION_MODE == "prepare":
                report["validation_pass"] = False
                report["note"] = "Prepared validation actors; run verify_cleanup after editor ticks."
            else:
                report["validation_pass"] = all(case["checks"]["case_pass"] for case in report["cases"])
        elif VALIDATION_MODE == "verify_cleanup":
            for index, spec in enumerate(CASE_SPECS):
                report["cases"].append(read_existing_case(spec, index))
            report["validation_pass"] = all(case["checks"]["case_pass"] for case in report["cases"])
        else:
            report["validation_pass"] = False
            report["error"] = "Unknown VALIDATION_MODE: " + str(VALIDATION_MODE)
    except Exception as exc:
        report["validation_pass"] = False
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
    finally:
        if VALIDATION_MODE in ("run", "verify_cleanup"):
            report["destroyed_after"] = destroy_validation_actors()
            report["save_target_level"] = save_target_level_if_safe(dirty_before)
        else:
            report["destroyed_after"] = []
            report["save_target_level"] = {"attempted": False, "reason": "prepare mode keeps actors for delayed read"}
        report["dirty_maps_after"] = get_dirty_map_package_names()
        report["dirty_content_after"] = get_dirty_content_package_names()

    report_path = write_report(report)
    print(
        json.dumps(
            {
                "report_path": report_path,
                "validation_pass": report["validation_pass"],
                "case_checks": {case["name"]: case["checks"] for case in report["cases"]},
                "dirty_maps_after": report["dirty_maps_after"],
                "dirty_content_after": report["dirty_content_after"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print("MCP_CUBELESS_PCG_RUNTIME_ACTOR_PROPERTY_OVERRIDE_VALIDATE_END")


if __name__ == "__main__":
    main()
