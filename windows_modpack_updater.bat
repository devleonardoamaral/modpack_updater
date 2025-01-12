@echo off

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python não encontrado! Certifique-se de que o Python esteja instalado e no PATH.
    pause
    exit /b
)

python main.py
pause
