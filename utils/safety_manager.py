import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SafetyManager:
    """
    Gestionnaire de sécurité avec circuit breaker et mécanismes de protection.
    """
    def __init__(self, 
                 max_drawdown: float = 0.08,
                 max_daily_loss: float = 0.03,
                 max_position_size: float = 0.2,
                 volatility_threshold: float = 0.02,
                 recovery_period: int = 5):
        """
        Initialise le gestionnaire de sécurité.
        
        Args:
            max_drawdown (float): Drawdown maximum autorisé (0-1)
            max_daily_loss (float): Perte journalière maximum autorisée (0-1)
            max_position_size (float): Taille maximum d'une position (0-1)
            volatility_threshold (float): Seuil de volatilité pour l'arrêt (0-1)
            recovery_period (int): Période de récupération en jours
        """
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.volatility_threshold = volatility_threshold
        self.recovery_period = recovery_period
        
        self.portfolio_history: List[Dict[str, Any]] = []
        self.daily_high = 0
        self.daily_start = 0
        self.emergency_stop_triggered = False
        self.stop_date = None
        
    def check_risk(self, current_value: float, timestamp: datetime) -> bool:
        """
        Vérifie les risques et déclenche le circuit breaker si nécessaire.
        
        Args:
            current_value (float): Valeur actuelle du portfolio
            timestamp (datetime): Horodatage de la vérification
            
        Returns:
            bool: True si le trading peut continuer, False sinon
        """
        try:
            if self.emergency_stop_triggered:
                return False
                
            # Mise à jour de l'historique
            self.portfolio_history.append({
                'timestamp': timestamp,
                'value': current_value
            })
            
            # Vérification du drawdown global
            peak = max(h['value'] for h in self.portfolio_history)
            drawdown = (peak - current_value) / peak
            
            if drawdown > self.max_drawdown:
                logger.warning(f"Drawdown maximum atteint: {drawdown:.2%}")
                self.trigger_emergency_stop("Drawdown maximum dépassé")
                return False
                
            # Vérification de la perte journalière
            if timestamp.date() != self.daily_start.date():
                self.daily_start = current_value
                self.daily_high = current_value
            else:
                self.daily_high = max(self.daily_high, current_value)
                
            daily_drawdown = (self.daily_high - current_value) / self.daily_high
            if daily_drawdown > self.max_daily_loss:
                logger.warning(f"Perte journalière maximum atteinte: {daily_drawdown:.2%}")
                self.trigger_emergency_stop("Perte journalière maximum dépassée")
                return False
                
            # Vérification de la volatilité
            if len(self.portfolio_history) > 1:
                returns = np.diff([h['value'] for h in self.portfolio_history[-20:]])
                volatility = np.std(returns) / np.mean(returns) if np.mean(returns) != 0 else 0
                
                if volatility > self.volatility_threshold:
                    logger.warning(f"Volatilité excessive détectée: {volatility:.2%}")
                    self.trigger_emergency_stop("Volatilité excessive")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des risques: {str(e)}")
            return False
            
    def check_position_size(self, position_value: float, portfolio_value: float) -> bool:
        """
        Vérifie si la taille d'une position est acceptable.
        
        Args:
            position_value (float): Valeur de la position
            portfolio_value (float): Valeur totale du portfolio
            
        Returns:
            bool: True si la taille est acceptable, False sinon
        """
        try:
            position_ratio = position_value / portfolio_value
            return position_ratio <= self.max_position_size
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la taille de position: {str(e)}")
            return False
            
    def trigger_emergency_stop(self, reason: str) -> None:
        """
        Déclenche l'arrêt d'urgence.
        
        Args:
            reason (str): Raison de l'arrêt
        """
        try:
            self.emergency_stop_triggered = True
            self.stop_date = datetime.now()
            
            logger.warning(f"🚨 Arrêt d'urgence déclenché: {reason}")
            logger.warning("Liquidation des positions en cours...")
            
            # Ici, ajouter le code pour liquider les positions
            # self.liquidate_positions()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt d'urgence: {str(e)}")
            
    def can_resume_trading(self) -> bool:
        """
        Vérifie si le trading peut reprendre après un arrêt d'urgence.
        
        Returns:
            bool: True si le trading peut reprendre, False sinon
        """
        try:
            if not self.emergency_stop_triggered:
                return True
                
            # Vérification de la période de récupération
            if self.stop_date is None:
                return False
                
            recovery_days = (datetime.now() - self.stop_date).days
            if recovery_days < self.recovery_period:
                return False
                
            # Vérification de la stabilité du portfolio
            if len(self.portfolio_history) < 20:
                return False
                
            recent_values = [h['value'] for h in self.portfolio_history[-20:]]
            volatility = np.std(recent_values) / np.mean(recent_values)
            
            if volatility > self.volatility_threshold:
                return False
                
            # Réinitialisation
            self.emergency_stop_triggered = False
            self.stop_date = None
            logger.info("Trading autorisé à reprendre")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de reprise: {str(e)}")
            return False
            
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Retourne les métriques de risque actuelles.
        
        Returns:
            Dict[str, Any]: Métriques de risque
        """
        try:
            if not self.portfolio_history:
                return {}
                
            current_value = self.portfolio_history[-1]['value']
            peak = max(h['value'] for h in self.portfolio_history)
            drawdown = (peak - current_value) / peak
            
            # Calcul de la volatilité
            values = [h['value'] for h in self.portfolio_history]
            returns = np.diff(values)
            volatility = np.std(returns) / np.mean(returns) if np.mean(returns) != 0 else 0
            
            return {
                'current_value': current_value,
                'peak_value': peak,
                'drawdown': drawdown,
                'volatility': volatility,
                'emergency_stop_active': self.emergency_stop_triggered,
                'stop_date': self.stop_date.isoformat() if self.stop_date else None,
                'days_since_stop': (datetime.now() - self.stop_date).days if self.stop_date else 0
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques de risque: {str(e)}")
            return {} 