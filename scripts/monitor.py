import os
import sys
import logging
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any
from .monitoring_setup import MonitoringSetup
from .health_checker import HealthChecker
from .security_manager import SecurityManager
from .optimization_manager import OptimizationManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        argparse.Namespace: Arguments parsés
    """
    parser = argparse.ArgumentParser(description='Script de monitoring du bot de trading')
    parser.add_argument('--setup', action='store_true', help='Configure le monitoring')
    parser.add_argument('--audit', action='store_true', help='Exécute un audit de sécurité')
    parser.add_argument('--optimize', action='store_true', help='Optimise la stratégie de trading')
    parser.add_argument('--report', action='store_true', help='Génère un rapport de monitoring')
    parser.add_argument('--config', type=str, default='config/monitoring_config.json',
                      help='Chemin du fichier de configuration')
    return parser.parse_args()

async def main():
    """
    Fonction principale du script.
    """
    try:
        # Parse des arguments
        args = parse_args()
        
        # Initialisation des gestionnaires
        health_checker = HealthChecker()
        security_manager = SecurityManager()
        optimization_manager = OptimizationManager()
        
        # Création du gestionnaire de monitoring
        monitoring = MonitoringSetup(
            health_checker=health_checker,
            security_manager=security_manager,
            optimization_manager=optimization_manager,
            config_file=args.config
        )
        
        # Exécution des tâches demandées
        if args.setup:
            logger.info("Configuration du monitoring...")
            if monitoring.setup_monitoring():
                logger.info("Configuration terminée avec succès")
            else:
                logger.error("Échec de la configuration")
                
        if args.audit:
            logger.info("Exécution de l'audit de sécurité...")
            results = monitoring.run_security_audit()
            logger.info(f"Score de sécurité: {results['score']}")
            logger.info(f"Vulnérabilités trouvées: {len(results['vulnerabilities'])}")
            logger.info(f"Corrections appliquées: {len(results['fixes_applied'])}")
            
        if args.optimize:
            logger.info("Optimisation de la stratégie de trading...")
            results = monitoring.optimize_trading_strategy()
            if results.get('success', False):
                logger.info("Optimisation réussie")
                logger.info(f"Paramètres optimaux: {results['parameters']}")
            else:
                logger.error("Échec de l'optimisation")
                
        if args.report:
            logger.info("Génération du rapport de monitoring...")
            report = monitoring.generate_report()
            
            # Sauvegarde du rapport
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f'reports/monitoring_report_{timestamp}.json'
            
            os.makedirs('reports', exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=4)
                
            logger.info(f"Rapport sauvegardé dans {report_file}")
            
        # Si aucune tâche n'est spécifiée, exécute toutes les tâches
        if not any([args.setup, args.audit, args.optimize, args.report]):
            logger.info("Exécution de toutes les tâches de monitoring...")
            
            # Configuration
            if monitoring.setup_monitoring():
                logger.info("Configuration terminée avec succès")
            else:
                logger.error("Échec de la configuration")
                
            # Audit de sécurité
            security_results = monitoring.run_security_audit()
            logger.info(f"Score de sécurité: {security_results['score']}")
            
            # Optimisation
            optimization_results = monitoring.optimize_trading_strategy()
            if optimization_results.get('success', False):
                logger.info("Optimisation réussie")
            else:
                logger.error("Échec de l'optimisation")
                
            # Rapport
            report = monitoring.generate_report()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f'reports/monitoring_report_{timestamp}.json'
            
            os.makedirs('reports', exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=4)
                
            logger.info(f"Rapport sauvegardé dans {report_file}")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du script: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 