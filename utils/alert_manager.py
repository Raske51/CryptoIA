import os
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Gestionnaire d'alertes pour le bot de trading.
    """
    def __init__(self,
                 telegram_token: Optional[str] = None,
                 telegram_chat_id: Optional[str] = None,
                 email_smtp_server: Optional[str] = None,
                 email_smtp_port: Optional[int] = None,
                 email_username: Optional[str] = None,
                 email_password: Optional[str] = None,
                 email_recipients: Optional[list] = None):
        """
        Initialise le gestionnaire d'alertes.
        
        Args:
            telegram_token (str): Token du bot Telegram
            telegram_chat_id (str): ID du chat Telegram
            email_smtp_server (str): Serveur SMTP pour les emails
            email_smtp_port (int): Port SMTP
            email_username (str): Nom d'utilisateur email
            email_password (str): Mot de passe email
            email_recipients (list): Liste des destinataires email
        """
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.email_smtp_server = email_smtp_server or os.getenv('EMAIL_SMTP_SERVER')
        self.email_smtp_port = email_smtp_port or int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email_username = email_username or os.getenv('EMAIL_USERNAME')
        self.email_password = email_password or os.getenv('EMAIL_PASSWORD')
        self.email_recipients = email_recipients or json.loads(os.getenv('EMAIL_RECIPIENTS', '[]'))
        
        # Initialisation de l'application Telegram
        if self.telegram_token:
            self.telegram_app = ApplicationBuilder().token(self.telegram_token).build()
            
    async def send_telegram_alert(self, message: str) -> bool:
        """
        Envoie une alerte via Telegram.
        
        Args:
            message (str): Message à envoyer
            
        Returns:
            bool: True si l'envoi est réussi
        """
        try:
            if not self.telegram_token or not self.telegram_chat_id:
                logger.warning("Configuration Telegram manquante")
                return False
                
            await self.telegram_app.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte Telegram: {str(e)}")
            return False
            
    def send_email_alert(self, subject: str, message: str) -> bool:
        """
        Envoie une alerte par email.
        
        Args:
            subject (str): Sujet de l'email
            message (str): Contenu de l'email
            
        Returns:
            bool: True si l'envoi est réussi
        """
        try:
            if not all([self.email_smtp_server, self.email_username, self.email_password, self.email_recipients]):
                logger.warning("Configuration email manquante")
                return False
                
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = ', '.join(self.email_recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'html'))
            
            with smtplib.SMTP(self.email_smtp_server, self.email_smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte email: {str(e)}")
            return False
            
    async def send_trade_alert(self, signal: Dict[str, Any]) -> bool:
        """
        Envoie une alerte de trading.
        
        Args:
            signal (Dict[str, Any]): Données du signal
            
        Returns:
            bool: True si l'envoi est réussi
        """
        try:
            # Formatage du message
            message = f"""
🚨 **Nouveau Signal** 🚨
➤ Paire: {signal['pair']}
➤ Prix Entrée: {signal['entry_price']}
➤ Stop-Loss: {signal['stop_loss']} ({round(signal['sl_pct'],2)}%)
➤ Take-Profit: {signal['take_profit']} 
➤ Ratio R/R: {signal['risk_reward']}x
➤ Confiance IA: {signal['confidence']}/100
📊 Volatilité 24h: {signal['volatility']}%
            """
            
            # Envoi via Telegram
            telegram_success = await self.send_telegram_alert(message)
            
            # Envoi via Email
            email_success = self.send_email_alert(
                subject=f"Nouveau Signal de Trading - {signal['pair']}",
                message=message.replace('*', '')
            )
            
            return telegram_success or email_success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte de trading: {str(e)}")
            return False
            
    async def send_risk_alert(self, risk_metrics: Dict[str, Any]) -> bool:
        """
        Envoie une alerte de risque.
        
        Args:
            risk_metrics (Dict[str, Any]): Métriques de risque
            
        Returns:
            bool: True si l'envoi est réussi
        """
        try:
            # Formatage du message
            message = f"""
⚠️ **Alerte de Risque** ⚠️
➤ Drawdown: {risk_metrics['drawdown']:.2%}
➤ Volatilité: {risk_metrics['volatility']:.2%}
➤ Win Rate: {risk_metrics['win_rate']:.2%}
➤ Ratio R/R: {risk_metrics['risk_reward_ratio']:.2f}
            """
            
            # Envoi via Telegram
            telegram_success = await self.send_telegram_alert(message)
            
            # Envoi via Email
            email_success = self.send_email_alert(
                subject="Alerte de Risque - Trading Bot",
                message=message.replace('*', '')
            )
            
            return telegram_success or email_success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte de risque: {str(e)}")
            return False
            
    async def send_error_alert(self, error: Exception, context: str) -> bool:
        """
        Envoie une alerte d'erreur.
        
        Args:
            error (Exception): L'erreur à signaler
            context (str): Contexte de l'erreur
            
        Returns:
            bool: True si l'envoi est réussi
        """
        try:
            # Formatage du message
            message = f"""
❌ **Erreur Critique** ❌
➤ Contexte: {context}
➤ Type: {type(error).__name__}
➤ Message: {str(error)}
➤ Timestamp: {datetime.now().isoformat()}
            """
            
            # Envoi via Telegram
            telegram_success = await self.send_telegram_alert(message)
            
            # Envoi via Email
            email_success = self.send_email_alert(
                subject="Erreur Critique - Trading Bot",
                message=message.replace('*', '')
            )
            
            return telegram_success or email_success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte d'erreur: {str(e)}")
            return False
            
    async def close(self):
        """
        Ferme les connexions.
        """
        try:
            if hasattr(self, 'telegram_app'):
                await self.telegram_app.shutdown()
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture des connexions: {str(e)}") 