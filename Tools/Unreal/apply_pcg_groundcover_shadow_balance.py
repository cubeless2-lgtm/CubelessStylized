"""Disable shadow casting on dense groundcover PCG components.

Dense grass, fern, flower, and ground-leaf cards are visual fill rather than
primary silhouette objects. Keeping their shadows enabled across more than a
million instances creates dark card-like artifacts and extra render cost.
Tree/conifer shadows are intentionally left untouched.
"""

import json
import os
import time

import unreal


REPORT_NAME = "CubelessGroundcoverShadowBalance_Report.json"

GROUNDCOVER_MESHES = {
    "grass": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
        "SM_Grass_Medium01.SM_Grass_Medium01",
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
        "SM_Grass_Medium03.SM_Grass_Medium03",
    ],
    "fern": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Plants/"
        "SM_Fern_01.SM_Fern_01",
    ],
    "groundleaf": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Plants/"
        "SM_GroundLeaf_01.SM_GroundLeaf_01",
    ],
    "flowers": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Flowers/"
        "SM_FlowerGroup_01_White.SM_FlowerGroup_01_White",
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Flowers/"
        "SM_FlowerGroup_01_Yellow.SM_FlowerGroup_01_Yellow",
    ],
}


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


def _set_cast_shadow(component, value):
    try:
        component.set_cast_shadow(value)
    except Exception:
        component.set_editor_property("cast_shadow", value)
    try:
        component.mark_render_state_dirty()
    except Exception:
        pass


def apply_groundcover_shadow_balance(save=True):
    mesh_to_group = {
        mesh_path: group
        for group, paths in GROUNDCOVER_MESHES.items()
        for mesh_path in paths
    }
    summary = {
        group: {"components": 0, "instances": 0, "changed": 0}
        for group in GROUNDCOVER_MESHES
    }
    samples = []

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            group = mesh_to_group.get(_mesh_path(component))
            if not group:
                continue

            before = None
            try:
                before = bool(component.get_editor_property("cast_shadow"))
            except Exception:
                pass

            _set_cast_shadow(component, False)
            count = _instance_count(component)
            summary[group]["components"] += 1
            summary[group]["instances"] += count
            if before is not False:
                summary[group]["changed"] += 1

            if len(samples) < 40:
                samples.append(
                    {
                        "actor": label,
                        "component": component.get_name(),
                        "group": group,
                        "instances": count,
                        "cast_shadow_before": before,
                        "cast_shadow_after": False,
                    }
                )

    if save:
        try:
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
            save_attempted = True
        except Exception as exc:
            save_attempted = "failed: " + str(exc)
    else:
        save_attempted = False

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "samples": samples,
        "conifer_shadow_untouched": True,
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
    apply_groundcover_shadow_balance(save=True)
