"""Compile a natural-language StackOBot animation request into a safe route.

This helper is local/read-only. It does not call Unreal, does not touch assets,
and does not require the editor bridge. It mirrors the route tokens documented
in the StackOBot animation study docs so future requests can start from a
consistent sample-only command and verification gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_DocAudit" / "StackOBotAnimationRequestCompiler.json"
SCHEMA = "stackobot_animation_request_compiler_v1"
SAMPLE_ROOT = "/Game/_MCP_Sample/AnimStudy"
EVIDENCE_ROOT = "D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy"


ROUTES: dict[str, dict[str, Any]] = {
    "Post Process ModifyBone": {
        "target_character": "Bot",
        "target_body_area": "head",
        "timing_type": "static late additive rotation",
        "runtime_layer": "Post Process AnimBP",
        "sample_target": f"{SAMPLE_ROOT}/ABP_Bot_PostProcess_Study_HeadYawPlus5Study",
        "first_read_or_authoring_command": "ensure_postprocess_anim_demo_variant",
        "verification_command": (
            "sample_anim_node_pre_post_runtime_pose("
            "mode=pose_watch_capture, anim_instance_source=post_process, prefer_pie_world=false)"
        ),
        "expected_evidence": "runtime_graph_prepost=true, same_instance_prepost=true, requested bone delta",
        "handoff_template": "Post Process ModifyBone",
        "cxx_api_status": "not needed",
        "ask_user_first": False,
        "assumption": "Use a reversible sample-only late bone adjustment unless original mutation is approved.",
        "priority": 80,
    },
    "BlendSpace sample variant": {
        "target_character": "Bot",
        "target_body_area": "locomotion body response",
        "timing_type": "continuous BlendSpace axis response",
        "runtime_layer": "main AnimBP source BlendSpace",
        "sample_target": f"{SAMPLE_ROOT}/BS_Bot_WalkRunLean_LeanWideStudy",
        "first_read_or_authoring_command": "ensure_blendspace_sample_variant",
        "verification_command": "sample_blendspace_runtime_pose_grid",
        "expected_evidence": "valid_pose_count and input_changed_pose=true for requested grid inputs",
        "handoff_template": "BlendSpace Sample Variant",
        "cxx_api_status": "not needed",
        "ask_user_first": False,
        "assumption": "Edit only the sample BlendSpace axis or sample coordinates.",
        "priority": 60,
    },
    "Bot Trail sample": {
        "target_character": "Bot",
        "target_body_area": "antenna_04_l chain, mirrored only if requested",
        "timing_type": "secondary motion / follow-through",
        "runtime_layer": "Post Process AnimBP physics-style node",
        "sample_target": f"{SAMPLE_ROOT}/ABP_Bot_Trail_Study",
        "first_read_or_authoring_command": "ensure_anim_graph_trail_demo",
        "verification_command": (
            "sample_anim_node_pre_post_runtime_pose("
            "mode=pose_watch_capture, anim_instance_source=post_process, prefer_pie_world=true)"
        ),
        "expected_evidence": "same-instance Trail input/output and target chain delta in SIE/PIE",
        "handoff_template": "Trail Or Secondary Motion",
        "cxx_api_status": "not needed for current Trail sample",
        "ask_user_first": False,
        "assumption": "Use the existing Bot Trail sample route; do not reactivate the original disconnected Trail node.",
        "priority": 70,
    },
    "UpperBody Slot and LayeredBlend": {
        "target_character": "Bot",
        "target_body_area": "upper body",
        "timing_type": "overlay action over locomotion",
        "runtime_layer": "Slot / LayeredBoneBlend in main AnimBP",
        "sample_target": "none for route proof; future sample overlay only if action source is required",
        "first_read_or_authoring_command": "slot/cached-pose inventory, then all-input PoseWatch",
        "verification_command": "sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture, input_pose_mode=all)",
        "expected_evidence": (
            "BasePose from LocomotionPose and BlendPoses[0] from CashedPose_UpperBody in the same AnimInstance"
        ),
        "handoff_template": "UpperBody Slot And LayeredBlend",
        "cxx_api_status": "candidate only if a new visible action source or overlay branch is required",
        "ask_user_first": False,
        "assumption": "Prove the existing UpperBody route first; do not claim visible action proof without a source.",
        "priority": 65,
    },
    "protected metadata boundary": {
        "target_character": "Bot or Baddy, depending on the named asset",
        "target_body_area": "animation source metadata",
        "timing_type": "notify / curve / sync marker / Montage metadata",
        "runtime_layer": "animation asset metadata, not pose graph",
        "sample_target": "none until a guarded native API is approved/implemented",
        "first_read_or_authoring_command": "safe animation asset inventory and AssetRegistry-level scan only",
        "verification_command": "none for protected internals with current tooling",
        "expected_evidence": "clear report of readable fields and blocked protected fields",
        "handoff_template": "Notify, Curve, Sync Marker, Or Montage Internals",
        "cxx_api_status": "candidate guarded native API for concrete metadata requests",
        "ask_user_first": True,
        "assumption": "Do not broad-probe Montage or notify internals with generic Python.",
        "priority": 100,
    },
    "ControlRig gate probe": {
        "target_character": "Bot",
        "target_body_area": "foot IK / interaction reach",
        "timing_type": "late correction gated by runtime inputs and curves",
        "runtime_layer": "ControlRig inside the main AnimBP",
        "sample_target": f"{SAMPLE_ROOT}/ABP_Bot_ControlRig_ForcedDriver_Study",
        "first_read_or_authoring_command": "inspect_anim_graph_protected_topology, then controlrig_direct_gate_probe",
        "verification_command": "sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture)",
        "expected_evidence": (
            "ControlRig is root-connected, required gates are identified, and same-instance pre/post delta appears"
        ),
        "handoff_template": "ControlRig Late Correction",
        "cxx_api_status": "not needed unless the requested gate or pin cannot be driven by existing commands",
        "ask_user_first": False,
        "assumption": "Use direct gate probe first; create a forced-driver sample only if gameplay gates stay inactive.",
        "priority": 75,
    },
    "state-machine runtime-driver proof": {
        "target_character": "Bot",
        "target_body_area": "locomotion state-machine behavior",
        "timing_type": "state duration or transition condition",
        "runtime_layer": "main AnimBP state machine",
        "sample_target": "none for first pass; future sample graph only if runtime-driver proof is insufficient",
        "first_read_or_authoring_command": "inspect_anim_state_machine_transitions",
        "verification_command": "sample_anim_state_machine_runtime_response",
        "expected_evidence": "driver cases show current state, transition progress, state weight, and restored properties",
        "handoff_template": "State Machine Or Runtime Driver",
        "cxx_api_status": "candidate only if a new state, sequence player, or transition rule must be authored",
        "ask_user_first": False,
        "assumption": "Read and prove runtime-driver behavior before any graph authoring.",
        "priority": 68,
    },
    "Baddy RigidBody": {
        "target_character": "Baddy",
        "target_body_area": "stalk / body secondary motion",
        "timing_type": "animation physics response",
        "runtime_layer": "RigidBody node in the AnimBP",
        "sample_target": f"{SAMPLE_ROOT}/ABP_Baddy_RigidBody_Study",
        "first_read_or_authoring_command": "inspect_anim_graph_node_settings",
        "verification_command": "sample_anim_node_pre_post_runtime_pose(mode=compiled_graph_mapping)",
        "expected_evidence": "RigidBody settings, mapped runtime node, and source-vs-output or pre/post pose deltas",
        "handoff_template": "Trail Or Secondary Motion",
        "cxx_api_status": "not needed for narrow setting reads or sample tuning; candidate for deeper PhysicsAsset inspection",
        "ask_user_first": False,
        "assumption": "Separate animation physics from world collision/destruction physics.",
        "priority": 72,
    },
    "node resolver plus same-instance pre/post proof": {
        "target_character": "Bot or Baddy, depending on the selected graph",
        "target_body_area": "target node output and affected bones",
        "timing_type": "instrumentation only",
        "runtime_layer": "compiled AnimGraph node contribution",
        "sample_target": "none unless a controlled sample actor is needed for runtime proof",
        "first_read_or_authoring_command": "inspect_anim_graph_protected_topology or compiled mapping for the suspected node",
        "verification_command": "sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture)",
        "expected_evidence": "target node selection, input/output links, sampled bone deltas, and same-instance confirmation",
        "handoff_template": "no authoring handoff unless the proof needs a sample actor setup",
        "cxx_api_status": "not needed unless the node class is unsupported or actor resolution repeatedly fails",
        "ask_user_first": False,
        "assumption": "Do not edit assets; identify the suspected node before interpreting pose deltas.",
        "priority": 55,
    },
}


SIGNAL_RULES: list[dict[str, Any]] = [
    {
        "route": "protected metadata boundary",
        "weight": 10,
        "keywords": ["notify", "notifies", "curve", "sync marker", "montage", "section", "노티파이", "커브", "싱크", "몽타주"],
    },
    {
        "route": "node resolver plus same-instance pre/post proof",
        "weight": 9,
        "keywords": ["which node", "caused", "pre/post", "pose change", "어느 노드", "어떤 노드", "왜", "증명", "원인"],
    },
    {
        "route": "ControlRig gate probe",
        "weight": 8,
        "keywords": ["foot", "feet", "ik", "interaction", "touch", "reach", "발", "상호작용", "닿", "짚"],
    },
    {
        "route": "UpperBody Slot and LayeredBlend",
        "weight": 8,
        "keywords": ["upper body", "attack", "button", "while moving", "상체", "공격", "버튼", "이동 중", "움직이면서"],
    },
    {
        "route": "Baddy RigidBody",
        "weight": 9,
        "keywords": ["baddy", "stalk", "rigidbody", "soft body", "말랑", "줄기", "물렁", "리짓바디"],
    },
    {
        "route": "Baddy RigidBody",
        "weight": 4,
        "keywords": ["jiggle", "tail", "흔들", "꼬리"],
    },
    {
        "route": "Bot Trail sample",
        "weight": 9,
        "keywords": ["antenna", "wobble", "lag", "trail", "follow-through", "안테나", "뒤로", "끌리", "따라"],
    },
    {
        "route": "Bot Trail sample",
        "weight": 4,
        "keywords": ["흔들", "덜렁", "출렁"],
    },
    {
        "route": "Post Process ModifyBone",
        "weight": 8,
        "keywords": [
            "head",
            "neck",
            "look",
            "tilt",
            "turn",
            "after animation",
            "머리",
            "고개",
            "목",
            "바라",
            "돌려",
            "머리 기울",
            "고개 기울",
        ],
    },
    {
        "route": "BlendSpace sample variant",
        "weight": 8,
        "keywords": ["lean", "speed", "blendspace", "기울", "속도", "블렌드스페이스"],
    },
    {
        "route": "BlendSpace sample variant",
        "weight": 3,
        "keywords": ["walk", "run", "걷", "달리"],
    },
    {
        "route": "state-machine runtime-driver proof",
        "weight": 9,
        "keywords": ["idle", "jump", "hover", "transition", "state", "landing", "착지", "점프", "호버", "전환", "상태"],
    },
    {
        "route": "state-machine runtime-driver proof",
        "weight": 3,
        "keywords": ["walk", "run", "걷", "달리"],
    },
]


def _configure_output_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _extract_request(args: argparse.Namespace) -> str:
    if args.request:
        return str(args.request).strip()
    if args.request_parts:
        return " ".join(str(part) for part in args.request_parts).strip()
    return ""


def _score_request(normalized: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    route_scores: dict[str, dict[str, Any]] = {}
    matches: list[dict[str, Any]] = []

    def add_score(route: str, score: int, signal: str) -> None:
        route_score = route_scores.setdefault(
            route,
            {
                "route": route,
                "score": 0,
                "priority": ROUTES[route]["priority"],
                "matched_signals": [],
            },
        )
        route_score["score"] += score
        route_score["matched_signals"].append(signal)
        matches.append({"route": route, "keyword": signal, "weight": score})

    for rule in SIGNAL_RULES:
        route = str(rule["route"])
        for keyword in rule["keywords"]:
            if str(keyword).lower() in normalized:
                add_score(route, int(rule["weight"]), str(keyword))

    if any(token in normalized for token in ["머리", "고개", "head"]) and any(
        token in normalized for token in ["기울", "tilt"]
    ):
        add_score("Post Process ModifyBone", 6, "compound:head_tilt")

    if any(token in normalized for token in ["달리", "run", "walk", "걷"]) and any(
        token in normalized for token in ["기울", "lean"]
    ):
        add_score("BlendSpace sample variant", 6, "compound:locomotion_lean")

    ranked = sorted(
        route_scores.values(),
        key=lambda item: (int(item["score"]), int(item["priority"])),
        reverse=True,
    )
    return ranked, matches


def _extract_requested_values(request: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    degree_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:도|deg|degree|degrees)", request, flags=re.IGNORECASE)
    if degree_match:
        values["angle_degrees"] = float(degree_match.group(1))

    direction_signals = {
        "right": ["right", "오른", "우측"],
        "left": ["left", "왼", "좌측"],
        "up": ["up", "위"],
        "down": ["down", "아래"],
    }
    normalized = _normalize(request)
    for direction, keywords in direction_signals.items():
        if any(keyword in normalized for keyword in keywords):
            values["direction"] = direction
            break
    return values


def _build_compiled_intent(route: str, request: str) -> dict[str, Any]:
    route_data = ROUTES[route]
    compiled = {
        "target_character": route_data["target_character"],
        "target_body_area": route_data["target_body_area"],
        "timing_type": route_data["timing_type"],
        "runtime_layer": route_data["runtime_layer"],
        "route": route,
        "sample_target": route_data["sample_target"],
        "first_read_or_authoring_command": route_data["first_read_or_authoring_command"],
        "verification_command": route_data["verification_command"],
        "expected_evidence": route_data["expected_evidence"],
        "handoff_template": route_data["handoff_template"],
        "cxx_api_status": route_data["cxx_api_status"],
        "ask_user_first": route_data["ask_user_first"],
        "route_matrix_checked": True,
        "route_token_document_map_checked": True,
        "route_token_acceptance_map_checked": True,
        "sample_only_default": True,
        "allow_non_sample": False,
        "original_assets_modified": False,
        "evidence_root": EVIDENCE_ROOT,
        "assumptions": [
            route_data["assumption"],
            "Keep original StackOBot assets read-only for the first pass.",
        ],
    }

    requested_values = _extract_requested_values(request)
    if requested_values:
        compiled["requested_values"] = requested_values
    return compiled


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    request = _extract_request(args)
    normalized = _normalize(request)
    ranked, matches = _score_request(normalized)

    if not request:
        compiled_intent: dict[str, Any] = {
            "ask_user_first": True,
            "assumptions": ["No request text was supplied."],
        }
        return {
            "schema": SCHEMA,
            "elapsed_seconds": round(time.monotonic() - started_at, 4),
            "project_root": PROJECT_ROOT.as_posix(),
            "pass": False,
            "request": request,
            "route": "",
            "confidence": "none",
            "matched_signals": [],
            "ranked_routes": [],
            "compiled_intent": compiled_intent,
            "errors": ["empty_request"],
            "warnings": [],
        }

    if not ranked:
        compiled_intent = {
            "target_character": "Bot",
            "route": "unclassified",
            "ask_user_first": True,
            "sample_only_default": True,
            "allow_non_sample": False,
            "original_assets_modified": False,
            "assumptions": [
                "No documented StackOBot animation route signal matched the request.",
                "Ask for the body area, timing type, or runtime layer before editor work.",
            ],
        }
        report = {
            "schema": SCHEMA,
            "elapsed_seconds": round(time.monotonic() - started_at, 4),
            "project_root": PROJECT_ROOT.as_posix(),
            "pass": False,
            "request": request,
            "route": "unclassified",
            "confidence": "none",
            "matched_signals": [],
            "ranked_routes": [],
            "compiled_intent": compiled_intent,
            "errors": ["unclassified_request"],
            "warnings": ["No route token matched. Do not touch assets before clarifying."],
        }
    else:
        best = ranked[0]
        second_score = int(ranked[1]["score"]) if len(ranked) > 1 else 0
        confidence = "high" if int(best["score"]) >= second_score + 4 else "medium"
        warnings = []
        if confidence == "medium" and len(ranked) > 1:
            warnings.append(
                f"Close route scores: {best['route']}={best['score']}, {ranked[1]['route']}={ranked[1]['score']}"
            )
        report = {
            "schema": SCHEMA,
            "elapsed_seconds": round(time.monotonic() - started_at, 4),
            "project_root": PROJECT_ROOT.as_posix(),
            "pass": True,
            "request": request,
            "route": best["route"],
            "confidence": confidence,
            "matched_signals": matches,
            "ranked_routes": ranked,
            "compiled_intent": _build_compiled_intent(str(best["route"]), request),
            "errors": [],
            "warnings": warnings,
        }

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = REPORT_PATH.relative_to(PROJECT_ROOT).as_posix()
    return report


def _format_summary(report: dict[str, Any]) -> str:
    status = "PASS" if report["pass"] else "FAIL"
    compiled = report.get("compiled_intent", {})
    lines = [
        f"StackOBot request compiler: {status}",
        (
            f"schema={report['schema']} route={report.get('route') or 'none'} "
            f"confidence={report.get('confidence', 'none')} "
            f"ask_user_first={str(compiled.get('ask_user_first', True)).lower()}"
        ),
    ]
    if compiled.get("first_read_or_authoring_command"):
        lines.append(f"first={compiled['first_read_or_authoring_command']}")
    if compiled.get("verification_command"):
        lines.append(f"verify={compiled['verification_command']}")
    if compiled.get("cxx_api_status"):
        lines.append(f"cxx_api_status={compiled['cxx_api_status']}")
    if compiled.get("sample_target"):
        lines.append(f"sample_target={compiled['sample_target']}")
    if report.get("report_path"):
        lines.append(f"report={report['report_path']}")
    if report.get("warnings"):
        lines.append("warnings:")
        lines.extend(f"  - {warning}" for warning in report["warnings"])
    if report.get("errors"):
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in report["errors"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    _configure_output_encoding()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_parts", nargs="*", help="Request text when --request is not used.")
    parser.add_argument("--request", default="", help="Natural-language StackOBot animation request.")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write JSON report under Saved/MCP_DocAudit.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a concise pass/fail summary instead of full JSON.",
    )
    args = parser.parse_args(argv)

    report = run(args)
    if args.summary:
        print(_format_summary(report))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
