import os
from dotenv import load_dotenv
from binance.client import Client
import ccxt
import pandas as pd
import numpy as np

# Charger les variables d'environnement
load_dotenv()

# Configuration des clés API
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

class CryptoBot:
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        
    def get_account_balance(self):
        """Récupère le solde du compte"""
        try:
            account = self.client.get_account()
            balances = account['balances']
            # Filtrer uniquement les actifs non nuls
            return [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
        except Exception as e:
            print(f"Erreur lors de la récupération du solde: {e}")
            return None

    def get_market_data(self, symbol='BTCUSDT', interval='1h', limit=100):
        """Récupère les données du marché"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                               'close_time', 'quote_asset_volume', 'number_of_trades',
                                               'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume',
                                               'ignore'])
        except Exception as e:
            print(f"Erreur lors de la récupération des données du marché: {e}")
            return None

def main():
    bot = CryptoBot()
    
    # Test de connexion
    print("Vérification du solde du compte...")
    balances = bot.get_account_balance()
    if balances:
        print("Soldes disponibles:")
        for balance in balances:
            print(f"{balance['asset']}: Free={balance['free']}, Locked={balance['locked']}")
    
    # Test de récupération des données du marché
    print("\nRécupération des données du marché pour BTC/USDT...")
    market_data = bot.get_market_data()
    if market_data is not None:
        print(f"Dernières données récupérées:\n{market_data.tail()}")

if __name__ == "__main__":
    main() 