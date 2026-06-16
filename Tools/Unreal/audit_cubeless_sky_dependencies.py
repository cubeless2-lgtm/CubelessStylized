#!/usr/bin/env python3
"""Audit Cubeless sky assets for forbidden UDS dependencies.

This is a read-only UnrealMCP AssetRegistry audit. It scans a Cubeless sky
package root, resolves direct and recursive dependencies, and flags references
to `/Game/UltraDynamicSky` or other configured forbidden roots.
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
    send,
)


DEFAULT_PACKAGE_ROOT = "/Game/Cubeless/Sky"
DEFAULT_FORBIDDEN_ROOTS = ["/Game/UltraDynamicSky"]
REPORT_DIR = PROJECT_ROOT / "Saved" / "UDS_Analysis"
DEFAULT_REPORT_PATH = REPORT_DIR / "cubeless_sky_dependency_audit.json"


UNREAL_AUDIT_CODE = r"""
import json
import traceback

import unreal


PACKAGE_ROOT = __PACKAGE_ROOT__
FORBIDDEN_ROOTS = __FORBIDDEN_ROOTS__
MAX_RECURSION_NODES = __MAX_RECURSION_NODES__


def to_string(value):
    try:
        return str(value)
    except Exception:
        return ""


def asset_data_package(asset_data):
    return to_string(getattr(asset_data, "package_name", ""))


def asset_data_name(asset_data):
    return to_string(getattr(asset_data, "asset_name", ""))


def asset_data_class(asset_data):
    class_path = getattr(asset_data, "asset_class_path", None)
    if class_path:
        asset_name = getattr(class_path, "asset_name", None)
        if asset_name:
            return to_string(asset_name)
        return to_string(class_path)
    return to_string(getattr(asset_data, "asset_class", ""))


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


def normalize_package_name(value):
    text = to_string(value)
    if "." in text and text.startswith("/Game/"):
        return text.split(".", 1)[0]
    return text


def package_starts_with(package_name, roots):
    return any(package_name == root or package_name.startswith(root + "/") for root in roots)


def classify_forbidden_dependency(package_name):
    if "/Materials/Material_Functions/" in package_name and package_name.endswith("_MPC"):
        return "uds_mpc"
    if "/Materials/Material_Functions/" in package_name:
        return "uds_material_function"
    if "/Materials/" in package_name:
        return "uds_material"
    if "/Textures/" in package_name:
        return "uds_texture"
    if "/Meshes/" in package_name:
        return "uds_mesh"
    if "/Blueprints/" in package_name:
        return "uds_blueprint"
    return "uds_other"


def should_recurse(package_name):
    if package_name.startswith("/Script/"):
        return False
    if package_name.startswith("/Engine/"):
        return False
    return True


def get_dependencies(registry, options, package_name):
    try:
        deps = registry.get_dependencies(package_name, options)
    except Exception as exc:
        return [], str(exc)
    return sorted({normalize_package_name(dep) for dep in deps if to_string(dep)}), None


def reconstruct_path(parent_by_node, source, target):
    path = [target]
    cursor = target
    seen = set()
    while cursor != source and cursor in parent_by_node and cursor not in seen:
        seen.add(cursor)
        cursor = parent_by_node[cursor]
        path.append(cursor)
    path.reverse()
    return path


def recursive_dependencies(registry, options, source_package):
    queue = [source_package]
    visited = set([source_package])
    parent_by_node = {}
    errors = []
    all_dependencies = set()

    while queue and len(visited) < MAX_RECURSION_NODES:
        current = queue.pop(0)
        deps, error = get_dependencies(registry, options, current)
        if error:
            errors.append({"package": current, "error": error})
            continue
        for dep in deps:
            all_dependencies.add(dep)
            if dep not in parent_by_node:
                parent_by_node[dep] = current
            if dep not in visited and should_recurse(dep):
                visited.add(dep)
                queue.append(dep)

    truncated = bool(queue)
    forbidden = sorted(
        dep for dep in all_dependencies
        if package_starts_with(dep, FORBIDDEN_ROOTS)
    )
    forbidden_paths = [
        {
            "forbidden_dependency": dep,
            "classification": classify_forbidden_dependency(dep),
            "path": reconstruct_path(parent_by_node, source_package, dep),
        }
        for dep in forbidden
    ]
    return {
        "dependency_count": len(all_dependencies),
        "forbidden_dependency_count": len(forbidden),
        "forbidden_dependencies": forbidden,
        "forbidden_paths": forbidden_paths,
        "visited_count": len(visited),
        "truncated": truncated,
        "errors": errors,
    }


try:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = make_dependency_options()
    scan_error = None
    try:
        registry.scan_paths_synchronous([PACKAGE_ROOT], True)
    except Exception as exc:
        scan_error = str(exc)

    try:
        asset_data_items = list(registry.get_assets_by_path(PACKAGE_ROOT, True, False))
    except TypeError:
        asset_data_items = list(registry.get_assets_by_path(PACKAGE_ROOT, recursive=True))

    asset_records = []
    direct_offenders = []
    recursive_offenders = []
    class_counts = {}
    direct_dependency_errors = []

    for asset_data in asset_data_items:
        package_name = asset_data_package(asset_data)
        class_name = asset_data_class(asset_data)
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        direct_dependencies, direct_error = get_dependencies(registry, options, package_name)
        if direct_error:
            direct_dependency_errors.append({"package": package_name, "error": direct_error})
            direct_dependencies = []

        direct_forbidden = sorted(
            dep for dep in direct_dependencies
            if package_starts_with(dep, FORBIDDEN_ROOTS)
        )
        recursive = recursive_dependencies(registry, options, package_name)

        record = {
            "package": package_name,
            "asset_name": asset_data_name(asset_data),
            "class": class_name,
            "direct_dependency_count": len(direct_dependencies),
            "direct_forbidden_dependency_count": len(direct_forbidden),
            "direct_forbidden_dependencies": [
                {
                    "package": dep,
                    "classification": classify_forbidden_dependency(dep),
                }
                for dep in direct_forbidden
            ],
            "recursive_dependency_count": recursive["dependency_count"],
            "recursive_forbidden_dependency_count": recursive["forbidden_dependency_count"],
            "recursive_forbidden_dependencies": [
                {
                    "package": dep,
                    "classification": classify_forbidden_dependency(dep),
                }
                for dep in recursive["forbidden_dependencies"]
            ],
            "recursive_forbidden_paths": recursive["forbidden_paths"],
            "recursive_truncated": recursive["truncated"],
            "recursive_errors": recursive["errors"],
        }
        asset_records.append(record)
        if direct_forbidden:
            direct_offenders.append(record)
        if recursive["forbidden_dependencies"]:
            recursive_offenders.append(record)

    classification_counts = {}
    for record in asset_records:
        for dep in record["recursive_forbidden_dependencies"]:
            key = dep["classification"]
            classification_counts[key] = classification_counts.get(key, 0) + 1

    report = {
        "success": bool(not scan_error and not direct_dependency_errors),
        "schema": "cubeless_sky_dependency_audit_unreal_v1",
        "policy": "Read-only AssetRegistry dependency audit. Does not save or modify Unreal assets.",
        "package_root": PACKAGE_ROOT,
        "forbidden_roots": FORBIDDEN_ROOTS,
        "asset_count": len(asset_records),
        "class_counts": class_counts,
        "scan_error": scan_error,
        "direct_dependency_errors": direct_dependency_errors,
        "direct_offender_count": len(direct_offenders),
        "recursive_offender_count": len(recursive_offenders),
        "forbidden_classification_counts": classification_counts,
        "direct_offenders": direct_offenders,
        "recursive_offenders": recursive_offenders,
        "assets": asset_records,
    }
except Exception as exc:
    report = {
        "success": False,
        "schema": "cubeless_sky_dependency_audit_unreal_v1",
        "policy": "Read-only AssetRegistry dependency audit. Does not save or modify Unreal assets.",
        "package_root": PACKAGE_ROOT,
        "forbidden_roots": FORBIDDEN_ROOTS,
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }

print(json.dumps(report, ensure_ascii=False))
"""


def _json_literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _build_unreal_code(args: argparse.Namespace) -> str:
    return (
        UNREAL_AUDIT_CODE.replace("__PACKAGE_ROOT__", _json_literal(args.package_root.rstrip("/")))
        .replace("__FORBIDDEN_ROOTS__", _json_literal([root.rstrip("/") for root in args.forbidden_root]))
        .replace("__MAX_RECURSION_NODES__", str(args.max_recursion_nodes))
    )


def _execute_unreal_audit(unreal: UnrealConnection, args: argparse.Namespace) -> dict[str, Any]:
    response = send(
        unreal,
        "execute_python",
        {"code": _build_unreal_code(args), "mode": "ExecuteFile"},
    )
    return parse_execute_python_log_json(response)


def _build_validation(unreal_audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "unreal_audit_success": bool(unreal_audit.get("success")),
        "assets_found": int(unreal_audit.get("asset_count", 0) or 0) > 0,
        "no_direct_forbidden_dependencies": int(unreal_audit.get("direct_offender_count", -1)) == 0,
        "no_recursive_forbidden_dependencies": int(unreal_audit.get("recursive_offender_count", -1)) == 0,
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
        output_path = REPORT_DIR / f"cubeless_sky_dependency_audit_{timestamp}.json"

    unreal_audit = _execute_unreal_audit(unreal, args)
    validation = _build_validation(unreal_audit)
    report = {
        "schema": "cubeless_sky_dependency_audit_runner_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only Cubeless sky dependency audit. Does not save or modify Unreal assets.",
        "package_root": args.package_root.rstrip("/"),
        "forbidden_roots": [root.rstrip("/") for root in args.forbidden_root],
        "unreal_audit": unreal_audit,
        "validation": validation,
        "pass": all(bool(value) for value in validation.values()),
        "report_path": str(output_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Cubeless sky assets for forbidden UDS dependencies.")
    parser.add_argument("--package-root", default=DEFAULT_PACKAGE_ROOT)
    parser.add_argument("--forbidden-root", action="append", default=list(DEFAULT_FORBIDDEN_ROOTS))
    parser.add_argument("--output", default="")
    parser.add_argument("--timestamped-output", action="store_true")
    parser.add_argument("--max-recursion-nodes", type=int, default=5000)
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=180)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
