import asyncio
import aiohttp
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class AsyncDataFetcher:
    """
    Gestionnaire de requêtes asynchrones pour les données de marché.
    """
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialise le gestionnaire de requêtes.
        
        Args:
            cache_manager (Optional[CacheManager]): Gestionnaire de cache
            timeout (int): Timeout des requêtes en secondes
            max_retries (int): Nombre maximum de tentatives
        """
        self.cache_manager = cache_manager
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None

    async def __aenter__(self):
        """Initialise la session aiohttp."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session aiohttp."""
        if self.session:
            await self.session.close()

    async def fetch_data(
        self,
        url: str,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère les données d'une URL avec gestion des erreurs.
        
        Args:
            url (str): URL à appeler
            retry_count (int): Nombre de tentatives actuelles
            
        Returns:
            Optional[Dict[str, Any]]: Données récupérées ou None
        """
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429 and retry_count < self.max_retries:
                    # Rate limit atteint, on attend et on réessaie
                    await asyncio.sleep(2 ** retry_count)
                    return await self.fetch_data(url, retry_count + 1)
                else:
                    logger.error(f"Erreur HTTP {response.status} pour {url}")
                    return None
        except Exception as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.fetch_data(url, retry_count + 1)
            logger.error(f"Erreur lors de la requête {url}: {str(e)}")
            return None

    async def fetch_market_data(
        self,
        symbol: str,
        interval: str = '1h',
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Récupère les données de marché avec gestion du cache.
        
        Args:
            symbol (str): Symbole de trading
            interval (str): Intervalle de temps
            limit (int): Nombre de données à récupérer
            
        Returns:
            Optional[pd.DataFrame]: DataFrame des données ou None
        """
        # Vérification du cache
        if self.cache_manager:
            cached_data = self.cache_manager.get_cached_data(symbol)
            if cached_data is not None:
                return cached_data

        # Construction de l'URL
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        
        # Récupération des données
        data = await self.fetch_data(url)
        if data is None:
            return None

        # Conversion en DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Conversion des types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Mise en cache
        if self.cache_manager:
            self.cache_manager.set_cached_data(symbol, df)
        
        return df

    async def fetch_multiple_symbols(
        self,
        symbols: List[str],
        interval: str = '1h',
        limit: int = 100
    ) -> Dict[str, pd.DataFrame]:
        """
        Récupère les données pour plusieurs symboles en parallèle.
        
        Args:
            symbols (List[str]): Liste des symboles
            interval (str): Intervalle de temps
            limit (int): Nombre de données à récupérer
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionnaire des données par symbole
        """
        tasks = [
            self.fetch_market_data(symbol, interval, limit)
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks)
        return {symbol: df for symbol, df in zip(symbols, results) if df is not None}

async def main():
    """
    Fonction principale pour tester le gestionnaire de requêtes.
    """
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    async with AsyncDataFetcher() as fetcher:
        data = await fetcher.fetch_multiple_symbols(symbols)
        for symbol, df in data.items():
            print(f"\nDonnées pour {symbol}:")
            print(df.head()) 