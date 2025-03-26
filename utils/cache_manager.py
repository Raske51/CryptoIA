import os
import json
import logging
from typing import Any, Optional, Union, List, Dict
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Gestionnaire de cache avec Redis pour le bot de trading.
    """
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 decode_responses: bool = True):
        """
        Initialise le gestionnaire de cache.
        
        Args:
            host (str): Hôte Redis
            port (int): Port Redis
            db (int): Base de données Redis
            password (str): Mot de passe Redis
            decode_responses (bool): Si True, décode automatiquement les réponses
        """
        try:
            self.redis = redis.Redis(
                host=host or os.getenv('REDIS_HOST', 'localhost'),
                port=port or int(os.getenv('REDIS_PORT', '6379')),
                db=db or int(os.getenv('REDIS_DB', '0')),
                password=password or os.getenv('REDIS_PASSWORD'),
                decode_responses=decode_responses
            )
            
            # Test de connexion
            self.redis.ping()
            logger.info("Connexion à Redis établie avec succès")
            
        except RedisError as e:
            logger.error(f"Erreur de connexion à Redis: {str(e)}")
            raise
            
    def set(self, 
            key: str, 
            value: Any, 
            ttl: Optional[int] = None,
            prefix: str = "trading_bot:") -> bool:
        """
        Stocke une valeur dans le cache.
        
        Args:
            key (str): Clé du cache
            value (Any): Valeur à stocker
            ttl (int): Durée de vie en secondes
            prefix (str): Préfixe pour les clés
            
        Returns:
            bool: True si l'opération est réussie
        """
        try:
            full_key = f"{prefix}{key}"
            serialized_value = json.dumps(value)
            
            if ttl:
                self.redis.setex(full_key, ttl, serialized_value)
            else:
                self.redis.set(full_key, serialized_value)
                
            logger.debug(f"Données mises en cache: {full_key}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache: {str(e)}")
            return False
            
    def get(self, 
            key: str, 
            prefix: str = "trading_bot:",
            default: Any = None) -> Any:
        """
        Récupère une valeur du cache.
        
        Args:
            key (str): Clé du cache
            prefix (str): Préfixe pour les clés
            default (Any): Valeur par défaut si la clé n'existe pas
            
        Returns:
            Any: Valeur du cache ou valeur par défaut
        """
        try:
            full_key = f"{prefix}{key}"
            cached_value = self.redis.get(full_key)
            
            if cached_value:
                return json.loads(cached_value)
            return default
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache: {str(e)}")
            return default
            
    def delete(self, key: str, prefix: str = "trading_bot:") -> bool:
        """
        Supprime une valeur du cache.
        
        Args:
            key (str): Clé du cache
            prefix (str): Préfixe pour les clés
            
        Returns:
            bool: True si l'opération est réussie
        """
        try:
            full_key = f"{prefix}{key}"
            self.redis.delete(full_key)
            logger.debug(f"Données supprimées du cache: {full_key}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du cache: {str(e)}")
            return False
            
    def exists(self, key: str, prefix: str = "trading_bot:") -> bool:
        """
        Vérifie si une clé existe dans le cache.
        
        Args:
            key (str): Clé du cache
            prefix (str): Préfixe pour les clés
            
        Returns:
            bool: True si la clé existe
        """
        try:
            full_key = f"{prefix}{key}"
            return bool(self.redis.exists(full_key))
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du cache: {str(e)}")
            return False
            
    def set_market_data(self, 
                       symbol: str, 
                       data: Dict[str, Any], 
                       ttl: int = 300) -> bool:
        """
        Stocke les données de marché.
        
        Args:
            symbol (str): Symbole de la paire
            data (Dict[str, Any]): Données de marché
            ttl (int): Durée de vie en secondes
            
        Returns:
            bool: True si l'opération est réussie
        """
        try:
            key = f"market_data:{symbol}"
            return self.set(key, data, ttl)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache des données de marché: {str(e)}")
            return False
            
    def get_market_data(self, 
                       symbol: str, 
                       default: Any = None) -> Any:
        """
        Récupère les données de marché.
        
        Args:
            symbol (str): Symbole de la paire
            default (Any): Valeur par défaut
            
        Returns:
            Any: Données de marché ou valeur par défaut
        """
        try:
            key = f"market_data:{symbol}"
            return self.get(key, default=default)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de marché: {str(e)}")
            return default
            
    def set_trade_data(self, 
                      trade_id: str, 
                      data: Dict[str, Any], 
                      ttl: int = 3600) -> bool:
        """
        Stocke les données d'un trade.
        
        Args:
            trade_id (str): ID du trade
            data (Dict[str, Any]): Données du trade
            ttl (int): Durée de vie en secondes
            
        Returns:
            bool: True si l'opération est réussie
        """
        try:
            key = f"trade:{trade_id}"
            return self.set(key, data, ttl)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache des données de trade: {str(e)}")
            return False
            
    def get_trade_data(self, 
                      trade_id: str, 
                      default: Any = None) -> Any:
        """
        Récupère les données d'un trade.
        
        Args:
            trade_id (str): ID du trade
            default (Any): Valeur par défaut
            
        Returns:
            Any: Données du trade ou valeur par défaut
        """
        try:
            key = f"trade:{trade_id}"
            return self.get(key, default=default)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de trade: {str(e)}")
            return default
            
    def set_indicators(self, 
                      symbol: str, 
                      timeframe: str, 
                      data: Dict[str, Any], 
                      ttl: int = 300) -> bool:
        """
        Stocke les indicateurs techniques.
        
        Args:
            symbol (str): Symbole de la paire
            timeframe (str): Intervalle de temps
            data (Dict[str, Any]): Données des indicateurs
            ttl (int): Durée de vie en secondes
            
        Returns:
            bool: True si l'opération est réussie
        """
        try:
            key = f"indicators:{symbol}:{timeframe}"
            return self.set(key, data, ttl)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache des indicateurs: {str(e)}")
            return False
            
    def get_indicators(self, 
                      symbol: str, 
                      timeframe: str, 
                      default: Any = None) -> Any:
        """
        Récupère les indicateurs techniques.
        
        Args:
            symbol (str): Symbole de la paire
            timeframe (str): Intervalle de temps
            default (Any): Valeur par défaut
            
        Returns:
            Any: Données des indicateurs ou valeur par défaut
        """
        try:
            key = f"indicators:{symbol}:{timeframe}"
            return self.get(key, default=default)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des indicateurs: {str(e)}")
            return default
            
    def clear_pattern(self, pattern: str) -> bool:
        """
        Supprime toutes les clés correspondant à un pattern.
        
        Args:
            pattern (str): Pattern de recherche
            
        Returns:
            bool: True si l'opération est réussie
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du pattern: {str(e)}")
            return False
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache.
        
        Returns:
            Dict[str, Any]: Statistiques du cache
        """
        try:
            info = self.redis.info()
            return {
                'used_memory': info['used_memory_human'],
                'connected_clients': info['connected_clients'],
                'total_connections_received': info['total_connections_received'],
                'total_commands_processed': info['total_commands_processed'],
                'keyspace_hits': info['keyspace_hits'],
                'keyspace_misses': info['keyspace_misses']
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {} 