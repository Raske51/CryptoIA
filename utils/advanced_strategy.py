import logging
import numpy as np
import pandas as pd
import talib
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class AdvancedStrategy:
    """
    Stratégie de trading avancée utilisant plusieurs indicateurs techniques.
    """
    def __init__(self, 
                 ema_short: int = 20,
                 ema_long: int = 50,
                 rsi_period: int = 14,
                 rsi_overbought: float = 70,
                 rsi_oversold: float = 30,
                 atr_period: int = 14,
                 atr_multiplier: float = 1.5,
                 macd_fast: int = 12,
                 macd_slow: int = 26,
                 macd_signal: int = 9,
                 bb_period: int = 20,
                 bb_std: float = 2.0):
        """
        Initialise la stratégie avec les paramètres spécifiés.
        
        Args:
            ema_short (int): Période de l'EMA court
            ema_long (int): Période de l'EMA long
            rsi_period (int): Période du RSI
            rsi_overbought (float): Seuil de surachat RSI
            rsi_oversold (float): Seuil de survente RSI
            atr_period (int): Période de l'ATR
            atr_multiplier (float): Multiplicateur ATR pour le stop-loss
            macd_fast (int): Période rapide du MACD
            macd_slow (int): Période lente du MACD
            macd_signal (int): Période du signal MACD
            bb_period (int): Période des bandes de Bollinger
            bb_std (float): Écart-type des bandes de Bollinger
        """
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule tous les indicateurs techniques.
        
        Args:
            df (pd.DataFrame): DataFrame avec les données OHLCV
            
        Returns:
            pd.DataFrame: DataFrame avec les indicateurs ajoutés
        """
        try:
            # Indicateurs de base
            df['EMA_20'] = talib.EMA(df['close'], self.ema_short)
            df['EMA_50'] = talib.EMA(df['close'], self.ema_long)
            
            # Indicateurs avancés
            df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], self.atr_period)
            df['MACD'], df['MACD_SIGNAL'], df['MACD_HIST'] = talib.MACD(
                df['close'],
                fastperiod=self.macd_fast,
                slowperiod=self.macd_slow,
                signalperiod=self.macd_signal
            )
            df['BOLLINGER_UP'], df['BOLLINGER_MID'], df['BOLLINGER_LOW'] = talib.BBANDS(
                df['close'],
                timeperiod=self.bb_period,
                nbdevup=self.bb_std,
                nbdevdn=self.bb_std
            )
            df['RSI'] = talib.RSI(df['close'], timeperiod=self.rsi_period)
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs: {str(e)}")
            raise
            
    def generate_signals(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Génère les signaux de trading.
        
        Args:
            df (pd.DataFrame): DataFrame avec les indicateurs
            
        Returns:
            Tuple[pd.Series, pd.Series]: Signaux d'achat et stop-loss
        """
        try:
            # Conditions d'achat améliorées
            buy_condition = (
                (df['EMA_20'] > df['EMA_50']) &  # Tendance haussière
                (df['MACD'] > df['MACD_SIGNAL']) &  # Croisement MACD positif
                (df['close'] > df['BOLLINGER_UP']) &  # Prix au-dessus de la bande supérieure
                (df['RSI'] < self.rsi_oversold)  # RSI en zone de survente
            )
            
            # Stop-loss dynamique basé sur l'ATR
            stop_loss = df['close'] - (self.atr_multiplier * df['ATR'])
            
            return buy_condition, stop_loss
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des signaux: {str(e)}")
            raise
            
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Méthode requise pour la compatibilité avec scikit-learn.
        
        Args:
            X (pd.DataFrame): Features
            y (pd.Series): Target
        """
        pass
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Génère les prédictions pour les données d'entrée.
        
        Args:
            X (pd.DataFrame): Données d'entrée
            
        Returns:
            np.ndarray: Prédictions (1 pour achat, 0 pour pas d'action)
        """
        try:
            # Calcul des indicateurs
            df = self.calculate_indicators(X.copy())
            
            # Génération des signaux
            buy_signals, _ = self.generate_signals(df)
            
            return buy_signals.astype(int).values
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {str(e)}")
            raise
            
    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """
        Retourne les paramètres de la stratégie.
        
        Args:
            deep (bool): Si True, retourne les paramètres imbriqués
            
        Returns:
            Dict[str, Any]: Paramètres de la stratégie
        """
        return {
            'ema_short': self.ema_short,
            'ema_long': self.ema_long,
            'rsi_period': self.rsi_period,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'atr_period': self.atr_period,
            'atr_multiplier': self.atr_multiplier,
            'macd_fast': self.macd_fast,
            'macd_slow': self.macd_slow,
            'macd_signal': self.macd_signal,
            'bb_period': self.bb_period,
            'bb_std': self.bb_std
        }
        
    def set_params(self, **params: Dict[str, Any]) -> None:
        """
        Met à jour les paramètres de la stratégie.
        
        Args:
            **params: Nouveaux paramètres
        """
        for key, value in params.items():
            setattr(self, key, value) 