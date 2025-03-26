from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
from strategies.advanced_strategy import advanced_strategy
import logging

logger = logging.getLogger(__name__)

class AdvancedTradingStrategy(Strategy):
    """
    Stratégie de trading avancée utilisant EMA, RSI et MACD.
    """
    def init(self):
        # Initialisation des indicateurs
        self.df = self.data.df
        self.buy_signal, self.sell_signal = advanced_strategy(self.df)
        
        # Paramètres de la stratégie
        self.stop_loss = 0.02  # 2% de stop loss
        self.take_profit = 0.04  # 4% de take profit
        
        logger.info("Initialisation de la stratégie de backtesting")

    def next(self):
        # Vérification des conditions d'achat
        if self.buy_signal.iloc[-1] and not self.position:
            # Calcul de la taille de la position
            price = self.data.Close[-1]
            size = self.equity * 0.95 / price  # Utilise 95% du capital disponible
            
            # Entrée dans la position
            self.buy(size=size)
            logger.info(f"Signal d'achat détecté à {price}")
            
            # Définition du stop loss et take profit
            self.position.stop_loss = price * (1 - self.stop_loss)
            self.position.take_profit = price * (1 + self.take_profit)
        
        # Vérification des conditions de vente
        elif self.sell_signal.iloc[-1] and self.position:
            self.position.close()
            logger.info(f"Signal de vente détecté à {self.data.Close[-1]}")
        
        # Vérification du stop loss et take profit
        elif self.position:
            current_price = self.data.Close[-1]
            if current_price <= self.position.stop_loss:
                self.position.close()
                logger.info(f"Stop loss atteint à {current_price}")
            elif current_price >= self.position.take_profit:
                self.position.close()
                logger.info(f"Take profit atteint à {current_price}")

def run_backtest(df: pd.DataFrame, initial_cash: float = 10000, commission: float = 0.002) -> dict:
    """
    Exécute le backtesting de la stratégie.
    
    Args:
        df (pd.DataFrame): DataFrame contenant les données OHLCV
        initial_cash (float): Capital initial
        commission (float): Commission par trade (en %)
        
    Returns:
        dict: Résultats du backtesting
    """
    try:
        # Préparation des données
        df = df.copy()
        df.columns = [col.capitalize() for col in df.columns]
        
        # Création et exécution du backtest
        bt = Backtest(
            df,
            AdvancedTradingStrategy,
            cash=initial_cash,
            commission=commission,
            exclusive_orders=True
        )
        
        # Exécution du backtest
        results = bt.run()
        
        # Affichage des résultats
        logger.info(f"Résultats du backtesting:\n{results}")
        
        # Plot des résultats
        bt.plot()
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur lors du backtesting: {str(e)}")
        raise 