#!/usr/bin/env python3
"""Block accidental project dependencies on the UnrealMCP plugin."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


SCANNED_ENDINGS = (
    ".cpp",
    ".h",
    ".hpp",
    ".hxx",
    ".inl",
    ".Build.cs",
    ".Target.cs",
    ".ini",
    ".uplugin",
    ".uproject",
)

ALLOW_TOKEN = "cubeless-mcp-plugin-dependency: explicit-user-request"
SKIPPED_PARTS = {
    "unrealmcp",
}
HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("UnrealMCP module or class reference", re.compile(r"\bUnrealMCP[A-Za-z0-9_]*\b")),
    ("UnrealMCP script path reference", re.compile(r"/Script/UnrealMCP\b")),
    ("UnrealMCP package or plugin reference", re.compile(r"/(?:Game/)?UnrealMCP\b", re.IGNORECASE)),
    ("UnrealMCP plugin path reference", re.compile(r"Plugins[/\\]UnrealMCP\b", re.IGNORECASE)),
    ("MCP-only plugin identifier", re.compile(r"\b(?:MCPUnreal|mcp_unreal)\b", re.IGNORECASE)),
    ("MCP plugin/module dependency", re.compile(r"""["'](?:UnrealMCP|MCPUnreal|mcp_unreal)["']""", re.IGNORECASE)),
)


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def should_scan(path: Path) -> bool:
    normalized_parts = {part.lower() for part in path.parts}
    if normalized_parts & SKIPPED_PARTS:
        return False

    path_text = path.as_posix()
    return any(path_text.endswith(ending) for ending in SCANNED_ENDINGS)


def staged_files() -> list[Path]:
    output = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [Path(line.strip()) for line in output.splitlines() if line.strip() and should_scan(Path(line.strip()))]


def staged_text(path: Path) -> str | None:
    try:
        return run_git(["show", f":{path.as_posix()}"])
    except subprocess.CalledProcessError:
        return None
    except UnicodeDecodeError:
        return None


def staged_added_lines(path: Path) -> list[tuple[int, str]]:
    try:
        diff = run_git(["diff", "--cached", "--unified=0", "--no-ext-diff", "--", path.as_posix()])
    except subprocess.CalledProcessError:
        return []

    added: list[tuple[int, str]] = []
    new_line_number: int | None = None
    for line in diff.splitlines():
        hunk_match = HUNK_HEADER_RE.match(line)
        if hunk_match:
            new_line_number = int(hunk_match.group(1))
            continue

        if new_line_number is None:
            continue

        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            added.append((new_line_number, line[1:]))
            new_line_number += 1
        elif line.startswith("-"):
            continue
        else:
            new_line_number += 1

    return added


def matching_lines(lines: list[tuple[int, str]]) -> list[tuple[int, str, str]]:
    matches: list[tuple[int, str, str]] = []
    allow_next_added_line = False
    for line_number, line in lines:
        if ALLOW_TOKEN in line:
            allow_next_added_line = True
            continue

        matched_line: tuple[int, str, str] | None = None
        for label, pattern in BLOCK_PATTERNS:
            if pattern.search(line):
                matched_line = (line_number, label, line.strip())
                break

        if matched_line:
            if allow_next_added_line:
                allow_next_added_line = False
                continue
            matches.append(matched_line)
        else:
            allow_next_added_line = False

    return matches


def main() -> int:
    failures: list[tuple[Path, list[tuple[int, str, str]]]] = []

    for path in staged_files():
        text = staged_text(path)
        if text is None:
            continue

        matches = matching_lines(staged_added_lines(path))
        if matches:
            failures.append((path, matches))

    if not failures:
        return 0

    print("Project-side dependency on the UnrealMCP/MCP plugin detected.", file=sys.stderr)
    print(
        "MCP is an optional editor-only authoring aid by default. Project C++ APIs, "
        "module descriptors, config files, and promoted assets must remain "
        "buildable/openable/cookable/packageable without the MCP plugin unless the "
        "user explicitly requested that dependency.",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    for path, matches in failures:
        print(f"- {path.as_posix()}", file=sys.stderr)
        for line_number, label, line in matches[:8]:
            print(f"  line {line_number}: {label}: {line}", file=sys.stderr)
        if len(matches) > 8:
            print(f"  ... {len(matches) - 8} more match(es)", file=sys.stderr)

    print("", file=sys.stderr)
    print(
        "Keep MCP C++ extensions in editor-only tooling, move final runtime/Blueprint/PCG "
        "functionality into the project or an approved project plugin, use soft optional "
        "tooling, or get explicit user approval for the MCP plugin dependency.",
        file=sys.stderr,
    )
    print(
        f"If the dependency was explicitly requested, add a line containing: {ALLOW_TOKEN}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
