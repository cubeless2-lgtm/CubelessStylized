"""Archive StaticMeshSpawner actor-property audit cleanup candidates.

This is intentionally conservative: it only moves graphs already classified as
cleanup candidates by the audit report, and it blocks any candidate referenced
outside disposable _MCP_Temp assets.
"""

import json
import os

import unreal


AUDIT_SCRIPT = os.path.join(
    unreal.Paths.project_dir(),
    "Tools",
    "Unreal",
    "audit_pcg_static_mesh_spawner_actor_property_overrides.py",
)
REPORT_NAME = "pcg_static_mesh_spawner_cleanup_archive_report.json"
ARCHIVE_ROOT = "/Game/Cubeless/_Archive/PCG_StaticMeshSpawnerActorPropertyAudit_20260612"
DRY_RUN = bool(globals().get("DRY_RUN", True))


def _run_audit():
    namespace = {
        "__name__": "__audit_loader__",
        "__file__": AUDIT_SCRIPT,
        "AUDIT_PRINT_FULL_REPORT": False,
    }
    with open(AUDIT_SCRIPT, "r", encoding="utf-8") as handle:
        exec(compile(handle.read(), AUDIT_SCRIPT, "exec"), namespace)
    audit_func = namespace.get("audit_pcg_static_mesh_spawner_actor_property_overrides")
    if not audit_func:
        raise RuntimeError("Audit function was not loaded")
    return audit_func()


def _object_to_asset_path(object_path):
    text = str(object_path)
    if "." in text:
        return text.rsplit(".", 1)[0]
    return text


def _asset_name(asset_path):
    return str(asset_path).rstrip("/").rsplit("/", 1)[-1]


def _folder_path(asset_path):
    return str(asset_path).rstrip("/").rsplit("/", 1)[0]


def _is_temp_ref(ref):
    text = str(ref)
    return text.startswith("/Game/_MCP_Temp/") or "/Game/__ExternalActors__/_MCP_Temp/" in text


def _destination_for(asset_path):
    prefix = "/Game/Cubeless/PCG/"
    if asset_path.startswith(prefix):
        relative = asset_path[len(prefix) :]
    else:
        relative = asset_path.replace("/Game/", "", 1)
    return "{}/PCG/{}".format(ARCHIVE_ROOT, relative)


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    unreal.log("PCG cleanup archive report: {}".format(report_path))
    print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    return report_path


def _archive_candidate(graph):
    object_path = graph.get("asset")
    source_path = _object_to_asset_path(object_path)
    destination_path = _destination_for(source_path)
    referencers = list(graph.get("referencers") or [])
    non_temp_referencers = [ref for ref in referencers if not _is_temp_ref(ref)]

    item = {
        "asset": object_path,
        "source_path": source_path,
        "destination_path": destination_path,
        "classification": graph.get("review_classification"),
        "referencer_count": len(referencers),
        "referencers": referencers,
        "non_temp_referencers": non_temp_referencers,
        "status": "pending",
    }

    if non_temp_referencers:
        item["status"] = "blocked_non_temp_referencers"
        return item
    if not unreal.EditorAssetLibrary.does_asset_exist(source_path):
        item["status"] = "source_missing"
        return item
    if unreal.EditorAssetLibrary.does_asset_exist(destination_path):
        item["status"] = "destination_exists"
        return item

    if DRY_RUN:
        item["status"] = "dry_run_ready"
        return item

    destination_folder = _folder_path(destination_path)
    unreal.EditorAssetLibrary.make_directory(destination_folder)
    moved = unreal.EditorAssetLibrary.rename_asset(source_path, destination_path)
    item["rename_result"] = bool(moved)
    if not moved:
        item["status"] = "rename_failed"
        return item

    if unreal.EditorAssetLibrary.does_asset_exist(destination_path):
        unreal.EditorAssetLibrary.save_asset(destination_path, only_if_is_dirty=False)
        item["destination_exists_after_move"] = True
    else:
        item["destination_exists_after_move"] = False
    item["source_exists_after_move"] = unreal.EditorAssetLibrary.does_asset_exist(source_path)
    item["status"] = "archived" if item["destination_exists_after_move"] else "archive_missing_destination"
    return item


def archive_pcg_static_mesh_spawner_cleanup_candidates():
    if not os.path.exists(AUDIT_SCRIPT):
        raise RuntimeError("Missing audit script: {}".format(AUDIT_SCRIPT))

    audit_report = _run_audit()
    candidates = [
        graph
        for graph in audit_report.get("graphs", [])
        if "cleanup_candidate" in str(graph.get("review_classification", ""))
    ]
    items = [_archive_candidate(graph) for graph in candidates]
    blocked = [item for item in items if item.get("status", "").startswith("blocked")]
    failed = [
        item
        for item in items
        if item.get("status")
        not in ("dry_run_ready", "archived", "source_missing", "destination_exists")
        and not item.get("status", "").startswith("blocked")
    ]
    archived = [item for item in items if item.get("status") == "archived"]
    report = {
        "dry_run": DRY_RUN,
        "archive_root": ARCHIVE_ROOT,
        "candidate_count": len(candidates),
        "archived_count": len(archived),
        "blocked_count": len(blocked),
        "failed_count": len(failed),
        "items": items,
        "pass": bool(candidates) and not blocked and not failed,
    }
    _write_report(report)
    if blocked or failed:
        raise RuntimeError(
            "PCG cleanup archive had blocked/failed candidates: blocked={} failed={}".format(
                len(blocked), len(failed)
            )
        )
    return report


if __name__ == "__main__":
    archive_pcg_static_mesh_spawner_cleanup_candidates()
