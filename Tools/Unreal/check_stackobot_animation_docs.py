"""Audit StackOBot animation study documentation references and structure.

This local/read-only check validates that StackOBot study docs point to existing
relative docs, required study documents still exist, key template sections,
request-run example fields, and MCP command syntax examples are present, and the
sibling/sample workspace paths used by the workflow still exist on this machine.
It does not call Unreal, does not touch assets, and does not require the editor
bridge to be online.
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
DOCS_ROOT = PROJECT_ROOT / "docs"
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_DocAudit" / "StackOBotAnimationDocsLinkAudit.json"

RELATIVE_DOC_RE = re.compile(r"(?<![A-Za-z0-9_:/.-])docs/[A-Za-z0-9._/-]+\.md")
EXAMPLE_SECTION_RE = re.compile(r"^## Example (?P<number>\d+): (?P<title>.+)$", re.MULTILINE)
TEXT_FENCE_RE = re.compile(r"```text\n(?P<body>.*?)\n```", re.DOTALL)
JSON_FENCE_RE = re.compile(r"```json\n(?P<body>.*?)\n```", re.DOTALL)
EXAMPLE_FIELD_RE = re.compile(r"^(?P<name>[a-z_]+):\s*(?P<value>.*)$")
STACKOBOT_DOC_GLOB = "stackobot*.md"

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
    "docs/stackobot-animation-tivret-handoff-templates.md",
    "docs/stackobot-animation-authoring-templates.md",
    "docs/stackobot-animation-mcp-command-syntax.md",
    "docs/stackobot-cpp-api-decision-matrix.md",
    "docs/stackobot-animation-execution-map.md",
    "docs/stackobot-sample-asset-manifest.md",
    "docs/stackobot-live-read-drill-2026-06-19.md",
    "docs/stackobot-physics-request-grammar.md",
]

REQUIRED_SECTIONS = {
    "docs/stackobot-animation-doc-index.md": [
        "## Start Here",
        "## Request Execution Pages",
        "## Route Deep Dives",
        "## Default Workflow",
        "## Local Checks",
        "## Safe Defaults",
    ],
    "docs/stackobot-animation-quickstart.md": [
        "## Start Here",
        "## Preflight Checklist",
        "## Route Shortcuts",
        "## Do Not Do First",
        "## Main References",
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
    "docs/stackobot-animation-acceptance-checklist.md": [
        "## Universal Pass Gate",
        "## Route-Specific Pass Criteria",
        "## Evidence Strength Levels",
        "## When To Stop And Escalate",
        "## Final User Report Checklist",
    ],
    "docs/stackobot-animation-tivret-handoff-templates.md": [
        "## Post Process ModifyBone",
        "## BlendSpace Sample Variant",
        "## State Machine Or Runtime Driver",
        "## ControlRig Late Correction",
        "## UpperBody Slot And LayeredBlend",
        "## Trail Or Secondary Motion",
        "## Notify, Curve, Sync Marker, Or Montage Internals",
        "## Final Report Shape",
    ],
    "docs/stackobot-animation-authoring-templates.md": [
        "## Routing Table",
        "## Template Cards",
        "### Post Process ModifyBone",
        "### BlendSpace Sample Variant",
        "### State Machine Or Runtime Driver",
        "### ControlRig Late Correction",
        "### UpperBody Slot And LayeredBlend",
        "### Secondary Motion Or Physics",
        "### Notify, Curve, Sync Marker, And Montage Internals",
        "## Completion Contract",
        "## C++/API Escalation Gate",
    ],
    "docs/stackobot-cpp-api-decision-matrix.md": [
        "## Current Rule",
        "## Covered, Do Not Rebuild",
        "## Candidate Matrix",
        "## Immediate Implementation Triggers",
        "## Verification For Any New C++ API",
        "## Timing Decision",
    ],
}

REQUIRED_TOKENS = {
    "docs/stackobot-animation-quickstart.md": [
        "run_stackobot_animation_local_checks.py --summary",
        "--require-bridge",
        "D:/Git/SampleProject/StackOBot",
        "127.0.0.1:55557",
        "D:/Git/SampleProject/StackOBot/Plugins/UnrealMCP",
        "/Game/_MCP_Sample/AnimStudy",
        "allow_non_sample=false",
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
    "docs/stackobot-animation-request-playbook.md": [
        "Start sample-only unless",
        "티브렛에게 전달할 지시",
        "allow_non_sample=false",
        "C++/API Escalation",
        "Do not broad-probe Montage",
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
]

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


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    docs = sorted(DOCS_ROOT.glob(args.glob))
    references = _collect_doc_references(docs)
    missing_references = [entry for entry in references if not entry["exists"]]
    external_paths = _external_path_entries()
    missing_external_paths = [entry for entry in external_paths if not entry["exists"]]
    required_docs = _required_doc_entries()
    missing_required_docs = [entry for entry in required_docs if not entry["exists"]]
    required_sections = _required_section_entries()
    missing_required_sections = [entry for entry in required_sections if not entry["exists"]]
    required_tokens = _required_token_entries()
    missing_required_tokens = [entry for entry in required_tokens if not entry["exists"]]
    example_fields = _request_example_field_entries()
    missing_example_fields = [
        entry for entry in example_fields if not entry["exists"] or not entry["has_value"]
    ]
    command_syntax_json_blocks = _command_syntax_json_blocks()
    invalid_command_syntax_json = [
        entry for entry in command_syntax_json_blocks if not entry["parse_success"]
    ]
    command_syntax_commands = _command_syntax_command_entries(command_syntax_json_blocks)
    missing_command_syntax_commands = [
        entry for entry in command_syntax_commands if not entry["exists"]
    ]
    command_syntax_authoring_safety = _command_syntax_authoring_safety_entries(command_syntax_json_blocks)
    unsafe_command_syntax_authoring = [
        entry
        for entry in command_syntax_authoring_safety
        if not entry["exists"] or not entry["safe_value"]
    ]
    pass_value = (
        not missing_references
        and not missing_external_paths
        and not missing_required_docs
        and not missing_required_sections
        and not missing_required_tokens
        and not missing_example_fields
        and not invalid_command_syntax_json
        and not missing_command_syntax_commands
        and not unsafe_command_syntax_authoring
    )

    report = {
        "schema": "stackobot_animation_docs_link_audit_v5",
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": PROJECT_ROOT.as_posix(),
        "doc_glob": args.glob,
        "doc_count": len(docs),
        "reference_count": len(references),
        "missing_reference_count": len(missing_references),
        "missing_external_path_count": len(missing_external_paths),
        "missing_required_doc_count": len(missing_required_docs),
        "missing_required_section_count": len(missing_required_sections),
        "missing_required_token_count": len(missing_required_tokens),
        "missing_example_field_count": len(missing_example_fields),
        "invalid_command_syntax_json_count": len(invalid_command_syntax_json),
        "missing_command_syntax_command_count": len(missing_command_syntax_commands),
        "unsafe_command_syntax_authoring_count": len(unsafe_command_syntax_authoring),
        "pass": pass_value,
        "docs": [_project_relative(path) for path in docs],
        "missing_references": missing_references,
        "external_paths": external_paths,
        "missing_required_docs": missing_required_docs,
        "missing_required_sections": missing_required_sections,
        "missing_required_tokens": missing_required_tokens,
        "example_fields": example_fields,
        "missing_example_fields": missing_example_fields,
        "command_syntax_json_blocks": command_syntax_json_blocks,
        "invalid_command_syntax_json": invalid_command_syntax_json,
        "command_syntax_commands": command_syntax_commands,
        "missing_command_syntax_commands": missing_command_syntax_commands,
        "command_syntax_authoring_safety": command_syntax_authoring_safety,
        "unsafe_command_syntax_authoring": unsafe_command_syntax_authoring,
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
            f"missing_required_sections={report['missing_required_section_count']} "
            f"missing_required_tokens={report['missing_required_token_count']} "
            f"missing_example_fields={report['missing_example_field_count']} "
            f"invalid_command_json={report['invalid_command_syntax_json_count']} "
            f"missing_command_examples={report['missing_command_syntax_command_count']} "
            f"unsafe_authoring_examples={report['unsafe_command_syntax_authoring_count']}"
        ),
    ]
    if report.get("report_path"):
        lines.append(f"report={report['report_path']}")
    if not report["pass"]:
        for key in [
            "missing_references",
            "missing_required_docs",
            "missing_required_sections",
            "missing_required_tokens",
            "missing_example_fields",
            "invalid_command_syntax_json",
            "missing_command_syntax_commands",
            "unsafe_command_syntax_authoring",
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
