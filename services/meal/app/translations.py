TRANSLATIONS = {
    "EN": {
        # Aliment
        "aliment_already_exists": "This food already exists.",
        "aliment_not_found": "Food not found (id={id}).",
        # User
        "email_already_used": "Email already in use.",
        "user_not_found": "User not found.",
        # Meal
        "meal_not_found": "Meal not found.",
        # Subscription
        "invalid_subscription": "Invalid subscription. Accepted values: {values}.",
        # Objective
        "objective_not_found": "Objective not found.",
        "objective_already_set": "This objective is already set for this user.",
        "user_objective_not_found": "Objective not found for this user.",
    },
    "FR": {
        # Aliment
        "aliment_already_exists": "Cet aliment existe déjà.",
        "aliment_not_found": "Aliment introuvable (id={id}).",
        # User
        "email_already_used": "Email déjà utilisé.",
        "user_not_found": "Utilisateur introuvable.",
        # Meal
        "meal_not_found": "Repas introuvable.",
        # Subscription
        "invalid_subscription": "Abonnement invalide. Valeurs acceptées : {values}.",
        # Objective
        "objective_not_found": "Objectif introuvable.",
        "objective_already_set": "Cet objectif est déjà défini pour cet utilisateur.",
        "user_objective_not_found": "Objectif introuvable pour cet utilisateur.",
    },
}


def get_message(key: str, language: str = "EN", **kwargs) -> str:
    language = language.upper()
    if language not in TRANSLATIONS:
        language = "EN"
    msg = TRANSLATIONS.get(language, {}).get(key) or TRANSLATIONS["EN"].get(key, key)
    return msg.format(**kwargs) if kwargs else msg
