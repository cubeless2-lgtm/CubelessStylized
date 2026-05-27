@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "GENERATOR=%SCRIPT_DIR%generate_stylized_formation_volume.py"
set "CONFIG=%SCRIPT_DIR%stylized_formation_volume_default.json"
set "OUTPUT=%SCRIPT_DIR%FormationVolumeSheet_Stylized.png"
set "PREVIEW=%SCRIPT_DIR%FormationVolumeSheet_Stylized_preview.png"
set "STATS=%SCRIPT_DIR%FormationVolumeSheet_Stylized_stats.json"

"%PYTHON_EXE%" "%GENERATOR%" --config "%CONFIG%" --output "%OUTPUT%" --preview "%PREVIEW%" --stats "%STATS%"

pause
