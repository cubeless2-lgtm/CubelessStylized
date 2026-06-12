"""Apply a project-local balanced grass material to MCP PCG grass components."""

import json
import os
import time

import unreal


SOURCE_MATERIAL = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Materials/Foliage/Grass/"
    "MI_GrassMedium.MI_GrassMedium"
)
TARGET_FOLDER = "/Game/Cubeless/PCG/Runtime/Materials"
TARGET_NAME = "MI_Cubeless_PCG_GrassMedium_ForestBalanced"
TARGET_MATERIAL = f"{TARGET_FOLDER}/{TARGET_NAME}.{TARGET_NAME}"
REPORT_NAME = "CubelessGrassMaterialBalance_Report.json"


def _load_or_create_material():
    existing = unreal.load_object(None, TARGET_MATERIAL)
    if existing:
        return existing, False

    source = unreal.load_object(None, SOURCE_MATERIAL)
    if not source:
        raise RuntimeError("Failed to load source material: " + SOURCE_MATERIAL)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.duplicate_asset(TARGET_NAME, TARGET_FOLDER, source)
    if not material:
        raise RuntimeError("Failed to duplicate material instance to " + TARGET_MATERIAL)
    return material, True


def _set_parameters(material):
    lib = unreal.MaterialEditingLibrary
    vector_params = {
        "Color Tint": unreal.LinearColor(0.035, 0.155, 0.026, 1.0),
        "Cloud Color": unreal.LinearColor(0.055, 0.125, 0.028, 1.0),
        "Emissive Color": unreal.LinearColor(0.010, 0.035, 0.004, 1.0),
        "Emissive Clouds": unreal.LinearColor(0.012, 0.040, 0.014, 1.0),
    }
    scalar_params = {
        "Emissive Power": 0.035,
        "Specular": 0.08,
        "Roughness": 0.94,
    }

    changed = {"vectors": {}, "scalars": {}}
    for name, value in vector_params.items():
        try:
            lib.set_material_instance_vector_parameter_value(material, name, value)
            changed["vectors"][name] = str(value)
        except Exception as exc:
            changed["vectors"][name] = "failed: " + str(exc)

    for name, value in scalar_params.items():
        try:
            lib.set_material_instance_scalar_parameter_value(material, name, value)
            changed["scalars"][name] = value
        except Exception as exc:
            changed["scalars"][name] = "failed: " + str(exc)

    try:
        lib.update_material_instance(material)
    except Exception:
        pass
    return changed


def _is_grass_component(component):
    name = component.get_name().lower()
    if "grass" in name:
        return True
    try:
        mesh = component.get_editor_property("static_mesh")
        path = mesh.get_path_name().lower() if mesh else ""
    except Exception:
        path = ""
    return "grass" in path


def apply_grass_material_balance():
    material, created = _load_or_create_material()
    parameter_report = _set_parameters(material)

    actor_count = 0
    component_count = 0
    instance_count = 0
    samples = []

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue

        touched_actor = False
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not _is_grass_component(component):
                continue
            try:
                component.set_material(0, material)
                component_count += 1
                try:
                    count = int(component.get_instance_count())
                except Exception:
                    count = 0
                instance_count += count
                touched_actor = True
                if len(samples) < 30:
                    samples.append(
                        {
                            "actor": label,
                            "component": component.get_name(),
                            "instances": count,
                        }
                    )
            except Exception as exc:
                if len(samples) < 30:
                    samples.append(
                        {
                            "actor": label,
                            "component": component.get_name(),
                            "error": str(exc),
                        }
                    )
        if touched_actor:
            actor_count += 1

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(material)
    except Exception:
        pass
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_material": SOURCE_MATERIAL,
        "target_material": TARGET_MATERIAL,
        "created": created,
        "parameters": parameter_report,
        "actor_count": actor_count,
        "component_count": component_count,
        "instance_count": instance_count,
        "sample": samples,
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
    apply_grass_material_balance()
