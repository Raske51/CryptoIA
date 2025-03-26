#!/bin/bash

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Déploiement du Bot Crypto sur Clouding.io${NC}"

# Vérification des dépendances
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python3 est requis mais n'est pas installé.${NC}" >&2; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo -e "${RED}pip3 est requis mais n'est pas installé.${NC}" >&2; exit 1; }

# Création de l'environnement virtuel
echo -e "${GREEN}Création de l'environnement virtuel...${NC}"
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
echo -e "${GREEN}Installation des dépendances...${NC}"
pip install -r requirements.txt

# Vérification du fichier .env
if [ ! -f .env ]; then
    echo -e "${RED}Fichier .env non trouvé. Création d'un nouveau fichier...${NC}"
    cp .env.example .env
    echo -e "${RED}Veuillez configurer vos variables d'environnement dans le fichier .env${NC}"
    exit 1
fi

# Configuration du service systemd
echo -e "${GREEN}Configuration du service systemd...${NC}"
sudo tee /etc/systemd/system/cryptobot.service << EOF
[Unit]
Description=Bot de Trading Crypto
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Rechargement de systemd et démarrage du service
echo -e "${GREEN}Démarrage du service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable cryptobot
sudo systemctl start cryptobot

# Vérification du statut
echo -e "${GREEN}Vérification du statut du service...${NC}"
sudo systemctl status cryptobot

echo -e "${GREEN}Déploiement terminé !${NC}"
echo -e "Pour voir les logs: ${GREEN}sudo journalctl -u cryptobot -f${NC}" 