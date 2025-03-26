import os
import json
import logging
import requests
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .alert_manager import AlertManager
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class HealthChecker:
    """
    Gestionnaire de vérification de santé du système.
    """
    def __init__(self,
                 alert_manager: AlertManager,
                 cache_manager: CacheManager,
                 config_file: str = 'config/health_config.json'):
        """
        Initialise le vérificateur de santé.
        
        Args:
            alert_manager (AlertManager): Gestionnaire d'alertes
            cache_manager (CacheManager): Gestionnaire de cache
            config_file (str): Chemin du fichier de configuration
        """
        self.alert_manager = alert_manager
        self.cache_manager = cache_manager
        self.config = self._load_config(config_file)
        self.last_check = None
        self.health_status = {}
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """
        Charge la configuration de santé.
        
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
                'endpoints': {
                    'api': 'https://crypto-ia.vercel.app/healthcheck',
                    'database': 'http://localhost:8086/health',
                    'redis': 'http://localhost:6379/health'
                },
                'thresholds': {
                    'cpu_percent': 80,
                    'memory_percent': 80,
                    'disk_percent': 80,
                    'response_time': 2.0
                },
                'check_interval': 300,  # 5 minutes
                'alert_cooldown': 1800,  # 30 minutes
                'retry_attempts': 3,
                'retry_delay': 1
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
            return {}
            
    def check_system_resources(self) -> Dict[str, Any]:
        """
        Vérifie les ressources système.
        
        Returns:
            Dict[str, Any]: État des ressources
        """
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des ressources: {str(e)}")
            return {}
            
    def check_endpoint(self, url: str) -> Dict[str, Any]:
        """
        Vérifie un endpoint.
        
        Args:
            url (str): URL à vérifier
            
        Returns:
            Dict[str, Any]: État de l'endpoint
        """
        try:
            start_time = time.time()
            response = requests.get(url, timeout=self.config['thresholds']['response_time'])
            response_time = time.time() - start_time
            
            return {
                'status_code': response.status_code,
                'response_time': response_time,
                'is_healthy': response.status_code == 200,
                'timestamp': datetime.now().isoformat()
            }
        except requests.Timeout:
            return {
                'status_code': 408,
                'response_time': self.config['thresholds']['response_time'],
                'is_healthy': False,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'endpoint {url}: {str(e)}")
            return {
                'status_code': 500,
                'response_time': 0,
                'is_healthy': False,
                'timestamp': datetime.now().isoformat()
            }
            
    def check_database(self) -> Dict[str, Any]:
        """
        Vérifie l'état de la base de données.
        
        Returns:
            Dict[str, Any]: État de la base de données
        """
        try:
            # Vérification de la connexion
            db_status = self.check_endpoint(self.config['endpoints']['database'])
            
            # Vérification des métriques
            metrics = self.cache_manager.get('db_metrics')
            if metrics:
                return {
                    **db_status,
                    'metrics': metrics
                }
            return db_status
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la base de données: {str(e)}")
            return {}
            
    def check_redis(self) -> Dict[str, Any]:
        """
        Vérifie l'état de Redis.
        
        Returns:
            Dict[str, Any]: État de Redis
        """
        try:
            # Vérification de la connexion
            redis_status = self.check_endpoint(self.config['endpoints']['redis'])
            
            # Vérification des métriques
            metrics = self.cache_manager.get('redis_metrics')
            if metrics:
                return {
                    **redis_status,
                    'metrics': metrics
                }
            return redis_status
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de Redis: {str(e)}")
            return {}
            
    def check_trading_bot(self) -> Dict[str, Any]:
        """
        Vérifie l'état du bot de trading.
        
        Returns:
            Dict[str, Any]: État du bot
        """
        try:
            # Vérification de l'API
            api_status = self.check_endpoint(self.config['endpoints']['api'])
            
            # Vérification des métriques
            metrics = self.cache_manager.get('trading_metrics')
            if metrics:
                return {
                    **api_status,
                    'metrics': metrics
                }
            return api_status
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du bot: {str(e)}")
            return {}
            
    def should_alert(self, component: str) -> bool:
        """
        Vérifie si une alerte doit être envoyée.
        
        Args:
            component (str): Composant à vérifier
            
        Returns:
            bool: True si une alerte doit être envoyée
        """
        try:
            last_alert = self.cache_manager.get(f'last_alert_{component}')
            if not last_alert:
                return True
                
            last_alert_time = datetime.fromisoformat(last_alert)
            cooldown = timedelta(seconds=self.config['alert_cooldown'])
            
            return datetime.now() - last_alert_time > cooldown
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des alertes: {str(e)}")
            return True
            
    async def run_health_check(self) -> bool:
        """
        Exécute une vérification de santé complète.
        
        Returns:
            bool: True si tout est en bonne santé
        """
        try:
            # Vérification des ressources système
            system_status = self.check_system_resources()
            self.health_status['system'] = system_status
            
            # Vérification des composants
            self.health_status['database'] = self.check_database()
            self.health_status['redis'] = self.check_redis()
            self.health_status['trading_bot'] = self.check_trading_bot()
            
            # Analyse des résultats
            is_healthy = True
            alerts = []
            
            # Vérification des ressources système
            if system_status['cpu_percent'] > self.config['thresholds']['cpu_percent']:
                alerts.append(f"CPU usage élevé: {system_status['cpu_percent']}%")
                is_healthy = False
                
            if system_status['memory_percent'] > self.config['thresholds']['memory_percent']:
                alerts.append(f"Utilisation mémoire élevée: {system_status['memory_percent']}%")
                is_healthy = False
                
            if system_status['disk_percent'] > self.config['thresholds']['disk_percent']:
                alerts.append(f"Espace disque faible: {system_status['disk_percent']}%")
                is_healthy = False
                
            # Vérification des composants
            for component, status in self.health_status.items():
                if component != 'system':
                    if not status.get('is_healthy', False):
                        alerts.append(f"{component} non fonctionnel")
                        is_healthy = False
                        
                    if status.get('response_time', 0) > self.config['thresholds']['response_time']:
                        alerts.append(f"{component} lent: {status['response_time']:.2f}s")
                        
            # Envoi des alertes si nécessaire
            if alerts and self.should_alert('system'):
                await self.alert_manager.send_telegram_alert(
                    os.getenv('TELEGRAM_ADMIN_ID'),
                    "⚠️ Alertes de santé:\n" + "\n".join(alerts)
                )
                self.cache_manager.set('last_alert_system', datetime.now().isoformat())
                
            # Mise à jour du cache
            self.cache_manager.set('health_status', self.health_status)
            self.last_check = datetime.now()
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé: {str(e)}")
            return False
            
    def get_health_status(self) -> Dict[str, Any]:
        """
        Récupère l'état de santé actuel.
        
        Returns:
            Dict[str, Any]: État de santé
        """
        return self.health_status
        
    def get_last_check(self) -> Optional[datetime]:
        """
        Récupère la date de la dernière vérification.
        
        Returns:
            Optional[datetime]: Date de la dernière vérification
        """
        return self.last_check 