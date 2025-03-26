#!/bin/bash

# Configuration
LOG_FILE="logs/deploy.log"
CONFIG_FILE="config/deploy_config.json"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Fonction de logging
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Fonction de vérification des prérequis
check_prerequisites() {
    log "INFO" "Vérification des prérequis..."
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python3 n'est pas installé"
        exit 1
    fi
    
    # Vérifier les dépendances
    if ! pip freeze | grep -q "schedule"; then
        log "WARNING" "Installation des dépendances manquantes..."
        pip install -r requirements.txt
    fi
    
    # Vérifier les fichiers de configuration
    if [ ! -f "$CONFIG_FILE" ]; then
        log "ERROR" "Fichier de configuration $CONFIG_FILE non trouvé"
        exit 1
    fi
    
    # Créer les dossiers nécessaires
    mkdir -p logs backups
}

# Fonction de sauvegarde
backup() {
    local backup_name="backup_${TIMESTAMP}"
    log "INFO" "Création de la sauvegarde $backup_name..."
    
    # Sauvegarder les fichiers de configuration
    cp config/* "$BACKUP_DIR/${backup_name}_config/"
    
    # Sauvegarder les données
    cp data/* "$BACKUP_DIR/${backup_name}_data/"
    
    log "INFO" "Sauvegarde terminée"
}

# Fonction de test
run_tests() {
    log "INFO" "Exécution des tests..."
    
    # Tests unitaires
    if ! python3 -m pytest tests/unit/ -v; then
        log "ERROR" "Échec des tests unitaires"
        exit 1
    fi
    
    # Tests d'intégration
    if ! python3 -m pytest tests/integration/ -v; then
        log "ERROR" "Échec des tests d'intégration"
        exit 1
    fi
    
    # Tests de performance
    if ! python3 -m pytest tests/performance/ -v; then
        log "WARNING" "Tests de performance non optimaux"
    fi
    
    log "INFO" "Tests terminés avec succès"
}

# Fonction d'optimisation
optimize() {
    log "INFO" "Optimisation des paramètres..."
    
    # Optimisation de la stratégie
    python3 scripts/optimize_strategy.py --strategy=enhanced_v2 --risk=4
    
    # Optimisation des paramètres de trading
    python3 scripts/optimize_params.py --risk=4
    
    # Vérification des résultats
    if [ ! -f "config/optimized_params.json" ]; then
        log "ERROR" "Échec de l'optimisation"
        exit 1
    fi
    
    log "INFO" "Optimisation terminée"
}

# Fonction de déploiement progressif
deploy_progressive() {
    local total_capital=$1
    local risk_level=$2
    
    log "INFO" "Démarrage du déploiement progressif..."
    
    # Déploiement par paliers
    for percentage in 5 25 50 100; do
        log "INFO" "Déploiement à $percentage% du capital..."
        
        # Calcul du capital pour ce palier
        local capital=$((total_capital * percentage / 100))
        
        # Déploiement avec gestion des erreurs
        if ! python3 scripts/deploy.py --capital=$capital --risk=$risk_level; then
            log "ERROR" "Échec du déploiement à $percentage%"
            return 1
        fi
        
        # Vérification de la santé du système
        if ! python3 scripts/health_check.py; then
            log "ERROR" "Problème de santé détecté à $percentage%"
            return 1
        fi
        
        # Attente proportionnelle
        local wait_time=$((percentage * 60))
        log "INFO" "Attente de $wait_time secondes..."
        sleep $wait_time
    done
    
    log "INFO" "Déploiement progressif terminé"
    return 0
}

# Fonction de vérification post-déploiement
verify_deployment() {
    log "INFO" "Vérification post-déploiement..."
    
    # Vérification des services
    if ! python3 scripts/check_services.py; then
        log "ERROR" "Services non fonctionnels"
        return 1
    fi
    
    # Vérification des métriques
    if ! python3 scripts/check_metrics.py; then
        log "WARNING" "Métriques non optimales"
    fi
    
    # Vérification des alertes
    if ! python3 scripts/check_alerts.py; then
        log "WARNING" "Système d'alertes non fonctionnel"
    fi
    
    log "INFO" "Vérification post-déploiement terminée"
    return 0
}

# Fonction principale
main() {
    log "INFO" "Démarrage du processus de déploiement..."
    
    # Vérification des prérequis
    check_prerequisites
    
    # Sauvegarde
    backup
    
    # Tests
    run_tests
    
    # Optimisation
    optimize
    
    # Déploiement progressif
    if ! deploy_progressive 100000 3; then
        log "ERROR" "Échec du déploiement progressif"
        exit 1
    fi
    
    # Vérification post-déploiement
    if ! verify_deployment; then
        log "ERROR" "Échec de la vérification post-déploiement"
        exit 1
    fi
    
    log "INFO" "Déploiement terminé avec succès"
}

# Gestion des erreurs
set -e
trap 'log "ERROR" "Une erreur est survenue à la ligne $LINENO"' ERR
trap 'log "INFO" "Arrêt du script"' EXIT

# Exécution
main 