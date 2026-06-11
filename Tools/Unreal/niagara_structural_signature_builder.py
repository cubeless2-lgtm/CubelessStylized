from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("docs/niagara-learning/niagara_asset_index.json")
DEFAULT_OUTPUT = Path("docs/niagara-learning/niagara_structural_signature_index.json")


ROLE_RULES = {
    "ground_area": ["area", "ring", "radial", "circle", "disc", "torus", "ground", "shockwave"],
    "lightning_arc": ["lightning", "electric", "elec", "beam", "laser", "spark"],
    "spark_spray": ["spark", "ember", "burst", "hitref", "shot"],
    "smoke_volume": ["smoke", "fog", "mist", "dust", "cloud", "volumetric"],
    "fire_flame": ["fire", "flame", "torch", "ember", "chimney"],
    "ribbon_trail": ["trail", "ribbon", "slash", "swing", "sword", "animtrail"],
    "impact_burst": ["burst", "impact", "hit", "blast", "grenade", "projectile", "stab"],
    "weather_loop": ["rain", "snow", "weather", "puddle", "drip", "splash", "storm"],
    "reactive_runtime": ["reactive", "interaction", "foliage", "painter", "rendertexture", "grid2d"],
}


MOTION_RULES = {
    "radial_expand": ["ring", "radial", "circle", "shockwave", "burst", "torus"],
    "upward_spark": ["spark", "ember", "rising", "jump"],
    "falling": ["rain", "snow", "drip", "fall"],
    "follow_or_attached": ["trail", "ribbon", "swing", "slash", "animtrail", "sword"],
    "swirl_or_vortex": ["vortex", "swirl", "orbit", "spiral"],
    "fluid_or_grid": ["fluidgrid", "grid2d", "puddle", "waterlevel", "reactive"],
}


MATERIAL_ROLE_RULES = {
    "additive_glow": ["glow", "aura", "light", "emissive", "hitref"],
    "stylized_lightning": ["lightning", "elec", "beam", "laser", "spark"],
    "soft_smoke": ["smoke", "fog", "mist", "dust", "cloud"],
    "radial_shockwave": ["shockwave", "radialblur", "ring", "circle"],
    "ribbon_slash": ["trail", "ribbon", "slash", "sword"],
    "spark_sprite": ["spark", "ember"],
    "fire_flipbook": ["fire", "flame", "torch"],
    "water_splash": ["water", "rain", "splash", "puddle"],
    "decal_crack": ["decal", "crack", "groundcrack"],
}


MESH_ROLE_RULES = {
    "ring_mesh": ["torus", "circle", "ring", "disc"],
    "beam_mesh": ["beam", "lightning"],
    "cone_mesh": ["cone"],
    "plane_mesh": ["plane", "card"],
}


STYLE_RULES = [
    ("EL_StylizedCombat", ["/Game/EL/ART/FX", "/Game/EL/ART/BG/FX"]),
    ("UltraDynamicSky_Weather", ["/Game/UltraDynamicSky"]),
    ("UltraVolumetrics_SoftVolume", ["/Game/UltraVolumetrics", "/UltraVolumetrics/"]),
    ("Cubeless_Reactive", ["/Game/Cubeless/Reactive"]),
    ("Cubeless_Generated", ["/Game/Cubeless/FX/Generated", "/Game/_MCP_Temp/NiagaraGenerated"]),
]


RENDERER_HINT_RULES = {
    "ribbon": ["RibbonRenderer", "ribbon", "trail", "beam"],
    "mesh": ["MeshRenderer", "/mesh/", "_ms_", "torus", "circle", "cone"],
    "sprite": ["SpriteRenderer", "sprite", "particle", "spark", "smoke", "ember"],
    "decal_or_ground": ["decal", "groundcrack", "crack"],
    "grid_or_sim": ["Grid2D", "FluidGrid", "RenderTarget", "grid2d", "fluidgrid"],
}


def repo_root_from(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "StylizedCubeless.uproject").exists():
            return candidate
    return current


def normalized_blob(asset: dict[str, Any]) -> str:
    deps = asset.get("dependency_buckets", {})
    parts = [
        asset.get("name", ""),
        asset.get("package", ""),
        " ".join(asset.get("tokens", [])),
        " ".join(asset.get("categories", [])),
        " ".join(deps.get("materials", [])),
        " ".join(deps.get("textures", [])),
        " ".join(deps.get("meshes", [])),
        " ".join(deps.get("niagara_modules", [])),
        " ".join(deps.get("niagara_defs", [])),
        " ".join(deps.get("project_assets", [])),
    ]
    return " ".join(parts).casefold()


def semantic_blob(asset: dict[str, Any]) -> str:
    deps = asset.get("dependency_buckets", {})
    parts = [
        asset.get("name", ""),
        asset.get("package", ""),
        " ".join(asset.get("tokens", [])),
        " ".join(asset.get("categories", [])),
        " ".join(deps.get("materials", [])),
        " ".join(deps.get("textures", [])),
        " ".join(deps.get("meshes", [])),
        " ".join(deps.get("project_assets", [])),
    ]
    return " ".join(parts).casefold()


def contains_any(blob: str, needles: list[str]) -> bool:
    return any(needle.casefold() in blob for needle in needles)


def tags_from_rules(blob: str, rules: dict[str, list[str]]) -> list[str]:
    return sorted(tag for tag, needles in rules.items() if contains_any(blob, needles))


def style_profiles(asset: dict[str, Any], blob: str) -> list[str]:
    package = asset.get("package", "")
    styles = []
    for style, prefixes in STYLE_RULES:
        if any(prefix.casefold() in package.casefold() or prefix.casefold() in blob for prefix in prefixes):
            styles.append(style)
    return styles or ["UnknownProjectStyle"]


def timing_hints(blob: str, roles: list[str], asset_class: str) -> list[str]:
    hints = set()
    if "weather_loop" in roles or contains_any(blob, ["loop", "rain", "snow", "weather", "ambient"]):
        hints.add("loop_or_ambient")
    if contains_any(blob, ["burst", "impact", "hit", "shot", "blast", "stab"]):
        hints.add("short_burst")
    if contains_any(blob, ["trail", "ribbon", "swing", "slash"]):
        hints.add("motion_attached")
    if contains_any(blob, ["torch", "chimney", "fire", "fog", "smoke"]):
        hints.add("lingering_or_loop")
    if asset_class == "NiagaraEmitter":
        hints.add("emitter_layer")
    return sorted(hints) or ["unknown_timing"]


def usable_as(asset: dict[str, Any], roles: list[str], renderer_hints: list[str]) -> list[str]:
    uses = set()
    asset_class = asset.get("class", "")
    if asset_class == "NiagaraSystem":
        uses.add("primary_template")
    if asset_class == "NiagaraEmitter":
        uses.add("support_layer")
    if asset_class == "NiagaraScript":
        uses.add("module_reference")
    if roles:
        uses.add("reference_source")
    if "mesh" in renderer_hints or "ribbon" in renderer_hints or "sprite" in renderer_hints:
        uses.add("primitive_candidate")
    if "reactive_runtime" in roles:
        uses.add("bp_driven_source")
    return sorted(uses) or ["reference_source"]


def display_name(asset: dict[str, Any], roles: list[str], style: list[str]) -> str:
    name = asset.get("name", "Unnamed")
    main_role = roles[0] if roles else "uncategorized"
    main_style = style[0] if style else "Unknown"
    return f"{name} ({main_role}, {main_style})"


def bp_linkage_hints(blob: str) -> list[str]:
    hints = []
    if contains_any(blob, ["reactive", "rendertexture", "rendertarget", "grid2d", "skeletal", "staticmesh"]):
        hints.append("possible_runtime_input")
    if contains_any(blob, ["animnotify", "socket", "sword", "trailcharacter"]):
        hints.append("possible_anim_or_socket_input")
    if contains_any(blob, ["parametercollection", "mpc", "udw_", "uds_"]):
        hints.append("possible_parameter_collection_input")
    return sorted(hints)


def scratch_pad_hints(asset: dict[str, Any], blob: str) -> list[str]:
    hints = []
    if asset.get("class") in {"NiagaraSystem", "NiagaraEmitter"}:
        hints.append("not_inspected_no_cpp_api")
    if contains_any(blob, ["scratch", "parent_scratch_pad"]):
        hints.append("possible_scratch_pad_reference")
    return hints


def confidence(asset: dict[str, Any], roles: list[str], renderer_hints: list[str], material_roles: list[str]) -> tuple[str, list[str]]:
    reasons = []
    if roles:
        reasons.append("role inferred from name/path/dependencies")
    if renderer_hints:
        reasons.append("renderer hint inferred from module/material/mesh names")
    if material_roles:
        reasons.append("material role inferred from material dependency names")
    if asset.get("class") in {"NiagaraSystem", "NiagaraEmitter"}:
        reasons.append("deep emitter stack not inspected yet")
    if len(reasons) >= 3 and roles and (renderer_hints or material_roles):
        return "medium", reasons
    return "low", reasons or ["insufficient non-C++ evidence"]


def build_signature(asset: dict[str, Any]) -> dict[str, Any]:
    blob = normalized_blob(asset)
    semantic = semantic_blob(asset)
    deps = asset.get("dependency_buckets", {})
    roles = tags_from_rules(semantic, ROLE_RULES)
    renderer_hints = tags_from_rules(blob, RENDERER_HINT_RULES)
    material_roles = tags_from_rules(semantic, MATERIAL_ROLE_RULES)
    mesh_roles = tags_from_rules(" ".join(deps.get("meshes", [])).casefold(), MESH_ROLE_RULES)
    motions = tags_from_rules(semantic, MOTION_RULES)
    styles = style_profiles(asset, semantic)
    conf, reasons = confidence(asset, roles, renderer_hints, material_roles)

    return {
        "object_path": asset.get("object_path", ""),
        "package": asset.get("package", ""),
        "asset_class": asset.get("class", ""),
        "display_name": display_name(asset, roles, styles),
        "aliases": sorted(set([asset.get("name", ""), *roles, *material_roles])),
        "confidence": conf,
        "confidence_reasons": reasons,
        "visual_roles": roles or ["unknown_visual_role"],
        "renderer_hints": renderer_hints or ["unknown_renderer"],
        "motion_hints": motions or ["unknown_motion"],
        "timing_hints": timing_hints(semantic, roles, asset.get("class", "")),
        "style_profiles": styles,
        "material_roles": material_roles,
        "mesh_roles": mesh_roles,
        "bp_linkage_hints": bp_linkage_hints(semantic),
        "scratch_pad_hints": scratch_pad_hints(asset, semantic),
        "usable_as": usable_as(asset, roles, renderer_hints),
        "source_materials": deps.get("materials", [])[:20],
        "source_meshes": deps.get("meshes", [])[:20],
        "source_modules": deps.get("niagara_modules", [])[:30],
    }


def build_index(source: dict[str, Any]) -> dict[str, Any]:
    signatures = [build_signature(asset) for asset in source.get("assets", [])]
    signatures.sort(key=lambda item: (item["asset_class"], item["package"]))
    return {
        "schema_version": 1,
        "generated_from": str(DEFAULT_INPUT),
        "coverage_notes": [
            "This is a no-C++ first pass.",
            "Tags are inferred from names, paths, dependencies, material names, mesh names, and module dependency paths.",
            "Actual emitter stacks, renderer properties, user parameters, and Scratch Pad inputs/outputs require future Niagara Inspector API.",
        ],
        "assets": signatures,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a first-pass structural signature index from Niagara asset dependencies.")
    parser.add_argument("--input", type=Path, default=None, help="Path to niagara_asset_index.json.")
    parser.add_argument("--output", type=Path, default=None, help="Output path for niagara_structural_signature_index.json.")
    parser.add_argument("--summary", action="store_true", help="Print a compact summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root_from(Path.cwd())
    input_path = args.input or root / DEFAULT_INPUT
    output_path = args.output or root / DEFAULT_OUTPUT
    source = json.loads(input_path.read_text(encoding="utf-8"))
    output = build_index(source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        role_counts: dict[str, int] = {}
        style_counts: dict[str, int] = {}
        for asset in output["assets"]:
            for role in asset["visual_roles"]:
                role_counts[role] = role_counts.get(role, 0) + 1
            for style in asset["style_profiles"]:
                style_counts[style] = style_counts.get(style, 0) + 1
        print(json.dumps({
            "output": str(output_path),
            "asset_count": len(output["assets"]),
            "role_counts": dict(sorted(role_counts.items(), key=lambda item: (-item[1], item[0]))),
            "style_counts": dict(sorted(style_counts.items(), key=lambda item: (-item[1], item[0]))),
        }, ensure_ascii=False, indent=2))
    else:
        print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
