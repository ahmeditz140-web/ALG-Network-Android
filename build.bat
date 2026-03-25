@echo off
echo =======================================
echo  Andols ECU Tuning Tool - Build Script
echo =======================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Building executable...
pyinstaller andols.spec --clean
echo.
echo Build complete!
echo Executable: dist\Andols_ECU_Tool.exe
pause
