import os
import sys
import unreal

current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)
    
from PySide2 import QtWidgets


winName = 'unreal Button Window'

class TestWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TestWidget, self).__init__(parent)
        self.setWindowTitle(winName)
        self.setFixedWidth(300)
        self.create_widgets()

    def create_widgets(self):
        #Button
        self.pushButton = QtWidgets.QPushButton("Test")
        self.pushButton.setFixedSize(100, 50)
        self.pushButton.clicked.connect(self.Button_command)

        #Layout
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.pushButton)

    def Button_command(self):
        print("aa")


app = None
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
widget = TestWidget()
widget.show()
unreal.parent_external_window_to_slate(widget.winId())