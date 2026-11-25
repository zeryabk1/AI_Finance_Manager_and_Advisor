@echo off
REM ============================================================
REM Builds AI_Finance_Manager.exe from this project.
REM Run this on the SAME Windows machine where the app already
REM works (double-click it, or run it from a terminal in this
REM folder). Needs internet access the first time to install
REM PyInstaller.
REM
REM To use your own logo: put a file named app_icon.ico in this
REM same folder before running this script. See MAKE_YOUR_ICON.txt
REM for how to turn a PNG/JPG logo into an .ico file.
REM ============================================================

echo Installing PyInstaller (skips if already installed)...
python -m pip install --upgrade pyinstaller

echo.
if exist app_icon.ico (
    echo Using app_icon.ico as the exe icon.
    set ICON_FLAG=--icon "app_icon.ico"
) else (
    echo No app_icon.ico found next to build_exe.bat - building with the default icon.
    echo ^(See MAKE_YOUR_ICON.txt if you want your own logo on the exe.^)
    set ICON_FLAG=
)

echo.
echo Building AI_Finance_Manager.exe - this can take several minutes...
echo.

python -m PyInstaller ^
  --name AI_Finance_Manager ^
  --onedir ^
  --noupx ^
  --windowed ^
  %ICON_FLAG% ^
  --clean ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --add-data "accounts\templates;accounts\templates" ^
  --add-data "companies\templates;companies\templates" ^
  --add-data "accounting\templates;accounting\templates" ^
  --add-data "transactions\templates;transactions\templates" ^
  --add-data "inventory\templates;inventory\templates" ^
  --add-data "assets\templates;assets\templates" ^
  --add-data "reports\templates;reports\templates" ^
  --add-data "dashboard\templates;dashboard\templates" ^
  --collect-submodules financeproject ^
  --collect-submodules accounts ^
  --collect-submodules companies ^
  --collect-submodules accounting ^
  --collect-submodules transactions ^
  --collect-submodules inventory ^
  --collect-submodules assets ^
  --collect-submodules reports ^
  --collect-submodules dashboard ^
  --hidden-import accounting.management.commands.seed_demo_data ^
  --collect-submodules api ^
  --collect-submodules ai_models ^
  --collect-all django ^
  --collect-all rest_framework ^
  --collect-all sklearn ^
  --collect-all scipy ^
  --collect-all pandas ^
  --collect-all numpy ^
  --collect-all joblib ^
  --collect-all reportlab ^
  --collect-all openpyxl ^
  --collect-all PIL ^
  desktop_launcher.py

echo.
if exist dist\AI_Finance_Manager\AI_Finance_Manager.exe (
    echo ============================================================
    echo   BUILD SUCCEEDED
    echo   Your app is the FOLDER: dist\AI_Finance_Manager
    echo   AI_Finance_Manager.exe lives inside that folder along with
    echo   a "_internal" folder of dependencies it needs next to it.
    echo.
    echo   TO SHARE: zip the whole "AI_Finance_Manager" folder ^(right
    echo   click it -^> Send to -^> Compressed folder^) and send that.
    echo   The other person unzips it once, then double-clicks the
    echo   .exe inside every time after that - much faster to open
    echo   than a single-file exe, since nothing needs to be
    echo   unpacked again on every launch.
    echo ============================================================
) else (
    echo ============================================================
    echo   BUILD FAILED - scroll up to see the error from PyInstaller.
    echo   Common fix: it will usually say "No module named X" -
    echo   copy that error and send it back so it can be fixed.
    echo ============================================================
)
pause
