#!/bin/bash

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Fonction pour afficher les messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    print_message "Python3 n'est pas installé. Installation..." "$YELLOW"
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

# Vérification de pip
if ! command -v pip3 &> /dev/null; then
    print_message "pip3 n'est pas installé. Installation..." "$YELLOW"
    sudo apt-get install -y python3-pip
fi

# Installation des dépendances Python
print_message "Installation des dépendances Python..." "$YELLOW"
pip3 install -r requirements.txt

# Vérification de Docker
if ! command -v docker &> /dev/null; then
    print_message "Docker n'est pas installé. Installation..." "$YELLOW"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
fi

# Vérification de Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_message "Docker Compose n'est pas installé. Installation..." "$YELLOW"
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.5.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Création des répertoires nécessaires
print_message "Création des répertoires..." "$YELLOW"
mkdir -p logs data reports config

# Configuration de Grafana et InfluxDB
print_message "Configuration de Grafana et InfluxDB..." "$YELLOW"
cat > docker-compose.yml << EOL
version: '3'
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=\${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-storage:/var/lib/grafana
    depends_on:
      - influxdb

  influxdb:
    image: influxdb:latest
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=\${INFLUXDB_USER}
      - DOCKER_INFLUXDB_INIT_PASSWORD=\${INFLUXDB_PASSWORD}
      - DOCKER_INFLUXDB_INIT_ORG=\${INFLUXDB_ORG}
      - DOCKER_INFLUXDB_INIT_BUCKET=\${INFLUXDB_BUCKET}
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=\${INFLUXDB_TOKEN}
    volumes:
      - influxdb-storage:/var/lib/influxdb2

volumes:
  grafana-storage:
  influxdb-storage:
EOL

# Création du fichier .env
print_message "Configuration des variables d'environnement..." "$YELLOW"
cat > .env << EOL
GRAFANA_ADMIN_PASSWORD=admin
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=admin
INFLUXDB_ORG=trading_bot
INFLUXDB_BUCKET=trading_metrics
INFLUXDB_TOKEN=your-token-here
GRAFANA_API_KEY=your-api-key-here
TELEGRAM_ADMIN_ID=your-telegram-id
ALERT_EMAIL=your-email@example.com
EOL

# Démarrage des services
print_message "Démarrage des services..." "$YELLOW"
docker-compose up -d

# Vérification des services
print_message "Vérification des services..." "$YELLOW"
sleep 5

if curl -s http://localhost:3000 > /dev/null; then
    print_message "Grafana est accessible sur http://localhost:3000" "$GREEN"
else
    print_message "Erreur: Grafana n'est pas accessible" "$RED"
    exit 1
fi

if curl -s http://localhost:8086/health > /dev/null; then
    print_message "InfluxDB est accessible sur http://localhost:8086" "$GREEN"
else
    print_message "Erreur: InfluxDB n'est pas accessible" "$RED"
    exit 1
fi

print_message "Installation terminée avec succès!" "$GREEN"
print_message "N'oubliez pas de configurer les variables d'environnement dans le fichier .env" "$YELLOW" 