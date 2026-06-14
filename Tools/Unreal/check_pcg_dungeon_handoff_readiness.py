"""Check the Cubeless PCG dungeon V1 handoff readiness.

This is a local/read-only report combiner. It does not call UnrealMCP, does not
modify Unreal assets, and does not implement gameplay. It verifies that the
latest generated evidence agrees on the native PCG output that artists should
review and use as the current dungeon-generation result.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "MCP_Dungeon"
REPORT_PATH = REPORT_DIR / "CubelessDungeonMVP_HandoffReadiness.json"

EXPECTED_LEVEL = "/Game/Cubeless/PCG/Dungeon/Maps/LVL_Cubeless_PCG_Dungeon_MVP"
EXPECTED_PRODUCTION_GRAPH = "/Game/Cubeless/PCG/Dungeon/Graphs/PCG_Cubeless_Dungeon_MVP_NativeIntegration"
EXPECTED_POINT_SOURCE_GRAPH = "/Game/Cubeless/PCG/Dungeon/Graphs/PCG_Cubeless_Dungeon_MVP_NativePointSource"
EXPECTED_OUTPUT_ACTOR = "MCP_Cubeless_Dungeon_MVP_NativeOutput"
EXPECTED_BRIDGE_ACTOR = "MCP_Cubeless_Dungeon_MVP_PCGBridge"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _report_path(name: str) -> Path:
    return REPORT_DIR / name


def _load_report(name: str) -> dict[str, Any]:
    path = _report_path(name)
    return _read_json(path) if path.exists() else {}


def _nested_dict(source: dict[str, Any], *keys: str) -> dict[str, Any]:
    value: Any = source
    for key in keys:
        if not isinstance(value, dict):
            return {}
        value = value.get(key)
    return value if isinstance(value, dict) else {}


def _package_path_matches(value: Any, expected_package: str) -> bool:
    text = str(value or "")
    return text == expected_package or text.startswith(expected_package + ".")


def _failed_checks(checks: dict[str, Any]) -> list[str]:
    return [key for key, value in checks.items() if not bool(value)]


def _report_meta(name: str, data: dict[str, Any]) -> dict[str, Any]:
    path = _report_path(name)
    return {
        "path": str(path),
        "exists": path.exists(),
        "schema": data.get("schema"),
        "pass": data.get("pass"),
        "success": data.get("success"),
        "status": data.get("status"),
        "timestamp": data.get("timestamp"),
    }


def run(_args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    final_gate = _load_report("CubelessDungeonMVP_PCGGeneration_FinalGate.json")
    visual_gate = _load_report("CubelessDungeonMVP_PCGGeneration_VisualGateQA_Report.json")
    native_evidence = _load_report("CubelessDungeonMVP_NativeEvidenceRefresh_Report.json")
    point_source_graph = _load_report("CubelessDungeonMVP_NativePointSourceGraph_Report.json")
    integration_graph = _load_report("CubelessDungeonMVP_NativeIntegrationGraph_Report.json")
    integration_audit = _load_report("CubelessDungeonMVP_NativeIntegrationAudit_Report.json")
    native_output = _load_report("CubelessDungeonMVP_NativeIntegrationOutput_Report.json")
    output_only_review = _load_report("CubelessDungeonMVP_NativeOutputOnlyReview_Report.json")
    asset_audit = _load_report("CubelessDungeonMVP_AssetManifestAudit.json")
    dirty_state = _load_report("CubelessDungeonMVP_LiveDirtyState.json")

    final_component_summary = _nested_dict(final_gate, "live_native_output", "component_summary")
    expected_components = final_component_summary.get("component_count")
    expected_instances = final_component_summary.get("instance_count_total")
    final_target = _nested_dict(final_gate, "native_generation_target")
    final_checks = final_gate.get("checks", {}) if isinstance(final_gate.get("checks"), dict) else {}

    visual_top = _nested_dict(visual_gate, "top_capture")
    visual_oblique = _nested_dict(visual_gate, "oblique_capture")
    evidence_checks = native_evidence.get("checks", {}) if isinstance(native_evidence.get("checks"), dict) else {}

    point_source_counts = {
        "pcg_point_count": point_source_graph.get("pcg_point_count"),
        "source_point_count": point_source_graph.get("source_point_count"),
        "source_group_count": point_source_graph.get("source_group_count"),
        "branch_count": point_source_graph.get("branch_count"),
    }
    output_generation = _nested_dict(native_output, "generation_verification")
    output_summary = _nested_dict(output_generation, "component_summary")
    review_generation = _nested_dict(output_only_review, "native_output_generation")
    review_summary = _nested_dict(review_generation, "component_summary")
    bridge_after = _nested_dict(output_only_review, "bridge_static_mesh_after")
    preview_after = _nested_dict(output_only_review, "preview_after")
    review_lights_after = _nested_dict(output_only_review, "bridge_review_lights_after")
    live_dirty = _nested_dict(dirty_state, "dirty_state")
    asset_registry = _nested_dict(asset_audit, "unreal_audit")

    checks = {
        "expected_counts_available": expected_components is not None and expected_instances is not None,
        "final_gate_pass": bool(final_gate.get("pass") and final_gate.get("status") == "passed"),
        "final_gate_dirty_zero": final_gate.get("live_dirty_packages", {}).get("count") == 0,
        "final_gate_failed_checks_zero": not [key for key, value in final_checks.items() if value is False],
        "native_target_graph_matches": final_target.get("production_graph") == EXPECTED_PRODUCTION_GRAPH,
        "native_target_output_actor_matches": final_target.get("production_output_actor") == EXPECTED_OUTPUT_ACTOR,
        "native_target_bridge_actor_matches": final_target.get("bridge_actor") == EXPECTED_BRIDGE_ACTOR,
        "visual_gate_pass": bool(visual_gate.get("success") and visual_gate.get("exposure_review_pass")),
        "visual_gate_counts_match": _nested_dict(visual_gate, "final_gate").get("native_components") == expected_components
        and _nested_dict(visual_gate, "final_gate").get("native_instances") == expected_instances,
        "visual_gate_dirty_zero": _nested_dict(visual_gate, "final_gate").get("dirty_count") == 0,
        "top_screenshot_pass": bool(visual_top.get("qa_pass") and visual_top.get("capture_qa_pass")),
        "oblique_screenshot_pass": bool(visual_oblique.get("qa_pass") and visual_oblique.get("capture_qa_pass")),
        "native_evidence_summary_pass": bool(native_evidence.get("success")),
        "native_evidence_summary_checks_pass": bool(evidence_checks)
        and all(bool(value) for value in evidence_checks.values()),
        "native_evidence_counts_match": _nested_dict(native_evidence, "active_gate").get("native_components")
        == expected_components
        and _nested_dict(native_evidence, "active_gate").get("native_instances") == expected_instances,
        "point_source_graph_pass": bool(point_source_graph.get("pass")),
        "point_source_graph_path_matches": _package_path_matches(point_source_graph.get("graph_path"), EXPECTED_POINT_SOURCE_GRAPH),
        "point_source_graph_role_production": point_source_graph.get("graph_role") == "production",
        "point_source_outputs_points": bool(point_source_graph.get("output_connected"))
        and not bool(point_source_graph.get("spawns_static_meshes")),
        "point_source_counts_match": point_source_graph.get("pcg_point_count") == expected_instances
        and point_source_graph.get("source_point_count") == expected_instances,
        "integration_graph_pass": bool(integration_graph.get("pass")),
        "integration_graph_path_matches": _package_path_matches(
            integration_graph.get("graph_path"),
            EXPECTED_PRODUCTION_GRAPH,
        ),
        "integration_graph_role_production": integration_graph.get("graph_role") == "production",
        "integration_graph_output_connected": bool(integration_graph.get("output_connected")),
        "integration_graph_spawns_static_meshes": bool(integration_graph.get("spawns_static_meshes")),
        "integration_graph_point_source_loaded": bool(integration_graph.get("source_point_graph_loaded")),
        "integration_graph_point_source_count_match": integration_graph.get("source_point_graph_point_count")
        == expected_instances,
        "integration_graph_spawner_count_match": integration_graph.get("static_mesh_spawner_node_count")
        == expected_components,
        "integration_graph_no_setup_errors": integration_graph.get("setup_error_count") == 0
        and integration_graph.get("failed_edge_count") == 0,
        "integration_audit_pass": bool(integration_audit.get("pass")),
        "integration_audit_output_connected": bool(integration_audit.get("latest_native_integration_output_connected")),
        "integration_audit_mismatch_counts_zero": all(
            integration_audit.get(key) == 0
            for key in [
                "missing_filter_title_count",
                "missing_spawner_title_count",
                "unexpected_spawner_title_count",
                "spawner_mismatch_count",
                "class_count_mismatch_count",
                "duplicate_title_count",
                "missing_description_count",
                "subgraph_override_mismatch_count",
            ]
        ),
        "native_output_pass": bool(native_output.get("pass") and native_output.get("status") == "generated"),
        "native_output_graph_matches": _package_path_matches(native_output.get("graph_path"), EXPECTED_PRODUCTION_GRAPH),
        "native_output_actor_matches": native_output.get("actor_label") == EXPECTED_OUTPUT_ACTOR,
        "native_output_generation_ready": bool(
            output_generation.get("actor_found")
            and output_generation.get("component_found")
            and output_generation.get("generated_attr")
        ),
        "native_output_counts_match": output_summary.get("component_count") == expected_components
        and output_summary.get("instance_count_total") == expected_instances,
        "output_only_review_pass": bool(output_only_review.get("pass")),
        "output_only_review_enabled": bool(output_only_review.get("enabled")),
        "output_only_review_actor_matches": output_only_review.get("native_output_actor_label") == EXPECTED_OUTPUT_ACTOR,
        "output_only_review_counts_match": review_summary.get("component_count") == expected_components
        and review_summary.get("instance_count_total") == expected_instances,
        "bridge_validation_output_hidden": bridge_after.get("visible_static_mesh_component_count") == 0
        and bridge_after.get("hidden_static_mesh_component_count") == expected_instances,
        "preview_output_hidden": preview_after.get("visible_static_mesh_component_count") == 0,
        "bridge_review_lights_hidden": review_lights_after.get("visible_light_component_count") == 0,
        "asset_manifest_pass": bool(asset_audit.get("pass")),
        "asset_manifest_counts_match": asset_audit.get("expected_asset_count") == asset_registry.get("registry_count")
        == asset_registry.get("loaded_count"),
        "asset_manifest_no_redirectors": asset_registry.get("redirector_count") == 0
        and asset_registry.get("load_failure_count") == 0,
        "live_dirty_state_pass": bool(dirty_state.get("pass") and live_dirty.get("pass")),
        "live_dirty_state_zero": live_dirty.get("dirty_total_count") == 0,
        "gameplay_not_required": True,
    }

    pass_value = all(bool(value) for value in checks.values())
    report = {
        "schema": "cubeless_pcg_dungeon_handoff_readiness_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "policy": (
            "Read-only V1 handoff gate for PCG dungeon generation. It verifies the native PCG output, "
            "graph reports, screenshots, asset manifest, and dirty state. Gameplay implementation is out of scope."
        ),
        "expected": {
            "level": EXPECTED_LEVEL,
            "production_graph": EXPECTED_PRODUCTION_GRAPH,
            "point_source_graph": EXPECTED_POINT_SOURCE_GRAPH,
            "production_output_actor": EXPECTED_OUTPUT_ACTOR,
            "bridge_actor": EXPECTED_BRIDGE_ACTOR,
            "native_components": expected_components,
            "native_instances": expected_instances,
        },
        "reports": {
            "final_gate": _report_meta("CubelessDungeonMVP_PCGGeneration_FinalGate.json", final_gate),
            "visual_gate": _report_meta("CubelessDungeonMVP_PCGGeneration_VisualGateQA_Report.json", visual_gate),
            "native_evidence": _report_meta("CubelessDungeonMVP_NativeEvidenceRefresh_Report.json", native_evidence),
            "point_source_graph": _report_meta("CubelessDungeonMVP_NativePointSourceGraph_Report.json", point_source_graph),
            "integration_graph": _report_meta("CubelessDungeonMVP_NativeIntegrationGraph_Report.json", integration_graph),
            "integration_audit": _report_meta("CubelessDungeonMVP_NativeIntegrationAudit_Report.json", integration_audit),
            "native_output": _report_meta("CubelessDungeonMVP_NativeIntegrationOutput_Report.json", native_output),
            "output_only_review": _report_meta("CubelessDungeonMVP_NativeOutputOnlyReview_Report.json", output_only_review),
            "asset_manifest": _report_meta("CubelessDungeonMVP_AssetManifestAudit.json", asset_audit),
            "live_dirty_state": _report_meta("CubelessDungeonMVP_LiveDirtyState.json", dirty_state),
        },
        "summary": {
            "native_output_components": output_summary.get("component_count"),
            "native_output_instances": output_summary.get("instance_count_total"),
            "point_source": point_source_counts,
            "integration_graph_nodes": integration_graph.get("node_count"),
            "integration_graph_edges": integration_graph.get("edge_count"),
            "integration_graph_spawners": integration_graph.get("static_mesh_spawner_node_count"),
            "bridge_hidden_components": bridge_after.get("hidden_static_mesh_component_count"),
            "preview_hidden_components": preview_after.get("hidden_static_mesh_component_count"),
            "top_screenshot": visual_top.get("screenshot_path"),
            "oblique_screenshot": visual_oblique.get("screenshot_path"),
            "dirty_total_count": live_dirty.get("dirty_total_count"),
        },
        "checks": checks,
        "failed_checks": _failed_checks(checks),
        "pass": pass_value,
        "report_path": str(REPORT_PATH),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check PCG dungeon V1 handoff readiness from existing reports.")
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False))
