import pandas as pd
import numpy as np
import talib
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Gestionnaire de risques pour le trading.
    """
    def __init__(self, kelly_fraction: float = 0.5):
        """
        Initialise le gestionnaire de risque.
        
        Args:
            kelly_fraction (float): Fraction du critère de Kelly à utiliser (0-1)
        """
        self.kelly_fraction = kelly_fraction

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcule l'Average True Range (ATR).
        
        Args:
            high (pd.Series): Prix hauts
            low (pd.Series): Prix bas
            close (pd.Series): Prix de clôture
            period (int): Période de calcul
            
        Returns:
            pd.Series: ATR calculé
        """
        try:
            return talib.ATR(high, low, close, timeperiod=period)
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'ATR: {str(e)}")
            raise

    def calculate_dynamic_stop_loss(self, entry_price: float, atr: float, multiplier: float = 2.0) -> float:
        """
        Calcule un stop-loss dynamique basé sur l'ATR.
        
        Args:
            entry_price (float): Prix d'entrée
            atr (float): ATR actuel
            multiplier (float): Multiplicateur de l'ATR
            
        Returns:
            float: Niveau de stop-loss
        """
        try:
            return entry_price - (multiplier * atr)
        except Exception as e:
            logger.error(f"Erreur lors du calcul du stop-loss: {str(e)}")
            raise

    def kelly_criterion(self, win_rate: float, win_loss_ratio: float) -> float:
        """
        Calcule la fraction optimale du capital à risquer selon le critère de Kelly.
        
        Args:
            win_rate (float): Taux de réussite (0-1)
            win_loss_ratio (float): Ratio gain/pertes
            
        Returns:
            float: Fraction optimale du capital à risquer (0-1)
        """
        try:
            # Calcul du critère de Kelly
            kelly = (win_rate - ((1 - win_rate) / win_loss_ratio)) / win_loss_ratio
            
            # Limitation entre 0 et 1
            kelly = max(0, min(1, kelly))
            
            # Application de la fraction de Kelly
            return kelly * self.kelly_fraction
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du critère de Kelly: {str(e)}")
            raise

    def calculate_position_size(self, capital: float, entry_price: float, stop_loss: float,
                              win_rate: Optional[float] = None, win_loss_ratio: Optional[float] = None) -> float:
        """
        Calcule la taille de position optimale.
        
        Args:
            capital (float): Capital disponible
            entry_price (float): Prix d'entrée
            stop_loss (float): Niveau de stop-loss
            win_rate (float, optional): Taux de réussite pour le critère de Kelly
            win_loss_ratio (float, optional): Ratio gain/pertes pour le critère de Kelly
            
        Returns:
            float: Taille de position en unités
        """
        try:
            # Calcul du risque par unité
            risk_per_unit = entry_price - stop_loss
            
            if risk_per_unit <= 0:
                logger.warning("Le stop-loss est supérieur ou égal au prix d'entrée")
                return 0
                
            # Si les statistiques de trading sont disponibles, utiliser le critère de Kelly
            if win_rate is not None and win_loss_ratio is not None:
                risk_fraction = self.kelly_criterion(win_rate, win_loss_ratio)
                risk_amount = capital * risk_fraction
            else:
                # Sinon, utiliser un risque fixe de 2%
                risk_amount = capital * 0.02
                
            # Calcul de la taille de position
            position_size = risk_amount / risk_per_unit
            
            return position_size
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la taille de position: {str(e)}")
            raise

    def calculate_take_profit(self, entry_price: float, stop_loss: float, risk_reward_ratio: float = 2.0) -> float:
        """
        Calcule le niveau de take-profit basé sur le ratio risque/récompense.
        
        Args:
            entry_price (float): Prix d'entrée
            stop_loss (float): Niveau de stop-loss
            risk_reward_ratio (float): Ratio risque/récompense
            
        Returns:
            float: Niveau de take-profit
        """
        try:
            risk = entry_price - stop_loss
            return entry_price + (risk * risk_reward_ratio)
        except Exception as e:
            logger.error(f"Erreur lors du calcul du take-profit: {str(e)}")
            raise

    def analyze_trade_setup(self, entry_price: float, atr: float, capital: float,
                          win_rate: Optional[float] = None, win_loss_ratio: Optional[float] = None) -> Tuple[float, float, float]:
        """
        Analyse un setup de trade et retourne les niveaux de stop-loss, take-profit et la taille de position.
        
        Args:
            entry_price (float): Prix d'entrée
            atr (float): ATR actuel
            capital (float): Capital disponible
            win_rate (float, optional): Taux de réussite
            win_loss_ratio (float, optional): Ratio gain/pertes
            
        Returns:
            Tuple[float, float, float]: (stop_loss, take_profit, position_size)
        """
        try:
            # Calcul du stop-loss
            stop_loss = self.calculate_dynamic_stop_loss(entry_price, atr)
            
            # Calcul du take-profit
            take_profit = self.calculate_take_profit(entry_price, stop_loss)
            
            # Calcul de la taille de position
            position_size = self.calculate_position_size(
                capital, entry_price, stop_loss, win_rate, win_loss_ratio
            )
            
            return stop_loss, take_profit, position_size
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du setup: {str(e)}")
            raise 