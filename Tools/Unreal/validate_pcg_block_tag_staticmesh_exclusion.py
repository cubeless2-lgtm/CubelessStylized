"""Validate block-tagged StaticMesh exclusion against closed-spline PCG output.

This fixture proves two things separately:
- whether the current PCG graph natively avoids StaticMesh actors/components
  tagged with a token containing "block"
- whether the current Python validation workaround can remove any remaining
  overlaps until the native graph/API support exists
"""

import json
import os
import time

import unreal


LEVEL_PATH = "/Game/_MCP_Temp/PCG/LVL_Cubeless_PCG_IntentGallery_MCP"
REPORT_NAME = "CubelessBlockTagStaticMeshExclusion_Report.json"
BLOCKER_LABEL = "MCP_PCG_BlockTagExclusion_Blocker"
WAIT_SECONDS = 8.0
STATE_ATTR = "_cubeless_block_tag_staticmesh_exclusion_state"

TOOLS_DIR = os.path.join(unreal.Paths.project_dir(), "Tools", "Unreal")
CLOSED_SCRIPT = os.path.join(TOOLS_DIR, "validate_pcg_closed_spline_grass_area.py")
CUBE_MESH_PATH = "/Engine/BasicShapes/Cube.Cube"
BLOCK_GRAPH_FOLDER = "/Game/_MCP_Temp/PCG/Graphs"
BLOCK_GRAPH_NAME = "PCG_Cubeless_ClosedSplineGrassArea_BlockTagNative_MCP"
BLOCK_GRAPH_PATH = BLOCK_GRAPH_FOLDER + "/" + BLOCK_GRAPH_NAME
BLOCK_GRAPH_OBJECT = BLOCK_GRAPH_PATH + "." + BLOCK_GRAPH_NAME


def _load_helpers(path):
    namespace = {"__name__": "cubeless_helper_" + os.path.basename(path)}
    with open(path, "r", encoding="utf-8") as handle:
        code = handle.read()
    exec(compile(code, path, "exec"), namespace)
    return namespace


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


def _actor_tags(actor):
    try:
        return [str(tag) for tag in actor.get_editor_property("tags")]
    except Exception:
        try:
            return [str(tag) for tag in actor.tags]
        except Exception:
            return []


def _actor_is_destroyable(actor):
    if not actor:
        return False
    try:
        if hasattr(unreal, "SystemLibrary") and not unreal.SystemLibrary.is_valid(actor):
            return False
    except Exception:
        pass
    try:
        editor_world = unreal.EditorLevelLibrary.get_editor_world()
        actor_world = actor.get_world()
        if editor_world and actor_world and actor_world != editor_world:
            return False
    except Exception:
        pass
    return True


def _destroy_actor_safely(actor):
    if not _actor_is_destroyable(actor):
        return False
    try:
        unreal.EditorLevelLibrary.destroy_actor(actor)
        return True
    except Exception:
        return False


def _find_actor(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _delete_existing_blockers():
    deleted = 0
    seen = set()
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        actor_path = actor.get_path_name()
        if actor_path in seen:
            continue
        seen.add(actor_path)
        label = _actor_label(actor)
        tags = _actor_tags(actor)
        if label != BLOCKER_LABEL and "PCGBlockExclusionFixture" not in tags:
            continue
        if _destroy_actor_safely(actor):
            deleted += 1
    return deleted


def _delete_duplicate_blockers_keep(keep_actor):
    keep_path = keep_actor.get_path_name() if keep_actor else ""
    deleted = 0
    seen = set()
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        actor_path = actor.get_path_name()
        if actor_path in seen or actor_path == keep_path:
            continue
        seen.add(actor_path)
        label = _actor_label(actor)
        tags = _actor_tags(actor)
        if label != BLOCKER_LABEL and "PCGBlockExclusionFixture" not in tags:
            continue
        if _destroy_actor_safely(actor):
            deleted += 1
    return deleted


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report_path


def _pin_label(pin):
    try:
        return str(pin.get_editor_property("properties").get_editor_property("label"))
    except Exception:
        try:
            return pin.get_name()
        except Exception:
            return str(pin)


def _add_node(graph, settings_cls, title, x, y):
    created = graph.add_node_of_type(settings_cls.static_class())
    node = created[0] if isinstance(created, tuple) else created
    try:
        node.set_editor_property("node_title", title)
    except Exception:
        try:
            node.node_title = title
        except Exception:
            pass
    try:
        node.set_node_position(int(x), int(y))
    except Exception:
        pass
    return node


def _add_edge(graph, from_node, to_node, from_pin="Out", to_pin="In"):
    try:
        graph.add_edge(from_node, unreal.Name(from_pin), to_node, unreal.Name(to_pin))
        return {"from": from_node.get_name(), "from_pin": from_pin, "to": to_node.get_name(), "to_pin": to_pin, "ok": True}
    except Exception as exc:
        return {"from": from_node.get_name(), "from_pin": from_pin, "to": to_node.get_name(), "to_pin": to_pin, "ok": False, "error": str(exc)}


def _remove_edge(graph, from_node, to_node, from_pin="Out", to_pin="In"):
    try:
        graph.remove_edge(from_node, unreal.Name(from_pin), to_node, unreal.Name(to_pin))
        return {"from": from_node.get_name(), "from_pin": from_pin, "to": to_node.get_name(), "to_pin": to_pin, "ok": True}
    except Exception as exc:
        return {"from": from_node.get_name(), "from_pin": from_pin, "to": to_node.get_name(), "to_pin": to_pin, "ok": False, "error": str(exc)}


def _node_summary(node):
    try:
        settings_class = node.get_settings().get_class().get_name()
    except Exception:
        settings_class = ""
    return {
        "node": node.get_name(),
        "title": str(getattr(node, "node_title", "")),
        "settings_class": settings_class,
        "input_pins": [{"label": _pin_label(pin), "connected": bool(pin.is_connected())} for pin in getattr(node, "input_pins", [])],
        "output_pins": [{"label": _pin_label(pin), "connected": bool(pin.is_connected())} for pin in getattr(node, "output_pins", [])],
    }


def _configure_block_actor_data(node):
    settings = node.get_settings()
    actor_selector = settings.get_editor_property("actor_selector")
    actor_selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    actor_selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    actor_selector.set_editor_property("actor_selection_tag", "block")
    actor_selector.set_editor_property("select_multiple", True)
    actor_selector.set_editor_property("ignore_self_and_children", False)
    settings.set_editor_property("actor_selector", actor_selector)
    settings.set_editor_property("always_requery_actors", True)
    settings.set_editor_property("track_actors_only_within_bounds", False)
    try:
        settings.set_editor_property("also_output_single_point_data", False)
        settings.set_editor_property("merge_single_point_data", False)
    except Exception:
        pass


def _configure_difference(node):
    settings = node.get_settings()
    try:
        settings.set_editor_property("mode", unreal.PCGDifferenceMode.INFERRED)
    except Exception:
        pass
    try:
        settings.set_editor_property("keep_zero_density_points", False)
    except Exception:
        pass


def _create_or_update_block_graph(base_graph_object, closed_helpers=None):
    if not unreal.EditorAssetLibrary.does_directory_exist(BLOCK_GRAPH_FOLDER):
        unreal.EditorAssetLibrary.make_directory(BLOCK_GRAPH_FOLDER)
    graph = unreal.load_object(None, BLOCK_GRAPH_OBJECT)
    removed_mesh_override_nodes = []
    if graph:
        # Never delete this graph while a PCGComponent may still reference it.
        # Updating in place avoids the editor prompt/force-delete loop.
        for node in list(graph.nodes):
            try:
                cls_name = node.get_settings().get_class().get_name()
            except Exception:
                cls_name = ""
            if cls_name in {"PCGDataFromActorSettings", "PCGDifferenceSettings"}:
                try:
                    graph.remove_node(node)
                except Exception:
                    pass
    else:
        duplicated = unreal.EditorAssetLibrary.duplicate_asset(base_graph_object.get_path_name(), BLOCK_GRAPH_PATH)
        graph = duplicated or unreal.load_object(None, BLOCK_GRAPH_OBJECT)
        if not graph:
            raise RuntimeError("Failed to duplicate block-aware graph from " + base_graph_object.get_path_name())

    if closed_helpers and "_remove_generated_grass_mesh_override_nodes" in closed_helpers:
        removed_mesh_override_nodes = closed_helpers["_remove_generated_grass_mesh_override_nodes"](graph)

    sampler = None
    spawner = None
    for node in list(graph.nodes):
        try:
            cls_name = node.get_settings().get_class().get_name()
        except Exception:
            cls_name = ""
        title = str(getattr(node, "node_title", ""))
        if cls_name == "PCGSplineSamplerSettings":
            sampler = node
        elif cls_name == "PCGStaticMeshSpawnerSettings" and "Closed Grass Mesh Override" not in title:
            spawner = node
    if not sampler or not spawner:
        raise RuntimeError("Block-aware graph could not find sampler/spawner nodes.")

    block_data = _add_node(graph, unreal.PCGDataFromActorSettings, "Get block-tagged StaticMesh actors", 640, -280)
    difference = _add_node(graph, unreal.PCGDifferenceSettings, "Subtract block actor data from grass points", 980, 0)
    _configure_block_actor_data(block_data)
    _configure_difference(difference)

    output_node = graph.get_output_node()
    edges = [
        _remove_edge(graph, sampler, spawner, "Out", "In"),
        _remove_edge(graph, spawner, output_node, "Out", "Out"),
    ]
    mesh_override_update = {
        "mode": "attribute_before_difference",
        "removed_generated_override_nodes": removed_mesh_override_nodes,
    }
    if closed_helpers:
        get_mesh = closed_helpers["_add_node"](
            graph,
            unreal.PCGGetActorPropertySettings,
            "Closed Grass Mesh Override Get GrassMeshOverride",
            500,
            -360,
        )
        copy_mesh = closed_helpers["_add_node"](
            graph,
            unreal.PCGCopyAttributesSettings,
            "Closed Grass Mesh Override Copy To DynamicMeshPath",
            720,
            -80,
        )
        closed_helpers["_configure_get_actor_property"](
            get_mesh,
            "GrassMeshOverride",
            "GrassMeshOverride",
        )
        closed_helpers["_configure_copy_actor_mesh"](
            copy_mesh,
            "GrassMeshOverride",
            closed_helpers["DYNAMIC_MESH_ATTR"],
        )
        try:
            spawner.set_editor_property("node_title", "Spawn Closed Area Grass Actor Property Direct")
        except Exception:
            pass
        closed_helpers["_configure_by_attribute_spawner"](spawner)
        edges.extend(
            [
                _add_edge(graph, sampler, copy_mesh, "Out", "Target"),
                _add_edge(graph, get_mesh, copy_mesh, "Out", "Source"),
                _add_edge(graph, copy_mesh, difference, "Out", "Source"),
                _add_edge(graph, block_data, difference, "Out", "Differences"),
                _add_edge(graph, difference, spawner, "Out", "In"),
                _add_edge(graph, spawner, output_node, "Out", "Out"),
            ]
        )
        mesh_override_update.update(
            {
                "get_mesh": closed_helpers["_node_summary"](get_mesh),
                "copy_mesh": closed_helpers["_node_summary"](copy_mesh),
                "spawner": closed_helpers["_node_summary"](spawner),
                "override_attribute": closed_helpers["DYNAMIC_MESH_ATTR"],
                "actor_property_tag": closed_helpers["SOURCE_ACTOR_TAG"],
            }
        )
    else:
        edges.extend(
            [
                _add_edge(graph, sampler, difference, "Out", "Source"),
                _add_edge(graph, block_data, difference, "Out", "Differences"),
                _add_edge(graph, difference, spawner, "Out", "In"),
                _add_edge(graph, spawner, output_node, "Out", "Out"),
            ]
        )
    mesh_override_update["edges"] = edges
    mesh_override_update["edge_errors"] = [edge for edge in edges if not edge.get("ok")]

    try:
        graph.description = (
            "Closed-spline grass validation graph with native block-tag actor data difference "
            "and actor-property StaticMesh override copied before the difference operation."
        )
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(graph, False)
    return {
        "graph": BLOCK_GRAPH_OBJECT,
        "base_graph": base_graph_object.get_path_name(),
        "edges": edges,
        "mesh_override_update": mesh_override_update,
        "nodes": [_node_summary(node) for node in list(graph.nodes)],
    }


def _collect_generated_locations(closed, generated_actor):
    rows = []
    for component in generated_actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        category = closed["_classify"](component)
        count = int(component.get_instance_count())
        for index in range(count):
            try:
                transform = component.get_instance_transform(index, True)
                location = transform.translation
            except Exception:
                continue
            rows.append(
                {
                    "component": component.get_name(),
                    "category": category,
                    "index": index,
                    "location": [float(location.x), float(location.y), float(location.z)],
                }
            )
    return rows


def _choose_blocker_location(rows):
    grass_rows = [row for row in rows if row.get("category") == "grass"]
    candidates = grass_rows or rows
    if not candidates:
        return None
    return candidates[len(candidates) // 2]["location"]


def _spawn_blocker(location):
    mesh = unreal.EditorAssetLibrary.load_asset(CUBE_MESH_PATH)
    if not mesh:
        raise RuntimeError("Missing blocker cube mesh: " + CUBE_MESH_PATH)
    spawn_location = unreal.Vector(float(location[0]), float(location[1]), float(location[2]) + 55.0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        spawn_location,
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn block-tagged StaticMeshActor.")
    actor.set_actor_label(BLOCKER_LABEL)
    actor.set_actor_scale3d(unreal.Vector(12.0, 12.0, 1.0))
    try:
        actor.set_editor_property(
            "tags",
            [
                unreal.Name("MCPValidation"),
                unreal.Name("PCGBlockExclusionFixture"),
                unreal.Name("block"),
            ],
        )
    except Exception:
        pass
    try:
        actor.tags = [
            unreal.Name("MCPValidation"),
            unreal.Name("PCGBlockExclusionFixture"),
            unreal.Name("block"),
        ]
    except Exception:
        pass
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component:
        component.set_static_mesh(mesh)
        try:
            component.set_editor_property(
                "component_tags",
                [
                    unreal.Name("PCGBlockExclusionFixture"),
                    unreal.Name("block"),
                ],
            )
        except Exception:
            pass
        try:
            component.component_tags = [
                unreal.Name("PCGBlockExclusionFixture"),
                unreal.Name("block"),
            ]
        except Exception:
            pass
        try:
            component.register_component()
        except Exception:
            pass
        try:
            component.update_bounds()
        except Exception:
            pass
    return actor


def _remove_block_overlaps(closed, generated_actor):
    block_bounds = closed["_collect_block_bounds"]()
    removed = []
    total_removed = 0
    for component in generated_actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        category = closed["_classify"](component)
        count = int(component.get_instance_count())
        removed_from_component = 0
        for index in range(count - 1, -1, -1):
            try:
                transform = component.get_instance_transform(index, True)
                location = transform.translation
            except Exception:
                continue
            if not closed["_inside_block"](location, block_bounds):
                continue
            try:
                if component.remove_instance(index):
                    removed_from_component += 1
                    total_removed += 1
            except Exception:
                pass
        if removed_from_component:
            try:
                component.mark_render_state_dirty()
            except Exception:
                pass
            removed.append(
                {
                    "component": component.get_name(),
                    "category": category,
                    "removed": removed_from_component,
                }
            )
    return {"total_removed": total_removed, "components": removed, "block_bounds": block_bounds}


def _configure_and_generate(closed, source, volume, graph, use_grass_mesh_override=False):
    if "_apply_grass_mesh_override_properties" in closed:
        closed["_apply_grass_mesh_override_properties"](source, bool(use_grass_mesh_override))
    closed["_configure_spline"](source)
    pcg_components = closed["_configure_pcg"](volume, graph)
    if "_apply_grass_mesh_override_properties" in closed:
        closed["_apply_grass_mesh_override_properties"](source, bool(use_grass_mesh_override))
    closed["_configure_spline"](source)
    generation = closed["_generate_enabled_pcg"](volume)
    return {
        "pcg_components": pcg_components,
        "pcg_generation": generation,
        "use_grass_mesh_override": bool(use_grass_mesh_override),
    }


def validate_block_tag_staticmesh_exclusion():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle"):
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    level_load = _load_level()
    closed = _load_helpers(CLOSED_SCRIPT)
    source = _find_actor(closed["ACTOR_LABEL"])
    volume = _find_actor(closed["PCG_VOLUME_LABEL"])
    graph = unreal.load_object(None, closed["GRASS_GRAPH_PATH"])
    deleted_blockers = _delete_existing_blockers()

    if not source or not volume or not graph:
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
            "level_load": level_load,
            "deleted_existing_blockers": deleted_blockers,
            "source_found": bool(source),
            "volume_found": bool(volume),
            "graph_found": bool(graph),
            "status": "failed",
            "error": "closed-spline fixture must exist before block-tag exclusion validation",
            "pass": False,
        }
        _write_report(report)
        return report

    state = {
        "started_at": time.time(),
        "stage_started_at": time.time(),
        "stage": "baseline_wait",
        "error": None,
        "handle": None,
        "completed": False,
        "level_load": level_load,
        "deleted_existing_blockers": deleted_blockers,
        "closed": closed,
        "source_label": closed["ACTOR_LABEL"],
        "volume_label": closed["PCG_VOLUME_LABEL"],
        "baseline_generation": _configure_and_generate(closed, source, volume, graph),
        "block_generation": None,
        "block_graph": None,
        "blocker": None,
        "blocker_info": None,
    }

    def _finish_with_error(message):
        state["completed"] = True
        try:
            if state.get("handle"):
                unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
            "level_load": level_load,
            "deleted_existing_blockers": deleted_blockers,
            "status": "failed",
            "error": message,
            "pass": False,
        }
        _write_report(report)
        return False

    def _tick(_delta_seconds):
        if state["completed"]:
            return False
        if time.time() - state["stage_started_at"] < WAIT_SECONDS:
            return True

        closed_helpers = state["closed"]
        source_actor = _find_actor(state["source_label"])
        volume_actor = _find_actor(state["volume_label"])
        if not source_actor or not volume_actor:
            return _finish_with_error("closed-spline source or volume disappeared")

        if state["stage"] == "baseline_wait":
            baseline_rows = _collect_generated_locations(closed_helpers, volume_actor)
            blocker_location = _choose_blocker_location(baseline_rows)
            if not blocker_location:
                return _finish_with_error("baseline closed-spline PCG generated no instances")
            blocker = _spawn_blocker(blocker_location)
            state["blocker"] = blocker
            duplicate_blockers_removed = _delete_duplicate_blockers_keep(blocker)
            block_bounds_after_spawn = closed_helpers["_collect_block_bounds"]()
            state["blocker_info"] = {
                "label": BLOCKER_LABEL,
                "location": [round(value, 2) for value in blocker_location],
                "scale": [12.0, 12.0, 1.0],
                "tags": _actor_tags(blocker),
                "baseline_instance_count": len(baseline_rows),
                "duplicate_blockers_removed_after_spawn": duplicate_blockers_removed,
                "detected_block_bounds_after_spawn": block_bounds_after_spawn,
            }
            if not block_bounds_after_spawn:
                return _finish_with_error("spawned blocker was not detected by block-tag bounds collector")
            try:
                state["block_graph"] = _create_or_update_block_graph(graph, closed_helpers)
            except Exception as exc:
                return _finish_with_error("block-aware graph setup failed: " + str(exc))
            graph_object = unreal.load_object(None, BLOCK_GRAPH_OBJECT)
            state["block_generation"] = _configure_and_generate(
                closed_helpers,
                source_actor,
                volume_actor,
                graph_object,
                True,
            )
            state["stage"] = "block_wait"
            state["stage_started_at"] = time.time()
            return True

        if state["stage"] != "block_wait":
            return _finish_with_error("unknown validation stage: " + str(state["stage"]))

        raw_validation = closed_helpers["_validate"](
            source_actor,
            source_actor.get_components_by_class(unreal.SplineComponent)[0],
            volume_actor,
        )
        postprocess = _remove_block_overlaps(closed_helpers, volume_actor)
        fixed_validation = closed_helpers["_validate"](
            source_actor,
            source_actor.get_components_by_class(unreal.SplineComponent)[0],
            volume_actor,
        )
        blocker = state.get("blocker")
        cleanup = {"destroyed": False}
        if blocker:
            if _destroy_actor_safely(blocker):
                cleanup["destroyed"] = True
            else:
                cleanup["destroyed"] = _find_actor(BLOCKER_LABEL) is None
                if not cleanup["destroyed"]:
                    cleanup["error"] = "blocker was not destroyable in the current editor world"
        cleanup["deleted_leftover_blockers"] = _delete_existing_blockers()
        if "_apply_grass_mesh_override_properties" in closed_helpers:
            try:
                cleanup["source_reset_properties"] = closed_helpers["_apply_grass_mesh_override_properties"](
                    source_actor,
                    False,
                )
            except Exception as exc:
                cleanup["source_reset_error"] = str(exc)

        try:
            unreal.EditorLevelLibrary.save_current_level()
            save_current_level = True
        except Exception as exc:
            save_current_level = "failed: " + str(exc)

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "world": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
            "level_load": state["level_load"],
            "deleted_existing_blockers": state["deleted_existing_blockers"],
            "policy": {
                "block_tag": "StaticMesh actor/component tags containing 'block' must exclude generated PCG objects",
                "native_graph_preferred": True,
                "python_postprocess_is_temporary_workaround": True,
            },
            "blocker": state["blocker_info"],
            "baseline_generation": state["baseline_generation"],
            "block_aware_graph": state["block_graph"],
            "block_generation": state["block_generation"],
            "raw_validation_before_python_prune": raw_validation,
            "native_graph_exclusion_pass": bool(
                raw_validation.get("block_tagged_component_count", 0) > 0
                and raw_validation.get("block_overlap_violation_count") == 0
            ),
            "python_prune": postprocess,
            "validation_after_python_prune": fixed_validation,
            "postprocess_exclusion_pass": bool(
                fixed_validation.get("block_tagged_component_count", 0) > 0
                and fixed_validation.get("block_overlap_violation_count") == 0
                and fixed_validation.get("pass")
            ),
            "blocker_cleanup": cleanup,
            "save_current_level": save_current_level,
        }
        report["pass"] = bool(report["postprocess_exclusion_pass"])
        state["completed"] = True
        try:
            unreal.unregister_slate_post_tick_callback(state["handle"])
        except Exception:
            pass
        _write_report(report)
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)

    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "scheduled",
        "wait_seconds_per_generation": WAIT_SECONDS,
        "level_load": level_load,
        "deleted_existing_blockers": deleted_blockers,
        "source": closed["ACTOR_LABEL"],
        "volume": closed["PCG_VOLUME_LABEL"],
        "baseline_generation": state["baseline_generation"],
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    validate_block_tag_staticmesh_exclusion()
