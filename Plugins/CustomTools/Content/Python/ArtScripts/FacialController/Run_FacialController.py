import sys
import unreal
import os

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)
    
from PySide2 import QtCore, QtGui, QtWidgets
# ============================================
# Control Rig 이름 매핑 설정
# ============================================
# ============================================
# Control Rig 이름 매핑 설정
# ============================================
# ============================================
# Control Rig 이름 매핑 설정 (업데이트됨)
# ============================================
CONTROL_RIG_MAPPING = {
    # 눈썹 컨트롤
    "browraiseOutR_PN_CTR": "CTRL_R_brow_raiseOut",
    "browraiseOutL_PN_CTR": "CTRL_L_brow_raiseOut", 
    "browraiseIn_PN_CTR": "CTRL_R_brow_raiseIn",  # 또는 CTRL_R_brow_raiseIn - 중앙이므로 선택 필요
    "browdownL_PN_CTR": "CTRL_L_brow_down",
    "browdownR_PN_CTR": "CTRL_R_brow_down",
    "browlateralR_PN_CTR": "CTRL_R_brow_lateral",
    "browlateralL_PN_CTR": "CTRL_L_brow_lateral",
    
    # 눈 컨트롤
    "eyefaceScrunchL_PN_CTR": "CTRL_L_eye_faceScrunch",
    "eyefaceScrunchR_PN_CTR": "CTRL_R_eye_faceScrunch",
    "Eye_L_PN_CTR": "CTRL_L_eye",
    "Eye_R_PN_CTR": "CTRL_R_eye",
    "Eye_Center_PN_CTR": "CTRL_C_eye",  # 중앙 눈 컨트롤러
    "EyeBlink_L_PN_CTR": "CTRL_L_eye_blink",
    "EyeBlink_R_PN_CTR": "CTRL_R_eye_blink",
    "EyeSqWi_L_PN_CTR": "CTRL_L_eye_squintInner",  # 또는 적절한 squint 컨트롤
    "EyeSqWi_R_PN_CTR": "CTRL_R_eye_squintInner",
    "EyeSquint_L_PN_CTR": "CTRL_L_eye_cheekRaise",
    "EyeSquint_R_PN_CTR": "CTRL_R_eye_cheekRaise",
    
    # 코 컨트롤
    "NoseSneer_L_PN_CTR": "CTRL_L_nose",
    "NoseSneer_R_PN_CTR": "CTRL_R_nose",
    
    # 입 컨트롤 - 중앙
    "Mouth_PN_CTR": "CTRL_C_mouth", 
    "mouthPucker_CTR": "CTRL_C_mouth_purseU",  # 또는 purseD
    "MouthClose_PN_CTR": "CTRL_C_mouth_lipsTogetherU",  # 또는 lipsTogetherD
    "MouthFunnel_PN_CTR": "CTRL_C_mouth_funnelU",  # 또는 funnelD
    "mouthLipTowards_PN_CTR": "CTRL_C_mouth_towardsU",  # 또는 towardsD
    "MouthRoll_PN_CTR": "CTRL_C_mouth_lipsRollU",  # 또는 lipsRollD
    "MouthPress_PN_CTR": "CTRL_C_mouth_pressU",  # 또는 pressD
    "MouthLipsThighten_PN_CTR": "CTRL_C_mouth_tightenU",  # 또는 tightenD
    
    # 입 컨트롤 - 좌우
    "upperLipRaise_R_PN_CTR": "CTRL_R_mouth_upperLipRaise",
    "upperLipRaise_L_PN_CTR": "CTRL_L_mouth_upperLipRaise",
    "lowerLipDepresse_R_PN_CTR": "CTRL_R_mouth_lowerLipDepress",
    "lowerLipDepresse_L_PN_CTR": "CTRL_L_mouth_lowerLipDepress",
    "nasolabialDeepenR_PN_CTR": "CTRL_R_nose_nasolabialDeepen",
    "nasolabialDeepenL_PN_CTR": "CTRL_L_nose_nasolabialDeepen",
    "mouthLipsBlowR_PN_CTR": "CTRL_R_mouth_lipsBlow",
    "mouthLipsBlowL_PN_CTR": "CTRL_L_mouth_lipsBlow",
    "mouthDimple_R_PN_CTR": "CTRL_R_mouth_sharpCornerPull",
    "mouthDimple_L_PN_CTR": "CTRL_L_mouth_sharpCornerPull",
    "mouthSmile_R_PN_CTR": "CTRL_R_mouth_cornerPull",  # 스마일은 보통 corner pull
    "mouthSmile_L_PN_CTR": "CTRL_L_mouth_cornerPull",
    "mouthFrown_R_PN_CTR": "CTRL_R_mouth_cornerDepress",
    "mouthFrown_L_PN_CTR": "CTRL_L_mouth_cornerDepress",
    "mouthStretch_R_PN_CTR": "CTRL_R_mouth_stretch",
    "mouthStretch_L_PN_CTR": "CTRL_L_mouth_stretch",
    "mouthCorner_R_PN_CTR": "CTRL_R_mouth_corner",
    "mouthCorner_L_PN_CTR": "CTRL_L_mouth_corner",
    "mouthCornerRS_R_PN_CTR": "CTRL_R_mouth_cornerSharpnessU",  # 또는 sharpCornerPull
    "mouthCornerRS_L_PN_CTR": "CTRL_L_mouth_cornerSharpnessU",
    
    # 턱 컨트롤
    "jaw_ChinRais_CTR": "CTRL_C_jaw_ChinRaiseU",  # 또는 ChinRaiseD
    "Jaw_PN_CTR": "CTRL_C_jaw",
    "jawForward_PN_CTR": "CTRL_C_jaw_fwdBack",
    "JawClenchR_PN_CTR": "CTRL_R_jaw_clench",
    "JawClenchL_PN_CTR": "CTRL_L_jaw_clench",
    "CheekPuff_PN_CTR": "CTRL_R_mouth_suckBlow",  # 또는 R_ - 양쪽 중 선택 필요
    
    # 혀 컨트롤
    "tongue_inOut_PN_CTR": "CTRL_C_tongue_inOut",
    "tongue_press_PN_CTR": "CTRL_C_tongue_press",
    "tongue_PN_CTR": "CTRL_C_tongue",
    "tongue_roll_PN_CTR": "CTRL_C_tongue_roll",
    "tongue_tip_PN_CTR": "CTRL_C_tongue_tip",
    
    # 목 컨트롤
    "neckThroat_PN_CTR": "CTRL_neck_digastricUpDown",  # 또는 throatUpDown
    
    # 추가 가능한 매핑들 (현재 UI에는 없지만 향후 사용 가능)
    # 눈 관련
    "eyeLidPressL_PN_CTR": "CTRL_L_eye_lidPress",
    "eyeLidPressR_PN_CTR": "CTRL_R_eye_lidPress",
    "eyePupilL_PN_CTR": "CTRL_L_eye_pupil",
    "eyePupilR_PN_CTR": "CTRL_R_eye_pupil",
    "eyelidUpL_PN_CTR": "CTRL_L_eye_eyelidU",
    "eyelidUpR_PN_CTR": "CTRL_R_eye_eyelidU",
    "eyelidDownL_PN_CTR": "CTRL_L_eye_eyelidD",
    "eyelidDownR_PN_CTR": "CTRL_R_eye_eyelidD",
    
    # 속눈썹
    "eyelashTweakerInL_PN_CTR": "CTRL_L_eyelash_tweakerIn",
    "eyelashTweakerInR_PN_CTR": "CTRL_R_eyelash_tweakerIn",
    "eyelashTweakerOutL_PN_CTR": "CTRL_L_eyelash_tweakerOut",
    "eyelashTweakerOutR_PN_CTR": "CTRL_R_eyelash_tweakerOut",
    
    # 귀
    "earUpL_PN_CTR": "CTRL_L_ear_up",
    "earUpR_PN_CTR": "CTRL_R_ear_up",
    
    # 치아
    "teethUpL_PN_CTR": "CTRL_C_teethU",
    "teethDownL_PN_CTR": "CTRL_C_teethD",
    "teethFwdBackUpL_PN_CTR": "CTRL_C_teeth_fwdBackU",
    "teethFwdBackDownL_PN_CTR": "CTRL_C_teeth_fwdBackD",
    
    # 목 상세 컨트롤
    "neckMastoidL_PN_CTR": "CTRL_L_neck_mastoidContract",
    "neckMastoidR_PN_CTR": "CTRL_R_neck_mastoidContract",
    "neckStretchL_PN_CTR": "CTRL_L_neck_stretch",
    "neckStretchR_PN_CTR": "CTRL_R_neck_stretch",
    "neckDigastric_PN_CTR": "CTRL_neck_digastricUpDown",
    "neckThroatExhale_PN_CTR": "CTRL_neck_throatExhaleInhale",
    
    # 시스템 컨트롤
    "lookAtSwitch_PN_CTR": "CTRL_lookAtSwitch",
    "rigLogicSwitch_PN_CTR": "CTRL_rigLogicSwitch",
    "eyeParallelLook_PN_CTR": "CTRL_C_eye_parallelLook",
    
    # 혀 추가 컨트롤
    "tongueNarrowWide_PN_CTR": "CTRL_C_tongue_narrowWide",
    
    # 입술 상세 컨트롤
    "lipShiftUpL_PN_CTR": "CTRL_C_mouth_lipShiftU",
    "lipShiftDownL_PN_CTR": "CTRL_C_mouth_lipShiftD",
    "lipStickyUpL_PN_CTR": "CTRL_C_mouth_stickyU",
    "lipStickyDownL_PN_CTR": "CTRL_C_mouth_stickyD",
}

# 시퀀서 경로 설정
SEQUENCE_PATH = "/Game/NewLevelSequence"
SKELETON_BINDING_NAME = "SkeletalMesh"  # 또는 "SK Mannequin"

class BaseControl:
    def __init__(self, node_name, movement_area, boundary_color=QtGui.QColor(0, 255, 0), invert_x=False, invert_y=False):
        self.node_name = node_name
        self.control_rig_name = CONTROL_RIG_MAPPING.get(node_name, node_name)  # Control Rig 매핑 이름
        self.node = None
        self.movement_area = movement_area
        self.rect_size = 20
        self.half_size = self.rect_size / 2
        self.invert_x = invert_x  # X축 반전 여부
        self.invert_y = invert_y  # Y축 반전 여부
        
        # ✅ 정확한 중심점 계산
        center_x = movement_area.x() + movement_area.width() / 2.0
        center_y = movement_area.y() + movement_area.height() / 2.0
        self.pos = QtCore.QPoint(int(center_x), int(center_y))
        self.boundary_color = boundary_color
        self.update_rect_size()

    def update_rect_size(self):
        self.rect_size = min(self.movement_area.width(), self.movement_area.height()) * 0.2
        self.half_size = self.rect_size / 2

    def reset_position(self):
        # ✅ 정확한 중심점으로 리셋
        center_x = self.movement_area.x() + self.movement_area.width() / 2.0
        center_y = self.movement_area.y() + self.movement_area.height() / 2.0
        self.pos = QtCore.QPoint(int(center_x), int(center_y))

    def draw_movement_area(self, painter):
        pass

class SingleAxisNegativeRestrictedControl(BaseControl):
    def __init__(self, node_name, movement_area, axis='x', boundary_color=QtGui.QColor(0, 255, 255), invert_x=False, invert_y=False):
        super().__init__(node_name, movement_area, boundary_color, invert_x, invert_y)
        self.axis = axis

    def update_position(self, new_pos):
        center_pos = self.movement_area.center()
        
        if self.axis == 'x':
            # X축: 중심점에서 왼쪽으로만 이동 가능
            min_x = self.movement_area.left() + self.half_size
            max_x = center_pos.x()
            new_x = max(min_x, min(max_x, new_pos.x()))
            # ✅ Y축은 현재 위치 유지 (중심에 강제로 고정하지 않음)
            self.pos = QtCore.QPoint(int(new_x), self.pos.y())
        else:
            # Y축: 중심점에서 위쪽으로만 이동 가능
            min_y = self.movement_area.top() + self.half_size
            max_y = center_pos.y()
            new_y = max(min_y, min(max_y, new_pos.y()))
            # ✅ X축은 현재 위치 유지 (중심에 강제로 고정하지 않음)
            self.pos = QtCore.QPoint(self.pos.x(), int(new_y))

    def draw_movement_area(self, painter):
        pen = QtGui.QPen(self.boundary_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(200, 200, 200, 50))

        if self.axis == 'x':
            painter.drawLine(self.movement_area.left(), self.movement_area.center().y(),
                           self.movement_area.center().x(), self.movement_area.center().y())
            # 중심점 표시
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 4))
            painter.drawPoint(self.movement_area.center().x(), self.movement_area.center().y())
        else:
            painter.drawLine(self.movement_area.center().x(), self.movement_area.top(),
                           self.movement_area.center().x(), self.movement_area.center().y())
            # 중심점 표시
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 4))
            painter.drawPoint(self.movement_area.center().x(), self.movement_area.center().y())


class SingleAxisPositiveRestrictedControl(BaseControl):
    def __init__(self, node_name, movement_area, axis='x', boundary_color=QtGui.QColor(255, 100, 0), invert_x=False, invert_y=False):
        super().__init__(node_name, movement_area, boundary_color, invert_x, invert_y)
        self.axis = axis

    def update_position(self, new_pos):
        center_pos = self.movement_area.center()
        
        if self.axis == 'x':
            # X축: 중심점에서 오른쪽으로만 이동 가능
            min_x = center_pos.x()
            max_x = self.movement_area.right() - self.half_size
            new_x = max(min_x, min(max_x, new_pos.x()))
            # ✅ Y축은 현재 위치 유지 (중심에 강제로 고정하지 않음)
            self.pos = QtCore.QPoint(int(new_x), self.pos.y())
        else:
            # Y축: 중심점에서 아래쪽으로만 이동 가능
            min_y = center_pos.y()
            max_y = self.movement_area.bottom() - self.half_size
            new_y = max(min_y, min(max_y, new_pos.y()))
            # ✅ X축은 현재 위치 유지 (중심에 강제로 고정하지 않음)
            self.pos = QtCore.QPoint(self.pos.x(), int(new_y))

    def draw_movement_area(self, painter):
        pen = QtGui.QPen(self.boundary_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(200, 200, 200, 50))

        if self.axis == 'x':
            painter.drawLine(self.movement_area.center().x(), self.movement_area.center().y(),
                           self.movement_area.right(), self.movement_area.center().y())
            # 중심점 표시
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 4))
            painter.drawPoint(self.movement_area.center().x(), self.movement_area.center().y())
        else:
            painter.drawLine(self.movement_area.center().x(), self.movement_area.center().y(),
                           self.movement_area.center().x(), self.movement_area.bottom())
            # 중심점 표시
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 4))
            painter.drawPoint(self.movement_area.center().x(), self.movement_area.center().y())


class SingleAxisControl(BaseControl):
    def __init__(self, node_name, movement_area, axis='x', boundary_color=QtGui.QColor(255, 165, 0), invert_x=False, invert_y=False):
        super().__init__(node_name, movement_area, boundary_color, invert_x, invert_y)
        self.axis = axis

    def update_position(self, new_pos):
        if self.axis == 'x':
            min_x = self.movement_area.left() + self.half_size
            max_x = self.movement_area.right() - self.half_size
            new_x = max(min_x, min(max_x, new_pos.x()))
            self.pos = QtCore.QPoint(int(new_x), self.pos.y())
        else:  # y축
            min_y = self.movement_area.top() + self.half_size
            max_y = self.movement_area.bottom() - self.half_size
            new_y = max(min_y, min(max_y, new_pos.y()))
            self.pos = QtCore.QPoint(self.pos.x(), int(new_y))

    def draw_movement_area(self, painter):
        pen = QtGui.QPen(self.boundary_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(200, 200, 200, 50))
        
        if self.axis == 'x':
            y_center = self.movement_area.center().y()
            painter.drawLine(self.movement_area.left(), y_center,
                           self.movement_area.right(), y_center)
            # 중심점 표시
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 3))
            painter.drawPoint(self.movement_area.center().x(), y_center)
        else:
            x_center = self.movement_area.center().x()
            painter.drawLine(x_center, self.movement_area.top(),
                           x_center, self.movement_area.bottom())
            # 중심점 표시
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 3))
            painter.drawPoint(x_center, self.movement_area.center().y())


class DualAxisControl(BaseControl):
    def __init__(self, node_name, movement_area, boundary_color=QtGui.QColor(0, 255, 0), invert_x=False, invert_y=False):
        super().__init__(node_name, movement_area, boundary_color, invert_x, invert_y)

    def update_position(self, new_pos):
        min_x = self.movement_area.left() + self.half_size
        max_x = self.movement_area.right() - self.half_size
        min_y = self.movement_area.top() + self.half_size
        max_y = self.movement_area.bottom() - self.half_size

        new_x = max(min_x, min(max_x, new_pos.x()))
        new_y = max(min_y, min(max_y, new_pos.y()))

        self.pos = QtCore.QPoint(int(new_x), int(new_y))

    def draw_movement_area(self, painter):
        pen = QtGui.QPen(self.boundary_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(200, 200, 200, 50))
        painter.drawRect(self.movement_area)

class RestrictedDualAxisControl(BaseControl):
    def __init__(self, node_name, movement_area, y_bottom_limit=0.5, boundary_color=QtGui.QColor(255, 0, 255), invert_x=False, invert_y=False):
        super().__init__(node_name, movement_area, boundary_color, invert_x, invert_y)
        self.y_bottom_limit = y_bottom_limit

    def update_position(self, new_pos):
        min_x = self.movement_area.left() + self.half_size
        max_x = self.movement_area.right() - self.half_size
        min_y = self.movement_area.top() + self.half_size
        
        allowed_height = self.movement_area.height() * (1 - self.y_bottom_limit)
        max_y = self.movement_area.top() + allowed_height - self.half_size

        new_x = max(min_x, min(max_x, new_pos.x()))
        new_y = max(min_y, min(max_y, new_pos.y()))
        
        self.pos = QtCore.QPoint(new_x, new_y)

    def draw_movement_area(self, painter):
        pen = QtGui.QPen(self.boundary_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(200, 200, 200, 50))
        
        allowed_height = self.movement_area.height() * (1 - self.y_bottom_limit)
        movement_rect = QtCore.QRect(
            self.movement_area.left(),
            self.movement_area.top(),
            self.movement_area.width(),
            allowed_height
        )
        painter.drawRect(movement_rect)

class RestrictedDualAxisControlTopLimit(BaseControl):
    def __init__(self, node_name, movement_area, y_top_limit=0.5, boundary_color=QtGui.QColor(255, 0, 255), invert_x=False, invert_y=False):
        super().__init__(node_name, movement_area, boundary_color, invert_x, invert_y)
        self.y_top_limit = y_top_limit

    def update_position(self, new_pos):
        min_x = self.movement_area.left() + self.half_size
        max_x = self.movement_area.right() - self.half_size
        max_y = self.movement_area.bottom() - self.half_size
        
        allowed_height = self.movement_area.height() * (1 - self.y_top_limit)
        min_y = self.movement_area.bottom() - allowed_height + self.half_size
        
        new_x = max(min_x, min(max_x, new_pos.x()))
        new_y = max(min_y, min(max_y, new_pos.y()))
        
        self.pos = QtCore.QPoint(new_x, new_y)

    def draw_movement_area(self, painter):
        pen = QtGui.QPen(self.boundary_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(200, 200, 200, 50))
        
        allowed_height = self.movement_area.height() * (1 - self.y_top_limit)
        movement_rect = QtCore.QRect(
            self.movement_area.left(),
            self.movement_area.bottom() - allowed_height,
            self.movement_area.width(),
            allowed_height
        )
        painter.drawRect(movement_rect)

class FacialControlPanel(QtWidgets.QMainWindow):
    def __init__(self):
        super(FacialControlPanel, self).__init__()
        
        self.setWindowTitle("Facial Control Panel")
        self.setFixedSize(500, 700)  # 높이 증가

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # 리셋 버튼
        self.reset_button = QtWidgets.QPushButton("Reset All Controls", self)
        self.reset_button.setGeometry(150, 630, 200, 40)
        self.reset_button.clicked.connect(self.reset_all_controls)

        # ✅ 스켈레톤 선택 UI를 리셋 버튼 위에 배치
        self.skeleton_label = QtWidgets.QLabel("Select Skeleton:", self)
        self.skeleton_label.setGeometry(20, 590, 100, 20)
        
        self.skeleton_dropdown = QtWidgets.QComboBox(self)
        self.skeleton_dropdown.setGeometry(130, 590, 250, 25)
        self.skeleton_dropdown.currentTextChanged.connect(self.on_skeleton_changed)
        
        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.refresh_button.setGeometry(390, 590, 80, 25)
        self.refresh_button.clicked.connect(self.refresh_skeletons)

        # ✅ 바인딩 관련 변수들 한 번만 초기화
        self.current_skeleton_binding = None
        self.selected_skeleton_name = ""
        self.binding_map = {}

        # 컨트롤 초기화 (Y 오프셋 추가)
        self.controls = []
        self.init_controls()
        
        self.current_control = None
        self.drag_start_pos = QtCore.QPoint()
        
        # 초기 스켈레톤 목록 로드
        self.refresh_skeletons()
        
    def refresh_skeletons(self):
        """현재 열린 레벨시퀀스에서 스켈레톤 바인딩 목록을 새로고침"""
        self.skeleton_dropdown.clear()
        
        try:
            # ✅ 하드코딩된 경로 대신 현재 열린 시퀀스 사용
            current_sequence = unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
            
            if not current_sequence:
                unreal.log_error("현재 열린 레벨 시퀀스가 없습니다.")
                self.skeleton_dropdown.addItem("No open sequence")
                return

            sequence = unreal.LevelSequence.cast(current_sequence)
            if not sequence:
                unreal.log_error("레벨 시퀀스 캐스팅에 실패했습니다.")
                self.skeleton_dropdown.addItem("Invalid sequence")
                return

            unreal.log(f"현재 열린 시퀀스: {sequence.get_name()}")

            bindings = sequence.get_bindings()
            skeleton_bindings = []
            
            def explore_bindings(binding_list, parent_name=""):
                for binding in binding_list:
                    binding_name = binding.get_name()
                    binding_id = str(binding.get_id())
                    
                    # 현재 바인딩에 Control Rig가 있는지 확인
                    has_control_rig = False
                    for track in binding.get_tracks():
                        if track.get_class().get_name() == "MovieSceneControlRigParameterTrack":
                            has_control_rig = True
                            break
                    
                    # ✅ Control Rig가 있고 부모가 있는 경우만 추가
                    if has_control_rig and parent_name:
                        display_name = f"{parent_name} > {binding_name}"
                        skeleton_bindings.append((display_name, binding, binding_id))
                        unreal.log(f"Found Control Rig binding with parent: {display_name} (ID: {binding_id})")
                    elif has_control_rig and not parent_name:
                        # ✅ 부모가 없는 경우는 로그만 출력하고 추가하지 않음
                        unreal.log(f"Skipped Control Rig binding without parent: {binding_name} (ID: {binding_id})")
                    
                    # 자식 바인딩들도 재귀적으로 탐색
                    child_bindings = binding.get_child_possessables()
                    if child_bindings:
                        if has_control_rig:
                            # 현재 바인딩에 Control Rig가 있으면 부모 이름으로 사용하지 않음
                            next_parent = parent_name if parent_name else binding_name
                        else:
                            # 현재 바인딩에 Control Rig가 없으면 부모 이름으로 사용
                            if parent_name:
                                next_parent = f"{parent_name} > {binding_name}"
                            else:
                                next_parent = binding_name
                        
                        explore_bindings(child_bindings, next_parent)
            
            # 최상위 바인딩부터 탐색 시작
            explore_bindings(bindings)
                    
            if skeleton_bindings:
                # 바인딩 정보를 저장 (display_name -> (binding, binding_id) 매핑)
                self.binding_map = {}
                
                for display_name, binding, binding_id in skeleton_bindings:
                    self.skeleton_dropdown.addItem(display_name)
                    self.binding_map[display_name] = (binding, binding_id)
                    
                # 첫 번째 항목 선택
                if len(skeleton_bindings) > 0:
                    first_display_name = skeleton_bindings[0][0]
                    self.current_skeleton_binding = skeleton_bindings[0][1]
                    self.selected_skeleton_name = first_display_name
                    
                unreal.log(f"Found {len(skeleton_bindings)} binding(s) with Control Rig and parent")
            else:
                self.skeleton_dropdown.addItem("No bindings with Control Rig and parent found")
                unreal.log_warning("No bindings with Control Rig and parent found")
                
        except Exception as e:
            unreal.log_error(f"Failed to refresh skeletons: {e}")
            import traceback
            unreal.log_error(traceback.format_exc())
            self.skeleton_dropdown.addItem("Error loading skeletons")
        
    def on_skeleton_changed(self, skeleton_display_name):
        """스켈레톤 선택이 변경되었을 때 호출"""
        if not skeleton_display_name or skeleton_display_name in ["No sequence found", "Invalid sequence", "No bindings with Control Rig found", "Error loading skeletons"]:
            self.current_skeleton_binding = None
            self.selected_skeleton_name = ""
            return
            
        try:
            # ✅ 바인딩 맵에서 직접 가져오기
            if hasattr(self, 'binding_map') and skeleton_display_name in self.binding_map:
                binding, binding_id = self.binding_map[skeleton_display_name]
                self.current_skeleton_binding = binding
                self.selected_skeleton_name = skeleton_display_name
                unreal.log(f"Selected skeleton: {skeleton_display_name} (ID: {binding_id})")
            else:
                unreal.log_warning(f"Could not find binding for: {skeleton_display_name}")
                self.current_skeleton_binding = None
                self.selected_skeleton_name = ""
                        
        except Exception as e:
            unreal.log_error(f"Failed to change skeleton: {e}")
            
    def init_controls(self):
        """모든 컨트롤을 초기화"""
        self.controls = []
        
        # === 색상 정의 ===
        red = QtGui.QColor(255, 0, 0)
        pink = QtGui.QColor(235, 182, 182)
        orange = QtGui.QColor(255, 100, 0)
        blue = QtGui.QColor(50, 50, 255)
        light_blue = QtGui.QColor(183, 186, 255)
        green = QtGui.QColor(0, 186, 0)
        yellow = QtGui.QColor(183, 186, 0)
        purple = QtGui.QColor(200, 150, 200)
        
        # === 눈썹 컨트롤러 ===
        self.controls.extend([
            SingleAxisNegativeRestrictedControl("browraiseOutR_PN_CTR", QtCore.QRect(130, 10, 100, 100), 'y', red, invert_y=True),
            SingleAxisNegativeRestrictedControl("browraiseIn_PN_CTR", QtCore.QRect(180, 10, 100, 100), 'y', red, invert_y=True),
            SingleAxisNegativeRestrictedControl("browraiseOutL_PN_CTR", QtCore.QRect(230, 10, 100, 100), 'y', red, invert_y=True),
            SingleAxisPositiveRestrictedControl("browdownR_PN_CTR", QtCore.QRect(150, 43, 100, 100), 'y', red),
            SingleAxisPositiveRestrictedControl("browdownL_PN_CTR", QtCore.QRect(210, 43, 100, 100), 'y', red),
            SingleAxisPositiveRestrictedControl("browlateralR_PN_CTR", QtCore.QRect(120, 43, 100, 100), 'y', red),
            SingleAxisPositiveRestrictedControl("browlateralL_PN_CTR", QtCore.QRect(240, 43, 100, 100), 'y', red),
            SingleAxisPositiveRestrictedControl("eyefaceScrunchR_PN_CTR", QtCore.QRect(90, 23, 100, 100), 'y', pink),
            SingleAxisPositiveRestrictedControl("eyefaceScrunchL_PN_CTR", QtCore.QRect(270, 23, 100, 100), 'y', pink)
        ])
        
        # === 눈 컨트롤러 ===
        self.controls.extend([
            DualAxisControl("Eye_R_PN_CTR", QtCore.QRect(120, 163, 70, 70), pink, invert_y=True),
            DualAxisControl("Eye_Center_PN_CTR", QtCore.QRect(195, 163, 70, 70), purple, invert_y=True),
            DualAxisControl("Eye_L_PN_CTR", QtCore.QRect(270, 163, 70, 70), pink, invert_y=True),
            SingleAxisControl("EyeBlink_R_PN_CTR", QtCore.QRect(50, 133, 100, 100), 'y', pink),
            SingleAxisControl("EyeBlink_L_PN_CTR", QtCore.QRect(310, 133, 100, 100), 'y', pink),
            SingleAxisNegativeRestrictedControl("EyeSqWi_R_PN_CTR", QtCore.QRect(45, 143, 50, 50), 'y', pink,invert_y=True),
            SingleAxisNegativeRestrictedControl("EyeSqWi_L_PN_CTR", QtCore.QRect(365, 143, 50, 50), 'y', pink,invert_y=True),
            SingleAxisNegativeRestrictedControl("EyeSquint_R_PN_CTR", QtCore.QRect(30, 213, 100, 100), 'y', pink,invert_y=True),
            SingleAxisNegativeRestrictedControl("EyeSquint_L_PN_CTR", QtCore.QRect(330, 213, 100, 100), 'y', pink,invert_y=True)
        ])
        
        # === 코 컨트롤러 ===
        self.controls.extend([
            SingleAxisNegativeRestrictedControl("NoseSneer_R_PN_CTR", QtCore.QRect(160, 263, 100, 100), 'y', orange, invert_y=True),
            SingleAxisNegativeRestrictedControl("NoseSneer_L_PN_CTR", QtCore.QRect(200, 263, 100, 100), 'y', orange, invert_y=True)
        ])
        
        # === 입 관련 컨트롤러 ===
        self.controls.extend([
            DualAxisControl("Mouth_PN_CTR", QtCore.QRect(190, 353, 80, 80), light_blue, invert_y=True),
            SingleAxisNegativeRestrictedControl("upperLipRaise_R_PN_CTR", QtCore.QRect(120, 313, 100, 100), 'y', light_blue, invert_y=True),
            SingleAxisNegativeRestrictedControl("upperLipRaise_L_PN_CTR", QtCore.QRect(240, 313, 100, 100), 'y', light_blue, invert_y=True),
            SingleAxisPositiveRestrictedControl("lowerLipDepresse_R_PN_CTR", QtCore.QRect(120, 353, 100, 100), 'y', light_blue),
            SingleAxisPositiveRestrictedControl("lowerLipDepresse_L_PN_CTR", QtCore.QRect(240, 353, 100, 100), 'y', light_blue),
            SingleAxisNegativeRestrictedControl("mouthPucker_CTR", QtCore.QRect(215, 310, 60, 60), 'x', light_blue),
            SingleAxisNegativeRestrictedControl("mouthDimple_R_PN_CTR", QtCore.QRect(120, 323, 60, 60), 'x', yellow, invert_x=True),
            SingleAxisPositiveRestrictedControl("mouthDimple_L_PN_CTR", QtCore.QRect(280, 323, 60, 60), 'x', yellow),
            SingleAxisNegativeRestrictedControl("mouthSmile_R_PN_CTR", QtCore.QRect(95, 323, 100, 100), 'x', blue, invert_x=True),
            SingleAxisPositiveRestrictedControl("mouthSmile_L_PN_CTR", QtCore.QRect(265, 323, 100, 100), 'x', blue),
            SingleAxisNegativeRestrictedControl("mouthFrown_R_PN_CTR", QtCore.QRect(95, 353, 100, 100), 'x', blue, invert_x=True),
            SingleAxisPositiveRestrictedControl("mouthFrown_L_PN_CTR", QtCore.QRect(265, 353, 100, 100), 'x', blue),
            SingleAxisNegativeRestrictedControl("mouthStretch_R_PN_CTR", QtCore.QRect(120, 393, 60, 60), 'x', yellow, invert_x=True),
            SingleAxisPositiveRestrictedControl("mouthStretch_L_PN_CTR", QtCore.QRect(280, 393, 60, 60), 'x', yellow),
            DualAxisControl("mouthCorner_R_PN_CTR", QtCore.QRect(30, 353, 60, 60), light_blue, invert_y=True, invert_x=False),
            DualAxisControl("mouthCorner_L_PN_CTR", QtCore.QRect(370, 353, 60, 60), light_blue, invert_y=True, invert_x=True),
            SingleAxisControl("mouthCornerRS_R_PN_CTR", QtCore.QRect(-5, 353, 50, 50), 'y', light_blue),
            SingleAxisControl("mouthCornerRS_L_PN_CTR", QtCore.QRect(415, 353, 50, 50), 'y', light_blue),
            SingleAxisNegativeRestrictedControl("nasolabialDeepenR_PN_CTR", QtCore.QRect(125, 283, 50, 50), 'y', yellow, invert_y=True),
            SingleAxisNegativeRestrictedControl("nasolabialDeepenL_PN_CTR", QtCore.QRect(285, 283, 50, 50), 'y', yellow, invert_y=True),
            SingleAxisNegativeRestrictedControl("mouthLipsBlowR_PN_CTR", QtCore.QRect(85, 303, 50, 50), 'y', yellow, invert_y=True),
            SingleAxisNegativeRestrictedControl("mouthLipsBlowL_PN_CTR", QtCore.QRect(325, 303, 50, 50), 'y', yellow, invert_y=True)
        ])
        
        # === 턱 관련 컨트롤러 ===
        self.controls.extend([
            RestrictedDualAxisControl("jaw_ChinRais_CTR", QtCore.QRect(200, 443, 60, 60), 0.4, light_blue),
            SingleAxisNegativeRestrictedControl("MouthClose_PN_CTR", QtCore.QRect(215, 468, 60, 60), 'x', blue),
            RestrictedDualAxisControlTopLimit("Jaw_PN_CTR", QtCore.QRect(180, 473, 100, 100), 0.4, blue, invert_x=True),
            SingleAxisNegativeRestrictedControl("JawClenchR_PN_CTR", QtCore.QRect(80, 438, 50, 50), 'y', light_blue, invert_y=True),
            SingleAxisNegativeRestrictedControl("JawClenchL_PN_CTR", QtCore.QRect(330, 438, 50, 50), 'y', light_blue, invert_y=True),
            SingleAxisControl("jawForward_PN_CTR", QtCore.QRect(270, 513, 50, 50), 'y', light_blue, invert_y=True)
        ])
        
        # === 혀 컨트롤러 ===
        self.controls.extend([
            SingleAxisControl("tongue_inOut_PN_CTR", QtCore.QRect(-10, 513, 50, 50), 'y', light_blue,invert_y=True),
            SingleAxisNegativeRestrictedControl("tongue_press_PN_CTR", QtCore.QRect(5, 513, 50, 50), 'y', light_blue, invert_y=True),
            DualAxisControl("tongue_PN_CTR", QtCore.QRect(45, 523, 40, 40), light_blue,invert_y=True),
            DualAxisControl("tongue_roll_PN_CTR", QtCore.QRect(90, 523, 40, 40), light_blue,invert_y=True),
            DualAxisControl("tongue_tip_PN_CTR", QtCore.QRect(135, 523, 40, 40), light_blue,invert_y=True)
        ])
        
        # === 기타 컨트롤러 ===
        self.controls.extend([
            SingleAxisControl("CheekPuff_PN_CTR", QtCore.QRect(30, 240, 100, 100), 'x', green, invert_x=True),
            SingleAxisControl("neckThroat_PN_CTR", QtCore.QRect(320, 493, 80, 80), 'y', green , invert_y=True),
            SingleAxisNegativeRestrictedControl("MouthFunnel_PN_CTR", QtCore.QRect(380, 155, 100, 100), 'y', orange),
            SingleAxisNegativeRestrictedControl("mouthLipTowards_PN_CTR", QtCore.QRect(410, 155, 100, 100), 'y', orange),
            RestrictedDualAxisControl("MouthRoll_PN_CTR", QtCore.QRect(415, 220, 60, 60), 0.4, green),
            RestrictedDualAxisControl("MouthPress_PN_CTR", QtCore.QRect(415, 260, 60, 60), 0.4, green),
            RestrictedDualAxisControl("MouthLipsThighten_PN_CTR", QtCore.QRect(415, 300, 60, 60), 0.4, green)
        ])

    def reset_all_controls(self):
        """모든 컨트롤을 초기 위치로 리셋"""
        for control in self.controls:
            control.reset_position()
            self.update()
            self.update_node_position(control)
        unreal.log("All controls reset complete")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        
        for control in self.controls:
            control.draw_movement_area(painter)
            
        for control in self.controls:
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
            painter.setBrush(QtGui.QColor(100, 100, 100))
            painter.drawRect(
                control.pos.x() - control.half_size,
                control.pos.y() - control.half_size,
                control.rect_size,
                control.rect_size
            )
            
            # 컨트롤 이름 표시 (옵션)
            painter.setPen(QtGui.QPen(QtCore.Qt.white))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(
                control.pos.x() - 30,
                control.pos.y() + control.half_size + 15,
                control.node_name.split('_')[0][:6]  # 짧게 표시
            )

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            for control in self.controls:
                rect = QtCore.QRect(
                    control.pos.x() - control.half_size,
                    control.pos.y() - control.half_size,
                    control.rect_size,
                    control.rect_size
                )
                if rect.contains(event.pos()):
                    self.current_control = control
                    # ✅ 수정: 컨트롤 중심에서의 오프셋이 아닌 클릭 위치 저장
                    self.drag_start_pos = event.pos()
                    self.control_start_pos = control.pos
                    break
        elif event.button() == QtCore.Qt.RightButton:
            for control in self.controls:
                rect = QtCore.QRect(
                    control.pos.x() - control.half_size,
                    control.pos.y() - control.half_size,
                    control.rect_size,
                    control.rect_size
                )
                if rect.contains(event.pos()):
                    control.reset_position()
                    self.update()
                    self.update_node_position(control)
                    break

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self.current_control:
            # ✅ 수정: 드래그 거리만큼 이동
            delta = event.pos() - self.drag_start_pos
            new_pos = self.control_start_pos + delta
            self.current_control.update_position(new_pos)
            self.update()
            self.update_node_position(self.current_control)

    def mouseReleaseEvent(self, event):
        self.current_control = None

    def update_node_position(self, control):
        """Control Rig의 위치를 업데이트 - 여러 Control Rig 환경에서 정확한 선택"""
        try:
            # 선택된 스켈레톤 바인딩이 없으면 종료
            if not self.current_skeleton_binding:
                unreal.log_warning("선택된 스켈레톤이 없습니다.")
                return

            # 현재 열려있는 Level Sequence 가져오기
            level_sequence = unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
            
            if not level_sequence:
                unreal.log_error("현재 열려있는 레벨 시퀀서가 없습니다.")
                return

            # 선택된 바인딩에서 Control Rig 트랙 찾기
            control_rig_track = None
            control_rig_section = None
            
            for track in self.current_skeleton_binding.get_tracks():
                if isinstance(track, unreal.MovieSceneControlRigParameterTrack):
                    control_rig_track = track
                    # 해당 트랙의 섹션도 가져오기
                    sections = track.get_sections()
                    if sections:
                        control_rig_section = sections[0]  # 첫 번째 섹션 사용
                    break
            
            if not control_rig_track or not control_rig_section:
                unreal.log_error(f"선택된 스켈레톤 '{self.selected_skeleton_name}'에서 Control Rig 트랙 또는 섹션을 찾을 수 없습니다.")
                return

            # ✅ 핵심: 선택된 바인딩의 Control Rig 섹션에서 직접 Control Rig 가져오기
            target_control_rig = None
            
            try:
                # 방법 1: 섹션에서 직접 Control Rig 가져오기
                if hasattr(control_rig_section, 'get_control_rig'):
                    target_control_rig = control_rig_section.get_control_rig()
                    if target_control_rig:
                        unreal.log(f"✅ 섹션에서 Control Rig 직접 획득: {target_control_rig.get_name()}")
                elif hasattr(control_rig_section, 'control_rig'):
                    target_control_rig = control_rig_section.control_rig
                    if target_control_rig:
                        unreal.log(f"✅ 섹션 속성에서 Control Rig 획득: {target_control_rig.get_name()}")
            except Exception as e:
                unreal.log_warning(f"섹션에서 Control Rig 가져오기 실패: {e}")

            # 방법 2: Control Rig 목록에서 매칭하기 (백업)
            if not target_control_rig:
                unreal.log("백업 방법 사용: Control Rig 목록에서 매칭")
                
                rig_proxies = unreal.ControlRigSequencerLibrary.get_control_rigs(level_sequence)
                
                # 선택된 바인딩과 연결된 Control Rig 찾기
                for rig_proxy in rig_proxies:
                    try:
                        rig = rig_proxy.control_rig
                        rig_track = rig_proxy.track
                        
                        # 현재 선택된 바인딩의 트랙과 일치하는지 확인
                        if rig_track == control_rig_track:
                            target_control_rig = rig
                            unreal.log(f"✅ 트랙 매칭으로 Control Rig 발견: {rig.get_name()}")
                            break
                            
                    except Exception as e:
                        unreal.log_warning(f"Control Rig 프록시 확인 중 오류: {e}")
                        continue
            
            # 방법 3: 첫 번째 Control Rig 사용 (최후의 수단)
            if not target_control_rig:
                rig_proxies = unreal.ControlRigSequencerLibrary.get_control_rigs(level_sequence)
                if rig_proxies:
                    target_control_rig = rig_proxies[0].control_rig
                    unreal.log_warning(f"⚠️ 최후의 수단: 첫 번째 Control Rig 사용: {target_control_rig.get_name()}")

            if not target_control_rig:
                unreal.log_error("Control Rig을 찾을 수 없습니다.")
                return

            # 컨트롤 이름 확인
            target_control_name = control.control_rig_name
            
            try:
                hierarchy = target_control_rig.get_hierarchy()
                all_controls = hierarchy.get_all_keys()
                control_names = [str(ctrl.name) for ctrl in all_controls if ctrl.type == unreal.RigElementType.CONTROL]
                
                if target_control_name not in control_names:
                    unreal.log_error(f"❌ 컨트롤 '{target_control_name}'이 Control Rig '{target_control_rig.get_name()}'에 존재하지 않습니다.")
                    unreal.log_error(f"❌ 사용 가능한 컨트롤 목록: {control_names[:10]}...")  # 처음 10개만 로그에 출력
                    return
                else:
                    unreal.log(f"✅ 컨트롤 '{target_control_name}' 확인됨")
                    
            except Exception as e:
                unreal.log_warning(f"컨트롤 존재 확인 실패: {e}")

            # 위치 값 계산
            center_x = control.movement_area.x() + control.movement_area.width() / 2.0
            center_y = control.movement_area.y() + control.movement_area.height() / 2.0
            
            x_offset = control.pos.x() - center_x
            y_offset = control.pos.y() - center_y
            
            max_x_range = control.movement_area.width() / 2.0
            max_y_range = control.movement_area.height() / 2.0
            
            x_value = 0.0
            y_value = 0.0
            
            # 값 계산 로직
            if isinstance(control, SingleAxisNegativeRestrictedControl):
                if control.axis == 'x':
                    if max_x_range > 0:
                        normalized_distance = abs(x_offset) / max_x_range
                        if control.invert_x:
                            x_value = max(0.0, min(1.0, normalized_distance * 1.0))
                        else:
                            x_value = max(-1.0, min(0.0, -normalized_distance * 1.0))
                else:  # y축
                    if max_y_range > 0:
                        normalized_distance = abs(y_offset) / max_y_range
                        if control.invert_y:
                            y_value = max(0.0, min(1.0, normalized_distance * 1.0))
                        else:
                            y_value = max(-1.0, min(0.0, -normalized_distance * 1.0))
                            
            elif isinstance(control, SingleAxisPositiveRestrictedControl):
                if control.axis == 'x':
                    if max_x_range > 0:
                        normalized_distance = x_offset / max_x_range
                        if control.invert_x:
                            x_value = max(-1.0, min(0.0, -normalized_distance * 1.0))
                        else:
                            x_value = max(0.0, min(1.0, normalized_distance * 1.0))
                else:  # y축
                    if max_y_range > 0:
                        normalized_distance = y_offset / max_y_range
                        if control.invert_y:
                            y_value = max(-1.0, min(0.0, -normalized_distance * 1.0))
                        else:
                            y_value = max(0.0, min(1.0, normalized_distance * 1.0))
                            
            elif isinstance(control, SingleAxisControl):
                if control.axis == 'x':
                    if max_x_range > 0:
                        x_multiplier = -1.0 if control.invert_x else 1.0
                        x_value = max(-1.0, min(1.0, (x_offset / max_x_range) * x_multiplier * 1.0))
                else:  # y축
                    if max_y_range > 0:
                        y_multiplier = -1.0 if control.invert_y else 1.0
                        y_value = max(-1.0, min(1.0, (y_offset / max_y_range) * y_multiplier * 1.0))
                        
            else:
                # 다중 축 컨트롤러들
                if max_x_range > 0:
                    x_multiplier = -1.0 if control.invert_x else 1.0
                    x_value = max(-1.0, min(1.0, (x_offset / max_x_range) * x_multiplier * 1.0))
                    
                if max_y_range > 0:
                    y_multiplier = -1.0 if control.invert_y else 1.0
                    y_value = max(-1.0, min(1.0, (y_offset / max_y_range) * y_multiplier * 1.0))

            # 경계 보정
            boundary_threshold = 0.0001
            left_boundary = control.movement_area.left() + control.half_size
            right_boundary = control.movement_area.right() - control.half_size
            top_boundary = control.movement_area.top() + control.half_size
            bottom_boundary = control.movement_area.bottom() - control.half_size
            
            if control.pos.x() <= left_boundary + boundary_threshold:
                if isinstance(control, SingleAxisNegativeRestrictedControl) and control.axis == 'x':
                    x_value = 1.0 if control.invert_x else -1.0
                elif not isinstance(control, SingleAxisPositiveRestrictedControl):
                    x_value = 1.0 if control.invert_x else -1.0
                    
            if control.pos.x() >= right_boundary - boundary_threshold:
                if isinstance(control, SingleAxisPositiveRestrictedControl) and control.axis == 'x':
                    x_value = -1.0 if control.invert_x else 1.0
                elif not isinstance(control, SingleAxisNegativeRestrictedControl):
                    x_value = -1.0 if control.invert_x else 1.0
            
            if control.pos.y() <= top_boundary + boundary_threshold:
                if isinstance(control, SingleAxisNegativeRestrictedControl) and control.axis == 'y':
                    y_value = 1.0 if control.invert_y else -1.0
                elif not isinstance(control, SingleAxisPositiveRestrictedControl):
                    y_value = 1.0 if control.invert_y else -1.0
                    
            if control.pos.y() >= bottom_boundary - boundary_threshold:
                if isinstance(control, SingleAxisPositiveRestrictedControl) and control.axis == 'y':
                    y_value = -1.0 if control.invert_y else 1.0
                elif not isinstance(control, SingleAxisNegativeRestrictedControl):
                    y_value = -1.0 if control.invert_y else 1.0

            # 0 근처 자동 스냅
            center_threshold = 3.0
            if abs(control.pos.x() - center_x) <= center_threshold:
                x_value = 0.0
            if abs(control.pos.y() - center_y) <= center_threshold:
                y_value = 0.0

            # 소수점 3자리로 반올림
            x_value = round(x_value, 3)
            y_value = round(y_value, 3)

            # ✅ 정확한 컨트롤 매칭을 위한 함수
            def is_exact_control_match(channel_name_str, target_control_name):
                """정확한 컨트롤 매칭을 위한 함수"""
                # 1. 완전히 동일한 경우
                if channel_name_str == target_control_name:
                    return True
                
                # 2. 컨트롤 이름 뒤에 바로 점(.)이 오는 경우만 허용
                if channel_name_str.startswith(target_control_name + "."):
                    return True
                
                return False

            # ✅ 키프레임 설정과 컨트롤 선택을 동일한 Control Rig에서 수행
            channels_updated = 0
            
            # 키프레임 설정
            current_time = unreal.LevelSequenceEditorBlueprintLibrary.get_current_time()
            frame_time = unreal.FrameNumber(int(current_time))
            
            all_channels = control_rig_section.get_all_channels()
            is_single_axis = isinstance(control, (SingleAxisControl, SingleAxisNegativeRestrictedControl, SingleAxisPositiveRestrictedControl))
            
            if is_single_axis:
                target_value = x_value if control.axis == 'x' else y_value
                
                for channel in all_channels:
                    try:
                        channel_name = getattr(channel, 'channel_name', '')
                        channel_name_str = str(channel_name) if hasattr(channel_name, '__str__') else repr(channel_name)
                        
                        # ✅ 정확한 매칭만 허용
                        if is_exact_control_match(channel_name_str, target_control_name):
                            try:
                                if hasattr(channel, 'add_key'):
                                    channel.add_key(frame_time, target_value)
                                    unreal.log(f"✅ 단일축 채널 키 추가: {channel_name_str} = {target_value}")
                                    channels_updated += 1
                                elif hasattr(channel, 'set_default'):
                                    channel.set_default(target_value)
                                    unreal.log(f"✅ 단일축 채널 기본값 설정: {channel_name_str} = {target_value}")
                                    channels_updated += 1
                            except Exception as e:
                                unreal.log_error(f"❌ 단일축 채널 설정 오류: {str(e)}")
                                
                    except Exception as e:
                        unreal.log_error(f"❌ 단일축 채널 처리 중 오류: {str(e)}")
            
            else:
                # 다중 축 컨트롤 - 정확한 X, Y 채널 매칭
                x_channel_patterns = [".Location.X", ".Transform.Translation.X", ".Translation.X", ".X"]
                y_channel_patterns = [".Location.Y", ".Transform.Translation.Y", ".Translation.Y", ".Y"]
                
                for channel in all_channels:
                    try:
                        channel_name = getattr(channel, 'channel_name', '')
                        channel_name_str = str(channel_name) if hasattr(channel_name, '__str__') else repr(channel_name)
                        
                        # X축 채널 정확한 매칭
                        for pattern in x_channel_patterns:
                            if channel_name_str == target_control_name + pattern:
                                try:
                                    if hasattr(channel, 'add_key'):
                                        channel.add_key(frame_time, x_value)
                                        unreal.log(f"✅ X 채널 키 추가: {channel_name_str} = {x_value}")
                                        channels_updated += 1
                                    elif hasattr(channel, 'set_default'):
                                        channel.set_default(x_value)
                                        unreal.log(f"✅ X 채널 기본값 설정: {channel_name_str} = {x_value}")
                                        channels_updated += 1
                                    break
                                except Exception as e:
                                    unreal.log_error(f"❌ X 채널 설정 오류: {str(e)}")
                        
                        # Y축 채널 정확한 매칭
                        for pattern in y_channel_patterns:
                            if channel_name_str == target_control_name + pattern:
                                try:
                                    if hasattr(channel, 'add_key'):
                                        channel.add_key(frame_time, y_value)
                                        unreal.log(f"✅ Y 채널 키 추가: {channel_name_str} = {y_value}")
                                        channels_updated += 1
                                    elif hasattr(channel, 'set_default'):
                                        channel.set_default(y_value)
                                        unreal.log(f"✅ Y 채널 기본값 설정: {channel_name_str} = {y_value}")
                                        channels_updated += 1
                                    break
                                except Exception as e:
                                    unreal.log_error(f"❌ Y 채널 설정 오류: {str(e)}")
                                    
                    except Exception as e:
                        unreal.log_error(f"❌ 다중축 채널 처리 중 오류: {str(e)}")

            # ✅ 키프레임 설정 후 동일한 Control Rig에서 컨트롤 선택 (선택 해제 → 선택)
            try:
                # 1단계: 모든 Control Rig의 선택 해제
                rig_proxies = unreal.ControlRigSequencerLibrary.get_control_rigs(level_sequence)
                for rig_proxy in rig_proxies:
                    try:
                        rig = rig_proxy.control_rig
                        if rig:
                            rig.clear_control_selection()
                            unreal.log(f"🔄 Control Rig '{rig.get_name()}' 선택 해제")
                    except Exception as e:
                        unreal.log_warning(f"선택 해제 중 오류: {e}")
                
                # 2단계: 대상 Control Rig에서 컨트롤 선택
                selection_result = target_control_rig.select_control(target_control_name)
                
                if selection_result:
                    unreal.log(f"🎯 컨트롤 '{target_control_name}' 선택 성공 (Control Rig: {target_control_rig.get_name()})")
                else:
                    unreal.log_warning(f"⚠️ 컨트롤 '{target_control_name}' 선택 실패 (Control Rig: {target_control_rig.get_name()})")
                    
            except Exception as e:
                unreal.log_warning(f"❌ 컨트롤 선택 중 오류: {e}")

            unreal.log(f"📊 [{self.selected_skeleton_name}] 총 {channels_updated}개 채널에 키프레임 설정 완료")

        except Exception as e:
            unreal.log_error(f"❌ 노드 위치 업데이트 실패: {e}")
            import traceback
            unreal.log_error(traceback.format_exc())

def launch_facial_control_panel():
    """Facial Control Panel 실행"""
    app = None
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    widget = FacialControlPanel()
    widget.show()
    unreal.parent_external_window_to_slate(widget.winId())
    return widget

# Unreal에서 실행
facial_panel = launch_facial_control_panel()