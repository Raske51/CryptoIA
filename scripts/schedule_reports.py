import schedule
import time
import logging
from datetime import datetime
from utils.report_manager import ReportManager
from utils.trading_bot import TradingBot
from utils.sentiment_analyzer import SentimentAnalyzer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_daily_report():
    """
    Génère le rapport quotidien.
    """
    try:
        # Initialisation des composants
        report_manager = ReportManager()
        trading_bot = TradingBot()
        sentiment_analyzer = SentimentAnalyzer()
        
        # Récupération des données
        trades = trading_bot.get_daily_trades()
        performance_metrics = trading_bot.get_performance_metrics()
        market_data = trading_bot.get_market_data()
        
        # Analyse du sentiment
        sentiment_results = sentiment_analyzer.get_sentiment_score("Bitcoin")
        market_data['sentiment'] = sentiment_results['average_sentiment']
        
        # Génération du rapport
        report_path = report_manager.generate_daily_report(
            trades=trades,
            performance_metrics=performance_metrics,
            market_data=market_data
        )
        
        logger.info(f"Rapport quotidien généré: {report_path}")
        
        # Mise à jour des métriques pour Grafana
        report_manager.update_metrics({
            'daily_return': performance_metrics['daily_return'],
            'win_rate': performance_metrics['win_rate'],
            'sentiment_score': sentiment_results['average_sentiment'],
            'volume': market_data['volume'].iloc[-1],
            'trade_count': len(trades)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {str(e)}")

def update_metrics():
    """
    Met à jour les métriques pour le dashboard Grafana.
    """
    try:
        # Initialisation des composants
        report_manager = ReportManager()
        trading_bot = TradingBot()
        sentiment_analyzer = SentimentAnalyzer()
        
        # Récupération des données
        performance_metrics = trading_bot.get_performance_metrics()
        market_data = trading_bot.get_market_data()
        sentiment_results = sentiment_analyzer.get_sentiment_score("Bitcoin")
        
        # Mise à jour des métriques
        report_manager.update_metrics({
            'daily_return': performance_metrics['daily_return'],
            'win_rate': performance_metrics['win_rate'],
            'sentiment_score': sentiment_results['average_sentiment'],
            'volume': market_data['volume'].iloc[-1]
        })
        
        logger.info("Métriques mises à jour pour Grafana")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des métriques: {str(e)}")

def main():
    """
    Fonction principale pour planifier les tâches.
    """
    try:
        # Planification des tâches
        schedule.every().day.at("23:59").do(generate_daily_report)
        schedule.every(5).minutes.do(update_metrics)
        
        logger.info("Planification des tâches démarrée")
        
        # Boucle principale
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Erreur dans la boucle principale: {str(e)}")

if __name__ == "__main__":
    main() 