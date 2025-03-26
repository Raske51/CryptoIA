import os
import json
import logging
import pyotp
import qrcode
import base64
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from io import BytesIO
from .security_manager import SecurityManager
from .alert_manager import AlertManager

logger = logging.getLogger(__name__)

class AuthManager:
    """
    Gestionnaire d'authentification pour la sécurité des accès.
    """
    def __init__(self,
                 security_manager: SecurityManager,
                 alert_manager: AlertManager,
                 users_file: str = 'config/users.json',
                 session_file: str = 'config/sessions.json'):
        """
        Initialise le gestionnaire d'authentification.
        
        Args:
            security_manager (SecurityManager): Gestionnaire de sécurité
            alert_manager (AlertManager): Gestionnaire d'alertes
            users_file (str): Chemin du fichier des utilisateurs
            session_file (str): Chemin du fichier des sessions
        """
        self.security_manager = security_manager
        self.alert_manager = alert_manager
        self.users_file = users_file
        self.session_file = session_file
        self.users = self._load_users()
        self.sessions = self._load_sessions()
        
    def _load_users(self) -> Dict[str, Any]:
        """
        Charge les utilisateurs depuis le fichier de configuration.
        
        Returns:
            Dict[str, Any]: Dictionnaire des utilisateurs
        """
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Erreur lors du chargement des utilisateurs: {str(e)}")
            return {}
            
    def _load_sessions(self) -> Dict[str, Any]:
        """
        Charge les sessions depuis le fichier de configuration.
        
        Returns:
            Dict[str, Any]: Dictionnaire des sessions
        """
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Erreur lors du chargement des sessions: {str(e)}")
            return {}
            
    def _save_users(self):
        """
        Sauvegarde les utilisateurs dans le fichier de configuration.
        """
        try:
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=4)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des utilisateurs: {str(e)}")
            
    def _save_sessions(self):
        """
        Sauvegarde les sessions dans le fichier de configuration.
        """
        try:
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(self.sessions, f, indent=4)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des sessions: {str(e)}")
            
    def create_user(self,
                   user_id: str,
                   username: str,
                   password: str,
                   telegram_id: Optional[str] = None,
                   enable_2fa: bool = True) -> bool:
        """
        Crée un nouvel utilisateur.
        
        Args:
            user_id (str): Identifiant unique de l'utilisateur
            username (str): Nom d'utilisateur
            password (str): Mot de passe
            telegram_id (str): ID Telegram pour 2FA
            enable_2fa (bool): Activer l'authentification à deux facteurs
            
        Returns:
            bool: True si la création est réussie
        """
        try:
            if user_id in self.users:
                logger.warning(f"L'utilisateur {user_id} existe déjà")
                return False
                
            # Génération de la clé 2FA
            secret = pyotp.random_base32() if enable_2fa else None
            
            # Création de l'utilisateur
            self.users[user_id] = {
                'username': username,
                'password': self.security_manager.encrypt_data(password),
                'telegram_id': telegram_id,
                '2fa_secret': secret,
                '2fa_enabled': enable_2fa,
                'created_at': datetime.now().isoformat(),
                'last_login': None,
                'failed_attempts': 0,
                'locked_until': None
            }
            
            self._save_users()
            logger.info(f"Utilisateur {user_id} créé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            return False
            
    def generate_qr_code(self, user_id: str) -> Optional[str]:
        """
        Génère un QR code pour l'authentification à deux facteurs.
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            
        Returns:
            Optional[str]: QR code en base64 ou None
        """
        try:
            if user_id not in self.users:
                logger.warning(f"Utilisateur {user_id} non trouvé")
                return None
                
            user = self.users[user_id]
            if not user.get('2fa_secret'):
                logger.warning(f"2FA non activé pour l'utilisateur {user_id}")
                return None
                
            # Génération du QR code
            totp = pyotp.TOTP(user['2fa_secret'])
            provisioning_uri = totp.provisioning_uri(
                user['username'],
                issuer_name="Trading Bot"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
            return None
            
    async def verify_2fa(self, user_id: str, code: str) -> bool:
        """
        Vérifie le code 2FA.
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            code (str): Code à vérifier
            
        Returns:
            bool: True si le code est valide
        """
        try:
            if user_id not in self.users:
                logger.warning(f"Utilisateur {user_id} non trouvé")
                return False
                
            user = self.users[user_id]
            if not user.get('2fa_secret'):
                logger.warning(f"2FA non activé pour l'utilisateur {user_id}")
                return False
                
            totp = pyotp.TOTP(user['2fa_secret'])
            is_valid = totp.verify(code)
            
            if is_valid:
                # Réinitialisation des tentatives échouées
                user['failed_attempts'] = 0
                user['locked_until'] = None
                self._save_users()
                
                # Notification de connexion réussie
                await self.alert_manager.send_telegram_alert(
                    user['telegram_id'],
                    "🔐 Connexion réussie avec 2FA"
                )
            else:
                # Incrémentation des tentatives échouées
                user['failed_attempts'] += 1
                if user['failed_attempts'] >= 3:
                    user['locked_until'] = (datetime.now() + timedelta(minutes=15)).isoformat()
                    await self.alert_manager.send_telegram_alert(
                        user['telegram_id'],
                        "⚠️ Compte temporairement verrouillé après 3 tentatives échouées"
                    )
                self._save_users()
                
            return is_valid
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification 2FA: {str(e)}")
            return False
            
    async def send_2fa_code(self, user_id: str) -> bool:
        """
        Envoie le code 2FA par Telegram.
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            
        Returns:
            bool: True si l'envoi est réussi
        """
        try:
            if user_id not in self.users:
                logger.warning(f"Utilisateur {user_id} non trouvé")
                return False
                
            user = self.users[user_id]
            if not user.get('2fa_secret') or not user.get('telegram_id'):
                logger.warning(f"2FA ou Telegram ID non configuré pour l'utilisateur {user_id}")
                return False
                
            totp = pyotp.TOTP(user['2fa_secret'])
            code = totp.now()
            
            await self.alert_manager.send_telegram_alert(
                user['telegram_id'],
                f"🔑 Votre code 2FA: {code}\nCe code expire dans 30 secondes."
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du code 2FA: {str(e)}")
            return False
            
    def create_session(self, user_id: str, token: str) -> bool:
        """
        Crée une nouvelle session.
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            token (str): Token de session
            
        Returns:
            bool: True si la création est réussie
        """
        try:
            self.sessions[token] = {
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            
            self._save_sessions()
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la session: {str(e)}")
            return False
            
    def verify_session(self, token: str) -> Optional[str]:
        """
        Vérifie la validité d'une session.
        
        Args:
            token (str): Token de session
            
        Returns:
            Optional[str]: ID de l'utilisateur si la session est valide
        """
        try:
            if token not in self.sessions:
                return None
                
            session = self.sessions[token]
            expires_at = datetime.fromisoformat(session['expires_at'])
            
            if datetime.now() > expires_at:
                del self.sessions[token]
                self._save_sessions()
                return None
                
            # Mise à jour de la dernière activité
            session['last_activity'] = datetime.now().isoformat()
            self._save_sessions()
            
            return session['user_id']
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la session: {str(e)}")
            return None
            
    def revoke_session(self, token: str) -> bool:
        """
        Révoque une session.
        
        Args:
            token (str): Token de session
            
        Returns:
            bool: True si la révocation est réussie
        """
        try:
            if token in self.sessions:
                del self.sessions[token]
                self._save_sessions()
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la révocation de la session: {str(e)}")
            return False
            
    def cleanup_expired_sessions(self):
        """
        Nettoie les sessions expirées.
        """
        try:
            now = datetime.now()
            expired_tokens = []
            
            for token, session in self.sessions.items():
                expires_at = datetime.fromisoformat(session['expires_at'])
                if now > expires_at:
                    expired_tokens.append(token)
                    
            for token in expired_tokens:
                del self.sessions[token]
                
            if expired_tokens:
                self._save_sessions()
                logger.info(f"{len(expired_tokens)} sessions expirées nettoyées")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des sessions: {str(e)}") 