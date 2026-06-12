"""Add micro grass instances to the generated ground-carpet PCG layer.

This is a visual-density supplement for MCP_PCG_GroundCarpetFillLayer actors.
It keeps the PCG layer structure and adds extra HISM instances to the generated
grass components instead of spawning thousands more PCG actors.
"""

import json
import math
import os
import random
import time

import unreal


PREFIX = "MCP_PCG_GroundCarpetFillLayer"
REPORT_NAME = "CubelessGroundCarpetMicroSupplement_Report.json"
SUPPLEMENT_SKIP_THRESHOLD = 150

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
        if length > 0:
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


def _component_priority(component):
    name = component.get_name().lower()
    if "grass" in name:
        return 0
    return 9


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _actor_instance_total(actor):
    total = 0
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        total += _instance_count(component)
    return total


def _target_count(distance):
    if distance < 1200.0:
        return 0
    if distance < 1600.0:
        return 30
    if distance < 2200.0:
        return 75
    if distance < 3000.0:
        return 120
    return 180


def _make_transform(x, y, z, rng):
    rot = unreal.Rotator()
    rot.pitch = rng.uniform(-2.0, 2.0)
    rot.yaw = rng.uniform(0.0, 360.0)
    rot.roll = rng.uniform(-2.0, 2.0)

    scale = rng.uniform(0.78, 1.32)
    transform = unreal.Transform()
    transform.translation = unreal.Vector(x, y, z)
    transform.rotation = rot.quaternion()
    transform.scale3d = unreal.Vector(scale, scale, rng.uniform(0.88, 1.22))
    return transform


def _candidate_location(origin, radius, rng):
    angle = rng.uniform(0.0, math.tau)
    distance = math.sqrt(rng.random()) * radius
    return origin.x + math.cos(angle) * distance, origin.y + math.sin(angle) * distance


def supplement_ground_carpet():
    rng = random.Random(6112027)
    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]

    added_total = 0
    skipped_already_supplemented = 0
    skipped_no_component = 0
    skipped_road_core = 0
    actor_reports = []

    for actor in actors:
        before_total = _actor_instance_total(actor)
        if before_total > SUPPLEMENT_SKIP_THRESHOLD:
            skipped_already_supplemented += 1
            continue

        origin = actor.get_actor_location()
        road_distance = _road_distance(origin.x, origin.y)
        target = _target_count(road_distance)
        if target <= 0:
            skipped_road_core += 1
            continue

        components = [
            component
            for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
            if _component_priority(component) < 9
        ]
        components.sort(key=_component_priority)
        if not components:
            skipped_no_component += 1
            continue

        radius = 520.0 if road_distance < 2400.0 else 680.0
        transforms_by_component = {component: [] for component in components}
        attempts = 0
        made = 0
        max_attempts = max(60, target * 8)

        while made < target and attempts < max_attempts:
            attempts += 1
            x, y = _candidate_location(origin, radius, rng)
            if _road_distance(x, y) < 950.0:
                continue

            component = components[made % len(components)]
            z = origin.z + rng.uniform(-12.0, 12.0)
            transforms_by_component[component].append(_make_transform(x, y, z, rng))
            made += 1

        actor_added = 0
        for component, transforms in transforms_by_component.items():
            if not transforms:
                continue
            component.add_instances(transforms, False, True)
            actor_added += len(transforms)
            try:
                component.mark_render_state_dirty()
            except Exception:
                pass

        added_total += actor_added
        if len(actor_reports) < 30:
            actor_reports.append(
                {
                    "actor": actor.get_actor_label(),
                    "road_distance": round(road_distance, 1),
                    "before": before_total,
                    "added": actor_added,
                    "after": _actor_instance_total(actor),
                    "target": target,
                }
            )

    final_total = 0
    zero_actor_count = 0
    for actor in actors:
        total = _actor_instance_total(actor)
        final_total += total
        if total == 0:
            zero_actor_count += 1

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "actor_count": len(actors),
        "added_instances": added_total,
        "final_layer_instances": final_total,
        "zero_actor_count": zero_actor_count,
        "skipped_already_supplemented": skipped_already_supplemented,
        "skipped_no_component": skipped_no_component,
        "skipped_road_core": skipped_road_core,
        "sample": actor_reports,
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
    supplement_ground_carpet()
