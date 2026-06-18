import os
import sys
import traceback
import importlib
import json

import unreal


MENU_OWNER = "CubelessPythonTools"
MAIN_MENU_NAME = "LevelEditor.MainMenu"
ROOT_MENU_NAME = "Cubeless"
SECTION_NAME = "Scripts"

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)


def _log_exception(context):
    unreal.log_error("{}\n{}".format(context, traceback.format_exc()))


def _python_command(function_name, *args):
    args_text = ", ".join(repr(arg) for arg in args)
    return "from ArtScripts import RegisterMenu; RegisterMenu.{}({})".format(function_name, args_text)


def _add_python_entry(menu, name, label, tooltip, command, section_name=SECTION_NAME):
    try:
        entry = unreal.ToolMenuEntry(
            name=name,
            owner=MENU_OWNER,
            type=unreal.MultiBlockType.MENU_ENTRY
        )
    except Exception:
        entry = unreal.ToolMenuEntry(
            name=name,
            type=unreal.MultiBlockType.MENU_ENTRY
        )

    entry.set_label(label)
    entry.set_tool_tip(tooltip)
    entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, "", command)
    menu.add_menu_entry(section_name, entry)


def open_editor_utility(asset_path):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not asset:
        unreal.EditorDialog.show_message("Error", "Asset not found:\n{}".format(asset_path), unreal.AppMsgType.OK)
        return

    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    if not subsystem:
        unreal.EditorDialog.show_message("Error", "EditorUtilitySubsystem is not available.", unreal.AppMsgType.OK)
        return

    subsystem.spawn_and_register_tab(asset)


def open_asset(asset_path):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not asset:
        unreal.EditorDialog.show_message("Error", "Asset not found:\n{}".format(asset_path), unreal.AppMsgType.OK)
        return

    subsystem = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
    if subsystem:
        subsystem.open_editor_for_assets([asset])


def open_foliage_sample_map():
    map_path = "/Game/EL/Maps/SampleMap/EL_Foliage_InteractionSampleMap/EL_Foliage_InteractionSampleMap"

    if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        unreal.EditorDialog.show_message("Error", "Level not found:\n{}".format(map_path), unreal.AppMsgType.OK)
        return

    result = unreal.EditorDialog.show_message(
        "레벨 열기",
        "EL_Foliage_InteractionSampleMap 레벨을 여시겠습니까?",
        unreal.AppMsgType.YES_NO
    )

    if result != unreal.AppReturnType.YES:
        return

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if level_subsystem and hasattr(level_subsystem, "load_level"):
        level_subsystem.load_level(map_path)
    else:
        unreal.EditorLevelLibrary.load_level(map_path)


def apply_cubeless_ed_authoring_selector():
    from ArtScripts import CubelessEDPCG
    CubelessEDPCG.apply_authoring_selectors_from_menu()


def regenerate_pcg_dungeon_v2_from_bp_controller(show_dialog=True):
    from ArtScripts import CubelessDungeonPCGV2

    dungeon_v2 = importlib.reload(CubelessDungeonPCGV2)
    try:
        result = dungeon_v2.begin_generation_refresh_with_bp_controller(
            keep_existing_output=False,
            save_dirty_packages=True,
        )
        sync = result.get("bp_controller_sync", {})
        controller_config = sync.get("controller_config", {})
        config = controller_config.get("config", {})
        clamped_values = controller_config.get("clamped_values", [])
        layout_adjustments = sync.get("layout_resolution", {}).get("adjustments", [])
        requested = bool(
            result.get("status") == "generation_requested"
            and sync.get("pass")
            and result.get("native_output_begin", {}).get("generate_request", {}).get("ok")
        )
        summary = {
            "success": requested,
            "status": result.get("status"),
            "controller_label": sync.get("controller_label"),
            "bp_controller_sync_pass": bool(sync.get("pass")),
            "room_count": config.get("room_count"),
            "seed": config.get("seed"),
            "use_ceiling": config.get("use_ceiling"),
            "clamped_values": clamped_values,
            "layout_adjustments": layout_adjustments,
            "output_requested": result.get("native_output_begin", {}).get("generate_request", {}).get("ok"),
            "report_path": result.get("report_path"),
        }
        unreal.log("Cubeless PCG Dungeon V2 regenerate from BP: " + json.dumps(summary, ensure_ascii=False))
        if show_dialog:
            if requested:
                clamp_message = ""
                if clamped_values:
                    clamp_lines = [
                        "- {variable}: {from} -> {to}".format(**entry)
                        for entry in clamped_values
                    ]
                    clamp_message = "\nClamped values:\n" + "\n".join(clamp_lines) + "\n"
                if layout_adjustments:
                    layout_lines = [
                        "- {variable}: {from} -> {to}".format(**entry)
                        for entry in layout_adjustments
                        if "variable" in entry and "from" in entry and "to" in entry
                    ]
                    if layout_lines:
                        clamp_message += "\nLayout adjustments:\n" + "\n".join(layout_lines) + "\n"
                message = (
                    "Regeneration requested from BP controller.\n\n"
                    "Controller: {}\nSeed: {}\nRoomCount: {}\nUseCeiling: {}\n{}"
                    "\n"
                    "Wait a moment for PCG NativeOutput to finish updating."
                ).format(
                    sync.get("controller_label"),
                    config.get("seed"),
                    config.get("room_count"),
                    config.get("use_ceiling"),
                    clamp_message,
                )
                unreal.EditorDialog.show_message("PCG Dungeon V2", message, unreal.AppMsgType.OK)
            else:
                message = "Regeneration request failed.\n\n{}".format(json.dumps(summary, indent=2, ensure_ascii=False))
                unreal.EditorDialog.show_message("PCG Dungeon V2 Error", message, unreal.AppMsgType.OK)
        return summary
    except Exception:
        _log_exception("Cubeless PCG Dungeon V2 regenerate from BP failed")
        if show_dialog:
            unreal.EditorDialog.show_message(
                "PCG Dungeon V2 Error",
                "Regeneration failed. Check the Output Log for the Python traceback.",
                unreal.AppMsgType.OK,
            )
        return {"success": False, "error": traceback.format_exc()}


def _register_menu():
    unreal.log("Cubeless: registering Python tool menu")
    menus = unreal.ToolMenus.get()

    try:
        menus.unregister_owner_by_name(MENU_OWNER)
    except Exception:
        unreal.log_warning("Cubeless: previous Python tool menu owner was not registered")

    main_menu = menus.find_menu(MAIN_MENU_NAME)
    if not main_menu:
        unreal.log_warning("Cubeless: failed to find menu '{}'".format(MAIN_MENU_NAME))
        return

    cubeless_menu = main_menu.add_sub_menu(
        owner=MENU_OWNER,
        section_name=ROOT_MENU_NAME,
        name=ROOT_MENU_NAME,
        label=ROOT_MENU_NAME,
        tool_tip="Cubeless tools"
    )
    cubeless_menu.add_section(SECTION_NAME, SECTION_NAME)

    _add_python_entry(
        cubeless_menu,
        "Python.CaptureCOI",
        "EL : PCG Info",
        "Open the PCG Analytics Widget",
        _python_command("open_editor_utility", "/Game/Developers/TA/Script/WB_PCGAnalytics/WB_PCGAnalytics")
    )

    _add_python_entry(
        cubeless_menu,
        "Python.ISMScript",
        "EL : ISM Script",
        "Open the ISM Script Widget",
        _python_command("open_editor_utility", "/Game/Developers/TA/Script/WB_ISM/WB_ISM")
    )

    data_asset_menu = cubeless_menu.add_sub_menu(
        owner=MENU_OWNER,
        section_name=SECTION_NAME,
        name="DataAsset",
        label="EL : Data Asset",
        tool_tip="EL : Data Asset"
    )
    data_asset_menu.add_section(SECTION_NAME, SECTION_NAME)

    _add_python_entry(
        data_asset_menu,
        "Python.DACuttedFoliageList",
        "DA_CuttedFoliageList",
        "Load DA_CuttedFoliageList Data Asset",
        _python_command("open_asset", "/Game/EL/Art/BG/Common/BP/BP_ReactiveFoliage/Resource/DA_CuttedFoliageList")
    )

    _add_python_entry(
        data_asset_menu,
        "Python.CuttedFoliageSmapleMap",
        "SampleMap_CuttedFoliage",
        "Open EL_Foliage_InteractionSampleMap",
        _python_command("open_foliage_sample_map")
    )

    _add_python_entry(
        cubeless_menu,
        "Python.ShowFlagManager",
        "EL : ShowFlag Manager",
        "Open ShowFlag Manager Tool",
        _python_command("open_editor_utility", "/Game/EL/Tools/Script/WB_ShowFlagManager")
    )

    _add_python_entry(
        cubeless_menu,
        "Python.ApplyCubelessEDPCGSelector",
        "Cubeless ED : Apply PCG Selector",
        "Apply selected Cubeless ED PCG selector or production candidate actors, or all selector actors if none are selected.",
        _python_command("apply_cubeless_ed_authoring_selector")
    )

    dungeon_v2_menu = cubeless_menu.add_sub_menu(
        owner=MENU_OWNER,
        section_name=SECTION_NAME,
        name="PCGDungeonV2",
        label="PCG Dungeon V2",
        tool_tip="Cubeless PCG Dungeon V2 authoring commands"
    )
    dungeon_v2_menu.add_section(SECTION_NAME, SECTION_NAME)

    _add_python_entry(
        dungeon_v2_menu,
        "Python.PCGDungeonV2.RegenerateFromBPController",
        "Regenerate From BP Controller",
        "Read MCP_Cubeless_Dungeon_V2_Controller values and refresh the V2 NativeOutput dungeon.",
        _python_command("regenerate_pcg_dungeon_v2_from_bp_controller")
    )

    actor_menu = menus.find_menu("LevelEditor.ActorContextMenu")
    if actor_menu:
        actor_menu.add_section(ROOT_MENU_NAME, ROOT_MENU_NAME)
        _add_python_entry(
            actor_menu,
            "Python.PCGDungeonV2.RegenerateFromBPController.Context",
            "Cubeless : Regenerate Dungeon V2 From BP Controller",
            "Read MCP_Cubeless_Dungeon_V2_Controller values and refresh the V2 NativeOutput dungeon.",
            _python_command("regenerate_pcg_dungeon_v2_from_bp_controller"),
            section_name=ROOT_MENU_NAME
        )

    menus.refresh_all_widgets()


def main():
    try:
        _register_menu()
    except Exception:
        _log_exception("Cubeless: failed to register Python tool menu")


if __name__ == "__main__":
    main()
