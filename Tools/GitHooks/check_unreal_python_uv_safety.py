#!/usr/bin/env python3
"""Block unsafe Unreal Python UV channel probes before commit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCANNED_SUFFIXES = {".py", ".pyw"}
UNSAFE_TOKEN = "GetVertexInstanceUV"
ALLOW_TOKEN = "unreal-uv-safety: allow-getvertexinstanceuv"
GUARD_TOKENS = (
    "get_num_uv_channels",
    "get_num_uv_channel",
    "GetNumUVChannels",
    "num_uv_channels",
    "uv_channel_count",
)


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def staged_files() -> list[Path]:
    output = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [
        Path(line.strip())
        for line in output.splitlines()
        if line.strip() and Path(line.strip()).suffix.lower() in SCANNED_SUFFIXES
    ]


def staged_text(path: Path) -> str | None:
    try:
        return run_git(["show", f":{path.as_posix()}"])
    except subprocess.CalledProcessError:
        return None
    except UnicodeDecodeError:
        return None


def has_guard(text: str) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in GUARD_TOKENS)


def main() -> int:
    failures: list[tuple[Path, list[int]]] = []

    for path in staged_files():
        text = staged_text(path)
        if text is None or UNSAFE_TOKEN not in text or ALLOW_TOKEN in text:
            continue
        if has_guard(text):
            continue

        lines = [
            index
            for index, line in enumerate(text.splitlines(), start=1)
            if UNSAFE_TOKEN in line
        ]
        failures.append((path, lines))

    if not failures:
        return 0

    print("Unsafe Unreal Python UV inspection detected.", file=sys.stderr)
    print(
        "StaticMeshDescription.GetVertexInstanceUV can crash Unreal when the UV "
        "channel does not exist.",
        file=sys.stderr,
    )
    print(
        "Check the mesh UV channel count first, then read only confirmed channels.",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    for path, lines in failures:
        joined = ", ".join(str(line) for line in lines)
        print(f"- {path.as_posix()} lines {joined}", file=sys.stderr)

    print("", file=sys.stderr)
    print(
        "Expected guard examples: get_num_uv_channels(...), num_uv_channels, "
        "or uv_channel_count.",
        file=sys.stderr,
    )
    print(
        f"If this is intentionally safe, add a comment containing: {ALLOW_TOKEN}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
