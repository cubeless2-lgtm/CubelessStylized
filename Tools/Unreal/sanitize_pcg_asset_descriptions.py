"""Scan PCG graph descriptions and shorten values that can crash AssetRegistry."""

from __future__ import annotations

import json
import os
import time

import unreal


SCAN_ROOTS = [
    "/Game/Cubeless/PCG",
    "/Game/PCG",
]
RISK_LIMIT_CHARS = 800
SAFE_LIMIT_CHARS = 240
REPORT_NAME = "pcg_description_safety_report.json"


def _asset_label(obj) -> str:
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _read_description(obj) -> str:
    if not obj:
        return ""
    try:
        return str(obj.get_editor_property("description") or "")
    except Exception:
        try:
            return str(obj.description or "")
        except Exception:
            return ""


def _write_description(obj, text: str) -> bool:
    safe_text = str(text or "")[:SAFE_LIMIT_CHARS].rstrip()
    try:
        obj.set_editor_property("description", safe_text)
        return True
    except Exception:
        try:
            obj.description = safe_text
            return True
        except Exception:
            return False


def _safe_preview(text: str) -> str:
    return str(text or "").replace("\n", " ")[:160]


def _shorten_text(text: str, scope: str) -> str:
    base = str(text or "").strip()
    if not base:
        base = "PCG graph description"
    prefix = scope[:48].strip()
    if prefix:
        base = f"{prefix}: {base}"
    if len(base) <= SAFE_LIMIT_CHARS:
        return base
    return base[: SAFE_LIMIT_CHARS - 3].rstrip() + "..."


def _pcg_asset_paths() -> list[str]:
    paths: list[str] = []
    for root in SCAN_ROOTS:
        try:
            if not unreal.EditorAssetLibrary.does_directory_exist(root):
                continue
        except Exception:
            pass
        try:
            for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
                normalized = str(path).split(".")[0]
                class_name = _asset_data_class_name(normalized)
                if "PCGGraph" in class_name:
                    paths.append(normalized)
        except Exception as exc:
            unreal.log_warning(f"PCG description safety scan skipped root {root}: {exc}")
    return sorted(set(paths))


def _asset_data_class_name(path: str) -> str:
    try:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
    except Exception:
        return ""
    for property_name in ("asset_class_path", "asset_class"):
        try:
            value = asset_data.get_editor_property(property_name)
        except Exception:
            try:
                value = getattr(asset_data, property_name)
            except Exception:
                value = None
        if not value:
            continue
        try:
            asset_name = value.asset_name
            if asset_name:
                return str(asset_name)
        except Exception:
            pass
        text = str(value)
        if text:
            return text
    return ""


def _graph_nodes(graph) -> list:
    try:
        return list(graph.get_editor_property("nodes"))
    except Exception:
        try:
            return list(graph.nodes)
        except Exception:
            return []


def _node_title(node) -> str:
    try:
        value = str(node.get_editor_property("node_title") or "")
    except Exception:
        value = ""
    return value or node.get_name()


def _settings_for(node):
    try:
        return node.get_settings()
    except Exception:
        return None


def _scan_graph(path: str) -> dict:
    item = {
        "asset_path": path,
        "loaded": False,
        "is_pcg_graph": False,
        "offenders": [],
        "fixes": [],
        "saved": False,
        "errors": [],
    }
    try:
        asset = unreal.EditorAssetLibrary.load_asset(path)
    except Exception as exc:
        item["errors"].append(f"load_exception: {exc}")
        return item
    if not asset:
        item["errors"].append("load_failed")
        return item
    item["loaded"] = True

    class_name = asset.get_class().get_name()
    if "PCGGraph" not in class_name:
        return item
    item["is_pcg_graph"] = True

    dirty = False
    graph_description = _read_description(asset)
    if len(graph_description) > RISK_LIMIT_CHARS:
        offender = {
            "scope": "graph",
            "length": len(graph_description),
            "preview": _safe_preview(graph_description),
        }
        item["offenders"].append(offender)
        replacement = _shorten_text(graph_description, "graph")
        if _write_description(asset, replacement):
            dirty = True
            item["fixes"].append({**offender, "new_length": len(_read_description(asset))})
        else:
            item["errors"].append("graph_description_write_failed")

    for node in _graph_nodes(asset):
        settings = _settings_for(node)
        if not settings:
            continue
        description = _read_description(settings)
        if len(description) <= RISK_LIMIT_CHARS:
            continue
        scope = f"settings:{_node_title(node)}"
        offender = {
            "scope": scope,
            "length": len(description),
            "preview": _safe_preview(description),
        }
        item["offenders"].append(offender)
        replacement = _shorten_text(description, scope)
        if _write_description(settings, replacement):
            dirty = True
            item["fixes"].append({**offender, "new_length": len(_read_description(settings))})
        else:
            item["errors"].append(f"{scope}:description_write_failed")

    if dirty:
        try:
            item["saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(asset, False))
            if not item["saved"]:
                item["errors"].append("save_failed")
        except Exception as exc:
            item["errors"].append(f"save_exception: {exc}")

    return item


def _write_report(report: dict) -> str:
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return report_path


def main() -> None:
    paths = _pcg_asset_paths()
    results = [_scan_graph(path) for path in paths]
    pcg_graphs = [item for item in results if item.get("is_pcg_graph")]
    offenders = [item for item in pcg_graphs if item.get("offenders")]
    failures = [item for item in pcg_graphs if item.get("errors") or (item.get("fixes") and not item.get("saved"))]
    report = {
        "success": not failures,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scan_roots": SCAN_ROOTS,
        "risk_limit_chars": RISK_LIMIT_CHARS,
        "safe_limit_chars": SAFE_LIMIT_CHARS,
        "asset_count": len(paths),
        "pcg_graph_count": len(pcg_graphs),
        "offender_count": len(offenders),
        "fixed_graph_count": sum(1 for item in pcg_graphs if item.get("fixes")),
        "failure_count": len(failures),
        "offenders": offenders,
        "failures": failures,
    }
    report_path = _write_report(report)
    unreal.log(
        "PCG description safety scan: graphs={} offenders={} fixed={} failures={} report={}".format(
            report["pcg_graph_count"],
            report["offender_count"],
            report["fixed_graph_count"],
            report["failure_count"],
            report_path,
        )
    )
    if failures:
        raise RuntimeError(f"PCG description safety scan had {len(failures)} failure(s): {report_path}")


if __name__ == "__main__":
    main()
