"""Path helpers for Cubeless project documents migrated into CubelessOps."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def cubeless_ops_root(project_root: Path = PROJECT_ROOT) -> Path:
    """Resolve the sibling CubelessOps checkout without assuming a drive."""

    candidates: list[Path] = []
    candidates.append(project_root.parent / "CubelessOps")
    env_root = os.environ.get("CUBELESS_OPS_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())

    for candidate in candidates:
        if (candidate / "AGENTS.md").is_file():
            return candidate.resolve()

    return candidates[-1].resolve()


def cubeless_stylized_docs_root(project_root: Path = PROJECT_ROOT) -> Path:
    return cubeless_ops_root(project_root) / "docs" / "projects" / "cubeless-stylized"


def project_doc_path(path_text: str, project_root: Path = PROJECT_ROOT) -> Path:
    """Map legacy CubelessStylized docs/foo paths to their Ops locations."""

    rel = path_text.replace("\\", "/").strip("/")
    docs_root = cubeless_stylized_docs_root(project_root)

    if rel == "docs/work-log.md":
        return docs_root / "logs" / "work-log.md"
    if rel == "docs/interaction-field-system.md":
        return docs_root / "systems" / "interaction-field-system.md"
    if rel == "docs/pcg-cpp-improvement-backlog.md":
        return docs_root / "learning" / "pcg" / "pcg-cpp-improvement-backlog.md"
    if rel.startswith("docs/pcg-dungeon"):
        return docs_root / "systems" / "pcg-dungeon" / Path(rel).name
    if rel.startswith("docs/stackobot"):
        return docs_root / "studies" / "stackobot-animation" / Path(rel).name
    if rel.startswith("docs/uds-analysis/"):
        return docs_root / "studies" / "uds-analysis" / rel.removeprefix("docs/uds-analysis/")

    migrated_files = {
        "docs/agent-workflow.md": docs_root / "legacy" / "agent-workflow.md",
        "docs/git-hooks.md": docs_root / "hooks" / "git-hooks.md",
        "docs/unreal-cpp-conventions.md": docs_root / "reviews" / "unreal-cpp-conventions.md",
        "docs/cloud-plane-lightpacked-workflow.md": docs_root
        / "learning"
        / "sky-vfx"
        / "cloud-plane-lightpacked-workflow.md",
        "docs/skysystem-anime-sky.md": docs_root / "learning" / "sky-vfx" / "skysystem-anime-sky.md",
        "docs/skysystem-v2-plan.md": docs_root / "learning" / "sky-vfx" / "skysystem-v2-plan.md",
        "docs/stylized-sky-plugin.md": docs_root / "learning" / "sky-vfx" / "stylized-sky-plugin.md",
        "docs/ultra-volumetrics-modularization.md": docs_root
        / "learning"
        / "sky-vfx"
        / "ultra-volumetrics-modularization.md",
        "docs/silhouette-pom-research.md": docs_root
        / "learning"
        / "materials"
        / "silhouette-pom-research.md",
        "docs/pcgstudy-source-independent-authoring.md": docs_root
        / "learning"
        / "pcg"
        / "pcgstudy-source-independent-authoring.md",
        "docs/reference-index/README.md": docs_root / "reference-index" / "README.md",
        "docs/reference-index/indexing-candidates.md": docs_root / "reference-index" / "indexing-candidates.md",
        "docs/research/stylized-volumetric-clouds.html": docs_root
        / "research"
        / "stylized-volumetric-clouds.html",
        "docs/research/subculture-game-rendering-tech.html": docs_root
        / "research"
        / "subculture-game-rendering-tech.html",
    }
    if rel in migrated_files:
        return migrated_files[rel]

    return project_root / rel


def project_doc_display(path: Path, project_root: Path = PROJECT_ROOT) -> str:
    """Return a compact display path for reports."""

    docs_root = cubeless_stylized_docs_root(project_root)
    try:
        return path.relative_to(docs_root).as_posix()
    except ValueError:
        pass
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def project_docs_glob(glob_pattern: str, project_root: Path = PROJECT_ROOT) -> list[Path]:
    """Glob migrated project docs while preserving legacy default globs."""

    docs_root = cubeless_stylized_docs_root(project_root)
    if glob_pattern.startswith("stackobot"):
        return sorted((docs_root / "studies" / "stackobot-animation").glob(glob_pattern))
    if glob_pattern.startswith("pcg-dungeon"):
        return sorted((docs_root / "systems" / "pcg-dungeon").glob(glob_pattern))
    legacy_glob_roots = {
        "uds-analysis/": docs_root / "studies" / "uds-analysis",
        "reference-index/": docs_root / "reference-index",
        "research/": docs_root / "research",
    }
    for prefix, root in legacy_glob_roots.items():
        if glob_pattern.startswith(prefix):
            return sorted(root.glob(glob_pattern.removeprefix(prefix)))
    if glob_pattern == "**/*.md":
        return sorted(docs_root.rglob("*.md"))
    return sorted(docs_root.rglob(glob_pattern))
