import os
import sys
import unreal
import importlib

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)

def open_foliage_sample_map():
    import unreal
    map_path = "/Game/EL/Maps/SampleMap/EL_Foliage_InteractionSampleMap/EL_Foliage_InteractionSampleMap"
    
    # 레벨 에셋 존재 여부 확인
    if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        unreal.EditorDialog.show_message("Error", f"Level not found:\n{map_path}", unreal.AppMsgType.OK)
        return

    # 다이얼로그 메시지 표시
    result = unreal.EditorDialog.show_message("레벨 열기", "EL_Foliage_InteractionSampleMap 레벨을 여시겠습니까?", unreal.AppMsgType.YES_NO)
    
    # Yes 선택 시 레벨 열기
    if result == unreal.AppReturnType.YES:
        unreal.EditorLevelLibrary.load_level(map_path)

def main():
    print("Creating Menus!")
    menus = unreal.ToolMenus.get()

    main_menu = menus.find_menu("LevelEditor.MainMenu")
    if not main_menu:
        print("Failed to find the 'Main' menu. Something is wrong in the force!")
    else:
        # Cubeless 메인 메뉴
        el_env_menu = main_menu.add_sub_menu(main_menu.get_name(), "Cubeless", "Cubeless", "Cubeless")

        # Cubeless 메뉴에 항목 추가
        coi_capture_entry = unreal.ToolMenuEntry(
            name="Python.CaptureCOI",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        coi_capture_entry.set_label("EL : PCG Info")
        coi_capture_entry.set_tool_tip("Open the PCG Analytics Widget")
        coi_capture_entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', 'import unreal; bp = unreal.EditorAssetLibrary.load_asset("/Game/Developers/TA/Script/WB_PCGAnalytics/WB_PCGAnalytics"); unreal.EditorUtilitySubsystem().spawn_and_register_tab(bp)')
        el_env_menu.add_menu_entry("Scripts", coi_capture_entry)

        # EL : ISM Script 메뉴에 항목 추가
        ism_script_entry = unreal.ToolMenuEntry(
            name="Python.ISMScript",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        ism_script_entry.set_label("EL : ISM Script")
        ism_script_entry.set_tool_tip("Open the ISM Script Widget")
        ism_script_entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', 'import unreal; bp = unreal.EditorAssetLibrary.load_asset("/Game/Developers/TA/Script/WB_ISM/WB_ISM"); unreal.EditorUtilitySubsystem().spawn_and_register_tab(bp)')
        el_env_menu.add_menu_entry("Scripts", ism_script_entry)

        # Cubeless 메뉴에 "EL : Data Asset" 서브메뉴 추가
        data_asset_menu = el_env_menu.add_sub_menu(el_env_menu.get_name(), "DataAsset", "EL : Data Asset", "EL : Data Asset")

        # DA_CuttedFoliageList 버튼 추가
        da_cutted_foliage_list_entry = unreal.ToolMenuEntry(
            name="Python.DACuttedFoliageList",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        da_cutted_foliage_list_entry.set_label("DA_CuttedFoliageList")
        da_cutted_foliage_list_entry.set_tool_tip("Load DA_CuttedFoliageList Data Asset")
        da_cutted_foliage_list_entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', 'asset=unreal.EditorAssetLibrary.load_asset("/Game/EL/Art/BG/Common/BP/BP_ReactiveFoliage/Resource/DA_CuttedFoliageList");unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([asset])')
        data_asset_menu.add_menu_entry("Scripts", da_cutted_foliage_list_entry)

        # CuttedFoliageSmapleMap 버튼 추가
        cutted_foliage_smaple_map_entry = unreal.ToolMenuEntry(
            name="Python.CuttedFoliageSmapleMap",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        cutted_foliage_smaple_map_entry.set_label("SampleMap_CuttedFoliage")
        cutted_foliage_smaple_map_entry.set_tool_tip("Open EL_Foliage_InteractionSampleMap")
        command_string = 'import RegisterMenu; import importlib; importlib.reload(RegisterMenu); RegisterMenu.open_foliage_sample_map()'
        cutted_foliage_smaple_map_entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', command_string)
        data_asset_menu.add_menu_entry("Scripts", cutted_foliage_smaple_map_entry)

        # EL : ShowFlag Manager
        showflag_manager_entry = unreal.ToolMenuEntry(
            name="Python.ShowFlagManager",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        showflag_manager_entry.set_label("EL : ShowFlag Manager")
        showflag_manager_entry.set_tool_tip("Open ShowFlag Manager Tool")
        showflag_manager_entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', 'import unreal; bp = unreal.EditorAssetLibrary.load_asset("/Game/EL/Tools/Script/WB_ShowFlagManager"); unreal.EditorUtilitySubsystem().spawn_and_register_tab(bp)')
        el_env_menu.add_menu_entry("Scripts", showflag_manager_entry)

        # Refresh UI
        menus.refresh_all_widgets()

if __name__ == '__main__':
    main()
