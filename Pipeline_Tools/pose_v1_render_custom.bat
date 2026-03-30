@echo off
set BLENDER="C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
set FILE="X:\Project\ysj\pub\lgt_comp\lookdev\yjTie\pose_v1\pose_v1.blend"

:: Custom Frames
set FRAMES="101,112,117,151,162,167,201,206,213,221,240,245,251,256,263,271,290,295"
set WRAPPER="X:\AI_Automation\Pipeline_Tools\render_frames_batch.py"

echo ===========================================
echo BATCH RENDER: pose_v1.blend (Custom Frames)
echo ===========================================


echo --- Scene: Scene_color ---
echo Rendering Scene_color_001...
%BLENDER% -b %FILE% -y -S "Scene_color" -P %WRAPPER% -- "Scene_color_001" %FRAMES%

echo --- Scene: Scene_light ---
echo Rendering Scene_light_001...
%BLENDER% -b %FILE% -y -S "Scene_light" -P %WRAPPER% -- "Scene_light_001" %FRAMES%
echo Rendering Scene_light_002...
%BLENDER% -b %FILE% -y -S "Scene_light" -P %WRAPPER% -- "Scene_light_002" %FRAMES%
echo Rendering Scene_light_003...
%BLENDER% -b %FILE% -y -S "Scene_light" -P %WRAPPER% -- "Scene_light_003" %FRAMES%
echo Rendering Scene_light_004...
%BLENDER% -b %FILE% -y -S "Scene_light" -P %WRAPPER% -- "Scene_light_004" %FRAMES%
echo Rendering Scene_light_005...
%BLENDER% -b %FILE% -y -S "Scene_light" -P %WRAPPER% -- "Scene_light_005" %FRAMES%
echo Rendering Scene_light_006...
%BLENDER% -b %FILE% -y -S "Scene_light" -P %WRAPPER% -- "Scene_light_006" %FRAMES%
echo Rendering Scene_light_007...
%BLENDER% -b %FILE% -y -S "Scene_light" -P %WRAPPER% -- "Scene_light_007" %FRAMES%

echo --- Scene: Scene_sss ---
echo Rendering Scene_sss_001...
%BLENDER% -b %FILE% -y -S "Scene_sss" -P %WRAPPER% -- "Scene_sss_001" %FRAMES%
echo Rendering Scene_sss_002...
%BLENDER% -b %FILE% -y -S "Scene_sss" -P %WRAPPER% -- "Scene_sss_002" %FRAMES%
echo Rendering Scene_sss_003...
%BLENDER% -b %FILE% -y -S "Scene_sss" -P %WRAPPER% -- "Scene_sss_003" %FRAMES%
echo Rendering Scene_sss_004...
%BLENDER% -b %FILE% -y -S "Scene_sss" -P %WRAPPER% -- "Scene_sss_004" %FRAMES%
echo Rendering Scene_sss_005...
%BLENDER% -b %FILE% -y -S "Scene_sss" -P %WRAPPER% -- "Scene_sss_005" %FRAMES%
echo Rendering Scene_sss_006...
%BLENDER% -b %FILE% -y -S "Scene_sss" -P %WRAPPER% -- "Scene_sss_006" %FRAMES%
echo Rendering Scene_sss_007...
%BLENDER% -b %FILE% -y -S "Scene_sss" -P %WRAPPER% -- "Scene_sss_007" %FRAMES%

echo --- Scene: Scene_twod ---
echo Rendering Scene_twod_001...
%BLENDER% -b %FILE% -y -S "Scene_twod" -P %WRAPPER% -- "Scene_twod_001" %FRAMES%
echo Rendering Scene_twod_002...
%BLENDER% -b %FILE% -y -S "Scene_twod" -P %WRAPPER% -- "Scene_twod_002" %FRAMES%

echo DONE
pause