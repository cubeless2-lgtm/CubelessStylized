"""Align generated grass-like PCG ISM instances to Landscape normals.

This is a validation-scene repair tool for dense Landscape PCG tests. It keeps
the existing yaw variation, but interprets it around the hit Landscape normal
instead of world Z.
"""

import json
import math
import os

import unreal


REPORT_NAME = "pcg_grass_normal_alignment_report.json"
GRASS_TOKENS = ("grass", "fern", "groundleaf", "flower", "leaf", "foliage", "plant")
EXCLUDE_TOKENS = ("tree", "pine", "conifer", "rock", "stone", "boulder")
PASS_P95_DEGREES = 8.0
TRACE_UP = 50000.0
TRACE_DOWN = 50000.0
WORLD_UP = unreal.Vector(0.0, 0.0, 1.0)


def _vector_size(vector):
    return math.sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z)


def _normalized(vector, fallback=None):
    size = _vector_size(vector)
    if size <= 1.0e-6:
        return fallback or WORLD_UP
    return unreal.Vector(vector.x / size, vector.y / size, vector.z / size)


def _angle_degrees(a, b):
    aa = _normalized(a)
    bb = _normalized(b)
    dot = max(-1.0, min(1.0, aa.x * bb.x + aa.y * bb.y + aa.z * bb.z))
    return math.degrees(math.acos(dot))


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return ""


def _is_grass_component(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(token in text for token in EXCLUDE_TOKENS):
        return False
    return any(token in text for token in GRASS_TOKENS)


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _hit_landscape_normal(world, location):
    start = unreal.Vector(location.x, location.y, location.z + TRACE_UP)
    end = unreal.Vector(location.x, location.y, location.z - TRACE_DOWN)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        values = hit.to_tuple()
    except Exception:
        return None, "trace_exception"

    if not values or not bool(values[0]):
        return None, "trace_miss"

    actor = values[9]
    component = values[10]
    actor_name = actor.get_name() if actor else ""
    actor_label = actor.get_actor_label() if actor and hasattr(actor, "get_actor_label") else actor_name
    actor_class = actor.get_class().get_name() if actor else ""
    component_name = component.get_name() if component else ""
    component_class = component.get_class().get_name() if component else ""
    hit_text = " ".join([actor_name, actor_label, actor_class, component_name, component_class])

    if "Landscape" not in hit_text and "HLOD" not in hit_text:
        return None, "non_landscape_hit:" + hit_text[:160]

    return _normalized(values[7]), actor_label + "/" + component_name


def _quat_up(quat):
    try:
        return _normalized(unreal.MathLibrary.quat_rotate_vector(quat, WORLD_UP))
    except Exception:
        x, y, z, w = quat.x, quat.y, quat.z, quat.w
        return _normalized(
            unreal.Vector(
                2.0 * (x * z + w * y),
                2.0 * (y * z - w * x),
                1.0 - 2.0 * (x * x + y * y),
            )
        )


def _normal_aligned_quat(normal, yaw_degrees):
    normal = _normalized(normal)
    align_quat = unreal.MathLibrary.quat_find_between_normals(WORLD_UP, normal)
    yaw_rotator = unreal.MathLibrary.rotator_from_axis_and_angle(normal, yaw_degrees)
    yaw_quat = yaw_rotator.quaternion()
    return unreal.MathLibrary.multiply_quat_quat(yaw_quat, align_quat)


def _percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * fraction))
    return ordered[max(0, min(len(ordered) - 1, index))]


def align_pcg_grass_to_landscape_normals():
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    report = {
        "world": world.get_path_name() if world else None,
        "component_count": 0,
        "instance_count": 0,
        "updated": 0,
        "trace_miss_count": 0,
        "before": {},
        "after": {},
        "components": [],
        "failures": [],
    }
    before_angles = []
    after_angles = []

    for actor in actors:
        label = actor.get_actor_label() if hasattr(actor, "get_actor_label") else actor.get_name()
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not _is_grass_component(component):
                continue

            count = _instance_count(component)
            if count <= 0:
                continue

            report["component_count"] += 1
            report["instance_count"] += count
            component_report = {
                "actor": label,
                "component": component.get_name(),
                "instance_count": count,
                "updated": 0,
                "trace_miss_count": 0,
                "before_max": 0.0,
                "after_max": 0.0,
            }

            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, True)
                    location = transform.translation
                    normal, hit_name = _hit_landscape_normal(world, location)
                    if normal is None:
                        component_report["trace_miss_count"] += 1
                        report["trace_miss_count"] += 1
                        if len(report["failures"]) < 40:
                            report["failures"].append(
                                {
                                    "actor": label,
                                    "component": component.get_name(),
                                    "index": index,
                                    "reason": hit_name,
                                }
                            )
                        continue

                    old_up = _quat_up(transform.rotation)
                    before_angle = _angle_degrees(old_up, normal)
                    before_angles.append(before_angle)
                    component_report["before_max"] = max(
                        component_report["before_max"], before_angle
                    )

                    yaw = transform.rotation.rotator().yaw
                    transform.rotation = _normal_aligned_quat(normal, yaw)
                    new_up = _quat_up(transform.rotation)
                    after_angle = _angle_degrees(new_up, normal)
                    after_angles.append(after_angle)
                    component_report["after_max"] = max(
                        component_report["after_max"], after_angle
                    )

                    if component.update_instance_transform(index, transform, True, False, True):
                        report["updated"] += 1
                        component_report["updated"] += 1
                except Exception as exc:
                    if len(report["failures"]) < 40:
                        report["failures"].append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "reason": str(exc),
                            }
                        )

            try:
                component.mark_render_state_dirty()
            except Exception:
                pass
            report["components"].append(component_report)

    report["before"] = {
        "sample_count": len(before_angles),
        "avg_align_deg": round(sum(before_angles) / len(before_angles), 4)
        if before_angles
        else None,
        "p95_align_deg": round(_percentile(before_angles, 0.95), 4)
        if before_angles
        else None,
        "max_align_deg": round(max(before_angles), 4) if before_angles else None,
    }
    report["after"] = {
        "sample_count": len(after_angles),
        "avg_align_deg": round(sum(after_angles) / len(after_angles), 4)
        if after_angles
        else None,
        "p95_align_deg": round(_percentile(after_angles, 0.95), 4)
        if after_angles
        else None,
        "max_align_deg": round(max(after_angles), 4) if after_angles else None,
    }
    after_p95 = _percentile(after_angles, 0.95)
    report["normal_alignment_pass"] = bool(
        after_angles and after_p95 is not None and after_p95 <= PASS_P95_DEGREES
    )

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    report["report_path"] = report_path

    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    align_pcg_grass_to_landscape_normals()
