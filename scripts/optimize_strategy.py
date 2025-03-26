import os
import sys
import json
import logging
import asyncio
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple
from .optimization_manager import OptimizationManager
from .alert_manager import AlertManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/optimization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        argparse.Namespace: Arguments parsés
    """
    parser = argparse.ArgumentParser(description='Script d\'optimisation de la stratégie de trading')
    parser.add_argument('--data', type=str, default='data/latest.csv',
                      help='Chemin du fichier de données')
    parser.add_argument('--iterations', type=int, default=1000,
                      help='Nombre d\'itérations pour l\'optimisation')
    parser.add_argument('--risk-level', type=int, default=3,
                      help='Niveau de risque (1-5)')
    parser.add_argument('--config', type=str, default='config/monitoring_config.json',
                      help='Chemin du fichier de configuration')
    parser.add_argument('--output', type=str, default='reports/optimization.json',
                      help='Chemin du fichier de rapport')
    return parser.parse_args()

def load_data(data_path: str) -> pd.DataFrame:
    """
    Charge et prépare les données pour l'optimisation.
    
    Args:
        data_path (str): Chemin du fichier de données
        
    Returns:
        pd.DataFrame: Données préparées
    """
    try:
        # Chargement des données
        data = pd.read_csv(data_path)
        
        # Conversion des timestamps
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)
        
        # Calcul des indicateurs techniques
        data['rsi'] = calculate_rsi(data['close'])
        data['macd'], data['macd_signal'] = calculate_macd(data['close'])
        
        return data
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données: {str(e)}")
        raise

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcule le RSI.
    
    Args:
        prices (pd.Series): Prix de clôture
        period (int): Période du RSI
        
    Returns:
        pd.Series: RSI calculé
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
    """
    Calcule le MACD.
    
    Args:
        prices (pd.Series): Prix de clôture
        fast (int): Période rapide
        slow (int): Période lente
        signal (int): Période du signal
        
    Returns:
        Tuple[pd.Series, pd.Series]: MACD et signal
    """
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

async def optimize_parameters(optimization_manager: OptimizationManager,
                            data: pd.DataFrame,
                            iterations: int,
                            risk_level: int) -> Dict[str, Any]:
    """
    Optimise les paramètres de la stratégie.
    
    Args:
        optimization_manager (OptimizationManager): Gestionnaire d'optimisation
        data (pd.DataFrame): Données de trading
        iterations (int): Nombre d'itérations
        risk_level (int): Niveau de risque
        
    Returns:
        Dict[str, Any]: Résultats de l'optimisation
    """
    try:
        results = await optimization_manager.optimize(
            data=data,
            iterations=iterations,
            risk_level=risk_level
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation: {str(e)}")
        return {}

def evaluate_strategy(data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, float]:
    """
    Évalue la stratégie avec les paramètres optimisés.
    
    Args:
        data (pd.DataFrame): Données de trading
        parameters (Dict[str, Any]): Paramètres optimisés
        
    Returns:
        Dict[str, float]: Métriques de performance
    """
    try:
        # Simulation de la stratégie
        trades = []
        position = 0
        entry_price = 0
        
        for i in range(len(data)):
            if position == 0:  # Pas de position
                if data['rsi'].iloc[i] < parameters['rsi_oversold']:
                    position = 1
                    entry_price = data['close'].iloc[i]
                    trades.append({
                        'type': 'buy',
                        'price': entry_price,
                        'timestamp': data.index[i]
                    })
                elif data['rsi'].iloc[i] > parameters['rsi_overbought']:
                    position = -1
                    entry_price = data['close'].iloc[i]
                    trades.append({
                        'type': 'sell',
                        'price': entry_price,
                        'timestamp': data.index[i]
                    })
            else:  # Position ouverte
                current_price = data['close'].iloc[i]
                pnl = (current_price - entry_price) / entry_price * position
                
                if pnl >= parameters['take_profit'] or pnl <= -parameters['stop_loss']:
                    trades.append({
                        'type': 'close',
                        'price': current_price,
                        'timestamp': data.index[i],
                        'pnl': pnl
                    })
                    position = 0
                    
        # Calcul des métriques
        if not trades:
            return {
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'profit_factor': 0
            }
            
        # Calcul du ratio de Sharpe
        returns = pd.Series([t['pnl'] for t in trades if 'pnl' in t])
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 1 else 0
        
        # Calcul du drawdown maximum
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # Calcul du taux de réussite
        winning_trades = len(returns[returns > 0])
        win_rate = winning_trades / len(returns)
        
        # Calcul du facteur de profit
        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation de la stratégie: {str(e)}")
        return {}

async def main():
    """
    Fonction principale du script.
    """
    try:
        # Parse des arguments
        args = parse_args()
        
        # Initialisation des gestionnaires
        optimization_manager = OptimizationManager()
        alert_manager = AlertManager()
        
        # Chargement des données
        logger.info(f"Chargement des données depuis {args.data}...")
        data = load_data(args.data)
        
        # Optimisation des paramètres
        logger.info("Démarrage de l'optimisation...")
        results = await optimize_parameters(
            optimization_manager,
            data,
            args.iterations,
            args.risk_level
        )
        
        if not results.get('success', False):
            logger.error("Échec de l'optimisation")
            sys.exit(1)
            
        # Évaluation de la stratégie
        logger.info("Évaluation de la stratégie optimisée...")
        metrics = evaluate_strategy(data, results['parameters'])
        
        # Mise à jour des résultats
        results['metrics'] = metrics
        
        # Envoi des alertes si nécessaire
        if metrics['sharpe_ratio'] < 1.0 or metrics['win_rate'] < 0.5:
            await alert_manager.send_telegram_alert(
                os.getenv('TELEGRAM_ADMIN_ID'),
                f"⚠️ Performance de la stratégie sous-optimale:\n"
                f"Ratio de Sharpe: {metrics['sharpe_ratio']:.2f}\n"
                f"Taux de réussite: {metrics['win_rate']:.2%}\n"
                f"Drawdown maximum: {metrics['max_drawdown']:.2%}"
            )
            
        # Sauvegarde du rapport
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=4)
            
        logger.info(f"Rapport sauvegardé dans {args.output}")
        
        # Affichage du résumé
        print("\nRésumé de l'optimisation:")
        print(f"Paramètres optimaux: {json.dumps(results['parameters'], indent=2)}")
        print(f"Ratio de Sharpe: {metrics['sharpe_ratio']:.2f}")
        print(f"Taux de réussite: {metrics['win_rate']:.2%}")
        print(f"Drawdown maximum: {metrics['max_drawdown']:.2%}")
        print(f"Facteur de profit: {metrics['profit_factor']:.2f}")
        
        # Code de sortie basé sur les métriques
        sys.exit(0 if metrics['sharpe_ratio'] >= 1.0 and metrics['win_rate'] >= 0.5 else 1)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du script: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 