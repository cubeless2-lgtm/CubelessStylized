"""Audit StackOBot animation study documentation references and structure.

This local/read-only check validates that StackOBot study docs point to existing
relative docs, required study documents still exist, the doc index covers the
required document set, key template sections, request-run example fields, MCP
command quick-map entries, command syntax examples, command parameters,
doc-index route coverage, C++/API route decisions, handoff route mapping,
command route mapping, authoring route templates, request-run route and acceptance-focus coverage, and command/sample-path guards are
present, concrete sample targets are registered in the sample manifest,
request-run routes map to the expected handoff templates and
first/verification commands, target character/body area, timing type, runtime layer,
C++/API status, expected evidence, sample target scope, plus route-specific
acceptance route tokens, acceptance focus and approval boundaries, request compiler route coverage, and acceptance
universal/route/evidence/reporting fields plus escalation triggers are
preserved. It also confirms the sibling/sample workspace paths used by the
workflow still exist on this machine.
It does not call Unreal, does not touch assets, and does not require the editor
bridge to be online.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_DocAudit" / "StackOBotAnimationDocsLinkAudit.json"
SAMPLE_ANIM_STUDY_ROOT = "/Game/_MCP_Sample/AnimStudy"

RELATIVE_DOC_RE = re.compile(r"(?<![A-Za-z0-9_:/.-])docs/[A-Za-z0-9._/-]+\.md")
EXAMPLE_SECTION_RE = re.compile(r"^## Example (?P<number>\d+): (?P<title>.+)$", re.MULTILINE)
TEXT_FENCE_RE = re.compile(r"```text\n(?P<body>.*?)\n```", re.DOTALL)
JSON_FENCE_RE = re.compile(r"```json\n(?P<body>.*?)\n```", re.DOTALL)
EXAMPLE_FIELD_RE = re.compile(r"^(?P<name>[a-z_]+):\s*(?P<value>.*)$")
SAMPLE_ASSET_PATH_RE = re.compile(r"/Game/_MCP_Sample/AnimStudy/[A-Za-z0-9_]+")
STACKOBOT_DOC_GLOB = "stackobot*.md"
DOCS_AUDIT_SCHEMA = "stackobot_animation_docs_link_audit_v92"

LOCAL_CHECK_RUNNER_SCHEMA_TOKENS = {
    "local_check_schema": '"schema": "stackobot_animation_local_checks_v13"',
    "expected_docs_audit_schema": f'EXPECTED_DOCS_AUDIT_SCHEMA = "{DOCS_AUDIT_SCHEMA}"',
    "expected_preflight_schema": 'EXPECTED_PREFLIGHT_SCHEMA = "stackobot_animation_preflight_v1"',
    "expected_staging_scope_schema": 'EXPECTED_STAGING_SCOPE_SCHEMA = "stackobot_animation_staging_scope_v1"',
    "checker_docs_compile_target": '"Tools/Unreal/check_stackobot_animation_docs.py"',
    "checker_preflight_compile_target": '"Tools/Unreal/check_stackobot_animation_preflight.py"',
    "checker_staging_scope_compile_target": '"Tools/Unreal/check_stackobot_animation_staging_scope.py"',
    "checker_local_runner_compile_target": '"Tools/Unreal/run_stackobot_animation_local_checks.py"',
}

DOC_INDEX_LOCAL_CHECK_COMMANDS = [
    "python Tools/Unreal/run_stackobot_animation_local_checks.py --summary",
    "python Tools/Unreal/run_stackobot_animation_local_checks.py --summary --require-sibling-clean",
    "python Tools/Unreal/check_stackobot_animation_preflight.py --summary",
    "python Tools/Unreal/check_stackobot_animation_preflight.py --summary --require-bridge",
    "python Tools/Unreal/check_stackobot_animation_docs.py --summary",
    "python Tools/Unreal/check_stackobot_animation_staging_scope.py --summary",
    "python Tools/Unreal/check_stackobot_animation_docs.py --write-report",
]

QUICKSTART_PREFLIGHT_CHECKLIST_TOKENS = {
    "local_runner": "python Tools/Unreal/run_stackobot_animation_local_checks.py --summary",
    "stackobot_project_path": "D:/Git/SampleProject/StackOBot",
    "primary_bridge": "127.0.0.1:55557",
    "stackobot_plugin_path": "D:/Git/SampleProject/StackOBot/Plugins/UnrealMCP",
    "command_surface_sync": "command-surface sync issue",
    "dirty_package_capture": "Pre-existing dirty packages are captured",
    "sample_root": "/Game/_MCP_Sample/AnimStudy",
    "sample_only_flag": "allow_non_sample=false",
    "sample_manifest": "docs/stackobot-sample-asset-manifest.md",
    "evidence_root": "D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy",
    "bridge_required_flag": "--require-bridge",
}

CLOSEOUT_NEXT_REQUEST_PROTOCOL_TOKENS = {
    "request_compiler": "classify the request with the compiler",
    "sample_only_route": "choose the narrowest sample-only route",
    "visible_tivret_handoff": "show the visible Tivret handoff block before asset work",
    "sample_asset_boundary": "_MCP_Sample/AnimStudy",
    "runtime_evidence": "verify with route-specific runtime evidence",
    "created_paths": "report created paths",
    "original_mutation_status": "original mutation status",
    "proof_result": "proof result",
    "artifacts": "artifacts",
    "dirty_packages": "dirty packages",
    "cxx_api_decision": "C++/API decision",
    "no_user_sample_needed": "without asking the user for a sample first",
}

CLOSEOUT_CXX_API_TIMING_TOKENS = {
    "no_new_cxx_now": "no new C++ is needed before the next concrete request",
    "decision_matrix": "docs/stackobot-cpp-api-decision-matrix.md",
    "state_transition_trigger": "new state or transition authoring",
    "visible_upper_body_source": "visible upper-body action source",
    "bot_rigidbody_physics": "new Bot RigidBody-style physics",
    "protected_animation_metadata": "notifies, curves, sync markers, or Montage internals",
    "posewatch_failure": "repeated PoseWatch failures",
    "ordinary_request_block": "Do not add C++ for ordinary",
    "ordinary_turn_head": "turn head",
    "ordinary_lean_more": "lean more",
    "ordinary_antenna_lag": "antenna lag",
    "ordinary_make_stronger": "stronger",
    "ordinary_node_question": "which node changed the pose",
}

ACCEPTANCE_COMPLETION_EVIDENCE_TOKENS = {
    "asset_exists_not_enough": "Do not mark the task complete when the only evidence is that an asset exists.",
    "route_specific_runtime_proof": "route-specific runtime proof",
    "read_only_statement": "request was read-only",
}

ACCEPTANCE_EVIDENCE_STRENGTH_DETAIL_TOKENS = {
    "strongest_feasible": "Use the strongest feasible level for the request",
    "sample_compile_not_final": "Authoring smoke only; not enough for final visual behavior.",
    "runtime_smoke_scope": "State-machine and BlendSpace behavior checks",
    "same_instance_definition": "Input and output of the target node are captured on the same AnimInstance.",
    "same_instance_final_proof": "Final proof for ModifyBone, Trail, RigidBody, ControlRig, LayeredBoneBlend, and node contribution requests.",
}

QUICKSTART_START_HERE_TOKENS = {
    "bridge_endpoint": "127.0.0.1:55557",
    "request_compiler": "docs/stackobot-request-compiler-drills.md",
    "route_matrix": "docs/stackobot-animation-route-matrix.md",
    "request_run_template": "docs/stackobot-animation-request-run-template.md",
    "tivret_handoff_template": "docs/stackobot-animation-tivret-handoff-templates.md",
    "sample_root": "/Game/_MCP_Sample/AnimStudy",
    "command_syntax": "docs/stackobot-animation-mcp-command-syntax.md",
    "authoring_templates": "docs/stackobot-animation-authoring-templates.md",
    "work_log": "docs/work-log.md",
    "local_runner": "python Tools/Unreal/run_stackobot_animation_local_checks.py --summary",
    "commit_scope": "commit only relevant docs/tooling",
}

EXPECTED_EXTERNAL_PATHS = [
    PROJECT_ROOT.parent / "unreal-mcp-cubeless" / "Python" / "tools" / "node_tools.py",
    PROJECT_ROOT.parent / "unreal-mcp-cubeless" / "Docs" / "Tools" / "node_tools.md",
    PROJECT_ROOT.parent / "SampleProject" / "StackOBot" / "Plugins" / "UnrealMCP",
]

REQUIRED_DOC_PATHS = [
    "docs/stackobot-animation-doc-index.md",
    "docs/stackobot-animation-quickstart.md",
    "docs/stackobot-animation-study-closeout.md",
    "docs/stackobot-animation-next-work-backlog.md",
    "docs/stackobot-animation-acceptance-checklist.md",
    "docs/stackobot-request-compiler-drills.md",
    "docs/stackobot-animation-request-playbook.md",
    "docs/stackobot-animation-request-run-template.md",
    "docs/stackobot-animation-request-run-examples.md",
    "docs/stackobot-animation-route-matrix.md",
    "docs/stackobot-animation-tivret-handoff-templates.md",
    "docs/stackobot-animation-authoring-templates.md",
    "docs/stackobot-animation-mcp-command-syntax.md",
    "docs/stackobot-cpp-api-decision-matrix.md",
    "docs/stackobot-animation-execution-map.md",
    "docs/stackobot-animbp-inventory.md",
    "docs/stackobot-animbp-authoring-patterns.md",
    "docs/stackobot-animation-study.md",
    "docs/stackobot-sample-asset-manifest.md",
    "docs/stackobot-live-read-drill-2026-06-19.md",
    "docs/stackobot-physics-request-grammar.md",
]

REQUIRED_SECTIONS = {
    "docs/stackobot-animation-doc-index.md": [
        "## Start Here",
        "## Request Execution Pages",
        "## Route Coverage",
        "## Route Token Document Map",
        "## Route Deep Dives",
        "## Default Workflow",
        "## Local Checks",
        "## Safe Defaults",
    ],
    "docs/stackobot-animation-quickstart.md": [
        "## Start Here",
        "## Preflight Checklist",
        "## Route Shortcuts",
        "## Route Token Quick Map",
        "## Do Not Do First",
        "## Main References",
    ],
    "docs/stackobot-animation-study-closeout.md": [
        "## Objective Covered",
        "## First Page Order",
        "## Ready Routes",
        "## Ready Route Token Map",
        "## Current Evidence Baseline",
        "## C++ / API Timing",
        "## Residual Risks",
        "## Next Request Protocol",
    ],
    "docs/stackobot-animation-next-work-backlog.md": [
        "## Current Default",
        "## Route Token Backlog Map",
        "## P0: Before Any New Asset Work",
        "## P1: Most Likely Future Work",
        "## P2: Reusable Tooling Only If Repeated",
        "## P3: Maintenance",
        "## Do Not Spend Time On Yet",
        "## Practical Next Step When The User Wakes Up",
    ],
    "docs/stackobot-request-compiler-drills.md": [
        "## Compiler Output",
        "## Signal Words",
        "## Route Token Compiler Map",
        "## Drill Table",
        "## Filled Handoff Example",
        "## Ambiguity Rules",
        "## C++/API Decision Quick Check",
    ],
    "docs/stackobot-animation-request-playbook.md": [
        "## Default Rule",
        "## Intake",
        "## Classification Matrix",
        "## Route Token Playbook Map",
        "## Execution Protocol",
        "## Tivret Instruction Templates",
        "## Dry-Run Request Scenarios",
        "## Known Safe Routes",
        "## Approval Gates",
        "## C++/API Escalation",
        "## Failure Handling",
        "## Route Token Failure Map",
        "## Delivery Shape",
    ],
    "docs/stackobot-animation-request-run-template.md": [
        "## Request",
        "## Compiled Intent",
        "## Assumptions",
        "## Safety Scope",
        "## Preflight Checklist",
        "## Tivret Handoff",
        "## Execution Log",
        "## Acceptance Checklist",
        "## Final Report Draft",
        "## Work-Log Entry Draft",
    ],
    "docs/stackobot-animation-request-run-examples.md": [
        "## Example 1: Bot Head Yaw",
        "## Example 2: Wider Run Lean",
        "## Example 3: Antenna Lag",
        "## Example 4: Upper Body While Moving",
        "## Example 5: Notify Or Montage Timing",
        "## Example 6: ControlRig Foot Interaction",
        "## Example 7: Hover Transition Timing",
        "## Example 8: Baddy Soft Stalk",
        "## Example 9: Node Contribution Proof",
    ],
    "docs/stackobot-animation-route-matrix.md": [
        "## Route Classification",
        "## Execution Matrix",
        "## Evidence And Approval Matrix",
        "## Selection Rules",
        "## Stop Conditions",
    ],
    "docs/stackobot-animation-acceptance-checklist.md": [
        "## Universal Pass Gate",
        "## Route Token Acceptance Map",
        "## Route-Specific Pass Criteria",
        "## Evidence Strength Levels",
        "## When To Stop And Escalate",
        "## Final User Report Checklist",
    ],
    "docs/stackobot-animation-tivret-handoff-templates.md": [
        "## Route Token To Handoff",
        "## Post Process ModifyBone",
        "## BlendSpace Sample Variant",
        "## State Machine Or Runtime Driver",
        "## ControlRig Late Correction",
        "## UpperBody Slot And LayeredBlend",
        "## Trail Or Secondary Motion",
        "## Notify, Curve, Sync Marker, Or Montage Internals",
        "## Route Token Final Report Map",
        "## Final Report Shape",
    ],
    "docs/stackobot-animation-authoring-templates.md": [
        "## Routing Table",
        "## Route Token Template Map",
        "## Template Cards",
        "### Post Process ModifyBone",
        "### BlendSpace Sample Variant",
        "### State Machine Or Runtime Driver",
        "### ControlRig Late Correction",
        "### UpperBody Slot And LayeredBlend",
        "### Secondary Motion Or Physics",
        "### Node Contribution Proof",
        "### Notify, Curve, Sync Marker, And Montage Internals",
        "## Completion Contract",
        "## C++/API Escalation Gate",
    ],
    "docs/stackobot-animation-mcp-command-syntax.md": [
        "## Command Quick Map",
        "## Route Token Command Map",
        "## Common StackOBot Asset Paths",
        "## Authoring Syntax",
        "### Post Process ModifyBone sample",
        "### BlendSpace sample variant",
        "### ControlRig forced-driver sample",
        "### State-machine runtime response",
        "### Trail or secondary motion sample",
        "### RigidBody settings and sample tuning",
        "## Result Checklist",
    ],
    "docs/stackobot-animation-execution-map.md": [
        "## Route Token Evidence Map",
        "## Runtime Pose Flow",
        "## System Roles",
        "## Main AnimBP Chains",
        "## Playback Asset Data",
        "## Post Process Variant Samples",
        "## Baddy RigidBody Source vs Runtime Split",
        "## Bot BlendSpace Source Pose Map",
        "## Bot BlendSpace SIE Pose Grid",
        "## Transition Inventory Status",
        "## Runtime State Probe Status",
        "## Control Rig Gate Summary",
        "## Trail Controller Status",
        "## Physics Pre/Post Evidence Synthesis",
        "## Deferred API Work",
    ],
    "docs/stackobot-animbp-inventory.md": [
        "## ABP_Bot",
        "## ABP_Baddy",
        "## Transition Graph Inventory",
        "## Runtime State Probe",
        "## Post Process AnimBP Variant Samples",
        "## Animation Asset Read Limits",
        "## Baddy RigidBody Source vs Runtime Split",
        "## Bot BlendSpace Source Pose Map",
        "## Bot BlendSpace SIE Pose Grid",
        "## Control Rig Contribution Synthesis",
        "## Bot Active Trail Sample",
        "## Physics Pre/Post Evidence Synthesis",
        "## Read Limitations",
    ],
    "docs/stackobot-animbp-authoring-patterns.md": [
        "## Runtime Grammar",
        "## Request Classification",
        "## Route Token Pattern Map",
        "## Authoring Patterns",
        "### 1. State Machine Pattern",
        "### 2. BlendSpace Pattern",
        "### 3. Slot And Layered Blend Pattern",
        "### 4. Control Rig Pattern",
        "### 5. Post Process AnimBP Pattern",
        "### 6. Physics And Secondary Motion Pattern",
        "## MCP Command Map",
        "## C++ And API Escalation Rules",
        "## Verification Gate",
        "## Safety Notes",
    ],
    "docs/stackobot-animation-study.md": [
        "## Post Process Variant Samples",
        "## ABP_Baddy RigidBody",
        "## Baddy RigidBody Study Samples",
        "## ABP_Bot Trail Controller",
        "## Current Next Candidate",
        "## ABP_Bot Runtime Driver Matrix",
        "## Remaining Study Backlog",
        "## Bot Slot and Layered Blend Inventory",
        "## Deferred UnrealMCP C++ API Candidates",
        "## Trail No-C++ Active Sample Feasibility",
        "## Learning Map",
        "## AnimBP State Machine Inventory",
        "## AnimBP Transition Graph Inventory",
        "## AnimInstance Runtime State Probe",
        "## Animation Asset Playback Inventory",
        "## Baddy RigidBody Source vs Runtime Comparison",
        "## Bot BlendSpace Source Pose Map",
        "## Bot BlendSpace SIE Pose Grid",
        "## Control Rig Contribution Synthesis",
        "## ABP_Bot Active Trail Sample",
        "## Physics Pre/Post Evidence Synthesis",
        "## Post Process Runtime and Static Pose Comparison",
    ],
    "docs/stackobot-live-read-drill-2026-06-19.md": [
        "## Live Read Results",
        "## Interpretation",
        "## Caveats",
    ],
    "docs/stackobot-cpp-api-decision-matrix.md": [
        "## Current Rule",
        "## Covered, Do Not Rebuild",
        "## Route Token Decision Map",
        "## Current Candidate Shortlist",
        "## Candidate Matrix",
        "## Immediate Implementation Triggers",
        "## Verification For Any New C++ API",
        "## Timing Decision",
    ],
    "docs/stackobot-physics-request-grammar.md": [
        "## Route Matrix",
        "## Physics Route Token Map",
        "## Decision Rules",
        "## Known Evidence",
        "## Safe Command Patterns",
        "## C++/API Parking Lot",
        "## Final Response Checklist",
    ],
    "docs/stackobot-sample-asset-manifest.md": [
        "## Asset Groups",
        "## Package Manifest",
        "## Regeneration Routes",
        "## Route Token Sample Target Map",
        "## Evidence Root",
        "## Safety Notes",
    ],
}

REQUIRED_TOKENS = {
    "docs/stackobot-animation-quickstart.md": [
        "run_stackobot_animation_local_checks.py --summary",
        "--require-bridge",
        "docs/stackobot-animation-route-matrix.md",
        "D:/Git/SampleProject/StackOBot",
        "127.0.0.1:55557",
        "D:/Git/SampleProject/StackOBot/Plugins/UnrealMCP",
        "/Game/_MCP_Sample/AnimStudy",
        "allow_non_sample=false",
        "Concrete `_MCP_Sample/AnimStudy` sample targets named in route matrix or",
        "command-surface sync issue",
        "티브렛에게 전달할 지시",
        "Do not edit original StackOBot assets",
        "Do not add C++ unless",
    ],
    "docs/stackobot-animation-doc-index.md": [
        "Original StackOBot assets stay read-only",
        "Sample assets go under `/Game/_MCP_Sample/AnimStudy`",
        "run_stackobot_animation_local_checks.py --summary",
        "run_stackobot_animation_local_checks.py --summary --require-sibling-clean",
        "check_stackobot_animation_preflight.py --summary",
        "check_stackobot_animation_preflight.py --summary --require-bridge",
        "check_stackobot_animation_staging_scope.py --summary",
        "Do not broad-probe Montage internals",
        "Do not add new C++",
    ],
    "docs/stackobot-animation-study-closeout.md": [
        "ready for sample-first implementation requests",
        "original StackOBot assets unless the user explicitly approves",
        "docs/stackobot-request-compiler-drills.md",
        "docs/stackobot-animation-authoring-templates.md",
        "docs/stackobot-animation-tivret-handoff-templates.md",
        "docs/stackobot-cpp-api-decision-matrix.md",
        "/Game/_MCP_Sample/AnimStudy",
        "D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy",
        "no new C++ is needed before the next concrete request",
        "AnimMontage.h:770",
        "D:/Git/SampleProject/StackOBot/Plugins/UnrealMCP",
    ],
    "docs/stackobot-animation-next-work-backlog.md": [
        "The next real animation request should start sample-only.",
        "No immediate C++ work is scheduled.",
        "127.0.0.1:55557",
        "D:/Git/SampleProject/StackOBot/Plugins/UnrealMCP",
        "/Game/_MCP_Sample/AnimStudy",
        "ensure_layered_slot_overlay_sample",
        "ensure_state_machine_sample_variant",
        "ensure_anim_graph_rigidbody_demo_variant",
        "Do not add new C++ without a concrete blocked request.",
        "Do not mutate original StackOBot assets during study work.",
        "Compile the sentence in `docs/stackobot-request-compiler-drills.md`.",
    ],
    "docs/stackobot-request-compiler-drills.md": [
        "classify first",
        "execute only the sample-safe route unless original asset mutation was",
        "first_read_or_authoring_command",
        "verification_command",
        "cxx_api_status",
        "ask_user_first",
        "ensure_postprocess_anim_demo_variant",
        "ensure_anim_graph_trail_demo",
        "ensure_blendspace_sample_variant",
        "controlrig_direct_gate_probe",
        "inspect_anim_graph_node_settings",
        "sample_anim_node_pre_post_runtime_pose",
        "do not broad-probe Montage",
        "Use `candidate, not now`",
    ],
    "docs/stackobot-animation-request-playbook.md": [
        "Start sample-only unless",
        "티브렛에게 전달할 지시",
        "allow_non_sample=false",
        "C++/API Escalation",
        "Do not broad-probe Montage",
        "/Game/_MCP_Sample/AnimStudy",
        "D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy",
        "Do not edit original StackOBot assets",
        "Update Cubeless docs/work-log, then commit only relevant docs or tooling files.",
        "Generic `execute_python` would need unsafe map switching",
        "resolve_anim_posewatch_target_actor",
    ],
    "docs/stackobot-animation-tivret-handoff-templates.md": [
        "티브렛에게 전달할 지시",
        "원본",
        "/Game/_MCP_Sample/AnimStudy",
        "완료 조건",
        "ensure_postprocess_anim_demo_variant",
        "ensure_blendspace_sample_variant",
        "inspect_anim_state_machine_transitions",
        "controlrig_direct_gate_probe",
        "ensure_controlrig_forced_driver_animbp",
        "sample_anim_node_pre_post_runtime_pose",
        "ensure_anim_graph_trail_demo",
        "AnimMontage.h:770",
        "route:",
        "dirty_packages:",
        "cxx_api_needed:",
    ],
    "docs/stackobot-animation-authoring-templates.md": [
        "sample-only under `/Game/_MCP_Sample/AnimStudy`",
        "show the matching handoff block",
        "ensure_postprocess_anim_demo_variant",
        "sample_blendspace_runtime_pose_grid",
        "sample_anim_state_machine_runtime_response",
        "controlrig_direct_gate_probe",
        "sample_anim_node_pre_post_runtime_pose",
        "ensure_anim_graph_trail_demo",
        "Do not reactivate the disconnected original Bot Trail node directly.",
        "AnimMontage.h:770",
        "Do not add C++ just because a request is complex.",
    ],
    "docs/stackobot-animation-mcp-command-syntax.md": [
        "D:/Git/unreal-mcp-cubeless/Python/tools/node_tools.py",
        "D:/Git/unreal-mcp-cubeless/Docs/Tools/node_tools.md",
        "Start under `/Game/_MCP_Sample/AnimStudy` unless original asset mutation was explicitly approved.",
        "Keep `allow_non_sample=false` for authoring commands.",
        "D:/Git/SampleProject/StackOBot/Plugins/UnrealMCP",
        "Commands here do not open maps. Do not use generic Python map switching as setup.",
        "/Game/StackOBot/Characters/Bot/ABP_Bot.ABP_Bot",
        "/Game/StackOBot/Characters/Bot/Mesh/SKM_Bot.SKM_Bot",
        "/Game/_MCP_Sample/AnimStudy",
        "D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy",
        "original_assets_modified=false",
        "sampled_world_type",
        "Dirty package status after transient actor work.",
    ],
    "docs/stackobot-animation-execution-map.md": [
        "The original `SKM_Bot` has no Post Process AnimBP assigned.",
        "The original Trail Controller node in `ABP_Bot` is disconnected",
        "LocomotionPose -> UpperBody Slot -> CashedPose_UpperBody -> LayeredBoneBlend.BlendPoses_0",
        "AnimMontage.h:770",
        "/Game/_MCP_Sample/AnimStudy",
        "sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture",
        "ensure_blendspace_sample_variant",
        "ensure_anim_graph_trail_demo",
        "original asset mutation by default",
        "Remaining C++/UnrealMCP candidates if reusable tooling is explicitly resumed",
    ],
    "docs/stackobot-animbp-inventory.md": [
        "ABP_Bot",
        "ABP_Baddy",
        "LayeredBoneBlend",
        "RigidBody runs in component space by default with `Alpha=1`.",
        "Original `SKM_Bot` still has no Post Process AnimBP assignment.",
        "Do not inspect `AnimMontage` internals with broad Unreal Python reflection",
        "D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy",
        "/Game/_MCP_Sample/AnimStudy/ABP_Bot_Trail_Study",
        "same_instance_prepost=true",
        "Use the C++ MCP topology commands for static graph reads instead of protected Python reflection.",
    ],
    "docs/stackobot-animbp-authoring-patterns.md": [
        "Default safe authoring target: `/Game/_MCP_Sample/AnimStudy`.",
        "ensure_blendspace_sample_variant",
        "sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture",
        "ensure_postprocess_anim_demo_variant",
        "ensure_anim_graph_trail_demo",
        "Non-UnrealMCP project C++ still requires explicit user approval before editing.",
        "Asset-only requests should stay in Blueprint, AnimBP, ControlRig, Post Process AnimBP, or MCP/editor scripting unless code is explicitly requested.",
        "Keep `_MCP_Sample` learning assets disposable and gitignored unless the user explicitly asks to version a specific sample asset.",
    ],
    "docs/stackobot-animation-study.md": [
        "D:/Git/SampleProject/StackOBot",
        "/Game/_MCP_Sample/AnimStudy/",
        "Original StackOBot assets were not edited.",
        "original_assets_modified=false",
        "do not wire this original node directly.",
        "set_anim_graph_rigidbody_settings",
        "ensure_anim_graph_trail_demo",
        "inspect_anim_state_machine_transitions",
        "sample_anim_node_pre_post_runtime_pose(mode=pose_watch_capture",
        "the only loaded AnimMontage asset found by class scan is Baddy death",
        "Deferred UnrealMCP C++ API Candidates",
        "Remaining expansion is only for unusual node classes outside the smoked coverage.",
        "explicit component Post Process override",
        "same_instance_prepost=true",
    ],
    "docs/stackobot-live-read-drill-2026-06-19.md": [
        "Primary bridge: `127.0.0.1:55557`",
        "Post Process ModifyBone",
        "Trail secondary motion",
        "RigidBody physics",
        "ControlRig late correction",
        "LayeredBoneBlend",
        "Advanced PoseWatch, BlendSpace grid, and ControlRig forced-driver commands were",
    ],
    "docs/stackobot-animation-request-run-template.md": [
        "Original StackOBot assets modified?",
        "Original maps saved?",
        "Sample root",
        "Primary bridge `127.0.0.1:55557` reachable",
        "Required command exposed by current plugin copy",
        "Pre-existing dirty packages captured",
        "`allow_non_sample=false` for authoring commands",
        "C++/API decision recorded",
    ],
    "docs/stackobot-animation-acceptance-checklist.md": [
        "Do not mark the task complete when the only evidence is that an asset exists.",
        "Same-instance pre/post",
        "Stop before final delivery and mark C++/API as `candidate`",
    ],
    "docs/stackobot-cpp-api-decision-matrix.md": [
        "Current timing: do not implement more C++ yet.",
        "Covered, Do Not Rebuild",
        "Immediate Implementation Triggers",
        "sample-root guard",
    ],
    "docs/stackobot-physics-request-grammar.md": [
        "original StackOBot assets stay read-only",
        "/Game/_MCP_Sample/AnimStudy",
        "ensure_anim_graph_trail_demo",
        "set_anim_graph_rigidbody_settings",
        "allow_non_sample",
        "ensure_anim_graph_rigidbody_demo_variant",
        "inspect_physics_asset_constraints_guarded",
        "Final Response Checklist",
    ],
    "docs/stackobot-sample-asset-manifest.md": [
        "D:/Git/SampleProject/StackOBot/Content/_MCP_Sample/AnimStudy",
        "The StackOBot sample project is not a git repository.",
        "Do not stage them in `CubelessStylized`",
        "/Game/_MCP_Sample/AnimStudy/ABP_Bot_PostProcess_Study",
        "/Game/_MCP_Sample/AnimStudy/ABP_Bot_Trail_Study",
        "/Game/_MCP_Sample/AnimStudy/ABP_Bot_ControlRig_ForcedDriver_Study",
        "/Game/_MCP_Sample/AnimStudy/ABP_Baddy_RigidBody_Study",
        "/Game/_MCP_Sample/AnimStudy/BS_Bot_WalkRunLean_LeanTemplateRehearsal",
        "D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy",
        "names a concrete",
        "this manifest and the matching `docs/work-log.md` entry",
        "command-surface sync issue",
    ],
    "docs/stackobot-animation-request-run-examples.md": [
        "They are not execution",
        "do not reactivate the disconnected original `ABP_Bot` Trail node",
        "do not broad-probe Montage internals",
        "AnimMontage.h:770",
        "controlrig_direct_gate_probe",
        "sample_anim_state_machine_runtime_response",
        "Baddy RigidBody",
        "same-instance confirmation",
    ],
    "docs/stackobot-animation-route-matrix.md": [
        "Post Process ModifyBone",
        "BlendSpace sample variant",
        "Bot Trail sample",
        "UpperBody Slot and LayeredBlend",
        "protected metadata boundary",
        "ControlRig gate probe",
        "state-machine runtime-driver proof",
        "Baddy RigidBody",
        "node resolver plus same-instance pre/post proof",
        "/Game/_MCP_Sample/AnimStudy",
        "sample_anim_node_pre_post_runtime_pose",
        "candidate only if",
        "If the route requires original asset mutation, stop and ask",
        "protected metadata or Montage internals",
        "same-instance or route-specific proof",
        "new non-exception C++ API",
    ],
}

REQUEST_EXAMPLE_REQUIRED_FIELDS = [
    "user_request",
    "target_character",
    "target_body_area",
    "timing_type",
    "runtime_layer",
    "route",
    "sample_target",
    "first_read_or_authoring_command",
    "verification_command",
    "expected_evidence",
    "handoff_template",
    "cxx_api_status",
    "ask_user_first",
    "route_matrix_checked",
    "route_token_document_map_checked",
    "route_token_acceptance_map_checked",
    "route_matrix_notes",
]

REQUEST_EXAMPLE_ALLOWED_HANDOFFS = {
    "Post Process ModifyBone",
    "BlendSpace Sample Variant",
    "Trail Or Secondary Motion",
    "UpperBody Slot And LayeredBlend",
    "Notify, Curve, Sync Marker, Or Montage Internals",
    "ControlRig Late Correction",
    "State Machine Or Runtime Driver",
}

REQUEST_EXAMPLE_FIRST_COMMAND_KEYWORDS = [
    "ensure_postprocess_anim_demo_variant",
    "ensure_blendspace_sample_variant",
    "ensure_anim_graph_trail_demo",
    "slot/cached-pose inventory",
    "safe animation asset inventory",
    "inspect_anim_graph_protected_topology",
    "inspect_anim_state_machine_transitions",
    "inspect_anim_graph_node_settings",
    "compiled mapping",
]

REQUEST_EXAMPLE_VERIFICATION_KEYWORDS = [
    "sample_anim_node_pre_post_runtime_pose",
    "sample_blendspace_runtime_pose_grid",
    "sample_anim_state_machine_runtime_response",
    "none for protected internals",
]

REQUEST_EXAMPLE_ROUTE_COVERAGE = {
    "post_process_modifybone": "Post Process ModifyBone",
    "blendspace_sample_variant": "BlendSpace sample variant",
    "trail_secondary_motion": "Bot Trail sample",
    "upperbody_layeredblend": "UpperBody Slot and LayeredBlend",
    "protected_metadata": "protected metadata boundary",
    "controlrig_late_correction": "ControlRig gate probe",
    "state_machine_runtime_driver": "state-machine runtime-driver proof",
    "rigidbody_physics": "Baddy RigidBody",
    "node_contribution_proof": "node resolver plus same-instance pre/post proof",
}

DOC_INDEX_ROUTE_TOKEN_DOCUMENTS = [
    "docs/stackobot-animation-quickstart.md",
    "docs/stackobot-request-compiler-drills.md",
    "docs/stackobot-animation-route-matrix.md",
    "docs/stackobot-animation-authoring-templates.md",
    "docs/stackobot-animation-tivret-handoff-templates.md",
    "docs/stackobot-animation-mcp-command-syntax.md",
    "docs/stackobot-animation-execution-map.md",
    "docs/stackobot-sample-asset-manifest.md",
]

REQUEST_COMPILER_ROUTE_COVERAGE_RULES = {
    "post_process_modifybone": {
        "signal_tokens": ["머리", "Post Process ModifyBone", "ensure_postprocess_anim_demo_variant"],
        "drill_tokens": ["Bot 머리를 오른쪽으로 5도", "Post Process ModifyBone", "no-SIE Post Process PoseWatch"],
    },
    "blendspace_sample_variant": {
        "signal_tokens": ["기울", "BlendSpace sample variant", "ensure_blendspace_sample_variant"],
        "drill_tokens": ["달릴 때 좌우 기울기", "BlendSpace sample variant", "sample_blendspace_runtime_pose_grid"],
    },
    "trail_secondary_motion": {
        "signal_tokens": ["안테나", "Trail or secondary motion", "ensure_anim_graph_trail_demo"],
        "drill_tokens": ["안테나가 달릴 때", "Trail secondary motion", "SIE Post Process PoseWatch"],
    },
    "upperbody_layeredblend": {
        "signal_tokens": ["상체", "UpperBody Slot/LayeredBlend", "all-input PoseWatch"],
        "drill_tokens": ["움직이면서 버튼", "UpperBody Slot/LayeredBlend", "New overlay/action source remains candidate"],
    },
    "protected_metadata": {
        "signal_tokens": ["notify", "Protected metadata", "Existing safe inventory only"],
        "drill_tokens": ["몽타주 notify", "Protected metadata", "Candidate guarded native API"],
    },
    "controlrig_late_correction": {
        "signal_tokens": ["발", "ControlRig late correction", "controlrig_direct_gate_probe"],
        "drill_tokens": ["상호작용 지점", "ControlRig late correction", "ControlRig same-instance PoseWatch"],
    },
    "state_machine_runtime_driver": {
        "signal_tokens": ["transition", "State machine/runtime driver", "inspect_anim_state_machine_transitions"],
        "drill_tokens": ["점프에서 착지", "State machine/runtime driver", "runtime state response cases"],
    },
    "rigidbody_physics": {
        "signal_tokens": ["말랑", "RigidBody physics", "inspect_anim_graph_node_settings"],
        "drill_tokens": ["Baddy 줄기", "RigidBody sample tuning", "SIE variant metrics or PoseWatch"],
    },
    "node_contribution_proof": {
        "signal_tokens": ["which node", "Instrumentation", "sample_anim_node_pre_post_runtime_pose"],
        "drill_tokens": ["어느 노드", "Instrumentation", "compiled mapping"],
    },
}

REQUEST_EXAMPLE_ROUTE_HANDOFF_RULES = {
    "Post Process ModifyBone": "Post Process ModifyBone",
    "BlendSpace sample variant": "BlendSpace Sample Variant",
    "Bot Trail sample": "Trail Or Secondary Motion",
    "UpperBody Slot and LayeredBlend": "UpperBody Slot And LayeredBlend",
    "protected metadata boundary": "Notify, Curve, Sync Marker, Or Montage Internals",
    "ControlRig gate probe": "ControlRig Late Correction",
    "state-machine runtime-driver proof": "State Machine Or Runtime Driver",
    "Baddy RigidBody": "Trail Or Secondary Motion",
    "node resolver plus same-instance pre/post proof": "no authoring handoff",
}

REQUEST_EXAMPLE_ROUTE_VERIFICATION_RULES = {
    "Post Process ModifyBone": ["sample_anim_node_pre_post_runtime_pose"],
    "BlendSpace sample variant": ["sample_blendspace_runtime_pose_grid"],
    "Bot Trail sample": ["sample_anim_node_pre_post_runtime_pose"],
    "UpperBody Slot and LayeredBlend": ["sample_anim_node_pre_post_runtime_pose"],
    "protected metadata boundary": ["none for protected internals"],
    "ControlRig gate probe": ["sample_anim_node_pre_post_runtime_pose"],
    "state-machine runtime-driver proof": ["sample_anim_state_machine_runtime_response"],
    "Baddy RigidBody": ["sample_anim_node_pre_post_runtime_pose"],
    "node resolver plus same-instance pre/post proof": ["sample_anim_node_pre_post_runtime_pose"],
}

REQUEST_EXAMPLE_ROUTE_FIRST_COMMAND_RULES = {
    "Post Process ModifyBone": ["ensure_postprocess_anim_demo_variant"],
    "BlendSpace sample variant": ["ensure_blendspace_sample_variant"],
    "Bot Trail sample": ["ensure_anim_graph_trail_demo"],
    "UpperBody Slot and LayeredBlend": ["slot/cached-pose inventory"],
    "protected metadata boundary": ["safe animation asset inventory"],
    "ControlRig gate probe": ["inspect_anim_graph_protected_topology", "controlrig_direct_gate_probe"],
    "state-machine runtime-driver proof": ["inspect_anim_state_machine_transitions"],
    "Baddy RigidBody": ["inspect_anim_graph_node_settings"],
    "node resolver plus same-instance pre/post proof": ["inspect_anim_graph_protected_topology", "compiled mapping"],
}

REQUEST_EXAMPLE_ROUTE_TARGET_CHARACTER_RULES = {
    "Post Process ModifyBone": ["Bot"],
    "BlendSpace sample variant": ["Bot"],
    "Bot Trail sample": ["Bot"],
    "UpperBody Slot and LayeredBlend": ["Bot"],
    "protected metadata boundary": ["Bot or Baddy", "depending on the named asset"],
    "ControlRig gate probe": ["Bot"],
    "state-machine runtime-driver proof": ["Bot"],
    "Baddy RigidBody": ["Baddy"],
    "node resolver plus same-instance pre/post proof": ["Bot or Baddy", "depending on the selected graph"],
}

REQUEST_EXAMPLE_ROUTE_TARGET_BODY_AREA_RULES = {
    "Post Process ModifyBone": ["head"],
    "BlendSpace sample variant": ["locomotion body response"],
    "Bot Trail sample": ["antenna_04_l chain", "mirrored only if requested"],
    "UpperBody Slot and LayeredBlend": ["upper body"],
    "protected metadata boundary": ["animation source metadata"],
    "ControlRig gate probe": ["foot IK", "interaction reach"],
    "state-machine runtime-driver proof": ["locomotion state-machine behavior"],
    "Baddy RigidBody": ["stalk", "body secondary motion"],
    "node resolver plus same-instance pre/post proof": ["target node output", "affected bones"],
}

REQUEST_EXAMPLE_ROUTE_TIMING_TYPE_RULES = {
    "Post Process ModifyBone": ["static late additive rotation"],
    "BlendSpace sample variant": ["continuous BlendSpace axis response"],
    "Bot Trail sample": ["secondary motion", "follow-through"],
    "UpperBody Slot and LayeredBlend": ["overlay action", "locomotion"],
    "protected metadata boundary": ["notify", "curve", "sync marker", "Montage metadata"],
    "ControlRig gate probe": ["late correction", "runtime inputs", "curves"],
    "state-machine runtime-driver proof": ["state duration", "transition condition"],
    "Baddy RigidBody": ["animation physics response"],
    "node resolver plus same-instance pre/post proof": ["instrumentation only"],
}

REQUEST_EXAMPLE_ROUTE_RUNTIME_LAYER_RULES = {
    "Post Process ModifyBone": ["Post Process AnimBP"],
    "BlendSpace sample variant": ["main AnimBP source BlendSpace"],
    "Bot Trail sample": ["Post Process AnimBP", "physics-style node"],
    "UpperBody Slot and LayeredBlend": ["Slot / LayeredBoneBlend", "main AnimBP"],
    "protected metadata boundary": ["animation asset metadata", "not pose graph"],
    "ControlRig gate probe": ["ControlRig", "main AnimBP"],
    "state-machine runtime-driver proof": ["main AnimBP state machine"],
    "Baddy RigidBody": ["RigidBody node", "AnimBP"],
    "node resolver plus same-instance pre/post proof": ["compiled AnimGraph", "node contribution"],
}

REQUEST_EXAMPLE_ROUTE_CXX_STATUS_RULES = {
    "Post Process ModifyBone": ["not needed"],
    "BlendSpace sample variant": ["not needed"],
    "Bot Trail sample": ["not needed"],
    "UpperBody Slot and LayeredBlend": ["candidate"],
    "protected metadata boundary": ["candidate"],
    "ControlRig gate probe": ["not needed"],
    "state-machine runtime-driver proof": ["candidate"],
    "Baddy RigidBody": ["not needed", "candidate"],
    "node resolver plus same-instance pre/post proof": ["not needed"],
}

REQUEST_EXAMPLE_ROUTE_EXPECTED_EVIDENCE_RULES = {
    "Post Process ModifyBone": ["runtime_graph_prepost", "same_instance_prepost"],
    "BlendSpace sample variant": ["valid_pose_count", "input_changed_pose"],
    "Bot Trail sample": ["same-instance Trail", "target chain delta"],
    "UpperBody Slot and LayeredBlend": ["BasePose", "BlendPoses[0]"],
    "protected metadata boundary": ["readable fields", "blocked protected fields"],
    "ControlRig gate probe": ["root-connected", "required gates", "same-instance pre/post"],
    "state-machine runtime-driver proof": ["current state", "transition progress", "restored runtime properties"],
    "Baddy RigidBody": ["RigidBody settings", "mapped runtime node", "pose deltas"],
    "node resolver plus same-instance pre/post proof": ["target node selection", "input/output links", "same-instance confirmation"],
}

REQUEST_EXAMPLE_ROUTE_SAMPLE_TARGET_RULES = {
    "Post Process ModifyBone": ["/Game/_MCP_Sample/AnimStudy/", "ABP_Bot_PostProcess_Study_HeadYawPlus5Study"],
    "BlendSpace sample variant": ["/Game/_MCP_Sample/AnimStudy/", "BS_Bot_WalkRunLean_LeanWideStudy"],
    "Bot Trail sample": ["/Game/_MCP_Sample/AnimStudy/", "ABP_Bot_Trail_Study"],
    "UpperBody Slot and LayeredBlend": ["none for route proof", "future sample overlay"],
    "protected metadata boundary": ["none until", "guarded native API"],
    "ControlRig gate probe": ["/Game/_MCP_Sample/AnimStudy/", "ABP_Bot_ControlRig_ForcedDriver_Study"],
    "state-machine runtime-driver proof": ["none for first pass", "future sample graph"],
    "Baddy RigidBody": ["/Game/_MCP_Sample/AnimStudy/", "ABP_Baddy_RigidBody_Study"],
    "node resolver plus same-instance pre/post proof": ["none unless", "controlled sample actor"],
}

CPP_API_CANDIDATE_MATRIX_REQUIRED_ROWS = [
    "ensure_state_machine_sample_variant",
    "ensure_layered_slot_overlay_sample",
    "ensure_anim_graph_rigidbody_demo_variant",
    "sample_anim_physics_variant_matrix",
    "inspect_physics_asset_constraints_guarded",
    "inspect_or_author_anim_notifies_curves",
    "resolve_anim_posewatch_target_actor",
    "extend_anim_node_runtime_mapping",
    "Broader Trail parameter editor",
    "inspect_blueprint_graph_call_topology",
]

REQUEST_EXAMPLE_MIN_ACCEPTANCE_FOCUS_BULLETS = 3

REQUEST_EXAMPLE_ROUTE_ACCEPTANCE_FOCUS_RULES = {
    "Post Process ModifyBone": ["sample Post Process AnimBP", "PoseWatch samples", "original `ABP_Bot`"],
    "BlendSpace sample variant": ["original `BS_Bot_WalkRunLean`", "edited sample coordinates", "pose grid compares"],
    "Bot Trail sample": ["disconnected original `ABP_Bot` Trail node", "component-level Post Process override", "SIE/PIE"],
    "UpperBody Slot and LayeredBlend": ["near-zero pose delta", "visible action proof", "explicit approval"],
    "protected metadata boundary": ["broad-probe Montage internals", "guarded API candidate", "AnimMontage.h:770"],
    "ControlRig gate probe": ["direct ControlRig solve", "gate names", "forced-driver sample"],
    "state-machine runtime-driver proof": ["runtime properties must be restored", "sampled world and AnimInstance", "graph authoring stays parked"],
    "Baddy RigidBody": ["animation-physics behavior", "same-instance proof", "original Baddy assets"],
    "node resolver plus same-instance pre/post proof": ["do not start by editing assets", "suspected node", "compiled mapping", "report ambiguity"],
}

REQUEST_EXAMPLE_ROUTE_ASK_USER_FIRST_RULES = {
    "Post Process ModifyBone": ["false"],
    "BlendSpace sample variant": ["false"],
    "Bot Trail sample": ["false"],
    "UpperBody Slot and LayeredBlend": ["false for route proof", "true before original asset mutation"],
    "protected metadata boundary": ["true before implementing", "guarded native API"],
    "ControlRig gate probe": ["false for sample proof", "true before editing original ABP_Bot or CR_Bot_Correction"],
    "state-machine runtime-driver proof": ["false for read/runtime proof", "true before original graph mutation", "new authoring API"],
    "Baddy RigidBody": ["false for sample/read proof", "true before original physics asset or AnimBP mutation"],
    "node resolver plus same-instance pre/post proof": ["false while the work is read-only instrumentation"],
}

REQUEST_EXAMPLE_ROUTE_MATRIX_CHECKED_RULES = {
    "Post Process ModifyBone": ["true"],
    "BlendSpace sample variant": ["true"],
    "Bot Trail sample": ["true"],
    "UpperBody Slot and LayeredBlend": ["true"],
    "protected metadata boundary": ["true"],
    "ControlRig gate probe": ["true"],
    "state-machine runtime-driver proof": ["true"],
    "Baddy RigidBody": ["true"],
    "node resolver plus same-instance pre/post proof": ["true"],
}

REQUEST_EXAMPLE_ROUTE_MATRIX_NOTE_RULES = {
    "Post Process ModifyBone": ["Post Process ModifyBone", "route classification", "execution", "evidence/approval"],
    "BlendSpace sample variant": ["BlendSpace sample variant", "route classification", "execution", "evidence/approval"],
    "Bot Trail sample": ["Bot Trail sample", "route classification", "execution", "evidence/approval"],
    "UpperBody Slot and LayeredBlend": ["UpperBody Slot and LayeredBlend", "route classification", "execution", "evidence/approval"],
    "protected metadata boundary": ["protected metadata boundary", "route classification", "execution", "evidence/approval"],
    "ControlRig gate probe": ["ControlRig gate probe", "route classification", "execution", "evidence/approval"],
    "state-machine runtime-driver proof": ["state-machine runtime-driver proof", "route classification", "execution", "evidence/approval"],
    "Baddy RigidBody": ["Baddy RigidBody", "route classification", "execution", "evidence/approval"],
    "node resolver plus same-instance pre/post proof": ["node resolver plus same-instance pre/post proof", "route classification", "execution", "evidence/approval"],
}

REQUEST_RUN_TEMPLATE_FIELD_GROUPS = {
    "request": [
        "user_request:",
        "date:",
        "operator:",
    ],
    "compiled_intent": [
        "target_character:",
        "target_body_area:",
        "timing_type:",
        "runtime_layer:",
        "route:",
        "sample_target:",
        "first_read_or_authoring_command:",
        "verification_command:",
        "expected_evidence:",
        "handoff_template:",
        "cxx_api_status:",
        "ask_user_first:",
        "route_matrix_checked:",
        "route_token_document_map_checked:",
        "route_token_acceptance_map_checked:",
        "route_matrix_notes:",
    ],
    "final_report": [
        "route:",
        "assets_created_or_reused:",
        "original_assets_modified:",
        "runtime_world:",
        "main_command_results:",
        "pose_or_state_evidence:",
        "errors:",
        "warnings:",
        "dirty_packages:",
        "cleanup:",
        "cxx_api_needed:",
        "artifact_paths:",
        "residual_risk:",
    ],
    "acceptance_checklist": [
        "Route token document map checked",
        "Route token acceptance map checked",
    ],
    "work_log": [
        "- Request:",
        "- Route:",
        "- Assets/evidence:",
        "- Verification:",
        "- C++/API decision:",
        "- Dirty packages/cleanup:",
        "- Residual risk:",
    ],
}

REQUEST_RUN_TEMPLATE_FIELD_SECTIONS = {
    "request": "## Request",
    "compiled_intent": "## Compiled Intent",
    "acceptance_checklist": "## Acceptance Checklist",
    "final_report": "## Final Report Draft",
    "work_log": "## Work-Log Entry Draft",
}

ACCEPTANCE_FINAL_REPORT_FIELDS = {
    "made_or_inspected": "what was made or inspected",
    "sample_or_evidence_location": "where the sample or evidence lives",
    "original_asset_scope": "whether original StackOBot assets were untouched",
    "runtime_proof_metric": "the runtime proof result in one or two concrete metrics",
    "cxx_api_status": "whether C++/API was unnecessary or parked",
    "residual_risk": "any residual risk that affects the next request",
}

ACCEPTANCE_UNIVERSAL_PASS_FIELDS = {
    "route_classification": "route classification and why it was chosen",
    "assets_created_or_reused": "assets created or reused",
    "original_asset_modification": "whether original StackOBot assets were modified",
    "compile_save_result": "compile/save result for authored sample assets",
    "runtime_world": "runtime world used for proof",
    "evidence_artifact_paths": "evidence artifact paths under `D:/Git/SampleProject/StackOBot/Saved/MCP/AnimStudy`",
    "errors_warnings": "command `errors` and `warnings`",
    "dirty_package_status": "dirty content and map package status",
    "cleanup_status": "cleanup status for transient actors and play sessions",
    "cxx_api_decision": "C++/API decision: `not needed`, `candidate`, or `implemented`",
}

ACCEPTANCE_ROUTE_CRITERIA = [
    "Post Process ModifyBone",
    "BlendSpace sample variant",
    "State-machine runtime driver",
    "ControlRig late correction",
    "UpperBody Slot/LayeredBlend",
    "Bot Trail secondary motion",
    "Baddy RigidBody physics",
    "Notify/curve/sync-marker/Montage metadata",
    "Node contribution proof",
]

ACCEPTANCE_EVIDENCE_STRENGTH_LEVELS = [
    "Read-only topology",
    "Sample compile/load",
    "Runtime smoke",
    "Same-instance pre/post",
]

ACCEPTANCE_ROUTE_TOKEN_MIN_STRENGTH_RULES = {
    "Post Process ModifyBone": "Same-instance pre/post",
    "BlendSpace sample variant": "Runtime smoke",
    "Bot Trail sample": "Same-instance pre/post",
    "UpperBody Slot and LayeredBlend": "Same-instance pre/post",
    "protected metadata boundary": "Read-only topology",
    "ControlRig gate probe": "Same-instance pre/post",
    "state-machine runtime-driver proof": "Runtime smoke",
    "Baddy RigidBody": "Same-instance pre/post",
    "node resolver plus same-instance pre/post proof": "Same-instance pre/post",
}

ACCEPTANCE_ESCALATION_TRIGGERS = {
    "cannot_author_sample_graph": "the current command surface cannot author the requested sample graph",
    "cannot_verify_route_proof": "the current command surface cannot verify the result with route-specific proof",
    "protected_metadata_required": "protected notifies, curves, sync markers, or Montage internals are required",
    "actor_resolution_repeated_failure": "target actor or AnimInstance resolution fails repeatedly",
    "missing_visible_action_source": "a visible action request needs a source clip, Montage, Slot path, or overlay",
    "missing_visible_action_sample": "sample that does not exist",
    "do_not_escalate_visual_complexity": "Do not escalate just because the request is visually complex.",
    "only_when_safe_route_blocked": "Escalate only when",
    "safe_route_blocked": "the existing safe route is blocked.",
}

COMMAND_SYNTAX_REQUIRED_QUICK_MAP_COMMANDS = [
    "inspect_anim_graph_protected_topology",
    "inspect_anim_state_machine_transitions",
    "inspect_anim_instance_runtime_state",
    "sample_anim_state_machine_runtime_response",
    "sample_anim_node_pre_post_runtime_pose",
    "sample_blendspace_runtime_pose_grid",
    "ensure_blendspace_sample_variant",
    "ensure_postprocess_anim_demo_variant",
    "controlrig_direct_gate_probe",
    "ensure_controlrig_forced_driver_animbp",
    "ensure_anim_graph_trail_demo",
    "inspect_anim_graph_node_settings",
    "set_anim_graph_rigidbody_settings",
]

COMMAND_SYNTAX_RESULT_CHECKLIST_TOKENS = {
    "success_errors_warnings": "`success`, `errors`, and `warnings`",
    "original_asset_scope": "original_assets_modified=false",
    "sample_asset_paths": "Target sample asset paths",
    "compile_save": "Compile/save result",
    "runtime_world": "`sampled_world_type` and `is_play_session_active`",
    "pose_or_state_evidence": "Key pose deltas or state-machine response",
    "dirty_packages": "Dirty package status",
    "cleanup": "Cleanup status",
    "artifact_paths": "Evidence artifact paths",
    "cxx_api_decision": "C++/API decision",
    "residual_risk": "Residual risk",
}

COMMAND_SYNTAX_REQUIRED_JSON_COMMANDS = [
    "ensure_postprocess_anim_demo_variant",
    "sample_anim_node_pre_post_runtime_pose",
    "ensure_blendspace_sample_variant",
    "sample_blendspace_runtime_pose_grid",
    "ensure_controlrig_forced_driver_animbp",
    "controlrig_direct_gate_probe",
    "inspect_anim_state_machine_transitions",
    "sample_anim_state_machine_runtime_response",
    "ensure_anim_graph_trail_demo",
    "inspect_anim_graph_node_settings",
    "set_anim_graph_rigidbody_settings",
]

COMMAND_SYNTAX_AUTHORING_COMMANDS = [
    "ensure_postprocess_anim_demo_variant",
    "ensure_blendspace_sample_variant",
    "ensure_controlrig_forced_driver_animbp",
    "ensure_anim_graph_trail_demo",
    "set_anim_graph_rigidbody_settings",
]

COMMAND_SYNTAX_REQUIRED_PARAM_SPECS: dict[str, list[str | tuple[str, ...]]] = {
    "ensure_postprocess_anim_demo_variant": [
        "source_blueprint_name",
        "source_skeletal_mesh",
        "variant_name",
        "target_blueprint_name",
        "target_skeletal_mesh",
        "bone_name",
        "rotation",
        "allow_non_sample",
    ],
    "sample_anim_node_pre_post_runtime_pose": [
        "blueprint_name",
        "node_type",
        "mode",
        "anim_instance_source",
        "sample_bones",
    ],
    "ensure_blendspace_sample_variant": [
        "source_blendspace",
        "variant_name",
        "sample_edits",
        "allow_non_sample",
    ],
    "sample_blendspace_runtime_pose_grid": [
        "skeletal_mesh",
        "blendspaces",
        "sample_bones",
    ],
    "ensure_controlrig_forced_driver_animbp": [
        "blueprint_name",
        "graph_name",
        "graph_type",
        "control_rig_class",
        "allow_non_sample",
    ],
    "controlrig_direct_gate_probe": [
        ("control_rig_path", "control_rig_class"),
        "sample_elements",
        "cases",
    ],
    "inspect_anim_state_machine_transitions": [
        "blueprint_name",
        "state_machine_name",
    ],
    "sample_anim_state_machine_runtime_response": [
        ("actor_label", "actor_name", "actor_filter"),
        "state_machine_name",
        "cases",
    ],
    "ensure_anim_graph_trail_demo": [
        "blueprint_name",
        "trail_bone",
        "base_joint",
        "allow_non_sample",
    ],
    "inspect_anim_graph_node_settings": [
        "blueprint_name",
        "node_type",
    ],
    "set_anim_graph_rigidbody_settings": [
        "blueprint_name",
        "allow_non_sample",
    ],
}

COMMAND_SYNTAX_SAMPLE_PATH_FIELDS = {
    "ensure_postprocess_anim_demo_variant": [
        "source_blueprint_name",
        "target_blueprint_name",
        "target_skeletal_mesh",
    ],
    "ensure_controlrig_forced_driver_animbp": [
        "blueprint_name",
    ],
    "ensure_anim_graph_trail_demo": [
        "blueprint_name",
    ],
    "set_anim_graph_rigidbody_settings": [
        "blueprint_name",
    ],
}

COMMAND_SYNTAX_PARAM_VALUE_RULES: dict[str, list[dict[str, Any]]] = {
    "ensure_postprocess_anim_demo_variant": [
        {"path": "bone_name", "operator": "equals", "expected": "head"},
        {"path": "compile", "operator": "equals", "expected": True},
        {"path": "save", "operator": "equals", "expected": True},
    ],
    "sample_anim_node_pre_post_runtime_pose": [
        {"path": "mode", "operator": "equals", "expected": "pose_watch_capture"},
        {"path": "anim_instance_source", "operator": "equals", "expected": "post_process"},
        {"path": "prefer_pie_world", "operator": "equals", "expected": False},
        {"path": "require_pie_world", "operator": "equals", "expected": False},
        {"path": "sample_bones", "operator": "contains", "expected": "head"},
    ],
    "ensure_blendspace_sample_variant": [
        {"path": "sample_edits", "operator": "non_empty_list"},
        {"path": "source_blendspace", "operator": "contains", "expected": "BS_Bot_WalkRunLean"},
    ],
    "sample_blendspace_runtime_pose_grid": [
        {"path": "blendspaces", "operator": "non_empty_list"},
        {"path": "blendspaces.0.samples", "operator": "non_empty_list"},
        {"path": "cleanup", "operator": "equals", "expected": True},
    ],
    "ensure_controlrig_forced_driver_animbp": [
        {"path": "graph_name", "operator": "equals", "expected": "AnimGraph"},
        {"path": "graph_type", "operator": "equals", "expected": "function"},
        {"path": "curve_values.IKBlend_l", "operator": "equals", "expected": 1.0},
        {"path": "input_defaults.ShouldDoIKTrace", "operator": "equals", "expected": True},
    ],
    "controlrig_direct_gate_probe": [
        {"path": "sample_elements", "operator": "non_empty_list"},
        {"path": "cases", "operator": "non_empty_list"},
        {"path": "cases.0.name", "operator": "equals", "expected": "baseline"},
    ],
    "inspect_anim_state_machine_transitions": [
        {"path": "include_pins", "operator": "equals", "expected": True},
        {"path": "include_rule_graph_nodes", "operator": "equals", "expected": True},
    ],
    "sample_anim_state_machine_runtime_response": [
        {"path": "cases", "operator": "non_empty_list"},
        {"path": "restore_after_case", "operator": "equals", "expected": True},
        {"path": "prefer_pie_world", "operator": "equals", "expected": True},
        {"path": "require_pie_world", "operator": "equals", "expected": False},
    ],
    "ensure_anim_graph_trail_demo": [
        {"path": "trail_bone", "operator": "equals", "expected": "antenna_04_l"},
        {"path": "base_joint", "operator": "equals", "expected": "head"},
    ],
    "inspect_anim_graph_node_settings": [
        {"path": "node_type", "operator": "equals", "expected": "RigidBody"},
        {"path": "include_pins", "operator": "equals", "expected": True},
    ],
    "set_anim_graph_rigidbody_settings": [
        {"path": "simulation_space", "operator": "equals", "expected": "ComponentSpace"},
        {"path": "enable_world_geometry", "operator": "equals", "expected": "false"},
    ],
}


def _project_relative(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _collect_doc_references(docs: list[Path]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for path in docs:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        for line_number, line in enumerate(lines, start=1):
            for match in RELATIVE_DOC_RE.finditer(line):
                ref_text = match.group(0)
                target = PROJECT_ROOT / ref_text
                references.append(
                    {
                        "source": _project_relative(path),
                        "line": line_number,
                        "reference": ref_text,
                        "target": _project_relative(target),
                        "exists": target.exists(),
                    }
                )
    return references


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def _external_path_entries() -> list[dict[str, Any]]:
    return [
        {
            "path": path.as_posix(),
            "exists": path.exists(),
            "kind": "directory" if path.is_dir() else "file" if path.is_file() else "missing",
        }
        for path in EXPECTED_EXTERNAL_PATHS
    ]


def _required_doc_entries() -> list[dict[str, Any]]:
    return [
        {
            "path": path_text,
            "exists": (PROJECT_ROOT / path_text).exists(),
        }
        for path_text in REQUIRED_DOC_PATHS
    ]


def _doc_index_coverage_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-doc-index.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    return [
        {
            "path": path_text,
            "required_doc": required_doc,
            "exists": required_doc in text,
        }
        for required_doc in REQUIRED_DOC_PATHS
        if required_doc != path_text
    ]


def _required_section_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path_text, sections in REQUIRED_SECTIONS.items():
        path = PROJECT_ROOT / path_text
        text = _read_text(path) if path.exists() else ""
        for section in sections:
            entries.append(
                {
                    "path": path_text,
                    "section": section,
                    "exists": section in text,
                }
            )
    return entries


def _required_token_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path_text, tokens in REQUIRED_TOKENS.items():
        path = PROJECT_ROOT / path_text
        text = _read_text(path) if path.exists() else ""
        for token in tokens:
            entries.append(
                {
                    "path": path_text,
                    "token": token,
                    "exists": token in text,
                }
            )
    return entries


def _markdown_heading_section(text: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    section_start = match.end()
    next_heading = re.search(r"^##\s+", text[section_start:], re.MULTILINE)
    if not next_heading:
        return text[section_start:]
    return text[section_start : section_start + next_heading.start()]


def _markdown_heading_exists(text: str, heading: str) -> bool:
    return bool(re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE))


def _markdown_table_cells(row: str) -> list[str]:
    stripped = row.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _parse_example_fields(block: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current_field = ""
    for line in block.splitlines():
        match = EXAMPLE_FIELD_RE.match(line)
        if match and match.group("name") in REQUEST_EXAMPLE_REQUIRED_FIELDS:
            current_field = match.group("name")
            fields[current_field] = [match.group("value").strip()]
        elif current_field:
            fields[current_field].append(line.strip())

    return {name: "\n".join(parts).strip() for name, parts in fields.items()}


def _request_example_field_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-request-run-examples.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    matches = list(EXAMPLE_SECTION_RE.finditer(text))
    entries: list[dict[str, Any]] = []

    for index, match in enumerate(matches):
        section_start = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section_text = text[section_start:section_end]
        fence_match = TEXT_FENCE_RE.search(section_text)
        fields = _parse_example_fields(fence_match.group("body")) if fence_match else {}

        for field in REQUEST_EXAMPLE_REQUIRED_FIELDS:
            value = fields.get(field, "")
            entries.append(
                {
                    "path": path_text,
                    "example": match.group(0).strip(),
                    "field": field,
                    "exists": field in fields,
                    "has_value": bool(value),
                }
            )

    if not matches:
        entries.append(
            {
                "path": path_text,
                "example": "",
                "field": "example_sections",
                "exists": False,
                "has_value": False,
            }
        )

    return entries


def _request_example_records() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-request-run-examples.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    matches = list(EXAMPLE_SECTION_RE.finditer(text))
    records: list[dict[str, Any]] = []

    for index, match in enumerate(matches):
        section_start = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section_text = text[section_start:section_end]
        fence_match = TEXT_FENCE_RE.search(section_text)
        fields = _parse_example_fields(fence_match.group("body")) if fence_match else {}
        records.append(
            {
                "path": path_text,
                "example": match.group(0).strip(),
                "section_text": section_text,
                "fields": fields,
            }
        )

    return records


def _sample_manifest_paths() -> set[str]:
    path = PROJECT_ROOT / "docs/stackobot-sample-asset-manifest.md"
    text = _read_text(path) if path.exists() else ""
    return set(SAMPLE_ASSET_PATH_RE.findall(text))


def _sample_target_manifest_entries() -> list[dict[str, Any]]:
    manifest_paths = _sample_manifest_paths()
    entries: list[dict[str, Any]] = []

    for record in _request_example_records():
        fields = record["fields"]
        sample_target = fields.get("sample_target", "")
        for sample_path in SAMPLE_ASSET_PATH_RE.findall(sample_target):
            entries.append(
                {
                    "path": record["path"],
                    "source": "request_example",
                    "example": record["example"],
                    "sample_target": sample_target,
                    "sample_path": sample_path,
                    "listed": sample_path in manifest_paths,
                }
            )

    route_matrix_path_text = "docs/stackobot-animation-route-matrix.md"
    route_matrix_path = PROJECT_ROOT / route_matrix_path_text
    route_matrix_text = _read_text(route_matrix_path) if route_matrix_path.exists() else ""
    execution_matrix = _markdown_heading_section(route_matrix_text, "## Execution Matrix")
    for sample_path in SAMPLE_ASSET_PATH_RE.findall(execution_matrix):
        entries.append(
            {
                "path": route_matrix_path_text,
                "source": "route_matrix_execution",
                "example": "",
                "sample_target": sample_path,
                "sample_path": sample_path,
                "listed": sample_path in manifest_paths,
            }
        )

    return entries


def _route_matrix_sample_target_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-route-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    execution_matrix = _markdown_heading_section(text, "## Execution Matrix")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in REQUEST_EXAMPLE_ROUTE_SAMPLE_TARGET_RULES.items():
        row = next(
            (
                line
                for line in execution_matrix.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        missing_tokens = [
            token for token in expected_tokens if token not in row
        ]
        entries.append(
            {
                "path": path_text,
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "missing_tokens": missing_tokens,
                "exists": bool(row),
                "matches": bool(row) and not missing_tokens,
            }
        )

    return entries


def _sample_manifest_route_target_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-sample-asset-manifest.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route Token Sample Target Map")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in REQUEST_EXAMPLE_ROUTE_SAMPLE_TARGET_RULES.items():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        missing_tokens = [
            token for token in expected_tokens if token not in row
        ]
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Sample Target Map",
                "check": "sample_manifest_route_target",
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "missing_tokens": missing_tokens,
                "exists": bool(row),
                "matches": bool(row) and not missing_tokens,
            }
        )

    return entries


def _route_matrix_any_token_entries(
    rules: dict[str, list[str]],
    field_name: str,
) -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-route-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    execution_matrix = _markdown_heading_section(text, "## Execution Matrix")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in rules.items():
        row = next(
            (
                line
                for line in execution_matrix.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        entries.append(
            {
                "path": path_text,
                "field": field_name,
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "exists": bool(row),
                "matches": bool(row) and _contains_any(row, set(expected_tokens)),
            }
        )

    return entries


def _route_matrix_classification_entries(
    rules: dict[str, list[str]],
    field_name: str,
) -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-route-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    classification = _markdown_heading_section(text, "## Route Classification")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in rules.items():
        row = next(
            (
                line
                for line in classification.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        missing_tokens = [
            token for token in expected_tokens if token not in row
        ]
        entries.append(
            {
                "path": path_text,
                "field": field_name,
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "missing_tokens": missing_tokens,
                "exists": bool(row),
                "matches": bool(row) and not missing_tokens,
            }
        )

    return entries


def _route_matrix_evidence_required_entries(
    rules: dict[str, list[str]],
    field_name: str,
) -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-route-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    evidence_matrix = _markdown_heading_section(text, "## Evidence And Approval Matrix")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in rules.items():
        row = next(
            (
                line
                for line in evidence_matrix.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        missing_tokens = [
            token for token in expected_tokens if token not in row
        ]
        entries.append(
            {
                "path": path_text,
                "field": field_name,
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "missing_tokens": missing_tokens,
                "exists": bool(row),
                "matches": bool(row) and not missing_tokens,
            }
        )

    return entries


def _route_matrix_evidence_any_token_entries(
    rules: dict[str, list[str]],
    field_name: str,
    *,
    lower_value: bool = False,
) -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-route-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    evidence_matrix = _markdown_heading_section(text, "## Evidence And Approval Matrix")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in rules.items():
        row = next(
            (
                line
                for line in evidence_matrix.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        comparison_row = row.lower() if lower_value else row
        comparison_tokens = [
            token.lower() if lower_value else token
            for token in expected_tokens
        ]
        entries.append(
            {
                "path": path_text,
                "field": field_name,
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "exists": bool(row),
                "matches": bool(row) and _contains_any(comparison_row, set(comparison_tokens)),
            }
        )

    return entries


def _route_matrix_selection_rule_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-route-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    selection_rules = _markdown_heading_section(text, "## Selection Rules")
    return [
        {
            "path": path_text,
            "route_key": route_key,
            "token": route_token,
            "exists": route_token in selection_rules,
        }
        for route_key, route_token in REQUEST_EXAMPLE_ROUTE_COVERAGE.items()
    ]


def _quickstart_route_shortcut_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-quickstart.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    route_shortcuts = _markdown_heading_section(text, "## Route Shortcuts")
    return [
        {
            "path": path_text,
            "route_key": route_key,
            "token": route_token,
            "exists": route_token in route_shortcuts,
        }
        for route_key, route_token in REQUEST_EXAMPLE_ROUTE_COVERAGE.items()
    ]


def _quickstart_start_here_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-quickstart.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Start Here")
    return [
        {
            "path": path_text,
            "section": "## Start Here",
            "key": key,
            "token": token,
            "exists": token in section,
        }
        for key, token in QUICKSTART_START_HERE_TOKENS.items()
    ]


def _quickstart_preflight_checklist_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-quickstart.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Preflight Checklist")
    return [
        {
            "path": path_text,
            "section": "## Preflight Checklist",
            "key": key,
            "token": token,
            "exists": token in section,
        }
        for key, token in QUICKSTART_PREFLIGHT_CHECKLIST_TOKENS.items()
    ]


def _doc_index_route_coverage_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-doc-index.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    route_coverage = _markdown_heading_section(text, "## Route Coverage")
    required_tokens = [
        *REQUEST_EXAMPLE_ROUTE_COVERAGE.values(),
        "docs/stackobot-animation-quickstart.md",
        "docs/stackobot-animation-route-matrix.md",
        "docs/stackobot-animation-request-run-examples.md",
    ]
    return [
        {
            "path": path_text,
            "section": "## Route Coverage",
            "token": token,
            "exists": token in route_coverage,
        }
        for token in required_tokens
    ]


def _doc_index_route_token_document_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-doc-index.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route Token Document Map")
    entries: list[dict[str, Any]] = []

    for route_token in REQUEST_EXAMPLE_ROUTE_COVERAGE.values():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        missing_docs = [
            doc for doc in DOC_INDEX_ROUTE_TOKEN_DOCUMENTS if doc not in row
        ]
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Document Map",
                "route_token": route_token,
                "row": row,
                "expected_docs": DOC_INDEX_ROUTE_TOKEN_DOCUMENTS,
                "missing_docs": missing_docs,
                "exists": bool(row),
                "matches": bool(row) and not missing_docs,
            }
        )

    return entries


def _cpp_api_route_decision_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-cpp-api-decision-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    route_decisions = _markdown_heading_section(text, "## Route Token Decision Map")
    entries: list[dict[str, Any]] = []
    for route_token, expected_tokens in REQUEST_EXAMPLE_ROUTE_CXX_STATUS_RULES.items():
        row = next(
            (
                line
                for line in route_decisions.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        lower_row = row.lower()
        expected_lower = [token.lower() for token in expected_tokens]
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Decision Map",
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "exists": bool(row),
                "matches": bool(row) and _contains_any(lower_row, set(expected_lower)),
            }
        )
    return entries


def _cpp_api_candidate_matrix_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-cpp-api-decision-matrix.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    candidate_matrix = _markdown_heading_section(text, "## Candidate Matrix")
    return [
        {
            "path": path_text,
            "section": "## Candidate Matrix",
            "candidate": candidate,
            "exists": candidate in candidate_matrix,
        }
        for candidate in CPP_API_CANDIDATE_MATRIX_REQUIRED_ROWS
    ]


def _handoff_route_map_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-tivret-handoff-templates.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    route_map = _markdown_heading_section(text, "## Route Token To Handoff")
    entries: list[dict[str, Any]] = []
    for route_token, expected_handoff in REQUEST_EXAMPLE_ROUTE_HANDOFF_RULES.items():
        row = next(
            (
                line
                for line in route_map.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token To Handoff",
                "route_token": route_token,
                "row": row,
                "expected_handoff": expected_handoff,
                "exists": bool(row),
                "matches": bool(row) and expected_handoff in row,
            }
        )
    return entries


def _route_token_command_row_entries(
    *,
    path_text: str,
    heading: str,
    check_name: str,
    route_tokens: list[str] | None = None,
) -> list[dict[str, Any]]:
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, heading)
    entries: list[dict[str, Any]] = []

    tokens = route_tokens or list(REQUEST_EXAMPLE_ROUTE_COVERAGE.values())
    for route_token in tokens:
        row = next(
            (
                line
                for line in section.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        expected_first_tokens = REQUEST_EXAMPLE_ROUTE_FIRST_COMMAND_RULES[route_token]
        expected_verification_tokens = REQUEST_EXAMPLE_ROUTE_VERIFICATION_RULES[route_token]
        missing_first_tokens = [
            token for token in expected_first_tokens if token not in row
        ]
        missing_verification_tokens = [
            token for token in expected_verification_tokens if token not in row
        ]
        entries.append(
            {
                "path": path_text,
                "section": heading,
                "check": check_name,
                "route_token": route_token,
                "row": row,
                "expected_first_tokens": expected_first_tokens,
                "expected_verification_tokens": expected_verification_tokens,
                "missing_first_tokens": missing_first_tokens,
                "missing_verification_tokens": missing_verification_tokens,
                "exists": bool(row),
                "matches": bool(row) and not missing_first_tokens and not missing_verification_tokens,
            }
        )

    return entries


def _contains_any(value: str, needles: list[str] | set[str]) -> bool:
    return any(needle in value for needle in needles)


def _request_example_safety_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in _request_example_records():
        fields = record["fields"]
        sample_target = fields.get("sample_target", "")
        sample_target_lower = sample_target.lower()
        sample_target_safe = (
            sample_target.startswith(SAMPLE_ANIM_STUDY_ROOT)
            or sample_target_lower.startswith("none")
        )
        entries.append(
            {
                "path": record["path"],
                "example": record["example"],
                "check": "sample_target_scope",
                "value": sample_target,
                "safe": sample_target_safe,
            }
        )

        handoff_template = fields.get("handoff_template", "")
        handoff_safe = (
            handoff_template in REQUEST_EXAMPLE_ALLOWED_HANDOFFS
            or handoff_template.startswith("no authoring handoff")
        )
        entries.append(
            {
                "path": record["path"],
                "example": record["example"],
                "check": "handoff_template",
                "value": handoff_template,
                "safe": handoff_safe,
            }
        )

        cxx_api_status = fields.get("cxx_api_status", "").lower()
        cxx_safe = "not needed" in cxx_api_status or "candidate" in cxx_api_status
        entries.append(
            {
                "path": record["path"],
                "example": record["example"],
                "check": "cxx_api_status",
                "value": fields.get("cxx_api_status", ""),
                "safe": cxx_safe,
            }
        )

        ask_user_first = fields.get("ask_user_first", "").lower()
        ask_user_safe = ask_user_first.startswith("false") or ask_user_first.startswith("true")
        entries.append(
            {
                "path": record["path"],
                "example": record["example"],
                "check": "ask_user_first",
                "value": fields.get("ask_user_first", ""),
                "safe": ask_user_safe,
            }
        )

        first_command = fields.get("first_read_or_authoring_command", "")
        entries.append(
            {
                "path": record["path"],
                "example": record["example"],
                "check": "first_read_or_authoring_command",
                "value": first_command,
                "safe": _contains_any(first_command, REQUEST_EXAMPLE_FIRST_COMMAND_KEYWORDS),
            }
        )

        verification_command = fields.get("verification_command", "")
        entries.append(
            {
                "path": record["path"],
                "example": record["example"],
                "check": "verification_command",
                "value": verification_command,
                "safe": _contains_any(verification_command, REQUEST_EXAMPLE_VERIFICATION_KEYWORDS),
            }
        )

    return entries


def _request_example_route_coverage_entries() -> list[dict[str, Any]]:
    records = _request_example_records()
    routes = [
        str(record["fields"].get("route", ""))
        for record in records
    ]
    return [
        {
            "path": "docs/stackobot-animation-request-run-examples.md",
            "route_key": route_key,
            "token": token,
            "exists": any(token in route for route in routes),
        }
        for route_key, token in REQUEST_EXAMPLE_ROUTE_COVERAGE.items()
    ]


def _request_compiler_route_coverage_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-request-compiler-drills.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    sections = {
        "signal_words": _markdown_heading_section(text, "## Signal Words"),
        "drill_table": _markdown_heading_section(text, "## Drill Table"),
    }
    entries: list[dict[str, Any]] = []
    for route_key, rules in REQUEST_COMPILER_ROUTE_COVERAGE_RULES.items():
        for section_key, tokens_key in [
            ("signal_words", "signal_tokens"),
            ("drill_table", "drill_tokens"),
        ]:
            section_text = sections[section_key]
            for token in rules[tokens_key]:
                entries.append(
                    {
                        "path": path_text,
                        "route_key": route_key,
                        "section": section_key,
                        "token": token,
                        "exists": token in section_text,
                    }
                )
    return entries


def _request_example_route_tokens(route: str, rules: dict[str, Any]) -> list[str]:
    return [token for token in rules if token in route]


def _request_example_route_prefix_entries(
    rules: dict[str, str],
    field_name: str,
    expected_key: str,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in _request_example_records():
        fields = record["fields"]
        route = fields.get("route", "")
        value = fields.get(field_name, "")
        matched_tokens = _request_example_route_tokens(route, rules)
        if not matched_tokens:
            entries.append(
                {
                    "path": record["path"],
                    "example": record["example"],
                    "route": route,
                    field_name: value,
                    expected_key: "",
                    "matches": False,
                    "known_route": False,
                }
            )
            continue

        for route_token in matched_tokens:
            expected_value = rules[route_token]
            entries.append(
                {
                    "path": record["path"],
                    "example": record["example"],
                    "route": route,
                    "route_token": route_token,
                    field_name: value,
                    expected_key: expected_value,
                    "matches": value.startswith(expected_value),
                    "known_route": True,
                }
            )

    return entries


def _request_example_route_any_token_entries(
    rules: dict[str, list[str]],
    field_name: str,
    expected_key: str,
    *,
    lower_value: bool = False,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in _request_example_records():
        fields = record["fields"]
        route = fields.get("route", "")
        value = fields.get(field_name, "")
        comparison_value = value.lower() if lower_value else value
        matched_tokens = _request_example_route_tokens(route, rules)
        if not matched_tokens:
            entries.append(
                {
                    "path": record["path"],
                    "example": record["example"],
                    "route": route,
                    field_name: value,
                    expected_key: [],
                    "matches": False,
                    "known_route": False,
                }
            )
            continue

        for route_token in matched_tokens:
            expected_values = rules[route_token]
            entries.append(
                {
                    "path": record["path"],
                    "example": record["example"],
                    "route": route,
                    "route_token": route_token,
                    field_name: value,
                    expected_key: expected_values,
                    "matches": _contains_any(comparison_value, set(expected_values)),
                    "known_route": True,
                }
            )

    return entries


def _request_example_route_required_token_entries(
    rules: dict[str, list[str]],
    field_name: str,
    *,
    value_getter: Any = None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in _request_example_records():
        fields = record["fields"]
        route = fields.get("route", "")
        value = value_getter(record) if value_getter else fields.get(field_name, "")
        matched_tokens = _request_example_route_tokens(route, rules)
        if not matched_tokens:
            entries.append(
                {
                    "path": record["path"],
                    "example": record["example"],
                    "route": route,
                    field_name: value,
                    "expected_tokens": [],
                    "missing_tokens": [],
                    "matches": False,
                    "known_route": False,
                }
            )
            continue

        for route_token in matched_tokens:
            expected_tokens = rules[route_token]
            missing_tokens = [
                token for token in expected_tokens if token not in value
            ]
            entries.append(
                {
                    "path": record["path"],
                    "example": record["example"],
                    "route": route,
                    "route_token": route_token,
                    field_name: value,
                    "expected_tokens": expected_tokens,
                    "missing_tokens": missing_tokens,
                    "matches": not missing_tokens,
                    "known_route": True,
                }
            )

    return entries


def _request_example_route_handoff_entries() -> list[dict[str, Any]]:
    return _request_example_route_prefix_entries(
        REQUEST_EXAMPLE_ROUTE_HANDOFF_RULES,
        "handoff_template",
        "expected_handoff",
    )


def _request_example_route_verification_entries() -> list[dict[str, Any]]:
    return _request_example_route_any_token_entries(
        REQUEST_EXAMPLE_ROUTE_VERIFICATION_RULES,
        "verification_command",
        "expected_verification",
    )


def _request_example_route_first_command_entries() -> list[dict[str, Any]]:
    return _request_example_route_any_token_entries(
        REQUEST_EXAMPLE_ROUTE_FIRST_COMMAND_RULES,
        "first_read_or_authoring_command",
        "expected_first_command",
    )


def _request_example_route_target_character_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_TARGET_CHARACTER_RULES,
        "target_character",
    )


def _request_example_route_target_body_area_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_TARGET_BODY_AREA_RULES,
        "target_body_area",
    )


def _request_example_route_timing_type_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_TIMING_TYPE_RULES,
        "timing_type",
    )


def _request_example_route_runtime_layer_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_RUNTIME_LAYER_RULES,
        "runtime_layer",
    )


def _request_example_route_cxx_status_entries() -> list[dict[str, Any]]:
    return _request_example_route_any_token_entries(
        REQUEST_EXAMPLE_ROUTE_CXX_STATUS_RULES,
        "cxx_api_status",
        "expected_cxx_status",
        lower_value=True,
    )


def _request_example_route_expected_evidence_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_EXPECTED_EVIDENCE_RULES,
        "expected_evidence",
    )


def _request_example_route_sample_target_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_SAMPLE_TARGET_RULES,
        "sample_target",
    )


def _request_example_route_ask_user_first_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_ASK_USER_FIRST_RULES,
        "ask_user_first",
    )


def _request_example_route_matrix_checked_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_MATRIX_CHECKED_RULES,
        "route_matrix_checked",
    )


def _request_example_route_token_document_map_checked_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_MATRIX_CHECKED_RULES,
        "route_token_document_map_checked",
    )


def _request_example_route_token_acceptance_map_checked_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_MATRIX_CHECKED_RULES,
        "route_token_acceptance_map_checked",
    )


def _request_example_route_matrix_notes_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_MATRIX_NOTE_RULES,
        "route_matrix_notes",
    )


def _request_example_acceptance_focus_text(record: dict[str, Any]) -> str:
    section_text = str(record.get("section_text", ""))
    focus_index = section_text.find("Acceptance focus:")
    return section_text[focus_index:] if focus_index >= 0 else ""


def _request_example_acceptance_focus_entries() -> list[dict[str, Any]]:
    records = _request_example_records()
    entries: list[dict[str, Any]] = []

    for record in records:
        focus_text = _request_example_acceptance_focus_text(record)
        bullet_count = len(re.findall(r"(?m)^- ", focus_text))
        entries.append(
            {
                "path": record["path"],
                "example": record["example"],
                "check": "acceptance_focus_block",
                "exists": bool(focus_text),
                "bullet_count": bullet_count,
                "minimum_bullet_count": REQUEST_EXAMPLE_MIN_ACCEPTANCE_FOCUS_BULLETS,
                "has_minimum_bullets": bullet_count >= REQUEST_EXAMPLE_MIN_ACCEPTANCE_FOCUS_BULLETS,
            }
        )

    if not records:
        entries.append(
            {
                "path": "docs/stackobot-animation-request-run-examples.md",
                "example": "",
                "check": "acceptance_focus_block",
                "exists": False,
                "bullet_count": 0,
                "minimum_bullet_count": REQUEST_EXAMPLE_MIN_ACCEPTANCE_FOCUS_BULLETS,
                "has_minimum_bullets": False,
            }
        )

    return entries


def _request_example_route_acceptance_focus_entries() -> list[dict[str, Any]]:
    return _request_example_route_required_token_entries(
        REQUEST_EXAMPLE_ROUTE_ACCEPTANCE_FOCUS_RULES,
        "acceptance_focus",
        value_getter=_request_example_acceptance_focus_text,
    )


def _request_run_template_field_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-request-run-template.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    entries: list[dict[str, Any]] = []

    for group, fields in REQUEST_RUN_TEMPLATE_FIELD_GROUPS.items():
        for field in fields:
            entries.append(
                {
                    "path": path_text,
                    "group": group,
                    "field": field,
                    "exists": field in text,
                }
            )
    return entries


def _request_run_template_section_field_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-request-run-template.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    entries: list[dict[str, Any]] = []

    for group, fields in REQUEST_RUN_TEMPLATE_FIELD_GROUPS.items():
        heading = REQUEST_RUN_TEMPLATE_FIELD_SECTIONS[group]
        if group == "work_log":
            match = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
            section = text[match.end() :] if match else ""
        else:
            section = _markdown_heading_section(text, heading)
        for field in fields:
            entries.append(
                {
                    "path": path_text,
                    "group": group,
                    "section": heading,
                    "field": field,
                    "exists": field in section,
                }
            )

    return entries


def _request_run_template_acceptance_gate_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-request-run-template.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Acceptance Checklist")
    tokens = list(ACCEPTANCE_UNIVERSAL_PASS_FIELDS.values())
    tokens.extend(REQUEST_RUN_TEMPLATE_FIELD_GROUPS["acceptance_checklist"])
    return [
        {
            "path": path_text,
            "section": "## Acceptance Checklist",
            "token": token,
            "exists": token in section,
        }
        for token in tokens
    ]


def _playbook_delivery_shape_field_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-request-playbook.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Delivery Shape")
    return [
        {
            "path": path_text,
            "section": "## Delivery Shape",
            "field": field,
            "exists": field in section,
        }
        for field in REQUEST_RUN_TEMPLATE_FIELD_GROUPS["final_report"]
    ]


def _handoff_final_report_field_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-tivret-handoff-templates.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Final Report Shape")
    return [
        {
            "path": path_text,
            "section": "## Final Report Shape",
            "field": field,
            "exists": field in section,
        }
        for field in REQUEST_RUN_TEMPLATE_FIELD_GROUPS["final_report"]
    ]


def _handoff_route_token_final_report_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-tivret-handoff-templates.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route Token Final Report Map")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in REQUEST_EXAMPLE_ROUTE_EXPECTED_EVIDENCE_RULES.items():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        lower_row = row.lower()
        missing_tokens = [
            token for token in expected_tokens if token.lower() not in lower_row
        ]
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Final Report Map",
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "missing_tokens": missing_tokens,
                "exists": bool(row),
                "matches": bool(row) and not missing_tokens,
            }
        )

    return entries


def _handoff_route_token_final_report_cxx_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-tivret-handoff-templates.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route Token Final Report Map")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in REQUEST_EXAMPLE_ROUTE_CXX_STATUS_RULES.items():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        lower_row = row.lower()
        expected_lower = [token.lower() for token in expected_tokens]
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Final Report Map",
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "exists": bool(row),
                "matches": bool(row) and _contains_any(lower_row, set(expected_lower)),
            }
        )

    return entries


def _acceptance_final_report_field_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Final User Report Checklist")
    return [
        {
            "path": path_text,
            "section": "## Final User Report Checklist",
            "field": field,
            "token": token,
            "exists": token in section,
        }
        for field, token in ACCEPTANCE_FINAL_REPORT_FIELDS.items()
    ]


def _acceptance_universal_pass_field_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Universal Pass Gate")
    return [
        {
            "path": path_text,
            "section": "## Universal Pass Gate",
            "field": field,
            "token": token,
            "exists": token in section,
        }
        for field, token in ACCEPTANCE_UNIVERSAL_PASS_FIELDS.items()
    ]


def _acceptance_completion_evidence_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Universal Pass Gate")
    return [
        {
            "path": path_text,
            "section": "## Universal Pass Gate",
            "key": key,
            "token": token,
            "exists": token in section,
        }
        for key, token in ACCEPTANCE_COMPLETION_EVIDENCE_TOKENS.items()
    ]


def _acceptance_route_criteria_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route-Specific Pass Criteria")
    return [
        {
            "path": path_text,
            "section": "## Route-Specific Pass Criteria",
            "route": route,
            "exists": f"| {route} |" in section,
        }
        for route in ACCEPTANCE_ROUTE_CRITERIA
    ]


def _acceptance_route_token_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route-Specific Pass Criteria")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in REQUEST_EXAMPLE_ROUTE_EXPECTED_EVIDENCE_RULES.items():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"| `{route_token}` |" in line
            ),
            "",
        )
        lower_row = row.lower()
        missing_tokens = [
            token for token in expected_tokens if token.lower() not in lower_row
        ]
        entries.append(
            {
                "path": path_text,
                "section": "## Route-Specific Pass Criteria",
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "missing_tokens": missing_tokens,
                "exists": bool(row),
                "matches": bool(row) and not missing_tokens,
            }
        )

    return entries


def _acceptance_evidence_strength_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Evidence Strength Levels")
    return [
        {
            "path": path_text,
            "section": "## Evidence Strength Levels",
            "level": level,
            "exists": f"| {level} |" in section,
        }
        for level in ACCEPTANCE_EVIDENCE_STRENGTH_LEVELS
    ]


def _acceptance_evidence_strength_detail_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Evidence Strength Levels")
    return [
        {
            "path": path_text,
            "section": "## Evidence Strength Levels",
            "key": key,
            "token": token,
            "exists": token in section,
        }
        for key, token in ACCEPTANCE_EVIDENCE_STRENGTH_DETAIL_TOKENS.items()
    ]


def _acceptance_escalation_trigger_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## When To Stop And Escalate")
    return [
        {
            "path": path_text,
            "section": "## When To Stop And Escalate",
            "trigger": trigger,
            "token": token,
            "exists": token in section,
        }
        for trigger, token in ACCEPTANCE_ESCALATION_TRIGGERS.items()
    ]


def _command_syntax_json_blocks() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-mcp-command-syntax.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    entries: list[dict[str, Any]] = []

    for index, match in enumerate(JSON_FENCE_RE.finditer(text), start=1):
        body = match.group("body")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            entries.append(
                {
                    "path": path_text,
                    "block_index": index,
                    "parse_success": False,
                    "command": "",
                    "error": str(exc),
                }
            )
            continue

        entries.append(
            {
                "path": path_text,
                "block_index": index,
                "parse_success": True,
                "command": str(payload.get("command", "")),
                "params": payload.get("params", {}),
            }
        )

    return entries


def _command_syntax_command_entries(json_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    commands = {
        str(block.get("command", ""))
        for block in json_blocks
        if block.get("parse_success") and block.get("command")
    }
    return [
        {
            "path": "docs/stackobot-animation-mcp-command-syntax.md",
            "command": command,
            "exists": command in commands,
        }
        for command in COMMAND_SYNTAX_REQUIRED_JSON_COMMANDS
    ]


def _command_quick_map_command_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-mcp-command-syntax.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Command Quick Map")
    return [
        {
            "path": path_text,
            "section": "## Command Quick Map",
            "command": command,
            "exists": f"`{command}`" in section,
        }
        for command in COMMAND_SYNTAX_REQUIRED_QUICK_MAP_COMMANDS
    ]


def _command_route_map_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-mcp-command-syntax.md",
        heading="## Route Token Command Map",
        check_name="command_route_map",
    )


def _authoring_route_template_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-authoring-templates.md",
        heading="## Route Token Template Map",
        check_name="authoring_route_template",
    )


def _playbook_route_map_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-request-playbook.md",
        heading="## Route Token Playbook Map",
        check_name="playbook_route_map",
    )


def _playbook_route_failure_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-request-playbook.md",
        heading="## Route Token Failure Map",
        check_name="playbook_route_failure",
    )


def _playbook_route_failure_cxx_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-request-playbook.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route Token Failure Map")
    entries: list[dict[str, Any]] = []

    for route_token, expected_tokens in REQUEST_EXAMPLE_ROUTE_CXX_STATUS_RULES.items():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        lower_row = row.lower()
        expected_lower = [token.lower() for token in expected_tokens]
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Failure Map",
                "route_token": route_token,
                "row": row,
                "expected_tokens": expected_tokens,
                "exists": bool(row),
                "matches": bool(row) and _contains_any(lower_row, set(expected_lower)),
            }
        )

    return entries


def _animbp_authoring_pattern_route_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animbp-authoring-patterns.md",
        heading="## Route Token Pattern Map",
        check_name="animbp_authoring_pattern_route",
    )


def _physics_route_token_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-physics-request-grammar.md",
        heading="## Physics Route Token Map",
        check_name="physics_route_token",
        route_tokens=["Bot Trail sample", "Baddy RigidBody"],
    )


def _backlog_route_token_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-next-work-backlog.md",
        heading="## Route Token Backlog Map",
        check_name="backlog_route_token",
    )


def _closeout_ready_route_token_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-study-closeout.md",
        heading="## Ready Route Token Map",
        check_name="closeout_ready_route_token",
    )


def _closeout_next_request_protocol_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-study-closeout.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Next Request Protocol")
    return [
        {
            "path": path_text,
            "section": "## Next Request Protocol",
            "key": key,
            "token": token,
            "exists": token in section,
        }
        for key, token in CLOSEOUT_NEXT_REQUEST_PROTOCOL_TOKENS.items()
    ]


def _closeout_cxx_api_timing_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-study-closeout.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## C++ / API Timing")
    return [
        {
            "path": path_text,
            "section": "## C++ / API Timing",
            "key": key,
            "token": token,
            "exists": token in section,
        }
        for key, token in CLOSEOUT_CXX_API_TIMING_TOKENS.items()
    ]


def _quickstart_route_token_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-quickstart.md",
        heading="## Route Token Quick Map",
        check_name="quickstart_route_token",
    )


def _request_compiler_route_token_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-request-compiler-drills.md",
        heading="## Route Token Compiler Map",
        check_name="request_compiler_route_token",
    )


def _acceptance_route_token_map_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-acceptance-checklist.md",
        heading="## Route Token Acceptance Map",
        check_name="acceptance_route_token_map",
    )


def _acceptance_route_token_min_strength_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-acceptance-checklist.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route Token Acceptance Map")
    entries: list[dict[str, Any]] = []

    for route_token, expected_strength in ACCEPTANCE_ROUTE_TOKEN_MIN_STRENGTH_RULES.items():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"| `{route_token}` |" in line
            ),
            "",
        )
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Acceptance Map",
                "route_token": route_token,
                "row": row,
                "expected_strength": expected_strength,
                "exists": bool(row),
                "matches": bool(row) and expected_strength in row,
            }
        )

    return entries


def _execution_evidence_route_token_entries() -> list[dict[str, Any]]:
    return _route_token_command_row_entries(
        path_text="docs/stackobot-animation-execution-map.md",
        heading="## Route Token Evidence Map",
        check_name="execution_evidence_route_token",
    )


def _execution_evidence_section_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-execution-map.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Route Token Evidence Map")
    entries: list[dict[str, Any]] = []

    for route_token in REQUEST_EXAMPLE_ROUTE_COVERAGE.values():
        row = next(
            (
                line
                for line in section.splitlines()
                if f"`{route_token}`" in line
            ),
            "",
        )
        cells = _markdown_table_cells(row)
        evidence_cell = cells[1] if len(cells) > 1 else ""
        evidence_sections = re.findall(r"`([^`]+)`", evidence_cell)
        missing_sections = [
            heading
            for heading in evidence_sections
            if not _markdown_heading_exists(text, heading)
        ]
        entries.append(
            {
                "path": path_text,
                "section": "## Route Token Evidence Map",
                "check": "execution_evidence_sections",
                "route_token": route_token,
                "row": row,
                "evidence_sections": evidence_sections,
                "missing_sections": missing_sections,
                "exists": bool(row),
                "matches": bool(row) and bool(evidence_sections) and not missing_sections,
            }
        )

    return entries


def _command_syntax_result_checklist_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-mcp-command-syntax.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Result Checklist")
    return [
        {
            "path": path_text,
            "section": "## Result Checklist",
            "field": field,
            "token": token,
            "exists": token in section,
        }
        for field, token in COMMAND_SYNTAX_RESULT_CHECKLIST_TOKENS.items()
    ]


def _local_check_runner_schema_entries() -> list[dict[str, Any]]:
    path_text = "Tools/Unreal/run_stackobot_animation_local_checks.py"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    return [
        {
            "path": path_text,
            "key": key,
            "token": token,
            "exists": token in text,
        }
        for key, token in LOCAL_CHECK_RUNNER_SCHEMA_TOKENS.items()
    ]


def _doc_index_local_check_command_entries() -> list[dict[str, Any]]:
    path_text = "docs/stackobot-animation-doc-index.md"
    path = PROJECT_ROOT / path_text
    text = _read_text(path) if path.exists() else ""
    section = _markdown_heading_section(text, "## Local Checks")
    return [
        {
            "path": path_text,
            "section": "## Local Checks",
            "command": command,
            "exists": command in section,
        }
        for command in DOC_INDEX_LOCAL_CHECK_COMMANDS
    ]


def _preflight_required_command_entries() -> list[dict[str, Any]]:
    path_text = "Tools/Unreal/check_stackobot_animation_preflight.py"
    path = PROJECT_ROOT / path_text
    required_commands: set[str] = set()
    if path.exists():
        try:
            module = ast.parse(_read_text(path), filename=path_text)
            for node in module.body:
                if not isinstance(node, ast.Assign):
                    continue
                has_required_commands_target = any(
                    isinstance(target, ast.Name) and target.id == "REQUIRED_COMMANDS"
                    for target in node.targets
                )
                if not has_required_commands_target:
                    continue
                value = ast.literal_eval(node.value)
                if isinstance(value, list):
                    required_commands = {command for command in value if isinstance(command, str)}
                break
        except (SyntaxError, TypeError, ValueError):
            required_commands = set()
    return [
        {
            "path": path_text,
            "command": command,
            "source": "REQUIRED_COMMANDS",
            "exists": command in required_commands,
        }
        for command in COMMAND_SYNTAX_REQUIRED_QUICK_MAP_COMMANDS
    ]


def _command_syntax_authoring_safety_entries(json_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for command in COMMAND_SYNTAX_AUTHORING_COMMANDS:
        matching_blocks = [
            block
            for block in json_blocks
            if block.get("parse_success") and block.get("command") == command
        ]
        if not matching_blocks:
            entries.append(
                {
                    "path": "docs/stackobot-animation-mcp-command-syntax.md",
                    "command": command,
                    "block_index": None,
                    "field": "allow_non_sample",
                    "exists": False,
                    "safe_value": False,
                }
            )
            continue

        for block in matching_blocks:
            params = block.get("params") if isinstance(block.get("params"), dict) else {}
            value = params.get("allow_non_sample")
            entries.append(
                {
                    "path": "docs/stackobot-animation-mcp-command-syntax.md",
                    "command": command,
                    "block_index": block.get("block_index"),
                    "field": "allow_non_sample",
                    "exists": "allow_non_sample" in params,
                    "safe_value": value is False,
                }
            )
    return entries


def _param_has_value(params: dict[str, Any], field: str) -> bool:
    if field not in params:
        return False
    value = params[field]
    return value not in ("", None, [], {})


def _param_spec_label(spec: str | tuple[str, ...]) -> str:
    if isinstance(spec, tuple):
        return " or ".join(spec)
    return spec


def _param_spec_satisfied(params: dict[str, Any], spec: str | tuple[str, ...]) -> tuple[bool, str]:
    if isinstance(spec, tuple):
        matched = [field for field in spec if _param_has_value(params, field)]
        return bool(matched), matched[0] if matched else ""
    return _param_has_value(params, spec), spec if _param_has_value(params, spec) else ""


def _command_syntax_required_param_entries(json_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for command, param_specs in COMMAND_SYNTAX_REQUIRED_PARAM_SPECS.items():
        matching_blocks = [
            block
            for block in json_blocks
            if block.get("parse_success") and block.get("command") == command
        ]
        if not matching_blocks:
            for spec in param_specs:
                entries.append(
                    {
                        "path": "docs/stackobot-animation-mcp-command-syntax.md",
                        "command": command,
                        "block_index": None,
                        "param": _param_spec_label(spec),
                        "exists": False,
                        "has_value": False,
                        "matched_param": "",
                    }
                )
            continue

        for block in matching_blocks:
            params = block.get("params") if isinstance(block.get("params"), dict) else {}
            for spec in param_specs:
                satisfied, matched_param = _param_spec_satisfied(params, spec)
                entries.append(
                    {
                        "path": "docs/stackobot-animation-mcp-command-syntax.md",
                        "command": command,
                        "block_index": block.get("block_index"),
                        "param": _param_spec_label(spec),
                        "exists": satisfied,
                        "has_value": satisfied,
                        "matched_param": matched_param,
                    }
                )
    return entries


def _is_safe_sample_path(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(SAMPLE_ANIM_STUDY_ROOT)


def _command_syntax_sample_path_entries(json_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for command, fields in COMMAND_SYNTAX_SAMPLE_PATH_FIELDS.items():
        matching_blocks = [
            block
            for block in json_blocks
            if block.get("parse_success") and block.get("command") == command
        ]
        if not matching_blocks:
            for field in fields:
                entries.append(
                    {
                        "path": "docs/stackobot-animation-mcp-command-syntax.md",
                        "command": command,
                        "block_index": None,
                        "field": field,
                        "exists": False,
                        "safe_value": False,
                        "value": "",
                    }
                )
            continue

        for block in matching_blocks:
            params = block.get("params") if isinstance(block.get("params"), dict) else {}
            for field in fields:
                value = params.get(field)
                entries.append(
                    {
                        "path": "docs/stackobot-animation-mcp-command-syntax.md",
                        "command": command,
                        "block_index": block.get("block_index"),
                        "field": field,
                        "exists": field in params,
                        "safe_value": _is_safe_sample_path(value),
                        "value": value if isinstance(value, str) else "",
                    }
                )
    return entries


def _param_path_value(params: dict[str, Any], path: str) -> tuple[bool, Any]:
    value: Any = params
    for part in path.split("."):
        if isinstance(value, dict):
            if part not in value:
                return False, None
            value = value[part]
            continue
        if isinstance(value, list) and part.isdigit():
            index = int(part)
            if index >= len(value):
                return False, None
            value = value[index]
            continue
        return False, None
    return True, value


def _param_value_matches(value: Any, spec: dict[str, Any]) -> bool:
    operator = spec.get("operator")
    if operator == "equals":
        return value == spec.get("expected")
    if operator == "contains":
        expected = spec.get("expected")
        if isinstance(value, str):
            return isinstance(expected, str) and expected in value
        if isinstance(value, list):
            return expected in value
        if isinstance(value, dict):
            return isinstance(expected, str) and expected in value
    if operator == "non_empty_list":
        return isinstance(value, list) and bool(value)
    if operator == "non_empty_dict":
        return isinstance(value, dict) and bool(value)
    return False


def _command_syntax_param_value_entries(json_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for command, specs in COMMAND_SYNTAX_PARAM_VALUE_RULES.items():
        matching_blocks = [
            block
            for block in json_blocks
            if block.get("parse_success") and block.get("command") == command
        ]
        if not matching_blocks:
            for spec in specs:
                entries.append(
                    {
                        "path": "docs/stackobot-animation-mcp-command-syntax.md",
                        "command": command,
                        "block_index": None,
                        "param_path": spec["path"],
                        "operator": spec.get("operator", ""),
                        "expected": spec.get("expected", ""),
                        "exists": False,
                        "matches": False,
                        "value": None,
                    }
                )
            continue

        for block in matching_blocks:
            params = block.get("params") if isinstance(block.get("params"), dict) else {}
            for spec in specs:
                exists, value = _param_path_value(params, str(spec["path"]))
                entries.append(
                    {
                        "path": "docs/stackobot-animation-mcp-command-syntax.md",
                        "command": command,
                        "block_index": block.get("block_index"),
                        "param_path": spec["path"],
                        "operator": spec.get("operator", ""),
                        "expected": spec.get("expected", ""),
                        "exists": exists,
                        "matches": exists and _param_value_matches(value, spec),
                        "value": value,
                    }
                )
    return entries


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    docs = sorted(DOCS_ROOT.glob(args.glob))
    references = _collect_doc_references(docs)
    missing_references = [entry for entry in references if not entry["exists"]]
    external_paths = _external_path_entries()
    missing_external_paths = [entry for entry in external_paths if not entry["exists"]]
    required_docs = _required_doc_entries()
    missing_required_docs = [entry for entry in required_docs if not entry["exists"]]
    doc_index_coverage = _doc_index_coverage_entries()
    missing_doc_index_entries = [
        entry for entry in doc_index_coverage if not entry["exists"]
    ]
    required_sections = _required_section_entries()
    missing_required_sections = [entry for entry in required_sections if not entry["exists"]]
    required_tokens = _required_token_entries()
    missing_required_tokens = [entry for entry in required_tokens if not entry["exists"]]
    example_fields = _request_example_field_entries()
    missing_example_fields = [
        entry for entry in example_fields if not entry["exists"] or not entry["has_value"]
    ]
    request_example_safety = _request_example_safety_entries()
    unsafe_request_examples = [
        entry for entry in request_example_safety if not entry["safe"]
    ]
    sample_target_manifest_entries = _sample_target_manifest_entries()
    missing_sample_target_manifest_entries = [
        entry for entry in sample_target_manifest_entries if not entry["listed"]
    ]
    route_matrix_sample_targets = _route_matrix_sample_target_entries()
    mismatched_route_matrix_sample_targets = [
        entry for entry in route_matrix_sample_targets if not entry["matches"]
    ]
    sample_manifest_route_targets = _sample_manifest_route_target_entries()
    mismatched_sample_manifest_route_targets = [
        entry for entry in sample_manifest_route_targets if not entry["matches"]
    ]
    route_matrix_first_commands = _route_matrix_any_token_entries(
        REQUEST_EXAMPLE_ROUTE_FIRST_COMMAND_RULES,
        "first_command",
    )
    mismatched_route_matrix_first_commands = [
        entry for entry in route_matrix_first_commands if not entry["matches"]
    ]
    route_matrix_verifications = _route_matrix_any_token_entries(
        REQUEST_EXAMPLE_ROUTE_VERIFICATION_RULES,
        "verification_command",
    )
    mismatched_route_matrix_verifications = [
        entry for entry in route_matrix_verifications if not entry["matches"]
    ]
    route_matrix_target_characters = _route_matrix_classification_entries(
        REQUEST_EXAMPLE_ROUTE_TARGET_CHARACTER_RULES,
        "target_character",
    )
    route_matrix_target_body_areas = _route_matrix_classification_entries(
        REQUEST_EXAMPLE_ROUTE_TARGET_BODY_AREA_RULES,
        "target_body_area",
    )
    route_matrix_timing_types = _route_matrix_classification_entries(
        REQUEST_EXAMPLE_ROUTE_TIMING_TYPE_RULES,
        "timing_type",
    )
    route_matrix_runtime_layers = _route_matrix_classification_entries(
        REQUEST_EXAMPLE_ROUTE_RUNTIME_LAYER_RULES,
        "runtime_layer",
    )
    mismatched_route_matrix_classification = [
        entry
        for entry in (
            route_matrix_target_characters
            + route_matrix_target_body_areas
            + route_matrix_timing_types
            + route_matrix_runtime_layers
        )
        if not entry["matches"]
    ]
    route_matrix_expected_evidence = _route_matrix_evidence_required_entries(
        REQUEST_EXAMPLE_ROUTE_EXPECTED_EVIDENCE_RULES,
        "expected_evidence",
    )
    route_matrix_cxx_statuses = _route_matrix_evidence_any_token_entries(
        REQUEST_EXAMPLE_ROUTE_CXX_STATUS_RULES,
        "cxx_api_status",
        lower_value=True,
    )
    route_matrix_approval_boundaries = _route_matrix_evidence_required_entries(
        REQUEST_EXAMPLE_ROUTE_ASK_USER_FIRST_RULES,
        "approval_boundary",
    )
    mismatched_route_matrix_evidence_approval = [
        entry
        for entry in (
            route_matrix_expected_evidence
            + route_matrix_cxx_statuses
            + route_matrix_approval_boundaries
        )
        if not entry["matches"]
    ]
    route_matrix_selection_rules = _route_matrix_selection_rule_entries()
    missing_route_matrix_selection_rules = [
        entry for entry in route_matrix_selection_rules if not entry["exists"]
    ]
    quickstart_route_shortcuts = _quickstart_route_shortcut_entries()
    missing_quickstart_route_shortcuts = [
        entry for entry in quickstart_route_shortcuts if not entry["exists"]
    ]
    quickstart_start_here = _quickstart_start_here_entries()
    missing_quickstart_start_here = [
        entry for entry in quickstart_start_here if not entry["exists"]
    ]
    quickstart_preflight_checklist = _quickstart_preflight_checklist_entries()
    missing_quickstart_preflight_checklist = [
        entry for entry in quickstart_preflight_checklist if not entry["exists"]
    ]
    doc_index_route_coverage = _doc_index_route_coverage_entries()
    missing_doc_index_route_coverage = [
        entry for entry in doc_index_route_coverage if not entry["exists"]
    ]
    doc_index_route_token_documents = _doc_index_route_token_document_entries()
    missing_doc_index_route_token_documents = [
        entry for entry in doc_index_route_token_documents if not entry["matches"]
    ]
    cpp_api_route_decisions = _cpp_api_route_decision_entries()
    mismatched_cpp_api_route_decisions = [
        entry for entry in cpp_api_route_decisions if not entry["matches"]
    ]
    cpp_api_candidate_matrix = _cpp_api_candidate_matrix_entries()
    missing_cpp_api_candidate_matrix = [
        entry for entry in cpp_api_candidate_matrix if not entry["exists"]
    ]
    handoff_route_map = _handoff_route_map_entries()
    mismatched_handoff_route_map = [
        entry for entry in handoff_route_map if not entry["matches"]
    ]
    request_example_route_coverage = _request_example_route_coverage_entries()
    missing_request_example_route_coverage = [
        entry for entry in request_example_route_coverage if not entry["exists"]
    ]
    request_compiler_route_coverage = _request_compiler_route_coverage_entries()
    missing_request_compiler_route_coverage = [
        entry for entry in request_compiler_route_coverage if not entry["exists"]
    ]
    request_example_route_handoffs = _request_example_route_handoff_entries()
    mismatched_request_example_route_handoffs = [
        entry
        for entry in request_example_route_handoffs
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_verifications = _request_example_route_verification_entries()
    mismatched_request_example_route_verifications = [
        entry
        for entry in request_example_route_verifications
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_first_commands = _request_example_route_first_command_entries()
    mismatched_request_example_route_first_commands = [
        entry
        for entry in request_example_route_first_commands
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_target_characters = _request_example_route_target_character_entries()
    mismatched_request_example_route_target_characters = [
        entry
        for entry in request_example_route_target_characters
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_target_body_areas = _request_example_route_target_body_area_entries()
    mismatched_request_example_route_target_body_areas = [
        entry
        for entry in request_example_route_target_body_areas
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_timing_types = _request_example_route_timing_type_entries()
    mismatched_request_example_route_timing_types = [
        entry
        for entry in request_example_route_timing_types
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_runtime_layers = _request_example_route_runtime_layer_entries()
    mismatched_request_example_route_runtime_layers = [
        entry
        for entry in request_example_route_runtime_layers
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_cxx_statuses = _request_example_route_cxx_status_entries()
    mismatched_request_example_route_cxx_statuses = [
        entry
        for entry in request_example_route_cxx_statuses
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_expected_evidence = _request_example_route_expected_evidence_entries()
    mismatched_request_example_route_expected_evidence = [
        entry
        for entry in request_example_route_expected_evidence
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_sample_targets = _request_example_route_sample_target_entries()
    mismatched_request_example_route_sample_targets = [
        entry
        for entry in request_example_route_sample_targets
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_ask_user_first = _request_example_route_ask_user_first_entries()
    mismatched_request_example_route_ask_user_first = [
        entry
        for entry in request_example_route_ask_user_first
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_matrix_checked = _request_example_route_matrix_checked_entries()
    mismatched_request_example_route_matrix_checked = [
        entry
        for entry in request_example_route_matrix_checked
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_token_document_map_checked = (
        _request_example_route_token_document_map_checked_entries()
    )
    mismatched_request_example_route_token_document_map_checked = [
        entry
        for entry in request_example_route_token_document_map_checked
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_token_acceptance_map_checked = (
        _request_example_route_token_acceptance_map_checked_entries()
    )
    mismatched_request_example_route_token_acceptance_map_checked = [
        entry
        for entry in request_example_route_token_acceptance_map_checked
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_route_matrix_notes = _request_example_route_matrix_notes_entries()
    mismatched_request_example_route_matrix_notes = [
        entry
        for entry in request_example_route_matrix_notes
        if not entry["known_route"] or not entry["matches"]
    ]
    request_example_acceptance_focus = _request_example_acceptance_focus_entries()
    missing_request_example_acceptance_focus = [
        entry
        for entry in request_example_acceptance_focus
        if not entry["exists"] or not entry["has_minimum_bullets"]
    ]
    request_example_route_acceptance_focus = _request_example_route_acceptance_focus_entries()
    mismatched_request_example_route_acceptance_focus = [
        entry
        for entry in request_example_route_acceptance_focus
        if not entry["known_route"] or not entry["matches"]
    ]
    request_run_template_fields = _request_run_template_field_entries()
    missing_request_run_template_fields = [
        entry for entry in request_run_template_fields if not entry["exists"]
    ]
    request_run_template_section_fields = _request_run_template_section_field_entries()
    missing_request_run_template_section_fields = [
        entry for entry in request_run_template_section_fields if not entry["exists"]
    ]
    request_run_template_acceptance_gates = _request_run_template_acceptance_gate_entries()
    missing_request_run_template_acceptance_gates = [
        entry for entry in request_run_template_acceptance_gates if not entry["exists"]
    ]
    playbook_delivery_shape_fields = _playbook_delivery_shape_field_entries()
    missing_playbook_delivery_shape_fields = [
        entry for entry in playbook_delivery_shape_fields if not entry["exists"]
    ]
    handoff_final_report_fields = _handoff_final_report_field_entries()
    missing_handoff_final_report_fields = [
        entry for entry in handoff_final_report_fields if not entry["exists"]
    ]
    handoff_route_token_final_reports = _handoff_route_token_final_report_entries()
    mismatched_handoff_route_token_final_reports = [
        entry for entry in handoff_route_token_final_reports if not entry["matches"]
    ]
    handoff_route_token_final_report_cxx = _handoff_route_token_final_report_cxx_entries()
    mismatched_handoff_route_token_final_report_cxx = [
        entry for entry in handoff_route_token_final_report_cxx if not entry["matches"]
    ]
    acceptance_final_report_fields = _acceptance_final_report_field_entries()
    missing_acceptance_final_report_fields = [
        entry for entry in acceptance_final_report_fields if not entry["exists"]
    ]
    acceptance_universal_pass_fields = _acceptance_universal_pass_field_entries()
    missing_acceptance_universal_pass_fields = [
        entry for entry in acceptance_universal_pass_fields if not entry["exists"]
    ]
    acceptance_completion_evidence = _acceptance_completion_evidence_entries()
    missing_acceptance_completion_evidence = [
        entry for entry in acceptance_completion_evidence if not entry["exists"]
    ]
    acceptance_route_criteria = _acceptance_route_criteria_entries()
    missing_acceptance_route_criteria = [
        entry for entry in acceptance_route_criteria if not entry["exists"]
    ]
    acceptance_route_tokens = _acceptance_route_token_entries()
    mismatched_acceptance_route_tokens = [
        entry for entry in acceptance_route_tokens if not entry["matches"]
    ]
    acceptance_evidence_strength_levels = _acceptance_evidence_strength_entries()
    missing_acceptance_evidence_strength_levels = [
        entry for entry in acceptance_evidence_strength_levels if not entry["exists"]
    ]
    acceptance_evidence_strength_details = _acceptance_evidence_strength_detail_entries()
    missing_acceptance_evidence_strength_details = [
        entry for entry in acceptance_evidence_strength_details if not entry["exists"]
    ]
    acceptance_escalation_triggers = _acceptance_escalation_trigger_entries()
    missing_acceptance_escalation_triggers = [
        entry for entry in acceptance_escalation_triggers if not entry["exists"]
    ]
    command_syntax_json_blocks = _command_syntax_json_blocks()
    invalid_command_syntax_json = [
        entry for entry in command_syntax_json_blocks if not entry["parse_success"]
    ]
    command_syntax_commands = _command_syntax_command_entries(command_syntax_json_blocks)
    missing_command_syntax_commands = [
        entry for entry in command_syntax_commands if not entry["exists"]
    ]
    command_quick_map_commands = _command_quick_map_command_entries()
    missing_command_quick_map_commands = [
        entry for entry in command_quick_map_commands if not entry["exists"]
    ]
    command_route_map = _command_route_map_entries()
    mismatched_command_route_map = [
        entry for entry in command_route_map if not entry["matches"]
    ]
    authoring_route_templates = _authoring_route_template_entries()
    mismatched_authoring_route_templates = [
        entry for entry in authoring_route_templates if not entry["matches"]
    ]
    playbook_route_map = _playbook_route_map_entries()
    mismatched_playbook_route_map = [
        entry for entry in playbook_route_map if not entry["matches"]
    ]
    playbook_route_failures = _playbook_route_failure_entries()
    mismatched_playbook_route_failures = [
        entry for entry in playbook_route_failures if not entry["matches"]
    ]
    playbook_route_failure_cxx = _playbook_route_failure_cxx_entries()
    mismatched_playbook_route_failure_cxx = [
        entry for entry in playbook_route_failure_cxx if not entry["matches"]
    ]
    animbp_authoring_pattern_routes = _animbp_authoring_pattern_route_entries()
    mismatched_animbp_authoring_pattern_routes = [
        entry
        for entry in animbp_authoring_pattern_routes
        if not entry["matches"]
    ]
    physics_route_tokens = _physics_route_token_entries()
    mismatched_physics_route_tokens = [
        entry for entry in physics_route_tokens if not entry["matches"]
    ]
    backlog_route_tokens = _backlog_route_token_entries()
    mismatched_backlog_route_tokens = [
        entry for entry in backlog_route_tokens if not entry["matches"]
    ]
    closeout_ready_route_tokens = _closeout_ready_route_token_entries()
    mismatched_closeout_ready_route_tokens = [
        entry for entry in closeout_ready_route_tokens if not entry["matches"]
    ]
    closeout_next_request_protocol = _closeout_next_request_protocol_entries()
    missing_closeout_next_request_protocol = [
        entry for entry in closeout_next_request_protocol if not entry["exists"]
    ]
    closeout_cxx_api_timing = _closeout_cxx_api_timing_entries()
    missing_closeout_cxx_api_timing = [
        entry for entry in closeout_cxx_api_timing if not entry["exists"]
    ]
    quickstart_route_tokens = _quickstart_route_token_entries()
    mismatched_quickstart_route_tokens = [
        entry for entry in quickstart_route_tokens if not entry["matches"]
    ]
    request_compiler_route_tokens = _request_compiler_route_token_entries()
    mismatched_request_compiler_route_tokens = [
        entry for entry in request_compiler_route_tokens if not entry["matches"]
    ]
    acceptance_route_token_map = _acceptance_route_token_map_entries()
    mismatched_acceptance_route_token_map = [
        entry for entry in acceptance_route_token_map if not entry["matches"]
    ]
    acceptance_route_token_min_strength = _acceptance_route_token_min_strength_entries()
    mismatched_acceptance_route_token_min_strength = [
        entry for entry in acceptance_route_token_min_strength if not entry["matches"]
    ]
    execution_evidence_route_tokens = _execution_evidence_route_token_entries()
    mismatched_execution_evidence_route_tokens = [
        entry for entry in execution_evidence_route_tokens if not entry["matches"]
    ]
    execution_evidence_sections = _execution_evidence_section_entries()
    missing_execution_evidence_sections = [
        entry for entry in execution_evidence_sections if not entry["matches"]
    ]
    command_syntax_result_checklist = _command_syntax_result_checklist_entries()
    missing_command_syntax_result_checklist = [
        entry for entry in command_syntax_result_checklist if not entry["exists"]
    ]
    local_check_runner_schemas = _local_check_runner_schema_entries()
    missing_local_check_runner_schemas = [
        entry for entry in local_check_runner_schemas if not entry["exists"]
    ]
    doc_index_local_check_commands = _doc_index_local_check_command_entries()
    missing_doc_index_local_check_commands = [
        entry for entry in doc_index_local_check_commands if not entry["exists"]
    ]
    preflight_required_commands = _preflight_required_command_entries()
    missing_preflight_required_commands = [
        entry for entry in preflight_required_commands if not entry["exists"]
    ]
    command_syntax_authoring_safety = _command_syntax_authoring_safety_entries(command_syntax_json_blocks)
    unsafe_command_syntax_authoring = [
        entry
        for entry in command_syntax_authoring_safety
        if not entry["exists"] or not entry["safe_value"]
    ]
    command_syntax_required_params = _command_syntax_required_param_entries(command_syntax_json_blocks)
    missing_command_syntax_required_params = [
        entry
        for entry in command_syntax_required_params
        if not entry["exists"] or not entry["has_value"]
    ]
    command_syntax_sample_paths = _command_syntax_sample_path_entries(command_syntax_json_blocks)
    unsafe_command_syntax_sample_paths = [
        entry
        for entry in command_syntax_sample_paths
        if not entry["exists"] or not entry["safe_value"]
    ]
    command_syntax_param_values = _command_syntax_param_value_entries(command_syntax_json_blocks)
    mismatched_command_syntax_param_values = [
        entry
        for entry in command_syntax_param_values
        if not entry["exists"] or not entry["matches"]
    ]
    pass_value = (
        not missing_references
        and not missing_external_paths
        and not missing_required_docs
        and not missing_doc_index_entries
        and not missing_required_sections
        and not missing_required_tokens
        and not missing_example_fields
        and not unsafe_request_examples
        and not missing_sample_target_manifest_entries
        and not mismatched_route_matrix_sample_targets
        and not mismatched_sample_manifest_route_targets
        and not mismatched_route_matrix_first_commands
        and not mismatched_route_matrix_verifications
        and not mismatched_route_matrix_classification
        and not mismatched_route_matrix_evidence_approval
        and not missing_route_matrix_selection_rules
        and not missing_quickstart_route_shortcuts
        and not missing_quickstart_start_here
        and not missing_quickstart_preflight_checklist
        and not missing_doc_index_route_coverage
        and not missing_doc_index_route_token_documents
        and not mismatched_cpp_api_route_decisions
        and not missing_cpp_api_candidate_matrix
        and not mismatched_handoff_route_map
        and not missing_request_example_route_coverage
        and not missing_request_compiler_route_coverage
        and not mismatched_request_example_route_handoffs
        and not mismatched_request_example_route_first_commands
        and not mismatched_request_example_route_target_characters
        and not mismatched_request_example_route_target_body_areas
        and not mismatched_request_example_route_timing_types
        and not mismatched_request_example_route_runtime_layers
        and not mismatched_request_example_route_cxx_statuses
        and not mismatched_request_example_route_expected_evidence
        and not mismatched_request_example_route_sample_targets
        and not mismatched_request_example_route_ask_user_first
        and not mismatched_request_example_route_matrix_checked
        and not mismatched_request_example_route_token_document_map_checked
        and not mismatched_request_example_route_token_acceptance_map_checked
        and not mismatched_request_example_route_matrix_notes
        and not mismatched_request_example_route_verifications
        and not missing_request_example_acceptance_focus
        and not mismatched_request_example_route_acceptance_focus
        and not missing_request_run_template_fields
        and not missing_request_run_template_section_fields
        and not missing_request_run_template_acceptance_gates
        and not missing_playbook_delivery_shape_fields
        and not missing_handoff_final_report_fields
        and not mismatched_handoff_route_token_final_reports
        and not mismatched_handoff_route_token_final_report_cxx
        and not missing_acceptance_final_report_fields
        and not missing_acceptance_universal_pass_fields
        and not missing_acceptance_completion_evidence
        and not missing_acceptance_route_criteria
        and not mismatched_acceptance_route_tokens
        and not missing_acceptance_evidence_strength_levels
        and not missing_acceptance_evidence_strength_details
        and not missing_acceptance_escalation_triggers
        and not invalid_command_syntax_json
        and not missing_command_syntax_commands
        and not missing_command_quick_map_commands
        and not mismatched_command_route_map
        and not mismatched_authoring_route_templates
        and not mismatched_playbook_route_map
        and not mismatched_playbook_route_failures
        and not mismatched_playbook_route_failure_cxx
        and not mismatched_animbp_authoring_pattern_routes
        and not mismatched_physics_route_tokens
        and not mismatched_backlog_route_tokens
        and not mismatched_closeout_ready_route_tokens
        and not missing_closeout_next_request_protocol
        and not missing_closeout_cxx_api_timing
        and not mismatched_quickstart_route_tokens
        and not mismatched_request_compiler_route_tokens
        and not mismatched_acceptance_route_token_map
        and not mismatched_acceptance_route_token_min_strength
        and not mismatched_execution_evidence_route_tokens
        and not missing_execution_evidence_sections
        and not missing_command_syntax_result_checklist
        and not missing_local_check_runner_schemas
        and not missing_doc_index_local_check_commands
        and not missing_preflight_required_commands
        and not unsafe_command_syntax_authoring
        and not missing_command_syntax_required_params
        and not unsafe_command_syntax_sample_paths
        and not mismatched_command_syntax_param_values
    )

    report = {
        "schema": DOCS_AUDIT_SCHEMA,
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": PROJECT_ROOT.as_posix(),
        "doc_glob": args.glob,
        "doc_count": len(docs),
        "reference_count": len(references),
        "missing_reference_count": len(missing_references),
        "missing_external_path_count": len(missing_external_paths),
        "missing_required_doc_count": len(missing_required_docs),
        "missing_doc_index_entry_count": len(missing_doc_index_entries),
        "missing_required_section_count": len(missing_required_sections),
        "missing_required_token_count": len(missing_required_tokens),
        "missing_example_field_count": len(missing_example_fields),
        "unsafe_request_example_count": len(unsafe_request_examples),
        "missing_sample_target_manifest_count": len(missing_sample_target_manifest_entries),
        "mismatched_route_matrix_sample_target_count": len(mismatched_route_matrix_sample_targets),
        "mismatched_sample_manifest_route_target_count": len(mismatched_sample_manifest_route_targets),
        "mismatched_route_matrix_first_command_count": len(mismatched_route_matrix_first_commands),
        "mismatched_route_matrix_verification_count": len(mismatched_route_matrix_verifications),
        "mismatched_route_matrix_classification_count": len(mismatched_route_matrix_classification),
        "mismatched_route_matrix_evidence_approval_count": len(mismatched_route_matrix_evidence_approval),
        "missing_route_matrix_selection_rule_count": len(missing_route_matrix_selection_rules),
        "missing_quickstart_route_shortcut_count": len(missing_quickstart_route_shortcuts),
        "missing_quickstart_start_here_count": len(missing_quickstart_start_here),
        "missing_quickstart_preflight_checklist_count": len(missing_quickstart_preflight_checklist),
        "missing_doc_index_route_coverage_count": len(missing_doc_index_route_coverage),
        "missing_doc_index_route_token_document_count": len(missing_doc_index_route_token_documents),
        "mismatched_cpp_api_route_decision_count": len(mismatched_cpp_api_route_decisions),
        "missing_cpp_api_candidate_matrix_count": len(missing_cpp_api_candidate_matrix),
        "mismatched_handoff_route_map_count": len(mismatched_handoff_route_map),
        "missing_request_example_route_coverage_count": len(missing_request_example_route_coverage),
        "missing_request_compiler_route_coverage_count": len(missing_request_compiler_route_coverage),
        "mismatched_request_example_route_handoff_count": len(mismatched_request_example_route_handoffs),
        "mismatched_request_example_route_first_command_count": len(mismatched_request_example_route_first_commands),
        "mismatched_request_example_route_target_character_count": len(mismatched_request_example_route_target_characters),
        "mismatched_request_example_route_target_body_area_count": len(mismatched_request_example_route_target_body_areas),
        "mismatched_request_example_route_timing_type_count": len(mismatched_request_example_route_timing_types),
        "mismatched_request_example_route_runtime_layer_count": len(mismatched_request_example_route_runtime_layers),
        "mismatched_request_example_route_cxx_status_count": len(mismatched_request_example_route_cxx_statuses),
        "mismatched_request_example_route_expected_evidence_count": len(mismatched_request_example_route_expected_evidence),
        "mismatched_request_example_route_sample_target_count": len(mismatched_request_example_route_sample_targets),
        "mismatched_request_example_route_ask_user_first_count": len(mismatched_request_example_route_ask_user_first),
        "mismatched_request_example_route_matrix_checked_count": len(mismatched_request_example_route_matrix_checked),
        "mismatched_request_example_route_token_document_map_checked_count": len(mismatched_request_example_route_token_document_map_checked),
        "mismatched_request_example_route_token_acceptance_map_checked_count": len(mismatched_request_example_route_token_acceptance_map_checked),
        "mismatched_request_example_route_matrix_note_count": len(mismatched_request_example_route_matrix_notes),
        "mismatched_request_example_route_verification_count": len(mismatched_request_example_route_verifications),
        "missing_request_example_acceptance_focus_count": len(missing_request_example_acceptance_focus),
        "mismatched_request_example_route_acceptance_focus_count": len(mismatched_request_example_route_acceptance_focus),
        "missing_request_run_template_field_count": len(missing_request_run_template_fields),
        "missing_request_run_template_section_field_count": len(missing_request_run_template_section_fields),
        "missing_request_run_template_acceptance_gate_count": len(missing_request_run_template_acceptance_gates),
        "missing_playbook_delivery_shape_field_count": len(missing_playbook_delivery_shape_fields),
        "missing_handoff_final_report_field_count": len(missing_handoff_final_report_fields),
        "mismatched_handoff_route_token_final_report_count": len(mismatched_handoff_route_token_final_reports),
        "mismatched_handoff_route_token_final_report_cxx_count": len(mismatched_handoff_route_token_final_report_cxx),
        "missing_acceptance_final_report_field_count": len(missing_acceptance_final_report_fields),
        "missing_acceptance_universal_pass_field_count": len(missing_acceptance_universal_pass_fields),
        "missing_acceptance_completion_evidence_count": len(missing_acceptance_completion_evidence),
        "missing_acceptance_route_criteria_count": len(missing_acceptance_route_criteria),
        "mismatched_acceptance_route_token_count": len(mismatched_acceptance_route_tokens),
        "missing_acceptance_evidence_strength_level_count": len(missing_acceptance_evidence_strength_levels),
        "missing_acceptance_evidence_strength_detail_count": len(missing_acceptance_evidence_strength_details),
        "missing_acceptance_escalation_trigger_count": len(missing_acceptance_escalation_triggers),
        "invalid_command_syntax_json_count": len(invalid_command_syntax_json),
        "missing_command_syntax_command_count": len(missing_command_syntax_commands),
        "missing_command_quick_map_command_count": len(missing_command_quick_map_commands),
        "mismatched_command_route_map_count": len(mismatched_command_route_map),
        "mismatched_authoring_route_template_count": len(mismatched_authoring_route_templates),
        "mismatched_playbook_route_map_count": len(mismatched_playbook_route_map),
        "mismatched_playbook_route_failure_count": len(mismatched_playbook_route_failures),
        "mismatched_playbook_route_failure_cxx_count": len(mismatched_playbook_route_failure_cxx),
        "mismatched_animbp_authoring_pattern_route_count": len(mismatched_animbp_authoring_pattern_routes),
        "mismatched_physics_route_token_count": len(mismatched_physics_route_tokens),
        "mismatched_backlog_route_token_count": len(mismatched_backlog_route_tokens),
        "mismatched_closeout_ready_route_token_count": len(mismatched_closeout_ready_route_tokens),
        "missing_closeout_next_request_protocol_count": len(missing_closeout_next_request_protocol),
        "missing_closeout_cxx_api_timing_count": len(missing_closeout_cxx_api_timing),
        "mismatched_quickstart_route_token_count": len(mismatched_quickstart_route_tokens),
        "mismatched_request_compiler_route_token_count": len(mismatched_request_compiler_route_tokens),
        "mismatched_acceptance_route_token_map_count": len(mismatched_acceptance_route_token_map),
        "mismatched_acceptance_route_token_min_strength_count": len(mismatched_acceptance_route_token_min_strength),
        "mismatched_execution_evidence_route_token_count": len(mismatched_execution_evidence_route_tokens),
        "missing_execution_evidence_section_count": len(missing_execution_evidence_sections),
        "missing_command_syntax_result_checklist_count": len(missing_command_syntax_result_checklist),
        "missing_local_check_runner_schema_count": len(missing_local_check_runner_schemas),
        "missing_doc_index_local_check_command_count": len(missing_doc_index_local_check_commands),
        "missing_preflight_required_command_count": len(missing_preflight_required_commands),
        "unsafe_command_syntax_authoring_count": len(unsafe_command_syntax_authoring),
        "missing_command_syntax_required_param_count": len(missing_command_syntax_required_params),
        "unsafe_command_syntax_sample_path_count": len(unsafe_command_syntax_sample_paths),
        "mismatched_command_syntax_param_value_count": len(mismatched_command_syntax_param_values),
        "pass": pass_value,
        "docs": [_project_relative(path) for path in docs],
        "missing_references": missing_references,
        "external_paths": external_paths,
        "missing_required_docs": missing_required_docs,
        "doc_index_coverage": doc_index_coverage,
        "missing_doc_index_entries": missing_doc_index_entries,
        "missing_required_sections": missing_required_sections,
        "missing_required_tokens": missing_required_tokens,
        "example_fields": example_fields,
        "missing_example_fields": missing_example_fields,
        "request_example_safety": request_example_safety,
        "unsafe_request_examples": unsafe_request_examples,
        "sample_target_manifest_entries": sample_target_manifest_entries,
        "missing_sample_target_manifest_entries": missing_sample_target_manifest_entries,
        "route_matrix_sample_targets": route_matrix_sample_targets,
        "mismatched_route_matrix_sample_targets": mismatched_route_matrix_sample_targets,
        "sample_manifest_route_targets": sample_manifest_route_targets,
        "mismatched_sample_manifest_route_targets": mismatched_sample_manifest_route_targets,
        "route_matrix_first_commands": route_matrix_first_commands,
        "mismatched_route_matrix_first_commands": mismatched_route_matrix_first_commands,
        "route_matrix_verifications": route_matrix_verifications,
        "mismatched_route_matrix_verifications": mismatched_route_matrix_verifications,
        "route_matrix_target_characters": route_matrix_target_characters,
        "route_matrix_target_body_areas": route_matrix_target_body_areas,
        "route_matrix_timing_types": route_matrix_timing_types,
        "route_matrix_runtime_layers": route_matrix_runtime_layers,
        "mismatched_route_matrix_classification": mismatched_route_matrix_classification,
        "route_matrix_expected_evidence": route_matrix_expected_evidence,
        "route_matrix_cxx_statuses": route_matrix_cxx_statuses,
        "route_matrix_approval_boundaries": route_matrix_approval_boundaries,
        "mismatched_route_matrix_evidence_approval": mismatched_route_matrix_evidence_approval,
        "route_matrix_selection_rules": route_matrix_selection_rules,
        "missing_route_matrix_selection_rules": missing_route_matrix_selection_rules,
        "quickstart_route_shortcuts": quickstart_route_shortcuts,
        "missing_quickstart_route_shortcuts": missing_quickstart_route_shortcuts,
        "quickstart_start_here": quickstart_start_here,
        "missing_quickstart_start_here": missing_quickstart_start_here,
        "quickstart_preflight_checklist": quickstart_preflight_checklist,
        "missing_quickstart_preflight_checklist": missing_quickstart_preflight_checklist,
        "doc_index_route_coverage": doc_index_route_coverage,
        "missing_doc_index_route_coverage": missing_doc_index_route_coverage,
        "doc_index_route_token_documents": doc_index_route_token_documents,
        "missing_doc_index_route_token_documents": missing_doc_index_route_token_documents,
        "cpp_api_route_decisions": cpp_api_route_decisions,
        "mismatched_cpp_api_route_decisions": mismatched_cpp_api_route_decisions,
        "cpp_api_candidate_matrix": cpp_api_candidate_matrix,
        "missing_cpp_api_candidate_matrix": missing_cpp_api_candidate_matrix,
        "handoff_route_map": handoff_route_map,
        "mismatched_handoff_route_map": mismatched_handoff_route_map,
        "request_example_route_coverage": request_example_route_coverage,
        "missing_request_example_route_coverage": missing_request_example_route_coverage,
        "request_compiler_route_coverage": request_compiler_route_coverage,
        "missing_request_compiler_route_coverage": missing_request_compiler_route_coverage,
        "request_example_route_handoffs": request_example_route_handoffs,
        "mismatched_request_example_route_handoffs": mismatched_request_example_route_handoffs,
        "request_example_route_first_commands": request_example_route_first_commands,
        "mismatched_request_example_route_first_commands": mismatched_request_example_route_first_commands,
        "request_example_route_target_characters": request_example_route_target_characters,
        "mismatched_request_example_route_target_characters": mismatched_request_example_route_target_characters,
        "request_example_route_target_body_areas": request_example_route_target_body_areas,
        "mismatched_request_example_route_target_body_areas": mismatched_request_example_route_target_body_areas,
        "request_example_route_timing_types": request_example_route_timing_types,
        "mismatched_request_example_route_timing_types": mismatched_request_example_route_timing_types,
        "request_example_route_runtime_layers": request_example_route_runtime_layers,
        "mismatched_request_example_route_runtime_layers": mismatched_request_example_route_runtime_layers,
        "request_example_route_cxx_statuses": request_example_route_cxx_statuses,
        "mismatched_request_example_route_cxx_statuses": mismatched_request_example_route_cxx_statuses,
        "request_example_route_expected_evidence": request_example_route_expected_evidence,
        "mismatched_request_example_route_expected_evidence": mismatched_request_example_route_expected_evidence,
        "request_example_route_sample_targets": request_example_route_sample_targets,
        "mismatched_request_example_route_sample_targets": mismatched_request_example_route_sample_targets,
        "request_example_route_ask_user_first": request_example_route_ask_user_first,
        "mismatched_request_example_route_ask_user_first": mismatched_request_example_route_ask_user_first,
        "request_example_route_matrix_checked": request_example_route_matrix_checked,
        "mismatched_request_example_route_matrix_checked": mismatched_request_example_route_matrix_checked,
        "request_example_route_token_document_map_checked": request_example_route_token_document_map_checked,
        "mismatched_request_example_route_token_document_map_checked": mismatched_request_example_route_token_document_map_checked,
        "request_example_route_token_acceptance_map_checked": request_example_route_token_acceptance_map_checked,
        "mismatched_request_example_route_token_acceptance_map_checked": mismatched_request_example_route_token_acceptance_map_checked,
        "request_example_route_matrix_notes": request_example_route_matrix_notes,
        "mismatched_request_example_route_matrix_notes": mismatched_request_example_route_matrix_notes,
        "request_example_route_verifications": request_example_route_verifications,
        "mismatched_request_example_route_verifications": mismatched_request_example_route_verifications,
        "request_example_acceptance_focus": request_example_acceptance_focus,
        "missing_request_example_acceptance_focus": missing_request_example_acceptance_focus,
        "request_example_route_acceptance_focus": request_example_route_acceptance_focus,
        "mismatched_request_example_route_acceptance_focus": mismatched_request_example_route_acceptance_focus,
        "request_run_template_fields": request_run_template_fields,
        "missing_request_run_template_fields": missing_request_run_template_fields,
        "request_run_template_section_fields": request_run_template_section_fields,
        "missing_request_run_template_section_fields": missing_request_run_template_section_fields,
        "request_run_template_acceptance_gates": request_run_template_acceptance_gates,
        "missing_request_run_template_acceptance_gates": missing_request_run_template_acceptance_gates,
        "playbook_delivery_shape_fields": playbook_delivery_shape_fields,
        "missing_playbook_delivery_shape_fields": missing_playbook_delivery_shape_fields,
        "handoff_final_report_fields": handoff_final_report_fields,
        "missing_handoff_final_report_fields": missing_handoff_final_report_fields,
        "handoff_route_token_final_reports": handoff_route_token_final_reports,
        "mismatched_handoff_route_token_final_reports": mismatched_handoff_route_token_final_reports,
        "handoff_route_token_final_report_cxx": handoff_route_token_final_report_cxx,
        "mismatched_handoff_route_token_final_report_cxx": mismatched_handoff_route_token_final_report_cxx,
        "acceptance_final_report_fields": acceptance_final_report_fields,
        "missing_acceptance_final_report_fields": missing_acceptance_final_report_fields,
        "acceptance_universal_pass_fields": acceptance_universal_pass_fields,
        "missing_acceptance_universal_pass_fields": missing_acceptance_universal_pass_fields,
        "acceptance_completion_evidence": acceptance_completion_evidence,
        "missing_acceptance_completion_evidence": missing_acceptance_completion_evidence,
        "acceptance_route_criteria": acceptance_route_criteria,
        "missing_acceptance_route_criteria": missing_acceptance_route_criteria,
        "acceptance_route_tokens": acceptance_route_tokens,
        "mismatched_acceptance_route_tokens": mismatched_acceptance_route_tokens,
        "acceptance_evidence_strength_levels": acceptance_evidence_strength_levels,
        "missing_acceptance_evidence_strength_levels": missing_acceptance_evidence_strength_levels,
        "acceptance_evidence_strength_details": acceptance_evidence_strength_details,
        "missing_acceptance_evidence_strength_details": missing_acceptance_evidence_strength_details,
        "acceptance_escalation_triggers": acceptance_escalation_triggers,
        "missing_acceptance_escalation_triggers": missing_acceptance_escalation_triggers,
        "command_syntax_json_blocks": command_syntax_json_blocks,
        "invalid_command_syntax_json": invalid_command_syntax_json,
        "command_syntax_commands": command_syntax_commands,
        "missing_command_syntax_commands": missing_command_syntax_commands,
        "command_quick_map_commands": command_quick_map_commands,
        "missing_command_quick_map_commands": missing_command_quick_map_commands,
        "command_route_map": command_route_map,
        "mismatched_command_route_map": mismatched_command_route_map,
        "authoring_route_templates": authoring_route_templates,
        "mismatched_authoring_route_templates": mismatched_authoring_route_templates,
        "playbook_route_map": playbook_route_map,
        "mismatched_playbook_route_map": mismatched_playbook_route_map,
        "playbook_route_failures": playbook_route_failures,
        "mismatched_playbook_route_failures": mismatched_playbook_route_failures,
        "playbook_route_failure_cxx": playbook_route_failure_cxx,
        "mismatched_playbook_route_failure_cxx": mismatched_playbook_route_failure_cxx,
        "animbp_authoring_pattern_routes": animbp_authoring_pattern_routes,
        "mismatched_animbp_authoring_pattern_routes": mismatched_animbp_authoring_pattern_routes,
        "physics_route_tokens": physics_route_tokens,
        "mismatched_physics_route_tokens": mismatched_physics_route_tokens,
        "backlog_route_tokens": backlog_route_tokens,
        "mismatched_backlog_route_tokens": mismatched_backlog_route_tokens,
        "closeout_ready_route_tokens": closeout_ready_route_tokens,
        "mismatched_closeout_ready_route_tokens": mismatched_closeout_ready_route_tokens,
        "closeout_next_request_protocol": closeout_next_request_protocol,
        "missing_closeout_next_request_protocol": missing_closeout_next_request_protocol,
        "closeout_cxx_api_timing": closeout_cxx_api_timing,
        "missing_closeout_cxx_api_timing": missing_closeout_cxx_api_timing,
        "quickstart_route_tokens": quickstart_route_tokens,
        "mismatched_quickstart_route_tokens": mismatched_quickstart_route_tokens,
        "request_compiler_route_tokens": request_compiler_route_tokens,
        "mismatched_request_compiler_route_tokens": mismatched_request_compiler_route_tokens,
        "acceptance_route_token_map": acceptance_route_token_map,
        "mismatched_acceptance_route_token_map": mismatched_acceptance_route_token_map,
        "acceptance_route_token_min_strength": acceptance_route_token_min_strength,
        "mismatched_acceptance_route_token_min_strength": mismatched_acceptance_route_token_min_strength,
        "execution_evidence_route_tokens": execution_evidence_route_tokens,
        "mismatched_execution_evidence_route_tokens": mismatched_execution_evidence_route_tokens,
        "execution_evidence_sections": execution_evidence_sections,
        "missing_execution_evidence_sections": missing_execution_evidence_sections,
        "command_syntax_result_checklist": command_syntax_result_checklist,
        "missing_command_syntax_result_checklist": missing_command_syntax_result_checklist,
        "local_check_runner_schemas": local_check_runner_schemas,
        "missing_local_check_runner_schemas": missing_local_check_runner_schemas,
        "doc_index_local_check_commands": doc_index_local_check_commands,
        "missing_doc_index_local_check_commands": missing_doc_index_local_check_commands,
        "preflight_required_commands": preflight_required_commands,
        "missing_preflight_required_commands": missing_preflight_required_commands,
        "command_syntax_authoring_safety": command_syntax_authoring_safety,
        "unsafe_command_syntax_authoring": unsafe_command_syntax_authoring,
        "command_syntax_required_params": command_syntax_required_params,
        "missing_command_syntax_required_params": missing_command_syntax_required_params,
        "command_syntax_sample_paths": command_syntax_sample_paths,
        "unsafe_command_syntax_sample_paths": unsafe_command_syntax_sample_paths,
        "command_syntax_param_values": command_syntax_param_values,
        "mismatched_command_syntax_param_values": mismatched_command_syntax_param_values,
    }

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = _project_relative(REPORT_PATH)

    return report


def _format_summary(report: dict[str, Any]) -> str:
    status = "PASS" if report["pass"] else "FAIL"
    lines = [
        f"StackOBot animation docs check: {status}",
        (
            f"schema={report['schema']} docs={report['doc_count']} refs={report['reference_count']} "
            f"missing_refs={report['missing_reference_count']} "
            f"missing_external={report['missing_external_path_count']} "
            f"missing_required_docs={report['missing_required_doc_count']} "
            f"missing_doc_index_entries={report['missing_doc_index_entry_count']} "
            f"missing_required_sections={report['missing_required_section_count']} "
            f"missing_required_tokens={report['missing_required_token_count']} "
            f"missing_example_fields={report['missing_example_field_count']} "
            f"unsafe_request_examples={report['unsafe_request_example_count']} "
            f"missing_sample_target_manifest={report['missing_sample_target_manifest_count']} "
            f"mismatched_route_matrix_sample_targets={report['mismatched_route_matrix_sample_target_count']} "
            f"mismatched_sample_manifest_route_targets={report['mismatched_sample_manifest_route_target_count']} "
            f"mismatched_route_matrix_first_commands={report['mismatched_route_matrix_first_command_count']} "
            f"mismatched_route_matrix_verifications={report['mismatched_route_matrix_verification_count']} "
            f"mismatched_route_matrix_classification={report['mismatched_route_matrix_classification_count']} "
            f"mismatched_route_matrix_evidence_approval={report['mismatched_route_matrix_evidence_approval_count']} "
            f"missing_route_matrix_selection_rules={report['missing_route_matrix_selection_rule_count']} "
            f"missing_quickstart_route_shortcuts={report['missing_quickstart_route_shortcut_count']} "
            f"missing_quickstart_start_here={report['missing_quickstart_start_here_count']} "
            f"missing_quickstart_preflight_checklist={report['missing_quickstart_preflight_checklist_count']} "
            f"missing_doc_index_route_coverage={report['missing_doc_index_route_coverage_count']} "
            f"missing_doc_index_route_token_documents={report['missing_doc_index_route_token_document_count']} "
            f"mismatched_cpp_api_route_decisions={report['mismatched_cpp_api_route_decision_count']} "
            f"missing_cpp_api_candidate_matrix={report['missing_cpp_api_candidate_matrix_count']} "
            f"mismatched_handoff_route_map={report['mismatched_handoff_route_map_count']} "
            f"missing_request_example_routes={report['missing_request_example_route_coverage_count']} "
            f"missing_request_compiler_routes={report['missing_request_compiler_route_coverage_count']} "
            f"mismatched_request_example_route_handoffs={report['mismatched_request_example_route_handoff_count']} "
            f"mismatched_request_example_first_commands={report['mismatched_request_example_route_first_command_count']} "
            f"mismatched_request_example_target_characters={report['mismatched_request_example_route_target_character_count']} "
            f"mismatched_request_example_target_body_areas={report['mismatched_request_example_route_target_body_area_count']} "
            f"mismatched_request_example_timing_types={report['mismatched_request_example_route_timing_type_count']} "
            f"mismatched_request_example_runtime_layers={report['mismatched_request_example_route_runtime_layer_count']} "
            f"mismatched_request_example_cxx_status={report['mismatched_request_example_route_cxx_status_count']} "
            f"mismatched_request_example_expected_evidence={report['mismatched_request_example_route_expected_evidence_count']} "
            f"mismatched_request_example_sample_targets={report['mismatched_request_example_route_sample_target_count']} "
            f"mismatched_request_example_ask_user_first={report['mismatched_request_example_route_ask_user_first_count']} "
            f"mismatched_request_example_route_matrix_checked={report['mismatched_request_example_route_matrix_checked_count']} "
            f"mismatched_request_example_route_token_document_map_checked={report['mismatched_request_example_route_token_document_map_checked_count']} "
            f"mismatched_request_example_route_token_acceptance_map_checked={report['mismatched_request_example_route_token_acceptance_map_checked_count']} "
            f"mismatched_request_example_route_matrix_notes={report['mismatched_request_example_route_matrix_note_count']} "
            f"mismatched_request_example_verification_commands={report['mismatched_request_example_route_verification_count']} "
            f"missing_acceptance_focus_blocks={report['missing_request_example_acceptance_focus_count']} "
            f"mismatched_acceptance_focus_tokens={report['mismatched_request_example_route_acceptance_focus_count']} "
            f"missing_template_fields={report['missing_request_run_template_field_count']} "
            f"missing_request_template_section_fields={report['missing_request_run_template_section_field_count']} "
            f"missing_request_template_acceptance_gates={report['missing_request_run_template_acceptance_gate_count']} "
            f"missing_playbook_delivery_shape_fields={report['missing_playbook_delivery_shape_field_count']} "
            f"missing_handoff_report_fields={report['missing_handoff_final_report_field_count']} "
            f"mismatched_handoff_route_token_final_reports={report['mismatched_handoff_route_token_final_report_count']} "
            f"mismatched_handoff_route_token_final_report_cxx={report['mismatched_handoff_route_token_final_report_cxx_count']} "
            f"missing_acceptance_report_fields={report['missing_acceptance_final_report_field_count']} "
            f"missing_acceptance_universal_fields={report['missing_acceptance_universal_pass_field_count']} "
            f"missing_acceptance_completion_evidence={report['missing_acceptance_completion_evidence_count']} "
            f"missing_acceptance_routes={report['missing_acceptance_route_criteria_count']} "
            f"mismatched_acceptance_route_tokens={report['mismatched_acceptance_route_token_count']} "
            f"missing_evidence_strength_levels={report['missing_acceptance_evidence_strength_level_count']} "
            f"missing_evidence_strength_details={report['missing_acceptance_evidence_strength_detail_count']} "
            f"missing_acceptance_escalation_triggers={report['missing_acceptance_escalation_trigger_count']} "
            f"invalid_command_json={report['invalid_command_syntax_json_count']} "
            f"missing_command_examples={report['missing_command_syntax_command_count']} "
            f"missing_quick_map_commands={report['missing_command_quick_map_command_count']} "
            f"mismatched_command_route_map={report['mismatched_command_route_map_count']} "
            f"mismatched_authoring_route_templates={report['mismatched_authoring_route_template_count']} "
            f"mismatched_playbook_route_map={report['mismatched_playbook_route_map_count']} "
            f"mismatched_playbook_route_failures={report['mismatched_playbook_route_failure_count']} "
            f"mismatched_playbook_route_failure_cxx={report['mismatched_playbook_route_failure_cxx_count']} "
            f"mismatched_animbp_authoring_patterns={report['mismatched_animbp_authoring_pattern_route_count']} "
            f"mismatched_physics_route_tokens={report['mismatched_physics_route_token_count']} "
            f"mismatched_backlog_route_tokens={report['mismatched_backlog_route_token_count']} "
            f"mismatched_closeout_ready_routes={report['mismatched_closeout_ready_route_token_count']} "
            f"missing_closeout_next_request_protocol={report['missing_closeout_next_request_protocol_count']} "
            f"missing_closeout_cxx_api_timing={report['missing_closeout_cxx_api_timing_count']} "
            f"mismatched_quickstart_route_tokens={report['mismatched_quickstart_route_token_count']} "
            f"mismatched_request_compiler_route_tokens={report['mismatched_request_compiler_route_token_count']} "
            f"mismatched_acceptance_route_token_map={report['mismatched_acceptance_route_token_map_count']} "
            f"mismatched_acceptance_route_token_min_strength={report['mismatched_acceptance_route_token_min_strength_count']} "
            f"mismatched_execution_evidence_route_tokens={report['mismatched_execution_evidence_route_token_count']} "
            f"missing_execution_evidence_sections={report['missing_execution_evidence_section_count']} "
            f"missing_command_result_checklist={report['missing_command_syntax_result_checklist_count']} "
            f"missing_local_check_runner_schemas={report['missing_local_check_runner_schema_count']} "
            f"missing_doc_index_local_check_commands={report['missing_doc_index_local_check_command_count']} "
            f"missing_preflight_required_commands={report['missing_preflight_required_command_count']} "
            f"unsafe_authoring_examples={report['unsafe_command_syntax_authoring_count']} "
            f"missing_command_params={report['missing_command_syntax_required_param_count']} "
            f"unsafe_command_paths={report['unsafe_command_syntax_sample_path_count']} "
            f"mismatched_command_param_values={report['mismatched_command_syntax_param_value_count']}"
        ),
    ]
    if report.get("report_path"):
        lines.append(f"report={report['report_path']}")
    if not report["pass"]:
        for key in [
            "missing_references",
            "missing_required_docs",
            "missing_doc_index_entries",
            "missing_required_sections",
            "missing_required_tokens",
            "missing_example_fields",
            "unsafe_request_examples",
            "missing_sample_target_manifest_entries",
            "mismatched_route_matrix_sample_targets",
            "mismatched_sample_manifest_route_targets",
            "mismatched_route_matrix_first_commands",
            "mismatched_route_matrix_verifications",
            "mismatched_route_matrix_classification",
            "mismatched_route_matrix_evidence_approval",
            "missing_route_matrix_selection_rules",
            "missing_quickstart_route_shortcuts",
            "missing_quickstart_start_here",
            "missing_quickstart_preflight_checklist",
            "missing_doc_index_route_coverage",
            "missing_doc_index_route_token_documents",
            "mismatched_cpp_api_route_decisions",
            "missing_cpp_api_candidate_matrix",
            "mismatched_handoff_route_map",
            "missing_request_example_route_coverage",
            "missing_request_compiler_route_coverage",
            "mismatched_request_example_route_handoffs",
            "mismatched_request_example_route_first_commands",
            "mismatched_request_example_route_target_characters",
            "mismatched_request_example_route_target_body_areas",
            "mismatched_request_example_route_timing_types",
            "mismatched_request_example_route_runtime_layers",
            "mismatched_request_example_route_cxx_statuses",
            "mismatched_request_example_route_expected_evidence",
            "mismatched_request_example_route_sample_targets",
            "mismatched_request_example_route_ask_user_first",
            "mismatched_request_example_route_matrix_checked",
            "mismatched_request_example_route_token_document_map_checked",
            "mismatched_request_example_route_token_acceptance_map_checked",
            "mismatched_request_example_route_matrix_notes",
            "mismatched_request_example_route_verifications",
            "missing_request_example_acceptance_focus",
            "mismatched_request_example_route_acceptance_focus",
            "missing_request_run_template_fields",
            "missing_request_run_template_section_fields",
            "missing_request_run_template_acceptance_gates",
            "missing_playbook_delivery_shape_fields",
            "missing_handoff_final_report_fields",
            "mismatched_handoff_route_token_final_reports",
            "mismatched_handoff_route_token_final_report_cxx",
            "missing_acceptance_final_report_fields",
            "missing_acceptance_universal_pass_fields",
            "missing_acceptance_completion_evidence",
            "missing_acceptance_route_criteria",
            "mismatched_acceptance_route_tokens",
            "missing_acceptance_evidence_strength_levels",
            "missing_acceptance_evidence_strength_details",
            "missing_acceptance_escalation_triggers",
            "invalid_command_syntax_json",
            "missing_command_syntax_commands",
            "missing_command_quick_map_commands",
            "mismatched_command_route_map",
            "mismatched_authoring_route_templates",
            "mismatched_playbook_route_map",
            "mismatched_playbook_route_failures",
            "mismatched_playbook_route_failure_cxx",
            "mismatched_animbp_authoring_pattern_routes",
            "mismatched_physics_route_tokens",
            "mismatched_backlog_route_tokens",
            "mismatched_closeout_ready_route_tokens",
            "missing_closeout_next_request_protocol",
            "missing_closeout_cxx_api_timing",
            "mismatched_quickstart_route_tokens",
            "mismatched_request_compiler_route_tokens",
            "mismatched_acceptance_route_token_map",
            "mismatched_acceptance_route_token_min_strength",
            "mismatched_execution_evidence_route_tokens",
            "missing_execution_evidence_sections",
            "missing_command_syntax_result_checklist",
            "missing_local_check_runner_schemas",
            "missing_doc_index_local_check_commands",
            "missing_preflight_required_commands",
            "unsafe_command_syntax_authoring",
            "missing_command_syntax_required_params",
            "unsafe_command_syntax_sample_paths",
            "mismatched_command_syntax_param_values",
        ]:
            entries = report.get(key) or []
            if entries:
                lines.append(f"{key}:")
                for entry in entries[:10]:
                    lines.append(f"  - {entry}")
                if len(entries) > 10:
                    lines.append(f"  ... {len(entries) - 10} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--glob",
        default=STACKOBOT_DOC_GLOB,
        help="Documentation glob under docs/ to scan. Default: %(default)s",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write JSON report under Saved/MCP_DocAudit.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a concise pass/fail summary instead of the full JSON report.",
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
