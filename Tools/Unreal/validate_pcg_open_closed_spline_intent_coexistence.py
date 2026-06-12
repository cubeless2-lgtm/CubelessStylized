"""Validate that open linear and closed area spline PCG intents coexist.

This script reads the current validation level after the closed-area and
open-linear scripts have run, reapplies both spline intents, regenerates the
fixture outputs, then proves that:
- the closed spline remains a 3+ point area mask with grass inside the polygon
- the open 2-point spline remains linear and drives SpawnSplineMesh output
- the two intent paths keep separate source actors, tags, and generated outputs
"""

import json
import os
import time

import unreal


LEVEL_PATH = "/Game/_MCP_Temp/PCG/LVL_Cubeless_PCG_IntentGallery_MCP"
REPORT_NAME = "CubelessSplineIntentCoexistence_Report.json"
WAIT_SECONDS = 8.0
STATE_ATTR = "_cubeless_spline_intent_coexistence_state"

CLOSED_SCRIPT = "D:/Git/CubelessStylized/Tools/Unreal/validate_pcg_closed_spline_grass_area.py"
OPEN_SCRIPT = "D:/Git/CubelessStylized/Tools/Unreal/validate_pcg_two_point_open_spline_fence_native_graph.py"


def _load_helpers(path):
    namespace = {"__name__": "cubeless_helper_" + os.path.basename(path)}
    with open(path, "r", encoding="utf-8") as handle:
        code = handle.read()
    exec(compile(code, path, "exec"), namespace)
    return namespace


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


def _actor_tags(actor):
    try:
        return sorted(str(tag) for tag in actor.get_editor_property("tags"))
    except Exception:
        try:
            return sorted(str(tag) for tag in actor.tags)
        except Exception:
            return []


def _component_tags(component):
    try:
        return sorted(str(tag) for tag in component.get_editor_property("component_tags"))
    except Exception:
        return []


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report_path


def _load_level():
    world = unreal.EditorLevelLibrary.get_editor_world()
    current_path = world.get_path_name() if world else ""
    if current_path.startswith(LEVEL_PATH + "."):
        return {"loaded": False, "world_before": current_path}
    unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    return {"loaded": True, "world_before": current_path, "world_after": world.get_path_name()}


def _validate_current_state(state):
    closed = state["closed_helpers"]
    opened = state["open_helpers"]

    closed_source = _find_actor(closed["ACTOR_LABEL"])
    closed_volume = _find_actor(closed["PCG_VOLUME_LABEL"])
    open_source = _find_actor(opened["SOURCE_LABEL"])
    open_volume = _find_actor(opened["PCG_VOLUME_LABEL"])

    missing = [
        label
        for label, actor in [
            (closed["ACTOR_LABEL"], closed_source),
            (closed["PCG_VOLUME_LABEL"], closed_volume),
            (opened["SOURCE_LABEL"], open_source),
            (opened["PCG_VOLUME_LABEL"], open_volume),
        ]
        if not actor
    ]

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
        "level_load": state.get("level_load", {}),
        "repair": state.get("repair", {}),
        "policy": {
            "open_2_point_spline": "linear intent for fences, guides, roads, borders, masks, and gradients",
            "closed_3plus_point_spline": "area intent for grass or groundcover masks",
            "intent_isolation": "open and closed splines must coexist without converting one intent into the other",
        },
        "actors": {},
        "missing_actors": missing,
    }

    closed_validation = None
    if closed_source and closed_volume:
        closed_splines = closed_source.get_components_by_class(unreal.SplineComponent)
        if closed_splines:
            closed_validation = closed["_validate"](closed_source, closed_splines[0], closed_volume)
            report["actors"]["closed_source"] = {
                "label": _actor_label(closed_source),
                "tags": _actor_tags(closed_source),
                "spline_component_tags": _component_tags(closed_splines[0]),
            }
        else:
            closed_validation = {"pass": False, "error": "closed source has no SplineComponent"}

    open_validation = None
    if open_source and open_volume:
        open_splines = open_source.get_components_by_class(unreal.SplineComponent)
        if open_splines:
            open_validation = opened["_validate"](open_source, open_splines[0], open_volume)
            report["actors"]["open_source"] = {
                "label": _actor_label(open_source),
                "tags": _actor_tags(open_source),
                "spline_component_tags": _component_tags(open_splines[0]),
            }
        else:
            open_validation = {"pass": False, "error": "open source has no SplineComponent"}

    closed_tags = set(report.get("actors", {}).get("closed_source", {}).get("tags", []))
    open_tags = set(report.get("actors", {}).get("open_source", {}).get("tags", []))
    closed_component_tags = set(report.get("actors", {}).get("closed_source", {}).get("spline_component_tags", []))
    open_component_tags = set(report.get("actors", {}).get("open_source", {}).get("spline_component_tags", []))

    isolation = {
        "closed_has_area_tag": "PCGClosedSplineArea" in closed_tags or "PCGClosedSplineArea" in closed_component_tags,
        "closed_has_grass_area_tag": "PCGGrassArea" in closed_tags or "PCGGrassArea" in closed_component_tags,
        "open_has_linear_tag": "PCGOpenLinearSpline" in open_tags or "PCGOpenLinearSpline" in open_component_tags,
        "open_has_two_point_tag": "PCGTwoPointOpenSpline" in open_tags or "PCGTwoPointOpenSpline" in open_component_tags,
        "open_has_fence_tag": "PCGFenceGuide" in open_tags or "PCGFenceGuide" in open_component_tags,
        "closed_not_open_two_point": "PCGTwoPointOpenSpline" not in closed_tags and "PCGTwoPointOpenSpline" not in closed_component_tags,
        "open_not_closed_area": "PCGClosedSplineArea" not in open_tags and "PCGClosedSplineArea" not in open_component_tags,
    }
    isolation["pass"] = all(isolation.values())

    report["closed_area_validation"] = closed_validation
    report["open_linear_validation"] = open_validation
    report["intent_isolation"] = isolation
    report["pass"] = (
        not missing
        and bool(closed_validation and closed_validation.get("pass"))
        and bool(open_validation and open_validation.get("pass"))
        and bool(isolation.get("pass"))
    )

    try:
        unreal.EditorLevelLibrary.save_current_level()
        report["save_current_level"] = True
    except Exception as exc:
        report["save_current_level"] = "failed: " + str(exc)

    _write_report(report)
    return report


def _prepare_for_validation(state):
    closed = state["closed_helpers"]
    opened = state["open_helpers"]
    closed_source = _find_actor(closed["ACTOR_LABEL"])
    closed_volume = _find_actor(closed["PCG_VOLUME_LABEL"])
    open_source = _find_actor(opened["SOURCE_LABEL"])
    open_volume = _find_actor(opened["PCG_VOLUME_LABEL"])
    repair = {
        "closed_source_found": bool(closed_source),
        "closed_volume_found": bool(closed_volume),
        "open_source_found": bool(open_source),
        "open_volume_found": bool(open_volume),
        "closed_reconfigured": False,
        "closed_generation": [],
        "open_reconfigured": False,
        "open_component_update": None,
    }

    if closed_source and closed_volume:
        graph = unreal.load_object(None, closed["GRASS_GRAPH_PATH"])
        if graph:
            if "_ensure_closed_grass_graph_mesh_override" in closed:
                repair["closed_graph_update"] = closed["_ensure_closed_grass_graph_mesh_override"](graph)
            if "_apply_grass_mesh_override_properties" in closed:
                repair["closed_source_properties"] = closed["_apply_grass_mesh_override_properties"](
                    closed_source,
                    False,
                )
            closed["_configure_spline"](closed_source)
            repair["closed_pcg_components"] = closed["_configure_pcg"](closed_volume, graph)
            # Reapply after component setup in case construction side effects touched the source.
            if "_apply_grass_mesh_override_properties" in closed:
                repair["closed_source_properties"] = closed["_apply_grass_mesh_override_properties"](
                    closed_source,
                    False,
                )
            closed["_configure_spline"](closed_source)
            repair["closed_generation"] = closed["_generate_enabled_pcg"](closed_volume)
            repair["closed_reconfigured"] = True
        else:
            repair["closed_error"] = "missing graph: " + closed["GRASS_GRAPH_PATH"]

    if open_source and open_volume:
        graph = unreal.load_object(None, opened["GRAPH_OBJECT"])
        if graph:
            opened["_configure_open_spline"](open_source)
            repair["open_component_update"] = opened["_configure_component"](open_volume, graph)
            opened["_configure_open_spline"](open_source)
            repair["open_reconfigured"] = True
        else:
            repair["open_error"] = "missing graph: " + opened["GRAPH_OBJECT"]

    state["repair"] = repair


def validate_spline_intent_coexistence():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle"):
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    level_load = _load_level()
    state = {
        "started_at": time.time(),
        "handle": None,
        "completed": False,
        "level_load": level_load,
        "closed_helpers": _load_helpers(CLOSED_SCRIPT),
        "open_helpers": _load_helpers(OPEN_SCRIPT),
        "repair": {},
    }

    try:
        _prepare_for_validation(state)
    except Exception as exc:
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
            "level_load": level_load,
            "status": "failed",
            "stage": "prepare",
            "error": str(exc),
            "pass": False,
        }
        _write_report(report)
        return report

    def _tick(_delta_seconds):
        if state["completed"]:
            return False
        if time.time() - state["started_at"] < WAIT_SECONDS:
            return True
        state["completed"] = True
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        try:
            _validate_current_state(state)
        except Exception as exc:
            _write_report(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
                    "level_load": level_load,
                    "repair": state.get("repair", {}),
                    "status": "failed",
                    "stage": "validate",
                    "error": str(exc),
                    "pass": False,
                }
            )
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)
    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "scheduled",
        "wait_seconds": WAIT_SECONDS,
        "level_load": level_load,
        "repair": state["repair"],
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    validate_spline_intent_coexistence()
