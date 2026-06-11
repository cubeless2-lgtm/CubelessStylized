from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SIGNATURE_INDEX = Path("docs/niagara-learning/niagara_structural_signature_index.json")
DEFAULT_MATERIAL_INDEX = Path("docs/niagara-learning/niagara_material_style_index.json")
DEFAULT_OUTPUT_DIR = Path("Saved/MCP_NiagaraGeneration")
TEMP_ROOT = "/Game/_MCP_Temp/NiagaraGenerated"
PRODUCTION_ROOT = "/Game/Cubeless/FX/Generated"
REVIEW_MAP = "/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'"


ROLE_TERMS = {
    "ground_area": ["area", "field", "ring", "circle", "aoe", "ground", "장판", "원형", "범위", "마법진"],
    "lightning_arc": ["lightning", "electric", "beam", "laser", "spark", "번개", "전기", "전격", "빔", "레이저"],
    "spark_spray": ["spark", "ember", "spray", "튀", "스파크", "불씨"],
    "smoke_volume": ["smoke", "fog", "mist", "dust", "연기", "안개", "먼지"],
    "fire_flame": ["fire", "flame", "torch", "불", "화염", "불꽃", "횃불"],
    "ribbon_trail": ["trail", "ribbon", "slash", "swing", "궤적", "잔상", "검기", "베기"],
    "impact_burst": ["burst", "impact", "explosion", "blast", "hit", "폭발", "충돌", "타격"],
    "weather_loop": ["rain", "snow", "storm", "비", "눈", "폭풍"],
    "reactive_runtime": ["reactive", "interaction", "foliage", "반응형", "상호작용", "잔디"],
}


MATERIAL_TERMS = {
    "additive_glow": ["glow", "light", "emissive", "빛", "광휘", "발광"],
    "stylized_lightning": ["lightning", "electric", "번개", "전기", "전격"],
    "soft_smoke": ["smoke", "fog", "mist", "연기", "안개"],
    "radial_shockwave": ["shockwave", "ring", "radial", "충격파", "원형", "장판"],
    "ribbon_slash": ["trail", "ribbon", "slash", "검기", "베기", "궤적"],
    "spark_sprite": ["spark", "ember", "스파크", "불씨"],
    "fire_flipbook": ["fire", "flame", "불", "화염"],
    "water_splash": ["water", "rain", "splash", "물", "비", "물방울"],
}


COLOR_TERMS = {
    "blue": ["blue", "cyan", "푸른", "파란", "청색", "하늘색"],
    "red": ["red", "crimson", "붉은", "빨간", "적색"],
    "purple": ["purple", "violet", "magenta", "보라", "자주"],
    "green": ["green", "emerald", "녹색", "초록"],
    "yellow": ["yellow", "gold", "노란", "금색", "황금"],
    "orange": ["orange", "amber", "주황"],
    "black": ["black", "dark", "검은", "어두운", "암흑"],
    "white": ["white", "silver", "흰", "하얀", "은색"],
}


MOTION_TERMS = {
    "radial_expand": ["expand", "outward", "radial", "퍼지", "확산", "방사"],
    "upward_spark": ["upward", "rise", "위로", "상승", "솟"],
    "falling": ["fall", "falling", "내리", "떨어", "낙하"],
    "follow_or_attached": ["follow", "attached", "trail", "따라", "부착", "궤적"],
    "swirl_or_vortex": ["swirl", "vortex", "spiral", "소용돌이", "회전", "나선"],
}


def repo_root_from(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "StylizedCubeless.uproject").exists():
            return candidate
    return current


def contains_any(prompt: str, terms: list[str]) -> bool:
    lowered = prompt.casefold()
    return any(term.casefold() in lowered for term in terms)


def detect_tags(prompt: str, table: dict[str, list[str]]) -> list[str]:
    return sorted(tag for tag, terms in table.items() if contains_any(prompt, terms))


def detect_duration(prompt: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:sec|secs|second|seconds|s)\b",
        r"(\d+(?:\.\d+)?)\s*초",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def slugify(text: str, fallback: str = "niagara_recipe") -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return (slug or fallback)[:64]


def score_signature(asset: dict[str, Any], desired_roles: list[str], motions: list[str]) -> float:
    score = 0.0
    roles = set(asset.get("visual_roles", []))
    motion_hints = set(asset.get("motion_hints", []))
    usable = set(asset.get("usable_as", []))
    materials = asset.get("source_materials", [])
    score += len(roles.intersection(desired_roles)) * 25.0
    score += len(motion_hints.intersection(motions)) * 8.0
    score += len(materials) * 0.3
    if "primary_template" in usable:
        score += 12.0
    if "support_layer" in usable:
        score += 5.0
    if asset.get("confidence") == "medium":
        score += 4.0
    return round(score, 3)


def choose_sources(signatures: list[dict[str, Any]], desired_roles: list[str], motions: list[str]) -> list[dict[str, Any]]:
    candidates = []
    for asset in signatures:
        score = score_signature(asset, desired_roles, motions)
        if score <= 0:
            continue
        item = dict(asset)
        item["recipe_score"] = score
        candidates.append(item)
    candidates.sort(key=lambda item: (-item["recipe_score"], item.get("object_path", "")))
    return candidates


def score_material(material: dict[str, Any], desired_material_roles: list[str], source_styles: list[str]) -> float:
    roles = set(material.get("material_roles", []))
    styles = set(material.get("style_profiles", []))
    score = len(roles.intersection(desired_material_roles)) * 20.0
    score += len(styles.intersection(source_styles)) * 4.0
    score += min(material.get("used_by_count", 0), 20) * 0.2
    if material.get("recommended_operation") == "duplicate_material_instance":
        score += 4.0
    if material.get("confidence") == "medium":
        score += 2.0
    return round(score, 3)


def choose_materials(materials: list[dict[str, Any]], desired_material_roles: list[str], source_styles: list[str]) -> list[dict[str, Any]]:
    candidates = []
    for material in materials:
        score = score_material(material, desired_material_roles, source_styles)
        if score <= 0:
            continue
        item = dict(material)
        item["recipe_score"] = score
        candidates.append(item)
    candidates.sort(key=lambda item: (-item["recipe_score"], item.get("material_path", "")))
    return candidates


def build_layers(sources: list[dict[str, Any]], desired_roles: list[str]) -> list[dict[str, Any]]:
    layers = []
    if not sources:
        return [
            {
                "role": "missing_primary",
                "operation": "defer_until_api_available",
                "source": "",
                "notes": ["No structural signature source matched the request."],
            }
        ]

    primary = next((item for item in sources if "primary_template" in item.get("usable_as", [])), sources[0])
    layers.append(
        {
            "role": "primary_template",
            "operation": "duplicate_system",
            "source": primary["object_path"],
            "notes": [
                f"Matched roles: {', '.join([role for role in primary.get('visual_roles', []) if role in desired_roles]) or 'inferred closest source'}",
                f"Confidence: {primary.get('confidence', 'unknown')}",
            ],
        }
    )

    seen = {primary["object_path"]}
    for source in sources:
        if source["object_path"] in seen:
            continue
        if len(layers) >= 5:
            break
        operation = "duplicate_emitter" if "support_layer" in source.get("usable_as", []) else "reuse_source_as_reference"
        layers.append(
            {
                "role": "support_layer",
                "operation": operation,
                "source": source["object_path"],
                "notes": [
                    f"Visual roles: {', '.join(source.get('visual_roles', []))}",
                    "No-C++ recipe only. Actual add/remove emitter execution waits for Niagara edit API.",
                ],
            }
        )
        seen.add(source["object_path"])
    return layers


def build_material_plan(materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan = []
    for material in materials[:8]:
        plan.append(
            {
                "role": ",".join(material.get("material_roles", [])),
                "operation": material.get("recommended_operation", "inspect_before_use"),
                "source_material": material["material_path"],
                "target_material": "",
                "parameter_overrides": {},
            }
        )
    if not plan:
        plan.append(
            {
                "role": "missing_material_style",
                "operation": "defer_until_material_analysis",
                "source_material": "",
                "target_material": "",
                "parameter_overrides": {},
            }
        )
    return plan


def build_user_parameters(colors: list[str], duration: float | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if colors:
        params["User.Gen_ColorName"] = colors[0]
    if duration is not None:
        params["User.Gen_Duration"] = duration
    params["User.Gen_ReviewMap"] = REVIEW_MAP
    return params


def build_recipe(prompt: str, signatures: dict[str, Any], material_index: dict[str, Any], output_name: str | None) -> dict[str, Any]:
    desired_roles = detect_tags(prompt, ROLE_TERMS) or ["unknown_visual_role"]
    material_roles = detect_tags(prompt, MATERIAL_TERMS) or ["additive_glow"]
    colors = detect_tags(prompt, COLOR_TERMS)
    motions = detect_tags(prompt, MOTION_TERMS)
    duration = detect_duration(prompt)
    sources = choose_sources(signatures.get("assets", []), desired_roles, motions)
    source_styles = sorted({style for source in sources[:5] for style in source.get("style_profiles", [])})
    materials = choose_materials(material_index.get("materials", []), material_roles, source_styles)
    slug = output_name or slugify(prompt)

    risk_notes = [
        "Recipe is no-C++ and inference-based.",
        "Original source assets are read-only.",
        "Emitter add/remove, renderer material replacement, and Scratch Pad reuse require future Niagara edit APIs.",
    ]
    for source in sources[:5]:
        if source.get("bp_linkage_hints"):
            risk_notes.append(f"BP linkage hint on {source['object_path']}: {', '.join(source['bp_linkage_hints'])}")
        if source.get("scratch_pad_hints"):
            risk_notes.append(f"Scratch Pad not deeply inspected on {source['object_path']}.")

    return {
        "schema_version": 1,
        "request": prompt,
        "parsed_intent": {
            "visual_roles": desired_roles,
            "material_roles": material_roles,
            "colors": colors,
            "motions": motions,
            "duration_seconds": duration,
        },
        "write_scope": {
            "temporary_root": f"{TEMP_ROOT}/{slug}",
            "production_root": PRODUCTION_ROOT,
            "source_policy": "Original Niagara, Material, Blueprint, Texture, and Mesh assets are read-only references.",
        },
        "reference_analysis": {
            "primary_sources": [source["object_path"] for source in sources[:3]],
            "support_sources": [source["object_path"] for source in sources[3:10]],
            "material_sources": [material["material_path"] for material in materials[:10]],
            "bp_linkage_sources": [
                source["object_path"]
                for source in sources[:10]
                if source.get("bp_linkage_hints")
            ],
            "scratch_pad_sources": [
                source["object_path"]
                for source in sources[:10]
                if source.get("scratch_pad_hints")
            ],
            "risk_notes": risk_notes,
        },
        "layers": build_layers(sources, desired_roles),
        "material_plan": build_material_plan(materials),
        "user_parameters": build_user_parameters(colors, duration),
        "validation": {
            "required_checks": [
                "load_generated_asset",
                "compile_or_collect_compile_status",
                "verify_no_source_asset_dirty",
                "verify_niagara_preview_lab_map_without_same_session_reload",
                "spawn_preview_actor_in_niagara_preview_lab",
                "capture_one_quick_preview_from_first_reviewable_bookmark",
                "capture_frame_sequence_for_timing_sensitive_effects",
            ],
            "review_map": REVIEW_MAP,
            "preview_system": "Niagara Preview Lab",
            "camera_bookmarks": {
                "1": "near",
                "2": "mid",
                "3": "far",
            },
            "quick_preview_fallback": ["1", "2", "3"],
            "quick_preview_rule": "Capture one screenshot by default. Start at bookmark 1. If the effect is too large, clipped, invisible, or not reviewable, use bookmark 2. If bookmark 2 still fails, use bookmark 3 and record the selected bookmark. Capture all three only for explicit distance comparison.",
            "video_review_rule": "For timing-sensitive Niagara such as sword trails or slash ribbons, capture a PNG frame sequence first. Convert to video only after the frame sequence is verified.",
            "map_reload_safety_rule": "Niagara Preview Lab must not reload the review map from the same Unreal Python session after preview actors or world references exist. Reuse the loaded map, delete preview actors by prefix, and restart Unreal if a full reset is needed.",
            "preview_frames_seconds": [0.5, 1.0, duration if duration else 2.0],
            "review_gate": "Ieta reviews request match, stylized readability, BP/User parameter safety, material fit, selected bookmark screenshot, and timing frame sequence when needed before production promotion.",
        },
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a first-pass generative Niagara recipe from structural and material indices.")
    parser.add_argument("prompt", nargs="?", default=None)
    parser.add_argument("--prompt-file", type=Path, default=None)
    parser.add_argument("--signature-index", type=Path, default=None)
    parser.add_argument("--material-index", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--output-name", default=None)
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        raise SystemExit("Provide a prompt argument or --prompt-file.")

    root = repo_root_from(Path.cwd())
    signature_path = args.signature_index or root / DEFAULT_SIGNATURE_INDEX
    material_path = args.material_index or root / DEFAULT_MATERIAL_INDEX
    output_dir = args.output_dir or root / DEFAULT_OUTPUT_DIR
    recipe = build_recipe(prompt, load_json(signature_path), load_json(material_path), args.output_name)

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = args.output_name or slugify(prompt)
    output_path = output_dir / f"{slug}_generation_recipe.json"
    output_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.print_json:
        print(json.dumps(recipe, ensure_ascii=False, indent=2))
    else:
        print(f"Recipe: {output_path}")
        print(f"Primary: {recipe['layers'][0]['source'] if recipe['layers'] else 'NONE'}")
        print(f"Roles: {', '.join(recipe['parsed_intent']['visual_roles'])}")
        print(f"Preview system: {recipe['validation']['preview_system']}")
        print(f"Review map: {recipe['validation']['review_map']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
