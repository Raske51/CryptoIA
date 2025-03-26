import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List
from .security_manager import SecurityManager
from .alert_manager import AlertManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security_audit.log'),
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
    parser = argparse.ArgumentParser(description='Script d\'audit de sécurité')
    parser.add_argument('--auto-fix', action='store_true', help='Applique automatiquement les corrections')
    parser.add_argument('--config', type=str, default='config/monitoring_config.json',
                      help='Chemin du fichier de configuration')
    parser.add_argument('--output', type=str, default='reports/security_audit.json',
                      help='Chemin du fichier de rapport')
    return parser.parse_args()

async def run_security_checks(security_manager: SecurityManager) -> Dict[str, Any]:
    """
    Exécute les vérifications de sécurité.
    
    Args:
        security_manager (SecurityManager): Gestionnaire de sécurité
        
    Returns:
        Dict[str, Any]: Résultats des vérifications
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'vulnerabilities': [],
        'fixes_applied': [],
        'score': 0.0
    }
    
    try:
        # Vérification des dépendances
        logger.info("Vérification des dépendances...")
        dependencies = await security_manager.check_dependencies()
        results['checks']['dependencies'] = dependencies
        results['vulnerabilities'].extend(dependencies)
        
        # Vérification des configurations
        logger.info("Vérification des configurations...")
        configs = await security_manager.check_configurations()
        results['checks']['configurations'] = configs
        results['vulnerabilities'].extend(configs)
        
        # Vérification des permissions
        logger.info("Vérification des permissions...")
        permissions = await security_manager.check_permissions()
        results['checks']['permissions'] = permissions
        results['vulnerabilities'].extend(permissions)
        
        # Vérification des clés API
        logger.info("Vérification des clés API...")
        api_keys = await security_manager.check_api_keys()
        results['checks']['api_keys'] = api_keys
        results['vulnerabilities'].extend(api_keys)
        
        # Vérification des logs
        logger.info("Vérification des logs...")
        logs = await security_manager.check_logs()
        results['checks']['logs'] = logs
        results['vulnerabilities'].extend(logs)
        
        # Calcul du score
        total_vulns = len(results['vulnerabilities'])
        results['score'] = 1.0 - (total_vulns / max(total_vulns, 1))
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur lors des vérifications de sécurité: {str(e)}")
        return results

async def apply_fixes(security_manager: SecurityManager, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Applique les corrections de sécurité.
    
    Args:
        security_manager (SecurityManager): Gestionnaire de sécurité
        vulnerabilities (List[Dict[str, Any]]): Liste des vulnérabilités
        
    Returns:
        List[Dict[str, Any]]: Liste des corrections appliquées
    """
    fixes_applied = []
    
    try:
        for vuln in vulnerabilities:
            if vuln.get('fixable', False):
                logger.info(f"Application de la correction pour: {vuln['description']}")
                fix = await security_manager.apply_fix(vuln)
                if fix:
                    fixes_applied.append(fix)
                    
        return fixes_applied
        
    except Exception as e:
        logger.error(f"Erreur lors de l'application des corrections: {str(e)}")
        return fixes_applied

async def main():
    """
    Fonction principale du script.
    """
    try:
        # Parse des arguments
        args = parse_args()
        
        # Initialisation des gestionnaires
        security_manager = SecurityManager()
        alert_manager = AlertManager()
        
        # Exécution des vérifications
        logger.info("Démarrage de l'audit de sécurité...")
        results = await run_security_checks(security_manager)
        
        # Application des corrections si demandé
        if args.auto_fix:
            logger.info("Application des corrections...")
            results['fixes_applied'] = await apply_fixes(
                security_manager,
                results['vulnerabilities']
            )
            
        # Envoi des alertes si nécessaire
        if results['score'] < 0.7:
            await alert_manager.send_telegram_alert(
                os.getenv('TELEGRAM_ADMIN_ID'),
                f"⚠️ Score de sécurité faible: {results['score']:.2f}\n"
                f"Vulnérabilités trouvées: {len(results['vulnerabilities'])}\n"
                f"Corrections appliquées: {len(results['fixes_applied'])}"
            )
            
        # Sauvegarde du rapport
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=4)
            
        logger.info(f"Rapport sauvegardé dans {args.output}")
        
        # Affichage du résumé
        print("\nRésumé de l'audit de sécurité:")
        print(f"Score: {results['score']:.2f}")
        print(f"Vulnérabilités trouvées: {len(results['vulnerabilities'])}")
        print(f"Corrections appliquées: {len(results['fixes_applied'])}")
        
        # Code de sortie basé sur le score
        sys.exit(0 if results['score'] >= 0.7 else 1)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du script: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 