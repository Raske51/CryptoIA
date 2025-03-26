import redis
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Gestionnaire de cache Redis pour les données de trading.
    """
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        cache_ttl: int = 3600  # 1 heure par défaut
    ):
        """
        Initialise le gestionnaire de cache.
        
        Args:
            host (str): Adresse du serveur Redis
            port (int): Port du serveur Redis
            db (int): Base de données Redis à utiliser
            cache_ttl (int): Durée de vie du cache en secondes
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
            self.cache_ttl = cache_ttl
            logger.info(f"Connexion Redis établie sur {host}:{port}")
        except Exception as e:
            logger.error(f"Erreur de connexion Redis: {str(e)}")
            raise

    def get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Récupère les données mises en cache pour un symbole.
        
        Args:
            symbol (str): Symbole de trading (ex: 'BTCUSDT')
            
        Returns:
            Optional[pd.DataFrame]: DataFrame des données ou None si non trouvé
        """
        try:
            cached_data = self.redis_client.get(f"market_data:{symbol}")
            if cached_data:
                df = pd.read_json(cached_data)
                df.index = pd.to_datetime(df.index)
                logger.info(f"Données récupérées du cache pour {symbol}")
                return df
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache: {str(e)}")
            return None

    def set_cached_data(
        self,
        symbol: str,
        data: pd.DataFrame,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Met en cache les données pour un symbole.
        
        Args:
            symbol (str): Symbole de trading
            data (pd.DataFrame): Données à mettre en cache
            ttl (Optional[int]): Durée de vie personnalisée en secondes
            
        Returns:
            bool: True si la mise en cache a réussi
        """
        try:
            # Conversion du DataFrame en JSON
            json_data = data.to_json()
            
            # Mise en cache avec TTL
            ttl = ttl or self.cache_ttl
            self.redis_client.setex(
                f"market_data:{symbol}",
                ttl,
                json_data
            )
            
            logger.info(f"Données mises en cache pour {symbol} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache: {str(e)}")
            return False

    def delete_cached_data(self, symbol: str) -> bool:
        """
        Supprime les données mises en cache pour un symbole.
        
        Args:
            symbol (str): Symbole de trading
            
        Returns:
            bool: True si la suppression a réussi
        """
        try:
            self.redis_client.delete(f"market_data:{symbol}")
            logger.info(f"Données supprimées du cache pour {symbol}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du cache: {str(e)}")
            return False

    def clear_cache(self) -> bool:
        """
        Vide tout le cache.
        
        Returns:
            bool: True si le nettoyage a réussi
        """
        try:
            self.redis_client.flushdb()
            logger.info("Cache vidé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {str(e)}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache.
        
        Returns:
            Dict[str, Any]: Statistiques du cache
        """
        try:
            info = self.redis_client.info()
            return {
                "used_memory": info["used_memory_human"],
                "connected_clients": info["connected_clients"],
                "total_keys": self.redis_client.dbsize(),
                "uptime": info["uptime_in_seconds"]
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {str(e)}")
            return {} 