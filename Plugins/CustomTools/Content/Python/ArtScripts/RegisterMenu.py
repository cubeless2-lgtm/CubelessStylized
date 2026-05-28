import os
import sys
import traceback

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


def _add_python_entry(menu, name, label, tooltip, command):
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
    menu.add_menu_entry(SECTION_NAME, entry)


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

    menus.refresh_all_widgets()


def main():
    try:
        _register_menu()
    except Exception:
        _log_exception("Cubeless: failed to register Python tool menu")


if __name__ == "__main__":
    main()
