from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_INDEX_PATH = Path("docs/niagara-learning/niagara_generation_index.json")
DEFAULT_OUTPUT_DIR = Path("Saved/MCP_NiagaraGeneration")
DEFAULT_TEMP_ROOT = "/Game/_MCP_Temp/NiagaraGenerated"


CATEGORY_LEXICON = {
    "fire_flame": [
        "fire",
        "flame",
        "torch",
        "ember",
        "burn",
        "ignite",
        "chimney",
        "불",
        "화염",
        "불꽃",
        "횃불",
        "불씨",
        "연소",
    ],
    "smoke_fog": [
        "smoke",
        "fog",
        "mist",
        "cloud",
        "steam",
        "volumetric",
        "연기",
        "안개",
        "구름",
        "수증기",
        "먼지구름",
    ],
    "weather_rain_snow": [
        "rain",
        "snow",
        "storm",
        "weather",
        "drip",
        "puddle",
        "splash",
        "비",
        "눈",
        "폭풍",
        "날씨",
        "물방울",
        "빗방울",
        "웅덩이",
    ],
    "lightning_energy": [
        "lightning",
        "electric",
        "beam",
        "laser",
        "spark",
        "energy",
        "shock",
        "bolt",
        "번개",
        "전기",
        "전격",
        "빔",
        "레이저",
        "스파크",
        "에너지",
        "충격",
    ],
    "aura_glow_magic": [
        "aura",
        "glow",
        "magic",
        "rising",
        "entangle",
        "curse",
        "buff",
        "오라",
        "광휘",
        "마법",
        "주문",
        "버프",
        "저주",
        "상승",
        "속박",
    ],
    "trail_ribbon_motion": [
        "trail",
        "ribbon",
        "slash",
        "swing",
        "run",
        "animtrail",
        "sword",
        "궤적",
        "잔상",
        "베기",
        "참격",
        "스윙",
        "검기",
        "리본",
    ],
    "burst_impact_projectile": [
        "burst",
        "impact",
        "hit",
        "projectile",
        "grenade",
        "explosion",
        "blast",
        "shot",
        "폭발",
        "충돌",
        "타격",
        "피격",
        "투사체",
        "탄환",
        "발사",
        "폭파",
    ],
    "ring_vortex_area": [
        "ring",
        "vortex",
        "radial",
        "circle",
        "disc",
        "torus",
        "area",
        "aoe",
        "장판",
        "원형",
        "고리",
        "소용돌이",
        "범위",
        "광역",
        "마법진",
    ],
    "reactive_interaction": [
        "reactive",
        "interaction",
        "interactive",
        "foliage",
        "painter",
        "fluidgrid",
        "occlusion",
        "반응형",
        "상호작용",
        "잔디",
        "풀",
        "페인트",
        "렌더타겟",
    ],
    "ambient_dust_debris": [
        "dust",
        "debris",
        "leaf",
        "leaves",
        "wind",
        "particlecloud",
        "먼지",
        "파편",
        "낙엽",
        "잎",
        "바람",
        "흙먼지",
    ],
}


COLOR_LEXICON = {
    "blue": ["blue", "cyan", "azure", "푸른", "파란", "청색", "하늘색", "시안"],
    "red": ["red", "crimson", "scarlet", "붉은", "빨간", "적색"],
    "orange": ["orange", "amber", "주황", "호박색"],
    "yellow": ["yellow", "gold", "golden", "노란", "금색", "황금"],
    "green": ["green", "emerald", "녹색", "초록", "에메랄드"],
    "purple": ["purple", "violet", "magenta", "보라", "자주", "마젠타"],
    "white": ["white", "silver", "흰", "하얀", "백색", "은색"],
    "black": ["black", "dark", "검은", "어두운", "암흑"],
}


SHAPE_LEXICON = {
    "ring": ["ring", "circle", "disc", "radial", "aoe", "장판", "원형", "고리", "마법진"],
    "beam": ["beam", "laser", "line", "ray", "빔", "레이저", "광선", "직선"],
    "trail": ["trail", "ribbon", "slash", "swing", "궤적", "잔상", "베기", "검기"],
    "burst": ["burst", "explosion", "blast", "impact", "폭발", "충돌", "타격"],
    "weather": ["rain", "snow", "storm", "비", "눈", "폭풍"],
    "field": ["field", "area", "volume", "fog", "장막", "영역", "범위", "안개"],
}


MOTION_LEXICON = {
    "upward": ["up", "upward", "rise", "rising", "위로", "솟", "상승"],
    "outward": ["out", "outward", "expand", "radial", "퍼지", "확산", "방사"],
    "falling": ["fall", "falling", "drop", "내리", "떨어", "낙하"],
    "swirl": ["swirl", "vortex", "spiral", "소용돌이", "회전", "나선"],
    "follow": ["follow", "attached", "trail", "따라", "부착", "궤적"],
}


@dataclass(frozen=True)
class Match:
    category: str
    score: float
    matched_terms: list[str]


def repo_root_from(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "StylizedCubeless.uproject").exists():
            return candidate
    return current


def normalize(text: str) -> str:
    return text.casefold()


def slugify(text: str, fallback: str = "effect") -> str:
    asciiish = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    if asciiish:
        return asciiish[:48]
    return fallback


def find_terms(prompt: str, terms: list[str]) -> list[str]:
    normalized = normalize(prompt)
    return [term for term in terms if normalize(term) in normalized]


def detect_keyed_values(prompt: str, lexicon: dict[str, list[str]]) -> list[str]:
    found = []
    for key, terms in lexicon.items():
        if find_terms(prompt, terms):
            found.append(key)
    return found


def detect_duration_seconds(prompt: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:sec|secs|second|seconds|s)\b",
        r"(\d+(?:\.\d+)?)\s*초",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def match_categories(prompt: str) -> list[Match]:
    matches = []
    for category, terms in CATEGORY_LEXICON.items():
        matched = find_terms(prompt, terms)
        if matched:
            matches.append(Match(category, float(len(matched) * 10), matched))
    matches.sort(key=lambda item: (-item.score, item.category))
    return matches


def token_overlap_score(prompt: str, value: str) -> float:
    prompt_tokens = set(re.findall(r"[A-Za-z0-9_]+", normalize(prompt)))
    if not prompt_tokens:
        return 0.0
    value_tokens = set(re.findall(r"[A-Za-z0-9_]+", normalize(value)))
    return float(len(prompt_tokens & value_tokens))


def template_score(prompt: str, template: dict[str, Any], desired_shapes: list[str]) -> float:
    score = float(template.get("reuse_score", 0.0))
    haystack = " ".join(
        [
            str(template.get("name", "")),
            str(template.get("object_path", "")),
            " ".join(template.get("categories", [])),
        ]
    )
    score += token_overlap_score(prompt, haystack) * 4.0
    lowered = normalize(haystack)
    if "ring" in desired_shapes and any(term in lowered for term in ["ring", "radial", "vortex"]):
        score += 12.0
    if "beam" in desired_shapes and any(term in lowered for term in ["beam", "laser", "lightning"]):
        score += 12.0
    if "trail" in desired_shapes and any(term in lowered for term in ["trail", "ribbon", "swing", "slash"]):
        score += 12.0
    if "burst" in desired_shapes and any(term in lowered for term in ["burst", "blast", "impact"]):
        score += 10.0
    return round(score, 3)


def choose_templates(prompt: str, index: dict[str, Any], categories: list[str], shapes: list[str]) -> list[dict[str, Any]]:
    category_to_templates = index.get("category_to_best_templates", {})
    candidates_by_path: dict[str, dict[str, Any]] = {}
    for category in categories:
        for template in category_to_templates.get(category, []):
            path = str(template.get("object_path", ""))
            if not path:
                continue
            candidate = dict(template)
            candidate["matched_category"] = category
            candidate["selection_score"] = template_score(prompt, candidate, shapes)
            old = candidates_by_path.get(path)
            if old is None or candidate["selection_score"] > old["selection_score"]:
                candidates_by_path[path] = candidate

    candidates = list(candidates_by_path.values())
    candidates.sort(key=lambda item: (-float(item.get("selection_score", 0.0)), item.get("object_path", "")))
    return candidates


def choose_emitters(index: dict[str, Any], categories: list[str], limit: int = 8) -> list[dict[str, Any]]:
    emitters = []
    for emitter in index.get("emitter_library", []):
        if any(category in emitter.get("categories", []) for category in categories):
            emitters.append(emitter)
    emitters.sort(key=lambda item: (item.get("package", ""), item.get("name", "")))
    return emitters[:limit]


def choose_parameter_collections(index: dict[str, Any], categories: list[str]) -> list[dict[str, Any]]:
    collections = []
    for collection in index.get("parameter_collections", []):
        if any(category in collection.get("categories", []) for category in categories):
            collections.append(collection)
    return collections


def build_plan(prompt: str, index: dict[str, Any], temp_root: str, output_name: str | None = None) -> dict[str, Any]:
    category_matches = match_categories(prompt)
    shapes = detect_keyed_values(prompt, SHAPE_LEXICON)
    colors = detect_keyed_values(prompt, COLOR_LEXICON)
    motions = detect_keyed_values(prompt, MOTION_LEXICON)
    duration = detect_duration_seconds(prompt)

    categories = [match.category for match in category_matches]
    if "ring" in shapes and "ring_vortex_area" not in categories:
        categories.append("ring_vortex_area")
    if "burst" in shapes and "burst_impact_projectile" not in categories:
        categories.append("burst_impact_projectile")
    if not categories:
        categories = ["uncategorized"]

    templates = choose_templates(prompt, index, categories, shapes)
    primary = templates[0] if templates else None
    slug = output_name or slugify(prompt)
    asset_name = "NG_" + slug
    destination_package = f"{temp_root.rstrip('/')}/{slug}/{asset_name}"

    support_categories = [category for category in categories if primary is None or category != primary.get("matched_category")]
    support_templates = []
    seen = {primary.get("object_path")} if primary else set()
    for template in templates[1:8]:
        path = template.get("object_path")
        if path in seen:
            continue
        if template.get("matched_category") in support_categories or len(support_templates) < 3:
            support_templates.append(template)
            seen.add(path)

    plan = {
        "request": prompt,
        "parsed_intent": {
            "category_matches": [match.__dict__ for match in category_matches],
            "categories": categories,
            "colors": colors,
            "shapes": shapes,
            "motions": motions,
            "duration_seconds": duration,
        },
        "generation": {
            "mode": "template_duplicate_plan",
            "destination_package": destination_package,
            "destination_object": f"{destination_package}.{asset_name}",
            "source_system": primary,
            "support_templates": support_templates,
            "candidate_emitters": choose_emitters(index, categories),
            "candidate_parameter_collections": choose_parameter_collections(index, categories),
            "initial_adjustments": suggested_adjustments(colors, shapes, motions, duration),
        },
        "safety": {
            "source_policy": index.get("source_policy", "Treat original Niagara assets as read-only."),
            "write_scope": f"Duplicate only into {temp_root.rstrip('/')}/<slug>/ by default.",
            "requires_unreal_editing_api_for_deep_changes": True,
        },
    }
    return plan


def suggested_adjustments(
    colors: list[str],
    shapes: list[str],
    motions: list[str],
    duration: float | None,
) -> list[str]:
    suggestions = []
    if colors:
        suggestions.append(f"Prefer color parameter/material tint near: {', '.join(colors)}.")
    if duration is not None:
        suggestions.append(f"Set system or emitter lifetime/duration near {duration:g} seconds where exposed.")
    if "ring" in shapes:
        suggestions.append("Prefer ring/radial/vortex support templates for ground or area readability.")
    if "beam" in shapes:
        suggestions.append("Preserve beam/ribbon renderer dependencies and avoid replacing beam materials blindly.")
    if "trail" in shapes:
        suggestions.append("Preserve ribbon renderer modules and attach/follow behavior.")
    if "upward" in motions:
        suggestions.append("Favor upward velocity, rising spawn, or spark lift modules in the duplicate.")
    if "outward" in motions:
        suggestions.append("Favor radial expansion or burst velocity in the duplicate.")
    if not suggestions:
        suggestions.append("Start from the selected source system duplicate, then inspect exposed Niagara parameters.")
    return suggestions


def unreal_python_for_duplicate(plan: dict[str, Any]) -> str:
    source = plan["generation"].get("source_system") or {}
    source_path = source.get("object_path")
    destination_package = plan["generation"]["destination_package"]
    request = plan["request"]
    if not source_path:
        raise RuntimeError("Cannot emit Unreal Python without a source_system candidate.")

    return f'''from __future__ import annotations

import json
import os
import unreal

REQUEST = {request!r}
SOURCE_SYSTEM = {source_path!r}
DESTINATION_PACKAGE = {destination_package!r}


def duplicate_template() -> dict:
    report = {{
        "request": REQUEST,
        "source_system": SOURCE_SYSTEM,
        "destination_package": DESTINATION_PACKAGE,
        "status": "pending",
        "notes": [
            "Original Niagara asset is treated as read-only.",
            "This first-pass generator duplicates the closest template only.",
            "Deep Niagara module/parameter editing should run after system info is available.",
        ],
    }}
    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE_SYSTEM):
        report["status"] = "source_missing"
        return report

    if unreal.EditorAssetLibrary.does_asset_exist(DESTINATION_PACKAGE):
        report["status"] = "already_exists"
        report["destination_object"] = DESTINATION_PACKAGE + "." + DESTINATION_PACKAGE.rsplit("/", 1)[-1]
        return report

    duplicated = unreal.EditorAssetLibrary.duplicate_asset(SOURCE_SYSTEM, DESTINATION_PACKAGE)
    if not duplicated:
        report["status"] = "duplicate_failed"
        return report

    saved = unreal.EditorAssetLibrary.save_asset(DESTINATION_PACKAGE, only_if_is_dirty=True)
    report["status"] = "duplicated"
    report["destination_object"] = duplicated.get_path_name()
    report["duplicated_class"] = duplicated.get_class().get_name()
    report["saved"] = bool(saved)
    return report


result = duplicate_template()
saved_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
report_dir = os.path.join(saved_dir, "MCP_NiagaraGeneration")
os.makedirs(report_dir, exist_ok=True)
report_path = os.path.join(report_dir, DESTINATION_PACKAGE.rsplit("/", 2)[-2] + "_duplicate_report.json")
with open(report_path, "w", encoding="utf-8") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
unreal.log("NIAGARA_NL_GENERATION_REPORT=" + json.dumps(result, ensure_ascii=False))
'''


def write_outputs(plan: dict[str, Any], output_dir: Path, emit_unreal_python: bool) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = plan["generation"]["destination_package"].split("/")[-2]
    plan_path = output_dir / f"{slug}_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outputs = {"plan": str(plan_path)}
    if emit_unreal_python:
        script_path = output_dir / f"{slug}_duplicate_unreal.py"
        script_path.write_text(unreal_python_for_duplicate(plan), encoding="utf-8")
        outputs["unreal_python"] = str(script_path)
    return outputs


def load_index(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a safe Niagara generation plan from a natural-language prompt.",
    )
    parser.add_argument("prompt", nargs="?", default=None, help="Natural-language effect request.")
    parser.add_argument("--prompt-file", type=Path, default=None, help="UTF-8 text file containing the prompt.")
    parser.add_argument("--index", type=Path, default=None, help="Path to niagara_generation_index.json.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for generated plan files.")
    parser.add_argument("--temp-root", default=DEFAULT_TEMP_ROOT, help="Unreal package root for generated duplicates.")
    parser.add_argument("--output-name", default=None, help="ASCII asset slug to use instead of deriving one from the prompt.")
    parser.add_argument("--emit-unreal-python", action="store_true", help="Also write an Unreal Python duplicate script.")
    parser.add_argument("--print-json", action="store_true", help="Print the full plan JSON.")
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
    index_path = args.index or root / DEFAULT_INDEX_PATH
    output_dir = args.output_dir or root / DEFAULT_OUTPUT_DIR
    index = load_index(index_path)
    plan = build_plan(prompt, index, args.temp_root, args.output_name)
    outputs = write_outputs(plan, output_dir, args.emit_unreal_python)
    if args.print_json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        source = plan["generation"].get("source_system") or {}
        print(f"Plan: {outputs['plan']}")
        if "unreal_python" in outputs:
            print(f"UnrealPython: {outputs['unreal_python']}")
        print(f"Source: {source.get('object_path', 'NONE')}")
        print(f"Destination: {plan['generation']['destination_package']}")
        print(f"Categories: {', '.join(plan['parsed_intent']['categories'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
