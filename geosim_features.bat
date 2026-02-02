@echo off
REM GeoSim CLI Wrapper - Place this anywhere

REM Try to find the Python script
if exist ".\geo-core\features_Enrichment_Engine\cli\geosim_features.py" (
    set SCRIPT_PATH=.\geo-core\features_Enrichment_Engine\cli\geosim_features.py
    goto run
)

if exist "..\geo-core\features_Enrichment_Engine\cli\geosim_features.py" (
    set SCRIPT_PATH=..\geo-core\features_Enrichment_Engine\cli\geosim_features.py
    goto run
)

if exist "geo-core\features_Enrichment_Engine\cli\geosim_features.py" (
    set SCRIPT_PATH=geo-core\features_Enrichment_Engine\cli\geosim_features.py
    goto run
)

echo ❌ ERROR: Could not find geosim_features.py
echo Looking in:
echo   .\geo-core\features_Enrichment_Engine\cli\
echo   ..\geo-core\features_Enrichment_Engine\cli\
echo   geo-core\features_Enrichment_Engine\cli\
echo.
echo Place this batch file in your project root or near geosim_features.py
pause
exit /b 1

:run
python "%SCRIPT_PATH%" %*