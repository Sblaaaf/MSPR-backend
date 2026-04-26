# Dictionnaire des traductions pour les messages d'authentification
TRANSLATIONS = {
    "EN": {
        "invalid_credentials": "Email or password incorrect.",
        "user_inactive": "User account is inactive.",
        "login_success": "Authentication successful.",
    },
    "FR": {
        "invalid_credentials": "Email ou mot de passe incorrect.",
        "user_inactive": "Utilisateur inactif.",
        "login_success": "Authentification réussie.",
    }
}

def get_message(key: str, language: str = "EN") -> str:
    """
    Récupère un message traduit.
    
    Args:
        key: Clé du message
        language: Code de langue ("EN" ou "FR")
    
    Returns:
        Message traduit ou le message par défaut en anglais
    """
    language = language.upper()
    if language not in TRANSLATIONS:
        language = "EN"
    
    return TRANSLATIONS.get(language, {}).get(key, TRANSLATIONS["EN"].get(key, key))
