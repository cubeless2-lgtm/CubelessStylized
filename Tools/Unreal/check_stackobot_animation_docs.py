"""Audit StackOBot animation study documentation references.

This local/read-only check validates that StackOBot study docs point to existing
relative docs and that the sibling/sample workspace paths used by the workflow
still exist on this machine. It does not call Unreal, does not touch assets, and
does not require the editor bridge to be online.
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


def _external_path_entries() -> list[dict[str, Any]]:
    return [
        {
            "path": path.as_posix(),
            "exists": path.exists(),
            "kind": "directory" if path.is_dir() else "file" if path.is_file() else "missing",
        }
        for path in EXPECTED_EXTERNAL_PATHS
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    docs = sorted(DOCS_ROOT.glob(args.glob))
    references = _collect_doc_references(docs)
    missing_references = [entry for entry in references if not entry["exists"]]
    external_paths = _external_path_entries()
    missing_external_paths = [entry for entry in external_paths if not entry["exists"]]

    report = {
        "schema": "stackobot_animation_docs_link_audit_v1",
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": PROJECT_ROOT.as_posix(),
        "doc_glob": args.glob,
        "doc_count": len(docs),
        "reference_count": len(references),
        "missing_reference_count": len(missing_references),
        "missing_external_path_count": len(missing_external_paths),
        "pass": not missing_references and not missing_external_paths,
        "docs": [_project_relative(path) for path in docs],
        "missing_references": missing_references,
        "external_paths": external_paths,
    }

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = _project_relative(REPORT_PATH)

    return report


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
    args = parser.parse_args(argv)

    report = run(args)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
