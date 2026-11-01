"""Point d'entrée du projet : lance le dashboard avec « python main.py »."""

import logging

import config
from src.app import creer_application


def main() -> None:
    """Crée l'application et démarre le serveur web local, sans journal de requêtes."""
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    application = creer_application()
    print(f"Dashboard disponible sur http://{config.HOTE}:{config.PORT}")
    application.run(host=config.HOTE, port=config.PORT, debug=False)


if __name__ == "__main__":
    main()
