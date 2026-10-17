@echo off
cd /d "%~dp0"
python -m pip install --user Pillow
python "%~dp0subtitle_generator.py"
echo.
echo Program closed. If an error appeared above, take a screenshot of it.
pause
