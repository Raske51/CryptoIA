@echo on
setlocal enabledelayedexpansion

echo ====================================
echo Starting monitoring system
echo ====================================
echo.

:: Creating necessary directories
echo [1/7] Creating directories...
if not exist logs mkdir logs
if not exist data mkdir data
if not exist reports mkdir reports
if not exist config mkdir config
echo.

:: Installing dependencies
echo [2/7] Installing dependencies...
call scripts\install_dependencies.bat
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

:: Configuring monitoring
echo [3/7] Configuring monitoring...
py -m scripts.monitor --setup
if errorlevel 1 (
    echo ERROR: Failed to configure monitoring
    pause
    exit /b 1
)
echo.

:: Security audit
echo [4/7] Running security audit...
py -m scripts.security_audit --auto-fix
if errorlevel 1 (
    echo ERROR: Security audit failed
    pause
    exit /b 1
)
echo.

:: Strategy optimization
echo [5/7] Optimizing strategy...
py -m scripts.optimize_strategy --data data\latest.csv --iterations 1000 --risk-level 3
if errorlevel 1 (
    echo ERROR: Strategy optimization failed
    pause
    exit /b 1
)
echo.

:: Report generation
echo [6/7] Generating report...
py -m scripts.monitor --report
if errorlevel 1 (
    echo ERROR: Report generation failed
    pause
    exit /b 1
)
echo.

:: Service verification
echo [7/7] Verifying services...
timeout /t 5 /nobreak > nul

echo Checking Grafana...
curl -s http://localhost:3000 > nul
if errorlevel 1 (
    echo ERROR: Grafana is not accessible
    pause
    exit /b 1
)
echo OK: Grafana is accessible at http://localhost:3000

echo Checking InfluxDB...
curl -s http://localhost:8086/health > nul
if errorlevel 1 (
    echo ERROR: InfluxDB is not accessible
    pause
    exit /b 1
)
echo OK: InfluxDB is accessible at http://localhost:8086

echo.
echo ====================================
echo Installation completed successfully!
echo ====================================
echo.
echo Reports are available in the reports/ folder
echo.
pause 