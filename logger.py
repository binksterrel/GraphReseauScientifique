"""
Module de configuration centralisée du logging pour Episteme-Network.

Usage:
    from logger import get_logger
    logger = get_logger(__name__)
    logger.info("Message informatif")
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Récupère ou crée un logger configuré pour le module spécifié.

    Args:
        name: Nom du module (généralement __name__)
        level: Niveau de logging (par défaut INFO, peut être surchargé via LOG_LEVEL env var)

    Returns:
        Logger configuré avec handler stdout et formatage timestamp
    """
    import os

    # Déterminer le niveau de log
    if level is None:
        env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Éviter les handlers dupliqués
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Format avec timestamp, nom du module et niveau
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def setup_root_logger(level: int = logging.INFO) -> None:
    """
    Configure le logger racine pour l'application.

    Args:
        level: Niveau de logging pour le logger racine
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
