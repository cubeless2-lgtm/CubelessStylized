"""Validate the spline ecosystem falloff role for BP_Cubeless_PCG_EcosystemCandidate.

This is a non-destructive validation route. It creates/updates a dedicated
production-candidate PCG graph, places one unsaved validation actor in TestMap,
and proves that the candidate can act as a spline-driven ecosystem volume:
grass/tree/rock density is highest near the spline and fades with distance.
An optional external road-clearance spline can cut a path through the output.
"""

from __future__ import annotations

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

        def send_command(self, command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
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
            if not chunks:
                raise RuntimeError("No response from UnrealMCP bridge")
            return json.loads(b"".join(chunks).decode("utf-8"))


SETUP_CODE = r"""
import json
import os
import runpy
import time

import unreal


LEVEL_PATH = "/Game/Cubeless/TestMap"
REPORT_NAME = "CubelessSplineEcosystemCandidateFalloff_Report.json"

CANDIDATE_CLASS_PATH = (
    "/Game/Cubeless/PCG/ProductionCandidates/Blueprints/"
    "BP_Cubeless_PCG_EcosystemCandidate.BP_Cubeless_PCG_EcosystemCandidate_C"
)
CANDIDATE_BP_OBJECT = (
    "/Game/Cubeless/PCG/ProductionCandidates/Blueprints/"
    "BP_Cubeless_PCG_EcosystemCandidate.BP_Cubeless_PCG_EcosystemCandidate"
)
ROAD_BP_CLASS_PATH = (
    "/Game/Cubeless/PCG/Runtime/Blueprints/"
    "BP_Cubeless_PCG_ForestRoadRuntime.BP_Cubeless_PCG_ForestRoadRuntime_C"
)

GRAPH_FOLDER = "/Game/Cubeless/PCG/ProductionCandidates/Graphs"
GRAPH_NAME = "PCG_Cubeless_EcosystemCandidate_SplineEcosystemFalloff"
GRAPH_OBJECT = GRAPH_FOLDER + "/" + GRAPH_NAME + "." + GRAPH_NAME

VALIDATION_ACTOR_LABEL = "MCP_Cubeless_PCG_SplineEcosystemCandidate_Validation"
VALIDATION_ACTOR_TAG = "CubelessSplineEcosystemCandidateValidation"
ROAD_CLEARANCE_ACTOR_LABEL = "MCP_Cubeless_PCG_ExternalRoadClearanceSpline_Validation"
LEGACY_ROADSIDE_VALIDATION_ACTOR_LABEL = "MCP_Cubeless_PCG_RoadsideEcosystemCandidate_Validation"
SPLINE_COMPONENT_TAG = "CubelessPCGProductionCandidateSpline"
ROAD_CLEARANCE_SPLINE_TAG = "CubelessExternalRoadClearanceSpline"
ROAD_CLEARANCE_CM = 650.0
ROAD_FILTER_EXTRA_CLEARANCE_CM = 120.0
ENABLE_EXTERNAL_ROAD_VALIDATION = False

DYNAMIC_MESH_ATTR = "DynamicMeshPath"
DYNAMIC_MATERIAL_SLOT0_ATTR = "DynamicMaterialSlot0"
ROAD_CLEARANCE_DISTANCE_ATTR = "RoadClearanceDistance"

GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)
TREE_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_05.SM_Conifer_05"
)
ROCK_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Stones/Rocks/"
    "SM_SmallRock_01.SM_SmallRock_01"
)
GRASS_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_GrassMedium_ForestBalanced.MI_Cubeless_PCG_GrassMedium_ForestBalanced"
)

BRANCH_SPECS = [
    {
        "name": "Grass center",
        "param": "GrassCenter",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_spacing_cm": 18.0,
        "offset_min": (-28.0, -280.0, 0.0),
        "offset_max": (28.0, 280.0, 0.0),
    },
    {
        "name": "Grass inner left",
        "param": "GrassInnerLeft",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_spacing_cm": 50.0,
        "offset_min": (-42.0, -760.0, 0.0),
        "offset_max": (42.0, -360.0, 0.0),
    },
    {
        "name": "Grass inner right",
        "param": "GrassInnerRight",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_spacing_cm": 50.0,
        "offset_min": (-42.0, 360.0, 0.0),
        "offset_max": (42.0, 760.0, 0.0),
    },
    {
        "name": "Grass mid left",
        "param": "GrassMidLeft",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_spacing_cm": 260.0,
        "offset_min": (-80.0, -1320.0, 0.0),
        "offset_max": (80.0, -900.0, 0.0),
    },
    {
        "name": "Grass mid right",
        "param": "GrassMidRight",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_spacing_cm": 260.0,
        "offset_min": (-80.0, 900.0, 0.0),
        "offset_max": (80.0, 1320.0, 0.0),
    },
    {
        "name": "Grass outer left",
        "param": "GrassOuterLeft",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_spacing_cm": 1500.0,
        "offset_min": (-140.0, -2300.0, 0.0),
        "offset_max": (140.0, -1700.0, 0.0),
    },
    {
        "name": "Grass outer right",
        "param": "GrassOuterRight",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_spacing_cm": 1500.0,
        "offset_min": (-140.0, 1700.0, 0.0),
        "offset_max": (140.0, 2300.0, 0.0),
    },
    {
        "name": "Tree center",
        "param": "TreeCenter",
        "kind": "tree",
        "mesh_node": "tree_mesh",
        "source_attr": "TreeMeshOverride",
        "density_spacing_cm": 720.0,
        "offset_min": (-160.0, -240.0, 0.0),
        "offset_max": (160.0, 240.0, 0.0),
    },
    {
        "name": "Tree inner left",
        "param": "TreeInnerLeft",
        "kind": "tree",
        "mesh_node": "tree_mesh",
        "source_attr": "TreeMeshOverride",
        "density_spacing_cm": 1700.0,
        "offset_min": (-190.0, -880.0, 0.0),
        "offset_max": (190.0, -500.0, 0.0),
    },
    {
        "name": "Tree inner right",
        "param": "TreeInnerRight",
        "kind": "tree",
        "mesh_node": "tree_mesh",
        "source_attr": "TreeMeshOverride",
        "density_spacing_cm": 1700.0,
        "offset_min": (-190.0, 500.0, 0.0),
        "offset_max": (190.0, 880.0, 0.0),
    },
    {
        "name": "Tree outer left",
        "param": "TreeOuterLeft",
        "kind": "tree",
        "mesh_node": "tree_mesh",
        "source_attr": "TreeMeshOverride",
        "density_spacing_cm": 12000.0,
        "offset_min": (-240.0, -2300.0, 0.0),
        "offset_max": (240.0, -1750.0, 0.0),
    },
    {
        "name": "Tree outer right",
        "param": "TreeOuterRight",
        "kind": "tree",
        "mesh_node": "tree_mesh",
        "source_attr": "TreeMeshOverride",
        "density_spacing_cm": 12000.0,
        "offset_min": (-240.0, 1750.0, 0.0),
        "offset_max": (240.0, 2300.0, 0.0),
    },
    {
        "name": "Rock center",
        "param": "RockCenter",
        "kind": "rock",
        "mesh_node": "rock_mesh",
        "source_attr": "RockMeshOverride",
        "density_spacing_cm": 220.0,
        "offset_min": (-130.0, -300.0, 0.0),
        "offset_max": (130.0, 300.0, 0.0),
    },
    {
        "name": "Rock inner left",
        "param": "RockInnerLeft",
        "kind": "rock",
        "mesh_node": "rock_mesh",
        "source_attr": "RockMeshOverride",
        "density_spacing_cm": 700.0,
        "offset_min": (-170.0, -820.0, 0.0),
        "offset_max": (170.0, -440.0, 0.0),
    },
    {
        "name": "Rock inner right",
        "param": "RockInnerRight",
        "kind": "rock",
        "mesh_node": "rock_mesh",
        "source_attr": "RockMeshOverride",
        "density_spacing_cm": 700.0,
        "offset_min": (-170.0, 440.0, 0.0),
        "offset_max": (170.0, 820.0, 0.0),
    },
    {
        "name": "Rock outer left",
        "param": "RockOuterLeft",
        "kind": "rock",
        "mesh_node": "rock_mesh",
        "source_attr": "RockMeshOverride",
        "density_spacing_cm": 9000.0,
        "offset_min": (-220.0, -2250.0, 0.0),
        "offset_max": (220.0, -1700.0, 0.0),
    },
    {
        "name": "Rock outer right",
        "param": "RockOuterRight",
        "kind": "rock",
        "mesh_node": "rock_mesh",
        "source_attr": "RockMeshOverride",
        "density_spacing_cm": 9000.0,
        "offset_min": (-220.0, 1700.0, 0.0),
        "offset_max": (220.0, 2250.0, 0.0),
    },
]

GRID_GRADIENT_DEFAULTS = {
    "EcosystemGridExtents": (9000.0, 6500.0, 30.0),
    "EcosystemGridCellSize": (240.0, 240.0, 50.0),
    "EcosystemRibbonStepCm": 160.0,
    "EcosystemRibbonPlanarSubdivisions": 24.0,
    "EcosystemGrassSpacingCm": 75.0,
    "EcosystemWidthCm": 1400.0,
    "EcosystemGrassSpawnRatio": 0.35,
    "EcosystemTreeSpawnRatio": 0.018,
    "EcosystemRockSpawnRatio": 0.04,
}
RIBBON_LATERAL_ROWS_PER_SIDE = 14

CATEGORY_SPECS = [
    {
        "name": "Grass",
        "kind": "grass",
        "mesh_node": "grass_mesh",
        "source_attr": "GrassMeshOverride",
        "density_scale_node": "grass_density_scale",
        "density_scale_property": "EcosystemGrassSpawnRatio",
        "spawn_roll_attr": "GrassSpawnRoll",
        "spawn_roll_seed": 6132037,
        "offset_min": (-65.0, -65.0, 0.0),
        "offset_max": (65.0, 65.0, 0.0),
        "overlap_extents": (38.0, 38.0, 18.0),
    },
    {
        "name": "Tree",
        "kind": "tree",
        "mesh_node": "tree_mesh",
        "source_attr": "TreeMeshOverride",
        "density_scale_node": "tree_density_scale",
        "density_scale_property": "EcosystemTreeSpawnRatio",
        "spawn_roll_attr": "TreeSpawnRoll",
        "spawn_roll_seed": 6132038,
        "offset_min": (-90.0, -90.0, 0.0),
        "offset_max": (90.0, 90.0, 0.0),
        "overlap_extents": (170.0, 170.0, 220.0),
    },
    {
        "name": "Rock",
        "kind": "rock",
        "mesh_node": "rock_mesh",
        "source_attr": "RockMeshOverride",
        "density_scale_node": "rock_density_scale",
        "density_scale_property": "EcosystemRockSpawnRatio",
        "spawn_roll_attr": "RockSpawnRoll",
        "spawn_roll_seed": 6132039,
        "offset_min": (-80.0, -80.0, 0.0),
        "offset_max": (80.0, 80.0, 0.0),
        "overlap_extents": (105.0, 105.0, 60.0),
    },
]

OVERLAP_VALIDATION_EXTENTS = {
    "grass": (38.0, 38.0),
    "tree": (170.0, 170.0),
    "rock": (105.0, 105.0),
}
GRASS_NEAR_DUPLICATE_TOLERANCE_CM = 8.0


def _editor_world():
    subsystem_cls = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_cls:
        subsystem = unreal.get_editor_subsystem(subsystem_cls)
        if subsystem:
            world = subsystem.get_editor_world()
            if world:
                return world
    return unreal.EditorLevelLibrary.get_editor_world()


def _load_level():
    world = _editor_world()
    if not world or not world.get_path_name().startswith(LEVEL_PATH + "."):
        unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    return _editor_world()


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


def _object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _load_asset(path):
    return unreal.EditorAssetLibrary.load_asset(path) or unreal.load_object(None, path)


def _blueprint_variable_exists(blueprint, variable_name):
    try:
        cls = unreal.EditorAssetLibrary.load_blueprint_class(CANDIDATE_BP_OBJECT)
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


def _set_variable_editable(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(blueprint, variable_name, value)
    except Exception:
        blueprint.set_blueprint_variable_instance_editable(variable_name, value)


def _set_variable_expose_on_spawn(blueprint, variable_name, value):
    try:
        unreal.BlueprintEditorLibrary.set_blueprint_variable_expose_on_spawn(blueprint, variable_name, value)
    except Exception:
        blueprint.set_blueprint_variable_expose_on_spawn(variable_name, value)


def _ensure_candidate_variables():
    blueprint = unreal.EditorAssetLibrary.load_asset(CANDIDATE_BP_OBJECT)
    if not blueprint:
        raise RuntimeError("Missing candidate Blueprint: " + CANDIDATE_BP_OBJECT)

    added = []
    material_type = unreal.BlueprintEditorLibrary.get_object_reference_type(unreal.MaterialInterface.static_class())
    bool_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    float_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("real")
    int_type = unreal.BlueprintEditorLibrary.get_basic_type_by_name("int")
    vector_type = unreal.BlueprintEditorLibrary.get_struct_type(unreal.Vector.static_struct())
    variable_specs = [
        ("UseGrassMaterialOverride", bool_type),
        ("GrassMaterialOverride", material_type),
        ("EnableExternalRoadClearance", bool_type),
        ("EcosystemGridExtents", vector_type),
        ("EcosystemGridCellSize", vector_type),
        ("EcosystemWidthCm", float_type),
        ("EcosystemGrassSpawnRatio", float_type),
        ("EcosystemTreeSpawnRatio", float_type),
        ("EcosystemRockSpawnRatio", float_type),
    ]
    legacy_variable_names = [
        "GrassDensityScale",
        "TreeDensityScale",
        "RockDensityScale",
        "EcosystemGrassDensityScale",
        "EcosystemTreeDensityScale",
        "EcosystemRockDensityScale",
        "EcosystemRibbonStepCm",
        "EcosystemRibbonPlanarSubdivisions",
        "EcosystemGrassSpacingCm",
        "EcosystemGrassPlanarSubdivisions",
    ]
    for spec in BRANCH_SPECS:
        prefix = spec["param"]
        legacy_variable_names.extend(
            [prefix + "DensitySpacingCm", prefix + "SpawnOffsetMin", prefix + "SpawnOffsetMax"]
        )
        variable_specs.extend(
            [
                (prefix + "DensitySpacingCm", float_type),
                (prefix + "SpawnOffsetMin", vector_type),
                (prefix + "SpawnOffsetMax", vector_type),
            ]
        )
    for variable_name, variable_type in variable_specs:
        if not _blueprint_variable_exists(blueprint, variable_name):
            if not unreal.BlueprintEditorLibrary.add_member_variable(blueprint, variable_name, variable_type):
                raise RuntimeError("Failed to add Blueprint variable: " + variable_name)
            added.append(variable_name)
        visible = variable_name not in legacy_variable_names
        _set_variable_editable(blueprint, variable_name, visible)
        _set_variable_expose_on_spawn(blueprint, variable_name, visible)
    for variable_name in legacy_variable_names:
        if _blueprint_variable_exists(blueprint, variable_name):
            _set_variable_editable(blueprint, variable_name, False)
            _set_variable_expose_on_spawn(blueprint, variable_name, False)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)

    cls = unreal.EditorAssetLibrary.load_blueprint_class(CANDIDATE_BP_OBJECT)
    if not cls:
        raise RuntimeError("Failed to load candidate class after adding candidate variables.")
    cdo = unreal.get_default_object(cls)
    material = _load_asset(GRASS_MATERIAL)
    if not material:
        raise RuntimeError("Missing grass material: " + GRASS_MATERIAL)
    cdo.set_editor_property("UseGrassMaterialOverride", True)
    cdo.set_editor_property("GrassMaterialOverride", material)
    cdo.set_editor_property("EnableExternalRoadClearance", False)
    for property_name, default_value in GRID_GRADIENT_DEFAULTS.items():
        try:
            if isinstance(default_value, tuple):
                cdo.set_editor_property(property_name, unreal.Vector(*[float(value) for value in default_value]))
            elif isinstance(default_value, int):
                cdo.set_editor_property(property_name, int(default_value))
            else:
                cdo.set_editor_property(property_name, float(default_value))
        except Exception:
            pass
    branch_defaults = {}
    for spec in BRANCH_SPECS:
        prefix = spec["param"]
        density_name = prefix + "DensitySpacingCm"
        offset_min_name = prefix + "SpawnOffsetMin"
        offset_max_name = prefix + "SpawnOffsetMax"
        min_x, min_y, min_z = spec["offset_min"]
        max_x, max_y, max_z = spec["offset_max"]
        offset_min = unreal.Vector(float(min_x), float(min_y), float(min_z))
        offset_max = unreal.Vector(float(max_x), float(max_y), float(max_z))
        cdo.set_editor_property(density_name, float(spec["density_spacing_cm"]))
        cdo.set_editor_property(offset_min_name, offset_min)
        cdo.set_editor_property(offset_max_name, offset_max)
        branch_defaults[prefix] = {
            "density_spacing_cm": float(spec["density_spacing_cm"]),
            "spawn_offset_min": [float(min_x), float(min_y), float(min_z)],
            "spawn_offset_max": [float(max_x), float(max_y), float(max_z)],
        }
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(blueprint))
    return {
        "added": added,
        "saved": saved,
        "grass_material": GRASS_MATERIAL,
        "enable_external_road_clearance_default": False,
        "grid_gradient_defaults": {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in GRID_GRADIENT_DEFAULTS.items()
        },
        "legacy_branch_parameters_hidden": legacy_variable_names,
        "legacy_branch_defaults": branch_defaults,
    }


def _make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


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


def _configure_get_self_spline(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.SELF)
    settings.set_editor_property("actor_selector", actor_selector)

    component_selector = settings.get_editor_property("component_selector")
    component_selector.set_editor_property("component_selection", unreal.PCGComponentSelection.BY_TAG)
    component_selector.set_editor_property("component_selection_tag", SPLINE_COMPONENT_TAG)
    settings.set_editor_property("component_selector", component_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("components_must_overlap_self", False)
    settings.set_editor_property("track_actors_only_within_bounds", False)


def _configure_get_external_road_spline(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", ROAD_CLEARANCE_SPLINE_TAG)
    actor_selector.set_editor_property("select_multiple", True)
    actor_selector.set_editor_property("must_overlap_self", False)
    settings.set_editor_property("actor_selector", actor_selector)

    component_selector = settings.get_editor_property("component_selector")
    component_selector.set_editor_property("component_selection", unreal.PCGComponentSelection.BY_TAG)
    component_selector.set_editor_property("component_selection_tag", ROAD_CLEARANCE_SPLINE_TAG)
    settings.set_editor_property("component_selector", component_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("components_must_overlap_self", False)
    settings.set_editor_property("track_actors_only_within_bounds", False)


def _configure_sampler(node, increment):
    settings = node.get_settings()
    params = settings.get_editor_property("sampler_params")
    params.set_editor_property("dimension", unreal.PCGSplineSamplingDimension.ON_SPLINE)
    params.set_editor_property("mode", unreal.PCGSplineSamplingMode.DISTANCE)
    params.set_editor_property("distance_increment", float(increment))
    params.set_editor_property("subdivisions_per_segment", 8)
    params.set_editor_property("compute_distance", True)
    params.set_editor_property("compute_segment_index", True)
    params.set_editor_property("unbounded", True)
    settings.set_editor_property("sampler_params", params)
    try:
        settings.set_editor_property("seed", 612301)
    except Exception:
        pass


def _configure_road_reference_sampler(node):
    settings = node.get_settings()
    params = settings.get_editor_property("sampler_params")
    params.set_editor_property("dimension", unreal.PCGSplineSamplingDimension.ON_SPLINE)
    params.set_editor_property("mode", unreal.PCGSplineSamplingMode.DISTANCE)
    params.set_editor_property("distance_increment", 120.0)
    params.set_editor_property("subdivisions_per_segment", 8)
    params.set_editor_property("compute_distance", True)
    settings.set_editor_property("sampler_params", params)


def _configure_ribbon_sampler(
    node,
    distance_increment_default="EcosystemRibbonStepCm",
    planar_subdivisions_default="EcosystemRibbonPlanarSubdivisions",
):
    settings = node.get_settings()
    params = settings.get_editor_property("sampler_params")
    params.set_editor_property("dimension", unreal.PCGSplineSamplingDimension.ON_HORIZONTAL)
    params.set_editor_property("mode", unreal.PCGSplineSamplingMode.DISTANCE)
    params.set_editor_property("fill", unreal.PCGSplineSamplingFill.FILL)
    params.set_editor_property("distance_increment", float(GRID_GRADIENT_DEFAULTS[distance_increment_default]))
    params.set_editor_property("subdivisions_per_segment", 8)
    params.set_editor_property("num_planar_subdivisions", int(GRID_GRADIENT_DEFAULTS[planar_subdivisions_default]))
    params.set_editor_property("num_height_subdivisions", 0)
    params.set_editor_property("start_offset", 0.0)
    params.set_editor_property("end_offset", 0.0)
    params.set_editor_property("max_random_offset_normalized", 0.0)
    params.set_editor_property("fit_to_curve", True)
    params.set_editor_property("compute_distance", True)
    params.set_editor_property("compute_segment_index", True)
    params.set_editor_property("unbounded", True)
    settings.set_editor_property("sampler_params", params)
    try:
        settings.set_editor_property("seed", 6132026)
    except Exception:
        pass


def _configure_point_extents(node, planar_subdivisions_default="EcosystemRibbonPlanarSubdivisions"):
    settings = node.get_settings()
    lateral_step = float(GRID_GRADIENT_DEFAULTS["EcosystemWidthCm"]) / float(
        GRID_GRADIENT_DEFAULTS[planar_subdivisions_default]
    )
    # Duplicate Point uses full bounds size as the per-row offset, so extents are half of the wanted row spacing.
    settings.set_editor_property("extents", unreal.Vector(0.0, lateral_step * 0.5, 0.0))
    try:
        settings.set_editor_property("mode", unreal.PCGPointExtentsModifierMode.SET)
    except Exception:
        try:
            settings.set_editor_property("mode", 0)
        except Exception:
            pass


def _configure_lateral_duplicate(node, side, iterations_default="EcosystemRibbonPlanarSubdivisions"):
    settings = node.get_settings()
    settings.set_editor_property("iterations", int(GRID_GRADIENT_DEFAULTS[iterations_default]))
    settings.set_editor_property("direction", unreal.Vector(0.0, float(side), 0.0))
    # UE 5.7 PCG can assert on non-normalized point rotations when Duplicate Point
    # applies the direction in relative space after spline sampling.
    settings.set_editor_property("direction_applied_in_relative_space", False)
    settings.set_editor_property("output_source_point", False)


def _configure_rotation_normalize(node):
    settings = node.get_settings()
    settings.set_editor_property("absolute_offset", False)
    settings.set_editor_property("absolute_rotation", False)
    settings.set_editor_property("absolute_scale", False)
    settings.set_editor_property("uniform_scale", True)
    settings.set_editor_property("offset_min", unreal.Vector(0.0, 0.0, 0.0))
    settings.set_editor_property("offset_max", unreal.Vector(0.0, 0.0, 0.0))
    settings.set_editor_property("rotation_min", _make_rotator(0.0, 0.0, 0.0))
    settings.set_editor_property("rotation_max", _make_rotator(0.0, 0.0, 0.0))
    settings.set_editor_property("scale_min", unreal.Vector(1.0, 1.0, 1.0))
    settings.set_editor_property("scale_max", unreal.Vector(1.0, 1.0, 1.0))
    settings.set_editor_property("recompute_seed", False)


def _configure_scale_normalize(node):
    settings = node.get_settings()
    settings.set_editor_property("absolute_offset", False)
    settings.set_editor_property("absolute_rotation", True)
    settings.set_editor_property("absolute_scale", True)
    settings.set_editor_property("uniform_scale", True)
    settings.set_editor_property("offset_min", unreal.Vector(0.0, 0.0, 0.0))
    settings.set_editor_property("offset_max", unreal.Vector(0.0, 0.0, 0.0))
    settings.set_editor_property("rotation_min", _make_rotator(0.0, 0.0, 0.0))
    settings.set_editor_property("rotation_max", _make_rotator(0.0, 0.0, 0.0))
    settings.set_editor_property("scale_min", unreal.Vector(1.0, 1.0, 1.0))
    settings.set_editor_property("scale_max", unreal.Vector(1.0, 1.0, 1.0))
    settings.set_editor_property("recompute_seed", False)


def _configure_get_actor_property(node, property_name, output_attr):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.SELF)
    settings.set_editor_property("actor_selector", actor_selector)
    settings.set_editor_property("property_name", property_name)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("force_object_and_struct_extraction", False)
    settings.set_editor_property("sanitize_output_attribute_name", True)
    _selector_import(settings, "output_attribute_name", output_attr)


def _selector(text, selector_cls):
    selector = selector_cls()
    selector.import_text("PCGBegin({})PCGEnd".format(text))
    return selector


def _constant(metadata_type, value):
    constant = unreal.PCGMetadataTypesConstantStruct()
    constant.set_editor_property("type", metadata_type)
    if metadata_type == unreal.PCGMetadataTypes.DOUBLE:
        constant.set_editor_property("double_value", float(value))
    elif metadata_type == unreal.PCGMetadataTypes.BOOLEAN:
        constant.set_editor_property("bool_value", bool(value))
    return constant


def _configure_distance(node):
    settings = node.get_settings()
    settings.set_editor_property("output_to_attribute", True)
    settings.set_editor_property(
        "output_attribute",
        _selector(ROAD_CLEARANCE_DISTANCE_ATTR, unreal.PCGAttributePropertySelector),
    )
    settings.set_editor_property("maximum_distance", 20000.0)
    settings.set_editor_property("source_shape", unreal.PCGDistanceShape.CENTER)
    settings.set_editor_property("target_shape", unreal.PCGDistanceShape.CENTER)


def _configure_road_filter(node):
    settings = node.get_settings()
    settings.set_editor_property(
        "target_attribute",
        _selector(ROAD_CLEARANCE_DISTANCE_ATTR, unreal.PCGAttributePropertyInputSelector),
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


def _configure_grid(node):
    settings = node.get_settings()
    settings.set_editor_property(
        "grid_extents",
        unreal.Vector(*[float(value) for value in GRID_GRADIENT_DEFAULTS["EcosystemGridExtents"]]),
    )
    settings.set_editor_property(
        "cell_size",
        unreal.Vector(*[float(value) for value in GRID_GRADIENT_DEFAULTS["EcosystemGridCellSize"]]),
    )
    settings.set_editor_property("coordinate_space", unreal.PCGCoordinateSpace.LOCAL_COMPONENT)
    settings.set_editor_property("set_points_bounds", True)
    settings.set_editor_property("cull_points_outside_volume", False)
    settings.set_editor_property("point_steepness", 0.5)
    try:
        settings.set_editor_property("point_position", unreal.PCGPointPosition.CELL_CENTER)
        settings.set_editor_property("seed", 6132026)
    except Exception:
        pass


def _configure_gradient_distance(node):
    settings = node.get_settings()
    settings.set_editor_property("output_to_attribute", True)
    settings.set_editor_property(
        "output_attribute",
        _selector("SplineDistance", unreal.PCGAttributePropertySelector),
    )
    settings.set_editor_property("maximum_distance", float(GRID_GRADIENT_DEFAULTS["EcosystemWidthCm"]))
    settings.set_editor_property("set_density", True)
    settings.set_editor_property("source_shape", unreal.PCGDistanceShape.CENTER)
    settings.set_editor_property("target_shape", unreal.PCGDistanceShape.CENTER)


def _configure_width_filter(node):
    settings = node.get_settings()
    settings.set_editor_property("lower_bound", 0.0)
    settings.set_editor_property("upper_bound", 0.999)
    settings.set_editor_property("invert_filter", False)
    try:
        settings.set_editor_property("keep_zero_density_points", False)
    except Exception:
        pass


def _configure_category_density_remap(node, density_scale):
    settings = node.get_settings()
    settings.set_editor_property("range_min", 0.0)
    settings.set_editor_property("range_max", 1.0)
    # PCGDistance density is 0 at the spline and 1 at max distance, so invert it here.
    settings.set_editor_property("out_range_min", float(density_scale))
    settings.set_editor_property("out_range_max", 0.0)
    settings.set_editor_property("exclude_values_outside_input_range", False)


def _configure_spawn_roll_noise(node, output_attr, seed):
    settings = node.get_settings()
    _selector_import(settings, "output_target", output_attr)
    try:
        settings.set_editor_property("mode", unreal.PCGAttributeNoiseMode.SET)
        settings.set_editor_property("noise_min", 0.0)
        settings.set_editor_property("noise_max", 1.0)
        settings.set_editor_property("invert_source", False)
        settings.set_editor_property("clamp_result", True)
        settings.set_editor_property("seed", int(seed))
    except Exception:
        pass


def _configure_probability_filter(node, spawn_roll_attr):
    settings = node.get_settings()
    settings.set_editor_property(
        "target_attribute",
        _selector(spawn_roll_attr, unreal.PCGAttributePropertyInputSelector),
    )
    settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.LESSER_OR_EQUAL)
    settings.set_editor_property("use_constant_threshold", False)
    settings.set_editor_property("use_spatial_query", False)
    settings.set_editor_property("generate_output_data_even_if_empty", True)
    try:
        settings.set_editor_property("warn_on_data_missing_attribute", False)
    except Exception:
        pass


def _configure_copy_attr(node, source_attr, target_attr):
    settings = node.get_settings()
    settings.set_editor_property("copy_all_attributes", False)
    settings.set_editor_property("copy_all_domains", False)
    _selector_import(settings, "input_source", source_attr)
    _selector_import(settings, "output_target", target_attr)


def _configure_transform(node, kind, offset_min, offset_max):
    settings = node.get_settings()
    settings.set_editor_property("absolute_offset", False)
    settings.set_editor_property("absolute_rotation", False)
    settings.set_editor_property("absolute_scale", False)
    settings.set_editor_property("uniform_scale", True)
    settings.set_editor_property("offset_min", unreal.Vector(*[float(value) for value in offset_min]))
    settings.set_editor_property("offset_max", unreal.Vector(*[float(value) for value in offset_max]))
    settings.set_editor_property("rotation_min", _make_rotator(0.0, 0.0, 0.0))
    settings.set_editor_property("rotation_max", _make_rotator(0.0, 359.0, 0.0))
    if kind == "tree":
        settings.set_editor_property("scale_min", unreal.Vector(0.88, 0.88, 0.92))
        settings.set_editor_property("scale_max", unreal.Vector(1.18, 1.18, 1.12))
    elif kind == "rock":
        settings.set_editor_property("scale_min", unreal.Vector(0.42, 0.42, 0.36))
        settings.set_editor_property("scale_max", unreal.Vector(0.9, 0.9, 0.72))
    else:
        settings.set_editor_property("scale_min", unreal.Vector(0.74, 0.74, 0.86))
        settings.set_editor_property("scale_max", unreal.Vector(1.32, 1.32, 1.14))
    settings.set_editor_property("recompute_seed", True)


def _configure_overlap_bounds(node, extents):
    settings = node.get_settings()
    x, y, z = [float(value) for value in extents]
    settings.set_editor_property("mode", unreal.PCGBoundsModifierMode.SET)
    settings.set_editor_property("bounds_min", unreal.Vector(-x, -y, -z))
    settings.set_editor_property("bounds_max", unreal.Vector(x, y, z))
    settings.set_editor_property("affect_steepness", True)
    settings.set_editor_property("steepness", 1.0)


def _configure_self_pruning(node, pruning_type, seed):
    settings = node.get_settings()
    params = settings.get_editor_property("parameters")
    params.set_editor_property("pruning_type", pruning_type)
    params.set_editor_property("radius_similarity_factor", 0.0)
    params.set_editor_property("randomized_pruning", True)
    params.set_editor_property("use_collision_attribute", False)
    settings.set_editor_property("parameters", params)
    try:
        settings.set_editor_property("seed", int(seed))
    except Exception:
        pass


def _configure_by_attribute_spawner(node, use_material_override=False):
    settings = node.get_settings()
    settings.set_editor_property("allow_descriptor_changes", True)
    settings.set_mesh_selector_type(unreal.PCGMeshSelectorByAttribute.static_class())
    params = settings.get_editor_property("mesh_selector_parameters")
    params.set_editor_property("attribute_name", DYNAMIC_MESH_ATTR)
    params.set_editor_property("use_attribute_material_overrides", bool(use_material_override))
    if use_material_override:
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


def _category_branch(graph, nodes, edges, spec, x, y, defer_spawn=False):
    remap = _add_node(graph, unreal.PCGDensityRemapSettings, spec["name"] + " gradient density scale", x, y)
    roll = _add_node(graph, unreal.PCGAttributeNoiseSettings, spec["name"] + " spawn roll", x + 320, y)
    probability_filter = _add_node(
        graph,
        unreal.PCGAttributeFilteringSettings,
        spec["name"] + " density probability filter",
        x + 640,
        y,
    )
    copy_mesh = _add_node(graph, unreal.PCGCopyAttributesSettings, spec["name"] + " mesh attr", x + 960, y)
    x_after_mesh = x + 1280
    copy_material = None
    if spec["kind"] == "grass":
        copy_material = _add_node(graph, unreal.PCGCopyAttributesSettings, spec["name"] + " material attr", x_after_mesh, y)
        x_after_mesh += 320
    transform = _add_node(graph, unreal.PCGTransformPointsSettings, spec["name"] + " jitter/yaw/scale", x_after_mesh, y)
    bounds = _add_node(graph, unreal.PCGBoundsModifierSettings, spec["name"] + " overlap bounds", x_after_mesh + 320, y)
    grass_prune = None
    x_after_bounds = x_after_mesh + 640
    if spec["kind"] == "grass":
        grass_prune = _add_node(graph, unreal.PCGSelfPruningSettings, spec["name"] + " loose self overlap prune", x_after_bounds, y)
        x_after_bounds += 320
    road_distance = _add_node(graph, unreal.PCGDistanceSettings, spec["name"] + " external road distance", x_after_bounds, y - 80)
    road_filter = _add_node(graph, unreal.PCGAttributeFilteringSettings, spec["name"] + " road clearance filter", x_after_bounds + 320, y - 80)
    select = _add_node(graph, unreal.PCGBooleanSelectSettings, spec["name"] + " optional road cut", x_after_bounds + 640, y)
    spawn = None if defer_spawn else _add_node(graph, unreal.PCGStaticMeshSpawnerSettings, spec["name"] + " spawn", x_after_bounds + 960, y)

    default_scale = GRID_GRADIENT_DEFAULTS[spec["density_scale_property"]]
    _configure_category_density_remap(remap, default_scale)
    _configure_spawn_roll_noise(roll, spec["spawn_roll_attr"], spec["spawn_roll_seed"])
    _configure_probability_filter(probability_filter, spec["spawn_roll_attr"])
    _configure_copy_attr(copy_mesh, spec["source_attr"], DYNAMIC_MESH_ATTR)
    if copy_material:
        _configure_copy_attr(copy_material, "GrassMaterialOverride", DYNAMIC_MATERIAL_SLOT0_ATTR)
    _configure_transform(transform, spec["kind"], spec["offset_min"], spec["offset_max"])
    _configure_overlap_bounds(bounds, spec["overlap_extents"])
    if grass_prune:
        _configure_self_pruning(grass_prune, unreal.PCGSelfPruningType.ALL_EQUAL, 6132047)
    _configure_distance(road_distance)
    _configure_road_filter(road_filter)
    if spawn:
        _configure_by_attribute_spawner(spawn, use_material_override=(spec["kind"] == "grass"))

    edges.extend(
        [
            _add_edge(
                graph,
                nodes["width_filter"],
                remap,
                "Out",
                "In",
            ),
            _add_edge(graph, nodes[spec["density_scale_node"]], remap, "Out", "OutRangeMin"),
            _add_edge(graph, remap, roll, "Out", "In"),
            _add_edge(graph, roll, probability_filter, "Out", "In"),
            _add_edge(graph, roll, probability_filter, "Out", "Filter"),
            _add_edge(graph, probability_filter, copy_mesh, "InsideFilter", "Target"),
            _add_edge(graph, nodes[spec["mesh_node"]], copy_mesh, "Out", "Source"),
        ]
    )
    if copy_material:
        edges.extend(
            [
                _add_edge(graph, copy_mesh, copy_material, "Out", "Target"),
                _add_edge(graph, nodes["grass_material"], copy_material, "Out", "Source"),
                _add_edge(graph, copy_material, transform, "Out", "In"),
            ]
        )
        branch_nodes = [remap, roll, probability_filter, copy_mesh, copy_material, transform, bounds, road_distance, road_filter, select]
    else:
        edges.append(_add_edge(graph, copy_mesh, transform, "Out", "In"))
        branch_nodes = [remap, roll, probability_filter, copy_mesh, transform, bounds, road_distance, road_filter, select]
    if grass_prune:
        branch_nodes.append(grass_prune)
    if spawn:
        branch_nodes.append(spawn)
    branch_input_to_road = grass_prune if grass_prune else bounds
    edges.extend(
        [
            _add_edge(graph, transform, bounds, "Out", "In"),
            _add_edge(graph, branch_input_to_road, road_distance, "Out", "Source"),
            _add_edge(graph, nodes["road_reference_points"], road_distance, "Out", "Target"),
            _add_edge(graph, road_distance, road_filter, "Out", "In"),
            _add_edge(graph, branch_input_to_road, select, "Out", "Input A"),
            _add_edge(graph, road_filter, select, "InsideFilter", "Input B"),
            _add_edge(graph, nodes["enable_road_clearance"], select, "Out", "bUseInputB"),
        ]
    )
    if grass_prune:
        edges.append(_add_edge(graph, bounds, grass_prune, "Out", "In"))
    if spawn:
        edges.extend(
            [
                _add_edge(graph, select, spawn, "Out", "In"),
                _add_edge(graph, spawn, graph.get_output_node(), "Out", "Out"),
            ]
        )
    return {"nodes": branch_nodes, "output": select}


def _create_or_update_graph():
    unreal.EditorAssetLibrary.make_directory(GRAPH_FOLDER)
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
        graph.remove_node(node)

    nodes = {
        "spline": _add_node(graph, unreal.PCGGetSplineSettings, "Get Candidate Source Spline", -1500, -360),
        "spline_reference_points": _add_node(graph, unreal.PCGSplineSamplerSettings, "Sample Source Spline Reference Points", -1160, -360),
        "grid_points": _add_node(graph, unreal.PCGCreatePointsGridSettings, "Create Local Ecosystem Candidate Grid", -1160, 0),
        "grid_scale_normalize": _add_node(graph, unreal.PCGTransformPointsSettings, "Normalize Ecosystem Grid Point Scale", -520, 0),
        "spline_distance": _add_node(graph, unreal.PCGDistanceSettings, "Distance To Source Spline", 460, 0),
        "width_filter": _add_node(graph, unreal.PCGDensityFilterSettings, "Clip To Ecosystem Width", 780, 0),
        "road_spline": _add_node(graph, unreal.PCGGetSplineSettings, "Get Optional External Road Clearance Spline", -1500, 360),
        "road_reference_points": _add_node(graph, unreal.PCGSplineSamplerSettings, "Sample External Road Clearance Reference Points", -1160, 360),
        "grid_extents": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor EcosystemGridExtents", -1500, -900),
        "grid_cell_size": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor EcosystemGridCellSize", -1500, -720),
        "ecosystem_width": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor EcosystemWidthCm", -1500, -540),
        "grass_mesh": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor GrassMeshOverride", -1160, -1140),
        "grass_material": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor GrassMaterialOverride", -1160, -1320),
        "tree_mesh": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor TreeMeshOverride", -1160, -960),
        "rock_mesh": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor RockMeshOverride", -1160, -780),
        "enable_road_clearance": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor EnableExternalRoadClearance", -1160, -600),
        "grass_density_scale": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor EcosystemGrassSpawnRatio", -820, -1140),
        "tree_density_scale": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor EcosystemTreeSpawnRatio", -820, -960),
        "rock_density_scale": _add_node(graph, unreal.PCGGetActorPropertySettings, "Get Actor EcosystemRockSpawnRatio", -820, -780),
        "hard_overlap_merge": _add_node(graph, unreal.PCGMergeSettings, "Merge Tree And Rock Candidates", 1980, 60),
        "hard_overlap_prune": _add_node(graph, unreal.PCGSelfPruningSettings, "Tree/Rock hard overlap prune", 2300, 60),
        "hard_overlap_spawn": _add_node(graph, unreal.PCGStaticMeshSpawnerSettings, "Tree/Rock non-overlap spawn", 2620, 60),
    }
    _configure_get_self_spline(nodes["spline"])
    _configure_sampler(nodes["spline_reference_points"], 120.0)
    _configure_grid(nodes["grid_points"])
    _configure_scale_normalize(nodes["grid_scale_normalize"])
    _configure_gradient_distance(nodes["spline_distance"])
    _configure_width_filter(nodes["width_filter"])
    _configure_get_external_road_spline(nodes["road_spline"])
    _configure_road_reference_sampler(nodes["road_reference_points"])
    _configure_get_actor_property(nodes["grid_extents"], "EcosystemGridExtents", "EcosystemGridExtents")
    _configure_get_actor_property(nodes["grid_cell_size"], "EcosystemGridCellSize", "EcosystemGridCellSize")
    _configure_get_actor_property(nodes["ecosystem_width"], "EcosystemWidthCm", "EcosystemWidthCm")
    _configure_get_actor_property(nodes["grass_mesh"], "GrassMeshOverride", "GrassMeshOverride")
    _configure_get_actor_property(nodes["grass_material"], "GrassMaterialOverride", "GrassMaterialOverride")
    _configure_get_actor_property(nodes["tree_mesh"], "TreeMeshOverride", "TreeMeshOverride")
    _configure_get_actor_property(nodes["rock_mesh"], "RockMeshOverride", "RockMeshOverride")
    _configure_get_actor_property(nodes["enable_road_clearance"], "EnableExternalRoadClearance", "EnableExternalRoadClearance")
    _configure_get_actor_property(nodes["grass_density_scale"], "EcosystemGrassSpawnRatio", "EcosystemGrassSpawnRatio")
    _configure_get_actor_property(nodes["tree_density_scale"], "EcosystemTreeSpawnRatio", "EcosystemTreeSpawnRatio")
    _configure_get_actor_property(nodes["rock_density_scale"], "EcosystemRockSpawnRatio", "EcosystemRockSpawnRatio")
    _configure_self_pruning(nodes["hard_overlap_prune"], unreal.PCGSelfPruningType.LARGE_TO_SMALL, 6132048)
    _configure_by_attribute_spawner(nodes["hard_overlap_spawn"], use_material_override=False)

    edges = [
        _add_edge(graph, nodes["spline"], nodes["spline_reference_points"], "Out", "Spline"),
        _add_edge(graph, nodes["grid_extents"], nodes["grid_points"], "Out", "GridExtents"),
        _add_edge(graph, nodes["grid_cell_size"], nodes["grid_points"], "Out", "CellSize"),
        _add_edge(graph, nodes["grid_points"], nodes["grid_scale_normalize"], "Out", "In"),
        _add_edge(graph, nodes["grid_scale_normalize"], nodes["spline_distance"], "Out", "Source"),
        _add_edge(graph, nodes["spline_reference_points"], nodes["spline_distance"], "Out", "Target"),
        _add_edge(graph, nodes["ecosystem_width"], nodes["spline_distance"], "Out", "MaximumDistance"),
        _add_edge(graph, nodes["spline_distance"], nodes["width_filter"], "Out", "In"),
        _add_edge(graph, nodes["road_spline"], nodes["road_reference_points"], "Out", "Spline"),
    ]
    all_nodes = list(nodes.values())
    specs = CATEGORY_SPECS
    for index, spec in enumerate(specs):
        branch = _category_branch(graph, nodes, edges, spec, -160, -360 + index * 360, defer_spawn=(spec["kind"] in ("tree", "rock")))
        all_nodes.extend(branch["nodes"])
        if spec["kind"] in ("tree", "rock"):
            edges.append(_add_edge(graph, branch["output"], nodes["hard_overlap_merge"], "Out", "In"))
    edges.extend(
        [
            _add_edge(graph, nodes["hard_overlap_merge"], nodes["hard_overlap_prune"], "Out", "In"),
            _add_edge(graph, nodes["hard_overlap_prune"], nodes["hard_overlap_spawn"], "Out", "In"),
            _add_edge(graph, nodes["hard_overlap_spawn"], graph.get_output_node(), "Out", "Out"),
        ]
    )

    try:
        graph.description = (
            "Production-candidate spline ecosystem graph. It creates a local "
            "candidate grid around the actor and computes each point's "
            "distance back to the tagged source spline. This keeps open "
            "two-point and multi-point splines useful for forest/guide/fence/"
            "road intent while producing a filled ecosystem band without the "
            "UE 5.7 Duplicate Point relative-rotation crash path. "
            "EcosystemGridExtents controls candidate volume bounds, "
            "EcosystemGridCellSize controls candidate spacing, "
            "EcosystemWidthCm controls the falloff width, and per-category "
            "spawn ratios scale probability after the spline-distance "
            "gradient. Spawn meshes/materials are still read from BP actor "
            "properties. Grass uses a loose self-prune pass to prevent nearly "
            "identical clumps while still allowing visual overlap; tree and "
            "rock candidates are merged and hard-pruned before spawning so "
            "large props do not overlap each other. When "
            "EnableExternalRoadClearance is true, a separate tagged external "
            "spline can cut a road/guide corridor without making this graph "
            "road-specific."
        )
        graph.get_input_node().set_node_position(-1800, 0)
        graph.get_output_node().set_node_position(2860, 520)
    except Exception:
        pass
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(graph, False))
    return {
        "graph": GRAPH_OBJECT,
        "created": created,
        "saved": saved,
        "graph_model": "spline_local_grid_density_gradient",
        "grid_extents": list(GRID_GRADIENT_DEFAULTS["EcosystemGridExtents"]),
        "grid_cell_size": list(GRID_GRADIENT_DEFAULTS["EcosystemGridCellSize"]),
        "category_count": len(specs),
        "edge_errors": [edge for edge in edges if not edge.get("ok")],
        "edges": edges,
        "nodes": [_node_summary(node) for node in all_nodes],
    }


def _delete_existing_validation_actor():
    deleted = 0
    for actor in list(_all_level_actors()):
        if _actor_label(actor) in {
            VALIDATION_ACTOR_LABEL,
            ROAD_CLEARANCE_ACTOR_LABEL,
            LEGACY_ROADSIDE_VALIDATION_ACTOR_LABEL,
        }:
            for component in actor.get_components_by_class(unreal.PCGComponent):
                try:
                    component.cleanup(True)
                except Exception:
                    pass
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted += 1
    return deleted


def _vector_delta(lhs, rhs):
    return unreal.Vector(
        float(lhs.x) - float(rhs.x),
        float(lhs.y) - float(rhs.y),
        float(lhs.z) - float(rhs.z),
    )


def _vector_scale(vector, scale):
    return unreal.Vector(
        float(vector.x) * float(scale),
        float(vector.y) * float(scale),
        float(vector.z) * float(scale),
    )


def _default_curve_tangent(points, index):
    count = len(points)
    if count < 2:
        return unreal.Vector(0.0, 0.0, 0.0)
    if index <= 0:
        delta = _vector_delta(points[1], points[0])
    elif index >= count - 1:
        delta = _vector_delta(points[index], points[index - 1])
    else:
        delta = _vector_scale(_vector_delta(points[index + 1], points[index - 1]), 0.5)
    return _vector_scale(delta, 0.5)


def _set_editable_curve_tangents(spline, coordinate_space):
    point_count = int(spline.get_number_of_spline_points())
    points = [
        spline.get_location_at_spline_point(index, coordinate_space)
        for index in range(point_count)
    ]
    point_type = getattr(unreal.SplinePointType, "CURVE_CUSTOM_TANGENT", unreal.SplinePointType.CURVE)
    changed = []
    for index in range(point_count):
        tangent = _default_curve_tangent(points, index)
        try:
            spline.set_spline_point_type(index, point_type, False)
        except Exception:
            pass
        try:
            spline.set_tangents_at_spline_point(index, tangent, tangent, coordinate_space, False)
        except Exception:
            try:
                spline.set_tangent_at_spline_point(index, tangent, coordinate_space, False)
            except Exception:
                pass
        changed.append(index)
    return changed


def _set_spline_points(actor):
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        raise RuntimeError("Candidate validation actor has no SplineComponent.")
    spline = splines[0]
    tags = list(spline.get_editor_property("component_tags"))
    if SPLINE_COMPONENT_TAG not in [str(tag) for tag in tags]:
        tags.append(unreal.Name(SPLINE_COMPONENT_TAG))
        spline.set_editor_property("component_tags", tags)
    while spline.get_number_of_spline_points() < 2:
        spline.add_spline_point(unreal.Vector(0.0, 0.0, 0.0), unreal.SplineCoordinateSpace.LOCAL, False)
    while spline.get_number_of_spline_points() > 2:
        spline.remove_spline_point(spline.get_number_of_spline_points() - 1, False)
    spline.set_location_at_spline_point(0, unreal.Vector(-4200.0, 0.0, 0.0), unreal.SplineCoordinateSpace.LOCAL, False)
    spline.set_location_at_spline_point(1, unreal.Vector(4200.0, 0.0, 0.0), unreal.SplineCoordinateSpace.LOCAL, False)
    width = float(GRID_GRADIENT_DEFAULTS["EcosystemWidthCm"])
    for index in range(spline.get_number_of_spline_points()):
        try:
            spline.set_scale_at_spline_point(index, unreal.Vector(1.0, width, 1.0), False)
        except Exception:
            pass
    _set_editable_curve_tangents(spline, unreal.SplineCoordinateSpace.LOCAL)
    spline.set_closed_loop(False, False)
    spline.update_spline()
    return spline


def _road_spline(actor):
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        raise RuntimeError("External road actor has no SplineComponent.")
    for spline in splines:
        if spline.get_name() == "Road_SourceSpline":
            return spline
    return splines[0]


def _tag_external_road_spline(spline):
    tags = list(spline.get_editor_property("component_tags"))
    tag_names = {str(tag) for tag in tags}
    if ROAD_CLEARANCE_SPLINE_TAG not in tag_names:
        tags.append(unreal.Name(ROAD_CLEARANCE_SPLINE_TAG))
        spline.set_editor_property("component_tags", tags)


def _set_external_road_points(actor):
    spline = _road_spline(actor)
    _tag_external_road_spline(spline)
    while spline.get_number_of_spline_points() < 2:
        spline.add_spline_point(unreal.Vector(0.0, 0.0, 0.0), unreal.SplineCoordinateSpace.WORLD, False)
    while spline.get_number_of_spline_points() > 2:
        spline.remove_spline_point(spline.get_number_of_spline_points() - 1, False)
    spline.set_location_at_spline_point(0, unreal.Vector(6000.0, 16600.0, 0.0), unreal.SplineCoordinateSpace.WORLD, False)
    spline.set_location_at_spline_point(1, unreal.Vector(6000.0, 21400.0, 0.0), unreal.SplineCoordinateSpace.WORLD, False)
    _set_editable_curve_tangents(spline, unreal.SplineCoordinateSpace.WORLD)
    spline.set_closed_loop(False, False)
    spline.update_spline()
    return spline


def _spawn_external_road_actor():
    actor_class = unreal.load_object(None, CANDIDATE_CLASS_PATH)
    if not actor_class:
        actor_class = unreal.EditorAssetLibrary.load_blueprint_class(CANDIDATE_BP_OBJECT)
    if not actor_class:
        raise RuntimeError("Missing candidate class for external spline holder: " + CANDIDATE_CLASS_PATH)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        unreal.Vector(0.0, 0.0, 0.0),
        _make_rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn external road clearance actor.")
    actor.set_actor_label(ROAD_CLEARANCE_ACTOR_LABEL)
    actor.set_editor_property("tags", [unreal.Name(ROAD_CLEARANCE_SPLINE_TAG), unreal.Name("MCPValidation")])
    for component in actor.get_components_by_class(unreal.PCGComponent):
        try:
            component.cleanup(True)
            component.deactivate()
        except Exception:
            pass
    spline = _set_external_road_points(actor)
    return {
        "actor": _actor_label(actor),
        "spline_component": spline.get_name(),
        "spline_tag": ROAD_CLEARANCE_SPLINE_TAG,
        "spline_closed_loop": bool(spline.is_closed_loop()),
        "spline_point_count": int(spline.get_number_of_spline_points()),
        "spline_length": round(float(spline.get_spline_length()), 2),
    }


def _spawn_validation_actor(graph):
    blueprint_update = _ensure_candidate_variables()
    actor_class = unreal.load_object(None, CANDIDATE_CLASS_PATH)
    if not actor_class:
        actor_class = unreal.EditorAssetLibrary.load_blueprint_class(CANDIDATE_BP_OBJECT)
    if not actor_class:
        raise RuntimeError("Missing candidate class: " + CANDIDATE_CLASS_PATH)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        unreal.Vector(6000.0, 19000.0, 0.0),
        _make_rotator(0.0, 28.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn validation candidate actor.")
    actor.set_actor_label(VALIDATION_ACTOR_LABEL)
    actor.set_editor_property("tags", [unreal.Name(VALIDATION_ACTOR_TAG), unreal.Name("MCPValidation")])

    for prop, value in {
        "PresetType": 6,
        "DensityOverride": 2,
        "TreeOverride": 3,
        "UseGrassMeshOverride": True,
        "UseTreeMeshOverride": True,
        "UseRockMeshOverride": True,
        "EnableExternalRoadClearance": bool(ENABLE_EXTERNAL_ROAD_VALIDATION),
    }.items():
        try:
            actor.set_editor_property(prop, value)
        except Exception:
            pass
    for prop, value in GRID_GRADIENT_DEFAULTS.items():
        try:
            if isinstance(value, tuple):
                actor.set_editor_property(prop, unreal.Vector(*[float(component) for component in value]))
            elif isinstance(value, int):
                actor.set_editor_property(prop, int(value))
            else:
                actor.set_editor_property(prop, float(value))
        except Exception:
            pass
    for prop, path in {
        "GrassMeshOverride": GRASS_MESH,
        "TreeMeshOverride": TREE_MESH,
        "RockMeshOverride": ROCK_MESH,
        "GrassMaterialOverride": GRASS_MATERIAL,
    }.items():
        asset = _load_asset(path)
        if not asset:
            raise RuntimeError("Missing asset for {}: {}".format(prop, path))
        actor.set_editor_property(prop, asset)

    spline = _set_spline_points(actor)
    selector_script = os.path.join(
        unreal.Paths.project_dir(),
        "Plugins",
        "CustomTools",
        "Content",
        "Python",
        "ArtScripts",
        "CubelessEDPCG.py",
    )
    selector_namespace = runpy.run_path(selector_script, run_name="cubeless_edpcg_spline_ecosystem_validation")
    selector_result = selector_namespace["apply_production_candidate_selector"](actor, force=True)
    spline = _set_spline_points(actor)

    style_component = None
    for component in actor.get_components_by_class(unreal.PCGComponent):
        if component.get_name().startswith("PCG_Style"):
            style_component = component
    if not style_component:
        raise RuntimeError("Candidate validation actor is missing PCG_Style component.")
    try:
        style_component.activate(True)
        style_component.generate(True)
        style_component.generate(True)
    except Exception:
        pass
    return {
        "actor": _actor_label(actor),
        "graph": GRAPH_OBJECT,
        "blueprint_update": blueprint_update,
        "selector_result": selector_result,
        "spline_closed_loop": bool(spline.is_closed_loop()),
        "spline_point_count": int(spline.get_number_of_spline_points()),
        "spline_length": round(float(spline.get_spline_length()), 2),
        "grass_mesh": GRASS_MESH,
        "tree_mesh": TREE_MESH,
        "rock_mesh": ROCK_MESH,
        "grass_material": GRASS_MATERIAL,
        "external_road_clearance_enabled": bool(ENABLE_EXTERNAL_ROAD_VALIDATION),
        "active_component": style_component.get_name(),
    }


def main():
    world = _load_level()
    deleted = _delete_existing_validation_actor()
    graph_update = _create_or_update_graph()
    graph = _load_asset(GRAPH_OBJECT)
    external_road_actor = _spawn_external_road_actor() if ENABLE_EXTERNAL_ROAD_VALIDATION else None
    validation_actor = _spawn_validation_actor(graph)
    result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": _object_path(world),
        "deleted_existing_validation_actors": deleted,
        "graph_update": graph_update,
        "external_road_actor": external_road_actor,
        "validation_actor": validation_actor,
        "external_road_validation_enabled": bool(ENABLE_EXTERNAL_ROAD_VALIDATION),
        "blueprint_update": validation_actor.get("blueprint_update"),
    }
    print(json.dumps(result, ensure_ascii=False))


main()
"""


VALIDATE_CODE = r"""
import json
import math
import os
import time

import unreal


REPORT_NAME = "CubelessSplineEcosystemCandidateFalloff_Report.json"
VALIDATION_ACTOR_LABEL = "MCP_Cubeless_PCG_SplineEcosystemCandidate_Validation"
ROAD_CLEARANCE_ACTOR_LABEL = "MCP_Cubeless_PCG_ExternalRoadClearanceSpline_Validation"
ROAD_CLEARANCE_CM = 650.0
ENABLE_EXTERNAL_ROAD_VALIDATION = False
GRAPH_OBJECT = (
    "/Game/Cubeless/PCG/ProductionCandidates/Graphs/"
    "PCG_Cubeless_EcosystemCandidate_SplineEcosystemFalloff."
    "PCG_Cubeless_EcosystemCandidate_SplineEcosystemFalloff"
)
GRASS_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
    "SM_Grass_Medium01.SM_Grass_Medium01"
)
TREE_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_05.SM_Conifer_05"
)
ROCK_MESH = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Stones/Rocks/"
    "SM_SmallRock_01.SM_SmallRock_01"
)
GRASS_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_GrassMedium_ForestBalanced.MI_Cubeless_PCG_GrassMedium_ForestBalanced"
)


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


def _object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
        return _object_path(mesh)
    except Exception:
        return None


def _material_path(component, index=0):
    try:
        material = component.get_material(index)
        return _object_path(material)
    except Exception:
        return None


def _classify_component(component):
    text = ((component.get_name() or "") + " " + (_mesh_path(component) or "")).lower()
    if any(token in text for token in ("rock", "stone", "boulder")):
        return "rock"
    if any(token in text for token in ("tree", "pine", "spruce", "conifer", "trunk")):
        return "tree"
    if any(token in text for token in ("grass", "fern", "leaf", "foliage", "plant")):
        return "grass"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _instance_transform(component, index):
    return component.get_instance_transform(index, True)


def _instance_location(component, index):
    return _instance_transform(component, index).translation


def _instance_scale(component, index):
    try:
        return _instance_transform(component, index).scale3d
    except Exception:
        return unreal.Vector(1.0, 1.0, 1.0)


def _segment_distance_2d(point, start, end):
    px, py = point.x, point.y
    ax, ay = start.x, start.y
    bx, by = end.x, end.y
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 0.0001:
        return math.sqrt((px - ax) ** 2 + (py - ay) ** 2)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    cx = ax + dx * t
    cy = ay + dy * t
    return math.sqrt((px - cx) ** 2 + (py - cy) ** 2)


def _point_distance_2d(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _scaled_overlap_extents_2d(kind, scale):
    extents = OVERLAP_VALIDATION_EXTENTS.get(kind, (0.0, 0.0))
    return abs(float(extents[0]) * float(scale.x)), abs(float(extents[1]) * float(scale.y))


def _bounds_overlap_2d(a, b):
    ax, ay = _scaled_overlap_extents_2d(a["kind"], a["scale"])
    bx, by = _scaled_overlap_extents_2d(b["kind"], b["scale"])
    dx = abs(float(a["location"].x) - float(b["location"].x))
    dy = abs(float(a["location"].y) - float(b["location"].y))
    return dx < (ax + bx - 0.01) and dy < (ay + by - 0.01)


def _collect_overlap_stats(instances, kinds, mode):
    filtered = [row for row in instances if row["kind"] in kinds]
    min_distance = None
    violations = []
    for index, first in enumerate(filtered):
        for second in filtered[index + 1:]:
            if mode == "self" and first["kind"] != second["kind"]:
                continue
            if mode == "cross" and first["kind"] == second["kind"]:
                continue
            distance = _point_distance_2d(first["location"], second["location"])
            min_distance = distance if min_distance is None else min(min_distance, distance)
            if _bounds_overlap_2d(first, second):
                if len(violations) < 20:
                    violations.append({
                        "a_kind": first["kind"],
                        "b_kind": second["kind"],
                        "a_component": first["component"],
                        "b_component": second["component"],
                        "distance_2d": round(distance, 2),
                        "a_location": [
                            round(float(first["location"].x), 2),
                            round(float(first["location"].y), 2),
                            round(float(first["location"].z), 2),
                        ],
                        "b_location": [
                            round(float(second["location"].x), 2),
                            round(float(second["location"].y), 2),
                            round(float(second["location"].z), 2),
                        ],
                    })
    return {
        "count": len(violations),
        "samples": violations,
        "min_distance_2d": round(float(min_distance), 2) if min_distance is not None else None,
    }


def _spline_world_points(actor):
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    if not splines:
        return [], None
    spline = splines[0]
    points = []
    for index in range(spline.get_number_of_spline_points()):
        points.append(spline.get_location_at_spline_point(index, unreal.SplineCoordinateSpace.WORLD))
    return points, spline


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, REPORT_NAME)
    report["report_path"] = path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False))
    return path


actor = _find_actor(VALIDATION_ACTOR_LABEL)
if not actor:
    raise RuntimeError("Missing validation actor: " + VALIDATION_ACTOR_LABEL)
road_actor = _find_actor(ROAD_CLEARANCE_ACTOR_LABEL)
if ENABLE_EXTERNAL_ROAD_VALIDATION and not road_actor:
    raise RuntimeError("Missing external road clearance actor: " + ROAD_CLEARANCE_ACTOR_LABEL)

spline_points, spline = _spline_world_points(actor)
if len(spline_points) < 2:
    raise RuntimeError("Validation actor spline has fewer than 2 points.")
road_points, road_spline = _spline_world_points(road_actor) if road_actor else ([], None)
if ENABLE_EXTERNAL_ROAD_VALIDATION and len(road_points) < 2:
    raise RuntimeError("External road clearance spline has fewer than 2 points.")

counts = {
    "grass": {"center": 0, "inner": 0, "mid": 0, "far": 0, "total": 0},
    "tree": {"center": 0, "inner": 0, "mid": 0, "far": 0, "total": 0},
    "rock": {"center": 0, "inner": 0, "mid": 0, "far": 0, "total": 0},
    "other": {"total": 0},
}
mesh_sets = {"grass": set(), "tree": set(), "rock": set(), "other": set()}
material_sets = {"grass": set(), "tree": set(), "rock": set(), "other": set()}
height_ranges = {
    "grass": {"min_z": None, "max_z": None},
    "tree": {"min_z": None, "max_z": None},
    "rock": {"min_z": None, "max_z": None},
    "other": {"min_z": None, "max_z": None},
}
sample_rows = []
instances_by_kind = []
min_distance = None
max_distance = None
road_clearance_violations = 0
road_violation_samples = []
endpoint_radius_cm = 650.0
endpoint_counts = {
    "grass": {"start": 0, "end": 0},
    "tree": {"start": 0, "end": 0},
    "rock": {"start": 0, "end": 0},
}


def _update_height_range(kind, z):
    height_ranges.setdefault(kind, {"min_z": None, "max_z": None})
    current = height_ranges[kind]
    current["min_z"] = z if current["min_z"] is None else min(current["min_z"], z)
    current["max_z"] = z if current["max_z"] is None else max(current["max_z"], z)


for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
    kind = _classify_component(component)
    mesh = _mesh_path(component)
    material = _material_path(component)
    mesh_sets.setdefault(kind, set()).add(mesh)
    material_sets.setdefault(kind, set()).add(material)
    total = _instance_count(component)
    for index in range(total):
        location = _instance_location(component, index)
        scale = _instance_scale(component, index)
        if kind in ("grass", "tree", "rock"):
            instances_by_kind.append({
                "kind": kind,
                "component": component.get_name(),
                "location": location,
                "scale": scale,
            })
        _update_height_range(kind, float(location.z))
        distance = min(
            _segment_distance_2d(location, spline_points[seg_index], spline_points[seg_index + 1])
            for seg_index in range(len(spline_points) - 1)
        )
        if road_points and len(road_points) >= 2:
            road_distance = min(
                _segment_distance_2d(location, road_points[seg_index], road_points[seg_index + 1])
                for seg_index in range(len(road_points) - 1)
            )
        else:
            road_distance = 999999.0
        min_distance = distance if min_distance is None else min(min_distance, distance)
        max_distance = distance if max_distance is None else max(max_distance, distance)
        if kind in ("grass", "tree", "rock"):
            counts[kind]["total"] += 1
            if distance <= 350.0:
                counts[kind]["center"] += 1
            elif distance <= 900.0:
                counts[kind]["inner"] += 1
            elif distance <= 1800.0:
                counts[kind]["mid"] += 1
            elif distance <= 3000.0:
                counts[kind]["far"] += 1
            if _point_distance_2d(location, spline_points[0]) <= endpoint_radius_cm:
                endpoint_counts[kind]["start"] += 1
            if _point_distance_2d(location, spline_points[-1]) <= endpoint_radius_cm:
                endpoint_counts[kind]["end"] += 1
            if road_distance < ROAD_CLEARANCE_CM:
                road_clearance_violations += 1
                if len(road_violation_samples) < 20:
                    road_violation_samples.append({
                        "component": component.get_name(),
                        "kind": kind,
                        "road_distance": round(road_distance, 2),
                        "location": [round(float(location.x), 2), round(float(location.y), 2), round(float(location.z), 2)],
                    })
        else:
            counts["other"]["total"] += 1
        if len(sample_rows) < 40:
            sample_rows.append({
                "component": component.get_name(),
                "kind": kind,
                "mesh": mesh,
                "material": material,
                "distance_to_spline": round(distance, 2),
                "distance_to_external_road": round(road_distance, 2),
                "location_z": round(float(location.z), 2),
            })

grass_meshes = sorted(mesh for mesh in mesh_sets.get("grass", set()) if mesh)
tree_meshes = sorted(mesh for mesh in mesh_sets.get("tree", set()) if mesh)
rock_meshes = sorted(mesh for mesh in mesh_sets.get("rock", set()) if mesh)
grass_materials = sorted(material for material in material_sets.get("grass", set()) if material)
expected_surface_z = round(float(actor.get_actor_location().z), 2)
height_ranges_report = {
    kind: {
        key: (round(float(value), 2) if value is not None else None)
        for key, value in ranges.items()
    }
    for kind, ranges in height_ranges.items()
}
grass_overlap_stats = _collect_overlap_stats(instances_by_kind, {"grass"}, "self")
tree_overlap_stats = _collect_overlap_stats(instances_by_kind, {"tree"}, "self")
rock_overlap_stats = _collect_overlap_stats(instances_by_kind, {"rock"}, "self")
hard_prop_overlap_stats = _collect_overlap_stats(instances_by_kind, {"tree", "rock"}, "cross")
validation = {
    "actor": _actor_label(actor),
    "graph": GRAPH_OBJECT,
    "spline_closed_loop": bool(spline.is_closed_loop()),
    "spline_point_count": int(spline.get_number_of_spline_points()),
    "spline_length": round(float(spline.get_spline_length()), 2),
    "external_road_validation_enabled": bool(ENABLE_EXTERNAL_ROAD_VALIDATION),
    "external_road_actor": _actor_label(road_actor) if road_actor else None,
    "external_road_spline_closed_loop": bool(road_spline.is_closed_loop()) if road_spline else False,
    "external_road_spline_point_count": int(road_spline.get_number_of_spline_points()) if road_spline else 0,
    "external_road_spline_length": round(float(road_spline.get_spline_length()), 2) if road_spline else 0.0,
    "external_road_clearance_cm": ROAD_CLEARANCE_CM,
    "external_road_clearance_violations": road_clearance_violations,
    "external_road_violation_samples": road_violation_samples,
    "counts": counts,
    "grass_meshes": grass_meshes,
    "tree_meshes": tree_meshes,
    "rock_meshes": rock_meshes,
    "grass_materials": grass_materials,
    "expected_grass_mesh": GRASS_MESH,
    "expected_tree_mesh": TREE_MESH,
    "expected_rock_mesh": ROCK_MESH,
    "expected_grass_material": GRASS_MATERIAL,
    "expected_surface_z": expected_surface_z,
    "height_ranges": height_ranges_report,
    "overlap_policy": {
        "grass": "loose self-prune; partial visual overlap is allowed, near-identical bounds overlap is rejected",
        "tree": "hard self-prune; tree points must not overlap",
        "rock": "hard self-prune; rock points must not overlap",
        "tree_rock": "merged hard-prune; tree and rock prop bounds must not overlap each other",
        "validation_extents_xy_cm": OVERLAP_VALIDATION_EXTENTS,
        "grass_near_duplicate_tolerance_cm": GRASS_NEAR_DUPLICATE_TOLERANCE_CM,
    },
    "overlap_stats": {
        "grass": grass_overlap_stats,
        "tree": tree_overlap_stats,
        "rock": rock_overlap_stats,
        "tree_rock": hard_prop_overlap_stats,
    },
    "endpoint_radius_cm": endpoint_radius_cm,
    "endpoint_counts": endpoint_counts,
    "min_distance_to_spline": round(min_distance or 0.0, 2),
    "max_distance_to_spline": round(max_distance or 0.0, 2),
    "samples": sample_rows,
}
validation["grass_falloff_pass"] = (
    (counts["grass"]["center"] + counts["grass"]["inner"]) > counts["grass"]["mid"] >= counts["grass"]["far"]
    and counts["grass"]["far"] <= max(30, int(counts["grass"]["total"] * 0.22))
)
validation["tree_falloff_pass"] = (
    (counts["tree"]["center"] + counts["tree"]["inner"]) > counts["tree"]["far"]
    and counts["tree"]["far"] <= max(5, int(counts["tree"]["total"] * 0.35))
)
validation["rock_falloff_pass"] = (
    (counts["rock"]["center"] + counts["rock"]["inner"]) > counts["rock"]["far"]
    and counts["rock"]["far"] <= max(8, int(counts["rock"]["total"] * 0.35))
)
validation["endpoint_cluster_pass"] = (
    endpoint_counts["tree"]["start"] <= max(4, int(counts["tree"]["total"] * 0.2))
    and endpoint_counts["tree"]["end"] <= max(4, int(counts["tree"]["total"] * 0.2))
)
validation["external_road_clearance_pass"] = (not ENABLE_EXTERNAL_ROAD_VALIDATION) or road_clearance_violations == 0
validation["mesh_override_pass"] = (
    grass_meshes == [GRASS_MESH]
    and tree_meshes == [TREE_MESH]
    and rock_meshes == [ROCK_MESH]
)
validation["material_override_pass"] = grass_materials == [GRASS_MATERIAL]
validation["grass_self_overlap_pass"] = grass_overlap_stats["count"] == 0
validation["tree_self_overlap_pass"] = tree_overlap_stats["count"] == 0
validation["rock_self_overlap_pass"] = rock_overlap_stats["count"] == 0
validation["tree_rock_overlap_pass"] = hard_prop_overlap_stats["count"] == 0
validation["dense_grass_pass"] = counts["grass"]["total"] >= 500
validation["low_density_grass_spawn_pass"] = counts["grass"]["total"] >= 20
validation["rock_spawn_pass"] = counts["rock"]["total"] >= 1
validation["tree_spawn_pass"] = counts["tree"]["total"] >= 1
validation["surface_height_pass"] = (
    height_ranges_report["grass"]["min_z"] is not None
    and height_ranges_report["tree"]["min_z"] is not None
    and height_ranges_report["rock"]["min_z"] is not None
    and height_ranges_report["grass"]["min_z"] >= expected_surface_z - 25.0
    and height_ranges_report["tree"]["min_z"] >= expected_surface_z - 25.0
    and height_ranges_report["rock"]["min_z"] >= expected_surface_z - 25.0
    and height_ranges_report["grass"]["max_z"] <= expected_surface_z + 25.0
    and height_ranges_report["tree"]["max_z"] <= expected_surface_z + 25.0
    and height_ranges_report["rock"]["max_z"] <= expected_surface_z + 25.0
)
validation["pass"] = (
    not validation["spline_closed_loop"]
    and validation["spline_point_count"] == 2
    and (not ENABLE_EXTERNAL_ROAD_VALIDATION or not validation["external_road_spline_closed_loop"])
    and (not ENABLE_EXTERNAL_ROAD_VALIDATION or validation["external_road_spline_point_count"] == 2)
    and validation["grass_falloff_pass"]
    and validation["tree_falloff_pass"]
    and validation["rock_falloff_pass"]
    and validation["endpoint_cluster_pass"]
    and validation["external_road_clearance_pass"]
    and validation["mesh_override_pass"]
    and validation["material_override_pass"]
    and validation["grass_self_overlap_pass"]
    and validation["tree_self_overlap_pass"]
    and validation["rock_self_overlap_pass"]
    and validation["tree_rock_overlap_pass"]
    and validation["low_density_grass_spawn_pass"]
    and validation["rock_spawn_pass"]
    and validation["tree_spawn_pass"]
    and validation["surface_height_pass"]
)

dirty_content = []
dirty_maps = []
try:
    dirty_content = [package.get_name() for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    dirty_maps = [package.get_name() for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
except Exception:
    pass

report = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "mode": "candidate_actor_spline_ecosystem_falloff_validation",
    "policy": {
        "ecosystem_candidate_role": "actor-local candidate grid volume with continuous spline-distance density gradient for grass/tree/rock",
        "fence_role": "separate BP_Cubeless_PCG_FenceSourceRuntime / PCG_Cubeless_FenceRuntime_Native path",
        "mesh_override_rule": "GrassMeshOverride, TreeMeshOverride, and RockMeshOverride are read from BP actor properties",
        "open_2_point_spline": "valid for ecosystem guide/fence/road linear intent",
        "surface_height_rule": "ecosystem guide spline world height is the spawn surface for this candidate",
        "start_end_rule": "grid candidate generation should not add extra endpoint cap clusters beyond the open guide spline length",
        "overlap_rule": "grass allows some visual overlap but rejects near-identical self overlap; tree and rock candidates are hard-pruned together so tree/tree, rock/rock, and tree/rock prop bounds do not overlap",
        "external_road_rule": "road clearing is optional and owned by a separate tagged external spline",
        "level_save_attempted": False,
    },
    "validation": validation,
    "dirty_content_packages": dirty_content,
    "dirty_map_packages": dirty_maps,
}
report["pass"] = bool(validation["pass"])
_write_report(report)
"""


def _extract_log_json(response: dict[str, Any]) -> dict[str, Any] | None:
    logs = response.get("result", {}).get("logs", [])
    for entry in reversed(logs):
        output = str(entry.get("output", "")).strip()
        if not output.startswith("{"):
            continue
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            continue
    return None


def _send_execute(connection: UnrealConnection, code: str) -> dict[str, Any]:
    response = connection.send_command("execute_python", {"code": code, "mode": "ExecuteFile"})
    if not isinstance(response, dict) or response.get("status") != "success":
        raise RuntimeError(json.dumps(response, ensure_ascii=False, indent=2))
    return response


REFRESH_FALLBACK_CODE = r"""
import json
import time

import unreal


ACTOR_LABEL = "MCP_Cubeless_PCG_SplineEcosystemCandidate_Validation"
GENERATE = __GENERATE__


def _all_level_actors():
    try:
        return unreal.EditorLevelLibrary.get_all_level_actors()
    except Exception:
        subsystem_cls = getattr(unreal, "UnrealEditorSubsystem", None)
        if subsystem_cls:
            subsystem = unreal.get_editor_subsystem(subsystem_cls)
            world = subsystem.get_editor_world() if subsystem else None
            if world:
                return list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor))
    return []


def _actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def _point_count_for_component(component):
    total_points = 0
    try:
        collection = component.get_generated_graph_output()
        for item in collection.get_editor_property("tagged_data"):
            data = item.get_editor_property("data").get_editor_property("data")
            if data and hasattr(data, "get_num_points"):
                total_points += int(data.get_num_points())
    except Exception as exc:
        return total_points, str(exc)
    return total_points, None


actor = next((candidate for candidate in _all_level_actors() if _actor_label(candidate) == ACTOR_LABEL), None)
rows = []
if actor:
    for component in actor.get_components_by_class(unreal.PCGComponent):
        if not component.get_name().startswith("PCG_Style"):
            continue
        row = {
            "component": component.get_name(),
            "generated": False,
            "managed_resource_count": 0,
        }
        if GENERATE:
            try:
                component.activate(True)
                component.generate(True)
                component.generate(True)
                row["generated"] = True
            except Exception as exc:
                row["generate_error"] = str(exc)
        point_count, point_count_error = _point_count_for_component(component)
        row["managed_resource_count"] = int(point_count)
        if point_count_error:
            row["point_count_error"] = point_count_error
        rows.append(row)

payload = {
    "fallback": "execute_python",
    "wait_completed": True,
    "wait_timed_out": False,
    "actor": ACTOR_LABEL if actor else None,
    "components": rows,
    "initial_components": rows,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
"""


def _refresh_candidate(connection: UnrealConnection, generate: bool) -> dict[str, Any]:
    response = connection.send_command(
        "refresh_pcg_components",
        {
            "actor_label": "MCP_Cubeless_PCG_SplineEcosystemCandidate_Validation",
            "cleanup": False,
            "notify_properties_changed": bool(generate),
            "refresh": bool(generate),
            "generate": bool(generate),
            "force": bool(generate),
            "wait_until_complete": True,
            "min_managed_resource_count": 1,
            "max_components": 1,
        },
    )
    if isinstance(response, dict) and response.get("status") == "success":
        return response
    error = str(response.get("error", "")) if isinstance(response, dict) else ""
    if "Unknown command" not in error:
        raise RuntimeError(json.dumps(response, ensure_ascii=False, indent=2))
    fallback_code = REFRESH_FALLBACK_CODE.replace("__GENERATE__", "True" if generate else "False")
    fallback_response = _send_execute(connection, fallback_code)
    fallback_result = _extract_log_json(fallback_response) or {}
    return {"status": "success", "result": fallback_result}


def main() -> int:
    connection = UnrealConnection()
    setup_response = _send_execute(connection, SETUP_CODE)
    setup = _extract_log_json(setup_response) or {}

    refresh = _refresh_candidate(connection, generate=True)
    for _ in range(20):
        result = refresh.get("result", {})
        if result.get("wait_completed") and not result.get("wait_timed_out"):
            components = result.get("components") or result.get("initial_components") or []
            if components and int(components[0].get("managed_resource_count") or 0) > 0:
                break
        time.sleep(0.25)
        refresh = _refresh_candidate(connection, generate=False)

    validate_response = _send_execute(connection, VALIDATE_CODE)
    report = _extract_log_json(validate_response) or {}
    external_road_setup = setup.get("external_road_actor") or {}
    summary = {
        "setup": {
            "graph": setup.get("graph_update", {}).get("graph"),
            "edge_error_count": len(setup.get("graph_update", {}).get("edge_errors", [])),
            "actor": setup.get("validation_actor", {}).get("actor"),
            "external_road_actor": external_road_setup.get("actor"),
            "external_road_validation_enabled": setup.get("external_road_validation_enabled"),
        },
        "refresh": refresh.get("result", {}),
        "report": {
            "path": report.get("report_path"),
            "pass": report.get("pass"),
            "counts": report.get("validation", {}).get("counts"),
            "grass_falloff_pass": report.get("validation", {}).get("grass_falloff_pass"),
            "tree_falloff_pass": report.get("validation", {}).get("tree_falloff_pass"),
            "rock_falloff_pass": report.get("validation", {}).get("rock_falloff_pass"),
            "endpoint_cluster_pass": report.get("validation", {}).get("endpoint_cluster_pass"),
            "low_density_grass_spawn_pass": report.get("validation", {}).get("low_density_grass_spawn_pass"),
            "rock_spawn_pass": report.get("validation", {}).get("rock_spawn_pass"),
            "tree_spawn_pass": report.get("validation", {}).get("tree_spawn_pass"),
            "dense_grass_pass_diagnostic": report.get("validation", {}).get("dense_grass_pass"),
            "external_road_clearance_pass": report.get("validation", {}).get("external_road_clearance_pass"),
            "mesh_override_pass": report.get("validation", {}).get("mesh_override_pass"),
            "material_override_pass": report.get("validation", {}).get("material_override_pass"),
            "grass_self_overlap_pass": report.get("validation", {}).get("grass_self_overlap_pass"),
            "tree_self_overlap_pass": report.get("validation", {}).get("tree_self_overlap_pass"),
            "rock_self_overlap_pass": report.get("validation", {}).get("rock_self_overlap_pass"),
            "tree_rock_overlap_pass": report.get("validation", {}).get("tree_rock_overlap_pass"),
            "overlap_stats": report.get("validation", {}).get("overlap_stats"),
            "surface_height_pass": report.get("validation", {}).get("surface_height_pass"),
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
