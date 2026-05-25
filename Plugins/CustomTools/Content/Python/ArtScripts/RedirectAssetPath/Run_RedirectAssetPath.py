import os
import sys
import unreal

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)
    
from PySide2 import QtWidgets

class AssetSourceFileEditorUI(QtWidgets.QWidget):
    def __init__(self):
        super(AssetSourceFileEditorUI, self).__init__()
        self.setWindowTitle("Source File Path Editor")
        self.setMinimumWidth(400)
        self.folder_path = ""  # Default folder path

        # Layouts
        layout = QtWidgets.QVBoxLayout(self)

        # Folder path selection
        self.path_label = QtWidgets.QLabel("Folder Path: Not Set")
        layout.addWidget(self.path_label)

        self.select_folder_button = QtWidgets.QPushButton("Set Folder Path")
        self.select_folder_button.clicked.connect(self.set_folder_path)
        layout.addWidget(self.select_folder_button)

        # Execute button
        self.execute_button = QtWidgets.QPushButton("Execute")
        self.execute_button.clicked.connect(self.execute_script)
        layout.addWidget(self.execute_button)

    def set_folder_path(self):
        """Open a folder dialog to set the folder path."""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.path_label.setText(f"Folder Path: {self.folder_path}")

    def execute_script(self):
        """Execute the Unreal script to update source file paths."""
        if not self.folder_path:
            unreal.EditorDialog.show_message("Error", "Please set a folder path first.", unreal.AppMsgType.OK)
            return

        # Get selected assets
        now_selects = unreal.EditorUtilityLibrary.get_selected_assets()

        if not now_selects:
            unreal.EditorDialog.show_message("Error", "No assets selected.", unreal.AppMsgType.OK)
            return

        for now_asset in now_selects:
            # Get file name
            asset_name = now_asset.get_name()
            print(f"Asset Name: {asset_name}")

            # Get asset's import data
            import_data = now_asset.get_editor_property("asset_import_data")

            # Get asset's original source file path
            source_files = import_data.extract_filenames()
            print(f"Source Files: {source_files}")

            # Set new source file path
            new_source_file = f"{self.folder_path}/{asset_name}.fbx"
            import_data.scripted_add_filename(new_source_file, 0, "")

        unreal.EditorDialog.show_message("Success", "Source file paths updated successfully.", unreal.AppMsgType.OK)

# Create and show the UI
app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(sys.argv)

window = AssetSourceFileEditorUI()
window.show()

unreal.parent_external_window_to_slate(window.winId())