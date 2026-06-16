#!/usr/bin/env python3
"""Run the Cubeless sky promotion preflight checks through UnrealMCP.

This is a read-only gate for promoting Cubeless sky assets away from UDS
vendor dependencies. It combines the recursive dependency audit with targeted
asset-default checks for the current Cubeless sky replacement assets.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import audit_cubeless_sky_dependencies
from run_pcg_bookmark_visual_qa import (
    PROJECT_ROOT,
    UnrealConnection,
    parse_execute_python_log_json,
    response_result,
    send,
)


DEFAULT_PACKAGE_ROOT = "/Game/Cubeless/Sky"
DEFAULT_FORBIDDEN_ROOTS = ["/Game/UltraDynamicSky"]
DEFAULT_BP_SKY_SYSTEM = "/Game/Cubeless/Sky/BP_SkySystem"
DEFAULT_SKY_DOME_COMPONENT = "SkyDomeMesh"
DEFAULT_SKY_DOME_MATERIAL = "/Game/Cubeless/Sky/Materials/M_Sky_Dome"
DEFAULT_SKY_MESH = "/Game/Cubeless/Sky/Meshes/SM_Cubeless_SkySphere"
DEFAULT_CLOUD_TEXTURE = "/Game/Cubeless/Env/Sky/Textures/T_CloudPlaneAtlas_LightPacked_UDSLike"
DEFAULT_WEATHER_DATA_ASSETS = [
    "/Game/Cubeless/Sky/Data/DA_Weather_Clear",
    "/Game/Cubeless/Sky/Data/DA_Weather_Cloudy",
    "/Game/Cubeless/Sky/Data/DA_Weather_Overcast",
]

REPORT_DIR = PROJECT_ROOT / "Saved" / "UDS_Analysis"
DEFAULT_REPORT_PATH = REPORT_DIR / "cubeless_sky_promotion_preflight.json"


UNREAL_PREFLIGHT_CODE = r"""
import json
import traceback

import unreal


EXPECTED_SKY_MESH = __EXPECTED_SKY_MESH__
EXPECTED_CLOUD_TEXTURE = __EXPECTED_CLOUD_TEXTURE__
SKY_DOME_MATERIAL = __SKY_DOME_MATERIAL__
WEATHER_DATA_ASSETS = __WEATHER_DATA_ASSETS__
FORBIDDEN_ROOTS = __FORBIDDEN_ROOTS__


def to_string(value):
    try:
        return str(value)
    except Exception:
        return ""


def object_path(obj):
    if not obj:
        return None
    if hasattr(obj, "get_path_name"):
        try:
            return obj.get_path_name()
        except Exception:
            pass
    return to_string(obj)


def object_path_from_package(package_path):
    return package_path + "." + package_path.rsplit("/", 1)[-1]


def normalize_package_name(value):
    text = to_string(value)
    if "." in text and text.startswith("/"):
        return text.split(".", 1)[0]
    return text


def package_starts_with(package_name, roots):
    return any(package_name == root or package_name.startswith(root + "/") for root in roots)


def load_asset(package_path):
    asset = None
    try:
        asset = unreal.EditorAssetLibrary.load_asset(package_path)
    except Exception:
        asset = None
    if asset:
        return asset
    try:
        return unreal.load_object(None, object_path_from_package(package_path))
    except Exception:
        return None


def read_property(obj, candidates):
    errors = []
    for candidate in candidates:
        try:
            value = obj.get_editor_property(candidate)
            return {
                "ok": True,
                "property": candidate,
                "value": object_path(value),
            }
        except Exception as exc:
            errors.append({"property": candidate, "error": str(exc)})
    return {
        "ok": False,
        "property": None,
        "value": None,
        "errors": errors,
    }


def make_dependency_options():
    options = unreal.AssetRegistryDependencyOptions()
    for name, value in [
        ("include_soft_package_references", True),
        ("include_hard_package_references", True),
        ("include_searchable_names", False),
        ("include_soft_management_references", True),
        ("include_hard_management_references", True),
    ]:
        try:
            options.set_editor_property(name, value)
        except Exception:
            pass
    return options


def direct_dependencies(package_path):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = make_dependency_options()
    try:
        deps = registry.get_dependencies(package_path, options)
        return sorted({normalize_package_name(dep) for dep in deps if to_string(dep)}), None
    except Exception as exc:
        return [], str(exc)


def dirty_packages():
    errors = []

    def names(packages):
        result = []
        for package in packages or []:
            try:
                result.append(package.get_name())
            except Exception:
                result.append(to_string(package))
        return sorted(set(result))

    try:
        dirty_content = names(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    except Exception as exc:
        dirty_content = []
        errors.append("get_dirty_content_packages failed: " + str(exc))

    try:
        dirty_maps = names(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    except Exception as exc:
        dirty_maps = []
        errors.append("get_dirty_map_packages failed: " + str(exc))

    return {
        "dirty_content_packages": dirty_content,
        "dirty_map_packages": dirty_maps,
        "dirty_content_count": len(dirty_content),
        "dirty_map_count": len(dirty_maps),
        "errors": errors,
    }


def expected_assets():
    sky_mesh = load_asset(EXPECTED_SKY_MESH)
    cloud_texture = load_asset(EXPECTED_CLOUD_TEXTURE)
    sky_material = load_asset(SKY_DOME_MATERIAL)
    weather_assets = []
    for path in WEATHER_DATA_ASSETS:
        asset = load_asset(path)
        weather_assets.append(
            {
                "package": path,
                "exists": bool(asset),
                "object_path": object_path(asset),
            }
        )

    return {
        "sky_mesh": {
            "package": EXPECTED_SKY_MESH,
            "exists": bool(sky_mesh),
            "object_path": object_path(sky_mesh),
        },
        "cloud_texture": {
            "package": EXPECTED_CLOUD_TEXTURE,
            "exists": bool(cloud_texture),
            "object_path": object_path(cloud_texture),
        },
        "sky_dome_material": {
            "package": SKY_DOME_MATERIAL,
            "exists": bool(sky_material),
            "object_path": object_path(sky_material),
        },
        "weather_data_assets": weather_assets,
    }


def weather_texture_checks():
    checks = []
    expected_package = EXPECTED_CLOUD_TEXTURE
    expected_object = object_path_from_package(EXPECTED_CLOUD_TEXTURE)
    for path in WEATHER_DATA_ASSETS:
        asset = load_asset(path)
        if not asset:
            checks.append(
                {
                    "package": path,
                    "exists": False,
                    "property_ok": False,
                    "matches_expected_texture": False,
                    "expected_texture": expected_object,
                }
            )
            continue

        prop = read_property(asset, ["FarCloudTexture", "far_cloud_texture"])
        value = prop.get("value")
        checks.append(
            {
                "package": path,
                "exists": True,
                "property_ok": bool(prop.get("ok")),
                "property": prop,
                "texture": value,
                "texture_package": normalize_package_name(value),
                "expected_texture": expected_object,
                "matches_expected_texture": normalize_package_name(value) == expected_package,
            }
        )
    return checks


def material_checks():
    dependencies, dependency_error = direct_dependencies(SKY_DOME_MATERIAL)
    forbidden = [
        dep for dep in dependencies
        if package_starts_with(dep, FORBIDDEN_ROOTS)
    ]
    return {
        "package": SKY_DOME_MATERIAL,
        "direct_dependencies": dependencies,
        "dependency_error": dependency_error,
        "forbidden_dependencies": forbidden,
        "forbidden_dependency_count": len(forbidden),
        "expected_texture": EXPECTED_CLOUD_TEXTURE,
        "uses_expected_texture": EXPECTED_CLOUD_TEXTURE in dependencies,
    }


try:
    assets = expected_assets()
    weather = weather_texture_checks()
    material = material_checks()
    dirty = dirty_packages()
    report = {
        "success": True,
        "schema": "cubeless_sky_promotion_preflight_unreal_v1",
        "policy": "Read-only targeted Cubeless sky promotion checks. Does not save or modify Unreal assets.",
        "expected_assets": assets,
        "weather_data_texture_checks": weather,
        "sky_dome_material_check": material,
        "dirty_packages": dirty,
    }
except Exception as exc:
    report = {
        "success": False,
        "schema": "cubeless_sky_promotion_preflight_unreal_v1",
        "policy": "Read-only targeted Cubeless sky promotion checks. Does not save or modify Unreal assets.",
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }

print(json.dumps(report, ensure_ascii=False))
"""


def _json_literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _object_path_from_package(package_path: str) -> str:
    return package_path.rstrip("/") + "." + package_path.rstrip("/").rsplit("/", 1)[-1]


def _build_unreal_code(args: argparse.Namespace) -> str:
    return (
        UNREAL_PREFLIGHT_CODE.replace("__EXPECTED_SKY_MESH__", _json_literal(args.expected_sky_mesh.rstrip("/")))
        .replace("__EXPECTED_CLOUD_TEXTURE__", _json_literal(args.expected_cloud_texture.rstrip("/")))
        .replace("__SKY_DOME_MATERIAL__", _json_literal(args.sky_dome_material.rstrip("/")))
        .replace("__WEATHER_DATA_ASSETS__", _json_literal([path.rstrip("/") for path in args.weather_data_asset]))
        .replace("__FORBIDDEN_ROOTS__", _json_literal([root.rstrip("/") for root in args.forbidden_root]))
    )


def _execute_unreal_preflight(unreal: UnrealConnection, args: argparse.Namespace) -> dict[str, Any]:
    response = send(
        unreal,
        "execute_python",
        {"code": _build_unreal_code(args), "mode": "ExecuteFile"},
    )
    return parse_execute_python_log_json(response)


def _list_sky_dome_component(unreal: UnrealConnection, args: argparse.Namespace) -> dict[str, Any]:
    try:
        response = send(
            unreal,
            "list_blueprint_components",
            {
                "blueprint_name": args.bp_sky_system.rstrip("/"),
                "component_name": args.sky_dome_component_name,
            },
        )
        result = response_result(response)
        if isinstance(result, dict):
            return result
        return {"success": False, "result": result}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _sky_dome_static_mesh(blueprint_components: dict[str, Any], component_name: str) -> str:
    for component in blueprint_components.get("components", []) or []:
        if not isinstance(component, dict):
            continue
        if component.get("component_name") == component_name:
            return str(component.get("static_mesh") or "")
    return ""


def _expected_assets_exist(unreal_preflight: dict[str, Any]) -> bool:
    expected = unreal_preflight.get("expected_assets", {})
    if not expected:
        return False
    required = [
        expected.get("sky_mesh", {}),
        expected.get("cloud_texture", {}),
        expected.get("sky_dome_material", {}),
    ]
    required.extend(expected.get("weather_data_assets", []) or [])
    return all(bool(item.get("exists")) for item in required if isinstance(item, dict))


def _weather_data_textures_expected(unreal_preflight: dict[str, Any]) -> bool:
    checks = unreal_preflight.get("weather_data_texture_checks", [])
    return bool(checks) and all(
        bool(check.get("matches_expected_texture"))
        for check in checks
        if isinstance(check, dict)
    )


def _material_uds_free(unreal_preflight: dict[str, Any]) -> bool:
    material = unreal_preflight.get("sky_dome_material_check", {})
    return bool(material) and not material.get("dependency_error") and int(material.get("forbidden_dependency_count", -1)) == 0


def _material_uses_expected_texture(unreal_preflight: dict[str, Any]) -> bool:
    material = unreal_preflight.get("sky_dome_material_check", {})
    return bool(material.get("uses_expected_texture"))


def _dirty_content_clean(unreal_preflight: dict[str, Any]) -> bool:
    dirty = unreal_preflight.get("dirty_packages", {})
    return int(dirty.get("dirty_content_count", -1)) == 0


def _safe_dependency_audit(args: argparse.Namespace, output_path: Path) -> dict[str, Any]:
    audit_args = argparse.Namespace(
        package_root=args.package_root,
        forbidden_root=list(args.forbidden_root),
        output=str(output_path),
        timestamped_output=False,
        max_recursion_nodes=args.max_recursion_nodes,
        mcp_response_timeout_seconds=args.mcp_response_timeout_seconds,
    )
    try:
        return audit_cubeless_sky_dependencies.run(audit_args)
    except Exception as exc:
        return {
            "schema": "cubeless_sky_dependency_audit_runner_v1",
            "success": False,
            "pass": False,
            "error": str(exc),
            "report_path": str(output_path),
        }


def _build_validation(
    dependency_audit: dict[str, Any],
    unreal_preflight: dict[str, Any],
    blueprint_components: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    expected_sky_mesh = _object_path_from_package(args.expected_sky_mesh.rstrip("/"))
    sky_dome_mesh = _sky_dome_static_mesh(blueprint_components, args.sky_dome_component_name)
    return {
        "dependency_audit_pass": bool(dependency_audit.get("pass")),
        "targeted_unreal_preflight_success": bool(unreal_preflight.get("success")),
        "expected_assets_exist": _expected_assets_exist(unreal_preflight),
        "bp_sky_dome_mesh_expected": sky_dome_mesh == expected_sky_mesh,
        "weather_data_textures_expected": _weather_data_textures_expected(unreal_preflight),
        "sky_dome_material_uds_free": _material_uds_free(unreal_preflight),
        "sky_dome_material_uses_expected_texture": _material_uses_expected_texture(unreal_preflight),
        "dirty_content_clean": _dirty_content_clean(unreal_preflight),
    }


def _build_warnings(unreal_preflight: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    dirty = unreal_preflight.get("dirty_packages", {})
    dirty_maps = dirty.get("dirty_map_packages", []) if isinstance(dirty, dict) else []
    if dirty_maps:
        warnings.append(
            "Dirty map packages are reported but do not fail this preflight: "
            + ", ".join(str(item) for item in dirty_maps)
        )
    return warnings


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
        output_path = REPORT_DIR / f"cubeless_sky_promotion_preflight_{timestamp}.json"

    if args.timestamped_output:
        audit_output_path = REPORT_DIR / f"cubeless_sky_dependency_audit_for_preflight_{timestamp}.json"
    else:
        audit_output_path = REPORT_DIR / "cubeless_sky_dependency_audit_for_preflight.json"

    dependency_report = _safe_dependency_audit(args, audit_output_path)
    unreal_preflight = _execute_unreal_preflight(unreal, args)
    blueprint_components = _list_sky_dome_component(unreal, args)
    validation = _build_validation(dependency_report, unreal_preflight, blueprint_components, args)

    report = {
        "schema": "cubeless_sky_promotion_preflight_runner_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only Cubeless sky promotion preflight. Does not save or modify Unreal assets.",
        "package_root": args.package_root.rstrip("/"),
        "forbidden_roots": [root.rstrip("/") for root in args.forbidden_root],
        "expected": {
            "bp_sky_system": args.bp_sky_system.rstrip("/"),
            "sky_dome_component_name": args.sky_dome_component_name,
            "expected_sky_mesh": args.expected_sky_mesh.rstrip("/"),
            "expected_sky_mesh_object": _object_path_from_package(args.expected_sky_mesh.rstrip("/")),
            "sky_dome_material": args.sky_dome_material.rstrip("/"),
            "expected_cloud_texture": args.expected_cloud_texture.rstrip("/"),
            "expected_cloud_texture_object": _object_path_from_package(args.expected_cloud_texture.rstrip("/")),
            "weather_data_assets": [path.rstrip("/") for path in args.weather_data_asset],
        },
        "dependency_audit_report_path": dependency_report.get("report_path", str(audit_output_path)),
        "dependency_audit": dependency_report,
        "targeted_unreal_preflight": unreal_preflight,
        "blueprint_components": blueprint_components,
        "validation": validation,
        "warnings": _build_warnings(unreal_preflight),
        "pass": all(bool(value) for value in validation.values()),
        "report_path": str(output_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Cubeless sky promotion preflight checks.")
    parser.add_argument("--package-root", default=DEFAULT_PACKAGE_ROOT)
    parser.add_argument("--forbidden-root", action="append", default=list(DEFAULT_FORBIDDEN_ROOTS))
    parser.add_argument("--bp-sky-system", default=DEFAULT_BP_SKY_SYSTEM)
    parser.add_argument("--sky-dome-component-name", default=DEFAULT_SKY_DOME_COMPONENT)
    parser.add_argument("--sky-dome-material", default=DEFAULT_SKY_DOME_MATERIAL)
    parser.add_argument("--expected-sky-mesh", default=DEFAULT_SKY_MESH)
    parser.add_argument("--expected-cloud-texture", default=DEFAULT_CLOUD_TEXTURE)
    parser.add_argument("--weather-data-asset", action="append", default=list(DEFAULT_WEATHER_DATA_ASSETS))
    parser.add_argument("--output", default="")
    parser.add_argument("--timestamped-output", action="store_true")
    parser.add_argument("--max-recursion-nodes", type=int, default=5000)
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=180)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
