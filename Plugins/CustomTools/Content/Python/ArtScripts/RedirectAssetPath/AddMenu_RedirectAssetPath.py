import os
import sys
import unreal
import importlib

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)

def add_asset_editor_menu():
    print("Adding Asset Editor Menu!")
    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.MainMenu")
    
    if not main_menu:
        print("Failed to find the 'Main' menu!")
        return
    
    # Find existing PythonTools menu or create if not exists
    python_tools_menu = menus.find_menu("LevelEditor.MainMenu.PythonTools")
    if not python_tools_menu:
        python_tools_menu = main_menu.add_sub_menu(main_menu.get_name(), "PythonTools", "ToolsA", "EL Tools")
    
    # Create Asset Editor menu entry
    asset_editor_entry = unreal.ToolMenuEntry(
        name="Python.AssetEditor",
        type=unreal.MultiBlockType.MENU_ENTRY,
        insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.FIRST)
    )
    
    asset_editor_entry.set_label("Redirect Asset Path")
    asset_editor_entry.set_tool_tip("Open Asset Editor Tool")
    asset_editor_entry.set_string_command(
        unreal.ToolMenuStringCommandType.PYTHON, 
        '', 
        string='import Run_RedirectAssetPath; import importlib; importlib.reload(Run_RedirectAssetPath);'
    )
    
    # Add the entry to the menu
    python_tools_menu.add_menu_entry("Scripts", asset_editor_entry)
    
    # Refresh UI
    menus.refresh_all_widgets()
add_asset_editor_menu()
# if __name__ == '__main__':
    # add_asset_editor_menu()