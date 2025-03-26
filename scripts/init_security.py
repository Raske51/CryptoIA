import os
import logging
from utils.security_manager import SecurityManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_security():
    """
    Initialise la sécurité et chiffre les données sensibles.
    """
    try:
        # Initialisation du gestionnaire de sécurité
        security_manager = SecurityManager()
        
        # Vérification du fichier .env
        if not os.path.exists(".env"):
            logger.error("Fichier .env non trouvé")
            return
        
        # Chiffrement des variables d'environnement
        security_manager.secure_env_vars()
        
        logger.info("Initialisation de la sécurité terminée")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la sécurité: {str(e)}")
        raise

def test_encryption():
    """
    Teste le chiffrement et le déchiffrement.
    """
    try:
        security_manager = SecurityManager()
        
        # Test de chiffrement simple
        test_data = "Données sensibles de test"
        encrypted = security_manager.encrypt_data(test_data)
        decrypted = security_manager.decrypt_data(encrypted)
        
        logger.info("Test de chiffrement:")
        logger.info(f"Données originales: {test_data}")
        logger.info(f"Données chiffrées: {encrypted}")
        logger.info(f"Données déchiffrées: {decrypted}")
        logger.info(f"Test réussi: {test_data == decrypted}")
        
        # Test de configuration
        test_config = {
            "api_key": "test_key_123",
            "api_secret": "test_secret_456",
            "other_setting": "non_sensible"
        }
        
        encrypted_config = security_manager.encrypt_sensitive_config(test_config)
        decrypted_config = security_manager.decrypt_sensitive_config(encrypted_config)
        
        logger.info("\nTest de configuration:")
        logger.info(f"Configuration originale: {test_config}")
        logger.info(f"Configuration chiffrée: {encrypted_config}")
        logger.info(f"Configuration déchiffrée: {decrypted_config}")
        logger.info(f"Test réussi: {test_config == decrypted_config}")
        
    except Exception as e:
        logger.error(f"Erreur lors des tests de chiffrement: {str(e)}")
        raise

def main():
    """
    Fonction principale.
    """
    try:
        logger.info("Démarrage de l'initialisation de la sécurité")
        
        # Initialisation de la sécurité
        init_security()
        
        # Tests de chiffrement
        test_encryption()
        
        logger.info("Initialisation de la sécurité terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 