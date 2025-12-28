@echo off
REM filepath: c:\Users\dennis\Desktop\nom\launch.bat
setlocal enabledelayedexpansion

REM Check if venv exists
if not exist venv\Scripts\activate.bat (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

REM Activate the virtual environment
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Run the main script
python main.py
if %errorlevel% neq 0 (
    echo The program exited with an error.
    pause
)

REM Deactivate the virtual environment
call venv\Scripts\deactivate.bat

echo Program execution completed.
pause