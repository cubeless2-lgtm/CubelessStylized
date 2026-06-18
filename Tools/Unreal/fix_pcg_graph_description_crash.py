"""Shorten PCG graph descriptions that can crash UE asset registry dependency scans."""

from __future__ import annotations

import unreal


TARGET_GRAPH = (
    "/Game/Cubeless/PCG/ProductionCandidates/Graphs/"
    "PCG_Cubeless_EcosystemCandidate_SplineEcosystemFalloff"
)

SAFE_DESCRIPTION = (
    "Spline ecosystem candidate. Closed or open source spline drives a local "
    "area grid with distance falloff for grass, trees, and rocks."
)
MAX_SAFE_DESCRIPTION_CHARS = 240


def _read_description(asset):
    try:
        return str(asset.get_editor_property("description") or "")
    except Exception:
        try:
            return str(asset.description or "")
        except Exception:
            return ""


def _write_description(asset, text: str) -> None:
    safe_text = text[:MAX_SAFE_DESCRIPTION_CHARS].rstrip()
    try:
        asset.set_editor_property("description", safe_text)
    except Exception:
        asset.description = safe_text


def _read_dependencies(package_path: str) -> list[str]:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        options = unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True,
            include_hard_package_references=True,
            include_searchable_names=False,
            include_soft_management_references=False,
            include_hard_management_references=False,
        )
        return [str(item) for item in registry.get_dependencies(package_path, options)]
    except TypeError:
        return [str(item) for item in registry.get_dependencies(package_path)]


def main() -> None:
    graph = unreal.EditorAssetLibrary.load_asset(TARGET_GRAPH)
    if not graph:
        raise RuntimeError(f"Could not load PCG graph: {TARGET_GRAPH}")
    if "PCGGraph" not in graph.get_class().get_name():
        raise RuntimeError(f"Target is not a PCG graph: {graph.get_path_name()}")

    old_description = _read_description(graph)
    _write_description(graph, SAFE_DESCRIPTION)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(graph, False)
    new_description = _read_description(graph)
    dependencies = _read_dependencies(TARGET_GRAPH)

    unreal.log(
        "PCG description crash fix: old_len={} new_len={} saved={} dependencies={} target={}".format(
            len(old_description),
            len(new_description),
            bool(saved),
            len(dependencies),
            graph.get_path_name(),
        )
    )
    if len(new_description) > MAX_SAFE_DESCRIPTION_CHARS:
        raise RuntimeError(f"Description is still too long: {len(new_description)}")
    if not saved:
        raise RuntimeError("Failed to save shortened PCG graph description")


if __name__ == "__main__":
    main()
