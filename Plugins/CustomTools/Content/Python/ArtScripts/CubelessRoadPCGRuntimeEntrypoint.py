"""PCG Execute Python guard for Cubeless forest-road runtime authoring."""

import os
import runpy

import unreal


def _main():
    script_path = os.path.join(
        unreal.Paths.project_dir(),
        "Plugins",
        "CustomTools",
        "Content",
        "Python",
        "ArtScripts",
        "CubelessRoadPCG.py",
    )
    module = runpy.run_path(script_path)
    report = module["write_runtime_road_bridge_guard_report"]()
    unreal.log(
        "CubelessRoadPCGRuntimeEntrypoint skipped legacy road actor generation: {}".format(
            report.get("report_path")
        )
    )


_main()
