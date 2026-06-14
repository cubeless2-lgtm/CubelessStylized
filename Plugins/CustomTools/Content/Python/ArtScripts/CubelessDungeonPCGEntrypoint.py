"""PCG Execute Python entrypoint for the Cubeless Geometry Script dungeon MVP."""

import os
import runpy

import unreal


def _main():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CubelessDungeonPCG.py")
    module = runpy.run_path(script_path)
    actor = module["_find_pcg_bridge_actor"]()
    config = module["_parse_dungeon_config_from_actor"](actor)
    report = module["spawn_validation_dungeon"](source="pcg_bridge", config=config)
    unreal.log("CubelessDungeonPCGEntrypoint report: {}".format(report.get("pass")))


_main()
