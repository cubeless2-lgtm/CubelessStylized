"""Run local read-only preflight checks for StackOBot animation requests.

This tool validates the static pieces needed before Tivret touches StackOBot
editor state: project paths, .mcp.json routing, the StackOBot-local UnrealMCP
plugin copy, sibling Python/docs command surface, sample/evidence roots, and
the primary bridge port. It does not call Unreal commands, mutate assets, or
require the editor to be open unless --require-bridge is used.
"""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STACKOBOT_ROOT = PROJECT_ROOT.parent / "SampleProject" / "StackOBot"
SIBLING_MCP_ROOT = PROJECT_ROOT.parent / "unreal-mcp-cubeless"
STACKOBOT_PLUGIN_ROOT = STACKOBOT_ROOT / "Plugins" / "UnrealMCP"
STACKOBOT_MCP_JSON = STACKOBOT_ROOT / ".mcp.json"
SAMPLE_CONTENT_DIR = STACKOBOT_ROOT / "Content" / "_MCP_Sample" / "AnimStudy"
EVIDENCE_DIR = STACKOBOT_ROOT / "Saved" / "MCP" / "AnimStudy"
REPORT_PATH = PROJECT_ROOT / "Saved" / "MCP_DocAudit" / "StackOBotAnimationPreflight.json"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 55557

REQUIRED_COMMANDS = [
    "inspect_anim_graph_protected_topology",
    "inspect_anim_state_machine_transitions",
    "inspect_anim_instance_runtime_state",
    "inspect_anim_graph_node_settings",
    "controlrig_direct_gate_probe",
    "sample_anim_node_pre_post_runtime_pose",
    "ensure_blendspace_sample_variant",
    "sample_blendspace_runtime_pose_grid",
    "sample_anim_state_machine_runtime_response",
    "set_anim_graph_rigidbody_settings",
    "ensure_postprocess_anim_demo_variant",
    "ensure_controlrig_forced_driver_animbp",
    "ensure_anim_graph_trail_demo",
]

REQUIRED_COMMAND_SURFACE_FILES = [
    SIBLING_MCP_ROOT / "Python" / "tools" / "node_tools.py",
    SIBLING_MCP_ROOT / "Docs" / "Tools" / "node_tools.md",
    STACKOBOT_PLUGIN_ROOT / "Source" / "UnrealMCP" / "Private" / "UnrealMCPBridge.cpp",
    (
        STACKOBOT_PLUGIN_ROOT
        / "Source"
        / "UnrealMCP"
        / "Private"
        / "Commands"
        / "UnrealMCPBlueprintNodeCommands.cpp"
    ),
]

REFERENCE_COMMAND_SURFACE_FILES = [
    SIBLING_MCP_ROOT / "Python" / "unreal_mcp_server.py",
]


def _project_relative(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _path_entry(label: str, path: Path, expected_kind: str) -> dict[str, Any]:
    exists = path.exists()
    if expected_kind == "directory":
        kind_ok = path.is_dir()
    elif expected_kind == "file":
        kind_ok = path.is_file()
    else:
        kind_ok = exists
    return {
        "label": label,
        "path": path.as_posix(),
        "exists": exists,
        "expected_kind": expected_kind,
        "kind_ok": kind_ok,
        "pass": exists and kind_ok,
    }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def _load_mcp_json() -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": STACKOBOT_MCP_JSON.as_posix(),
        "exists": STACKOBOT_MCP_JSON.is_file(),
        "server_present": False,
        "command": "",
        "uv_resolves": False,
        "python_root_arg": "",
        "python_root_resolved": "",
        "python_root_matches_expected": False,
        "uses_python_3_11": False,
        "server_script_present": False,
        "pass": False,
    }
    if not STACKOBOT_MCP_JSON.is_file():
        entry["error"] = "Missing StackOBot .mcp.json."
        return entry

    try:
        data = json.loads(STACKOBOT_MCP_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        entry["error"] = str(exc)
        return entry

    server = data.get("mcpServers", {}).get("unrealMCP", {})
    args = server.get("args", [])
    entry["server_present"] = bool(server)
    entry["command"] = str(server.get("command", ""))
    entry["uv_resolves"] = bool(shutil.which(entry["command"])) if entry["command"] else False
    entry["uses_python_3_11"] = "--python" in args and "3.11" in args

    if "--directory" in args:
        directory_index = args.index("--directory") + 1
        if directory_index < len(args):
            directory_arg = str(args[directory_index])
            resolved = (STACKOBOT_ROOT / directory_arg).resolve()
            entry["python_root_arg"] = directory_arg
            entry["python_root_resolved"] = resolved.as_posix()
            entry["python_root_matches_expected"] = resolved == (SIBLING_MCP_ROOT / "Python").resolve()

    entry["server_script_present"] = "unreal_mcp_server.py" in args and (
        SIBLING_MCP_ROOT / "Python" / "unreal_mcp_server.py"
    ).is_file()
    entry["pass"] = all(
        [
            entry["server_present"],
            entry["command"] == "uv",
            entry["uv_resolves"],
            entry["python_root_matches_expected"],
            entry["uses_python_3_11"],
            entry["server_script_present"],
        ]
    )
    return entry


def _command_surface_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in REQUIRED_COMMAND_SURFACE_FILES:
        text = _read_text(path) if path.is_file() else ""
        missing = [command for command in REQUIRED_COMMANDS if command not in text]
        entries.append(
            {
                "path": path.as_posix(),
                "required": True,
                "exists": path.is_file(),
                "missing_commands": missing,
                "missing_command_count": len(missing),
                "pass": path.is_file() and not missing,
            }
        )
    for path in REFERENCE_COMMAND_SURFACE_FILES:
        text = _read_text(path) if path.is_file() else ""
        missing = [command for command in REQUIRED_COMMANDS if command not in text]
        entries.append(
            {
                "path": path.as_posix(),
                "required": False,
                "exists": path.is_file(),
                "missing_commands": missing,
                "missing_command_count": len(missing),
                "pass": path.is_file(),
            }
        )
    return entries


def _bridge_entry(host: str, port: int, timeout_seconds: float) -> dict[str, Any]:
    started_at = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            reachable = True
            error = ""
    except OSError as exc:
        reachable = False
        error = str(exc)
    return {
        "host": host,
        "port": port,
        "timeout_seconds": timeout_seconds,
        "reachable": reachable,
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "error": error,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    started_at = time.monotonic()
    path_checks = [
        _path_entry("StackOBot project", STACKOBOT_ROOT, "directory"),
        _path_entry("StackOBot uproject", STACKOBOT_ROOT / "StackOBot.uproject", "file"),
        _path_entry("StackOBot .mcp.json", STACKOBOT_MCP_JSON, "file"),
        _path_entry("StackOBot UnrealMCP plugin", STACKOBOT_PLUGIN_ROOT, "directory"),
        _path_entry("sibling UnrealMCP Python root", SIBLING_MCP_ROOT / "Python", "directory"),
        _path_entry("sibling node_tools wrapper", SIBLING_MCP_ROOT / "Python" / "tools" / "node_tools.py", "file"),
        _path_entry("sibling node_tools docs", SIBLING_MCP_ROOT / "Docs" / "Tools" / "node_tools.md", "file"),
        _path_entry("sample content root", SAMPLE_CONTENT_DIR, "directory"),
        _path_entry("evidence root", EVIDENCE_DIR, "directory"),
    ]
    mcp_json = _load_mcp_json()
    command_surface = _command_surface_entries()
    bridge = _bridge_entry(args.host, args.port, args.timeout_seconds)

    static_pass = (
        all(entry["pass"] for entry in path_checks)
        and mcp_json["pass"]
        and all(entry["pass"] for entry in command_surface if entry["required"])
    )
    live_pass = bridge["reachable"]
    pass_value = static_pass and (live_pass or not args.require_bridge)

    report = {
        "schema": "stackobot_animation_preflight_v1",
        "elapsed_seconds": round(time.monotonic() - started_at, 4),
        "project_root": PROJECT_ROOT.as_posix(),
        "stackobot_root": STACKOBOT_ROOT.as_posix(),
        "static_pass": static_pass,
        "bridge_required": args.require_bridge,
        "bridge_reachable": live_pass,
        "ready_for_editor_work": static_pass and live_pass,
        "pass": pass_value,
        "path_checks": path_checks,
        "mcp_json": mcp_json,
        "required_commands": REQUIRED_COMMANDS,
        "command_surface": command_surface,
        "bridge": bridge,
        "notes": [
            "This check is local/read-only and does not call Unreal commands.",
            "Dirty package status still requires a live editor command immediately before asset work.",
            "Use --require-bridge when this is the final gate before Tivret editor work.",
        ],
    }

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = _project_relative(REPORT_PATH)

    return report


def _format_summary(report: dict[str, Any]) -> str:
    status = "PASS" if report["pass"] else "FAIL"
    live = "reachable" if report["bridge_reachable"] else "not reachable"
    ready = "yes" if report["ready_for_editor_work"] else "no"
    lines = [
        f"StackOBot animation preflight: {status}",
        (
            f"schema={report['schema']} static_pass={str(report['static_pass']).lower()} "
            f"bridge={live} bridge_required={str(report['bridge_required']).lower()} "
            f"ready_for_editor_work={ready}"
        ),
    ]
    if report.get("report_path"):
        lines.append(f"report={report['report_path']}")

    failed_paths = [entry for entry in report["path_checks"] if not entry["pass"]]
    failed_surfaces = [entry for entry in report["command_surface"] if entry["required"] and not entry["pass"]]
    reference_warnings = [
        entry
        for entry in report["command_surface"]
        if not entry["required"] and entry["exists"] and entry["missing_commands"]
    ]
    if failed_paths:
        lines.append("failed_paths:")
        for entry in failed_paths:
            lines.append(f"  - {entry['label']}: {entry['path']}")
    if not report["mcp_json"]["pass"]:
        lines.append(f"mcp_json_failed: {report['mcp_json']}")
    if failed_surfaces:
        lines.append("command_surface_failures:")
        for entry in failed_surfaces:
            lines.append(f"  - {entry['path']}: missing={entry['missing_commands']}")
    if reference_warnings:
        lines.append("reference_surface_warnings:")
        for entry in reference_warnings:
            lines.append(f"  - {entry['path']}: missing_from_summary={entry['missing_commands']}")
    if not report["bridge_reachable"]:
        lines.append(f"bridge_error={report['bridge']['error']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST, help="UnrealMCP bridge host. Default: %(default)s")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UnrealMCP bridge port. Default: %(default)s")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=0.5,
        help="Socket connect timeout for the bridge check. Default: %(default)s",
    )
    parser.add_argument(
        "--require-bridge",
        action="store_true",
        help="Fail if the primary bridge is not reachable.",
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
