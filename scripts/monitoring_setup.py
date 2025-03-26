import os
import json
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .health_checker import HealthChecker
from .security_manager import SecurityManager
from .optimization_manager import OptimizationManager

logger = logging.getLogger(__name__)

class MonitoringSetup:
    """
    Gestionnaire de configuration du monitoring.
    """
    def __init__(self,
                 health_checker: HealthChecker,
                 security_manager: SecurityManager,
                 optimization_manager: OptimizationManager,
                 config_file: str = 'config/monitoring_config.json'):
        """
        Initialise le gestionnaire de monitoring.
        
        Args:
            health_checker (HealthChecker): Vérificateur de santé
            security_manager (SecurityManager): Gestionnaire de sécurité
            optimization_manager (OptimizationManager): Gestionnaire d'optimisation
            config_file (str): Chemin du fichier de configuration
        """
        self.health_checker = health_checker
        self.security_manager = security_manager
        self.optimization_manager = optimization_manager
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """
        Charge la configuration du monitoring.
        
        Args:
            config_file (str): Chemin du fichier de configuration
            
        Returns:
            Dict[str, Any]: Configuration chargée
        """
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            return {
                'grafana': {
                    'url': 'http://localhost:3000',
                    'api_key': os.getenv('GRAFANA_API_KEY'),
                    'dashboard': {
                        'title': 'Trading Bot Dashboard',
                        'panels': [
                            {
                                'title': 'Performance',
                                'type': 'graph',
                                'datasource': 'InfluxDB',
                                'targets': [
                                    {
                                        'query': 'SELECT mean("value") FROM "trading_metrics" WHERE $timeFilter GROUP BY time($interval)',
                                        'legendFormat': '{{metric}}'
                                    }
                                ]
                            },
                            {
                                'title': 'Risques',
                                'type': 'gauge',
                                'datasource': 'InfluxDB',
                                'targets': [
                                    {
                                        'query': 'SELECT last("value") FROM "risk_metrics" WHERE $timeFilter',
                                        'legendFormat': '{{metric}}'
                                    }
                                ]
                            }
                        ]
                    }
                },
                'security': {
                    'scan_interval': 3600,  # 1 heure
                    'vulnerability_threshold': 0.7,
                    'auto_fix': True
                },
                'optimization': {
                    'data_window': '7d',
                    'iterations': 1000,
                    'risk_level': 3
                }
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
            return {}
            
    def setup_grafana_dashboard(self) -> bool:
        """
        Configure le dashboard Grafana.
        
        Returns:
            bool: True si la configuration est réussie
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.config["grafana"]["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            # Création du dashboard
            dashboard_config = {
                'dashboard': {
                    'id': None,
                    'title': self.config['grafana']['dashboard']['title'],
                    'panels': self.config['grafana']['dashboard']['panels'],
                    'refresh': '5s',
                    'time': {
                        'from': 'now-7d',
                        'to': 'now'
                    }
                },
                'overwrite': True
            }
            
            response = requests.post(
                f"{self.config['grafana']['url']}/api/dashboards/db",
                headers=headers,
                json=dashboard_config
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur lors de la création du dashboard: {response.text}")
                return False
                
            logger.info("Dashboard Grafana créé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de Grafana: {str(e)}")
            return False
            
    def run_security_audit(self) -> Dict[str, Any]:
        """
        Exécute un audit de sécurité.
        
        Returns:
            Dict[str, Any]: Résultats de l'audit
        """
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'vulnerabilities': [],
                'fixes_applied': [],
                'score': 0.0
            }
            
            # Vérification des dépendances
            dependencies = self.security_manager.check_dependencies()
            results['vulnerabilities'].extend(dependencies)
            
            # Vérification des configurations
            configs = self.security_manager.check_configurations()
            results['vulnerabilities'].extend(configs)
            
            # Vérification des permissions
            permissions = self.security_manager.check_permissions()
            results['vulnerabilities'].extend(permissions)
            
            # Application des corrections si activé
            if self.config['security']['auto_fix']:
                for vuln in results['vulnerabilities']:
                    if vuln.get('fixable', False):
                        fix = self.security_manager.apply_fix(vuln)
                        if fix:
                            results['fixes_applied'].append(fix)
                            
            # Calcul du score
            total_vulns = len(results['vulnerabilities'])
            fixed_vulns = len(results['fixes_applied'])
            results['score'] = 1.0 - (total_vulns - fixed_vulns) / max(total_vulns, 1)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'audit de sécurité: {str(e)}")
            return {}
            
    def optimize_trading_strategy(self) -> Dict[str, Any]:
        """
        Optimise la stratégie de trading.
        
        Returns:
            Dict[str, Any]: Résultats de l'optimisation
        """
        try:
            # Chargement des données
            data = pd.read_csv('data/latest.csv')
            
            # Préparation des données
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data.set_index('timestamp', inplace=True)
            
            # Optimisation des paramètres
            results = self.optimization_manager.optimize(
                data=data,
                iterations=self.config['optimization']['iterations'],
                risk_level=self.config['optimization']['risk_level']
            )
            
            # Mise à jour des paramètres
            if results['success']:
                self.optimization_manager.update_parameters(results['parameters'])
                
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation: {str(e)}")
            return {}
            
    def setup_monitoring(self) -> bool:
        """
        Configure l'ensemble du système de monitoring.
        
        Returns:
            bool: True si la configuration est réussie
        """
        try:
            # Configuration de Grafana
            if not self.setup_grafana_dashboard():
                return False
                
            # Audit de sécurité
            security_results = self.run_security_audit()
            if security_results['score'] < self.config['security']['vulnerability_threshold']:
                logger.warning(f"Score de sécurité faible: {security_results['score']}")
                
            # Optimisation de la stratégie
            optimization_results = self.optimize_trading_strategy()
            if not optimization_results.get('success', False):
                logger.warning("Optimisation non optimale")
                
            # Configuration des alertes
            self.setup_alerts()
            
            logger.info("Configuration du monitoring terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du monitoring: {str(e)}")
            return False
            
    def setup_alerts(self):
        """
        Configure les alertes de monitoring.
        """
        try:
            # Alertes de santé
            self.health_checker.setup_alerts(
                cpu_threshold=self.config['health']['thresholds']['cpu_percent'],
                memory_threshold=self.config['health']['thresholds']['memory_percent'],
                disk_threshold=self.config['health']['thresholds']['disk_percent']
            )
            
            # Alertes de performance
            self.optimization_manager.setup_alerts(
                min_win_rate=0.5,
                max_drawdown=0.1,
                min_sharpe_ratio=1.0
            )
            
            # Alertes de sécurité
            self.security_manager.setup_alerts(
                vulnerability_threshold=self.config['security']['vulnerability_threshold'],
                failed_login_threshold=3
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration des alertes: {str(e)}")
            
    def generate_report(self) -> Dict[str, Any]:
        """
        Génère un rapport de monitoring.
        
        Returns:
            Dict[str, Any]: Rapport complet
        """
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'health_status': self.health_checker.get_health_status(),
                'security_audit': self.run_security_audit(),
                'optimization_results': self.optimize_trading_strategy(),
                'alerts': {
                    'active': self.health_checker.get_active_alerts(),
                    'resolved': self.health_checker.get_resolved_alerts()
                }
            }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
            return {} 