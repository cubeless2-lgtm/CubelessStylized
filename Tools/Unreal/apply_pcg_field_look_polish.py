"""Apply a fast visual look polish pass to the Cubeless PCG field level.

This pass intentionally avoids regenerating every PCG actor. It keeps the
existing PCG instance components, reduces test-marker-looking plants/flowers,
and tunes the terrain/road materials so validation cameras read as a forest
road rather than scattered samples on a brown test floor.
"""

import json
import math
import os
import time

import unreal


REPORT_NAME = "CubelessFieldLookPolish_Report.json"
BLOCK_TAG_TOKEN = "block"

GRASS_BALANCED_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_GrassMedium_ForestBalanced"
)
FLOWER_BALANCED_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_FlowerYellow_ForestBalanced"
)
ROCK_MUTED_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "M_Cubeless_PCG_Rock_MutedVisualQA"
)

MATERIAL_SPECS = {
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Duff": {
        "base": (0.085, 0.128, 0.046, 1.0),
        "roughness": 0.98,
        "specular": 0.02,
        "emissive": (0.009, 0.014, 0.004, 1.0),
    },
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Core": {
        "base": (0.205, 0.132, 0.062, 1.0),
        "roughness": 0.96,
        "specular": 0.015,
        "emissive": (0.012, 0.007, 0.003, 1.0),
    },
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Shoulder": {
        "base": (0.145, 0.132, 0.062, 1.0),
        "roughness": 0.98,
        "specular": 0.015,
        "emissive": (0.008, 0.007, 0.003, 1.0),
    },
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_RoadSurface_CoreVisual": {
        "base": (0.220, 0.142, 0.066, 1.0),
        "roughness": 0.97,
        "specular": 0.012,
        "emissive": (0.013, 0.008, 0.003, 1.0),
    },
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_RoadSurface_ShoulderVisual": {
        "base": (0.150, 0.135, 0.066, 1.0),
        "roughness": 0.98,
        "specular": 0.012,
        "emissive": (0.008, 0.007, 0.003, 1.0),
    },
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestFloor_VisualQA": {
        "base": (0.074, 0.118, 0.039, 1.0),
        "roughness": 0.98,
        "specular": 0.02,
        "emissive": (0.008, 0.012, 0.003, 1.0),
    },
    ROCK_MUTED_MATERIAL: {
        "base": (0.300, 0.270, 0.190, 1.0),
        "roughness": 0.96,
        "specular": 0.025,
        "emissive": (0.006, 0.005, 0.003, 1.0),
    },
}

ROAD_POINTS = [
    (4740.5, 10249.0),
    (11204.9, 12049.1),
    (17281.7, 16363.3),
    (23407.1, 20512.5),
    (29277.9, 25104.5),
    (35071.3, 29853.7),
    (40847.3, 34671.2),
    (46419.2, 39919.5),
]


def _road_segments():
    segments = []
    for index in range(len(ROAD_POINTS) - 1):
        ax, ay = ROAD_POINTS[index]
        bx, by = ROAD_POINTS[index + 1]
        dx = bx - ax
        dy = by - ay
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0.0:
            segments.append((ax, ay, dx, dy, length))
    return segments


ROAD_SEGMENTS = _road_segments()


def _road_distance(x, y):
    best = 10**12
    for ax, ay, dx, dy, length in ROAD_SEGMENTS:
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (length * length)))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best


def _stable_hash(*parts):
    value = 2166136261
    for part in parts:
        for char in str(part):
            value ^= ord(char)
            value = (value * 16777619) & 0xFFFFFFFF
    return value


def _component_tags(component):
    try:
        return [str(tag) for tag in component.get_editor_property("component_tags")]
    except Exception:
        return []


def _actor_tags(actor):
    try:
        return [str(tag) for tag in actor.tags]
    except Exception:
        return []


def _tagged_as_block(actor, component=None):
    tags = _actor_tags(actor)
    if component is not None:
        tags.extend(_component_tags(component))
    return any(BLOCK_TAG_TOKEN in tag.lower() for tag in tags)


def _collect_block_bounds():
    bounds = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        actor_has_block_tag = _tagged_as_block(actor)
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not actor_has_block_tag and not _tagged_as_block(actor, component):
                continue
            try:
                origin = component.bounds.origin
                extent = component.bounds.box_extent
            except Exception:
                try:
                    origin = component.get_component_location()
                    extent = unreal.Vector(0.0, 0.0, 0.0)
                except Exception:
                    continue
            try:
                mesh = component.get_editor_property("static_mesh")
            except Exception:
                mesh = None
            bounds.append(
                {
                    "actor": actor.get_actor_label(),
                    "component": component.get_name(),
                    "tags": _actor_tags(actor) + _component_tags(component),
                    "mesh": mesh.get_path_name() if mesh else None,
                    "origin": [float(origin.x), float(origin.y), float(origin.z)],
                    "extent": [float(extent.x), float(extent.y), float(extent.z)],
                }
            )
    return bounds


def _inside_block_bounds(location, block_bounds, margin=180.0):
    for entry in block_bounds or []:
        origin = entry.get("origin") or [0.0, 0.0, 0.0]
        extent = entry.get("extent") or [0.0, 0.0, 0.0]
        if (
            abs(location.x - origin[0]) <= extent[0] + margin
            and abs(location.y - origin[1]) <= extent[1] + margin
        ):
            return True
    return False


def _load_material(path):
    return unreal.EditorAssetLibrary.load_asset(path)


def _create_material(path):
    folder, name = path.rsplit("/", 1)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    return asset_tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())


def _set_flat_material(path, spec):
    material = _load_material(path)
    if not material:
        material = _create_material(path)
    if not material:
        return {"path": path, "applied": False, "reason": "missing_or_create_failed"}
    if material.get_class().get_name() != "Material":
        return {"path": path, "applied": False, "reason": "not_material"}

    try:
        lib = unreal.MaterialEditingLibrary
        lib.delete_all_material_expressions(material)

        base = lib.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -360, -140
        )
        base.set_editor_property("constant", unreal.LinearColor(*spec["base"]))
        lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

        rough = lib.create_material_expression(
            material, unreal.MaterialExpressionConstant, -360, 20
        )
        rough.set_editor_property("r", float(spec["roughness"]))
        lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

        specular = lib.create_material_expression(
            material, unreal.MaterialExpressionConstant, -360, 170
        )
        specular.set_editor_property("r", float(spec["specular"]))
        lib.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)

        if spec.get("emissive"):
            emissive = lib.create_material_expression(
                material, unreal.MaterialExpressionConstant3Vector, -360, 320
            )
            emissive.set_editor_property("constant", unreal.LinearColor(*spec["emissive"]))
            lib.connect_material_property(
                emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
            )

        lib.layout_material_expressions(material)
        lib.recompile_material(material)
        unreal.EditorAssetLibrary.save_asset(path)
        return {"path": path, "applied": True}
    except Exception as exc:
        return {"path": path, "applied": False, "reason": str(exc)}


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return ""


def _classify(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(token in text for token in ["tree", "pine", "spruce", "conifer", "trunk"]):
        return "tree"
    if any(token in text for token in ["rock", "stone", "boulder"]):
        return "rock"
    if "flower" in text:
        return "flower"
    if any(token in text for token in ["fern", "leaf", "leaves", "plant"]):
        return "plant"
    if "grass" in text:
        return "grass"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _set_visible(component, visible):
    try:
        component.set_visibility(visible, True)
    except Exception:
        pass
    try:
        component.set_hidden_in_game(not visible)
    except Exception:
        pass
    try:
        component.set_editor_property("visible", visible)
    except Exception:
        pass
    try:
        component.mark_render_state_dirty()
    except Exception:
        pass


def _component_origin_distance(actor, component):
    try:
        origin = component.bounds.origin
    except Exception:
        origin = actor.get_actor_location()
    return _road_distance(origin.x, origin.y)


def _apply_component_look(block_bounds):
    grass_material = _load_material(GRASS_BALANCED_MATERIAL)
    flower_material = _load_material(FLOWER_BALANCED_MATERIAL)
    rock_material = _load_material(ROCK_MUTED_MATERIAL)
    summary = {
        "components": {"grass": 0, "flower": 0, "plant": 0, "tree": 0, "rock": 0, "other": 0},
        "instances": {"grass": 0, "flower": 0, "plant": 0, "tree": 0, "rock": 0, "other": 0},
        "grass_material_overrides": 0,
        "flower_material_overrides": 0,
        "hidden_plant_components": 0,
        "hidden_flower_components": 0,
        "kept_flower_components": 0,
        "hidden_road_preview_rock_components": 0,
        "rock_material_overrides": 0,
        "block_overlap_violations": 0,
        "block_overlap_samples": [],
    }

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not (
            label.startswith("MCP_PCG_")
            or label.startswith("MCP_TMP_NativeRoadPCGValidation")
        ):
            continue

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _classify(component)
            count = _instance_count(component)
            summary["components"][category] = summary["components"].get(category, 0) + 1
            summary["instances"][category] = summary["instances"].get(category, 0) + count

            if category == "grass":
                _set_visible(component, True)
                if grass_material:
                    try:
                        component.set_material(0, grass_material)
                        summary["grass_material_overrides"] += 1
                    except Exception:
                        pass
                continue

            if category == "plant":
                _set_visible(component, False)
                summary["hidden_plant_components"] += 1
                continue

            if category == "flower":
                _set_visible(component, False)
                summary["hidden_flower_components"] += 1
                continue

            if category == "rock" and rock_material:
                if label.startswith("MCP_TMP_NativeRoadPCGValidation"):
                    _set_visible(component, False)
                    summary["hidden_road_preview_rock_components"] += 1
                    continue
                try:
                    slot_count = max(1, int(component.get_num_materials()))
                    for slot_index in range(slot_count):
                        component.set_material(slot_index, rock_material)
                    summary["rock_material_overrides"] += 1
                except Exception:
                    pass

            _set_visible(component, True)

            if not block_bounds or category not in ["tree", "rock", "grass", "flower", "plant"]:
                continue

            # Full block validation is only needed when a block tag exists.
            for index in range(count):
                try:
                    location = component.get_instance_transform(index, True).translation
                except Exception:
                    continue
                if not _inside_block_bounds(location, block_bounds):
                    continue
                summary["block_overlap_violations"] += 1
                if len(summary["block_overlap_samples"]) < 30:
                    summary["block_overlap_samples"].append(
                        {
                            "actor": label,
                            "component": component.get_name(),
                            "category": category,
                            "index": index,
                            "location": [
                                round(location.x, 1),
                                round(location.y, 1),
                                round(location.z, 1),
                            ],
                        }
                    )
    return summary


def _assign_landscape_material():
    material = _load_material("/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestRoad_Duff")
    if not material:
        return {"applied": False, "reason": "missing_forest_duff_material"}
    landscapes = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_class().get_name() != "Landscape":
            continue
        try:
            actor.modify()
            actor.set_editor_property("landscape_material", material)
            landscapes.append(actor.get_actor_label())
        except Exception:
            pass
    return {"applied": bool(landscapes), "landscapes": landscapes}


def apply_field_look_polish():
    material_reports = [
        _set_flat_material(path, spec) for path, spec in MATERIAL_SPECS.items()
    ]
    landscape_report = _assign_landscape_material()
    block_bounds = _collect_block_bounds()
    component_report = _apply_component_look(block_bounds)

    save_report = None
    try:
        unreal.EditorLevelLibrary.save_current_level()
        save_report = True
    except Exception as exc:
        save_report = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
        "policy": {
            "flowers": "sparse accent only; most flower components hidden",
            "plants": "dark fern/groundleaf card meshes hidden for validation cameras",
            "grass": "kept visible and material-balanced",
            "block_tag": "when a StaticMesh actor/component has a tag containing 'block', overlap is reported",
        },
        "materials": material_reports,
        "landscape": landscape_report,
        "block_tagged_component_count": len(block_bounds),
        "block_tagged_components": block_bounds[:40],
        "component_look": component_report,
        "save_current_level": save_report,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    apply_field_look_polish()
