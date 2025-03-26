import os
import json
import logging
import requests
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class GrafanaDashboardDeployer:
    """
    Déployeur de dashboard Grafana pour le bot de trading.
    """
    def __init__(self, 
                 grafana_url: str,
                 api_key: str,
                 datasource_name: str = "trading_metrics"):
        """
        Initialise le déployeur de dashboard.
        
        Args:
            grafana_url (str): URL de l'instance Grafana
            api_key (str): Clé API Grafana
            datasource_name (str): Nom de la source de données
        """
        self.grafana_url = grafana_url.rstrip('/')
        self.api_key = api_key
        self.datasource_name = datasource_name
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
    def create_datasource(self) -> bool:
        """
        Crée la source de données dans Grafana.
        
        Returns:
            bool: True si la création est réussie
        """
        try:
            datasource_config = {
                "name": self.datasource_name,
                "type": "influxdb",
                "url": "http://influxdb:8086",
                "access": "proxy",
                "database": "trading_metrics",
                "jsonData": {
                    "organization": "trading_bot",
                    "defaultBucket": "trading_metrics",
                    "version": "Flux"
                }
            }
            
            response = requests.post(
                f"{self.grafana_url}/api/datasources",
                headers=self.headers,
                json=datasource_config
            )
            
            if response.status_code == 200:
                logger.info("Source de données créée avec succès")
                return True
            else:
                logger.error(f"Erreur lors de la création de la source de données: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de la source de données: {str(e)}")
            return False
            
    def create_dashboard(self) -> bool:
        """
        Crée le dashboard dans Grafana.
        
        Returns:
            bool: True si la création est réussie
        """
        try:
            dashboard_config = {
                "dashboard": {
                    "id": None,
                    "uid": "trading-bot-dashboard",
                    "title": "Trading Bot Dashboard",
                    "tags": ["trading", "crypto"],
                    "timezone": "browser",
                    "schemaVersion": 38,
                    "version": 0,
                    "refresh": "5s",
                    "panels": [
                        # Panel 1: Performance Journalière
                        {
                            "id": 1,
                            "title": "Performance Journalière",
                            "type": "timeseries",
                            "datasource": self.datasource_name,
                            "gridPos": {
                                "h": 8,
                                "w": 12,
                                "x": 0,
                                "y": 0
                            },
                            "targets": [
                                {
                                    "query": """
                                    from(bucket: "trading_metrics")
                                        |> range(start: -7d)
                                        |> filter(fn: (r) => r["_measurement"] == "daily_return")
                                        |> yield(name: "mean")
                                    """,
                                    "refId": "A"
                                }
                            ],
                            "fieldConfig": {
                                "defaults": {
                                    "color": {
                                        "mode": "palette-classic"
                                    },
                                    "custom": {
                                        "axisCenteredZero": False,
                                        "axisColorMode": "text",
                                        "axisLabel": "",
                                        "axisPlacement": "auto",
                                        "barAlignment": 0,
                                        "drawStyle": "line",
                                        "fillOpacity": 10,
                                        "gradientMode": "none",
                                        "hideFrom": {
                                            "legend": False,
                                            "tooltip": False,
                                            "viz": False
                                        },
                                        "lineInterpolation": "linear",
                                        "lineWidth": 1,
                                        "pointSize": 5,
                                        "scaleDistribution": {
                                            "type": "linear"
                                        },
                                        "showPoints": "auto",
                                        "spanNulls": False,
                                        "stacking": {
                                            "group": "A",
                                            "mode": "none"
                                        },
                                        "thresholdsStyle": {
                                            "mode": "off"
                                        }
                                    },
                                    "mappings": [],
                                    "thresholds": {
                                        "mode": "absolute",
                                        "steps": [
                                            {
                                                "color": "red",
                                                "value": None
                                            },
                                            {
                                                "color": "green",
                                                "value": 0
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        # Panel 2: Win Rate
                        {
                            "id": 2,
                            "title": "Win Rate",
                            "type": "gauge",
                            "datasource": self.datasource_name,
                            "gridPos": {
                                "h": 8,
                                "w": 12,
                                "x": 12,
                                "y": 0
                            },
                            "targets": [
                                {
                                    "query": """
                                    from(bucket: "trading_metrics")
                                        |> range(start: -1h)
                                        |> filter(fn: (r) => r["_measurement"] == "win_rate")
                                        |> last()
                                    """,
                                    "refId": "A"
                                }
                            ],
                            "fieldConfig": {
                                "defaults": {
                                    "mappings": [],
                                    "thresholds": {
                                        "mode": "percentage",
                                        "steps": [
                                            {
                                                "color": "red",
                                                "value": None
                                            },
                                            {
                                                "color": "yellow",
                                                "value": 50
                                            },
                                            {
                                                "color": "green",
                                                "value": 70
                                            }
                                        ]
                                    },
                                    "unit": "percent"
                                }
                            }
                        },
                        # Panel 3: Drawdown et Volatilité
                        {
                            "id": 3,
                            "title": "Risques",
                            "type": "timeseries",
                            "datasource": self.datasource_name,
                            "gridPos": {
                                "h": 8,
                                "w": 12,
                                "x": 0,
                                "y": 8
                            },
                            "targets": [
                                {
                                    "query": """
                                    from(bucket: "trading_metrics")
                                        |> range(start: -7d)
                                        |> filter(fn: (r) => r["_measurement"] == "risk_metrics")
                                        |> filter(fn: (r) => r["_field"] == "drawdown")
                                    """,
                                    "refId": "A"
                                },
                                {
                                    "query": """
                                    from(bucket: "trading_metrics")
                                        |> range(start: -7d)
                                        |> filter(fn: (r) => r["_measurement"] == "risk_metrics")
                                        |> filter(fn: (r) => r["_field"] == "volatility")
                                    """,
                                    "refId": "B"
                                }
                            ],
                            "fieldConfig": {
                                "defaults": {
                                    "color": {
                                        "mode": "palette-classic"
                                    },
                                    "custom": {
                                        "axisCenteredZero": False,
                                        "axisColorMode": "text",
                                        "axisLabel": "",
                                        "axisPlacement": "auto",
                                        "barAlignment": 0,
                                        "drawStyle": "line",
                                        "fillOpacity": 10,
                                        "gradientMode": "none",
                                        "hideFrom": {
                                            "legend": False,
                                            "tooltip": False,
                                            "viz": False
                                        },
                                        "lineInterpolation": "linear",
                                        "lineWidth": 1,
                                        "pointSize": 5,
                                        "scaleDistribution": {
                                            "type": "linear"
                                        },
                                        "showPoints": "auto",
                                        "spanNulls": False,
                                        "stacking": {
                                            "group": "A",
                                            "mode": "none"
                                        },
                                        "thresholdsStyle": {
                                            "mode": "off"
                                        }
                                    },
                                    "mappings": [],
                                    "thresholds": {
                                        "mode": "percentage",
                                        "steps": [
                                            {
                                                "color": "green",
                                                "value": None
                                            },
                                            {
                                                "color": "yellow",
                                                "value": 5
                                            },
                                            {
                                                "color": "red",
                                                "value": 8
                                            }
                                        ]
                                    },
                                    "unit": "percent"
                                }
                            }
                        },
                        # Panel 4: Volume d'Échange
                        {
                            "id": 4,
                            "title": "Volume d'Échange",
                            "type": "timeseries",
                            "datasource": self.datasource_name,
                            "gridPos": {
                                "h": 8,
                                "w": 12,
                                "x": 12,
                                "y": 8
                            },
                            "targets": [
                                {
                                    "query": """
                                    from(bucket: "trading_metrics")
                                        |> range(start: -7d)
                                        |> filter(fn: (r) => r["_measurement"] == "trading_volume")
                                        |> yield(name: "mean")
                                    """,
                                    "refId": "A"
                                }
                            ],
                            "fieldConfig": {
                                "defaults": {
                                    "color": {
                                        "mode": "palette-classic"
                                    },
                                    "custom": {
                                        "axisCenteredZero": False,
                                        "axisColorMode": "text",
                                        "axisLabel": "",
                                        "axisPlacement": "auto",
                                        "barAlignment": 0,
                                        "drawStyle": "line",
                                        "fillOpacity": 10,
                                        "gradientMode": "none",
                                        "hideFrom": {
                                            "legend": False,
                                            "tooltip": False,
                                            "viz": False
                                        },
                                        "lineInterpolation": "linear",
                                        "lineWidth": 1,
                                        "pointSize": 5,
                                        "scaleDistribution": {
                                            "type": "linear"
                                        },
                                        "showPoints": "auto",
                                        "spanNulls": False,
                                        "stacking": {
                                            "group": "A",
                                            "mode": "none"
                                        },
                                        "thresholdsStyle": {
                                            "mode": "off"
                                        }
                                    },
                                    "mappings": [],
                                    "thresholds": {
                                        "mode": "absolute",
                                        "steps": [
                                            {
                                                "color": "red",
                                                "value": None
                                            },
                                            {
                                                "color": "green",
                                                "value": 0
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                },
                "overwrite": True
            }
            
            response = requests.post(
                f"{self.grafana_url}/api/dashboards/db",
                headers=self.headers,
                json=dashboard_config
            )
            
            if response.status_code == 200:
                logger.info("Dashboard créé avec succès")
                return True
            else:
                logger.error(f"Erreur lors de la création du dashboard: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la création du dashboard: {str(e)}")
            return False
            
    def deploy(self) -> bool:
        """
        Déploie le dashboard complet.
        
        Returns:
            bool: True si le déploiement est réussi
        """
        try:
            # Création de la source de données
            if not self.create_datasource():
                return False
                
            # Création du dashboard
            if not self.create_dashboard():
                return False
                
            logger.info("Déploiement du dashboard terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement: {str(e)}")
            return False

def main():
    """
    Fonction principale pour le déploiement du dashboard.
    """
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Récupération des variables d'environnement
    grafana_url = os.getenv('GRAFANA_URL', 'http://localhost:3000')
    api_key = os.getenv('GRAFANA_API_KEY')
    
    if not api_key:
        logger.error("La clé API Grafana n'est pas définie")
        return
        
    # Création et déploiement du dashboard
    deployer = GrafanaDashboardDeployer(grafana_url, api_key)
    if deployer.deploy():
        logger.info("Dashboard déployé avec succès")
    else:
        logger.error("Échec du déploiement du dashboard")

if __name__ == "__main__":
    main() 