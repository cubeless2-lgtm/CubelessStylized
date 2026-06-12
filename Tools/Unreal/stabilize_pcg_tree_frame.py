"""Stabilize actor-centered tree instances after PCG regeneration.

Run this inside Unreal Editor Python after regenerating
MCP_PCG_VisualTreeFrameLayer actors. The tree profile PCG graphs create
origin-centered template points, so Conifer instances may appear near world
origin after a regenerate. This script moves only unshifted Conifer instances
back into actor-local space and normalizes tilted Conifer variants to the
upright green Conifer mesh used by the visual QA pass.
"""

import json
import math
import os
import time

import unreal


PREFIX = "MCP_PCG_VisualTreeFrameLayer"
TARGET_CONIFER = (
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
    "SM_Conifer_05.SM_Conifer_05"
)
REPORT_NAME = "CubelessVisualTreeFrameLayer_StabilizeUtility_Report.json"
SAVE_AFTER = True


def _dist_2d(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)


def _is_unshifted_template(world_location, actor_location):
    """Return true when a graph-created point is still near world origin.

    The known tree profile template points are within roughly 1,500 cm of
    (0, 0). Once stabilized, their world positions should be within that same
    radius around the owning actor.
    """

    if _dist_2d(world_location, actor_location) <= 2600.0:
        return False
    return abs(world_location.x) <= 2600.0 and abs(world_location.y) <= 2600.0


def _get_mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return str(mesh)


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _normalize_mesh(component, target_mesh):
    mesh_path = _get_mesh_path(component)
    if "SM_Conifer_08" not in mesh_path and "SM_Conifer_09" not in mesh_path:
        return False, mesh_path

    component.set_static_mesh(target_mesh)
    try:
        component.mark_render_state_dirty()
    except Exception:
        pass
    return True, mesh_path


def stabilize_tree_frame():
    target_mesh = unreal.load_object(None, TARGET_CONIFER)
    if not target_mesh:
        raise RuntimeError("Failed to load target mesh: " + TARGET_CONIFER)

    updated_instances = 0
    normalized_components = 0
    normalized_instances = 0
    skipped_already_centered = 0
    skipped_non_template = 0
    failures = []
    samples = []

    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]

    for actor in actors:
        actor_location = actor.get_actor_location()
        components = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)

        for component in components:
            mesh_path = _get_mesh_path(component)
            if "Conifer" not in mesh_path:
                continue

            count = _instance_count(component)
            did_normalize, old_mesh_path = _normalize_mesh(component, target_mesh)
            if did_normalize:
                normalized_components += 1
                normalized_instances += count
                mesh_path = target_mesh.get_path_name()

            for index in range(count):
                try:
                    world_transform = component.get_instance_transform(index, True)
                    world_location = world_transform.translation

                    if not _is_unshifted_template(world_location, actor_location):
                        if _dist_2d(world_location, actor_location) <= 2600.0:
                            skipped_already_centered += 1
                        else:
                            skipped_non_template += 1
                        continue

                    # Convert the origin-centered template position into a
                    # component-local transform. The component already lives at
                    # the actor, so this makes world = actor + template.
                    local_transform = unreal.Transform()
                    local_transform.translation = unreal.Vector(
                        world_transform.translation.x,
                        world_transform.translation.y,
                        world_transform.translation.z,
                    )
                    local_transform.rotation = world_transform.rotation
                    local_transform.scale3d = world_transform.scale3d

                    ok = component.update_instance_transform(
                        index, local_transform, False, True, True
                    )
                    if not ok:
                        failures.append(
                            {
                                "actor": actor.get_actor_label(),
                                "component": component.get_name(),
                                "index": index,
                                "error": "update_instance_transform returned false",
                            }
                        )
                        continue

                    updated_instances += 1
                    if len(samples) < 20:
                        after_location = component.get_instance_transform(
                            index, True
                        ).translation
                        samples.append(
                            {
                                "actor_label": actor.get_actor_label(),
                                "component": component.get_name(),
                                "mesh": mesh_path,
                                "before": [
                                    round(world_location.x, 2),
                                    round(world_location.y, 2),
                                    round(world_location.z, 2),
                                ],
                                "actor_location": [
                                    round(actor_location.x, 2),
                                    round(actor_location.y, 2),
                                    round(actor_location.z, 2),
                                ],
                                "after": [
                                    round(after_location.x, 2),
                                    round(after_location.y, 2),
                                    round(after_location.z, 2),
                                ],
                            }
                        )
                except Exception as exc:
                    failures.append(
                        {
                            "actor": actor.get_actor_label(),
                            "component": component.get_name(),
                            "index": index,
                            "error": str(exc),
                        }
                    )

            try:
                component.mark_render_state_dirty()
            except Exception:
                pass

    save_attempted = False
    if SAVE_AFTER:
        try:
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
            save_attempted = True
        except Exception as exc:
            failures.append({"save_error": str(exc)})

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "actor_count": len(actors),
        "updated_instances": updated_instances,
        "normalized_components": normalized_components,
        "normalized_instances": normalized_instances,
        "skipped_already_centered": skipped_already_centered,
        "skipped_non_template": skipped_non_template,
        "failure_count": len(failures),
        "failures": failures[:50],
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
    stabilize_tree_frame()
