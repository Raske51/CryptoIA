import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from config.config import TELEGRAM_CONFIG, TRADING_CONFIG
from main import CryptoBot
import time

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialisation du bot de trading
crypto_bot = CryptoBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande de démarrage"""
    await update.message.reply_text(
        "👋 Bienvenue sur votre Bot de Trading Crypto!\n\n"
        "Commandes disponibles:\n"
        "/balance - Voir vos soldes\n"
        "/price <symbol> - Prix actuel (ex: /price BTCUSDT)\n"
        "/status - État du bot\n"
        "/help - Aide"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les soldes du compte"""
    balances = crypto_bot.get_account_balance()
    if balances:
        message = "💰 Vos soldes:\n\n"
        for balance in balances:
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                message += f"🔸 {balance['asset']}:\n"
                message += f"   Disponible: {balance['free']}\n"
                message += f"   Bloqué: {balance['locked']}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("❌ Erreur lors de la récupération des soldes")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche le prix actuel d'une paire"""
    if not context.args:
        await update.message.reply_text("❌ Veuillez spécifier une paire (ex: /price BTCUSDT)")
        return
    
    symbol = context.args[0].upper()
    market_data = crypto_bot.get_market_data(symbol=symbol, limit=1)
    
    if market_data is not None and not market_data.empty:
        last_price = market_data.iloc[-1]['close']
        await update.message.reply_text(f"💲 Prix actuel de {symbol}: {last_price}")
    else:
        await update.message.reply_text(f"❌ Erreur lors de la récupération du prix de {symbol}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche l'état du bot"""
    status_message = (
        "📊 État du Bot:\n\n"
        f"Symbol par défaut: {TRADING_CONFIG['default_symbol']}\n"
        f"Interval: {TRADING_CONFIG['default_interval']}\n"
        f"Trades max/jour: {TRADING_CONFIG['max_trades_per_day']}\n"
        f"Risk par trade: {TRADING_CONFIG['risk_percentage']}%\n"
        f"Stop Loss: {TRADING_CONFIG['stop_loss_percentage']}%\n"
        f"Take Profit: {TRADING_CONFIG['take_profit_percentage']}%"
    )
    await update.message.reply_text(status_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche l'aide"""
    help_text = (
        "🤖 Commandes disponibles:\n\n"
        "/start - Démarrer le bot\n"
        "/balance - Voir vos soldes\n"
        "/price <symbol> - Prix actuel\n"
        "/status - État du bot\n"
        "/help - Cette aide\n\n"
        "Pour plus d'informations, consultez la documentation."
    )
    await update.message.reply_text(help_text)

def main():
    # Initialize the bot with your token
    bot = Bot(token='7269334707:AAHS0X2aXPidWlSpum9pki6pfq-jl4oY_M9s')
    
    # Chat ID where messages will be sent
    chat_id = '7072895112'
    
    print("Bot started! Sending messages every 10 seconds...")
    
    try:
        while True:
            bot.send_message(chat_id=chat_id, text="🤖 Bot en marche !")
            time.sleep(10)  # Wait for 10 seconds before sending next message
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 