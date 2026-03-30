@echo off
title PPAS Lib QC Dashboard
echo [PPAS] Checking Blender dependencies...
set BLENDER_PY="C:\Program Files\Blender Foundation\Blender 5.0\5.0\python\bin\python.exe"
if exist %BLENDER_PY% (
    %BLENDER_PY% -c "import shotgun_api3" >nul 2>&1
    if errorlevel 1 (
        echo [PPAS] Auto-installing Flow plugin for Blender...
        %BLENDER_PY% -m pip install shotgun_api3
    )
) else (
    echo [PPAS] WARNING: Blender 5.0 not found at default C: path!
    timeout /t 3 >nul
)

echo [PPAS] Launching with Portable Python Environment...
set PORTABLE_PY="X:\AI_Automation\.gemini\env_core\Python27_Portable\pythonw.exe"
cd /d "X:\AI_Automation\.gemini\skills\qc-dashboard-pro\scripts"
start "" %PORTABLE_PY% lib_qc_dashboard.py
exit