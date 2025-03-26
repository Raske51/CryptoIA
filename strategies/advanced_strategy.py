import talib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def advanced_strategy(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Stratégie avancée utilisant EMA, RSI et MACD.
    
    Args:
        df (pd.DataFrame): DataFrame contenant les données OHLCV
        
    Returns:
        tuple[pd.Series, pd.Series]: Signaux d'achat et de vente
    """
    try:
        # Calcul des indicateurs techniques
        df['EMA_20'] = talib.EMA(df['close'], timeperiod=20)
        df['EMA_50'] = talib.EMA(df['close'], timeperiod=50)
        df['RSI'] = talib.RSI(df['close'], timeperiod=14)
        df['MACD'], df['MACD_Signal'], _ = talib.MACD(df['close'])
        
        # Conditions d'achat
        buy_signal = (
            (df['EMA_20'] > df['EMA_50']) &  # Croisement haussier des EMA
            (df['RSI'] < 30) &                 # Survente
            (df['MACD'] > df['MACD_Signal'])  # Croisement haussier du MACD
        )
        
        # Conditions de vente
        sell_signal = (
            (df['EMA_20'] < df['EMA_50']) &  # Croisement baissier des EMA
            (df['RSI'] > 70) &                # Surachat
            (df['MACD'] < df['MACD_Signal']) # Croisement baissier du MACD
        )
        
        logger.info("Stratégie avancée calculée avec succès")
        return buy_signal, sell_signal
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul de la stratégie avancée: {str(e)}")
        raise 