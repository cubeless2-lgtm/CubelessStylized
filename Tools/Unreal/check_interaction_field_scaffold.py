#!/usr/bin/env python3
"""Validate the InteractionField plugin scaffold before Unreal asset work."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cubeless_ops_paths import project_doc_path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "Plugins" / "InteractionField"
UPROJECT = REPO_ROOT / "StylizedCubeless.uproject"
DESCRIPTOR = PLUGIN_ROOT / "InteractionField.uplugin"
PLAN_DOC = project_doc_path("docs/interaction-field-system.md", REPO_ROOT)


REQUIRED_CONTENT_DIRS = [
    "Content/Core",
    "Content/Core/Blueprints",
    "Content/Core/Data",
    "Content/Niagara",
    "Content/Niagara/DataChannels",
    "Content/Niagara/Modules",
    "Content/Niagara/Systems",
    "Content/Materials",
    "Content/Materials/Debug",
    "Content/Materials/Functions",
    "Content/Demo",
    "Content/Demo/Blueprints",
    "Content/Demo/Maps",
]


REQUIRED_ASSET_FILES = [
    "Content/Core/Blueprints/BPC_InteractionSource.uasset",
    "Content/Core/Blueprints/BP_InteractionField.uasset",
    "Content/Core/Data/MPC_InteractionField.uasset",
    "Content/Core/Data/RT_IF_Deform.uasset",
    "Content/Niagara/Systems/NS_InteractionField.uasset",
    "Content/Materials/Functions/MF_SampleInteractionField.uasset",
    "Content/Materials/Debug/M_IF_DebugFieldPreview.uasset",
    "Content/Materials/Debug/M_IF_DebugFieldUV.uasset",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"[FAIL] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def require_text_term(plan_text: str, term: str, failures: list[str]) -> None:
    if term in plan_text:
        ok(f"plan records: {term}")
    else:
        fail(f"plan missing term: {term}", failures)


def main() -> int:
    failures: list[str] = []

    if not DESCRIPTOR.exists():
        fail(f"missing descriptor: {DESCRIPTOR}", failures)
    else:
        descriptor = load_json(DESCRIPTOR)
        ok("InteractionField.uplugin parses as JSON")

        if descriptor.get("CanContainContent") is True:
            ok("plugin can contain content")
        else:
            fail("InteractionField.uplugin must set CanContainContent=true", failures)

        if descriptor.get("Modules"):
            fail("InteractionField must remain content-only for this phase; Modules must be absent", failures)
        else:
            ok("plugin has no Modules")

        deps = {entry.get("Name") for entry in descriptor.get("Plugins", [])}
        if "Niagara" in deps:
            ok("plugin depends on Niagara")
        else:
            fail("InteractionField.uplugin must depend on Niagara", failures)

        forbidden_deps = {"Water", "WaterAdvanced", "WaterExtras"}
        present_forbidden = sorted(deps & forbidden_deps)
        if present_forbidden:
            fail(f"forbidden plugin dependencies present: {present_forbidden}", failures)
        else:
            ok("plugin has no Water/WaterAdvanced/WaterExtras dependency")

    for rel_dir in REQUIRED_CONTENT_DIRS:
        path = PLUGIN_ROOT / rel_dir
        if path.is_dir():
            ok(f"content folder exists: {rel_dir}")
        else:
            fail(f"missing content folder: {rel_dir}", failures)

    for rel_file in REQUIRED_ASSET_FILES:
        path = PLUGIN_ROOT / rel_file
        if path.is_file():
            ok(f"asset file exists: {rel_file}")
        else:
            fail(f"missing asset file: {rel_file}", failures)

    if not UPROJECT.exists():
        fail(f"missing uproject: {UPROJECT}", failures)
    else:
        uproject = load_json(UPROJECT)
        enabled_plugins = {
            entry.get("Name"): entry for entry in uproject.get("Plugins", [])
        }
        if enabled_plugins.get("InteractionField", {}).get("Enabled") is True:
            ok("StylizedCubeless.uproject enables InteractionField")
        else:
            fail("StylizedCubeless.uproject must enable InteractionField", failures)

    if PLAN_DOC.exists():
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        required_terms = [
            "Niagara(Grid2D)",
            "RT export",
            "SceneCapture",
            "BPC_InteractionSource",
            "SourceProfile",
            "CapsuleGround",
            "MultiPointOffsets",
        ]
        for term in required_terms:
            require_text_term(plan_text, term, failures)

        forbidden_terms = [
            "SceneCapture+",
            "SceneCapture fallback",
            "SceneCapture fallback wording",
        ]
        present_forbidden = [term for term in forbidden_terms if term in plan_text]
        if present_forbidden:
            fail(
                "plan still contains old SceneCapture fallback wording: "
                f"{present_forbidden}",
                failures,
            )
        else:
            ok("old SceneCapture fallback wording is absent")
    else:
        fail(f"missing plan document: {PLAN_DOC}", failures)

    print()
    if failures:
        print(f"InteractionField scaffold preflight failed: {len(failures)} issue(s)")
        return 1

    print("InteractionField scaffold preflight passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
