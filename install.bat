@echo off
echo Installing Cando...
echo.

REM Create installation directory
set INSTALL_DIR=%PROGRAMFILES%\Cando
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy executable
copy "Cando.exe" "%INSTALL_DIR%\Cando.exe"

REM Create desktop shortcut
set DESKTOP=%USERPROFILE%\Desktop
echo @echo off > "%DESKTOP%\Cando.bat"
echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\Cando.bat"
echo start Cando.exe >> "%DESKTOP%\Cando.bat"

echo.
echo Installation complete!
echo You can now run Cando from your desktop or start menu.
pause
