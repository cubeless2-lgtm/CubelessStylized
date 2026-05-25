import os
import sys
import unreal
from PySide2 import QtWidgets, QtCore

# Path setup
current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)

from PIL import Image
import numpy as np
from scipy.ndimage import distance_transform_edt

import EL_Level_Editor as ELLevelEditor

winName = 'SDF Generator'

class SDFGen_Class(QtWidgets.QWidget):
    def __init__(self):
        super(SDFGen_Class, self).__init__()
        self.setWindowTitle(winName)
        self.setFixedWidth(500)

        # Layouts
        layout = QtWidgets.QVBoxLayout(self)

        # 이미지 불러오는 경로를 설정할 수 있는 버튼
        self.SDF_lb1 = QtWidgets.QLabel("Input Image : ")
        self.SDF_lineEdit1 = QtWidgets.QLineEdit()
        self.SDF_lineEdit1.setDisabled(True)  # 비활성화
        self.SDF_lineEdit1.setPlaceholderText("Select an image file")
        self.SDF_lineEdit1.setText("input.png")
        self.SDF_btn1 = QtWidgets.QPushButton("...")
        self.SDF_btn1.setFixedWidth(40)
        self.SDF_btn1.clicked.connect(self.browse_input)
        layout.addWidget(self.SDF_lb1)
        input_tex_layout = QtWidgets.QHBoxLayout()
        input_tex_layout.addWidget(self.SDF_lineEdit1)
        input_tex_layout.addWidget(self.SDF_btn1)
        layout.addLayout(input_tex_layout)

        # 변환된 이미지를 저장하는는 경로를 설정할 수 있는 버튼
        self.SDF_lb2 = QtWidgets.QLabel("Output Image : ")
        self.SDF_lineEdit2 = QtWidgets.QLineEdit()
        self.SDF_lineEdit2.setDisabled(True)  # 비활성화
        self.SDF_lineEdit2.setPlaceholderText("Select an output file")
        self.SDF_lineEdit2.setText("output.png")
        self.SDF_btn2 = QtWidgets.QPushButton("...")
        self.SDF_btn2.setFixedWidth(40)
        self.SDF_btn2.clicked.connect(self.browse_output)
        layout.addWidget(self.SDF_lb2)
        output_tex_layout = QtWidgets.QHBoxLayout()
        output_tex_layout.addWidget(self.SDF_lineEdit2)
        output_tex_layout.addWidget(self.SDF_btn2)
        layout.addLayout(output_tex_layout)

        # 변환 옵션 설정정
        self.SDF_lb3 = QtWidgets.QLabel("Invert : ")
        self.SDF_cb1 = QtWidgets.QCheckBox()
        self.SDF_lb5 = QtWidgets.QLabel("SDF : ")
        self.SDF_cb2 = QtWidgets.QCheckBox()
        self.SDF_cb2.setChecked(True)
        self.SDF_lb4 = QtWidgets.QLabel("Max Distance: ")
        self.SDF_spinbox1 = QtWidgets.QDoubleSpinBox()
        self.SDF_spinbox1.setRange(0.0, 256.0)
        self.SDF_spinbox1.setValue(50.0)
        self.SDF_spinbox1.setSingleStep(1.0)
        # 라벨과 체크박스를 같은 행에 배치하기 위해 QHBoxLayout 사용
        option_layout1 = QtWidgets.QHBoxLayout()
        option_layout1.addWidget(self.SDF_lb3)
        option_layout1.addWidget(self.SDF_cb1)
        option_layout1.addWidget(self.SDF_lb5)
        option_layout1.addWidget(self.SDF_cb2)
        option_layout1.addWidget(self.SDF_lb4)
        option_layout1.addWidget(self.SDF_spinbox1)
        layout.addLayout(option_layout1)

        # 텍스처 크기 저장 변수
        self.output_texture_size = 64  # 기본값

        # 텍스처 크기 설정 버튼 추가
        self.SDF_lb6 = QtWidgets.QLabel("Output Texture Size: ")
        self.SDF_lb7 = QtWidgets.QLabel(f"{self.output_texture_size}")
        size_label_layout = QtWidgets.QHBoxLayout()
        size_label_layout.addWidget(self.SDF_lb6)
        size_label_layout.addWidget(self.SDF_lb7)
        layout.addLayout(size_label_layout)

        # 텍스처 크기 버튼 추가
        # 버튼 레이아웃 설정
        size_button_layout = QtWidgets.QHBoxLayout()
        # size_button_layout.setAlignment(QtCore.Qt.AlignRight)
        # size_button_layout.setSpacing(10)

        # 1024 버튼
        button_1024 = QtWidgets.QPushButton("1024")
        button_1024.setFixedWidth(60)
        button_1024.clicked.connect(self.set_texture_size_1024)
        size_button_layout.addWidget(button_1024)

        # 512 버튼
        button_512 = QtWidgets.QPushButton("512")
        button_512.setFixedWidth(60)
        button_512.clicked.connect(self.set_texture_size_512)
        size_button_layout.addWidget(button_512)

        # 256 버튼
        button_256 = QtWidgets.QPushButton("256")
        button_256.setFixedWidth(60)
        button_256.clicked.connect(self.set_texture_size_256)
        size_button_layout.addWidget(button_256)

        # 128 버튼
        button_128 = QtWidgets.QPushButton("128")
        button_128.setFixedWidth(60)
        button_128.clicked.connect(self.set_texture_size_128)
        size_button_layout.addWidget(button_128)

        # 64 버튼
        button_64 = QtWidgets.QPushButton("64")
        button_64.setFixedWidth(60)
        button_64.clicked.connect(self.set_texture_size_64)
        size_button_layout.addWidget(button_64)

        layout.addLayout(size_button_layout)

        # Add spacing before custom input area for clarity
        layout.addSpacing(20)

        # 변환 버튼튼
        self.sdf_gen_button = QtWidgets.QPushButton("SDF Texture Gen")
        self.sdf_gen_button.clicked.connect(self.generate_sdf)
        layout.addWidget(self.sdf_gen_button)

        # Add spacing before custom input area for clarity
        layout.addSpacing(20)

        # 변환 버튼튼
        self.ta_test_button = QtWidgets.QPushButton("TA Test!!!")
        self.ta_test_button.clicked.connect(self.ta_test)
        layout.addWidget(self.ta_test_button)

    def set_texture_size(self, size):
        self.output_texture_size = size
        self.SDF_lb7.setText(f"{size}")
        print(f"Output texture size set to: {size}")

    def set_texture_size_1024(self):
        self.set_texture_size(1024)

    def set_texture_size_512(self):
        self.set_texture_size(512)

    def set_texture_size_256(self):
        self.set_texture_size(256)

    def set_texture_size_128(self):
        self.set_texture_size(128)

    def set_texture_size_64(self):
        self.set_texture_size(64)

    def browse_input(self):
        input_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Input Image", "", "Image Files (*.png *.jpg *.bmp)")
        self.SDF_lineEdit1.setText(input_path)

    def browse_output(self):
        output_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Output Image", "", "Image Files (*.png)")
        self.SDF_lineEdit2.setText(output_path)

    def ta_test(self):
        print("Nothing happens.")
        # input_r16_path = "D:\EL_Art_Resource\BG\Gaea\EL_Proto_04\Render\HeightMap.r16"
        # output_png16_path = "D:\EL_Art_Resource\BG\Gaea\EL_Proto_04\Render\HeightMap.png"
        # self.convert_r16_to_png16(input_r16_path, output_png16_path)

        # input_png16_path = "D:\EL_Art_Resource\BG\Gaea\EL_Proto_04\Render\HeightMap_4033.png"
        # output_png16_path = "D:\EL_Art_Resource\BG\Gaea\EL_Proto_04\Render\HeightMap_8129.png"
        # self.upscale_png16_to_8129(input_png16_path, output_png16_path)

        # ELLevelEditor.duplicate_level_to_new_folder(
        #     original_level_path="/Game/EL/Maps/EL_Proto_04/EL_Proto_04",
        #     destination_folder="/Game/EL/Maps/EL_World_01",
        #     new_level_name="EL_World_01"
        # )

    def generate_sdf(self):
        input_path = self.SDF_lineEdit1.text()
        output_path = self.SDF_lineEdit2.text()
        invert = self.SDF_cb1.isChecked()
        is_sdf = self.SDF_cb2.isChecked()
        max_distance = self.SDF_spinbox1.value() * 8
        
        # # 1) 이미지 불러오기 (Pillow)
        # img = Image.open(input_path).convert("L")  # Grayscale로 변환

        # 1) 이미지 불러오기 (Pillow)
        img = Image.open(input_path).convert("RGBA")  # RGBA 모드로 열기
        r, g, b, a = img.split()  # RGBA 채널 분리

        # 1-1) 투명 부분을 검정색으로 처리
        #img = Image.composite(img.convert("RGB"), Image.new("RGB", img.size, (0, 0, 0)), a)
        img = Image.composite(Image.new("RGB", img.size, (255, 255, 255)), Image.new("RGB", img.size, (0, 0, 0)), a)

        # 1-2) Grayscale로 변환
        img = img.convert("L")

        # 1-1) 텍스처 해상도를 4K로 강제 조정
        img = img.resize((4096, 4096), Image.LANCZOS)

        img_data = np.array(img, dtype=np.float32)


        # 2) 배경/도형 구분을 위해 threshold
        #    → 0(배경)과 1(도형)로 구분
        #    → invert=True면 밝은 부분이 '도형'이 되도록反전
        if invert:
            # 밝을수록 도형이므로 반전
            mask = (img_data > 128).astype(np.float32)
        else:
            # 어두울수록 도형
            mask = (img_data < 128).astype(np.float32)
            
        # 3) distance transform (scipy)
        #    mask=1 인 영역은 "도형"으로 봄 → 거리=0
        #    배경(0) 픽셀에 대해서 "가장 가까운 도형까지의 거리"를 계산
        dist_outside = distance_transform_edt(1 - mask)  # 도형 외부로부터의 거리

        if (is_sdf):
            # 도형 내부 픽셀(=1)에도 거리 변환을 적용해, 도형 내부에 대해서는 도형 경계까지 거리를 음수로 볼 수 있게 구성 가능
            dist_inside = distance_transform_edt(mask)
            signed_dist = dist_outside - dist_inside
            sdf = signed_dist
        else:
            # 도형 외부로부터의 거리만 계산하여 사용 (부호 없이 생성)
            sdf = dist_outside
        
        # # 4) 거리 범위 조절(spread)
        # #    spread 값에 비례하여 distance를 스케일링할 수 있음
        # print(f"Before spread: min={sdf.min()}, max={sdf.max()}")
        # sdf *= spread
        # print(f"After spread: min={sdf.min()}, max={sdf.max()}")

        # 5) 시각화를 위해 0~255로 정규화
        #    최소값 ~ 최대값을 0~1 범위로 맞춘 뒤 255 배
        # sdf_normalized = (sdf - sdf.min()) / (sdf.max() - sdf.min() + 1e-8)  # 0~1 범위
        # sdf_8bit = (sdf_normalized * 255).astype(np.uint8)
        sdf = np.clip(sdf, -max_distance, max_distance) # 최대 거리로 클리핑
        sdf_normalized = (sdf + max_distance) / (2 * max_distance)
        sdf_8bit = (sdf_normalized * 255).astype(np.uint8)
        
        # 6) 이미지 저장
        sdf_img = Image.fromarray(sdf_8bit, mode="L")

        # 텍스처 크기 설정
        sdf_img = sdf_img.resize((self.output_texture_size, self.output_texture_size), Image.LANCZOS)

        # 이미지 저장
        sdf_img.save(output_path)
        print(f"SDF 텍스처가 {output_path}에 저장되었습니다.")
        
        # 메시지 박스 표시
        unreal.EditorDialog.show_message("SDF 텍스처 생성 완료", f"SDF 텍스처가 {output_path}에 저장되었습니다.", unreal.AppMsgType.OK)

    def convert_r16_to_png16(self, input_path, output_path):
        """
        Converts a .r16 file to a 16-bit PNG file.

        Args:
            input_path (str): Path to the input .r16 file.
            output_path (str): Path to save the output .png file.
        """
        # Read the .r16 file as raw 16-bit unsigned integers
        with open(input_path, 'rb') as f:
            data = np.fromfile(f, dtype=np.uint16)

        # Assuming the .r16 file is a square image, calculate the dimensions
        size = int(np.sqrt(data.size))
        if size * size != data.size:
            raise ValueError("The .r16 file does not contain a square image.")

        # Reshape the data into a 2D array
        image_data = data.reshape((size, size))

        # Convert the numpy array to a Pillow Image
        image = Image.fromarray(image_data, mode='I;16')

        # Save the image as a 16-bit PNG
        image.save(output_path, format='PNG')
        print(f"Converted {input_path} to {output_path}.")

    def upscale_png16_to_8129(self, input_path, output_path):
        """
        Upscales a 16-bit PNG file from 4033x4033 resolution to 8129x8129 resolution.

        Args:
            input_path (str): Path to the input 16-bit PNG file.
            output_path (str): Path to save the upscaled 16-bit PNG file.
        """
        # Open the input PNG file as a Pillow Image
        image = Image.open(input_path)

        # Ensure the input image is in 16-bit mode
        if image.mode != 'I;16':
            raise ValueError("Input image is not a 16-bit PNG file.")

        # Resize the image to 8129x8129 using LANCZOS filter for high-quality upscaling
        upscaled_image = image.resize((8129, 8129), Image.LANCZOS)

        # Save the upscaled image as a 16-bit PNG
        upscaled_image.save(output_path, format='PNG')
        print(f"Upscaled {input_path} to {output_path} with resolution 8129x8129.")

# Create and show the UI
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()

window = SDFGen_Class()
window.show()

unreal.parent_external_window_to_slate(window.winId())
