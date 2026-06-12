"""Audit PCG StaticMeshSpawner mesh selection routes.

Read-only audit for the project rule that newly authored PCG Static Mesh
spawner choices should be controllable through Blueprint actor properties where
practical. The script does not modify or save assets.
"""

import json
import os

import unreal


ROOT_PATHS = [
    "/Game/Cubeless/PCG",
]
REPORT_NAME = "CubelessPCGStaticMeshSpawnerActorPropertyAudit_Report.json"
POLICY_NAME = "pcg_static_mesh_spawner_audit_policy.json"
AUDIT_PRINT_FULL_REPORT = bool(globals().get("AUDIT_PRINT_FULL_REPORT", True))
DEFAULT_PRODUCTION_PATH_PREFIXES = (
    "/Game/Cubeless/PCG/Runtime/",
)
DEFAULT_RUNTIME_CLEANUP_PATH_PREFIXES = (
    "/Game/Cubeless/PCG/RuntimeGrass/",
)
DEFAULT_LEARNING_PATH_PREFIX = "/Game/Cubeless/PCG/ElectricDreamsLearning/"


def _load_audit_policy():
    policy_path = os.path.join(os.path.dirname(__file__), POLICY_NAME)
    policy = {
        "version": 0,
        "policy_path": policy_path,
        "loaded": False,
        "production_path_prefixes": list(DEFAULT_PRODUCTION_PATH_PREFIXES),
        "runtime_cleanup_path_prefixes": list(DEFAULT_RUNTIME_CLEANUP_PATH_PREFIXES),
        "learning_path_prefix": DEFAULT_LEARNING_PATH_PREFIX,
        "legacy_learning_allowlist": [],
        "cleanup_candidates": {},
    }
    if not os.path.exists(policy_path):
        return policy
    try:
        with open(policy_path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except Exception as exc:
        policy["load_error"] = str(exc)
        return policy
    policy.update(loaded)
    policy["policy_path"] = policy_path
    policy["loaded"] = True
    return policy


AUDIT_POLICY = _load_audit_policy()
PRODUCTION_PATH_PREFIXES = tuple(
    AUDIT_POLICY.get("production_path_prefixes") or DEFAULT_PRODUCTION_PATH_PREFIXES
)
RUNTIME_CLEANUP_PATH_PREFIXES = tuple(
    AUDIT_POLICY.get("runtime_cleanup_path_prefixes") or DEFAULT_RUNTIME_CLEANUP_PATH_PREFIXES
)
LEARNING_PATH_PREFIX = AUDIT_POLICY.get("learning_path_prefix") or DEFAULT_LEARNING_PATH_PREFIX
LEGACY_LEARNING_ALLOWLIST = set(AUDIT_POLICY.get("legacy_learning_allowlist") or [])
CLEANUP_CANDIDATE_BY_ASSET = {}
for _kind, _assets in (AUDIT_POLICY.get("cleanup_candidates") or {}).items():
    for _asset in _assets:
        CLEANUP_CANDIDATE_BY_ASSET[str(_asset)] = str(_kind)


def _object_path(obj):
    if not obj:
        return None
    try:
        return obj.get_path_name()
    except Exception:
        return str(obj)


def _safe_prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _pin_label(pin):
    try:
        return str(pin.get_editor_property("properties").get_editor_property("label"))
    except Exception:
        try:
            return pin.get_name()
        except Exception:
            return str(pin)


def _node_title(node):
    try:
        return str(node.get_editor_property("node_title"))
    except Exception:
        return str(getattr(node, "node_title", ""))


def _settings_class(node):
    try:
        return node.get_settings().get_class().get_name()
    except Exception:
        return ""


def _mesh_entries(params):
    entries = _safe_prop(params, "mesh_entries", [])
    rows = []
    try:
        iterator = list(entries)
    except Exception:
        iterator = []
    for entry in iterator:
        descriptor = _safe_prop(entry, "descriptor")
        mesh = _safe_prop(descriptor, "static_mesh") if descriptor else None
        rows.append(
            {
                "mesh": _object_path(mesh),
                "weight": _safe_prop(entry, "weight"),
            }
        )
    return rows


def _spawner_summary(node):
    settings = node.get_settings()
    selector_type = _object_path(_safe_prop(settings, "mesh_selector_type"))
    params = _safe_prop(settings, "mesh_selector_parameters")
    params_class = ""
    if params:
        try:
            params_class = params.get_class().get_name()
        except Exception:
            params_class = type(params).__name__
    attribute_name = _safe_prop(params, "attribute_name") if params else None
    entries = _mesh_entries(params) if params else []
    material_override_attrs = _safe_prop(params, "material_override_attributes", []) if params else []
    try:
        material_override_attrs = [str(item) for item in list(material_override_attrs)]
    except Exception:
        material_override_attrs = []
    use_attribute_material_overrides = bool(
        _safe_prop(params, "use_attribute_material_overrides", False)
    ) if params else False
    is_by_attribute = "PCGMeshSelectorByAttribute" in str(selector_type) or params_class == "PCGMeshSelectorByAttribute"
    is_weighted = "PCGMeshSelectorWeighted" in str(selector_type) or params_class == "PCGMeshSelectorWeighted"
    return {
        "node": node.get_name(),
        "title": _node_title(node),
        "selector_type": selector_type,
        "selector_parameters_class": params_class,
        "attribute_name": str(attribute_name) if attribute_name is not None else None,
        "weighted_mesh_entries": entries,
        "use_attribute_material_overrides": use_attribute_material_overrides,
        "material_override_attributes": material_override_attrs,
        "is_by_attribute": bool(is_by_attribute),
        "is_weighted_or_static": bool(is_weighted or entries),
        "covered_by_actor_property_split": False,
        "needs_actor_property_review": bool((is_weighted or entries) and not is_by_attribute),
    }


def _actor_property_nodes(graph):
    rows = []
    for node in list(getattr(graph, "nodes", [])):
        if _settings_class(node) != "PCGGetActorPropertySettings":
            continue
        settings = node.get_settings()
        rows.append(
            {
                "node": node.get_name(),
                "title": _node_title(node),
                "property_name": str(_safe_prop(settings, "property_name", "")),
                "output_attribute_name": str(_safe_prop(settings, "output_attribute_name", "")),
                "force_object_and_struct_extraction": str(
                    _safe_prop(settings, "force_object_and_struct_extraction", "")
                ),
            }
        )
    return rows


def _copy_attribute_nodes(graph):
    rows = []
    for node in list(getattr(graph, "nodes", [])):
        if _settings_class(node) != "PCGCopyAttributesSettings":
            continue
        settings = node.get_settings()
        rows.append(
            {
                "node": node.get_name(),
                "title": _node_title(node),
                "input_source": str(_safe_prop(settings, "input_source", "")),
                "output_target": str(_safe_prop(settings, "output_target", "")),
            }
        )
    return rows


def _asset_referencers(asset_path):
    try:
        return sorted(
            set(str(item) for item in unreal.EditorAssetLibrary.find_package_referencers_for_asset(asset_path, False))
        )
    except Exception as exc:
        return ["ERROR: {}".format(exc)]


def _is_empty_weighted_spawner(spawner):
    entries = spawner.get("weighted_mesh_entries") or []
    return bool(entries) and all(not entry.get("mesh") for entry in entries)


def _review_spawners(spawners):
    return [spawner for spawner in spawners if spawner.get("needs_actor_property_review")]


def _only_temp_referencers(referencers):
    if not referencers:
        return False
    for ref in referencers:
        text = str(ref)
        if text.startswith("/Game/_MCP_Temp/"):
            continue
        if "/Game/__ExternalActors__/_MCP_Temp/" in text:
            continue
        return False
    return True


def _graph_review_classification(asset_path, review_spawners, referencers):
    if not review_spawners:
        return "covered"

    policy_cleanup_kind = CLEANUP_CANDIDATE_BY_ASSET.get(asset_path)
    if policy_cleanup_kind:
        return "cleanup_candidate_{}".format(policy_cleanup_kind)

    if asset_path in LEGACY_LEARNING_ALLOWLIST:
        return "legacy_learning_referenced"

    all_empty_spawners = all(_is_empty_weighted_spawner(spawner) for spawner in review_spawners)
    if all_empty_spawners and not referencers:
        return "cleanup_candidate_empty_unreferenced"

    if any(asset_path.startswith(prefix) for prefix in PRODUCTION_PATH_PREFIXES):
        return "production_review"

    if any(asset_path.startswith(prefix) for prefix in RUNTIME_CLEANUP_PATH_PREFIXES):
        return "runtime_cleanup_candidate" if all_empty_spawners else "production_review"

    if asset_path.startswith(LEARNING_PATH_PREFIX):
        if "/MaterialOverridePresets/" in asset_path and not referencers:
            return "legacy_unreferenced_cleanup_candidate"
        if "/MaterialOverridePresets/" in asset_path and _only_temp_referencers(referencers):
            return "legacy_temp_referenced_cleanup_candidate"
        return "legacy_learning_referenced"

    return "review"


def _weighted_default_prefix(title):
    lowered = str(title).strip().lower()
    for marker in (
        " weightedmaterialoverride",
        " weighted material override",
        " truematerial default",
        " true material default",
        " weighted default",
        " default",
    ):
        if marker in lowered:
            return lowered.split(marker, 1)[0].strip()
    return None


def _is_material_override_weighted_spawner(spawner):
    title = str(spawner.get("title", "")).strip().lower()
    if "weightedmaterialoverride" not in title and "weighted material override" not in title:
        return False
    return bool(spawner.get("use_attribute_material_overrides")) and bool(
        spawner.get("material_override_attributes")
    )


def _has_matching_by_attribute_override(spawner, by_attribute_titles):
    prefix = _weighted_default_prefix(spawner.get("title", ""))
    if not prefix:
        return False
    return any(title.startswith(prefix) and "override" in title for title in by_attribute_titles)


def _mark_spawner_covered(spawner, covered, coverage):
    spawner["covered_by_actor_property_split"] = True
    spawner["needs_actor_property_review"] = False
    covered.append(
        {
            "node": spawner.get("node"),
            "title": spawner.get("title"),
            "coverage": coverage,
        }
    )


def _mark_actor_property_split_coverage(spawners, actor_props, copy_nodes):
    if not actor_props or not copy_nodes:
        return []
    by_attribute_titles = [
        str(spawner.get("title", "")).strip().lower()
        for spawner in spawners
        if spawner.get("is_by_attribute")
    ]
    covered = []
    for spawner in spawners:
        if not spawner.get("needs_actor_property_review"):
            continue
        if not _has_matching_by_attribute_override(spawner, by_attribute_titles):
            continue
        if _is_material_override_weighted_spawner(spawner):
            _mark_spawner_covered(
                spawner,
                covered,
                (
                    "weighted material override keeps weighted mesh selection and is paired "
                    "with a same-prefix by-attribute actor mesh/material override branch"
                ),
            )
        else:
            _mark_spawner_covered(
                spawner,
                covered,
                "weighted default is paired with same-prefix by-attribute actor-property override",
            )
    return covered


def _graph_summary(asset_path):
    graph = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not graph or not hasattr(graph, "nodes"):
        return None
    spawners = []
    for node in list(graph.nodes):
        if _settings_class(node) == "PCGStaticMeshSpawnerSettings":
            spawners.append(_spawner_summary(node))
    if not spawners:
        return None
    actor_props = _actor_property_nodes(graph)
    copy_nodes = _copy_attribute_nodes(graph)
    covered_split_defaults = _mark_actor_property_split_coverage(spawners, actor_props, copy_nodes)
    review_spawners = _review_spawners(spawners)
    review_count = len(review_spawners)
    referencers = _asset_referencers(asset_path) if review_count else []
    review_classification = _graph_review_classification(asset_path, review_spawners, referencers)
    return {
        "asset": asset_path,
        "review_classification": review_classification,
        "spawner_count": len(spawners),
        "needs_actor_property_review_count": review_count,
        "referencer_count": len(referencers),
        "referencers": referencers,
        "has_actor_property_nodes": bool(actor_props),
        "has_copy_attribute_nodes": bool(copy_nodes),
        "covered_split_default_count": len(covered_split_defaults),
        "covered_split_defaults": covered_split_defaults,
        "spawners": spawners,
        "actor_property_nodes": actor_props,
        "copy_attribute_nodes": copy_nodes,
    }


def _list_graph_assets():
    assets = []
    for root in ROOT_PATHS:
        for path in unreal.EditorAssetLibrary.list_assets(root, True, False):
            if path.endswith("_C"):
                continue
            asset = unreal.EditorAssetLibrary.load_asset(path)
            if asset and asset.get_class().get_name() == "PCGGraph":
                assets.append(path)
    return sorted(set(assets))


def _write_report(report):
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "MCP_PCG")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, REPORT_NAME)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    if AUDIT_PRINT_FULL_REPORT:
        print(json.dumps({"report": report_path, **report}, ensure_ascii=False))
    else:
        print(
            json.dumps(
                {
                    "report": report_path,
                    "policy": report.get("policy"),
                    "graph_asset_count": report.get("graph_asset_count"),
                    "static_mesh_spawner_count": report.get("static_mesh_spawner_count"),
                    "actionable_graphs_needing_actor_property_review": report.get(
                        "actionable_graphs_needing_actor_property_review"
                    ),
                    "actionable_review_spawner_count": report.get("actionable_review_spawner_count"),
                    "production_graphs_needing_actor_property_review": report.get(
                        "production_graphs_needing_actor_property_review"
                    ),
                    "production_review_spawner_count": report.get("production_review_spawner_count"),
                    "cleanup_candidate_graph_count": report.get("cleanup_candidate_graph_count"),
                    "cleanup_candidate_spawner_count": report.get("cleanup_candidate_spawner_count"),
                },
                ensure_ascii=False,
            )
        )
    return report_path


def audit_pcg_static_mesh_spawner_actor_property_overrides():
    graph_assets = _list_graph_assets()
    graphs = []
    for asset_path in graph_assets:
        summary = _graph_summary(asset_path)
        if summary:
            graphs.append(summary)
    review_graphs = [
        graph for graph in graphs if int(graph.get("needs_actor_property_review_count", 0)) > 0
    ]
    production_review_graphs = [
        graph for graph in review_graphs if graph.get("review_classification") == "production_review"
    ]
    cleanup_candidate_graphs = [
        graph
        for graph in review_graphs
        if "cleanup_candidate" in str(graph.get("review_classification", ""))
    ]
    actionable_review_graphs = [
        graph
        for graph in review_graphs
        if graph.get("review_classification")
        not in (
            "legacy_learning_referenced",
            "legacy_unreferenced_cleanup_candidate",
            "legacy_temp_referenced_cleanup_candidate",
            "cleanup_candidate_empty_unreferenced",
        )
        and "cleanup_candidate" not in str(graph.get("review_classification", ""))
    ]
    classification_counts = {}
    classification_spawner_counts = {}
    for graph in graphs:
        classification = graph.get("review_classification", "unknown")
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        classification_spawner_counts[classification] = classification_spawner_counts.get(classification, 0) + int(
            graph.get("needs_actor_property_review_count", 0)
        )
    report = {
        "root_paths": ROOT_PATHS,
        "policy": {
            "loaded": bool(AUDIT_POLICY.get("loaded")),
            "version": AUDIT_POLICY.get("version"),
            "policy_path": AUDIT_POLICY.get("policy_path"),
            "legacy_learning_allowlist_count": len(LEGACY_LEARNING_ALLOWLIST),
            "cleanup_candidate_count": len(CLEANUP_CANDIDATE_BY_ASSET),
            "load_error": AUDIT_POLICY.get("load_error"),
        },
        "graph_asset_count": len(graph_assets),
        "graphs_with_static_mesh_spawners": len(graphs),
        "graphs_needing_actor_property_review": len(review_graphs),
        "actionable_graphs_needing_actor_property_review": len(actionable_review_graphs),
        "actionable_review_spawner_count": sum(
            graph["needs_actor_property_review_count"] for graph in actionable_review_graphs
        ),
        "production_graphs_needing_actor_property_review": len(production_review_graphs),
        "production_review_spawner_count": sum(
            graph["needs_actor_property_review_count"] for graph in production_review_graphs
        ),
        "cleanup_candidate_graph_count": len(cleanup_candidate_graphs),
        "cleanup_candidate_spawner_count": sum(
            graph["needs_actor_property_review_count"] for graph in cleanup_candidate_graphs
        ),
        "review_classification_counts": classification_counts,
        "review_classification_spawner_counts": classification_spawner_counts,
        "static_mesh_spawner_count": sum(graph["spawner_count"] for graph in graphs),
        "review_spawner_count": sum(graph["needs_actor_property_review_count"] for graph in graphs),
        "graphs": graphs,
    }
    _write_report(report)
    return report


if __name__ == "__main__":
    audit_pcg_static_mesh_spawner_actor_property_overrides()
