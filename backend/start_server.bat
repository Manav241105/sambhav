@echo off
REM Start the AutoPredict API for local development.
cd /d "%~dp0"
set PYTHONUTF8=1

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Applying database migrations...
alembic upgrade head || exit /b 1

echo.
echo Starting AutoPredict API on http://localhost:8001 (docs: /docs)
echo No demo data yet? Run: python -m sim.build
echo.
python webhook_server.py
