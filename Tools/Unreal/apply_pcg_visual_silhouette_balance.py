"""Apply a visual silhouette balance pass to generated Cubeless PCG instances.

This is a level-side stabilization pass for the field QA map. It does not change
the source Dreamscape assets. The goal is to make the generated PCG output read
as a forest from the validation bookmarks instead of as tiny scattered dots.
"""

import json
import math
import os
import random
import time

import unreal


REPORT_NAME = "CubelessPCGVisualSilhouetteBalance_Report.json"

FOREST_FLOOR_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/M_Cubeless_PCG_ForestFloor_VisualQA"
)
FLOWER_BALANCED_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_FlowerYellow_ForestBalanced"
)
GRASS_BALANCED_MATERIAL = (
    "/Game/Cubeless/PCG/Runtime/Materials/"
    "MI_Cubeless_PCG_GrassMedium_ForestBalanced"
)

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


def _stable_rng(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return random.Random(seed)


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


def _clamp_angle(value, limit=5.0):
    while value > 180.0:
        value -= 360.0
    while value < -180.0:
        value += 360.0
    return max(-limit, min(limit, value))


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _target_scale(category, road_distance, rng):
    if category == "tree":
        if road_distance < 3500.0:
            s = rng.uniform(1.10, 1.45)
        elif road_distance < 5200.0:
            s = rng.uniform(1.45, 2.10)
        else:
            s = rng.uniform(1.90, 3.10)
        return unreal.Vector(s, s, s * rng.uniform(1.00, 1.18))

    if category == "grass":
        return unreal.Vector(
            rng.uniform(2.20, 3.60),
            rng.uniform(2.20, 3.60),
            rng.uniform(1.35, 2.15),
        )

    if category == "plant":
        s = rng.uniform(1.45, 2.35)
        return unreal.Vector(s, s, s * rng.uniform(0.90, 1.20))

    if category == "flower":
        s = rng.uniform(0.42, 0.82)
        return unreal.Vector(s, s, s)

    if category == "rock":
        s = rng.uniform(0.50, 4.00)
        return unreal.Vector(s, s, s * rng.uniform(0.75, 1.15))

    return None


def _apply_forest_floor_material():
    material = unreal.EditorAssetLibrary.load_asset(FOREST_FLOOR_MATERIAL)
    if not material:
        return {"applied": False, "reason": "missing_material"}

    # Keep the material intentionally plain and dark for high-view coverage.
    try:
        mel = unreal.MaterialEditingLibrary
        mel.delete_all_material_expressions(material)
        base = mel.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -300, -80
        )
        base.set_editor_property("constant", unreal.LinearColor(0.028, 0.043, 0.018, 1.0))
        mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

        rough = mel.create_material_expression(
            material, unreal.MaterialExpressionConstant, -300, 100
        )
        rough.set_editor_property("r", 0.96)
        mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

        spec = mel.create_material_expression(
            material, unreal.MaterialExpressionConstant, -300, 220
        )
        spec.set_editor_property("r", 0.02)
        mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
        mel.recompile_material(material)
        unreal.EditorAssetLibrary.save_asset(FOREST_FLOOR_MATERIAL)
    except Exception as exc:
        return {"applied": False, "reason": "material_rebuild_failed", "error": str(exc)}

    landscapes = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_class().get_name() != "Landscape":
            continue
        actor.modify()
        actor.set_editor_property("landscape_material", material)
        landscapes.append(actor.get_actor_label())

    return {"applied": True, "landscapes": landscapes}


def _apply_component_material_balance(component, category):
    changed = False
    if category == "grass":
        material = unreal.EditorAssetLibrary.load_asset(GRASS_BALANCED_MATERIAL)
        if material:
            component.set_material(0, material)
            changed = True
    elif category == "flower":
        material = unreal.EditorAssetLibrary.load_asset(FLOWER_BALANCED_MATERIAL)
        if material:
            component.set_material(0, material)
            changed = True
    return changed


def apply_visual_silhouette_balance():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    floor_report = _apply_forest_floor_material()

    report = {
        "timestamp": started,
        "forest_floor": floor_report,
        "components": {"tree": 0, "grass": 0, "plant": 0, "flower": 0, "rock": 0},
        "instances": {"tree": 0, "grass": 0, "plant": 0, "flower": 0, "rock": 0},
        "updated_instances": 0,
        "material_overrides": 0,
        "pitch_roll_violations_after": 0,
        "tree_near_road_after": {"within_1800": 0, "within_2400": 0},
        "rock_near_road_after": {"within_1800": 0, "within_2400": 0},
        "samples": [],
        "failures": [],
    }

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _classify(component)
            if category not in report["components"]:
                continue

            count = _instance_count(component)
            if count <= 0:
                continue

            report["components"][category] += 1
            report["instances"][category] += count
            if _apply_component_material_balance(component, category):
                report["material_overrides"] += 1

            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, False)
                    world_transform = component.get_instance_transform(index, True)
                    world_location = world_transform.translation
                    road_distance = _road_distance(world_location.x, world_location.y)
                    rng = _stable_rng(label, component.get_name(), index, category)
                    scale = _target_scale(category, road_distance, rng)
                    if not scale:
                        continue

                    rotator = transform.rotation.rotator()
                    pitch = _clamp_angle(rotator.pitch)
                    roll = _clamp_angle(rotator.roll)
                    yaw = rotator.yaw
                    if abs(yaw) < 0.01:
                        yaw = rng.uniform(0.0, 360.0)

                    transform.scale3d = scale
                    transform.rotation = _make_rotator(pitch, yaw, roll).quaternion()

                    if component.update_instance_transform(
                        index, transform, False, False, True
                    ):
                        report["updated_instances"] += 1
                        if len(report["samples"]) < 24:
                            report["samples"].append(
                                {
                                    "actor": label,
                                    "component": component.get_name(),
                                    "category": category,
                                    "road_distance": round(road_distance, 1),
                                    "scale": [
                                        round(scale.x, 2),
                                        round(scale.y, 2),
                                        round(scale.z, 2),
                                    ],
                                }
                            )
                except Exception as exc:
                    if len(report["failures"]) < 40:
                        report["failures"].append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "error": str(exc),
                            }
                        )

            try:
                component.mark_render_state_dirty()
            except Exception:
                pass

    # Lightweight post-check for pitch/roll and road safety after scaling.
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not actor.get_actor_label().startswith("MCP_PCG_"):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _classify(component)
            if category not in ["tree", "grass", "plant", "flower", "rock"]:
                continue
            count = _instance_count(component)
            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, False)
                    rotator = transform.rotation.rotator()
                    if abs(_clamp_angle(rotator.pitch) - rotator.pitch) > 0.01:
                        report["pitch_roll_violations_after"] += 1
                    if abs(_clamp_angle(rotator.roll) - rotator.roll) > 0.01:
                        report["pitch_roll_violations_after"] += 1

                    if category not in ["tree", "rock"]:
                        continue
                    location = component.get_instance_transform(index, True).translation
                    distance = _road_distance(location.x, location.y)
                    key = "tree_near_road_after" if category == "tree" else "rock_near_road_after"
                    if distance < 1800.0:
                        report[key]["within_1800"] += 1
                    if distance < 2400.0:
                        report[key]["within_2400"] += 1
                except Exception:
                    pass

    report["failure_count"] = len(report["failures"])
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    apply_visual_silhouette_balance()
