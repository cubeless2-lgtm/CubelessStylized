import os
import sys
import unreal

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)
    
from PySide2 import QtWidgets



winName = 'Set Mesh LOD'

class TestWidget(QtWidgets.QWidget):
    def __init__(self):
        super(TestWidget, self).__init__()
        self.setWindowTitle(winName)
        self.setFixedWidth(300)

        # Main Layout
        self.mainBoxLayout_ = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainBoxLayout_)

        # LOD1 Layout
        self.LOD1_layout_ =  QtWidgets.QVBoxLayout()
        # LOD1 in BoxLayout
        self.LOD1_T = QtWidgets.QHBoxLayout()
        self.LOD1_M = QtWidgets.QHBoxLayout()
        self.LOD1_B = QtWidgets.QHBoxLayout()
        self.LOD1_layout_.addStretch()

        # LOD2 Layout
        self.LOD2_layout_ = QtWidgets.QVBoxLayout()
        # LOD2 in BoxLayout
        self.LOD2_T = QtWidgets.QHBoxLayout()
        self.LOD2_M = QtWidgets.QHBoxLayout()
        self.LOD2_B = QtWidgets.QHBoxLayout()
        self.LOD2_layout_.addStretch()

        # Button Layout
        self.Button_layout_ = QtWidgets.QVBoxLayout()
        self.Button_layout_.addStretch()

        # Add Controls
        self.LOD1_lb0 = QtWidgets.QLabel("LOD 1")

        self.LOD1_lb1 = QtWidgets.QLabel("Screen Size : ")
        self.LOD1_spinbox1 = QtWidgets.QDoubleSpinBox()
        self.LOD1_spinbox1.setRange(0.0, 1.0)
        self.LOD1_spinbox1.setValue(0.5)
        self.LOD1_lb2 = QtWidgets.QLabel("Triangles : ")
        self.LOD1_spinbox2 = QtWidgets.QDoubleSpinBox()
        self.LOD1_spinbox2.setRange(0.0, 1.0)
        self.LOD1_spinbox2.setValue(0.5)

        self.LOD2_lb0 = QtWidgets.QLabel("LOD 2")

        self.LOD2_lb1 = QtWidgets.QLabel("Screen Size : ")
        self.LOD2_spinbox1 = QtWidgets.QDoubleSpinBox()
        self.LOD2_spinbox1.setRange(0.0, 1.0)
        self.LOD2_spinbox1.setValue(0.3)
        self.LOD2_lb2 = QtWidgets.QLabel("Triangles : ")
        self.LOD2_spinbox2 = QtWidgets.QDoubleSpinBox()
        self.LOD2_spinbox2.setRange(0.0, 1.0)
        self.LOD2_spinbox2.setValue(0.3)

        self.Set_LOD_Button = QtWidgets.QPushButton("Set LOD")

        # Add Widget
        self.LOD1_T.addWidget(self.LOD1_lb0)
        self.LOD1_M.addWidget(self.LOD1_lb1)
        self.LOD1_M.addWidget(self.LOD1_spinbox1)
        self.LOD1_B.addWidget(self.LOD1_lb2)
        self.LOD1_B.addWidget(self.LOD1_spinbox2)

        self.LOD2_T.addWidget(self.LOD2_lb0)
        self.LOD2_M.addWidget(self.LOD2_lb1)
        self.LOD2_M.addWidget(self.LOD2_spinbox1)
        self.LOD2_B.addWidget(self.LOD2_lb2)
        self.LOD2_B.addWidget(self.LOD2_spinbox2)

        self.Button_layout_.addWidget(self.Set_LOD_Button)

        # Add Layout
        self.mainBoxLayout_.addLayout(self.LOD1_layout_)
        self.mainBoxLayout_.addLayout(self.LOD2_layout_)
        self.mainBoxLayout_.addLayout(self.Button_layout_)

        self.LOD1_layout_.addLayout(self.LOD1_T)
        self.LOD1_layout_.addLayout(self.LOD1_M)
        self.LOD1_layout_.addLayout(self.LOD1_B)

        self.LOD2_layout_.addLayout(self.LOD2_T)
        self.LOD2_layout_.addLayout(self.LOD2_M)
        self.LOD2_layout_.addLayout(self.LOD2_B)

        # Connect Button Command
        self.Set_LOD_Button.clicked.connect(self.Set_LOD_Command)

    def Set_LOD_Command(self):
        Count_LOD = 3
        Minimum_LOD = 0

        self.ScreenSize_LOD1 = self.LOD1_spinbox1.value()
        self.Triangles_LOD1 = self.LOD1_spinbox2.value()

        self.ScreenSize_LOD2 = self.LOD2_spinbox1.value()
        self.Triangles_LOD2 = self.LOD2_spinbox2.value()

        sel_ = unreal.EditorUtilityLibrary.get_selected_assets()

        for i in sel_:
            # Check Mesh Class Type
            if i.get_class().get_name() == "StaticMesh":
                number_of_vertices = unreal.EditorStaticMeshLibrary.get_number_verts(i, 0)

                options = unreal.EditorScriptingMeshReductionOptions()

                options.reduction_settings = [unreal.EditorScriptingMeshReductionSettings(1.0, 1.0),
                                              unreal.EditorScriptingMeshReductionSettings(self.Triangles_LOD1,
                                                                                          self.ScreenSize_LOD1),
                                              unreal.EditorScriptingMeshReductionSettings(self.Triangles_LOD2,
                                                                                          self.ScreenSize_LOD2),

                                              ]

                options.auto_compute_lod_screen_size = False
                # i.set_minimum_lod_for_platform("Mobile", 3) -- unreal5 version

                unreal.EditorStaticMeshLibrary.set_lods(i, options)

                # MinLOD
                PerPlatformInt = unreal.PerPlatformInt()
                PerPlatformInt.set_editor_property("default", 0)
                i.set_editor_property("min_lod", PerPlatformInt)
                PerPlatformInt.set_editor_property("per_platform", {'Mobile': 1})
                i.set_editor_property("min_lod", PerPlatformInt)

                unreal.EditorAssetLibrary.save_loaded_asset(i)

            elif i.get_class().get_name() == "SkeletalMesh":
                util = unreal.EditorUtilityLibrary.get_default_object()
                assetList = util.get_selected_asset_data()

                #
                for asset in assetList:
                    skeletalmesh = asset.get_asset()

                    # Lod
                    lodinfo = []

                    # Base
                    baselodinfo = skeletalmesh.get_editor_property("lod_info")
                    lodinfo.append(baselodinfo[0])

                    # ScreenSize
                    screensizearray = [self.LOD1_spinbox1.value(), self.LOD2_spinbox1.value()]
                    # ScreenSize
                    for screensize in screensizearray:
                        PerPlatformFloat = unreal.PerPlatformFloat()
                        PerPlatformFloat.set_editor_property("default", screensize)
                        Info = unreal.SkeletalMeshLODInfo()
                        Info.set_editor_property("screen_size", PerPlatformFloat)
                        lodinfo.append(Info)

                    # BaseLOD
                    vertparcentagearray = [self.LOD1_spinbox2.value(), self.LOD2_spinbox2.value()]
                    #
                    terminationarray = [1, 1]
                    # BaseLod
                    count = 1
                    for i in range(len(screensizearray)):
                        OptimizationSetting = unreal.SkeletalMeshOptimizationSettings()
                        OptimizationSetting.set_editor_property("num_of_vert_percentage", vertparcentagearray[i])
                        #
                        OptimizationSetting.set_editor_property("termination_criterion",
                                                                unreal.SkeletalMeshTerminationCriterion.cast(
                                                                    terminationarray[i]))
                        lodinfo[count].set_editor_property("reduction_settings", OptimizationSetting)
                        count += 1
                    # LODInfo
                    skeletalmesh.set_editor_property("lod_info", lodinfo)
                    # LOD
                    skeletalmesh.regenerate_lod(len(lodinfo), True)

                    minlod = [0]
                    # MinLOD
                    for SettingVal in minlod:
                        PerPlatformInt = unreal.PerPlatformInt()
                        PerPlatformInt.set_editor_property("default", SettingVal)
                        skeletalmesh.set_editor_property("min_lod", PerPlatformInt)
                        PerPlatformInt.set_editor_property("per_platform", {'Mobile': 1})
                        skeletalmesh.set_editor_property("min_lod", PerPlatformInt)

                    unreal.EditorAssetLibrary.save_asset(asset.get_full_name(), only_if_is_dirty=False)



app = None
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
widget = TestWidget()
widget.show()

unreal.parent_external_window_to_slate(widget.winId())

