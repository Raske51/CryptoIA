import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pdfkit
import logging
import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ReportManager:
    """
    Gestionnaire de rapports et de monitoring pour le bot de trading.
    """
    def __init__(self):
        """
        Initialise le gestionnaire de rapports.
        """
        load_dotenv()
        
        # Configuration des chemins
        self.reports_dir = "reports"
        self.metrics_dir = "metrics"
        self.ensure_directories()
        
        # Configuration de PDFKit
        self.pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None
        }

    def ensure_directories(self):
        """
        Crée les répertoires nécessaires s'ils n'existent pas.
        """
        for directory in [self.reports_dir, self.metrics_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Répertoire créé: {directory}")

    def generate_daily_report(
        self,
        trades: List[Dict],
        performance_metrics: Dict,
        market_data: pd.DataFrame
    ) -> str:
        """
        Génère un rapport PDF quotidien.
        
        Args:
            trades (List[Dict]): Liste des trades du jour
            performance_metrics (Dict): Métriques de performance
            market_data (pd.DataFrame): Données de marché
            
        Returns:
            str: Chemin du rapport généré
        """
        try:
            # Création du rapport HTML
            html_content = self._generate_html_report(
                trades, performance_metrics, market_data
            )
            
            # Génération du PDF
            timestamp = datetime.now().strftime("%Y%m%d")
            pdf_path = os.path.join(self.reports_dir, f"daily_report_{timestamp}.pdf")
            pdfkit.from_string(html_content, pdf_path, options=self.pdf_options)
            
            logger.info(f"Rapport quotidien généré: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
            raise

    def _generate_html_report(
        self,
        trades: List[Dict],
        performance_metrics: Dict,
        market_data: pd.DataFrame
    ) -> str:
        """
        Génère le contenu HTML du rapport.
        """
        # Création des graphiques
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Performance du Portfolio',
                'Distribution des Trades',
                'Volume d\'Échange',
                'Sentiment du Marché'
            )
        )
        
        # Graphique de performance
        fig.add_trace(
            go.Scatter(
                x=market_data.index,
                y=market_data['close'],
                name='Prix'
            ),
            row=1, col=1
        )
        
        # Distribution des trades
        trade_types = [trade['type'] for trade in trades]
        fig.add_trace(
            go.Pie(
                labels=['Achats', 'Ventes'],
                values=[trade_types.count('buy'), trade_types.count('sell')],
                name='Distribution'
            ),
            row=1, col=2
        )
        
        # Volume d'échange
        fig.add_trace(
            go.Bar(
                x=market_data.index,
                y=market_data['volume'],
                name='Volume'
            ),
            row=2, col=1
        )
        
        # Graphique de sentiment
        fig.add_trace(
            go.Scatter(
                x=market_data.index,
                y=market_data['sentiment'],
                name='Sentiment'
            ),
            row=2, col=2
        )
        
        # Mise à jour du layout
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Rapport de Trading Quotidien"
        )
        
        # Génération du HTML
        html_content = f"""
        <html>
        <head>
            <title>Rapport de Trading Quotidien</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
                .metric-card {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Rapport de Trading Quotidien</h1>
                <p>Date: {datetime.now().strftime('%Y-%m-%d')}</p>
                
                <div class="metrics">
                    <div class="metric-card">
                        <h3>Performance Journalière</h3>
                        <div class="metric-value">{performance_metrics['daily_return']:.2%}</div>
                    </div>
                    <div class="metric-card">
                        <h3>Nombre de Trades</h3>
                        <div class="metric-value">{len(trades)}</div>
                    </div>
                    <div class="metric-card">
                        <h3>Win Rate</h3>
                        <div class="metric-value">{performance_metrics['win_rate']:.2%}</div>
                    </div>
                </div>
                
                {fig.to_html(full_html=False)}
                
                <h2>Détails des Trades</h2>
                <table border="1" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Prix</th>
                        <th>Quantité</th>
                        <th>P&L</th>
                    </tr>
                    {''.join([f"""
                    <tr>
                        <td>{trade['timestamp']}</td>
                        <td>{trade['type']}</td>
                        <td>{trade['price']:.2f}</td>
                        <td>{trade['quantity']:.4f}</td>
                        <td>{trade['pnl']:.2f}</td>
                    </tr>
                    """ for trade in trades])}
                </table>
            </div>
        </body>
        </html>
        """
        
        return html_content

    def update_metrics(
        self,
        metrics: Dict,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Met à jour les métriques pour Grafana.
        
        Args:
            metrics (Dict): Nouvelles métriques
            timestamp (datetime, optional): Horodatage des métriques
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Format des métriques pour Grafana
            grafana_metrics = {
                "timestamp": timestamp.isoformat(),
                "metrics": metrics
            }
            
            # Sauvegarde des métriques
            metrics_file = os.path.join(
                self.metrics_dir,
                f"metrics_{timestamp.strftime('%Y%m%d')}.json"
            )
            
            with open(metrics_file, 'w') as f:
                json.dump(grafana_metrics, f)
            
            logger.info(f"Métriques mises à jour: {metrics_file}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des métriques: {str(e)}")
            raise

    def get_metrics_for_grafana(
        self,
        days: int = 7
    ) -> List[Dict]:
        """
        Récupère les métriques pour Grafana.
        
        Args:
            days (int): Nombre de jours de données à récupérer
            
        Returns:
            List[Dict]: Liste des métriques formatées pour Grafana
        """
        try:
            metrics_list = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            current_date = start_date
            while current_date <= end_date:
                metrics_file = os.path.join(
                    self.metrics_dir,
                    f"metrics_{current_date.strftime('%Y%m%d')}.json"
                )
                
                if os.path.exists(metrics_file):
                    with open(metrics_file, 'r') as f:
                        metrics = json.load(f)
                        metrics_list.append(metrics)
                
                current_date += timedelta(days=1)
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques: {str(e)}")
            raise 