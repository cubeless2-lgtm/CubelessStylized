#!/usr/bin/env python3
"""Capture a read-only UDS/UDW sky state snapshot through UnrealMCP.

The snapshot is designed for debugging UDS reference states and for building
Cubeless-owned sky regression checks. It does not save or modify Unreal assets.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from run_pcg_bookmark_visual_qa import (
    PROJECT_ROOT,
    UnrealConnection,
    parse_execute_python_log_json,
    response_result,
    send,
)


UDS_VOLUME_MPC = "/Game/UltraDynamicSky/Materials/Material_Functions/UDS_VolumetricClouds_MPC"
UDW_WEATHER_MPC = "/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters"

REPORT_DIR = PROJECT_ROOT / "Saved" / "UDS_Analysis"
DEFAULT_REPORT_PATH = REPORT_DIR / "uds_sky_snapshot.json"

UDS_VOLUME_MPC_PARAMETERS = [
    "Cloud Density",
    "Layer 2 Density",
    "Cloud Coverage Target Opacity",
    "Layer 2 Cloud Coverage Target Opacity",
    "Bottom Altitude",
    "Top Altitude",
    "Cloud Layer Height",
    "Clouds Scale",
    "Macro Scale",
    "Macro Variation",
    "High Frequency Noise",
    "3D Erosion",
    "3D Erosion Power",
    "Extinction Scale",
    "Layer 2 Extinction",
    "PhaseG",
    "PhaseG2",
    "Phase Blend",
    "Cloud Shadow Falloff",
    "Albedo",
    "Top Emissive Color",
    "Bottom Emissive Color",
    "Clouds Position",
    "Fog Position",
]

UDW_WEATHER_MPC_PARAMETERS = [
    "Cloud Coverage",
    "Fog",
    "Wind Intensity",
    "Wind Angle",
    "Cloud Bottom Altitude",
    "Time of Day",
    "Wind Force",
    "Sun Vector",
    "Moon Vector",
    "Ambient Fog Color",
    "Lightning Color",
]


UNREAL_SNAPSHOT_CODE = r"""
import json
import math
import traceback

import unreal


UDS_ACTOR_HINT = __UDS_ACTOR_HINT__
UDW_ACTOR_HINT = __UDW_ACTOR_HINT__
UDS_VOLUME_MPC = __UDS_VOLUME_MPC__
UDW_WEATHER_MPC = __UDW_WEATHER_MPC__
UDS_VOLUME_MPC_PARAMETERS = __UDS_VOLUME_MPC_PARAMETERS__
UDW_WEATHER_MPC_PARAMETERS = __UDW_WEATHER_MPC_PARAMETERS__


def to_jsonable(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if hasattr(value, "get_path_name"):
        try:
            return value.get_path_name()
        except Exception:
            pass
    if all(hasattr(value, attr) for attr in ("x", "y", "z")):
        result = {
            "x": float(getattr(value, "x")),
            "y": float(getattr(value, "y")),
            "z": float(getattr(value, "z")),
        }
        if hasattr(value, "w"):
            result["w"] = float(getattr(value, "w"))
        return result
    if all(hasattr(value, attr) for attr in ("r", "g", "b")):
        result = {
            "r": float(getattr(value, "r")),
            "g": float(getattr(value, "g")),
            "b": float(getattr(value, "b")),
        }
        if hasattr(value, "a"):
            result["a"] = float(getattr(value, "a"))
        return result
    try:
        return str(value)
    except Exception:
        return repr(value)


def coerce_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except Exception:
            return None
    return None


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
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def get_all_level_actors():
    actor_subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if actor_subsystem_cls:
        actor_subsystem = unreal.get_editor_subsystem(actor_subsystem_cls)
        if actor_subsystem:
            return list(actor_subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def actor_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def object_path(obj):
    if not obj:
        return None
    if hasattr(obj, "get_path_name"):
        try:
            return obj.get_path_name()
        except Exception:
            pass
    return str(obj)


def class_name(obj):
    if not obj:
        return None
    try:
        return obj.get_class().get_name()
    except Exception:
        return type(obj).__name__


def dirty_packages():
    errors = []
    content = []
    maps = []
    try:
        content = list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() or [])
    except Exception as exc:
        errors.append("get_dirty_content_packages failed: " + str(exc))
    try:
        maps = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or [])
    except Exception as exc:
        errors.append("get_dirty_map_packages failed: " + str(exc))

    def names(packages):
        result = []
        for package in packages:
            try:
                result.append(package.get_name())
            except Exception:
                result.append(str(package))
        return sorted(set(result))

    content_names = names(content)
    map_names = names(maps)
    return {
        "dirty_content_packages": content_names,
        "dirty_map_packages": map_names,
        "dirty_content_count": len(content_names),
        "dirty_map_count": len(map_names),
        "dirty_total_count": len(set(content_names + map_names)),
        "errors": errors,
    }


def actor_summary(actor):
    if not actor:
        return {"found": False}
    return {
        "found": True,
        "label": actor_label(actor),
        "name": actor.get_name(),
        "class": class_name(actor),
        "path": object_path(actor),
    }


def actor_search_text(actor, include_path=False):
    parts = [
        actor_label(actor),
        actor.get_name(),
        class_name(actor) or "",
    ]
    if include_path:
        parts.append(object_path(actor) or "")
    return " ".join(
        [
            str(part)
            for part in parts
            if part
        ]
    ).lower()


def find_actor(kind, hint):
    actors = get_all_level_actors()
    if hint:
        lowered_hint = hint.lower()
        for actor in actors:
            if lowered_hint in actor_search_text(actor, include_path=True):
                return actor

    if kind == "uds":
        tokens = ("ultra_dynamic_sky", "ultradynamicsky", "ultra dynamic sky")
    else:
        tokens = ("ultra_dynamic_weather", "ultradynamicweather", "ultra dynamic weather")

    for actor in actors:
        text = actor_search_text(actor)
        if any(token in text for token in tokens):
            return actor
    return None


def read_property(obj, label, candidates):
    errors = []
    for candidate in candidates:
        try:
            value = obj.get_editor_property(candidate)
            return {
                "ok": True,
                "label": label,
                "property": candidate,
                "value": to_jsonable(value),
                "type": type(value).__name__,
            }
        except Exception as exc:
            errors.append({"property": candidate, "error": str(exc)})
    return {
        "ok": False,
        "label": label,
        "property": None,
        "value": None,
        "errors": errors,
    }


def read_properties(obj, specs):
    if not obj:
        return {}
    result = {}
    for label, candidates in specs.items():
        result[label] = read_property(obj, label, candidates)
    return result


def call_method(obj, label, method_name, args=None):
    if not obj:
        return {"ok": False, "label": label, "method": method_name, "value": None, "errors": ["missing object"]}
    errors = []
    attempts = []
    if args is None:
        attempts.append(())
    else:
        attempts.append(tuple(args))
        attempts.append(list(args))
    for method_args in attempts:
        try:
            if method_args:
                value = obj.call_method(method_name, method_args)
            else:
                value = obj.call_method(method_name)
            return {
                "ok": True,
                "label": label,
                "method": method_name,
                "args": to_jsonable(method_args),
                "value": to_jsonable(value),
                "type": type(value).__name__,
            }
        except Exception as exc:
            errors.append(str(exc))
    return {
        "ok": False,
        "label": label,
        "method": method_name,
        "args": to_jsonable(args),
        "value": None,
        "errors": errors,
    }


def call_methods(obj, specs):
    result = {}
    for label, method_name, args in specs:
        result[label] = call_method(obj, label, method_name, args)
    return result


def read_material_scalar(material, name):
    if not material:
        return {"ok": False, "value": None, "errors": ["missing material"]}
    errors = []
    try:
        value = material.get_scalar_parameter_value(name)
        return {"ok": True, "value": to_jsonable(value), "source": "material_method"}
    except Exception as exc:
        errors.append("material method: " + str(exc))
    try:
        value = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, name)
        return {"ok": True, "value": to_jsonable(value), "source": "MaterialEditingLibrary"}
    except Exception as exc:
        errors.append("MaterialEditingLibrary: " + str(exc))
    return {"ok": False, "value": None, "errors": errors}


def read_material_vector(material, name):
    if not material:
        return {"ok": False, "value": None, "errors": ["missing material"]}
    errors = []
    try:
        value = material.get_vector_parameter_value(name)
        return {"ok": True, "value": to_jsonable(value), "source": "material_method"}
    except Exception as exc:
        errors.append("material method: " + str(exc))
    try:
        value = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, name)
        return {"ok": True, "value": to_jsonable(value), "source": "MaterialEditingLibrary"}
    except Exception as exc:
        errors.append("MaterialEditingLibrary: " + str(exc))
    return {"ok": False, "value": None, "errors": errors}


def read_material_texture(material, name):
    if not material:
        return {"ok": False, "value": None, "errors": ["missing material"]}
    errors = []
    try:
        value = material.get_texture_parameter_value(name)
        return {"ok": True, "value": to_jsonable(value), "source": "material_method"}
    except Exception as exc:
        errors.append("material method: " + str(exc))
    try:
        value = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, name)
        return {"ok": True, "value": to_jsonable(value), "source": "MaterialEditingLibrary"}
    except Exception as exc:
        errors.append("MaterialEditingLibrary: " + str(exc))
    return {"ok": False, "value": None, "errors": errors}


def read_material_parent(material):
    if not material:
        return None
    for prop in ("parent", "Parent"):
        try:
            parent = material.get_editor_property(prop)
            return object_path(parent)
        except Exception:
            pass
    return None


def read_component_material(component, index=0):
    if not component:
        return {"found": False}
    material = None
    errors = []
    try:
        material = component.get_material(index)
    except Exception as exc:
        errors.append(str(exc))
    if not material:
        for prop in ("material", "Material"):
            try:
                material = component.get_editor_property(prop)
                break
            except Exception as exc:
                errors.append(f"{prop}: {exc}")
    return {
        "found": bool(material),
        "slot": index,
        "material": object_path(material),
        "material_class": class_name(material),
        "parent": read_material_parent(material),
        "errors": errors,
        "object": material,
    }


def component_summary(component):
    if not component:
        return {"found": False}
    return {
        "found": True,
        "name": component.get_name(),
        "class": class_name(component),
        "path": object_path(component),
    }


def get_actor_components(actor):
    if not actor:
        return []
    try:
        return list(actor.get_components_by_class(unreal.ActorComponent))
    except Exception:
        return []


def find_component(actor, tokens):
    lowered = tuple(token.lower() for token in tokens)
    for component in get_actor_components(actor):
        text = " ".join([component.get_name(), class_name(component) or "", object_path(component) or ""]).lower()
        if any(token in text for token in lowered):
            return component
    return None


def read_volumetric_component(uds_actor):
    component = find_component(uds_actor, ("volumetriccloud", "volumetric_cloud", "volumetric cloud"))
    material_info = read_component_material(component)
    material_object = material_info.pop("object", None)
    return {
        "component": component_summary(component),
        "properties": read_properties(
            component,
            {
                "visible": ["visible", "Visible"],
                "hidden_in_game": ["hidden_in_game", "Hidden In Game"],
                "layer_bottom_altitude": ["layer_bottom_altitude", "Layer Bottom Altitude"],
                "layer_height": ["layer_height", "Layer Height"],
                "tracing_start_max_distance": ["tracing_start_max_distance", "Tracing Start Max Distance"],
                "tracing_max_distance": ["tracing_max_distance", "Tracing Max Distance"],
                "planet_radius": ["planet_radius", "Planet Radius"],
            },
        ),
        "material": material_info,
        "material_parameters": {
            "RefractionDepthBias": read_material_scalar(material_object, "RefractionDepthBias"),
            "TwoLayers": read_material_scalar(material_object, "TwoLayers"),
        },
    }


def read_sky_sphere(uds_actor):
    component = find_component(uds_actor, ("sky_sphere", "sky sphere"))
    material_info = read_component_material(component)
    material_object = material_info.pop("object", None)
    return {
        "component": component_summary(component),
        "material": material_info,
        "scalars": {
            "Cloud Density": read_material_scalar(material_object, "Cloud Density"),
            "Wispy Cloud Alpha": read_material_scalar(material_object, "Wispy Cloud Alpha"),
            "Cloud Tiling": read_material_scalar(material_object, "Cloud Tiling"),
            "Cloud Height": read_material_scalar(material_object, "Cloud Height"),
            "Cloud Sharpness": read_material_scalar(material_object, "Cloud Sharpness"),
            "Overall Intensity": read_material_scalar(material_object, "Overall Intensity"),
        },
        "vectors": {
            "Cloud Wisps Gradient": read_material_vector(material_object, "Cloud Wisps Gradient"),
            "Cloud Wisps Color": read_material_vector(material_object, "Cloud Wisps Color"),
            "Clouds Position": read_material_vector(material_object, "Clouds Position"),
        },
        "textures": {
            "Cloud_Wisps_Texture": read_material_texture(material_object, "Cloud_Wisps_Texture"),
        },
    }


def load_asset(path):
    try:
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if asset:
            return asset
    except Exception:
        pass
    object_name = path.rsplit("/", 1)[-1]
    try:
        return unreal.load_object(None, path + "." + object_name)
    except Exception:
        return None


def read_world_summary(world):
    if not world:
        return {"found": False}
    try:
        map_name = world.get_map_name()
    except Exception:
        map_name = None
    return {
        "found": True,
        "map_name": map_name,
        "world_path": object_path(world),
        "world_class": class_name(world),
    }


try:
    world = get_editor_world()
    uds_actor = find_actor("uds", UDS_ACTOR_HINT)
    udw_actor = find_actor("udw", UDW_ACTOR_HINT)

    uds_properties = read_properties(
        uds_actor,
        {
            "Sky Mode": ["Sky Mode", "sky_mode"],
            "Feature Level": ["Feature Level", "feature_level"],
            "Project Mode": ["Project Mode", "project_mode"],
            "Cloud Coverage": ["Cloud Coverage", "cloud_coverage"],
            "Cloud Coverage 0-3": ["Cloud Coverage 0-3", "cloud_coverage_0_3"],
            "Cloud Speed": ["Cloud Speed", "cloud_speed"],
            "Cloud Direction": ["Cloud Direction", "cloud_direction"],
            "Cloud Phase": ["Cloud Phase", "cloud_phase"],
            "Composite Weather Change Speed": [
                "Composite Weather Change Speed",
                "composite_weather_change_speed",
            ],
            "Using Volumetric Clouds": ["Using Volumetric Clouds", "using_volumetric_clouds"],
            "Two Layers": ["Two Layers", "two_layers"],
            "Time of Day": ["Time of Day", "time_of_day"],
            "Cloud Movement Update Period": [
                "Cloud Movement Update Period",
                "cloud_movement_update_period",
            ],
            "Active Update Speed": ["Active Update Speed", "active_update_speed"],
        },
    )
    udw_properties = read_properties(
        udw_actor,
        {
            "Weather Speed": ["Weather Speed", "weather_speed"],
            "Cloud Coverage": ["Cloud Coverage", "cloud_coverage"],
            "Fog": ["Fog", "fog"],
            "Rain": ["Rain", "rain"],
            "Snow": ["Snow", "snow"],
            "Dust": ["Dust", "dust"],
            "Wind Intensity": ["Wind Intensity", "wind_intensity"],
        },
    )
    uds_methods = call_methods(
        uds_actor,
        [
            ("Current Volumetric Clouds Density", "Current Volumetric Clouds Density", None),
            ("Current Volumetric Clouds Density Layer1", "Current Volumetric Clouds Density", [True]),
            ("Current Volumetric Clouds Density Layer2", "Current Volumetric Clouds Density", [False]),
            (
                "Get Current Volumetric Cloud Extinction Scale",
                "Get Current Volumetric Cloud Extinction Scale",
                None,
            ),
            ("Current Volumetric Cloud Macro Variation", "Current Volumetric Cloud Macro Variation", None),
            ("Current Base Clouds Scale", "Current Base Clouds Scale", None),
            ("Cloud Shadows Cloud Density", "Cloud Shadows Cloud Density", None),
        ],
    )
    udw_methods = call_methods(
        udw_actor,
        [
            ("Currently Cloudy", "Currently Cloudy", None),
            ("Currently Raining", "Currently Raining", None),
            ("Currently Snowing", "Currently Snowing", None),
            ("Currently Foggy", "Currently Foggy", None),
            ("Currently Dusty", "Currently Dusty", None),
            ("Sky Cloud Speed", "Sky Cloud Speed", None),
            ("Get Weather Speed", "Get Weather Speed", None),
        ],
    )
    report = {
        "success": True,
        "schema": "cubeless_uds_sky_snapshot_unreal_v1",
        "policy": "Read-only UDS/UDW sky state snapshot. Does not save or modify Unreal assets.",
        "world": read_world_summary(world),
        "dirty_packages": dirty_packages(),
        "actors": {
            "uds": actor_summary(uds_actor),
            "udw": actor_summary(udw_actor),
        },
        "uds": {
            "properties": uds_properties,
            "methods": uds_methods,
            "volumetric_component": read_volumetric_component(uds_actor),
            "sky_sphere": read_sky_sphere(uds_actor),
        },
        "udw": {
            "properties": udw_properties,
            "methods": udw_methods,
        },
    }
except Exception as exc:
    report = {
        "success": False,
        "schema": "cubeless_uds_sky_snapshot_unreal_v1",
        "policy": "Read-only UDS/UDW sky state snapshot. Does not save or modify Unreal assets.",
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }

print(json.dumps(report, ensure_ascii=False))
"""


def _json_literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _build_unreal_code(args: argparse.Namespace) -> str:
    return (
        UNREAL_SNAPSHOT_CODE.replace("__UDS_ACTOR_HINT__", _json_literal(args.uds_actor_hint))
        .replace("__UDW_ACTOR_HINT__", _json_literal(args.udw_actor_hint))
        .replace("__UDS_VOLUME_MPC__", _json_literal(UDS_VOLUME_MPC))
        .replace("__UDW_WEATHER_MPC__", _json_literal(UDW_WEATHER_MPC))
        .replace("__UDS_VOLUME_MPC_PARAMETERS__", _json_literal(UDS_VOLUME_MPC_PARAMETERS))
        .replace("__UDW_WEATHER_MPC_PARAMETERS__", _json_literal(UDW_WEATHER_MPC_PARAMETERS))
    )


def _execute_unreal_snapshot(unreal: UnrealConnection, args: argparse.Namespace) -> dict[str, Any]:
    response = send(
        unreal,
        "execute_python",
        {"code": _build_unreal_code(args), "mode": "ExecuteFile"},
    )
    return parse_execute_python_log_json(response)


def _get_mpc_values(
    unreal: UnrealConnection,
    collection_path: str,
    parameter_names: list[str],
) -> dict[str, Any]:
    try:
        response = send(
            unreal,
            "get_material_parameter_collection_values",
            {
                "collection_path": collection_path,
                "parameter_names": parameter_names,
                "include_asset_defaults": True,
                "include_runtime": True,
            },
        )
        result = response_result(response)
        if isinstance(result, dict):
            return result
        return {"success": False, "result": result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _capture_screenshot(unreal: UnrealConnection, output_path: Path, redraw_count: int) -> dict[str, Any]:
    try:
        response = send(
            unreal,
            "capture_viewport_bookmark_screenshot",
            {
                "filepath": str(output_path),
                "redraw_count": redraw_count,
            },
        )
        result = response_result(response)
        if isinstance(result, dict):
            result["exists_on_disk"] = output_path.exists()
            return result
        return {"success": False, "result": result, "exists_on_disk": output_path.exists()}
    except Exception as exc:
        return {"success": False, "error": str(exc), "exists_on_disk": output_path.exists()}


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _record_value(record: Any) -> Any:
    if not isinstance(record, dict) or not record.get("ok"):
        return None
    return record.get("value")


def _extract_uds_record_value(unreal_snapshot: dict[str, Any], group: str, name: str) -> Any:
    try:
        record = unreal_snapshot["uds"][group][name]
    except (KeyError, TypeError):
        return None
    return _record_value(record)


def _mpc_read_succeeded(result: dict[str, Any]) -> bool:
    if not isinstance(result, dict) or result.get("error"):
        return False
    if result.get("success") is False:
        return False
    return bool(result.get("scalars") or result.get("vectors"))


def _find_mpc_parameter(result: dict[str, Any], name: str, bucket: str = "scalars") -> dict[str, Any] | None:
    for item in result.get(bucket, []) or []:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def _build_density_sync_check(
    unreal_snapshot: dict[str, Any],
    mpc_defaults: dict[str, Any],
) -> dict[str, Any]:
    sky_mode = _extract_uds_record_value(unreal_snapshot, "properties", "Sky Mode")
    derived_density = _coerce_number(
        _extract_uds_record_value(unreal_snapshot, "methods", "Current Volumetric Clouds Density")
    )
    if derived_density is None:
        derived_density = _coerce_number(
            _extract_uds_record_value(unreal_snapshot, "methods", "Current Volumetric Clouds Density Layer1")
        )

    volume_mpc = mpc_defaults.get("uds_volumetric_clouds", {})
    density_record = _find_mpc_parameter(volume_mpc, "Cloud Density")
    runtime_density = _coerce_number((density_record or {}).get("runtime_value"))
    asset_default_density = _coerce_number((density_record or {}).get("asset_default"))

    sky_mode_text = str(sky_mode or "")
    issue = False
    if "VOLUMETRIC" in sky_mode_text.upper() and derived_density is not None and runtime_density is not None:
        issue = derived_density > 0.001 and abs(runtime_density) <= 0.001

    return {
        "sky_mode": sky_mode_text,
        "derived_density": derived_density,
        "asset_default_cloud_density": asset_default_density,
        "runtime_cloud_density": runtime_density,
        "runtime_density_zero_while_derived_positive": issue,
        "pass": not issue,
    }


def _build_validation(
    unreal_snapshot: dict[str, Any],
    mpc_defaults: dict[str, Any],
    density_sync_check: dict[str, Any],
) -> dict[str, Any]:
    actors = unreal_snapshot.get("actors", {}) if isinstance(unreal_snapshot, dict) else {}
    return {
        "unreal_snapshot_success": bool(unreal_snapshot.get("success")),
        "uds_actor_found": bool(actors.get("uds", {}).get("found")),
        "udw_actor_found": bool(actors.get("udw", {}).get("found")),
        "density_sync_check_pass": bool(density_sync_check.get("pass")),
        "volume_mpc_defaults_read": _mpc_read_succeeded(
            mpc_defaults.get("uds_volumetric_clouds", {})
        ),
        "weather_mpc_defaults_read": _mpc_read_succeeded(mpc_defaults.get("udw_weather", {})),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    unreal = UnrealConnection()
    if hasattr(unreal, "timeout"):
        unreal.timeout = max(
            int(getattr(unreal, "timeout", 0)),
            int(args.mcp_response_timeout_seconds),
        )

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(args.output) if args.output else DEFAULT_REPORT_PATH
    if args.timestamped_output:
        output_path = REPORT_DIR / f"uds_sky_snapshot_{timestamp}.json"
    screenshot_path = REPORT_DIR / f"uds_sky_snapshot_{timestamp}.png"

    unreal_snapshot = _execute_unreal_snapshot(unreal, args)
    mpc_defaults = {
        "uds_volumetric_clouds": _get_mpc_values(unreal, UDS_VOLUME_MPC, UDS_VOLUME_MPC_PARAMETERS),
        "udw_weather": _get_mpc_values(unreal, UDW_WEATHER_MPC, UDW_WEATHER_MPC_PARAMETERS),
    }
    screenshot = None
    if args.capture_screenshot:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        screenshot = _capture_screenshot(unreal, screenshot_path, args.redraw_count)

    density_sync_check = _build_density_sync_check(unreal_snapshot, mpc_defaults)
    validation = _build_validation(unreal_snapshot, mpc_defaults, density_sync_check)
    report = {
        "schema": "cubeless_uds_sky_snapshot_runner_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only UDS/UDW sky state snapshot. Does not save or modify Unreal assets.",
        "unreal_snapshot": unreal_snapshot,
        "mpc_asset_and_runtime_values": mpc_defaults,
        "density_sync_check": density_sync_check,
        "screenshot": screenshot,
        "validation": validation,
        "pass": all(bool(value) for value in validation.values()),
        "report_path": str(output_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a read-only UDS/UDW sky state snapshot.")
    parser.add_argument("--uds-actor-hint", default="", help="Optional label/name/path hint for the UDS actor.")
    parser.add_argument("--udw-actor-hint", default="", help="Optional label/name/path hint for the UDW actor.")
    parser.add_argument("--output", default="", help="Report path. Defaults to Saved/UDS_Analysis/uds_sky_snapshot.json.")
    parser.add_argument("--timestamped-output", action="store_true", help="Write a timestamped report under Saved/UDS_Analysis.")
    parser.add_argument("--capture-screenshot", action="store_true", help="Also capture the active editor viewport.")
    parser.add_argument("--redraw-count", type=int, default=2)
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=120)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
