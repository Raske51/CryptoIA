import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from utils.advanced_strategy import AdvancedStrategy
from utils.risk_manager import RiskManager
from utils.optimization_manager import OptimizationManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedBacktest:
    """
    Système de backtesting avec optimisation et gestion des risques.
    """
    def __init__(self, risk_percentage: float = 3.0):
        """
        Initialise le système de backtesting.
        
        Args:
            risk_percentage (float): Pourcentage de risque par trade
        """
        self.risk_percentage = risk_percentage
        self.risk_manager = RiskManager()
        self.optimization_manager = OptimizationManager(None, self.risk_manager)
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Charge les données historiques.
        
        Args:
            file_path (str): Chemin du fichier CSV
            
        Returns:
            pd.DataFrame: Données historiques
        """
        try:
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {str(e)}")
            raise
            
    def calculate_metrics(self, trades: pd.DataFrame) -> Dict[str, float]:
        """
        Calcule les métriques de performance.
        
        Args:
            trades (pd.DataFrame): Historique des trades
            
        Returns:
            Dict[str, float]: Métriques de performance
        """
        try:
            # Calcul des retours
            returns = trades['pnl'].pct_change()
            
            # Métriques de base
            total_return = (trades['pnl'].iloc[-1] / trades['initial_capital'].iloc[0]) - 1
            sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() != 0 else 0
            max_drawdown = (trades['equity'].cummax() - trades['equity']) / trades['equity'].cummax()
            max_drawdown = max_drawdown.max()
            
            # Métriques de trading
            win_rate = len(trades[trades['pnl'] > 0]) / len(trades)
            profit_factor = abs(trades[trades['pnl'] > 0]['pnl'].sum() / trades[trades['pnl'] < 0]['pnl'].sum())
            
            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': len(trades),
                'avg_trade': trades['pnl'].mean(),
                'std_trade': trades['pnl'].std()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques: {str(e)}")
            raise
            
    def run_backtest(self, data: pd.DataFrame, strategy: AdvancedStrategy) -> pd.DataFrame:
        """
        Exécute le backtest avec la stratégie donnée.
        
        Args:
            data (pd.DataFrame): Données historiques
            strategy (AdvancedStrategy): Stratégie à tester
            
        Returns:
            pd.DataFrame: Historique des trades
        """
        try:
            # Initialisation
            trades = pd.DataFrame()
            position = 0
            entry_price = 0
            stop_loss = 0
            equity = 10000  # Capital initial
            trades['equity'] = equity
            trades['initial_capital'] = equity
            
            # Calcul des indicateurs
            df = strategy.calculate_indicators(data.copy())
            
            # Génération des signaux
            buy_signals, stop_losses = strategy.generate_signals(df)
            
            # Statistiques de trading pour le critère de Kelly
            win_rate = 0.65  # À remplacer par des statistiques réelles
            win_loss_ratio = 2.5  # À remplacer par des statistiques réelles
            
            # Simulation des trades
            for i in range(len(df)):
                current_price = df['close'].iloc[i]
                
                # Gestion des positions existantes
                if position > 0:
                    # Vérification du stop-loss
                    if current_price <= stop_loss:
                        pnl = (current_price - entry_price) * position
                        equity += pnl
                        position = 0
                        trades.loc[df.index[i]] = {
                            'type': 'sell',
                            'price': current_price,
                            'pnl': pnl,
                            'equity': equity,
                            'initial_capital': trades['initial_capital'].iloc[0]
                        }
                
                # Entrée en position
                elif buy_signals.iloc[i]:
                    # Calcul de la taille de position avec le critère de Kelly
                    atr = df['ATR'].iloc[i]
                    stop_loss = stop_losses.iloc[i]
                    
                    # Analyse du setup avec le critère de Kelly
                    stop_loss, take_profit, position_size = self.risk_manager.analyze_trade_setup(
                        current_price,
                        atr,
                        equity,
                        win_rate,
                        win_loss_ratio
                    )
                    
                    position = position_size
                    entry_price = current_price
                    trades.loc[df.index[i]] = {
                        'type': 'buy',
                        'price': current_price,
                        'pnl': 0,
                        'equity': equity,
                        'initial_capital': trades['initial_capital'].iloc[0],
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'position_size': position_size
                    }
            
            return trades
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest: {str(e)}")
            raise
            
    def optimize_strategy(self, data: pd.DataFrame, param_grid: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimise les paramètres de la stratégie.
        
        Args:
            data (pd.DataFrame): Données historiques
            param_grid (Dict[str, Any]): Grille de paramètres
            
        Returns:
            Dict[str, Any]: Meilleurs paramètres et résultats
        """
        try:
            # Création de la stratégie de base
            base_strategy = AdvancedStrategy()
            
            # Optimisation
            results = self.optimization_manager.optimize_parameters(
                'BTCUSDT',  # Symbole fictif pour l'optimisation
                base_strategy,
                param_grid,
                data.index[0],
                data.index[-1]
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation: {str(e)}")
            raise
            
    def generate_report(self, trades: pd.DataFrame, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Génère un rapport de backtest.
        
        Args:
            trades (pd.DataFrame): Historique des trades
            metrics (Dict[str, float]): Métriques de performance
            
        Returns:
            Dict[str, Any]: Rapport complet
        """
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'risk_percentage': self.risk_percentage,
                'metrics': metrics,
                'trades_summary': {
                    'total_trades': len(trades),
                    'buy_trades': len(trades[trades['type'] == 'buy']),
                    'sell_trades': len(trades[trades['type'] == 'sell']),
                    'winning_trades': len(trades[trades['pnl'] > 0]),
                    'losing_trades': len(trades[trades['pnl'] < 0])
                },
                'equity_curve': trades['equity'].tolist(),
                'dates': trades.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
            raise

def main():
    """
    Fonction principale.
    """
    try:
        # Arguments de ligne de commande
        import argparse
        parser = argparse.ArgumentParser(description='Backtest avec optimisation et gestion des risques')
        parser.add_argument('--data', type=str, required=True, help='Chemin du fichier de données historiques')
        parser.add_argument('--risk', type=float, default=3.0, help='Pourcentage de risque par trade')
        args = parser.parse_args()
        
        # Initialisation
        backtest = EnhancedBacktest(risk_percentage=args.risk)
        
        # Chargement des données
        logger.info(f"Chargement des données depuis {args.data}")
        data = backtest.load_data(args.data)
        
        # Création de la stratégie
        strategy = AdvancedStrategy()
        
        # Optimisation
        logger.info("Démarrage de l'optimisation")
        param_grid = {
            'ema_short': range(10, 30, 2),
            'ema_long': range(40, 60, 5),
            'rsi_period': range(10, 20, 2),
            'rsi_overbought': range(65, 80, 5),
            'rsi_oversold': range(20, 35, 5),
            'atr_period': range(10, 20, 2),
            'atr_multiplier': [1.0, 1.5, 2.0, 2.5],
            'macd_fast': range(8, 16, 2),
            'macd_slow': range(20, 30, 2),
            'macd_signal': range(7, 11, 1),
            'bb_period': range(15, 25, 2),
            'bb_std': [1.5, 2.0, 2.5, 3.0]
        }
        
        optimization_results = backtest.optimize_strategy(data, param_grid)
        
        # Mise à jour de la stratégie avec les meilleurs paramètres
        strategy.set_params(**optimization_results['best_params'])
        
        # Exécution du backtest
        logger.info("Démarrage du backtest")
        trades = backtest.run_backtest(data, strategy)
        
        # Calcul des métriques
        metrics = backtest.calculate_metrics(trades)
        
        # Génération du rapport
        report = backtest.generate_report(trades, metrics)
        
        # Sauvegarde des résultats
        results_dir = 'results'
        os.makedirs(results_dir, exist_ok=True)
        
        # Sauvegarde du rapport
        report_file = os.path.join(results_dir, f'backtest_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=4)
        
        logger.info(f"Rapport sauvegardé dans {report_file}")
        
        # Affichage des résultats
        print("\nRésultats du backtest:")
        print(f"Retour total: {metrics['total_return']:.2%}")
        print(f"Ratio de Sharpe: {metrics['sharpe_ratio']:.2f}")
        print(f"Drawdown maximum: {metrics['max_drawdown']:.2%}")
        print(f"Win rate: {metrics['win_rate']:.2%}")
        print(f"Profit factor: {metrics['profit_factor']:.2f}")
        print(f"Nombre total de trades: {metrics['total_trades']}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 