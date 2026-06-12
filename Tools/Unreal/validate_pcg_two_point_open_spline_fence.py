"""Validate that a 2-point open spline remains valid for linear fence intent.

This fixture is paired with the closed-spline area fixture:
- open 2-point splines are valid for fences, guides, roads, borders, and other
  linear placement
- closed 3+ point splines are the separate area-mask case

The script creates a tagged open spline and applies a fence-like mesh along it.
It uses disposable _MCP_Temp validation actors only.
"""

import json
import math
import os
import time

import unreal


LEVEL_PATH = "/Game/_MCP_Temp/PCG/LVL_Cubeless_PCG_IntentGallery_MCP"
SOURCE_LABEL = "MCP_PCG_TwoPointOpenFence_Source"
SEGMENT_PREFIX = "MCP_PCG_TwoPointOpenFence_Segment_"
REPORT_NAME = "CubelessTwoPointOpenSplineFence_Report.json"
SETTLE_SECONDS = 0.75
STATE_ATTR = "_cubeless_two_point_open_spline_fence_state"

BP_CLASS_PATH = (
    "/Game/_MCP_Temp/PCG/Blueprints/"
    "BP_Cubeless_ClosedSplineAreaAuthoring.BP_Cubeless_ClosedSplineAreaAuthoring_C"
)

FENCE_MESH_CANDIDATES = [
    "/Game/AI_Generated/Meshes/SM_Ieta_RoadFence_A.SM_Ieta_RoadFence_A",
    (
        "/Game/AI_Generated/AIModeling/Additional_512/14_blue_corrugated_fence_gate/"
        "Models/SM_14_blue_corrugated_fence_gate.SM_14_blue_corrugated_fence_gate"
    ),
    (
        "/Game/AI_Generated/AIModeling/Additional_512/12_stair_retaining_wall_rail_module/"
        "Models/SM_12_stair_retaining_wall_rail_module.SM_12_stair_retaining_wall_rail_module"
    ),
    "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Props/Objects/SM_Wood_03.SM_Wood_03",
]

LOCAL_POINTS = [
    unreal.Vector(-4200.0, -750.0, 0.0),
    unreal.Vector(4200.0, 750.0, 0.0),
]


def _make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _load_level():
    world = unreal.EditorLevelLibrary.get_editor_world()
    current_path = world.get_path_name() if world else ""
    if current_path.startswith(LEVEL_PATH + "."):
        return {"loaded": False, "world_before": current_path}
    unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    return {"loaded": True, "world_before": current_path, "world_after": world.get_path_name()}


def _actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return ""


def _find_actor(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _delete_existing():
    deleted = []
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        label = _actor_label(actor)
        if label != SOURCE_LABEL and not label.startswith(SEGMENT_PREFIX):
            continue
        for component in actor.get_components_by_class(unreal.PCGComponent):
            try:
                component.cleanup(True)
            except Exception:
                pass
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted.append(label)
        except Exception:
            pass
    return deleted


def _sample_ground_z(world, x, y, fallback_z=0.0):
    start = unreal.Vector(x, y, 50000.0)
    end = unreal.Vector(x, y, -10000.0)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            [],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        values = hit.to_tuple()
    except Exception:
        return fallback_z, False
    if not values or not bool(values[0]):
        return fallback_z, False
    try:
        actor = values[9]
        actor_name = actor.get_name() if actor else ""
        actor_class = actor.get_class().get_name() if actor else ""
    except Exception:
        actor_name = ""
        actor_class = ""
    if "Landscape" not in actor_name and "Landscape" not in actor_class:
        return fallback_z, False
    try:
        return float(values[4].z), True
    except Exception:
        return fallback_z, False


def _find_mesh():
    for path in FENCE_MESH_CANDIDATES:
        mesh = unreal.load_object(None, path)
        if mesh:
            return mesh, path
    return None, None


def _deactivate_pcg(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.PCGComponent):
        row = {"component": component.get_name()}
        try:
            component.cleanup(True)
        except Exception as exc:
            row["cleanup_error"] = str(exc)
        try:
            component.deactivate()
            row["deactivated"] = True
        except Exception as exc:
            row["deactivated"] = False
            row["error"] = str(exc)
        rows.append(row)
    return rows


def _configure_open_spline(actor):
    splines = actor.get_components_by_class(unreal.SplineComponent)
    if not splines:
        raise RuntimeError("Source actor has no SplineComponent.")
    spline = splines[0]
    spline.clear_spline_points(True)
    for point in LOCAL_POINTS:
        spline.add_spline_point(point, unreal.SplineCoordinateSpace.LOCAL, True)
    for index in range(spline.get_number_of_spline_points()):
        try:
            spline.set_spline_point_type(index, unreal.SplinePointType.LINEAR, True)
        except Exception:
            pass
    spline.set_closed_loop(False, True)
    spline.update_spline()
    try:
        spline.set_editor_property(
            "component_tags",
            [
                unreal.Name("PCGOpenLinearSpline"),
                unreal.Name("PCGFenceGuide"),
                unreal.Name("PCGTwoPointOpenSpline"),
            ],
        )
    except Exception:
        pass
    return spline


def _world_point(actor, local_point):
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    yaw = math.radians(float(rotation.yaw))
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    return unreal.Vector(
        location.x + local_point.x * cos_yaw - local_point.y * sin_yaw,
        location.y + local_point.x * sin_yaw + local_point.y * cos_yaw,
        location.z + local_point.z,
    )


def _mesh_nominal_length(mesh):
    try:
        bounds = mesh.get_bounds()
        extent = bounds.box_extent
        longest = max(float(extent.x), float(extent.y), float(extent.z)) * 2.0
        if longest > 50.0:
            return min(max(longest, 350.0), 1200.0)
    except Exception:
        pass
    return 700.0


def _lerp_vector(a, b, alpha):
    return unreal.Vector(
        a.x + (b.x - a.x) * alpha,
        a.y + (b.y - a.y) * alpha,
        a.z + (b.z - a.z) * alpha,
    )


def _distance_xy(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _set_actor_tags(actor, tags):
    try:
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])
    except Exception:
        pass


def _spawn_spline_mesh_segment(label, mesh, start, end):
    direction = unreal.Vector(end.x - start.x, end.y - start.y, 0.0)
    length_xy = max(_distance_xy(start, end), 1.0)
    yaw = math.degrees(math.atan2(direction.y, direction.x))
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SplineMeshActor,
        start,
        _make_rotator(0.0, yaw, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn SplineMeshActor.")
    actor.set_actor_label(label)
    _set_actor_tags(actor, ["MCPValidation", "PCGOpenLinearFenceSegment"])
    components = actor.get_components_by_class(unreal.SplineMeshComponent)
    if not components:
        raise RuntimeError("SplineMeshActor has no SplineMeshComponent.")
    component = components[0]
    try:
        component.set_static_mesh(mesh)
    except Exception as exc:
        raise RuntimeError("Failed to assign fence mesh to SplineMeshComponent: " + str(exc))
    try:
        component.set_forward_axis(unreal.SplineMeshAxis.X, True)
    except Exception:
        pass
    z_delta = float(end.z - start.z)
    local_start = unreal.Vector(0.0, 0.0, 0.0)
    local_end = unreal.Vector(length_xy, 0.0, z_delta)
    tangent = unreal.Vector(length_xy, 0.0, z_delta)
    try:
        component.set_start_and_end(local_start, tangent, local_end, tangent, True)
    except Exception as exc:
        raise RuntimeError("Failed to configure SplineMesh start/end: " + str(exc))
    try:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    try:
        component.set_editor_property(
            "component_tags",
            [unreal.Name("PCGOpenLinearFenceSegment")],
        )
    except Exception:
        pass
    return {
        "label": label,
        "actor_class": actor.get_class().get_name(),
        "component_class": component.get_class().get_name(),
        "method": "SplineMeshActor",
        "start": [round(start.x, 2), round(start.y, 2), round(start.z, 2)],
        "end": [round(end.x, 2), round(end.y, 2), round(end.z, 2)],
        "length_xy": round(length_xy, 2),
    }


def _spawn_static_mesh_segment(label, mesh, start, end):
    direction = unreal.Vector(end.x - start.x, end.y - start.y, 0.0)
    yaw = math.degrees(math.atan2(direction.y, direction.x))
    midpoint = _lerp_vector(start, end, 0.5)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        midpoint,
        _make_rotator(0.0, yaw, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn StaticMeshActor fallback.")
    actor.set_actor_label(label)
    _set_actor_tags(actor, ["MCPValidation", "PCGOpenLinearFenceSegment", "StaticMeshFallback"])
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        raise RuntimeError("StaticMeshActor has no StaticMeshComponent.")
    component.set_static_mesh(mesh)
    try:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    return {
        "label": label,
        "actor_class": actor.get_class().get_name(),
        "component_class": component.get_class().get_name(),
        "method": "StaticMeshActorFallback",
        "start": [round(start.x, 2), round(start.y, 2), round(start.z, 2)],
        "end": [round(end.x, 2), round(end.y, 2), round(end.z, 2)],
        "length_xy": round(_distance_xy(start, end), 2),
    }


def _spawn_fence_segments(world, mesh, start, end):
    route_length = _distance_xy(start, end)
    target_length = _mesh_nominal_length(mesh)
    segment_count = max(1, int(math.ceil(route_length / target_length)))
    rows = []
    method = None
    for index in range(segment_count):
        alpha0 = float(index) / float(segment_count)
        alpha1 = float(index + 1) / float(segment_count)
        a = _lerp_vector(start, end, alpha0)
        b = _lerp_vector(start, end, alpha1)
        a.z, _ = _sample_ground_z(world, a.x, a.y, a.z)
        b.z, _ = _sample_ground_z(world, b.x, b.y, b.z)
        label = "{}{:03d}".format(SEGMENT_PREFIX, index)
        try:
            row = _spawn_spline_mesh_segment(label, mesh, a, b)
        except Exception as exc:
            row = _spawn_static_mesh_segment(label, mesh, a, b)
            row["spline_mesh_error"] = str(exc)
        method = method or row.get("method")
        rows.append(row)
    return {
        "route_length_xy": round(route_length, 2),
        "target_segment_length": round(target_length, 2),
        "segment_count": len(rows),
        "primary_method": method,
        "segments": rows,
    }


def _validate(source_actor, spline, mesh_path, segment_summary):
    segment_labels = []
    spline_mesh_count = 0
    static_mesh_fallback_count = 0
    mesh_mismatch_count = 0
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = _actor_label(actor)
        if not label.startswith(SEGMENT_PREFIX):
            continue
        segment_labels.append(label)
        for component in actor.get_components_by_class(unreal.SplineMeshComponent):
            spline_mesh_count += 1
            try:
                mesh = component.get_editor_property("static_mesh")
                if not mesh or mesh.get_path_name() != mesh_path:
                    mesh_mismatch_count += 1
            except Exception:
                mesh_mismatch_count += 1
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if actor.get_class().get_name() != "StaticMeshActor":
                continue
            static_mesh_fallback_count += 1
            try:
                mesh = component.get_editor_property("static_mesh")
                if not mesh or mesh.get_path_name() != mesh_path:
                    mesh_mismatch_count += 1
            except Exception:
                mesh_mismatch_count += 1

    point_count = int(spline.get_number_of_spline_points())
    closed = bool(spline.is_closed_loop())
    result = {
        "source_actor": _actor_label(source_actor),
        "spline_closed_loop": closed,
        "spline_point_count": point_count,
        "spline_length": round(float(spline.get_spline_length()), 2),
        "segment_actor_count": len(segment_labels),
        "spline_mesh_component_count": spline_mesh_count,
        "static_mesh_fallback_component_count": static_mesh_fallback_count,
        "mesh_mismatch_count": mesh_mismatch_count,
        "segment_summary": segment_summary,
    }
    result["pass"] = (
        not closed
        and point_count == 2
        and len(segment_labels) > 0
        and mesh_mismatch_count == 0
        and (spline_mesh_count + static_mesh_fallback_count) > 0
    )
    return result


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report_path


def validate_two_point_open_spline_fence():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle"):
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    level_load = _load_level()
    world = unreal.EditorLevelLibrary.get_editor_world()
    deleted_existing = _delete_existing()
    mesh, mesh_path = _find_mesh()
    if not mesh:
        raise RuntimeError("No fence-like mesh candidate could be loaded.")
    actor_class = unreal.load_object(None, BP_CLASS_PATH)
    if not actor_class:
        raise RuntimeError("Missing source actor class: " + BP_CLASS_PATH)

    origin_x = 23800.0
    origin_y = 18100.0
    origin_z, hit_landscape = _sample_ground_z(world, origin_x, origin_y, 0.0)
    source_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        unreal.Vector(origin_x, origin_y, origin_z),
        _make_rotator(0.0, 10.0, 0.0),
    )
    if not source_actor:
        raise RuntimeError("Failed to spawn two-point open spline source.")
    source_actor.set_actor_label(SOURCE_LABEL)
    _set_actor_tags(
        source_actor,
        [
            "MCPValidation",
            "PCGOpenLinearSpline",
            "PCGFenceGuide",
            "PCGTwoPointOpenSpline",
        ],
    )
    source_pcg_components = _deactivate_pcg(source_actor)
    spline = _configure_open_spline(source_actor)
    start = _world_point(source_actor, LOCAL_POINTS[0])
    end = _world_point(source_actor, LOCAL_POINTS[1])
    start.z, _ = _sample_ground_z(world, start.x, start.y, start.z)
    end.z, _ = _sample_ground_z(world, end.x, end.y, end.z)

    segment_summary = _spawn_fence_segments(world, mesh, start, end)
    state = {
        "started_at": time.time(),
        "handle": None,
        "completed": False,
        "level_load": level_load,
        "deleted_existing": deleted_existing,
        "mesh_path": mesh_path,
        "hit_landscape": hit_landscape,
        "source_pcg_components": source_pcg_components,
        "segment_summary": segment_summary,
    }

    def _tick(_delta_seconds):
        if state["completed"]:
            return False
        if time.time() - state["started_at"] < SETTLE_SECONDS:
            return True
        state["completed"] = True
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        try:
            settled_actor = _find_actor(SOURCE_LABEL)
            if not settled_actor:
                raise RuntimeError("Source actor disappeared: " + SOURCE_LABEL)
            settled_spline = _configure_open_spline(settled_actor)
            validation = _validate(
                settled_actor,
                settled_spline,
                state["mesh_path"],
                state["segment_summary"],
            )
            try:
                unreal.EditorLevelLibrary.save_current_level()
                save_current_level = True
            except Exception as exc:
                save_current_level = "failed: " + str(exc)
            world_now = unreal.EditorLevelLibrary.get_editor_world()
            report = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "world": world_now.get_path_name() if world_now else None,
                "policy": {
                    "open_2_point_spline": (
                        "valid for fences, guides, roads, borders, masks, "
                        "gradients, and linear placement"
                    ),
                    "closed_area_spline": (
                        "separate 3+ point area-mask case; not used by this fence fixture"
                    ),
                },
                "level_load": state["level_load"],
                "deleted_existing": state["deleted_existing"],
                "source_actor": SOURCE_LABEL,
                "mesh": state["mesh_path"],
                "hit_landscape": state["hit_landscape"],
                "source_pcg_components": state["source_pcg_components"],
                "validation": validation,
                "save_current_level": save_current_level,
            }
            report["pass"] = bool(validation.get("pass"))
            _write_report(report)
        except Exception as exc:
            _write_report(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "failed",
                    "pass": False,
                    "error": str(exc),
                    "level_load": state.get("level_load", {}),
                    "source_actor": SOURCE_LABEL,
                    "mesh": state.get("mesh_path"),
                }
            )
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)
    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "scheduled",
        "wait_seconds": SETTLE_SECONDS,
        "source_actor": SOURCE_LABEL,
        "mesh": mesh_path,
        "segment_count": int(segment_summary.get("segment_count", 0)),
        "primary_method": segment_summary.get("primary_method"),
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    validate_two_point_open_spline_fence()
