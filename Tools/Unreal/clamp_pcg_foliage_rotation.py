"""Clamp world-space PCG foliage tilt while preserving Z yaw variation.

Project rule: foliage may vary freely around Z/Yaw, but X/Y tilt must stay
within roughly 5 degrees. Use direct Rotator property assignment because this
Unreal Python build does not map Rotator(...) constructor arguments in the
usual pitch/yaw/roll order.
"""

import json
import os
import random
import time

import unreal


REPORT_NAME = "CubelessPCGFoliageRotationClamp_Report.json"
TILT_LIMIT = 4.9
RANDOM_LIMIT = 4.0


def _norm_angle(value):
    while value > 180.0:
        value -= 360.0
    while value < -180.0:
        value += 360.0
    return value


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


def _category(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(
        token in text
        for token in ["tree", "pine", "spruce", "conifer", "trunk", "branch"]
    ):
        return "tree"
    if any(token in text for token in ["rock", "stone", "boulder"]):
        return "rock"
    if "grass" in text:
        return "grass"
    if "flower" in text:
        return "flower"
    if any(token in text for token in ["fern", "leaf", "leaves", "foliage", "plant"]):
        return "plant"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _fixed_tilt(value, rng):
    value = _norm_angle(value)
    if abs(value) <= TILT_LIMIT:
        return value
    return rng.uniform(-RANDOM_LIMIT, RANDOM_LIMIT)


def _needs_fix(pitch, roll):
    return abs(_norm_angle(pitch)) > TILT_LIMIT or abs(_norm_angle(roll)) > TILT_LIMIT


def clamp_pcg_foliage_rotation():
    before = {}
    after = {}
    samples = []
    failures = []
    updated_instances = 0
    scanned_instances = 0
    touched_components = set()

    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith("MCP_PCG_")
        and not actor.get_actor_label().startswith("MCP_PCG_CameraBookmark_")
    ]

    for actor in actors:
        label = actor.get_actor_label()
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _category(component)
            if category == "other":
                continue

            before.setdefault(
                category,
                {
                    "instances": 0,
                    "violations": 0,
                    "max_pitch": 0.0,
                    "max_roll": 0.0,
                },
            )
            after.setdefault(
                category,
                {
                    "instances": 0,
                    "violations": 0,
                    "max_pitch": 0.0,
                    "max_roll": 0.0,
                },
            )

            count = _instance_count(component)
            for index in range(count):
                scanned_instances += 1
                try:
                    world_transform = component.get_instance_transform(index, True)
                    rotator = world_transform.rotation.rotator()
                    pitch = _norm_angle(rotator.pitch)
                    yaw = _norm_angle(rotator.yaw)
                    roll = _norm_angle(rotator.roll)
                except Exception as exc:
                    if len(failures) < 50:
                        failures.append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "stage": "read",
                                "error": str(exc),
                            }
                        )
                    continue

                before[category]["instances"] += 1
                before[category]["max_pitch"] = max(
                    before[category]["max_pitch"], abs(pitch)
                )
                before[category]["max_roll"] = max(
                    before[category]["max_roll"], abs(roll)
                )
                if _needs_fix(pitch, roll):
                    before[category]["violations"] += 1
                else:
                    after[category]["instances"] += 1
                    after[category]["max_pitch"] = max(
                        after[category]["max_pitch"], abs(pitch)
                    )
                    after[category]["max_roll"] = max(
                        after[category]["max_roll"], abs(roll)
                    )
                    continue

                rng = _stable_rng(label, component.get_name(), index, "tilt")
                fixed_pitch = _fixed_tilt(pitch, rng)
                fixed_roll = _fixed_tilt(roll, rng)

                # Preserve existing yaw if it carries variation. If it is an
                # exact zero from a template, give it stable Z variation.
                fixed_yaw = yaw
                if abs(fixed_yaw) < 0.01:
                    fixed_yaw = rng.uniform(0.0, 360.0)

                desired_rotator = _make_rotator(fixed_pitch, fixed_yaw, fixed_roll)
                world_transform.rotation = desired_rotator.quaternion()

                try:
                    ok = component.update_instance_transform(
                        index, world_transform, True, True, True
                    )
                except Exception as exc:
                    ok = False
                    if len(failures) < 50:
                        failures.append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "stage": "update",
                                "error": str(exc),
                            }
                        )

                if not ok:
                    if len(failures) < 50:
                        failures.append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "stage": "update",
                                "error": "update_instance_transform returned false",
                            }
                        )
                    continue

                updated_instances += 1
                touched_components.add(component)
                after_pitch = abs(_norm_angle(fixed_pitch))
                after_roll = abs(_norm_angle(fixed_roll))
                after[category]["instances"] += 1
                after[category]["max_pitch"] = max(
                    after[category]["max_pitch"], after_pitch
                )
                after[category]["max_roll"] = max(
                    after[category]["max_roll"], after_roll
                )
                if after_pitch > TILT_LIMIT or after_roll > TILT_LIMIT:
                    after[category]["violations"] += 1

                if len(samples) < 40:
                    samples.append(
                        {
                            "actor": label,
                            "component": component.get_name(),
                            "category": category,
                            "index": index,
                            "before": [
                                round(pitch, 2),
                                round(yaw, 2),
                                round(roll, 2),
                            ],
                            "after": [
                                round(fixed_pitch, 2),
                                round(fixed_yaw, 2),
                                round(fixed_roll, 2),
                            ],
                        }
                    )

    for component in touched_components:
        try:
            component.mark_render_state_dirty()
        except Exception:
            pass

    verification = _verify_current_rotation()

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tilt_limit": TILT_LIMIT,
        "random_limit": RANDOM_LIMIT,
        "actor_count": len(actors),
        "scanned_instances": scanned_instances,
        "updated_instances": updated_instances,
        "before": before,
        "after_expected": after,
        "verification": verification,
        "failure_count": len(failures),
        "failures": failures,
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


def _verify_current_rotation():
    summary = {}
    samples = []

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue
        if label.startswith("MCP_PCG_CameraBookmark_"):
            continue

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = _category(component)
            if category == "other":
                continue
            entry = summary.setdefault(
                category,
                {
                    "instances": 0,
                    "violations": 0,
                    "max_pitch": 0.0,
                    "max_roll": 0.0,
                },
            )
            count = _instance_count(component)
            for index in range(count):
                try:
                    rotator = component.get_instance_transform(
                        index, True
                    ).rotation.rotator()
                    pitch = _norm_angle(rotator.pitch)
                    roll = _norm_angle(rotator.roll)
                    yaw = _norm_angle(rotator.yaw)
                except Exception:
                    continue
                entry["instances"] += 1
                entry["max_pitch"] = max(entry["max_pitch"], abs(pitch))
                entry["max_roll"] = max(entry["max_roll"], abs(roll))
                if _needs_fix(pitch, roll):
                    entry["violations"] += 1
                    if len(samples) < 30:
                        samples.append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "category": category,
                                "index": index,
                                "world": [
                                    round(pitch, 2),
                                    round(yaw, 2),
                                    round(roll, 2),
                                ],
                            }
                        )

    return {"summary": summary, "samples": samples}


if __name__ == "__main__":
    clamp_pcg_foliage_rotation()
