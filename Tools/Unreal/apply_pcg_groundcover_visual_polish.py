"""Polish PCG groundcover visibility after dense landscape generation.

The broad field is grass-dense enough already. Ground-leaf and fern card
meshes read as dark slashes from validation cameras, so they are hidden as
secondary clutter. Yellow flower material is also softened to keep accent
color without neon spots dominating the forest-road composition.
"""

import json
import os
import time

import unreal


REPORT_NAME = "CubelessGroundcoverVisualPolish_Report.json"

TARGET_FOLDER = "/Game/Cubeless/PCG/Runtime/Materials"
YELLOW_SOURCE = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Plants/"
    "MI_Flower_04.MI_Flower_04"
)
YELLOW_TARGET_NAME = "MI_Cubeless_PCG_FlowerYellow_ForestBalanced"
YELLOW_TARGET = f"{TARGET_FOLDER}/{YELLOW_TARGET_NAME}.{YELLOW_TARGET_NAME}"

DARK_PLANT_MESH_TOKENS = [
    "SM_GroundLeaf_01",
    "SM_Fern_01",
]
YELLOW_FLOWER_MESH_TOKEN = "SM_FlowerGroup_01_Yellow"


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return ""


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _load_or_create_yellow_material():
    existing = unreal.load_object(None, YELLOW_TARGET)
    if existing:
        return existing, False

    source = unreal.load_object(None, YELLOW_SOURCE)
    if not source:
        raise RuntimeError("Failed to load source material: " + YELLOW_SOURCE)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.duplicate_asset(YELLOW_TARGET_NAME, TARGET_FOLDER, source)
    if not material:
        raise RuntimeError("Failed to duplicate material instance to " + YELLOW_TARGET)
    return material, True


def _set_yellow_parameters(material):
    lib = unreal.MaterialEditingLibrary
    vector_params = {
        "Color Tint": unreal.LinearColor(0.355, 0.285, 0.035, 1.0),
        "Stem Color": unreal.LinearColor(0.045, 0.082, 0.018, 1.0),
        "Color Gradient 01": unreal.LinearColor(0.82, 0.78, 0.55, 1.0),
        "Color Gradient 02": unreal.LinearColor(0.62, 0.56, 0.22, 1.0),
    }
    scalar_params = {
        "Specular": 0.05,
        "Roughness Amount": 1.0,
        "Virtual Texture Coverage": 0.18,
        "Flatten Normal": 0.35,
    }

    report = {"vectors": {}, "scalars": {}}
    for name, value in vector_params.items():
        try:
            lib.set_material_instance_vector_parameter_value(material, name, value)
            report["vectors"][name] = str(value)
        except Exception as exc:
            report["vectors"][name] = "failed: " + str(exc)
    for name, value in scalar_params.items():
        try:
            lib.set_material_instance_scalar_parameter_value(material, name, value)
            report["scalars"][name] = value
        except Exception as exc:
            report["scalars"][name] = "failed: " + str(exc)
    try:
        lib.update_material_instance(material)
    except Exception:
        pass
    return report


def _set_component_visible(component, visible):
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


def apply_groundcover_visual_polish():
    yellow_material, created = _load_or_create_yellow_material()
    parameter_report = _set_yellow_parameters(yellow_material)

    summary = {
        "dark_plants_hidden": {"components": 0, "instances": 0},
        "yellow_flowers_softened": {"components": 0, "instances": 0},
    }
    samples = []

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh_path = _mesh_path(component)
            count = _instance_count(component)

            if any(token in mesh_path for token in DARK_PLANT_MESH_TOKENS):
                _set_component_visible(component, False)
                summary["dark_plants_hidden"]["components"] += 1
                summary["dark_plants_hidden"]["instances"] += count
                if len(samples) < 40:
                    samples.append(
                        {
                            "actor": label,
                            "component": component.get_name(),
                            "mesh": mesh_path,
                            "action": "hidden",
                            "instances": count,
                        }
                    )
                continue

            if YELLOW_FLOWER_MESH_TOKEN in mesh_path:
                try:
                    component.set_material(0, yellow_material)
                    try:
                        component.mark_render_state_dirty()
                    except Exception:
                        pass
                    summary["yellow_flowers_softened"]["components"] += 1
                    summary["yellow_flowers_softened"]["instances"] += count
                    if len(samples) < 40:
                        samples.append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "mesh": mesh_path,
                                "action": "yellow_material",
                                "instances": count,
                            }
                        )
                except Exception as exc:
                    if len(samples) < 40:
                        samples.append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "mesh": mesh_path,
                                "action": "yellow_material_failed",
                                "error": str(exc),
                            }
                        )

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(yellow_material)
    except Exception:
        pass
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "yellow_material": YELLOW_TARGET,
        "yellow_material_created": created,
        "yellow_parameters": parameter_report,
        "summary": summary,
        "samples": samples,
        "save_attempted": save_attempted,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    apply_groundcover_visual_polish()
