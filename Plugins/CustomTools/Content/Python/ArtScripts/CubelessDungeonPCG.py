from __future__ import annotations

import json
import math
import os
import random
import time
from collections import deque

import unreal


ROOT = "/Game/Cubeless/PCG/Dungeon"
MATERIAL_DIR = ROOT + "/Materials"
MESH_DIR = ROOT + "/Meshes"
GRAPH_DIR = ROOT + "/Graphs"
MAP_DIR = ROOT + "/Maps"
BLUEPRINT_DIR = ROOT + "/Blueprints"

LEVEL_PATH = MAP_DIR + "/LVL_Cubeless_PCG_Dungeon_MVP"
GRAPH_NAME = "PCG_Cubeless_Dungeon_MVP_Bridge"
GRAPH_PATH = GRAPH_DIR + "/" + GRAPH_NAME
NATIVE_GRAPH_NAME = "PCG_Cubeless_Dungeon_MVP_NativeSkeleton"
NATIVE_GRAPH_PATH = GRAPH_DIR + "/" + NATIVE_GRAPH_NAME
NATIVE_POINT_SOURCE_GRAPH_NAME = "PCG_Cubeless_Dungeon_MVP_NativePointSource"
NATIVE_POINT_SOURCE_GRAPH_PATH = GRAPH_DIR + "/" + NATIVE_POINT_SOURCE_GRAPH_NAME
NATIVE_INTEGRATION_GRAPH_NAME = "PCG_Cubeless_Dungeon_MVP_NativeIntegration"
NATIVE_INTEGRATION_GRAPH_PATH = GRAPH_DIR + "/" + NATIVE_INTEGRATION_GRAPH_NAME
NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME = "PCG_Cubeless_Dungeon_MVP_NativePointSource_PreviewOffset"
NATIVE_POINT_SOURCE_PREVIEW_GRAPH_PATH = GRAPH_DIR + "/" + NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME
NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME = "PCG_Cubeless_Dungeon_MVP_NativeIntegration_PreviewOffset"
NATIVE_INTEGRATION_PREVIEW_GRAPH_PATH = GRAPH_DIR + "/" + NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME

REVIEW_DIRECTIONAL_LIGHT_INTENSITY = 0.72
REVIEW_DIRECTIONAL_LIGHT_COLOR = (232, 238, 242, 255)
REVIEW_SKY_LIGHT_INTENSITY = 0.18
REVIEW_ROOM_POINT_LIGHT_INTENSITY = 33.75
REVIEW_ROOM_POINT_LIGHT_RADIUS = 864.0
REVIEW_EXPOSURE_BIAS = 1.52
REVIEW_EXPOSURE_MIN_BRIGHTNESS = 0.0
REVIEW_EXPOSURE_MAX_BRIGHTNESS = 0.0
REVIEW_BLOOM_INTENSITY = 0.04
REVIEW_GLOBAL_GAIN = 0.90
REVIEW_MIDTONE_GAIN = 1.02
REVIEW_HIGHLIGHT_GAIN = 0.55
REVIEW_SHADOW_GAIN = 1.55
REVIEW_SHADOW_GAMMA = 0.78
REVIEW_SHADOW_CONTRAST = 0.66

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRYPOINT_PATH = os.path.join(SCRIPT_DIR, "CubelessDungeonPCGEntrypoint.py")
REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_Report.json",
)
SEED_SUITE_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_SeedSuite_Report.json",
)
AUTHORING_PRESET_MATRIX_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_AuthoringPresetMatrix_Report.json",
)
GAMEPLAY_DATA_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GameplayData.json",
)
GAMEPLAY_PLACEHOLDER_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GameplayPlaceholder_Report.json",
)
GAMEPLAY_INTERACTION_CONTRACT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GameplayInteractionContract.json",
)
GAMEPLAY_CONTENT_OUTCOME_CONTRACT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GameplayContentOutcomeContract.json",
)
GAMEPLAY_FLOW_SIMULATION_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GameplayFlowSimulation_Report.json",
)
GAMEPLAY_STATE_EVENT_VALIDATION_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GameplayStateEventValidation_Report.json",
)
GAMEPLAY_PLACEHOLDER_VISUAL_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GameplayPlaceholderVisual_Report.json",
)
PCG_SPAWNER_CONTRACT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_PCGSpawnerContract.json",
)
PCG_GRAPH_HANDOFF_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_PCGGraphHandoff.json",
)
NATIVE_GRAPH_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeSkeletonGraph_Report.json",
)
NATIVE_GRAPH_AUDIT_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeSkeletonAudit_Report.json",
)
NATIVE_POINT_SOURCE_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativePointSource_Report.json",
)
NATIVE_POINT_SOURCE_GRAPH_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativePointSourceGraph_Report.json",
)
NATIVE_INTEGRATION_GRAPH_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeIntegrationGraph_Report.json",
)
NATIVE_INTEGRATION_AUDIT_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeIntegrationAudit_Report.json",
)
NATIVE_INTEGRATION_TEST_ACTOR_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeIntegrationTestActor_Report.json",
)
NATIVE_INTEGRATION_TEST_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeIntegrationTest_Report.json",
)
NATIVE_INTEGRATION_OUTPUT_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeIntegrationOutput_Report.json",
)
NATIVE_INTEGRATION_OUTPUT_REVIEW_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeOutputOnlyReview_Report.json",
)
NATIVE_PRIMARY_REFRESH_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativePrimaryRefresh_Report.json",
)
NATIVE_PRIMARY_REFRESH_FINAL_GATE_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativePrimaryRefresh_FinalGate.json",
)
PCG_STRUCTURE_AUDIT_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_PCGStructureAudit_Report.json",
)
PCG_GENERATION_GATE_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_PCGGeneration_FinalGate.json",
)
PCG_GENERATION_REFRESH_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_PCGGeneration_Refresh_Report.json",
)
PCG_GENERATION_OUTPUT_ONLY_SCREENSHOT_QA_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_PCGGeneration_NativeOutputOnly_ScreenshotQA.json",
)
PCG_GENERATION_OUTPUT_ONLY_OBLIQUE_SCREENSHOT_QA_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_PCGGeneration_NativeOutputOnly_Oblique_ScreenshotQA.json",
)
PCG_GENERATION_PARAMETER_SCALE_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_GenerationParameterScale_Report.json",
)
AUTHORING_SURFACE_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_AuthoringSurface_Report.json",
)
AUTHORING_PRESET_SMOKE_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_AuthoringPresetSmoke_Report.json",
)
NATIVE_POINT_SOURCE_PREVIEW_GRAPH_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativePointSourcePreviewGraph_Report.json",
)
NATIVE_INTEGRATION_PREVIEW_GRAPH_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeIntegrationPreviewGraph_Report.json",
)
NATIVE_INTEGRATION_PREVIEW_REPORT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_NativeIntegrationPreview_Report.json",
)
MINIMAP_PATH = os.path.join(
    unreal.Paths.project_saved_dir(),
    "MCP_Dungeon",
    "CubelessDungeonMVP_Minimap.txt",
)

ACTOR_PREFIX = "MCP_Dungeon_MVP_"
GAMEPLAY_PLACEHOLDER_PREFIX = "MCP_Dungeon_Gameplay_"
PCG_BRIDGE_LABEL = "MCP_Cubeless_Dungeon_MVP_PCGBridge"
PCG_NATIVE_INTEGRATION_TEST_LABEL = "MCP_Cubeless_Dungeon_MVP_NativeIntegrationTest"
PCG_NATIVE_INTEGRATION_OUTPUT_LABEL = "MCP_Cubeless_Dungeon_MVP_NativeOutput"
PCG_NATIVE_INTEGRATION_PREVIEW_LABEL = "MCP_Cubeless_Dungeon_MVP_NativeIntegrationPreview"

TILE = 400.0
WALL_THICKNESS = 28.0
WALL_HEIGHT = 320.0
GENERATION_METRICS = {
    "grid_cell_size": float(TILE),
    "corridor_width": float(TILE),
}

DEFAULT_DUNGEON_CONFIG = {
    "seed": 142857,
    "room_count": 11,
    "ceiling_stride": 1,
    "chest_count": 3,
    "enemy_count": 4,
    "key_count": 1,
    "shop_count": 1,
    "locked_door_count": 1,
    "boss_enabled": 1,
    "branch_chance_percent": 100,
    "max_loop_edges": 2,
    "grid_cell_size": int(TILE),
    "corridor_width": int(TILE),
    "use_ceiling": 1,
    "use_theme_materials": 1,
    "preview_mode": 1,
}
CONFIG_TAG_PREFIX = "Dungeon"

CONFIG_AUTHORING_SPECS = [
    {"config_key": "seed", "tag": "Seed", "type": "int", "min": 1, "max": 2147483647, "purpose": "deterministic layout seed"},
    {"config_key": "room_count", "tag": "RoomCount", "type": "int", "min": 2, "max": 32, "purpose": "requested room count"},
    {"config_key": "ceiling_stride", "tag": "CeilingStride", "type": "int", "min": 0, "max": 64, "purpose": "ceiling sample cadence; 1 covers every generated cell and 0 disables ceiling samples"},
    {"config_key": "chest_count", "tag": "ChestCount", "aliases": ["TreasureCount"], "type": "int", "min": 0, "max": 16, "purpose": "treasure room count"},
    {"config_key": "enemy_count", "tag": "EnemyCount", "type": "int", "min": 0, "max": 32, "purpose": "combat room budget"},
    {"config_key": "key_count", "tag": "KeyCount", "type": "int", "min": 0, "max": 8, "purpose": "progression key room count"},
    {"config_key": "shop_count", "tag": "ShopCount", "type": "int", "min": 0, "max": 6, "purpose": "shop room count"},
    {"config_key": "locked_door_count", "tag": "LockedDoorCount", "type": "int", "min": 0, "max": 8, "purpose": "locked progression gate count"},
    {"config_key": "boss_enabled", "tag": "BossEnabled", "type": "bool_int", "min": 0, "max": 1, "purpose": "boss role toggle"},
    {"config_key": "branch_chance_percent", "tag": "BranchChancePercent", "aliases": ["BranchChance"], "type": "int", "min": 0, "max": 100, "purpose": "chance to add valid loop/branch edges"},
    {"config_key": "max_loop_edges", "tag": "MaxLoopEdges", "type": "int", "min": 0, "max": 16, "purpose": "maximum added loop/branch edges"},
    {"config_key": "grid_cell_size", "tag": "GridCellSize", "type": "int", "min": 200, "max": 1200, "purpose": "world grid spacing and base XY module scale"},
    {"config_key": "corridor_width", "tag": "CorridorWidth", "type": "int", "min": 200, "max": 1200, "purpose": "corridor, door, connector, and seal width scale"},
    {"config_key": "use_ceiling", "tag": "UseCeiling", "type": "bool_int", "min": 0, "max": 1, "purpose": "ceiling module toggle"},
    {"config_key": "use_theme_materials", "tag": "UseThemeMaterials", "type": "bool_int", "min": 0, "max": 1, "purpose": "theme material override toggle"},
    {"config_key": "preview_mode", "tag": "PreviewMode", "type": "bool_int", "min": 0, "max": 1, "purpose": "review metadata flag"},
]

DUNGEON_AUTHORING_PRESETS = {
    "default": dict(DEFAULT_DUNGEON_CONFIG),
    "compact_branching": dict(
        DEFAULT_DUNGEON_CONFIG,
        seed=142860,
        room_count=8,
        max_loop_edges=1,
        grid_cell_size=340,
        corridor_width=260,
    ),
    "wide_looped": dict(
        DEFAULT_DUNGEON_CONFIG,
        seed=142858,
        room_count=11,
        max_loop_edges=4,
        grid_cell_size=520,
        corridor_width=360,
    ),
    "open_cutaway": dict(
        DEFAULT_DUNGEON_CONFIG,
        seed=142864,
        ceiling_stride=0,
        use_ceiling=0,
        max_loop_edges=2,
    ),
    "small_route": dict(
        DEFAULT_DUNGEON_CONFIG,
        seed=142872,
        room_count=7,
        chest_count=2,
        enemy_count=3,
        max_loop_edges=1,
        grid_cell_size=340,
        corridor_width=260,
    ),
    "long_route": dict(
        DEFAULT_DUNGEON_CONFIG,
        seed=142876,
        room_count=11,
        chest_count=3,
        enemy_count=4,
        branch_chance_percent=55,
        max_loop_edges=1,
        grid_cell_size=440,
        corridor_width=340,
    ),
    "loop_dense": dict(
        DEFAULT_DUNGEON_CONFIG,
        seed=142880,
        room_count=11,
        enemy_count=5,
        branch_chance_percent=100,
        max_loop_edges=5,
        grid_cell_size=440,
        corridor_width=340,
    ),
    "boss_focus": dict(
        DEFAULT_DUNGEON_CONFIG,
        seed=142884,
        room_count=10,
        chest_count=2,
        enemy_count=5,
        branch_chance_percent=85,
        max_loop_edges=2,
        grid_cell_size=460,
        corridor_width=360,
    ),
}

DUNGEON_AUTHORING_PRESET_NOTES = {
    "default": {
        "label": "Default closed-ceiling delivery",
        "intent": "Stable V1 handoff preset with full ceiling coverage and balanced room roles.",
    },
    "compact_branching": {
        "label": "Compact branching",
        "intent": "Smaller footprint for quick review and dense branch readability.",
    },
    "wide_looped": {
        "label": "Wide looped",
        "intent": "Wider module spacing with more loops for route variety checks.",
    },
    "open_cutaway": {
        "label": "Open cutaway",
        "intent": "Ceiling-off structural review preset for top-down inspection.",
    },
    "small_route": {
        "label": "Small route",
        "intent": "Short dungeon pass for fast layout iteration and small-room readability.",
    },
    "long_route": {
        "label": "Long route",
        "intent": "Longer critical-path dungeon with limited loops for route-distance checks.",
    },
    "loop_dense": {
        "label": "Loop dense",
        "intent": "Higher loop budget stress preset for branch and connector validation.",
    },
    "boss_focus": {
        "label": "Boss focus",
        "intent": "Compact combat-heavy preset that keeps the boss/exit room prominent.",
    },
}

MATERIALS = [
    ("M_Dungeon_Floor_Stone", (0.28, 0.30, 0.27, 1.0), 0.76, 0.0, 0.22, False, 1.0),
    ("M_Dungeon_Wall_ColdStone", (0.18, 0.21, 0.23, 1.0), 0.82, 0.0, 0.20, False, 1.0),
    ("M_Dungeon_Trim_DarkIron", (0.035, 0.040, 0.045, 1.0), 0.52, 0.0, 0.45, False, 1.0),
    ("M_Dungeon_Door_WornBronze", (0.44, 0.30, 0.14, 1.0), 0.58, 0.0, 0.42, False, 1.0),
    ("M_Dungeon_Ceiling_SootStone", (0.11, 0.13, 0.14, 1.0), 0.86, 0.0, 0.18, False, 1.0),
    ("M_Dungeon_Start_Green", (0.10, 0.85, 0.42, 1.0), 0.40, 0.0, 0.20, True, 1.0),
    ("M_Dungeon_Exit_Blue", (0.16, 0.44, 1.20, 1.0), 0.34, 0.0, 0.16, True, 1.0),
    ("M_Dungeon_Chest_Gold", (1.10, 0.68, 0.16, 1.0), 0.42, 0.0, 0.22, True, 1.0),
    ("M_Dungeon_Enemy_Red", (1.10, 0.14, 0.10, 1.0), 0.45, 0.0, 0.18, True, 1.0),
    ("M_Dungeon_Key_Cyan", (0.14, 1.15, 1.10, 1.0), 0.35, 0.0, 0.18, True, 1.0),
    ("M_Dungeon_LockedDoor_Violet", (0.72, 0.22, 1.25, 1.0), 0.36, 0.0, 0.18, True, 1.0),
    ("M_Dungeon_Boss_Magenta", (1.20, 0.14, 0.75, 1.0), 0.40, 0.0, 0.16, True, 1.0),
    ("M_Dungeon_Shop_Teal", (0.10, 0.95, 0.62, 1.0), 0.42, 0.0, 0.20, True, 1.0),
    ("M_Dungeon_Theme_EntryStone", (0.22, 0.34, 0.28, 1.0), 0.74, 0.0, 0.22, False, 1.0),
    ("M_Dungeon_Theme_CombatStone", (0.34, 0.24, 0.24, 1.0), 0.78, 0.0, 0.20, False, 1.0),
    ("M_Dungeon_Theme_KeyStone", (0.18, 0.33, 0.36, 1.0), 0.72, 0.0, 0.22, False, 1.0),
    ("M_Dungeon_Theme_UtilityStone", (0.20, 0.34, 0.31, 1.0), 0.70, 0.0, 0.24, False, 1.0),
    ("M_Dungeon_Theme_RewardStone", (0.42, 0.33, 0.18, 1.0), 0.68, 0.0, 0.26, False, 1.0),
    ("M_Dungeon_Theme_FinaleStone", (0.32, 0.20, 0.36, 1.0), 0.76, 0.0, 0.22, False, 1.0),
    ("M_Dungeon_Theme_AmbientStone", (0.25, 0.27, 0.25, 1.0), 0.82, 0.0, 0.18, False, 1.0),
    ("M_Dungeon_Theme_ConnectorStone", (0.24, 0.28, 0.31, 1.0), 0.80, 0.0, 0.18, False, 1.0),
    ("M_Dungeon_Theme_CorridorStone", (0.19, 0.22, 0.24, 1.0), 0.84, 0.0, 0.18, False, 1.0),
]
MAT = {name: index for index, (name, *_rest) in enumerate(MATERIALS)}

MODULE_SPECS = [
    ("floor", "SM_GS_Dungeon_FloorTile"),
    ("wall", "SM_GS_Dungeon_WallPanel"),
    ("door", "SM_GS_Dungeon_DoorFrame"),
    ("corridor", "SM_GS_Dungeon_CorridorSegment"),
    ("corner", "SM_GS_Dungeon_CornerSegment"),
    ("ceiling", "SM_GS_Dungeon_CeilingPanel"),
    ("ceiling_room", "SM_GS_Dungeon_Ceiling_Room"),
    ("ceiling_corridor", "SM_GS_Dungeon_Ceiling_Corridor"),
    ("ceiling_corner", "SM_GS_Dungeon_Ceiling_Corner"),
    ("column", "SM_GS_Dungeon_Column"),
    ("stair", "SM_GS_Dungeon_Stair"),
    ("marker", "SM_GS_Dungeon_SpawnMarker"),
    ("seal", "SM_GS_Dungeon_LockedDoorSeal"),
    ("detail_pedestal", "SM_GS_Dungeon_Detail_Pedestal"),
    ("detail_cover", "SM_GS_Dungeon_Detail_Cover"),
    ("detail_wall_trim", "SM_GS_Dungeon_Detail_WallTrim"),
    ("detail_counter", "SM_GS_Dungeon_Detail_Counter"),
    ("detail_brazier", "SM_GS_Dungeon_Detail_Brazier"),
    ("detail_sign", "SM_GS_Dungeon_Detail_Sign"),
    ("detail_arch", "SM_GS_Dungeon_Detail_Arch"),
    ("detail_boss_focus", "SM_GS_Dungeon_Detail_BossFocus"),
    ("connector_threshold", "SM_GS_Dungeon_Connector_Threshold"),
    ("connector_locked", "SM_GS_Dungeon_Connector_LockedThreshold"),
    ("corridor_detail_straight", "SM_GS_Dungeon_CorridorDetail_Straight"),
    ("corridor_detail_corner", "SM_GS_Dungeon_CorridorDetail_Corner"),
    ("corridor_detail_junction", "SM_GS_Dungeon_CorridorDetail_Junction"),
    ("corridor_detail_endcap", "SM_GS_Dungeon_CorridorDetail_Endcap"),
    ("room_variant_entry_inlay", "SM_GS_Dungeon_RoomVariant_EntryInlay"),
    ("room_variant_combat_partition", "SM_GS_Dungeon_RoomVariant_CombatPartition"),
    ("room_variant_reward_border", "SM_GS_Dungeon_RoomVariant_RewardBorder"),
    ("room_variant_utility_market", "SM_GS_Dungeon_RoomVariant_UtilityMarket"),
    ("room_variant_progression_rune", "SM_GS_Dungeon_RoomVariant_ProgressionRune"),
    ("room_variant_finale_ring", "SM_GS_Dungeon_RoomVariant_FinaleRing"),
    ("room_variant_ambient_rubble", "SM_GS_Dungeon_RoomVariant_AmbientRubble"),
]
MESH_KEY_BY_ASSET_NAME = {asset_name: module_key for module_key, asset_name in MODULE_SPECS}
STATIC_MESH_COUNT_KEYS = [
    "floor",
    "corridor",
    "corner",
    "ceiling_room",
    "ceiling_corridor",
    "ceiling_corner",
    "wall",
    "door",
    "column",
    "stair",
    "marker",
    "seal",
    "connector_detail",
    "corridor_detail",
    "room_variant_detail",
    "detail_mesh",
]


def ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def ensure_dirs() -> None:
    for path in (ROOT, MATERIAL_DIR, MESH_DIR, GRAPH_DIR, MAP_DIR):
        ensure_dir(path)


def transform(location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
    return unreal.Transform(
        unreal.Vector(float(location[0]), float(location[1]), float(location[2])),
        unreal.Rotator(float(rotation[0]), float(rotation[1]), float(rotation[2])),
        unreal.Vector(float(scale[0]), float(scale[1]), float(scale[2])),
    )


def _vector3_list(value=None, default=None):
    if default is None:
        default = [0.0, 0.0, 0.0]
    if value is None:
        value = default
    try:
        return [float(value[0]), float(value[1]), float(value[2])]
    except Exception:
        return [float(default[0]), float(default[1]), float(default[2])]


def _set_generation_metrics(grid_cell_size=None, corridor_width=None):
    grid_value = _coerce_float(grid_cell_size, TILE, 200.0, 1200.0)
    corridor_value = _coerce_float(corridor_width, grid_value, 120.0, 1200.0)
    corridor_value = min(corridor_value, grid_value)
    GENERATION_METRICS["grid_cell_size"] = grid_value
    GENERATION_METRICS["corridor_width"] = corridor_value
    return dict(GENERATION_METRICS)


def _grid_cell_size():
    return float(GENERATION_METRICS.get("grid_cell_size", TILE) or TILE)


def _grid_scale_xy():
    return _grid_cell_size() / float(TILE)


def _corridor_width_scale():
    return float(GENERATION_METRICS.get("corridor_width", _grid_cell_size()) or _grid_cell_size()) / _grid_cell_size()


def _module_scale(scale_x=None, scale_y=None, scale_z=1.0):
    base_scale = _grid_scale_xy()
    x = base_scale if scale_x is None else base_scale * float(scale_x)
    y = base_scale if scale_y is None else base_scale * float(scale_y)
    return unreal.Vector(float(x), float(y), float(scale_z))


def _scaled_xy(value):
    return float(value) * _grid_scale_xy()


def _directional_width_scale(direction, width_scale=None):
    width = _corridor_width_scale() if width_scale is None else float(width_scale)
    return _module_scale(scale_x=width, scale_y=1.0)


def _yaw_width_scale(yaw, width_scale=None):
    width = _corridor_width_scale() if width_scale is None else float(width_scale)
    return _module_scale(scale_x=1.0, scale_y=width)


def _actor_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    # Unreal Python's positional Rotator order is roll, pitch, yaw; set fields explicitly for actor spawns.
    rotation = unreal.Rotator()
    rotation.pitch = float(pitch)
    rotation.yaw = float(yaw)
    rotation.roll = float(roll)
    return rotation


def _yaw_rotator(yaw):
    return _actor_rotator(yaw=float(yaw))


def primitive_opts(material_name: str):
    options = unreal.GeometryScriptPrimitiveOptions()
    options.material_id = MAT[material_name]
    return options


def box(mesh, material_name, loc, dims, rot=(0, 0, 0)):
    unreal.GeometryScript_Primitives.append_box(
        mesh,
        primitive_opts(material_name),
        transform(loc, rot),
        float(dims[0]),
        float(dims[1]),
        float(dims[2]),
        0,
        0,
        0,
        unreal.GeometryScriptPrimitiveOriginMode.CENTER,
    )


def cylinder(mesh, material_name, loc, radius, height, rot=(0, 0, 0), radial_steps=12):
    unreal.GeometryScript_Primitives.append_cylinder(
        mesh,
        primitive_opts(material_name),
        transform(loc, rot),
        float(radius),
        float(height),
        int(radial_steps),
        0,
        True,
        unreal.GeometryScriptPrimitiveOriginMode.CENTER,
    )


def _constant(material, value, x, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, x, y
    )
    node.set_editor_property("r", float(value))
    return node


def _constant3(material, color, x, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, x, y
    )
    node.set_editor_property("constant", unreal.LinearColor(*color))
    return node


def create_material(name, color, roughness, metallic, specular, emissive, opacity):
    ensure_dir(MATERIAL_DIR)
    path = MATERIAL_DIR + "/" + name
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.EditorAssetLibrary.load_asset(path)
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    else:
        material = tools.create_asset(name, MATERIAL_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError("Failed to create material: " + path)

    material.set_editor_property("two_sided", True)
    material.set_editor_property(
        "blend_mode",
        unreal.BlendMode.BLEND_TRANSLUCENT if opacity < 1.0 else unreal.BlendMode.BLEND_OPAQUE,
    )
    material.set_editor_property(
        "shading_model",
        unreal.MaterialShadingModel.MSM_UNLIT if emissive else unreal.MaterialShadingModel.MSM_DEFAULT_LIT,
    )

    color_node = _constant3(material, color, -420, -60)
    if emissive:
        unreal.MaterialEditingLibrary.connect_material_property(
            color_node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        base = _constant3(material, tuple(min(1.0, value) for value in color), -420, 100)
        unreal.MaterialEditingLibrary.connect_material_property(
            base, "", unreal.MaterialProperty.MP_BASE_COLOR
        )
    else:
        unreal.MaterialEditingLibrary.connect_material_property(
            color_node, "", unreal.MaterialProperty.MP_BASE_COLOR
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, roughness, -420, 120), "", unreal.MaterialProperty.MP_ROUGHNESS
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, metallic, -420, 260), "", unreal.MaterialProperty.MP_METALLIC
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, specular, -420, 400), "", unreal.MaterialProperty.MP_SPECULAR
        )
    if opacity < 1.0:
        unreal.MaterialEditingLibrary.connect_material_property(
            _constant(material, opacity, -420, 540), "", unreal.MaterialProperty.MP_OPACITY
        )

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def create_materials():
    return [
        create_material(name, color, roughness, metallic, specular, emissive, opacity)
        for name, color, roughness, metallic, specular, emissive, opacity in MATERIALS
    ]


def build_floor_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Floor_Stone", (0, 0, -8), (TILE, TILE, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -TILE * 0.5 + 12, 4), (TILE, 16, 8))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, TILE * 0.5 - 12, 4), (TILE, 16, 8))
    return mesh


def build_wall_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Wall_ColdStone", (0, 0, WALL_HEIGHT * 0.5), (TILE, WALL_THICKNESS, WALL_HEIGHT))
    for x in (-TILE * 0.34, 0, TILE * 0.34):
        box(mesh, "M_Dungeon_Trim_DarkIron", (x, -WALL_THICKNESS * 0.55, WALL_HEIGHT * 0.5), (10, 8, WALL_HEIGHT))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -WALL_THICKNESS * 0.58, 20), (TILE, 9, 20))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -WALL_THICKNESS * 0.58, WALL_HEIGHT - 20), (TILE, 9, 20))
    return mesh


def build_door_mesh():
    mesh = unreal.DynamicMesh()
    side_width = 70.0
    lintel_height = 64.0
    opening_width = 220.0
    opening_height = 250.0
    total_width = opening_width + side_width * 2.0
    box(mesh, "M_Dungeon_Door_WornBronze", (-opening_width * 0.5 - side_width * 0.5, 0, opening_height * 0.5), (side_width, WALL_THICKNESS * 1.35, opening_height))
    box(mesh, "M_Dungeon_Door_WornBronze", (opening_width * 0.5 + side_width * 0.5, 0, opening_height * 0.5), (side_width, WALL_THICKNESS * 1.35, opening_height))
    box(mesh, "M_Dungeon_Door_WornBronze", (0, 0, opening_height + lintel_height * 0.5), (total_width, WALL_THICKNESS * 1.45, lintel_height))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -WALL_THICKNESS, opening_height + 8), (total_width + 28, 12, 16))
    return mesh


def build_corridor_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Floor_Stone", (0, 0, -7), (TILE, TILE, 14))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -TILE * 0.5 + 22, 10), (TILE, 20, 20))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, TILE * 0.5 - 22, 10), (TILE, 20, 20))
    return mesh


def build_corner_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Floor_Stone", (0, 0, -7), (TILE, TILE, 14))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-TILE * 0.5 + 22, 0, 12), (20, TILE, 24))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -TILE * 0.5 + 22, 12), (TILE, 20, 24))
    cylinder(mesh, "M_Dungeon_Door_WornBronze", (-TILE * 0.5 + 34, -TILE * 0.5 + 34, 34), 26, 42, radial_steps=10)
    return mesh


def build_ceiling_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Ceiling_SootStone", (0, 0, 0), (TILE, TILE, 18))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, -12), (TILE * 0.72, 18, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, -12), (18, TILE * 0.72, 12))
    return mesh


def build_ceiling_room_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Ceiling_SootStone", (0, 0, 0), (TILE, TILE, 18))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -TILE * 0.5 + 26, -12), (TILE * 0.86, 16, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, TILE * 0.5 - 26, -12), (TILE * 0.86, 16, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-TILE * 0.5 + 26, 0, -12), (16, TILE * 0.86, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (TILE * 0.5 - 26, 0, -12), (16, TILE * 0.86, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, -15), (TILE * 0.42, 12, 10))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, -15), (12, TILE * 0.42, 10))
    return mesh


def build_ceiling_corridor_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Ceiling_SootStone", (0, 0, 0), (TILE, TILE, 18))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -TILE * 0.5 + 24, -12), (TILE * 0.92, 14, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, TILE * 0.5 - 24, -12), (TILE * 0.92, 14, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-TILE * 0.25, 0, -14), (12, TILE * 0.58, 10))
    box(mesh, "M_Dungeon_Trim_DarkIron", (TILE * 0.25, 0, -14), (12, TILE * 0.58, 10))
    return mesh


def build_ceiling_corner_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Ceiling_SootStone", (0, 0, 0), (TILE, TILE, 18))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-TILE * 0.5 + 24, 0, -12), (14, TILE * 0.9, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -TILE * 0.5 + 24, -12), (TILE * 0.9, 14, 12))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-TILE * 0.22, -TILE * 0.22, -14), (TILE * 0.5, 12, 10))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-TILE * 0.22, -TILE * 0.22, -14), (12, TILE * 0.5, 10))
    return mesh


def build_column_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Wall_ColdStone", (0, 0, WALL_HEIGHT * 0.5), 42, WALL_HEIGHT, radial_steps=14)
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 18), 58, 36, radial_steps=14)
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, WALL_HEIGHT - 18), 54, 36, radial_steps=14)
    return mesh


def build_stair_mesh():
    mesh = unreal.DynamicMesh()
    step_count = 5
    step_depth = TILE / step_count
    for index in range(step_count):
        height = 22.0 + index * 22.0
        y = -TILE * 0.5 + step_depth * (index + 0.5)
        box(mesh, "M_Dungeon_Floor_Stone", (0, y, height * 0.5), (TILE * 0.9, step_depth, height))
        box(mesh, "M_Dungeon_Trim_DarkIron", (0, y + step_depth * 0.45, height + 4), (TILE * 0.9, 10, 8))
    return mesh


def build_marker_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Start_Green", (0, 0, 24), (90, 90, 48))
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 8), 62, 16, radial_steps=12)
    return mesh


def build_seal_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_LockedDoor_Violet", (0, 0, 76), (88, 18, 88))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -12, 76), (104, 10, 14))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -12, 76), (14, 10, 104))
    box(mesh, "M_Dungeon_LockedDoor_Violet", (0, -18, 122), (48, 12, 30))
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, -22, 76), 18, 12, radial_steps=10)
    return mesh


def build_detail_pedestal_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Wall_ColdStone", (0, 0, 26), 58, 52, radial_steps=14)
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 62), 70, 18, radial_steps=14)
    cylinder(mesh, "M_Dungeon_Chest_Gold", (0, 0, 92), 42, 38, radial_steps=12)
    return mesh


def build_detail_cover_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Wall_ColdStone", (0, 0, 42), (220, 62, 84))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -36, 88), (236, 12, 18))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-82, -38, 50), (18, 14, 70))
    box(mesh, "M_Dungeon_Trim_DarkIron", (82, -38, 50), (18, 14, 70))
    return mesh


def build_detail_wall_trim_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Wall_ColdStone", (0, 0, 148), (250, 34, 170))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -24, 232), (270, 12, 20))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -24, 64), (270, 12, 20))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-124, -26, 148), (16, 14, 170))
    box(mesh, "M_Dungeon_Trim_DarkIron", (124, -26, 148), (16, 14, 170))
    return mesh


def build_detail_counter_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Door_WornBronze", (0, 0, 48), (250, 86, 96))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -50, 104), (270, 14, 18))
    box(mesh, "M_Dungeon_Shop_Teal", (0, -58, 124), (190, 10, 18))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-92, -52, 56), (16, 14, 76))
    box(mesh, "M_Dungeon_Trim_DarkIron", (92, -52, 56), (16, 14, 76))
    return mesh


def build_detail_brazier_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 22), 44, 44, radial_steps=12)
    cylinder(mesh, "M_Dungeon_Door_WornBronze", (0, 0, 64), 34, 36, radial_steps=12)
    cylinder(mesh, "M_Dungeon_Key_Cyan", (0, 0, 102), 28, 38, radial_steps=10)
    return mesh


def build_detail_sign_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Door_WornBronze", (0, 0, 180), (210, 24, 92))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -18, 180), (230, 10, 112))
    box(mesh, "M_Dungeon_Shop_Teal", (0, -24, 180), (150, 8, 38))
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (-88, 0, 106), 10, 126, radial_steps=8)
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (88, 0, 106), 10, 126, radial_steps=8)
    return mesh


def build_detail_arch_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Wall_ColdStone", (-112, 0, 132), (46, 54, 264))
    box(mesh, "M_Dungeon_Wall_ColdStone", (112, 0, 132), (46, 54, 264))
    box(mesh, "M_Dungeon_Wall_ColdStone", (0, 0, 252), (270, 58, 54))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -34, 286), (296, 14, 20))
    box(mesh, "M_Dungeon_Start_Green", (0, -40, 220), (86, 8, 28))
    return mesh


def build_detail_boss_focus_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 20), 72, 40, radial_steps=14)
    box(mesh, "M_Dungeon_LockedDoor_Violet", (0, 0, 96), (72, 72, 144), rot=(0, 0, 45))
    box(mesh, "M_Dungeon_Boss_Magenta", (0, -44, 172), (58, 12, 42), rot=(0, 0, 45))
    return mesh


def build_connector_threshold_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_ConnectorStone", (0, 0, 8), (312, 104, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -58, 22), (328, 16, 28))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 58, 22), (328, 16, 28))
    box(mesh, "M_Dungeon_Door_WornBronze", (-140, 0, 38), (28, 108, 44))
    box(mesh, "M_Dungeon_Door_WornBronze", (140, 0, 38), (28, 108, 44))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 58), (250, 18, 16))
    return mesh


def build_connector_locked_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_ConnectorStone", (0, 0, 8), (322, 112, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -62, 24), (342, 18, 32))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 62, 24), (342, 18, 32))
    box(mesh, "M_Dungeon_Door_WornBronze", (-148, 0, 62), (32, 116, 92))
    box(mesh, "M_Dungeon_Door_WornBronze", (148, 0, 62), (32, 116, 92))
    box(mesh, "M_Dungeon_LockedDoor_Violet", (0, -68, 118), (128, 12, 54))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -76, 118), (154, 10, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -76, 118), (18, 10, 72))
    return mesh


def build_corridor_detail_straight_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_CorridorStone", (0, 0, 8), (316, 48, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -34, 20), (300, 10, 24))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 34, 20), (300, 10, 24))
    box(mesh, "M_Dungeon_Door_WornBronze", (-114, 0, 34), (38, 26, 24))
    box(mesh, "M_Dungeon_Door_WornBronze", (114, 0, 34), (38, 26, 24))
    return mesh


def build_corridor_detail_corner_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_CorridorStone", (74, 0, 8), (170, 46, 16))
    box(mesh, "M_Dungeon_Theme_CorridorStone", (0, 74, 8), (46, 170, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (92, 34, 22), (184, 10, 28))
    box(mesh, "M_Dungeon_Trim_DarkIron", (34, 92, 22), (10, 184, 28))
    cylinder(mesh, "M_Dungeon_Door_WornBronze", (22, 22, 34), 28, 24, radial_steps=10)
    return mesh


def build_corridor_detail_junction_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Theme_ConnectorStone", (0, 0, 10), 92, 20, radial_steps=16)
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 26), (246, 22, 22))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 26), (22, 246, 22))
    cylinder(mesh, "M_Dungeon_Door_WornBronze", (0, 0, 48), 34, 28, radial_steps=12)
    return mesh


def build_corridor_detail_endcap_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_CorridorStone", (64, 0, 8), (188, 60, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-38, 0, 28), (34, 132, 40))
    box(mesh, "M_Dungeon_Trim_DarkIron", (72, -42, 22), (162, 10, 28))
    box(mesh, "M_Dungeon_Trim_DarkIron", (72, 42, 22), (162, 10, 28))
    box(mesh, "M_Dungeon_Door_WornBronze", (132, 0, 40), (38, 36, 32))
    return mesh


def build_room_variant_entry_inlay_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Theme_EntryStone", (0, 0, 7), 132, 14, radial_steps=20)
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 18), 146, 12, radial_steps=20)
    box(mesh, "M_Dungeon_Start_Green", (0, 0, 26), (168, 18, 12))
    box(mesh, "M_Dungeon_Start_Green", (0, 0, 26), (18, 168, 12))
    return mesh


def build_room_variant_combat_partition_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_CombatStone", (-92, 0, 46), (220, 54, 92))
    box(mesh, "M_Dungeon_Theme_CombatStone", (92, 0, 46), (220, 54, 92))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-92, -34, 98), (238, 12, 20))
    box(mesh, "M_Dungeon_Trim_DarkIron", (92, 34, 98), (238, 12, 20))
    box(mesh, "M_Dungeon_Enemy_Red", (0, 0, 116), (72, 16, 18))
    return mesh


def build_room_variant_reward_border_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_RewardStone", (0, 0, 8), (286, 286, 16))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -152, 24), (316, 18, 32))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 152, 24), (316, 18, 32))
    box(mesh, "M_Dungeon_Trim_DarkIron", (-152, 0, 24), (18, 316, 32))
    box(mesh, "M_Dungeon_Trim_DarkIron", (152, 0, 24), (18, 316, 32))
    cylinder(mesh, "M_Dungeon_Chest_Gold", (0, 0, 42), 58, 36, radial_steps=14)
    return mesh


def build_room_variant_utility_market_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_UtilityStone", (0, 0, 8), (292, 220, 16))
    box(mesh, "M_Dungeon_Door_WornBronze", (0, -72, 46), (244, 52, 92))
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, -106, 102), (260, 12, 20))
    box(mesh, "M_Dungeon_Shop_Teal", (0, 56, 26), (210, 20, 20))
    box(mesh, "M_Dungeon_Shop_Teal", (-88, 76, 40), (46, 34, 38))
    box(mesh, "M_Dungeon_Shop_Teal", (88, 76, 40), (46, 34, 38))
    return mesh


def build_room_variant_progression_rune_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Theme_KeyStone", (0, 0, 6), 118, 12, radial_steps=18)
    cylinder(mesh, "M_Dungeon_Key_Cyan", (0, 0, 20), 86, 14, radial_steps=18)
    box(mesh, "M_Dungeon_Key_Cyan", (0, 0, 34), (178, 14, 18), rot=(0, 0, 45))
    box(mesh, "M_Dungeon_Key_Cyan", (0, 0, 34), (178, 14, 18), rot=(0, 0, -45))
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, 0, 48), 28, 30, radial_steps=12)
    return mesh


def build_room_variant_finale_ring_mesh():
    mesh = unreal.DynamicMesh()
    cylinder(mesh, "M_Dungeon_Theme_FinaleStone", (0, 0, 8), 178, 16, radial_steps=24)
    cylinder(mesh, "M_Dungeon_LockedDoor_Violet", (0, 0, 24), 132, 14, radial_steps=24)
    for x, y in ((-132, -132), (132, -132), (-132, 132), (132, 132)):
        cylinder(mesh, "M_Dungeon_Trim_DarkIron", (x, y, 52), 34, 104, radial_steps=12)
        cylinder(mesh, "M_Dungeon_Boss_Magenta", (x, y, 118), 24, 28, radial_steps=10)
    box(mesh, "M_Dungeon_Boss_Magenta", (0, 0, 72), (82, 82, 86), rot=(0, 0, 45))
    return mesh


def build_room_variant_ambient_rubble_mesh():
    mesh = unreal.DynamicMesh()
    box(mesh, "M_Dungeon_Theme_AmbientStone", (-74, -22, 24), (128, 58, 48), rot=(0, 0, 8))
    box(mesh, "M_Dungeon_Theme_AmbientStone", (74, 34, 18), (110, 52, 36), rot=(0, 0, -14))
    cylinder(mesh, "M_Dungeon_Trim_DarkIron", (0, -88, 24), 34, 48, radial_steps=8)
    box(mesh, "M_Dungeon_Trim_DarkIron", (0, 78, 32), (172, 18, 30), rot=(0, 0, 18))
    return mesh


MESH_BUILDERS = {
    "floor": build_floor_mesh,
    "wall": build_wall_mesh,
    "door": build_door_mesh,
    "corridor": build_corridor_mesh,
    "corner": build_corner_mesh,
    "ceiling": build_ceiling_mesh,
    "ceiling_room": build_ceiling_room_mesh,
    "ceiling_corridor": build_ceiling_corridor_mesh,
    "ceiling_corner": build_ceiling_corner_mesh,
    "column": build_column_mesh,
    "stair": build_stair_mesh,
    "marker": build_marker_mesh,
    "seal": build_seal_mesh,
    "detail_pedestal": build_detail_pedestal_mesh,
    "detail_cover": build_detail_cover_mesh,
    "detail_wall_trim": build_detail_wall_trim_mesh,
    "detail_counter": build_detail_counter_mesh,
    "detail_brazier": build_detail_brazier_mesh,
    "detail_sign": build_detail_sign_mesh,
    "detail_arch": build_detail_arch_mesh,
    "detail_boss_focus": build_detail_boss_focus_mesh,
    "connector_threshold": build_connector_threshold_mesh,
    "connector_locked": build_connector_locked_mesh,
    "corridor_detail_straight": build_corridor_detail_straight_mesh,
    "corridor_detail_corner": build_corridor_detail_corner_mesh,
    "corridor_detail_junction": build_corridor_detail_junction_mesh,
    "corridor_detail_endcap": build_corridor_detail_endcap_mesh,
    "room_variant_entry_inlay": build_room_variant_entry_inlay_mesh,
    "room_variant_combat_partition": build_room_variant_combat_partition_mesh,
    "room_variant_reward_border": build_room_variant_reward_border_mesh,
    "room_variant_utility_market": build_room_variant_utility_market_mesh,
    "room_variant_progression_rune": build_room_variant_progression_rune_mesh,
    "room_variant_finale_ring": build_room_variant_finale_ring_mesh,
    "room_variant_ambient_rubble": build_room_variant_ambient_rubble_mesh,
}


def configure_mesh_navigation_collision(static_mesh):
    if not static_mesh:
        return {"ok": False, "error": "missing mesh"}
    try:
        body_setup = static_mesh.get_editor_property("body_setup")
        before = str(body_setup.get_editor_property("collision_trace_flag"))
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        after = str(body_setup.get_editor_property("collision_trace_flag"))
        return {
            "ok": True,
            "mesh": static_mesh.get_name(),
            "before": before,
            "after": after,
        }
    except Exception as exc:
        return {"ok": False, "mesh": static_mesh.get_name(), "error": str(exc)}


def ensure_module_navigation_collision(meshes):
    reports = {}
    for key, mesh in sorted(meshes.items()):
        reports[key] = configure_mesh_navigation_collision(mesh)
        if reports[key].get("ok"):
            try:
                unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
            except Exception as exc:
                reports[key]["save_error"] = str(exc)
    return reports


def bake_static_mesh(module_key, mesh, materials):
    asset_name = dict(MODULE_SPECS)[module_key]
    asset_path = MESH_DIR + "/" + asset_name
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)

    normal_options = unreal.GeometryScriptCalculateNormalsOptions()
    normal_options.angle_weighted = True
    normal_options.area_weighted = True
    unreal.GeometryScript_Normals.recompute_normals(mesh, normal_options)

    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    options.enable_collision = True
    options.enable_recompute_normals = True
    options.enable_recompute_tangents = True
    options.enable_nanite = False
    static_mesh, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh,
        asset_path,
        options,
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS or not static_mesh:
        raise RuntimeError("Static mesh creation failed for {}: {}".format(asset_path, outcome))

    for index, material in enumerate(materials):
        static_mesh.set_material(index, material)
    configure_mesh_navigation_collision(static_mesh)
    unreal.EditorAssetLibrary.save_loaded_asset(static_mesh, only_if_is_dirty=False)
    return static_mesh


def build_module_assets():
    ensure_dirs()
    materials = create_materials()
    meshes = {}
    for module_key, _asset_name in MODULE_SPECS:
        meshes[module_key] = bake_static_mesh(module_key, MESH_BUILDERS[module_key](), materials)
    return meshes


def _make_file_path(file_path):
    value = unreal.FilePath()
    value.file_path = file_path
    return value


def _pcg_pin_label(pin):
    try:
        return str(pin.get_editor_property("properties").get_editor_property("label"))
    except Exception:
        return pin.get_name()


def _try_add_edge(graph, from_node, to_node, from_pin="Out", to_pin="In"):
    from_name = from_node.get_name() if from_node else "<missing>"
    to_name = to_node.get_name() if to_node else "<missing>"
    try:
        from_labels = [_pcg_pin_label(pin) for pin in from_node.output_pins]
        to_labels = [_pcg_pin_label(pin) for pin in to_node.input_pins]
        if from_pin not in from_labels or to_pin not in to_labels:
            return {
                "ok": False,
                "from": from_name,
                "to": to_name,
                "from_pin": from_pin,
                "to_pin": to_pin,
                "from_available": from_labels,
                "to_available": to_labels,
            }
        graph.add_edge(from_node, unreal.Name(from_pin), to_node, unreal.Name(to_pin))
        return {"ok": True, "from": from_name, "to": to_name, "from_pin": from_pin, "to_pin": to_pin}
    except Exception as exc:
        return {"ok": False, "from": from_name, "to": to_name, "error": str(exc), "from_pin": from_pin, "to_pin": to_pin}


def _load_object(path):
    if not path:
        return None
    return unreal.load_object(None, str(path))


def _pcg_set_description(settings, text):
    try:
        settings.description = str(text)
        return True
    except Exception:
        try:
            settings.set_editor_property("description", str(text))
            return True
        except Exception:
            return False


def _pcg_output_attribute_selector(attribute_name):
    selector = unreal.PCGAttributePropertyOutputSelector()
    selector.import_text('(AttributeName="{}")'.format(attribute_name))
    return selector


def _pcg_input_attribute_selector(attribute_name):
    selector = unreal.PCGAttributePropertyInputSelector()
    selector.import_text('(AttributeName="{}")'.format(attribute_name))
    return selector


def _pcg_constant_value(metadata_type, value):
    constant = unreal.PCGMetadataTypesConstantStruct()
    constant.set_editor_property("type", metadata_type)
    if metadata_type == unreal.PCGMetadataTypes.BOOLEAN:
        constant.set_editor_property("bool_value", bool(value))
    elif metadata_type == unreal.PCGMetadataTypes.SOFT_OBJECT_PATH:
        constant.set_editor_property("soft_object_path_value", unreal.SoftObjectPath(value))
    elif metadata_type == unreal.PCGMetadataTypes.INTEGER32:
        constant.set_editor_property("int32_value", int(value))
    elif metadata_type == unreal.PCGMetadataTypes.NAME:
        constant.set_editor_property("name_value", unreal.Name(value))
    elif metadata_type == unreal.PCGMetadataTypes.FLOAT:
        constant.set_editor_property("float_value", float(value))
    elif metadata_type == unreal.PCGMetadataTypes.DOUBLE:
        constant.set_editor_property("double_value", float(value))
    elif metadata_type == unreal.PCGMetadataTypes.STRING:
        constant.set_editor_property("string_value", str(value))
    else:
        raise ValueError("Unsupported PCG constant metadata type: {}".format(metadata_type))
    return constant


def _pcg_weighted_mesh_entry(mesh_path, material_path=None, weight=1):
    entry = unreal.PCGMeshSelectorWeightedEntry()
    text = entry.export_text()
    text = text.replace("StaticMesh=None", 'StaticMesh="{}"'.format(mesh_path))
    if material_path:
        text = text.replace("OverrideMaterials=", 'OverrideMaterials=("{}")'.format(material_path))
    entry.import_text(text)
    try:
        entry.set_editor_property("weight", int(weight))
    except Exception:
        pass
    return entry


def _material_object_path(material_key):
    if not material_key or material_key == "baked":
        return None
    asset_path = MATERIAL_DIR + "/" + str(material_key)
    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return None
    return asset_path + "." + str(material_key)


def _pcg_configure_static_mesh_spawner(settings, mesh_path, material_path=None):
    result = {}
    try:
        settings.set_mesh_selector_type(unreal.PCGMeshSelectorWeighted)
        result["selector_type"] = "PCGMeshSelectorWeighted"
    except Exception as exc:
        result["selector_type_error"] = str(exc)
    try:
        selector = settings.get_editor_property("mesh_selector_parameters")
        entries = selector.get_editor_property("mesh_entries")
        entries.clear()
        entries.append(_pcg_weighted_mesh_entry(mesh_path, material_path, weight=1))
        result["mesh_path"] = str(mesh_path)
        result["material_path"] = str(material_path) if material_path else None
        result["mesh_entries"] = len(selector.get_editor_property("mesh_entries"))
    except Exception as exc:
        result["mesh_entries_error"] = str(exc)
    try:
        settings.set_editor_property("synchronous_load", True)
        settings.set_editor_property("apply_mesh_bounds_to_points", True)
        result["spawner_flags"] = "synchronous_load, apply_mesh_bounds_to_points"
    except Exception as exc:
        result["spawner_flags_error"] = str(exc)
    return result


def _pcg_configure_string_filter(settings, attribute_name, value):
    result = {}
    try:
        settings.set_editor_property("target_attribute", _pcg_input_attribute_selector(attribute_name))
        settings.set_editor_property("operator", unreal.PCGAttributeFilterOperator.EQUAL)
        settings.set_editor_property("use_constant_threshold", True)
        settings.set_editor_property("use_spatial_query", False)
        settings.set_editor_property("attribute_types", _pcg_constant_value(unreal.PCGMetadataTypes.STRING, value))
        settings.set_editor_property("warn_on_data_missing_attribute", False)
        settings.set_editor_property("generate_output_data_even_if_empty", True)
        result["filter"] = "{} == {}".format(attribute_name, value)
    except Exception as exc:
        result["filter_error"] = str(exc)
    return result


def _pcg_configure_add_attribute(settings, attribute_name, metadata_type, value):
    result = {}
    try:
        settings.set_editor_property("copy_all_attributes", False)
        settings.set_editor_property("copy_all_domains", False)
        settings.set_editor_property("input_source", _pcg_input_attribute_selector("@Last"))
        settings.set_editor_property("output_target", _pcg_output_attribute_selector(attribute_name))
        settings.set_editor_property("attribute_types", _pcg_constant_value(metadata_type, value))
        result["attribute"] = str(attribute_name)
        result["metadata_type"] = str(metadata_type)
        result["value"] = str(value)
    except Exception as exc:
        result["add_attribute_error"] = str(exc)
    return result


def create_or_update_pcg_bridge_graph():
    ensure_dirs()
    graph = unreal.load_object(None, GRAPH_PATH + "." + GRAPH_NAME)
    created = False
    if not graph:
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            GRAPH_NAME,
            GRAPH_DIR,
            unreal.PCGGraph,
            unreal.PCGGraphFactory(),
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load PCG graph: " + GRAPH_PATH)

    for node in list(graph.nodes):
        graph.remove_node(node)
    node, settings = graph.add_node_of_type(unreal.PCGExecutePythonScriptSettings)
    node.set_node_position(120, 0)
    edge_reports = []
    try:
        node.node_title = "Cubeless Dungeon MVP Geometry Script Bridge"
    except Exception:
        pass
    try:
        graph.description = (
            "MVP bridge for Geometry Script-generated dungeon modules. "
            "The node calls CubelessDungeonPCGEntrypoint.py, which delegates to "
            "CubelessDungeonPCG.spawn_validation_dungeon(source='pcg_bridge'). "
            "StaticMeshActor validation output is exported as PCG spawner contract "
            "and native graph handoff JSON in Saved/MCP_Dungeon."
        )
    except Exception:
        pass
    settings_report = {}
    try:
        settings.description = (
            "Generate the validation dungeon from baked Geometry Script modules and export "
            "MeshKey-filtered PCG Static Mesh Spawner handoff metadata."
        )
        settings.set_editor_property("script_input_method", unreal.PCGPythonScriptInputMethod.FILE)
        settings.set_editor_property("script_path", _make_file_path(ENTRYPOINT_PATH))
        settings_report["script_input_method"] = str(settings.get_editor_property("script_input_method"))
        settings_report["script_path"] = str(settings.get_editor_property("script_path"))
    except Exception as exc:
        settings_report["error"] = str(exc)

    try:
        graph.get_input_node().set_node_position(-240, 0)
        graph.get_output_node().set_node_position(500, 0)
        edge_reports.append(_try_add_edge(graph, graph.get_input_node(), node, "In", "Execution Dependency"))
        edge_reports.append(_try_add_edge(graph, node, graph.get_output_node(), "Execution Dependency", "Out"))
    except Exception as exc:
        edge_reports.append({"ok": False, "error": str(exc)})

    try:
        graph.notify_graph_changed()
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(graph, only_if_is_dirty=False)
    return {
        "created": created,
        "graph_path": graph.get_path_name(),
        "entrypoint_path": ENTRYPOINT_PATH,
        "entrypoint_exists": os.path.exists(ENTRYPOINT_PATH),
        "node_count": len(graph.nodes),
        "edge_reports": edge_reports,
        "settings": settings_report,
    }


def _load_saved_pcg_graph_handoff():
    if not os.path.exists(PCG_GRAPH_HANDOFF_PATH):
        raise RuntimeError("PCG graph handoff JSON does not exist yet: " + PCG_GRAPH_HANDOFF_PATH)
    with open(PCG_GRAPH_HANDOFF_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_saved_native_point_source_report():
    if not os.path.exists(NATIVE_POINT_SOURCE_REPORT_PATH):
        raise RuntimeError("Native point-source JSON does not exist yet: " + NATIVE_POINT_SOURCE_REPORT_PATH)
    with open(NATIVE_POINT_SOURCE_REPORT_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _static_mesh_point_bounds(static_mesh_path, cache):
    if static_mesh_path in cache:
        return cache[static_mesh_path]
    default_bounds = {
        "min": unreal.Vector(-TILE * 0.5, -TILE * 0.5, -8.0),
        "max": unreal.Vector(TILE * 0.5, TILE * 0.5, WALL_HEIGHT),
        "source": "fallback",
    }
    mesh = _load_object(static_mesh_path)
    if not mesh:
        cache[static_mesh_path] = default_bounds
        return default_bounds
    try:
        bounds = mesh.get_bounds()
        origin = bounds.origin
        extent = bounds.box_extent
        result = {
            "min": unreal.Vector(origin.x - extent.x, origin.y - extent.y, origin.z - extent.z),
            "max": unreal.Vector(origin.x + extent.x, origin.y + extent.y, origin.z + extent.z),
            "source": "static_mesh_bounds",
        }
    except Exception:
        result = default_bounds
    cache[static_mesh_path] = result
    return result


def _pcg_point_from_native_point(point_record, bounds_cache, location_offset=None):
    transform_record = point_record.get("transform", {})
    location = transform_record.get("location", [0.0, 0.0, 0.0])
    rotation = transform_record.get("rotation", [0.0, 0.0, 0.0])
    scale = transform_record.get("scale", [1.0, 1.0, 1.0])
    offset = _vector3_list(location_offset)
    point = unreal.PCGPoint()
    transform = point.get_editor_property("transform")
    transform.set_editor_property(
        "translation",
        unreal.Vector(
            float(location[0]) + offset[0],
            float(location[1]) + offset[1],
            float(location[2]) + offset[2],
        ),
    )
    rotator = _actor_rotator(float(rotation[0]), float(rotation[1]), float(rotation[2]))
    transform.set_editor_property("rotation", rotator.quaternion())
    transform.set_editor_property("scale3d", unreal.Vector(float(scale[0]), float(scale[1]), float(scale[2])))
    point.set_editor_property("transform", transform)
    bounds = _static_mesh_point_bounds(point_record.get("static_mesh_path"), bounds_cache)
    point.set_editor_property("bounds_min", bounds["min"])
    point.set_editor_property("bounds_max", bounds["max"])
    point.set_editor_property("density", 1.0)
    point.set_editor_property("steepness", 1.0)
    point.set_editor_property("seed", int(point_record.get("point_index", 0)) & 0x7FFFFFFF)
    return point


def _native_point_source_branches(native_point_source_report):
    branches = {}
    for point in native_point_source_report.get("points", []):
        mesh_key = point.get("mesh_key") or "<missing>"
        material_key = point.get("material_key") or "baked"
        branch_key = (mesh_key, material_key)
        branch = branches.setdefault(
            branch_key,
            {
                "mesh_key": mesh_key,
                "material_key": material_key,
                "material_mode": "baked" if material_key == "baked" else "override",
                "static_mesh_path": point.get("static_mesh_path"),
                "points": [],
                "sample_labels": [],
            },
        )
        branch["points"].append(point)
        if len(branch["sample_labels"]) < 5:
            branch["sample_labels"].append(point.get("source_label"))
    return [
        dict(branch, branch_name="{}_{}".format(_pcg_safe_identifier(branch["mesh_key"]), _pcg_safe_identifier(branch["material_key"])))
        for _key, branch in sorted(
            branches.items(),
            key=lambda item: (-len(item[1]["points"]), str(item[0][0]), str(item[0][1])),
        )
    ]


def create_or_update_native_point_source_graph(
    native_point_source_report=None,
    graph_name=None,
    graph_path=None,
    graph_report_path=None,
    location_offset=None,
    graph_role="production",
):
    ensure_dirs()
    graph_name = graph_name or NATIVE_POINT_SOURCE_GRAPH_NAME
    graph_path = graph_path or NATIVE_POINT_SOURCE_GRAPH_PATH
    graph_report_path = graph_report_path or NATIVE_POINT_SOURCE_GRAPH_REPORT_PATH
    location_offset = _vector3_list(location_offset)
    report_source = native_point_source_report or _load_saved_native_point_source_report()
    branches = _native_point_source_branches(report_source)
    graph = unreal.load_object(None, graph_path + "." + graph_name)
    created = False
    if not graph:
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            graph_name,
            GRAPH_DIR,
            unreal.PCGGraph,
            unreal.PCGGraphFactory(),
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load native point-source PCG graph: " + graph_path)

    for node in list(graph.nodes):
        graph.remove_node(node)

    edges = []
    setup_errors = []
    branch_reports = []
    bounds_cache = {}
    merge_node, merge_settings = graph.add_node_of_type(unreal.PCGMergeSettings)
    merge_node.set_node_position(2300, 0)
    try:
        merge_node.node_title = "Merge material-safe native dungeon source points"
    except Exception:
        pass
    _pcg_set_description(
        merge_settings,
        "Merges CreatePoints branches that already carry DungeonMeshKey and material attributes. "
        "This graph outputs points only and does not spawn Static Meshes.",
    )

    attribute_specs_template = [
        ("DungeonMeshKey", unreal.PCGMetadataTypes.STRING, None),
        ("DungeonStaticMeshPath", unreal.PCGMetadataTypes.STRING, None),
        ("DynamicMeshPath", unreal.PCGMetadataTypes.SOFT_OBJECT_PATH, None),
        ("DungeonMaterialMode", unreal.PCGMetadataTypes.STRING, None),
        ("DungeonMaterialName", unreal.PCGMetadataTypes.STRING, None),
    ]
    create_node_count = 0
    add_attribute_node_count = 0
    pcg_point_count = 0
    for branch_index, branch in enumerate(branches):
        y = branch_index * 150
        branch_name = branch["branch_name"]
        mesh_key = branch["mesh_key"]
        material_key = branch["material_key"]
        static_mesh_path = branch.get("static_mesh_path")
        create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
        create_node.set_node_position(0, y)
        try:
            create_node.node_title = "Create source points {} / {}".format(mesh_key, material_key)
        except Exception:
            pass
        point_objects = [_pcg_point_from_native_point(point, bounds_cache, location_offset) for point in branch["points"]]
        try:
            create_settings.set_editor_property("points_to_create", point_objects)
            create_settings.set_editor_property("cull_points_outside_volume", False)
            _pcg_set_description(
                create_settings,
                "Native point-source branch for DungeonMeshKey={} material_key={} point_count={}. "
                "No mesh spawning happens in this graph. Location offset: [{:.1f}, {:.1f}, {:.1f}].".format(
                    mesh_key,
                    material_key,
                    len(point_objects),
                    location_offset[0],
                    location_offset[1],
                    location_offset[2],
                ),
            )
        except Exception as exc:
            setup_errors.append({"branch": branch_name, "node": "CreatePoints", "error": str(exc)})
        try:
            create_settings.set_editor_property("seed", 142857 + branch_index)
        except Exception:
            pass
        create_node_count += 1
        pcg_point_count += len(point_objects)

        attribute_values = {
            "DungeonMeshKey": mesh_key,
            "DungeonStaticMeshPath": static_mesh_path,
            "DynamicMeshPath": static_mesh_path,
            "DungeonMaterialMode": branch["material_mode"],
            "DungeonMaterialName": "" if material_key == "baked" else material_key,
        }
        previous_node = create_node
        branch_attribute_reports = []
        for attribute_index, (attribute_name, metadata_type, _value) in enumerate(attribute_specs_template):
            attr_node, attr_settings = graph.add_node_of_type(unreal.PCGAddAttributeSettings)
            attr_node.set_node_position(360 + attribute_index * 350, y)
            try:
                attr_node.node_title = "{} {}".format(branch_name, attribute_name)
            except Exception:
                pass
            value = attribute_values[attribute_name]
            property_updates = _pcg_configure_add_attribute(attr_settings, attribute_name, metadata_type, value)
            if any(str(key).endswith("_error") for key in property_updates):
                setup_errors.append({"branch": branch_name, "node": attribute_name, "error": property_updates})
            _pcg_set_description(
                attr_settings,
                "Attach {}={} to native dungeon point-source branch {}.".format(attribute_name, value, branch_name),
            )
            branch_attribute_reports.append(property_updates)
            edges.append(_try_add_edge(graph, previous_node, attr_node, "Out", "In"))
            previous_node = attr_node
            add_attribute_node_count += 1
        edges.append(_try_add_edge(graph, previous_node, merge_node, "Out", "In"))
        branch_reports.append(
            {
                "branch_name": branch_name,
                "mesh_key": mesh_key,
                "material_key": material_key,
                "material_mode": branch["material_mode"],
                "static_mesh_path": static_mesh_path,
                "point_count": len(point_objects),
                "sample_labels": branch["sample_labels"],
                "attribute_reports": branch_attribute_reports,
            }
        )

    graph.get_input_node().set_node_position(-360, 0)
    graph.get_output_node().set_node_position(2700, 0)
    edges.append(_try_add_edge(graph, merge_node, graph.get_output_node(), "Out", "Out"))
    try:
        graph.description = (
            "Native point-source candidate for the Cubeless dungeon. "
            "This graph creates material-safe point streams from Saved/MCP_Dungeon/"
            "CubelessDungeonMVP_NativePointSource_Report.json and outputs PCG points only. "
            "It is not connected to the Static Mesh Spawner skeleton yet. "
            "Graph role: {}; location offset: [{:.1f}, {:.1f}, {:.1f}].".format(
                graph_role,
                location_offset[0],
                location_offset[1],
                location_offset[2],
            )
        )
    except Exception:
        pass
    try:
        graph.notify_graph_changed()
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(graph, only_if_is_dirty=False)

    failed_edges = [edge for edge in edges if not edge.get("ok")]
    output_connected = any(
        edge.get("ok")
        and edge.get("to_pin") == "Out"
        and edge.get("from") == merge_node.get_name()
        for edge in edges
    )
    result = {
        "schema": "cubeless_pcg_dungeon_native_point_source_graph_v1"
        if graph_report_path == NATIVE_POINT_SOURCE_GRAPH_REPORT_PATH
        else "cubeless_pcg_dungeon_native_point_source_preview_graph_v1",
        "graph_path": graph.get_path_name(),
        "graph_name": graph_name,
        "graph_role": graph_role,
        "location_offset": location_offset,
        "created": created,
        "source_report_path": NATIVE_POINT_SOURCE_REPORT_PATH,
        "source_schema": report_source.get("schema"),
        "source_pass": bool(report_source.get("pass")),
        "branch_count": len(branches),
        "create_points_node_count": create_node_count,
        "add_attribute_node_count": add_attribute_node_count,
        "merge_node_count": 1,
        "static_mesh_spawner_node_count": 0,
        "node_count": len(graph.nodes),
        "edge_count": len(edges),
        "failed_edge_count": len(failed_edges),
        "setup_error_count": len(setup_errors),
        "pcg_point_count": pcg_point_count,
        "source_point_count": int(report_source.get("validation", {}).get("point_count", 0)),
        "source_group_count": int(report_source.get("validation", {}).get("group_count", 0)),
        "output_connected": output_connected,
        "spawns_static_meshes": False,
        "integration_policy": "This graph outputs native PCG points only. The Static Mesh Spawner skeleton remains disconnected until a subgraph/input integration pass is validated.",
        "attribute_names": [spec[0] for spec in attribute_specs_template],
        "failed_edges": failed_edges[:20],
        "setup_errors": setup_errors[:50],
        "branches": branch_reports,
        "pass": bool(
            report_source.get("pass")
            and len(branches) > 0
            and pcg_point_count == int(report_source.get("validation", {}).get("point_count", 0))
            and create_node_count == len(branches)
            and add_attribute_node_count == len(branches) * len(attribute_specs_template)
            and output_connected
            and not failed_edges
            and not setup_errors
        ),
    }
    os.makedirs(os.path.dirname(graph_report_path), exist_ok=True)
    with open(graph_report_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    unreal.log(
        "CubelessDungeonPCG native point-source graph: "
        + json.dumps(
            {
                "pass": result["pass"],
                "graph_role": result["graph_role"],
                "branch_count": result["branch_count"],
                "pcg_point_count": result["pcg_point_count"],
                "node_count": result["node_count"],
                "failed_edge_count": result["failed_edge_count"],
                "setup_error_count": result["setup_error_count"],
                "output_connected": result["output_connected"],
            },
            ensure_ascii=False,
        )
    )
    return result


def create_or_update_native_skeleton_graph(pcg_graph_handoff=None):
    ensure_dirs()
    handoff = pcg_graph_handoff or _load_saved_pcg_graph_handoff()
    streams = sorted(
        handoff.get("point_streams", []),
        key=lambda item: (-int(item.get("point_count", 0)), str(item.get("mesh_key", ""))),
    )
    graph = unreal.load_object(None, NATIVE_GRAPH_PATH + "." + NATIVE_GRAPH_NAME)
    created = False
    if not graph:
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            NATIVE_GRAPH_NAME,
            GRAPH_DIR,
            unreal.PCGGraph,
            unreal.PCGGraphFactory(),
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load native PCG skeleton graph: " + NATIVE_GRAPH_PATH)

    for node in list(graph.nodes):
        graph.remove_node(node)

    setup = {}
    edges = []
    missing_static_mesh_path = []
    merge_node, merge_settings = graph.add_node_of_type(unreal.PCGMergeSettings)
    merge_node.set_node_position(1300, 0)
    try:
        merge_node.node_title = "Material-safe MeshKey branch merge (not connected to Output)"
    except Exception:
        pass
    setup["merge"] = {
        "settings_class": merge_settings.get_class().get_name(),
        "description_set": _pcg_set_description(
            merge_settings,
            "Diagnostic merge for material-safe DungeonMeshKey Static Mesh Spawner branches. "
            "The merge is intentionally not connected to graph Output until a native point source is promoted.",
        ),
        "property_updates": {},
    }

    mesh_filter_count = 0
    material_filter_count = 0
    spawner_count = 0
    row_index = 0
    for stream in streams:
        mesh_key = stream.get("mesh_key")
        safe_key = _pcg_safe_identifier(mesh_key)
        point_count = int(stream.get("point_count", 0))
        static_mesh_path = stream.get("static_mesh_path")
        if not static_mesh_path:
            missing_static_mesh_path.append(mesh_key)
            continue
        y = row_index * 190
        mesh_filter_key = "filter_mesh_{}".format(safe_key)
        mesh_filter_node, mesh_filter_settings = graph.add_node_of_type(unreal.PCGAttributeFilteringSettings)
        mesh_filter_node.set_node_position(0, y)
        try:
            mesh_filter_node.node_title = "Filter DungeonMeshKey={}".format(mesh_key)
        except Exception:
            pass
        setup[mesh_filter_key] = {
            "settings_class": mesh_filter_settings.get_class().get_name(),
            "description_set": _pcg_set_description(
                mesh_filter_settings,
                "Keep only point stream {}: DungeonMeshKey == {}. Source point count in current handoff: {}.".format(
                    stream.get("stream_name"),
                    mesh_key,
                    point_count,
                ),
            ),
            "property_updates": _pcg_configure_string_filter(mesh_filter_settings, "DungeonMeshKey", mesh_key),
        }
        mesh_filter_count += 1
        edges.append(_try_add_edge(graph, graph.get_input_node(), mesh_filter_node, "In", "In"))

        material_splits = stream.get("material_splits", [])
        if material_splits:
            split_base_y = y - (max(len(material_splits) - 1, 0) * 52)
            for split_index, split in enumerate(material_splits):
                material_key = split.get("material_key")
                material_attribute = split.get("filter", {}).get("attribute") or "DungeonMaterialName"
                split_y = split_base_y + (split_index * 104)
                material_safe = _pcg_safe_identifier(material_key)
                material_filter_key = "filter_{}_{}".format(safe_key, material_safe)
                material_filter_node, material_filter_settings = graph.add_node_of_type(unreal.PCGAttributeFilteringSettings)
                material_filter_node.set_node_position(420, split_y)
                try:
                    material_filter_node.node_title = "Filter {} {}={}".format(mesh_key, material_attribute, material_key)
                except Exception:
                    pass
                setup[material_filter_key] = {
                    "settings_class": material_filter_settings.get_class().get_name(),
                    "description_set": _pcg_set_description(
                        material_filter_settings,
                        "Material-safe split for {}: {} == {}. Split point count: {}.".format(
                            mesh_key,
                            material_attribute,
                            material_key,
                            int(split.get("point_count", 0)),
                        ),
                    ),
                    "property_updates": _pcg_configure_string_filter(material_filter_settings, material_attribute, material_key),
                }
                material_filter_count += 1
                edges.append(_try_add_edge(graph, mesh_filter_node, material_filter_node, "InsideFilter", "In"))

                spawner_key = "spawn_{}_{}".format(safe_key, material_safe)
                spawner_node, spawner_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
                spawner_node.set_node_position(850, split_y)
                try:
                    spawner_node.node_title = "Spawn {} / {}".format(mesh_key, material_key)
                except Exception:
                    pass
                material_path = _material_object_path(material_key)
                setup[spawner_key] = {
                    "settings_class": spawner_settings.get_class().get_name(),
                    "description_set": _pcg_set_description(
                        spawner_settings,
                        "Material-safe native skeleton spawner for DungeonMeshKey={} and material key {}. "
                        "Static Mesh: {}. This is not connected to graph Output yet.".format(
                            mesh_key,
                            material_key,
                            static_mesh_path,
                        ),
                    ),
                    "property_updates": _pcg_configure_static_mesh_spawner(spawner_settings, static_mesh_path, material_path),
                }
                spawner_count += 1
                edges.append(_try_add_edge(graph, material_filter_node, spawner_node, "InsideFilter", "In"))
                edges.append(_try_add_edge(graph, spawner_node, merge_node, "Out", "In"))
            row_index += max(1, len(material_splits))
        else:
            material_key = stream.get("single_material_key")
            spawner_key = "spawn_{}".format(safe_key)
            spawner_node, spawner_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
            spawner_node.set_node_position(850, y)
            try:
                spawner_node.node_title = "Spawn DungeonMeshKey={}".format(mesh_key)
            except Exception:
                pass
            material_path = _material_object_path(material_key)
            setup[spawner_key] = {
                "settings_class": spawner_settings.get_class().get_name(),
                "description_set": _pcg_set_description(
                    spawner_settings,
                    "Native skeleton spawner for DungeonMeshKey={}. Static Mesh: {}. "
                    "Material key: {}. This is not connected to graph Output yet.".format(
                        mesh_key,
                        static_mesh_path,
                        material_key or "mesh default",
                    ),
                ),
                "property_updates": _pcg_configure_static_mesh_spawner(spawner_settings, static_mesh_path, material_path),
            }
            spawner_count += 1
            edges.append(_try_add_edge(graph, mesh_filter_node, spawner_node, "InsideFilter", "In"))
            edges.append(_try_add_edge(graph, spawner_node, merge_node, "Out", "In"))
            row_index += 1

    graph.get_input_node().set_node_position(-320, 0)
    graph.get_output_node().set_node_position(1660, 0)
    try:
        graph.description = (
            "Native skeleton for Cubeless dungeon MeshKey/material-safe Static Mesh Spawner promotion. "
            "Built from Saved/MCP_Dungeon/CubelessDungeonMVP_PCGGraphHandoff.json. "
            "Input -> filters -> spawners -> merge is authored, but merge is intentionally not connected to Output "
            "until a native point source replaces the Python bridge validation actors."
        )
    except Exception:
        pass
    try:
        graph.notify_graph_changed()
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(graph, only_if_is_dirty=False)

    setup_error_count = 0
    for item in setup.values():
        for key, value in item.get("property_updates", {}).items():
            if str(key).endswith("_error") or str(key) == "filter_error":
                if value:
                    setup_error_count += 1
    failed_edges = [edge for edge in edges if not edge.get("ok")]
    report = {
        "schema": "cubeless_pcg_dungeon_native_skeleton_graph_report_v1",
        "graph_path": graph.get_path_name(),
        "created": created,
        "source_handoff_path": PCG_GRAPH_HANDOFF_PATH,
        "source_handoff_schema": handoff.get("schema"),
        "source_handoff_pass": bool(handoff.get("pass")),
        "point_stream_count": len(streams),
        "mesh_filter_node_count": mesh_filter_count,
        "material_filter_node_count": material_filter_count,
        "static_mesh_spawner_node_count": spawner_count,
        "merge_node_count": 1,
        "node_count": len(graph.nodes),
        "edge_count": len(edges),
        "failed_edge_count": len(failed_edges),
        "missing_static_mesh_path_count": len(missing_static_mesh_path),
        "setup_error_count": setup_error_count,
        "output_connected": False,
        "output_policy": "Output is intentionally disconnected until native point-source promotion is implemented.",
        "expected_mesh_only_spawner_count": int(handoff.get("promotion_targets", {}).get("mesh_only_spawner_count", 0)),
        "expected_material_safe_spawner_count": int(handoff.get("promotion_targets", {}).get("material_safe_spawner_count", 0)),
        "material_variant_group_count": int(handoff.get("promotion_targets", {}).get("material_variant_group_count", 0)),
        "failed_edges": failed_edges[:20],
        "missing_static_mesh_path_keys": missing_static_mesh_path,
        "setup": setup,
        "pass": bool(
            handoff.get("pass")
            and len(streams) > 0
            and not missing_static_mesh_path
            and spawner_count == int(handoff.get("promotion_targets", {}).get("material_safe_spawner_count", 0))
            and not failed_edges
            and setup_error_count == 0
        ),
    }
    os.makedirs(os.path.dirname(NATIVE_GRAPH_REPORT_PATH), exist_ok=True)
    with open(NATIVE_GRAPH_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("CubelessDungeonPCG native skeleton graph: " + json.dumps(report, ensure_ascii=False))
    return report


def _safe_editor_property(obj, prop_name, default=None):
    try:
        return obj.get_editor_property(prop_name)
    except Exception:
        return default


def _object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _pcg_node_title(node):
    title = _safe_editor_property(node, "node_title", None)
    if title is not None:
        return str(title)
    try:
        return str(node.node_title)
    except Exception:
        return node.get_name()


def _pcg_node_description(node):
    try:
        return str(node.get_settings().description)
    except Exception:
        value = _safe_editor_property(node.get_settings(), "description", "")
        return str(value or "")


def _pcg_settings_class(node):
    try:
        return node.get_settings().get_class().get_name()
    except Exception:
        return ""


def _pcg_spawner_weighted_entries(node):
    settings = node.get_settings()
    selector_type = _object_path(_safe_editor_property(settings, "mesh_selector_type", None))
    params = _safe_editor_property(settings, "mesh_selector_parameters", None)
    params_class = ""
    if params:
        try:
            params_class = params.get_class().get_name()
        except Exception:
            params_class = type(params).__name__
    entries = []
    if params:
        try:
            iterator = list(_safe_editor_property(params, "mesh_entries", []))
        except Exception:
            iterator = []
        for entry in iterator:
            descriptor = _safe_editor_property(entry, "descriptor", None)
            mesh = _safe_editor_property(descriptor, "static_mesh", None) if descriptor else None
            materials = []
            if descriptor:
                try:
                    materials = [
                        _object_path(material)
                        for material in list(_safe_editor_property(descriptor, "override_materials", []))
                        if material
                    ]
                except Exception:
                    materials = []
            entries.append(
                {
                    "mesh": _object_path(mesh),
                    "materials": materials,
                    "weight": _safe_editor_property(entry, "weight", None),
                }
            )
    return {
        "selector_type": selector_type,
        "selector_parameters_class": params_class,
        "entries": entries,
    }


def _expected_native_skeleton_from_handoff(handoff):
    streams = sorted(
        handoff.get("point_streams", []),
        key=lambda item: (-int(item.get("point_count", 0)), str(item.get("mesh_key", ""))),
    )
    mesh_filter_titles = []
    material_filter_titles = []
    spawners = []
    for stream in streams:
        mesh_key = stream.get("mesh_key")
        static_mesh_path = stream.get("static_mesh_path")
        mesh_filter_titles.append("Filter DungeonMeshKey={}".format(mesh_key))
        material_splits = stream.get("material_splits", [])
        if material_splits:
            for split in material_splits:
                material_key = split.get("material_key")
                material_attribute = split.get("filter", {}).get("attribute") or "DungeonMaterialName"
                material_filter_titles.append("Filter {} {}={}".format(mesh_key, material_attribute, material_key))
                spawners.append(
                    {
                        "title": "Spawn {} / {}".format(mesh_key, material_key),
                        "mesh_key": mesh_key,
                        "material_key": material_key,
                        "expected_mesh": static_mesh_path,
                        "expected_material": _material_object_path(material_key),
                    }
                )
        else:
            material_key = stream.get("single_material_key")
            spawners.append(
                {
                    "title": "Spawn DungeonMeshKey={}".format(mesh_key),
                    "mesh_key": mesh_key,
                    "material_key": material_key,
                    "expected_mesh": static_mesh_path,
                    "expected_material": _material_object_path(material_key),
                }
            )
    return {
        "mesh_filter_titles": mesh_filter_titles,
        "material_filter_titles": material_filter_titles,
        "spawners": spawners,
    }


def create_or_update_native_integration_graph(
    pcg_graph_handoff=None,
    native_point_source_graph_report=None,
    graph_name=None,
    graph_path=None,
    graph_report_path=None,
    point_source_graph_name=None,
    point_source_graph_path=None,
    point_source_graph_report_path=None,
    graph_role="production",
):
    ensure_dirs()
    graph_name = graph_name or NATIVE_INTEGRATION_GRAPH_NAME
    graph_path = graph_path or NATIVE_INTEGRATION_GRAPH_PATH
    graph_report_path = graph_report_path or NATIVE_INTEGRATION_GRAPH_REPORT_PATH
    point_source_graph_name = point_source_graph_name or NATIVE_POINT_SOURCE_GRAPH_NAME
    point_source_graph_path = point_source_graph_path or NATIVE_POINT_SOURCE_GRAPH_PATH
    point_source_graph_report_path = point_source_graph_report_path or NATIVE_POINT_SOURCE_GRAPH_REPORT_PATH
    handoff = pcg_graph_handoff or _load_saved_pcg_graph_handoff()
    source_graph_report = native_point_source_graph_report or {}
    if not source_graph_report and os.path.exists(point_source_graph_report_path):
        with open(point_source_graph_report_path, "r", encoding="utf-8") as handle:
            source_graph_report = json.load(handle)
    streams = sorted(
        handoff.get("point_streams", []),
        key=lambda item: (-int(item.get("point_count", 0)), str(item.get("mesh_key", ""))),
    )
    point_source_graph = unreal.load_object(
        None,
        point_source_graph_path + "." + point_source_graph_name,
    )
    graph = unreal.load_object(None, graph_path + "." + graph_name)
    created = False
    if not graph:
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            graph_name,
            GRAPH_DIR,
            unreal.PCGGraph,
            unreal.PCGGraphFactory(),
        )
        created = bool(graph)
    if not graph:
        raise RuntimeError("Failed to create/load native integration PCG graph: " + graph_path)

    for node in list(graph.nodes):
        graph.remove_node(node)

    setup = {}
    edges = []
    missing_static_mesh_path = []
    subgraph_node_count = 0
    mesh_filter_count = 0
    material_filter_count = 0
    spawner_count = 0

    source_node, source_settings = graph.add_node_of_type(unreal.PCGSubgraphSettings)
    source_node.set_node_position(-420, 0)
    try:
        source_node.node_title = "Subgraph {}".format(point_source_graph_name)
    except Exception:
        pass
    source_updates = {
        "point_source_graph_loaded": bool(point_source_graph),
        "point_source_graph_path": point_source_graph.get_path_name() if point_source_graph else None,
    }
    try:
        source_settings.set_editor_property("subgraph_override", point_source_graph)
        source_updates["subgraph_override"] = point_source_graph.get_path_name() if point_source_graph else None
    except Exception as exc:
        source_updates["subgraph_override_error"] = str(exc)
    setup["point_source_subgraph"] = {
        "settings_class": source_settings.get_class().get_name(),
        "description_set": _pcg_set_description(
            source_settings,
            (
                "Runs {} to provide native dungeon points. "
                "This integration graph then filters those points into material-safe Static Mesh Spawner branches."
            ).format(point_source_graph_name),
        ),
        "property_updates": source_updates,
    }
    subgraph_node_count += 1

    merge_node, merge_settings = graph.add_node_of_type(unreal.PCGMergeSettings)
    merge_node.set_node_position(1720, 0)
    try:
        merge_node.node_title = "Merge native spawned dungeon meshes"
    except Exception:
        pass
    setup["merge"] = {
        "settings_class": merge_settings.get_class().get_name(),
        "description_set": _pcg_set_description(
            merge_settings,
            "Merges Static Mesh Spawner branches fed by the {} subgraph and connects to graph Output.".format(
                point_source_graph_name
            ),
        ),
        "property_updates": {},
    }

    row_index = 0
    for stream in streams:
        mesh_key = stream.get("mesh_key")
        safe_key = _pcg_safe_identifier(mesh_key)
        point_count = int(stream.get("point_count", 0))
        static_mesh_path = stream.get("static_mesh_path")
        if not static_mesh_path:
            missing_static_mesh_path.append(mesh_key)
            continue
        y = row_index * 190
        mesh_filter_key = "filter_mesh_{}".format(safe_key)
        mesh_filter_node, mesh_filter_settings = graph.add_node_of_type(unreal.PCGAttributeFilteringSettings)
        mesh_filter_node.set_node_position(0, y)
        try:
            mesh_filter_node.node_title = "Filter DungeonMeshKey={}".format(mesh_key)
        except Exception:
            pass
        setup[mesh_filter_key] = {
            "settings_class": mesh_filter_settings.get_class().get_name(),
            "description_set": _pcg_set_description(
                mesh_filter_settings,
                "Keep only point stream {} from NativePointSource: DungeonMeshKey == {}. "
                "Source point count in current handoff: {}.".format(
                    stream.get("stream_name"),
                    mesh_key,
                    point_count,
                ),
            ),
            "property_updates": _pcg_configure_string_filter(mesh_filter_settings, "DungeonMeshKey", mesh_key),
        }
        mesh_filter_count += 1
        edges.append(_try_add_edge(graph, source_node, mesh_filter_node, "Out", "In"))

        material_splits = stream.get("material_splits", [])
        if material_splits:
            split_base_y = y - (max(len(material_splits) - 1, 0) * 52)
            for split_index, split in enumerate(material_splits):
                material_key = split.get("material_key")
                material_attribute = split.get("filter", {}).get("attribute") or "DungeonMaterialName"
                split_y = split_base_y + (split_index * 104)
                material_safe = _pcg_safe_identifier(material_key)
                material_filter_key = "filter_{}_{}".format(safe_key, material_safe)
                material_filter_node, material_filter_settings = graph.add_node_of_type(unreal.PCGAttributeFilteringSettings)
                material_filter_node.set_node_position(520, split_y)
                try:
                    material_filter_node.node_title = "Filter {} {}={}".format(mesh_key, material_attribute, material_key)
                except Exception:
                    pass
                setup[material_filter_key] = {
                    "settings_class": material_filter_settings.get_class().get_name(),
                    "description_set": _pcg_set_description(
                        material_filter_settings,
                        "Material-safe split for {} from NativePointSource: {} == {}. Split point count: {}.".format(
                            mesh_key,
                            material_attribute,
                            material_key,
                            int(split.get("point_count", 0)),
                        ),
                    ),
                    "property_updates": _pcg_configure_string_filter(material_filter_settings, material_attribute, material_key),
                }
                material_filter_count += 1
                edges.append(_try_add_edge(graph, mesh_filter_node, material_filter_node, "InsideFilter", "In"))

                spawner_key = "spawn_{}_{}".format(safe_key, material_safe)
                spawner_node, spawner_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
                spawner_node.set_node_position(1080, split_y)
                try:
                    spawner_node.node_title = "Spawn {} / {}".format(mesh_key, material_key)
                except Exception:
                    pass
                material_path = _material_object_path(material_key)
                setup[spawner_key] = {
                    "settings_class": spawner_settings.get_class().get_name(),
                    "description_set": _pcg_set_description(
                        spawner_settings,
                        "Native integration spawner for DungeonMeshKey={} and material key {}. Static Mesh: {}.".format(
                            mesh_key,
                            material_key,
                            static_mesh_path,
                        ),
                    ),
                    "property_updates": _pcg_configure_static_mesh_spawner(spawner_settings, static_mesh_path, material_path),
                }
                spawner_count += 1
                edges.append(_try_add_edge(graph, material_filter_node, spawner_node, "InsideFilter", "In"))
                edges.append(_try_add_edge(graph, spawner_node, merge_node, "Out", "In"))
            row_index += max(1, len(material_splits))
        else:
            material_key = stream.get("single_material_key")
            spawner_key = "spawn_{}".format(safe_key)
            spawner_node, spawner_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
            spawner_node.set_node_position(1080, y)
            try:
                spawner_node.node_title = "Spawn DungeonMeshKey={}".format(mesh_key)
            except Exception:
                pass
            material_path = _material_object_path(material_key)
            setup[spawner_key] = {
                "settings_class": spawner_settings.get_class().get_name(),
                "description_set": _pcg_set_description(
                    spawner_settings,
                    "Native integration spawner for DungeonMeshKey={}. Static Mesh: {}. Material key: {}.".format(
                        mesh_key,
                        static_mesh_path,
                        material_key or "mesh default",
                    ),
                ),
                "property_updates": _pcg_configure_static_mesh_spawner(spawner_settings, static_mesh_path, material_path),
            }
            spawner_count += 1
            edges.append(_try_add_edge(graph, mesh_filter_node, spawner_node, "InsideFilter", "In"))
            edges.append(_try_add_edge(graph, spawner_node, merge_node, "Out", "In"))
            row_index += 1

    graph.get_input_node().set_node_position(-780, 0)
    graph.get_output_node().set_node_position(2080, 0)
    edges.append(_try_add_edge(graph, merge_node, graph.get_output_node(), "Out", "Out"))
    try:
        graph.description = (
            "Native PCG integration candidate for the Cubeless dungeon. "
            "Subgraph {} creates material-safe dungeon points, then this graph filters by "
            "DungeonMeshKey/DungeonMaterialName, spawns Static Meshes, merges branches, and connects to Output. "
            "The diagnostic NativeSkeleton graph remains output-disconnected. Graph role: {}.".format(
                point_source_graph_name,
                graph_role,
            )
        )
    except Exception:
        pass
    try:
        graph.notify_graph_changed()
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(graph, only_if_is_dirty=False)

    setup_error_count = 0
    for item in setup.values():
        for key, value in item.get("property_updates", {}).items():
            if str(key).endswith("_error") or str(key) == "filter_error":
                if value:
                    setup_error_count += 1
    failed_edges = [edge for edge in edges if not edge.get("ok")]
    output_connected = any(
        edge.get("ok")
        and edge.get("to_pin") == "Out"
        and edge.get("from") == merge_node.get_name()
        for edge in edges
    )
    report = {
        "schema": "cubeless_pcg_dungeon_native_integration_graph_report_v1"
        if graph_report_path == NATIVE_INTEGRATION_GRAPH_REPORT_PATH
        else "cubeless_pcg_dungeon_native_integration_preview_graph_report_v1",
        "graph_path": graph.get_path_name(),
        "graph_name": graph_name,
        "graph_role": graph_role,
        "created": created,
        "source_handoff_path": PCG_GRAPH_HANDOFF_PATH,
        "source_handoff_schema": handoff.get("schema"),
        "source_handoff_pass": bool(handoff.get("pass")),
        "source_point_graph_path": point_source_graph_path,
        "source_point_graph_loaded": bool(point_source_graph),
        "source_point_graph_report_path": point_source_graph_report_path,
        "source_point_graph_report_schema": source_graph_report.get("schema"),
        "source_point_graph_report_pass": bool(source_graph_report.get("pass")),
        "source_point_graph_point_count": int(source_graph_report.get("pcg_point_count", 0) or 0),
        "point_stream_count": len(streams),
        "subgraph_node_count": subgraph_node_count,
        "mesh_filter_node_count": mesh_filter_count,
        "material_filter_node_count": material_filter_count,
        "static_mesh_spawner_node_count": spawner_count,
        "merge_node_count": 1,
        "node_count": len(graph.nodes),
        "edge_count": len(edges),
        "failed_edge_count": len(failed_edges),
        "missing_static_mesh_path_count": len(missing_static_mesh_path),
        "setup_error_count": setup_error_count,
        "output_connected": output_connected,
        "input_node_connected": False,
        "spawns_static_meshes": True,
        "expected_mesh_only_spawner_count": int(handoff.get("promotion_targets", {}).get("mesh_only_spawner_count", 0)),
        "expected_material_safe_spawner_count": int(handoff.get("promotion_targets", {}).get("material_safe_spawner_count", 0)),
        "material_variant_group_count": int(handoff.get("promotion_targets", {}).get("material_variant_group_count", 0)),
        "failed_edges": failed_edges[:20],
        "missing_static_mesh_path_keys": missing_static_mesh_path,
        "setup": setup,
        "integration_policy": (
            "This graph is a native spawning candidate. NativeSkeleton remains a disconnected diagnostic skeleton; "
            "{} uses {} as a subgraph and connects spawned mesh branches to Output.".format(
                graph_name,
                point_source_graph_name,
            )
        ),
        "pass": bool(
            handoff.get("pass")
            and source_graph_report.get("pass")
            and point_source_graph
            and len(streams) > 0
            and not missing_static_mesh_path
            and subgraph_node_count == 1
            and mesh_filter_count == len(streams)
            and spawner_count == int(handoff.get("promotion_targets", {}).get("material_safe_spawner_count", 0))
            and output_connected
            and not failed_edges
            and setup_error_count == 0
        ),
    }
    os.makedirs(os.path.dirname(graph_report_path), exist_ok=True)
    with open(graph_report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log(
        "CubelessDungeonPCG native integration graph: "
        + json.dumps(
            {
                "pass": report["pass"],
                "graph_role": report["graph_role"],
                "node_count": report["node_count"],
                "edge_count": report["edge_count"],
                "subgraph_node_count": report["subgraph_node_count"],
                "static_mesh_spawner_node_count": report["static_mesh_spawner_node_count"],
                "failed_edge_count": report["failed_edge_count"],
                "setup_error_count": report["setup_error_count"],
                "output_connected": report["output_connected"],
            },
            ensure_ascii=False,
        )
    )
    return report


def create_or_update_native_integration_preview_graphs(preview_offset=None):
    ensure_dirs()
    preview_offset = _vector3_list(preview_offset, [14000.0, 0.0, 0.0])
    native_point_source_report = _load_saved_native_point_source_report()
    preview_point_source_graph_report = create_or_update_native_point_source_graph(
        native_point_source_report=native_point_source_report,
        graph_name=NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME,
        graph_path=NATIVE_POINT_SOURCE_PREVIEW_GRAPH_PATH,
        graph_report_path=NATIVE_POINT_SOURCE_PREVIEW_GRAPH_REPORT_PATH,
        location_offset=preview_offset,
        graph_role="preview_offset",
    )
    preview_integration_graph_report = create_or_update_native_integration_graph(
        native_point_source_graph_report=preview_point_source_graph_report,
        graph_name=NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME,
        graph_path=NATIVE_INTEGRATION_PREVIEW_GRAPH_PATH,
        graph_report_path=NATIVE_INTEGRATION_PREVIEW_GRAPH_REPORT_PATH,
        point_source_graph_name=NATIVE_POINT_SOURCE_PREVIEW_GRAPH_NAME,
        point_source_graph_path=NATIVE_POINT_SOURCE_PREVIEW_GRAPH_PATH,
        point_source_graph_report_path=NATIVE_POINT_SOURCE_PREVIEW_GRAPH_REPORT_PATH,
        graph_role="preview_offset",
    )
    return {
        "schema": "cubeless_pcg_dungeon_native_integration_preview_graphs_v1",
        "preview_offset": preview_offset,
        "point_source_preview_graph": preview_point_source_graph_report,
        "integration_preview_graph": preview_integration_graph_report,
        "point_source_preview_graph_report_path": NATIVE_POINT_SOURCE_PREVIEW_GRAPH_REPORT_PATH,
        "integration_preview_graph_report_path": NATIVE_INTEGRATION_PREVIEW_GRAPH_REPORT_PATH,
        "pass": bool(
            preview_point_source_graph_report.get("pass")
            and preview_integration_graph_report.get("pass")
        ),
    }


def audit_native_skeleton_graph(pcg_graph_handoff=None):
    handoff = pcg_graph_handoff or _load_saved_pcg_graph_handoff()
    expected = _expected_native_skeleton_from_handoff(handoff)
    graph = unreal.load_object(None, NATIVE_GRAPH_PATH + "." + NATIVE_GRAPH_NAME)
    latest_graph_report = {}
    if os.path.exists(NATIVE_GRAPH_REPORT_PATH):
        with open(NATIVE_GRAPH_REPORT_PATH, "r", encoding="utf-8") as handle:
            latest_graph_report = json.load(handle)

    class_counts = {}
    nodes_by_title = {}
    duplicate_titles = []
    missing_description_titles = []
    spawner_summaries = []
    graph_exists = bool(graph)
    if graph:
        for node in list(graph.nodes):
            class_name = _pcg_settings_class(node)
            title = _pcg_node_title(node)
            description = _pcg_node_description(node)
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            if title in nodes_by_title:
                duplicate_titles.append(title)
            nodes_by_title[title] = node
            if not description.strip():
                missing_description_titles.append(title)
            if class_name == "PCGStaticMeshSpawnerSettings":
                spawner_summaries.append(
                    dict(
                        {
                            "title": title,
                            "description_present": bool(description.strip()),
                        },
                        **_pcg_spawner_weighted_entries(node),
                    )
                )

    expected_filter_titles = expected["mesh_filter_titles"] + expected["material_filter_titles"]
    missing_filter_titles = [title for title in expected_filter_titles if title not in nodes_by_title]
    missing_spawner_titles = [item["title"] for item in expected["spawners"] if item["title"] not in nodes_by_title]
    unexpected_spawner_titles = [
        item["title"]
        for item in spawner_summaries
        if item["title"] not in {expected_item["title"] for expected_item in expected["spawners"]}
    ]
    spawner_mismatches = []
    for expected_spawner in expected["spawners"]:
        node = nodes_by_title.get(expected_spawner["title"])
        if not node:
            continue
        actual = _pcg_spawner_weighted_entries(node)
        entries = actual.get("entries", [])
        mismatch = {
            "title": expected_spawner["title"],
            "mesh_key": expected_spawner["mesh_key"],
            "material_key": expected_spawner["material_key"],
            "expected_mesh": expected_spawner["expected_mesh"],
            "expected_material": expected_spawner["expected_material"],
            "actual_entries": entries,
            "problems": [],
        }
        if "PCGMeshSelectorWeighted" not in str(actual.get("selector_type")) and actual.get("selector_parameters_class") != "PCGMeshSelectorWeighted":
            mismatch["problems"].append("selector is not PCGMeshSelectorWeighted")
        if len(entries) != 1:
            mismatch["problems"].append("expected exactly one weighted mesh entry")
        else:
            actual_entry = entries[0]
            if actual_entry.get("mesh") != expected_spawner["expected_mesh"]:
                mismatch["problems"].append("static mesh mismatch")
            expected_material = expected_spawner["expected_material"]
            actual_materials = actual_entry.get("materials", [])
            if expected_material:
                if expected_material not in actual_materials:
                    mismatch["problems"].append("material override mismatch")
            elif actual_materials:
                mismatch["problems"].append("unexpected material override")
        if mismatch["problems"]:
            spawner_mismatches.append(mismatch)

    expected_class_counts = {
        "PCGMergeSettings": 1,
        "PCGAttributeFilteringSettings": len(expected_filter_titles),
        "PCGStaticMeshSpawnerSettings": len(expected["spawners"]),
    }
    class_count_mismatches = {}
    for class_name, expected_count in expected_class_counts.items():
        actual_count = int(class_counts.get(class_name, 0))
        if actual_count != expected_count:
            class_count_mismatches[class_name] = {
                "expected": expected_count,
                "actual": actual_count,
            }

    report = {
        "schema": "cubeless_pcg_dungeon_native_skeleton_audit_v1",
        "graph_path": NATIVE_GRAPH_PATH,
        "graph_exists": graph_exists,
        "source_handoff_path": PCG_GRAPH_HANDOFF_PATH,
        "source_handoff_schema": handoff.get("schema"),
        "source_handoff_pass": bool(handoff.get("pass")),
        "latest_native_graph_report_path": NATIVE_GRAPH_REPORT_PATH,
        "latest_native_graph_report_pass": bool(latest_graph_report.get("pass")),
        "latest_native_graph_output_connected": bool(latest_graph_report.get("output_connected")),
        "expected_counts": {
            "mesh_filter_titles": len(expected["mesh_filter_titles"]),
            "material_filter_titles": len(expected["material_filter_titles"]),
            "spawner_titles": len(expected["spawners"]),
            "class_counts": expected_class_counts,
        },
        "actual_counts": {
            "node_count": len(graph.nodes) if graph else 0,
            "class_counts": dict(sorted(class_counts.items())),
            "spawner_count": len(spawner_summaries),
        },
        "missing_filter_title_count": len(missing_filter_titles),
        "missing_spawner_title_count": len(missing_spawner_titles),
        "unexpected_spawner_title_count": len(unexpected_spawner_titles),
        "spawner_mismatch_count": len(spawner_mismatches),
        "class_count_mismatch_count": len(class_count_mismatches),
        "duplicate_title_count": len(duplicate_titles),
        "missing_description_count": len(missing_description_titles),
        "missing_filter_titles": missing_filter_titles[:60],
        "missing_spawner_titles": missing_spawner_titles[:60],
        "unexpected_spawner_titles": unexpected_spawner_titles[:60],
        "spawner_mismatches": spawner_mismatches[:60],
        "class_count_mismatches": class_count_mismatches,
        "duplicate_titles": duplicate_titles[:60],
        "missing_description_titles": missing_description_titles[:60],
        "spawner_summaries_sample": spawner_summaries[:20],
        "pass": bool(
            graph_exists
            and handoff.get("pass")
            and latest_graph_report.get("pass")
            and latest_graph_report.get("output_connected") is False
            and not missing_filter_titles
            and not missing_spawner_titles
            and not unexpected_spawner_titles
            and not spawner_mismatches
            and not class_count_mismatches
            and not duplicate_titles
            and not missing_description_titles
        ),
    }
    os.makedirs(os.path.dirname(NATIVE_GRAPH_AUDIT_REPORT_PATH), exist_ok=True)
    with open(NATIVE_GRAPH_AUDIT_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("CubelessDungeonPCG native skeleton audit: " + json.dumps(report, ensure_ascii=False))
    return report


def audit_native_integration_graph(pcg_graph_handoff=None):
    handoff = pcg_graph_handoff or _load_saved_pcg_graph_handoff()
    expected = _expected_native_skeleton_from_handoff(handoff)
    graph = unreal.load_object(None, NATIVE_INTEGRATION_GRAPH_PATH + "." + NATIVE_INTEGRATION_GRAPH_NAME)
    latest_graph_report = {}
    if os.path.exists(NATIVE_INTEGRATION_GRAPH_REPORT_PATH):
        with open(NATIVE_INTEGRATION_GRAPH_REPORT_PATH, "r", encoding="utf-8") as handle:
            latest_graph_report = json.load(handle)

    class_counts = {}
    nodes_by_title = {}
    duplicate_titles = []
    missing_description_titles = []
    spawner_summaries = []
    subgraph_summaries = []
    graph_exists = bool(graph)
    if graph:
        for node in list(graph.nodes):
            class_name = _pcg_settings_class(node)
            title = _pcg_node_title(node)
            description = _pcg_node_description(node)
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            if title in nodes_by_title:
                duplicate_titles.append(title)
            nodes_by_title[title] = node
            if not description.strip():
                missing_description_titles.append(title)
            if class_name == "PCGStaticMeshSpawnerSettings":
                spawner_summaries.append(
                    dict(
                        {
                            "title": title,
                            "description_present": bool(description.strip()),
                        },
                        **_pcg_spawner_weighted_entries(node),
                    )
                )
            elif class_name == "PCGSubgraphSettings":
                settings = node.get_settings()
                subgraph_summaries.append(
                    {
                        "title": title,
                        "description_present": bool(description.strip()),
                        "subgraph_override": _object_path(_safe_editor_property(settings, "subgraph_override", None)),
                    }
                )

    expected_filter_titles = expected["mesh_filter_titles"] + expected["material_filter_titles"]
    missing_filter_titles = [title for title in expected_filter_titles if title not in nodes_by_title]
    missing_spawner_titles = [item["title"] for item in expected["spawners"] if item["title"] not in nodes_by_title]
    unexpected_spawner_titles = [
        item["title"]
        for item in spawner_summaries
        if item["title"] not in {expected_item["title"] for expected_item in expected["spawners"]}
    ]
    spawner_mismatches = []
    for expected_spawner in expected["spawners"]:
        node = nodes_by_title.get(expected_spawner["title"])
        if not node:
            continue
        actual = _pcg_spawner_weighted_entries(node)
        entries = actual.get("entries", [])
        mismatch = {
            "title": expected_spawner["title"],
            "mesh_key": expected_spawner["mesh_key"],
            "material_key": expected_spawner["material_key"],
            "expected_mesh": expected_spawner["expected_mesh"],
            "expected_material": expected_spawner["expected_material"],
            "actual_entries": entries,
            "problems": [],
        }
        if "PCGMeshSelectorWeighted" not in str(actual.get("selector_type")) and actual.get("selector_parameters_class") != "PCGMeshSelectorWeighted":
            mismatch["problems"].append("selector is not PCGMeshSelectorWeighted")
        if len(entries) != 1:
            mismatch["problems"].append("expected exactly one weighted mesh entry")
        else:
            actual_entry = entries[0]
            if actual_entry.get("mesh") != expected_spawner["expected_mesh"]:
                mismatch["problems"].append("static mesh mismatch")
            expected_material = expected_spawner["expected_material"]
            actual_materials = actual_entry.get("materials", [])
            if expected_material:
                if expected_material not in actual_materials:
                    mismatch["problems"].append("material override mismatch")
            elif actual_materials:
                mismatch["problems"].append("unexpected material override")
        if mismatch["problems"]:
            spawner_mismatches.append(mismatch)

    expected_class_counts = {
        "PCGSubgraphSettings": 1,
        "PCGMergeSettings": 1,
        "PCGAttributeFilteringSettings": len(expected_filter_titles),
        "PCGStaticMeshSpawnerSettings": len(expected["spawners"]),
    }
    class_count_mismatches = {}
    for class_name, expected_count in expected_class_counts.items():
        actual_count = int(class_counts.get(class_name, 0))
        if actual_count != expected_count:
            class_count_mismatches[class_name] = {
                "expected": expected_count,
                "actual": actual_count,
            }

    expected_subgraph_path = NATIVE_POINT_SOURCE_GRAPH_PATH + "." + NATIVE_POINT_SOURCE_GRAPH_NAME
    subgraph_override_mismatches = [
        item
        for item in subgraph_summaries
        if item.get("subgraph_override") != expected_subgraph_path
    ]

    report = {
        "schema": "cubeless_pcg_dungeon_native_integration_audit_v1",
        "graph_path": NATIVE_INTEGRATION_GRAPH_PATH,
        "graph_exists": graph_exists,
        "source_handoff_path": PCG_GRAPH_HANDOFF_PATH,
        "source_handoff_schema": handoff.get("schema"),
        "source_handoff_pass": bool(handoff.get("pass")),
        "latest_native_integration_report_path": NATIVE_INTEGRATION_GRAPH_REPORT_PATH,
        "latest_native_integration_report_pass": bool(latest_graph_report.get("pass")),
        "latest_native_integration_output_connected": bool(latest_graph_report.get("output_connected")),
        "expected_counts": {
            "mesh_filter_titles": len(expected["mesh_filter_titles"]),
            "material_filter_titles": len(expected["material_filter_titles"]),
            "spawner_titles": len(expected["spawners"]),
            "class_counts": expected_class_counts,
        },
        "actual_counts": {
            "node_count": len(graph.nodes) if graph else 0,
            "class_counts": dict(sorted(class_counts.items())),
            "spawner_count": len(spawner_summaries),
            "subgraph_count": len(subgraph_summaries),
        },
        "missing_filter_title_count": len(missing_filter_titles),
        "missing_spawner_title_count": len(missing_spawner_titles),
        "unexpected_spawner_title_count": len(unexpected_spawner_titles),
        "spawner_mismatch_count": len(spawner_mismatches),
        "class_count_mismatch_count": len(class_count_mismatches),
        "duplicate_title_count": len(duplicate_titles),
        "missing_description_count": len(missing_description_titles),
        "subgraph_override_mismatch_count": len(subgraph_override_mismatches),
        "missing_filter_titles": missing_filter_titles[:60],
        "missing_spawner_titles": missing_spawner_titles[:60],
        "unexpected_spawner_titles": unexpected_spawner_titles[:60],
        "spawner_mismatches": spawner_mismatches[:60],
        "class_count_mismatches": class_count_mismatches,
        "duplicate_titles": duplicate_titles[:60],
        "missing_description_titles": missing_description_titles[:60],
        "subgraph_summaries": subgraph_summaries,
        "subgraph_override_mismatches": subgraph_override_mismatches,
        "spawner_summaries_sample": spawner_summaries[:20],
        "pass": bool(
            graph_exists
            and handoff.get("pass")
            and latest_graph_report.get("pass")
            and latest_graph_report.get("output_connected") is True
            and not missing_filter_titles
            and not missing_spawner_titles
            and not unexpected_spawner_titles
            and not spawner_mismatches
            and not class_count_mismatches
            and not duplicate_titles
            and not missing_description_titles
            and not subgraph_override_mismatches
        ),
    }
    os.makedirs(os.path.dirname(NATIVE_INTEGRATION_AUDIT_REPORT_PATH), exist_ok=True)
    with open(NATIVE_INTEGRATION_AUDIT_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("CubelessDungeonPCG native integration audit: " + json.dumps(report, ensure_ascii=False))
    return report


def generate_layout(seed=142857, room_count=11, branch_chance_percent=100, max_loop_edges=2):
    rng = random.Random(seed)
    branch_chance_percent = _coerce_int(branch_chance_percent, DEFAULT_DUNGEON_CONFIG["branch_chance_percent"], 0, 100)
    max_loop_edges = _coerce_int(max_loop_edges, DEFAULT_DUNGEON_CONFIG["max_loop_edges"], 0, 16)
    rooms = []
    occupied = set()
    attempts = 0
    while len(rooms) < room_count and attempts < 300:
        attempts += 1
        width = rng.randint(3, 5)
        height = rng.randint(3, 5)
        x = rng.randint(-10, 10)
        y = rng.randint(-8, 8)
        proposed = set((ix, iy) for ix in range(x, x + width) for iy in range(y, y + height))
        padded = set((ix, iy) for ix in range(x - 1, x + width + 1) for iy in range(y - 1, y + height + 1))
        if occupied.intersection(padded):
            continue
        room = {
            "id": len(rooms),
            "x": x,
            "y": y,
            "w": width,
            "h": height,
            "cells": proposed,
            "center": (x + width // 2, y + height // 2),
        }
        rooms.append(room)
        occupied.update(proposed)

    if len(rooms) < 2:
        raise RuntimeError("Failed to generate enough dungeon rooms")

    connected = [rooms[0]]
    remaining = rooms[1:]
    edges = []
    while remaining:
        best = None
        for a in connected:
            ax, ay = a["center"]
            for b in remaining:
                bx, by = b["center"]
                dist = abs(ax - bx) + abs(ay - by)
                if best is None or dist < best[0]:
                    best = (dist, a, b)
        _dist, a, b = best
        edges.append((a["id"], b["id"]))
        connected.append(b)
        remaining.remove(b)

    loop_candidates = []
    existing = set(tuple(sorted(edge)) for edge in edges)
    for index, a in enumerate(rooms):
        ax, ay = a["center"]
        for b in rooms[index + 1:]:
            pair = tuple(sorted((a["id"], b["id"])))
            if pair in existing:
                continue
            bx, by = b["center"]
            loop_candidates.append((abs(ax - bx) + abs(ay - by), pair))
    loop_candidates.sort()
    added_loop_edges = 0
    for _dist, pair in loop_candidates:
        if added_loop_edges >= max_loop_edges:
            break
        if rng.randint(1, 100) > branch_chance_percent:
            continue
        edges.append(pair)
        added_loop_edges += 1

    cells = {}
    for room in rooms:
        for cell in room["cells"]:
            cells[cell] = {"kind": "room", "room_id": room["id"]}

    corridor_cells = set()
    for a_id, b_id in edges:
        a = rooms[a_id]
        b = rooms[b_id]
        ax, ay = a["center"]
        bx, by = b["center"]
        if rng.random() < 0.5:
            x_range = range(min(ax, bx), max(ax, bx) + 1)
            for x in x_range:
                corridor_cells.add((x, ay))
            y_range = range(min(ay, by), max(ay, by) + 1)
            for y in y_range:
                corridor_cells.add((bx, y))
        else:
            y_range = range(min(ay, by), max(ay, by) + 1)
            for y in y_range:
                corridor_cells.add((ax, y))
            x_range = range(min(ax, bx), max(ax, bx) + 1)
            for x in x_range:
                corridor_cells.add((x, by))

    for cell in corridor_cells:
        if cell not in cells:
            cells[cell] = {"kind": "corridor", "room_id": -1}

    start_room = rooms[0]
    exit_room = max(rooms, key=lambda room: abs(room["center"][0] - start_room["center"][0]) + abs(room["center"][1] - start_room["center"][1]))
    return {
        "seed": seed,
        "rooms": rooms,
        "edges": edges,
        "branch_chance_percent": branch_chance_percent,
        "max_loop_edges": max_loop_edges,
        "added_loop_edges": added_loop_edges,
        "cells": cells,
        "start_room_id": start_room["id"],
        "exit_room_id": exit_room["id"],
    }


def _room_graph_adjacency(layout):
    adjacency = {room["id"]: set() for room in layout["rooms"]}
    for a_id, b_id in layout["edges"]:
        adjacency[int(a_id)].add(int(b_id))
        adjacency[int(b_id)].add(int(a_id))
    return adjacency


def _shortest_room_path(layout, start_room_id=None, exit_room_id=None):
    adjacency = _room_graph_adjacency(layout)
    start_room_id = layout["start_room_id"] if start_room_id is None else int(start_room_id)
    exit_room_id = layout["exit_room_id"] if exit_room_id is None else int(exit_room_id)
    parents = {start_room_id: None}
    queue = deque([start_room_id])
    while queue:
        room_id = queue.popleft()
        if room_id == exit_room_id:
            break
        for neighbor in sorted(adjacency.get(room_id, [])):
            if neighbor not in parents:
                parents[neighbor] = room_id
                queue.append(neighbor)
    if exit_room_id not in parents:
        return [start_room_id]
    path = []
    cursor = exit_room_id
    while cursor is not None:
        path.append(cursor)
        cursor = parents[cursor]
    path.reverse()
    return path


def _room_distances_from(adjacency, start_room_ids):
    distances = {}
    queue = deque()
    for room_id in start_room_ids:
        room_id = int(room_id)
        distances[room_id] = 0
        queue.append(room_id)
    while queue:
        room_id = queue.popleft()
        for neighbor in sorted(adjacency.get(room_id, [])):
            if neighbor not in distances:
                distances[neighbor] = distances[room_id] + 1
                queue.append(neighbor)
    return distances


def _nearest_main_path_index(room_id, main_path, adjacency):
    distances = _room_distances_from(adjacency, [room_id])
    best = None
    for index, path_room_id in enumerate(main_path):
        distance = distances.get(path_room_id, 9999)
        candidate = (distance, index)
        if best is None or candidate < best:
            best = candidate
    return best[1] if best else 0


def _add_room_role(room_roles, role_counts, room_id, role):
    roles = room_roles.setdefault(int(room_id), [])
    if role not in roles:
        roles.append(role)
        role_counts[role] = role_counts.get(role, 0) + 1


def assign_room_progression(layout, config=None):
    config = dict(DEFAULT_DUNGEON_CONFIG if config is None else config)
    adjacency = _room_graph_adjacency(layout)
    main_path = _shortest_room_path(layout)
    main_index = {room_id: index for index, room_id in enumerate(main_path)}
    side_room_ids = [room["id"] for room in layout["rooms"] if room["id"] not in main_index]
    side_room_ids.sort(key=lambda room_id: (_nearest_main_path_index(room_id, main_path, adjacency), room_id))

    locked_door_count = _coerce_int(config.get("locked_door_count"), DEFAULT_DUNGEON_CONFIG["locked_door_count"], 0, 8)
    key_count = _coerce_int(config.get("key_count"), DEFAULT_DUNGEON_CONFIG["key_count"], 0, 8)
    shop_count = _coerce_int(config.get("shop_count"), DEFAULT_DUNGEON_CONFIG["shop_count"], 0, 6)
    chest_count = _coerce_int(config.get("chest_count"), DEFAULT_DUNGEON_CONFIG["chest_count"], 0, 16)
    enemy_count = _coerce_int(config.get("enemy_count"), DEFAULT_DUNGEON_CONFIG["enemy_count"], 0, 32)
    boss_enabled = _coerce_int(config.get("boss_enabled"), DEFAULT_DUNGEON_CONFIG["boss_enabled"], 0, 1) > 0

    locked_indices = []
    if len(main_path) > 1 and locked_door_count > 0:
        cursor = max(0, len(main_path) - 2)
        while cursor >= 0 and len(locked_indices) < locked_door_count:
            locked_indices.append(cursor)
            cursor -= 2
        locked_indices = sorted(set(locked_indices))
    locked_door_specs = [
        {
            "path_index": index,
            "before_room_id": main_path[index],
            "after_room_id": main_path[index + 1],
        }
        for index in locked_indices
        if index + 1 < len(main_path)
    ]
    first_locked_index = min(locked_indices) if locked_indices else len(main_path) - 1

    room_roles = {}
    role_counts = {}
    used_room_ids = set()
    _add_room_role(room_roles, role_counts, layout["start_room_id"], "start")
    _add_room_role(room_roles, role_counts, layout["exit_room_id"], "exit")
    used_room_ids.update([layout["start_room_id"], layout["exit_room_id"]])
    if boss_enabled:
        _add_room_role(room_roles, role_counts, layout["exit_room_id"], "boss")

    early_side_rooms = [
        room_id
        for room_id in side_room_ids
        if _nearest_main_path_index(room_id, main_path, adjacency) <= first_locked_index
    ]
    key_candidates = early_side_rooms + [
        room_id for room_id in main_path[1:first_locked_index + 1] if room_id not in used_room_ids
    ]
    key_room_ids = []
    for room_id in key_candidates:
        if room_id in used_room_ids:
            continue
        _add_room_role(room_roles, role_counts, room_id, "key")
        used_room_ids.add(room_id)
        key_room_ids.append(room_id)
        if len(key_room_ids) >= key_count:
            break

    shop_room_ids = []
    for room_id in side_room_ids + list(reversed(main_path[1:-1])):
        if room_id in used_room_ids:
            continue
        _add_room_role(room_roles, role_counts, room_id, "shop")
        used_room_ids.add(room_id)
        shop_room_ids.append(room_id)
        if len(shop_room_ids) >= shop_count:
            break

    treasure_room_ids = []
    for room_id in side_room_ids + main_path[1:-1]:
        if room_id in used_room_ids:
            continue
        _add_room_role(room_roles, role_counts, room_id, "treasure")
        used_room_ids.add(room_id)
        treasure_room_ids.append(room_id)
        if len(treasure_room_ids) >= chest_count:
            break

    enemy_room_ids = []
    combat_candidates = [
        room["id"]
        for room in layout["rooms"]
        if room["id"] not in used_room_ids and room["id"] not in (layout["start_room_id"], layout["exit_room_id"])
    ]
    combat_candidates.sort(key=lambda room_id: (main_index.get(room_id, 999), room_id))
    for room_id in combat_candidates:
        _add_room_role(room_roles, role_counts, room_id, "combat")
        used_room_ids.add(room_id)
        enemy_room_ids.append(room_id)
        if len(enemy_room_ids) >= enemy_count:
            break

    for spec in locked_door_specs:
        _add_room_role(room_roles, role_counts, spec["after_room_id"], "locked_after")

    key_access_indices = [
        _nearest_main_path_index(room_id, main_path, adjacency) for room_id in key_room_ids
    ]
    expected_locked_count = min(max(0, len(main_path) - 1), locked_door_count)
    progression_pass = bool(len(main_path) >= 2 and len(locked_door_specs) == expected_locked_count)
    if locked_door_specs and key_count > 0:
        progression_pass = progression_pass and bool(key_access_indices) and min(key_access_indices) <= first_locked_index
    if boss_enabled:
        progression_pass = progression_pass and "boss" in room_roles.get(layout["exit_room_id"], [])

    return {
        "main_path_room_ids": main_path,
        "main_path_room_count": len(main_path),
        "side_room_ids": side_room_ids,
        "side_room_count": len(side_room_ids),
        "locked_door_specs": locked_door_specs,
        "key_room_ids": key_room_ids,
        "shop_room_ids": shop_room_ids,
        "treasure_room_ids": treasure_room_ids,
        "enemy_room_ids": enemy_room_ids,
        "boss_room_id": layout["exit_room_id"] if boss_enabled else None,
        "room_roles": {str(room_id): roles for room_id, roles in sorted(room_roles.items())},
        "role_counts": role_counts,
        "key_access_main_path_indices": key_access_indices,
        "first_locked_main_path_index": first_locked_index if locked_door_specs else None,
        "pass": progression_pass,
    }


def _cell_text(cell):
    return "{},{}".format(int(cell[0]), int(cell[1]))


def _world_xy(cell):
    cell_size = _grid_cell_size()
    return [float(cell[0]) * cell_size, float(cell[1]) * cell_size]


def _room_roles_for(progression, room_id):
    if room_id is None or int(room_id) < 0:
        return []
    return list(progression.get("room_roles", {}).get(str(int(room_id)), []))


def _dungeon_actor_tags(seed, module, cell=None, room_id=None, cell_kind=None, roles=None, extra=None):
    tags = [
        "DungeonGenerated",
        "DungeonModule={}".format(module),
        "DungeonSeed={}".format(int(seed)),
    ]
    if cell is not None:
        tags.append("DungeonCell={}".format(_cell_text(cell)))
    if room_id is not None and int(room_id) >= 0:
        tags.append("DungeonRoomId={}".format(int(room_id)))
    if cell_kind:
        tags.append("DungeonCellKind={}".format(cell_kind))
    for role in roles or []:
        tags.append("DungeonRole={}".format(role))
    if extra:
        tags.extend(str(value) for value in extra)
    return tags


def _apply_actor_tags(actor, tags):
    actor.tags = [unreal.Name(str(tag)) for tag in tags if str(tag)]
    return actor


def _room_main_path_index(progression, room_id):
    try:
        return progression["main_path_room_ids"].index(int(room_id))
    except ValueError:
        return -1


def _minimap_symbol(room_id, kind, room_center_roles):
    if kind == "corridor":
        return "."
    roles = room_center_roles.get(int(room_id), [])
    priority = [
        ("start", "S"),
        ("boss", "B"),
        ("exit", "X"),
        ("key", "K"),
        ("shop", "H"),
        ("treasure", "T"),
        ("combat", "E"),
        ("locked_after", "L"),
    ]
    for role, symbol in priority:
        if role in roles:
            return symbol
    return "R"


def build_minimap_text(layout, progression):
    cells = layout["cells"]
    if not cells:
        return "empty dungeon"
    min_x = min(cell[0] for cell in cells)
    max_x = max(cell[0] for cell in cells)
    min_y = min(cell[1] for cell in cells)
    max_y = max(cell[1] for cell in cells)
    center_to_room_id = {tuple(room["center"]): room["id"] for room in layout["rooms"]}
    room_center_roles = {
        room_id: _room_roles_for(progression, room_id)
        for room_id in center_to_room_id.values()
    }
    lines = [
        "Cubeless Dungeon MVP Minimap",
        "Legend: S=start X=exit B=boss K=key H=shop T=treasure E=combat L=locked-after R=room .=corridor",
        "Seed: {}".format(layout["seed"]),
        "Bounds: x {}..{}, y {}..{}".format(min_x, max_x, min_y, max_y),
        "",
    ]
    for y in range(max_y, min_y - 1, -1):
        row = []
        for x in range(min_x, max_x + 1):
            cell = (x, y)
            if cell not in cells:
                row.append(" ")
                continue
            data = cells[cell]
            if cell in center_to_room_id:
                row.append(_minimap_symbol(center_to_room_id[cell], data["kind"], room_center_roles))
            elif data["kind"] == "corridor":
                row.append(".")
            else:
                row.append("R")
        lines.append("".join(row).rstrip())
    return "\n".join(lines) + "\n"


def _encounter_profile_for_room(layout, progression, room_id):
    room_id = int(room_id)
    roles = _room_roles_for(progression, room_id)
    main_index = _room_main_path_index(progression, room_id)
    lock_state = "after_gate" if "locked_after" in roles else "none"
    if "start" in roles:
        kind = "safe"
        tier = "start"
        reward = "none"
        spawn_budget = 0
    elif "boss" in roles:
        kind = "boss"
        tier = "final"
        reward = "exit_unlock"
        spawn_budget = 1
    elif "key" in roles:
        kind = "utility"
        tier = "key_reward"
        reward = "key"
        spawn_budget = 0
        lock_state = "pre_gate"
    elif "shop" in roles:
        kind = "utility"
        tier = "shop"
        reward = "shop"
        spawn_budget = 0
    elif "treasure" in roles:
        kind = "reward"
        tier = "treasure"
        reward = "treasure"
        spawn_budget = 0
    elif "combat" in roles:
        kind = "combat"
        reward = "minor"
        if main_index >= 3:
            tier = "elite"
            spawn_budget = 4
        elif main_index >= 1:
            tier = "standard"
            spawn_budget = 3
        else:
            tier = "light"
            spawn_budget = 2
    elif "exit" in roles:
        kind = "safe"
        tier = "exit"
        reward = "exit"
        spawn_budget = 0
    else:
        kind = "ambient"
        tier = "side" if room_id in progression["side_room_ids"] else "main"
        reward = "none"
        spawn_budget = 0
    return {
        "room_id": room_id,
        "encounter_id": "D{:d}_R{:02d}".format(int(layout["seed"]), room_id),
        "kind": kind,
        "tier": tier,
        "reward": reward,
        "lock_state": lock_state,
        "spawn_budget": spawn_budget,
        "roles": roles,
        "main_path_index": main_index,
        "is_side_room": room_id in progression["side_room_ids"],
    }


def assign_encounter_profiles(layout, progression):
    return {
        int(room["id"]): _encounter_profile_for_room(layout, progression, room["id"])
        for room in layout["rooms"]
    }


def _room_size_class(room):
    area = int(room["w"]) * int(room["h"])
    if area <= 12:
        return "small"
    if area <= 18:
        return "medium"
    return "large"


def _room_archetype_for_room(layout, progression, encounter_profiles, adjacency, room):
    room_id = int(room["id"])
    roles = _room_roles_for(progression, room_id)
    role_set = set(roles)
    main_index = _room_main_path_index(progression, room_id)
    route_kind = "main" if main_index >= 0 else "side"
    encounter = encounter_profiles.get(room_id)
    degree = len(adjacency.get(room_id, []))
    if "start" in role_set:
        archetype = "start_chamber"
        theme = "entry"
    elif "boss" in role_set:
        archetype = "boss_exit_chamber"
        theme = "finale"
    elif "key" in role_set:
        archetype = "key_room"
        theme = "progression"
    elif "shop" in role_set:
        archetype = "shop_room"
        theme = "utility"
    elif "treasure" in role_set:
        archetype = "treasure_vault"
        theme = "reward"
    elif "combat" in role_set and route_kind == "main":
        archetype = "main_combat_room"
        theme = "combat"
    elif "combat" in role_set:
        archetype = "side_combat_room"
        theme = "combat"
    elif degree >= 3:
        archetype = "junction_room"
        theme = "connector"
    elif route_kind == "side":
        archetype = "side_room"
        theme = "ambient"
    else:
        archetype = "main_room"
        theme = "ambient"
    return {
        "room_id": room_id,
        "archetype": archetype,
        "theme": theme,
        "size_class": _room_size_class(room),
        "area_cells": int(room["w"]) * int(room["h"]),
        "route_kind": route_kind,
        "main_path_index": int(main_index),
        "graph_degree": int(degree),
        "roles": roles,
        "encounter_id": encounter["encounter_id"] if encounter else None,
        "encounter_kind": encounter["kind"] if encounter else None,
        "encounter_tier": encounter["tier"] if encounter else None,
    }


def assign_room_archetypes(layout, progression, encounter_profiles):
    adjacency = _room_graph_adjacency(layout)
    return {
        int(room["id"]): _room_archetype_for_room(layout, progression, encounter_profiles, adjacency, room)
        for room in layout["rooms"]
    }


def _room_archetype_tags(profile):
    if not profile:
        return []
    return [
        "DungeonRoomArchetype={}".format(profile["archetype"]),
        "DungeonRoomTheme={}".format(profile["theme"]),
        "DungeonRoomSizeClass={}".format(profile["size_class"]),
        "DungeonRoomAreaCells={}".format(profile["area_cells"]),
        "DungeonRoomGraphDegree={}".format(profile["graph_degree"]),
    ]


ROOM_VARIANT_BY_ARCHETYPE = {
    "start_chamber": ("entry_focus_inlay", "room_variant_entry_inlay"),
    "main_combat_room": ("combat_partition", "room_variant_combat_partition"),
    "side_combat_room": ("combat_partition", "room_variant_combat_partition"),
    "key_room": ("progression_rune", "room_variant_progression_rune"),
    "shop_room": ("utility_market", "room_variant_utility_market"),
    "treasure_vault": ("reward_border", "room_variant_reward_border"),
    "boss_exit_chamber": ("finale_ring", "room_variant_finale_ring"),
    "junction_room": ("ambient_rubble", "room_variant_ambient_rubble"),
    "side_room": ("ambient_rubble", "room_variant_ambient_rubble"),
    "main_room": ("ambient_rubble", "room_variant_ambient_rubble"),
}


def _room_shape_family(room, archetype):
    width = int(room["w"])
    height = int(room["h"])
    area = width * height
    if archetype == "boss_exit_chamber":
        return "arena"
    if archetype == "treasure_vault":
        return "vault"
    if width >= height + 2:
        return "wide"
    if height >= width + 2:
        return "tall"
    if area >= 20:
        return "large_square"
    if area <= 12:
        return "compact"
    return "balanced"


def _room_shape_for_room(layout, progression, room_archetypes, room):
    room_id = int(room["id"])
    archetype = room_archetypes.get(room_id, {})
    archetype_name = str(archetype.get("archetype", "main_room"))
    family = _room_shape_family(room, archetype_name)
    width = int(room["w"])
    height = int(room["h"])
    axis = "x" if width > height else ("y" if height > width else "center")
    main_index = _room_main_path_index(progression, room_id)
    route_kind = "main" if main_index >= 0 else "side"
    variant_kind, mesh_key = ROOM_VARIANT_BY_ARCHETYPE.get(
        archetype_name,
        ROOM_VARIANT_BY_ARCHETYPE["main_room"],
    )
    if variant_kind == "combat_partition" and axis == "y":
        yaw = 90.0
    elif variant_kind == "utility_market" and axis == "x":
        yaw = 90.0
    elif variant_kind == "reward_border":
        yaw = 45.0 if family == "vault" else 0.0
    else:
        yaw = 0.0
    shape_name = "{}_{}".format(archetype_name, family)
    return {
        "room_id": room_id,
        "shape_name": shape_name,
        "shape_family": family,
        "shape_axis": axis,
        "width_cells": width,
        "height_cells": height,
        "area_cells": width * height,
        "aspect_ratio": round(float(width) / float(max(1, height)), 3),
        "route_kind": route_kind,
        "main_path_index": int(main_index),
        "archetype": archetype_name,
        "variant_kind": variant_kind,
        "variant_mesh_key": mesh_key,
        "variant_yaw": float(yaw),
    }


def assign_room_shapes(layout, progression, room_archetypes):
    return {
        int(room["id"]): _room_shape_for_room(layout, progression, room_archetypes, room)
        for room in layout["rooms"]
    }


def _room_shape_tags(profile):
    if not profile:
        return []
    return [
        "DungeonRoomShape={}".format(profile["shape_name"]),
        "DungeonRoomShapeFamily={}".format(profile["shape_family"]),
        "DungeonRoomShapeAxis={}".format(profile["shape_axis"]),
        "DungeonRoomVariantKind={}".format(profile["variant_kind"]),
        "DungeonRoomVariantMeshKey={}".format(profile["variant_mesh_key"]),
    ]


def _room_shape_counts(room_shapes):
    counts = {}
    for profile in room_shapes.values():
        family = profile["shape_family"]
        counts[family] = counts.get(family, 0) + 1
    return counts


THEME_MATERIAL_BY_NAME = {
    "entry": "M_Dungeon_Theme_EntryStone",
    "combat": "M_Dungeon_Theme_CombatStone",
    "progression": "M_Dungeon_Theme_KeyStone",
    "utility": "M_Dungeon_Theme_UtilityStone",
    "reward": "M_Dungeon_Theme_RewardStone",
    "finale": "M_Dungeon_Theme_FinaleStone",
    "ambient": "M_Dungeon_Theme_AmbientStone",
    "connector": "M_Dungeon_Theme_ConnectorStone",
    "corridor": "M_Dungeon_Theme_CorridorStone",
}


def _room_theme_from_archetype(profile):
    if not profile:
        return None
    theme_name = str(profile.get("theme", "ambient"))
    return {
        "room_id": int(profile["room_id"]),
        "theme_name": theme_name,
        "theme_role": str(profile.get("archetype", "main_room")),
        "material_name": THEME_MATERIAL_BY_NAME.get(theme_name, THEME_MATERIAL_BY_NAME["ambient"]),
        "archetype": str(profile.get("archetype", "main_room")),
        "size_class": str(profile.get("size_class", "medium")),
        "route_kind": str(profile.get("route_kind", "main")),
        "main_path_index": int(profile.get("main_path_index", -1)),
    }


def assign_room_themes(room_archetypes):
    return {
        int(room_id): _room_theme_from_archetype(profile)
        for room_id, profile in sorted(room_archetypes.items())
    }


def _corridor_theme():
    return {
        "room_id": -1,
        "theme_name": "corridor",
        "theme_role": "connector",
        "material_name": THEME_MATERIAL_BY_NAME["corridor"],
        "archetype": "corridor",
        "size_class": "connector",
        "route_kind": "connector",
        "main_path_index": -1,
    }


def _theme_for_cell(room_themes, room_id, cell_kind=None):
    if room_id is not None and int(room_id) >= 0:
        return room_themes.get(int(room_id))
    if cell_kind == "corridor":
        return _corridor_theme()
    return None


def _theme_tags(theme):
    if not theme:
        return []
    return [
        "DungeonThemeName={}".format(theme["theme_name"]),
        "DungeonThemeMaterial={}".format(theme["material_name"]),
        "DungeonThemeRole={}".format(theme["theme_role"]),
    ]


def _theme_material(materials, theme):
    if not theme:
        return None
    return materials.get(theme.get("material_name"))


def _theme_counts(room_themes):
    counts = {}
    for theme in room_themes.values():
        theme_name = theme["theme_name"]
        counts[theme_name] = counts.get(theme_name, 0) + 1
    return counts


LIGHT_PROFILE_BY_THEME = {
    "entry": {"profile": "entry_soft_green", "color": (142, 220, 154, 255), "intensity": 27.0, "radius": 984.0, "height": 250.0},
    "combat": {"profile": "combat_low_amber", "color": (255, 151, 96, 255), "intensity": 23.25, "radius": 912.0, "height": 238.0},
    "progression": {"profile": "key_cyan_focus", "color": (102, 238, 255, 255), "intensity": 28.5, "radius": 840.0, "height": 252.0},
    "utility": {"profile": "shop_teal_warm", "color": (108, 236, 190, 255), "intensity": 25.5, "radius": 936.0, "height": 244.0},
    "reward": {"profile": "reward_gold_pool", "color": (255, 196, 94, 255), "intensity": 27.75, "radius": 876.0, "height": 246.0},
    "finale": {"profile": "finale_violet_focus", "color": (212, 106, 255, 255), "intensity": 33.0, "radius": 1032.0, "height": 262.0},
    "ambient": {"profile": "ambient_cool_fill", "color": (178, 190, 205, 255), "intensity": 19.5, "radius": 840.0, "height": 240.0},
    "connector": {"profile": "connector_cool_fill", "color": (166, 196, 222, 255), "intensity": 18.75, "radius": 840.0, "height": 238.0},
}


def _light_profile_for_theme(theme):
    theme_name = str(theme.get("theme_name", "ambient")) if theme else "ambient"
    return LIGHT_PROFILE_BY_THEME.get(theme_name, LIGHT_PROFILE_BY_THEME["ambient"])


def _light_color(profile):
    color = profile.get("color", (255, 220, 180, 255))
    return unreal.Color(int(color[0]), int(color[1]), int(color[2]), int(color[3]))


def _detail_anchor_templates(archetype):
    templates = {
        "start_chamber": [
            ("entry_focus", "center", 0.0),
            ("start_arch", "north_wall", 180.0),
        ],
        "boss_exit_chamber": [
            ("boss_focus", "center", 0.0),
            ("exit_frame_detail", "south_wall", 0.0),
            ("finale_side_detail", "east_wall", -90.0),
        ],
        "key_room": [
            ("key_pedestal_detail", "center", 0.0),
            ("key_room_brazier", "north_wall", 180.0),
        ],
        "shop_room": [
            ("shop_counter", "center", 0.0),
            ("supply_shelf", "west_wall", 90.0),
            ("shop_sign", "north_wall", 180.0),
        ],
        "treasure_vault": [
            ("treasure_plinth", "center", 0.0),
            ("vault_trim", "north_wall", 180.0),
        ],
        "main_combat_room": [
            ("combat_cover_left", "west_wall", 90.0),
            ("combat_cover_right", "east_wall", -90.0),
        ],
        "side_combat_room": [
            ("side_cover", "west_wall", 90.0),
            ("side_torch", "north_wall", 180.0),
        ],
        "junction_room": [
            ("junction_marker", "center", 0.0),
            ("junction_trim", "north_wall", 180.0),
        ],
        "side_room": [
            ("ambient_ruin", "center", 0.0),
        ],
        "main_room": [
            ("ambient_trim", "north_wall", 180.0),
        ],
    }
    return templates.get(archetype, templates["main_room"])


def _detail_socket_offset(room, socket):
    cell_size = _grid_cell_size()
    half_x = max(cell_size * 0.35, float(room["w"]) * cell_size * 0.5 - _scaled_xy(150.0))
    half_y = max(cell_size * 0.35, float(room["h"]) * cell_size * 0.5 - _scaled_xy(150.0))
    offsets = {
        "center": unreal.Vector(0.0, 0.0, 116.0),
        "north_wall": unreal.Vector(0.0, half_y, 120.0),
        "south_wall": unreal.Vector(0.0, -half_y, 120.0),
        "east_wall": unreal.Vector(half_x, 0.0, 120.0),
        "west_wall": unreal.Vector(-half_x, 0.0, 120.0),
        "north_east": unreal.Vector(half_x, half_y, 116.0),
        "north_west": unreal.Vector(-half_x, half_y, 116.0),
        "south_east": unreal.Vector(half_x, -half_y, 116.0),
        "south_west": unreal.Vector(-half_x, -half_y, 116.0),
    }
    return offsets.get(socket, offsets["center"])


DETAIL_MESH_BY_KIND = {
    "entry_focus": "detail_pedestal",
    "start_arch": "detail_arch",
    "boss_focus": "detail_boss_focus",
    "exit_frame_detail": "detail_arch",
    "finale_side_detail": "detail_wall_trim",
    "key_pedestal_detail": "detail_pedestal",
    "key_room_brazier": "detail_brazier",
    "shop_counter": "detail_counter",
    "supply_shelf": "detail_wall_trim",
    "shop_sign": "detail_sign",
    "treasure_plinth": "detail_pedestal",
    "vault_trim": "detail_wall_trim",
    "combat_cover_left": "detail_cover",
    "combat_cover_right": "detail_cover",
    "side_cover": "detail_cover",
    "side_torch": "detail_brazier",
    "junction_marker": "detail_pedestal",
    "junction_trim": "detail_wall_trim",
    "ambient_ruin": "detail_cover",
    "ambient_trim": "detail_wall_trim",
}


def _detail_mesh_key(detail_kind):
    return DETAIL_MESH_BY_KIND.get(str(detail_kind), "detail_pedestal")


def _detail_mesh_location(anchor_location):
    return unreal.Vector(float(anchor_location.x), float(anchor_location.y), 0.0)


def _encounter_tags(profile):
    if not profile:
        return []
    return [
        "DungeonEncounterId={}".format(profile["encounter_id"]),
        "DungeonEncounterKind={}".format(profile["kind"]),
        "DungeonEncounterTier={}".format(profile["tier"]),
        "DungeonRewardKind={}".format(profile["reward"]),
        "DungeonLockState={}".format(profile["lock_state"]),
        "DungeonSpawnBudget={}".format(profile["spawn_budget"]),
    ]


def assign_lock_key_links(layout, progression):
    key_room_ids = [int(room_id) for room_id in progression.get("key_room_ids", [])]
    links = []
    for index, spec in enumerate(progression.get("locked_door_specs", [])):
        key_room_id = key_room_ids[min(index, len(key_room_ids) - 1)] if key_room_ids else None
        lock_id = "D{:d}_Lock_{:03d}".format(int(layout["seed"]), index)
        key_id = "D{:d}_Key_{:03d}".format(int(layout["seed"]), min(index, len(key_room_ids) - 1)) if key_room_id is not None else "None"
        links.append(
            {
                "lock_id": lock_id,
                "lock_index": int(index),
                "path_index": int(spec["path_index"]),
                "before_room_id": int(spec["before_room_id"]),
                "after_room_id": int(spec["after_room_id"]),
                "required_key_id": key_id,
                "key_room_id": int(key_room_id) if key_room_id is not None else None,
            }
        )
    return links


def _lock_tags(link):
    if not link:
        return []
    return [
        "DungeonLockId={}".format(link["lock_id"]),
        "DungeonRequiredKeyId={}".format(link["required_key_id"]),
        "DungeonLockIndex={}".format(link["lock_index"]),
        "DungeonLockPathIndex={}".format(link["path_index"]),
        "DungeonLockBeforeRoomId={}".format(link["before_room_id"]),
        "DungeonLockAfterRoomId={}".format(link["after_room_id"]),
    ]


def _key_tags_for_room(lock_links, room_id):
    links = [link for link in lock_links if link.get("key_room_id") == int(room_id)]
    if not links:
        return []
    key_id = links[0]["required_key_id"]
    return [
        "DungeonKeyId={}".format(key_id),
        "DungeonUnlocksLockIds={}".format("|".join(link["lock_id"] for link in links)),
        "DungeonUnlockCount={}".format(len(links)),
    ]


def _encounter_spawn_kind(profile):
    if not profile:
        return "none"
    if profile["kind"] == "boss":
        return "boss"
    if profile["kind"] == "combat":
        return "enemy"
    return profile["kind"]


def _encounter_spawn_offset(room, slot_index):
    pattern = [
        (0.00, 0.00),
        (0.42, 0.00),
        (-0.42, 0.00),
        (0.00, 0.42),
        (0.00, -0.42),
        (0.30, 0.30),
        (-0.30, 0.30),
        (0.30, -0.30),
        (-0.30, -0.30),
    ]
    normal_x, normal_y = pattern[int(slot_index) % len(pattern)]
    wave = int(slot_index) // len(pattern)
    scale = 1.0 + float(wave) * 0.35
    cell_size = _grid_cell_size()
    max_x = max(_scaled_xy(80.0), float(room["w"]) * cell_size * 0.5 - _scaled_xy(128.0))
    max_y = max(_scaled_xy(80.0), float(room["h"]) * cell_size * 0.5 - _scaled_xy(128.0))
    return unreal.Vector(max_x * normal_x * scale, max_y * normal_y * scale, 0.0)


def _reward_anchor_kind(profile):
    if not profile:
        return None
    reward = str(profile.get("reward", "none"))
    if reward in ("key", "shop", "treasure", "exit_unlock"):
        return reward
    return None


def _reward_interaction_kind(reward_kind):
    return {
        "key": "pickup",
        "shop": "shop",
        "treasure": "chest",
        "exit_unlock": "exit_unlock",
    }.get(reward_kind, "interact")


def _reward_anchor_offset(reward_kind):
    offsets = {
        "key": unreal.Vector(-_scaled_xy(138.0), _scaled_xy(132.0), 0.0),
        "shop": unreal.Vector(_scaled_xy(138.0), -_scaled_xy(132.0), 0.0),
        "treasure": unreal.Vector(_scaled_xy(132.0), _scaled_xy(124.0), 0.0),
        "exit_unlock": unreal.Vector(0.0, -_scaled_xy(156.0), 0.0),
    }
    return offsets.get(reward_kind, unreal.Vector(0.0, 0.0, 0.0))


def write_gameplay_exports(layout, progression, encounter_profiles, room_archetypes, room_themes, room_shapes, lock_key_links, config, marker_specs, volume_records, door_records, connector_detail_records, corridor_detail_records, room_variant_records, spawn_records, route_records, encounter_spawn_records, reward_records, theme_light_records, playtest_records, nav_waypoint_records, detail_records, detail_mesh_records, pcg_spawner_contract, pcg_graph_handoff, native_point_source_contract, counts, connectivity):
    cells = layout["cells"]
    rooms = []
    for room in layout["rooms"]:
        room_id = int(room["id"])
        center = room["center"]
        rooms.append(
            {
                "id": room_id,
                "bounds_grid": {
                    "x": int(room["x"]),
                    "y": int(room["y"]),
                    "w": int(room["w"]),
                    "h": int(room["h"]),
                },
                "center_grid": [int(center[0]), int(center[1])],
                "center_world": _world_xy(center),
                "roles": _room_roles_for(progression, room_id),
                "main_path_index": _room_main_path_index(progression, room_id),
                "is_side_room": room_id in progression["side_room_ids"],
                "encounter": encounter_profiles.get(room_id),
                "archetype": room_archetypes.get(room_id),
                "theme": room_themes.get(room_id),
                "shape": room_shapes.get(room_id),
            }
        )

    marker_role_by_label = {
        "Start": "start",
        "Exit": "exit",
        "Boss": "boss",
        "Key": "key",
        "Shop": "shop",
        "Chest": "treasure",
        "Enemy": "combat",
    }
    markers = []
    for label, room_id, _material_name, offset in marker_specs:
        center = _room_center(layout, room_id)
        markers.append(
            {
                "label": label,
                "role": marker_role_by_label.get(label, label.lower()),
                "room_id": int(room_id),
                "room_center_grid": [int(center[0]), int(center[1])],
                "offset_world": [float(offset.x), float(offset.y), float(offset.z)],
            }
        )

    data = {
        "schema": "cubeless_pcg_dungeon_gameplay_data_v1",
        "root": ROOT,
        "level_path": LEVEL_PATH,
        "seed": int(layout["seed"]),
        "config": {
            "room_count": int(config["room_count"]),
            "ceiling_stride": int(config["ceiling_stride"]),
            "chest_count": int(config["chest_count"]),
            "enemy_count": int(config["enemy_count"]),
            "key_count": int(config["key_count"]),
            "shop_count": int(config["shop_count"]),
            "locked_door_count": int(config["locked_door_count"]),
            "boss_enabled": int(config["boss_enabled"]),
            "branch_chance_percent": int(config["branch_chance_percent"]),
            "max_loop_edges": int(config["max_loop_edges"]),
            "grid_cell_size": int(config["grid_cell_size"]),
            "corridor_width": int(config["corridor_width"]),
            "grid_scale": float(config.get("grid_scale", 1.0)),
            "corridor_width_scale": float(config.get("corridor_width_scale", 1.0)),
            "base_module_tile_size": float(config.get("base_module_tile_size", TILE)),
            "generation_metrics": dict(config.get("generation_metrics", {})),
            "use_ceiling": int(config["use_ceiling"]),
            "use_theme_materials": int(config["use_theme_materials"]),
            "preview_mode": int(config["preview_mode"]),
            "parameter_application_status": dict(config.get("parameter_application_status", {})),
        },
        "tile_size": float(config.get("grid_cell_size", TILE)),
        "base_module_tile_size": float(config.get("base_module_tile_size", TILE)),
        "rooms": rooms,
        "cells": [
            {
                "grid": [int(cell[0]), int(cell[1])],
                "world": _world_xy(cell),
                "kind": cell_data["kind"],
                "room_id": int(cell_data["room_id"]),
            }
            for cell, cell_data in sorted(cells.items())
        ],
        "room_edges": [
            {
                "a": int(a_id),
                "b": int(b_id),
                "is_main_path_edge": (
                    int(a_id) in progression["main_path_room_ids"]
                    and int(b_id) in progression["main_path_room_ids"]
                    and abs(
                        progression["main_path_room_ids"].index(int(a_id))
                        - progression["main_path_room_ids"].index(int(b_id))
                    )
                    == 1
                ),
            }
            for a_id, b_id in layout["edges"]
        ],
        "progression": progression,
        "lock_key_links": lock_key_links,
        "encounters": [
            encounter_profiles[room_id]
            for room_id in sorted(encounter_profiles.keys())
        ],
        "room_archetypes": [
            room_archetypes[room_id]
            for room_id in sorted(room_archetypes.keys())
        ],
        "room_themes": [
            room_themes[room_id]
            for room_id in sorted(room_themes.keys())
        ],
        "room_shapes": [
            room_shapes[room_id]
            for room_id in sorted(room_shapes.keys())
        ],
        "markers": markers,
        "volumes": volume_records,
        "door_points": door_records,
        "connector_details": connector_detail_records,
        "corridor_details": corridor_detail_records,
        "room_variant_details": room_variant_records,
        "spawn_points": spawn_records,
        "route_points": route_records,
        "encounter_spawn_points": encounter_spawn_records,
        "reward_points": reward_records,
        "theme_lights": theme_light_records,
        "playtest_points": playtest_records,
        "navigation_waypoints": nav_waypoint_records,
        "detail_points": detail_records,
        "detail_meshes": detail_mesh_records,
        "pcg_spawner_contract": pcg_spawner_contract,
        "pcg_graph_handoff": pcg_graph_handoff,
        "native_point_source": {
            "schema": native_point_source_contract["schema"],
            "report_path": NATIVE_POINT_SOURCE_REPORT_PATH,
            "pass": bool(native_point_source_contract.get("pass")),
            "promotion_policy": native_point_source_contract.get("promotion_policy", {}),
            "attribute_schema": native_point_source_contract.get("attribute_schema", {}),
            "validation": native_point_source_contract.get("validation", {}),
        },
        "module_actor_counts": counts,
        "connectivity": connectivity,
    }
    os.makedirs(os.path.dirname(GAMEPLAY_DATA_PATH), exist_ok=True)
    with open(GAMEPLAY_DATA_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
    with open(PCG_SPAWNER_CONTRACT_PATH, "w", encoding="utf-8") as handle:
        json.dump(pcg_spawner_contract, handle, indent=2, ensure_ascii=False)
    with open(PCG_GRAPH_HANDOFF_PATH, "w", encoding="utf-8") as handle:
        json.dump(pcg_graph_handoff, handle, indent=2, ensure_ascii=False)
    minimap_text = build_minimap_text(layout, progression)
    with open(MINIMAP_PATH, "w", encoding="utf-8") as handle:
        handle.write(minimap_text)
    return {
        "gameplay_data_path": GAMEPLAY_DATA_PATH,
        "pcg_spawner_contract_path": PCG_SPAWNER_CONTRACT_PATH,
        "pcg_graph_handoff_path": PCG_GRAPH_HANDOFF_PATH,
        "native_point_source_report_path": NATIVE_POINT_SOURCE_REPORT_PATH,
        "minimap_path": MINIMAP_PATH,
        "schema": data["schema"],
        "pcg_spawner_contract_schema": pcg_spawner_contract["schema"],
        "pcg_spawner_contract_pass": bool(pcg_spawner_contract.get("pass")),
        "pcg_graph_handoff_schema": pcg_graph_handoff["schema"],
        "pcg_graph_handoff_pass": bool(pcg_graph_handoff.get("pass")),
        "native_point_source_schema": native_point_source_contract["schema"],
        "native_point_source_pass": bool(native_point_source_contract.get("pass")),
        "native_point_source_point_count": int(native_point_source_contract.get("validation", {}).get("point_count", 0)),
        "native_point_source_group_count": int(native_point_source_contract.get("validation", {}).get("group_count", 0)),
        "native_point_source_missing_required_attribute_count": int(native_point_source_contract.get("validation", {}).get("missing_required_attribute_count", 0)),
        "native_point_source_invalid_transform_count": int(native_point_source_contract.get("validation", {}).get("invalid_transform_count", 0)),
        "native_point_source_stream_count_mismatch_count": int(native_point_source_contract.get("validation", {}).get("stream_count_mismatch_count", 0)),
        "native_point_source_material_split_count_mismatch_count": int(native_point_source_contract.get("validation", {}).get("material_split_count_mismatch_count", 0)),
        "pcg_graph_handoff_stream_count": int(pcg_graph_handoff.get("validation", {}).get("stream_count", 0)),
        "pcg_graph_handoff_mesh_only_spawner_count": int(pcg_graph_handoff.get("promotion_targets", {}).get("mesh_only_spawner_count", 0)),
        "pcg_graph_handoff_material_safe_spawner_count": int(pcg_graph_handoff.get("promotion_targets", {}).get("material_safe_spawner_count", 0)),
        "pcg_spawn_point_record_count": int(pcg_spawner_contract.get("point_count", 0)),
        "pcg_spawner_group_count": int(pcg_spawner_contract.get("group_count", 0)),
        "pcg_spawner_material_variant_group_count": int(pcg_spawner_contract.get("material_variant_group_count", 0)),
        "pcg_spawner_missing_mesh_key_count": int(pcg_spawner_contract.get("missing_mesh_key_count", 0)),
        "pcg_spawner_missing_static_mesh_path_count": int(pcg_spawner_contract.get("missing_static_mesh_path_count", 0)),
        "pcg_spawner_unknown_mesh_key_count": int(pcg_spawner_contract.get("unknown_mesh_key_count", 0)),
        "pcg_spawner_static_mesh_path_conflict_count": int(pcg_spawner_contract.get("static_mesh_path_conflict_count", 0)),
        "room_record_count": len(rooms),
        "cell_record_count": len(data["cells"]),
        "marker_record_count": len(markers),
        "volume_record_count": len(volume_records),
        "lock_key_link_count": len(lock_key_links),
        "door_point_record_count": len(door_records),
        "connector_detail_record_count": len(connector_detail_records),
        "corridor_detail_record_count": len(corridor_detail_records),
        "room_variant_record_count": len(room_variant_records),
        "spawn_point_record_count": len(spawn_records),
        "route_point_record_count": len(route_records),
        "encounter_spawn_point_record_count": len(encounter_spawn_records),
        "reward_point_record_count": len(reward_records),
        "theme_light_record_count": len(theme_light_records),
        "playtest_point_record_count": len(playtest_records),
        "navigation_waypoint_record_count": len(nav_waypoint_records),
        "detail_point_record_count": len(detail_records),
        "detail_mesh_record_count": len(detail_mesh_records),
        "room_archetype_record_count": len(room_archetypes),
        "room_theme_record_count": len(room_themes),
        "room_shape_record_count": len(room_shapes),
        "encounter_record_count": len(encounter_profiles),
        "minimap_line_count": len(minimap_text.splitlines()),
    }


def _cell_to_location(cell, z=0.0):
    x, y = cell
    cell_size = _grid_cell_size()
    return unreal.Vector(float(x) * cell_size, float(y) * cell_size, float(z))


def _location_record(location):
    return [float(location.x), float(location.y), float(location.z)]


def _rotation_record(rotation):
    return [float(rotation.pitch), float(rotation.yaw), float(rotation.roll)]


def _scale_record(scale):
    return [float(scale.x), float(scale.y), float(scale.z)]


def _tag_values(tags):
    values = {}
    for tag in tags or []:
        text = str(tag)
        if "=" in text:
            key, value = text.split("=", 1)
            values[key] = value
        else:
            values[text] = True
    return values


def _has_tag_key(tags, key):
    prefix = str(key) + "="
    return any(str(tag).startswith(prefix) for tag in tags or [])


def _static_mesh_key(static_mesh):
    if not static_mesh:
        return None
    return MESH_KEY_BY_ASSET_NAME.get(static_mesh.get_name(), static_mesh.get_name())


def _with_static_mesh_contract_tags(tags, static_mesh, material=None):
    result = [str(tag) for tag in tags or []]
    mesh_key = _static_mesh_key(static_mesh)
    if mesh_key and not _has_tag_key(result, "DungeonMeshKey"):
        result.append("DungeonMeshKey={}".format(mesh_key))
    if static_mesh and not _has_tag_key(result, "DungeonStaticMeshPath"):
        result.append("DungeonStaticMeshPath={}".format(static_mesh.get_path_name()))
    if material and not _has_tag_key(result, "DungeonMaterialName"):
        result.append("DungeonMaterialName={}".format(material.get_name()))
    if not _has_tag_key(result, "DungeonMaterialMode"):
        result.append("DungeonMaterialMode={}".format("override" if material else "baked"))
    return result


def _expected_static_mesh_spawn_point_count(counts):
    return sum(int(counts.get(key, 0)) for key in STATIC_MESH_COUNT_KEYS)


def _dungeon_nav_bounds(cells, padding=720.0, z_extent=520.0):
    cell_size = _grid_cell_size()
    xs = [float(cell[0]) * cell_size for cell in cells]
    ys = [float(cell[1]) * cell_size for cell in cells]
    min_x = min(xs) - cell_size * 0.5 - padding
    max_x = max(xs) + cell_size * 0.5 + padding
    min_y = min(ys) - cell_size * 0.5 - padding
    max_y = max(ys) + cell_size * 0.5 + padding
    location = unreal.Vector((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, z_extent)
    extent = unreal.Vector((max_x - min_x) * 0.5, (max_y - min_y) * 0.5, z_extent)
    return location, extent


def _yaw_from_cell_to_cell(source_cell, target_cell):
    dx = float(target_cell[0] - source_cell[0])
    dy = float(target_cell[1] - source_cell[1])
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        return 0.0
    return math.degrees(math.atan2(dy, dx))


def _waypoint_neighbors(cell, cells):
    result = []
    for direction in ("N", "E", "S", "W"):
        neighbor = _neighbors(cell)[direction]
        if neighbor in cells:
            result.append({"direction": direction, "cell": [int(neighbor[0]), int(neighbor[1])]})
    return result


def _direction_yaw(direction):
    return {
        "E": 0.0,
        "N": 90.0,
        "W": 180.0,
        "S": -90.0,
    }.get(str(direction), 0.0)


def _corner_yaw_for_dirs(directions):
    direction_set = set(directions)
    if direction_set == {"E", "N"}:
        return 0.0
    if direction_set == {"N", "W"}:
        return 90.0
    if direction_set == {"W", "S"}:
        return 180.0
    if direction_set == {"S", "E"}:
        return -90.0
    return 0.0


def _corridor_detail_profile(cell, cells):
    corridor_dirs = []
    room_dirs = []
    traversable_dirs = []
    for direction in ("N", "E", "S", "W"):
        neighbor = _neighbors(cell)[direction]
        if neighbor not in cells:
            continue
        traversable_dirs.append(direction)
        neighbor_kind = cells[neighbor]["kind"]
        if neighbor_kind == "corridor":
            corridor_dirs.append(direction)
        elif neighbor_kind == "room":
            room_dirs.append(direction)

    if len(corridor_dirs) >= 3 or len(traversable_dirs) >= 3:
        detail_kind = "junction"
        mesh_key = "corridor_detail_junction"
        yaw = 0.0
    elif len(corridor_dirs) == 2:
        if set(corridor_dirs) in ({"N", "S"}, {"E", "W"}):
            detail_kind = "straight"
            mesh_key = "corridor_detail_straight"
            yaw = 90.0 if set(corridor_dirs) == {"N", "S"} else 0.0
        else:
            detail_kind = "corner"
            mesh_key = "corridor_detail_corner"
            yaw = _corner_yaw_for_dirs(corridor_dirs)
    elif len(corridor_dirs) == 1:
        detail_kind = "endcap"
        mesh_key = "corridor_detail_endcap"
        yaw = _direction_yaw(corridor_dirs[0])
    elif room_dirs:
        detail_kind = "doorway"
        mesh_key = "corridor_detail_endcap"
        yaw = _direction_yaw(room_dirs[0])
    else:
        detail_kind = "island"
        mesh_key = "corridor_detail_junction"
        yaw = 0.0

    return {
        "detail_kind": detail_kind,
        "mesh_key": mesh_key,
        "yaw": float(yaw),
        "corridor_dirs": corridor_dirs,
        "room_dirs": room_dirs,
        "traversable_dirs": traversable_dirs,
    }


def _ceiling_mesh_key_for_cell(cell_kind, floor_mesh_key):
    if str(cell_kind) == "corridor":
        if str(floor_mesh_key) == "corner":
            return "ceiling_corner"
        return "ceiling_corridor"
    return "ceiling_room"


def _spawn_static_mesh(label, mesh, location, rotation=None, material=None, tags=None, scale=None):
    if rotation is None:
        rotation = _actor_rotator()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    if not actor:
        raise RuntimeError("Failed to spawn StaticMeshActor: " + label)
    actor.set_actor_label(label, mark_dirty=True)
    actor.set_actor_scale3d(scale if scale is not None else _module_scale())
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        raise RuntimeError("Spawned actor has no StaticMeshComponent: " + label)
    component.set_static_mesh(mesh)
    if material:
        slot_count = max(1, component.get_num_materials())
        for slot_index in range(slot_count):
            component.set_material(slot_index, material)
    tags = _with_static_mesh_contract_tags(tags, mesh, material)
    if tags:
        _apply_actor_tags(actor, tags)
    return actor


def _spawn_trigger_box(label, location, extent, rotation=None, tags=None):
    if rotation is None:
        rotation = _actor_rotator()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TriggerBox, location, rotation)
    if not actor:
        raise RuntimeError("Failed to spawn TriggerBox: " + label)
    actor.set_actor_label(label, mark_dirty=True)
    component = actor.get_component_by_class(unreal.BoxComponent)
    if component:
        component.set_box_extent(
            unreal.Vector(float(extent[0]), float(extent[1]), float(extent[2])),
            True,
        )
        component.set_editor_property("hidden_in_game", True)
    if tags:
        _apply_actor_tags(actor, tags)
    return actor


def _spawn_target_point(label, location, rotation=None, tags=None):
    if rotation is None:
        rotation = _actor_rotator()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TargetPoint, location, rotation)
    if not actor:
        raise RuntimeError("Failed to spawn TargetPoint: " + label)
    actor.set_actor_label(label, mark_dirty=True)
    if tags:
        _apply_actor_tags(actor, tags)
    return actor


def _spawn_player_start(label, location, rotation=None, tags=None):
    if rotation is None:
        rotation = _actor_rotator()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, location, rotation)
    if not actor:
        raise RuntimeError("Failed to spawn PlayerStart: " + label)
    actor.set_actor_label(label, mark_dirty=True)
    if tags:
        _apply_actor_tags(actor, tags)
    return actor


def _spawn_nav_mesh_bounds(label, location, extent, tags=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.NavMeshBoundsVolume, location, _actor_rotator())
    if not actor:
        raise RuntimeError("Failed to spawn NavMeshBoundsVolume: " + label)
    actor.set_actor_label(label, mark_dirty=True)
    # Default volume brush is a 200cm cube, so scale maps directly from desired half-extents.
    actor.set_actor_scale3d(unreal.Vector(float(extent.x) / 100.0, float(extent.y) / 100.0, float(extent.z) / 100.0))
    if tags:
        _apply_actor_tags(actor, tags)
    return actor


def _component_static_mesh(component):
    if not component:
        return None
    try:
        return component.get_editor_property("static_mesh")
    except Exception:
        try:
            return component.get_static_mesh()
        except Exception:
            return None


def build_pcg_spawner_contract(actors):
    points = []
    groups = {}
    known_mesh_keys = {module_key for module_key, _asset_name in MODULE_SPECS}
    missing_mesh_key = []
    missing_static_mesh_path = []
    unknown_mesh_keys = set()
    for actor in actors:
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        static_mesh = _component_static_mesh(component)
        values = _tag_values(getattr(actor, "tags", []))
        mesh_key = values.get("DungeonMeshKey") or _static_mesh_key(static_mesh)
        static_mesh_path = values.get("DungeonStaticMeshPath")
        if not static_mesh_path and static_mesh:
            static_mesh_path = static_mesh.get_path_name()
        if not mesh_key:
            missing_mesh_key.append(actor.get_actor_label())
        elif mesh_key not in known_mesh_keys:
            unknown_mesh_keys.add(mesh_key)
        if not static_mesh_path:
            missing_static_mesh_path.append(actor.get_actor_label())
        transform_record = {
            "location": _location_record(actor.get_actor_location()),
            "rotation": _rotation_record(actor.get_actor_rotation()),
            "scale": _scale_record(actor.get_actor_scale3d()),
        }
        material_mode = values.get("DungeonMaterialMode", "baked")
        material_name = values.get("DungeonMaterialName")
        material_key = material_name if material_name else material_mode
        point = {
            "point_index": len(points),
            "label": actor.get_actor_label(),
            "module": values.get("DungeonModule", ""),
            "mesh_key": mesh_key,
            "static_mesh_path": static_mesh_path,
            "material_mode": material_mode,
            "material_name": material_name,
            "transform": transform_record,
            "attributes": dict(sorted(values.items())),
        }
        points.append(point)
        group_key = mesh_key or "<missing>"
        group = groups.setdefault(
            group_key,
            {
                "spawner_group_key": group_key,
                "mesh_key": mesh_key,
                "point_count": 0,
                "static_mesh_paths": set(),
                "modules": set(),
                "material_keys": set(),
                "sample_labels": [],
            },
        )
        group["point_count"] += 1
        if static_mesh_path:
            group["static_mesh_paths"].add(static_mesh_path)
        if point["module"]:
            group["modules"].add(point["module"])
        if material_key:
            group["material_keys"].add(material_key)
        if len(group["sample_labels"]) < 5:
            group["sample_labels"].append(point["label"])

    serialized_groups = []
    static_mesh_path_conflicts = []
    for group_key, group in sorted(groups.items()):
        static_mesh_paths = sorted(group["static_mesh_paths"])
        material_keys = sorted(group["material_keys"])
        modules = sorted(group["modules"])
        if len(static_mesh_paths) != 1:
            static_mesh_path_conflicts.append(group_key)
        serialized_groups.append(
            {
                "spawner_group_key": group["spawner_group_key"],
                "mesh_key": group["mesh_key"],
                "static_mesh_path": static_mesh_paths[0] if len(static_mesh_paths) == 1 else None,
                "static_mesh_paths": static_mesh_paths,
                "point_count": int(group["point_count"]),
                "modules": modules,
                "material_keys": material_keys,
                "material_variant_count": len(material_keys),
                "requires_material_attribute": len(material_keys) > 1,
                "sample_labels": list(group["sample_labels"]),
            }
        )

    module_counts = {}
    for point in points:
        module = point.get("module") or "<missing>"
        module_counts[module] = module_counts.get(module, 0) + 1

    return {
        "schema": "cubeless_pcg_spawner_contract_v1",
        "current_spawn_mode": "static_mesh_actor_validation",
        "future_spawn_mode": "pcg_static_mesh_spawner_by_mesh_key",
        "mesh_grouping_rule": "same DungeonMeshKey uses one spawner group",
        "gameplay_actor_policy": "TargetPoint, TriggerBox, PlayerStart, NavMeshBoundsVolume, and Light actors stay outside static mesh spawner groups.",
        "available_mesh_keys": [module_key for module_key, _asset_name in MODULE_SPECS],
        "point_count": len(points),
        "group_count": len(serialized_groups),
        "material_variant_group_count": sum(1 for group in serialized_groups if group["requires_material_attribute"]),
        "module_counts": dict(sorted(module_counts.items())),
        "missing_mesh_key_count": len(missing_mesh_key),
        "missing_static_mesh_path_count": len(missing_static_mesh_path),
        "unknown_mesh_key_count": len(unknown_mesh_keys),
        "static_mesh_path_conflict_count": len(static_mesh_path_conflicts),
        "missing_mesh_key_labels": missing_mesh_key,
        "missing_static_mesh_path_labels": missing_static_mesh_path,
        "unknown_mesh_keys": sorted(unknown_mesh_keys),
        "static_mesh_path_conflict_groups": static_mesh_path_conflicts,
        "groups": serialized_groups,
        "points": points,
        "pass": bool(
            len(points) > 0
            and not missing_mesh_key
            and not missing_static_mesh_path
            and not unknown_mesh_keys
            and not static_mesh_path_conflicts
        ),
    }


def _pcg_safe_identifier(value):
    text = str(value or "missing")
    safe = []
    for char in text:
        if char.isalnum():
            safe.append(char)
        else:
            safe.append("_")
    result = "".join(safe).strip("_")
    return result or "missing"


def build_pcg_graph_handoff(pcg_spawner_contract):
    point_counts_by_group_material = {}
    point_indexes_by_group = {}
    for point in pcg_spawner_contract.get("points", []):
        group_key = point.get("mesh_key") or "<missing>"
        material_key = point.get("material_name") or point.get("material_mode") or "<missing>"
        group_counts = point_counts_by_group_material.setdefault(group_key, {})
        group_counts[material_key] = group_counts.get(material_key, 0) + 1
        point_indexes_by_group.setdefault(group_key, []).append(int(point.get("point_index", 0)))

    streams = []
    material_variant_groups = []
    for group in pcg_spawner_contract.get("groups", []):
        mesh_key = group.get("mesh_key")
        group_key = group.get("spawner_group_key") or mesh_key or "<missing>"
        safe_group = _pcg_safe_identifier(group_key)
        material_counts = point_counts_by_group_material.get(group_key, {})
        material_splits = [
            {
                "material_key": material_key,
                "point_count": int(count),
                "stream_name": "MeshKey_%s_Material_%s" % (safe_group, _pcg_safe_identifier(material_key)),
                "filter": {
                    "attribute": "DungeonMaterialMode" if material_key == "baked" else "DungeonMaterialName",
                    "operation": "equals",
                    "value": material_key,
                },
            }
            for material_key, count in sorted(material_counts.items())
        ]
        requires_material_split = bool(group.get("requires_material_attribute"))
        stream = {
            "stream_name": "MeshKey_%s" % safe_group,
            "mesh_key": mesh_key,
            "point_count": int(group.get("point_count", 0)),
            "static_mesh_path": group.get("static_mesh_path"),
            "filter": {
                "attribute": "DungeonMeshKey",
                "operation": "equals",
                "value": mesh_key,
            },
            "pcg_spawner_target": {
                "node_type": "PCG Static Mesh Spawner",
                "same_static_mesh_spawner": True,
                "static_mesh_path": group.get("static_mesh_path"),
                "transform_source": "point transform",
                "attribute_source": "point attributes from PCGSpawnerContract",
            },
            "material_strategy": (
                "split_by_DungeonMaterialName_until_native_material_override_attribute_is_available"
                if requires_material_split
                else "single_spawner_uses_mesh_default_or_single_override"
            ),
            "material_keys": group.get("material_keys", []),
            "single_material_key": group.get("material_keys", [None])[0] if len(group.get("material_keys", [])) == 1 else None,
            "material_attribute": "DungeonMaterialName" if requires_material_split else None,
            "material_variant_count": int(group.get("material_variant_count", 0)),
            "material_splits": material_splits if requires_material_split else [],
            "source_contract_point_indexes_sample": point_indexes_by_group.get(group_key, [])[:12],
            "sample_labels": group.get("sample_labels", []),
        }
        streams.append(stream)
        if requires_material_split:
            material_variant_groups.append(
                {
                    "mesh_key": mesh_key,
                    "stream_name": stream["stream_name"],
                    "point_count": stream["point_count"],
                    "static_mesh_path": group.get("static_mesh_path"),
                    "material_attribute": "DungeonMaterialName",
                    "material_variant_count": stream["material_variant_count"],
                    "material_splits": material_splits,
                }
            )

    mesh_only_spawner_count = len(streams)
    material_split_spawner_count = 0
    for stream in streams:
        if stream["material_splits"]:
            material_split_spawner_count += max(1, len(stream["material_splits"]))
        else:
            material_split_spawner_count += 1

    excluded_actor_outputs = [
        {
            "actor_class": "TargetPoint",
            "reason": "Gameplay anchors and navigation waypoints keep actor identity and tags outside Static Mesh Spawner groups.",
            "record_groups": [
                "door_points",
                "spawn_points",
                "route_points",
                "encounter_spawn_points",
                "reward_points",
                "detail_points",
                "navigation_waypoints",
            ],
        },
        {
            "actor_class": "TriggerBox",
            "reason": "Room, door, and gate gameplay volumes are overlap actors, not mesh instances.",
            "record_groups": ["volumes"],
        },
        {
            "actor_class": "PlayerStart",
            "reason": "Playtest start actor must remain a gameplay actor.",
            "record_groups": ["playtest_records"],
        },
        {
            "actor_class": "NavMeshBoundsVolume",
            "reason": "Navigation coverage volume is editor/gameplay infrastructure.",
            "record_groups": ["playtest_records"],
        },
        {
            "actor_class": "PointLight, DirectionalLight, SkyLight",
            "reason": "Lighting actors are separate from Static Mesh Spawner output.",
            "record_groups": ["theme_lights", "review_lights"],
        },
    ]

    pass_value = bool(
        pcg_spawner_contract.get("pass")
        and mesh_only_spawner_count == int(pcg_spawner_contract.get("group_count", 0))
        and sum(stream["point_count"] for stream in streams) == int(pcg_spawner_contract.get("point_count", 0))
    )

    return {
        "schema": "cubeless_pcg_graph_handoff_v1",
        "purpose": "Native PCG graph authoring handoff for MeshKey-filtered Static Mesh Spawner branches.",
        "root": ROOT,
        "level_path": LEVEL_PATH,
        "graph_path": GRAPH_PATH,
        "source_contract_path": PCG_SPAWNER_CONTRACT_PATH,
        "point_contract": {
            "source_schema": pcg_spawner_contract.get("schema"),
            "point_count": int(pcg_spawner_contract.get("point_count", 0)),
            "group_count": int(pcg_spawner_contract.get("group_count", 0)),
            "filter_attribute": "DungeonMeshKey",
            "static_mesh_attribute": "DungeonStaticMeshPath",
            "material_attribute": "DungeonMaterialName",
            "transform_attributes": ["location", "rotation", "scale"],
        },
        "promotion_targets": {
            "mesh_only_spawner_count": mesh_only_spawner_count,
            "material_safe_spawner_count": material_split_spawner_count,
            "material_variant_group_count": len(material_variant_groups),
            "grouping_rule": "same DungeonMeshKey should feed the same native PCG Static Mesh Spawner when material strategy allows it",
            "fallback_rule": "split a MeshKey stream by DungeonMaterialName when a single spawner cannot preserve material overrides",
        },
        "point_streams": streams,
        "material_variant_groups": material_variant_groups,
        "excluded_actor_outputs": excluded_actor_outputs,
        "native_graph_steps": [
            "Read or recreate the point stream represented by CubelessDungeonMVP_PCGSpawnerContract.json.",
            "Filter points by DungeonMeshKey for each point_streams entry.",
            "Feed each filtered stream into one PCG Static Mesh Spawner using static_mesh_path.",
            "Apply point location, rotation, and scale as the spawned transform.",
            "For material_variant_groups, either support DungeonMaterialName as a material override attribute or split the stream by material_splits.",
            "Keep TargetPoint, TriggerBox, PlayerStart, NavMeshBoundsVolume, and Light outputs in gameplay actor layers, not Static Mesh Spawner output.",
        ],
        "validation": {
            "source_contract_pass": bool(pcg_spawner_contract.get("pass")),
            "missing_mesh_key_count": int(pcg_spawner_contract.get("missing_mesh_key_count", 0)),
            "missing_static_mesh_path_count": int(pcg_spawner_contract.get("missing_static_mesh_path_count", 0)),
            "unknown_mesh_key_count": int(pcg_spawner_contract.get("unknown_mesh_key_count", 0)),
            "static_mesh_path_conflict_count": int(pcg_spawner_contract.get("static_mesh_path_conflict_count", 0)),
            "stream_point_total": sum(stream["point_count"] for stream in streams),
            "stream_count": len(streams),
            "pass": pass_value,
        },
        "pass": pass_value,
    }


def _is_number(value):
    try:
        number = float(value)
    except Exception:
        return False
    return math.isfinite(number)


def _valid_number_triplet(values):
    return isinstance(values, list) and len(values) == 3 and all(_is_number(value) for value in values)


def _point_bounds_init(location):
    return {
        "min": [float(location[0]), float(location[1]), float(location[2])],
        "max": [float(location[0]), float(location[1]), float(location[2])],
    }


def _point_bounds_add(bounds, location):
    for index in range(3):
        value = float(location[index])
        bounds["min"][index] = min(bounds["min"][index], value)
        bounds["max"][index] = max(bounds["max"][index], value)


def _point_bounds_finish(bounds):
    if not bounds:
        return None
    return {
        "min": [round(value, 3) for value in bounds["min"]],
        "max": [round(value, 3) for value in bounds["max"]],
        "size": [round(bounds["max"][index] - bounds["min"][index], 3) for index in range(3)],
    }


def _native_point_attribute_subset(point):
    attributes = point.get("attributes", {}) or {}
    material_name = point.get("material_name") or ""
    return {
        "DungeonPointIndex": int(point.get("point_index", -1)),
        "DungeonSourceLabel": str(point.get("label", "")),
        "DungeonMeshKey": str(point.get("mesh_key", "")),
        "DungeonStaticMeshPath": str(point.get("static_mesh_path", "")),
        "DungeonMaterialMode": str(point.get("material_mode", "baked")),
        "DungeonMaterialName": str(material_name),
        "DungeonModule": str(point.get("module") or attributes.get("DungeonModule", "")),
        "DungeonSeed": str(attributes.get("DungeonSeed", "")),
        "DungeonCell": str(attributes.get("DungeonCell", "")),
        "DungeonCellKind": str(attributes.get("DungeonCellKind", "")),
        "DungeonRoomId": str(attributes.get("DungeonRoomId", "")),
        "DungeonRole": str(attributes.get("DungeonRole", "")),
        "DungeonRoomArchetype": str(attributes.get("DungeonRoomArchetype", "")),
        "DungeonRoomTheme": str(attributes.get("DungeonRoomTheme", "")),
        "DungeonThemeName": str(attributes.get("DungeonThemeName", "")),
        "DungeonThemeMaterial": str(attributes.get("DungeonThemeMaterial", "")),
    }


def build_native_point_source_contract(pcg_spawner_contract, pcg_graph_handoff):
    streams_by_mesh_key = {
        stream.get("mesh_key"): stream
        for stream in pcg_graph_handoff.get("point_streams", [])
    }
    groups = {}
    native_points = []
    missing_required_attribute_points = []
    invalid_transform_points = []
    duplicate_point_indexes = []
    duplicate_labels = []
    missing_handoff_stream_keys = set()
    static_mesh_path_mismatch_points = []
    material_attribute_mismatch_points = []
    seen_indexes = set()
    seen_labels = set()

    required_attributes = [
        "DungeonMeshKey",
        "DungeonStaticMeshPath",
        "DungeonMaterialMode",
    ]
    material_split_counts = {}

    for point in pcg_spawner_contract.get("points", []):
        point_index = int(point.get("point_index", -1))
        label = str(point.get("label", ""))
        mesh_key = point.get("mesh_key")
        stream = streams_by_mesh_key.get(mesh_key)
        attributes = point.get("attributes", {}) or {}
        transform = point.get("transform", {}) or {}
        location = transform.get("location", [])
        rotation = transform.get("rotation", [])
        scale = transform.get("scale", [])
        material_mode = point.get("material_mode") or "baked"
        material_name = point.get("material_name") or ""
        material_key = material_name if material_name else material_mode

        if point_index in seen_indexes:
            duplicate_point_indexes.append(point_index)
        seen_indexes.add(point_index)
        if label in seen_labels:
            duplicate_labels.append(label)
        seen_labels.add(label)

        missing_attributes = [
            attribute_name
            for attribute_name in required_attributes
            if attribute_name not in attributes or attributes.get(attribute_name) in (None, "")
        ]
        if material_mode == "override" and not attributes.get("DungeonMaterialName"):
            missing_attributes.append("DungeonMaterialName")
        if missing_attributes:
            missing_required_attribute_points.append(
                {
                    "point_index": point_index,
                    "label": label,
                    "missing_attributes": sorted(set(missing_attributes)),
                }
            )

        if not (_valid_number_triplet(location) and _valid_number_triplet(rotation) and _valid_number_triplet(scale)):
            invalid_transform_points.append(
                {
                    "point_index": point_index,
                    "label": label,
                    "transform": transform,
                }
            )

        if not stream:
            missing_handoff_stream_keys.add(mesh_key or "<missing>")
        else:
            expected_static_mesh_path = stream.get("static_mesh_path")
            if expected_static_mesh_path and point.get("static_mesh_path") != expected_static_mesh_path:
                static_mesh_path_mismatch_points.append(
                    {
                        "point_index": point_index,
                        "label": label,
                        "mesh_key": mesh_key,
                        "expected_static_mesh_path": expected_static_mesh_path,
                        "actual_static_mesh_path": point.get("static_mesh_path"),
                    }
                )
            if stream.get("material_attribute") == "DungeonMaterialName" and material_mode == "override":
                if not material_name:
                    material_attribute_mismatch_points.append(
                        {
                            "point_index": point_index,
                            "label": label,
                            "mesh_key": mesh_key,
                            "expected_attribute": "DungeonMaterialName",
                        }
                    )

        group = groups.setdefault(
            mesh_key or "<missing>",
            {
                "mesh_key": mesh_key,
                "point_count": 0,
                "static_mesh_path": point.get("static_mesh_path"),
                "material_key_counts": {},
                "bounds": None,
                "sample_point_indexes": [],
                "sample_labels": [],
                "handoff_stream_name": stream.get("stream_name") if stream else None,
                "handoff_point_count": int(stream.get("point_count", 0)) if stream else 0,
                "requires_material_split": bool(stream and stream.get("material_splits")),
            },
        )
        group["point_count"] += 1
        group["material_key_counts"][material_key] = group["material_key_counts"].get(material_key, 0) + 1
        if _valid_number_triplet(location):
            if group["bounds"] is None:
                group["bounds"] = _point_bounds_init(location)
            else:
                _point_bounds_add(group["bounds"], location)
        if len(group["sample_point_indexes"]) < 8:
            group["sample_point_indexes"].append(point_index)
        if len(group["sample_labels"]) < 5:
            group["sample_labels"].append(label)
        material_split_counts.setdefault(mesh_key or "<missing>", {})
        material_split_counts[mesh_key or "<missing>"][material_key] = (
            material_split_counts[mesh_key or "<missing>"].get(material_key, 0) + 1
        )

        native_points.append(
            {
                "point_index": point_index,
                "source_label": label,
                "mesh_key": mesh_key,
                "static_mesh_path": point.get("static_mesh_path"),
                "transform": {
                    "location": location,
                    "rotation": rotation,
                    "scale": scale,
                },
                "material_key": material_key,
                "attributes": _native_point_attribute_subset(point),
            }
        )

    group_records = []
    stream_count_mismatches = []
    material_split_count_mismatches = []
    for mesh_key, group in sorted(groups.items()):
        stream = streams_by_mesh_key.get(group.get("mesh_key"))
        if stream and int(stream.get("point_count", 0)) != int(group["point_count"]):
            stream_count_mismatches.append(
                {
                    "mesh_key": mesh_key,
                    "expected": int(stream.get("point_count", 0)),
                    "actual": int(group["point_count"]),
                }
            )
        if stream and stream.get("material_splits"):
            actual_material_counts = material_split_counts.get(mesh_key, {})
            for split in stream.get("material_splits", []):
                material_key = split.get("material_key")
                expected_count = int(split.get("point_count", 0))
                actual_count = int(actual_material_counts.get(material_key, 0))
                if expected_count != actual_count:
                    material_split_count_mismatches.append(
                        {
                            "mesh_key": mesh_key,
                            "material_key": material_key,
                            "expected": expected_count,
                            "actual": actual_count,
                        }
                    )
        group_records.append(
            {
                "mesh_key": mesh_key,
                "point_count": int(group["point_count"]),
                "handoff_stream_name": group["handoff_stream_name"],
                "handoff_point_count": int(group["handoff_point_count"]),
                "static_mesh_path": group["static_mesh_path"],
                "requires_material_split": bool(group["requires_material_split"]),
                "material_key_counts": dict(sorted(group["material_key_counts"].items())),
                "bounds": _point_bounds_finish(group["bounds"]),
                "sample_point_indexes": group["sample_point_indexes"],
                "sample_labels": group["sample_labels"],
            }
        )

    expected_stream_keys = {stream.get("mesh_key") for stream in pcg_graph_handoff.get("point_streams", [])}
    source_stream_keys = {group.get("mesh_key") for group in pcg_spawner_contract.get("groups", [])}
    handoff_streams_without_points = sorted(
        key for key in expected_stream_keys
        if key not in source_stream_keys
    )
    point_count = len(native_points)
    handoff_point_total = int(pcg_graph_handoff.get("validation", {}).get("stream_point_total", 0))
    validation = {
        "source_contract_pass": bool(pcg_spawner_contract.get("pass")),
        "source_handoff_pass": bool(pcg_graph_handoff.get("pass")),
        "point_count": point_count,
        "source_contract_point_count": int(pcg_spawner_contract.get("point_count", 0)),
        "handoff_stream_point_total": handoff_point_total,
        "group_count": len(group_records),
        "source_contract_group_count": int(pcg_spawner_contract.get("group_count", 0)),
        "handoff_stream_count": len(pcg_graph_handoff.get("point_streams", [])),
        "missing_required_attribute_count": len(missing_required_attribute_points),
        "invalid_transform_count": len(invalid_transform_points),
        "missing_handoff_stream_key_count": len(missing_handoff_stream_keys),
        "handoff_stream_without_points_count": len(handoff_streams_without_points),
        "static_mesh_path_mismatch_count": len(static_mesh_path_mismatch_points),
        "material_attribute_mismatch_count": len(material_attribute_mismatch_points),
        "stream_count_mismatch_count": len(stream_count_mismatches),
        "material_split_count_mismatch_count": len(material_split_count_mismatches),
        "duplicate_point_index_count": len(duplicate_point_indexes),
        "duplicate_label_count": len(duplicate_labels),
    }
    pass_value = bool(
        validation["source_contract_pass"]
        and validation["source_handoff_pass"]
        and point_count > 0
        and point_count == validation["source_contract_point_count"]
        and point_count == handoff_point_total
        and len(group_records) == validation["source_contract_group_count"]
        and len(group_records) == validation["handoff_stream_count"]
        and not missing_required_attribute_points
        and not invalid_transform_points
        and not missing_handoff_stream_keys
        and not handoff_streams_without_points
        and not static_mesh_path_mismatch_points
        and not material_attribute_mismatch_points
        and not stream_count_mismatches
        and not material_split_count_mismatches
        and not duplicate_point_indexes
        and not duplicate_labels
    )
    report = {
        "schema": "cubeless_pcg_dungeon_native_point_source_v1",
        "purpose": "Normalized point-source readiness contract for future native PCG Static Mesh Spawner input.",
        "root": ROOT,
        "level_path": LEVEL_PATH,
        "source_contract_path": PCG_SPAWNER_CONTRACT_PATH,
        "source_handoff_path": PCG_GRAPH_HANDOFF_PATH,
        "native_graph_path": NATIVE_GRAPH_PATH,
        "promotion_policy": {
            "current_status": "ready_contract_only",
            "output_connection_allowed": False,
            "reason_output_stays_disconnected": "The native skeleton still needs a real PCG point-source node or data-source actor before Merge can be connected to Output.",
            "point_transform_source": "transform.location, transform.rotation, transform.scale",
            "spawner_filter_attribute": "DungeonMeshKey",
            "material_split_attribute": "DungeonMaterialName",
            "actor_identity_policy": "Source labels are diagnostic attributes only; native PCG output should spawn mesh instances, not recreate validation StaticMeshActor labels.",
        },
        "attribute_schema": {
            "DungeonPointIndex": "int32",
            "DungeonSourceLabel": "string",
            "DungeonMeshKey": "string",
            "DungeonStaticMeshPath": "string",
            "DungeonMaterialMode": "string",
            "DungeonMaterialName": "string",
            "DungeonModule": "string",
            "DungeonSeed": "string",
            "DungeonCell": "string",
            "DungeonCellKind": "string",
            "DungeonRoomId": "string",
            "DungeonRole": "string",
            "DungeonRoomArchetype": "string",
            "DungeonRoomTheme": "string",
            "DungeonThemeName": "string",
            "DungeonThemeMaterial": "string",
        },
        "groups": group_records,
        "points": native_points,
        "validation": validation,
        "validation_details": {
            "missing_required_attribute_points": missing_required_attribute_points[:50],
            "invalid_transform_points": invalid_transform_points[:50],
            "missing_handoff_stream_keys": sorted(missing_handoff_stream_keys),
            "handoff_streams_without_points": handoff_streams_without_points,
            "static_mesh_path_mismatch_points": static_mesh_path_mismatch_points[:50],
            "material_attribute_mismatch_points": material_attribute_mismatch_points[:50],
            "stream_count_mismatches": stream_count_mismatches,
            "material_split_count_mismatches": material_split_count_mismatches,
            "duplicate_point_indexes": duplicate_point_indexes[:50],
            "duplicate_labels": duplicate_labels[:50],
        },
        "pass": pass_value,
    }
    os.makedirs(os.path.dirname(NATIVE_POINT_SOURCE_REPORT_PATH), exist_ok=True)
    with open(NATIVE_POINT_SOURCE_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def configure_validation_navigation():
    reports = []
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_class().get_name() != "RecastNavMesh":
                continue
            before_runtime = str(actor.get_editor_property("runtime_generation"))
            before_force = str(actor.get_editor_property("force_rebuild_on_load"))
            actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
            actor.set_editor_property("force_rebuild_on_load", True)
            reports.append(
                {
                    "label": actor.get_actor_label(),
                    "runtime_generation_before": before_runtime,
                    "runtime_generation_after": str(actor.get_editor_property("runtime_generation")),
                    "force_rebuild_on_load_before": before_force,
                    "force_rebuild_on_load_after": str(actor.get_editor_property("force_rebuild_on_load")),
                }
            )
        except Exception as exc:
            reports.append({"label": actor.get_actor_label(), "error": str(exc)})
    return reports


def clear_generated_dungeon():
    removed = 0
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_actor_label().startswith(ACTOR_PREFIX):
                unreal.EditorLevelLibrary.destroy_actor(actor)
                removed += 1
        except Exception:
            pass
    return removed


def _neighbors(cell):
    x, y = cell
    return {
        "N": (x, y + 1),
        "S": (x, y - 1),
        "E": (x + 1, y),
        "W": (x - 1, y),
    }


def _wall_transform(cell, direction):
    x, y = cell
    cell_size = _grid_cell_size()
    if direction == "N":
        return unreal.Vector(x * cell_size, y * cell_size + cell_size * 0.5, 0), _yaw_rotator(0.0)
    if direction == "S":
        return unreal.Vector(x * cell_size, y * cell_size - cell_size * 0.5, 0), _yaw_rotator(180.0)
    if direction == "E":
        return unreal.Vector(x * cell_size + cell_size * 0.5, y * cell_size, 0), _yaw_rotator(90.0)
    return unreal.Vector(x * cell_size - cell_size * 0.5, y * cell_size, 0), _yaw_rotator(-90.0)


def _is_corridor_corner(cell, cells):
    if cells[cell]["kind"] != "corridor":
        return False
    n = _neighbors(cell)
    corridor_dirs = [key for key, value in n.items() if value in cells and cells[value]["kind"] == "corridor"]
    return ("N" in corridor_dirs or "S" in corridor_dirs) and ("E" in corridor_dirs or "W" in corridor_dirs)


def validate_connectivity(cells):
    if not cells:
        return {"connected": False, "visited_count": 0, "cell_count": 0}
    start = next(iter(cells.keys()))
    visited = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for neighbor in _neighbors(cell).values():
            if neighbor in cells and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return {
        "connected": len(visited) == len(cells),
        "visited_count": len(visited),
        "cell_count": len(cells),
    }


def validate_layout_summary(seed, room_count, config=None):
    suite_config = dict(DEFAULT_DUNGEON_CONFIG)
    if config:
        suite_config.update(config)
    suite_config["seed"] = int(seed)
    suite_config["room_count"] = int(room_count)
    branch_chance_percent = _coerce_int(
        suite_config.get("branch_chance_percent"),
        DEFAULT_DUNGEON_CONFIG["branch_chance_percent"],
        0,
        100,
    )
    max_loop_edges = _coerce_int(suite_config.get("max_loop_edges"), DEFAULT_DUNGEON_CONFIG["max_loop_edges"], 0, 16)
    layout = generate_layout(
        seed=seed,
        room_count=room_count,
        branch_chance_percent=branch_chance_percent,
        max_loop_edges=max_loop_edges,
    )
    progression = assign_room_progression(layout, suite_config)
    encounter_profiles = assign_encounter_profiles(layout, progression)
    room_archetypes = assign_room_archetypes(layout, progression, encounter_profiles)
    room_themes = assign_room_themes(room_archetypes)
    room_shapes = assign_room_shapes(layout, progression, room_archetypes)
    lock_key_links = assign_lock_key_links(layout, progression)
    cells = layout["cells"]
    connectivity = validate_connectivity(cells)
    room_cells = sum(1 for data in cells.values() if data["kind"] == "room")
    corridor_cells = sum(1 for data in cells.values() if data["kind"] == "corridor")
    encounter_kind_counts = {}
    encounter_tier_counts = {}
    encounter_spawn_slot_count = 0
    reward_anchor_count = 0
    detail_anchor_count = 0
    detail_mesh_count = 0
    corridor_detail_count = 0
    for profile in encounter_profiles.values():
        encounter_kind_counts[profile["kind"]] = encounter_kind_counts.get(profile["kind"], 0) + 1
        encounter_tier_counts[profile["tier"]] = encounter_tier_counts.get(profile["tier"], 0) + 1
        encounter_spawn_slot_count += int(profile.get("spawn_budget", 0))
        if _reward_anchor_kind(profile):
            reward_anchor_count += 1
    archetype_counts = {}
    for profile in room_archetypes.values():
        archetype = profile["archetype"]
        archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
        template_count = len(_detail_anchor_templates(archetype))
        detail_anchor_count += template_count
        detail_mesh_count += template_count
    corridor_detail_count = corridor_cells
    boundary_wall_edges = 0
    room_corridor_edges = 0
    for cell, data in cells.items():
        for neighbor in _neighbors(cell).values():
            if neighbor not in cells:
                boundary_wall_edges += 1
            elif cell < neighbor and data["kind"] != cells[neighbor]["kind"]:
                room_corridor_edges += 1
    start = _room_center(layout, layout["start_room_id"])
    exit_cell = _room_center(layout, layout["exit_room_id"])
    start_exit_grid_distance = abs(start[0] - exit_cell[0]) + abs(start[1] - exit_cell[1])
    return {
        "seed": seed,
        "requested_room_count": room_count,
        "room_count": len(layout["rooms"]),
        "edge_count": len(layout["edges"]),
        "branch_chance_percent": branch_chance_percent,
        "max_loop_edges": max_loop_edges,
        "added_loop_edges": int(layout.get("added_loop_edges", 0)),
        "cell_count": len(cells),
        "room_cell_count": room_cells,
        "corridor_cell_count": corridor_cells,
        "boundary_wall_edge_count": boundary_wall_edges,
        "room_corridor_edge_count": room_corridor_edges,
        "main_path_room_count": progression["main_path_room_count"],
        "side_room_count": progression["side_room_count"],
        "locked_door_count": len(progression["locked_door_specs"]),
        "key_room_count": len(progression["key_room_ids"]),
        "shop_room_count": len(progression["shop_room_ids"]),
        "treasure_room_count": len(progression["treasure_room_ids"]),
        "enemy_room_count": len(progression["enemy_room_ids"]),
        "lock_key_link_count": len(lock_key_links),
        "lock_key_missing_key_count": sum(1 for link in lock_key_links if link.get("key_room_id") is None),
        "encounter_profile_count": len(encounter_profiles),
        "encounter_kind_counts": encounter_kind_counts,
        "encounter_tier_counts": encounter_tier_counts,
        "room_archetype_count": len(room_archetypes),
        "room_archetype_counts": archetype_counts,
        "room_theme_count": len(room_themes),
        "room_theme_counts": _theme_counts(room_themes),
        "room_shape_count": len(room_shapes),
        "room_shape_counts": _room_shape_counts(room_shapes),
        "room_variant_detail_count": len(room_shapes),
        "theme_light_count": len(room_themes),
        "connector_detail_count": room_corridor_edges,
        "corridor_detail_count": corridor_detail_count,
        "encounter_spawn_slot_count": encounter_spawn_slot_count,
        "reward_anchor_count": reward_anchor_count,
        "detail_anchor_count": detail_anchor_count,
        "detail_mesh_count": detail_mesh_count,
        "navigation_waypoint_count": len(cells),
        "route_anchor_count": len(layout["rooms"]),
        "door_anchor_count": room_corridor_edges,
        "role_counts": progression["role_counts"],
        "progression_pass": progression["pass"],
        "start_room_id": layout["start_room_id"],
        "exit_room_id": layout["exit_room_id"],
        "start_exit_grid_distance": start_exit_grid_distance,
        "connectivity": connectivity,
        "pass": bool(
            connectivity["connected"]
            and progression["pass"]
            and len(lock_key_links) == len(progression["locked_door_specs"])
            and sum(1 for link in lock_key_links if link.get("key_room_id") is None) == 0
            and len(encounter_profiles) == len(layout["rooms"])
            and len(room_archetypes) == len(layout["rooms"])
            and len(room_themes) == len(layout["rooms"])
            and len(room_shapes) == len(layout["rooms"])
            and len(room_shapes) == room_count
            and room_corridor_edges > 0
            and corridor_detail_count == corridor_cells
            and detail_anchor_count >= len(layout["rooms"])
            and detail_mesh_count == detail_anchor_count
            and encounter_spawn_slot_count >= len(progression["enemy_room_ids"])
            and room_corridor_edges > 0
            and len(layout["rooms"]) > 0
            and len(layout["rooms"]) == room_count
            and room_corridor_edges > 0
            and boundary_wall_edges > 0
            and start_exit_grid_distance >= 4
        ),
    }


def run_seed_suite(seeds=None, room_count=None, config=None):
    if seeds is None:
        seeds = [142857, 142858, 142859, 142860, 142861]
    suite_config = dict(DEFAULT_DUNGEON_CONFIG)
    if config:
        suite_config.update(config)
    if room_count is None:
        room_count = suite_config["room_count"]
    suite_config["room_count"] = int(room_count)
    summaries = [validate_layout_summary(int(seed), int(room_count), suite_config) for seed in seeds]
    report = {
        "root": ROOT,
        "room_count": int(room_count),
        "config": {
            "chest_count": _coerce_int(suite_config.get("chest_count"), DEFAULT_DUNGEON_CONFIG["chest_count"], 0, 16),
            "enemy_count": _coerce_int(suite_config.get("enemy_count"), DEFAULT_DUNGEON_CONFIG["enemy_count"], 0, 32),
            "key_count": _coerce_int(suite_config.get("key_count"), DEFAULT_DUNGEON_CONFIG["key_count"], 0, 8),
            "shop_count": _coerce_int(suite_config.get("shop_count"), DEFAULT_DUNGEON_CONFIG["shop_count"], 0, 6),
            "locked_door_count": _coerce_int(suite_config.get("locked_door_count"), DEFAULT_DUNGEON_CONFIG["locked_door_count"], 0, 8),
            "boss_enabled": _coerce_int(suite_config.get("boss_enabled"), DEFAULT_DUNGEON_CONFIG["boss_enabled"], 0, 1),
            "branch_chance_percent": _coerce_int(
                suite_config.get("branch_chance_percent"),
                DEFAULT_DUNGEON_CONFIG["branch_chance_percent"],
                0,
                100,
            ),
            "max_loop_edges": _coerce_int(suite_config.get("max_loop_edges"), DEFAULT_DUNGEON_CONFIG["max_loop_edges"], 0, 16),
            "grid_cell_size": _coerce_int(suite_config.get("grid_cell_size"), DEFAULT_DUNGEON_CONFIG["grid_cell_size"], 200, 1200),
            "corridor_width": _coerce_int(suite_config.get("corridor_width"), DEFAULT_DUNGEON_CONFIG["corridor_width"], 200, 1200),
            "use_ceiling": _coerce_int(suite_config.get("use_ceiling"), DEFAULT_DUNGEON_CONFIG["use_ceiling"], 0, 1),
            "use_theme_materials": _coerce_int(
                suite_config.get("use_theme_materials"),
                DEFAULT_DUNGEON_CONFIG["use_theme_materials"],
                0,
                1,
            ),
            "preview_mode": _coerce_int(suite_config.get("preview_mode"), DEFAULT_DUNGEON_CONFIG["preview_mode"], 0, 1),
        },
        "seed_count": len(seeds),
        "pass_count": sum(1 for item in summaries if item["pass"]),
        "fail_count": sum(1 for item in summaries if not item["pass"]),
        "summaries": summaries,
    }
    report["pass"] = report["fail_count"] == 0
    os.makedirs(os.path.dirname(SEED_SUITE_REPORT_PATH), exist_ok=True)
    with open(SEED_SUITE_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("CubelessDungeonPCG seed suite: " + json.dumps(report, ensure_ascii=False))
    return report


def _room_center(layout, room_id):
    return layout["rooms"][room_id]["center"]


def _coerce_int(value, fallback, min_value=None, max_value=None):
    try:
        coerced = int(str(value).strip())
    except Exception:
        coerced = fallback
    if min_value is not None:
        coerced = max(int(min_value), coerced)
    if max_value is not None:
        coerced = min(int(max_value), coerced)
    return coerced


def _config_tag_key(spec):
    return CONFIG_TAG_PREFIX + str(spec["tag"])


def _config_tag_alias_keys(spec):
    return [CONFIG_TAG_PREFIX + str(alias) for alias in spec.get("aliases", [])]


def _config_spec_lookup_by_tag_key():
    lookup = {}
    for spec in CONFIG_AUTHORING_SPECS:
        lookup[_config_tag_key(spec)] = spec
        for alias_key in _config_tag_alias_keys(spec):
            lookup[alias_key] = spec
    return lookup


def _coerce_config_spec_value(spec, value, fallback=None):
    config_key = spec["config_key"]
    fallback_value = DEFAULT_DUNGEON_CONFIG.get(config_key) if fallback is None else fallback
    return _coerce_int(value, fallback_value, spec.get("min"), spec.get("max"))


def _config_specs_report():
    report = []
    for spec in CONFIG_AUTHORING_SPECS:
        report.append(
            {
                "config_key": spec["config_key"],
                "tag": _config_tag_key(spec),
                "aliases": _config_tag_alias_keys(spec),
                "type": spec.get("type", "int"),
                "min": spec.get("min"),
                "max": spec.get("max"),
                "default": DEFAULT_DUNGEON_CONFIG.get(spec["config_key"]),
                "purpose": spec.get("purpose"),
            }
        )
    return report


def _config_tags_from_config(config):
    tags = []
    for spec in CONFIG_AUTHORING_SPECS:
        key = spec["config_key"]
        tags.append("{}={}".format(_config_tag_key(spec), config.get(key, DEFAULT_DUNGEON_CONFIG[key])))
    return tags


def _find_pcg_bridge_actor():
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_actor_label() == PCG_BRIDGE_LABEL:
                return actor
        except Exception:
            pass
    return None


def _parse_dungeon_config_from_actor(actor=None):
    config = dict(DEFAULT_DUNGEON_CONFIG)
    read_tags = []
    lookup = _config_spec_lookup_by_tag_key()
    if actor:
        for tag in list(actor.tags):
            text = str(tag)
            read_tags.append(text)
            if "=" not in text:
                continue
            key, value = text.split("=", 1)
            key = key.strip()
            value = value.strip()
            spec = lookup.get(key)
            if spec:
                config[spec["config_key"]] = _coerce_config_spec_value(spec, value, config.get(spec["config_key"]))
    config["source_actor_label"] = actor.get_actor_label() if actor else None
    config["source_actor_tags"] = read_tags
    return config


def _default_config_tags():
    return _config_tags_from_config(DEFAULT_DUNGEON_CONFIG)


def ensure_pcg_bridge_parameter_tags(save_dirty_packages=True):
    actor = _find_pcg_bridge_actor()
    if not actor:
        return {
            "actor_found": False,
            "actor_label": PCG_BRIDGE_LABEL,
            "added_tags": [],
            "existing_tags": [],
            "save_dirty_packages": {"skipped": True},
            "pass": False,
        }
    current_tags = [str(tag) for tag in list(actor.tags)]
    current_keys = set()
    for tag in current_tags:
        if "=" in tag:
            current_keys.add(tag.split("=", 1)[0])
        else:
            current_keys.add(tag)
    added_tags = []
    for tag in _default_config_tags():
        key = tag.split("=", 1)[0] if "=" in tag else tag
        if key in current_keys:
            continue
        current_tags.append(tag)
        current_keys.add(key)
        added_tags.append(tag)
    if added_tags:
        actor.tags = [unreal.Name(tag) for tag in current_tags]
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    result = {
        "actor_found": True,
        "actor_label": actor.get_actor_label(),
        "added_tags": added_tags,
        "existing_tags": current_tags,
        "save_dirty_packages": save_summary,
        "pass": bool(
            all((tag.split("=", 1)[0] if "=" in tag else tag) in current_keys for tag in _default_config_tags())
            and (not save_dirty_packages or _coerce_int(save_summary.get("dirty_after_count"), -1) == 0)
        ),
    }
    unreal.log(
        "CubelessDungeonPCG bridge parameter tags: "
        + json.dumps(
            {
                "pass": result["pass"],
                "actor_found": result["actor_found"],
                "added_tag_count": len(added_tags),
            },
            ensure_ascii=False,
        )
    )
    return result


def _write_authoring_surface_report(report):
    os.makedirs(os.path.dirname(AUTHORING_SURFACE_REPORT_PATH), exist_ok=True)
    with open(AUTHORING_SURFACE_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _write_authoring_preset_smoke_report(report):
    os.makedirs(os.path.dirname(AUTHORING_PRESET_SMOKE_REPORT_PATH), exist_ok=True)
    with open(AUTHORING_PRESET_SMOKE_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _normalize_authoring_config(config):
    normalized = dict(DEFAULT_DUNGEON_CONFIG)
    if config:
        normalized.update(config)
    for spec in CONFIG_AUTHORING_SPECS:
        key = spec["config_key"]
        normalized[key] = _coerce_config_spec_value(spec, normalized.get(key), DEFAULT_DUNGEON_CONFIG.get(key))
    return normalized


def _authoring_preset_reports():
    reports = {}
    for name, preset_config in sorted(DUNGEON_AUTHORING_PRESETS.items()):
        normalized = _normalize_authoring_config(preset_config)
        notes = DUNGEON_AUTHORING_PRESET_NOTES.get(name, {})
        layout_summary = validate_layout_summary(
            normalized["seed"],
            normalized["room_count"],
            normalized,
        )
        reports[name] = {
            "label": notes.get("label", name.replace("_", " ").title()),
            "intent": notes.get("intent", ""),
            "config": normalized,
            "tags": _config_tags_from_config(normalized),
            "layout_summary": {
                "pass": bool(layout_summary.get("pass")),
                "seed": layout_summary.get("seed"),
                "room_count": layout_summary.get("room_count"),
                "edge_count": layout_summary.get("edge_count"),
                "added_loop_edges": layout_summary.get("added_loop_edges"),
                "cell_count": layout_summary.get("cell_count"),
                "main_path_room_count": layout_summary.get("main_path_room_count"),
                "side_room_count": layout_summary.get("side_room_count"),
                "locked_door_count": layout_summary.get("locked_door_count"),
                "progression_pass": layout_summary.get("progression_pass"),
                "connectivity": layout_summary.get("connectivity"),
            },
        }
    return reports


def _compact_layout_summary(summary):
    return {
        "pass": bool(summary.get("pass")),
        "seed": summary.get("seed"),
        "requested_room_count": summary.get("requested_room_count"),
        "room_count": summary.get("room_count"),
        "edge_count": summary.get("edge_count"),
        "added_loop_edges": summary.get("added_loop_edges"),
        "cell_count": summary.get("cell_count"),
        "main_path_room_count": summary.get("main_path_room_count"),
        "side_room_count": summary.get("side_room_count"),
        "locked_door_count": summary.get("locked_door_count"),
        "lock_key_link_count": summary.get("lock_key_link_count"),
        "lock_key_missing_key_count": summary.get("lock_key_missing_key_count"),
        "encounter_spawn_slot_count": summary.get("encounter_spawn_slot_count"),
        "reward_anchor_count": summary.get("reward_anchor_count"),
        "start_exit_grid_distance": summary.get("start_exit_grid_distance"),
        "connectivity": summary.get("connectivity"),
        "role_counts": summary.get("role_counts"),
    }


def _preset_seed_values(config, seed_count):
    normalized = _normalize_authoring_config(config)
    base_seed = _coerce_int(normalized.get("seed"), DEFAULT_DUNGEON_CONFIG["seed"], 1, 2147483647)
    count = _coerce_int(seed_count, 5, 1, 32)
    return [base_seed + index for index in range(count)]


def _write_authoring_preset_matrix_report(report):
    os.makedirs(os.path.dirname(AUTHORING_PRESET_MATRIX_REPORT_PATH), exist_ok=True)
    with open(AUTHORING_PRESET_MATRIX_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def run_authoring_preset_seed_matrix(preset_names=None, seed_count=5, write_report=True):
    if preset_names is None:
        selected_names = sorted(DUNGEON_AUTHORING_PRESETS.keys())
    else:
        selected_names = [str(name) for name in preset_names]
    count = _coerce_int(seed_count, 5, 1, 32)
    presets = {}
    missing_presets = []
    failures = []
    for name in selected_names:
        preset = DUNGEON_AUTHORING_PRESETS.get(name)
        if preset is None:
            missing_presets.append(name)
            continue
        normalized = _normalize_authoring_config(preset)
        notes = DUNGEON_AUTHORING_PRESET_NOTES.get(name, {})
        seeds = _preset_seed_values(normalized, count)
        summaries = [
            _compact_layout_summary(validate_layout_summary(seed, normalized["room_count"], normalized))
            for seed in seeds
        ]
        failed_seeds = [summary.get("seed") for summary in summaries if not summary.get("pass")]
        pass_value = not failed_seeds
        if not pass_value:
            failures.append({"preset": name, "failed_seeds": failed_seeds})
        presets[name] = {
            "label": notes.get("label", name.replace("_", " ").title()),
            "intent": notes.get("intent", ""),
            "config": normalized,
            "tags": _config_tags_from_config(normalized),
            "seed_count": len(seeds),
            "seeds": seeds,
            "pass_count": sum(1 for summary in summaries if summary.get("pass")),
            "fail_count": len(failed_seeds),
            "failed_seeds": failed_seeds,
            "summaries": summaries,
            "pass": pass_value,
        }
    report = {
        "schema": "cubeless_pcg_dungeon_authoring_preset_matrix_v1",
        "status": "passed" if not failures and not missing_presets else "failed",
        "policy": (
            "Layout-only preset seed matrix for the PCG dungeon authoring surface. It does not regenerate "
            "Unreal assets, run NativeOutput, capture screenshots, implement gameplay, or touch project C++."
        ),
        "root": ROOT,
        "preset_count": len(presets),
        "seed_count": count,
        "available_presets": sorted(DUNGEON_AUTHORING_PRESETS.keys()),
        "selected_presets": selected_names,
        "missing_presets": missing_presets,
        "presets": presets,
        "failures": failures,
        "report_path": AUTHORING_PRESET_MATRIX_REPORT_PATH,
        "pass": not failures and not missing_presets,
    }
    if write_report:
        _write_authoring_preset_matrix_report(report)
    unreal.log(
        "CubelessDungeonPCG authoring preset matrix: "
        + json.dumps(
            {
                "pass": report["pass"],
                "preset_count": report["preset_count"],
                "seed_count": report["seed_count"],
                "failure_count": len(failures),
                "missing_presets": missing_presets,
            },
            ensure_ascii=False,
        )
    )
    return report


def get_authoring_preset_catalog(seed_count=0):
    presets = _authoring_preset_reports()
    matrix = None
    if _coerce_int(seed_count, 0, 0, 32) > 0:
        matrix = run_authoring_preset_seed_matrix(seed_count=seed_count, write_report=False)
    report = {
        "schema": "cubeless_pcg_dungeon_authoring_preset_catalog_v1",
        "status": "passed",
        "policy": (
            "Human-readable preset catalog for the C++-free PCG dungeon authoring surface. "
            "Use preset names with run_pcg_dungeon_generation_visual_gate_qa.py --preset <name>."
        ),
        "root": ROOT,
        "default_preset": "default",
        "available_presets": sorted(DUNGEON_AUTHORING_PRESETS.keys()),
        "preset_count": len(presets),
        "presets": presets,
        "operator_commands": {
            "list_matrix": "python Tools\\Unreal\\run_pcg_dungeon_authoring_preset_matrix.py --seed-count 5",
            "apply_preset_pattern": (
                "python Tools\\Unreal\\run_pcg_dungeon_generation_visual_gate_qa.py "
                "--preset <preset_name> --archive-label <label> --redraw-count 2"
            ),
            "restore_default": (
                "python Tools\\Unreal\\run_pcg_dungeon_generation_visual_gate_qa.py "
                "--preset default --archive-label default_restored_after_preset_review --redraw-count 2"
            ),
        },
        "seed_matrix": matrix,
        "pass": True if matrix is None else bool(matrix.get("pass")),
    }
    return report


def _config_preserved_actor_tags(tags):
    lookup = _config_spec_lookup_by_tag_key()
    preserved = []
    removed_config_tags = []
    for tag in [str(item) for item in list(tags or [])]:
        if "=" not in tag:
            preserved.append(tag)
            continue
        key = tag.split("=", 1)[0].strip()
        if key in lookup:
            removed_config_tags.append(tag)
        else:
            preserved.append(tag)
    return preserved, removed_config_tags


def _set_bridge_config_tags(actor, config):
    normalized = _normalize_authoring_config(config)
    current_tags = [str(tag) for tag in list(actor.tags)] if actor else []
    preserved_tags, removed_config_tags = _config_preserved_actor_tags(current_tags)
    next_tags = preserved_tags + _config_tags_from_config(normalized)
    actor.tags = [unreal.Name(tag) for tag in next_tags]
    return {
        "config": normalized,
        "previous_tags": current_tags,
        "preserved_tags": preserved_tags,
        "removed_config_tags": removed_config_tags,
        "next_tags": next_tags,
    }


def apply_authoring_preset_to_bridge(preset_name="default", save_dirty_packages=True):
    actor = _find_pcg_bridge_actor()
    preset = DUNGEON_AUTHORING_PRESETS.get(str(preset_name))
    if not actor or preset is None:
        result = {
            "schema": "cubeless_pcg_dungeon_authoring_preset_apply_v1",
            "status": "failed",
            "preset_name": str(preset_name),
            "actor_found": bool(actor),
            "preset_found": preset is not None,
            "available_presets": sorted(DUNGEON_AUTHORING_PRESETS.keys()),
            "pass": False,
        }
        unreal.log("CubelessDungeonPCG apply authoring preset: " + json.dumps(result, ensure_ascii=False))
        return result

    tag_update = _set_bridge_config_tags(actor, preset)
    parsed_config = _normalize_authoring_config(_parse_dungeon_config_from_actor(actor))
    layout_summary = validate_layout_summary(
        tag_update["config"]["seed"],
        tag_update["config"]["room_count"],
        tag_update["config"],
    )
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    checks = {
        "actor_found": True,
        "preset_found": True,
        "parsed_config_matches_preset": all(
            parsed_config.get(spec["config_key"]) == tag_update["config"].get(spec["config_key"])
            for spec in CONFIG_AUTHORING_SPECS
        ),
        "preset_layout_pass": bool(layout_summary.get("pass")),
        "save_dirty_packages_pass": (
            True if not save_dirty_packages else bool(save_summary.get("save_dirty_packages_result"))
            and _coerce_int(save_summary.get("dirty_after_count"), -1) == 0
        ),
    }
    pass_value = all(bool(value) for value in checks.values())
    result = {
        "schema": "cubeless_pcg_dungeon_authoring_preset_apply_v1",
        "status": "passed" if pass_value else "failed",
        "preset_name": str(preset_name),
        "actor_found": True,
        "preset_found": True,
        "actor_label": actor.get_actor_label(),
        "config": tag_update["config"],
        "tags": _config_tags_from_config(tag_update["config"]),
        "preserved_tag_count": len(tag_update["preserved_tags"]),
        "removed_config_tag_count": len(tag_update["removed_config_tags"]),
        "parsed_config": parsed_config,
        "layout_summary": layout_summary,
        "save_dirty_packages": save_summary,
        "checks": checks,
        "pass": pass_value,
    }
    unreal.log(
        "CubelessDungeonPCG apply authoring preset: "
        + json.dumps(
            {
                "pass": pass_value,
                "preset_name": str(preset_name),
                "seed": tag_update["config"].get("seed"),
                "room_count": tag_update["config"].get("room_count"),
                "added_loop_edges": layout_summary.get("added_loop_edges"),
            },
            ensure_ascii=False,
        )
    )
    return result


def validate_authoring_preset_apply_restore_smoke(preset_name="wide_looped", save_dirty_packages=True):
    actor = _find_pcg_bridge_actor()
    initial_tags = [str(tag) for tag in list(actor.tags)] if actor else []
    initial_config = _normalize_authoring_config(_parse_dungeon_config_from_actor(actor)) if actor else dict(DEFAULT_DUNGEON_CONFIG)
    apply_result = {}
    restored_tags = []
    restore_error = None
    try:
        apply_result = apply_authoring_preset_to_bridge(preset_name, save_dirty_packages=False)
    finally:
        if actor:
            try:
                actor.tags = [unreal.Name(tag) for tag in initial_tags]
                restored_tags = [str(tag) for tag in list(actor.tags)]
            except Exception as exc:
                restore_error = str(exc)

    restored_config = _normalize_authoring_config(_parse_dungeon_config_from_actor(actor)) if actor else dict(DEFAULT_DUNGEON_CONFIG)
    authoring_surface = validate_authoring_surface(actor) if actor else {"pass": False}
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    checks = {
        "bridge_actor_found": bool(actor),
        "preset_apply_pass": bool(apply_result.get("pass")),
        "restored_tags_match_initial": restored_tags == initial_tags,
        "restored_config_matches_initial": all(
            restored_config.get(spec["config_key"]) == initial_config.get(spec["config_key"])
            for spec in CONFIG_AUTHORING_SPECS
        ),
        "authoring_surface_pass_after_restore": bool(authoring_surface.get("pass")),
        "restore_error_absent": restore_error is None,
        "save_dirty_packages_pass": (
            True if not save_dirty_packages else bool(save_summary.get("save_dirty_packages_result"))
            and _coerce_int(save_summary.get("dirty_after_count"), -1) == 0
        ),
    }
    pass_value = all(bool(value) for value in checks.values())
    report = {
        "schema": "cubeless_pcg_dungeon_authoring_preset_smoke_v1",
        "status": "passed" if pass_value else "failed",
        "policy": (
            "C++-free preset workflow smoke. It applies one documented preset to the live bridge actor tags, "
            "validates parsed config/layout health, restores the exact original tags, then confirms the authoring "
            "surface and dirty-package state are clean."
        ),
        "preset_name": str(preset_name),
        "actor_label": actor.get_actor_label() if actor else None,
        "initial_config": initial_config,
        "initial_tags": initial_tags,
        "apply_result": apply_result,
        "restored_config": restored_config,
        "restored_tags": restored_tags,
        "restore_error": restore_error,
        "authoring_surface_after_restore": {
            "pass": bool(authoring_surface.get("pass")),
            "preset_failures": authoring_surface.get("preset_failures", []),
            "missing_config_keys": authoring_surface.get("current_actor", {}).get("missing_config_keys", []),
            "unknown_config_tags": authoring_surface.get("current_actor", {}).get("unknown_config_tags", []),
            "clamped_or_invalid_values": authoring_surface.get("current_actor", {}).get("clamped_or_invalid_values", []),
        },
        "save_dirty_packages": save_summary,
        "checks": checks,
        "report_path": AUTHORING_PRESET_SMOKE_REPORT_PATH,
        "pass": pass_value,
    }
    _write_authoring_preset_smoke_report(report)
    unreal.log(
        "CubelessDungeonPCG authoring preset smoke: "
        + json.dumps(
            {
                "pass": pass_value,
                "preset_name": str(preset_name),
                "failed_checks": [key for key, value in checks.items() if not value],
            },
            ensure_ascii=False,
        )
    )
    return report


def validate_authoring_surface(actor=None):
    actor = actor or _find_pcg_bridge_actor()
    lookup = _config_spec_lookup_by_tag_key()
    actor_found = bool(actor)
    raw_tags = [str(tag) for tag in list(actor.tags)] if actor else []
    unknown_config_tags = []
    malformed_config_tags = []
    non_config_dungeon_tags = []
    field_entries = {}
    clamped_or_invalid_values = []
    duplicate_fields = []

    for tag in raw_tags:
        text = str(tag)
        if not text.startswith(CONFIG_TAG_PREFIX):
            continue
        if "=" not in text:
            non_config_dungeon_tags.append(text)
            continue
        key, raw_value = text.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        spec = lookup.get(key)
        if not spec:
            unknown_config_tags.append(text)
            continue
        config_key = spec["config_key"]
        field_entries.setdefault(config_key, []).append({"tag": key, "value": raw_value})
        try:
            raw_int = int(str(raw_value).strip())
            parsed_ok = True
        except Exception:
            raw_int = None
            parsed_ok = False
            malformed_config_tags.append(text)
        coerced = _coerce_config_spec_value(spec, raw_value, DEFAULT_DUNGEON_CONFIG.get(config_key))
        if (not parsed_ok) or raw_int != coerced:
            clamped_or_invalid_values.append(
                {
                    "tag": key,
                    "value": raw_value,
                    "config_key": config_key,
                    "parsed_ok": parsed_ok,
                    "coerced": coerced,
                    "min": spec.get("min"),
                    "max": spec.get("max"),
                }
            )

    missing_config_keys = [
        spec["config_key"]
        for spec in CONFIG_AUTHORING_SPECS
        if spec["config_key"] not in field_entries
    ]
    for config_key, entries in sorted(field_entries.items()):
        if len(entries) > 1:
            duplicate_fields.append({"config_key": config_key, "entries": entries})

    current_config = _parse_dungeon_config_from_actor(actor) if actor else dict(DEFAULT_DUNGEON_CONFIG)
    normalized_current_config = _normalize_authoring_config(current_config)
    preset_reports = _authoring_preset_reports()
    preset_failures = [
        name for name, preset in preset_reports.items() if not bool(preset.get("layout_summary", {}).get("pass"))
    ]
    checks = {
        "bridge_actor_found": actor_found,
        "required_config_tags_present": not missing_config_keys,
        "unknown_config_tag_count_zero": not unknown_config_tags,
        "malformed_config_tag_count_zero": not malformed_config_tags,
        "clamped_or_invalid_value_count_zero": not clamped_or_invalid_values,
        "duplicate_canonical_field_count_zero": not duplicate_fields,
        "preset_layouts_pass": not preset_failures,
    }
    pass_value = all(bool(value) for value in checks.values())
    report = {
        "schema": "cubeless_pcg_dungeon_authoring_surface_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "bridge_actor_label": PCG_BRIDGE_LABEL,
        "policy": (
            "C++-free authoring surface report for the current PCG dungeon. The bridge actor tags are the supported "
            "authoring surface for this MVP; this report documents valid tags, ranges, aliases, presets, and current "
            "tag health before generation."
        ),
        "config_specs": _config_specs_report(),
        "presets": preset_reports,
        "current_actor": {
            "actor_found": actor_found,
            "actor_label": actor.get_actor_label() if actor else None,
            "raw_tags": raw_tags,
            "field_entries": field_entries,
            "current_config": normalized_current_config,
            "current_config_tags": _config_tags_from_config(normalized_current_config),
            "unknown_config_tags": unknown_config_tags,
            "malformed_config_tags": malformed_config_tags,
            "non_config_dungeon_tags": non_config_dungeon_tags,
            "missing_config_keys": missing_config_keys,
            "duplicate_fields": duplicate_fields,
            "clamped_or_invalid_values": clamped_or_invalid_values,
        },
        "preset_failures": preset_failures,
        "checks": checks,
        "report_path": AUTHORING_SURFACE_REPORT_PATH,
        "pass": pass_value,
    }
    _write_authoring_surface_report(report)
    unreal.log(
        "CubelessDungeonPCG authoring surface: "
        + json.dumps(
            {
                "pass": pass_value,
                "missing_config_key_count": len(missing_config_keys),
                "unknown_config_tag_count": len(unknown_config_tags),
                "clamped_or_invalid_value_count": len(clamped_or_invalid_values),
                "preset_failure_count": len(preset_failures),
            },
            ensure_ascii=False,
        )
    )
    return report


def spawn_validation_dungeon(source="direct", seed=None, config=None):
    if config is None:
        config = dict(DEFAULT_DUNGEON_CONFIG)
    else:
        merged = dict(DEFAULT_DUNGEON_CONFIG)
        merged.update(config)
        config = merged
    if seed is not None:
        config["seed"] = _coerce_int(seed, config["seed"], 1, 2147483647)
    seed = _coerce_int(config.get("seed"), DEFAULT_DUNGEON_CONFIG["seed"], 1, 2147483647)
    room_count = _coerce_int(config.get("room_count"), DEFAULT_DUNGEON_CONFIG["room_count"], 2, 32)
    ceiling_stride = _coerce_int(config.get("ceiling_stride"), DEFAULT_DUNGEON_CONFIG["ceiling_stride"], 0, 64)
    chest_count = _coerce_int(config.get("chest_count"), DEFAULT_DUNGEON_CONFIG["chest_count"], 0, 16)
    enemy_count = _coerce_int(config.get("enemy_count"), DEFAULT_DUNGEON_CONFIG["enemy_count"], 0, 32)
    key_count = _coerce_int(config.get("key_count"), DEFAULT_DUNGEON_CONFIG["key_count"], 0, 8)
    shop_count = _coerce_int(config.get("shop_count"), DEFAULT_DUNGEON_CONFIG["shop_count"], 0, 6)
    locked_door_count = _coerce_int(config.get("locked_door_count"), DEFAULT_DUNGEON_CONFIG["locked_door_count"], 0, 8)
    boss_enabled = _coerce_int(config.get("boss_enabled"), DEFAULT_DUNGEON_CONFIG["boss_enabled"], 0, 1)
    branch_chance_percent = _coerce_int(
        config.get("branch_chance_percent"),
        DEFAULT_DUNGEON_CONFIG["branch_chance_percent"],
        0,
        100,
    )
    max_loop_edges = _coerce_int(config.get("max_loop_edges"), DEFAULT_DUNGEON_CONFIG["max_loop_edges"], 0, 16)
    grid_cell_size = _coerce_int(config.get("grid_cell_size"), DEFAULT_DUNGEON_CONFIG["grid_cell_size"], 200, 1200)
    corridor_width = _coerce_int(config.get("corridor_width"), DEFAULT_DUNGEON_CONFIG["corridor_width"], 200, 1200)
    use_ceiling = _coerce_int(config.get("use_ceiling"), DEFAULT_DUNGEON_CONFIG["use_ceiling"], 0, 1)
    use_theme_materials = _coerce_int(
        config.get("use_theme_materials"),
        DEFAULT_DUNGEON_CONFIG["use_theme_materials"],
        0,
        1,
    )
    preview_mode = _coerce_int(config.get("preview_mode"), DEFAULT_DUNGEON_CONFIG["preview_mode"], 0, 1)
    effective_ceiling_stride = ceiling_stride if use_ceiling > 0 else 0
    generation_metrics = _set_generation_metrics(grid_cell_size=grid_cell_size, corridor_width=corridor_width)
    grid_cell_size = int(round(generation_metrics["grid_cell_size"]))
    corridor_width = int(round(generation_metrics["corridor_width"]))
    grid_scale = _grid_scale_xy()
    corridor_scale = _corridor_width_scale()

    meshes = {
        key: unreal.EditorAssetLibrary.load_asset(MESH_DIR + "/" + asset_name)
        for key, asset_name in MODULE_SPECS
    }
    missing = [key for key, mesh in meshes.items() if not mesh]
    if missing:
        build_module_assets()
        meshes = {
            key: unreal.EditorAssetLibrary.load_asset(MESH_DIR + "/" + asset_name)
            for key, asset_name in MODULE_SPECS
        }
        missing = [key for key, mesh in meshes.items() if not mesh]
    if missing:
        raise RuntimeError("Missing dungeon module meshes: " + ", ".join(missing))
    navigation_collision_report = ensure_module_navigation_collision(meshes)

    materials = (
        {name: unreal.EditorAssetLibrary.load_asset(MATERIAL_DIR + "/" + name) for name, *_rest in MATERIALS}
        if use_theme_materials > 0
        else {}
    )
    removed = clear_generated_dungeon()
    layout = generate_layout(
        seed=seed,
        room_count=room_count,
        branch_chance_percent=branch_chance_percent,
        max_loop_edges=max_loop_edges,
    )
    progression = assign_room_progression(
        layout,
        {
            "chest_count": chest_count,
            "enemy_count": enemy_count,
            "key_count": key_count,
            "shop_count": shop_count,
            "locked_door_count": locked_door_count,
            "boss_enabled": boss_enabled,
        },
    )
    encounter_profiles = assign_encounter_profiles(layout, progression)
    room_archetypes = assign_room_archetypes(layout, progression, encounter_profiles)
    room_themes = assign_room_themes(room_archetypes)
    room_shapes = assign_room_shapes(layout, progression, room_archetypes)
    lock_key_links = assign_lock_key_links(layout, progression)
    cells = layout["cells"]
    actors = []
    volume_records = []
    door_records = []
    connector_detail_records = []
    corridor_detail_records = []
    room_variant_records = []
    spawn_records = []
    route_records = []
    encounter_spawn_records = []
    reward_records = []
    theme_light_records = []
    playtest_records = []
    nav_waypoint_records = []
    detail_records = []
    detail_mesh_records = []
    counts = {
        "floor": 0,
        "corridor": 0,
        "corner": 0,
        "ceiling": 0,
        "ceiling_room": 0,
        "ceiling_corridor": 0,
        "ceiling_corner": 0,
        "wall": 0,
        "door": 0,
        "column": 0,
        "stair": 0,
        "marker": 0,
        "seal": 0,
        "light": 0,
        "theme_light": 0,
        "review_postprocess": 0,
        "connector_detail": 0,
        "corridor_detail": 0,
        "room_variant_detail": 0,
        "room_volume": 0,
        "door_volume": 0,
        "gate_volume": 0,
        "door_anchor": 0,
        "spawn_anchor": 0,
        "route_anchor": 0,
        "encounter_spawn": 0,
        "reward_anchor": 0,
        "player_start": 0,
        "nav_bounds": 0,
        "nav_waypoint": 0,
        "detail_anchor": 0,
        "detail_mesh": 0,
    }
    side_order = {int(room_id): index for index, room_id in enumerate(sorted(progression["side_room_ids"]))}
    lock_link_by_after_room_id = {
        int(link["after_room_id"]): link
        for link in lock_key_links
    }

    for index, cell in enumerate(sorted(cells.keys())):
        kind = cells[cell]["kind"]
        room_id = cells[cell]["room_id"]
        cell_theme = _theme_for_cell(room_themes, room_id, kind)
        cell_archetype = room_archetypes.get(int(room_id)) if room_id is not None and int(room_id) >= 0 else None
        cell_shape = room_shapes.get(int(room_id)) if room_id is not None and int(room_id) >= 0 else None
        if kind == "corridor" and _is_corridor_corner(cell, cells):
            mesh_key = "corner"
        elif kind == "corridor":
            mesh_key = "corridor"
        else:
            mesh_key = "floor"
        cell_mesh_scale = _module_scale()
        if kind == "corridor":
            corridor_profile = _corridor_detail_profile(cell, cells)
            if mesh_key == "corner":
                cell_mesh_scale = _module_scale(scale_x=corridor_scale, scale_y=corridor_scale)
            else:
                cell_mesh_scale = _yaw_width_scale(corridor_profile["yaw"], corridor_scale)
        cell_tags = _dungeon_actor_tags(
            seed,
            "cell",
            cell=cell,
            room_id=room_id,
            cell_kind=kind,
            roles=_room_roles_for(progression, room_id),
            extra=["DungeonMeshKey={}".format(mesh_key)]
            + _room_archetype_tags(cell_archetype)
            + _room_shape_tags(cell_shape)
            + _theme_tags(cell_theme),
        )
        actors.append(
            _spawn_static_mesh(
                ACTOR_PREFIX + mesh_key.capitalize() + "_{:03d}".format(index),
                meshes[mesh_key],
                _cell_to_location(cell, 0),
                material=_theme_material(materials, cell_theme),
                tags=cell_tags,
                scale=cell_mesh_scale,
            )
        )
        counts[mesh_key] += 1
        if effective_ceiling_stride > 0 and index % effective_ceiling_stride == 0:
            ceiling_mesh_key = _ceiling_mesh_key_for_cell(kind, mesh_key)
            ceiling_kind = ceiling_mesh_key.replace("ceiling_", "")
            ceiling_index = int(counts["ceiling"])
            actors.append(
                _spawn_static_mesh(
                    ACTOR_PREFIX + "Ceiling_{}_{:03d}".format(ceiling_kind.title(), ceiling_index),
                    meshes[ceiling_mesh_key],
                    _cell_to_location(cell, WALL_HEIGHT + 10),
                    tags=_dungeon_actor_tags(
                        seed,
                        "ceiling",
                        cell=cell,
                        room_id=room_id,
                        cell_kind=kind,
                        roles=_room_roles_for(progression, room_id),
                        extra=[
                            "DungeonCeilingKind={}".format(ceiling_kind),
                            "DungeonCeilingIndex={}".format(ceiling_index),
                            "DungeonCeilingMeshKey={}".format(ceiling_mesh_key),
                        ]
                        + _room_archetype_tags(cell_archetype)
                        + _room_shape_tags(cell_shape)
                        + _theme_tags(cell_theme),
                    ),
                    scale=cell_mesh_scale,
                )
            )
            counts["ceiling"] += 1
            counts[ceiling_mesh_key] += 1

    for room in layout["rooms"]:
        room_id = room["id"]
        center = room["center"]
        roles = _room_roles_for(progression, room_id)
        encounter = encounter_profiles.get(int(room_id))
        archetype = room_archetypes.get(int(room_id))
        theme = room_themes.get(int(room_id))
        shape = room_shapes.get(int(room_id))
        loc = _cell_to_location(center, WALL_HEIGHT * 0.5)
        cell_size = _grid_cell_size()
        extent = (
            max(cell_size * 0.5, room["w"] * cell_size * 0.5 - _scaled_xy(24.0)),
            max(cell_size * 0.5, room["h"] * cell_size * 0.5 - _scaled_xy(24.0)),
            WALL_HEIGHT * 0.5,
        )
        label = ACTOR_PREFIX + "RoomVolume_{:03d}".format(counts["room_volume"])
        actors.append(
            _spawn_trigger_box(
                label,
                loc,
                extent,
                tags=_dungeon_actor_tags(
                    seed,
                    "volume",
                    cell=center,
                    room_id=room_id,
                    cell_kind="room_volume",
                    roles=roles,
                    extra=["DungeonVolumeKind=room"]
                    + ["DungeonGameplayRole={}".format(role) for role in roles]
                    + _room_archetype_tags(archetype)
                    + _room_shape_tags(shape)
                    + _theme_tags(theme)
                    + _encounter_tags(encounter),
                ),
            )
        )
        volume_records.append(
            {
                "label": label,
                "kind": "room",
                "room_id": int(room_id),
                "cell": [int(center[0]), int(center[1])],
                "location": [float(loc.x), float(loc.y), float(loc.z)],
                "extent": [float(extent[0]), float(extent[1]), float(extent[2])],
                "roles": roles,
                "encounter": encounter,
                "archetype": archetype,
                "theme": theme,
                "shape": shape,
            }
        )
        counts["room_volume"] += 1

    locked_after_room_ids = set(lock_link_by_after_room_id.keys())
    locked_seal_room_ids = set()
    door_edges = set()
    for cell, data in cells.items():
        for direction, neighbor in _neighbors(cell).items():
            if neighbor not in cells:
                loc, rot = _wall_transform(cell, direction)
                wall_room_id = data["room_id"]
                wall_theme = _theme_for_cell(room_themes, wall_room_id, data["kind"])
                wall_archetype = room_archetypes.get(int(wall_room_id)) if int(wall_room_id) >= 0 else None
                wall_shape = room_shapes.get(int(wall_room_id)) if int(wall_room_id) >= 0 else None
                actors.append(
                    _spawn_static_mesh(
                        ACTOR_PREFIX + "Wall_{:03d}".format(counts["wall"]),
                        meshes["wall"],
                        loc,
                        rot,
                        material=_theme_material(materials, wall_theme),
                        tags=_dungeon_actor_tags(
                            seed,
                            "wall",
                            cell=cell,
                            room_id=wall_room_id,
                            cell_kind=data["kind"],
                            roles=_room_roles_for(progression, wall_room_id),
                            extra=["DungeonDirection={}".format(direction)]
                            + _room_archetype_tags(wall_archetype)
                            + _room_shape_tags(wall_shape)
                            + _theme_tags(wall_theme),
                        ),
                    )
                )
                counts["wall"] += 1
            else:
                a_kind = data["kind"]
                b_kind = cells[neighbor]["kind"]
                if a_kind != b_kind and cell < neighbor:
                    loc, rot = _wall_transform(cell, direction)
                    door_edges.add((cell, neighbor))
                    room_id = data["room_id"] if a_kind == "room" else cells[neighbor]["room_id"]
                    encounter = encounter_profiles.get(int(room_id))
                    door_archetype = room_archetypes.get(int(room_id))
                    door_theme = room_themes.get(int(room_id))
                    door_shape = room_shapes.get(int(room_id))
                    is_locked_gate = room_id in locked_after_room_ids and room_id not in locked_seal_room_ids
                    door_kind = "locked" if is_locked_gate else "normal"
                    lock_link = lock_link_by_after_room_id.get(int(room_id)) if is_locked_gate else None
                    room_cell = cell if a_kind == "room" else neighbor
                    corridor_cell = neighbor if a_kind == "room" else cell
                    main_index = _room_main_path_index(progression, room_id)
                    route_kind = "main" if main_index >= 0 else "side"
                    route_index = main_index if main_index >= 0 else side_order.get(int(room_id), -1)
                    door_label = ACTOR_PREFIX + "Door_{:03d}".format(counts["door"])
                    actors.append(
                        _spawn_static_mesh(
                            door_label,
                            meshes["door"],
                            loc,
                            rot,
                            material=_theme_material(materials, door_theme),
                            tags=_dungeon_actor_tags(
                                seed,
                                "door",
                                cell=cell,
                                room_id=room_id,
                                cell_kind="room_corridor_edge",
                                roles=_room_roles_for(progression, room_id),
                                extra=[
                                    "DungeonDoorKind={}".format(door_kind),
                                    "DungeonDirection={}".format(direction),
                                    "DungeonNeighborCell={}".format(_cell_text(neighbor)),
                                ]
                                + _room_archetype_tags(door_archetype)
                                + _room_shape_tags(door_shape)
                                + _theme_tags(door_theme)
                                + _lock_tags(lock_link)
                                + _encounter_tags(encounter),
                            ),
                            scale=_directional_width_scale(direction, corridor_scale),
                        )
                    )
                    counts["door"] += 1
                    door_volume_loc = unreal.Vector(loc.x, loc.y, WALL_HEIGHT * 0.5)
                    door_volume_extent = (
                        _scaled_xy(150.0) * corridor_scale,
                        _scaled_xy(75.0),
                        WALL_HEIGHT * 0.5,
                    )
                    door_volume_label = ACTOR_PREFIX + "DoorVolume_{:03d}".format(counts["door_volume"])
                    actors.append(
                        _spawn_trigger_box(
                            door_volume_label,
                            door_volume_loc,
                            door_volume_extent,
                            rot,
                            tags=_dungeon_actor_tags(
                                seed,
                                "volume",
                                cell=cell,
                                room_id=room_id,
                                cell_kind="room_corridor_edge",
                                roles=_room_roles_for(progression, room_id),
                                extra=[
                                    "DungeonVolumeKind=door",
                                    "DungeonDoorKind={}".format(door_kind),
                                    "DungeonDirection={}".format(direction),
                                    "DungeonNeighborCell={}".format(_cell_text(neighbor)),
                                ]
                                + _room_archetype_tags(door_archetype)
                                + _room_shape_tags(door_shape)
                                + _theme_tags(door_theme)
                                + _lock_tags(lock_link)
                                + _encounter_tags(encounter),
                            ),
                        )
                    )
                    volume_records.append(
                        {
                            "label": door_volume_label,
                            "kind": "door",
                            "door_kind": door_kind,
                            "room_id": int(room_id),
                            "cell": [int(cell[0]), int(cell[1])],
                            "neighbor_cell": [int(neighbor[0]), int(neighbor[1])],
                            "direction": direction,
                            "location": [float(door_volume_loc.x), float(door_volume_loc.y), float(door_volume_loc.z)],
                            "extent": [float(value) for value in door_volume_extent],
                            "roles": _room_roles_for(progression, room_id),
                            "lock_link": lock_link,
                            "encounter": encounter,
                            "archetype": door_archetype,
                            "theme": door_theme,
                            "shape": door_shape,
                        }
                    )
                    counts["door_volume"] += 1
                    door_anchor_loc = unreal.Vector(door_volume_loc.x, door_volume_loc.y, WALL_HEIGHT * 0.58)
                    door_anchor_label = ACTOR_PREFIX + "DoorAnchor_{:03d}".format(counts["door_anchor"])
                    actors.append(
                        _spawn_target_point(
                            door_anchor_label,
                            door_anchor_loc,
                            rot,
                            tags=_dungeon_actor_tags(
                                seed,
                                "door_anchor",
                                cell=cell,
                                room_id=room_id,
                                cell_kind="room_corridor_edge",
                                roles=_room_roles_for(progression, room_id),
                                extra=[
                                    "DungeonDoorIndex={}".format(counts["door_anchor"]),
                                    "DungeonDoorKind={}".format(door_kind),
                                    "DungeonDirection={}".format(direction),
                                    "DungeonNeighborCell={}".format(_cell_text(neighbor)),
                                    "DungeonRoomCell={}".format(_cell_text(room_cell)),
                                    "DungeonCorridorCell={}".format(_cell_text(corridor_cell)),
                                    "DungeonDoorInteraction=entry",
                                    "DungeonDoorActorLabel={}".format(door_label),
                                    "DungeonDoorVolumeLabel={}".format(door_volume_label),
                                    "DungeonRouteKind={}".format(route_kind),
                                    "DungeonRouteIndex={}".format(route_index),
                                    "DungeonMainPathIndex={}".format(main_index),
                                ]
                                + _room_archetype_tags(door_archetype)
                                + _room_shape_tags(door_shape)
                                + _theme_tags(door_theme)
                                + _lock_tags(lock_link)
                                + _encounter_tags(encounter),
                            ),
                        )
                    )
                    door_records.append(
                        {
                            "label": door_anchor_label,
                            "kind": "door_anchor",
                            "door_index": int(counts["door_anchor"]),
                            "door_kind": door_kind,
                            "door_actor_label": door_label,
                            "door_volume_label": door_volume_label,
                            "interaction": "entry",
                            "room_id": int(room_id),
                            "cell": [int(cell[0]), int(cell[1])],
                            "room_cell": [int(room_cell[0]), int(room_cell[1])],
                            "corridor_cell": [int(corridor_cell[0]), int(corridor_cell[1])],
                            "neighbor_cell": [int(neighbor[0]), int(neighbor[1])],
                            "direction": direction,
                            "location": [float(door_anchor_loc.x), float(door_anchor_loc.y), float(door_anchor_loc.z)],
                            "route_kind": route_kind,
                            "route_index": int(route_index),
                            "main_path_index": int(main_index),
                            "roles": _room_roles_for(progression, room_id),
                            "lock_link": lock_link,
                            "encounter": encounter,
                            "archetype": door_archetype,
                            "theme": door_theme,
                            "shape": door_shape,
                        }
                    )
                    connector_mesh_key = "connector_locked" if door_kind == "locked" else "connector_threshold"
                    connector_kind = "locked_threshold" if door_kind == "locked" else "threshold"
                    connector_index = int(counts["connector_detail"])
                    connector_label = ACTOR_PREFIX + "ConnectorDetail_{}_{:03d}".format(
                        connector_kind.title().replace("_", ""),
                        connector_index,
                    )
                    connector_loc = unreal.Vector(loc.x, loc.y, 0.0)
                    actors.append(
                        _spawn_static_mesh(
                            connector_label,
                            meshes[connector_mesh_key],
                            connector_loc,
                            rot,
                            tags=_dungeon_actor_tags(
                                seed,
                                "connector_detail",
                                cell=cell,
                                room_id=room_id,
                                cell_kind="room_corridor_edge",
                                roles=_room_roles_for(progression, room_id),
                                extra=[
                                    "DungeonConnectorKind={}".format(connector_kind),
                                    "DungeonConnectorIndex={}".format(connector_index),
                                    "DungeonConnectorMeshKey={}".format(connector_mesh_key),
                                    "DungeonDoorIndex={}".format(counts["door_anchor"]),
                                    "DungeonDoorKind={}".format(door_kind),
                                    "DungeonDirection={}".format(direction),
                                    "DungeonNeighborCell={}".format(_cell_text(neighbor)),
                                    "DungeonRoomCell={}".format(_cell_text(room_cell)),
                                    "DungeonCorridorCell={}".format(_cell_text(corridor_cell)),
                                    "DungeonDoorActorLabel={}".format(door_label),
                                    "DungeonDoorAnchorLabel={}".format(door_anchor_label),
                                    "DungeonDoorVolumeLabel={}".format(door_volume_label),
                                    "DungeonRouteKind={}".format(route_kind),
                                    "DungeonRouteIndex={}".format(route_index),
                                    "DungeonMainPathIndex={}".format(main_index),
                                ]
                                + _room_archetype_tags(door_archetype)
                                + _room_shape_tags(door_shape)
                                + _theme_tags(door_theme)
                                + _lock_tags(lock_link)
                                + _encounter_tags(encounter),
                            ),
                            scale=_directional_width_scale(direction, corridor_scale),
                        )
                    )
                    connector_detail_records.append(
                        {
                            "label": connector_label,
                            "kind": "connector_detail",
                            "connector_kind": connector_kind,
                            "connector_index": connector_index,
                            "mesh_key": connector_mesh_key,
                            "door_index": int(counts["door_anchor"]),
                            "door_kind": door_kind,
                            "door_actor_label": door_label,
                            "door_anchor_label": door_anchor_label,
                            "door_volume_label": door_volume_label,
                            "room_id": int(room_id),
                            "cell": [int(cell[0]), int(cell[1])],
                            "room_cell": [int(room_cell[0]), int(room_cell[1])],
                            "corridor_cell": [int(corridor_cell[0]), int(corridor_cell[1])],
                            "neighbor_cell": [int(neighbor[0]), int(neighbor[1])],
                            "direction": direction,
                            "location": _location_record(connector_loc),
                            "route_kind": route_kind,
                            "route_index": int(route_index),
                            "main_path_index": int(main_index),
                            "roles": _room_roles_for(progression, room_id),
                            "lock_link": lock_link,
                            "encounter": encounter,
                            "archetype": door_archetype,
                            "theme": door_theme,
                            "shape": door_shape,
                        }
                    )
                    counts["connector_detail"] += 1
                    counts["door_anchor"] += 1
                    if is_locked_gate:
                        seal_loc = unreal.Vector(loc.x, loc.y, loc.z + 120.0)
                        actors.append(
                            _spawn_static_mesh(
                                ACTOR_PREFIX + "LockedSeal_{:03d}".format(counts["seal"]),
                                meshes["seal"],
                                seal_loc,
                                rot,
                                tags=_dungeon_actor_tags(
                                    seed,
                                    "locked_door_seal",
                                    cell=cell,
                                    room_id=room_id,
                                    cell_kind="room_corridor_edge",
                                    roles=_room_roles_for(progression, room_id),
                                    extra=[
                                        "DungeonDoorKind=locked",
                                        "DungeonDirection={}".format(direction),
                                        "DungeonNeighborCell={}".format(_cell_text(neighbor)),
                                    ]
                                    + _room_archetype_tags(door_archetype)
                                    + _room_shape_tags(door_shape)
                                    + _theme_tags(door_theme)
                                    + _lock_tags(lock_link)
                                    + _encounter_tags(encounter),
                                ),
                                scale=_directional_width_scale(direction, corridor_scale),
                            )
                        )
                        counts["seal"] += 1
                        gate_volume_loc = unreal.Vector(loc.x, loc.y, WALL_HEIGHT * 0.5)
                        gate_volume_extent = (
                            _scaled_xy(190.0) * corridor_scale,
                            _scaled_xy(95.0),
                            WALL_HEIGHT * 0.56,
                        )
                        gate_volume_label = ACTOR_PREFIX + "GateVolume_{:03d}".format(counts["gate_volume"])
                        actors.append(
                            _spawn_trigger_box(
                                gate_volume_label,
                                gate_volume_loc,
                                gate_volume_extent,
                                rot,
                                tags=_dungeon_actor_tags(
                                    seed,
                                    "volume",
                                    cell=cell,
                                    room_id=room_id,
                                    cell_kind="locked_gate",
                                    roles=_room_roles_for(progression, room_id),
                                    extra=[
                                        "DungeonVolumeKind=gate",
                                        "DungeonDoorKind=locked",
                                        "DungeonDirection={}".format(direction),
                                        "DungeonNeighborCell={}".format(_cell_text(neighbor)),
                                    ]
                                    + _room_archetype_tags(door_archetype)
                                    + _room_shape_tags(door_shape)
                                    + _theme_tags(door_theme)
                                    + _lock_tags(lock_link)
                                    + _encounter_tags(encounter),
                                ),
                            )
                        )
                        volume_records.append(
                            {
                                "label": gate_volume_label,
                                "kind": "gate",
                                "door_kind": "locked",
                                "room_id": int(room_id),
                                "cell": [int(cell[0]), int(cell[1])],
                                "neighbor_cell": [int(neighbor[0]), int(neighbor[1])],
                                "direction": direction,
                                "location": [float(gate_volume_loc.x), float(gate_volume_loc.y), float(gate_volume_loc.z)],
                                "extent": [float(value) for value in gate_volume_extent],
                                "roles": _room_roles_for(progression, room_id),
                                "lock_link": lock_link,
                                "encounter": encounter,
                                "archetype": door_archetype,
                                "theme": door_theme,
                                "shape": door_shape,
                            }
                        )
                        counts["gate_volume"] += 1
                        locked_seal_room_ids.add(room_id)

    for room in layout["rooms"]:
        corner_cells = [
            (room["x"], room["y"]),
            (room["x"] + room["w"] - 1, room["y"]),
            (room["x"], room["y"] + room["h"] - 1),
            (room["x"] + room["w"] - 1, room["y"] + room["h"] - 1),
        ]
        for cell in corner_cells:
            loc = _cell_to_location(cell, 0)
            loc.z = 0
            loc.x += _scaled_xy(118.0) if cell[0] == room["x"] else -_scaled_xy(118.0)
            loc.y += _scaled_xy(118.0) if cell[1] == room["y"] else -_scaled_xy(118.0)
            column_archetype = room_archetypes.get(int(room["id"]))
            column_theme = room_themes.get(int(room["id"]))
            column_shape = room_shapes.get(int(room["id"]))
            actors.append(
                _spawn_static_mesh(
                    ACTOR_PREFIX + "Column_{:03d}".format(counts["column"]),
                    meshes["column"],
                    loc,
                    material=_theme_material(materials, column_theme),
                    tags=_dungeon_actor_tags(
                        seed,
                        "column",
                        cell=cell,
                        room_id=room["id"],
                        cell_kind="room_corner",
                        roles=_room_roles_for(progression, room["id"]),
                        extra=_room_archetype_tags(column_archetype) + _room_shape_tags(column_shape) + _theme_tags(column_theme),
                    ),
                )
            )
            counts["column"] += 1

    exit_center = _room_center(layout, layout["exit_room_id"])
    stair_loc = _cell_to_location(exit_center, 0)
    stair_loc.y += _scaled_xy(80.0)
    stair_archetype = room_archetypes.get(int(layout["exit_room_id"]))
    stair_theme = room_themes.get(int(layout["exit_room_id"]))
    stair_shape = room_shapes.get(int(layout["exit_room_id"]))
    actors.append(
        _spawn_static_mesh(
            ACTOR_PREFIX + "Stair_000",
            meshes["stair"],
            stair_loc,
            _actor_rotator(),
            material=_theme_material(materials, stair_theme),
            tags=_dungeon_actor_tags(
                seed,
                "stair",
                cell=exit_center,
                room_id=layout["exit_room_id"],
                cell_kind="exit_room",
                roles=_room_roles_for(progression, layout["exit_room_id"]),
                extra=_room_archetype_tags(stair_archetype) + _room_shape_tags(stair_shape) + _theme_tags(stair_theme),
            ),
        )
    )
    counts["stair"] += 1

    marker_specs = [
        ("Start", layout["start_room_id"], "M_Dungeon_Start_Green", unreal.Vector(0, 0, 0)),
        ("Exit", layout["exit_room_id"], "M_Dungeon_Exit_Blue", unreal.Vector(0, -_scaled_xy(90.0), 0)),
    ]
    if progression["boss_room_id"] is not None:
        marker_specs.append(("Boss", progression["boss_room_id"], "M_Dungeon_Boss_Magenta", unreal.Vector(_scaled_xy(82.0), _scaled_xy(82.0), 0)))
    for room_id in progression["key_room_ids"]:
        marker_specs.append(("Key", room_id, "M_Dungeon_Key_Cyan", unreal.Vector(-_scaled_xy(80.0), _scaled_xy(78.0), 0)))
    for room_id in progression["shop_room_ids"]:
        marker_specs.append(("Shop", room_id, "M_Dungeon_Shop_Teal", unreal.Vector(_scaled_xy(78.0), -_scaled_xy(78.0), 0)))
    for room_id in progression["treasure_room_ids"]:
        marker_specs.append(("Chest", room_id, "M_Dungeon_Chest_Gold", unreal.Vector(_scaled_xy(80.0), _scaled_xy(70.0), 0)))
    for room_id in progression["enemy_room_ids"]:
        marker_specs.append(("Enemy", room_id, "M_Dungeon_Enemy_Red", unreal.Vector(-_scaled_xy(80.0), -_scaled_xy(70.0), 0)))

    for label, room_id, material_name, offset in marker_specs:
        cell = _room_center(layout, room_id)
        loc = _cell_to_location(cell, 0)
        loc.x += offset.x
        loc.y += offset.y
        loc.z = 18
        material = materials.get(material_name)
        encounter = encounter_profiles.get(int(room_id))
        marker_archetype = room_archetypes.get(int(room_id))
        marker_theme = room_themes.get(int(room_id))
        marker_shape = room_shapes.get(int(room_id))
        role_name = {
            "Start": "start",
            "Exit": "exit",
            "Boss": "boss",
            "Key": "key",
            "Shop": "shop",
            "Chest": "treasure",
            "Enemy": "combat",
        }.get(label, label.lower())
        key_tags = _key_tags_for_room(lock_key_links, room_id)
        key_links = [link for link in lock_key_links if link.get("key_room_id") == int(room_id)]
        actors.append(
            _spawn_static_mesh(
                ACTOR_PREFIX + label + "Marker_{:03d}".format(counts["marker"]),
                meshes["marker"],
                loc,
                material=material,
                tags=_dungeon_actor_tags(
                    seed,
                    "marker",
                    cell=cell,
                    room_id=room_id,
                    cell_kind="room_center",
                    roles=_room_roles_for(progression, room_id),
                    extra=[
                        "DungeonMarker={}".format(label),
                        "DungeonGameplayRole={}".format(role_name),
                    ]
                    + key_tags
                    + _room_archetype_tags(marker_archetype)
                    + _room_shape_tags(marker_shape)
                    + _theme_tags(marker_theme)
                    + _encounter_tags(encounter),
                ),
            )
        )
        counts["marker"] += 1
        anchor_loc = unreal.Vector(loc.x, loc.y, 92.0)
        anchor_label = ACTOR_PREFIX + "SpawnAnchor_{}_{:03d}".format(label, counts["spawn_anchor"])
        actors.append(
            _spawn_target_point(
                anchor_label,
                anchor_loc,
                tags=_dungeon_actor_tags(
                    seed,
                    "spawn_anchor",
                    cell=cell,
                    room_id=room_id,
                    cell_kind="room_center",
                    roles=_room_roles_for(progression, room_id),
                    extra=[
                        "DungeonMarker={}".format(label),
                        "DungeonGameplayRole={}".format(role_name),
                        "DungeonSpawnKind={}".format(role_name),
                        "DungeonAnchorIndex={}".format(counts["spawn_anchor"]),
                    ]
                    + key_tags
                    + _room_archetype_tags(marker_archetype)
                    + _room_shape_tags(marker_shape)
                    + _theme_tags(marker_theme)
                    + _encounter_tags(encounter),
                ),
            )
        )
        spawn_records.append(
            {
                "label": anchor_label,
                "kind": role_name,
                "marker": label,
                "room_id": int(room_id),
                "cell": [int(cell[0]), int(cell[1])],
                "location": [float(anchor_loc.x), float(anchor_loc.y), float(anchor_loc.z)],
                "roles": _room_roles_for(progression, room_id),
                "key_links": key_links,
                "encounter": encounter,
                "archetype": marker_archetype,
                "theme": marker_theme,
                "shape": marker_shape,
            }
        )
        counts["spawn_anchor"] += 1

    adjacency = _room_graph_adjacency(layout)
    start_distances = _room_distances_from(adjacency, [layout["start_room_id"]])
    exit_distances = _room_distances_from(adjacency, [layout["exit_room_id"]])

    start_room_id = int(layout["start_room_id"])
    start_cell = _room_center(layout, start_room_id)
    start_target_room_id = int(progression["main_path_room_ids"][1]) if len(progression["main_path_room_ids"]) > 1 else int(layout["exit_room_id"])
    start_target_cell = _room_center(layout, start_target_room_id)
    player_start_yaw = _yaw_from_cell_to_cell(start_cell, start_target_cell)
    player_start_location = _cell_to_location(start_cell, 96.0)
    player_start_label = ACTOR_PREFIX + "PlayerStart_000"
    start_encounter = encounter_profiles.get(start_room_id)
    actors.append(
        _spawn_player_start(
            player_start_label,
            player_start_location,
            _yaw_rotator(player_start_yaw),
            tags=_dungeon_actor_tags(
                seed,
                "player_start",
                cell=start_cell,
                room_id=start_room_id,
                cell_kind="room_center",
                roles=_room_roles_for(progression, start_room_id),
                extra=[
                    "DungeonPlaytestRole=player_start",
                    "DungeonPlaytestIndex={}".format(counts["player_start"]),
                    "DungeonGameplayRole=start",
                    "DungeonRouteKind=main",
                    "DungeonRouteIndex=0",
                    "DungeonMainPathIndex=0",
                    "DungeonRouteDistanceFromStart=0",
                    "DungeonRouteDistanceToExit={}".format(exit_distances.get(start_room_id, -1)),
                    "DungeonFacesRoomId={}".format(start_target_room_id),
                ]
                + _encounter_tags(start_encounter),
            ),
        )
    )
    playtest_records.append(
        {
            "label": player_start_label,
            "kind": "player_start",
            "class": "PlayerStart",
            "playtest_index": int(counts["player_start"]),
            "room_id": start_room_id,
            "cell": [int(start_cell[0]), int(start_cell[1])],
            "location": _location_record(player_start_location),
            "yaw": float(player_start_yaw),
            "faces_room_id": start_target_room_id,
            "route_kind": "main",
            "route_index": 0,
            "main_path_index": 0,
            "distance_from_start": 0,
            "distance_to_exit": int(exit_distances.get(start_room_id, -1)),
            "roles": _room_roles_for(progression, start_room_id),
            "encounter": start_encounter,
        }
    )
    counts["player_start"] += 1

    nav_location, nav_extent = _dungeon_nav_bounds(cells.keys())
    nav_label = ACTOR_PREFIX + "NavBounds_000"
    actors.append(
        _spawn_nav_mesh_bounds(
            nav_label,
            nav_location,
            nav_extent,
            tags=_dungeon_actor_tags(
                seed,
                "nav_bounds",
                extra=[
                    "DungeonPlaytestRole=nav_bounds",
                    "DungeonPlaytestIndex={}".format(counts["nav_bounds"]),
                    "DungeonNavBoundsExtent={:.1f},{:.1f},{:.1f}".format(nav_extent.x, nav_extent.y, nav_extent.z),
                    "DungeonNavBoundsPadding=720.0",
                    "DungeonCoveredCellCount={}".format(len(cells)),
                ],
            ),
        )
    )
    playtest_records.append(
        {
            "label": nav_label,
            "kind": "nav_bounds",
            "class": "NavMeshBoundsVolume",
            "playtest_index": int(counts["nav_bounds"]),
            "location": _location_record(nav_location),
            "extent": _location_record(nav_extent),
            "padding": 720.0,
            "covered_cell_count": int(len(cells)),
        }
    )
    counts["nav_bounds"] += 1

    nav_waypoint_index_by_cell = {}
    for cell in sorted(cells.keys()):
        cell_data = cells[cell]
        cell_kind = cell_data["kind"]
        room_id = int(cell_data["room_id"])
        roles = _room_roles_for(progression, room_id) if room_id >= 0 else []
        main_index = _room_main_path_index(progression, room_id) if room_id >= 0 else -1
        route_kind = "main" if main_index >= 0 else ("side" if room_id >= 0 else "connector")
        route_index = main_index if main_index >= 0 else (side_order.get(room_id, -1) if room_id >= 0 else -1)
        encounter = encounter_profiles.get(room_id) if room_id >= 0 else None
        neighbors = _waypoint_neighbors(cell, cells)
        neighbor_tag = "|".join("{}:{}".format(item["direction"], _cell_text(item["cell"])) for item in neighbors)
        waypoint_loc = _cell_to_location(cell, 68.0)
        waypoint_index = int(counts["nav_waypoint"])
        nav_waypoint_index_by_cell[cell] = waypoint_index
        waypoint_label = ACTOR_PREFIX + "NavWaypoint_{:03d}".format(waypoint_index)
        actors.append(
            _spawn_target_point(
                waypoint_label,
                waypoint_loc,
                tags=_dungeon_actor_tags(
                    seed,
                    "nav_waypoint",
                    cell=cell,
                    room_id=room_id,
                    cell_kind=cell_kind,
                    roles=roles,
                    extra=[
                        "DungeonWaypointIndex={}".format(waypoint_index),
                        "DungeonWaypointKind={}".format(cell_kind),
                        "DungeonWaypointDegree={}".format(len(neighbors)),
                        "DungeonWaypointNeighbors={}".format(neighbor_tag),
                        "DungeonRouteKind={}".format(route_kind),
                        "DungeonRouteIndex={}".format(route_index),
                        "DungeonMainPathIndex={}".format(main_index),
                        "DungeonRouteDistanceFromStart={}".format(start_distances.get(room_id, -1) if room_id >= 0 else -1),
                        "DungeonRouteDistanceToExit={}".format(exit_distances.get(room_id, -1) if room_id >= 0 else -1),
                    ]
                    + _encounter_tags(encounter),
                ),
            )
        )
        nav_waypoint_records.append(
            {
                "label": waypoint_label,
                "index": waypoint_index,
                "kind": cell_kind,
                "room_id": room_id,
                "cell": [int(cell[0]), int(cell[1])],
                "location": _location_record(waypoint_loc),
                "neighbors": neighbors,
                "degree": int(len(neighbors)),
                "route_kind": route_kind,
                "route_index": int(route_index),
                "main_path_index": int(main_index),
                "distance_from_start": int(start_distances.get(room_id, -1) if room_id >= 0 else -1),
                "distance_to_exit": int(exit_distances.get(room_id, -1) if room_id >= 0 else -1),
                "roles": roles,
                "encounter": encounter,
            }
        )
        counts["nav_waypoint"] += 1

    corridor_theme = _corridor_theme()
    for cell in sorted(cells.keys()):
        cell_data = cells[cell]
        if cell_data["kind"] != "corridor":
            continue
        profile = _corridor_detail_profile(cell, cells)
        corridor_index = int(counts["corridor_detail"])
        corridor_loc = _cell_to_location(cell, 0.0)
        corridor_rot = _yaw_rotator(profile["yaw"])
        if profile["detail_kind"] in ("corner", "junction"):
            corridor_detail_scale = _module_scale(scale_x=corridor_scale, scale_y=corridor_scale)
        else:
            corridor_detail_scale = _yaw_width_scale(profile["yaw"], corridor_scale)
        corridor_neighbors = _waypoint_neighbors(cell, cells)
        corridor_neighbor_tag = "|".join(
            "{}:{}".format(item["direction"], _cell_text(item["cell"]))
            for item in corridor_neighbors
        )
        corridor_label = ACTOR_PREFIX + "CorridorDetail_{}_{:03d}".format(
            str(profile["detail_kind"]).title().replace("_", ""),
            corridor_index,
        )
        actors.append(
            _spawn_static_mesh(
                corridor_label,
                meshes[profile["mesh_key"]],
                corridor_loc,
                corridor_rot,
                tags=_dungeon_actor_tags(
                    seed,
                    "corridor_detail",
                    cell=cell,
                    room_id=-1,
                    cell_kind="corridor",
                    roles=[],
                    extra=[
                        "DungeonCorridorDetailKind={}".format(profile["detail_kind"]),
                        "DungeonCorridorDetailIndex={}".format(corridor_index),
                        "DungeonCorridorDetailMeshKey={}".format(profile["mesh_key"]),
                        "DungeonCorridorDetailYaw={:.1f}".format(float(profile["yaw"])),
                        "DungeonCorridorNeighborDirs={}".format("|".join(profile["corridor_dirs"])),
                        "DungeonCorridorRoomDirs={}".format("|".join(profile["room_dirs"])),
                        "DungeonWaypointIndex={}".format(nav_waypoint_index_by_cell.get(cell, -1)),
                        "DungeonWaypointKind=corridor",
                        "DungeonWaypointDegree={}".format(len(corridor_neighbors)),
                        "DungeonWaypointNeighbors={}".format(corridor_neighbor_tag),
                        "DungeonRouteKind=connector",
                        "DungeonRouteIndex=-1",
                        "DungeonMainPathIndex=-1",
                        "DungeonRouteDistanceFromStart=-1",
                        "DungeonRouteDistanceToExit=-1",
                    ]
                    + _theme_tags(corridor_theme),
                ),
                scale=corridor_detail_scale,
            )
        )
        corridor_detail_records.append(
            {
                "label": corridor_label,
                "kind": profile["detail_kind"],
                "mesh_key": profile["mesh_key"],
                "detail_index": corridor_index,
                "cell": [int(cell[0]), int(cell[1])],
                "location": _location_record(corridor_loc),
                "yaw": float(profile["yaw"]),
                "corridor_dirs": list(profile["corridor_dirs"]),
                "room_dirs": list(profile["room_dirs"]),
                "traversable_dirs": list(profile["traversable_dirs"]),
                "waypoint_index": int(nav_waypoint_index_by_cell.get(cell, -1)),
                "waypoint_degree": int(len(corridor_neighbors)),
                "waypoint_neighbors": corridor_neighbors,
                "theme": corridor_theme,
            }
        )
        counts["corridor_detail"] += 1

    route_room_order = list(progression["main_path_room_ids"]) + sorted(progression["side_room_ids"])
    for room_id in route_room_order:
        room_id = int(room_id)
        cell = _room_center(layout, room_id)
        main_index = _room_main_path_index(progression, room_id)
        route_kind = "main" if main_index >= 0 else "side"
        route_index = main_index if main_index >= 0 else side_order.get(room_id, -1)
        route_archetype = room_archetypes.get(room_id)
        route_theme = room_themes.get(room_id)
        route_shape = room_shapes.get(room_id)
        encounter = encounter_profiles.get(room_id)
        route_loc = _cell_to_location(cell, 132.0 if route_kind == "main" else 118.0)
        route_label = ACTOR_PREFIX + "RouteAnchor_{}_{:03d}".format(route_kind.capitalize(), counts["route_anchor"])
        actors.append(
            _spawn_target_point(
                route_label,
                route_loc,
                tags=_dungeon_actor_tags(
                    seed,
                    "route_anchor",
                    cell=cell,
                    room_id=room_id,
                    cell_kind="room_center",
                    roles=_room_roles_for(progression, room_id),
                    extra=[
                        "DungeonRouteKind={}".format(route_kind),
                        "DungeonRouteIndex={}".format(route_index),
                        "DungeonMainPathRoom={}".format(1 if main_index >= 0 else 0),
                        "DungeonMainPathIndex={}".format(main_index),
                        "DungeonRouteDistanceFromStart={}".format(start_distances.get(room_id, -1)),
                        "DungeonRouteDistanceToExit={}".format(exit_distances.get(room_id, -1)),
                    ]
                    + _room_archetype_tags(route_archetype)
                    + _room_shape_tags(route_shape)
                    + _theme_tags(route_theme)
                    + _encounter_tags(encounter),
                ),
            )
        )
        route_records.append(
            {
                "label": route_label,
                "kind": route_kind,
                "route_index": int(route_index),
                "main_path_index": int(main_index),
                "room_id": room_id,
                "cell": [int(cell[0]), int(cell[1])],
                "location": [float(route_loc.x), float(route_loc.y), float(route_loc.z)],
                "distance_from_start": int(start_distances.get(room_id, -1)),
                "distance_to_exit": int(exit_distances.get(room_id, -1)),
                "roles": _room_roles_for(progression, room_id),
                "archetype": route_archetype,
                "theme": route_theme,
                "shape": route_shape,
                "encounter": encounter,
            }
        )
        counts["route_anchor"] += 1

    for room in sorted(layout["rooms"], key=lambda item: int(item["id"])):
        room_id = int(room["id"])
        archetype = room_archetypes.get(room_id)
        theme = room_themes.get(room_id)
        shape = room_shapes.get(room_id)
        encounter = encounter_profiles.get(room_id)
        if not shape:
            continue
        cell = room["center"]
        roles = _room_roles_for(progression, room_id)
        main_index = _room_main_path_index(progression, room_id)
        route_kind = "main" if main_index >= 0 else "side"
        route_index = main_index if main_index >= 0 else side_order.get(room_id, -1)
        variant_index = int(counts["room_variant_detail"])
        variant_kind = shape["variant_kind"]
        variant_mesh_key = shape["variant_mesh_key"]
        variant_loc = _cell_to_location(cell, 0.0)
        variant_rot = _yaw_rotator(shape["variant_yaw"])
        variant_label = ACTOR_PREFIX + "RoomVariant_{}_{:03d}".format(
            str(variant_kind).title().replace("_", ""),
            variant_index,
        )
        actors.append(
            _spawn_static_mesh(
                variant_label,
                meshes[variant_mesh_key],
                variant_loc,
                variant_rot,
                tags=_dungeon_actor_tags(
                    seed,
                    "room_variant_detail",
                    cell=cell,
                    room_id=room_id,
                    cell_kind="room_center",
                    roles=roles,
                    extra=[
                        "DungeonRoomVariantKind={}".format(variant_kind),
                        "DungeonRoomVariantIndex={}".format(variant_index),
                        "DungeonRoomVariantMeshKey={}".format(variant_mesh_key),
                        "DungeonRoomVariantYaw={:.1f}".format(float(shape["variant_yaw"])),
                        "DungeonRouteKind={}".format(route_kind),
                        "DungeonRouteIndex={}".format(route_index),
                        "DungeonMainPathIndex={}".format(main_index),
                        "DungeonRouteDistanceFromStart={}".format(start_distances.get(room_id, -1)),
                        "DungeonRouteDistanceToExit={}".format(exit_distances.get(room_id, -1)),
                    ]
                    + _room_archetype_tags(archetype)
                    + _room_shape_tags(shape)
                    + _theme_tags(theme)
                    + _encounter_tags(encounter),
                ),
            )
        )
        room_variant_records.append(
            {
                "label": variant_label,
                "kind": variant_kind,
                "variant_index": variant_index,
                "mesh_key": variant_mesh_key,
                "room_id": room_id,
                "cell": [int(cell[0]), int(cell[1])],
                "location": _location_record(variant_loc),
                "yaw": float(shape["variant_yaw"]),
                "route_kind": route_kind,
                "route_index": int(route_index),
                "main_path_index": int(main_index),
                "distance_from_start": int(start_distances.get(room_id, -1)),
                "distance_to_exit": int(exit_distances.get(room_id, -1)),
                "roles": roles,
                "archetype": archetype,
                "theme": theme,
                "shape": shape,
                "encounter": encounter,
            }
        )
        counts["room_variant_detail"] += 1

    for room in sorted(layout["rooms"], key=lambda item: int(item["id"])):
        room_id = int(room["id"])
        archetype = room_archetypes.get(room_id)
        if not archetype:
            continue
        theme = room_themes.get(room_id)
        shape = room_shapes.get(room_id)
        cell = room["center"]
        roles = _room_roles_for(progression, room_id)
        encounter = encounter_profiles.get(room_id)
        main_index = _room_main_path_index(progression, room_id)
        route_kind = "main" if main_index >= 0 else "side"
        route_index = main_index if main_index >= 0 else side_order.get(room_id, -1)
        for local_index, (detail_kind, socket, yaw) in enumerate(_detail_anchor_templates(archetype["archetype"])):
            offset = _detail_socket_offset(room, socket)
            detail_loc = _cell_to_location(cell, offset.z)
            detail_loc.x += offset.x
            detail_loc.y += offset.y
            detail_index = int(counts["detail_anchor"])
            detail_mesh_index = int(counts["detail_mesh"])
            detail_mesh_key = _detail_mesh_key(detail_kind)
            detail_rot = _yaw_rotator(yaw)
            detail_label = ACTOR_PREFIX + "DetailAnchor_{}_{:03d}".format(
                archetype["archetype"].title().replace("_", ""),
                detail_index,
            )
            detail_mesh_label = ACTOR_PREFIX + "DetailMesh_{}_{:03d}".format(
                archetype["archetype"].title().replace("_", ""),
                detail_mesh_index,
            )
            actors.append(
                _spawn_target_point(
                    detail_label,
                    detail_loc,
                    detail_rot,
                    tags=_dungeon_actor_tags(
                        seed,
                        "detail_anchor",
                        cell=cell,
                        room_id=room_id,
                        cell_kind="room_center",
                        roles=roles,
                        extra=[
                            "DungeonDetailKind={}".format(detail_kind),
                            "DungeonDetailIndex={}".format(detail_index),
                            "DungeonDetailLocalIndex={}".format(local_index),
                            "DungeonDetailSocket={}".format(socket),
                            "DungeonDetailPlacement=pcg_room_detail",
                            "DungeonDetailMeshKey={}".format(detail_mesh_key),
                            "DungeonDetailMeshLabel={}".format(detail_mesh_label),
                            "DungeonDetailMeshIndex={}".format(detail_mesh_index),
                            "DungeonRouteKind={}".format(route_kind),
                            "DungeonRouteIndex={}".format(route_index),
                            "DungeonMainPathIndex={}".format(main_index),
                            "DungeonRouteDistanceFromStart={}".format(start_distances.get(room_id, -1)),
                            "DungeonRouteDistanceToExit={}".format(exit_distances.get(room_id, -1)),
                        ]
                        + _room_archetype_tags(archetype)
                        + _room_shape_tags(shape)
                        + _theme_tags(theme)
                        + _encounter_tags(encounter),
                    ),
                )
            )
            detail_mesh_loc = _detail_mesh_location(detail_loc)
            actors.append(
                _spawn_static_mesh(
                    detail_mesh_label,
                    meshes[detail_mesh_key],
                    detail_mesh_loc,
                    detail_rot,
                    material=_theme_material(materials, theme),
                    tags=_dungeon_actor_tags(
                        seed,
                        "detail_mesh",
                        cell=cell,
                        room_id=room_id,
                        cell_kind="room_center",
                        roles=roles,
                        extra=[
                            "DungeonDetailKind={}".format(detail_kind),
                            "DungeonDetailIndex={}".format(detail_index),
                            "DungeonDetailLocalIndex={}".format(local_index),
                            "DungeonDetailSocket={}".format(socket),
                            "DungeonDetailPlacement=pcg_room_detail",
                            "DungeonDetailMeshKey={}".format(detail_mesh_key),
                            "DungeonDetailMeshIndex={}".format(detail_mesh_index),
                            "DungeonDetailAnchorLabel={}".format(detail_label),
                            "DungeonRouteKind={}".format(route_kind),
                            "DungeonRouteIndex={}".format(route_index),
                            "DungeonMainPathIndex={}".format(main_index),
                            "DungeonRouteDistanceFromStart={}".format(start_distances.get(room_id, -1)),
                            "DungeonRouteDistanceToExit={}".format(exit_distances.get(room_id, -1)),
                        ]
                        + _room_archetype_tags(archetype)
                        + _room_shape_tags(shape)
                        + _theme_tags(theme)
                        + _encounter_tags(encounter),
                    ),
                )
            )
            detail_records.append(
                {
                    "label": detail_label,
                    "kind": detail_kind,
                    "socket": socket,
                    "detail_index": detail_index,
                    "local_index": int(local_index),
                    "mesh_label": detail_mesh_label,
                    "mesh_key": detail_mesh_key,
                    "mesh_index": detail_mesh_index,
                    "room_id": room_id,
                    "room_archetype": archetype,
                    "theme": theme,
                    "shape": shape,
                    "cell": [int(cell[0]), int(cell[1])],
                    "location": _location_record(detail_loc),
                    "yaw": float(yaw),
                    "route_kind": route_kind,
                    "route_index": int(route_index),
                    "main_path_index": int(main_index),
                    "distance_from_start": int(start_distances.get(room_id, -1)),
                    "distance_to_exit": int(exit_distances.get(room_id, -1)),
                    "roles": roles,
                    "encounter": encounter,
                }
            )
            detail_mesh_records.append(
                {
                    "label": detail_mesh_label,
                    "kind": detail_kind,
                    "socket": socket,
                    "mesh_key": detail_mesh_key,
                    "mesh_index": detail_mesh_index,
                    "detail_anchor_label": detail_label,
                    "detail_index": detail_index,
                    "local_index": int(local_index),
                    "room_id": room_id,
                    "room_archetype": archetype,
                    "theme": theme,
                    "shape": shape,
                    "cell": [int(cell[0]), int(cell[1])],
                    "location": _location_record(detail_mesh_loc),
                    "anchor_location": _location_record(detail_loc),
                    "yaw": float(yaw),
                    "route_kind": route_kind,
                    "route_index": int(route_index),
                    "main_path_index": int(main_index),
                    "distance_from_start": int(start_distances.get(room_id, -1)),
                    "distance_to_exit": int(exit_distances.get(room_id, -1)),
                    "roles": roles,
                    "encounter": encounter,
                }
            )
            counts["detail_anchor"] += 1
            counts["detail_mesh"] += 1

    for room in sorted(layout["rooms"], key=lambda item: int(item["id"])):
        room_id = int(room["id"])
        encounter = encounter_profiles.get(room_id)
        reward_kind = _reward_anchor_kind(encounter)
        if not reward_kind:
            continue
        cell = room["center"]
        reward_archetype = room_archetypes.get(room_id)
        reward_theme = room_themes.get(room_id)
        reward_shape = room_shapes.get(room_id)
        main_index = _room_main_path_index(progression, room_id)
        route_kind = "main" if main_index >= 0 else "side"
        route_index = main_index if main_index >= 0 else side_order.get(room_id, -1)
        interaction_kind = _reward_interaction_kind(reward_kind)
        reward_id = "{}_Reward_{}".format(encounter["encounter_id"], reward_kind)
        offset = _reward_anchor_offset(reward_kind)
        reward_loc = _cell_to_location(cell, 104.0)
        reward_loc.x += offset.x
        reward_loc.y += offset.y
        reward_label = ACTOR_PREFIX + "RewardAnchor_{}_{:03d}".format(
            reward_kind.capitalize(),
            counts["reward_anchor"],
        )
        key_tags = _key_tags_for_room(lock_key_links, room_id) if reward_kind == "key" else []
        key_links = [link for link in lock_key_links if link.get("key_room_id") == room_id] if reward_kind == "key" else []
        actors.append(
            _spawn_target_point(
                reward_label,
                reward_loc,
                tags=_dungeon_actor_tags(
                    seed,
                    "reward_anchor",
                    cell=cell,
                    room_id=room_id,
                    cell_kind="room_center",
                    roles=_room_roles_for(progression, room_id),
                    extra=[
                        "DungeonRewardAnchorKind={}".format(reward_kind),
                        "DungeonRewardId={}".format(reward_id),
                        "DungeonRewardIndex={}".format(counts["reward_anchor"]),
                        "DungeonInteractionKind={}".format(interaction_kind),
                        "DungeonRewardSourceEncounterId={}".format(encounter["encounter_id"]),
                        "DungeonGameplayRole={}".format(reward_kind),
                        "DungeonRouteKind={}".format(route_kind),
                        "DungeonRouteIndex={}".format(route_index),
                        "DungeonMainPathIndex={}".format(main_index),
                        "DungeonRouteDistanceFromStart={}".format(start_distances.get(room_id, -1)),
                        "DungeonRouteDistanceToExit={}".format(exit_distances.get(room_id, -1)),
                    ]
                    + key_tags
                    + _room_archetype_tags(reward_archetype)
                    + _room_shape_tags(reward_shape)
                    + _theme_tags(reward_theme)
                    + _encounter_tags(encounter),
                ),
            )
        )
        reward_records.append(
            {
                "label": reward_label,
                "kind": reward_kind,
                "reward_id": reward_id,
                "reward_index": int(counts["reward_anchor"]),
                "interaction": interaction_kind,
                "encounter_id": encounter["encounter_id"],
                "room_id": room_id,
                "cell": [int(cell[0]), int(cell[1])],
                "location": [float(reward_loc.x), float(reward_loc.y), float(reward_loc.z)],
                "route_kind": route_kind,
                "route_index": int(route_index),
                "main_path_index": int(main_index),
                "distance_from_start": int(start_distances.get(room_id, -1)),
                "distance_to_exit": int(exit_distances.get(room_id, -1)),
                "roles": _room_roles_for(progression, room_id),
                "key_links": key_links,
                "encounter": encounter,
                "archetype": reward_archetype,
                "theme": reward_theme,
                "shape": reward_shape,
            }
        )
        counts["reward_anchor"] += 1

    for room in sorted(layout["rooms"], key=lambda item: int(item["id"])):
        room_id = int(room["id"])
        encounter = encounter_profiles.get(room_id)
        if not encounter:
            continue
        slot_count = int(encounter.get("spawn_budget", 0))
        if slot_count <= 0:
            continue
        cell = room["center"]
        spawn_archetype = room_archetypes.get(room_id)
        spawn_theme = room_themes.get(room_id)
        spawn_shape = room_shapes.get(room_id)
        main_index = _room_main_path_index(progression, room_id)
        route_kind = "main" if main_index >= 0 else "side"
        route_index = main_index if main_index >= 0 else side_order.get(room_id, -1)
        spawn_kind = _encounter_spawn_kind(encounter)
        for slot_index in range(slot_count):
            offset = _encounter_spawn_offset(room, slot_index)
            slot_loc = _cell_to_location(cell, 108.0)
            slot_loc.x += offset.x
            slot_loc.y += offset.y
            yaw = 0.0
            if abs(offset.x) > 0.1 or abs(offset.y) > 0.1:
                yaw = math.degrees(math.atan2(-offset.y, -offset.x))
            slot_label = ACTOR_PREFIX + "EncounterSpawn_{}_{:03d}".format(
                spawn_kind.capitalize(),
                counts["encounter_spawn"],
            )
            actors.append(
                _spawn_target_point(
                    slot_label,
                    slot_loc,
                    _yaw_rotator(yaw),
                    tags=_dungeon_actor_tags(
                        seed,
                        "encounter_spawn",
                        cell=cell,
                        room_id=room_id,
                        cell_kind="room_center",
                        roles=_room_roles_for(progression, room_id),
                        extra=[
                            "DungeonEncounterSpawnKind={}".format(spawn_kind),
                            "DungeonEncounterSlotIndex={}".format(slot_index),
                            "DungeonEncounterSlotCount={}".format(slot_count),
                            "DungeonEncounterSpawnIndex={}".format(counts["encounter_spawn"]),
                        "DungeonGameplayRole={}".format(spawn_kind),
                        "DungeonRouteKind={}".format(route_kind),
                        "DungeonRouteIndex={}".format(route_index),
                            "DungeonMainPathIndex={}".format(main_index),
                        ]
                        + _room_archetype_tags(spawn_archetype)
                        + _room_shape_tags(spawn_shape)
                        + _theme_tags(spawn_theme)
                        + _encounter_tags(encounter),
                    ),
                )
            )
            encounter_spawn_records.append(
                {
                    "label": slot_label,
                    "kind": spawn_kind,
                    "encounter_id": encounter["encounter_id"],
                    "slot_index": int(slot_index),
                    "slot_count": int(slot_count),
                    "global_index": int(counts["encounter_spawn"]),
                    "room_id": room_id,
                    "cell": [int(cell[0]), int(cell[1])],
                    "location": [float(slot_loc.x), float(slot_loc.y), float(slot_loc.z)],
                    "yaw": float(yaw),
                    "route_kind": route_kind,
                    "route_index": int(route_index),
                    "main_path_index": int(main_index),
                    "roles": _room_roles_for(progression, room_id),
                    "archetype": spawn_archetype,
                    "theme": spawn_theme,
                    "shape": spawn_shape,
                    "encounter": encounter,
                }
            )
            counts["encounter_spawn"] += 1

    for room in sorted(layout["rooms"], key=lambda item: int(item["id"])):
        room_id = int(room["id"])
        cell = room["center"]
        theme = room_themes.get(room_id)
        archetype = room_archetypes.get(room_id)
        shape = room_shapes.get(room_id)
        encounter = encounter_profiles.get(room_id)
        profile = _light_profile_for_theme(theme)
        main_index = _room_main_path_index(progression, room_id)
        route_kind = "main" if main_index >= 0 else "side"
        route_index = main_index if main_index >= 0 else side_order.get(room_id, -1)
        light_loc = _cell_to_location(cell, float(profile["height"]))
        light_label = ACTOR_PREFIX + "ThemeLight_{}_{:03d}".format(
            str(theme["theme_name"]).title().replace("_", "") if theme else "Ambient",
            counts["theme_light"],
        )
        light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, light_loc, _actor_rotator())
        if light:
            light.set_actor_label(light_label, mark_dirty=True)
            _apply_actor_tags(
                light,
                _dungeon_actor_tags(
                    seed,
                    "theme_light",
                    cell=cell,
                    room_id=room_id,
                    cell_kind="room_center",
                    roles=_room_roles_for(progression, room_id),
                    extra=[
                        "DungeonLightKind=theme_room",
                        "DungeonLightProfile={}".format(profile["profile"]),
                        "DungeonLightIndex={}".format(counts["theme_light"]),
                        "DungeonLightIntensity={:.1f}".format(float(profile["intensity"])),
                        "DungeonLightRadius={:.1f}".format(float(profile["radius"])),
                        "DungeonRouteKind={}".format(route_kind),
                        "DungeonRouteIndex={}".format(route_index),
                        "DungeonMainPathIndex={}".format(main_index),
                        "DungeonRouteDistanceFromStart={}".format(start_distances.get(room_id, -1)),
                        "DungeonRouteDistanceToExit={}".format(exit_distances.get(room_id, -1)),
                    ]
                    + _room_archetype_tags(archetype)
                    + _room_shape_tags(shape)
                    + _theme_tags(theme)
                    + _encounter_tags(encounter),
                ),
            )
            component = light.get_component_by_class(unreal.PointLightComponent)
            if component:
                component.set_editor_property("intensity", float(profile["intensity"]))
                component.set_editor_property("attenuation_radius", float(profile["radius"]))
                component.set_editor_property("light_color", _light_color(profile))
                try:
                    component.set_editor_property("cast_shadows", False)
                except Exception:
                    pass
            actors.append(light)
            theme_light_records.append(
                {
                    "label": light_label,
                    "kind": "theme_room",
                    "light_index": int(counts["theme_light"]),
                    "profile": profile["profile"],
                    "intensity": float(profile["intensity"]),
                    "radius": float(profile["radius"]),
                    "color": [int(value) for value in profile["color"]],
                    "room_id": room_id,
                    "cell": [int(cell[0]), int(cell[1])],
                    "location": _location_record(light_loc),
                    "route_kind": route_kind,
                    "route_index": int(route_index),
                    "main_path_index": int(main_index),
                    "distance_from_start": int(start_distances.get(room_id, -1)),
                    "distance_to_exit": int(exit_distances.get(room_id, -1)),
                    "roles": _room_roles_for(progression, room_id),
                    "archetype": archetype,
                    "theme": theme,
                    "shape": shape,
                    "encounter": encounter,
                }
            )
            counts["theme_light"] += 1

    for room in layout["rooms"][::2]:
        loc = _cell_to_location(room["center"], 220)
        light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, loc, _actor_rotator())
        if light:
            light.set_actor_label(ACTOR_PREFIX + "PointLight_{:03d}".format(counts["light"]), mark_dirty=True)
            _apply_actor_tags(
                light,
                _dungeon_actor_tags(
                    seed,
                    "light",
                    cell=room["center"],
                    room_id=room["id"],
                    cell_kind="room_center",
                    roles=_room_roles_for(progression, room["id"]),
                    extra=[
                        "DungeonLightKind=room",
                        "DungeonLightIntensity={:.1f}".format(REVIEW_ROOM_POINT_LIGHT_INTENSITY),
                        "DungeonLightRadius={:.1f}".format(REVIEW_ROOM_POINT_LIGHT_RADIUS),
                    ],
                ),
            )
            component = light.get_component_by_class(unreal.PointLightComponent)
            if component:
                component.set_editor_property("intensity", REVIEW_ROOM_POINT_LIGHT_INTENSITY)
                component.set_editor_property("attenuation_radius", REVIEW_ROOM_POINT_LIGHT_RADIUS)
                component.set_editor_property("light_color", unreal.Color(255, 188, 112, 255))
            actors.append(light)
            counts["light"] += 1

    directional = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0, 0, 3600),
        _actor_rotator(pitch=-58.0, yaw=35.0),
    )
    if directional:
        directional.set_actor_label(ACTOR_PREFIX + "ReviewDirectionalLight", mark_dirty=True)
        _apply_actor_tags(
            directional,
            _dungeon_actor_tags(
                seed,
                "light",
                extra=[
                    "DungeonLightKind=review_directional",
                    "DungeonReviewLightIntensity={:.2f}".format(REVIEW_DIRECTIONAL_LIGHT_INTENSITY),
                ],
            ),
        )
        component = directional.get_component_by_class(unreal.DirectionalLightComponent)
        if component:
            component.set_editor_property("intensity", REVIEW_DIRECTIONAL_LIGHT_INTENSITY)
            component.set_editor_property("light_color", unreal.Color(*REVIEW_DIRECTIONAL_LIGHT_COLOR))
        actors.append(directional)
        counts["light"] += 1

    sky_light = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyLight,
        unreal.Vector(0, 0, 800),
        _actor_rotator(),
    )
    if sky_light:
        sky_light.set_actor_label(ACTOR_PREFIX + "ReviewSkyLight", mark_dirty=True)
        _apply_actor_tags(
            sky_light,
            _dungeon_actor_tags(
                seed,
                "light",
                extra=[
                    "DungeonLightKind=review_sky",
                    "DungeonReviewSkyIntensity={:.2f}".format(REVIEW_SKY_LIGHT_INTENSITY),
                ],
            ),
        )
        component = sky_light.get_component_by_class(unreal.SkyLightComponent)
        if component:
            component.set_editor_property("intensity", REVIEW_SKY_LIGHT_INTENSITY)
        actors.append(sky_light)
        counts["light"] += 1

    post_process = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PostProcessVolume,
        unreal.Vector(0, 0, 0),
        _actor_rotator(),
    )
    if post_process:
        post_process.set_actor_label(ACTOR_PREFIX + "ReviewExposureVolume", mark_dirty=True)
        _apply_actor_tags(
            post_process,
            _dungeon_actor_tags(
                seed,
                "review_postprocess",
                extra=[
                    "DungeonReviewExposure=manual",
                    "DungeonReviewExposureBias={:.2f}".format(REVIEW_EXPOSURE_BIAS),
                    "DungeonReviewExposureMinBrightness={:.2f}".format(REVIEW_EXPOSURE_MIN_BRIGHTNESS),
                    "DungeonReviewExposureMaxBrightness={:.2f}".format(REVIEW_EXPOSURE_MAX_BRIGHTNESS),
                    "DungeonReviewBloomIntensity={:.2f}".format(REVIEW_BLOOM_INTENSITY),
                    "DungeonReviewGlobalGain={:.2f}".format(REVIEW_GLOBAL_GAIN),
                    "DungeonReviewMidtoneGain={:.2f}".format(REVIEW_MIDTONE_GAIN),
                    "DungeonReviewHighlightGain={:.2f}".format(REVIEW_HIGHLIGHT_GAIN),
                    "DungeonReviewShadowGain={:.2f}".format(REVIEW_SHADOW_GAIN),
                    "DungeonReviewShadowGamma={:.2f}".format(REVIEW_SHADOW_GAMMA),
                    "DungeonReviewShadowContrast={:.2f}".format(REVIEW_SHADOW_CONTRAST),
                ],
            ),
        )
        post_process.set_editor_property("enabled", True)
        post_process.set_editor_property("unbound", True)
        post_process.set_editor_property("priority", 1000.0)
        post_process.set_editor_property("blend_weight", 1.0)
        settings = post_process.get_editor_property("settings")
        settings.set_editor_property("override_auto_exposure_method", True)
        settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        settings.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
        settings.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
        settings.set_editor_property("override_auto_exposure_bias", True)
        settings.set_editor_property("auto_exposure_bias", REVIEW_EXPOSURE_BIAS)
        settings.set_editor_property("override_auto_exposure_min_brightness", True)
        settings.set_editor_property("auto_exposure_min_brightness", REVIEW_EXPOSURE_MIN_BRIGHTNESS)
        settings.set_editor_property("override_auto_exposure_max_brightness", True)
        settings.set_editor_property("auto_exposure_max_brightness", REVIEW_EXPOSURE_MAX_BRIGHTNESS)
        settings.set_editor_property("override_bloom_intensity", True)
        settings.set_editor_property("bloom_intensity", REVIEW_BLOOM_INTENSITY)
        settings.set_editor_property("override_color_gain", True)
        settings.set_editor_property(
            "color_gain",
            unreal.Vector4(REVIEW_GLOBAL_GAIN, REVIEW_GLOBAL_GAIN, REVIEW_GLOBAL_GAIN, 1.0),
        )
        settings.set_editor_property("override_color_gain_midtones", True)
        settings.set_editor_property(
            "color_gain_midtones",
            unreal.Vector4(REVIEW_MIDTONE_GAIN, REVIEW_MIDTONE_GAIN, REVIEW_MIDTONE_GAIN, 1.0),
        )
        settings.set_editor_property("override_color_gain_highlights", True)
        settings.set_editor_property(
            "color_gain_highlights",
            unreal.Vector4(REVIEW_HIGHLIGHT_GAIN, REVIEW_HIGHLIGHT_GAIN, REVIEW_HIGHLIGHT_GAIN, 1.0),
        )
        settings.set_editor_property("override_color_gain_shadows", True)
        settings.set_editor_property(
            "color_gain_shadows",
            unreal.Vector4(REVIEW_SHADOW_GAIN, REVIEW_SHADOW_GAIN, REVIEW_SHADOW_GAIN, 1.0),
        )
        settings.set_editor_property("override_color_gamma_shadows", True)
        settings.set_editor_property(
            "color_gamma_shadows",
            unreal.Vector4(REVIEW_SHADOW_GAMMA, REVIEW_SHADOW_GAMMA, REVIEW_SHADOW_GAMMA, 1.0),
        )
        settings.set_editor_property("override_color_contrast_shadows", True)
        settings.set_editor_property(
            "color_contrast_shadows",
            unreal.Vector4(REVIEW_SHADOW_CONTRAST, REVIEW_SHADOW_CONTRAST, REVIEW_SHADOW_CONTRAST, 1.0),
        )
        post_process.set_editor_property("settings", settings)
        actors.append(post_process)
        counts["review_postprocess"] += 1

    connectivity = validate_connectivity(cells)
    start = _room_center(layout, layout["start_room_id"])
    exit_cell = _room_center(layout, layout["exit_room_id"])
    start_exit_grid_distance = abs(start[0] - exit_cell[0]) + abs(start[1] - exit_cell[1])
    expected_encounter_spawn_count = sum(
        int(profile.get("spawn_budget", 0))
        for profile in encounter_profiles.values()
    )
    expected_reward_anchor_count = sum(
        1 for profile in encounter_profiles.values()
        if _reward_anchor_kind(profile)
    )
    archetype_counts = {}
    expected_detail_anchor_count = 0
    expected_detail_mesh_count = 0
    theme_counts = _theme_counts(room_themes)
    expected_theme_light_count = len(room_themes)
    expected_connector_detail_count = len(door_records)
    expected_corridor_detail_count = sum(1 for data in cells.values() if data["kind"] == "corridor")
    expected_room_variant_count = len(room_shapes)
    expected_ceiling_count = (
        sum(1 for index, _cell in enumerate(sorted(cells.keys())) if index % effective_ceiling_stride == 0)
        if effective_ceiling_stride > 0
        else 0
    )
    expected_pcg_spawn_point_count = _expected_static_mesh_spawn_point_count(counts)
    for archetype in room_archetypes.values():
        archetype_name = archetype["archetype"]
        archetype_counts[archetype_name] = archetype_counts.get(archetype_name, 0) + 1
        template_count = len(_detail_anchor_templates(archetype_name))
        expected_detail_anchor_count += template_count
        expected_detail_mesh_count += template_count
    runtime_config = {
        "seed": seed,
        "room_count": room_count,
        "ceiling_stride": ceiling_stride,
        "effective_ceiling_stride": effective_ceiling_stride,
        "chest_count": chest_count,
        "enemy_count": enemy_count,
        "key_count": key_count,
        "shop_count": shop_count,
        "locked_door_count": locked_door_count,
        "boss_enabled": boss_enabled,
        "branch_chance_percent": branch_chance_percent,
        "max_loop_edges": max_loop_edges,
        "grid_cell_size": grid_cell_size,
        "corridor_width": corridor_width,
        "grid_scale": float(grid_scale),
        "corridor_width_scale": float(corridor_scale),
        "base_module_tile_size": float(TILE),
        "generation_metrics": dict(generation_metrics),
        "use_ceiling": use_ceiling,
        "use_theme_materials": use_theme_materials,
        "preview_mode": preview_mode,
        "parameter_application_status": {
            "seed": "applied",
            "room_count": "applied",
            "branch_chance_percent": "applied_to_loop_edges",
            "max_loop_edges": "applied_to_loop_edges",
            "use_ceiling": "applied",
            "use_theme_materials": "applied",
            "grid_cell_size": "applied_to_world_spacing_and_static_mesh_xy_scale",
            "corridor_width": "applied_to_corridor_door_connector_xy_scale",
            "preview_mode": "metadata_only_review_policy",
        },
    }
    navigation_setup_report = configure_validation_navigation()
    pcg_spawner_contract = build_pcg_spawner_contract(actors)
    pcg_graph_handoff = build_pcg_graph_handoff(pcg_spawner_contract)
    native_point_source_contract = build_native_point_source_contract(pcg_spawner_contract, pcg_graph_handoff)
    gameplay_export = write_gameplay_exports(
        layout,
        progression,
        encounter_profiles,
        room_archetypes,
        room_themes,
        room_shapes,
        lock_key_links,
        runtime_config,
        marker_specs,
        volume_records,
        door_records,
        connector_detail_records,
        corridor_detail_records,
        room_variant_records,
        spawn_records,
        route_records,
        encounter_spawn_records,
        reward_records,
        theme_light_records,
        playtest_records,
        nav_waypoint_records,
        detail_records,
        detail_mesh_records,
        pcg_spawner_contract,
        pcg_graph_handoff,
        native_point_source_contract,
        counts,
        connectivity,
    )
    report = {
        "source": source,
        "level_path": LEVEL_PATH,
        "root": ROOT,
        "config": dict(
            runtime_config,
            **{
            "source_actor_label": config.get("source_actor_label"),
            "source_actor_tags": config.get("source_actor_tags", []),
            },
        ),
        "seed": seed,
        "removed_before_spawn": removed,
        "room_count": len(layout["rooms"]),
        "edge_count": len(layout["edges"]),
        "cell_count": len(cells),
        "door_count": counts["door"],
        "locked_door_count": len(progression["locked_door_specs"]),
        "locked_door_spawn_count": counts["seal"],
        "lock_key_link_count": len(lock_key_links),
        "encounter_spawn_slot_count": expected_encounter_spawn_count,
        "reward_anchor_count": expected_reward_anchor_count,
        "playtest_actor_count": counts["player_start"] + counts["nav_bounds"],
        "navigation_waypoint_count": counts["nav_waypoint"],
        "room_archetype_count": len(room_archetypes),
        "room_archetype_counts": archetype_counts,
        "room_theme_count": len(room_themes),
        "room_theme_counts": theme_counts,
        "room_shape_count": len(room_shapes),
        "room_shape_counts": _room_shape_counts(room_shapes),
        "theme_light_count": expected_theme_light_count,
        "review_postprocess_count": counts["review_postprocess"],
        "connector_detail_count": expected_connector_detail_count,
        "corridor_detail_count": expected_corridor_detail_count,
        "room_variant_detail_count": expected_room_variant_count,
        "ceiling_actor_count": counts["ceiling"],
        "expected_ceiling_actor_count": expected_ceiling_count,
        "pcg_spawn_point_count": expected_pcg_spawn_point_count,
        "pcg_spawner_group_count": int(pcg_spawner_contract.get("group_count", 0)),
        "pcg_spawner_material_variant_group_count": int(pcg_spawner_contract.get("material_variant_group_count", 0)),
        "pcg_graph_handoff_stream_count": int(pcg_graph_handoff.get("validation", {}).get("stream_count", 0)),
        "pcg_graph_handoff_mesh_only_spawner_count": int(pcg_graph_handoff.get("promotion_targets", {}).get("mesh_only_spawner_count", 0)),
        "pcg_graph_handoff_material_safe_spawner_count": int(pcg_graph_handoff.get("promotion_targets", {}).get("material_safe_spawner_count", 0)),
        "native_point_source_point_count": int(native_point_source_contract.get("validation", {}).get("point_count", 0)),
        "native_point_source_group_count": int(native_point_source_contract.get("validation", {}).get("group_count", 0)),
        "native_point_source_pass": bool(native_point_source_contract.get("pass")),
        "detail_anchor_count": expected_detail_anchor_count,
        "detail_mesh_count": expected_detail_mesh_count,
        "navigation_collision": navigation_collision_report,
        "navigation_setup": navigation_setup_report,
        "module_actor_counts": counts,
        "actor_count": len(actors),
        "progression": progression,
        "gameplay_export": gameplay_export,
        "connectivity": connectivity,
        "start_room_id": layout["start_room_id"],
        "exit_room_id": layout["exit_room_id"],
        "start_exit_grid_distance": start_exit_grid_distance,
        "pass": bool(
            connectivity["connected"]
            and progression["pass"]
            and counts["door"] > 0
            and counts["wall"] > 0
            and counts["seal"] == len(progression["locked_door_specs"])
            and len(lock_key_links) == len(progression["locked_door_specs"])
            and sum(1 for link in lock_key_links if link.get("key_room_id") is None) == 0
            and counts["encounter_spawn"] == expected_encounter_spawn_count
            and counts["reward_anchor"] == expected_reward_anchor_count
            and counts["player_start"] == 1
            and counts["nav_bounds"] == 1
            and counts["nav_waypoint"] == len(cells)
            and len(room_archetypes) == len(layout["rooms"])
            and len(room_themes) == len(layout["rooms"])
            and len(room_shapes) == len(layout["rooms"])
            and counts["theme_light"] == expected_theme_light_count
            and counts["review_postprocess"] == 1
            and counts["connector_detail"] == expected_connector_detail_count
            and counts["corridor_detail"] == expected_corridor_detail_count
            and counts["room_variant_detail"] == expected_room_variant_count
            and counts["ceiling"] == expected_ceiling_count
            and pcg_spawner_contract.get("pass")
            and pcg_graph_handoff.get("pass")
            and native_point_source_contract.get("pass")
            and int(pcg_spawner_contract.get("point_count", 0)) == expected_pcg_spawn_point_count
            and int(native_point_source_contract.get("validation", {}).get("point_count", 0)) == expected_pcg_spawn_point_count
            and counts["detail_anchor"] == expected_detail_anchor_count
            and counts["detail_mesh"] == expected_detail_mesh_count
            and len(actors) > 0
        ),
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("CubelessDungeonPCG spawn report: " + json.dumps(report, ensure_ascii=False))
    return report


def create_or_update_validation_level():
    ensure_dir(MAP_DIR)
    current_world = unreal.EditorLevelLibrary.get_editor_world()
    current_path = current_world.get_path_name() if current_world else None
    if current_path and current_path.startswith(LEVEL_PATH + "."):
        opened = True
    elif unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        opened = bool(unreal.EditorLevelLibrary.load_level(LEVEL_PATH))
    else:
        opened = bool(unreal.EditorLevelLibrary.new_level(LEVEL_PATH))
    if not opened:
        raise RuntimeError("Failed to open/create validation level: " + LEVEL_PATH)
    return {"level_path": LEVEL_PATH, "opened": opened}


def _find_actor_by_label(label):
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_actor_label() == label:
                return actor
        except Exception:
            pass
    return None


def _call_pcg_component_method(component, method_name, arg_variants=None):
    if arg_variants is None:
        arg_variants = [(), (True,), (False,)]
    method = getattr(component, method_name, None)
    if not method:
        return {"ok": False, "method": method_name, "error": "method unavailable"}
    attempts = []
    for args in arg_variants:
        try:
            result = method(*args)
            return {
                "ok": True,
                "method": method_name,
                "args": list(args),
                "result": str(result),
            }
        except Exception as exc:
            attempts.append({"args": list(args), "error": str(exc)})
    return {"ok": False, "method": method_name, "attempts": attempts}


def _pcg_generated_output_summary(component):
    summary = {
        "available": False,
        "tagged_data_count": 0,
        "data_class_counts": {},
        "tag_samples": [],
        "error": None,
    }
    try:
        collection = component.get_generated_graph_output()
        tagged_data = list(collection.get_editor_property("tagged_data"))
        summary["available"] = True
        summary["tagged_data_count"] = len(tagged_data)
        for item in tagged_data:
            data = _safe_editor_property(item, "data", None)
            if data:
                try:
                    class_name = data.get_class().get_name()
                except Exception:
                    class_name = type(data).__name__
            else:
                class_name = "<missing>"
            summary["data_class_counts"][class_name] = summary["data_class_counts"].get(class_name, 0) + 1
            if len(summary["tag_samples"]) < 10:
                try:
                    tags = [str(tag) for tag in list(_safe_editor_property(item, "tags", []))]
                except Exception:
                    tags = []
                summary["tag_samples"].append({"data_class": class_name, "tags": tags[:10]})
    except Exception as exc:
        summary["error"] = str(exc)
    return summary


def _actor_static_mesh_component_summary(actor):
    summary = {
        "component_count": 0,
        "instance_count_total": 0,
        "class_counts": {},
        "mesh_counts": {},
        "samples": [],
        "error": None,
    }
    if not actor:
        return summary
    try:
        components = list(actor.get_components_by_class(unreal.StaticMeshComponent))
        summary["component_count"] = len(components)
        for component in components:
            class_name = component.get_class().get_name()
            summary["class_counts"][class_name] = summary["class_counts"].get(class_name, 0) + 1
            mesh = _safe_editor_property(component, "static_mesh", None)
            mesh_path = _object_path(mesh) if mesh else None
            if mesh_path:
                summary["mesh_counts"][mesh_path] = summary["mesh_counts"].get(mesh_path, 0) + 1
            instance_count = 0
            get_instance_count = getattr(component, "get_instance_count", None)
            if get_instance_count:
                try:
                    instance_count = int(get_instance_count())
                except Exception:
                    instance_count = 0
            summary["instance_count_total"] += instance_count
            if len(summary["samples"]) < 10:
                summary["samples"].append(
                    {
                        "component": component.get_name(),
                        "class": class_name,
                        "mesh": mesh_path,
                        "instance_count": instance_count,
                    }
                )
    except Exception as exc:
        summary["error"] = str(exc)
    return summary


def create_or_update_native_integration_test_actor(smoke_generate=False, cleanup_after=True):
    ensure_dirs()
    create_or_update_validation_level()
    graph = unreal.load_object(None, NATIVE_INTEGRATION_GRAPH_PATH + "." + NATIVE_INTEGRATION_GRAPH_NAME)
    existing = _find_actor_by_label(PCG_NATIVE_INTEGRATION_TEST_LABEL)
    existing_cleanup = None
    if existing:
        existing_component = existing.get_component_by_class(unreal.PCGComponent)
        if existing_component:
            existing_cleanup = _call_pcg_component_method(existing_component, "cleanup")
        try:
            unreal.EditorLevelLibrary.destroy_actor(existing)
        except Exception:
            pass

    pcg_volume_class = getattr(unreal, "PCGVolume", None)
    actor = None
    if pcg_volume_class:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            pcg_volume_class,
            unreal.Vector(0, 0, 0),
            _actor_rotator(),
        )
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    setup = {
        "graph_loaded": bool(graph),
        "existing_cleanup": existing_cleanup,
        "pcg_volume_class_available": bool(pcg_volume_class),
        "actor_created": bool(actor),
        "component_found": bool(component),
    }
    if actor:
        actor.set_actor_label(PCG_NATIVE_INTEGRATION_TEST_LABEL, mark_dirty=True)
        actor.tags = [
            unreal.Name("DungeonNativeIntegrationTest"),
            unreal.Name("DungeonGraph=NativeIntegration"),
            unreal.Name("DungeonOutputPolicy=SmokeGenerateThenCleanup"),
        ]
    if component and graph:
        try:
            component.set_graph(graph)
            setup["set_graph"] = graph.get_path_name()
        except Exception as exc:
            setup["set_graph_error"] = str(exc)
        try:
            component.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
            setup["generation_trigger"] = str(component.get_editor_property("generation_trigger"))
        except Exception as exc:
            setup["generation_trigger_error"] = str(exc)
        try:
            component.set_editor_property("input_type", unreal.PCGComponentInput.ACTOR)
            setup["input_type"] = str(component.get_editor_property("input_type"))
        except Exception as exc:
            setup["input_type_error"] = str(exc)

    cleanup_before = _call_pcg_component_method(component, "cleanup") if component else {"ok": False, "error": "missing component"}
    dirty_generated = _call_pcg_component_method(component, "dirty_generated", arg_variants=[(), (True,)]) if component else {"ok": False, "error": "missing component"}
    generate_result = {"ok": False, "skipped": not smoke_generate}
    output_after_generate = {}
    components_after_generate = {}
    if smoke_generate and component:
        generate_result = _call_pcg_component_method(component, "generate")
        output_after_generate = _pcg_generated_output_summary(component)
        components_after_generate = _actor_static_mesh_component_summary(actor)
    cleanup_after_result = {"ok": None, "skipped": not cleanup_after}
    if cleanup_after and component:
        cleanup_after_result = _call_pcg_component_method(component, "cleanup")
    output_after_cleanup = _pcg_generated_output_summary(component) if component else {}
    components_after_cleanup = _actor_static_mesh_component_summary(actor)

    report = {
        "schema": "cubeless_pcg_dungeon_native_integration_test_v1",
        "level_path": LEVEL_PATH,
        "actor_label": PCG_NATIVE_INTEGRATION_TEST_LABEL,
        "actor_path": actor.get_path_name() if actor else None,
        "graph_path": graph.get_path_name() if graph else NATIVE_INTEGRATION_GRAPH_PATH,
        "smoke_generate_requested": bool(smoke_generate),
        "cleanup_after_requested": bool(cleanup_after),
        "setup": setup,
        "cleanup_before": cleanup_before,
        "dirty_generated": dirty_generated,
        "generate": generate_result,
        "output_after_generate": output_after_generate,
        "components_after_generate": components_after_generate,
        "cleanup_after": cleanup_after_result,
        "output_after_cleanup": output_after_cleanup,
        "components_after_cleanup": components_after_cleanup,
        "residual_static_mesh_component_count": int(components_after_cleanup.get("component_count", 0)),
        "residual_static_mesh_instance_count": int(components_after_cleanup.get("instance_count_total", 0)),
        "async_smoke_policy": (
            "For reliable generation counts, use begin_native_integration_smoke_test(), then after an editor tick use "
            "verify_native_integration_smoke_generation(), then after another tick use verify_native_integration_smoke_cleanup(). "
            "Immediate generate/cleanup calls in one Python execution are only API-call checks."
        ),
        "policy": (
            "NativeIntegration is attached to a separate PCGVolume for smoke testing. "
            "The test calls cleanup before generation and cleanup after generation so native PCG output does not remain mixed with bridge validation actors."
        ),
    }
    report["pass"] = bool(
        graph
        and actor
        and component
        and not setup.get("set_graph_error")
        and cleanup_before.get("ok")
        and (not smoke_generate or generate_result.get("ok"))
        and (not cleanup_after or cleanup_after_result.get("ok"))
        and report["residual_static_mesh_component_count"] == 0
        and report["residual_static_mesh_instance_count"] == 0
    )
    os.makedirs(os.path.dirname(NATIVE_INTEGRATION_TEST_ACTOR_REPORT_PATH), exist_ok=True)
    with open(NATIVE_INTEGRATION_TEST_ACTOR_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log(
        "CubelessDungeonPCG native integration test actor: "
        + json.dumps(
            {
                "pass": report["pass"],
                "actor_created": setup["actor_created"],
                "component_found": setup["component_found"],
                "generate_ok": generate_result.get("ok"),
                "cleanup_after_ok": cleanup_after_result.get("ok"),
                "residual_static_mesh_component_count": report["residual_static_mesh_component_count"],
                "residual_static_mesh_instance_count": report["residual_static_mesh_instance_count"],
            },
            ensure_ascii=False,
        )
    )
    return report


def _native_integration_expected_runtime_counts():
    graph_report = {}
    point_report = {}
    if os.path.exists(NATIVE_INTEGRATION_GRAPH_REPORT_PATH):
        with open(NATIVE_INTEGRATION_GRAPH_REPORT_PATH, "r", encoding="utf-8") as handle:
            graph_report = json.load(handle)
    if os.path.exists(NATIVE_POINT_SOURCE_GRAPH_REPORT_PATH):
        with open(NATIVE_POINT_SOURCE_GRAPH_REPORT_PATH, "r", encoding="utf-8") as handle:
            point_report = json.load(handle)
    return {
        "static_mesh_component_count": int(graph_report.get("static_mesh_spawner_node_count", 0) or 0),
        "static_mesh_instance_count": int(point_report.get("pcg_point_count", 0) or 0),
        "source_graph_report_pass": bool(point_report.get("pass")),
        "integration_graph_report_pass": bool(graph_report.get("pass")),
    }


def _load_native_integration_test_report():
    if os.path.exists(NATIVE_INTEGRATION_TEST_REPORT_PATH):
        with open(NATIVE_INTEGRATION_TEST_REPORT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _write_native_integration_test_report(report):
    os.makedirs(os.path.dirname(NATIVE_INTEGRATION_TEST_REPORT_PATH), exist_ok=True)
    with open(NATIVE_INTEGRATION_TEST_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def begin_native_integration_smoke_test():
    actor_setup = create_or_update_native_integration_test_actor(smoke_generate=False, cleanup_after=True)
    actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_TEST_LABEL)
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    cleanup_before = _call_pcg_component_method(component, "cleanup") if component else {"ok": False, "error": "missing component"}
    generate = _call_pcg_component_method(component, "generate") if component else {"ok": False, "error": "missing component"}
    report = {
        "schema": "cubeless_pcg_dungeon_native_integration_smoke_v1",
        "status": "generation_requested",
        "level_path": LEVEL_PATH,
        "actor_label": PCG_NATIVE_INTEGRATION_TEST_LABEL,
        "actor_setup": actor_setup,
        "expected_runtime_counts": _native_integration_expected_runtime_counts(),
        "cleanup_before_generation": cleanup_before,
        "generate_request": generate,
        "generation_verification": {},
        "cleanup_request": {},
        "cleanup_verification": {},
        "pass": False,
    }
    _write_native_integration_test_report(report)
    unreal.log(
        "CubelessDungeonPCG native integration smoke begin: "
        + json.dumps(
            {
                "actor_setup_pass": actor_setup.get("pass"),
                "generate_request_ok": generate.get("ok"),
                "status": report["status"],
            },
            ensure_ascii=False,
        )
    )
    return report


def verify_native_integration_smoke_generation(request_cleanup=True):
    report = _load_native_integration_test_report()
    actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_TEST_LABEL)
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    expected = _native_integration_expected_runtime_counts()
    component_summary = _actor_static_mesh_component_summary(actor)
    try:
        generated_attr = bool(component.generated) if component else False
    except Exception:
        generated_attr = False
    output_summary = _pcg_generated_output_summary(component) if component else {}
    generation_verification = {
        "actor_found": bool(actor),
        "component_found": bool(component),
        "generated_attr": generated_attr,
        "output_summary": output_summary,
        "component_summary": component_summary,
        "expected_static_mesh_component_count": expected["static_mesh_component_count"],
        "expected_static_mesh_instance_count": expected["static_mesh_instance_count"],
    }
    generation_verification["pass"] = bool(
        actor
        and component
        and generated_attr
        and int(component_summary.get("component_count", 0)) == expected["static_mesh_component_count"]
        and int(component_summary.get("instance_count_total", 0)) == expected["static_mesh_instance_count"]
    )
    cleanup_request = {}
    if request_cleanup and component:
        cleanup_request = _call_pcg_component_method(component, "cleanup")
    report.update(
        {
            "schema": "cubeless_pcg_dungeon_native_integration_smoke_v1",
            "status": "cleanup_requested" if request_cleanup else "generation_verified",
            "level_path": LEVEL_PATH,
            "actor_label": PCG_NATIVE_INTEGRATION_TEST_LABEL,
            "expected_runtime_counts": expected,
            "generation_verification": generation_verification,
            "cleanup_request": cleanup_request,
            "pass": bool(generation_verification["pass"] and not request_cleanup),
        }
    )
    _write_native_integration_test_report(report)
    unreal.log(
        "CubelessDungeonPCG native integration smoke generation: "
        + json.dumps(
            {
                "generation_pass": generation_verification["pass"],
                "component_count": component_summary.get("component_count"),
                "instance_count_total": component_summary.get("instance_count_total"),
                "cleanup_requested": bool(request_cleanup),
                "cleanup_request_ok": cleanup_request.get("ok"),
            },
            ensure_ascii=False,
        )
    )
    return report


def verify_native_integration_smoke_cleanup():
    report = _load_native_integration_test_report()
    actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_TEST_LABEL)
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    component_summary = _actor_static_mesh_component_summary(actor)
    try:
        generated_attr = bool(component.generated) if component else False
    except Exception:
        generated_attr = False
    cleanup_verification = {
        "actor_found": bool(actor),
        "component_found": bool(component),
        "generated_attr": generated_attr,
        "component_summary": component_summary,
        "residual_static_mesh_component_count": int(component_summary.get("component_count", 0)),
        "residual_static_mesh_instance_count": int(component_summary.get("instance_count_total", 0)),
    }
    cleanup_verification["pass"] = bool(
        actor
        and component
        and not generated_attr
        and cleanup_verification["residual_static_mesh_component_count"] == 0
        and cleanup_verification["residual_static_mesh_instance_count"] == 0
    )
    generation_pass = bool(report.get("generation_verification", {}).get("pass"))
    report.update(
        {
            "schema": "cubeless_pcg_dungeon_native_integration_smoke_v1",
            "status": "passed" if generation_pass and cleanup_verification["pass"] else "failed",
            "level_path": LEVEL_PATH,
            "actor_label": PCG_NATIVE_INTEGRATION_TEST_LABEL,
            "cleanup_verification": cleanup_verification,
            "pass": bool(generation_pass and cleanup_verification["pass"]),
        }
    )
    _write_native_integration_test_report(report)
    unreal.log(
        "CubelessDungeonPCG native integration smoke cleanup: "
        + json.dumps(
            {
                "cleanup_pass": cleanup_verification["pass"],
                "overall_pass": report["pass"],
                "residual_static_mesh_component_count": cleanup_verification["residual_static_mesh_component_count"],
                "residual_static_mesh_instance_count": cleanup_verification["residual_static_mesh_instance_count"],
            },
            ensure_ascii=False,
        )
    )
    return report


def _destroy_actor_by_label(label):
    actor = _find_actor_by_label(label)
    if not actor:
        return {"found": False, "destroyed": False}
    component = actor.get_component_by_class(unreal.PCGComponent)
    cleanup = _call_pcg_component_method(component, "cleanup") if component else {"ok": False, "error": "missing component"}
    try:
        unreal.EditorLevelLibrary.destroy_actor(actor)
        destroyed = True
        error = None
    except Exception as exc:
        destroyed = False
        error = str(exc)
    return {"found": True, "destroyed": destroyed, "cleanup": cleanup, "error": error}


def _write_native_integration_output_report(report):
    os.makedirs(os.path.dirname(NATIVE_INTEGRATION_OUTPUT_REPORT_PATH), exist_ok=True)
    with open(NATIVE_INTEGRATION_OUTPUT_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _load_native_integration_output_report():
    if os.path.exists(NATIVE_INTEGRATION_OUTPUT_REPORT_PATH):
        with open(NATIVE_INTEGRATION_OUTPUT_REPORT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def begin_native_integration_output(keep_existing=False):
    ensure_dirs()
    create_or_update_validation_level()
    graph = unreal.load_object(None, NATIVE_INTEGRATION_GRAPH_PATH + "." + NATIVE_INTEGRATION_GRAPH_NAME)
    destroy_existing = {"skipped": bool(keep_existing)}
    if not keep_existing:
        destroy_existing = _destroy_actor_by_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL)
    pcg_volume_class = getattr(unreal, "PCGVolume", None)
    actor = None
    if pcg_volume_class:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            pcg_volume_class,
            unreal.Vector(0.0, 0.0, 0.0),
            _actor_rotator(),
        )
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    setup = {
        "graph_loaded": bool(graph),
        "pcg_volume_class_available": bool(pcg_volume_class),
        "actor_created": bool(actor),
        "component_found": bool(component),
        "destroy_existing": destroy_existing,
        "output_location": [0.0, 0.0, 0.0],
    }
    if actor:
        actor.set_actor_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL, mark_dirty=True)
        actor.tags = [
            unreal.Name("DungeonNativeIntegrationOutput"),
            unreal.Name("DungeonGraph=NativeIntegration"),
            unreal.Name("DungeonOutputPolicy=ProductionCandidateKeepGenerated"),
        ]
    if component and graph:
        try:
            component.set_graph(graph)
            setup["set_graph"] = graph.get_path_name()
        except Exception as exc:
            setup["set_graph_error"] = str(exc)
        try:
            component.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
            setup["generation_trigger"] = str(component.get_editor_property("generation_trigger"))
        except Exception as exc:
            setup["generation_trigger_error"] = str(exc)
        try:
            component.set_editor_property("input_type", unreal.PCGComponentInput.ACTOR)
            setup["input_type"] = str(component.get_editor_property("input_type"))
        except Exception as exc:
            setup["input_type_error"] = str(exc)

    cleanup_before = _call_pcg_component_method(component, "cleanup") if component else {"ok": False, "error": "missing component"}
    generate = _call_pcg_component_method(component, "generate") if component else {"ok": False, "error": "missing component"}
    report = {
        "schema": "cubeless_pcg_dungeon_native_integration_output_v1",
        "status": "generation_requested",
        "level_path": LEVEL_PATH,
        "actor_label": PCG_NATIVE_INTEGRATION_OUTPUT_LABEL,
        "actor_path": actor.get_path_name() if actor else None,
        "graph_path": graph.get_path_name() if graph else NATIVE_INTEGRATION_GRAPH_PATH,
        "graph_role": "production_output_candidate",
        "setup": setup,
        "expected_runtime_counts": _native_integration_expected_runtime_counts(),
        "cleanup_before_generation": cleanup_before,
        "generate_request": generate,
        "generation_verification": {},
        "cleanup_policy": "Native output is intentionally kept generated until cleanup_native_integration_output() is called.",
        "bridge_policy": "Bridge StaticMeshActor output remains in the level as the current data/contract source; native output overlaps it at the origin.",
        "pass": False,
    }
    _write_native_integration_output_report(report)
    unreal.log(
        "CubelessDungeonPCG native integration output begin: "
        + json.dumps(
            {
                "actor_created": setup["actor_created"],
                "generate_request_ok": generate.get("ok"),
                "graph_loaded": setup["graph_loaded"],
            },
            ensure_ascii=False,
        )
    )
    return report


def verify_native_integration_output_generation():
    report = _load_native_integration_output_report()
    actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL)
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    expected = _native_integration_expected_runtime_counts()
    component_summary = _actor_static_mesh_component_summary(actor)
    bounds = _bounds_for_actor(actor)
    try:
        generated_attr = bool(component.generated) if component else False
    except Exception:
        generated_attr = False
    generation_verification = {
        "actor_found": bool(actor),
        "component_found": bool(component),
        "generated_attr": generated_attr,
        "component_summary": component_summary,
        "bounds": bounds,
        "expected_static_mesh_component_count": expected["static_mesh_component_count"],
        "expected_static_mesh_instance_count": expected["static_mesh_instance_count"],
    }
    generation_verification["pass"] = bool(
        actor
        and component
        and generated_attr
        and int(component_summary.get("component_count", 0)) == expected["static_mesh_component_count"]
        and int(component_summary.get("instance_count_total", 0)) == expected["static_mesh_instance_count"]
    )
    report.update(
        {
            "schema": "cubeless_pcg_dungeon_native_integration_output_v1",
            "status": "generated" if generation_verification["pass"] else "generation_failed",
            "level_path": LEVEL_PATH,
            "actor_label": PCG_NATIVE_INTEGRATION_OUTPUT_LABEL,
            "expected_runtime_counts": expected,
            "generation_verification": generation_verification,
            "pass": bool(generation_verification["pass"]),
        }
    )
    _write_native_integration_output_report(report)
    unreal.log(
        "CubelessDungeonPCG native integration output generation: "
        + json.dumps(
            {
                "pass": report["pass"],
                "component_count": component_summary.get("component_count"),
                "instance_count_total": component_summary.get("instance_count_total"),
            },
            ensure_ascii=False,
        )
    )
    return report


def cleanup_native_integration_output(destroy_actor=False):
    actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL)
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    cleanup = _call_pcg_component_method(component, "cleanup") if component else {"ok": False, "error": "missing component"}
    destroyed = False
    destroy_error = None
    if destroy_actor and actor:
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            destroyed = True
        except Exception as exc:
            destroy_error = str(exc)
    report = _load_native_integration_output_report()
    report.update(
        {
            "status": "cleanup_requested",
            "cleanup_request": cleanup,
            "destroy_actor_requested": bool(destroy_actor),
            "destroyed": destroyed,
            "destroy_error": destroy_error,
            "pass": False,
        }
    )
    _write_native_integration_output_report(report)
    return report


def _write_native_output_only_review_report(report):
    os.makedirs(os.path.dirname(NATIVE_INTEGRATION_OUTPUT_REVIEW_REPORT_PATH), exist_ok=True)
    with open(NATIVE_INTEGRATION_OUTPUT_REVIEW_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _load_native_output_only_review_report():
    if os.path.exists(NATIVE_INTEGRATION_OUTPUT_REVIEW_REPORT_PATH):
        with open(NATIVE_INTEGRATION_OUTPUT_REVIEW_REPORT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _bridge_validation_static_mesh_actors():
    actors = []
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            label = actor.get_actor_label()
        except Exception:
            continue
        if not label.startswith(ACTOR_PREFIX):
            continue
        if not actor.get_component_by_class(unreal.StaticMeshComponent):
            continue
        actors.append(actor)
    return actors


def _component_visibility(component):
    try:
        is_visible = getattr(component, "is_visible", None)
        if is_visible:
            return bool(is_visible())
    except Exception:
        pass
    try:
        return bool(component.get_editor_property("visible"))
    except Exception:
        return None


def _set_component_visibility(component, visible):
    set_visibility = getattr(component, "set_visibility", None)
    if set_visibility:
        set_visibility(bool(visible), True)
        return "set_visibility"
    component.set_editor_property("visible", bool(visible))
    return "visible_property"


def _bridge_validation_static_mesh_actor_summary():
    actors = _bridge_validation_static_mesh_actors()
    summary = {
        "actor_count": len(actors),
        "static_mesh_component_count": 0,
        "visible_static_mesh_component_count": 0,
        "hidden_static_mesh_component_count": 0,
        "unknown_visibility_component_count": 0,
        "sample_labels": [],
    }
    for actor in actors:
        if len(summary["sample_labels"]) < 12:
            try:
                summary["sample_labels"].append(actor.get_actor_label())
            except Exception:
                pass
        for component in list(actor.get_components_by_class(unreal.StaticMeshComponent)):
            summary["static_mesh_component_count"] += 1
            visible = _component_visibility(component)
            if visible is True:
                summary["visible_static_mesh_component_count"] += 1
            elif visible is False:
                summary["hidden_static_mesh_component_count"] += 1
            else:
                summary["unknown_visibility_component_count"] += 1
    return summary


def _set_bridge_validation_static_mesh_visibility(visible):
    operations = {
        "target_visible": bool(visible),
        "actor_count": 0,
        "component_count": 0,
        "actor_hidden_in_game_updates": 0,
        "actor_editor_hidden_updates": 0,
        "component_visibility_updates": 0,
        "errors": [],
        "sample_labels": [],
    }
    for actor in _bridge_validation_static_mesh_actors():
        operations["actor_count"] += 1
        try:
            if len(operations["sample_labels"]) < 12:
                operations["sample_labels"].append(actor.get_actor_label())
        except Exception:
            pass
        try:
            actor.set_actor_hidden_in_game(not bool(visible))
            operations["actor_hidden_in_game_updates"] += 1
        except Exception as exc:
            operations["errors"].append({"actor": actor.get_path_name(), "operation": "set_actor_hidden_in_game", "error": str(exc)})
        editor_hidden_method = getattr(actor, "set_is_temporarily_hidden_in_editor", None)
        if editor_hidden_method:
            try:
                editor_hidden_method(not bool(visible))
                operations["actor_editor_hidden_updates"] += 1
            except Exception as exc:
                operations["errors"].append(
                    {"actor": actor.get_path_name(), "operation": "set_is_temporarily_hidden_in_editor", "error": str(exc)}
                )
        for component in list(actor.get_components_by_class(unreal.StaticMeshComponent)):
            operations["component_count"] += 1
            try:
                _set_component_visibility(component, bool(visible))
                operations["component_visibility_updates"] += 1
            except Exception as exc:
                operations["errors"].append(
                    {
                        "actor": actor.get_path_name(),
                        "component": component.get_name(),
                        "operation": "set_component_visibility",
                        "error": str(exc),
                    }
                )
    return operations


def _actor_static_mesh_visibility_summary(actor):
    summary = {
        "actor_found": bool(actor),
        "static_mesh_component_count": 0,
        "visible_static_mesh_component_count": 0,
        "hidden_static_mesh_component_count": 0,
        "unknown_visibility_component_count": 0,
    }
    if not actor:
        return summary
    for component in list(actor.get_components_by_class(unreal.StaticMeshComponent)):
        summary["static_mesh_component_count"] += 1
        visible = _component_visibility(component)
        if visible is True:
            summary["visible_static_mesh_component_count"] += 1
        elif visible is False:
            summary["hidden_static_mesh_component_count"] += 1
        else:
            summary["unknown_visibility_component_count"] += 1
    return summary


def _set_actor_static_mesh_visibility(actor, visible):
    operations = {
        "actor_found": bool(actor),
        "target_visible": bool(visible),
        "component_count": 0,
        "actor_hidden_in_game_updated": False,
        "actor_editor_hidden_updated": False,
        "component_visibility_updates": 0,
        "errors": [],
    }
    if not actor:
        return operations
    try:
        actor.set_actor_hidden_in_game(not bool(visible))
        operations["actor_hidden_in_game_updated"] = True
    except Exception as exc:
        operations["errors"].append({"actor": actor.get_path_name(), "operation": "set_actor_hidden_in_game", "error": str(exc)})
    editor_hidden_method = getattr(actor, "set_is_temporarily_hidden_in_editor", None)
    if editor_hidden_method:
        try:
            editor_hidden_method(not bool(visible))
            operations["actor_editor_hidden_updated"] = True
        except Exception as exc:
            operations["errors"].append(
                {"actor": actor.get_path_name(), "operation": "set_is_temporarily_hidden_in_editor", "error": str(exc)}
            )
    for component in list(actor.get_components_by_class(unreal.StaticMeshComponent)):
        operations["component_count"] += 1
        try:
            _set_component_visibility(component, bool(visible))
            operations["component_visibility_updates"] += 1
        except Exception as exc:
            operations["errors"].append(
                {
                    "actor": actor.get_path_name(),
                    "component": component.get_name(),
                    "operation": "set_component_visibility",
                    "error": str(exc),
                }
            )
    return operations


def _bridge_validation_review_light_actors():
    actors = []
    light_component_classes = (
        unreal.PointLightComponent,
        unreal.SpotLightComponent,
        unreal.RectLightComponent,
    )
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            label = actor.get_actor_label()
        except Exception:
            continue
        if not label.startswith(ACTOR_PREFIX):
            continue
        if "ReviewDirectionalLight" in label or "ReviewSkyLight" in label:
            continue
        if any(actor.get_component_by_class(component_class) for component_class in light_component_classes):
            actors.append(actor)
    return actors


def _light_actor_visibility_summary():
    actors = _bridge_validation_review_light_actors()
    summary = {
        "actor_count": len(actors),
        "light_component_count": 0,
        "visible_light_component_count": 0,
        "hidden_light_component_count": 0,
        "unknown_visibility_component_count": 0,
        "sample_labels": [],
    }
    light_component_classes = (
        unreal.PointLightComponent,
        unreal.SpotLightComponent,
        unreal.RectLightComponent,
    )
    for actor in actors:
        try:
            if len(summary["sample_labels"]) < 12:
                summary["sample_labels"].append(actor.get_actor_label())
        except Exception:
            pass
        for component_class in light_component_classes:
            for component in list(actor.get_components_by_class(component_class)):
                summary["light_component_count"] += 1
                visible = _component_visibility(component)
                if visible is True:
                    summary["visible_light_component_count"] += 1
                elif visible is False:
                    summary["hidden_light_component_count"] += 1
                else:
                    summary["unknown_visibility_component_count"] += 1
    return summary


def _set_bridge_validation_review_light_visibility(visible):
    operations = {
        "target_visible": bool(visible),
        "actor_count": 0,
        "component_count": 0,
        "actor_hidden_in_game_updates": 0,
        "actor_editor_hidden_updates": 0,
        "component_visibility_updates": 0,
        "errors": [],
        "sample_labels": [],
    }
    light_component_classes = (
        unreal.PointLightComponent,
        unreal.SpotLightComponent,
        unreal.RectLightComponent,
    )
    for actor in _bridge_validation_review_light_actors():
        operations["actor_count"] += 1
        try:
            if len(operations["sample_labels"]) < 12:
                operations["sample_labels"].append(actor.get_actor_label())
        except Exception:
            pass
        try:
            actor.set_actor_hidden_in_game(not bool(visible))
            operations["actor_hidden_in_game_updates"] += 1
        except Exception as exc:
            operations["errors"].append({"actor": actor.get_path_name(), "operation": "set_actor_hidden_in_game", "error": str(exc)})
        editor_hidden_method = getattr(actor, "set_is_temporarily_hidden_in_editor", None)
        if editor_hidden_method:
            try:
                editor_hidden_method(not bool(visible))
                operations["actor_editor_hidden_updates"] += 1
            except Exception as exc:
                operations["errors"].append(
                    {"actor": actor.get_path_name(), "operation": "set_is_temporarily_hidden_in_editor", "error": str(exc)}
                )
        for component_class in light_component_classes:
            for component in list(actor.get_components_by_class(component_class)):
                operations["component_count"] += 1
                try:
                    _set_component_visibility(component, bool(visible))
                    operations["component_visibility_updates"] += 1
                except Exception as exc:
                    operations["errors"].append(
                        {
                            "actor": actor.get_path_name(),
                            "component": component.get_name(),
                            "operation": "set_light_component_visibility",
                            "error": str(exc),
                        }
                    )
    return operations


def set_native_output_only_review_mode(enabled=True):
    ensure_dirs()
    create_or_update_validation_level()
    previous_report = _load_native_output_only_review_report()
    output_report = verify_native_integration_output_generation()
    expected = _native_integration_expected_runtime_counts()
    preview_actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_PREVIEW_LABEL)
    before = _bridge_validation_static_mesh_actor_summary()
    preview_before = _actor_static_mesh_visibility_summary(preview_actor)
    light_before = _light_actor_visibility_summary()
    operations = _set_bridge_validation_static_mesh_visibility(visible=not bool(enabled))
    preview_operations = _set_actor_static_mesh_visibility(preview_actor, visible=not bool(enabled))
    light_operations = _set_bridge_validation_review_light_visibility(visible=not bool(enabled))
    after = _bridge_validation_static_mesh_actor_summary()
    preview_after = _actor_static_mesh_visibility_summary(preview_actor)
    light_after = _light_actor_visibility_summary()
    expected_bridge_actor_count = int(expected.get("static_mesh_instance_count", 0) or 0)
    report = {
        "schema": "cubeless_pcg_dungeon_native_output_only_review_v1",
        "status": "native_output_only_enabled" if enabled else "bridge_validation_output_restored",
        "level_path": LEVEL_PATH,
        "native_output_actor_label": PCG_NATIVE_INTEGRATION_OUTPUT_LABEL,
        "bridge_actor_label": PCG_BRIDGE_LABEL,
        "enabled": bool(enabled),
        "policy": (
            "This review mode hides bridge-generated MCP_Dungeon_MVP_* StaticMeshActor validation output and the offset native preview PCG actor "
            "so the kept production NativeOutput actor can be reviewed alone. "
            "It does not delete the bridge actor, native output actor, preview actor, gameplay validation actors, or native PCG generated components."
        ),
        "expected_bridge_static_mesh_actor_count": expected_bridge_actor_count,
        "native_output_generation": output_report.get("generation_verification", {}),
        "bridge_static_mesh_before": before,
        "visibility_operations": operations,
        "bridge_static_mesh_after": after,
        "preview_actor_label": PCG_NATIVE_INTEGRATION_PREVIEW_LABEL,
        "preview_before": preview_before,
        "preview_visibility_operations": preview_operations,
        "preview_after": preview_after,
        "bridge_review_lights_before": light_before,
        "bridge_review_light_visibility_operations": light_operations,
        "bridge_review_lights_after": light_after,
        "screenshot": previous_report.get("screenshot", {}) if bool(enabled) else {},
    }
    errors = operations.get("errors", []) + preview_operations.get("errors", []) + light_operations.get("errors", [])
    hidden_ok = bool(enabled) and after.get("visible_static_mesh_component_count") == 0
    restored_ok = (not bool(enabled)) and after.get("visible_static_mesh_component_count") == after.get("static_mesh_component_count")
    preview_hidden_ok = bool(enabled) and preview_after.get("visible_static_mesh_component_count") == 0
    preview_restored_ok = (not bool(enabled)) and (
        preview_after.get("static_mesh_component_count") == 0
        or preview_after.get("visible_static_mesh_component_count") == preview_after.get("static_mesh_component_count")
    )
    light_hidden_ok = bool(enabled) and light_after.get("visible_light_component_count") == 0
    light_restored_ok = (not bool(enabled)) and (
        light_after.get("light_component_count") == 0
        or light_after.get("visible_light_component_count") == light_after.get("light_component_count")
    )
    report["pass"] = bool(
        output_report.get("pass")
        and not errors
        and after.get("actor_count") == before.get("actor_count")
        and (expected_bridge_actor_count <= 0 or after.get("actor_count") == expected_bridge_actor_count)
        and (hidden_ok or restored_ok)
        and (preview_hidden_ok or preview_restored_ok)
        and (light_hidden_ok or light_restored_ok)
    )
    _write_native_output_only_review_report(report)
    unreal.log(
        "CubelessDungeonPCG native output-only review mode: "
        + json.dumps(
            {
                "pass": report["pass"],
                "enabled": report["enabled"],
                "bridge_actor_count": after.get("actor_count"),
                "visible_components": after.get("visible_static_mesh_component_count"),
                "hidden_components": after.get("hidden_static_mesh_component_count"),
                "preview_visible_components": preview_after.get("visible_static_mesh_component_count"),
                "preview_hidden_components": preview_after.get("hidden_static_mesh_component_count"),
                "review_light_visible_components": light_after.get("visible_light_component_count"),
                "review_light_hidden_components": light_after.get("hidden_light_component_count"),
                "native_output_pass": output_report.get("pass"),
            },
            ensure_ascii=False,
        )
    )
    return report


def restore_native_output_only_review_mode():
    return set_native_output_only_review_mode(enabled=False)


def verify_native_output_only_review_restore_roundtrip():
    previous = _load_native_output_only_review_report()
    previous_screenshot = previous.get("screenshot", {})
    expected = _native_integration_expected_runtime_counts()
    expected_bridge_component_count = int(expected.get("static_mesh_instance_count", 0) or 0)
    expected_preview_component_count = int(expected.get("static_mesh_component_count", 0) or 0)
    restored = set_native_output_only_review_mode(enabled=False)
    re_enabled = set_native_output_only_review_mode(enabled=True)
    roundtrip = {
        "restore_pass": bool(restored.get("pass")),
        "restore_status": restored.get("status"),
        "restore_bridge_visible_static_mesh_component_count": restored.get("bridge_static_mesh_after", {}).get(
            "visible_static_mesh_component_count"
        ),
        "restore_bridge_hidden_static_mesh_component_count": restored.get("bridge_static_mesh_after", {}).get(
            "hidden_static_mesh_component_count"
        ),
        "restore_preview_visible_static_mesh_component_count": restored.get("preview_after", {}).get(
            "visible_static_mesh_component_count"
        ),
        "restore_preview_hidden_static_mesh_component_count": restored.get("preview_after", {}).get(
            "hidden_static_mesh_component_count"
        ),
        "re_enable_pass": bool(re_enabled.get("pass")),
        "re_enable_status": re_enabled.get("status"),
        "re_enable_bridge_visible_static_mesh_component_count": re_enabled.get("bridge_static_mesh_after", {}).get(
            "visible_static_mesh_component_count"
        ),
        "re_enable_bridge_hidden_static_mesh_component_count": re_enabled.get("bridge_static_mesh_after", {}).get(
            "hidden_static_mesh_component_count"
        ),
        "re_enable_preview_visible_static_mesh_component_count": re_enabled.get("preview_after", {}).get(
            "visible_static_mesh_component_count"
        ),
        "re_enable_preview_hidden_static_mesh_component_count": re_enabled.get("preview_after", {}).get(
            "hidden_static_mesh_component_count"
        ),
        "expected_bridge_static_mesh_component_count": expected_bridge_component_count,
        "expected_preview_static_mesh_component_count": expected_preview_component_count,
    }
    roundtrip["pass"] = bool(
        roundtrip["restore_pass"]
        and roundtrip["re_enable_pass"]
        and roundtrip["restore_bridge_visible_static_mesh_component_count"] == expected_bridge_component_count
        and roundtrip["restore_preview_visible_static_mesh_component_count"] == expected_preview_component_count
        and roundtrip["re_enable_bridge_visible_static_mesh_component_count"] == 0
        and roundtrip["re_enable_preview_visible_static_mesh_component_count"] == 0
    )
    report = _load_native_output_only_review_report()
    report["screenshot"] = previous_screenshot
    report["restore_roundtrip"] = roundtrip
    report["pass"] = bool(report.get("pass") and roundtrip["pass"])
    _write_native_output_only_review_report(report)
    unreal.log("CubelessDungeonPCG native output-only restore roundtrip: " + json.dumps(roundtrip, ensure_ascii=False))
    return report


def setup_native_output_only_review_camera(camera_height=14500.0, y_backoff=2600.0):
    output_bounds = _bounds_for_actor(_find_actor_by_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL))
    if not output_bounds:
        return {"success": False, "output_bounds": output_bounds, "error": "native output bounds unavailable"}
    center = [
        (output_bounds["min"][0] + output_bounds["max"][0]) * 0.5,
        (output_bounds["min"][1] + output_bounds["max"][1]) * 0.5,
        (output_bounds["min"][2] + output_bounds["max"][2]) * 0.5,
    ]
    span = [
        output_bounds["max"][0] - output_bounds["min"][0],
        output_bounds["max"][1] - output_bounds["min"][1],
        output_bounds["max"][2] - output_bounds["min"][2],
    ]
    location = unreal.Vector(float(center[0]), float(center[1] - y_backoff), float(camera_height))
    rotation = _actor_rotator(pitch=-86.5, yaw=90.0)
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(location, rotation)
        success = True
        error = None
    except Exception as exc:
        success = False
        error = str(exc)
    camera = {
        "success": success,
        "error": error,
        "location": [float(location.x), float(location.y), float(location.z)],
        "rotation": [-86.5, 90.0, 0.0],
        "output_bounds": output_bounds,
        "output_span": span,
        "output_center": center,
        "camera_height": float(camera_height),
        "y_backoff": float(y_backoff),
    }
    report = _load_native_output_only_review_report()
    report.setdefault("screenshot", {})["camera"] = camera
    _write_native_output_only_review_report(report)
    return camera


def setup_pcg_generation_oblique_review_camera(
    camera_height=4200.0,
    x_backoff=5200.0,
    y_backoff=6900.0,
    pitch=-32.0,
    yaw=48.0,
):
    output_bounds = _bounds_for_actor(_find_actor_by_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL))
    if not output_bounds:
        return {"success": False, "output_bounds": output_bounds, "error": "native output bounds unavailable"}
    center = [
        (output_bounds["min"][0] + output_bounds["max"][0]) * 0.5,
        (output_bounds["min"][1] + output_bounds["max"][1]) * 0.5,
        (output_bounds["min"][2] + output_bounds["max"][2]) * 0.5,
    ]
    span = [
        output_bounds["max"][0] - output_bounds["min"][0],
        output_bounds["max"][1] - output_bounds["min"][1],
        output_bounds["max"][2] - output_bounds["min"][2],
    ]
    location = unreal.Vector(float(center[0] - x_backoff), float(center[1] - y_backoff), float(camera_height))
    rotation = _actor_rotator(pitch=float(pitch), yaw=float(yaw))
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(location, rotation)
        success = True
        error = None
    except Exception as exc:
        success = False
        error = str(exc)
    camera = {
        "success": success,
        "error": error,
        "location": [float(location.x), float(location.y), float(location.z)],
        "rotation": [float(pitch), float(yaw), 0.0],
        "output_bounds": output_bounds,
        "output_span": span,
        "output_center": center,
        "camera_height": float(camera_height),
        "x_backoff": float(x_backoff),
        "y_backoff": float(y_backoff),
    }
    report = _load_native_output_only_review_report()
    report.setdefault("screenshot", {})["pcg_generation_oblique_camera"] = camera
    _write_native_output_only_review_report(report)
    return camera


def record_native_output_only_review_screenshot(screenshot_report_path=None):
    if screenshot_report_path is None:
        screenshot_report_path = os.path.join(
            unreal.Paths.project_saved_dir(),
            "MCP_Dungeon",
            "CubelessDungeonMVP_NativeOutputOnly_ScreenshotQA.json",
        )
    screenshot = {
        "screenshot_report_path": screenshot_report_path,
        "report_exists": os.path.exists(screenshot_report_path),
    }
    if os.path.exists(screenshot_report_path):
        try:
            with open(screenshot_report_path, "r", encoding="utf-8") as handle:
                screenshot_report = json.load(handle)
            captures = screenshot_report.get("captures", [])
            active = captures[0] if captures else {}
            screenshot.update(
                {
                    "qa_pass": bool(screenshot_report.get("qa_pass")),
                    "capture_qa_pass": bool(screenshot_report.get("capture_qa_pass")),
                    "screenshot_path": active.get("filepath"),
                    "file_size": active.get("file_size"),
                    "sha256": active.get("sha256"),
                    "capture_source": active.get("capture_source"),
                }
            )
        except Exception as exc:
            screenshot["error"] = str(exc)
    report = _load_native_output_only_review_report()
    report.setdefault("screenshot", {})["active_viewport"] = screenshot
    report["pass"] = bool(report.get("pass") and screenshot.get("capture_qa_pass"))
    _write_native_output_only_review_report(report)
    return report


def _write_native_primary_refresh_report(report):
    os.makedirs(os.path.dirname(NATIVE_PRIMARY_REFRESH_REPORT_PATH), exist_ok=True)
    with open(NATIVE_PRIMARY_REFRESH_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _load_native_primary_refresh_report():
    if os.path.exists(NATIVE_PRIMARY_REFRESH_REPORT_PATH):
        with open(NATIVE_PRIMARY_REFRESH_REPORT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _native_primary_refresh_checks_pass(checks):
    if not checks:
        return False
    for key, value in checks.items():
        if key == "dirty_after_count":
            if _coerce_int(value, -1) != 0:
                return False
            continue
        if not bool(value):
            return False
    return True


def _dirty_package_names():
    names = []
    try:
        packages = list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
        packages += list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    except Exception:
        packages = []
    for package in packages:
        try:
            names.append(package.get_name())
        except Exception:
            names.append(str(package))
    return sorted(set(names))


def _save_dirty_packages_summary():
    before = _dirty_package_names()
    try:
        save_result = bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
        error = None
    except Exception as exc:
        save_result = False
        error = str(exc)
    after = _dirty_package_names()
    return {
        "dirty_before_count": len(before),
        "dirty_before": before,
        "save_dirty_packages_result": save_result,
        "error": error,
        "dirty_after_count": len(after),
        "dirty_after": after,
    }


def _write_pcg_generation_refresh_report(report):
    os.makedirs(os.path.dirname(PCG_GENERATION_REFRESH_REPORT_PATH), exist_ok=True)
    with open(PCG_GENERATION_REFRESH_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _load_pcg_generation_refresh_report():
    if os.path.exists(PCG_GENERATION_REFRESH_REPORT_PATH):
        with open(PCG_GENERATION_REFRESH_REPORT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def begin_pcg_generation_refresh_from_bridge(keep_existing_output=False):
    ensure_dirs()
    level_report = create_or_update_validation_level()
    bridge_graph_report = create_or_update_pcg_bridge_graph()
    bridge_graph = unreal.load_object(None, GRAPH_PATH + "." + GRAPH_NAME)
    bridge_actor = _find_pcg_bridge_actor()
    bridge_actor_report = {"found": bool(bridge_actor), "created": False}
    if not bridge_actor and bridge_graph:
        bridge_actor_report = spawn_or_update_pcg_bridge_actor(bridge_graph)
        bridge_actor = _find_pcg_bridge_actor()
    elif bridge_actor and bridge_graph:
        component = bridge_actor.get_component_by_class(unreal.PCGComponent)
        if component:
            try:
                component.set_graph(bridge_graph)
                bridge_actor_report["set_graph"] = bridge_graph.get_path_name()
            except Exception as exc:
                bridge_actor_report["set_graph_error"] = str(exc)
        try:
            bridge_actor_report["actor_label"] = bridge_actor.get_actor_label()
            bridge_actor_report["config_tags"] = [str(tag) for tag in list(bridge_actor.tags)]
        except Exception:
            pass

    ensure_tags_report = ensure_pcg_bridge_parameter_tags(save_dirty_packages=False)
    authoring_surface_report = validate_authoring_surface(bridge_actor)
    preset_smoke_report = validate_authoring_preset_apply_restore_smoke(save_dirty_packages=False)
    config = _parse_dungeon_config_from_actor(bridge_actor)
    scale_report = validate_generation_scale_parameters()
    dungeon_report = spawn_validation_dungeon(source="pcg_generation_refresh", config=config)
    seed_suite_report = run_seed_suite(config=config)
    native_point_source_graph_report = create_or_update_native_point_source_graph()
    native_skeleton_graph_report = create_or_update_native_skeleton_graph()
    native_skeleton_audit_report = audit_native_skeleton_graph()
    native_integration_graph_report = create_or_update_native_integration_graph(
        native_point_source_graph_report=native_point_source_graph_report,
    )
    native_integration_audit_report = audit_native_integration_graph()
    output_begin_report = begin_native_integration_output(keep_existing=keep_existing_output)
    report = {
        "schema": "cubeless_pcg_dungeon_generation_refresh_v1",
        "status": "generation_requested",
        "level_path": LEVEL_PATH,
        "refresh_policy": (
            "PCG-generation-only refresh. It reads the bridge tag authoring surface, regenerates the validation dungeon "
            "and point contract, rebuilds native point-source/skeleton/integration graph reports, then requests the "
            "kept NativeOutput PCG generation. Gameplay implementation validation is intentionally excluded."
        ),
        "keep_existing_output": bool(keep_existing_output),
        "level": level_report,
        "bridge_graph": bridge_graph_report,
        "bridge_actor": bridge_actor_report,
        "ensure_tags": ensure_tags_report,
        "authoring_surface": authoring_surface_report,
        "authoring_preset_smoke": preset_smoke_report,
        "generation_parameter_scale": scale_report,
        "config": config,
        "dungeon": dungeon_report,
        "seed_suite": seed_suite_report,
        "native_point_source_graph": native_point_source_graph_report,
        "native_skeleton_graph": native_skeleton_graph_report,
        "native_skeleton_audit": native_skeleton_audit_report,
        "native_integration_graph": native_integration_graph_report,
        "native_integration_audit": native_integration_audit_report,
        "native_output_begin": output_begin_report,
        "native_output_verify": {},
        "structure_audit": {},
        "native_output_only_review": {},
        "native_output_only_camera": {},
        "save_dirty_packages": {},
        "pass": False,
    }
    _write_pcg_generation_refresh_report(report)
    unreal.log(
        "CubelessDungeonPCG PCG generation refresh begin: "
        + json.dumps(
            {
                "dungeon_pass": dungeon_report.get("pass"),
                "authoring_surface_pass": authoring_surface_report.get("pass"),
                "preset_smoke_pass": preset_smoke_report.get("pass"),
                "point_source_graph_pass": native_point_source_graph_report.get("pass"),
                "integration_graph_pass": native_integration_graph_report.get("pass"),
                "output_generate_requested": output_begin_report.get("generate_request", {}).get("ok"),
            },
            ensure_ascii=False,
        )
    )
    return report


def begin_pcg_generation_refresh_with_authoring_preset(
    preset_name="default",
    keep_existing_output=False,
    save_dirty_packages=True,
):
    ensure_dirs()
    preset_apply_report = apply_authoring_preset_to_bridge(
        preset_name=preset_name,
        save_dirty_packages=save_dirty_packages,
    )
    if not preset_apply_report.get("pass"):
        report = {
            "schema": "cubeless_pcg_dungeon_generation_refresh_v1",
            "status": "failed",
            "refresh_policy": (
                "Preset-backed PCG generation refresh. Preset application failed before the bridge validation "
                "dungeon or native output generation was requested."
            ),
            "preset_name": str(preset_name),
            "preset_apply": preset_apply_report,
            "checks": {
                "preset_apply_pass": False,
            },
            "pass": False,
        }
        _write_pcg_generation_refresh_report(report)
        unreal.log(
            "CubelessDungeonPCG preset-backed PCG generation refresh begin failed: "
            + json.dumps(
                {
                    "preset_name": str(preset_name),
                    "available_presets": preset_apply_report.get("available_presets", []),
                },
                ensure_ascii=False,
            )
        )
        return report

    report = begin_pcg_generation_refresh_from_bridge(keep_existing_output=keep_existing_output)
    report["preset_name"] = str(preset_name)
    report["preset_apply"] = preset_apply_report
    report["refresh_policy"] = (
        "Preset-backed PCG-generation-only refresh. It applies the requested bridge authoring preset, "
        "then reads the bridge tag authoring surface, regenerates the validation dungeon and point contract, "
        "rebuilds native point-source/skeleton/integration graph reports, and requests the kept NativeOutput "
        "PCG generation. Gameplay implementation validation is intentionally excluded."
    )
    report["checks"] = dict(report.get("checks", {}), preset_apply_pass=True)
    _write_pcg_generation_refresh_report(report)
    unreal.log(
        "CubelessDungeonPCG preset-backed PCG generation refresh begin: "
        + json.dumps(
            {
                "preset_name": str(preset_name),
                "preset_apply_pass": True,
                "status": report.get("status"),
                "output_generate_requested": report.get("native_output_begin", {}).get("generate_request", {}).get("ok"),
            },
            ensure_ascii=False,
        )
    )
    return report


def verify_pcg_generation_refresh(enable_output_only_review=True, save_dirty_packages=True):
    report = _load_pcg_generation_refresh_report()
    output_verify = verify_native_integration_output_generation()
    structure_audit = audit_pcg_dungeon_structure_and_orientation()
    output_only_review = {}
    review_camera = {}
    if enable_output_only_review and output_verify.get("pass"):
        output_only_review = set_native_output_only_review_mode(True)
        review_camera = setup_native_output_only_review_camera()
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    dirty_after_count = int(save_summary.get("dirty_after_count", 0) or 0)
    checks = {
        "report_loaded": bool(report),
        "preset_apply_pass": bool(report.get("preset_apply", {}).get("pass")) if report.get("preset_apply") else True,
        "dungeon_pass": bool(report.get("dungeon", {}).get("pass")),
        "seed_suite_pass": bool(report.get("seed_suite", {}).get("pass")),
        "authoring_surface_pass": bool(report.get("authoring_surface", {}).get("pass")),
        "authoring_preset_smoke_pass": bool(report.get("authoring_preset_smoke", {}).get("pass")),
        "generation_parameter_scale_pass": bool(report.get("generation_parameter_scale", {}).get("pass")),
        "native_point_source_graph_pass": bool(report.get("native_point_source_graph", {}).get("pass")),
        "native_skeleton_graph_pass": bool(report.get("native_skeleton_graph", {}).get("pass")),
        "native_skeleton_audit_pass": bool(report.get("native_skeleton_audit", {}).get("pass")),
        "native_integration_graph_pass": bool(report.get("native_integration_graph", {}).get("pass")),
        "native_integration_audit_pass": bool(report.get("native_integration_audit", {}).get("pass")),
        "native_output_generation_pass": bool(output_verify.get("pass")),
        "structure_audit_pass": bool(structure_audit.get("pass")),
        "native_output_only_review_pass": bool(output_only_review.get("pass")) if enable_output_only_review else True,
        "native_output_only_camera_success": bool(review_camera.get("success")) if enable_output_only_review else True,
        "save_dirty_packages_pass": bool(save_summary.get("save_dirty_packages_result")) if save_dirty_packages else True,
        "dirty_after_count_zero": dirty_after_count == 0,
    }
    pass_value = bool(all(checks.values()))
    report.update(
        {
            "schema": "cubeless_pcg_dungeon_generation_refresh_v1",
            "status": "passed" if pass_value else "failed",
            "native_output_verify": output_verify,
            "structure_audit": structure_audit,
            "native_output_only_review": output_only_review,
            "native_output_only_camera": review_camera,
            "save_dirty_packages": save_summary,
            "checks": checks,
            "dirty_after_count": dirty_after_count,
            "pass": pass_value,
        }
    )
    _write_pcg_generation_refresh_report(report)
    unreal.log(
        "CubelessDungeonPCG PCG generation refresh verify: "
        + json.dumps(
            {
                "pass": pass_value,
                "failed_checks": [key for key, value in checks.items() if not value],
                "component_count": output_verify.get("generation_verification", {}).get("component_summary", {}).get("component_count"),
                "instance_count": output_verify.get("generation_verification", {}).get("component_summary", {}).get("instance_count_total"),
                "dirty_after_count": dirty_after_count,
            },
            ensure_ascii=False,
        )
    )
    return report


def begin_native_primary_output_refresh(keep_existing_output=False):
    ensure_dirs()
    level_report = create_or_update_validation_level()
    bridge_graph_report = create_or_update_pcg_bridge_graph()
    bridge_graph = unreal.load_object(None, GRAPH_PATH + "." + GRAPH_NAME)
    bridge_actor = _find_pcg_bridge_actor()
    bridge_actor_report = {"found": bool(bridge_actor), "created": False}
    if not bridge_actor and bridge_graph:
        bridge_actor_report = spawn_or_update_pcg_bridge_actor(bridge_graph)
        bridge_actor = _find_pcg_bridge_actor()
    elif bridge_actor and bridge_graph:
        component = bridge_actor.get_component_by_class(unreal.PCGComponent)
        if component:
            try:
                component.set_graph(bridge_graph)
                bridge_actor_report["set_graph"] = bridge_graph.get_path_name()
            except Exception as exc:
                bridge_actor_report["set_graph_error"] = str(exc)
        try:
            bridge_actor_report["actor_label"] = bridge_actor.get_actor_label()
            bridge_actor_report["config_tags"] = [str(tag) for tag in list(bridge_actor.tags)]
        except Exception:
            pass

    config = _parse_dungeon_config_from_actor(bridge_actor)
    dungeon_report = spawn_validation_dungeon(source="native_primary_refresh", config=config)
    native_point_source_graph_report = create_or_update_native_point_source_graph()
    native_skeleton_graph_report = create_or_update_native_skeleton_graph()
    native_skeleton_audit_report = audit_native_skeleton_graph()
    native_integration_graph_report = create_or_update_native_integration_graph(
        native_point_source_graph_report=native_point_source_graph_report,
    )
    native_integration_audit_report = audit_native_integration_graph()
    output_begin_report = begin_native_integration_output(keep_existing=keep_existing_output)
    report = {
        "schema": "cubeless_pcg_dungeon_native_primary_refresh_v1",
        "status": "generation_requested",
        "level_path": LEVEL_PATH,
        "refresh_policy": (
            "Refreshes the bridge validation dungeon and contract, rebuilds native point-source/integration graph reports, "
            "requests production NativeOutput generation, then waits for verify_native_primary_output_refresh() after an editor tick."
        ),
        "keep_existing_output": bool(keep_existing_output),
        "level": level_report,
        "bridge_graph": bridge_graph_report,
        "bridge_actor": bridge_actor_report,
        "config": config,
        "dungeon": dungeon_report,
        "native_point_source_graph": native_point_source_graph_report,
        "native_skeleton_graph": native_skeleton_graph_report,
        "native_skeleton_audit": native_skeleton_audit_report,
        "native_integration_graph": native_integration_graph_report,
        "native_integration_audit": native_integration_audit_report,
        "native_output_begin": output_begin_report,
        "native_output_verify": {},
        "native_output_only_review": {},
        "save_dirty_packages": {},
        "pass": False,
    }
    _write_native_primary_refresh_report(report)
    unreal.log(
        "CubelessDungeonPCG native primary refresh begin: "
        + json.dumps(
            {
                "dungeon_pass": dungeon_report.get("pass"),
                "point_source_graph_pass": native_point_source_graph_report.get("pass"),
                "integration_graph_pass": native_integration_graph_report.get("pass"),
                "integration_audit_pass": native_integration_audit_report.get("pass"),
                "output_generate_requested": output_begin_report.get("generate_request", {}).get("ok"),
            },
            ensure_ascii=False,
        )
    )
    return report


def verify_native_primary_output_refresh(enable_output_only_review=True, save_dirty_packages=True):
    report = _load_native_primary_refresh_report()
    output_verify = verify_native_integration_output_generation()
    output_only_review = {}
    review_camera = {}
    if enable_output_only_review and output_verify.get("pass"):
        output_only_review = set_native_output_only_review_mode(True)
        review_camera = setup_native_output_only_review_camera()
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    checks = {
        "dungeon_pass": bool(report.get("dungeon", {}).get("pass")),
        "native_point_source_graph_pass": bool(report.get("native_point_source_graph", {}).get("pass")),
        "native_skeleton_graph_pass": bool(report.get("native_skeleton_graph", {}).get("pass")),
        "native_skeleton_audit_pass": bool(report.get("native_skeleton_audit", {}).get("pass")),
        "native_integration_graph_pass": bool(report.get("native_integration_graph", {}).get("pass")),
        "native_integration_audit_pass": bool(report.get("native_integration_audit", {}).get("pass")),
        "native_output_generation_pass": bool(output_verify.get("pass")),
        "native_output_only_review_pass": bool(output_only_review.get("pass")) if enable_output_only_review else True,
        "native_output_only_camera_success": bool(review_camera.get("success")) if enable_output_only_review else True,
        "save_dirty_packages_pass": bool(save_summary.get("save_dirty_packages_result")) if save_dirty_packages else True,
        "dirty_after_count": int(save_summary.get("dirty_after_count", 0) or 0),
    }
    pass_value = bool(
        all(value for key, value in checks.items() if key != "dirty_after_count")
        and checks["dirty_after_count"] == 0
    )
    report.update(
        {
            "schema": "cubeless_pcg_dungeon_native_primary_refresh_v1",
            "status": "passed" if pass_value else "failed",
            "native_output_verify": output_verify,
            "native_output_only_review": output_only_review,
            "native_output_only_camera": review_camera,
            "save_dirty_packages": save_summary,
            "checks": checks,
            "pass": pass_value,
        }
    )
    _write_native_primary_refresh_report(report)
    unreal.log("CubelessDungeonPCG native primary refresh verify: " + json.dumps({"pass": pass_value, "checks": checks}, ensure_ascii=False))
    return report


def record_native_primary_refresh_screenshot(screenshot_report_path=None):
    if screenshot_report_path is None:
        screenshot_report_path = os.path.join(
            unreal.Paths.project_saved_dir(),
            "MCP_Dungeon",
            "CubelessDungeonMVP_NativePrimaryRefresh_ScreenshotQA.json",
        )
    screenshot = {
        "screenshot_report_path": screenshot_report_path,
        "report_exists": os.path.exists(screenshot_report_path),
    }
    if os.path.exists(screenshot_report_path):
        try:
            with open(screenshot_report_path, "r", encoding="utf-8") as handle:
                screenshot_report = json.load(handle)
            captures = screenshot_report.get("captures", [])
            active = captures[0] if captures else {}
            screenshot.update(
                {
                    "qa_pass": bool(screenshot_report.get("qa_pass")),
                    "capture_qa_pass": bool(screenshot_report.get("capture_qa_pass")),
                    "screenshot_path": active.get("filepath"),
                    "file_size": active.get("file_size"),
                    "sha256": active.get("sha256"),
                    "capture_source": active.get("capture_source"),
                    "dirty_package_added_count": active.get("dirty_package_added_count"),
                }
            )
        except Exception as exc:
            screenshot["error"] = str(exc)
    report = _load_native_primary_refresh_report()
    checks = dict(report.get("checks", {}))
    checks["screenshot_qa_pass"] = bool(screenshot.get("qa_pass") and screenshot.get("capture_qa_pass"))
    report["screenshot"] = {"active_viewport": screenshot}
    report["checks"] = checks
    report["pass"] = _native_primary_refresh_checks_pass(checks)
    _write_native_primary_refresh_report(report)
    return report


def record_native_primary_refresh_smoke_result(smoke_report_path=None):
    if smoke_report_path is None:
        smoke_report_path = NATIVE_INTEGRATION_TEST_REPORT_PATH
    smoke = {
        "smoke_report_path": smoke_report_path,
        "report_exists": os.path.exists(smoke_report_path),
    }
    if os.path.exists(smoke_report_path):
        try:
            with open(smoke_report_path, "r", encoding="utf-8") as handle:
                smoke_report = json.load(handle)
            generation = smoke_report.get("generation_verification", {})
            cleanup = smoke_report.get("cleanup_verification", {})
            component_summary = generation.get("component_summary", {})
            smoke.update(
                {
                    "schema": smoke_report.get("schema"),
                    "status": smoke_report.get("status"),
                    "pass": bool(smoke_report.get("pass")),
                    "generation_pass": bool(generation.get("pass")),
                    "generated_static_mesh_component_count": component_summary.get("component_count"),
                    "generated_static_mesh_instance_count": component_summary.get("instance_count_total"),
                    "cleanup_pass": bool(cleanup.get("pass")),
                    "cleanup_residual_static_mesh_component_count": cleanup.get("residual_static_mesh_component_count"),
                    "cleanup_residual_static_mesh_instance_count": cleanup.get("residual_static_mesh_instance_count"),
                }
            )
        except Exception as exc:
            smoke["error"] = str(exc)
    report = _load_native_primary_refresh_report()
    checks = dict(report.get("checks", {}))
    checks["smoke_test_pass"] = bool(
        smoke.get("pass")
        and smoke.get("generation_pass")
        and smoke.get("cleanup_pass")
        and _coerce_int(smoke.get("cleanup_residual_static_mesh_component_count"), -1) == 0
        and _coerce_int(smoke.get("cleanup_residual_static_mesh_instance_count"), -1) == 0
    )
    report["smoke_test"] = smoke
    report["checks"] = checks
    report["pass"] = _native_primary_refresh_checks_pass(checks)
    _write_native_primary_refresh_report(report)
    return report


def record_native_primary_refresh_artifacts(screenshot_report_path=None, smoke_report_path=None):
    report = record_native_primary_refresh_screenshot(screenshot_report_path=screenshot_report_path)
    report = record_native_primary_refresh_smoke_result(smoke_report_path=smoke_report_path)
    unreal.log(
        "CubelessDungeonPCG native primary refresh artifacts: "
        + json.dumps(
            {
                "pass": report.get("pass"),
                "screenshot_qa_pass": report.get("checks", {}).get("screenshot_qa_pass"),
                "smoke_test_pass": report.get("checks", {}).get("smoke_test_pass"),
            },
            ensure_ascii=False,
        )
    )
    return report


def _read_json_report(path):
    report = {
        "path": path,
        "exists": os.path.exists(path),
        "load_ok": False,
        "data": {},
    }
    if not report["exists"]:
        return report
    try:
        modified_time_epoch = os.path.getmtime(path)
        report["modified_time_epoch"] = modified_time_epoch
        report["modified_time_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(modified_time_epoch))
    except Exception as exc:
        report["modified_time_error"] = str(exc)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            report["data"] = json.load(handle)
        report["load_ok"] = True
    except Exception as exc:
        report["error"] = str(exc)
    return report


def _write_native_primary_refresh_final_gate_report(report):
    os.makedirs(os.path.dirname(NATIVE_PRIMARY_REFRESH_FINAL_GATE_REPORT_PATH), exist_ok=True)
    with open(NATIVE_PRIMARY_REFRESH_FINAL_GATE_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def record_native_primary_refresh_final_gate(
    primary_refresh_report_path=None,
    screenshot_report_path=None,
    smoke_report_path=None,
    output_only_review_report_path=None,
    gameplay_state_event_report_path=None,
    gameplay_placeholder_visual_report_path=None,
    gameplay_content_outcome_contract_path=None,
):
    primary_refresh_report_path = primary_refresh_report_path or NATIVE_PRIMARY_REFRESH_REPORT_PATH
    smoke_report_path = smoke_report_path or NATIVE_INTEGRATION_TEST_REPORT_PATH
    output_only_review_report_path = output_only_review_report_path or NATIVE_INTEGRATION_OUTPUT_REVIEW_REPORT_PATH
    gameplay_state_event_report_path = gameplay_state_event_report_path or GAMEPLAY_STATE_EVENT_VALIDATION_REPORT_PATH
    gameplay_placeholder_visual_report_path = gameplay_placeholder_visual_report_path or GAMEPLAY_PLACEHOLDER_VISUAL_REPORT_PATH
    gameplay_content_outcome_contract_path = gameplay_content_outcome_contract_path or GAMEPLAY_CONTENT_OUTCOME_CONTRACT_PATH

    primary_source = _read_json_report(primary_refresh_report_path)
    primary = primary_source.get("data", {})
    embedded_screenshot = primary.get("screenshot", {}).get("active_viewport", {})
    if screenshot_report_path is None:
        screenshot_report_path = embedded_screenshot.get("screenshot_report_path") or os.path.join(
            unreal.Paths.project_saved_dir(),
            "MCP_Dungeon",
            "CubelessDungeonMVP_NativePrimaryRefresh_ScreenshotQA.json",
        )
    screenshot_source = _read_json_report(screenshot_report_path)
    smoke_source = _read_json_report(smoke_report_path)
    output_only_source = _read_json_report(output_only_review_report_path)
    gameplay_state_event_source = _read_json_report(gameplay_state_event_report_path)
    gameplay_visual_source = _read_json_report(gameplay_placeholder_visual_report_path)
    gameplay_outcome_source = _read_json_report(gameplay_content_outcome_contract_path)

    expected = _native_integration_expected_runtime_counts()
    expected_components = _coerce_int(expected.get("static_mesh_component_count"), 63)
    expected_instances = _coerce_int(expected.get("static_mesh_instance_count"), 630)

    output_actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL)
    live_output_summary = _actor_static_mesh_component_summary(output_actor)
    live_dirty_packages = _dirty_package_names()

    primary_checks = dict(primary.get("checks", {}))
    primary_output_generation = primary.get("native_output_verify", {}).get("generation_verification", {})
    primary_output_summary = primary_output_generation.get("component_summary", {})
    embedded_smoke = primary.get("smoke_test", {})
    output_only = output_only_source.get("data", {})
    output_only_generation = output_only.get("native_output_generation", {})
    output_only_summary = output_only_generation.get("component_summary", {})
    screenshot_data = screenshot_source.get("data", {})
    screenshot_captures = screenshot_data.get("captures", [])
    screenshot_capture = screenshot_captures[0] if screenshot_captures else {}
    smoke_data = smoke_source.get("data", {})
    smoke_generation = smoke_data.get("generation_verification", {})
    smoke_cleanup = smoke_data.get("cleanup_verification", {})
    smoke_summary = smoke_generation.get("component_summary", {})
    gameplay_state_event_data = gameplay_state_event_source.get("data", {})
    gameplay_visual_data = gameplay_visual_source.get("data", {})
    gameplay_outcome_data = gameplay_outcome_source.get("data", {})
    gameplay_state_event_total = _coerce_int(gameplay_state_event_data.get("key_event_result_count"), 0) + _coerce_int(
        gameplay_state_event_data.get("event_result_count"), 0
    )

    checks = {
        "primary_refresh_report_load_ok": bool(primary_source.get("load_ok")),
        "primary_refresh_pass": bool(primary.get("pass")),
        "primary_refresh_status_passed": primary.get("status") == "passed",
        "primary_refresh_checks_pass": _native_primary_refresh_checks_pass(primary_checks),
        "primary_refresh_dirty_after_zero": _coerce_int(primary_checks.get("dirty_after_count"), -1) == 0,
        "primary_output_generation_pass": bool(primary_output_generation.get("pass")),
        "primary_output_component_count": _coerce_int(primary_output_summary.get("component_count"), -1) == expected_components,
        "primary_output_instance_count": _coerce_int(primary_output_summary.get("instance_count_total"), -1) == expected_instances,
        "embedded_screenshot_qa_pass": bool(primary_checks.get("screenshot_qa_pass")),
        "screenshot_report_load_ok": bool(screenshot_source.get("load_ok")),
        "screenshot_report_pass": bool(screenshot_data.get("qa_pass") and screenshot_data.get("capture_qa_pass")),
        "screenshot_file_nonzero": bool(
            screenshot_capture.get("filepath")
            and os.path.exists(screenshot_capture.get("filepath"))
            and _coerce_int(screenshot_capture.get("file_size"), 0) > 0
        ),
        "embedded_smoke_test_pass": bool(primary_checks.get("smoke_test_pass")),
        "smoke_report_load_ok": bool(smoke_source.get("load_ok")),
        "smoke_report_pass": bool(smoke_data.get("pass")),
        "smoke_generation_count": _coerce_int(smoke_summary.get("component_count"), -1) == expected_components
        and _coerce_int(smoke_summary.get("instance_count_total"), -1) == expected_instances,
        "smoke_cleanup_zero": _coerce_int(smoke_cleanup.get("residual_static_mesh_component_count"), -1) == 0
        and _coerce_int(smoke_cleanup.get("residual_static_mesh_instance_count"), -1) == 0,
        "embedded_smoke_generation_count": _coerce_int(embedded_smoke.get("generated_static_mesh_component_count"), -1) == expected_components
        and _coerce_int(embedded_smoke.get("generated_static_mesh_instance_count"), -1) == expected_instances,
        "embedded_smoke_cleanup_zero": _coerce_int(embedded_smoke.get("cleanup_residual_static_mesh_component_count"), -1) == 0
        and _coerce_int(embedded_smoke.get("cleanup_residual_static_mesh_instance_count"), -1) == 0,
        "output_only_report_load_ok": bool(output_only_source.get("load_ok")),
        "output_only_review_pass": bool(output_only.get("pass")),
        "output_only_generation_pass": bool(output_only_generation.get("pass")),
        "output_only_component_count": _coerce_int(output_only_summary.get("component_count"), -1) == expected_components,
        "output_only_instance_count": _coerce_int(output_only_summary.get("instance_count_total"), -1) == expected_instances,
        "gameplay_state_event_report_load_ok": bool(gameplay_state_event_source.get("load_ok")),
        "gameplay_state_event_validation_pass": bool(gameplay_state_event_data.get("pass")),
        "gameplay_state_event_key_result_count": _coerce_int(gameplay_state_event_data.get("key_event_result_count"), 0) > 0,
        "gameplay_state_event_result_count": _coerce_int(gameplay_state_event_data.get("event_result_count"), 0) > 0,
        "gameplay_state_event_failure_count_zero": len(gameplay_state_event_data.get("validation_failures", [])) == 0,
        "gameplay_state_event_visual_failure_count_zero": len(gameplay_state_event_data.get("visual_validation_failures", [])) == 0,
        "gameplay_state_event_reset_failure_count_zero": len(gameplay_state_event_data.get("reset_failures", [])) == 0,
        "gameplay_state_event_visual_reset_failure_count_zero": len(gameplay_state_event_data.get("visual_reset_failures", [])) == 0,
        "gameplay_placeholder_visual_report_load_ok": bool(gameplay_visual_source.get("load_ok")),
        "gameplay_placeholder_visual_pass": bool(gameplay_visual_data.get("pass")),
        "gameplay_placeholder_visual_actor_count": _coerce_int(gameplay_visual_data.get("actor_count"), -1) == 22,
        "gameplay_placeholder_visual_component_fail_zero": _coerce_int(gameplay_visual_data.get("component_fail_count"), -1) == 0,
        "gameplay_placeholder_visual_mesh_fail_zero": _coerce_int(gameplay_visual_data.get("mesh_fail_count"), -1) == 0,
        "gameplay_content_outcome_contract_report_load_ok": bool(gameplay_outcome_source.get("load_ok")),
        "gameplay_content_outcome_contract_pass": bool(gameplay_outcome_data.get("pass")),
        "gameplay_content_outcome_contract_entry_count": _coerce_int(gameplay_outcome_data.get("outcome_count"), 0) > 0,
        "gameplay_content_outcome_contract_matches_state_events": _coerce_int(gameplay_outcome_data.get("state_event_covered_count"), -1)
        == gameplay_state_event_total,
        "gameplay_content_outcome_contract_failure_count_zero": _coerce_int(
            gameplay_outcome_data.get("validation", {}).get("failure_count"), -1
        )
        == 0,
        "live_native_output_actor_found": bool(output_actor),
        "live_native_output_component_count": _coerce_int(live_output_summary.get("component_count"), -1) == expected_components,
        "live_native_output_instance_count": _coerce_int(live_output_summary.get("instance_count_total"), -1) == expected_instances,
        "live_dirty_package_count_zero": len(live_dirty_packages) == 0,
    }
    pass_value = all(bool(value) for value in checks.values())
    gate = {
        "schema": "cubeless_pcg_dungeon_native_primary_refresh_final_gate_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "policy": (
            "Final production-readiness gate for the current native primary refresh evidence. "
            "It does not regenerate the dungeon; it reads the latest primary refresh, screenshot QA, smoke test, "
            "and output-only review reports, then checks the live native output actor and dirty packages."
        ),
        "report_paths": {
            "primary_refresh": primary_refresh_report_path,
            "screenshot_qa": screenshot_report_path,
            "smoke_test": smoke_report_path,
            "output_only_review": output_only_review_report_path,
            "gameplay_state_event_validation": gameplay_state_event_report_path,
            "gameplay_placeholder_visual_validation": gameplay_placeholder_visual_report_path,
            "gameplay_content_outcome_contract": gameplay_content_outcome_contract_path,
            "final_gate": NATIVE_PRIMARY_REFRESH_FINAL_GATE_REPORT_PATH,
        },
        "expected_counts": {
            "static_mesh_component_count": expected_components,
            "static_mesh_instance_count": expected_instances,
            "source_graph_report_pass": bool(expected.get("source_graph_report_pass")),
            "integration_graph_report_pass": bool(expected.get("integration_graph_report_pass")),
        },
        "source_reports": {
            "primary_refresh": {
                "exists": primary_source.get("exists"),
                "load_ok": primary_source.get("load_ok"),
                "schema": primary.get("schema"),
                "status": primary.get("status"),
                "pass": bool(primary.get("pass")),
            },
            "screenshot_qa": {
                "exists": screenshot_source.get("exists"),
                "load_ok": screenshot_source.get("load_ok"),
                "qa_pass": bool(screenshot_data.get("qa_pass")),
                "capture_qa_pass": bool(screenshot_data.get("capture_qa_pass")),
                "screenshot_path": screenshot_capture.get("filepath"),
                "file_size": screenshot_capture.get("file_size"),
                "dirty_package_added_count": screenshot_capture.get("dirty_package_added_count"),
            },
            "smoke_test": {
                "exists": smoke_source.get("exists"),
                "load_ok": smoke_source.get("load_ok"),
                "schema": smoke_data.get("schema"),
                "status": smoke_data.get("status"),
                "pass": bool(smoke_data.get("pass")),
                "generated_component_count": smoke_summary.get("component_count"),
                "generated_instance_count": smoke_summary.get("instance_count_total"),
                "cleanup_residual_component_count": smoke_cleanup.get("residual_static_mesh_component_count"),
                "cleanup_residual_instance_count": smoke_cleanup.get("residual_static_mesh_instance_count"),
            },
            "output_only_review": {
                "exists": output_only_source.get("exists"),
                "load_ok": output_only_source.get("load_ok"),
                "schema": output_only.get("schema"),
                "status": output_only.get("status"),
                "pass": bool(output_only.get("pass")),
                "generated_component_count": output_only_summary.get("component_count"),
                "generated_instance_count": output_only_summary.get("instance_count_total"),
            },
            "gameplay_state_event_validation": {
                "exists": gameplay_state_event_source.get("exists"),
                "load_ok": gameplay_state_event_source.get("load_ok"),
                "schema": gameplay_state_event_data.get("schema"),
                "status": gameplay_state_event_data.get("status"),
                "pass": bool(gameplay_state_event_data.get("pass")),
                "key_event_result_count": gameplay_state_event_data.get("key_event_result_count"),
                "event_result_count": gameplay_state_event_data.get("event_result_count"),
                "validation_failure_count": len(gameplay_state_event_data.get("validation_failures", [])),
                "visual_validation_failure_count": len(gameplay_state_event_data.get("visual_validation_failures", [])),
                "reset_failure_count": len(gameplay_state_event_data.get("reset_failures", [])),
                "visual_reset_failure_count": len(gameplay_state_event_data.get("visual_reset_failures", [])),
            },
            "gameplay_placeholder_visual_validation": {
                "exists": gameplay_visual_source.get("exists"),
                "load_ok": gameplay_visual_source.get("load_ok"),
                "schema": gameplay_visual_data.get("schema"),
                "status": gameplay_visual_data.get("status"),
                "pass": bool(gameplay_visual_data.get("pass")),
                "actor_count": gameplay_visual_data.get("actor_count"),
                "component_fail_count": gameplay_visual_data.get("component_fail_count"),
                "mesh_fail_count": gameplay_visual_data.get("mesh_fail_count"),
            },
            "gameplay_content_outcome_contract": {
                "exists": gameplay_outcome_source.get("exists"),
                "load_ok": gameplay_outcome_source.get("load_ok"),
                "schema": gameplay_outcome_data.get("schema"),
                "status": gameplay_outcome_data.get("status"),
                "pass": bool(gameplay_outcome_data.get("pass")),
                "outcome_count": gameplay_outcome_data.get("outcome_count"),
                "state_event_covered_count": gameplay_outcome_data.get("state_event_covered_count"),
                "state_event_total": gameplay_state_event_total,
                "failure_count": gameplay_outcome_data.get("validation", {}).get("failure_count"),
                "outcome_kind_counts": gameplay_outcome_data.get("outcome_kind_counts"),
            },
        },
        "live_native_output": {
            "actor_label": PCG_NATIVE_INTEGRATION_OUTPUT_LABEL,
            "actor_found": bool(output_actor),
            "component_summary": live_output_summary,
        },
        "live_dirty_packages": {
            "count": len(live_dirty_packages),
            "packages": live_dirty_packages,
        },
        "checks": checks,
        "pass": pass_value,
    }
    _write_native_primary_refresh_final_gate_report(gate)
    unreal.log(
        "CubelessDungeonPCG native primary refresh final gate: "
        + json.dumps(
            {
                "pass": pass_value,
                "status": gate["status"],
                "component_count": live_output_summary.get("component_count"),
                "instance_count": live_output_summary.get("instance_count_total"),
                "dirty_package_count": len(live_dirty_packages),
            },
            ensure_ascii=False,
        )
    )
    return gate


def _write_pcg_structure_audit_report(report):
    os.makedirs(os.path.dirname(PCG_STRUCTURE_AUDIT_REPORT_PATH), exist_ok=True)
    with open(PCG_STRUCTURE_AUDIT_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _write_pcg_generation_gate_report(report):
    os.makedirs(os.path.dirname(PCG_GENERATION_GATE_REPORT_PATH), exist_ok=True)
    with open(PCG_GENERATION_GATE_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _write_generation_parameter_scale_report(report):
    os.makedirs(os.path.dirname(PCG_GENERATION_PARAMETER_SCALE_REPORT_PATH), exist_ok=True)
    with open(PCG_GENERATION_PARAMETER_SCALE_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _float_close(actual, expected, tolerance=0.001):
    return math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=float(tolerance))


def _vector_close(actual, expected, tolerance=0.001):
    return bool(
        len(actual) == len(expected)
        and all(_float_close(actual[index], expected[index], tolerance) for index in range(len(expected)))
    )


def validate_generation_scale_parameters(grid_cell_size=520.0, corridor_width=280.0):
    previous_metrics = dict(GENERATION_METRICS)
    expected_grid = _coerce_float(grid_cell_size, TILE, 200.0, 1200.0)
    expected_corridor = min(_coerce_float(corridor_width, expected_grid, 120.0, 1200.0), expected_grid)
    expected_grid_scale = expected_grid / float(TILE)
    expected_corridor_width_scale = expected_corridor / expected_grid
    try:
        metrics = _set_generation_metrics(grid_cell_size=grid_cell_size, corridor_width=corridor_width)
        sample_cell_location = _cell_to_location((1, 2), 0.0)
        north_wall_location, north_wall_rotation = _wall_transform((0, 0), "N")
        east_wall_location, east_wall_rotation = _wall_transform((0, 0), "E")
        room_scale = _module_scale()
        corridor_east_west_scale = _yaw_width_scale(0.0)
        corridor_north_south_scale = _yaw_width_scale(90.0)
        door_north_south_scale = _directional_width_scale("N")
        door_east_west_scale = _directional_width_scale("E")
        checks = {
            "grid_cell_size_applied": _float_close(_grid_cell_size(), expected_grid),
            "corridor_width_applied": _float_close(metrics.get("corridor_width"), expected_corridor),
            "grid_scale_applied": _float_close(_grid_scale_xy(), expected_grid_scale),
            "corridor_width_scale_applied": _float_close(_corridor_width_scale(), expected_corridor_width_scale),
            "cell_location_uses_grid_cell_size": _vector_close(
                _location_record(sample_cell_location),
                [expected_grid, expected_grid * 2.0, 0.0],
            ),
            "north_wall_location_uses_grid_cell_size": _vector_close(
                _location_record(north_wall_location),
                [0.0, expected_grid * 0.5, 0.0],
            ),
            "east_wall_location_uses_grid_cell_size": _vector_close(
                _location_record(east_wall_location),
                [expected_grid * 0.5, 0.0, 0.0],
            ),
            "wall_rotations_preserved": _float_close(north_wall_rotation.yaw, 0.0)
            and _float_close(east_wall_rotation.yaw, 90.0),
            "room_module_xy_scale_uses_grid_scale": _vector_close(
                _scale_record(room_scale),
                [expected_grid_scale, expected_grid_scale, 1.0],
            ),
            "corridor_width_scales_local_y_axis": _vector_close(
                _scale_record(corridor_east_west_scale),
                [expected_grid_scale, expected_grid_scale * expected_corridor_width_scale, 1.0],
            )
            and _vector_close(
                _scale_record(corridor_north_south_scale),
                [expected_grid_scale, expected_grid_scale * expected_corridor_width_scale, 1.0],
            ),
            "door_connector_width_scales_local_x_axis": _vector_close(
                _scale_record(door_north_south_scale),
                [expected_grid_scale * expected_corridor_width_scale, expected_grid_scale, 1.0],
            )
            and _vector_close(
                _scale_record(door_east_west_scale),
                [expected_grid_scale * expected_corridor_width_scale, expected_grid_scale, 1.0],
            ),
            "scaled_offsets_use_grid_scale": _float_close(_scaled_xy(80.0), 80.0 * expected_grid_scale),
        }
        pass_value = all(bool(value) for value in checks.values())
        report = {
            "schema": "cubeless_pcg_dungeon_generation_parameter_scale_v1",
            "status": "passed" if pass_value else "failed",
            "policy": (
                "C++-free generation parameter smoke test. It does not modify level actors; it verifies that "
                "DungeonGridCellSize drives world spacing and base XY module scale, while DungeonCorridorWidth "
                "drives corridor/door connector width scale before PCG point export."
            ),
            "sample_input": {
                "grid_cell_size": float(grid_cell_size),
                "corridor_width": float(corridor_width),
            },
            "expected": {
                "grid_cell_size": float(expected_grid),
                "corridor_width": float(expected_corridor),
                "grid_scale": float(expected_grid_scale),
                "corridor_width_scale": float(expected_corridor_width_scale),
            },
            "actual": {
                "generation_metrics": dict(metrics),
                "grid_scale": float(_grid_scale_xy()),
                "corridor_width_scale": float(_corridor_width_scale()),
                "cell_location_1_2": _location_record(sample_cell_location),
                "north_wall_location": _location_record(north_wall_location),
                "north_wall_rotation": _rotation_record(north_wall_rotation),
                "east_wall_location": _location_record(east_wall_location),
                "east_wall_rotation": _rotation_record(east_wall_rotation),
                "room_module_scale": _scale_record(room_scale),
                "corridor_east_west_scale": _scale_record(corridor_east_west_scale),
                "corridor_north_south_scale": _scale_record(corridor_north_south_scale),
                "door_north_south_scale": _scale_record(door_north_south_scale),
                "door_east_west_scale": _scale_record(door_east_west_scale),
                "scaled_offset_80": float(_scaled_xy(80.0)),
            },
            "checks": checks,
            "report_path": PCG_GENERATION_PARAMETER_SCALE_REPORT_PATH,
            "pass": pass_value,
        }
    finally:
        GENERATION_METRICS.clear()
        GENERATION_METRICS.update(previous_metrics)
    _write_generation_parameter_scale_report(report)
    unreal.log(
        "CubelessDungeonPCG generation parameter scale validation: "
        + json.dumps(
            {
                "pass": report["pass"],
                "grid_cell_size": report["expected"]["grid_cell_size"],
                "corridor_width": report["expected"]["corridor_width"],
                "failed_checks": [key for key, value in checks.items() if not value],
            },
            ensure_ascii=False,
        )
    )
    return report


def _coerce_float(value, fallback, min_value=None, max_value=None):
    try:
        coerced = float(str(value).strip())
    except Exception:
        coerced = float(fallback)
    if min_value is not None:
        coerced = max(float(min_value), coerced)
    if max_value is not None:
        coerced = min(float(max_value), coerced)
    return coerced


def _normalize_yaw_degrees(yaw):
    normalized = (float(yaw) + 180.0) % 360.0 - 180.0
    if abs(normalized + 180.0) < 0.001:
        return 180.0
    return normalized


def _yaw_delta_degrees(actual, expected):
    return abs(_normalize_yaw_degrees(float(actual) - float(expected)))


def _expected_direction_yaw(direction):
    return {
        "N": 0.0,
        "E": 90.0,
        "S": 180.0,
        "W": -90.0,
    }.get(str(direction))


def _point_yaw(point):
    rotation = point.get("transform", {}).get("rotation", [0.0, 0.0, 0.0])
    try:
        return float(rotation[1])
    except Exception:
        return 0.0


def audit_pcg_dungeon_structure_and_orientation():
    dungeon_source = _read_json_report(REPORT_PATH)
    gameplay_source = _read_json_report(GAMEPLAY_DATA_PATH)
    spawner_source = _read_json_report(PCG_SPAWNER_CONTRACT_PATH)
    handoff_source = _read_json_report(PCG_GRAPH_HANDOFF_PATH)
    native_point_source = _read_json_report(NATIVE_POINT_SOURCE_REPORT_PATH)
    native_integration_graph = _read_json_report(NATIVE_INTEGRATION_GRAPH_REPORT_PATH)
    native_integration_audit = _read_json_report(NATIVE_INTEGRATION_AUDIT_REPORT_PATH)
    native_output_report = _read_json_report(NATIVE_INTEGRATION_OUTPUT_REPORT_PATH)

    dungeon = dungeon_source.get("data", {})
    gameplay = gameplay_source.get("data", {})
    spawner = spawner_source.get("data", {})
    handoff = handoff_source.get("data", {})
    native_points = native_point_source.get("data", {})
    integration_graph = native_integration_graph.get("data", {})
    integration_audit = native_integration_audit.get("data", {})
    native_output = native_output_report.get("data", {})
    config = dict(dungeon.get("config") or gameplay.get("config") or {})
    rooms = gameplay.get("rooms", [])
    room_edges = gameplay.get("room_edges", [])
    cells = gameplay.get("cells", [])
    progression = gameplay.get("progression", {})
    module_actor_counts = dict(dungeon.get("module_actor_counts") or gameplay.get("module_actor_counts") or {})
    start_room_id = dungeon.get("start_room_id")
    exit_room_id = dungeon.get("exit_room_id")
    if start_room_id is None:
        start_rooms = [room.get("id") for room in rooms if "start" in list(room.get("roles", []))]
        start_room_id = start_rooms[0] if start_rooms else None
    if exit_room_id is None:
        exit_rooms = [room.get("id") for room in rooms if "exit" in list(room.get("roles", []))]
        exit_room_id = exit_rooms[0] if exit_rooms else None
    points = spawner.get("points", [])
    groups = spawner.get("groups", [])
    spawner_module_counts = dict(spawner.get("module_counts") or {})
    use_ceiling_value = _coerce_int(config.get("use_ceiling"), 0, 0, 1)
    ceiling_stride_value = _coerce_int(config.get("ceiling_stride"), 0, 0, 64)
    ceiling_should_spawn = bool(use_ceiling_value > 0 and ceiling_stride_value > 0)
    ceiling_actor_count = _coerce_int(module_actor_counts.get("ceiling"), 0, 0, None)
    expected_ceiling_actor_count = _coerce_int(dungeon.get("expected_ceiling_actor_count"), -1, -1, None)
    ceiling_spawner_point_count = _coerce_int(spawner_module_counts.get("ceiling"), 0, 0, None)
    ceiling_mesh_group_keys = sorted(
        str(group.get("mesh_key"))
        for group in groups
        if str(group.get("mesh_key", "")).startswith("ceiling")
    )

    single_mesh_group_failures = []
    material_split_failures = []
    group_point_total = 0
    for group in groups:
        static_mesh_paths = list(group.get("static_mesh_paths", []))
        group_point_total += _coerce_int(group.get("point_count"), 0, 0, None)
        if len(static_mesh_paths) != 1:
            single_mesh_group_failures.append(
                {
                    "spawner_group_key": group.get("spawner_group_key"),
                    "static_mesh_paths": static_mesh_paths,
                }
            )
        if _coerce_int(group.get("material_variant_count"), 0, 0, None) > 1 and not bool(group.get("requires_material_attribute")):
            material_split_failures.append(
                {
                    "spawner_group_key": group.get("spawner_group_key"),
                    "material_variant_count": group.get("material_variant_count"),
                    "requires_material_attribute": group.get("requires_material_attribute"),
                }
            )

    direction_counts = {}
    module_direction_counts = {}
    direction_mismatches = []
    yaw_attribute_mismatches = []
    directional_point_count = 0
    for point in points:
        attributes = point.get("attributes", {})
        module = str(point.get("module") or attributes.get("DungeonModule") or "")
        direction = attributes.get("DungeonDirection")
        yaw = _point_yaw(point)
        if direction:
            directional_point_count += 1
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
            module_counts = module_direction_counts.setdefault(module, {})
            module_counts[direction] = module_counts.get(direction, 0) + 1
            expected_yaw = _expected_direction_yaw(direction)
            if expected_yaw is not None and _yaw_delta_degrees(yaw, expected_yaw) > 0.25:
                if len(direction_mismatches) < 40:
                    direction_mismatches.append(
                        {
                            "label": point.get("label"),
                            "module": module,
                            "direction": direction,
                            "expected_yaw": expected_yaw,
                            "actual_yaw": yaw,
                        }
                    )
        tagged_yaw = None
        if attributes.get("DungeonCorridorDetailYaw") is not None:
            tagged_yaw = attributes.get("DungeonCorridorDetailYaw")
        elif attributes.get("DungeonRoomVariantYaw") is not None:
            tagged_yaw = attributes.get("DungeonRoomVariantYaw")
        if tagged_yaw is not None:
            expected_tagged_yaw = _coerce_float(tagged_yaw, yaw)
            if _yaw_delta_degrees(yaw, expected_tagged_yaw) > 0.25:
                if len(yaw_attribute_mismatches) < 40:
                    yaw_attribute_mismatches.append(
                        {
                            "label": point.get("label"),
                            "module": module,
                            "tagged_yaw": expected_tagged_yaw,
                            "actual_yaw": yaw,
                        }
                    )

    required_wall_directions = {"N", "S", "E", "W"}
    wall_direction_counts = module_direction_counts.get("wall", {})
    missing_wall_directions = sorted(required_wall_directions - set(wall_direction_counts.keys()))

    exposed_parameters = {
        "Seed": config.get("seed"),
        "RoomCount": config.get("room_count"),
        "BranchChancePercent": config.get("branch_chance_percent"),
        "MaxLoopEdges": config.get("max_loop_edges"),
        "GridCellSize": config.get("grid_cell_size"),
        "CorridorWidth": config.get("corridor_width"),
        "UseCeiling": config.get("use_ceiling"),
        "UseThemeMaterials": config.get("use_theme_materials"),
        "PreviewMode": config.get("preview_mode"),
    }
    missing_exposed_parameters = sorted([key for key, value in exposed_parameters.items() if value is None])
    parameter_application_status = config.get("parameter_application_status", {})

    structure_checks = {
        "dungeon_report_load_ok": bool(dungeon_source.get("load_ok")),
        "dungeon_report_pass": bool(dungeon.get("pass")),
        "gameplay_data_load_ok": bool(gameplay_source.get("load_ok")),
        "room_count_matches_config": _coerce_int(dungeon.get("room_count"), -1) == _coerce_int(config.get("room_count"), -2),
        "room_records_match_report": len(rooms) == _coerce_int(dungeon.get("room_count"), -1),
        "edge_count_at_least_tree": len(room_edges) >= max(0, len(rooms) - 1),
        "cell_records_present": len(cells) > 0,
        "main_path_present": _coerce_int(progression.get("main_path_room_count"), 0) >= 2,
        "start_exit_distinct": start_room_id is not None and exit_room_id is not None and int(start_room_id) != int(exit_room_id),
        "progression_metadata_present": bool(progression),
        "gameplay_implementation_explicitly_deferred": True,
    }
    spawner_checks = {
        "spawner_contract_load_ok": bool(spawner_source.get("load_ok")),
        "spawner_contract_pass": bool(spawner.get("pass")),
        "spawner_points_present": len(points) > 0,
        "spawner_group_count_matches": len(groups) == _coerce_int(spawner.get("group_count"), -1),
        "spawner_point_total_matches_groups": group_point_total == _coerce_int(spawner.get("point_count"), -1),
        "single_static_mesh_per_group": not single_mesh_group_failures,
        "material_variant_groups_flagged": not material_split_failures,
        "handoff_load_ok": bool(handoff_source.get("load_ok")),
        "handoff_pass": bool(handoff.get("pass")),
        "native_point_source_load_ok": bool(native_point_source.get("load_ok")),
        "native_point_source_pass": bool(native_points.get("pass")),
    }
    native_checks = {
        "native_integration_graph_load_ok": bool(native_integration_graph.get("load_ok")),
        "native_integration_graph_pass": bool(integration_graph.get("pass")),
        "native_integration_audit_load_ok": bool(native_integration_audit.get("load_ok")),
        "native_integration_audit_pass": bool(integration_audit.get("pass")),
        "native_output_report_load_ok": bool(native_output_report.get("load_ok")),
        "native_output_report_pass": bool(native_output.get("pass")),
    }
    orientation_checks = {
        "directional_points_present": directional_point_count > 0,
        "direction_yaw_mismatch_zero": len(direction_mismatches) == 0,
        "tagged_yaw_mismatch_zero": len(yaw_attribute_mismatches) == 0,
        "wall_has_all_cardinal_directions": not missing_wall_directions,
    }
    config_checks = {
        "required_exposed_parameters_present": not missing_exposed_parameters,
        "branch_parameters_functional": exposed_parameters.get("BranchChancePercent") is not None and exposed_parameters.get("MaxLoopEdges") is not None,
        "grid_cell_size_functional": parameter_application_status.get("grid_cell_size") == "applied_to_world_spacing_and_static_mesh_xy_scale",
        "corridor_width_functional": parameter_application_status.get("corridor_width") == "applied_to_corridor_door_connector_xy_scale",
        "core_user_parameters_present": exposed_parameters.get("Seed") is not None and exposed_parameters.get("RoomCount") is not None,
        "ceiling_toggle_functional": (
            (not ceiling_should_spawn and ceiling_actor_count == 0)
            or (ceiling_should_spawn and ceiling_actor_count > 0)
        ),
        "ceiling_count_matches_expected": expected_ceiling_actor_count < 0 or ceiling_actor_count == expected_ceiling_actor_count,
        "full_ceiling_coverage_when_stride_one": (
            not ceiling_should_spawn
            or ceiling_stride_value != 1
            or ceiling_actor_count == len(cells)
        ),
        "ceiling_spawner_points_match_actor_count": ceiling_spawner_point_count == ceiling_actor_count,
        "ceiling_mesh_groups_present_when_enabled": (not ceiling_should_spawn) or bool(ceiling_mesh_group_keys),
    }
    pass_value = bool(
        all(structure_checks.values())
        and all(spawner_checks.values())
        and all(native_checks.values())
        and all(orientation_checks.values())
        and all(config_checks.values())
    )
    report = {
        "schema": "cubeless_pcg_dungeon_structure_orientation_audit_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "policy": (
            "PCG-generation-focused audit. Gameplay implementation reports are intentionally not required here; "
            "gameplay remains metadata/placeholder-only while dungeon structure, PCG spawner grouping, and module orientation stabilize."
        ),
        "native_generation_target": {
            "production_graph": NATIVE_INTEGRATION_GRAPH_PATH,
            "production_output_actor": PCG_NATIVE_INTEGRATION_OUTPUT_LABEL,
            "bridge_actor": PCG_BRIDGE_LABEL,
            "bridge_role": "validation_and_point_source_export",
        },
        "exposed_parameters": exposed_parameters,
        "parameter_application_status": parameter_application_status,
        "structure_summary": {
            "seed": dungeon.get("seed") or gameplay.get("seed"),
            "room_count": len(rooms),
            "edge_count": len(room_edges),
            "branch_count": max(0, len(room_edges) - max(0, len(rooms) - 1)),
            "cell_count": len(cells),
            "main_path_room_count": progression.get("main_path_room_count"),
            "side_room_count": progression.get("side_room_count"),
            "start_room_id": start_room_id,
            "exit_room_id": exit_room_id,
        },
        "spawner_grouping": {
            "point_count": spawner.get("point_count"),
            "group_count": spawner.get("group_count"),
            "material_variant_group_count": spawner.get("material_variant_group_count"),
            "group_point_total": group_point_total,
            "single_mesh_group_failure_count": len(single_mesh_group_failures),
            "material_split_failure_count": len(material_split_failures),
            "single_mesh_group_failures": single_mesh_group_failures[:20],
            "material_split_failures": material_split_failures[:20],
        },
        "ceiling": {
            "use_ceiling": use_ceiling_value,
            "ceiling_stride": ceiling_stride_value,
            "ceiling_should_spawn": ceiling_should_spawn,
            "actor_count": ceiling_actor_count,
            "expected_actor_count": expected_ceiling_actor_count,
            "spawner_point_count": ceiling_spawner_point_count,
            "mesh_group_keys": ceiling_mesh_group_keys,
            "module_actor_counts": {
                key: module_actor_counts.get(key, 0)
                for key in ("ceiling", "ceiling_room", "ceiling_corridor", "ceiling_corner")
            },
        },
        "orientation": {
            "directional_point_count": directional_point_count,
            "direction_counts": direction_counts,
            "module_direction_counts": module_direction_counts,
            "direction_mismatch_count": len(direction_mismatches),
            "tagged_yaw_mismatch_count": len(yaw_attribute_mismatches),
            "missing_wall_directions": missing_wall_directions,
            "direction_mismatches": direction_mismatches,
            "yaw_attribute_mismatches": yaw_attribute_mismatches,
        },
        "checks": {
            "structure": structure_checks,
            "spawner": spawner_checks,
            "native": native_checks,
            "orientation": orientation_checks,
            "config": config_checks,
        },
        "report_path": PCG_STRUCTURE_AUDIT_REPORT_PATH,
        "pass": pass_value,
    }
    _write_pcg_structure_audit_report(report)
    unreal.log(
        "CubelessDungeonPCG PCG structure/orientation audit: "
        + json.dumps(
            {
                "pass": pass_value,
                "room_count": len(rooms),
                "point_count": spawner.get("point_count"),
                "direction_mismatch_count": len(direction_mismatches),
                "tagged_yaw_mismatch_count": len(yaw_attribute_mismatches),
            },
            ensure_ascii=False,
        )
    )
    return report


def _summarize_screenshot_qa_report(source):
    data = source.get("data", {}) if source else {}
    captures = data.get("captures", []) if isinstance(data, dict) else []
    active = captures[0] if captures else {}
    screenshot_path = active.get("filepath")
    return {
        "exists": bool(source.get("exists")) if source else False,
        "load_ok": bool(source.get("load_ok")) if source else False,
        "report_timestamp": data.get("timestamp") if isinstance(data, dict) else None,
        "report_modified_time_epoch": source.get("modified_time_epoch") if source else None,
        "report_modified_time_utc": source.get("modified_time_utc") if source else None,
        "qa_pass": bool(data.get("qa_pass")) if isinstance(data, dict) else False,
        "capture_qa_pass": bool(data.get("capture_qa_pass")) if isinstance(data, dict) else False,
        "screenshot_path": screenshot_path,
        "file_size": active.get("file_size") or active.get("file_size_bytes"),
        "sha256": active.get("sha256"),
        "capture_source": active.get("capture_source"),
        "dirty_package_added_count": active.get("dirty_package_added_count"),
        "view_location": active.get("view_location"),
        "view_rotation": active.get("view_rotation"),
    }


def _screenshot_qa_summary_pass(summary):
    return bool(
        summary.get("load_ok")
        and summary.get("qa_pass")
        and summary.get("capture_qa_pass")
        and summary.get("screenshot_path")
        and os.path.exists(summary.get("screenshot_path"))
        and _coerce_int(summary.get("file_size"), 0) > 0
        and _coerce_int(summary.get("dirty_package_added_count"), 0) == 0
    )


def record_pcg_generation_final_gate(
    structure_audit_report_path=None,
    seed_suite_report_path=None,
    screenshot_report_path=None,
    oblique_screenshot_report_path=None,
    parameter_scale_report_path=None,
    authoring_surface_report_path=None,
    authoring_preset_smoke_report_path=None,
    generation_refresh_report_path=None,
):
    structure_audit_report_path = structure_audit_report_path or PCG_STRUCTURE_AUDIT_REPORT_PATH
    seed_suite_report_path = seed_suite_report_path or SEED_SUITE_REPORT_PATH
    screenshot_report_path = screenshot_report_path or PCG_GENERATION_OUTPUT_ONLY_SCREENSHOT_QA_PATH
    oblique_screenshot_report_path = oblique_screenshot_report_path or PCG_GENERATION_OUTPUT_ONLY_OBLIQUE_SCREENSHOT_QA_PATH
    parameter_scale_report_path = parameter_scale_report_path or PCG_GENERATION_PARAMETER_SCALE_REPORT_PATH
    authoring_surface_report_path = authoring_surface_report_path or AUTHORING_SURFACE_REPORT_PATH
    authoring_preset_smoke_report_path = authoring_preset_smoke_report_path or AUTHORING_PRESET_SMOKE_REPORT_PATH
    generation_refresh_report_path = generation_refresh_report_path or PCG_GENERATION_REFRESH_REPORT_PATH
    audit_source = _read_json_report(structure_audit_report_path)
    seed_suite_source = _read_json_report(seed_suite_report_path)
    output_source = _read_json_report(NATIVE_INTEGRATION_OUTPUT_REPORT_PATH)
    integration_graph_source = _read_json_report(NATIVE_INTEGRATION_GRAPH_REPORT_PATH)
    integration_audit_source = _read_json_report(NATIVE_INTEGRATION_AUDIT_REPORT_PATH)
    screenshot_source = _read_json_report(screenshot_report_path)
    oblique_screenshot_source = _read_json_report(oblique_screenshot_report_path)
    parameter_scale_source = _read_json_report(parameter_scale_report_path)
    authoring_surface_source = _read_json_report(authoring_surface_report_path)
    authoring_preset_smoke_source = _read_json_report(authoring_preset_smoke_report_path)
    generation_refresh_source = _read_json_report(generation_refresh_report_path)

    audit = audit_source.get("data", {})
    seed_suite = seed_suite_source.get("data", {})
    output_report = output_source.get("data", {})
    integration_graph = integration_graph_source.get("data", {})
    integration_audit = integration_audit_source.get("data", {})
    parameter_scale = parameter_scale_source.get("data", {})
    authoring_surface = authoring_surface_source.get("data", {})
    authoring_preset_smoke = authoring_preset_smoke_source.get("data", {})
    generation_refresh = generation_refresh_source.get("data", {})
    screenshot_summary = _summarize_screenshot_qa_report(screenshot_source)
    oblique_screenshot_summary = _summarize_screenshot_qa_report(oblique_screenshot_source)
    generation_refresh_mtime = generation_refresh_source.get("modified_time_epoch")
    screenshot_mtime = screenshot_source.get("modified_time_epoch")
    oblique_screenshot_mtime = oblique_screenshot_source.get("modified_time_epoch")
    expected = _native_integration_expected_runtime_counts()
    output_actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_OUTPUT_LABEL)
    live_output_summary = _actor_static_mesh_component_summary(output_actor)
    dirty_packages = _dirty_package_names()
    checks = {
        "structure_audit_load_ok": bool(audit_source.get("load_ok")),
        "structure_audit_pass": bool(audit.get("pass")),
        "seed_suite_load_ok": bool(seed_suite_source.get("load_ok")),
        "seed_suite_pass": bool(seed_suite.get("pass")),
        "seed_suite_fail_count_zero": _coerce_int(seed_suite.get("fail_count"), -1) == 0,
        "native_integration_graph_load_ok": bool(integration_graph_source.get("load_ok")),
        "native_integration_graph_pass": bool(integration_graph.get("pass")),
        "native_integration_audit_load_ok": bool(integration_audit_source.get("load_ok")),
        "native_integration_audit_pass": bool(integration_audit.get("pass")),
        "native_output_report_load_ok": bool(output_source.get("load_ok")),
        "native_output_report_pass": bool(output_report.get("pass")),
        "live_native_output_actor_found": bool(output_actor),
        "live_native_output_component_count": _coerce_int(live_output_summary.get("component_count"), -1) == expected["static_mesh_component_count"],
        "live_native_output_instance_count": _coerce_int(live_output_summary.get("instance_count_total"), -1) == expected["static_mesh_instance_count"],
        "orientation_direction_mismatch_zero": _coerce_int(audit.get("orientation", {}).get("direction_mismatch_count"), -1) == 0,
        "orientation_tagged_yaw_mismatch_zero": _coerce_int(audit.get("orientation", {}).get("tagged_yaw_mismatch_count"), -1) == 0,
        "spawner_single_mesh_groups": _coerce_int(
            audit.get("spawner_grouping", {}).get("single_mesh_group_failure_count"),
            -1,
        )
        == 0,
        "spawner_material_split_groups_valid": _coerce_int(
            audit.get("spawner_grouping", {}).get("material_split_failure_count"),
            -1,
        )
        == 0,
        "required_exposed_parameters_present": bool(
            audit.get("checks", {}).get("config", {}).get("required_exposed_parameters_present")
        ),
        "generation_parameter_scale_report_load_ok": bool(parameter_scale_source.get("load_ok")),
        "generation_parameter_scale_report_pass": bool(parameter_scale.get("pass")),
        "authoring_surface_report_load_ok": bool(authoring_surface_source.get("load_ok")),
        "authoring_surface_report_pass": bool(authoring_surface.get("pass")),
        "authoring_preset_smoke_report_load_ok": bool(authoring_preset_smoke_source.get("load_ok")),
        "authoring_preset_smoke_report_pass": bool(authoring_preset_smoke.get("pass")),
        "pcg_generation_refresh_report_load_ok": bool(generation_refresh_source.get("load_ok")),
        "pcg_generation_refresh_report_pass": bool(generation_refresh.get("pass")),
        "top_screenshot_qa_pass": _screenshot_qa_summary_pass(screenshot_summary),
        "oblique_screenshot_qa_pass": _screenshot_qa_summary_pass(oblique_screenshot_summary),
        "top_screenshot_after_generation_refresh": bool(
            screenshot_mtime
            and generation_refresh_mtime
            and float(screenshot_mtime) >= float(generation_refresh_mtime)
        ),
        "oblique_screenshot_after_generation_refresh": bool(
            oblique_screenshot_mtime
            and generation_refresh_mtime
            and float(oblique_screenshot_mtime) >= float(generation_refresh_mtime)
        ),
        "dirty_package_count_zero": len(dirty_packages) == 0,
    }
    pass_value = all(bool(value) for value in checks.values())
    gate = {
        "schema": "cubeless_pcg_dungeon_generation_final_gate_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "policy": (
            "PCG dungeon generation gate for the current goal. It ignores gameplay implementation readiness and requires "
            "native PCG output, seed suite, spawner grouping, orientation, exposed generation parameters, parameter-scale "
            "smoke validation, authoring surface validation, preset apply/restore smoke validation, PCG-generation-only "
            "refresh validation, top/oblique native-output-only screenshot QA, and clean dirty-package state."
        ),
        "report_paths": {
            "structure_audit": structure_audit_report_path,
            "seed_suite": seed_suite_report_path,
            "native_integration_output": NATIVE_INTEGRATION_OUTPUT_REPORT_PATH,
            "native_integration_graph": NATIVE_INTEGRATION_GRAPH_REPORT_PATH,
            "native_integration_audit": NATIVE_INTEGRATION_AUDIT_REPORT_PATH,
            "generation_parameter_scale": parameter_scale_report_path,
            "authoring_surface": authoring_surface_report_path,
            "authoring_preset_smoke": authoring_preset_smoke_report_path,
            "pcg_generation_refresh": generation_refresh_report_path,
            "top_screenshot_qa": screenshot_report_path,
            "oblique_screenshot_qa": oblique_screenshot_report_path,
            "generation_final_gate": PCG_GENERATION_GATE_REPORT_PATH,
        },
        "native_generation_target": audit.get("native_generation_target", {}),
        "exposed_parameters": audit.get("exposed_parameters", {}),
        "structure_summary": audit.get("structure_summary", {}),
        "spawner_grouping": audit.get("spawner_grouping", {}),
        "orientation": {
            "directional_point_count": audit.get("orientation", {}).get("directional_point_count"),
            "direction_counts": audit.get("orientation", {}).get("direction_counts"),
            "direction_mismatch_count": audit.get("orientation", {}).get("direction_mismatch_count"),
            "tagged_yaw_mismatch_count": audit.get("orientation", {}).get("tagged_yaw_mismatch_count"),
            "missing_wall_directions": audit.get("orientation", {}).get("missing_wall_directions"),
        },
        "seed_suite": {
            "exists": seed_suite_source.get("exists"),
            "load_ok": seed_suite_source.get("load_ok"),
            "pass": bool(seed_suite.get("pass")),
            "seed_count": seed_suite.get("seed_count"),
            "pass_count": seed_suite.get("pass_count"),
            "fail_count": seed_suite.get("fail_count"),
        },
        "generation_parameter_scale": {
            "exists": parameter_scale_source.get("exists"),
            "load_ok": parameter_scale_source.get("load_ok"),
            "pass": bool(parameter_scale.get("pass")),
            "sample_input": parameter_scale.get("sample_input"),
            "expected": parameter_scale.get("expected"),
            "failed_checks": [key for key, value in parameter_scale.get("checks", {}).items() if not value],
        },
        "authoring_surface": {
            "exists": authoring_surface_source.get("exists"),
            "load_ok": authoring_surface_source.get("load_ok"),
            "pass": bool(authoring_surface.get("pass")),
            "preset_count": len(authoring_surface.get("presets", {})),
            "preset_failures": authoring_surface.get("preset_failures", []),
            "missing_config_keys": authoring_surface.get("current_actor", {}).get("missing_config_keys", []),
            "unknown_config_tags": authoring_surface.get("current_actor", {}).get("unknown_config_tags", []),
            "clamped_or_invalid_values": authoring_surface.get("current_actor", {}).get("clamped_or_invalid_values", []),
        },
        "authoring_preset_smoke": {
            "exists": authoring_preset_smoke_source.get("exists"),
            "load_ok": authoring_preset_smoke_source.get("load_ok"),
            "pass": bool(authoring_preset_smoke.get("pass")),
            "preset_name": authoring_preset_smoke.get("preset_name"),
            "failed_checks": [
                key for key, value in authoring_preset_smoke.get("checks", {}).items() if not value
            ],
            "restored_config": authoring_preset_smoke.get("restored_config"),
        },
        "pcg_generation_refresh": {
            "exists": generation_refresh_source.get("exists"),
            "load_ok": generation_refresh_source.get("load_ok"),
            "report_modified_time_epoch": generation_refresh_source.get("modified_time_epoch"),
            "report_modified_time_utc": generation_refresh_source.get("modified_time_utc"),
            "pass": bool(generation_refresh.get("pass")),
            "status": generation_refresh.get("status"),
            "config": generation_refresh.get("config"),
            "failed_checks": [key for key, value in generation_refresh.get("checks", {}).items() if not value],
        },
        "live_native_output": {
            "actor_label": PCG_NATIVE_INTEGRATION_OUTPUT_LABEL,
            "actor_found": bool(output_actor),
            "component_summary": live_output_summary,
            "expected_component_count": expected["static_mesh_component_count"],
            "expected_instance_count": expected["static_mesh_instance_count"],
        },
        "live_dirty_packages": {
            "count": len(dirty_packages),
            "packages": dirty_packages,
        },
        "screenshot_qa": {
            "top": screenshot_summary,
            "oblique": oblique_screenshot_summary,
        },
        "checks": checks,
        "pass": pass_value,
    }
    _write_pcg_generation_gate_report(gate)
    unreal.log(
        "CubelessDungeonPCG PCG generation final gate: "
        + json.dumps(
            {
                "pass": pass_value,
                "failed_check_count": len([key for key, value in checks.items() if not value]),
                "component_count": live_output_summary.get("component_count"),
                "instance_count": live_output_summary.get("instance_count_total"),
                "dirty_package_count": len(dirty_packages),
            },
            ensure_ascii=False,
        )
    )
    return gate


GAMEPLAY_PLACEHOLDER_BLUEPRINT_SPECS = {
    "player_start": {
        "asset_name": "BP_DungeonGameplay_PlayerStartPlaceholder",
        "parent_class": unreal.PlayerStart,
    },
    "exit": {
        "asset_name": "BP_DungeonGameplay_ExitPlaceholder",
        "parent_class": unreal.TargetPoint,
    },
    "key": {
        "asset_name": "BP_DungeonGameplay_KeyPickupPlaceholder",
        "parent_class": unreal.TargetPoint,
    },
    "locked_gate": {
        "asset_name": "BP_DungeonGameplay_LockedGatePlaceholder",
        "parent_class": unreal.TriggerBox,
    },
    "reward": {
        "asset_name": "BP_DungeonGameplay_RewardPlaceholder",
        "parent_class": unreal.TargetPoint,
    },
    "enemy": {
        "asset_name": "BP_DungeonGameplay_EnemySpawnPlaceholder",
        "parent_class": unreal.TargetPoint,
    },
    "boss": {
        "asset_name": "BP_DungeonGameplay_BossSpawnPlaceholder",
        "parent_class": unreal.TargetPoint,
    },
    "shop": {
        "asset_name": "BP_DungeonGameplay_ShopPlaceholder",
        "parent_class": unreal.TargetPoint,
    },
}
GAMEPLAY_PLACEHOLDER_VISUAL_SPECS = {
    "player_start": {
        "component_name": "DungeonVisual_Start",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_SpawnMarker.SM_GS_Dungeon_SpawnMarker",
    },
    "exit": {
        "component_name": "DungeonVisual_Exit",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_Detail_Arch.SM_GS_Dungeon_Detail_Arch",
    },
    "key": {
        "component_name": "DungeonVisual_Key",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_RoomVariant_ProgressionRune.SM_GS_Dungeon_RoomVariant_ProgressionRune",
    },
    "locked_gate": {
        "component_name": "DungeonVisual_LockedGate",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_LockedDoorSeal.SM_GS_Dungeon_LockedDoorSeal",
    },
    "reward": {
        "component_name": "DungeonVisual_Reward",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_Detail_Pedestal.SM_GS_Dungeon_Detail_Pedestal",
    },
    "enemy": {
        "component_name": "DungeonVisual_EnemySpawn",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_RoomVariant_CombatPartition.SM_GS_Dungeon_RoomVariant_CombatPartition",
    },
    "boss": {
        "component_name": "DungeonVisual_BossSpawn",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_Detail_BossFocus.SM_GS_Dungeon_Detail_BossFocus",
    },
    "shop": {
        "component_name": "DungeonVisual_Shop",
        "mesh_path": MESH_DIR + "/SM_GS_Dungeon_Detail_Counter.SM_GS_Dungeon_Detail_Counter",
    },
}


def _write_gameplay_placeholder_report(report):
    os.makedirs(os.path.dirname(GAMEPLAY_PLACEHOLDER_REPORT_PATH), exist_ok=True)
    with open(GAMEPLAY_PLACEHOLDER_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _write_gameplay_placeholder_visual_report(report):
    os.makedirs(os.path.dirname(GAMEPLAY_PLACEHOLDER_VISUAL_REPORT_PATH), exist_ok=True)
    with open(GAMEPLAY_PLACEHOLDER_VISUAL_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _load_gameplay_data_report():
    if os.path.exists(GAMEPLAY_DATA_PATH):
        with open(GAMEPLAY_DATA_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _placeholder_kind_title(kind):
    return "".join(part.title() for part in str(kind).split("_"))


def _vector_from_record_location(record, z_offset=0.0):
    values = record.get("location") or record.get("world") or [0.0, 0.0, 0.0]
    return unreal.Vector(
        float(values[0]),
        float(values[1]),
        float(values[2]) + float(z_offset),
    )


def _rotator_from_record_yaw(record):
    return _yaw_rotator(float(record.get("yaw", 0.0) or 0.0))


def _blueprint_generated_class(blueprint, asset_path, asset_name):
    generated_class = None
    try:
        generated_class = blueprint.get_editor_property("generated_class")
    except Exception:
        generated_class = None
    if not generated_class:
        generated_attr = getattr(blueprint, "generated_class", None)
        if callable(generated_attr):
            try:
                generated_class = generated_attr()
            except Exception:
                generated_class = None
        else:
            generated_class = generated_attr
    if not generated_class:
        generated_class = unreal.load_object(None, "{}.{}_C".format(asset_path, asset_name))
    return generated_class


def _unreal_class_name(class_value):
    try:
        return class_value.static_class().get_name()
    except Exception:
        return getattr(class_value, "__name__", str(class_value))


def _ensure_gameplay_placeholder_blueprints():
    unreal.EditorAssetLibrary.make_directory(BLUEPRINT_DIR)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    results = {}
    for key, spec in sorted(GAMEPLAY_PLACEHOLDER_BLUEPRINT_SPECS.items()):
        asset_name = spec["asset_name"]
        asset_path = BLUEPRINT_DIR + "/" + asset_name
        blueprint = unreal.EditorAssetLibrary.load_asset(asset_path)
        created = False
        error = None
        if not blueprint:
            try:
                factory = unreal.BlueprintFactory()
                factory.set_editor_property("parent_class", spec["parent_class"])
                blueprint = asset_tools.create_asset(asset_name, BLUEPRINT_DIR, None, factory)
                created = bool(blueprint)
            except Exception as exc:
                error = str(exc)
        if blueprint:
            try:
                unreal.KismetCompilerLibrary.compile_blueprint(blueprint)
            except Exception:
                pass
            try:
                unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
            except Exception as exc:
                error = str(exc)
        generated_class = _blueprint_generated_class(blueprint, asset_path, asset_name) if blueprint else None
        results[key] = {
            "asset_name": asset_name,
            "asset_path": asset_path,
            "parent_class": _unreal_class_name(spec["parent_class"]),
            "created": created,
            "exists": bool(blueprint),
            "generated_class": generated_class.get_path_name() if generated_class else None,
            "error": error,
        }
    return results


def _gameplay_placeholder_actors():
    actors = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            label = actor.get_actor_label()
            tags = [str(tag) for tag in list(actor.tags)]
        except Exception:
            continue
        if label.startswith(GAMEPLAY_PLACEHOLDER_PREFIX) or "DungeonGameplayPlaceholder" in tags:
            actors.append(actor)
    return actors


def _static_mesh_component_path(component):
    try:
        static_mesh = component.get_editor_property("static_mesh")
        return static_mesh.get_path_name() if static_mesh else None
    except Exception:
        return None


def validate_gameplay_placeholder_visual_components(save_dirty_packages=True):
    actor_results = []
    kind_counts = {}
    missing_actor_kind_count = 0
    missing_spec_count = 0
    component_fail_count = 0
    mesh_fail_count = 0
    sample_failures = []

    for actor in _gameplay_placeholder_actors():
        try:
            label = actor.get_actor_label()
            tag_map = _tag_values([str(tag) for tag in list(actor.tags)])
        except Exception as exc:
            actor_results.append({"actor_label": "<unknown>", "pass": False, "error": str(exc)})
            component_fail_count += 1
            continue
        kind = tag_map.get("DungeonPlaceholderKind")
        if not kind:
            missing_actor_kind_count += 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        spec = GAMEPLAY_PLACEHOLDER_VISUAL_SPECS.get(kind)
        if not spec:
            missing_spec_count += 1
            result = {
                "actor_label": label,
                "placeholder_kind": kind,
                "pass": False,
                "error": "missing visual spec",
            }
            actor_results.append(result)
            sample_failures.append(result)
            continue

        expected_component = spec["component_name"]
        expected_mesh = spec["mesh_path"]
        matching_components = []
        static_mesh_components = []
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh_path = _static_mesh_component_path(component)
            record = {"component_name": component.get_name(), "static_mesh": mesh_path}
            static_mesh_components.append(record)
            if component.get_name() == expected_component:
                matching_components.append(record)
        component_pass = bool(matching_components)
        mesh_pass = bool(component_pass and any(item.get("static_mesh") == expected_mesh for item in matching_components))
        if not component_pass:
            component_fail_count += 1
        if not mesh_pass:
            mesh_fail_count += 1
        result = {
            "actor_label": label,
            "placeholder_kind": kind,
            "expected_component": expected_component,
            "expected_mesh": expected_mesh,
            "component_pass": component_pass,
            "mesh_pass": mesh_pass,
            "components": static_mesh_components,
            "pass": bool(component_pass and mesh_pass),
        }
        actor_results.append(result)
        if not result["pass"] and len(sample_failures) < 12:
            sample_failures.append(result)

    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    pass_value = bool(
        actor_results
        and missing_actor_kind_count == 0
        and missing_spec_count == 0
        and component_fail_count == 0
        and mesh_fail_count == 0
        and (not save_dirty_packages or (save_summary.get("save_dirty_packages_result") and _coerce_int(save_summary.get("dirty_after_count"), -1) == 0))
    )
    report = {
        "schema": "cubeless_pcg_dungeon_gameplay_placeholder_visual_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "blueprint_dir": BLUEPRINT_DIR,
        "policy": (
            "C++-free live gameplay placeholder visual validation. Visual components use existing Geometry Script Static Mesh assets "
            "so runtime placeholders are inspectable without adding new project C++."
        ),
        "actor_count": len(actor_results),
        "kind_counts": kind_counts,
        "expected_specs": GAMEPLAY_PLACEHOLDER_VISUAL_SPECS,
        "missing_actor_kind_count": missing_actor_kind_count,
        "missing_spec_count": missing_spec_count,
        "component_fail_count": component_fail_count,
        "mesh_fail_count": mesh_fail_count,
        "sample_failures": sample_failures,
        "actors": actor_results,
        "save_dirty_packages": save_summary,
        "report_path": GAMEPLAY_PLACEHOLDER_VISUAL_REPORT_PATH,
        "pass": pass_value,
    }
    _write_gameplay_placeholder_visual_report(report)
    unreal.log(
        "CubelessDungeonPCG gameplay placeholder visuals: "
        + json.dumps(
            {
                "pass": pass_value,
                "actor_count": len(actor_results),
                "component_fail_count": component_fail_count,
                "mesh_fail_count": mesh_fail_count,
            },
            ensure_ascii=False,
        )
    )
    return report


def clear_gameplay_placeholder_actors():
    removed = 0
    errors = []
    for actor in list(_gameplay_placeholder_actors()):
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed += 1
        except Exception as exc:
            try:
                label = actor.get_actor_label()
            except Exception:
                label = "<unknown>"
            errors.append({"label": label, "error": str(exc)})
    return {"removed": removed, "errors": errors}


def _gameplay_placeholder_tags(seed, placeholder_kind, source_collection, source_record, extra=None):
    tags = [
        "DungeonGameplayPlaceholder",
        "DungeonGeneratedFromGameplayData",
        "DungeonModule=gameplay_placeholder",
        "DungeonPlaceholderKind={}".format(placeholder_kind),
        "DungeonSeed={}".format(seed),
        "DungeonSourceCollection={}".format(source_collection),
        "DungeonSourceAnchorLabel={}".format(source_record.get("label")),
    ]
    if source_record.get("room_id") is not None:
        tags.append("DungeonRoomId={}".format(source_record.get("room_id")))
    if source_record.get("encounter_id"):
        tags.append("DungeonEncounterId={}".format(source_record.get("encounter_id")))
    if source_record.get("kind"):
        tags.append("DungeonSourceKind={}".format(source_record.get("kind")))
    if source_record.get("reward_id"):
        tags.append("DungeonRewardId={}".format(source_record.get("reward_id")))
    if source_record.get("interaction"):
        tags.append("DungeonInteractionKind={}".format(source_record.get("interaction")))
    if extra:
        tags.extend(extra)
    return tags


def _gameplay_placeholder_placements(data):
    seed = int(data.get("seed", 0) or 0)
    placements = []
    for record in data.get("spawn_points", []):
        kind = record.get("kind")
        if kind == "start":
            placements.append(
                {
                    "placeholder_kind": "player_start",
                    "source_collection": "spawn_points",
                    "source_record": record,
                    "location": _vector_from_record_location(record),
                    "rotation": _rotator_from_record_yaw(record),
                    "tags": _gameplay_placeholder_tags(seed, "player_start", "spawn_points", record, ["DungeonGameplayRole=start"]),
                }
            )
        elif kind == "exit":
            placements.append(
                {
                    "placeholder_kind": "exit",
                    "source_collection": "spawn_points",
                    "source_record": record,
                    "location": _vector_from_record_location(record),
                    "rotation": _rotator_from_record_yaw(record),
                    "tags": _gameplay_placeholder_tags(seed, "exit", "spawn_points", record, ["DungeonGameplayRole=exit"]),
                }
            )
    for record in data.get("reward_points", []):
        kind = record.get("kind")
        if kind == "key":
            extra = ["DungeonGameplayRole=key"]
            for link in record.get("key_links", []):
                extra.extend(
                    [
                        "DungeonKeyId={}".format(link.get("required_key_id")),
                        "DungeonUnlocksLockIds={}".format(link.get("lock_id")),
                        "DungeonUnlockCount=1",
                    ]
                )
            placements.append(
                {
                    "placeholder_kind": "key",
                    "source_collection": "reward_points",
                    "source_record": record,
                    "location": _vector_from_record_location(record),
                    "rotation": _rotator_from_record_yaw(record),
                    "tags": _gameplay_placeholder_tags(seed, "key", "reward_points", record, extra),
                }
            )
        elif kind == "shop":
            placements.append(
                {
                    "placeholder_kind": "shop",
                    "source_collection": "reward_points",
                    "source_record": record,
                    "location": _vector_from_record_location(record),
                    "rotation": _rotator_from_record_yaw(record),
                    "tags": _gameplay_placeholder_tags(seed, "shop", "reward_points", record, ["DungeonGameplayRole=shop"]),
                }
            )
        elif kind in ("treasure", "exit_unlock"):
            placements.append(
                {
                    "placeholder_kind": "reward",
                    "source_collection": "reward_points",
                    "source_record": record,
                    "location": _vector_from_record_location(record),
                    "rotation": _rotator_from_record_yaw(record),
                    "tags": _gameplay_placeholder_tags(seed, "reward", "reward_points", record, ["DungeonGameplayRole={}".format(kind)]),
                }
            )
    for record in data.get("door_points", []):
        if record.get("door_kind") != "locked":
            continue
        lock_link = record.get("lock_link") or {}
        placements.append(
            {
                "placeholder_kind": "locked_gate",
                "source_collection": "door_points",
                "source_record": record,
                "location": _vector_from_record_location(record),
                "rotation": _rotator_from_record_yaw(record),
                "box_extent": [150.0, 75.0, WALL_HEIGHT * 0.5],
                "tags": _gameplay_placeholder_tags(
                    seed,
                    "locked_gate",
                    "door_points",
                    record,
                    [
                        "DungeonGameplayRole=locked_gate",
                        "DungeonDoorKind=locked",
                        "DungeonLockId={}".format(lock_link.get("lock_id")),
                        "DungeonRequiredKeyId={}".format(lock_link.get("required_key_id")),
                        "DungeonLockIndex={}".format(lock_link.get("lock_index")),
                        "DungeonLockBeforeRoomId={}".format(lock_link.get("before_room_id")),
                        "DungeonLockAfterRoomId={}".format(lock_link.get("after_room_id")),
                    ],
                ),
            }
        )
    for record in data.get("encounter_spawn_points", []):
        kind = record.get("kind")
        if kind not in ("enemy", "boss"):
            continue
        placements.append(
            {
                "placeholder_kind": kind,
                "source_collection": "encounter_spawn_points",
                "source_record": record,
                "location": _vector_from_record_location(record),
                "rotation": _rotator_from_record_yaw(record),
                "tags": _gameplay_placeholder_tags(
                    seed,
                    kind,
                    "encounter_spawn_points",
                    record,
                    [
                        "DungeonGameplayRole={}".format(kind),
                        "DungeonEncounterSpawnKind={}".format(kind),
                        "DungeonEncounterSlotIndex={}".format(record.get("slot_index")),
                        "DungeonEncounterSlotCount={}".format(record.get("slot_count")),
                    ],
                ),
            }
        )
    return placements


def _spawn_gameplay_placeholder_actor(label, generated_class, placement):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        generated_class,
        placement["location"],
        placement["rotation"],
    )
    if not actor:
        raise RuntimeError("Failed to spawn gameplay placeholder actor: " + label)
    actor.set_actor_label(label, mark_dirty=True)
    _apply_actor_tags(actor, placement["tags"])
    if placement.get("placeholder_kind") == "locked_gate":
        component = actor.get_component_by_class(unreal.BoxComponent)
        if component and placement.get("box_extent"):
            extent = placement["box_extent"]
            component.set_box_extent(unreal.Vector(float(extent[0]), float(extent[1]), float(extent[2])), True)
            component.set_editor_property("hidden_in_game", True)
    return actor


def _audit_gameplay_placeholder_actors(expected_counts):
    actual_counts = {}
    missing_required_tag_count = 0
    lock_ids = []
    key_unlocks = []
    samples = []
    for actor in _gameplay_placeholder_actors():
        label = actor.get_actor_label()
        tags = [str(tag) for tag in list(actor.tags)]
        tag_map = _tag_values(tags)
        kind = tag_map.get("DungeonPlaceholderKind", "<missing>")
        actual_counts[kind] = actual_counts.get(kind, 0) + 1
        if "DungeonGameplayPlaceholder" not in tags or kind == "<missing>":
            missing_required_tag_count += 1
        if kind == "locked_gate":
            lock_ids.append(tag_map.get("DungeonLockId"))
        if kind == "key":
            key_unlocks.append(tag_map.get("DungeonUnlocksLockIds"))
        if len(samples) < 12:
            samples.append({"label": label, "kind": kind, "tags": tags[:12]})
    count_mismatches = {
        key: {
            "expected": int(expected_counts.get(key, 0)),
            "actual": int(actual_counts.get(key, 0)),
        }
        for key in sorted(set(expected_counts.keys()) | set(actual_counts.keys()))
        if int(expected_counts.get(key, 0)) != int(actual_counts.get(key, 0))
    }
    lock_key_link_pass = bool(
        expected_counts.get("locked_gate", 0) == 0
        or (
            len([item for item in lock_ids if item]) == int(expected_counts.get("locked_gate", 0))
            and len([item for item in key_unlocks if item]) >= min(1, int(expected_counts.get("key", 0)))
        )
    )
    return {
        "actual_counts": actual_counts,
        "expected_counts": expected_counts,
        "count_mismatches": count_mismatches,
        "missing_required_tag_count": missing_required_tag_count,
        "lock_ids": lock_ids,
        "key_unlocks": key_unlocks,
        "lock_key_link_pass": lock_key_link_pass,
        "samples": samples,
        "pass": bool(not count_mismatches and missing_required_tag_count == 0 and lock_key_link_pass),
    }


def create_or_update_gameplay_placeholders(save_dirty_packages=True):
    data = _load_gameplay_data_report()
    blueprint_report = _ensure_gameplay_placeholder_blueprints()
    cleanup = clear_gameplay_placeholder_actors()
    placements = _gameplay_placeholder_placements(data)
    expected_counts = {}
    for placement in placements:
        kind = placement["placeholder_kind"]
        expected_counts[kind] = expected_counts.get(kind, 0) + 1

    spawned = []
    spawn_errors = []
    next_index_by_kind = {}
    for placement in placements:
        kind = placement["placeholder_kind"]
        index = next_index_by_kind.get(kind, 0)
        next_index_by_kind[kind] = index + 1
        spec = GAMEPLAY_PLACEHOLDER_BLUEPRINT_SPECS[kind]
        blueprint_info = blueprint_report.get(kind, {})
        generated_class = None
        if blueprint_info.get("generated_class"):
            generated_class = unreal.load_object(None, blueprint_info["generated_class"])
        if not generated_class:
            asset_path = BLUEPRINT_DIR + "/" + spec["asset_name"]
            blueprint = unreal.EditorAssetLibrary.load_asset(asset_path)
            generated_class = _blueprint_generated_class(blueprint, asset_path, spec["asset_name"]) if blueprint else None
        label = "{}{}_{:03d}".format(GAMEPLAY_PLACEHOLDER_PREFIX, _placeholder_kind_title(kind), index)
        try:
            if not generated_class:
                raise RuntimeError("Missing generated class for " + spec["asset_name"])
            actor = _spawn_gameplay_placeholder_actor(label, generated_class, placement)
            spawned.append(
                {
                    "label": label,
                    "kind": kind,
                    "blueprint": spec["asset_name"],
                    "source_collection": placement["source_collection"],
                    "source_label": placement["source_record"].get("label"),
                    "room_id": placement["source_record"].get("room_id"),
                    "location": _location_record(actor.get_actor_location()),
                }
            )
        except Exception as exc:
            spawn_errors.append(
                {
                    "label": label,
                    "kind": kind,
                    "source_label": placement["source_record"].get("label"),
                    "error": str(exc),
                }
            )

    audit = _audit_gameplay_placeholder_actors(expected_counts)
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    blueprint_errors = {
        key: value
        for key, value in blueprint_report.items()
        if value.get("error") or not value.get("exists") or not value.get("generated_class")
    }
    pass_value = bool(
        data.get("schema") == "cubeless_pcg_dungeon_gameplay_data_v1"
        and not blueprint_errors
        and not cleanup.get("errors")
        and not spawn_errors
        and audit.get("pass")
        and (not save_dirty_packages or (save_summary.get("save_dirty_packages_result") and _coerce_int(save_summary.get("dirty_after_count"), -1) == 0))
    )
    report = {
        "schema": "cubeless_pcg_dungeon_gameplay_placeholder_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "root": ROOT,
        "blueprint_dir": BLUEPRINT_DIR,
        "gameplay_data_path": GAMEPLAY_DATA_PATH,
        "policy": (
            "C++-free placeholder gameplay actor bridge. Actors are generated from GameplayData anchors and tagged "
            "with DungeonGameplayPlaceholder so they can be cleaned/regenerated without touching PCG validation actors."
        ),
        "gameplay_data_schema": data.get("schema"),
        "seed": data.get("seed"),
        "blueprints": blueprint_report,
        "cleanup": cleanup,
        "placement_count": len(placements),
        "expected_counts": expected_counts,
        "spawned_count": len(spawned),
        "spawned": spawned,
        "spawn_errors": spawn_errors,
        "audit": audit,
        "save_dirty_packages": save_summary,
        "report_path": GAMEPLAY_PLACEHOLDER_REPORT_PATH,
        "pass": pass_value,
    }
    _write_gameplay_placeholder_report(report)
    unreal.log(
        "CubelessDungeonPCG gameplay placeholders: "
        + json.dumps(
            {
                "pass": pass_value,
                "spawned_count": len(spawned),
                "expected_counts": expected_counts,
                "failed_spawns": len(spawn_errors),
            },
            ensure_ascii=False,
        )
    )
    return report


def _load_gameplay_placeholder_report():
    if os.path.exists(GAMEPLAY_PLACEHOLDER_REPORT_PATH):
        with open(GAMEPLAY_PLACEHOLDER_REPORT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _write_gameplay_interaction_contract(report):
    os.makedirs(os.path.dirname(GAMEPLAY_INTERACTION_CONTRACT_PATH), exist_ok=True)
    with open(GAMEPLAY_INTERACTION_CONTRACT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _actor_by_label_map():
    result = {}
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            result[actor.get_actor_label()] = actor
        except Exception:
            pass
    return result


def _merge_actor_tag_values(actor, values):
    current_tags = [str(tag) for tag in list(actor.tags)]
    replace_keys = set(values.keys())
    merged = []
    for tag in current_tags:
        key = tag.split("=", 1)[0]
        if key not in replace_keys:
            merged.append(tag)
    for key, value in sorted(values.items()):
        if value is None:
            continue
        merged.append("{}={}".format(key, value))
    _apply_actor_tags(actor, merged)
    return merged


def _set_actor_instance_property(actor, property_name, value):
    def _report_value(source_value):
        if source_value is None or isinstance(source_value, (bool, int, float, str)):
            return source_value
        try:
            if hasattr(source_value, "get_actor_label"):
                return source_value.get_actor_label()
        except Exception:
            pass
        try:
            if hasattr(source_value, "get_path_name"):
                return source_value.get_path_name()
        except Exception:
            pass
        return str(source_value)

    try:
        actor.set_editor_property(property_name, value)
        return {"property": property_name, "ok": True, "value": _report_value(value)}
    except Exception as exc:
        return {"property": property_name, "ok": False, "value": _report_value(value), "error": str(exc)}


def _placeholder_interaction_kind(kind, tag_map):
    if kind == "player_start":
        return "player_spawn"
    if kind == "exit":
        return "exit_activation"
    if kind == "key":
        return "key_pickup"
    if kind == "locked_gate":
        return "locked_gate"
    if kind == "shop":
        return "shop_open"
    if kind == "enemy":
        return "enemy_spawn"
    if kind == "boss":
        return "boss_spawn"
    if kind == "reward":
        interaction = tag_map.get("DungeonInteractionKind")
        if interaction in ("reward_chest", "exit_unlock_reward"):
            return interaction
        if interaction == "exit_unlock":
            return "exit_unlock_reward"
        return "reward_{}".format(interaction or tag_map.get("DungeonSourceKind") or "generic")
    return str(kind)


def _placeholder_interaction_state(kind, tag_map):
    if kind == "locked_gate":
        return "locked"
    if kind in ("enemy", "boss"):
        return "pending_spawn"
    if kind == "exit":
        return "inactive_until_clear"
    if kind == "player_start":
        return "ready"
    return "available"


def _write_gameplay_flow_simulation_report(report):
    os.makedirs(os.path.dirname(GAMEPLAY_FLOW_SIMULATION_REPORT_PATH), exist_ok=True)
    with open(GAMEPLAY_FLOW_SIMULATION_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def build_gameplay_interaction_contract(save_dirty_packages=True):
    placeholder_report = _load_gameplay_placeholder_report()
    actor_map = _actor_by_label_map()
    contract_entries = []
    actor_update_errors = []
    coverage = {
        "placeholder_report_exists": bool(placeholder_report),
        "placeholder_report_pass": bool(placeholder_report.get("pass")),
        "placeholder_actor_count": 0,
        "contract_entry_count": 0,
        "missing_actor_count": 0,
        "missing_contract_tag_count": 0,
    }
    kind_counts = {}
    interaction_kind_counts = {}
    key_contracts = []
    gate_contracts = []
    exit_contracts = []
    reward_contracts = []
    encounter_contracts = []
    instance_variable_updates = []
    linked_gate_assignments = []
    gate_actor_by_lock_id = {}

    for spawned in placeholder_report.get("spawned", []):
        if spawned.get("kind") != "locked_gate":
            continue
        gate_actor = actor_map.get(spawned.get("label"))
        if not gate_actor:
            continue
        gate_tag_map = _tag_values([str(tag) for tag in list(gate_actor.tags)])
        gate_lock_id = gate_tag_map.get("DungeonLockId")
        if gate_lock_id:
            gate_actor_by_lock_id[gate_lock_id] = gate_actor

    for index, spawned in enumerate(placeholder_report.get("spawned", [])):
        label = spawned.get("label")
        actor = actor_map.get(label)
        kind = spawned.get("kind")
        if not actor:
            coverage["missing_actor_count"] += 1
            contract_entries.append(
                {
                    "contract_id": "missing_actor_{:03d}".format(index),
                    "actor_label": label,
                    "placeholder_kind": kind,
                    "pass": False,
                    "error": "placeholder actor missing in live level",
                }
            )
            continue
        tags = [str(tag) for tag in list(actor.tags)]
        tag_map = _tag_values(tags)
        kind = kind or tag_map.get("DungeonPlaceholderKind")
        interaction_kind = _placeholder_interaction_kind(kind, tag_map)
        interaction_state = _placeholder_interaction_state(kind, tag_map)
        contract_id = "D{}_{}_{}".format(
            placeholder_report.get("seed", "0"),
            str(interaction_kind).upper(),
            str(label).replace(GAMEPLAY_PLACEHOLDER_PREFIX, ""),
        )
        required_key_id = tag_map.get("DungeonRequiredKeyId")
        unlocks_lock_ids = tag_map.get("DungeonUnlocksLockIds")
        lock_id = tag_map.get("DungeonLockId")
        encounter_id = tag_map.get("DungeonEncounterId")
        reward_id = tag_map.get("DungeonRewardId")
        room_id = tag_map.get("DungeonRoomId")
        linked_gate_actor = None
        linked_gate_actor_label = None
        linked_gate_lock_id = None
        if kind == "key":
            for candidate_lock_id in _split_pipe_values(unlocks_lock_ids):
                candidate_actor = gate_actor_by_lock_id.get(candidate_lock_id)
                if candidate_actor:
                    linked_gate_actor = candidate_actor
                    linked_gate_actor_label = candidate_actor.get_actor_label()
                    linked_gate_lock_id = candidate_lock_id
                    break
        try:
            final_tags = _merge_actor_tag_values(
                actor,
                {
                    "DungeonInteractionContractId": contract_id,
                    "DungeonInteractionKind": interaction_kind,
                    "DungeonInteractionState": interaction_state,
                    "DungeonInteractionRequiredKeyId": required_key_id,
                    "DungeonInteractionUnlocksLockIds": unlocks_lock_ids,
                    "DungeonInteractionLockId": lock_id,
                    "DungeonInteractionEncounterId": encounter_id,
                    "DungeonInteractionRewardId": reward_id,
                    "DungeonLinkedGateActorLabel": linked_gate_actor_label,
                    "DungeonLinkedGateLockId": linked_gate_lock_id,
                },
            )
        except Exception as exc:
            final_tags = tags
            actor_update_errors.append({"actor_label": label, "error": str(exc)})
        property_updates = [
            _set_actor_instance_property(actor, "InteractionContractId", contract_id),
            _set_actor_instance_property(actor, "InteractionKind", interaction_kind),
            _set_actor_instance_property(actor, "InteractionState", interaction_state),
            _set_actor_instance_property(actor, "bInteractionReady", interaction_state not in ("disabled", "consumed")),
            _set_actor_instance_property(actor, "bInteractionConsumed", False),
        ]
        if kind == "key":
            linked_gate_update = _set_actor_instance_property(actor, "LinkedGateActor", linked_gate_actor)
            property_updates.append(linked_gate_update)
            requires_gate_link = bool(_split_pipe_values(unlocks_lock_ids))
            linked_gate_assignments.append(
                {
                    "actor_label": label,
                    "unlocks_lock_ids": unlocks_lock_ids,
                    "linked_gate_actor_label": linked_gate_actor_label,
                    "linked_gate_lock_id": linked_gate_lock_id,
                    "update_ok": bool(linked_gate_update.get("ok")),
                    "requires_gate_link": requires_gate_link,
                    "pass": bool((not requires_gate_link) or (linked_gate_actor_label and linked_gate_update.get("ok"))),
                }
            )
        instance_variable_updates.append({"actor_label": label, "updates": property_updates})

        entry = {
            "contract_id": contract_id,
            "actor_label": label,
            "placeholder_kind": kind,
            "interaction_kind": interaction_kind,
            "interaction_state": interaction_state,
            "source_collection": spawned.get("source_collection") or tag_map.get("DungeonSourceCollection"),
            "source_anchor_label": spawned.get("source_label") or tag_map.get("DungeonSourceAnchorLabel"),
            "room_id": _coerce_int(room_id, -1),
            "required_key_id": required_key_id,
            "unlocks_lock_ids": unlocks_lock_ids,
            "lock_id": lock_id,
            "linked_gate_actor_label": linked_gate_actor_label,
            "linked_gate_lock_id": linked_gate_lock_id,
            "encounter_id": encounter_id,
            "reward_id": reward_id,
            "tag_count": len(final_tags),
            "instance_variable_update_fail_count": len([item for item in property_updates if not item.get("ok")]),
            "pass": bool(contract_id and kind and interaction_kind and interaction_state),
        }
        contract_entries.append(entry)
        coverage["placeholder_actor_count"] += 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        interaction_kind_counts[interaction_kind] = interaction_kind_counts.get(interaction_kind, 0) + 1
        if kind == "key":
            key_contracts.append(entry)
        if kind == "locked_gate":
            gate_contracts.append(entry)
        if kind == "exit":
            exit_contracts.append(entry)
        if kind == "reward":
            reward_contracts.append(entry)
        if kind in ("enemy", "boss"):
            encounter_contracts.append(entry)

    coverage["contract_entry_count"] = len(contract_entries)
    for actor in _gameplay_placeholder_actors():
        tag_map = _tag_values([str(tag) for tag in list(actor.tags)])
        if not tag_map.get("DungeonInteractionContractId") or not tag_map.get("DungeonInteractionKind"):
            coverage["missing_contract_tag_count"] += 1

    unlocked_lock_ids = set()
    for contract in key_contracts:
        for lock_id in str(contract.get("unlocks_lock_ids") or "").split("|"):
            if lock_id:
                unlocked_lock_ids.add(lock_id)
    gate_lock_ids = set(contract.get("lock_id") for contract in gate_contracts if contract.get("lock_id"))
    gate_required_key_ids = set(contract.get("required_key_id") for contract in gate_contracts if contract.get("required_key_id"))
    key_ids = set()
    for contract in key_contracts:
        actor = actor_map.get(contract.get("actor_label"))
        tag_map = _tag_values([str(tag) for tag in list(actor.tags)]) if actor else {}
        key_id = tag_map.get("DungeonKeyId")
        if key_id:
            key_ids.add(key_id)

    validation = {
        "required_interaction_count": len(contract_entries),
        "key_contract_count": len(key_contracts),
        "locked_gate_contract_count": len(gate_contracts),
        "exit_contract_count": len(exit_contracts),
        "reward_contract_count": len(reward_contracts),
        "encounter_contract_count": len(encounter_contracts),
        "actor_update_error_count": len(actor_update_errors),
        "instance_variable_update_error_count": sum(
            len([item for item in update.get("updates", []) if not item.get("ok")])
            for update in instance_variable_updates
        ),
        "key_linked_gate_reference_count": len(
            [item for item in linked_gate_assignments if item.get("linked_gate_actor_label")]
        ),
        "key_linked_gate_reference_fail_count": len(
            [item for item in linked_gate_assignments if not item.get("pass")]
        ),
        "key_linked_gate_reference_pass": bool(
            len([item for item in linked_gate_assignments if not item.get("pass")]) == 0
            and (
                len(key_contracts) == 0
                or len([item for item in linked_gate_assignments if item.get("linked_gate_actor_label")]) >= len(key_contracts)
            )
        ),
        "entry_fail_count": len([entry for entry in contract_entries if not entry.get("pass")]),
        "key_gate_linkage_pass": bool(
            len(gate_contracts) == 0
            or (
                bool(gate_lock_ids)
                and gate_lock_ids.issubset(unlocked_lock_ids)
                and bool(gate_required_key_ids)
                and gate_required_key_ids.issubset(key_ids)
            )
        ),
        "placeholder_coverage_pass": bool(
            coverage["placeholder_report_pass"]
            and coverage["missing_actor_count"] == 0
            and coverage["missing_contract_tag_count"] == 0
            and coverage["contract_entry_count"] == int(placeholder_report.get("spawned_count", len(placeholder_report.get("spawned", []))) or 0)
        ),
    }
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    pass_value = bool(
        validation["entry_fail_count"] == 0
        and validation["actor_update_error_count"] == 0
        and validation["instance_variable_update_error_count"] == 0
        and validation["key_linked_gate_reference_pass"]
        and validation["key_gate_linkage_pass"]
        and validation["placeholder_coverage_pass"]
        and (not save_dirty_packages or (save_summary.get("save_dirty_packages_result") and _coerce_int(save_summary.get("dirty_after_count"), -1) == 0))
    )
    report = {
        "schema": "cubeless_pcg_dungeon_gameplay_interaction_contract_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "gameplay_placeholder_report_path": GAMEPLAY_PLACEHOLDER_REPORT_PATH,
        "policy": (
            "C++-free gameplay interaction contract. This step does not implement Blueprint graph behavior; "
            "it tags live placeholder actors and exports the contract that Blueprint, UI, AI, and interaction systems can consume."
        ),
        "seed": placeholder_report.get("seed"),
        "coverage": coverage,
        "kind_counts": kind_counts,
        "interaction_kind_counts": interaction_kind_counts,
        "validation": validation,
        "actor_update_errors": actor_update_errors,
        "instance_variable_updates": instance_variable_updates,
        "linked_gate_assignments": linked_gate_assignments,
        "contracts": contract_entries,
        "save_dirty_packages": save_summary,
        "report_path": GAMEPLAY_INTERACTION_CONTRACT_PATH,
        "pass": pass_value,
    }
    _write_gameplay_interaction_contract(report)
    unreal.log(
        "CubelessDungeonPCG gameplay interaction contract: "
        + json.dumps(
            {
                "pass": pass_value,
                "contract_entry_count": len(contract_entries),
                "key_gate_linkage_pass": validation["key_gate_linkage_pass"],
                "placeholder_coverage_pass": validation["placeholder_coverage_pass"],
            },
            ensure_ascii=False,
        )
    )
    return report


def _load_gameplay_interaction_contract_report():
    if os.path.exists(GAMEPLAY_INTERACTION_CONTRACT_PATH):
        with open(GAMEPLAY_INTERACTION_CONTRACT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _split_pipe_values(value):
    return [item for item in str(value or "").split("|") if item]


def _write_gameplay_content_outcome_contract(report):
    os.makedirs(os.path.dirname(GAMEPLAY_CONTENT_OUTCOME_CONTRACT_PATH), exist_ok=True)
    with open(GAMEPLAY_CONTENT_OUTCOME_CONTRACT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _gameplay_content_outcome_spec(interaction_kind):
    specs = {
        "player_spawn": {
            "outcome_kind": "player_start_proxy",
            "content_category": "spawn",
            "trigger_event_names": [],
            "expected_runtime_result": "player controller can use this as the start anchor",
            "visual_feedback": "start marker remains visible for editor review",
        },
        "key_pickup": {
            "outcome_kind": "inventory_key_token",
            "content_category": "progression",
            "trigger_event_names": ["DungeonInteract"],
            "expected_runtime_result": "key is consumed and grants the matching lock key token",
            "visual_feedback": "key visual hides after pickup",
        },
        "locked_gate": {
            "outcome_kind": "gate_unlock_token",
            "content_category": "progression",
            "trigger_event_names": ["DungeonUnlockGate"],
            "expected_runtime_result": "gate becomes unlocked after its required key is collected",
            "visual_feedback": "locked gate visual hides after unlock",
        },
        "reward_chest": {
            "outcome_kind": "loot_proxy",
            "content_category": "reward",
            "trigger_event_names": ["DungeonOpenReward"],
            "expected_runtime_result": "reward placeholder should spawn or grant loot content",
            "visual_feedback": "reward visual hides after open",
        },
        "exit_unlock_reward": {
            "outcome_kind": "loot_proxy",
            "content_category": "reward",
            "trigger_event_names": ["DungeonOpenReward"],
            "expected_runtime_result": "exit-unlock reward placeholder should spawn or grant loot content",
            "visual_feedback": "reward visual hides after open",
        },
        "shop_open": {
            "outcome_kind": "shop_service_proxy",
            "content_category": "utility",
            "trigger_event_names": ["DungeonOpenShop"],
            "expected_runtime_result": "shop placeholder should open a shop service or UI handoff",
            "visual_feedback": "shop visual remains visible while open",
        },
        "exit_activation": {
            "outcome_kind": "exit_flow_proxy",
            "content_category": "level_flow",
            "trigger_event_names": ["DungeonActivateExit", "DungeonUseExit"],
            "expected_runtime_result": "exit can become active after clear conditions and complete the dungeon when used",
            "visual_feedback": "exit visual remains visible when active and hides after use",
        },
        "enemy_spawn": {
            "outcome_kind": "enemy_spawn_proxy",
            "content_category": "encounter",
            "trigger_event_names": ["DungeonSpawnEnemy"],
            "expected_runtime_result": "enemy spawn placeholder should spawn or hand off to an enemy archetype",
            "visual_feedback": "enemy spawn visual hides after spawn",
        },
        "boss_spawn": {
            "outcome_kind": "boss_spawn_proxy",
            "content_category": "encounter",
            "trigger_event_names": ["DungeonSpawnBoss"],
            "expected_runtime_result": "boss spawn placeholder should spawn or hand off to a boss archetype",
            "visual_feedback": "boss spawn visual hides after spawn",
        },
    }
    return specs.get(interaction_kind)


def build_gameplay_content_outcome_contract(save_dirty_packages=True):
    contract = build_gameplay_interaction_contract(save_dirty_packages=save_dirty_packages)
    actor_map = _actor_by_label_map()
    outcomes = []
    failures = []
    outcome_kind_counts = {}
    content_category_counts = {}
    state_event_covered_count = 0

    for index, entry in enumerate(contract.get("contracts", [])):
        interaction_kind = entry.get("interaction_kind")
        spec = _gameplay_content_outcome_spec(interaction_kind)
        actor = actor_map.get(entry.get("actor_label"))
        if not spec:
            failures.append(
                {
                    "source_contract_id": entry.get("contract_id"),
                    "actor_label": entry.get("actor_label"),
                    "interaction_kind": interaction_kind,
                    "reason": "missing content outcome spec",
                }
            )
            continue

        outcome_kind = spec.get("outcome_kind")
        content_category = spec.get("content_category")
        trigger_event_names = list(spec.get("trigger_event_names", []))
        state_event_covered_count += len(trigger_event_names)
        outcome_kind_counts[outcome_kind] = outcome_kind_counts.get(outcome_kind, 0) + 1
        content_category_counts[content_category] = content_category_counts.get(content_category, 0) + 1
        outcome_id = "{}_Outcome_{:03d}".format(entry.get("contract_id"), index)
        payload = {
            "room_id": entry.get("room_id"),
            "encounter_id": entry.get("encounter_id"),
            "reward_id": entry.get("reward_id"),
            "required_key_id": entry.get("required_key_id"),
            "unlocks_lock_ids": entry.get("unlocks_lock_ids"),
            "lock_id": entry.get("lock_id"),
            "linked_gate_actor_label": entry.get("linked_gate_actor_label"),
            "linked_gate_lock_id": entry.get("linked_gate_lock_id"),
        }
        outcome_pass = bool(outcome_id and entry.get("contract_id") and entry.get("actor_label") and actor)
        outcome = {
            "outcome_id": outcome_id,
            "source_contract_id": entry.get("contract_id"),
            "actor_label": entry.get("actor_label"),
            "actor_found": bool(actor),
            "placeholder_kind": entry.get("placeholder_kind"),
            "interaction_kind": interaction_kind,
            "interaction_state": entry.get("interaction_state"),
            "outcome_kind": outcome_kind,
            "content_category": content_category,
            "trigger_event_names": trigger_event_names,
            "expected_runtime_result": spec.get("expected_runtime_result"),
            "visual_feedback": spec.get("visual_feedback"),
            "payload": payload,
            "implementation_status": "contract_only",
            "pass": outcome_pass,
        }
        outcomes.append(outcome)
        if not outcome_pass:
            failures.append(
                {
                    "source_contract_id": entry.get("contract_id"),
                    "actor_label": entry.get("actor_label"),
                    "interaction_kind": interaction_kind,
                    "reason": "outcome source actor or id missing",
                }
            )

    required_min_counts = {
        "player_start_proxy": 1,
        "inventory_key_token": 1,
        "gate_unlock_token": 1,
        "loot_proxy": 1,
        "shop_service_proxy": 1,
        "exit_flow_proxy": 1,
        "enemy_spawn_proxy": 1,
        "boss_spawn_proxy": 1,
    }
    required_count_failures = []
    for outcome_kind, minimum_count in sorted(required_min_counts.items()):
        actual_count = _coerce_int(outcome_kind_counts.get(outcome_kind), 0)
        if actual_count < minimum_count:
            required_count_failures.append(
                {
                    "outcome_kind": outcome_kind,
                    "minimum_count": minimum_count,
                    "actual_count": actual_count,
                }
            )

    validation = {
        "source_contract_pass": bool(contract.get("pass")),
        "source_contract_entry_count": len(contract.get("contracts", [])),
        "outcome_count": len(outcomes),
        "state_event_covered_count": state_event_covered_count,
        "missing_spec_count": len([item for item in failures if item.get("reason") == "missing content outcome spec"]),
        "missing_actor_or_id_count": len([item for item in failures if item.get("reason") == "outcome source actor or id missing"]),
        "required_count_failures": required_count_failures,
        "failure_count": len(failures) + len(required_count_failures),
        "coverage_pass": bool(len(outcomes) == len(contract.get("contracts", [])) and not failures),
        "required_counts_pass": not required_count_failures,
    }
    save_summary = _save_dirty_packages_summary() if save_dirty_packages else {"skipped": True}
    pass_value = bool(
        validation["source_contract_pass"]
        and validation["coverage_pass"]
        and validation["required_counts_pass"]
        and validation["failure_count"] == 0
        and (not save_dirty_packages or (save_summary.get("save_dirty_packages_result") and _coerce_int(save_summary.get("dirty_after_count"), -1) == 0))
    )
    report = {
        "schema": "cubeless_pcg_dungeon_gameplay_content_outcome_contract_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "interaction_contract_path": GAMEPLAY_INTERACTION_CONTRACT_PATH,
        "policy": (
            "C++-free gameplay content outcome contract. This is a production handoff map for reward, shop, enemy, boss, "
            "exit, key, gate, and player-start content that can replace placeholder behavior later without changing dungeon anchors."
        ),
        "source_contract_pass": bool(contract.get("pass")),
        "source_contract_entry_count": len(contract.get("contracts", [])),
        "outcome_count": len(outcomes),
        "state_event_covered_count": state_event_covered_count,
        "outcome_kind_counts": outcome_kind_counts,
        "content_category_counts": content_category_counts,
        "validation": validation,
        "failures": failures,
        "outcomes": outcomes,
        "save_dirty_packages": save_summary,
        "report_path": GAMEPLAY_CONTENT_OUTCOME_CONTRACT_PATH,
        "pass": pass_value,
    }
    _write_gameplay_content_outcome_contract(report)
    unreal.log(
        "CubelessDungeonPCG gameplay content outcome contract: "
        + json.dumps(
            {
                "pass": pass_value,
                "outcome_count": len(outcomes),
                "state_event_covered_count": state_event_covered_count,
                "failure_count": validation["failure_count"],
            },
            ensure_ascii=False,
        )
    )
    return report


def simulate_gameplay_interaction_flow():
    contract = _load_gameplay_interaction_contract_report()
    entries = contract.get("contracts", [])
    by_kind = {}
    for entry in entries:
        by_kind.setdefault(entry.get("interaction_kind"), []).append(entry)
    inventory_keys = set()
    opened_locks = set()
    consumed_contracts = []
    activated_contracts = []
    steps = []

    player_spawn = by_kind.get("player_spawn", [])
    steps.append(
        {
            "step": "player_spawn_ready",
            "count": len(player_spawn),
            "pass": len(player_spawn) == 1,
            "actors": [entry.get("actor_label") for entry in player_spawn],
        }
    )

    for key_entry in by_kind.get("key_pickup", []):
        actor = _find_actor_by_label(key_entry.get("actor_label"))
        tag_map = _tag_values([str(tag) for tag in list(actor.tags)]) if actor else {}
        key_id = tag_map.get("DungeonKeyId") or key_entry.get("required_key_id")
        if key_id:
            inventory_keys.add(key_id)
        consumed_contracts.append(key_entry.get("contract_id"))
    steps.append(
        {
            "step": "key_pickup",
            "key_count": len(inventory_keys),
            "keys": sorted(inventory_keys),
            "pass": len(inventory_keys) >= len(by_kind.get("key_pickup", [])),
        }
    )

    gate_results = []
    for gate_entry in by_kind.get("locked_gate", []):
        required_key = gate_entry.get("required_key_id")
        lock_id = gate_entry.get("lock_id")
        unlocked = bool(required_key and required_key in inventory_keys and lock_id)
        if unlocked:
            opened_locks.add(lock_id)
            activated_contracts.append(gate_entry.get("contract_id"))
        gate_results.append(
            {
                "actor_label": gate_entry.get("actor_label"),
                "required_key_id": required_key,
                "lock_id": lock_id,
                "unlocked": unlocked,
            }
        )
    steps.append(
        {
            "step": "locked_gate_unlock",
            "gate_results": gate_results,
            "opened_locks": sorted(opened_locks),
            "pass": all(item.get("unlocked") for item in gate_results),
        }
    )

    reward_entries = by_kind.get("reward_chest", []) + by_kind.get("exit_unlock_reward", [])
    steps.append(
        {
            "step": "reward_contracts_available",
            "reward_count": len(reward_entries),
            "reward_chest_count": len(by_kind.get("reward_chest", [])),
            "exit_unlock_reward_count": len(by_kind.get("exit_unlock_reward", [])),
            "pass": len(reward_entries) >= 1,
        }
    )

    encounter_entries = by_kind.get("enemy_spawn", []) + by_kind.get("boss_spawn", [])
    steps.append(
        {
            "step": "encounter_spawns_available",
            "enemy_spawn_count": len(by_kind.get("enemy_spawn", [])),
            "boss_spawn_count": len(by_kind.get("boss_spawn", [])),
            "pass": len(by_kind.get("enemy_spawn", [])) >= 1 and len(by_kind.get("boss_spawn", [])) == 1,
        }
    )

    exit_entries = by_kind.get("exit_activation", [])
    exit_ready = bool(exit_entries and (not by_kind.get("locked_gate") or opened_locks) and len(by_kind.get("boss_spawn", [])) == 1)
    steps.append(
        {
            "step": "exit_activation_ready",
            "exit_count": len(exit_entries),
            "required_locks_open": sorted(opened_locks),
            "pass": exit_ready,
        }
    )

    pass_value = bool(contract.get("pass") and all(step.get("pass") for step in steps))
    report = {
        "schema": "cubeless_pcg_dungeon_gameplay_flow_simulation_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "interaction_contract_path": GAMEPLAY_INTERACTION_CONTRACT_PATH,
        "policy": (
            "C++-free gameplay flow simulation. This validates the interaction contract order and linkage without running PIE "
            "or claiming final Blueprint behavior."
        ),
        "contract_pass": bool(contract.get("pass")),
        "contract_entry_count": len(entries),
        "inventory_keys_after_simulation": sorted(inventory_keys),
        "opened_locks_after_simulation": sorted(opened_locks),
        "consumed_contracts": consumed_contracts,
        "activated_contracts": activated_contracts,
        "steps": steps,
        "report_path": GAMEPLAY_FLOW_SIMULATION_REPORT_PATH,
        "pass": pass_value,
    }
    _write_gameplay_flow_simulation_report(report)
    unreal.log(
        "CubelessDungeonPCG gameplay flow simulation: "
        + json.dumps(
            {
                "pass": pass_value,
                "contract_entry_count": len(entries),
                "opened_locks": sorted(opened_locks),
                "keys": sorted(inventory_keys),
            },
            ensure_ascii=False,
        )
    )
    return report


def _write_gameplay_state_event_validation_report(report):
    os.makedirs(os.path.dirname(GAMEPLAY_STATE_EVENT_VALIDATION_REPORT_PATH), exist_ok=True)
    with open(GAMEPLAY_STATE_EVENT_VALIDATION_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _get_actor_editor_property(actor, property_name, default_value=None):
    try:
        return actor.get_editor_property(property_name)
    except Exception:
        return default_value


def _actor_state_snapshot(actor):
    if not actor:
        return {}
    snapshot = {
        "InteractionState": _get_actor_editor_property(actor, "InteractionState"),
        "bInteractionReady": _get_actor_editor_property(actor, "bInteractionReady"),
        "bInteractionConsumed": _get_actor_editor_property(actor, "bInteractionConsumed"),
    }
    try:
        linked_gate = actor.get_editor_property("LinkedGateActor")
    except Exception:
        linked_gate = None
    if linked_gate:
        try:
            snapshot["LinkedGateActor"] = linked_gate.get_actor_label()
        except Exception:
            snapshot["LinkedGateActor"] = str(linked_gate)
    return snapshot


def _actor_visual_component_visibility(actor):
    if not actor:
        return {"component_found": False, "visible": None}
    try:
        tag_map = _tag_values([str(tag) for tag in list(actor.tags)])
    except Exception:
        tag_map = {}
    spec = GAMEPLAY_PLACEHOLDER_VISUAL_SPECS.get(tag_map.get("DungeonPlaceholderKind"))
    component_name = spec.get("component_name") if spec else None
    result = {"expected_component": component_name, "component_found": False, "visible": None}
    if not component_name:
        return result
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        if component.get_name() != component_name:
            continue
        result["component_found"] = True
        try:
            result["visible"] = bool(component.is_visible())
        except Exception:
            try:
                result["visible"] = bool(component.get_editor_property("visible"))
            except Exception:
                result["visible"] = None
        break
    return result


def _validate_actor_visual_visibility(actor, expected_visible):
    snapshot = _actor_visual_component_visibility(actor)
    return {
        "expected_visible": bool(expected_visible),
        "actual_visible": snapshot.get("visible"),
        "component_found": bool(snapshot.get("component_found")),
        "component_name": snapshot.get("expected_component"),
        "pass": bool(snapshot.get("component_found") and snapshot.get("visible") == bool(expected_visible)),
    }


def _reset_gameplay_placeholder_visual_visibility(visible=True):
    results = []
    for actor in _gameplay_placeholder_actors():
        try:
            label = actor.get_actor_label()
        except Exception:
            label = "<unknown>"
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not component.get_name().startswith("DungeonVisual_"):
                continue
            try:
                component.set_visibility(bool(visible), True)
                results.append(
                    {
                        "actor_label": label,
                        "component_name": component.get_name(),
                        "visible": bool(component.is_visible()),
                        "ok": bool(component.is_visible()) == bool(visible),
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "actor_label": label,
                        "component_name": component.get_name(),
                        "visible": None,
                        "ok": False,
                        "error": str(exc),
                    }
                )
    return results


def _call_actor_state_event(actor, event_name):
    if not actor:
        return {"event": event_name, "ok": False, "error": "missing actor"}
    try:
        actor.call_method(event_name)
        return {"event": event_name, "ok": True}
    except Exception as exc:
        return {"event": event_name, "ok": False, "error": str(exc)}


def _validate_actor_state(actor, expected_state, expected_ready, expected_consumed):
    snapshot = _actor_state_snapshot(actor)
    return {
        "expected_state": expected_state,
        "actual_state": snapshot.get("InteractionState"),
        "expected_ready": expected_ready,
        "actual_ready": snapshot.get("bInteractionReady"),
        "expected_consumed": expected_consumed,
        "actual_consumed": snapshot.get("bInteractionConsumed"),
        "pass": bool(
            snapshot.get("InteractionState") == expected_state
            and snapshot.get("bInteractionReady") == expected_ready
            and snapshot.get("bInteractionConsumed") == expected_consumed
        ),
    }


def validate_gameplay_blueprint_state_events(save_dirty_packages=True):
    start_contract = build_gameplay_interaction_contract(save_dirty_packages=save_dirty_packages)
    initial_visual_reset = _reset_gameplay_placeholder_visual_visibility(True)
    actor_map = _actor_by_label_map()
    entries = start_contract.get("contracts", [])
    by_kind = {}
    for entry in entries:
        by_kind.setdefault(entry.get("interaction_kind"), []).append(entry)

    event_specs = [
        ("reward_chest", "DungeonOpenReward", "opened", False, True, False),
        ("exit_unlock_reward", "DungeonOpenReward", "opened", False, True, False),
        ("shop_open", "DungeonOpenShop", "open", True, False, True),
        ("exit_activation", "DungeonActivateExit", "active", True, False, True),
        ("exit_activation", "DungeonUseExit", "completed", False, True, False),
        ("enemy_spawn", "DungeonSpawnEnemy", "spawned", False, True, False),
        ("boss_spawn", "DungeonSpawnBoss", "boss_spawned", False, True, False),
    ]
    event_results = []
    validation_failures = []
    visual_validation_failures = []

    key_results = []
    for key_entry in by_kind.get("key_pickup", []):
        key_actor = actor_map.get(key_entry.get("actor_label"))
        linked_gate_actor = _get_actor_editor_property(key_actor, "LinkedGateActor") if key_actor else None
        result = {
            "actor_label": key_entry.get("actor_label"),
            "event": "DungeonInteract",
            "before": {
                "key": _actor_state_snapshot(key_actor),
                "linked_gate": _actor_state_snapshot(linked_gate_actor),
            },
        }
        result["call"] = _call_actor_state_event(key_actor, "DungeonInteract")
        result["after"] = {
            "key": _actor_state_snapshot(key_actor),
            "linked_gate": _actor_state_snapshot(linked_gate_actor),
        }
        key_validation = _validate_actor_state(key_actor, "consumed", False, True)
        gate_validation = _validate_actor_state(linked_gate_actor, "unlocked", True, False)
        key_visual_validation = _validate_actor_visual_visibility(key_actor, False)
        gate_visual_validation = _validate_actor_visual_visibility(linked_gate_actor, False)
        result["key_validation"] = key_validation
        result["linked_gate_validation"] = gate_validation
        result["key_visual_validation"] = key_visual_validation
        result["linked_gate_visual_validation"] = gate_visual_validation
        result["pass"] = bool(
            result["call"].get("ok")
            and key_validation.get("pass")
            and gate_validation.get("pass")
            and key_visual_validation.get("pass")
            and gate_visual_validation.get("pass")
        )
        key_results.append(result)
        if not result["pass"]:
            validation_failures.append(
                {
                    "actor_label": key_entry.get("actor_label"),
                    "event": "DungeonInteract",
                    "reason": "key-to-gate state validation failed",
                }
            )
            if not key_visual_validation.get("pass") or not gate_visual_validation.get("pass"):
                visual_validation_failures.append(
                    {
                        "actor_label": key_entry.get("actor_label"),
                        "event": "DungeonInteract",
                        "reason": "key-to-gate visual validation failed",
                    }
                )

    for gate_entry in by_kind.get("locked_gate", []):
        gate_actor = actor_map.get(gate_entry.get("actor_label"))
        call_result = _call_actor_state_event(gate_actor, "DungeonUnlockGate")
        state_validation = _validate_actor_state(gate_actor, "unlocked", True, False)
        visual_validation = _validate_actor_visual_visibility(gate_actor, False)
        result = {
            "actor_label": gate_entry.get("actor_label"),
            "interaction_kind": "locked_gate",
            "event": "DungeonUnlockGate",
            "call": call_result,
            "state_validation": state_validation,
            "visual_validation": visual_validation,
            "pass": bool(call_result.get("ok") and state_validation.get("pass") and visual_validation.get("pass")),
        }
        event_results.append(result)
        if not result["pass"]:
            validation_failures.append(
                {
                    "actor_label": gate_entry.get("actor_label"),
                    "event": "DungeonUnlockGate",
                    "reason": "state validation failed",
                }
            )
            if not visual_validation.get("pass"):
                visual_validation_failures.append(
                    {
                        "actor_label": gate_entry.get("actor_label"),
                        "event": "DungeonUnlockGate",
                        "reason": "visual validation failed",
                    }
                )

    for interaction_kind, event_name, expected_state, expected_ready, expected_consumed, expected_visible in event_specs:
        for entry in by_kind.get(interaction_kind, []):
            actor = actor_map.get(entry.get("actor_label"))
            call_result = _call_actor_state_event(actor, event_name)
            state_validation = _validate_actor_state(actor, expected_state, expected_ready, expected_consumed)
            visual_validation = _validate_actor_visual_visibility(actor, expected_visible)
            result = {
                "actor_label": entry.get("actor_label"),
                "interaction_kind": interaction_kind,
                "event": event_name,
                "call": call_result,
                "state_validation": state_validation,
                "visual_validation": visual_validation,
                "pass": bool(call_result.get("ok") and state_validation.get("pass") and visual_validation.get("pass")),
            }
            event_results.append(result)
            if not result["pass"]:
                validation_failures.append(
                    {
                        "actor_label": entry.get("actor_label"),
                        "event": event_name,
                        "reason": "state validation failed",
                    }
                )
                if not visual_validation.get("pass"):
                    visual_validation_failures.append(
                        {
                            "actor_label": entry.get("actor_label"),
                            "event": event_name,
                            "reason": "visual validation failed",
                        }
                    )

    reset_contract = build_gameplay_interaction_contract(save_dirty_packages=save_dirty_packages)
    final_visual_reset = _reset_gameplay_placeholder_visual_visibility(True)
    reset_actor_map = _actor_by_label_map()
    reset_failures = []
    visual_reset_failures = [item for item in initial_visual_reset + final_visual_reset if not item.get("ok")]
    for entry in reset_contract.get("contracts", []):
        actor = reset_actor_map.get(entry.get("actor_label"))
        expected_state = entry.get("interaction_state")
        state_validation = _validate_actor_state(
            actor,
            expected_state,
            expected_state not in ("disabled", "consumed"),
            False,
        )
        if not state_validation.get("pass"):
            reset_failures.append(
                {
                    "actor_label": entry.get("actor_label"),
                    "expected_state": expected_state,
                    "state_validation": state_validation,
                }
            )

    pass_value = bool(
        start_contract.get("pass")
        and reset_contract.get("pass")
        and not validation_failures
        and not visual_validation_failures
        and not reset_failures
        and not visual_reset_failures
        and key_results
        and event_results
    )
    report = {
        "schema": "cubeless_pcg_dungeon_gameplay_state_event_validation_v1",
        "status": "passed" if pass_value else "failed",
        "level_path": LEVEL_PATH,
        "interaction_contract_path": GAMEPLAY_INTERACTION_CONTRACT_PATH,
        "policy": (
            "C++-free Blueprint state event validation. This calls live placeholder Blueprint custom events in the editor, "
            "checks state variable results, then rebuilds the interaction contract to restore placeholder instance state."
        ),
        "start_contract_pass": bool(start_contract.get("pass")),
        "reset_contract_pass": bool(reset_contract.get("pass")),
        "initial_visual_reset": initial_visual_reset,
        "final_visual_reset": final_visual_reset,
        "key_event_results": key_results,
        "event_results": event_results,
        "validation_failures": validation_failures,
        "visual_validation_failures": visual_validation_failures,
        "reset_failures": reset_failures,
        "visual_reset_failures": visual_reset_failures,
        "event_result_count": len(event_results),
        "key_event_result_count": len(key_results),
        "report_path": GAMEPLAY_STATE_EVENT_VALIDATION_REPORT_PATH,
        "pass": pass_value,
    }
    _write_gameplay_state_event_validation_report(report)
    unreal.log(
        "CubelessDungeonPCG gameplay state event validation: "
        + json.dumps(
            {
                "pass": pass_value,
                "key_event_result_count": len(key_results),
                "event_result_count": len(event_results),
                "validation_failures": len(validation_failures),
                "reset_failures": len(reset_failures),
            },
            ensure_ascii=False,
        )
    )
    return report


def _write_native_integration_preview_report(report):
    os.makedirs(os.path.dirname(NATIVE_INTEGRATION_PREVIEW_REPORT_PATH), exist_ok=True)
    with open(NATIVE_INTEGRATION_PREVIEW_REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report


def _load_native_integration_preview_report():
    if os.path.exists(NATIVE_INTEGRATION_PREVIEW_REPORT_PATH):
        with open(NATIVE_INTEGRATION_PREVIEW_REPORT_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _bounds_for_generated_static_mesh_actors():
    found = False
    min_x = min_y = min_z = 0.0
    max_x = max_y = max_z = 0.0
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            label = actor.get_actor_label()
        except Exception:
            continue
        if not label.startswith(ACTOR_PREFIX):
            continue
        if not actor.get_component_by_class(unreal.StaticMeshComponent):
            continue
        try:
            origin, extent = actor.get_actor_bounds(False)
        except Exception:
            continue
        actor_min = (origin.x - extent.x, origin.y - extent.y, origin.z - extent.z)
        actor_max = (origin.x + extent.x, origin.y + extent.y, origin.z + extent.z)
        if not found:
            min_x, min_y, min_z = actor_min
            max_x, max_y, max_z = actor_max
            found = True
        else:
            min_x = min(min_x, actor_min[0])
            min_y = min(min_y, actor_min[1])
            min_z = min(min_z, actor_min[2])
            max_x = max(max_x, actor_max[0])
            max_y = max(max_y, actor_max[1])
            max_z = max(max_z, actor_max[2])
    if not found:
        return None
    return {"min": [float(min_x), float(min_y), float(min_z)], "max": [float(max_x), float(max_y), float(max_z)]}


def _bounds_for_actor(actor):
    if not actor:
        return None
    try:
        origin, extent = actor.get_actor_bounds(False)
        return {
            "min": [float(origin.x - extent.x), float(origin.y - extent.y), float(origin.z - extent.z)],
            "max": [float(origin.x + extent.x), float(origin.y + extent.y), float(origin.z + extent.z)],
        }
    except Exception:
        return None


def setup_native_preview_side_by_side_review_camera(camera_height=23500.0, y_backoff=3200.0):
    bridge_bounds = _bounds_for_generated_static_mesh_actors()
    preview_bounds = _bounds_for_actor(_find_actor_by_label(PCG_NATIVE_INTEGRATION_PREVIEW_LABEL))
    if not bridge_bounds or not preview_bounds:
        return {"success": False, "bridge_bounds": bridge_bounds, "preview_bounds": preview_bounds}
    combined_min = [
        min(bridge_bounds["min"][0], preview_bounds["min"][0]),
        min(bridge_bounds["min"][1], preview_bounds["min"][1]),
        min(bridge_bounds["min"][2], preview_bounds["min"][2]),
    ]
    combined_max = [
        max(bridge_bounds["max"][0], preview_bounds["max"][0]),
        max(bridge_bounds["max"][1], preview_bounds["max"][1]),
        max(bridge_bounds["max"][2], preview_bounds["max"][2]),
    ]
    combined_center = [
        (combined_min[0] + combined_max[0]) * 0.5,
        (combined_min[1] + combined_max[1]) * 0.5,
        (combined_min[2] + combined_max[2]) * 0.5,
    ]
    combined_span = [
        combined_max[0] - combined_min[0],
        combined_max[1] - combined_min[1],
        combined_max[2] - combined_min[2],
    ]
    location = unreal.Vector(float(combined_center[0]), float(combined_center[1] - y_backoff), float(camera_height))
    rotation = _actor_rotator(pitch=-88.0, yaw=90.0)
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(location, rotation)
        success = True
        error = None
    except Exception as exc:
        success = False
        error = str(exc)
    camera = {
        "success": success,
        "error": error,
        "location": [float(location.x), float(location.y), float(location.z)],
        "rotation": [-88.0, 90.0, 0.0],
        "bridge_bounds": bridge_bounds,
        "preview_bounds": preview_bounds,
        "combined_bounds": {"min": combined_min, "max": combined_max, "span": combined_span, "center": combined_center},
        "camera_height": float(camera_height),
        "y_backoff": float(y_backoff),
    }
    report = _load_native_integration_preview_report()
    report.setdefault("screenshot", {})["review_side_by_side_camera"] = camera
    _write_native_integration_preview_report(report)
    return camera


def begin_native_integration_preview(preview_offset=None, keep_existing=False):
    ensure_dirs()
    create_or_update_validation_level()
    if preview_offset is None:
        preview_offset = [14000.0, 0.0, 0.0]
    preview_offset = _vector3_list(preview_offset, [14000.0, 0.0, 0.0])
    preview_graph_setup = create_or_update_native_integration_preview_graphs(preview_offset)
    graph = unreal.load_object(None, NATIVE_INTEGRATION_PREVIEW_GRAPH_PATH + "." + NATIVE_INTEGRATION_PREVIEW_GRAPH_NAME)
    destroy_existing = {"skipped": bool(keep_existing)}
    if not keep_existing:
        destroy_existing = _destroy_actor_by_label(PCG_NATIVE_INTEGRATION_PREVIEW_LABEL)
    pcg_volume_class = getattr(unreal, "PCGVolume", None)
    actor = None
    if pcg_volume_class:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            pcg_volume_class,
            unreal.Vector(float(preview_offset[0]), float(preview_offset[1]), float(preview_offset[2])),
            _actor_rotator(),
        )
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    setup = {
        "graph_loaded": bool(graph),
        "pcg_volume_class_available": bool(pcg_volume_class),
        "actor_created": bool(actor),
        "component_found": bool(component),
        "destroy_existing": destroy_existing,
        "preview_offset": [float(preview_offset[0]), float(preview_offset[1]), float(preview_offset[2])],
    }
    if actor:
        actor.set_actor_label(PCG_NATIVE_INTEGRATION_PREVIEW_LABEL, mark_dirty=True)
        actor.tags = [
            unreal.Name("DungeonNativeIntegrationPreview"),
            unreal.Name("DungeonGraph=NativeIntegrationPreviewOffset"),
            unreal.Name("DungeonOutputPolicy=PreviewKeepGenerated"),
            unreal.Name("DungeonPreviewOffset={:.1f},{:.1f},{:.1f}".format(float(preview_offset[0]), float(preview_offset[1]), float(preview_offset[2]))),
        ]
    if component and graph:
        try:
            component.set_graph(graph)
            setup["set_graph"] = graph.get_path_name()
        except Exception as exc:
            setup["set_graph_error"] = str(exc)
        try:
            component.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
            setup["generation_trigger"] = str(component.get_editor_property("generation_trigger"))
        except Exception as exc:
            setup["generation_trigger_error"] = str(exc)
        try:
            component.set_editor_property("input_type", unreal.PCGComponentInput.ACTOR)
            setup["input_type"] = str(component.get_editor_property("input_type"))
        except Exception as exc:
            setup["input_type_error"] = str(exc)

    cleanup_before = _call_pcg_component_method(component, "cleanup") if component else {"ok": False, "error": "missing component"}
    generate = _call_pcg_component_method(component, "generate") if component else {"ok": False, "error": "missing component"}
    report = {
        "schema": "cubeless_pcg_dungeon_native_integration_preview_v1",
        "status": "generation_requested",
        "level_path": LEVEL_PATH,
        "actor_label": PCG_NATIVE_INTEGRATION_PREVIEW_LABEL,
        "actor_path": actor.get_path_name() if actor else None,
        "graph_path": graph.get_path_name() if graph else NATIVE_INTEGRATION_PREVIEW_GRAPH_PATH,
        "graph_role": "preview_offset",
        "preview_offset": preview_offset,
        "preview_graph_setup": preview_graph_setup,
        "setup": setup,
        "expected_runtime_counts": _native_integration_expected_runtime_counts(),
        "cleanup_before_generation": cleanup_before,
        "generate_request": generate,
        "generation_verification": {},
        "screenshot": {},
        "cleanup_policy": "Preview output is intentionally kept generated until cleanup_native_integration_preview() is called.",
        "pass": False,
    }
    _write_native_integration_preview_report(report)
    unreal.log(
        "CubelessDungeonPCG native integration preview begin: "
        + json.dumps(
            {
                "actor_created": setup["actor_created"],
                "generate_request_ok": generate.get("ok"),
                "preview_offset": setup["preview_offset"],
            },
            ensure_ascii=False,
        )
    )
    return report


def verify_native_integration_preview_generation():
    report = _load_native_integration_preview_report()
    actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_PREVIEW_LABEL)
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    expected = _native_integration_expected_runtime_counts()
    component_summary = _actor_static_mesh_component_summary(actor)
    try:
        generated_attr = bool(component.generated) if component else False
    except Exception:
        generated_attr = False
    generation_verification = {
        "actor_found": bool(actor),
        "component_found": bool(component),
        "generated_attr": generated_attr,
        "component_summary": component_summary,
        "expected_static_mesh_component_count": expected["static_mesh_component_count"],
        "expected_static_mesh_instance_count": expected["static_mesh_instance_count"],
    }
    generation_verification["pass"] = bool(
        actor
        and component
        and generated_attr
        and int(component_summary.get("component_count", 0)) == expected["static_mesh_component_count"]
        and int(component_summary.get("instance_count_total", 0)) == expected["static_mesh_instance_count"]
    )
    report.update(
        {
            "schema": "cubeless_pcg_dungeon_native_integration_preview_v1",
            "status": "generated" if generation_verification["pass"] else "generation_failed",
            "level_path": LEVEL_PATH,
            "actor_label": PCG_NATIVE_INTEGRATION_PREVIEW_LABEL,
            "expected_runtime_counts": expected,
            "generation_verification": generation_verification,
            "pass": bool(generation_verification["pass"]),
        }
    )
    _write_native_integration_preview_report(report)
    unreal.log(
        "CubelessDungeonPCG native integration preview generation: "
        + json.dumps(
            {
                "pass": report["pass"],
                "component_count": component_summary.get("component_count"),
                "instance_count_total": component_summary.get("instance_count_total"),
            },
            ensure_ascii=False,
        )
    )
    return report


def cleanup_native_integration_preview(destroy_actor=False):
    actor = _find_actor_by_label(PCG_NATIVE_INTEGRATION_PREVIEW_LABEL)
    component = actor.get_component_by_class(unreal.PCGComponent) if actor else None
    cleanup = _call_pcg_component_method(component, "cleanup") if component else {"ok": False, "error": "missing component"}
    destroyed = False
    destroy_error = None
    if destroy_actor and actor:
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            destroyed = True
        except Exception as exc:
            destroy_error = str(exc)
    report = _load_native_integration_preview_report()
    report.update(
        {
            "status": "cleanup_requested",
            "cleanup_request": cleanup,
            "destroy_actor_requested": bool(destroy_actor),
            "destroyed": destroyed,
            "destroy_error": destroy_error,
            "pass": False,
        }
    )
    _write_native_integration_preview_report(report)
    return report


def spawn_or_update_pcg_bridge_actor(graph):
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        try:
            if actor.get_actor_label() == PCG_BRIDGE_LABEL:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        except Exception:
            pass

    pcg_volume_class = getattr(unreal, "PCGVolume", None)
    if not pcg_volume_class:
        return {"created": False, "error": "unreal.PCGVolume class unavailable"}
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        pcg_volume_class,
        unreal.Vector(0, 0, 0),
        _actor_rotator(),
    )
    if not actor:
        return {"created": False, "error": "Failed to spawn PCGVolume"}
    actor.set_actor_label(PCG_BRIDGE_LABEL, mark_dirty=True)
    actor.tags = [unreal.Name(tag) for tag in _default_config_tags()]
    component = actor.get_component_by_class(unreal.PCGComponent)
    if component:
        component.set_graph(graph)
        try:
            component.set_editor_property("generate_on_drop", False)
        except Exception:
            pass
        try:
            component.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
        except Exception:
            pass
    return {
        "created": True,
        "actor_label": actor.get_actor_label(),
        "config_tags": [str(tag) for tag in actor.tags],
        "pcg_component": component.get_name() if component else None,
        "graph": graph.get_path_name(),
    }


def build_all():
    ensure_dirs()
    module_assets = build_module_assets()
    graph_report = create_or_update_pcg_bridge_graph()
    graph = unreal.load_object(None, GRAPH_PATH + "." + GRAPH_NAME)
    level_report = create_or_update_validation_level()
    bridge_report = spawn_or_update_pcg_bridge_actor(graph)
    config = _parse_dungeon_config_from_actor(_find_pcg_bridge_actor())
    dungeon_report = spawn_validation_dungeon(source="setup_direct", config=config)
    native_point_source_graph_report = create_or_update_native_point_source_graph()
    native_skeleton_report = create_or_update_native_skeleton_graph()
    native_skeleton_audit = audit_native_skeleton_graph()
    native_integration_report = create_or_update_native_integration_graph(
        native_point_source_graph_report=native_point_source_graph_report,
    )
    native_integration_audit = audit_native_integration_graph()
    native_integration_test = create_or_update_native_integration_test_actor()
    seed_suite_report = run_seed_suite(room_count=config["room_count"], config=config)
    save_level_result = None
    try:
        save_level_result = bool(unreal.EditorLevelLibrary.save_current_level())
    except Exception as exc:
        save_level_result = "failed: " + str(exc)
    try:
        save_dirty_result = bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
    except Exception as exc:
        save_dirty_result = "failed: " + str(exc)
    final_report = {
        "root": ROOT,
        "module_asset_count": len(module_assets),
        "module_assets": {key: mesh.get_path_name() for key, mesh in module_assets.items()},
        "graph": graph_report,
        "level": level_report,
        "bridge_actor": bridge_report,
        "dungeon": dungeon_report,
        "native_point_source_graph": native_point_source_graph_report,
        "native_skeleton_graph": native_skeleton_report,
        "native_skeleton_audit": native_skeleton_audit,
        "native_integration_graph": native_integration_report,
        "native_integration_audit": native_integration_audit,
        "native_integration_test_actor": native_integration_test,
        "seed_suite": seed_suite_report,
        "save_current_level": save_level_result,
        "save_dirty_packages": save_dirty_result,
        "report_path": REPORT_PATH,
        "seed_suite_report_path": SEED_SUITE_REPORT_PATH,
        "native_point_source_report_path": NATIVE_POINT_SOURCE_REPORT_PATH,
        "native_point_source_graph_report_path": NATIVE_POINT_SOURCE_GRAPH_REPORT_PATH,
        "native_skeleton_graph_report_path": NATIVE_GRAPH_REPORT_PATH,
        "native_skeleton_audit_report_path": NATIVE_GRAPH_AUDIT_REPORT_PATH,
        "native_integration_graph_report_path": NATIVE_INTEGRATION_GRAPH_REPORT_PATH,
        "native_integration_audit_report_path": NATIVE_INTEGRATION_AUDIT_REPORT_PATH,
        "native_integration_test_actor_report_path": NATIVE_INTEGRATION_TEST_ACTOR_REPORT_PATH,
        "native_integration_smoke_report_path": NATIVE_INTEGRATION_TEST_REPORT_PATH,
        "pass": bool(
            dungeon_report.get("pass")
            and seed_suite_report.get("pass")
            and native_point_source_graph_report.get("pass")
            and native_skeleton_report.get("pass")
            and native_skeleton_audit.get("pass")
            and native_integration_report.get("pass")
            and native_integration_audit.get("pass")
            and native_integration_test.get("pass")
            and bridge_report.get("created")
        ),
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(final_report, handle, indent=2, ensure_ascii=False)
    unreal.log("CubelessDungeonPCG build_all report: " + json.dumps(final_report, ensure_ascii=False))
    return final_report


def main():
    return build_all()
