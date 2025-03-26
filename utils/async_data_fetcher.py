import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class AsyncDataFetcher:
    """
    Gestionnaire de récupération de données asynchrone pour le bot de trading.
    """
    def __init__(self,
                 cache_manager: Optional[CacheManager] = None,
                 max_concurrent_requests: int = 10,
                 request_timeout: int = 30,
                 retry_attempts: int = 3,
                 retry_delay: float = 1.0,
                 rate_limit: int = 1200):  # 1200 requêtes par minute pour Binance
        """
        Initialise le gestionnaire de récupération de données.
        
        Args:
            cache_manager (CacheManager): Gestionnaire de cache
            max_concurrent_requests (int): Nombre maximum de requêtes simultanées
            request_timeout (int): Timeout des requêtes en secondes
            retry_attempts (int): Nombre de tentatives de réessai
            retry_delay (float): Délai entre les tentatives en secondes
            rate_limit (int): Limite de requêtes par minute
        """
        self.cache_manager = cache_manager or CacheManager()
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit
        
        # Rate limiting
        self.request_timestamps = []
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
    async def _make_request(self, 
                          session: aiohttp.ClientSession,
                          url: str,
                          method: str = 'GET',
                          params: Optional[Dict] = None,
                          headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête HTTP avec gestion des erreurs et retry.
        
        Args:
            session (aiohttp.ClientSession): Session HTTP
            url (str): URL de la requête
            method (str): Méthode HTTP
            params (Dict): Paramètres de la requête
            headers (Dict): En-têtes de la requête
            
        Returns:
            Dict[str, Any]: Réponse de la requête
            
        Raises:
            Exception: Si toutes les tentatives échouent
        """
        for attempt in range(self.retry_attempts):
            try:
                # Rate limiting
                await self._check_rate_limit()
                
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    timeout=self.request_timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Too Many Requests
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                        logger.warning(f"Rate limit atteint, attente de {retry_after}s")
                        await asyncio.sleep(retry_after)
                    else:
                        logger.error(f"Erreur HTTP {response.status}: {await response.text()}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout de la requête (tentative {attempt + 1}/{self.retry_attempts})")
            except Exception as e:
                logger.error(f"Erreur lors de la requête: {str(e)}")
                
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                
        raise Exception(f"Échec de la requête après {self.retry_attempts} tentatives")
        
    async def _check_rate_limit(self):
        """
        Vérifie et gère le rate limiting.
        """
        now = datetime.now()
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                 if now - ts < timedelta(minutes=1)]
        
        if len(self.request_timestamps) >= self.rate_limit:
            wait_time = (self.request_timestamps[0] + timedelta(minutes=1) - now).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit atteint, attente de {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
        self.request_timestamps.append(now)
        
    async def fetch_market_data(self, 
                              symbol: str,
                              use_cache: bool = True,
                              cache_ttl: int = 300) -> Dict[str, Any]:
        """
        Récupère les données de marché pour un symbole.
        
        Args:
            symbol (str): Symbole de la paire
            use_cache (bool): Utiliser le cache si disponible
            cache_ttl (int): Durée de vie du cache en secondes
            
        Returns:
            Dict[str, Any]: Données de marché
        """
        try:
            # Vérification du cache
            if use_cache:
                cached_data = self.cache_manager.get_market_data(symbol)
                if cached_data:
                    logger.debug(f"Données de marché récupérées du cache pour {symbol}")
                    return cached_data
                    
            async with aiohttp.ClientSession() as session:
                async with self.semaphore:
                    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
                    data = await self._make_request(session, url)
                    
                    # Mise en cache
                    if use_cache:
                        self.cache_manager.set_market_data(symbol, data, cache_ttl)
                        
                    return data
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de marché pour {symbol}: {str(e)}")
            raise
            
    async def fetch_multiple_market_data(self,
                                       symbols: List[str],
                                       use_cache: bool = True,
                                       cache_ttl: int = 300) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les données de marché pour plusieurs symboles.
        
        Args:
            symbols (List[str]): Liste des symboles
            use_cache (bool): Utiliser le cache si disponible
            cache_ttl (int): Durée de vie du cache en secondes
            
        Returns:
            Dict[str, Dict[str, Any]]: Données de marché par symbole
        """
        try:
            tasks = []
            for symbol in symbols:
                task = self.fetch_market_data(symbol, use_cache, cache_ttl)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traitement des résultats
            market_data = {}
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.error(f"Erreur pour {symbol}: {str(result)}")
                    market_data[symbol] = None
                else:
                    market_data[symbol] = result
                    
            return market_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de marché: {str(e)}")
            raise
            
    async def fetch_klines(self,
                          symbol: str,
                          interval: str,
                          limit: int = 100,
                          start_time: Optional[int] = None,
                          end_time: Optional[int] = None,
                          use_cache: bool = True,
                          cache_ttl: int = 300) -> List[List[Any]]:
        """
        Récupère les données OHLCV (Klines).
        
        Args:
            symbol (str): Symbole de la paire
            interval (str): Intervalle de temps (1m, 5m, 1h, etc.)
            limit (int): Nombre de klines à récupérer
            start_time (int): Timestamp de début
            end_time (int): Timestamp de fin
            use_cache (bool): Utiliser le cache si disponible
            cache_ttl (int): Durée de vie du cache en secondes
            
        Returns:
            List[List[Any]]: Données OHLCV
        """
        try:
            # Vérification du cache
            cache_key = f"klines:{symbol}:{interval}:{limit}:{start_time}:{end_time}"
            if use_cache:
                cached_data = self.cache_manager.get(cache_key)
                if cached_data:
                    logger.debug(f"Données OHLCV récupérées du cache pour {symbol}")
                    return cached_data
                    
            async with aiohttp.ClientSession() as session:
                async with self.semaphore:
                    url = "https://api.binance.com/api/v3/klines"
                    params = {
                        'symbol': symbol,
                        'interval': interval,
                        'limit': limit
                    }
                    if start_time:
                        params['startTime'] = start_time
                    if end_time:
                        params['endTime'] = end_time
                        
                    data = await self._make_request(session, url, params=params)
                    
                    # Mise en cache
                    if use_cache:
                        self.cache_manager.set(cache_key, data, cache_ttl)
                        
                    return data
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des klines pour {symbol}: {str(e)}")
            raise
            
    async def fetch_order_book(self,
                             symbol: str,
                             limit: int = 100,
                             use_cache: bool = True,
                             cache_ttl: int = 5) -> Dict[str, Any]:
        """
        Récupère le carnet d'ordres.
        
        Args:
            symbol (str): Symbole de la paire
            limit (int): Nombre d'ordres à récupérer
            use_cache (bool): Utiliser le cache si disponible
            cache_ttl (int): Durée de vie du cache en secondes
            
        Returns:
            Dict[str, Any]: Carnet d'ordres
        """
        try:
            # Vérification du cache
            cache_key = f"orderbook:{symbol}:{limit}"
            if use_cache:
                cached_data = self.cache_manager.get(cache_key)
                if cached_data:
                    logger.debug(f"Carnet d'ordres récupéré du cache pour {symbol}")
                    return cached_data
                    
            async with aiohttp.ClientSession() as session:
                async with self.semaphore:
                    url = "https://api.binance.com/api/v3/depth"
                    params = {
                        'symbol': symbol,
                        'limit': limit
                    }
                    
                    data = await self._make_request(session, url, params=params)
                    
                    # Mise en cache
                    if use_cache:
                        self.cache_manager.set(cache_key, data, cache_ttl)
                        
                    return data
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du carnet d'ordres pour {symbol}: {str(e)}")
            raise

async def main():
    """
    Fonction principale pour tester le gestionnaire de requêtes.
    """
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    async with AsyncDataFetcher() as fetcher:
        data = await fetcher.fetch_multiple_market_data(symbols)
        for symbol, df in data.items():
            print(f"\nDonnées pour {symbol}:")
            print(df) 