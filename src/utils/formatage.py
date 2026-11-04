"""Mise en forme française des nombres affichés (espace fine comme séparateur de milliers)."""

ESPACE_FINE = " "


def entier(valeur: float) -> str:
    """12345 → « 12 345 »."""
    return f"{valeur:,.0f}".replace(",", ESPACE_FINE)


def decimal(valeur: float, chiffres: int = 1) -> str:
    """5.66 → « 5,7 »."""
    return f"{valeur:,.{chiffres}f}".replace(",", ESPACE_FINE).replace(".", ",")


def pourcentage(part: float, chiffres: int = 0) -> str:
    """0.7015 → « 70 % » (part entre 0 et 1)."""
    return f"{decimal(part * 100, chiffres)}{ESPACE_FINE}%"
