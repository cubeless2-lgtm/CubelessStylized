"""PCG Execute Python entrypoint for the Cubeless Dungeon V2 prototype."""

import unreal

import CubelessDungeonPCGV2 as dungeon_v2


def _main():
    report = dungeon_v2.run_pcg_bridge_entrypoint()
    unreal.log("CubelessDungeonPCGV2Entrypoint report: {}".format(report.get("pass")))


_main()
