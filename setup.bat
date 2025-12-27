@echo off
echo ========================================
echo PPT Generator Setup Script
echo ========================================
echo.

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo Please make sure Python and pip are installed
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo [2/3] Creating config.yaml from template...
if not exist config.yaml (
    copy config.yaml.example config.yaml >nul
    echo [OK] config.yaml created
) else (
    echo [INFO] config.yaml already exists, skipping...
)
echo.

echo [3/3] Setup complete!
echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo 1. Edit config.yaml and add your API keys
echo 2. Run: python generate_ppt_from_pdf.py "your_file.pdf"
echo.
echo Press any key to open config.yaml for editing...
pause >nul
notepad config.yaml

