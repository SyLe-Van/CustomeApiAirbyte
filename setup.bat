@echo off
REM NetSuite Proxy API - Quick Start Script for Windows

echo ====================================
echo NetSuite Proxy API - Quick Start
echo ====================================
echo.

echo Choose setup method:
echo 1) Local Python setup
echo 2) Docker setup
set /p choice="Enter choice [1-2]: "

if "%choice%"=="1" goto python
if "%choice%"=="2" goto docker
echo Invalid choice
exit /b 1

:python
echo.
echo Setting up Python environment...
cd python

if not exist .env (
    echo Creating .env file...
    copy .env.example .env
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To start the server:
echo   cd python
echo   venv\Scripts\activate
echo   python main.py
echo.
echo Or with uvicorn:
echo   uvicorn main:app --reload
echo.
echo API will be available at: http://localhost:8000
echo API Key: netsuite_proxy_api_key_2026_secure
goto end

:docker
echo.
echo Setting up Docker...

if not exist python\.env (
    echo Creating python\.env...
    copy python\.env.example python\.env
)

echo Building and starting container...
docker-compose up -d --build

echo.
echo Setup complete!
echo.
echo API is running at: http://localhost:8000
echo API Key: netsuite_proxy_api_key_2026_secure
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop:
echo   docker-compose down

:end
echo.
echo Documentation:
echo   - README.md - General documentation
echo   - docs\AIRBYTE_SETUP.md - Airbyte integration guide
echo   - docs\API_EXAMPLES.md - API usage examples
echo.
echo Next steps:
echo   1. Test the API: curl http://localhost:8000/health
echo   2. Configure Airbyte using docs\AIRBYTE_SETUP.md
echo   3. Start syncing data!
echo.
pause
