"""Audit StackOBot animation study documentation references and structure.

This local/read-only check validates that StackOBot study docs point to existing
relative docs, required study documents still exist, key template sections are
present, and the sibling/sample workspace paths used by the workflow still exist
on this machine. It does not call Unreal, does not touch assets, and does not
require the editor bridge to be online.
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
    pass_value = (
        not missing_references
        and not missing_external_paths
        and not missing_required_docs
        and not missing_required_sections
        and not missing_required_tokens
    )

    report = {
        "schema": "stackobot_animation_docs_link_audit_v3",
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
        "pass": pass_value,
        "docs": [_project_relative(path) for path in docs],
        "missing_references": missing_references,
        "external_paths": external_paths,
        "missing_required_docs": missing_required_docs,
        "missing_required_sections": missing_required_sections,
        "missing_required_tokens": missing_required_tokens,
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
            f"missing_required_tokens={report['missing_required_token_count']}"
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
