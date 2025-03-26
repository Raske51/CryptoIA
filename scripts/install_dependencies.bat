@echo on
setlocal enabledelayedexpansion

:: Check Python
py --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

:: Check pip
py -m pip --version > nul 2>&1
if errorlevel 1 (
    echo pip is not installed. Installing...
    py -m ensurepip --default-pip
    if errorlevel 1 (
        echo Failed to install pip
        exit /b 1
    )
)

:: Install Python dependencies
echo Installing Python dependencies...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install Python dependencies
    exit /b 1
)

:: Check Docker
docker --version > nul 2>&1
if errorlevel 1 (
    echo Docker is not installed. Please install Docker Desktop for Windows.
    echo Download from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

:: Check Docker Compose
docker-compose --version > nul 2>&1
if errorlevel 1 (
    echo Docker Compose is not installed. Installing...
    py -m pip install docker-compose
    if errorlevel 1 (
        echo Failed to install Docker Compose
        exit /b 1
    )
)

:: Configure Grafana and InfluxDB
echo Configuring Grafana and InfluxDB...
(
echo version: '3'
echo services:
echo   grafana:
echo     image: grafana/grafana:latest
echo     ports:
echo       - "3000:3000"
echo     environment:
echo       - GF_SECURITY_ADMIN_PASSWORD=%%GRAFANA_ADMIN_PASSWORD%%
echo       - GF_USERS_ALLOW_SIGN_UP=false
echo     volumes:
echo       - grafana-storage:/var/lib/grafana
echo     depends_on:
echo       - influxdb
echo.
echo   influxdb:
echo     image: influxdb:latest
echo     ports:
echo       - "8086:8086"
echo     environment:
echo       - DOCKER_INFLUXDB_INIT_MODE=setup
echo       - DOCKER_INFLUXDB_INIT_USERNAME=%%INFLUXDB_USER%%
echo       - DOCKER_INFLUXDB_INIT_PASSWORD=%%INFLUXDB_PASSWORD%%
echo       - DOCKER_INFLUXDB_INIT_ORG=%%INFLUXDB_ORG%%
echo       - DOCKER_INFLUXDB_INIT_BUCKET=%%INFLUXDB_BUCKET%%
echo       - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=%%INFLUXDB_TOKEN%%
echo     volumes:
echo       - influxdb-storage:/var/lib/influxdb2
echo.
echo volumes:
echo   grafana-storage:
echo   influxdb-storage:
) > docker-compose.yml

:: Create .env file if it doesn't exist
if not exist .env (
    echo Configuring environment variables...
    (
    echo GRAFANA_ADMIN_PASSWORD=admin
    echo INFLUXDB_USER=admin
    echo INFLUXDB_PASSWORD=admin
    echo INFLUXDB_ORG=trading_bot
    echo INFLUXDB_BUCKET=trading_metrics
    echo INFLUXDB_TOKEN=your-token-here
    echo GRAFANA_API_KEY=your-api-key-here
    echo TELEGRAM_ADMIN_ID=your-telegram-id
    echo ALERT_EMAIL=your-email@example.com
    ) > .env
)

:: Start services
echo Starting services...
docker-compose up -d
if errorlevel 1 (
    echo Failed to start services
    exit /b 1
)

:: Check services
echo Checking services...
timeout /t 5 /nobreak > nul

curl -s http://localhost:3000 > nul
if errorlevel 1 (
    echo Error: Grafana is not accessible
    exit /b 1
)
echo Grafana is accessible at http://localhost:3000

curl -s http://localhost:8086/health > nul
if errorlevel 1 (
    echo Error: InfluxDB is not accessible
    exit /b 1
)
echo InfluxDB is accessible at http://localhost:8086

echo Installation completed successfully! 