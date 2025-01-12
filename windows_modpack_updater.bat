@echo off

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python não encontrado! Certifique-se de que o Python esteja instalado e no PATH.
    pause
    exit /b
)

start "" pythonw.exe ./main.py
exit
