import os
import sys
import traceback

import unreal


current_file_dir = os.path.dirname(os.path.abspath(__file__))
if current_file_dir not in sys.path:
    sys.path.append(current_file_dir)

try:
    from ArtScripts import RegisterMenu
    RegisterMenu.main()
except Exception:
    unreal.log_error("Cubeless: init_unreal.py failed\n{}".format(traceback.format_exc()))
