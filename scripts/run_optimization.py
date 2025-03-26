import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from utils.optimization_manager import OptimizationManager
from utils.data_manager import DataManager
from utils.risk_manager import RiskManager
from utils.advanced_strategy import AdvancedStrategy

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_base_strategy() -> Dict[str, Any]:
    """
    Charge la stratégie de base depuis le fichier de configuration.
    
    Returns:
        Dict[str, Any]: Paramètres de la stratégie de base
    """
    try:
        with open('config/strategy_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la stratégie de base: {str(e)}")
        raise

def define_param_grid() -> Dict[str, Any]:
    """
    Définit la grille de paramètres pour l'optimisation.
    
    Returns:
        Dict[str, Any]: Grille de paramètres
    """
    return {
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

def run_optimization():
    """
    Exécute l'optimisation continue des stratégies.
    """
    try:
        # Initialisation des composants
        data_manager = DataManager()
        risk_manager = RiskManager()
        optimization_manager = OptimizationManager(data_manager, risk_manager)
        
        # Chargement de la stratégie de base
        base_strategy = load_base_strategy()
        
        # Configuration des paramètres
        param_grid = define_param_grid()
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        # Période d'optimisation
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Exécution des tests A/B
        logger.info("Démarrage des tests A/B")
        for symbol in symbols:
            logger.info(f"Test A/B pour {symbol}")
            ab_results = optimization_manager.run_ab_test(
                symbol,
                base_strategy,
                start_date,
                end_date
            )
            
            # Sauvegarde des résultats
            results_file = f"results/ab_test_{symbol}_{datetime.now().strftime('%Y%m%d')}.json"
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(ab_results, f, indent=4)
            
            logger.info(f"Résultats A/B sauvegardés dans {results_file}")
        
        # Optimisation des paramètres
        logger.info("Démarrage de l'optimisation des paramètres")
        for symbol in symbols:
            logger.info(f"Optimisation des paramètres pour {symbol}")
            
            # Création de la stratégie
            strategy = AdvancedStrategy(**base_strategy)
            
            # Optimisation
            optimization_results = optimization_manager.optimize_parameters(
                symbol,
                strategy,
                param_grid,
                start_date,
                end_date
            )
            
            # Sauvegarde des résultats
            results_file = f"results/optimization_{symbol}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(results_file, 'w') as f:
                json.dump(optimization_results, f, indent=4)
            
            logger.info(f"Résultats d'optimisation sauvegardés dans {results_file}")
            
            # Génération du rapport
            report = optimization_manager.get_optimization_report(symbol)
            report_file = f"reports/optimization_report_{symbol}_{datetime.now().strftime('%Y%m%d')}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=4)
            
            logger.info(f"Rapport d'optimisation généré: {report_file}")
        
        logger.info("Optimisation terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation: {str(e)}")
        raise

def main():
    """
    Fonction principale.
    """
    try:
        logger.info("Démarrage de l'optimisation continue")
        run_optimization()
        logger.info("Optimisation continue terminée")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 