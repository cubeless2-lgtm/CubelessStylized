"""Audit the Cubeless PCG dungeon asset manifest through UnrealMCP.

The audit is read-only for Unreal assets. It compares the local files under
Content/Cubeless/PCG/Dungeon with AssetRegistry packages, attempts to load each
expected asset, checks for redirectors, and writes a generated report under
Saved/MCP_Dungeon.
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


DUNGEON_CONTENT_DIR = PROJECT_ROOT / "Content" / "Cubeless" / "PCG" / "Dungeon"
DUNGEON_PACKAGE_ROOT = "/Game/Cubeless/PCG/Dungeon"
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_Dungeon" / "CubelessDungeonMVP_AssetManifestAudit.json"


def _package_path_from_content_file(path: Path) -> str:
    relative = path.relative_to(PROJECT_ROOT / "Content").with_suffix("")
    return "/Game/" + relative.as_posix()


def _collect_expected_assets() -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for path in sorted(DUNGEON_CONTENT_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".uasset", ".umap"}:
            continue
        assets.append(
            {
                "file_path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "package_path": _package_path_from_content_file(path),
                "extension": path.suffix.lower(),
                "file_size": path.stat().st_size,
            }
        )
    return assets


def _execute_unreal_audit(unreal: UnrealConnection, expected_packages: list[str]) -> dict[str, Any]:
    expected_json = json.dumps(expected_packages, ensure_ascii=False, indent=2)
    code = f"""
import json
import unreal

PACKAGE_ROOT = {json.dumps(DUNGEON_PACKAGE_ROOT)}
EXPECTED_PACKAGES = {expected_json}


def _to_string(value):
    try:
        return str(value)
    except Exception:
        return ""


def _object_path_for_package(package_path):
    asset_name = package_path.rsplit("/", 1)[-1]
    return package_path + "." + asset_name


def _asset_data_package(asset_data):
    return _to_string(getattr(asset_data, "package_name", ""))


def _asset_data_class(asset_data):
    class_path = getattr(asset_data, "asset_class_path", None)
    if class_path:
        asset_name = getattr(class_path, "asset_name", None)
        if asset_name:
            return _to_string(asset_name)
        return _to_string(class_path)
    asset_class = getattr(asset_data, "asset_class", None)
    return _to_string(asset_class)


def _load_asset(package_path):
    exists = False
    load_error = None
    asset = None
    try:
        exists = bool(unreal.EditorAssetLibrary.does_asset_exist(package_path))
    except Exception as exc:
        load_error = "does_asset_exist failed: " + str(exc)
    for candidate in (package_path, _object_path_for_package(package_path)):
        if asset:
            break
        try:
            asset = unreal.EditorAssetLibrary.load_asset(candidate)
        except Exception as exc:
            load_error = "load_asset failed for " + candidate + ": " + str(exc)
    if not asset:
        try:
            asset = unreal.load_object(None, _object_path_for_package(package_path))
        except Exception as exc:
            load_error = "load_object failed: " + str(exc)
    class_name = None
    object_path = None
    if asset:
        try:
            class_name = asset.get_class().get_name()
        except Exception as exc:
            load_error = "get_class failed: " + str(exc)
        try:
            object_path = asset.get_path_name()
        except Exception:
            object_path = _object_path_for_package(package_path)
    return {{
        "package_path": package_path,
        "exists": bool(exists or asset),
        "loaded": bool(asset),
        "class": class_name,
        "object_path": object_path,
        "is_redirector": bool(class_name and "redirector" in class_name.lower()),
        "error": load_error,
    }}


scan_error = None
registry_error = None
asset_data_items = []
try:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        registry.scan_paths_synchronous([PACKAGE_ROOT], True)
    except Exception as exc:
        scan_error = str(exc)
    try:
        asset_data_items = list(registry.get_assets_by_path(PACKAGE_ROOT, True, False))
    except TypeError:
        asset_data_items = list(registry.get_assets_by_path(PACKAGE_ROOT, recursive=True))
except Exception as exc:
    registry_error = str(exc)

registry_records = []
for asset_data in asset_data_items:
    package_path = _asset_data_package(asset_data)
    registry_records.append({{
        "package_path": package_path,
        "asset_name": _to_string(getattr(asset_data, "asset_name", "")),
        "class": _asset_data_class(asset_data),
    }})

registry_packages = sorted({{item["package_path"] for item in registry_records if item.get("package_path")}})
expected_set = set(EXPECTED_PACKAGES)
registry_set = set(registry_packages)
load_records = [_load_asset(package_path) for package_path in sorted(EXPECTED_PACKAGES)]
load_failures = [item for item in load_records if not item.get("loaded")]
redirectors = [
    item for item in load_records
    if item.get("is_redirector") or "redirector" in str(item.get("class", "")).lower()
]
class_counts = {{}}
for item in load_records:
    class_name = item.get("class") or "UNLOADED"
    class_counts[class_name] = class_counts.get(class_name, 0) + 1

report = {{
    "success": bool(not registry_error and not scan_error and not load_failures and not redirectors and not (expected_set - registry_set)),
    "schema": "cubeless_pcg_dungeon_asset_manifest_audit_v1",
    "package_root": PACKAGE_ROOT,
    "expected_count": len(EXPECTED_PACKAGES),
    "registry_count": len(registry_packages),
    "loaded_count": len([item for item in load_records if item.get("loaded")]),
    "registry_error": registry_error,
    "scan_error": scan_error,
    "missing_from_registry": sorted(expected_set - registry_set),
    "extra_registry_packages": sorted(registry_set - expected_set),
    "load_failure_count": len(load_failures),
    "load_failures": load_failures,
    "redirector_count": len(redirectors),
    "redirectors": redirectors,
    "class_counts": class_counts,
    "registry_records": registry_records,
    "load_records": load_records,
}}
print(json.dumps(report, ensure_ascii=False))
"""
    response = send(unreal, "execute_python", {"code": code, "mode": "ExecuteFile"})
    return parse_execute_python_log_json(response)


def run(args: argparse.Namespace) -> dict[str, Any]:
    expected_assets = _collect_expected_assets()
    expected_packages = [item["package_path"] for item in expected_assets]
    unreal = UnrealConnection()
    if hasattr(unreal, "timeout"):
        unreal.timeout = max(int(getattr(unreal, "timeout", 0)), int(args.mcp_response_timeout_seconds))

    unreal_audit = _execute_unreal_audit(unreal, expected_packages)
    validation = {
        "local_asset_count_matches_expected": len(expected_assets) == len(expected_packages),
        "registry_contains_expected": not unreal_audit.get("missing_from_registry"),
        "all_expected_assets_loaded": int(unreal_audit.get("load_failure_count", -1)) == 0,
        "no_redirectors": int(unreal_audit.get("redirector_count", -1)) == 0,
        "unreal_audit_success": bool(unreal_audit.get("success")),
    }
    report = {
        "schema": "cubeless_pcg_dungeon_asset_manifest_audit_runner_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "policy": "Read-only PCG dungeon asset manifest audit. Does not modify or save Unreal assets.",
        "package_root": DUNGEON_PACKAGE_ROOT,
        "content_root": str(DUNGEON_CONTENT_DIR),
        "expected_assets": expected_assets,
        "expected_asset_count": len(expected_assets),
        "unreal_audit": unreal_audit,
        "validation": validation,
        "pass": all(bool(value) for value in validation.values()),
        "report_path": str(REPORT_PATH),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the Cubeless PCG dungeon Unreal asset manifest.")
    parser.add_argument("--mcp-response-timeout-seconds", type=int, default=120)
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps(result, ensure_ascii=False))
