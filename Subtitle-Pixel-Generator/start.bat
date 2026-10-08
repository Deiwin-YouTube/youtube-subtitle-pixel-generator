@echo off
cd /d "%~dp0"
python -m pip install --user Pillow
python "%~dp0subtitle_generator.py"
if errorlevel 1 (
    echo.
    echo Program exited with an error.
    pause
)
