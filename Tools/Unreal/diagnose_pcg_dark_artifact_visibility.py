"""Capture temporary visibility diagnostics for dark PCG card artifacts."""

import json
import os
import time

import unreal


REPORT_NAME = "CubelessDarkArtifactVisibilityDiagnostic_Report.json"
SCREENSHOT_DIR = "Screenshots"

GROUPS = {
    "groundleaf": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Plants/"
        "SM_GroundLeaf_01.SM_GroundLeaf_01"
    ],
    "fern": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Plants/"
        "SM_Fern_01.SM_Fern_01"
    ],
    "flowers": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Flowers/"
        "SM_FlowerGroup_01_White.SM_FlowerGroup_01_White",
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Flowers/"
        "SM_FlowerGroup_01_Yellow.SM_FlowerGroup_01_Yellow",
    ],
    "conifers": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
        "SM_Conifer_05.SM_Conifer_05",
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
        "SM_Conifer_08.SM_Conifer_08",
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Trees/"
        "SM_Conifer_09.SM_Conifer_09",
    ],
    "grass": [
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
        "SM_Grass_Medium01.SM_Grass_Medium01",
        "/Game/DreamscapeSeries/DreamscapeMountains/Meshes/Foliage/Grass/"
        "SM_Grass_Medium03.SM_Grass_Medium03",
    ],
}

SCENARIOS = [
    ("baseline_all_visible", []),
    ("hide_groundleaf", ["groundleaf"]),
    ("hide_fern", ["fern"]),
    ("hide_groundleaf_fern", ["groundleaf", "fern"]),
    ("hide_flowers", ["flowers"]),
    ("hide_conifers", ["conifers"]),
    ("hide_grass", ["grass"]),
]

CAMERAS = [
    "MCP_PCG_CameraBookmark_07_Corridor",
    "MCP_PCG_CameraBookmark_09_TopDown",
]


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


def _collect_components():
    watched_paths = set()
    for paths in GROUPS.values():
        watched_paths.update(paths)

    components_by_group = {name: [] for name in GROUPS}
    summary = {name: {"components": 0, "instances": 0} for name in GROUPS}

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("MCP_PCG_"):
            continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = _mesh_path(component)
            if mesh not in watched_paths:
                continue
            for group, paths in GROUPS.items():
                if mesh not in paths:
                    continue
                components_by_group[group].append(component)
                summary[group]["components"] += 1
                summary[group]["instances"] += _instance_count(component)

    return components_by_group, summary


def _set_components_visible(components, visible):
    for component in components:
        try:
            component.set_visibility(visible, True)
            component.set_hidden_in_game(not visible)
            component.mark_render_state_dirty()
        except Exception:
            pass


def _apply_scenario(components_by_group, hidden_groups):
    for components in components_by_group.values():
        _set_components_visible(components, True)
    for group in hidden_groups:
        _set_components_visible(components_by_group.get(group, []), False)


def _restore_all(components_by_group):
    for components in components_by_group.values():
        _set_components_visible(components, True)


def _camera_actors():
    actors = {}
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if label in CAMERAS:
            actors[label] = actor
    missing = [label for label in CAMERAS if label not in actors]
    if missing:
        raise RuntimeError("Missing diagnostic cameras: " + ", ".join(missing))
    return actors


def diagnose_dark_artifact_visibility():
    components_by_group, component_summary = _collect_components()
    cameras = _camera_actors()
    saved_root = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    screenshot_dir = os.path.join(saved_root, SCREENSHOT_DIR)
    os.makedirs(screenshot_dir, exist_ok=True)

    shots = []
    state = {
        "scenario_index": 0,
        "camera_index": 0,
        "last_time": 0.0,
        "handle": None,
        "completed": False,
        "error": None,
    }

    def _finish():
        _restore_all(components_by_group)
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "component_summary": component_summary,
            "scenarios": [
                {"name": name, "hidden_groups": hidden_groups}
                for name, hidden_groups in SCENARIOS
            ],
            "cameras": CAMERAS,
            "screenshots": shots,
            "restored_all_visibility": True,
            "save_attempted": False,
            "error": state["error"],
        }
        report_path = os.path.join(saved_root, REPORT_NAME)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        print(json.dumps({"report": report_path, **report}, ensure_ascii=False))

    def _tick(delta_seconds):
        now = time.time()
        if state["completed"]:
            return False
        if state["scenario_index"] > 0 or state["camera_index"] > 0:
            if now - state["last_time"] < 1.25:
                return True

        try:
            if state["scenario_index"] >= len(SCENARIOS):
                state["completed"] = True
                try:
                    unreal.unregister_slate_post_tick_callback(state["handle"])
                except Exception:
                    pass
                _finish()
                return False

            scenario_name, hidden_groups = SCENARIOS[state["scenario_index"]]
            if state["camera_index"] == 0:
                _apply_scenario(components_by_group, hidden_groups)

            camera_label = CAMERAS[state["camera_index"]]
            camera = cameras[camera_label]
            suffix = camera_label.replace("MCP_PCG_CameraBookmark_", "Bookmark")
            screenshot_path = os.path.join(
                screenshot_dir,
                f"LVL_Cubeless_PCG_Ecosystem_Field_QA_{suffix}_{scenario_name}.png",
            )
            unreal.EditorLevelLibrary.set_level_viewport_camera_info(
                camera.get_actor_location(), camera.get_actor_rotation()
            )
            requested = unreal.AutomationLibrary.take_high_res_screenshot(
                1600, 900, screenshot_path
            )
            shots.append(
                {
                    "scenario": scenario_name,
                    "hidden_groups": hidden_groups,
                    "camera": camera_label,
                    "screenshot": screenshot_path,
                    "requested": bool(requested),
                }
            )

            state["camera_index"] += 1
            if state["camera_index"] >= len(CAMERAS):
                state["camera_index"] = 0
                state["scenario_index"] += 1
            state["last_time"] = now
        except Exception as exc:
            state["completed"] = True
            state["error"] = str(exc)
            try:
                unreal.unregister_slate_post_tick_callback(state["handle"])
            except Exception:
                pass
            _finish()
            return False

        return True

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    print(
        json.dumps(
            {
                "status": "scheduled",
                "scenario_count": len(SCENARIOS),
                "camera_count": len(CAMERAS),
                "component_summary": component_summary,
                "save_attempted": False,
            },
            ensure_ascii=False,
        )
    )
    return {
        "status": "scheduled",
        "scenario_count": len(SCENARIOS),
        "camera_count": len(CAMERAS),
    }


if __name__ == "__main__":
    diagnose_dark_artifact_visibility()
