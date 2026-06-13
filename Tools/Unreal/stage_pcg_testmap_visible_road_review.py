"""Stage a visible TestMap road review ribbon over the volume-owned grass fixture.

This is a review-only visual layer. It uses the existing TestMap road source
spline from stage_pcg_testmap_volume_grass_blockmask.py, creates one procedural
road actor with duff/shoulder/core sections, and validates that the current
grass output still respects the road clearance.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIBLING_PYTHON_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless" / "Python"

if str(SIBLING_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(SIBLING_PYTHON_ROOT))

try:
    from unreal_mcp_server import UnrealConnection  # type: ignore  # noqa: E402
except ModuleNotFoundError:

    class UnrealConnection:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.host = os.environ.get("UNREAL_MCP_HOST", "127.0.0.1")
            self.port = int(os.environ.get("UNREAL_MCP_PORT", "55557"))
            self.timeout = int(os.environ.get("UNREAL_MCP_RESPONSE_TIMEOUT_SECONDS", "240"))

        def send_command(
            self,
            command: str,
            params: dict[str, Any] | None = None,
        ) -> dict[str, Any] | None:
            payload = {"type": command, "params": params or {}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.connect((self.host, self.port))
                sock.sendall(json.dumps(payload).encode("utf-8"))
                chunks: list[bytes] = []
                while True:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    try:
                        return json.loads(b"".join(chunks).decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
            return json.loads(b"".join(chunks).decode("utf-8")) if chunks else None


UNREAL_CODE_TEMPLATE = r"""
import json
import math
import os
import time

import unreal


TEST_LEVEL_PATH = "/Game/Cubeless/TestMap"
REPORT_NAME = "CubelessTestMapVisibleRoadReview.json"

ROAD_SOURCE_LABEL = "MCP_TestMap_VolumeGrass_RoadSource"
ROAD_VISUAL_LABEL = "MCP_TestMap_RoadVisual_Review"
ROAD_VISUAL_TAG = "MCPTestMapVisibleRoadReview"
VOLUME_LABEL = "MCP_TestMap_VolumeGrass_Review"
ROAD_MASK_LABEL = "MCP_TestMap_RoadClearance_Mask"
BLOCK_LABEL = "MCP_TestMap_Block_StaticMesh"

MATERIAL_FOLDER = "/Game/_MCP_Temp/PCG/Materials"
ROAD_CLEARANCE_CM = __ROAD_CLEARANCE_CM__
SAMPLE_STEP_CM = __SAMPLE_STEP_CM__
SAVE_ASSETS = __SAVE_ASSETS__
HIDE_HELPERS_FOR_GAME_VIEW = __HIDE_HELPERS_FOR_GAME_VIEW__
SETTLE_SECONDS = 30.0
PLANE_MESH = "/Engine/BasicShapes/Plane.Plane"

CROSS_VALUES = [-0.5, -0.36, -0.22, 0.0, 0.22, 0.36, 0.5]
LAYERS = [
    {
        "name": "DuffEdge",
        "section": 0,
        "material": "M_MCP_TestMap_RoadVisual_DuffEdge",
        "base_color": (0.028, 0.052, 0.024, 1.0),
        "roughness": 0.99,
        "specular": 0.006,
        "width": 1960.0,
        "z_offset": 7.0,
        "uv_scale": 900.0,
    },
    {
        "name": "Shoulder",
        "section": 1,
        "material": "M_MCP_TestMap_RoadVisual_Shoulder",
        "base_color": (0.060, 0.050, 0.034, 1.0),
        "roughness": 0.985,
        "specular": 0.008,
        "width": 1520.0,
        "z_offset": 9.0,
        "uv_scale": 820.0,
    },
    {
        "name": "Core",
        "section": 2,
        "material": "M_MCP_TestMap_RoadVisual_Core",
        "base_color": (0.082, 0.058, 0.036, 1.0),
        "roughness": 0.975,
        "specular": 0.01,
        "width": 1040.0,
        "z_offset": 11.0,
        "uv_scale": 760.0,
    },
]


def _get_editor_world():
    subsystem_cls = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_cls:
        try:
            subsystem = unreal.get_editor_subsystem(subsystem_cls)
            world = subsystem.get_editor_world() if subsystem else None
            if world:
                return world
        except Exception:
            pass
    return unreal.EditorLevelLibrary.get_editor_world()


def _load_test_map():
    world = _get_editor_world()
    if not world or not world.get_path_name().startswith(TEST_LEVEL_PATH + "."):
        unreal.EditorLevelLibrary.load_level(TEST_LEVEL_PATH)
    return _get_editor_world()


def _all_level_actors():
    subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if subsystem_cls:
        subsystem = unreal.get_editor_subsystem(subsystem_cls)
        if subsystem:
            return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def _actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def _find_actor(label):
    for actor in _all_level_actors():
        if _actor_label(actor) == label:
            return actor
    return None


def _load_asset(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        asset = unreal.load_object(None, path)
    return asset


def _ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _object_path(package_path):
    name = package_path.rsplit("/", 1)[-1]
    return package_path + "." + name


def _make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def _expr(material, cls, x, y):
    return unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)


def _ensure_material(layer):
    _ensure_directory(MATERIAL_FOLDER)
    package_path = MATERIAL_FOLDER + "/" + layer["material"]
    material = _load_asset(package_path)
    created = False
    if not material:
        factory_cls = getattr(unreal, "MaterialFactoryNew", None)
        if not factory_cls:
            raise RuntimeError("MaterialFactoryNew is unavailable")
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            layer["material"],
            MATERIAL_FOLDER,
            unreal.Material,
            factory_cls(),
        )
        created = bool(material)
    if not material:
        raise RuntimeError("Failed to create/load material: " + package_path)

    lib = unreal.MaterialEditingLibrary
    lib.delete_all_material_expressions(material)
    try:
        material.set_editor_property("two_sided", True)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
        material.set_editor_property("use_material_attributes", False)
    except Exception:
        pass

    base = _expr(material, unreal.MaterialExpressionConstant3Vector, -420, -120)
    base.set_editor_property("constant", unreal.LinearColor(*layer["base_color"]))
    lib.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = _expr(material, unreal.MaterialExpressionConstant, -420, 40)
    rough.set_editor_property("r", float(layer["roughness"]))
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    spec = _expr(material, unreal.MaterialExpressionConstant, -420, 180)
    spec.set_editor_property("r", float(layer["specular"]))
    lib.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)

    try:
        lib.layout_material_expressions(material)
    except Exception:
        pass
    try:
        lib.recompile_material(material)
    except Exception:
        pass
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(material, False)) if SAVE_ASSETS else False
    return {
        "material": material,
        "path": package_path,
        "created": created,
        "saved": saved,
    }


def _find_road_spline():
    actor = _find_actor(ROAD_SOURCE_LABEL)
    if not actor:
        raise RuntimeError(
            "Missing TestMap road source actor. Run stage_pcg_testmap_volume_grass_blockmask.py first."
        )
    splines = list(actor.get_components_by_class(unreal.SplineComponent))
    for spline in splines:
        if spline.get_name() == "Road_SourceSpline":
            return actor, spline
    if splines:
        return actor, splines[0]
    raise RuntimeError("Road source actor has no SplineComponent")


def _road_points_from_spline(spline):
    length = float(spline.get_spline_length())
    if length < 100.0:
        raise RuntimeError("Road spline is too short: {:.2f}".format(length))
    sample_count = max(2, int(math.ceil(length / max(SAMPLE_STEP_CM, 50.0))) + 1)
    points = []
    for index in range(sample_count):
        distance = min(length, (length * index) / float(sample_count - 1))
        location = spline.get_location_at_distance_along_spline(
            distance,
            unreal.SplineCoordinateSpace.WORLD,
        )
        points.append((float(location.x), float(location.y), float(location.z), distance))
    return points, length


def _control_points(spline):
    points = []
    for index in range(int(spline.get_number_of_spline_points())):
        location = spline.get_location_at_spline_point(index, unreal.SplineCoordinateSpace.WORLD)
        points.append((float(location.x), float(location.y), float(location.z)))
    return points


def _delete_existing_visuals():
    deleted = []
    for actor in list(_all_level_actors()):
        if not _actor_label(actor).startswith(ROAD_VISUAL_LABEL):
            continue
        try:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            deleted.append(_actor_label(actor))
        except Exception:
            pass
    return deleted


def _safe_normalize_xy(x, y):
    length = math.sqrt(x * x + y * y)
    if length <= 1.0e-6:
        return 1.0, 0.0
    return x / length, y / length


def _tangent(points, index):
    if index <= 0:
        a = points[0]
        b = points[1]
    elif index >= len(points) - 1:
        a = points[-2]
        b = points[-1]
    else:
        a = points[index - 1]
        b = points[index + 1]
    return _safe_normalize_xy(b[0] - a[0], b[1] - a[1])


def _center_origin(points):
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    return unreal.Vector((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, 0.0)


def _ignore_actors_for_trace():
    ignored = []
    for actor in _all_level_actors():
        label = _actor_label(actor)
        if (
            label.startswith(ROAD_VISUAL_LABEL)
            or label in (ROAD_MASK_LABEL, BLOCK_LABEL)
            or label.startswith("PCG_ModularBuilding_")
        ):
            ignored.append(actor)
    return ignored


def _sample_landscape(world, x, y, fallback_z, ignored):
    start = unreal.Vector(float(x), float(y), 80000.0)
    end = unreal.Vector(float(x), float(y), -20000.0)
    try:
        hits = unreal.SystemLibrary.line_trace_multi(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            ignored,
            unreal.DrawDebugTrace.NONE,
            True,
        )
    except Exception:
        hits = []

    for hit in hits:
        values = hit.to_tuple()
        if not values or not bool(values[0]):
            continue
        actor = values[9] if len(values) > 9 else None
        component = values[10] if len(values) > 10 else None
        actor_text = ""
        component_text = ""
        try:
            actor_text = actor.get_actor_label() + " " + actor.get_class().get_name()
        except Exception:
            pass
        try:
            component_text = component.get_name() + " " + component.get_class().get_name()
        except Exception:
            pass
        if "Landscape" not in actor_text and "Landscape" not in component_text:
            continue
        location = values[4]
        normal = values[7] if len(values) > 7 else unreal.Vector(0.0, 0.0, 1.0)
        return float(location.z), normal, True

    return float(fallback_z), unreal.Vector(0.0, 0.0, 1.0), False


def _make_tangent(x, y, z=0.0):
    tangent = unreal.ProcMeshTangent()
    tangent.set_editor_property("tangent_x", unreal.Vector(float(x), float(y), float(z)))
    return tangent


def _spawn_visual_actor(origin):
    actor_cls = getattr(unreal, "ProceduralMeshActor", None)
    component_cls = getattr(unreal, "ProceduralMeshComponent", None)
    if not actor_cls or not component_cls:
        return None, None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_cls, origin, _make_rotator())
    if not actor:
        raise RuntimeError("Failed to spawn ProceduralMeshActor")
    actor.set_actor_label(ROAD_VISUAL_LABEL)
    actor.set_editor_property("tags", [unreal.Name(ROAD_VISUAL_TAG), unreal.Name("MCPValidation")])
    try:
        actor.set_folder_path("MCP/TestMap/VisibleRoad")
    except Exception:
        pass
    component = actor.get_component_by_class(component_cls)
    if not component:
        raise RuntimeError("ProceduralMeshActor missing ProceduralMeshComponent")
    try:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("collision_profile_name", "NoCollision")
        component.set_editor_property("bounds_scale", 2.0)
    except Exception:
        pass
    return actor, component


def _layer_center_and_yaw(control_points):
    if len(control_points) < 2:
        raise RuntimeError("Road control points are missing")
    a = control_points[0]
    b = control_points[-1]
    center = unreal.Vector((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
    dx = float(b[0] - a[0])
    dy = float(b[1] - a[1])
    length = math.sqrt(dx * dx + dy * dy)
    yaw = math.degrees(math.atan2(dy, dx))
    return center, yaw, length


def _spawn_static_layer(layer, material, control_points, world, ignored):
    center, yaw, length = _layer_center_and_yaw(control_points)
    ground_z, _normal, _hit = _sample_landscape(world, center.x, center.y, center.z, ignored)
    location = unreal.Vector(center.x, center.y, ground_z + float(layer["z_offset"]))
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        location,
        _make_rotator(0.0, yaw, 0.0),
    )
    if not actor:
        raise RuntimeError("Failed to spawn static road layer: " + layer["name"])
    actor.set_actor_label(ROAD_VISUAL_LABEL + "_" + layer["name"])
    actor.set_editor_property("tags", [unreal.Name(ROAD_VISUAL_TAG), unreal.Name("MCPValidation")])
    try:
        actor.set_folder_path("MCP/TestMap/VisibleRoad")
    except Exception:
        pass
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        raise RuntimeError("Static road layer missing StaticMeshComponent: " + layer["name"])
    component.set_static_mesh(_load_asset(PLANE_MESH))
    component.set_material(0, material)
    try:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("collision_profile_name", "NoCollision")
    except Exception:
        pass
    actor.set_actor_scale3d(
        unreal.Vector(
            max(float(length) / 100.0, 1.0),
            max(float(layer["width"]) / 100.0, 1.0),
            1.0,
        )
    )
    return {
        "name": layer["name"],
        "mode": "static_mesh_plane_rect",
        "actor": _actor_label(actor),
        "width": float(layer["width"]),
        "length": round(float(length), 2),
        "z_offset": float(layer["z_offset"]),
        "vertex_count": 4,
        "triangle_count": 2,
        "trace_misses": 0,
    }


def _build_layer_section(component, layer, material, points, origin, world, ignored):
    width = float(layer["width"])
    z_offset = float(layer["z_offset"])
    uv_scale = max(1.0, float(layer["uv_scale"]))

    vertices = []
    triangles = []
    normals = []
    uv0 = []
    colors = []
    tangents = []
    trace_misses = 0

    for index, point in enumerate(points):
        tx, ty = _tangent(points, index)
        nx, ny = -ty, tx
        v = point[3] / uv_scale
        for cross in CROSS_VALUES:
            x = point[0] + nx * width * float(cross)
            y = point[1] + ny * width * float(cross)
            z, normal, hit = _sample_landscape(world, x, y, point[2], ignored)
            if not hit:
                trace_misses += 1
            vertex = unreal.Vector(x - origin.x, y - origin.y, z + z_offset)
            vertices.append(vertex)
            try:
                normal.normalize()
            except Exception:
                normal = unreal.Vector(0.0, 0.0, 1.0)
            normals.append(normal)
            uv0.append(unreal.Vector2D(float(cross) + 0.5, v))
            colors.append(unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
            tangents.append(_make_tangent(tx, ty, 0.0))

    column_count = len(CROSS_VALUES)
    for index in range(len(points) - 1):
        row0 = index * column_count
        row1 = row0 + column_count
        for column in range(column_count - 1):
            a = row0 + column
            b = row0 + column + 1
            c = row1 + column
            d = row1 + column + 1
            triangles.extend([a, c, b, b, c, d])

    section = int(layer["section"])
    component.create_mesh_section_linear_color(
        section,
        vertices,
        triangles,
        normals,
        uv0,
        [],
        [],
        [],
        colors,
        tangents,
        False,
        False,
    )
    component.set_material(section, material)
    return {
        "name": layer["name"],
        "section": section,
        "width": width,
        "z_offset": z_offset,
        "vertex_count": len(vertices),
        "triangle_count": int(len(triangles) / 3),
        "trace_misses": trace_misses,
    }


def _mesh_path(component):
    try:
        mesh = component.get_editor_property("static_mesh")
        if mesh and hasattr(mesh, "get_path_name"):
            return mesh.get_path_name()
    except Exception:
        pass
    return ""


def _component_category(component):
    text = (component.get_name() + " " + _mesh_path(component)).lower()
    if any(token in text for token in ("grass", "fern", "groundleaf", "flower", "leaf", "foliage", "plant")):
        return "grass"
    if any(token in text for token in ("tree", "pine", "spruce", "conifer", "trunk")):
        return "tree"
    if any(token in text for token in ("rock", "stone", "boulder")):
        return "rock"
    return "other"


def _instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def _road_distance_xy(x, y, points):
    if len(points) < 2:
        return None
    best = 10**18
    for index in range(len(points) - 1):
        ax, ay, _az = points[index]
        bx, by, _bz = points[index + 1]
        dx = bx - ax
        dy = by - ay
        length_sq = dx * dx + dy * dy
        if length_sq <= 0.001:
            continue
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / length_sq))
        px = ax + dx * t
        py = ay + dy * t
        best = min(best, math.sqrt((x - px) ** 2 + (y - py) ** 2))
    return best if best < 10**18 else None


def _validate_grass_clearance(control_points):
    volume = _find_actor(VOLUME_LABEL)
    if not volume:
        return {"pass": False, "reason": "missing volume actor", "grass": 0}
    summary = {
        "actor": _actor_label(volume),
        "instances": {"all": 0, "grass": 0, "tree": 0, "rock": 0, "other": 0},
        "road_clearance_cm": ROAD_CLEARANCE_CM,
        "road_clearance_violations": 0,
        "road_violation_samples": [],
    }
    for component in volume.get_components_by_class(unreal.InstancedStaticMeshComponent):
        count = _instance_count(component)
        if count <= 0:
            continue
        category = _component_category(component)
        summary["instances"]["all"] += count
        summary["instances"][category] += count
        if category != "grass":
            continue
        for index in range(count):
            transform = component.get_instance_transform(index, True)
            location = transform.translation
            distance = _road_distance_xy(float(location.x), float(location.y), control_points)
            if distance is not None and distance < ROAD_CLEARANCE_CM:
                summary["road_clearance_violations"] += 1
                if len(summary["road_violation_samples"]) < 20:
                    summary["road_violation_samples"].append(
                        {"component": component.get_name(), "index": index, "distance": round(distance, 2)}
                    )
    summary["pass"] = summary["instances"].get("grass", 0) > 0 and summary["road_clearance_violations"] == 0
    return summary


def _stabilize_grass_clearance(control_points):
    deadline = time.time() + max(float(SETTLE_SECONDS), 1.0)
    latest = None
    snapshots = []
    last_grass = None
    stable_ticks = 0
    while time.time() <= deadline:
        time.sleep(1.0)
        latest = _validate_grass_clearance(control_points)
        grass_count = latest["instances"].get("grass", 0)
        snapshots.append({"time": round(time.time(), 3), "grass": grass_count})
        if grass_count <= 0:
            stable_ticks = 0
            last_grass = grass_count
            continue
        if grass_count == last_grass:
            stable_ticks += 1
            if stable_ticks >= 2:
                break
        else:
            stable_ticks = 0
            last_grass = grass_count
    if latest is None:
        latest = _validate_grass_clearance(control_points)
    latest["stabilization"] = {
        "stable_ticks": stable_ticks,
        "snapshots": snapshots[-10:],
    }
    return latest


def _hide_helper_masks_for_game_view():
    changed = []
    if not HIDE_HELPERS_FOR_GAME_VIEW:
        return changed
    for label in (ROAD_MASK_LABEL, BLOCK_LABEL):
        actor = _find_actor(label)
        if not actor:
            continue
        try:
            actor.set_is_temporarily_hidden_in_editor(True)
        except Exception:
            pass
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            entry = {"actor": label, "component": component.get_name()}
            try:
                component.set_visibility(True, True)
                component.set_hidden_in_game(False)
                entry["visibility_preserved_for_pcg"] = True
            except Exception as exc:
                entry["visibility_preserved_for_pcg"] = False
                entry["error"] = str(exc)
            changed.append(entry)
    return changed


def _dirty_packages():
    dirty = []
    try:
        dirty.extend(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
        dirty.extend(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    except Exception:
        return []
    return [package.get_name() for package in dirty]


def _report_path():
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_RoadPCG")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, REPORT_NAME)


def _write_report(report):
    path = _report_path()
    report["report_path"] = path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("Cubeless TestMap visible road review report: {}".format(path))
    print(json.dumps(report, ensure_ascii=False))
    return path


def run():
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    world = _load_test_map()
    dirty_before = _dirty_packages()
    road_actor, spline = _find_road_spline()
    sample_points, spline_length = _road_points_from_spline(spline)
    control_points = _control_points(spline)
    origin = _center_origin(sample_points)

    deleted = _delete_existing_visuals()
    ignored = _ignore_actors_for_trace()
    actor, component = _spawn_visual_actor(origin)
    visual_mode = "procedural_mesh" if component else "static_mesh_plane_rect_layers"
    if actor:
        ignored.append(actor)

    material_reports = []
    layer_reports = []
    for layer in LAYERS:
        material_info = _ensure_material(layer)
        material_reports.append({key: value for key, value in material_info.items() if key != "material"})
        if component:
            layer_reports.append(
                _build_layer_section(
                    component,
                    layer,
                    material_info["material"],
                    sample_points,
                    origin,
                    world,
                    ignored,
                )
            )
        else:
            layer_reports.append(
                _spawn_static_layer(layer, material_info["material"], control_points, world, ignored)
            )

    validation = _stabilize_grass_clearance(control_points)
    helper_visibility = _hide_helper_masks_for_game_view()
    if component:
        try:
            section_count = int(component.get_num_sections())
        except Exception:
            section_count = len(layer_reports)
    else:
        section_count = len(layer_reports)

    trace_misses = sum(row.get("trace_misses", 0) for row in layer_reports)
    report = {
        "success": True,
        "timestamp": started,
        "world": world.get_path_name() if world else "",
        "road_actor": _actor_label(road_actor),
        "spline_component": spline.get_name(),
        "spline_point_count": int(spline.get_number_of_spline_points()),
        "spline_length": round(float(spline_length), 2),
        "sample_step_cm": SAMPLE_STEP_CM,
        "sample_count": len(sample_points),
        "visual_mode": visual_mode,
        "road_visual_actor": _actor_label(actor) if actor else None,
        "road_visual_actors": [
            row.get("actor") for row in layer_reports if row.get("actor")
        ] or ([_actor_label(actor)] if actor else []),
        "road_visual_tags": [str(tag) for tag in actor.get_editor_property("tags")] if actor else [ROAD_VISUAL_TAG, "MCPValidation"],
        "procedural_section_count": section_count,
        "deleted_previous_visuals": deleted,
        "materials": material_reports,
        "layers": layer_reports,
        "helper_visibility": helper_visibility,
        "grass_clearance_validation": validation,
        "dirty_before": dirty_before,
        "dirty_after": _dirty_packages(),
    }
    report["pass"] = (
        section_count == len(LAYERS)
        and trace_misses == 0
        and validation.get("pass") is True
        and int(report["spline_point_count"]) >= 2
    )
    _write_report(report)


run()
"""


def command_succeeded(response: dict[str, Any] | None) -> bool:
    if not response:
        return False
    return response.get("status") == "success" or response.get("success") is True


def response_result(response: dict[str, Any] | None) -> dict[str, Any]:
    if not response:
        return {}
    result = response.get("result", response)
    return result if isinstance(result, dict) else {"result": result}


def parse_response(response: dict[str, Any] | None) -> dict[str, Any]:
    result = response_result(response)
    parsed_logs: list[dict[str, Any]] = []
    for log_item in result.get("logs", []):
        if not isinstance(log_item, dict):
            continue
        output = str(log_item.get("output", "")).strip()
        if not output.startswith("{"):
            continue
        try:
            parsed_logs.append(json.loads(output))
        except json.JSONDecodeError:
            continue
    if parsed_logs:
        parsed = parsed_logs[-1]
        parsed["unreal_execute_summary"] = {
            "success": result.get("success"),
            "command_result": result.get("command_result"),
            "log_count": len(result.get("logs", [])),
        }
        return parsed
    return result


def build_unreal_code(args: argparse.Namespace) -> str:
    return (
        UNREAL_CODE_TEMPLATE.replace("__ROAD_CLEARANCE_CM__", repr(float(args.road_clearance_cm)))
        .replace("__SAMPLE_STEP_CM__", repr(float(args.sample_step_cm)))
        .replace("__SAVE_ASSETS__", "True" if args.save_assets else "False")
        .replace(
            "__HIDE_HELPERS_FOR_GAME_VIEW__",
            "True" if args.hide_helpers_for_game_view else "False",
        )
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    code = build_unreal_code(args)
    response = UnrealConnection().send_command(
        "execute_python",
        {
            "code": "exec({})".format(repr(code)),
            "mode": "ExecuteStatement",
            "description": "Stage visible TestMap road review ribbon",
        },
    )
    if not command_succeeded(response):
        raise RuntimeError(f"execute_python failed: {json.dumps(response, ensure_ascii=False)}")
    return parse_response(response)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage TestMap visible road review ribbon.")
    parser.add_argument("--road-clearance-cm", type=float, default=650.0)
    parser.add_argument("--sample-step-cm", type=float, default=280.0)
    parser.add_argument(
        "--save-assets",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save generated _MCP_Temp road visual materials.",
    )
    parser.add_argument(
        "--hide-helpers-for-game-view",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Hide helper mask meshes in game view after validation for clean screenshots.",
    )
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(parse_args()), ensure_ascii=False))


if __name__ == "__main__":
    main()
