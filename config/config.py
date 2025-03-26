import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration Binance
BINANCE_CONFIG = {
    'api_key': os.getenv('BINANCE_API_KEY'),
    'api_secret': os.getenv('BINANCE_API_SECRET'),
    'testnet': os.getenv('USE_TESTNET', 'False').lower() == 'true'
}

# Configuration Telegram
TELEGRAM_CONFIG = {
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
    'use_telegram': os.getenv('USE_TELEGRAM', 'True').lower() == 'true'
}

# Configuration Trading
TRADING_CONFIG = {
    'default_symbol': 'BTCUSDT',
    'default_interval': '1h',
    'default_limit': 100,
    'max_trades_per_day': 5,
    'risk_percentage': 1.0,  # Pourcentage du portfolio à risquer par trade
    'stop_loss_percentage': 2.0,  # Pourcentage de stop loss
    'take_profit_percentage': 3.0  # Pourcentage de take profit
}

# Configuration Cloud
CLOUD_CONFIG = {
    'provider': os.getenv('CLOUD_PROVIDER', 'clouding'),
    'instance_type': os.getenv('INSTANCE_TYPE', 'small'),
    'region': os.getenv('CLOUD_REGION', 'eu-west-1')
} 