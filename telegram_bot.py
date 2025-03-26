import os
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from config.config import TELEGRAM_CONFIG, TRADING_CONFIG
from main import CryptoBot
from dotenv import load_dotenv

load_dotenv()

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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

async def send_status_message(context: ContextTypes.DEFAULT_TYPE):
    """Envoie un message de statut périodique"""
    try:
        await context.bot.send_message(
            chat_id='7072895112',
            text="🤖 Bot en marche !"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message de statut : {e}")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Paramètres du bot:\n" + crypto_bot.get_settings())

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = crypto_bot.execute_trade()
    await update.message.reply_text(f"💰 Résultat du trade:\n{result}")

async def webhook_handler(request):
    """Handle incoming webhook requests from Telegram."""
    try:
        TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not TOKEN:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")

        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("settings", settings))
        app.add_handler(CommandHandler("trade", trade))

        # Process update
        update = Update.de_json(await request.json(), app.bot)
        await app.process_update(update)
        
        return {"statusCode": 200, "body": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"statusCode": 500, "body": str(e)}

def main():
    """Run the bot in polling mode for local development."""
    try:
        TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not TOKEN:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")

        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("settings", settings))
        app.add_handler(CommandHandler("trade", trade))

        # Start the bot in polling mode
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")

if __name__ == '__main__':
    main() 