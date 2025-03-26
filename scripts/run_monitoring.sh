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

# Fonction pour vérifier le code de sortie
check_exit_code() {
    if [ $? -eq 0 ]; then
        print_message "$1" "$GREEN"
    else
        print_message "$2" "$RED"
        exit 1
    fi
}

# Création des répertoires nécessaires
print_message "Création des répertoires..." "$YELLOW"
mkdir -p logs data reports config

# Installation des dépendances
print_message "Installation des dépendances..." "$YELLOW"
./scripts/install_dependencies.sh
check_exit_code "Dépendances installées avec succès" "Échec de l'installation des dépendances"

# Configuration du monitoring
print_message "Configuration du monitoring..." "$YELLOW"
python3 -m scripts.monitor --setup
check_exit_code "Configuration du monitoring terminée" "Échec de la configuration du monitoring"

# Audit de sécurité
print_message "Exécution de l'audit de sécurité..." "$YELLOW"
python3 -m scripts.security_audit --auto-fix
check_exit_code "Audit de sécurité terminé" "Échec de l'audit de sécurité"

# Optimisation de la stratégie
print_message "Optimisation de la stratégie..." "$YELLOW"
python3 -m scripts.optimize_strategy --data data/latest.csv --iterations 1000 --risk-level 3
check_exit_code "Optimisation terminée" "Échec de l'optimisation"

# Génération du rapport
print_message "Génération du rapport..." "$YELLOW"
python3 -m scripts.monitor --report
check_exit_code "Rapport généré avec succès" "Échec de la génération du rapport"

# Vérification des services
print_message "Vérification des services..." "$YELLOW"
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

# Affichage des résultats
print_message "\nRésumé de l'exécution:" "$YELLOW"
echo "1. Configuration du monitoring: ✓"
echo "2. Audit de sécurité: ✓"
echo "3. Optimisation de la stratégie: ✓"
echo "4. Génération du rapport: ✓"
echo "5. Services Grafana et InfluxDB: ✓"

print_message "\nToutes les tâches ont été exécutées avec succès!" "$GREEN"
print_message "Les rapports sont disponibles dans le répertoire reports/" "$YELLOW" 