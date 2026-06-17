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

V2_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
V2_ENTRYPOINT_PATH = os.path.join(V2_SCRIPT_DIR, "CubelessDungeonPCGV2Entrypoint.py")
V2_REPORT_DIR_NAME = "MCP_DungeonV2"
V2_REPORT_PREFIX = "CubelessDungeonV2"
V2_CORE_OUTPUT_EXCLUDED_MODULES = {
    "marker",
    "room_variant_detail",
    "detail_mesh",
}
V2_OUTPUT_POLICY = {
    "mode": "core_structure_output",
    "excluded_modules": sorted(V2_CORE_OUTPUT_EXCLUDED_MODULES),
    "reason": (
        "V2 keeps room-rule and gameplay marker data in reports, but excludes semantic floor "
        "markers and room-detail meshes from the default Native PCG structure output."
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


@contextlib.contextmanager
def v2_context(core_output_only=True):
    overrides = _v2_overrides()
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
        actor = dungeon._find_pcg_bridge_actor()
        config = dungeon._parse_dungeon_config_from_actor(actor)
        report = dungeon.spawn_validation_dungeon(source="pcg_bridge_v2", config=config)
        unreal.log("CubelessDungeonPCGV2Entrypoint report: {}".format(report.get("pass")))
        return report


def build_all():
    with v2_context() as dungeon:
        report = dungeon.build_all()
    return _write_v2_wrapper_report("BuildAll", report)


def begin_generation_refresh_from_bridge(keep_existing_output=False):
    with v2_context() as dungeon:
        return dungeon.begin_pcg_generation_refresh_from_bridge(keep_existing_output=keep_existing_output)


def begin_generation_refresh_with_authoring_preset(
    preset_name="default",
    keep_existing_output=False,
    save_dirty_packages=True,
):
    with v2_context() as dungeon:
        return dungeon.begin_pcg_generation_refresh_with_authoring_preset(
            preset_name=preset_name,
            keep_existing_output=keep_existing_output,
            save_dirty_packages=save_dirty_packages,
        )


def verify_generation_refresh(enable_output_only_review=True, save_dirty_packages=True):
    with v2_context() as dungeon:
        return dungeon.verify_pcg_generation_refresh(
            enable_output_only_review=enable_output_only_review,
            save_dirty_packages=save_dirty_packages,
        )


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


def record_generation_final_gate():
    with v2_context() as dungeon:
        return dungeon.record_pcg_generation_final_gate()


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
