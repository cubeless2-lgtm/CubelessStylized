from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ASSET_INDEX = Path("docs/niagara-learning/niagara_asset_index.json")
DEFAULT_SIGNATURE_INDEX = Path("docs/niagara-learning/niagara_structural_signature_index.json")
DEFAULT_OUTPUT = Path("docs/niagara-learning/niagara_material_style_index.json")


MATERIAL_ROLE_RULES = {
    "additive_glow": ["glow", "aura", "light", "emissive", "hitref", "radialblur"],
    "stylized_lightning": ["lightning", "elec", "electric", "beam", "laser", "spark"],
    "soft_smoke": ["smoke", "fog", "mist", "dust", "cloud", "steam"],
    "radial_shockwave": ["shockwave", "radial", "ring", "circle", "torus", "area"],
    "ribbon_slash": ["trail", "ribbon", "slash", "sword", "swing", "stab"],
    "spark_sprite": ["spark", "ember", "particle"],
    "fire_flipbook": ["fire", "flame", "torch", "chimney"],
    "water_splash": ["water", "rain", "splash", "puddle", "fluid"],
    "decal_crack": ["decal", "crack", "groundcrack", "crater"],
    "dissolve_noise": ["dissolve", "noise", "mask", "distortion"],
}


STYLE_RULES = [
    ("EL_StylizedCombat", ["/Game/EL/ART/FX", "/Game/EL/ART/BG/FX"]),
    ("UltraDynamicSky_Weather", ["/Game/UltraDynamicSky"]),
    ("UltraVolumetrics_SoftVolume", ["/Game/UltraVolumetrics", "/UltraVolumetrics/"]),
    ("Cubeless_Reactive", ["/Game/Cubeless/Reactive"]),
    ("Cubeless_Generated", ["/Game/Cubeless/FX/Generated", "/Game/_MCP_Temp/NiagaraGenerated"]),
]


BLEND_HINT_RULES = {
    "likely_additive": ["glow", "light", "beam", "laser", "spark", "lightning", "emissive"],
    "likely_translucent": ["smoke", "fog", "mist", "water", "rain", "particle", "cloud"],
    "likely_masked_or_decal": ["decal", "crack", "groundcrack", "mask"],
}


def repo_root_from(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "StylizedCubeless.uproject").exists():
            return candidate
    return current


def contains_any(blob: str, needles: list[str]) -> bool:
    return any(needle.casefold() in blob for needle in needles)


def tags_from_rules(blob: str, rules: dict[str, list[str]]) -> list[str]:
    return sorted(tag for tag, needles in rules.items() if contains_any(blob, needles))


def style_profiles(path: str, used_by_styles: set[str]) -> list[str]:
    styles = set(used_by_styles)
    lowered = path.casefold()
    for style, prefixes in STYLE_RULES:
        if any(prefix.casefold() in lowered for prefix in prefixes):
            styles.add(style)
    return sorted(styles) or ["UnknownProjectStyle"]


def material_name(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def source_operation(path: str, roles: list[str]) -> str:
    lowered = path.casefold()
    if "/mi_" in lowered or material_name(path).casefold().startswith("mi_"):
        return "duplicate_material_instance"
    if "/m_" in lowered or material_name(path).casefold().startswith("m_"):
        return "reuse_or_create_instance"
    if roles:
        return "reuse"
    return "inspect_before_use"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_signature_lookup(signature_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item.get("object_path", ""): item
        for item in signature_index.get("assets", [])
    }


def collect_materials(asset_index: dict[str, Any], signature_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    signature_lookup = build_signature_lookup(signature_index)
    materials: dict[str, dict[str, Any]] = {}

    for asset in asset_index.get("assets", []):
        deps = asset.get("dependency_buckets", {})
        source_path = asset.get("object_path", "")
        signature = signature_lookup.get(source_path, {})
        source_styles = set(signature.get("style_profiles", []))
        source_roles = set(signature.get("visual_roles", []))

        for material_path in deps.get("materials", []):
            entry = materials.setdefault(
                material_path,
                {
                    "material_path": material_path,
                    "name": material_name(material_path),
                    "used_by": [],
                    "used_by_visual_roles": set(),
                    "used_by_style_profiles": set(),
                },
            )
            entry["used_by"].append(source_path)
            entry["used_by_visual_roles"].update(source_roles)
            entry["used_by_style_profiles"].update(source_styles)

    return materials


def finalize_material_entry(entry: dict[str, Any]) -> dict[str, Any]:
    path = entry["material_path"]
    material_blob = " ".join([path, entry["name"]]).casefold()
    roles = tags_from_rules(material_blob, MATERIAL_ROLE_RULES)
    blend_hints = tags_from_rules(material_blob, BLEND_HINT_RULES)
    used_by = sorted(set(entry["used_by"]))
    used_by_roles = sorted(entry["used_by_visual_roles"])
    used_by_styles = style_profiles(path, set(entry["used_by_style_profiles"]))

    confidence_reasons = []
    if roles:
        confidence_reasons.append("role inferred from material path/name and Niagara usage")
    if blend_hints:
        confidence_reasons.append("blend hint inferred from material naming")
    if used_by_roles:
        confidence_reasons.append("visual context inferred from Niagara structural signatures")
    confidence = "medium" if roles and used_by_roles else "low"

    return {
        "material_path": path,
        "name": entry["name"],
        "display_name": f"{entry['name']} ({', '.join(roles[:2]) if roles else 'unknown_material_role'})",
        "material_roles": roles or ["unknown_material_role"],
        "blend_hints": blend_hints or ["unknown_blend"],
        "style_profiles": used_by_styles,
        "used_by_visual_roles": used_by_roles,
        "used_by_count": len(used_by),
        "used_by_sample": used_by[:25],
        "recommended_operation": source_operation(path, roles),
        "confidence": confidence,
        "confidence_reasons": confidence_reasons or ["insufficient non-C++ material evidence"],
    }


def build_index(asset_index: dict[str, Any], signature_index: dict[str, Any]) -> dict[str, Any]:
    collected = collect_materials(asset_index, signature_index)
    materials = [finalize_material_entry(entry) for entry in collected.values()]
    materials.sort(key=lambda item: (-item["used_by_count"], item["material_path"]))
    return {
        "schema_version": 1,
        "generated_from": {
            "asset_index": str(DEFAULT_ASSET_INDEX),
            "structural_signature_index": str(DEFAULT_SIGNATURE_INDEX),
        },
        "coverage_notes": [
            "This is a no-C++ first pass.",
            "Material roles are inferred from material names, paths, and Niagara dependency context.",
            "Actual material graph properties require a future Material/FX graph analysis pass.",
        ],
        "materials": materials,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a first-pass Niagara material style index.")
    parser.add_argument("--asset-index", type=Path, default=None)
    parser.add_argument("--signature-index", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root_from(Path.cwd())
    asset_index_path = args.asset_index or root / DEFAULT_ASSET_INDEX
    signature_index_path = args.signature_index or root / DEFAULT_SIGNATURE_INDEX
    output_path = args.output or root / DEFAULT_OUTPUT
    output = build_index(load_json(asset_index_path), load_json(signature_index_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        role_counts: dict[str, int] = {}
        for material in output["materials"]:
            for role in material["material_roles"]:
                role_counts[role] = role_counts.get(role, 0) + 1
        print(json.dumps({
            "output": str(output_path),
            "material_count": len(output["materials"]),
            "role_counts": dict(sorted(role_counts.items(), key=lambda item: (-item[1], item[0]))),
        }, ensure_ascii=False, indent=2))
    else:
        print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
