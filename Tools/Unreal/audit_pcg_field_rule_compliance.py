"""Audit the Cubeless field level against current PCG production rules.

This runner talks to the UnrealMCP bridge and keeps the report under Saved.
`--fix` only applies non-destructive repairs that are safe to repeat:
tree/rock instance pitch-roll clamping and accidental two-point spline closed
loop correction. It never creates or overwrites viewport bookmark slots.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import textwrap
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
            self.timeout = int(os.environ.get("UNREAL_MCP_RESPONSE_TIMEOUT_SECONDS", "120"))

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
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    try:
                        return json.loads(b"".join(chunks).decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
            return json.loads(b"".join(chunks).decode("utf-8")) if chunks else None


UNREAL_AUDIT_CODE = r"""
import json
import math
import os
import time

import unreal


FIELD_LEVEL_PATH = "/Game/Cubeless/Map/LVL_Cubeless_PCG_Ecosystem_Field"
REPORT_NAME = "pcg_field_rule_compliance_report.json"
FIX_MODE = __FIX_MODE__
GRASS_SAMPLE_LIMIT = __GRASS_SAMPLE_LIMIT__
TILT_LIMIT_DEG = 5.0
TILT_FIX_LIMIT_DEG = 4.9
GRASS_NORMAL_P95_LIMIT_DEG = 10.0
WORLD_UP = unreal.Vector(0.0, 0.0, 1.0)


def get_editor_world():
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


def all_level_actors():
    subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if subsystem_cls:
        subsystem = unreal.get_editor_subsystem(subsystem_cls)
        if subsystem:
            return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def object_path(obj):
    if hasattr(obj, "get_path_name"):
        return obj.get_path_name()
    return str(obj) if obj else ""


def mesh_path(component):
    try:
        return object_path(component.get_editor_property("static_mesh"))
    except Exception:
        return ""


def component_category(component):
    text = (component.get_name() + " " + mesh_path(component)).lower()
    if any(token in text for token in ("tree", "pine", "spruce", "conifer", "trunk")):
        return "tree"
    if any(token in text for token in ("rock", "stone", "boulder")):
        return "rock"
    if any(token in text for token in ("grass", "fern", "groundleaf", "flower", "leaf", "foliage", "plant")):
        return "grass"
    return "other"


def instance_count(component):
    try:
        return int(component.get_instance_count())
    except Exception:
        return 0


def vector_size(vector):
    return math.sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z)


def normalized(vector, fallback=None):
    size = vector_size(vector)
    if size <= 1.0e-6:
        return fallback or WORLD_UP
    return unreal.Vector(vector.x / size, vector.y / size, vector.z / size)


def angle_degrees(a, b):
    aa = normalized(a)
    bb = normalized(b)
    dot = max(-1.0, min(1.0, aa.x * bb.x + aa.y * bb.y + aa.z * bb.z))
    return math.degrees(math.acos(dot))


def quat_up(quat):
    try:
        return normalized(unreal.MathLibrary.quat_rotate_vector(quat, WORLD_UP))
    except Exception:
        x, y, z, w = quat.x, quat.y, quat.z, quat.w
        return normalized(
            unreal.Vector(
                2.0 * (x * z + w * y),
                2.0 * (y * z - w * x),
                1.0 - 2.0 * (x * x + y * y),
            )
        )


def rotated_axis(quat, axis):
    try:
        return normalized(unreal.MathLibrary.quat_rotate_vector(quat, axis))
    except Exception:
        x, y, z, w = quat.x, quat.y, quat.z, quat.w
        vx, vy, vz = axis.x, axis.y, axis.z
        # Quaternion-vector multiply expanded to avoid depending on Python
        # overloads that differ across Unreal builds.
        tx = 2.0 * (y * vz - z * vy)
        ty = 2.0 * (z * vx - x * vz)
        tz = 2.0 * (x * vy - y * vx)
        return normalized(
            unreal.Vector(
                vx + w * tx + (y * tz - z * ty),
                vy + w * ty + (z * tx - x * tz),
                vz + w * tz + (x * ty - y * tx),
            )
        )


def best_axis_alignment(quat, normal):
    axes = [
        ("+X", unreal.Vector(1.0, 0.0, 0.0)),
        ("-X", unreal.Vector(-1.0, 0.0, 0.0)),
        ("+Y", unreal.Vector(0.0, 1.0, 0.0)),
        ("-Y", unreal.Vector(0.0, -1.0, 0.0)),
        ("+Z", unreal.Vector(0.0, 0.0, 1.0)),
        ("-Z", unreal.Vector(0.0, 0.0, -1.0)),
    ]
    best = None
    for label, axis in axes:
        angle = angle_degrees(rotated_axis(quat, axis), normal)
        if best is None or angle < best[1]:
            best = (label, angle)
    return best or ("unknown", 180.0)


def norm_angle(value):
    while value > 180.0:
        value -= 360.0
    while value < -180.0:
        value += 360.0
    return value


def make_rotator(pitch, yaw, roll):
    rotator = unreal.Rotator()
    rotator.pitch = float(pitch)
    rotator.yaw = float(yaw)
    rotator.roll = float(roll)
    return rotator


def stable_jitter(*parts):
    seed = 2166136261
    for part in parts:
        for char in str(part):
            seed ^= ord(char)
            seed = (seed * 16777619) & 0xFFFFFFFF
    return ((seed % 9801) / 1000.0) - 4.9


def clamp_instance_tilt(component, index, label):
    transform = component.get_instance_transform(index, True)
    rotator = transform.rotation.rotator()
    pitch = norm_angle(float(rotator.pitch))
    yaw = norm_angle(float(rotator.yaw))
    roll = norm_angle(float(rotator.roll))
    fixed_pitch = pitch
    fixed_roll = roll
    if abs(fixed_pitch) > TILT_LIMIT_DEG:
        fixed_pitch = max(-TILT_FIX_LIMIT_DEG, min(TILT_FIX_LIMIT_DEG, fixed_pitch))
        if abs(fixed_pitch) >= TILT_FIX_LIMIT_DEG:
            fixed_pitch = stable_jitter(label, component.get_name(), index, "pitch")
    if abs(fixed_roll) > TILT_LIMIT_DEG:
        fixed_roll = max(-TILT_FIX_LIMIT_DEG, min(TILT_FIX_LIMIT_DEG, fixed_roll))
        if abs(fixed_roll) >= TILT_FIX_LIMIT_DEG:
            fixed_roll = stable_jitter(label, component.get_name(), index, "roll")
    transform.rotation = make_rotator(fixed_pitch, yaw, fixed_roll).quaternion()
    return bool(component.update_instance_transform(index, transform, True, True, True))


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * fraction))
    return ordered[max(0, min(len(ordered) - 1, index))]


def actor_tags(actor):
    try:
        return [str(tag) for tag in actor.get_editor_property("tags")]
    except Exception:
        return []


def component_tags(component):
    try:
        return [str(tag) for tag in component.get_editor_property("component_tags")]
    except Exception:
        return []


def has_block_tag(tags):
    return any("block" in str(tag).lower() for tag in tags)


def actor_bounds(actor):
    try:
        values = actor.get_actor_bounds(False)
        origin = values[0]
        extent = values[1]
        return {
            "origin": [round(float(origin.x), 3), round(float(origin.y), 3), round(float(origin.z), 3)],
            "extent": [round(float(extent.x), 3), round(float(extent.y), 3), round(float(extent.z), 3)],
            "_origin": origin,
            "_extent": extent,
        }
    except Exception:
        return None


def inside_bounds(location, blocker, pad=0.0):
    origin = blocker.get("_origin")
    extent = blocker.get("_extent")
    if not origin or not extent:
        return False
    return (
        abs(float(location.x) - float(origin.x)) <= float(extent.x) + pad
        and abs(float(location.y) - float(origin.y)) <= float(extent.y) + pad
        and abs(float(location.z) - float(origin.z)) <= float(extent.z) + pad
    )


def dirty_packages():
    rows = []
    try:
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():
            rows.append(package.get_name())
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
            rows.append(package.get_name())
    except Exception:
        pass
    return sorted(set(rows))


def trace_landscape_normal(world, location, ignore_actors):
    start = unreal.Vector(location.x, location.y, location.z + 60000.0)
    end = unreal.Vector(location.x, location.y, location.z - 60000.0)
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            ignore_actors,
            unreal.DrawDebugTrace.NONE,
            True,
        )
        values = hit.to_tuple()
    except Exception as exc:
        return None, "trace_exception:" + str(exc)
    if not values or not bool(values[0]):
        return None, "trace_miss"
    actor = values[9]
    component = values[10]
    actor_text = ""
    component_text = ""
    if actor:
        actor_text = " ".join([actor.get_name(), actor_label(actor), actor.get_class().get_name()])
    if component:
        component_text = " ".join([component.get_name(), component.get_class().get_name()])
    if "Landscape" not in actor_text and "Landscape" not in component_text:
        return None, ("non_landscape_hit:" + actor_text + "/" + component_text)[:200]
    return normalized(values[7]), "ok"


def find_splines(actors):
    rows = []
    summary = {
        "total": 0,
        "open_2_point": 0,
        "closed_3plus": 0,
        "two_point_closed": 0,
        "closed_under_3_points": 0,
    }
    repairs = []
    for actor in actors:
        label = actor_label(actor)
        for spline in actor.get_components_by_class(unreal.SplineComponent):
            try:
                point_count = int(spline.get_number_of_spline_points())
                closed = bool(spline.is_closed_loop())
                length = float(spline.get_spline_length())
            except Exception:
                continue
            summary["total"] += 1
            tags = sorted(set(actor_tags(actor) + component_tags(spline)))
            violation = None
            if point_count == 2 and closed:
                summary["two_point_closed"] += 1
                violation = "two_point_spline_must_remain_open"
                if FIX_MODE:
                    try:
                        spline.set_closed_loop(False, False)
                        spline.update_spline()
                        repairs.append({"actor": label, "component": spline.get_name(), "repair": "set_closed_loop_false"})
                        closed = False
                        violation = None
                    except Exception as exc:
                        repairs.append({"actor": label, "component": spline.get_name(), "repair_error": str(exc)})
            elif closed and point_count < 3:
                summary["closed_under_3_points"] += 1
                violation = "closed_area_spline_needs_3plus_points"
            elif point_count == 2 and not closed:
                summary["open_2_point"] += 1
            elif closed and point_count >= 3:
                summary["closed_3plus"] += 1
            rows.append(
                {
                    "actor": label,
                    "component": spline.get_name(),
                    "point_count": point_count,
                    "closed_loop": closed,
                    "length_cm": round(length, 2),
                    "tags": tags,
                    "violation": violation,
                }
            )
    return summary, rows, repairs


def read_json_file(path):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except Exception as exc:
        return {"read_error": str(exc), "path": path}
    return {"exists": False, "path": path}


def audit_field_rules():
    world = get_editor_world()
    if not world or not world.get_path_name().startswith(FIELD_LEVEL_PATH + "."):
        try:
            unreal.EditorLevelLibrary.load_level(FIELD_LEVEL_PATH)
            world = get_editor_world()
        except Exception:
            pass
    actors = all_level_actors()
    ignore_for_landscape_trace = [
        actor
        for actor in actors
        if "Landscape" not in actor.get_class().get_name()
    ]
    report = {
        "success": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "world": world.get_path_name() if world else None,
        "fix_mode": bool(FIX_MODE),
        "rules": {
            "tree_rock_tilt_max_deg": TILT_LIMIT_DEG,
            "grass_alignment": "diagnostic sample against landscape normal; final grass-card orientation needs visual review because imported foliage meshes use different local axes",
            "block_tag_staticmesh_exclusion": "no generated PCG instance should overlap block-tagged static mesh actors/components",
            "spline_intent": "2-point splines stay open for linear route/guide/mask; closed area splines need 3+ points",
            "bookmarks": "audit does not create, save, or overwrite viewport bookmark slots",
        },
        "counts": {"grass": 0, "tree": 0, "rock": 0},
        "components": {"grass": 0, "tree": 0, "rock": 0},
        "tilt": {
            "grass": {"violations": 0, "fixed": 0, "max_pitch_deg": 0.0, "max_roll_deg": 0.0, "max_up_angle_deg": 0.0, "samples": []},
            "tree": {"violations": 0, "fixed": 0, "max_pitch_deg": 0.0, "max_roll_deg": 0.0, "max_up_angle_deg": 0.0, "samples": []},
            "rock": {"violations": 0, "fixed": 0, "max_pitch_deg": 0.0, "max_roll_deg": 0.0, "max_up_angle_deg": 0.0, "samples": []},
        },
        "grass_normal_alignment": {
            "sample_limit": GRASS_SAMPLE_LIMIT,
            "mode": "best local mesh axis against landscape normal",
            "diagnostic_only": True,
            "sample_count": 0,
            "trace_miss_or_non_landscape": 0,
            "avg_angle_deg": None,
            "p95_angle_deg": None,
            "max_angle_deg": None,
            "direct_plus_z_p95_angle_deg": None,
            "axis_counts": {},
            "pass": False,
            "failures": [],
        },
        "block_tags": {
            "actor_count": 0,
            "component_count": 0,
            "actors": [],
            "components": [],
            "blockers": [],
            "overlap_violations": 0,
            "overlap_samples": [],
            "pass": True,
            "note": "block-tagged StaticMesh blockers are checked against generated ISM instance bounds",
        },
        "splines": {"summary": {}, "samples": [], "repairs": [], "violations": [], "pass": True},
        "native_road_report": {},
        "dirty_before": dirty_packages(),
    }

    grass_components = []
    block_actor_paths = set()
    component_seen = {"grass": set(), "tree": set(), "rock": set()}
    touched_components = set()

    for actor in actors:
        label = actor_label(actor)
        if has_block_tag(actor_tags(actor)):
            report["block_tags"]["actor_count"] += 1
            report["block_tags"]["actors"].append(label)
            bounds = actor_bounds(actor)
            if bounds:
                block_actor_paths.add(actor.get_path_name())
                report["block_tags"]["blockers"].append(
                    {
                        "actor": label,
                        "origin": bounds["origin"],
                        "extent": bounds["extent"],
                        "_origin": bounds["_origin"],
                        "_extent": bounds["_extent"],
                    }
                )
        for static_component in actor.get_components_by_class(unreal.StaticMeshComponent):
            tags = component_tags(static_component)
            if has_block_tag(tags):
                report["block_tags"]["component_count"] += 1
                report["block_tags"]["components"].append(
                    {"actor": label, "component": static_component.get_name(), "tags": tags}
                )
                if actor.get_path_name() not in block_actor_paths:
                    bounds = actor_bounds(actor)
                    if bounds:
                        block_actor_paths.add(actor.get_path_name())
                        report["block_tags"]["blockers"].append(
                            {
                                "actor": label,
                                "origin": bounds["origin"],
                                "extent": bounds["extent"],
                                "_origin": bounds["_origin"],
                                "_extent": bounds["_extent"],
                            }
                        )

        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            category = component_category(component)
            if category not in report["counts"]:
                continue
            count = instance_count(component)
            if count <= 0:
                continue
            report["counts"][category] += count
            key = component.get_path_name()
            if key not in component_seen[category]:
                component_seen[category].add(key)
                report["components"][category] += 1
            if category == "grass":
                grass_components.append((actor, component, count))
                for index in range(count):
                    try:
                        transform = component.get_instance_transform(index, True)
                    except Exception:
                        continue
                    row = report["tilt"]["grass"]
                    try:
                        rotator = transform.rotation.rotator()
                        pitch = abs(norm_angle(float(rotator.pitch)))
                        roll = abs(norm_angle(float(rotator.roll)))
                        row["max_pitch_deg"] = max(row["max_pitch_deg"], pitch)
                        row["max_roll_deg"] = max(row["max_roll_deg"], roll)
                        row["max_up_angle_deg"] = max(
                            row["max_up_angle_deg"],
                            angle_degrees(quat_up(transform.rotation), WORLD_UP),
                        )
                        if pitch > TILT_LIMIT_DEG + 0.05 or roll > TILT_LIMIT_DEG + 0.05:
                            row["violations"] += 1
                            if len(row["samples"]) < 10:
                                row["samples"].append(
                                    {
                                        "actor": label,
                                        "component": component.get_name(),
                                        "index": index,
                                        "mesh": mesh_path(component),
                                        "pitch_deg": round(pitch, 4),
                                        "roll_deg": round(roll, 4),
                                    }
                                )
                    except Exception:
                        pass
                    for blocker in report["block_tags"]["blockers"]:
                        if inside_bounds(transform.translation, blocker):
                            report["block_tags"]["overlap_violations"] += 1
                            if len(report["block_tags"]["overlap_samples"]) < 12:
                                report["block_tags"]["overlap_samples"].append(
                                    {
                                        "blocker": blocker["actor"],
                                        "actor": label,
                                        "component": component.get_name(),
                                        "category": category,
                                        "index": index,
                                    }
                                )
                            break
                continue
            if category not in ("tree", "rock"):
                continue
            for index in range(count):
                try:
                    transform = component.get_instance_transform(index, True)
                    rotator = transform.rotation.rotator()
                    pitch = abs(norm_angle(float(rotator.pitch)))
                    roll = abs(norm_angle(float(rotator.roll)))
                    for blocker in report["block_tags"]["blockers"]:
                        if inside_bounds(transform.translation, blocker):
                            report["block_tags"]["overlap_violations"] += 1
                            if len(report["block_tags"]["overlap_samples"]) < 12:
                                report["block_tags"]["overlap_samples"].append(
                                    {
                                        "blocker": blocker["actor"],
                                        "actor": label,
                                        "component": component.get_name(),
                                        "category": category,
                                        "index": index,
                                    }
                                )
                            break
                    up_angle = angle_degrees(quat_up(transform.rotation), WORLD_UP)
                    row = report["tilt"][category]
                    row["max_pitch_deg"] = max(row["max_pitch_deg"], pitch)
                    row["max_roll_deg"] = max(row["max_roll_deg"], roll)
                    row["max_up_angle_deg"] = max(row["max_up_angle_deg"], up_angle)
                    if pitch > TILT_LIMIT_DEG + 0.05 or roll > TILT_LIMIT_DEG + 0.05:
                        row["violations"] += 1
                        if len(row["samples"]) < 10:
                            row["samples"].append(
                                {
                                    "actor": label,
                                    "component": component.get_name(),
                                    "index": index,
                                    "mesh": mesh_path(component),
                                    "pitch_deg": round(pitch, 4),
                                    "roll_deg": round(roll, 4),
                                    "up_angle_deg": round(up_angle, 4),
                                }
                            )
                        if FIX_MODE and clamp_instance_tilt(component, index, label):
                            row["fixed"] += 1
                            touched_components.add(component)
                except Exception as exc:
                    if len(report["tilt"][category]["samples"]) < 10:
                        report["tilt"][category]["samples"].append(
                            {"actor": label, "component": component.get_name(), "index": index, "error": str(exc)}
                        )

    grass_total = sum(row[2] for row in grass_components)
    stride = max(1, int(math.ceil(float(max(grass_total, 1)) / float(max(GRASS_SAMPLE_LIMIT, 1)))))
    grass_seen = 0
    grass_angles = []
    grass_direct_up_angles = []
    axis_counts = {}
    for actor, component, count in grass_components:
        label = actor_label(actor)
        for index in range(count):
            take = (grass_seen % stride == 0) and len(grass_angles) < GRASS_SAMPLE_LIMIT
            grass_seen += 1
            if not take:
                continue
            try:
                transform = component.get_instance_transform(index, True)
                normal, reason = trace_landscape_normal(world, transform.translation, ignore_for_landscape_trace)
                if normal is None:
                    report["grass_normal_alignment"]["trace_miss_or_non_landscape"] += 1
                    if len(report["grass_normal_alignment"]["failures"]) < 12:
                        report["grass_normal_alignment"]["failures"].append(
                            {
                                "actor": label,
                                "component": component.get_name(),
                                "index": index,
                                "reason": reason,
                            }
                        )
                else:
                    direct_up_angle = angle_degrees(quat_up(transform.rotation), normal)
                    axis_label, best_angle = best_axis_alignment(transform.rotation, normal)
                    grass_direct_up_angles.append(direct_up_angle)
                    grass_angles.append(best_angle)
                    axis_counts[axis_label] = axis_counts.get(axis_label, 0) + 1
            except Exception as exc:
                report["grass_normal_alignment"]["trace_miss_or_non_landscape"] += 1
                if len(report["grass_normal_alignment"]["failures"]) < 12:
                    report["grass_normal_alignment"]["failures"].append(
                        {"actor": label, "component": component.get_name(), "index": index, "reason": str(exc)}
                    )

    if grass_angles:
        p95 = percentile(grass_angles, 0.95)
        report["grass_normal_alignment"].update(
            {
                "sample_count": len(grass_angles),
                "avg_angle_deg": round(sum(grass_angles) / len(grass_angles), 4),
                "p95_angle_deg": round(p95, 4),
                "max_angle_deg": round(max(grass_angles), 4),
                "direct_plus_z_p95_angle_deg": round(percentile(grass_direct_up_angles, 0.95), 4) if grass_direct_up_angles else None,
                "axis_counts": axis_counts,
                "pass": p95 <= GRASS_NORMAL_P95_LIMIT_DEG,
            }
        )
    report["tilt"]["grass"]["diagnostic_only"] = True
    report["tilt"]["grass"]["note"] = (
        "Grass cards and clumps can use rotated/flipped mesh-local axes; do not auto-clamp grass transforms from this diagnostic."
    )

    report["block_tags"]["pass"] = int(report["block_tags"]["overlap_violations"]) == 0
    for blocker in report["block_tags"]["blockers"]:
        blocker.pop("_origin", None)
        blocker.pop("_extent", None)

    spline_summary, spline_items, spline_repairs = find_splines(actors)
    report["splines"]["summary"] = spline_summary
    report["splines"]["samples"] = spline_items[:80]
    report["splines"]["repairs"] = spline_repairs
    report["splines"]["violations"] = [item for item in spline_items if item.get("violation")]
    report["splines"]["pass"] = not report["splines"]["violations"]

    for component in touched_components:
        try:
            component.mark_render_state_dirty()
            component.modify()
        except Exception:
            pass

    native_report_path = os.path.join(
        unreal.Paths.project_saved_dir(),
        "MCP_RoadPCG",
        "CubelessForestRoadNativeGraphVisualReview.json",
    )
    native_report = read_json_file(native_report_path)
    native_smoke = native_report.get("smoke", native_report) if isinstance(native_report, dict) else {}
    native_visual_quality = native_report.get("visual_quality", {}) if isinstance(native_report, dict) else {}
    report["native_road_report"] = {
        "path": native_report_path,
        "exists": bool(native_report and not native_report.get("exists") is False),
        "pass": bool(native_report.get("pass")) and bool(native_visual_quality.get("pass", True)) if isinstance(native_report, dict) else False,
        "spline_mesh_component_count": native_smoke.get("spline_mesh_component_count") if isinstance(native_smoke, dict) else None,
        "instanced_instance_total": native_smoke.get("instanced_instance_total") if isinstance(native_smoke, dict) else None,
        "roadside_clearance_violation_count": native_smoke.get("roadside_clearance_violation_count") if isinstance(native_smoke, dict) else None,
    }

    if FIX_MODE and (spline_repairs or any(report["tilt"][cat]["fixed"] for cat in ("tree", "rock"))):
        try:
            report["save_dirty_packages"] = bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
        except Exception as exc:
            report["save_dirty_packages_error"] = str(exc)

    report["dirty_after"] = dirty_packages()
    report["pass"] = (
        report["world"] and report["world"].startswith(FIELD_LEVEL_PATH + ".")
        and report["tilt"]["tree"]["violations"] == 0
        and report["tilt"]["rock"]["violations"] == 0
        and report["block_tags"]["pass"]
        and report["splines"]["pass"]
        and report["native_road_report"]["pass"]
        and int(report["native_road_report"].get("roadside_clearance_violation_count") or 0) == 0
    )
    report["visual_review_required"] = {
        "grass_card_orientation": True,
        "road_look_without_final_texture": True,
        "reason": "automatic gates cover production-rule safety; final grass read and road art feel still need viewport inspection",
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    report["report_path"] = report_path
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps(report, ensure_ascii=False))
    return report


audit_field_rules()
"""


def response_result(response: dict[str, Any] | None) -> Any:
    if not response:
        raise RuntimeError("No response from UnrealMCP bridge")
    if response.get("status") == "error" or response.get("success") is False:
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    return response.get("result", response)


def parse_execute_python_result(response: dict[str, Any] | None) -> dict[str, Any]:
    result = response_result(response)
    if isinstance(result, dict):
        if isinstance(result.get("result"), dict):
            return result["result"]
        logs = result.get("logs") or result.get("output") or []
    else:
        logs = []
    if isinstance(logs, str):
        logs = [logs]
    for line in reversed(logs):
        if isinstance(line, dict):
            text = str(line.get("output") or line.get("message") or "").strip()
        else:
            text = str(line).strip()
        start = text.find("{")
        if start >= 0:
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                continue
    raise RuntimeError("Could not parse Unreal Python JSON result: " + json.dumps(result, ensure_ascii=False)[:2000])


def run(args: argparse.Namespace) -> dict[str, Any]:
    code = UNREAL_AUDIT_CODE.replace("__FIX_MODE__", "True" if args.fix else "False")
    code = code.replace("__GRASS_SAMPLE_LIMIT__", str(int(args.grass_sample_limit)))
    response = UnrealConnection().send_command(
        "execute_python",
        {
            "code": code,
            "mode": "ExecuteFile",
            "description": "Audit Cubeless field PCG rule compliance",
        },
    )
    return parse_execute_python_result(response)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the Cubeless field PCG production rules.")
    parser.add_argument("--fix", action="store_true", help="Apply safe non-destructive rule repairs.")
    parser.add_argument("--grass-sample-limit", type=int, default=800)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
