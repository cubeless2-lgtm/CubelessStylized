import os
import sys
import unreal
from PySide2 import QtWidgets, QtCore

# Path setup
current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)

# Path to the curve name file
curve_names_file_path = os.path.join(current_file_dir, "CustomAnimCurveNames.txt")

# Define functions for adding and removing curves
def AddCustomCurverAnim_Fn(_AnimSequenceArray, curve_name):
    if not _AnimSequenceArray:
        unreal.log_warning("선택한 애셋 중 애니메이션 시퀀스가 없습니다.")
    else:
        for anim_sequence in _AnimSequenceArray:
            # Enable asset modification
            anim_sequence.modify(True)

            # Check if the curve already exists and remove it if present
            existing_curves = unreal.AnimationLibrary.get_animation_curve_names(anim_sequence,
                                                                             unreal.RawCurveTrackTypes.RCT_FLOAT)
            if curve_name in existing_curves:
                # Remove the existing curve before adding the new one
                unreal.AnimationLibrary.remove_curve(anim_sequence, curve_name, False)
                unreal.log(f"기존 커브 '{curve_name}' 삭제됨: {anim_sequence.get_name()}")

            # Add animation curve if not already present
            unreal.AnimationLibrary.add_curve(anim_sequence, curve_name, unreal.RawCurveTrackTypes.RCT_FLOAT)
            unreal.log(f"커브 '{curve_name}' 추가됨: {anim_sequence.get_name()}")

            # Add key at frame 0 with value 1.0
            unreal.AnimationLibrary.add_float_curve_key(anim_sequence, curve_name, 0.0, 1.0)
            unreal.log(f"{anim_sequence.get_name()} - '{curve_name}' 커브 0프레임 값 1.0 설정 완료")

            # Save asset
            unreal.EditorAssetLibrary.save_asset(anim_sequence.get_path_name())

        unreal.log(f"✅ '{curve_name}' 커브 추가 완료!")


def remove_animation_curve(_AnimSequenceArray, curve_name):
    if not _AnimSequenceArray:
        unreal.log_warning("선택한 애셋 중 애니메이션 시퀀스가 없습니다.")
    else:
        for anim_sequence in _AnimSequenceArray:
            # Enable asset modification
            anim_sequence.modify(True)

            # Remove animation curve if present
            existing_curves = unreal.AnimationLibrary.get_animation_curve_names(anim_sequence,
                                                                             unreal.RawCurveTrackTypes.RCT_FLOAT)
            if curve_name in existing_curves:
                unreal.AnimationLibrary.remove_curve(anim_sequence, curve_name, False)
                unreal.log(f"커브 '{curve_name}' 삭제됨: {anim_sequence.get_name()}")
            else:
                unreal.log_warning(f"{anim_sequence.get_name()} - '{curve_name}' 커브가 존재하지 않습니다.")

            # Save asset
            unreal.EditorAssetLibrary.save_asset(anim_sequence.get_path_name())

        unreal.log(f"✅ '{curve_name}' 커브 삭제 완료!")


# Define the UI for asset source file editor
class CustumCurveAnim_Class(QtWidgets.QWidget):
    def __init__(self):
        super(CustumCurveAnim_Class, self).__init__()
        self.setWindowTitle("AnimSequence:Add Custom Curve Anim ")
        self.setMinimumWidth(400)

        # Layouts
        layout = QtWidgets.QVBoxLayout(self)

        # Create a listbox layout for selecting curves
        self.curve_listbox = QtWidgets.QListWidget(self)
        self.load_curve_names_from_file()

        # Allow multiple selection
        self.curve_listbox.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        # Group the listbox at the top
        layout.addWidget(self.curve_listbox)

        # Button group for adding/removing selected curves based on listbox selection
        self.add_curve_button = QtWidgets.QPushButton("Add Selected Curves")
        self.add_curve_button.clicked.connect(self.add_selected_curves)
        layout.addWidget(self.add_curve_button)

        self.remove_curve_button = QtWidgets.QPushButton("Remove Selected Curves")
        self.remove_curve_button.clicked.connect(self.remove_selected_curves)
        layout.addWidget(self.remove_curve_button)

        # Add spacing before custom input area for clarity
        layout.addSpacing(20)

        # Input area for custom curve names, horizontally aligned
        self.custom_curve_layout = QtWidgets.QHBoxLayout()
        self.custom_curve_label = QtWidgets.QLabel("Custom Curve Name:")
        self.custom_curve_input = QtWidgets.QLineEdit()

        self.custom_curve_layout.addWidget(self.custom_curve_label)
        self.custom_curve_layout.addWidget(self.custom_curve_input)

        layout.addLayout(self.custom_curve_layout)

        # Button group for adding/removing custom curves based on input line
        self.add_custom_curve_button = QtWidgets.QPushButton("Add Custom Curve")
        self.add_custom_curve_button.clicked.connect(self.add_custom_curve)
        layout.addWidget(self.add_custom_curve_button)

        self.remove_custom_curve_button = QtWidgets.QPushButton("Remove Custom Curve")
        self.remove_custom_curve_button.clicked.connect(self.remove_custom_curve)
        layout.addWidget(self.remove_custom_curve_button)

    def load_curve_names_from_file(self):
        """Load curve names from the CustomAnimCurveNames.txt file."""
        if os.path.exists(curve_names_file_path):
            with open(curve_names_file_path, "r") as file:
                curve_names = file.readlines()
                for name in curve_names:
                    name = name.strip()  # Remove leading/trailing whitespaces
                    if name:  # Avoid adding empty lines
                        self.curve_listbox.addItem(name)
        else:
            unreal.log_warning(f"{curve_names_file_path} 파일이 존재하지 않습니다.")

    def add_selected_curves(self):
        """Add selected curves based on the listbox selections."""
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        anim_sequences = [asset for asset in selected_assets if isinstance(asset, unreal.AnimSequence)]

        selected_items = self.curve_listbox.selectedItems()
        for item in selected_items:
            curve_name = item.text()
            AddCustomCurverAnim_Fn(anim_sequences, curve_name)

    def remove_selected_curves(self):
        """Remove selected curves based on the listbox selections."""
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        anim_sequences = [asset for asset in selected_assets if isinstance(asset, unreal.AnimSequence)]

        selected_items = self.curve_listbox.selectedItems()
        for item in selected_items:
            curve_name = item.text()
            remove_animation_curve(anim_sequences, curve_name)

    def add_custom_curve(self):
        """Add custom curve based on input."""
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        anim_sequences = [asset for asset in selected_assets if isinstance(asset, unreal.AnimSequence)]

        custom_curve = self.custom_curve_input.text().strip()
        if custom_curve:
            AddCustomCurverAnim_Fn(anim_sequences, custom_curve)

    def remove_custom_curve(self):
        """Remove custom curve based on input."""
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        anim_sequences = [asset for asset in selected_assets if isinstance(asset, unreal.AnimSequence)]

        custom_curve = self.custom_curve_input.text().strip()
        if custom_curve:
            remove_animation_curve(anim_sequences, custom_curve)

# Create and show the UI
app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(sys.argv)

window = CustumCurveAnim_Class()
window.show()

unreal.parent_external_window_to_slate(window.winId())
