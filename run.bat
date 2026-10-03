@echo off
if exist "%~dp0..\run.bat" (
    call "%~dp0..\run.bat"
) else (
    cd /d "%~dp0"
    python app.py
)
