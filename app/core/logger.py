# app/core/logger.py

import logging
import os

# Asegúrate de que la carpeta 'logs' exista
os.makedirs("logs", exist_ok=True)

# Configura el logger
logging.basicConfig(
    filename="logs/sistema.log",
    level=logging.INFO,  # Puedes usar DEBUG, WARNING o ERROR según necesidad
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
