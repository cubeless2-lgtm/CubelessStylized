"""Build a dense ground-carpet PCG fill layer for the Cubeless field level."""

import json
import math
import os
import random
import time

import unreal


PREFIX = "MCP_PCG_GroundCarpetFillLayer"
REPORT_NAME = "CubelessGroundCarpetFill_Report.json"
WAIT_SECONDS = 45.0
STATE_ATTR = "_cubeless_ground_carpet_fill_state"

BP_CLASS_PATH = (
    "/Game/Cubeless/PCG/ProductionCandidates/Blueprints/"
    "BP_Cubeless_PCG_EcosystemCandidate.BP_Cubeless_PCG_EcosystemCandidate_C"
)

GRAPHS = {
    "ClassicGrass": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_ClassicGrass_Both_GroundDense_DitchDense"
    ),
    "MixedGrass": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_MixedGrass_Both_GroundDense_DitchDense"
    ),
    "TallGrass": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_TallGrass_Both_GroundDense_DitchDense"
    ),
    "GroundFoliage": (
        "/Game/Cubeless/PCG/ElectricDreamsLearning/"
        "DesignerStyleProfileMatrixCombos/"
        "PCG_Cubeless_ED_StyleProfileMatrix_GroundFoliage_Both_GroundDense_DitchDense"
    ),
}

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


def _road_offset_points(step=850.0):
    points = []
    offsets = [1700.0, 2250.0, 2850.0]
    for ax, ay, dx, dy, length in ROAD_SEGMENTS:
        nx = -dy / length
        ny = dx / length
        samples = max(1, int(length / step))
        for sample in range(samples + 1):
            t = sample / float(samples)
            cx = ax + dx * t
            cy = ay + dy * t
            for side in [-1.0, 1.0]:
                for offset in offsets:
                    points.append((cx + nx * side * offset, cy + ny * side * offset, "RoadFeather"))
    return points


def _weighted_graph_name(index, kind):
    if kind == "RoadFeather":
        pattern = ["ClassicGrass", "ClassicGrass", "MixedGrass", "TallGrass"]
    else:
        pattern = [
            "ClassicGrass",
            "ClassicGrass",
            "MixedGrass",
            "TallGrass",
            "ClassicGrass",
            "MixedGrass",
        ]
    return pattern[index % len(pattern)]


def _existing_actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def _delete_existing_layer(actors):
    deleted = 0
    for actor in actors:
        if not actor.get_actor_label().startswith(PREFIX):
            continue
        for component in actor.get_components_by_class(unreal.PCGComponent):
            try:
                component.cleanup(True)
            except Exception:
                pass
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted += 1
        except Exception:
            pass
    return deleted


def _z_references(actors):
    refs = []
    for actor in actors:
        label = actor.get_actor_label()
        if label.startswith(PREFIX):
            continue
        if not label.startswith("MCP_PCG_"):
            continue
        location = actor.get_actor_location()
        refs.append((location.x, location.y, location.z))
    return refs


def _nearest_z(x, y, refs):
    if not refs:
        return 0.0
    best = None
    best_dist = 10**18
    for rx, ry, rz in refs:
        distance = (x - rx) * (x - rx) + (y - ry) * (y - ry)
        if distance < best_dist:
            best = rz
            best_dist = distance
    return best if best is not None else 0.0


def _candidate_points():
    rng = random.Random(6102026)
    points = []
    occupied = set()

    def add_point(x, y, kind, min_road_distance):
        jitter = 0.0 if kind == "RoadFeather" else 180.0
        if jitter:
            x += rng.uniform(-jitter, jitter)
            y += rng.uniform(-jitter, jitter)
        if _road_distance(x, y) < min_road_distance:
            return
        if not (2500.0 <= x <= 48500.0 and -1000.0 <= y <= 52500.0):
            return
        key = (int(round(x / 350.0)), int(round(y / 350.0)))
        if key in occupied:
            return
        occupied.add(key)
        points.append((x, y, kind))

    for x in range(3500, 47501, 900):
        for y in range(0, 52001, 900):
            add_point(float(x), float(y), "ForestCarpet", 2400.0)

    for x, y, kind in _road_offset_points():
        add_point(x, y, kind, 1350.0)

    return points


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
    except Exception:
        mesh = None
    if hasattr(mesh, "get_path_name"):
        return mesh.get_path_name()
    return str(mesh)


def _classify(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(token in text for token in ["tree", "pine", "spruce", "conifer", "trunk"]):
        return "tree"
    if any(token in text for token in ["rock", "stone", "boulder"]):
        return "rock"
    if any(token in text for token in ["grass", "foliage", "leaf", "leaves", "fern", "plant", "flower"]):
        return "grass"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _instance_location(component, index):
    try:
        return component.get_instance_transform(index, True).translation
    except Exception:
        return None


def _configure_pcg_actor(actor, graph, seed):
    results = []
    components = list(actor.get_components_by_class(unreal.PCGComponent))

    for component in components:
        name = component.get_name()
        if name == "PCG_Style":
            continue
        entry = {"component": name}
        try:
            component.cleanup(True)
        except Exception as exc:
            entry["cleanup_error"] = str(exc)
        try:
            component.deactivate()
        except Exception:
            pass
        entry["configured"] = False
        entry["disabled"] = True
        results.append(entry)

    for component in components:
        name = component.get_name()
        if name != "PCG_Style":
            continue
        entry = {"component": name}
        try:
            component.cleanup(True)
        except Exception as exc:
            entry["cleanup_error"] = str(exc)
        try:
            component.activate(True)
            component.set_graph(graph)
            try:
                component.set_editor_property("seed", seed)
            except Exception:
                pass
            entry["configured"] = True
        except Exception as exc:
            entry["configured"] = False
            entry["error"] = str(exc)
        results.append(entry)
    return results


def _make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _generate_style_components():
    results = []
    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]
    for actor in actors:
        for component in actor.get_components_by_class(unreal.PCGComponent):
            if component.get_name() != "PCG_Style":
                continue
            entry = {"actor": actor.get_actor_label(), "component": component.get_name()}
            try:
                component.activate(True)
                component.cleanup(True)
                component.generate(True)
                try:
                    component.generate_local(True)
                except Exception as local_exc:
                    entry["generate_local_error"] = str(local_exc)
                entry["generated"] = True
            except Exception as exc:
                entry["generated"] = False
                entry["error"] = str(exc)
            results.append(entry)
    return results


def _spawn_layer(points, refs, actor_class, graphs):
    rng = random.Random(6112026)
    spawn_results = []
    for index, (x, y, kind) in enumerate(points):
        graph_name = _weighted_graph_name(index, kind)
        graph = graphs[graph_name]
        z = _nearest_z(x, y, refs)
        yaw = rng.uniform(0.0, 360.0)
        label = f"{PREFIX}_{index:04d}_{kind}_{graph_name}"
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            actor_class,
            unreal.Vector(x, y, z),
            _make_rotator(0.0, yaw, 0.0),
        )
        if not actor:
            spawn_results.append({"label": label, "spawned": False})
            continue
        actor.set_actor_label(label)
        component_results = _configure_pcg_actor(actor, graph, 6102026 + index)
        spawn_results.append(
            {
                "label": label,
                "kind": kind,
                "graph": graph_name,
                "x": round(x, 1),
                "y": round(y, 1),
                "z": round(z, 1),
                "road_distance": round(_road_distance(x, y), 1),
                "component_results": component_results,
            }
        )
    return spawn_results


def _summarize_layer():
    actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX)
    ]
    summary = {
        "actor_count": len(actors),
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "grass_within_900": 0,
        "grass_within_1400": 0,
        "tree_within_2400": 0,
        "rock_within_2400": 0,
        "zero_actor_count": 0,
        "zero_actor_sample": [],
    }
    samples = []

    for actor in actors:
        actor_total = 0
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            count = _instance_count(component)
            category = _classify(component)
            actor_total += count
            summary["instances"]["all"] += count
            summary["instances"][category] += count

            for index in range(count):
                location = _instance_location(component, index)
                if not location:
                    continue
                distance = _road_distance(location.x, location.y)
                if category == "grass":
                    if distance < 900.0:
                        summary["grass_within_900"] += 1
                    if distance < 1400.0:
                        summary["grass_within_1400"] += 1
                elif category == "tree" and distance < 2400.0:
                    summary["tree_within_2400"] += 1
                elif category == "rock" and distance < 2400.0:
                    summary["rock_within_2400"] += 1
                if distance < 1400.0 and len(samples) < 20:
                    samples.append(
                        {
                            "actor": actor.get_actor_label(),
                            "component": component.get_name(),
                            "class": category,
                            "distance": round(distance, 1),
                        }
                    )

        if actor_total == 0:
            summary["zero_actor_count"] += 1
            if len(summary["zero_actor_sample"]) < 20:
                summary["zero_actor_sample"].append(actor.get_actor_label())

    summary["near_road_samples"] = samples
    return summary


def _finish(state):
    summary = _summarize_layer()
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        save_attempted = True
    except Exception as exc:
        save_attempted = "failed: " + str(exc)

    spawn_results = state.get("spawn_results", [])
    generation_results = state.get("generation_results", [])
    failed_spawns = [entry for entry in spawn_results if not entry.get("spawned", True)]
    failed_generations = [
        entry for entry in generation_results if not entry.get("generated")
    ]
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "wait_seconds": WAIT_SECONDS,
        "deleted_existing": state.get("deleted_existing", 0),
        "candidate_count": state.get("candidate_count", 0),
        "spawn_count": len(spawn_results) - len(failed_spawns),
        "failed_spawn_count": len(failed_spawns),
        "generation_count": len(generation_results),
        "generation_failed_count": len(failed_generations),
        "spawn_sample": spawn_results[:30],
        "summary": summary,
        "save_attempted": save_attempted,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report


def build_ground_carpet_fill():
    previous_state = getattr(unreal, STATE_ATTR, None)
    if previous_state and previous_state.get("handle") is not None:
        try:
            unreal.unregister_slate_post_tick_callback(previous_state["handle"])
        except Exception:
            pass

    actor_class = unreal.load_object(None, BP_CLASS_PATH)
    if not actor_class:
        raise RuntimeError("Failed to load actor class: " + BP_CLASS_PATH)

    graphs = {}
    for name, path in GRAPHS.items():
        graph = unreal.load_object(None, path)
        if not graph:
            raise RuntimeError("Failed to load graph: " + path)
        graphs[name] = graph

    actors = _existing_actors()
    refs = _z_references(actors)
    deleted_existing = _delete_existing_layer(actors)
    points = _candidate_points()
    spawn_results = _spawn_layer(points, refs, actor_class, graphs)
    generation_results = _generate_style_components()

    state = {
        "started_at": time.time(),
        "handle": None,
        "completed": False,
        "deleted_existing": deleted_existing,
        "candidate_count": len(points),
        "spawn_results": spawn_results,
        "generation_results": generation_results,
    }

    def _tick(delta_seconds):
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
            state["final_report"] = _finish(state)
        except Exception as exc:
            state["error"] = str(exc)
            print(
                json.dumps(
                    {
                        "prefix": PREFIX,
                        "status": "failed",
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
        return False

    state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    setattr(unreal, STATE_ATTR, state)

    scheduled = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prefix": PREFIX,
        "status": "scheduled",
        "deleted_existing": deleted_existing,
        "candidate_count": len(points),
        "spawn_count": len(spawn_results),
        "generation_count": len(generation_results),
        "generation_failed_count": len(
            [entry for entry in generation_results if not entry.get("generated")]
        ),
        "wait_seconds": WAIT_SECONDS,
    }
    print(json.dumps(scheduled, ensure_ascii=False))
    return scheduled


if __name__ == "__main__":
    build_ground_carpet_fill()
