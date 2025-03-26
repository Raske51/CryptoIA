import os
import json
import logging
import base64
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SecurityManager:
    """
    Gestionnaire de sécurité pour le chiffrement et la protection des données sensibles.
    """
    def __init__(self,
                 key_file: str = 'config/encryption.key',
                 salt_file: str = 'config/salt.bin',
                 encrypted_file: str = 'config/encrypted_data.bin'):
        """
        Initialise le gestionnaire de sécurité.
        
        Args:
            key_file (str): Chemin du fichier de clé
            salt_file (str): Chemin du fichier de sel
            encrypted_file (str): Chemin du fichier de données chiffrées
        """
        self.key_file = key_file
        self.salt_file = salt_file
        self.encrypted_file = encrypted_file
        self.key = None
        self.cipher = None
        self._initialize_encryption()
        
    def _initialize_encryption(self):
        """
        Initialise le système de chiffrement.
        """
        try:
            # Création du dossier config si nécessaire
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            
            # Génération ou chargement de la clé
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(self.key)
                    
            self.cipher = Fernet(self.key)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du chiffrement: {str(e)}")
            raise
            
    def encrypt_data(self, data: str) -> str:
        """
        Chiffre une chaîne de caractères.
        
        Args:
            data (str): Données à chiffrer
            
        Returns:
            str: Données chiffrées en base64
        """
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement des données: {str(e)}")
            raise
            
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Déchiffre une chaîne de caractères.
        
        Args:
            encrypted_data (str): Données chiffrées en base64
            
        Returns:
            str: Données déchiffrées
        """
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement des données: {str(e)}")
            raise
            
    def encrypt_sensitive_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chiffre les données sensibles d'une configuration.
        
        Args:
            config (Dict[str, Any]): Configuration à sécuriser
            
        Returns:
            Dict[str, Any]: Configuration avec données sensibles chiffrées
        """
        try:
            sensitive_keys = ['api_key', 'api_secret', 'token', 'password', 'key']
            encrypted_config = config.copy()
            
            for key, value in config.items():
                if any(sk in key.lower() for sk in sensitive_keys):
                    if isinstance(value, str):
                        encrypted_config[key] = self.encrypt_data(value)
                    elif isinstance(value, dict):
                        encrypted_config[key] = self.encrypt_sensitive_config(value)
                        
            return encrypted_config
            
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement de la configuration: {str(e)}")
            raise
            
    def decrypt_sensitive_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Déchiffre les données sensibles d'une configuration.
        
        Args:
            config (Dict[str, Any]): Configuration chiffrée
            
        Returns:
            Dict[str, Any]: Configuration avec données sensibles déchiffrées
        """
        try:
            sensitive_keys = ['api_key', 'api_secret', 'token', 'password', 'key']
            decrypted_config = config.copy()
            
            for key, value in config.items():
                if any(sk in key.lower() for sk in sensitive_keys):
                    if isinstance(value, str):
                        decrypted_config[key] = self.decrypt_data(value)
                    elif isinstance(value, dict):
                        decrypted_config[key] = self.decrypt_sensitive_config(value)
                        
            return decrypted_config
            
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement de la configuration: {str(e)}")
            raise
            
    def secure_env_vars(self, env_file: str = '.env'):
        """
        Chiffre les variables d'environnement sensibles.
        
        Args:
            env_file (str): Chemin du fichier .env
        """
        try:
            if not os.path.exists(env_file):
                logger.warning(f"Le fichier {env_file} n'existe pas")
                return
                
            # Sauvegarde du fichier original
            backup_file = f"{env_file}.backup"
            if not os.path.exists(backup_file):
                with open(env_file, 'r') as f:
                    with open(backup_file, 'w') as bf:
                        bf.write(f.read())
                        
            # Lecture et chiffrement des variables
            encrypted_vars = {}
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if any(sk in key.lower() for sk in ['key', 'secret', 'token', 'password']):
                            encrypted_vars[key] = self.encrypt_data(value)
                        else:
                            encrypted_vars[key] = value
                            
            # Sauvegarde des variables chiffrées
            with open(self.encrypted_file, 'w') as f:
                json.dump(encrypted_vars, f, indent=4)
                
            logger.info(f"Variables d'environnement sécurisées sauvegardées dans {self.encrypted_file}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sécurisation des variables d'environnement: {str(e)}")
            raise
            
    def load_secure_env_vars(self):
        """
        Charge et déchiffre les variables d'environnement sécurisées.
        """
        try:
            if not os.path.exists(self.encrypted_file):
                logger.warning(f"Le fichier {self.encrypted_file} n'existe pas")
                return
                
            with open(self.encrypted_file, 'r') as f:
                encrypted_vars = json.load(f)
                
            for key, value in encrypted_vars.items():
                if any(sk in key.lower() for sk in ['key', 'secret', 'token', 'password']):
                    os.environ[key] = self.decrypt_data(value)
                else:
                    os.environ[key] = value
                    
            logger.info("Variables d'environnement sécurisées chargées")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des variables d'environnement: {str(e)}")
            raise
            
    def rotate_key(self):
        """
        Rotation de la clé de chiffrement.
        """
        try:
            # Sauvegarde de l'ancienne clé
            old_key_file = f"{self.key_file}.old"
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    with open(old_key_file, 'wb') as of:
                        of.write(f.read())
                        
            # Génération d'une nouvelle clé
            new_key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(new_key)
                
            # Mise à jour du chiffreur
            self.key = new_key
            self.cipher = Fernet(self.key)
            
            logger.info("Clé de chiffrement rotée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la rotation de la clé: {str(e)}")
            raise
            
    def verify_integrity(self, data: str, signature: str) -> bool:
        """
        Vérifie l'intégrité des données.
        
        Args:
            data (str): Données à vérifier
            signature (str): Signature en base64
            
        Returns:
            bool: True si l'intégrité est vérifiée
        """
        try:
            h = hashes.Hash(hashes.SHA256(), backend=default_backend())
            h.update(data.encode())
            computed_signature = base64.b64encode(h.finalize()).decode()
            return computed_signature == signature
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'intégrité: {str(e)}")
            return False

    def encrypt_sensitive_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chiffre les données sensibles dans un dictionnaire de configuration.
        
        Args:
            config (Dict[str, Any]): Configuration à chiffrer
            
        Returns:
            Dict[str, Any]: Configuration avec les données sensibles chiffrées
        """
        try:
            sensitive_fields = [
                'api_key', 'api_secret', 'access_token', 'access_token_secret',
                'private_key', 'password', 'secret'
            ]
            
            encrypted_config = config.copy()
            for key, value in config.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    encrypted_config[key] = self.encrypt_data(str(value))
            
            return encrypted_config
            
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement de la configuration: {str(e)}")
            raise

    def decrypt_sensitive_config(self, encrypted_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Déchiffre les données sensibles dans un dictionnaire de configuration.
        
        Args:
            encrypted_config (Dict[str, Any]): Configuration chiffrée
            
        Returns:
            Dict[str, Any]: Configuration avec les données sensibles déchiffrées
        """
        try:
            sensitive_fields = [
                'api_key', 'api_secret', 'access_token', 'access_token_secret',
                'private_key', 'password', 'secret'
            ]
            
            decrypted_config = encrypted_config.copy()
            for key, value in encrypted_config.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    decrypted_config[key] = self.decrypt_data(value)
            
            return decrypted_config
            
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement de la configuration: {str(e)}")
            raise

    def secure_env_vars(self, env_file: str = ".env") -> None:
        """
        Chiffre les variables d'environnement sensibles.
        
        Args:
            env_file (str): Chemin du fichier .env
        """
        try:
            if not os.path.exists(env_file):
                logger.warning(f"Fichier {env_file} non trouvé")
                return
            
            # Lecture du fichier .env
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Chiffrement des variables sensibles
            sensitive_vars = [
                'API_KEY', 'API_SECRET', 'ACCESS_TOKEN', 'ACCESS_TOKEN_SECRET',
                'PRIVATE_KEY', 'PASSWORD', 'SECRET'
            ]
            
            encrypted_lines = []
            for line in lines:
                if any(var in line for var in sensitive_vars):
                    key, value = line.strip().split('=', 1)
                    encrypted_value = self.encrypt_data(value)
                    encrypted_lines.append(f"{key}={encrypted_value}\n")
                else:
                    encrypted_lines.append(line)
            
            # Sauvegarde du fichier chiffré
            backup_file = f"{env_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            os.rename(env_file, backup_file)
            
            with open(env_file, 'w') as f:
                f.writelines(encrypted_lines)
            
            logger.info(f"Variables d'environnement chiffrées. Backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement des variables d'environnement: {str(e)}")
            raise

    def load_secure_env_vars(self) -> None:
        """
        Charge et déchiffre les variables d'environnement.
        """
        try:
            load_dotenv()
            
            # Déchiffrement des variables sensibles
            sensitive_vars = [
                'API_KEY', 'API_SECRET', 'ACCESS_TOKEN', 'ACCESS_TOKEN_SECRET',
                'PRIVATE_KEY', 'PASSWORD', 'SECRET'
            ]
            
            for var in sensitive_vars:
                value = os.getenv(var)
                if value:
                    try:
                        decrypted_value = self.decrypt_data(value)
                        os.environ[var] = decrypted_value
                    except:
                        logger.warning(f"Impossible de déchiffrer la variable {var}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des variables d'environnement: {str(e)}")
            raise 