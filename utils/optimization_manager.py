import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import make_scorer
from utils.backtesting import Backtest
from utils.advanced_strategy import AdvancedStrategy

logger = logging.getLogger(__name__)

class OptimizationManager:
    """
    Gestionnaire d'optimisation des stratégies de trading.
    """
    def __init__(self, data_manager, risk_manager):
        """
        Initialise le gestionnaire d'optimisation.
        
        Args:
            data_manager: Gestionnaire de données
            risk_manager: Gestionnaire de risque
        """
        self.data_manager = data_manager
        self.risk_manager = risk_manager
        self.strategies = {}
        self.results = {}
        
    def create_strategy_variants(self, base_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Crée des variantes de la stratégie de base pour A/B testing.
        
        Args:
            base_strategy (Dict[str, Any]): Stratégie de base
            
        Returns:
            List[Dict[str, Any]]: Liste des variantes de stratégie
        """
        variants = []
        
        # Variante 1: Paramètres plus agressifs
        aggressive = base_strategy.copy()
        aggressive.update({
            'ema_short': base_strategy['ema_short'] - 2,
            'ema_long': base_strategy['ema_long'] - 5,
            'rsi_period': base_strategy['rsi_period'] - 2,
            'rsi_overbought': base_strategy['rsi_overbought'] + 2,
            'rsi_oversold': base_strategy['rsi_oversold'] - 2
        })
        variants.append(aggressive)
        
        # Variante 2: Paramètres plus conservateurs
        conservative = base_strategy.copy()
        conservative.update({
            'ema_short': base_strategy['ema_short'] + 2,
            'ema_long': base_strategy['ema_long'] + 5,
            'rsi_period': base_strategy['rsi_period'] + 2,
            'rsi_overbought': base_strategy['rsi_overbought'] - 2,
            'rsi_oversold': base_strategy['rsi_oversold'] + 2
        })
        variants.append(conservative)
        
        return variants
        
    def run_ab_test(self, symbol: str, base_strategy: Dict[str, Any], 
                    start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Exécute un test A/B sur différentes variantes de stratégie.
        
        Args:
            symbol (str): Symbole à trader
            base_strategy (Dict[str, Any]): Stratégie de base
            start_date (datetime): Date de début
            end_date (datetime): Date de fin
            
        Returns:
            Dict[str, Any]: Résultats des tests
        """
        try:
            # Création des variantes
            variants = self.create_strategy_variants(base_strategy)
            results = {}
            
            # Test de la stratégie de base
            base_backtest = Backtest(
                self.data_manager,
                AdvancedStrategy(**base_strategy),
                self.risk_manager
            )
            base_results = base_backtest.run(symbol, start_date, end_date)
            results['base'] = base_results
            
            # Test des variantes
            for i, variant in enumerate(variants):
                variant_backtest = Backtest(
                    self.data_manager,
                    AdvancedStrategy(**variant),
                    self.risk_manager
                )
                variant_results = variant_backtest.run(symbol, start_date, end_date)
                results[f'variant_{i+1}'] = variant_results
            
            # Analyse des résultats
            analysis = self._analyze_ab_results(results)
            self.results[symbol] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors du test A/B: {str(e)}")
            raise
            
    def optimize_parameters(self, symbol: str, strategy: AdvancedStrategy,
                          param_grid: Dict[str, List[Any]], 
                          start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Optimise les paramètres de la stratégie avec GridSearchCV.
        
        Args:
            symbol (str): Symbole à trader
            strategy (AdvancedStrategy): Stratégie à optimiser
            param_grid (Dict[str, List[Any]]): Grille de paramètres
            start_date (datetime): Date de début
            end_date (datetime): Date de fin
            
        Returns:
            Dict[str, Any]: Meilleurs paramètres et résultats
        """
        try:
            # Préparation des données
            data = self.data_manager.get_historical_data(symbol, start_date, end_date)
            
            # Création du scorer personnalisé
            def custom_scorer(y_true, y_pred):
                # Simulation de trading avec les prédictions
                returns = np.where(y_pred == 1, data['returns'], 0)
                sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0
                return sharpe_ratio
            
            scorer = make_scorer(custom_scorer)
            
            # Configuration de la validation croisée temporelle
            tscv = TimeSeriesSplit(n_splits=5)
            
            # Grid Search
            grid_search = GridSearchCV(
                estimator=strategy,
                param_grid=param_grid,
                cv=tscv,
                scoring=scorer,
                n_jobs=-1,
                verbose=1
            )
            
            # Entraînement
            X = data.drop(['returns', 'target'], axis=1)
            y = data['target']
            grid_search.fit(X, y)
            
            # Analyse des résultats
            results = {
                'best_params': grid_search.best_params_,
                'best_score': grid_search.best_score_,
                'cv_results': grid_search.cv_results_
            }
            
            # Test avec les meilleurs paramètres
            best_strategy = AdvancedStrategy(**grid_search.best_params_)
            backtest = Backtest(self.data_manager, best_strategy, self.risk_manager)
            test_results = backtest.run(symbol, start_date, end_date)
            results['backtest_results'] = test_results
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation des paramètres: {str(e)}")
            raise
            
    def _analyze_ab_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse les résultats des tests A/B.
        
        Args:
            results (Dict[str, Any]): Résultats des tests
            
        Returns:
            Dict[str, Any]: Analyse des résultats
        """
        analysis = {}
        
        for strategy_name, strategy_results in results.items():
            analysis[strategy_name] = {
                'total_return': strategy_results['total_return'],
                'sharpe_ratio': strategy_results['sharpe_ratio'],
                'max_drawdown': strategy_results['max_drawdown'],
                'win_rate': strategy_results['win_rate'],
                'profit_factor': strategy_results['profit_factor']
            }
        
        # Identification de la meilleure stratégie
        best_strategy = max(
            analysis.items(),
            key=lambda x: x[1]['sharpe_ratio']
        )
        analysis['best_strategy'] = best_strategy
        
        return analysis
        
    def get_optimization_report(self, symbol: str) -> Dict[str, Any]:
        """
        Génère un rapport d'optimisation.
        
        Args:
            symbol (str): Symbole analysé
            
        Returns:
            Dict[str, Any]: Rapport d'optimisation
        """
        if symbol not in self.results:
            raise ValueError(f"Aucun résultat d'optimisation trouvé pour {symbol}")
            
        results = self.results[symbol]
        
        report = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'best_strategy': results['best_strategy'][0],
            'performance_metrics': results['best_strategy'][1],
            'all_strategies': results
        }
        
        return report 